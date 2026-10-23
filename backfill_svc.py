"""Full StrictlyVC archive pull -> local raw backup. Raw-first: keep payloads,
extraction can always be re-run. Resumable: skips pages already on disk."""
import json, os, time, gzip, urllib.request, urllib.error

BASE = os.path.expanduser("~/workspace/herd-tracker/raw/svc_full")
os.makedirs(BASE, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) HerdTrackerResearch/0.1"}
API = "https://strictlyvc.com/wp-json/wp/v2/posts?per_page=100&_fields=id,date,link,title,content,categories&page={}"

total_posts, page = 0, 1
while page <= 200:
    dest = f"{BASE}/page-{page:03d}.json.gz"
    if os.path.exists(dest):
        with gzip.open(dest, "rt") as f: total_posts += len(json.load(f))
        page += 1; continue
    url = API.format(page)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                posts = json.load(r)
            break
        except Exception as e:
            print(f"page {page} attempt {attempt+1} failed: {e}", flush=True)
            posts = None; time.sleep(3)
    if not posts:
        print(f"stopping at page {page} (empty or failed)", flush=True)
        break
    with gzip.open(dest, "wt") as f: json.dump(posts, f)
    total_posts += len(posts)
    if page % 10 == 0 or page == 1:
        print(f"page {page}: cumulative {total_posts} posts", flush=True)
    if len(posts) < 100:
        print(f"last page {page} ({len(posts)} posts)", flush=True)
        break
    page += 1
    time.sleep(0.3)

print("TOTAL POSTS:", total_posts)
