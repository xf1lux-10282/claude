"""scraper の価格抽出ロジックのテスト（ネットワーク不要）。

実行: python tests/test_scraper.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402

import scraper  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def _check(name, cond):
    print(f"  {'✔' if cond else '✖'} {name}")
    assert cond, name


def test_to_float():
    print("test_to_float")
    _check("£51.77", scraper._to_float("£51.77") == 51.77)
    _check("$78.50", scraper._to_float("$78.50") == 78.50)
    _check("1,234.56 円", scraper._to_float("1,234.56円") == 1234.56)
    _check("12,99 € (EU)", scraper._to_float("12,99 €") == 12.99)
    _check("1.234,56 (EU)", scraper._to_float("1.234,56") == 1234.56)
    _check("空文字 -> None", scraper._to_float("") is None)
    _check("数値なし -> None", scraper._to_float("お問い合わせ") is None)


def test_json_ld():
    print("test_json_ld (WooCommerce fixture)")
    html = (FIXTURES / "woocommerce_sample.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    result = scraper._from_json_ld(soup)
    _check("JSON-LD から 78.5 を抽出", result is not None and result.value == 78.5)


def test_css():
    print("test_css")
    html = (FIXTURES / "woocommerce_sample.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    result = scraper._from_css(soup, "p.price .woocommerce-Price-amount")
    _check("CSS セレクタから 78.5", result is not None and result.value == 78.5)


def test_strategy_order():
    print("test_strategy_order（自動抽出: 設定なしで取れる）")
    html = (FIXTURES / "woocommerce_sample.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    # fetch_price はネットワークを使うので、内部戦略のみ検証
    result = scraper._from_json_ld(soup) or scraper._from_meta(soup)
    _check("設定ゼロでも JSON-LD で抽出できる", result is not None and result.value == 78.5)


if __name__ == "__main__":
    test_to_float()
    test_json_ld()
    test_css()
    test_strategy_order()
    print("\nすべてのテストに合格しました ✅")
