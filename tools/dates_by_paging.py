#!/usr/bin/env python3
"""日付の絞り込み（created_after など）が効かない Omeka S のサイト向け。
/api/items を全件ページ送りで取り、各資料の o:created と o:modified の月を数える。

出力は update_frequency.py と同じ形（site, month, created, modified, total_at_measure, measured_on）。
資料の本文は保存しない。月ごとの件数だけを書く。

使い方: python3 tools/dates_by_paging.py <name> <base> <out.tsv> [--per-page 100] [--sleep 1.0]
"""
import argparse
import csv
import datetime as dt
import json
import sys
import time
import urllib.request
from collections import Counter

UA = "omeka-update-frequency-research/1.0 (digital-archive-papers)"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return int(r.headers.get("Omeka-S-Total-Results") or 0), json.load(r)
        except Exception as e:  # noqa: BLE001
            print(f"  retry {attempt + 1}: {url}: {e}", file=sys.stderr)
            time.sleep(10 * (attempt + 1))
    raise SystemExit(f"failed: {url}")


def month(v):
    s = v.get("@value") if isinstance(v, dict) else v
    return s[:7] if s else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("base")
    ap.add_argument("out")
    ap.add_argument("--per-page", type=int, default=100)
    ap.add_argument("--sleep", type=float, default=1.0)
    a = ap.parse_args()
    base = a.base.rstrip("/")
    c, m = Counter(), Counter()
    page, seen, total = 1, 0, None
    while True:
        t, items = fetch(f"{base}/api/items?per_page={a.per_page}&page={page}&sort_by=id&sort_order=asc")
        total = total or t
        if not items:
            break
        for it in items:
            if (k := month(it.get("o:created"))):
                c[k] += 1
            if (k := month(it.get("o:modified"))):
                m[k] += 1
        seen += len(items)
        if page % 50 == 0:
            print(f"{a.name}: {seen}/{total}", file=sys.stderr)
        page += 1
        time.sleep(a.sleep)
    today = dt.date.today().isoformat()
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["site", "month", "created", "modified", "total_at_measure", "measured_on"])
        for k in sorted(set(c) | set(m)):
            w.writerow([a.name, k, c[k], m[k], total, today])
    print(f"{a.name}: seen {seen}, total {total}", file=sys.stderr)


if __name__ == "__main__":
    main()
