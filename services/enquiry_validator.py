from models.enquiry import Enquiry
from datetime import date


def get_missing_required_fields(enquiry: Enquiry) -> list[str]:
    required_fields = [
        "destination",
        "check_in",
        "nights",
        "adults",
        "children",
        "rooms",
        "nationality",
        "residency",
        "currency"
    ]

    missing_fields = []

    for field in required_fields:
        if getattr(enquiry, field) is None:
            missing_fields.append(field)

        if enquiry.children is not None and enquiry.children > 0:
            if (
                enquiry.child_ages is None
                or len(enquiry.child_ages) != enquiry.children
            ):
                missing_fields.append("child_ages")
        if enquiry.adults is not None and enquiry.children is not None:
            if enquiry.adults + enquiry.children <= 0:
                for field in ["adults", "children"]:
                    if field not in missing_fields:
                        missing_fields.append(field)
        if enquiry.check_in is not None and enquiry.check_in < date.today():
            if "check_in" not in missing_fields:
                missing_fields.append("check_in")
    return missing_fields