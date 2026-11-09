#!/usr/bin/env python3
"""update_frequency.py の出力（月ごとの追加数・更新数）を、サイトごとに要約する。

出す列:
  site, total, first_month（最初に追加があった月。開始月より前の分は除く）,
  months_span（最初の追加の月から計測月まで）,
  add_months / mod_months（追加・更新が 1 件でもあった月の数）,
  mod_last（最後に更新があった月）, idle_months（最後の更新から計測月までの月数）,
  top_mod（更新が最も多い月と、全更新に占める割合）,
  march_share（3 月の更新が全更新に占める割合）

使い方: python3 tools/summarize_frequency.py <monthly.tsv>
"""
import csv
import sys
from collections import defaultdict


def mdiff(a, b):
    ya, ma = map(int, a.split("-"))
    yb, mb = map(int, b.split("-"))
    return (yb - ya) * 12 + (mb - ma)


rows = defaultdict(list)
total = {}
measured = {}
with open(sys.argv[1], encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["month"].startswith("before-"):
            continue
        rows[r["site"]].append(r)
        total[r["site"]] = r["total_at_measure"]
        measured[r["site"]] = r["measured_on"][:7]

w = csv.writer(sys.stdout, delimiter="\t")
w.writerow(["site", "total", "first_add", "add_months", "mod_months", "span_months",
            "mod_last", "idle_months", "top_mod", "top_share", "march_share"])
for site, rs in rows.items():
    blank = [r["month"] for r in rs if r["created"] == "" or r["modified"] == ""]
    if blank:
        # 取得に失敗した月（空欄）を 0 として数えると、追加の月を取りこぼす（2026-11-03、あるサイトで 14,760 件）
        print(f"warning: {site}: {len(blank)} months blank ({blank[0]}..{blank[-1]}); re-measure them", file=sys.stderr)
    c = {r["month"]: int(r["created"] or 0) for r in rs}
    m = {r["month"]: int(r["modified"] or 0) for r in rs}
    added = [k for k, v in c.items() if v > 0]
    mods = [k for k, v in m.items() if v > 0]
    first = min(added) if added else ""
    now = measured[site]
    span = mdiff(first, now) + 1 if first else ""
    mod_sum = sum(m.values())
    top = max(m, key=m.get) if mod_sum else ""
    mar = sum(v for k, v in m.items() if k.endswith("-03"))
    w.writerow([site, total[site], first, len(added), len(mods), span,
                max(mods) if mods else "", mdiff(max(mods), now) if mods else "",
                top, f"{m[top] / mod_sum:.0%}" if mod_sum else "",
                f"{mar / mod_sum:.0%}" if mod_sum else ""])
