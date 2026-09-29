from services.enquiry_parser import client


def write_clarification(message, enquiry, missing, fallback_question):
    if "check_in" in missing:
        return fallback_question
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful hotel travel assistant. "
                        "Reply naturally in one or two short sentences. "
                        "Briefly acknowledge the user's latest message, then ask "
                        "one clear question for the next missing detail. "
                        "The required question is provided below; preserve its meaning. "
                        "Use only facts in the enquiry state. Do not guess missing "
                        "details, claim availability, or mention software, models, "
                        "fields, JSON, or validation."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Latest message: {message}\n"
                        f"Known enquiry: {enquiry.model_dump_json()}\n"
                        f"Missing details: {', '.join(missing)}\n"
                        f"Question to ask: {fallback_question}"
                    ),
                },
            ],
        )
        reply = response.choices[0].message.content
        return reply.strip() if reply and reply.strip() else fallback_question
    except Exception:
        return fallback_question