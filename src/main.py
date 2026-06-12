import os
from src.config import MAX_PAGES, STATE_FILE
from src.state import load_sent_ids, save_sent_ids, push_state_to_github
from src.otomoto_client import fetch_page, normalize_offer, is_valid_offer
from src.telegram_client import send_offer

GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "oriuma/otmt")
REMOTE_STATE_PATH = "data/sent_ids_otomoto.json"


def main():
    print(f"[main] Loading state from {STATE_FILE}")
    sent_ids = load_sent_ids(STATE_FILE)
    print(f"[main] Already sent: {len(sent_ids)} offers")

    new_count = 0
    total_seen = 0

    for page in range(1, MAX_PAGES + 1):
        print(f"[main] Fetching page {page}/{MAX_PAGES}")
        edges = fetch_page(page)

        if not edges:
            print(f"[main] No edges on page {page}, stopping.")
            break

        for edge in edges:
            offer = normalize_offer(edge)
            if not offer:
                continue
            total_seen += 1

            if offer["id"] in sent_ids:
                continue

            if not is_valid_offer(offer):
                continue

            print(f"[main] New offer: {offer['title']} | {offer['price']} | {offer['location']}")
            success = send_offer(offer)

            if success:
                sent_ids.add(offer["id"])
                new_count += 1
            else:
                print(f"[main] Failed to send offer {offer['id']}")

    save_sent_ids(STATE_FILE, sent_ids)
    push_state_to_github(STATE_FILE, GITHUB_REPO, REMOTE_STATE_PATH)
    print(f"[main] Done. Seen: {total_seen}, sent new: {new_count}, state saved.")


if __name__ == "__main__":
    main()
