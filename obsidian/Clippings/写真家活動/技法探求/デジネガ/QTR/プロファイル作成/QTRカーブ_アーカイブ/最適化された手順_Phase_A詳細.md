# QTRカーブ作成: 最適化された手順（Phase A詳細）

**作成日**: 2026年3月15日
**対象**: 新規プリンター・技法でのカーブ作成
**前提**: 開発記録（v9-v18）の教訓を活かした最短ルート

---

## 🔴 最重要概念: ネガ濃度とプリント濃度の逆相関

コンタクトプリントでは、ネガ濃度とプリント濃度は**逆の関係**になります:

### 物理的メカニズム
- **ネガ濃度 ↑ (濃い・黒い)** → 光を遮る → **プリント濃度 ↓ (明るい・白い)**
- **ネガ濃度 ↓ (薄い・透明)** → 光を通す → **プリント濃度 ↑ (暗い・黒い)**

### 具体例
| 元画像 | Input値 | ネガの状態 | プリントの状態 |
|--------|---------|------------|----------------|
| 黒 | 0 | 薄い（透明に近い） | 濃い（黒い） |
| グレー | 128 | 中間濃度 | 中間濃度 |
| 白 | 255 | 濃い（黒い） | 薄い（白い） |

### カーブ作成への影響
- Input 255（画像の白）を最大ネガ濃度にする
- Input 0（画像の黒）を最小ネガ濃度にする
- これにより、プリントで正しい階調が再現される

⚠️ **注意**: この逆相関を理解していないと、カーブが逆になってしまいます

---

## Phase A: 最大出力濃度の特定

**目的**: Input 255の目標ネガ濃度を決定する

**所要時間**: 4-6時間（測定含む）

---

### ステップ1: 33段階ステップチャートの準備

**使用チャート**:
- ファイル名: `Precision_EDN_v2_33step_20260313_1113.psd`
- ステップ数: 33段階
- 刻み: 0, 8, 16, 24, 32, ..., 248, 255

**あなたがやること**:
```
[ ] Precision_EDN_v2_33step.psdを開く
[ ] または、Claudeにステップチャート生成を依頼
[ ] ファイルを確認: 33段階のグラデーションが表示されるか
```

---

### ステップ2: リニアカーブで印刷

**あなたがやること**:
```
[ ] QTR Print-Toolを開く
[ ] ステップチャート（Precision_EDN_v2_33step）を選択
[ ] カーブ: リニアカーブを選択
    - 例: UCpk-EnhMatte-neut（リニアに近いUCカーブ）
    - またはClaude生成のリニアカーブ
[ ] 用紙: ピクトリコOHPフィルム（プラチナ/パラジウム用）
[ ] プリント実行
[ ] 乾燥まで待機（1-2時間）
```

**Claudeに伝えること**:
- 使用したカーブ名
- 印刷完了時刻

---

### ステップ3: ネガ透過濃度測定（33箇所）

**最重要作業**: この測定データが全カーブ生成の基礎になります

**あなたがやること**:
```
[ ] 濃度計を準備（透過濃度測定モード）
[ ] 測定環境を整える:
    - 室温: 20-25℃
    - 湿度: 40-60%
    - 照明: 一定（蛍光灯またはLED）
[ ] ネガが完全に乾燥しているか確認（最低1-2時間）

[ ] Input 0, 8, 16, 24, ..., 248, 255の33箇所を測定
    測定箇所の例:
    ┌─────────────────────────────────────┐
    │ 0  8  16 24 32 40 48 56 64 72 80 88 │ ← 各ステップの中央を測定
    │                                      │
    │ 96 104 112 120 128 136 144 152 160  │
    │                                      │
    │ 168 176 184 192 200 208 216 224 232 │
    │                                      │
    │ 240 248 255                          │
    └─────────────────────────────────────┘

[ ] 各ポイントを3回測定して平均値を計算
    例: Input 0
    - 1回目: 0.0928
    - 2回目: 0.0932
    - 3回目: 0.0933
    - 平均: 0.0931

[ ] 測定データをExcel/テキストエディタに入力
```

**データフォーマット**: `measurement_ST.csv`（ネガ濃度部分）

```csv
input,negative_density
0,0.0931
8,0.1155
16,0.1429
24,0.1628
32,0.1890
40,0.2410
48,0.2592
56,0.2994
64,0.3331
72,0.3783
80,0.4192
88,0.4771
96,0.5203
104,0.5502
112,0.6188
120,0.6690
128,0.7060
136,0.7386
144,0.8182
152,0.8680
160,0.9315
168,1.0214
176,1.1119
184,1.1516
192,1.2420
200,1.3013
208,1.3538
216,1.4009
224,1.4537
232,1.5003
240,1.5512
248,1.5987
255,1.6455
```

**チェックポイント**:
- [ ] 1行目はヘッダー（`input,negative_density`）
- [ ] 33行のデータ（Input 0-255の33箇所）
- [ ] 濃度は小数点4桁まで記録
- [ ] カンマ区切り
- [ ] 空行なし
- [ ] 濃度が単調増加しているか確認

**Claudeに伝えること**:
- `measurement_ST.csv`ファイルのパス
- 測定時の環境条件（室温、湿度）
- 使用した濃度計の機種

---

### ステップ4: 技法でプリント作成

**あなたがやること**:
```
[ ] 測定したネガ（ステップ3のネガ）でコンタクトプリント作成
[ ] 技法: プラチナ/パラジウム（標準的な条件）
    - 露光時間: あなたの標準条件（例: UV 10分）
    - 現像: 標準プロセス
    - 定着・水洗: 標準プロセス
[ ] 完全乾燥まで待機（24時間推奨）
    - プリント濃度は乾燥後に変化するため、必ず乾燥後に測定
```

**Claudeに伝えること**:
- 露光条件（UV光源、時間）
- 現像・定着の条件
- プリント完了時刻

---

### ステップ5: プリント反射濃度測定（33箇所）

**最重要作業**: ネガ濃度とプリント濃度の関係から白飛び地点を特定

**あなたがやること**:
```
[ ] 濃度計を準備（反射濃度測定モード）
[ ] プリントが完全に乾燥しているか確認（24時間後推奨）
[ ] 測定環境を整える（ステップ3と同じ条件）

[ ] ネガと同じ位置（33箇所）を測定
    測定箇所: Input 0, 8, 16, ..., 248, 255に対応する位置

[ ] 各ポイントを3回測定して平均値を計算

[ ] 測定データを同じCSVファイルに追加
```

**データフォーマット**: `measurement_ST.csv`（完全版）

```csv
input,negative_density,print_density
0,0.0931,0.05
8,0.1155,0.08
16,0.1429,0.12
24,0.1628,0.18
32,0.1890,0.25
40,0.2410,0.35
48,0.2592,0.42
56,0.2994,0.51
64,0.3331,0.58
72,0.3783,0.67
80,0.4192,0.74
88,0.4771,0.84
96,0.5203,0.91
104,0.5502,0.98
112,0.6188,1.08
120,0.6690,1.16
128,0.7060,1.22
136,0.7386,1.28
144,0.8182,1.35
152,0.8680,1.40
160,0.9315,1.45
168,1.0214,1.48
176,1.1119,1.50
184,1.1516,1.50
192,1.2420,1.50
200,1.3013,0.05  ← 白飛び（紙白に戻った）
208,1.3538,0.05
216,1.4009,0.05
224,1.4537,0.05
232,1.5003,0.05
240,1.5512,0.05
248,1.5987,0.05
255,1.6455,0.05
```

**注記**:
- 上記は例示です。実際の値はあなたの技法条件により異なります
- Input 200付近で白飛び（紙白0.05に戻る）している例

**チェックポイント**:
- [ ] 3列のデータ（input, negative_density, print_density）
- [ ] 33行のデータ
- [ ] プリント濃度も小数点2桁以上で記録
- [ ] 白飛び地点（プリント濃度が急に下がる箇所）があるか確認

**Claudeに伝えること**:
- 完全版`measurement_モノクロ1.csv`ファイル
- 白飛びが見られた箇所（目視での推測）

---

### ステップ6: Claudeによる自動解析

**Claudeがやること**:

1. **白飛び地点の自動検出スクリプト実行**:
```python
#!/usr/bin/env python3
"""Phase A: 最大出力濃度の自動検出"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def find_maximum_output_density(csv_path='measurement_ST.csv'):
    print("=" * 60)
    print("Phase A: 最大出力濃度の検出")
    print("=" * 60)

    # データ読み込み
    data = pd.read_csv(csv_path)

    # 紙白（最小プリント濃度）
    d_min_print = data['print_density'].min()
    print(f"\n紙白（D_min）: {d_min_print:.4f}")

    # プリント濃度が最大になる地点
    max_print_idx = data['print_density'].idxmax()
    max_print_density = data['print_density'].max()
    max_print_input = data['input'].iloc[max_print_idx]

    print(f"最大プリント濃度: {max_print_density:.4f} (Input {max_print_input})")

    # 白飛び地点検出（プリント濃度が紙白+0.10以下になる最小Input）
    paper_white_threshold = 0.10
    white_blown = data[data['print_density'] <= d_min_print + paper_white_threshold]

    if len(white_blown) == 0:
        print("\n⚠️  警告: 白飛びが検出されませんでした")
        print("ネガ濃度範囲が不足している可能性があります")
        # 最大ネガ濃度を使用
        max_output_density = data['negative_density'].max()
    else:
        white_blown_input = white_blown['input'].min()
        max_output_density = data[data['input'] == white_blown_input]['negative_density'].values[0]

        print(f"\n✓ 白飛び地点を検出:")
        print(f"  Input: {white_blown_input}")
        print(f"  ネガ濃度: {max_output_density:.4f}")
        print(f"  プリント濃度: {white_blown['print_density'].values[0]:.4f}")

    print(f"\n→ Input 255の目標ネガ濃度（最大出力濃度）: {max_output_density:.4f}")

    # グラフ作成
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ネガ濃度カーブ
    axes[0].plot(data['input'], data['negative_density'], 'b-o', markersize=4)
    axes[0].axhline(y=max_output_density, color='r', linestyle='--',
                    label=f'最大出力濃度: {max_output_density:.4f}')
    axes[0].axvline(x=255, color='orange', linestyle=':', alpha=0.5)
    axes[0].set_xlabel('Input Value', fontsize=12)
    axes[0].set_ylabel('Negative Density (透過濃度)', fontsize=12)
    axes[0].set_title('Negative Density Curve', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # プリント濃度カーブ
    axes[1].plot(data['input'], data['print_density'], 'g-o', markersize=4)
    axes[1].axhline(y=d_min_print, color='orange', linestyle='--',
                    label=f'紙白: {d_min_print:.4f}')
    if len(white_blown) > 0:
        axes[1].axvline(x=white_blown_input, color='r', linestyle='--',
                        label=f'白飛び地点: Input {white_blown_input}')
    axes[1].set_xlabel('Input Value', fontsize=12)
    axes[1].set_ylabel('Print Density (反射濃度)', fontsize=12)
    axes[1].set_title('Print Density Curve', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('phase_a_maximum_output_density.png', dpi=300, bbox_inches='tight')
    print(f"\n✓ グラフ保存: phase_a_maximum_output_density.png")

    return max_output_density

if __name__ == '__main__':
    max_density = find_maximum_output_density()
    print(f"\n次のステップ:")
    print(f"  Phase B: カーブ1生成")
    print(f"    TARGET_DENSITY_255 = {max_density:.4f}")
```

2. **ユーザーへの報告**:
```
✓ Phase A完了

最大出力濃度: 1.22
（これはInput 200のネガ濃度で、プリントが白飛びした地点です）

次のステップ（Phase B）:
- Input 255が濃度1.22になるカーブを生成します
- これにより、ネガのダイナミックレンジを最大限活用できます
```

---

## Phase A完了の確認

**Claudeからユーザーへの質問**:
```
[ ] measurement_ST.csvが正しく保存されていますか？
[ ] グラフ（phase_a_maximum_output_density.png）で白飛び地点が明確ですか？
[ ] 最大出力濃度（例: 1.22）に納得できますか？
```

すべて「はい」であれば、Phase Bへ進みます。

---

## Phase Aのまとめ

**達成したこと**:
- ✅ リニアカーブでネガ作成・測定
- ✅ 技法でプリント作成・測定
- ✅ 白飛び地点の特定
- ✅ 最大出力濃度の決定（例: 1.22）

**Phase Bで使用するデータ**:
- `measurement_ST.csv`（33箇所のネガ・プリント濃度）
- 最大出力濃度（Input 255の目標値）

**所要時間**:
- 印刷・乾燥: 2-3時間
- ネガ測定: 1時間
- プリント作成・乾燥: 1-24時間（技法による）
- プリント測定: 1時間
- **合計**: 4-6時間（プリント乾燥時間除く実働）

---

次: [Phase B: カーブ1生成](./最適化された手順_Phase_B詳細.md)
