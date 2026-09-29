from datetime import date

from pydantic import BaseModel, field_validator


class Enquiry(BaseModel):
    destination: str | None = None
    check_in: date | None = None
    nights: int | None = None

    adults: int | None = None
    children: int | None = None
    child_ages: list[int] | None = None
    rooms: int | None = None
    nationality: str | None = None
    residency: str | None = None

    area: str | None = None
    star_rating: int | None = None
    board_basis: str | None = None
    budget: float | None = None
    currency: str | None = None
    @field_validator("*", mode="before")
    @classmethod
    def normalize_null_string(cls, value):
        if isinstance(value, str) and value.strip().lower() == "null":
            return None
        return value