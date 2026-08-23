from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP


def format_decimal_it(value: Decimal | int | float | None, decimals: int = 2) -> str:
    if value is None:
        return "n.d."
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    quantum = Decimal("1").scaleb(-decimals)
    rounded = decimal_value.quantize(quantum, rounding=ROUND_HALF_UP)
    integer, fraction = f"{rounded:.{decimals}f}".split(".")
    sign = "-" if integer.startswith("-") else ""
    integer = integer.lstrip("-")
    grouped = f"{int(integer):,}".replace(",", ".") if integer else "0"
    return f"{sign}{grouped},{fraction}"


def format_currency_it(value: Decimal | int | float | None) -> str:
    return "n.d." if value is None else f"{format_decimal_it(value, 2)} €"


def format_percent(value: Decimal | float | int | None, decimals: int = 1) -> str:
    if value is None:
        return "n.d."
    return f"{format_decimal_it(Decimal(str(value)), decimals)}%"


def format_date_it(value: date | datetime | None) -> str:
    if value is None:
        return "n.d."
    return value.strftime("%d/%m/%Y")


def format_datetime_it(value: datetime | None) -> str:
    if value is None:
        return "n.d."
    return value.strftime("%d/%m/%Y %H:%M")
