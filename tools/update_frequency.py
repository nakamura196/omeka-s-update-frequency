#!/usr/bin/env python3
"""Omeka S サイトの、月ごとの資料の追加数と更新数を、公開 API から数える。

全件は取り出さない。月の初めごとに
  /api/items?per_page=1&created_after=<YYYY-MM-01>
  /api/items?per_page=1&modified_after=<YYYY-MM-01>
を 1 回ずつ尋ね、応答ヘッダ Omeka-S-Total-Results（その日より後の件数）を取る。
隣の月との差が、その月の件数になる。

確かめたこと（2026-11-03、あるサイト）:
- created_before + created_after、modified_before + modified_after は、それぞれ足すと全体の件数に一致
- 2 つの条件を同時に付けると片方が無視される → 月ごとの差で出す
限界:
- modified は各資料の「最後の更新日」だけ。過去の更新の回数は数えられない（少なめに出る）
- 非公開の資料は数に入らない

使い方:
  python3 tools/update_frequency.py <sites.tsv> <out.tsv> [--from 2017-01] [--sleep 1.0]
sites.tsv: 1 行 1 サイト「名前<TAB>API の手前までの URL」（例: aa	https://example.org/omeka-s）
"""
import argparse
import csv
import datetime as dt
import sys
import time
import urllib.request

UA = "omeka-update-frequency-research/1.0 (digital-archive-papers)"


def total(base, query, sleep):
    url = f"{base}/api/items?per_page=1&{query}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                v = r.headers.get("Omeka-S-Total-Results")
                time.sleep(sleep)
                return int(v) if v is not None else None
        except Exception as e:  # noqa: BLE001
            print(f"  retry {attempt + 1}: {url}: {e}", file=sys.stderr)
            time.sleep(sleep * 5)
    return None


def months(start, end):
    y, m = start
    while (y, m) <= end:
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sites")
    ap.add_argument("out")
    ap.add_argument("--from", dest="start", default="2017-01")
    ap.add_argument("--sleep", type=float, default=1.0)
    a = ap.parse_args()

    sy, sm = map(int, a.start.split("-"))
    today = dt.date.today()
    end = (today.year, today.month)
    # 翌月の初め（= 今月分の差を取るための終端）
    ny, nm = (end[0] + 1, 1) if end[1] == 12 else (end[0], end[1] + 1)

    sites = [l.rstrip("\n").split("\t") for l in open(a.sites, encoding="utf-8") if l.strip() and not l.startswith("#")]
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["site", "month", "created", "modified", "total_at_measure", "measured_on"])
        for name, base in sites:
            base = base.rstrip("/")
            all_n = total(base, "", a.sleep)
            print(f"{name}: {all_n} items", file=sys.stderr)
            pts = list(months((sy, sm), end)) + [(ny, nm)]
            cum = {}
            for y, m in pts:
                d = f"{y:04d}-{m:02d}-01"
                cum[(y, m)] = (total(base, f"created_after={d}", a.sleep), total(base, f"modified_after={d}", a.sleep))
            for i in range(len(pts) - 1):
                c0, m0 = cum[pts[i]]
                c1, m1 = cum[pts[i + 1]]
                dc = c0 - c1 if None not in (c0, c1) else ""
                dm = m0 - m1 if None not in (m0, m1) else ""
                y, m = pts[i]
                w.writerow([name, f"{y:04d}-{m:02d}", dc, dm, all_n, today.isoformat()])
            # 開始月より前に追加された分（参考）
            c_first = cum[pts[0]][0]
            if all_n is not None and c_first is not None:
                w.writerow([name, f"before-{a.start}", all_n - c_first, "", all_n, today.isoformat()])
            f.flush()


if __name__ == "__main__":
    main()
