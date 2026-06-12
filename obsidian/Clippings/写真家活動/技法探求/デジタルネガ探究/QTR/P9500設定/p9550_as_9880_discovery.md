# P9500とStylus Pro 9880の関係

## 重要な発見

### 1. P9500 = Stylus Pro 9880（後継機）

EPSON SC-P9500シリーズは、海外では「Stylus Pro 9880」の後継機として知られています。

### 2. QTRにQuad9880プロファイルが存在

`/Library/Printers/QTR/quadtone/Quad9880/`に以下のカーブが用意されています：

**UCmk (Ultrachrome K3インク) カーブ**:
- 用紙別:
  - **EpsEnhMatte**: EPSON Enhanced Matte
  - **HanPhotoRag**: Hahnemühle Photo Rag  
  - **PmJetAlpha**: PremierArt Jetstream Alpha
  - **PmJetOmega**: PremierArt Jetstream Omega

- トーン別:
  - **Cool**: クールトーン
  - **Coolse**: クールセピア
  - **Sepia**: セピアトーン
  - **Warm**: ウォームトーン

**合計16個のカーブ**が提供されています。

### 3. インクシステムの違い

**Stylus Pro 9880**:
- Ultrachrome K3インク
- K, C, M, Y, LC, LM, LK, LLK (8色)

**SC-P9500**:
- Ultrachrome PRO12インク
- PK/MK, C, M, Y, LC, LM, LK, LLK, OR, GR, VI, VLM (12色)

### 4. 互換性の可能性

P9500はより新しいインクセットを持っていますが、基本的なプリンターエンジン（ESC/P-R）は同じ系統です。

**可能なアプローチ**:

1. **Quad9880カーブをP9500で使用**
   - K, C, M, Y, LC, LM, LK, LLKの8色を使用
   - OR, GR, VI, VLMは使わない
   - 基本的なモノクロ/セピア印刷には十分

2. **Quad9880カーブをベースにP9500用にカスタマイズ**
   - 9880カーブを出発点として
   - P9500の追加色（OR, GR, VI, VLM）を活用
   - より豊かなトーン再現

## QuadToneRIP公式プロファイル

ユーザーから指摘: `QuadToneRIP/Profiles/4880-7880-9880-UC`

これは、QuadToneRIPのインストールパッケージまたはダウンロード可能なプロファイル集に含まれている可能性があります。

### 確認すべき場所

1. QuadToneRIPのオフィシャルサイト
2. インストーラーパッケージの中
3. `/Applications/QuadToneRIP/` （もし存在すれば）
4. ユーザーのダウンロードフォルダ

## 次のステップ

### 短期
1. Quad9880カーブをP9550_QTRで試用
2. 8色モード（UCmk）での印刷テスト
3. 用紙別カーブの比較

### 中期
1. QuadToneRIP公式プロファイル集を入手
2. P9500の12色を活用したカスタムカーブ作成
3. QTR-Linearize-Dataツールでキャリブレーション

### 長期
1. 複数用紙タイプのプロファイル作成
2. デジタルネガティブワークフローの確立
3. プラチナ・パラジウムプリント最適化

## Quad9880カーブの適用方法

### PPDに追加する

現在の `P9550_QTR.ppd` の `*OpenUI *ripCurve1/Curve:` セクションに、
Quad9880のカーブを追加：

```ppd
*OpenUI *ripCurve1/Curve: PickOne
*OrderDependency: 40 AnySetup *ripCurve1
*DefaultripCurve1: UCmk-HanPhotoRag-Cool
*ripCurve1 UCmk-HanPhotoRag-Cool/Hahnemühle Photo Rag (Cool): ""
*ripCurve1 UCmk-HanPhotoRag-Warm/Hahnemühle Photo Rag (Warm): ""
*ripCurve1 UCmk-HanPhotoRag-Sepia/Hahnemühle Photo Rag (Sepia): ""
*ripCurve1 UCmk-EpsEnhMatte-Cool/EPSON Enhanced Matte (Cool): ""
... (他のカーブも同様に)
*ripCurve1 -/Linear: ""
*CloseUI: *ripCurve1
```

### カーブをQuadP9550ディレクトリにコピー

```bash
# Quad9880カーブをP9550用にコピー
cp /Library/Printers/QTR/quadtone/Quad9880/*.quad \
   /Library/Printers/QTR/quadtone/QuadP9550/
```

## 参考リンク

- QuadToneRIP公式サイト: https://www.quadtonerip.com/
- Stylus Pro 9880仕様: EPSONアーカイブ
- P9500仕様: EPSON公式サイト

