#!/usr/bin/env zsh
# Common Crawl の URL 索引（cdx）から、.jp のドメインで Omeka らしい URL を持つホストを拾う。
#
# 前提: curl, gzip, awk。索引の窓口（index.commoncrawl.org）は混んでいて時間切れになるので使わない。
#       data.commoncrawl.org の cluster.idx で .jp（SURT で "jp,"）の範囲を引き、
#       各 cdx ファイルのその範囲だけを Range 指定で流し読みする。保存はしない。
# 使い方: zsh tools/cc_find_omeka_jp.zsh <CC-MAIN-YYYY-WW> <cluster.idx> <出力.tsv>
# 出力: kind<TAB>host<TAB>URL数<TAB>例のURL（kind = omeka-s / omeka-classic）
# 限界: .jp 以外のドメイン（.com や .org）にある国内のサイトは拾えない。
#       Common Crawl が巡回していないサイトも拾えない。URL の形だけなので、別の CMS が混ざりうる
#       （次の段で API の応答を見て確かめる）。
set -euo pipefail

C=$1; IDX=$2; OUT=$3
BASE=https://data.commoncrawl.org/cc-index/collections/$C/indexes

# cdx ファイルごとに、.jp の範囲の先頭の位置と末尾の位置を出す
ranges=$(awk -F'\t' '$1 ~ /^jp[,)]/ { f=$2; s=$3; e=$3+$4-1; if (!(f in lo) || s<lo[f]) lo[f]=s; if (!(f in hi) || e>hi[f]) hi[f]=e } END { for (f in lo) print f, lo[f], hi[f] }' "$IDX" | sort)

tmp=$(mktemp)
print -r -- "$ranges" | while read -r f lo hi; do
  print -u2 "reading $f bytes $lo-$hi"
  curl -s --retry 5 --retry-delay 10 -r "$lo-$hi" "$BASE/$f" \
    | gzip -dc 2>/dev/null \
    | awk '{ u=$0; sub(/^[^{]*\{"url": "/, "", u); sub(/".*/, "", u);
             if (u ~ /\/s\/[^\/]+\/(item|item-set|media)\/[0-9]+/) k="omeka-s";
             else if (u ~ /\/items\/show\/[0-9]+/) k="omeka-classic"; else next;
             h=u; sub(/^https?:\/\//, "", h); sub(/\/.*/, "", h);
             print k "\t" h "\t" u }' >> "$tmp" || true
done

awk -F'\t' '{ key=$1 "\t" $2; n[key]++; if (!(key in ex)) ex[key]=$3 } END { for (k in n) print k "\t" n[k] "\t" ex[k] }' "$tmp" | sort -t$'\t' -k3,3nr > "$OUT"
rm -f "$tmp"
print -u2 "hosts: $(wc -l < "$OUT")"
