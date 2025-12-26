def format_uah(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)

    whole = cents // 100
    frac = cents % 100

    whole_str = f"{whole:,}".replace(",", " ")
    return f"{sign}{whole_str}.{frac:02d} грн"

