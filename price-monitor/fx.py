"""為替レート(USD/JPY)の取得。

無料・APIキー不要のソースを順に試すフォールバック方式。
GitHub Actions のランナーから到達できればよい（開発サンドボックスは
許可リスト制のため到達できないことがあるが、本番では問題ない）。

ソース:
  1. open.er-api.com (https://open.er-api.com/v6/latest/USD)
  2. frankfurter.app  (https://api.frankfurter.app/latest?from=USD&to=JPY) ※ECB営業日
"""

from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass
class FxResult:
    usdjpy: float
    source: str


def _from_er_api(timeout: int) -> FxResult | None:
    r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=timeout)
    r.raise_for_status()
    data = r.json()
    rate = (data.get("rates") or {}).get("JPY")
    if rate:
        return FxResult(usdjpy=float(rate), source="open.er-api.com")
    return None


def _from_frankfurter(timeout: int) -> FxResult | None:
    r = requests.get(
        "https://api.frankfurter.app/latest", params={"from": "USD", "to": "JPY"}, timeout=timeout
    )
    r.raise_for_status()
    data = r.json()
    rate = (data.get("rates") or {}).get("JPY")
    if rate:
        return FxResult(usdjpy=float(rate), source="frankfurter.app")
    return None


def get_usdjpy(timeout: int = 15) -> FxResult | None:
    """USD/JPY を取得。全ソース失敗時は None（価格記録は続行させる）。"""
    for fetch in (_from_er_api, _from_frankfurter):
        try:
            result = fetch(timeout)
        except Exception as exc:
            print(f"  [fx] {fetch.__name__} 失敗: {exc}")
            result = None
        if result is not None:
            return result
    print("  [fx] 為替レートを取得できませんでした（価格のみ記録します）")
    return None
