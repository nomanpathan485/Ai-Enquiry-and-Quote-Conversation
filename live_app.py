import requests
from services.enquiry_parser import parse_enquiry
from services.enquiry_validator import get_missing_required_fields
from services.clarification import get_clarification_question
from services.live_search import lookup_destinations, search_live_pages
from services.live_quote import build_three_options
from services.conversation import write_clarification



def show_quote(enquiry, options, hotel_count, total_pages):
    print("\n========== PROVISIONAL HOTEL SHORTLIST ==========")
    print(
        f"{enquiry.destination} | {enquiry.check_in} | "
        f"{enquiry.nights} nights | {enquiry.rooms} room"
    )
    print(
        f"Guests: {enquiry.adults} adults, {enquiry.children} children "
        f"| Nationality: {enquiry.nationality} "
        f"| Residence: {enquiry.residency}"
    )
    print(
        f"Hotels examined: {hotel_count} on page 1 "
        f"of {total_pages}"
    )
    print(
        "Budget choice is the lowest eligible price among hotels"
        "received so far. More RateLoc results may change these choices"
    )
    for number, (label, hotel, offer) in enumerate(options, start=1):
        print(f"\n{number}. {label}")
        print(f"   Hotel: {hotel['title']} ({hotel['rating']} stars)")
        print(f"   Room: {offer.get('roomName')}")
        print(f"   Board: {offer.get('boardBase')}")
        print(f"   Payment: {offer.get('paymentType')}")
        print(f"   Refundable: {offer.get('refundable')}")
        print(
            f"   Search price: {offer['displayPrice']:,.2f} "
            f"{offer['currency']}"
        )

    print(
        "\nSearch result preview. Recheck the selected offers and prices "
        "before sending a customer quote. No booking has been made."
    )
    print("===================================================")


def main():
    enquiry = None
    last_question = None
    pending_locations = None
    quote_data = None

    print("Describe your hotel enquiry. Type 'exit' to stop.")

    while True:
        message = input("\nYou: ").strip()

        if message.lower() == "exit":
            break
        if not message:
            continue

        if message.lower() == "quote":
            if quote_data is None:
                print("Assistant: Complete a live search first.")
            else:
                options, hotel_count, total_pages = quote_data
                show_quote(enquiry, options, hotel_count, total_pages)
            continue

        if pending_locations is not None:
            if not message.isdigit():
                print("Assistant: Enter a destination option number.")
                continue

            number = int(message)
            if not 1 <= number <= len(pending_locations):
                print("Assistant: Choose a number from the list.")
                continue

            location = pending_locations[number - 1]["Location"]
            pending_locations = None

            try:
                # Up to 100 pages; refuse to describe an incomplete
                # collection as the cheapest across the search.
                print("Assistant: Searching RateLoc's first Recommended page...")
                hotels, total_pages = search_live_pages(
                    enquiry, location, max_pages=1
)

                options = build_three_options(hotels, enquiry)
            except requests.exceptions.RequestException:
                quote_data = None
                print(
                    "Assistant: RateLoc did not return results promptly. "
                    "No live quote is available for this search."
                )
                continue
            except Exception as error:
                quote_data = None
                print("Assistant: Live search failed:", error)
                continue

            if not options:
                print("Assistant: No offers match those filters.")
                continue
            quote_data = (options, len(hotels), total_pages)
            show_quote(enquiry, *quote_data)
            print("\nType 'quote' to view it again, or update your enquiry.")
            continue
        if message.isdecimal() and enquiry is not None:
            missing_now = get_missing_required_fields(enquiry)

            if "nights" in missing_now:
                message = f"{message} nights"
            elif "check_in" in missing_now:
                print("Assistant: Please give the full check-in date.")
                continue
            elif "adults" in missing_now:
                message = f"{message} adults"
            elif "children" in missing_now:
                message = f"{message} children"
            elif "child_ages" in missing_now and enquiry.children == 1:
                message = f"The child is {message} years old"
            elif "rooms" in missing_now:
                message = f"{message} rooms"
            else:
                print(
                    "Assistant: Please describe what you'd like to change."
                )
                continue

        # Any change to the enquiry invalidates the previous quote.
        quote_data = None

        try:
            enquiry = parse_enquiry(
                message,
                current_enquiry=enquiry,
                last_question=last_question,
            )
        except Exception as error:
            print("Assistant: Could not interpret that message:", error)
            continue


        missing = get_missing_required_fields(enquiry)
        if missing:
            fallback_question = get_clarification_question(missing)
            last_question = write_clarification(
                message, enquiry, missing, fallback_question
            )
            print("\nAssistant:", last_question)
            continue

        last_question = None

        if enquiry.rooms != 1:
            print(
                "Assistant: Live search currently supports one room. "
                "For multiple rooms, we need the guest allocation "
                "for each room."
            )
            continue

        if enquiry.area is not None:
            print(
                "Assistant: Area filtering is not connected to "
                "the live search yet."
            )
            continue

        try:
            locations = lookup_destinations(enquiry.destination)
            locations = [
                item for item in locations
                if isinstance(item, dict)
                and isinstance(item.get("Location"), str)
                and item["Location"].strip()
                and isinstance(item.get("CityStateCountry"), str)
                and item["CityStateCountry"].strip()
            ]
        except Exception as error:
            print("Assistant: Destination lookup failed:", error)
            continue

        if not locations:
            print("Assistant: No RateLoc destination was found.")
            continue

        pending_locations = locations[:10]
        print("\nAssistant: Select the intended destination:")
        for number, item in enumerate(pending_locations, start=1):
            print(f"{number}. {item['CityStateCountry']}")


if __name__ == "__main__":
    main()