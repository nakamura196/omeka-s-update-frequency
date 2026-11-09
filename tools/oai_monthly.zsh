#!/usr/bin/env zsh
# OAI-PMH の ListIdentifiers に from=<月の初め> だけを付け、件数（completeListSize）の差で月ごとの更新数を出す。
# Omeka S の OaiPmhRepository では datestamp = 資料の最後の更新日（o:modified）。追加日は出ない。
# 注意: from と until を両方付けて月ごとに数える方法は使わない。あるサイト（OaiPmhRepository 3.4.7）で
#       2026-09 が 76 件と出た（from だけの差では 33,753 件）。until の扱いが当てにならない。
# 使い方: zsh tools/oai_monthly.zsh <name> <oai の URL> <開始 YYYY-MM> <出力.tsv>
set -euo pipefail
name=$1; oai=$2; start=$3; out=$4
UA='omeka-update-frequency-research/1.0 (digital-archive-papers)'
y=$((10#${start%-*})); m=$((10#${start#*-}))
ey=$(date +%Y); em=$((10#$(date +%m)))
(( em == 12 )) && { ey=$((ey+1)); em=1; } || em=$((em+1))   # 翌月の初めまで数える
count() {
  local x n
  x=$(curl -s -m 120 --retry 3 -A "$UA" "$oai?verb=ListIdentifiers&metadataPrefix=oai_dc&from=$1")
  n=$(print -r -- $x | grep -oE 'completeListSize="[0-9]+"' | grep -oE '[0-9]+' || true)
  if [[ -z $n ]]; then
    if print -r -- $x | grep -q noRecordsMatch; then n=0; else n=$(print -r -- $x | grep -c '<datestamp>' || true); fi
  fi
  sleep 1
  print $n
}
print -r -- $'site\tmonth\tmodified_oai\tmeasured_on' > $out
prev=$(count $(printf '%04d-%02d-01' $y $m)); pm=$(printf '%04d-%02d' $y $m)
while :; do
  (( m == 12 )) && { y=$((y+1)); m=1; } || m=$((m+1))
  ym=$(printf '%04d-%02d' $y $m)
  n=$(count $ym-01)
  print -r -- "$name	$pm	$((prev-n))	$(date +%F)" >> $out
  prev=$n; pm=$ym
  (( y > ey || (y == ey && m >= em) )) && break
done
