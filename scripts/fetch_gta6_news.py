#!/usr/bin/env python3
"""Pulls the latest GTA 6 headlines from free RSS feeds into gta6/news.json."""
import json, re, urllib.request, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import timezone

FEEDS = [
    ("Google News", "https://news.google.com/rss/search?q=%22GTA+6%22+OR+%22Grand+Theft+Auto+VI%22+when:7d&hl=en-US&gl=US&ceid=US:en"),
    ("Rockstar Newswire", "https://www.rockstargames.com/newswire/rss"),
    ("r/GTA6", "https://www.reddit.com/r/GTA6/top/.rss?t=day"),
]
UA = {"User-Agent": "Mozilla/5.0 (gta6-countdown dashboard)"}
KEYWORDS = re.compile(r"gta ?(6|vi)|grand theft auto|rockstar|vice city|lucia|jason", re.I)

def text(el, *tags):
    for t in tags:
        x = el.find(t)
        if x is not None:
            return (x.text or x.get("href") or "").strip()
    return ""

items, seen = [], set()
for source, url in FEEDS:
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()
        root = ET.fromstring(raw)
    except Exception as e:
        print("skip", source, e); continue
    A = "{http://www.w3.org/2005/Atom}"
    for it in root.iter("item"):
        title, link, date = text(it, "title"), text(it, "link"), text(it, "pubDate")
        src = text(it, "source") or source
        items.append((title, link, date, src, source))
    for it in root.iter(A + "entry"):
        l = it.find(A + "link")
        items.append((text(it, A + "title"), l.get("href") if l is not None else "", text(it, A + "updated"), source, source))

out = []
for title, link, date, src, feed in items:
    key = re.sub(r"\W+", "", title.lower())[:60]
    if not title or key in seen or not KEYWORDS.search(title):
        continue
    seen.add(key)
    try:
        d = parsedate_to_datetime(date)
    except Exception:
        from datetime import datetime
        try: d = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except Exception: continue
    title = re.sub(r"\s+-\s+[^-]+$", "", title) if feed == "Google News" else title
    out.append({"title": title, "url": link, "date": d.astimezone(timezone.utc).isoformat(), "source": src, "feed": feed})

out.sort(key=lambda x: x["date"], reverse=True)
from datetime import datetime
json.dump({"updated": datetime.now(timezone.utc).isoformat(), "items": out[:60]}, open("gta6/news.json", "w"), indent=1)
print(len(out), "items")
