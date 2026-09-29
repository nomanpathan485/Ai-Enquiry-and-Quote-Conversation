from models.enquiry import Enquiry


def build_three_options(hotels: list[dict], enquiry: Enquiry) -> list[tuple[str, dict, dict]]:
    candidates = []

    for position, hotel in enumerate(hotels):
        try:
            rating = int(hotel["rating"])
        except (KeyError, TypeError, ValueError):
            continue

        if enquiry.star_rating is not None and rating != enquiry.star_rating:
            continue

        offers = []

        for offer in hotel.get("offers") or []:
            price = offer.get("displayPrice")
            currency = offer.get("currency")

            if (
                not isinstance(price, (int, float))
                or isinstance(price, bool)
                or price <= 0
                or currency != enquiry.currency.upper()
            ):
                continue

            if (
                enquiry.board_basis is not None
                and offer.get("boardBase", "").strip().casefold()
                != enquiry.board_basis.strip().casefold()
            ):
                continue

            if enquiry.budget is not None and price > enquiry.budget:
                continue

            offers.append(offer)

        if offers:
            candidates.append({
                "position": position,
                "hotel": hotel,
                "rating": rating,
                "offer": min(offers, key=lambda item: item["displayPrice"]),
            })

    if not candidates:
        return []

    chosen = []
    used_codes = set()

    budget = min(
        candidates,
        key=lambda item: item["offer"]["displayPrice"],
    )
    chosen.append(("Budget choice", budget))
    used_codes.add(budget["hotel"]["uniqueCode"])

    recommended = next(
        (
            item for item in candidates
            if item["hotel"]["uniqueCode"] not in used_codes
        ),
        None,
    )
    if recommended:
        chosen.append(("RateLoc ranking choice", recommended))
        used_codes.add(recommended["hotel"]["uniqueCode"])

    premium_candidates = [
        item for item in candidates
        if item["hotel"]["uniqueCode"] not in used_codes
        and item["rating"] > budget["rating"]
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

    return [
        (label, item["hotel"], item["offer"])
        for label, item in chosen
    ]