#!/usr/bin/env python3
"""cc_find_omeka_jp.zsh の候補（ホストごと）を、公開 API に 1 回ずつ尋ねて Omeka かどうか確かめる。

- omeka-s: 例の URL の /s/ の手前を基点にし、<基点>/api/items?per_page=1 の
  応答ヘッダ Omeka-S-Total-Results を見る
- omeka-classic: /items/show/ の手前を基点にし、<基点>/api/items?per_page=1 の
  応答ヘッダ Omeka-Total-Results を見る（Classic は API が既定で無効なので、
  返らなくても Omeka でないとは言えない。その場合は HTML の generator を見る）

出力: kind, host, cc_urls, base, verdict（api / generator / no）, total, example
使い方: python3 tools/verify_candidates.py <candidates.tsv> <out.tsv> [--sleep 1.0]
"""
import argparse
import csv
import html as htmllib
import re
import sys
import time
import urllib.request

UA = "omeka-site-survey-research/1.0 (digital-archive-papers)"


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.headers, r.read(200_000).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates")
    ap.add_argument("out")
    ap.add_argument("--sleep", type=float, default=1.0)
    a = ap.parse_args()
    with open(a.candidates, encoding="utf-8") as f, open(a.out, "w", newline="", encoding="utf-8") as o:
        w = csv.writer(o, delimiter="\t")
        w.writerow(["kind", "host", "cc_urls", "base", "verdict", "total", "example"])
        for kind, host, n, ex in csv.reader(f, delimiter="\t"):
            pat = r"/s/[^/]+/" if kind == "omeka-s" else r"/items/show/"
            base = re.split(pat, ex, maxsplit=1)[0].rstrip("/")
            hdr, body = get(f"{base}/api/items?per_page=1")
            key = "Omeka-S-Total-Results" if kind == "omeka-s" else "Omeka-Total-Results"
            verdict, tot = "no", ""
            if hdr is not None and hdr.get(key) is not None:
                verdict, tot = "api", hdr.get(key)
            else:
                time.sleep(a.sleep)
                hdr2, html = get(ex)
                # Omeka S は属性の中の / を &#x2F; と書くので、戻してから探す
                html = htmllib.unescape(html)
                if hdr2 is not None and re.search(r'name="generator"[^>]*Omeka|Omeka[^"]*"\s+name="generator"|/application/asset/|/themes/[^/]+/asset/', html):
                    verdict = "generator"
            w.writerow([kind, host, n, base, verdict, tot, ex])
            o.flush()
            print(f"{verdict}\t{host}\t{tot}", file=sys.stderr)
            time.sleep(a.sleep)


if __name__ == "__main__":
    main()
