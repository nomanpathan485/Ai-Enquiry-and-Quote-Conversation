from services.hotel_search import load_mock_tables

hotels_df, offers_df = load_mock_tables()

print("\nHotels table shape:")
print(hotels_df.shape)

print("\nFirst 5 hotels:")
print(
    hotels_df[["uniqueCode", "title", "rating"]]
    .head()
    .to_string(index=False)
)

print("\nOffers table shape:")
print(offers_df.shape)

print("\nFirst 5 offers — mock dataset prices:")
print(
    offers_df[
        ["uniqueCode", "roomName", "boardBase",
         "displayPrice", "currency", "refundable"]
    ]
    .head()
    .to_string(index=False)
)

# Fixed practice criteria, not values extracted from an enquiry.
matches = offers_df.loc[
    (offers_df["boardBase"] == "All Inclusive")
    & (offers_df["currency"] == "INR")
    & (offers_df["displayPrice"] <= 500000)
]

results = (
    matches.merge(
        hotels_df[["uniqueCode", "title"]],
        on="uniqueCode",
        how="left",
        validate="many_to_one"
    )
    .sort_values("displayPrice")
)

print("\nMatching offers:", len(results))
print("\nLowest-priced 5 matching offers — mock prices:")
print(
    results[
        ["title", "roomName", "boardBase", "displayPrice", "currency"]
    ].head(5).to_string(index=False)
)