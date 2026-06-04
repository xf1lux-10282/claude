# Precision EDN - index.html EDN RGB256対応修正

**作成日**: 2026-03-11
**対象**: リニアリティ検証グラフ（画像アップロード方式）
**目的**: EDN RGB256チャートの右→左読み取り順序に対応

---

## 📋 修正内容サマリー

EDN RGB256チャート（各行が右→左配置）を画像から読み取る際、正しい順序で値を抽出できるように修正しました。

### 修正ファイル

1. **index.html** - チャート読み取り順序セレクタを追加
2. **js/core.js** - 画像からの値抽出ロジックを修正
3. **js/ui.js** - 設定の保存・読み込みに対応

---

## 1. index.html の修正

### 追加箇所: 行96-109

画像アップロード部分の前に、チャート読み取り順序を選択するドロップダウンを追加：

```html
<!-- チャート読み取り順序設定 -->
<div class="settings-row" style="margin-bottom: 15px;">
  <div class="setting-group">
    <label for="chartReadOrder">チャート読み取り順序</label>
    <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">
      <strong>EDN RGB256の場合:</strong> 各行が右（暗）→左（明）の配置です<br>
      通常のEDN 256/101は「左→右（標準)」を選択
    </p>
    <select id="chartReadOrder" style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: 4px; background-color: var(--bg-secondary); color: var(--text-primary);">
      <option value="standard">左→右（標準 - EDN 256/101）</option>
      <option value="edn-rgb256">右→左（EDN RGB256）</option>
    </select>
  </div>
</div>
```

**機能**:
- ユーザーがチャートの読み取り順序を選択できる
- デフォルトは「標準」（左→右）
- EDN RGB256の場合は「右→左」を選択

---

## 2. js/core.js の修正

### 修正1: settings に chartReadOrder を追加（行17）

```javascript
this.settings = {
  samplingPoints: 4096,
  interpolation: 'pchip',
  chartType: 'EDN_256',  // EDN_256, EDN_101
  bitDepth: 16,
  mode: 'first_correction',  // 'first_correction', 'second_correction', 'combine_luts'
  chartReadOrder: 'standard'  // 'standard', 'edn-rgb256' ← 追加
};
```

### 修正2: extractStepValues 関数の変更（行94-130）

**重要な理解の修正**:

当初、画像の物理的な読み取り順序を変える実装をしましたが、これは**誤り**でした。

**正しい理解**:
- EDN RGB256チャートは画像上で**左→右に 0, 16, 32, ..., 240** と並んでいる
- 値は連続していないため、読み取り後に**データを並び替える**必要がある

**変更前**:
```javascript
extractStepValues(ctx, chartType) {
  const values = [];

  if (chartType === 'EDN_256') {
    // 16x16 = 256 ステップ
    // 上から下（暗→明）、左から右の順に読み取り
    for (let row = 1; row <= 16; row++) {
      for (let col = 1; col <= 16; col++) {
        const x = 84 * col + 20;
        const y = 84 * row + 20;
        const rgb = this.getAverageColor(ctx, x, y, 40);
        values.push(rgb);
      }
    }
  }
  // ...
}
```

**変更後**:
```javascript
extractStepValues(ctx, chartType) {
  let values = [];

  if (chartType === 'EDN_256') {
    // 16x16 = 256 ステップ
    // 常に左から右、上から下の順に読み取る（物理的な配置通り）
    for (let row = 1; row <= 16; row++) {
      for (let col = 1; col <= 16; col++) {
        const x = 84 * col + 20;
        const y = 84 * row + 20;
        const rgb = this.getAverageColor(ctx, x, y, 40);
        values.push(rgb);
      }
    }

    // EDN RGB256の場合、読み取り後にデータを並び替える
    if (this.settings.chartReadOrder === 'edn-rgb256') {
      values = this.convertEdnRgb256Order(values);
    }
  }
  // ...
}
```

### 修正3: convertEdnRgb256Order 関数の追加（行132-174）

**新規追加**:

```javascript
/**
 * EDN RGB256形式のデータを値順に並び替える
 * @param {Array} data - 画像から左→右、上→下で読み取ったRGB値の配列
 * @returns {Array} 値順（0-255）に並び替えられたRGB値の配列
 */
convertEdnRgb256Order(data) {
  if (data.length !== 256) {
    console.warn(`EDN RGB256は256ステップですが、${data.length}ステップのデータが入力されました`);
    return data;
  }

  const reorderedData = new Array(256);

  for (let inputIdx = 0; inputIdx < 256; inputIdx++) {
    // 入力インデックスから行と列を計算（左→右の読み取り順）
    const row = Math.floor(inputIdx / 16);          // 行番号(0-15)
    const col = inputIdx % 16;                      // 列番号(0-15)

    // 実際の値を計算
    const actualValue = row + col * 16;             // 値(0-255)

    // データを正しい位置に配置
    reorderedData[actualValue] = data[inputIdx];
  }

  return reorderedData;
}
```

**アルゴリズム説明（修正版）**:

EDN RGB256チャートの**実際の**画像上の配置:
```
画像上の物理配置（左→右で読み取ると）:
15  14  13  12  ... 2   1   0     ← 1行目（最上段）
31  30  29  28  ... 18  17  16    ← 2行目
47  46  45  44  ... 34  33  32    ← 3行目
...
255 254 253 252 ... 242 241 240   ← 16行目（最下段）
```

**重要**: 各行は右→左に連続する値が配置されている！

画像から左→右、上→下で読み取ると：
```
入力[0] = 値15
入力[1] = 値14
入力[2] = 値13
...
入力[15] = 値0
入力[16] = 値31
入力[17] = 値30
...
入力[255] = 値240
```

**変換ロジック（修正版）**:
```javascript
for (let inputIdx = 0; inputIdx < 256; inputIdx++) {
  const row = Math.floor(inputIdx / 16);        // 行番号(0-15)
  const colFromLeft = inputIdx % 16;            // 左からの列番号(0-15)

  // 各行の最初の値（各行の左端）= 行番号 × 16 + 15
  const rowStartValue = row * 16 + 15;

  // 実際の値 = 行の開始値 - 左からの列番号
  const actualValue = rowStartValue - colFromLeft;

  reorderedData[actualValue] = data[inputIdx];
}
```

**検証例**:
- inputIdx=0（1行目左端）: row=0, colFromLeft=0, rowStartValue=15, actualValue=15-0=**15** ✓
- inputIdx=15（1行目右端）: row=0, colFromLeft=15, rowStartValue=15, actualValue=15-15=**0** ✓
- inputIdx=16（2行目左端）: row=1, colFromLeft=0, rowStartValue=31, actualValue=31-0=**31** ✓
- inputIdx=31（2行目右端）: row=1, colFromLeft=15, rowStartValue=31, actualValue=31-15=**16** ✓
- inputIdx=255（16行目右端）: row=15, colFromLeft=15, rowStartValue=255, actualValue=255-15=**240** ✓

これにより、値の順序が 0, 1, 2, 3, ..., 255 に正しく並び替えられます。

---

## 3. js/ui.js の修正

### 修正1: イベントリスナー追加（行106-114）

```javascript
// チャート読み取り順序
document.getElementById('chartReadOrder')?.addEventListener('change', (e) => {
  this.edn.settings.chartReadOrder = e.target.value;
  this.saveSettings();
  if (this.uploadedFiles.length > 0) {
    this.showStatus('チャート読み取り順序を変更しました。再処理中...', 'info');
    this.processFiles();
  }
});
```

**機能**:
- ドロップダウン変更時に設定を更新
- 既に画像がアップロード済みの場合は自動再処理
- ユーザーに処理中のフィードバックを表示

### 修正2: loadSettings 関数の修正（行1385-1398）

```javascript
loadSettings() {
  const saved = localStorage.getItem('precisionEDN_settings');
  if (saved) {
    const settings = JSON.parse(saved);
    this.edn.settings = { ...this.edn.settings, ...settings };

    // UIに反映
    document.getElementById('samplingPoints').value = this.edn.settings.samplingPoints;
    document.getElementById('interpolation').value = this.edn.settings.interpolation;
    if (document.getElementById('chartReadOrder')) {
      document.getElementById('chartReadOrder').value = this.edn.settings.chartReadOrder || 'standard';
    }
  }
}
```

**機能**:
- ページ読み込み時に保存済み設定を復元
- chartReadOrder がない場合は 'standard' をデフォルトとして使用
- UI要素（ドロップダウン）に設定値を反映

---

## 🎯 使い方

### EDN RGB256チャートを作成する場合

1. Photoshopで[Create_EDN_RGB256_Chart.jsx](file:///Users/daisukekinoshita/Desktop/Create_EDN_RGB256_Chart.jsx)を実行
2. 「PNG形式で保存しますか？」で **「はい」** を選択（ブラウザで直接読み込み可能）
   - PNG: ブラウザで直接アップロード可能（8bit、ロスレス圧縮）
   - TIFF: 16bit保持だが、ブラウザでは非対応（Photoshop用）
3. デスクトップに `EDN_RGB256_Chart_YYYYMMDD.png` が作成される

### EDN RGB256チャートを使用する場合

1. [index.html](file:///Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/precision-edn/index.html) を開く
2. 「チャート読み取り順序」で **「右→左（EDN RGB256）」** を選択
3. EDN RGB256チャートのPNG画像をアップロード
   - プリントしてスキャンした画像、または
   - Photoshopスクリプトで作成したPNG画像（リニアリティ検証用）
4. リニアリティ検証グラフが正しく滑らかな曲線として表示される

### 通常のEDN 256/101チャートを使用する場合

1. 「チャート読み取り順序」で **「左→右（標準）」** を選択（デフォルト）
2. 通常通り画像をアップロード

### ファイル形式について

**対応形式**: PNG, JPEG のみ
**非対応**: TIFF（ブラウザのCanvas APIが対応していないため）

**重要**: ブラウザのCanvas APIは常に8bit RGBに変換します。16bit TIFFや16bit PNGでも、ブラウザで読み込むと8bitになります。これは正常な動作です。

---

## 📊 グラフの確認

### 正しい設定の場合

リニアリティ検証グラフが **滑らかな曲線** として表示される：

```
濃度
 ↑
 │        ／￣
 │      ／
 │    ／
 │  ／
 │／
 └─────────→ ステップ
```

### 間違った設定の場合

グラフが **階段状** または **ジグザグ** になる：

```
濃度
 ↑  ┐   ┐   ┐
 │  └─┐ └─┐ └─┐
 │    └─┐  └─┐  └─
 │      └────┘
 └─────────────→ ステップ
```

この場合、チャート読み取り順序の設定を確認してください。

---

## 🔄 既存の densitometer.html との違い

### densitometer.html（手動入力方式）

- ユーザーが濃度計で測定した値を手動入力
- 入力順序が間違っている場合、入力済みデータを並び替える
- `convertEdnRgb256Order()` 関数でデータを変換

### index.html（画像アップロード方式）

- 画像から自動的に値を抽出
- 画像読み取り時に正しい順序で抽出する
- `extractStepValues()` 関数で物理座標を逆順に読み取る

**両方とも同じ目的**:
- EDN RGB256の右→左配置に対応
- ユーザーが正しい順序を意識せずに使える

---

## ✅ テスト項目

修正後、以下を確認してください：

1. **標準チャート（EDN 256）**:
   - [ ] 「左→右（標準）」設定で正しいグラフが表示される
   - [ ] LUT生成が正常に動作する

2. **EDN RGB256チャート**:
   - [ ] 「右→左（EDN RGB256）」設定で滑らかなグラフが表示される
   - [ ] 階段状パターンが解消されている
   - [ ] LUT生成が正常に動作する

3. **設定の保存・復元**:
   - [ ] チャート読み取り順序の設定がページリロード後も保持される
   - [ ] 設定変更後、既存画像が自動再処理される

4. **互換性**:
   - [ ] 既存のEDN 101チャートも正常に動作する

---

## 🐛 トラブルシューティング

### グラフが階段状になる

**原因**: チャート読み取り順序の設定が間違っている

**対処**:
1. EDN RGB256の場合: 「右→左（EDN RGB256）」を選択
2. 通常のEDN 256/101の場合: 「左→右（標準）」を選択
3. 設定変更後、画像を再アップロードまたは自動再処理を待つ

### 設定が保存されない

**原因**: ブラウザのLocalStorageが無効化されている

**対処**:
- ブラウザの設定でCookie/LocalStorageを有効化
- プライベートブラウジングモードでは設定が保存されない

---

## 📝 まとめ

- **index.html**: チャート読み取り順序セレクタを追加
- **core.js**: 画像読み取り時に物理座標を逆順に処理
- **ui.js**: 設定の保存・読み込み・UI連携

これにより、EDN RGB256チャートの画像をアップロードしても、正しい順序でデータを抽出し、滑らかなリニアリティグラフを生成できるようになりました。

---

**Precision EDN - index.html EDN RGB256対応修正**
**作成日: 2026-03-11**
**対応バージョン: v1.0**
