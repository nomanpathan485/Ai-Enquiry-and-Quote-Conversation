from services.enquiry_parser import parse_enquiry
from services.enquiry_validator import get_missing_required_fields
from services.clarification import get_clarification_question
from services.hotel_search import search_mock_offers


def main():
    enquiry = None
    last_question = None
    displayed_offers = None
    selected_offer = None

    print("Describe your hotel enquiry. Type 'exit' to stop.")

    while True:
        message = input("\nYou: ").strip()

        if message.lower() == "exit":
            break

        if not message:
            continue
        if message.lower() == "quote":
            if selected_offer is None:
                print("Assistant: Select an offer first, using 'select 1'.")
                continue

            print("\n========== MOCK QUOTE PREVIEW ==========")

            print("\nRequested stay:")
            print(f"Destination: {enquiry.destination}")
            print(f"Check-in: {enquiry.check_in}")
            print(f"Nights: {enquiry.nights}")
            print(f"Adults: {enquiry.adults}")
            print(f"Children: {enquiry.children}")
            print(f"Child ages: {enquiry.child_ages}")
            print(f"Rooms requested: {enquiry.rooms}")
            print(f"Nationality: {enquiry.nationality}")

            print("\nSelected dataset offer:")
            print(f"Hotel: {selected_offer['title']}")
            print(f"Room: {selected_offer['roomName']}")
            print(f"Board basis: {selected_offer['boardBase']}")
            print(f"Payment terms: {selected_offer['paymentType']}")
            print(f"Refundable: {selected_offer['refundable']}")
            print(
                f"Snapshot price: "
                f"{selected_offer['displayPrice']:,.2f} "
                f"{selected_offer['currency']}"
            )

            print(
                "\nPractice preview only. This snapshot price has not "
                "been verified for the requested dates, guests or room count. "
                "It has not been multiplied by nights or rooms. "
                "Hotel occupancy and age policies have not been checked. "
                "No booking has been made."
            )
            print("========================================")
            continue

        # Selection commands are handled by Python, not the AI.
        if message.split()[0].lower() == "select":
            if displayed_offers is None or displayed_offers.empty:
                print("Assistant: Search for offers before selecting one.")
                continue

            parts = message.split()

            if len(parts) != 2 or not parts[1].isdigit():
                print("Assistant: Use a command such as 'select 1'.")
                continue

            number = int(parts[1])

            if not 1 <= number <= len(displayed_offers):
                print(
                    f"Assistant: Choose a number from "
                    f"1 to {len(displayed_offers)}."
                )
                continue

            selected_offer = displayed_offers.iloc[number - 1].to_dict()

            print("\nSelected offer — mock dataset:")
            for label, field in [
                ("Hotel", "title"),
                ("Room", "roomName"),
                ("Board basis", "boardBase"),
                ("Payment terms", "paymentType"),
                ("Refundable", "refundable"),
            ]:
                print(f"{label}: {selected_offer[field]}")

            print(
                f"Mock price: {selected_offer['displayPrice']:,.2f} "
                f"{selected_offer['currency']}"
            )
            print(
                "This selects one dataset offer. Availability and price "
                "for your requested dates, guests and room count "
                "have not been verified."
            )
            print("No quote or booking has been created.")
            continue

        # An enquiry update invalidates the previous results and selection.
        displayed_offers = None
        selected_offer = None

        enquiry = parse_enquiry(
            message,
            current_enquiry=enquiry,
            last_question=last_question,
        )

        print("\nCurrent enquiry:")
        print(enquiry.model_dump())

        missing_fields = get_missing_required_fields(enquiry)

        if missing_fields:
            last_question = get_clarification_question(missing_fields)
            print("\nAssistant:", last_question)
            continue

        last_question = None

        try:
            results = search_mock_offers(enquiry)
        except ValueError as error:
            last_question = str(error)
            print("\nAssistant:", last_question)
            continue

        print(
            "\nAssistant: Dubai-only mock dataset results. "
            "Filters apply when supplied: board basis, budget, "
            "currency and exact star rating."
        )
        print(
            "Area and availability for your dates and occupancy "
            "have not been checked."
        )

        if results.empty:
            print("No offers match those filters.")
        else:
            displayed_offers = results.head(5).reset_index(drop=True)

            preview = displayed_offers[
                ["title", "roomName", "boardBase", "displayPrice", "currency"]
            ].copy()
            preview.insert(0, "Option", range(1, len(preview) + 1))

            print(f"\nMatching offers: {len(results)}")
            print(preview.to_string(index=False))
            print("\nType 'select 1' to select option 1.")

        print("You can update your enquiry or type 'exit'.")


if __name__ == "__main__":
    main()