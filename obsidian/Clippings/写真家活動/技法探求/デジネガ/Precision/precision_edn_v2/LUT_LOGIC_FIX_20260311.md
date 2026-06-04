# Precision EDN v2 - LUT計算ロジック修正

**修正日**: 2026-03-11
**重要度**: 🔴 最重要（LUT計算の根本的な誤り）

---

## 🚨 発見した問題

**inverse_curve.py の `_generate_from_combined()` メソッド**に、JavaScript版と同じ根本的な誤りがありました。

### ❌ 間違った実装（修正前）

```python
for step in config.STEP_VALUES:
    # 理想のプリント濃度(リニア)
    ideal_print_density = print_max - (step / 255.0) * print_range

    # 実際にその濃度を出すための入力値を逆算
    corrected_input = self._find_inverse_value(
        combined_curve,
        ideal_print_density,
        0, 255
    )

    control_points.append((step, corrected_input))
```

**問題点**:
- LUTが「濃度 → デジタル値」のマッピングになっている
- 実際に必要なのは「デジタル値 → 補正デジタル値」のマッピング
- ユーザーが指定した値を使えない（逆方向のLUT）

---

## ✅ 正しい実装（修正後）

### 1. `_generate_from_combined()` メソッドの完全な書き直し

```python
def _generate_from_combined(self) -> List[Tuple[int, float]]:
    """
    合成カーブ(入力→プリント)から完全な逆カーブを生成

    正しいロジック:
    - 入力デジタル値ごとに処理
    - 各入力値に対して、理想濃度を実現する補正値を求める
    """
    input_vals, print_dens = self.analyzer.data.get_combined_curve_data()

    if len(input_vals) == 0:
        return self._generate_from_negative_only()

    # 濃度範囲を取得
    print_min = min(print_dens)
    print_max = max(print_dens)
    print_range = print_max - print_min

    # 測定値を (inputDigital, measuredDensity) のペアに整理
    pairs = []
    for i, input_val in enumerate(input_vals):
        pairs.append({
            'inputDigital': input_val / 255.0,  # 正規化 (0-1)
            'measuredDensity': print_dens[i]
        })

    # 測定濃度でソート（逆補間のため）
    pairs.sort(key=lambda p: p['measuredDensity'])

    # 33点の制御点を生成
    control_points = []

    for step in config.STEP_VALUES:
        # 入力デジタル値（0-1）
        input_digital = step / 255.0

        # 目標濃度 = 入力値（線形）
        target_density_normalized = input_digital

        # 実際の濃度範囲にマッピング
        target_density = print_max - target_density_normalized * print_range

        # この濃度を実現する補正デジタル値を逆補間で求める
        corrected_digital = self._inverse_interpolate(pairs, target_density)

        # 0-255スケールに戻す
        corrected_input = corrected_digital * 255.0
        corrected_input = np.clip(corrected_input, 0, 255)

        control_points.append((step, corrected_input))

    # Version 2の弱逆S補正を適用
    control_points = self._apply_inverse_s_correction(control_points)

    self.control_points = control_points

    if config.VERBOSE:
        print("\n=== 逆カーブ生成(完全版) ===")
        print(f"  制御点数: {len(control_points)}")
        print(f"  入力0 → {control_points[0][1]:.1f}")
        print(f"  入力128 → {control_points[16][1]:.1f}")
        print(f"  入力255 → {control_points[-1][1]:.1f}")

    return control_points
```

### 2. `_inverse_interpolate()` メソッドの追加

```python
def _inverse_interpolate(self, pairs: List[Dict], target_density: float) -> float:
    """
    目標濃度を実現するデジタル値を逆補間で求める

    Args:
        pairs: [{'inputDigital': float, 'measuredDensity': float}, ...]
               measuredDensity でソート済み
        target_density: 目標濃度

    Returns:
        補正後のデジタル値（0-1）
    """
    if len(pairs) == 0:
        return 0.0

    min_density = pairs[0]['measuredDensity']
    max_density = pairs[-1]['measuredDensity']

    # 範囲外チェック
    if target_density <= min_density:
        return pairs[0]['inputDigital']
    if target_density >= max_density:
        return pairs[-1]['inputDigital']

    # 線形補間で逆算
    for i in range(len(pairs) - 1):
        d1 = pairs[i]['measuredDensity']
        d2 = pairs[i + 1]['measuredDensity']

        if d1 <= target_density <= d2:
            # 補間係数
            t = (target_density - d1) / (d2 - d1) if d2 != d1 else 0.0

            # デジタル値を補間
            v1 = pairs[i]['inputDigital']
            v2 = pairs[i + 1]['inputDigital']

            return v1 + t * (v2 - v1)

    # フォールバック（範囲内のはずだが念のため）
    return np.clip(target_density / max_density, 0.0, 1.0)
```

### 3. `_find_inverse_value()` メソッドの削除

古い二分探索ベースのメソッドは削除されました（不要）。

---

## 📊 修正前後の比較

### 修正前（間違い）

**LUTの方向**: 濃度 → デジタル値

```
濃度0.0  → デジタル値255
濃度0.5  → デジタル値128
濃度1.0  → デジタル値0
```

→ **ユーザーは濃度を指定できない！**

### 修正後（正しい）

**LUTの方向**: 入力デジタル値 → 補正デジタル値

```
入力0   → 補正値0   → 濃度0.0（最明）
入力128 → 補正値170 → 濃度0.5（中間調）
入力255 → 補正値255 → 濃度1.0（最暗）
```

→ **ユーザーが指定した値を正しく線形化できる！**

---

## 🎯 LUTの正しい目的

### 1. **線形化（Linearization）**
非線形なプリンタ特性を補正して、濃度を線形にする

### 2. **階調の最適配置（Tone Mapping）**
Dmax制限内に、正しい階調を線形に再配置する

**具体例**:

測定結果:
```
入力値  実際の濃度
0    →  0.15  （最明、Dmin制限）
128  →  0.40  （中間調が圧縮）
255  →  0.85  （最暗、Dmax制限）
```

補正LUT適用後:
```
ユーザー指定値  LUT補正  実際の濃度
0            →  0     →  0.15  ✓
128          →  180   →  0.50  ✓ 正しい中間調！
255          →  255   →  0.85  ✓
```

---

## 📝 修正ファイル

| ファイル | 修正内容 |
|---------|---------|
| **inverse_curve.py** | `_generate_from_combined()` メソッド全体を書き直し |
| **inverse_curve.py** | `_inverse_interpolate()` メソッドを追加 |
| **inverse_curve.py** | `_find_inverse_value()` メソッドを削除 |

---

## ✅ 動作確認

修正後、以下を確認してください:

1. **LUT生成**: 正しい方向（入力 → 補正値）でLUTが生成される
2. **線形性**: 補正LUT適用後、プリント濃度が線形になる
3. **中間調**: 入力128が正しい中間濃度（0.5）を出力する

---

## 🔗 関連修正

この修正は、JavaScript版（precision-edn/js/core.js）で行った修正と同じです:
- バージョン: 20260311p
- 同じロジックエラーを修正
- 両バージョンで整合性が取れました

---

**Precision EDN v2 - LUT計算ロジック修正**
**修正日: 2026-03-11**
**重要**: この修正により、LUTが正しい方向で生成されるようになりました。
