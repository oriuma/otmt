import os

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# --- Scraper settings ---
MAX_PRICE_PLN = int(os.getenv("MAX_PRICE_PLN", "10000"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))
TELEGRAM_SLEEP_SECONDS = float(os.getenv("TELEGRAM_SLEEP_SECONDS", "0.7"))

# --- State ---
STATE_FILE = os.getenv("STATE_FILE", "data/sent_ids_otomoto.json")

# --- Otomoto GraphQL ---
OTOMOTO_GRAPHQL_URL = "https://www.otomoto.pl/graphql"
PERSISTED_QUERY_HASH = "249637cf7043dc3a315a8c7c4654da5ca30a6883a8bb3010b84be0bf3367e84f"
