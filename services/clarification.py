def get_clarification_question(missing_fields: list[str]) -> str | None:
    if not missing_fields:
        return None

    if "destination" in missing_fields:
        return "Which city or destination would you like to stay in?"

    if "nights" in missing_fields:
        return "How many nights would you like to stay?"

    if "check_in" in missing_fields:
        return (
            "Please provide a check-in date today or later, "
            "including the day, month and year."
        )
    if "adults" in missing_fields and "children" in missing_fields:
        return "How many adults and children are travelling?"

    if "adults" in missing_fields:
        return "How many adults are travelling?"

    if "children" in missing_fields:
        return "How many children are travelling? Say 'none' if there are no children."

    if "child_ages" in missing_fields:
        return "Please provide the age of each child."

    if "rooms" in missing_fields:
        return "How many rooms do you need?"

    if "nationality" in missing_fields:
        return "What is the guest nationality?"
    if "residency" in missing_fields:
        return "What is the guest's country of residence?"
    if "currency" in missing_fields:
        return "Which currency would you like prices shown in?"

    return "Could you provide the remaining hotel enquiry details?"