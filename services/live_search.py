from datetime import timedelta
import os
import json
import time
import requests
from dotenv import load_dotenv
from models.enquiry import Enquiry
import multiprocessing as mp


COUNTRY_CODES = {
    "uk": "GB",
    "united kingdom": "GB",
    "british": "GB",
    "british passport": "GB",
    "india": "IN",
    "indian": "IN",
    "ind": "IN",
}


def country_code(value: str | None, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")

    code = COUNTRY_CODES.get(value.strip().casefold())
    if code is None:
        raise ValueError(
            f"Cannot resolve {field_name} '{value}' to a verified "
            "RateLoc country code."
        )
    return code


def build_live_search_payload(
    enquiry: Enquiry,
    location: str,
    page: int = 1,
) -> dict:
    if not location:
        raise ValueError("Select a RateLoc destination first.")

    if enquiry.check_in is None or enquiry.nights is None:
        raise ValueError("Check-in and nights are required.")
    if enquiry.nights <= 0:
        raise ValueError("Nights must be greater than zero.")

    if enquiry.rooms != 1:
        raise ValueError(
            "Live search currently needs an explicit guest allocation "
            "for multiple rooms."
        )

    if enquiry.adults is None or enquiry.children is None:
        raise ValueError("Adult and child counts are required.")
    if enquiry.adults < 0 or enquiry.children < 0:
        raise ValueError("Guest counts cannot be negative.")
    if enquiry.adults + enquiry.children == 0:
        raise ValueError("At least one guest is required.")

    ages = enquiry.child_ages or []
    if len(ages) != enquiry.children:
        raise ValueError("Provide the age of each child.")

    if enquiry.currency is None:
        raise ValueError("Currency is required.")

    return {
        "checkInDate": enquiry.check_in.isoformat(),
        "checkOutDate": (
            enquiry.check_in + timedelta(days=enquiry.nights)
        ).isoformat(),
        "nationality": country_code(enquiry.nationality, "nationality"),
        "residency": country_code(enquiry.residency, "residency"),
        "rooms": [{
            "adults": enquiry.adults,
            "children": enquiry.children,
            "childAges": ages,
        }],
        "currency": enquiry.currency.strip().upper(),
        "sort": "RANKING",
        "page": {"page": page, "size": 20},
        "location": location,
    }

def lookup_destinations(query: str) -> list[dict]:
    load_dotenv()
    token = os.getenv("RATELOC_BEARER_TOKEN")
    if not token:
        raise RuntimeError("RATELOC_BEARER_TOKEN is missing from .env")

    response = requests.get(
        "https://apic.rateloc.com/accommodation/destinationSearch/"
        + requests.utils.quote(query.strip(), safe=""),
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    response.raise_for_status()

    payload = response.json()
    if payload.get("status") is not True:
        raise RuntimeError(
            payload.get("message", "Destination lookup failed")
        )

    return payload.get("data") or []

def _search_live_page(
    enquiry: Enquiry,
    location: str,
    page: int = 1,
) -> dict:
    load_dotenv()
    token = os.getenv("RATELOC_BEARER_TOKEN")
    if not token:
        raise RuntimeError("RATELOC_BEARER_TOKEN is missing from .env")

    payload = build_live_search_payload(enquiry, location, page)
    started = time.monotonic()
    printed_first_partial = False

    response = requests.post(
        "https://apic.rateloc.com/accommodation/v2/search",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    body = response.json()
    search_id = body.get("data", {}).get("searchId")

    if body.get("status") is not True or not search_id:
        raise RuntimeError("RateLoc did not create a search session.")

    print(f"Search session created after {time.monotonic() - started:.1f}s")

    stream_url = (
        "https://stream.apic.rateloc.com/"
        f"accommodation/v2/search/{search_id}/stream"
    )

    with requests.get(
        stream_url,
        headers={"Accept": "text/event-stream"},
        stream=True,
        timeout=(5, 10),
    ) as stream_response:
        stream_response.raise_for_status()

        for line in stream_response.iter_lines(chunk_size=65536, decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue

            event = json.loads(line[5:].strip())
            print(
                f"Event {event.get('eventType')} "
                f"after {time.monotonic() - started:.1f}s"
            )

            if event.get("eventType") == "partial_result" and not printed_first_partial:
                printed_first_partial = True
                print(f"First partial result after {time.monotonic() - started:.1f}s")
                print("Partial keys:", list(event.keys()))
                print("Partial hotels:", len(event.get("hotels") or []))
                hotels = event.get("hotels") or []
                print("Partial hotels with offers:", sum(bool(h.get("offers")) for h in hotels))
                print("Partial page:", event.get("page"))
            if event.get("eventType") == "partial_result":
                hotels = event.get("hotels") or []
                page_info = event.get("page") or {}

                if (
                    sum(bool(hotel.get("offers")) for hotel in hotels) >= 3
                    and isinstance(page_info.get("totalPages"), int)
                    and page_info["totalPages"] >= 1
                ):
                    print(
                        f"Using provisional results from {len(hotels)} hotels "
                        f"after {time.monotonic() - started:.1f}s"
                    )
                    return event

            if event.get("eventType") == "search_complete":
                print("RateLoc cache hit:", event.get("cacheHit"))
                print(f"Search complete after {time.monotonic() - started:.1f}s")
                if event.get("partial") or event.get("stale"):
                    raise RuntimeError(
                        "RateLoc returned partial or stale results."
                    )
                return event

    raise RuntimeError("Stream ended without search_complete.")
def _search_worker(connection, enquiry, location, page):
    try:
        result = _search_live_page(enquiry, location, page)
        connection.send(("ok", result))
    except Exception as error:
        connection.send(("error", str(error)))
    finally:
        connection.close()


def search_live_page(
    enquiry: Enquiry,
    location: str,
    page: int = 1,
) -> dict:
    context = mp.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(
        target=_search_worker,
        args=(child, enquiry, location, page),
    )

    process.start()
    child.close()

    try:
        if not parent.poll(15):
            raise TimeoutError(
                "RateLoc search exceeded 15 seconds. No live quote is available."
            )

        status, value = parent.recv()
        if status == "error":
            raise RuntimeError(value)
        return value
    finally:
        parent.close()
        if process.is_alive():
            process.terminate()
        process.join(timeout=2)
def search_live_pages(
    enquiry: Enquiry,
    location: str,
    max_pages: int = 2,
) -> tuple[list[dict], int]:
    if max_pages < 1:
        raise ValueError("max_pages must be at least 1")

    hotels = []
    total_pages = None

    for page_number in range(1, max_pages + 1):
        event = search_live_page(enquiry, location, page=page_number)
        page_info = event.get("page") or {}

        reported_pages = page_info.get("totalPages")
        if not isinstance(reported_pages, int) or reported_pages < 1:
            raise RuntimeError("RateLoc did not report valid pagination")

        if total_pages is None:
            total_pages = reported_pages
        elif total_pages != reported_pages:
            raise RuntimeError("Total page count changed during search")

        hotels.extend(event.get("hotels") or [])

        if page_number >= total_pages:
            break

    return hotels, total_pages