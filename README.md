# Omeka S のサイトの更新の頻度を、公開 API から測る道具とデータ

中村 覚（東京大学）の論文（投稿準備中）の 3 章の測定に使った道具と、その結果です。

## 中身

- `tools/update_frequency.py` — 公開 API の `created_after` と `modified_after` で、月の初めごとの件数を取り、その差から月ごとの追加数・更新数を出す（Omeka S 4.0 以降）
- `tools/dates_by_paging.py` — 日付の絞り込みが効かないサイト（Omeka S 3.x）向け。全件をページ送りで取り、各資料の作成日時・更新日時の月を数える。資料の本文は保存しない
- `tools/oai_monthly.zsh` — OAI-PMH の `from` だけを付けた件数の差から、月ごとの更新数を出す（確かめ用）
- `tools/summarize_frequency.py` — 月ごとの表を、サイトごとに要約する（論文の表 2）
- `tools/cc_find_omeka_jp.zsh`・`tools/verify_candidates.py` — Common Crawl の URL の索引から Omeka のサイトの候補を拾い、API と HTML で確かめる（付録）
- `data/monthly-2026-11-03.tsv` — 8 サイトの月ごとの追加数・更新数（2026-11-03 に計測）。サイトは論文と同じ記号 A〜H
- `data/versions-2026-11-09.tsv` — 本体の版の系と、応答の見出しに出ていた PHP の版ごとのサイト数

## サイト名を記号にしている理由

本体の版の古いサイトを特定できる形で示すと、攻撃の手がかりになりうるためです。同じ理由で、版の表には記号を付けていません。

## 測り方の限界

- Omeka S が持つ更新日時は、各資料の最後の更新だけです。更新の頻度は実際より少なく出ます
- 非公開の資料は数えていません
- 相手のサーバの負担を避けるため、問い合わせの間隔を 1 秒以上空けています。使うときも同じようにしてください

## ライセンス

- 道具（`tools/`）: MIT License（`LICENSE`）
- データ（`data/`）: CC BY 4.0
