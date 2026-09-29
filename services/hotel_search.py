import json
from pathlib import Path

import pandas as pd

MOCK_DESTINATION = "Dubai"
def load_mock_tables():
    file_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "hotels_raw.json"
    )

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    hotel_columns = [
        "uniqueCode", "title", "address", "propertyType",
        "rating", "amenities", "latitude", "longitude", "image"
    ]

    offer_columns = [
        "uniqueCode", "bookingId", "roomName", "boardBase",
        "displayPrice", "currency", "paymentType", "refundable"
    ]

    hotels_df = pd.DataFrame(
        [
            {column: hotel.get(column) for column in hotel_columns}
            for hotel in data
        ],
        columns=hotel_columns,
    )

    offers_df = pd.DataFrame(
        [
            {column: offer.get(column) for column in offer_columns}
            for hotel in data
            for offer in hotel["offers"]
        ],
        columns=offer_columns,
    )

    return hotels_df, offers_df

def search_mock_offers(enquiry):
    if enquiry.destination is None:
        raise ValueError("Which destination would you like to search?")

    if enquiry.destination.strip().casefold() != MOCK_DESTINATION.casefold():
        raise ValueError(
            f"This practice dataset covers {MOCK_DESTINATION} only. "
            "Please enter Dubai to test this dataset."
        )
    hotels_df, offers_df = load_mock_tables()
    matches = offers_df.copy()

    board_names = {
        "ro": "room only",
        "bb": "bed and breakfast",
        "hb": "half board",
        "fb": "full board",
        "ai": "all inclusive",
    }

    if enquiry.board_basis is not None:
        board = enquiry.board_basis.strip().casefold()
        board = board_names.get(board, board)

        matches = matches.loc[
            matches["boardBase"].str.strip().str.casefold() == board
        ]

    if enquiry.currency is not None:
        currency = enquiry.currency.strip().upper()

        matches = matches.loc[
            matches["currency"].str.strip().str.upper() == currency
        ]

    if enquiry.budget is not None:
        if enquiry.currency is None:
            raise ValueError("Please specify the currency for your budget.")
        matches = matches.loc[
            matches["displayPrice"] <= enquiry.budget
        ]

    results = matches.merge(
        hotels_df[["uniqueCode", "title", "rating"]],
        on="uniqueCode",
        how="left",
        validate="many_to_one",
    )
    if enquiry.star_rating is not None:
            ratings = pd.to_numeric(results["rating"], errors="coerce")
            results = results.loc[ratings == enquiry.star_rating]

    return results.sort_values(
        ["currency", "displayPrice"],
        kind="stable",
    ).reset_index(drop=True)