from typing import Any


def success(message: str = "Success", data: Any = None) -> dict:
    return {"success": True, "message": message, "data": data}


def error(message: str = "Error", errors: dict | None = None) -> dict:
    return {"success": False, "message": message, "errors": errors or {}}