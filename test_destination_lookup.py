import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("RATELOC_BEARER_TOKEN")
if not token:
    raise RuntimeError("RATELOC_BEARER_TOKEN is missing from .env")

query = input("Destination: ").strip()
if not query:
    raise ValueError("Enter a destination.")

response = requests.get(
    f"https://apic.rateloc.com/accommodation/destinationSearch/{query}",
    headers={"Authorization": f"Bearer {token}"},
    timeout=15,
)
response.raise_for_status()

payload = response.json()
if payload.get("status") is not True:
    raise RuntimeError(payload.get("message", "Destination lookup failed"))

options = payload.get("data", [])[:10]
if not options:
    print("No destination suggestions found.")
    raise SystemExit

for number, option in enumerate(options, start=1):
    print(f"{number}. {option['CityStateCountry']}")

choice = int(input("Choose destination number: "))
if not 1 <= choice <= len(options):
    raise ValueError("Invalid selection.")

selected_location = options[choice - 1]["Location"]
print("API search location:", selected_location)
import json

base_payload = {
    "checkInDate": "2026-09-29",
    "checkOutDate": "2026-10-06",
    "nationality": "GB",
    "residency": "GB",
    "rooms": [{"adults": 2, "children": 0, "childAges": []}],
    "currency": "INR",
    "sort": "RANKING",
    "location": selected_location,
}

all_hotels = []
page_number = 1
total_pages = None

while total_pages is None or page_number <= total_pages:
    payload = {
        **base_payload,
        "page": {"page": page_number, "size": 20},
    }

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
        raise RuntimeError(f"Search session failed on page {page_number}")

    stream_url = (
        "https://stream.apic.rateloc.com/"
        f"accommodation/v2/search/{search_id}/stream"
    )

    complete_event = None

    with requests.get(
        stream_url,
        headers={"Accept": "text/event-stream"},
        stream=True,
        timeout=(15, 120),
    ) as stream_response:
        stream_response.raise_for_status()

        for line in stream_response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue

            event = json.loads(line[5:].strip())
            if event.get("eventType") == "search_complete":
                complete_event = event
                break

    if complete_event is None:
        raise RuntimeError(f"No search_complete event for page {page_number}")

    if complete_event.get("partial") or complete_event.get("stale"):
        raise RuntimeError(f"Page {page_number} is partial or stale")

    page_info = complete_event.get("page") or {}
    total_pages = page_info.get("totalPages")
    if not isinstance(total_pages, int) or total_pages < 1:
        raise RuntimeError("Missing or invalid totalPages")

    hotels = complete_event.get("hotels") or []
    all_hotels.extend(hotels)
    print(f"Page {page_number}/{total_pages}: {len(hotels)} hotels")

    page_number += 1

print("Hotels received:", len(all_hotels))
print("Distinct hotel codes:", len({
    hotel["uniqueCode"] for hotel in all_hotels
}))

for hotel in all_hotels[:5]:
    print(
        hotel.get("title"),
        "| rating:", hotel.get("rating"),
        "| listed price:", hotel.get("price"),
        "| offers:", len(hotel.get("offers") or []),
        "| amenities:", len(hotel.get("amenities") or []),
    )

def cheapest_offer(hotel):
    valid_offers = [
        offer
        for offer in hotel.get("offers", [])
        if isinstance(offer.get("displayPrice"), (int, float))
        and offer.get("currency") == "INR"
    ]
    return min(
        valid_offers,
        key=lambda offer: offer["displayPrice"],
        default=None,
    )


candidates = []

for position, hotel in enumerate(all_hotels):
    offer = cheapest_offer(hotel)
    if offer is None:
        continue

    try:
        rating = int(hotel["rating"])
    except (TypeError, ValueError, KeyError):
        continue

    candidates.append({
        "position": position,  # API RANKING order
        "code": hotel["uniqueCode"],
        "hotel": hotel["title"],
        "rating": rating,
        "offer": offer,
    })

chosen = []
used_codes = set()

# Budget choice: lowest offer price.
if candidates:
    budget_choice = min(
        candidates,
        key=lambda item: item["offer"]["displayPrice"],
    )
    chosen.append(("Budget choice", budget_choice))
    used_codes.add(budget_choice["code"])

# Recommended: first different hotel in the API's RANKING order.
recommended = next(
    (item for item in candidates if item["code"] not in used_codes),
    None,
)
if recommended:
    chosen.append(("RateLoc ranking choice", recommended))
    used_codes.add(recommended["code"])

# Premium: higher rating than the budget choice, lowest price at
# the highest eligible star rating.
if chosen:
    premium_candidates = [
        item for item in candidates
        if item["code"] not in used_codes
        and item["rating"] > budget_choice["rating"]
    ]

    if premium_candidates:
        premium = min(
            premium_candidates,
            key=lambda item: (
                -item["rating"],
                item["offer"]["displayPrice"],
            ),
        )
        chosen.append(("Premium choice", premium))

print("\nThree-option practice shortlist:")
for label, item in chosen:
    offer = item["offer"]
    print(
        f"{label}: {item['hotel']} | {item['rating']} stars | "
        f"{offer['roomName']} | {offer['boardBase']} | "
        f"{offer['displayPrice']:,.2f} {offer['currency']}"
    )