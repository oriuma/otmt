import os, json, time, requests
from pathlib import Path
from datetime import datetime, timezone

# ── конфиг ──────────────────────────────────────────────────
TELEGRAM_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT   = os.environ["TELEGRAM_CHAT_ID"]
STATE_FILE      = Path(os.environ.get("STATE_FILE", "data/seen_ids.json"))
MAX_PAGES       = int(os.environ.get("MAX_PAGES", "10"))

# ── 30 моделей для перепродажи ─────────────────────────────
ALLOWED_MODELS = [
    "seat ibiza",
    "opel astra",
    "fiat punto",
    "renault clio",
    "volkswagen polo", "vw polo",
    "skoda fabia", "škoda fabia",
    "ford fiesta",
    "opel corsa",
    "peugeot 206",
    "toyota yaris",
    "honda civic",
    "mazda 3",
    "citroen c3", "citroën c3",
    "hyundai getz",
    "suzuki splash",
    "daewoo matiz",
    "volkswagen golf", "vw golf",
    "audi a4",
    "bmw 3", "bmw e46",
    "mercedes c", "mercedes-benz c",
    "ford focus",
    "opel vectra",
    "toyota corolla",
    "skoda octavia", "škoda octavia",
    "citroen c4", "citroën c4",
    "mazda 5",
    "peugeot 307",
    "renault megane",
    "volkswagen passat", "vw passat",
    "audi a6",
]

# ── фильтры GraphQL: цена до 3000 PLN, пробег до 300 000 km ──────
SEARCH_FILTERS = [
    {"name": "category_id",                "value": "29"},
    {"name": "filter_float_price:to",      "value": "3000"},
    {"name": "filter_float_mileage:to",    "value": "300000"},
]

# ── заголовки ────────────────────────────────────────────────
HEADERS = {
    "accept":             "application/graphql-response+json, application/graphql+json, application/json",
    "accept-language":    "pl,ru;q=0.9,en;q=0.8",
    "cache-control":      "no-cache",
    "origin":             "https://www.otomoto.pl",
    "referer":            "https://www.otomoto.pl/osobowe",
    "sec-ch-ua":          '"Chromium";v="149", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile":   "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest":     "empty",
    "sec-fetch-mode":     "cors",
    "sec-fetch-site":     "same-origin",
    "sitecode":           "otomotopl",
    "user-agent":         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

LISTING_HASH = "5f9903c01d8e8b50a496ef5b10ce0ca397c85f795b158449db3492e6e8acb364"


def load_seen() -> set:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_seen(seen: set):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(list(seen)))


def is_wanted_model(title: str) -> bool:
    t = title.lower()
    return any(model in t for model in ALLOWED_MODELS)


def time_ago(created_at: str) -> str:
    if not created_at:
        return ""
    try:
        created_at = created_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(created_at)
        now = datetime.now(timezone.utc)
        diff = int((now - dt).total_seconds())

        if diff < 60:
            return f"{diff} сек назад"
        elif diff < 3600:
            m = diff // 60
            return f"{m} мин назад"
        elif diff < 86400:
            h = diff // 3600
            return f"{h} ч назад"
        elif diff < 86400 * 7:
            d = diff // 86400
            return f"{d} дней назад"
        else:
            return dt.strftime("%d.%m.%Y")
    except Exception:
        return ""


def fetch_page(page: int) -> list:
    variables = {
        "after": None,
        "experiments": [
            {"key": "CARS-85148", "variant": "a"},
            {"key": "CARS-81954", "variant": "a"},
            {"key": "CARS-82164", "variant": "a"},
            {"key": "CARS-85791", "variant": "a"},
            {"key": "CARS-87397", "variant": "a"},
            {"key": "CARS-88306", "variant": "c"},
            {"key": "CARS-64661", "variant": "b"},
        ],
        "filters": SEARCH_FILTERS,
        "includeCepik": True,
        "includeFiltersCounters": False,
        "includeNewPromotedAds": False,
        "includePremiumTopAd": False,
        "includePriceDrop": True,
        "includePriceEvaluation": True,
        "includePromotedAds": False,
        "includeSortOptions": False,
        "includeSuggestedFilters": True,
        "maxAge": 60,
        "page": page,
        "parameters": [
            "make", "offer_type", "show_pir", "fuel_type",
            "gearbox", "country_origin", "mileage", "engine_capacity",
            "engine_code", "engine_power", "first_registration_year",
            "model", "version", "year"
        ],
        "promotedInput": {},
        "searchTerms": [],
        "sortBy": "created_at:desc",
    }

    params = {
        "operationName": "listingScreen",
        "variables": json.dumps(variables, separators=(",", ":")),
        "extensions": json.dumps({
            "persistedQuery": {
                "sha256Hash": LISTING_HASH,
                "version": 1
            }
        }, separators=(",", ":")),
    }

    url = "https://www.otomoto.pl/graphql"
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        print(f"  fetch page {page} exception: {e}")
        return []

    if r.status_code != 200:
        print(f"  fetch page {page} error: {r.status_code} {r.text[:200]}")
        return []

    data = r.json()
    try:
        edges = data["data"]["advertSearch"]["edges"]
        return edges
    except (KeyError, TypeError):
        print(f"  page {page}: no edges in response")
        return []


def edge_to_post(edge: dict) -> dict | None:
    node = edge.get("node", {})
    if not node:
        return None

    ad_id      = node.get("id", "")
    title      = node.get("title", "Без названия")
    url        = node.get("url", "")
    price      = node.get("price", {})
    location   = node.get("location", {})
    params     = {p["key"]: p["displayValue"] for p in node.get("parameters", [])}
    created_at = node.get("createdAt") or node.get("created_at", "")

    if not is_wanted_model(title):
        return None

    price_val  = price.get("amount", {}).get("value", "?")
    price_curr = price.get("amount", {}).get("currency", "PLN")
    price_str  = f"{price_val} {price_curr}" if price_val != "?" else "Цена не указана"

    city    = location.get("city", {}).get("name", "")
    region  = location.get("region", {}).get("name", "")
    loc_str = ", ".join(filter(None, [city, region])) or "Польша"

    year    = params.get("year", "?")
    mileage = params.get("mileage", "?")
    fuel    = params.get("fuel_type", "")
    gearbox = params.get("gearbox", "")
    power   = params.get("engine_power", "")

    detail_parts = []
    if year    != "?": detail_parts.append(f"📅 {year}")
    if mileage != "?": detail_parts.append(f"🛣 {mileage} km")
    if fuel:           detail_parts.append(f"⛽ {fuel}")
    if gearbox:        detail_parts.append(f"⚙️ {gearbox}")
    if power:          detail_parts.append(f"🔧 {power}")

    ago = time_ago(created_at)
    ago_line = f"⏰ {ago}\n" if ago else ""

    return {
        "id": str(ad_id),
        "text": (
            f"🚗 *{title}*\n"
            f"💰 {price_str}\n"
            f"📍 {loc_str}\n"
            + ("\n".join(detail_parts) + "\n" if detail_parts else "")
            + ago_line
            + f"\n🔗 [Смотреть объявление]({url})"
        ),
    }


def send_telegram(text: str) -> bool:
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        },
        timeout=10,
    )
    if r.status_code != 200:
        print(f"  Telegram error: {r.status_code} {r.text[:200]}")
    return r.status_code == 200


def main():
    seen = load_seen()
    new_count = 0

    for page in range(1, MAX_PAGES + 1):
        print(f"Fetching page {page}...")
        edges = fetch_page(page)

        if not edges:
            print(f"  No edges on page {page}, stopping.")
            break

        for edge in edges:
            post = edge_to_post(edge)
            if not post:
                continue
            if post["id"] in seen:
                continue

            print(f"  NEW: {post['id']} – sending to Telegram...")
            ok = send_telegram(post["text"])
            if ok:
                seen.add(post["id"])
                new_count += 1
                time.sleep(0.5)

        time.sleep(1)

    save_seen(seen)
    print(f"\nDone. Sent {new_count} new ads.")


if __name__ == "__main__":
    main()
