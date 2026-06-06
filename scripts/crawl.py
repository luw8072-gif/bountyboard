"""Crawl GitHub API for open bounties and save as JSON."""
import json, requests, time, os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

BOUNTIES_FILE = DATA_DIR / "bounties.json"
META_FILE = DATA_DIR / "meta.json"

all_bounties = []

# Search queries covering different bounty patterns
QUERIES = [
    'label:bounty is:issue is:open',
    'label:"good first issue" is:issue is:open bounty',
    'is:issue is:open "bounty" label:"help wanted"',
    'is:issue is:open "/bounty"',
]

for query in QUERIES:
    try:
        r = requests.get(
            "https://api.github.com/search/issues",
            params={"q": query, "sort": "created", "order": "desc", "per_page": 50},
            headers={"Accept": "application/vnd.github+json"},
            timeout=30
        )
        if r.status_code == 200:
            data = r.json()
            for item in data.get("items", []):
                bounty = {
                    "title": item["title"],
                    "url": item["html_url"],
                    "repo": item["repository_url"].split("/")[-2] + "/" + item["repository_url"].split("/")[-1],
                    "labels": [l["name"] for l in item.get("labels", [])],
                    "state": item["state"],
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                }
                # Extract bounty amount if present in title
                import re
                amount_match = re.search(r'\$(\d[\d,]*)', item["title"])
                if amount_match:
                    bounty["amount_usd"] = int(amount_match.group(1).replace(",", ""))
                all_bounties.append(bounty)
        time.sleep(2)  # Rate limit friendly
    except Exception as e:
        print(f"Error: {e}")

# Deduplicate by URL
seen = set()
unique = []
for b in all_bounties:
    if b["url"] not in seen:
        seen.add(b["url"])
        unique.append(b)

unique.sort(key=lambda x: x["created_at"], reverse=True)

with open(BOUNTIES_FILE, "w") as f:
    json.dump(unique, f, indent=2)

with open(META_FILE, "w") as f:
    json.dump({
        "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(unique),
    }, f)

print(f"Crawled {len(unique)} bounties")
