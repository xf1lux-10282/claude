# Precision EDN v2 - RGB + Color Blocker ワークフロー

**確定版**: 2026-03-09

---

## 概要

このワークフローは:
- **RGB画像**で処理
- **Color Blocker**で余白保護
- **カラーモード印刷**でDmax 2.1を実現
- EDN方式と互換性あり

---

## ワークフロー図

### 測定フェーズ

```
33ステップチャート（RGB）
  ↓
階調の反転
  ↓
Color Blocker適用
  ↓
16bit RGB TIFF保存
  ↓
カラーモード印刷（クリスピア、レベル4、5760dpi）
  ↓
ネガ濃度測定① → data.csv
  ↓
プラチナプリント作成
  ↓
プリント濃度測定② → data.csv
  ↓
Precision EDN v2 実行
  ↓
LUT生成（precision_edn_v2.cube）
```

### 本番フェーズ

```
RAW現像画像（16bit RGB）
  ↓
Lightroom/Photoshop 基本編集
  ↓
Precision EDN v2 LUT適用（カラールックアップ）
  ↓
階調の反転
  ↓
Color Blocker適用
  ↓
16bit RGB TIFF保存
  ↓
カラーモード印刷（測定時と同じ設定）
  ↓
ネガ完成
  ↓
コンタクトプリント
  ↓
プラチナプリント完成
```

---

## 詳細手順

### Phase 1: 測定用チャート作成

#### 1-1. チャート生成

```
Photoshopスクリプト実行:
  Desktop/Create_33Step_Chart_with_CropMarks.jsx
  ↓
生成: Precision_EDN_v2_33step_chart_A4.tif
```

#### 1-2. RGB変換

```
Photoshopで開く
  ↓
イメージ > モード > RGBカラー
  カラープロファイル: Adobe RGB (1998)
  16bit/チャンネル維持
```

#### 1-3. 反転

```
イメージ > 色調補正 > 階調の反転
  ↓
チャートがネガ状態に
```

#### 1-4. Color Blocker適用

**EDNツール使用の場合**:
```
http://www.easydigitalnegatives.com/color-blocker/
  ↓
Color Blocker適用
```

**手動の場合**:
```
1. 新規レイヤー作成
2. 最背面に配置
3. RGB (0, 0, 0) で塗りつぶし
4. チャート周囲を完全に覆う
5. 統合
```

#### 1-5. 保存

```
ファイル > 別名で保存
  形式: TIFF
  圧縮: なし
  16bit RGB

ファイル名:
  "measurement_chart_RGB_inverted_blocked.tif"
```

---

### Phase 2: 印刷（測定用）

#### 2-1. Photoshop プリント設定

```
ファイル > プリント

カラーマネジメント:
  カラー処理: プリンターによるカラー管理
  ドキュメント: Adobe RGB (1998)
```

#### 2-2. macOS プリント設定

```
プリンタ: SC-PX1V
用紙サイズ: A4

「詳細を表示」→「印刷設定」:
  用紙種類: EPSON 写真用紙 <クリスピア>
  カラー: カラー ✓
  解像度: 5760x1440dpi
  品質: レベル4（高精細）
  双方向印刷: OFF

「カラー・マッチング」:
  カラーマッチング: カラーマッチングなし ✓
```

#### 2-3. プリセット保存

```
プリセット: 「現在の設定をプリセットとして保存」
  名前: "Precision_EDN_v2_RGB_Color_Dmax2.1"
```

#### 2-4. 印刷実行

```
「プリント」ボタン
  ↓
印刷完了後、30分乾燥
```

---

### Phase 3: 測定

#### 3-1. ネガ濃度測定①

```
濃度計（透過濃度モード）
  ↓
33ステップ各パッチの中央を測定
  ↓
各パッチ3箇所測定して平均（推奨）

記録:
  data/measurement_RGB_color.csv

例:
  input,negative_density,print_density
  0,2.10,
  8,2.05,
  ...
  128,0.70,
  ...
  255,0.10,
```

**確認ポイント**:
- Dmin ≈ 0.10
- Dmax ≈ 2.10
- 入力128 → ネガ濃度 ≈ 0.70

#### 3-2. プラチナプリント作成

```
同じネガ使用
  ↓
和紙にコンタクトプリント
  ↓
FO高濃度配合
  ↓
適正露光（Dmaxが出る露光）
  ↓
標準現像
  ↓
完全乾燥（24時間推奨）
```

#### 3-3. プリント濃度測定②

```
濃度計（反射濃度モード）
  ↓
33ステップ各パッチの濃度測定
  ↓
CSVに追記

例:
  input,negative_density,print_density
  0,2.10,0.05
  8,2.05,0.08
  ...
  128,0.70,0.85
  ...
  255,0.10,2.10
```

---

### Phase 4: LUT生成

#### 4-1. Precision EDN v2 実行

```bash
cd "/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision_edn_v2"

python3 main.py \
  --input data/measurement_RGB_color.csv \
  --output precision_edn_v2_RGB_color_Dmax2.1
```

#### 4-2. 出力確認

```
output/luts/
  ├── precision_edn_v2_RGB_color_Dmax2.1.cube ✓
  ├── precision_edn_v2_RGB_color_Dmax2.1_curve.csv
  └── precision_edn_v2_RGB_color_Dmax2.1_report.txt

output/graphs/
  └── analysis_curves.pdf ✓
```

#### 4-3. グラフ確認

```
analysis_curves.pdf を開く
  ↓
確認:
  - 入力値 → ネガ濃度（左）
  - ネガ濃度 → プリント濃度（中央）
  - 入力値 → プリント濃度（右）

異常がなければ完了 ✓
```

---

### Phase 5: 本番作品制作

#### 5-1. RAW現像

```
Lightroom / Camera Raw
  ↓
基本補正:
  - 露出
  - コントラスト
  - シャドウ/ハイライト
  - ホワイトバランス（必要なら）

16bit TIFF書き出し:
  カラースペース: Adobe RGB (1998)
  ビット深度: 16bit/チャンネル
```

#### 5-2. Photoshopで開く

```
書き出したTIFFを開く
  ↓
16bit RGB画像
```

#### 5-3. 作品編集（必要なら）

```
- トリミング
- 覆い焼き・焼き込み
- 部分調整
- 最終コントラスト調整

重要: R=G=Bを維持（ニュートラルグレー）
```

#### 5-4. LUT適用

```
レイヤー > 新規調整レイヤー > カラールックアップ
  ↓
3DLUT ファイル:
  output/luts/precision_edn_v2_RGB_color_Dmax2.1.cube
  ↓
読み込み → 適用
```

**確認**:
```
情報パネルで数値確認:
  適用前: R=128, G=128, B=128
  適用後: R=65, G=65, B=65
  ↓
R=G=B維持されている ✓
```

#### 5-5. 統合

```
レイヤー > 画像を統合
```

#### 5-6. 反転

```
イメージ > 色調補正 > 階調の反転
  ↓
ネガ状態
```

#### 5-7. Color Blocker適用

```
EDN Color Blocker または 手動で黒枠追加
  ↓
統合
```

#### 5-8. 保存

```
ファイル > 別名で保存
  形式: TIFF
  圧縮: なし
  16bit RGB

ファイル名: "[作品名]_negative_RGB_blocked.tif"
```

#### 5-9. 印刷

```
ファイル > プリント
  ↓
プリセット選択:
  "Precision_EDN_v2_RGB_Color_Dmax2.1"
  ↓
印刷実行
```

#### 5-10. コンタクトプリント

```
ネガ完成
  ↓
和紙にコンタクトプリント
  ↓
測定時と同じプロセス:
  - 同じFO濃度
  - 同じ露光時間
  - 同じ現像
  ↓
プラチナプリント完成 ✓
```

---

## 設定まとめ

### Photoshop設定

```
カラースペース: Adobe RGB (1998)
ビット深度: 16bit/チャンネル
カラー処理: プリンターによるカラー管理
```

### プリンター設定

```
機種: EPSON SC-PX1V
用紙（物理）: ピクトリコOHP TPS-100
用紙設定: EPSON 写真用紙 <クリスピア>
カラー: カラー
解像度: 5760x1440dpi
品質: レベル4（高精細）
双方向印刷: OFF
カラーマッチング: なし
```

### Precision EDN v2設定

```python
# config.py
PRINT_MODE = "Color"
NEGATIVE_DMAX = 2.10
WORKFLOW_TYPE = "RGB + Color Blocker"
```

---

## 期待される結果

### 測定データ

```
ネガDmin: 0.10
ネガDmax: 2.10
ネガ濃度レンジ: 2.0

プリントDmax: 2.1以上
露光レンジ: 約6.6 EV
```

### プリント品質

```
✓ 深いシャドウ（Dmax 2.1活用）
✓ 豊かな中間調（γ=1.8, 弱逆S）
✓ 滑らかなハイライト
✓ ランダムドット効果
✓ 色かぶりなし（R=G=B維持）
```

---

## トラブルシューティング

### 色かぶりが発生

**原因**: RGB画像がニュートラルグレーでない

**対策**:
```
1. 情報パネルで確認: R=G=B か？
2. グレースケール変換してからRGB変換
3. チャンネルミキサーで調整
```

### Dmaxが2.1より低い

**原因**: レベル4でインク量不足

**対策**:
```
レベル5を試す
または
印刷濃度を+1〜+2に
```

### Dmaxが2.3以上

**原因**: インク量過多

**対策**:
```
レベル3に下げる
または
印刷濃度を-1〜-2に
```

---

## ワークフローの利点

```
✓ 測定条件と本番条件の完全一致
✓ Dmax 2.1の実現
✓ ランダムドット効果
✓ ノズル分散
✓ Color Blocker対応
✓ EDN方式との互換性
✓ 再現性が高い
✓ 科学的根拠に基づく
```

---

## 次のステップ

```
1. 測定用チャート印刷 ✓
2. 測定①② → CSV作成
3. Precision EDN v2 実行
4. LUT生成確認
5. テスト画像でLUT検証
6. 本番作品制作開始
```

---

**作成**: 2026-03-09
**ワークフロー**: RGB + Color Blocker
**Dmax目標**: 2.10
**プリンター**: PX-1V カラーモード
**用紙**: クリスピア設定
