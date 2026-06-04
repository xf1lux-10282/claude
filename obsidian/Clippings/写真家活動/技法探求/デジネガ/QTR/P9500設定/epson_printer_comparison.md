# EPSONプリンターとQTR対応の比較

## プリンターモデルとインク構成

### Stylus Pro 9880 (Quad9880)
- **インク**: Ultrachrome K3 - **8色**
- `K, C, M, Y, LC, LM, LK, LLK`
- **QTRカーブ**: 16個（UCmk用）
- **対応用紙**: Enhanced Matte, Photo Rag, PremierArt Alpha/Omega

### Stylus Pro 9900 (Quad9900) ⭐
- **インク**: Ultrachrome HDR - **10色**
- `K, C, M, Y, LC, LM, LK, LLK, OR, GR`
- **QTRカーブ**: 23個（UCmk用16個 + UCpk用7個）
- **対応用紙**: Enhanced Matte, Photo Rag, PremierArt Alpha/Omega, Gloss
- **注目**: OrangeとGreenを含む！

### EPSON SC-P9500 (現在のプリンター)
- **インク**: Ultrachrome PRO12 - **12色**
- `PK/MK, C, M, Y, LC, LM, LK, LLK, OR, GR, VI, VLM`
- **QTRカーブ**: なし（これから作成）
- **特徴**: 9900の10色 + Violet, Vivid Light Magenta

## 互換性分析

### 9880 → P9500
- ✗ インク数が合わない（8色 vs 12色）
- ✗ OR, GRが使えない
- △ 基本的なモノクロには使えるが、色域が限定的

### 9900 → P9500 ⭐⭐⭐
- ✓ **10色が共通**（K, C, M, Y, LC, LM, LK, LLK, OR, GR）
- ✓ **互換性が高い！**
- △ VI, VLMは使われない（2色のみ未使用）
- ✓ ほぼすべてのトーンとカラーレンジをカバー

## Quad9900のカーブ一覧

### UCmk系（Matte Black用）- 16個
1. UCmk-EpsEnhMatte-Cool
2. UCmk-EpsEnhMatte-Coolse
3. UCmk-EpsEnhMatte-Sepia
4. UCmk-EpsEnhMatte-Warm
5. UCmk-HanPhotoRag-Cool
6. UCmk-HanPhotoRag-Coolse
7. UCmk-HanPhotoRag-Sepia
8. UCmk-HanPhotoRag-Warm
9. UCmk-PmJetAlpha-Cool1
10. UCmk-PmJetAlpha-Coolse
11. UCmk-PmJetAlpha-Sepia
12. UCmk-PmJetAlpha-Warm
13. UCmk-PmJetOmega-Cool1
14. UCmk-PmJetOmega-Coolse
15. UCmk-PmJetOmega-Sepia
16. UCmk-PmJetOmega-Warm

### UCpk系（Photo Black用）- 7個
17. UCpk-HmGloss-neutral
18. UCpk-HmGloss-warm
19. UCpk-HmGloss-warmer
20. UCpk-raw-neutral
21. UCpk-raw-warm
22. UCpk-raw-warmer
23. Purge-K（クリーニング用）

## 推奨アプローチ

### 最適解：Quad9900カーブを使用

**理由**:
1. インク構成が10色/12色で最も近い
2. OR（Orange）とGR（Green）を活用できる
3. 豊富なカーブ（23個）から選択可能
4. マットブラック・フォトブラック両対応

**手順**:
1. Quad9900カーブをQuadP9550ディレクトリにコピー
2. P9550_QTR.ppdに全カーブを追加
3. 用紙とトーンに応じて選択

**制限**:
- VI（Violet）とVLM（Vivid Light Magenta）は未使用
- ただし、これらは特殊な色域拡張用なので、モノクロ印刷には影響なし

## 実装方法

### 1. カーブをコピー

```bash
# QuadP9550ディレクトリを作成（なければ）
mkdir -p /Library/Printers/QTR/quadtone/QuadP9550

# Quad9900のカーブをコピー
cp /Library/Printers/QTR/quadtone/Quad9900/*.quad \
   /Library/Printers/QTR/quadtone/QuadP9550/
```

### 2. PPDにカーブを追加

`P9550_QTR_expanded.ppd`の`ripCurve1`セクションを拡張：

```ppd
*OpenUI *ripCurve1/Curve: PickOne
*OrderDependency: 40 AnySetup *ripCurve1
*DefaultripCurve1: UCmk-HanPhotoRag-Cool

# UCmk系（マットブラック）
*ripCurve1 UCmk-HanPhotoRag-Cool/Photo Rag - Cool (MK): ""
*ripCurve1 UCmk-HanPhotoRag-Warm/Photo Rag - Warm (MK): ""
*ripCurve1 UCmk-HanPhotoRag-Sepia/Photo Rag - Sepia (MK): ""
*ripCurve1 UCmk-HanPhotoRag-Coolse/Photo Rag - Cool Sepia (MK): ""

*ripCurve1 UCmk-EpsEnhMatte-Cool/Enhanced Matte - Cool (MK): ""
*ripCurve1 UCmk-EpsEnhMatte-Warm/Enhanced Matte - Warm (MK): ""
*ripCurve1 UCmk-EpsEnhMatte-Sepia/Enhanced Matte - Sepia (MK): ""
*ripCurve1 UCmk-EpsEnhMatte-Coolse/Enhanced Matte - Cool Sepia (MK): ""

... (他のUCmkカーブも同様)

# UCpk系（フォトブラック）
*ripCurve1 UCpk-HmGloss-neutral/Gloss - Neutral (PK): ""
*ripCurve1 UCpk-HmGloss-warm/Gloss - Warm (PK): ""
*ripCurve1 UCpk-HmGloss-warmer/Gloss - Warmer (PK): ""
*ripCurve1 UCpk-raw-neutral/Raw - Neutral (PK): ""
*ripCurve1 UCpk-raw-warm/Raw - Warm (PK): ""
*ripCurve1 UCpk-raw-warmer/Raw - Warmer (PK): ""

*ripCurve1 -/Linear: ""
*CloseUI: *ripCurve1
```

## 期待される結果

- **モノクロ印刷**: 9900と同等の高品質
- **トーン再現**: Cool, Warm, Sepia, Cool Sepiaから選択
- **用紙対応**: マット紙、ファインアート紙、光沢紙
- **色域**: OR, GRによる広い階調表現

## 次のステップ

1. Quad9900カーブのコピーとPPD更新
2. テスト印刷（用紙・トーン別）
3. 必要に応じてVI, VLMを活用したP9500専用カーブの作成

