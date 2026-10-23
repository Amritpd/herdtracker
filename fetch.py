"""Fetch raw posts from StrictlyVC + Finsmes WordPress APIs."""
import json, os, urllib.request

OUT = os.path.expanduser("~/workspace/herd-tracker/raw")
os.makedirs(OUT, exist_ok=True)
HDR = {"User-Agent": "Mozilla/5.0 (HerdTracker research)"}

def get(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def fetch(base, name, total, per=50):
    posts, page = [], 1
    while len(posts) < total:
        url = (f"{base}/wp-json/wp/v2/posts?per_page={per}&page={page}"
               f"&orderby=date&order=desc&_fields=date,title,link,content,categories")
        try:
            batch = get(url)
        except Exception as e:
            print(name, "page", page, "failed:", e)
            break
        if not batch:
            break
        posts.extend(batch)
        page += 1
    path = os.path.join(OUT, name + ".json")
    with open(path, "w") as f:
        json.dump(posts, f)
    print(name, "saved", len(posts), "posts ->", path)
    if posts:
        print("  newest:", posts[0]["date"], posts[0]["title"]["rendered"][:70])
        print("  oldest:", posts[-1]["date"], posts[-1]["title"]["rendered"][:70])

fetch("https://strictlyvc.com", "strictlyvc", 60)
fetch("https://www.finsmes.com", "finsmes", 200)
