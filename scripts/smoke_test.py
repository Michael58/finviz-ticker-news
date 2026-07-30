"""Daily smoke test: trigger a minimal actor run on Apify, poll, assert output."""
import os, sys, time
import httpx

TOKEN = os.environ["APIFY_TOKEN"]
ACTOR_ID = os.environ["ACTOR_ID"]
BASE = "https://api.apify.com/v2"
H = {"Authorization": f"Bearer {TOKEN}"}
MIN_INPUT = {"tickers": "AAPL", "daysBack": 7}
REQUIRED_FIELDS = ["ticker", "title", "publishedAt"]

r = httpx.post(f"{BASE}/acts/{ACTOR_ID}/runs", json=MIN_INPUT, headers=H, timeout=30)
r.raise_for_status()
run_id = r.json()["data"]["id"]
print(f"Run: {run_id}")

status = "RUNNING"
for _ in range(36):
    time.sleep(10)
    data = httpx.get(f"{BASE}/actor-runs/{run_id}", headers=H, timeout=30).json()["data"]
    status = data["status"]
    print(f"  {status}")
    if status not in {"RUNNING", "READY"}:
        break

if status != "SUCCEEDED":
    print(f"FAILED: {status}")
    sys.exit(1)

ds_id = data["defaultDatasetId"]
items = httpx.get(f"{BASE}/datasets/{ds_id}/items", headers=H, timeout=30).json()
assert len(items) > 0, "Empty dataset — no news articles returned for AAPL"
for field in REQUIRED_FIELDS:
    assert items[0].get(field) is not None, f"Missing: {field}"
print(f"OK — {len(items)} articles")
