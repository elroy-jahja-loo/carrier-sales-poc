from datetime import datetime
from decimal import Decimal


def format_currency_whole(value: Decimal) -> str:
    whole = int(value.quantize(Decimal("1")))
    return f"${whole:,}"


def safe_human_time(value: datetime) -> str:
    try:
        return value.strftime("%B %d at %-I %p")
    except ValueError:
        return value.strftime("%B %d at %I %p").replace(" 0", " ")
