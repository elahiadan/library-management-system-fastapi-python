import re


def normalize_isbn(value: str) -> str:
    cleaned = re.sub(r"[\s\-]", "", value.strip())
    if not re.fullmatch(r"\d{9}[\dXx]|\d{13}", cleaned):
        raise ValueError("ISBN must be a valid 10 or 13 digit code")
    return cleaned.upper()