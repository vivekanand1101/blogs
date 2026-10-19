#!/usr/bin/env python3
"""Fetch every blog in blogs.json and render public/index.html.

Standard library only. Posts are remembered in data/posts.json so a post
keeps its "first seen" date and survives a feed that drops older entries.
"""
import email.utils
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "posts.json"
OUT = ROOT / "public"
UA = "Mozilla/5.0 (compatible; blogs.anandvivek.in feed reader)"
KEEP_PER_BLOG = 60
NOW = datetime.now(timezone.utc)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        d = None
    if d is None:
        for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
            try:
                d = datetime.strptime(s, fmt)
                break
            except ValueError:
                pass
    if d is None:
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).isoformat()


def text_of(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def summarize(s, n=220):
    s = strip_tags(s)
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def parse_feed(raw, base):
    root = ET.fromstring(raw)
    posts = []
    atom = "{http://www.w3.org/2005/Atom}"
    if root.tag == f"{atom}feed":
        for e in root.iter(f"{atom}entry"):
            link = ""
            for l in e.findall(f"{atom}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
                    break
            posts.append({
                "title": text_of(e.find(f"{atom}title")),
                "url": urljoin(base, link),
                "date": parse_date(text_of(e.find(f"{atom}published")) or text_of(e.find(f"{atom}updated"))),
                "summary": summarize(text_of(e.find(f"{atom}summary")) or text_of(e.find(f"{atom}content"))),
            })
    else:
        for it in root.iter("item"):
            posts.append({
                "title": text_of(it.find("title")),
                "url": urljoin(base, text_of(it.find("link"))),
                "date": parse_date(text_of(it.find("pubDate"))),
                "summary": summarize(text_of(it.find("description"))),
            })
    return posts


def parse_anthropic(raw, base):
    """anthropic.com has no RSS; read the post links off the listing page."""
    page = raw.decode("utf-8", "replace")
    section = re.escape(base.rstrip("/").rsplit("/", 1)[-1])
    posts = []
    for m in re.finditer(rf'<a[^>]+href="(/{section}/[^"#?]+)"[^>]*>(.*?)</a>', page, re.S):
        href, inner = m.groups()
        heading = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", inner, re.S)
        if heading:
            title = strip_tags(heading.group(1))
        else:
            spans = [strip_tags(s) for s in re.findall(r"<span[^>]*>(.*?)</span>", inner, re.S)]
            spans = [s for s in spans if s]
            title = max(spans, key=len) if spans else ""
        t = re.search(r'<time[^>]*?(?:dateTime="([^"]+)")?[^>]*>(.*?)</time>', inner, re.S)
        date = parse_date(t.group(1) or strip_tags(t.group(2))) if t else None
        para = re.search(r"<p[^>]*>(.*?)</p>", inner, re.S)
        if title:
            posts.append({
                "title": title,
                "url": urljoin(base, href),
                "date": date,
                "summary": summarize(para.group(1)) if para else "",
            })
    # The same post can be linked twice (a featured tile and a list row);
    # keep one, preferring the copy that carries a date.
    by_url = {}
    for p in posts:
        old = by_url.get(p["url"])
        if not old or (not old["date"] and p["date"]):
            by_url[p["url"]] = {**p, "summary": p["summary"] or (old or {}).get("summary", "")}
    return list(by_url.values())


def anthropic_date(url):
    """Featured posts on the listing page carry no date; read it off the article."""
    try:
        m = re.search(r'"datePublished":"([^"]+)"', fetch(url).decode("utf-8", "replace"))
        return parse_date(m.group(1)) if m else None
    except Exception:
        return None


def fetch_source(src):
    raw = fetch(src["url"])
    parser = parse_anthropic if src["type"] == "anthropic" else parse_feed
    return [p for p in parser(raw, src["url"]) if p["title"] and p["url"].startswith("http")]


def main():
    blogs = json.loads((ROOT / "blogs.json").read_text())
    store = json.loads(DATA.read_text()) if DATA.exists() else {}
    status = {}

    jobs = [(b, s) for b in blogs for s in b["sources"]]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda j: _safe(fetch_source, j[1]), jobs))

    now = NOW.isoformat()
    for (blog, src), (posts, err) in zip(jobs, results):
        st = status.setdefault(blog["id"], {"ok": True, "errors": []})
        if err:
            st["ok"] = False
            st["errors"].append(f"{src['url']}: {err}")
            print(f"[warn] {blog['id']} {src['url']}: {err}", file=sys.stderr)
            continue
        known = {p["url"]: p for p in store.get(blog["id"], [])}
        for p in posts:
            old = known.get(p["url"])
            p["seen"] = old["seen"] if old else now
            if not p["date"] and old:
                p["date"] = old["date"]
            if not p["date"] and src["type"] == "anthropic":
                p["date"] = anthropic_date(p["url"])
            p["date"] = p["date"] or p["seen"]
            known[p["url"]] = p
        store[blog["id"]] = list(known.values())
        print(f"[ok] {blog['id']} {src['url']}: {len(posts)} posts")

    for bid in store:
        store[bid].sort(key=lambda p: p["date"], reverse=True)
        store[bid] = store[bid][:KEEP_PER_BLOG]

    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(store, indent=1, ensure_ascii=False) + "\n")

    payload = {
        "updated": now,
        "blogs": [
            {"id": b["id"], "name": b["name"], "home": b["home"],
             "ok": status.get(b["id"], {}).get("ok", False),
             "posts": store.get(b["id"], [])}
            for b in blogs
        ],
    }
    OUT.mkdir(exist_ok=True)
    data_js = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    page = (ROOT / "template.html").read_text().replace("/*__DATA__*/null", data_js)
    (OUT / "index.html").write_text(page)
    (OUT / "CNAME").write_text("blogs.anandvivek.in\n")

    failed = [b for b, s in status.items() if not s["ok"]]
    if len(failed) == len(blogs):
        sys.exit("every source failed")


def _safe(fn, arg):
    try:
        return fn(arg), None
    except Exception as e:  # one broken feed shouldn't stop the build
        return [], f"{type(e).__name__}: {e}"


if __name__ == "__main__":
    main()
