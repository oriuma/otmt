import json
import requests
from src.config import (
    OTOMOTO_GRAPHQL_URL,
    PERSISTED_QUERY_HASH,
    MAX_PRICE_PLN,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Origin": "https://www.otomoto.pl",
    "Referer": "https://www.otomoto.pl/",
}


def build_variables(page: int = 1) -> dict:
    """Build GraphQL variables for Otomoto search."""
    return {
        "after": None,
        "click2BuyExperimentId": "",
        "click2BuyExperimentVariant": "",
        "experiments": [],
        "filters": [
            {"name": "filter_enum_damaged", "value": "0"},
            {"name": "filter_float_price:to", "value": str(MAX_PRICE_PLN)},
        ],
        "includeCepik": False,
        "includeFiltersCounters": False,
        "includeNewPromotedAds": False,
        "includePriceEvaluation": True,
        "includePromotedAds": False,
        "includeRatings": False,
        "includeSortOptions": False,
        "includeSuggestedFilters": False,
        "maxAge": 60,
        "page": page,
        "parameters": [
            "make", "model", "year", "mileage",
            "engine_capacity", "fuel_type", "power",
        ],
        "promotedInput": {},
        "searchTerms": None,
    }


def build_payload(page: int) -> dict:
    return {
        "operationName": "listingScreen",
        "variables": build_variables(page),
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": PERSISTED_QUERY_HASH,
            }
        },
    }


def fetch_page(page: int) -> list[dict]:
    """Fetch one page of Otomoto listings. Returns list of raw edge nodes."""
    payload = build_payload(page)
    try:
        resp = requests.post(
            OTOMOTO_GRAPHQL_URL,
            headers=HEADERS,
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        edges = (
            data
            .get("data", {})
            .get("advertSearch", {})
            .get("edges", [])
        )
        return edges
    except Exception as e:
        print(f"[Otomoto] fetch_page({page}) error: {e}")
        return []


def _param(params: list, key: str) -> str:
    """Extract a parameter value by key from the params list."""
    for p in params or []:
        if p.get("key") == key:
            vals = p.get("displayValue") or p.get("value")
            if isinstance(vals, list):
                return ", ".join(str(v) for v in vals)
            return str(vals) if vals else ""
    return ""


def normalize_offer(edge: dict) -> dict | None:
    """Convert a raw edge node into a clean offer dict."""
    node = edge.get("node", {})
    if not node:
        return None

    listing_id = node.get("id") or node.get("publicId")
    if not listing_id:
        return None

    params = node.get("parameters", [])
    price_info = node.get("price") or {}
    price_amount = price_info.get("amount", {}).get("units", "")
    price_currency = price_info.get("currency", {}).get("code", "PLN")

    price_str = f"{price_amount} {price_currency}" if price_amount else "brak ceny"

    images = node.get("images", {}).get("nodes", [])
    image_url = images[0].get("url", "") if images else ""

    slug = node.get("url") or ""
    offer_url = f"https://www.otomoto.pl/oferta/{slug}" if slug else ""

    location_data = node.get("location") or {}
    city = location_data.get("city", {}).get("name", "")
    region = location_data.get("region", {}).get("name", "")
    location_str = ", ".join(x for x in [city, region] if x) or "?"

    return {
        "id": str(listing_id),
        "title": node.get("title", ""),
        "price": price_str,
        "year": _param(params, "year"),
        "mileage": _param(params, "mileage"),
        "fuel": _param(params, "fuel_type"),
        "power": _param(params, "power"),
        "location": location_str,
        "url": offer_url,
        "image_url": image_url,
    }


def is_valid_offer(offer: dict) -> bool:
    """Basic validation — skip empty or broken offers."""
    return bool(offer.get("title") and offer.get("url"))
