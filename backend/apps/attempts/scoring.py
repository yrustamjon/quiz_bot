"""Percentage display is positive decimal HALF_UP to two places everywhere."""

from decimal import ROUND_HALF_UP, Decimal


def percent_display(value):
    return format(
        Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f"
    )
