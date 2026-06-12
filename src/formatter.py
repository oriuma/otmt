def build_caption(offer: dict) -> str:
    """
    Build an HTML-formatted Telegram caption for one car offer.

    Expected offer keys:
        title, price, year, mileage, fuel, power, location, url, image_url
    """
    title    = offer.get("title", "Brak tytułu")
    price    = offer.get("price", "brak ceny")
    year     = offer.get("year", "?")
    mileage  = offer.get("mileage", "?")
    fuel     = offer.get("fuel", "?")
    power    = offer.get("power", "?")
    location = offer.get("location", "?")
    url      = offer.get("url", "")

    lines = [
        f"🚗 <b>{title}</b>",
        f"💰 <b>{price}</b>",
        f"📅 {year}   🛣 {mileage}   ⛽️ {fuel}   ⚡️ {power}",
        f"📍 {location}",
    ]
    if url:
        lines.append(f'🔗 <a href="{url}">Otomoto</a>')

    return "\n".join(lines)
