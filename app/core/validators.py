import re


def _isbn10_check_digit(first_nine: str) -> str:
    total = sum(int(digit) * (10 - index) for index, digit in enumerate(first_nine))
    check = (11 - total % 11) % 11
    return "X" if check == 10 else str(check)


def _isbn13_check_digit(first_twelve: str) -> str:
    total = sum(
        int(digit) * (1 if index % 2 == 0 else 3)
        for index, digit in enumerate(first_twelve)
    )
    return str((10 - total % 10) % 10)


def normalize_isbn(value: str) -> str:
    cleaned = re.sub(r"[\s\-]", "", value.strip())
    if not re.fullmatch(r"\d{9}[\dXx]|\d{13}", cleaned):
        raise ValueError("ISBN must be a valid 10 or 13 digit code")
    cleaned = cleaned.upper()
    if len(cleaned) == 10:
        if cleaned[-1] != _isbn10_check_digit(cleaned[:9]):
            raise ValueError("ISBN-10 check digit is invalid")
    else:
        if cleaned[-1] != _isbn13_check_digit(cleaned[:12]):
            raise ValueError("ISBN-13 check digit is invalid")
    return cleaned