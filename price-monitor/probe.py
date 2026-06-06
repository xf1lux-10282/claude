"""一時診断スクリプト: 指定URLのページから価格候補を洗い出して表示する。

GitHub Actions ランナー（サイトに到達できる環境）で実行し、
ログを読んで「メイン商品の価格をどのセレクタで取れるか」を特定するための使い捨てツール。
使い方: python price-monitor/probe.py <URL>
"""

from __future__ import annotations

import sys
import json

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def ancestors_desc(el) -> str:
    """要素の祖先のタグ.classチェーンを簡潔に返す（どのセクションに属すか把握用）。"""
    chain = []
    node = el
    for _ in range(6):
        if node is None or node.name is None:
            break
        cls = ".".join(node.get("class", []) or [])
        chain.append(node.name + (f".{cls}" if cls else ""))
        node = node.parent
    return " < ".join(chain)


def main(url: str) -> None:
    headers = {
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=25)
    print(f"### HTTP {resp.status_code} / {len(resp.text)} bytes")
    soup = BeautifulSoup(resp.text, "html.parser")

    print("\n### <title>:", (soup.title.get_text(strip=True) if soup.title else None))

    print("\n### og/meta price tags")
    for attr, key in [
        ("property", "product:price:amount"),
        ("property", "og:price:amount"),
        ("itemprop", "price"),
    ]:
        for t in soup.find_all("meta", attrs={attr: key}):
            print(f"  meta[{attr}={key}] = {t.get('content')!r}")

    print("\n### JSON-LD scripts")
    for t in soup.find_all("script", attrs={"type": "application/ld+json"}):
        s = (t.string or "").strip()
        print("  ", s[:400].replace("\n", " "))

    print("\n### .usg_product_field_3 matches (problem selector)")
    for el in soup.select(".usg_product_field_3"):
        print(f"  text={el.get_text(strip=True)!r}")
        print(f"     ancestry: {ancestors_desc(el)}")

    print("\n### WooCommerce standard price candidates")
    for sel in [
        ".summary .price",
        ".entry-summary .price",
        "p.price",
        ".summary .amount",
        ".woocommerce-Price-amount",
    ]:
        els = soup.select(sel)
        print(f"  [{sel}] -> {len(els)} match")
        for el in els[:4]:
            print(f"      text={el.get_text(strip=True)!r} | {ancestors_desc(el)}")

    print("\n### Related/upsell sections present?")
    for sel in [".related", ".up-sells", ".upsells", ".cross-sells", "[class*=related]"]:
        print(f"  [{sel}] -> {len(soup.select(sel))} match")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
