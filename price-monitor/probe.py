"""一時診断スクリプト: 商品ページのバリアント(サイズ)ごとの価格を洗い出す。

WooCommerce の変動商品は form.variations_form の data-product_variations に
各バリアントの属性(サイズ)と価格(display_price)が JSON で埋め込まれていることが多い。
それを読み出して「どのサイズがいくらか」を特定する。調査後は削除する。
使い方: python price-monitor/probe.py <URL>
"""

from __future__ import annotations

import sys
import json
import html as htmlmod

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def main(url: str) -> None:
    headers = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    resp = requests.get(url, headers=headers, timeout=25)
    print(f"### URL: {url}")
    print(f"### HTTP {resp.status_code} / {len(resp.text)} bytes")
    soup = BeautifulSoup(resp.text, "html.parser")
    print("### <title>:", soup.title.get_text(strip=True) if soup.title else None)

    # メイン価格ブロック（カルーセル外の最初の p.price）
    def in_carousel(el):
        node = el.parent
        while node is not None and getattr(node, "name", None):
            cls = node.get("class") or []
            if any(c in {"owl-carousel", "w-grid-list", "w-grid-item"} for c in cls):
                return True
            node = node.parent
        return False

    print("\n### メイン価格ブロック（カルーセル除外）")
    for b in soup.select("p.price"):
        if not in_carousel(b):
            print("  text:", b.get_text(strip=True)[:80])
            break

    print("\n### 変動商品のバリアント (form.variations_form)")
    forms = soup.select("form.variations_form")
    if not forms:
        print("  variations_form なし（単一価格商品の可能性）")
    for form in forms:
        raw = form.get("data-product_variations")
        if not raw or raw == "false":
            print("  data-product_variations なし/AJAX (=false)")
            # ドロップダウンの選択肢だけでも出す
            for sel in form.select("select"):
                opts = [o.get_text(strip=True) for o in sel.select("option") if o.get("value")]
                print(f"  select[{sel.get('name')}] options: {opts}")
            continue
        try:
            variations = json.loads(htmlmod.unescape(raw))
        except Exception as e:  # noqa: BLE001
            print("  JSON parse error:", e)
            continue
        for v in variations:
            attrs = v.get("attributes", {})
            price = v.get("display_price")
            print(f"  size={list(attrs.values())} -> display_price={price}  (regular={v.get('display_regular_price')})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
