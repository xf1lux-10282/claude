"""価格履歴の永続化。商品ごとに data/history/<id>.json を持つ。

履歴フォーマット:
{
  "id": "...",
  "name": "...",
  "url": "...",
  "currency": "JPY",
  "points": [
    {"t": "2026-06-05T09:00:00Z", "price": 1234.0, "method": "json-ld:price"}
  ]
}
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
HISTORY_DIR = DATA_DIR / "history"


def _history_path(product_id: str) -> Path:
    return HISTORY_DIR / f"{product_id}.json"


def load_history(product_id: str) -> dict:
    path = _history_path(product_id)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"id": product_id, "points": []}


def last_price(history: dict) -> float | None:
    points = history.get("points") or []
    return points[-1]["price"] if points else None


def append_point(product: dict, price: float, method: str, currency: str) -> dict:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    history = load_history(product["id"])
    history["id"] = product["id"]
    history["name"] = product.get("name")
    history["url"] = product.get("url")
    history["currency"] = currency
    history.setdefault("points", []).append(
        {
            "t": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "price": price,
            "method": method,
        }
    )
    _history_path(product["id"]).write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return history


def write_index(products: list[dict]) -> None:
    """ダッシュボード用の一覧 index.json を書き出す。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    index = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "products": []}
    for product in products:
        history = load_history(product["id"])
        points = history.get("points") or []
        latest = points[-1] if points else None
        first = points[0] if points else None
        index["products"].append(
            {
                "id": product["id"],
                "name": product.get("name"),
                "url": product.get("url"),
                "currency": history.get("currency") or product.get("currency"),
                "enabled": product.get("enabled", True),
                "target_price": product.get("target_price"),
                "latest_price": latest["price"] if latest else None,
                "latest_time": latest["t"] if latest else None,
                "first_price": first["price"] if first else None,
                "points": len(points),
            }
        )
    (DATA_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
