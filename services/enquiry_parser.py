import os

from dotenv import load_dotenv
from groq import Groq

from models.enquiry import Enquiry


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def parse_enquiry(
    message: str,
    current_enquiry: Enquiry | None = None,
    last_question: str | None = None,
) -> Enquiry:
    current_state = (
        current_enquiry.model_dump_json()
        if current_enquiry
        else "{}"
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You update a hotel enquiry from a user's latest message. "
                    "Use the existing enquiry state as context. "
                    "Keep existing values unless the user changes them. "
                    "Only update values supported by the user's latest message. "
                    "Do not guess missing information. "
                    "Unknown values must remain null."
                    "Interpret short answers using the last assistant question. "
                    "For example, '1' after a room-count question means rooms=1. "
                    "If the user explicitly says only adults are travelling, children=0. "
                    "Never invent a year for a date. "
                    "If a new check-in date has no year and no year was explicitly "
                    "established in the conversation, leave check_in null so it can be clarified. "
                    "Do not convert a duration expressed in days into nights. "
                    "If the user provides only days and nights is unknown, keep nights null "
                    "so the assistant can ask how many nights. "
                    "A newly stated value replaces the existing value for that field, "
                    "even when the user does not say 'change' or 'actually'. "
                    "For example, if the current budget is 70000 and the latest message "
                    "is 'under 80000 INR', set budget to 80000 and currency to INR. "
                    "Preserve all unrelated enquiry fields. "
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Current enquiry:\n{current_state}\n\n"
                    f"Last assistant question:\n{last_question or 'None'}\n\n"
                    f"Latest message:\n{message}"
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "hotel_enquiry",
                "strict": False,
                "schema": Enquiry.model_json_schema(),
            },
        },
    )

    return Enquiry.model_validate_json(
        response.choices[0].message.content
    )