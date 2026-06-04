/**
 * Precision EDN - コア機能
 * 16bit対応の色空間変換・LUT生成
 */

class PrecisionEDN {
  constructor() {
    this.imageData = null;
    this.measurements = [];
    this.curve = null;
    this.settings = {
      samplingPoints: 4096,
      interpolation: 'pchip',
      chartType: 'EDN_256',  // EDN_256, EDN_101
      bitDepth: 16,
      mode: 'first_correction',  // 'first_correction', 'second_correction', 'combine_luts'
      chartReadOrder: 'edn-rgb256'  // EDN RGB256形式に固定
    };
  }

  /**
   * EDNテストチャート画像を読み込み
   * @param {File} file - 画像ファイル
   * @returns {Promise} 処理完了後のPromise
   */
  loadImage(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        const img = new Image();

        img.onload = () => {
          // チャートタイプを判定
          const chartType = this.detectChartType(img.width, img.height);
          if (!chartType) {
            reject(new Error('サポートされていない画像サイズです。EDN 256 (1507x1507px)、EDN 256 Trimmed (1340x1340px) または EDN 101 (1003x1087px) を使用してください。'));
            return;
          }

          this.settings.chartType = chartType;

          // Canvas に描画して RGB 値を抽出
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d', { willReadFrequently: true });
          ctx.drawImage(img, 0, 0);

          // 各グレーステップの値を抽出
          this.measurements = this.extractStepValues(ctx, chartType);

          resolve({
            chartType: chartType,
            measurements: this.measurements,
            width: img.width,
            height: img.height
          });
        };

        img.onerror = () => reject(new Error('画像の読み込みに失敗しました'));
        img.src = e.target.result;
      };

      reader.onerror = () => reject(new Error('ファイルの読み込みに失敗しました'));
      reader.readAsDataURL(file);
    });
  }

  /**
   * 画像サイズからチャートタイプを判定
   * @param {number} width - 画像幅
   * @param {number} height - 画像高さ
   * @returns {string|null} チャートタイプ
   */
  detectChartType(width, height) {
    // EDN 256: 1507x1507 (±10px) - 110mm×110mm @ 300DPI with labels
    if (width >= 1497 && width <= 1517 && height >= 1497 && height <= 1517) {
      return 'EDN_256';
    }
    // EDN 256 Trimmed: 1340x1340 (±10px) - パッチ領域のみトリミング済み
    if (width >= 1330 && width <= 1350 && height >= 1330 && height <= 1350) {
      return 'EDN_256_TRIMMED';
    }
    // EDN 101: 1003x1087 (±10px)
    if (width >= 993 && width <= 1013 && height >= 1077 && height <= 1097) {
      return 'EDN_101';
    }
    return null;
  }

  /**
   * テストチャートから各ステップの値を抽出
   * @param {CanvasRenderingContext2D} ctx - Canvas コンテキスト
   * @param {string} chartType - チャートタイプ
   * @returns {Array} RGB値の配列
   */
  extractStepValues(ctx, chartType) {
    let values = [];

    if (chartType === 'EDN_256') {
      // 16x16 = 256 ステップ (1507×1507px)
      // 右上から左下に向かって読み取る（ステップ0=右上黒、ステップ255=左下白）

      // EDN 256チャートのレイアウト定数（Create_255Step_Tablet_with_labels.jsx と同じ）
      const patchSize = 79;      // パッチサイズ
      const margin = 5;          // パッチ間のマージン
      const leftMargin = 79;     // 左側余白
      const topMargin = 79;      // 上側余白

      console.log('EDN 256 検出: 1507×1507px, パッチ=79px, マージン=5px, 余白=79px');

      // 右上から左下に向かって読み取る
      for (let row = 0; row < 16; row++) {          // 上から下へ
        for (let col = 15; col >= 0; col--) {       // 右から左へ
          // 各パッチの左上座標（外側余白 + マージンを考慮）
          // スクリプト: x = leftMargin + margin + col * (patchSize + margin)
          const patchLeft = leftMargin + margin + col * (patchSize + margin);
          const patchTop = topMargin + margin + row * (patchSize + margin);

          // パッチの中心座標
          const x = patchLeft + patchSize / 2;
          const y = patchTop + patchSize / 2;

          // サンプリングエリアを65x65pxで読み取り（パッチ79pxの約82%をカバー）
          const rgb = this.getAverageColor(ctx, x, y, 65);
          values.push(rgb);
        }
      }

      console.log('EDN 256: 256ステップ読み取り完了（右上→左下）');
      console.log('サンプリング: 65×65px/パッチ (パッチサイズ79pxの82%カバー)');
      console.log('最初の16要素:', values.slice(0, 16).map(v => `[${v[0].toFixed(0)},${v[1].toFixed(0)},${v[2].toFixed(0)}]`));

      // 重要: 配列を反転（暗→明の順に並べる）
      values.reverse();
      console.log('配列を反転: 暗→明の順に修正');
    } else if (chartType === 'EDN_256_TRIMMED') {
      // 16x16 = 256 ステップ (1340×1340px、余白なしトリミング済み)
      // 右上から左下に向かって読み取る（ステップ0=右上黒、ステップ255=左下白）

      // EDN 256 トリミング済みチャートのレイアウト定数
      // 余白を完全に削除した1340×1340px画像
      // パッチ領域: (79+5)×16 = 1344px → 1340pxにトリミング（左右2px削減）
      const patchSize = 79;      // パッチサイズ
      const margin = 5;          // パッチ間のマージン
      const leftMargin = 0;      // 余白なし（左端から直接パッチ開始）
      const topMargin = 0;       // 余白なし（上端から直接パッチ開始）

      console.log('EDN 256 Trimmed 検出: 1340×1340px, パッチ=79px, マージン=5px, 余白なし');

      // 右上から左下に向かって読み取る
      for (let row = 0; row < 16; row++) {          // 上から下へ
        for (let col = 15; col >= 0; col--) {       // 右から左へ
          // 各パッチの左上座標（余白オフセット + マージンを考慮）
          const patchLeft = leftMargin + margin + col * (patchSize + margin);
          const patchTop = topMargin + margin + row * (patchSize + margin);

          // パッチの中心座標
          const x = patchLeft + patchSize / 2;
          const y = patchTop + patchSize / 2;

          // サンプリングエリアを55x55pxで読み取り（パッチ79pxの約70%をカバー、端のリスク軽減）
          const rgb = this.getAverageColor(ctx, x, y, 55);
          values.push(rgb);
        }
      }

      console.log('EDN 256 Trimmed: 256ステップ読み取り完了（右上→左下）');
      console.log('サンプリング: 55×55px/パッチ (パッチサイズ79pxの70%カバー、端のリスク軽減)');
      console.log('最初の16要素:', values.slice(0, 16).map(v => `[${v[0].toFixed(0)},${v[1].toFixed(0)},${v[2].toFixed(0)}]`));

      // 重要: 配列を反転（暗→明の順に並べる）
      values.reverse();
      console.log('配列を反転: 暗→明の順に修正');
    } else if (chartType === 'EDN_101') {
      // 10x10 + 1 = 101 ステップ
      // 上から下（暗→明）の順に読み取り
      for (let row = 1; row <= 10; row++) {
        for (let col = 1; col <= 10; col++) {
          const x = 84 * col + 20;
          const y = 84 * (row + 1) + 20;  // 1行オフセット
          const rgb = this.getAverageColor(ctx, x, y, 40);
          values.push(rgb);
        }
      }
      // 最後の1パッチ
      const rgb = this.getAverageColor(ctx, 104, 104, 40);
      values.push(rgb);
    }

    return values;
  }

  /**
   * 指定領域の平均RGB値を取得
   * @param {CanvasRenderingContext2D} ctx - Canvas コンテキスト
   * @param {number} cx - 中心X座標
   * @param {number} cy - 中心Y座標
   * @param {number} size - サンプリング領域のサイズ
   * @returns {Array} [R, G, B] 平均値
   */
  getAverageColor(ctx, cx, cy, size) {
    const halfSize = Math.floor(size / 2);
    const imageData = ctx.getImageData(cx - halfSize, cy - halfSize, size, size);
    const data = imageData.data;

    // RGB値を配列に格納（中央値計算用）
    const rValues = [];
    const gValues = [];
    const bValues = [];

    for (let i = 0; i < data.length; i += 4) {
      rValues.push(data[i]);
      gValues.push(data[i + 1]);
      bValues.push(data[i + 2]);
    }

    // 中央値を使用（外れ値に強い）
    // プリントのムラ・スキャンノイズ・ゴミの影響を軽減
    return [
      this.getMedian(rValues),
      this.getMedian(gValues),
      this.getMedian(bValues)
    ];
  }

  /**
   * 配列の中央値を計算（IQRフィルタで外れ値を除外）
   * @param {Array} values - 数値の配列
   * @returns {number} 中央値
   */
  getMedian(values) {
    if (values.length === 0) return 0;

    // ソート（破壊的操作を避けるためコピー）
    const sorted = values.slice().sort((a, b) => a - b);

    // IQR（四分位範囲）フィルタで外れ値を除外
    const filtered = this.filterOutliers(sorted);

    // フィルタ後の配列から中央値を計算
    const mid = Math.floor(filtered.length / 2);

    if (filtered.length % 2 === 0) {
      // 偶数個の場合は中央2つの平均
      return (filtered[mid - 1] + filtered[mid]) / 2;
    } else {
      // 奇数個の場合は中央値
      return filtered[mid];
    }
  }

  /**
   * IQR（四分位範囲）を使って外れ値を除外
   * @param {Array} sortedValues - ソート済みの数値配列
   * @returns {Array} 外れ値を除外した配列
   */
  filterOutliers(sortedValues) {
    if (sortedValues.length < 4) return sortedValues;

    const n = sortedValues.length;

    // 第1四分位数(Q1)と第3四分位数(Q3)を計算
    const q1Index = Math.floor(n * 0.25);
    const q3Index = Math.floor(n * 0.75);
    const q1 = sortedValues[q1Index];
    const q3 = sortedValues[q3Index];

    // 四分位範囲(IQR)
    const iqr = q3 - q1;

    // 外れ値の範囲（1.5倍のIQR範囲外を除外）
    const lowerBound = q1 - 1.5 * iqr;
    const upperBound = q3 + 1.5 * iqr;

    // 範囲内の値のみを返す
    const filtered = sortedValues.filter(v => v >= lowerBound && v <= upperBound);

    // 除外されすぎた場合は元の配列を返す（安全策）
    return filtered.length > 0 ? filtered : sortedValues;
  }

  /**
   * RGB → XYZ → Lab 色空間変換（D50白色点）
   * @param {Array} rgb - [R, G, B] 0-255
   * @returns {Array} [L*, a*, b*]
   */
  rgbToLab(rgb) {
    // RGB → XYZ (sRGB, D65)
    let r = rgb[0] / 255;
    let g = rgb[1] / 255;
    let b = rgb[2] / 255;

    // ガンマ補正解除
    r = r > 0.04045 ? Math.pow((r + 0.055) / 1.055, 2.4) : r / 12.92;
    g = g > 0.04045 ? Math.pow((g + 0.055) / 1.055, 2.4) : g / 12.92;
    b = b > 0.04045 ? Math.pow((b + 0.055) / 1.055, 2.4) : b / 12.92;

    r *= 100;
    g *= 100;
    b *= 100;

    // RGB → XYZ 変換行列（sRGB, D65）
    const x = r * 0.4124 + g * 0.3576 + b * 0.1805;
    const y = r * 0.2126 + g * 0.7152 + b * 0.0722;
    const z = r * 0.0193 + g * 0.1192 + b * 0.9505;

    // XYZ → Lab (D50 白色点)
    const xn = 95.0429;
    const yn = 100;
    const zn = 108.89;

    let xr = x / xn;
    let yr = y / yn;
    let zr = z / zn;

    const delta = 6 / 29;
    const deltaSquare = delta * delta;
    const deltaCube = delta * delta * delta;

    xr = xr > deltaCube ? Math.pow(xr, 1/3) : (xr / (3 * deltaSquare) + 4/29);
    yr = yr > deltaCube ? Math.pow(yr, 1/3) : (yr / (3 * deltaSquare) + 4/29);
    zr = zr > deltaCube ? Math.pow(zr, 1/3) : (zr / (3 * deltaSquare) + 4/29);

    const L = 116 * yr - 16;
    const a = 500 * (xr - yr);
    const bStar = 200 * (yr - zr);

    return [L, a, bStar];
  }

  /**
   * Lab → XYZ → RGB 色空間変換
   * @param {Array} lab - [L*, a*, b*]
   * @returns {Array} [R, G, B] 0-255
   */
  labToRgb(lab) {
    const L = lab[0];
    const a = lab[1];
    const b = lab[2];

    // Lab → XYZ
    const fy = (L + 16) / 116;
    const fx = a / 500 + fy;
    const fz = fy - b / 200;

    const delta = 6 / 29;
    const deltaCube = delta * delta * delta;

    const xr = fx * fx * fx > deltaCube ? fx * fx * fx : 3 * delta * delta * (fx - 4/29);
    const yr = fy * fy * fy > deltaCube ? fy * fy * fy : 3 * delta * delta * (fy - 4/29);
    const zr = fz * fz * fz > deltaCube ? fz * fz * fz : 3 * delta * delta * (fz - 4/29);

    const xn = 95.0429;
    const yn = 100;
    const zn = 108.89;

    const x = xr * xn;
    const y = yr * yn;
    const z = zr * zn;

    // XYZ → RGB 変換行列
    let r = x * 3.2405 + y * -1.5371 + z * -0.4985;
    let g = x * -0.9693 + y * 1.876 + z * 0.0416;
    let bVal = x * 0.0556 + y * -0.204 + z * 1.0572;

    // ガンマ補正
    r = r > 0.0031308 ? 1.055 * Math.pow(r, 1/2.4) - 0.055 : 12.92 * r;
    g = g > 0.0031308 ? 1.055 * Math.pow(g, 1/2.4) - 0.055 : 12.92 * g;
    bVal = bVal > 0.0031308 ? 1.055 * Math.pow(bVal, 1/2.4) - 0.055 : 12.92 * bVal;

    // 0-255 にクランプ
    r = Math.max(0, Math.min(255, r * 255));
    g = Math.max(0, Math.min(255, g * 255));
    bVal = Math.max(0, Math.min(255, bVal * 255));

    return [r, g, bVal];
  }

  /**
   * RGB値をグレースケール輝度に変換（16bit対応）
   * @param {Array} rgb - [R, G, B]
   * @returns {number} 輝度値 0-65535
   */
  rgbToLuminance16bit(rgb) {
    // ITU-R BT.709 の輝度係数
    const luminance = 0.2126 * rgb[0] + 0.7154 * rgb[1] + 0.0721 * rgb[2];
    // 8bit (0-255) → 16bit (0-65535)
    return Math.round((luminance / 255) * 65535);
  }

  /**
   * リニアリティ検証グラフ用: RGB値をそのまま正規化（反転なし）
   * @param {Array} measurements - RGB値の配列
   * @returns {Array} 正規化された値の配列（0-1）
   */
  normalizeRgbForGraph(measurements) {
    // EDN RGB256チャートはグレースケール（R=G=B）なので、R値を直接使用
    const values = measurements.map(rgb => rgb[0]);  // R値のみ使用

    const min = Math.min(...values);
    const max = Math.max(...values);

    // RGB値をそのまま正規化（反転なし）
    // RGB最小（最暗） → 0
    // RGB最大（最明） → 1
    return values.map(v => (v - min) / (max - min));
  }

  /**
   * 補正カーブ用: 測定値を濃度として正規化（RGB値を反転）
   * @param {Array} measurements - RGB値の配列
   * @returns {Array} 正規化された濃度の配列（0-1）
   */
  normalizeMeasurements(measurements) {
    // EDN RGB256チャートはグレースケール（R=G=B）なので、R値を直接使用
    const values = measurements.map(rgb => rgb[0]);  // R値のみ使用

    const min = Math.min(...values);  // RGB最小 = 最暗（高濃度）
    const max = Math.max(...values);  // RGB最大 = 最明（低濃度）

    // 濃度として正規化（RGB値を反転）
    // RGB最大（最明） → 濃度0（低濃度）
    // RGB最小（最暗） → 濃度1（高濃度）
    return values.map(v => (max - v) / (max - min));
  }

  /**
   * 線形化カーブを生成
   * @param {Array} measurements - 測定値（複数可）
   * @returns {Object} カーブデータ
   */
  generateLinearizationCurve(measurements) {
    // 複数測定の場合は平均化
    let avgMeasurements;
    if (measurements.length > 0 && Array.isArray(measurements[0][0])) {
      // 複数測定の平均
      avgMeasurements = this.averageMultipleMeasurements(measurements);
    } else {
      avgMeasurements = measurements;
    }

    // リニアリティ検証グラフ用: RGB値をそのまま正規化（反転なし）
    const rgbNormalized = this.normalizeRgbForGraph(avgMeasurements);

    // 補正カーブ用: RGB値を濃度に変換（反転あり）
    const densityNormalized = this.normalizeMeasurements(avgMeasurements);

    // 理想値（線形）
    const ideal = [];
    for (let i = 0; i < densityNormalized.length; i++) {
      ideal.push(i / (densityNormalized.length - 1));
    }

    // 補正LUTを生成（逆関数）
    // X軸: 入力デジタル値（0-1） → Y軸: 補正後デジタル値（0-1）
    const correctionCurve = this.computeInverseCurve(densityNormalized, ideal);

    // 補間してカーブを生成
    const interpolated = Interpolation.interpolate(
      this.settings.interpolation,
      correctionCurve.x,  // 入力デジタル値（0-1）
      correctionCurve.y,  // 補正後デジタル値（0-1）
      this.settings.samplingPoints
    );

    this.curve = {
      raw: densityNormalized,        // 補正カーブ用（濃度、反転済み）
      rawRgb: rgbNormalized,         // グラフ表示用（RGB、反転なし）
      ideal: ideal,
      correctionX: correctionCurve.x,
      correctionY: correctionCurve.y,
      interpolated: interpolated,
      points: this.settings.samplingPoints
    };

    return this.curve;
  }

  /**
   * 補正LUTを計算
   * @param {Array} measured - 測定値（実際の濃度、0-1）
   * @param {Array} ideal - 理想値（デジタル値、0-1）
   * @returns {Object} {x: 入力デジタル値配列, y: 補正後デジタル値配列}
   */
  computeInverseCurve(measured, ideal) {
    // measured[i]: デジタル値 ideal[i] を使ったときの実測濃度
    // ideal[i]: 入力デジタル値（0-1、昇順）

    // 【重要】LUTの方向性:
    // - 入力: 元画像のデジタル値（0-1）
    // - 出力: プリントで線形濃度を得るためのデジタル値（0-1）
    //
    // 例: デジタル値0.5を入力すると実測濃度0.3になってしまう場合
    //     → LUT(0.5) = 0.7（より明るい値に補正）して濃度0.5を実現

    // デバッグ: 測定データの状態を確認
    console.log('computeInverseCurve: measured data check');
    console.log(`  measured.length = ${measured.length}`);
    console.log(`  measured[0] = ${measured[0].toFixed(4)} (darkest)`);
    console.log(`  measured[${measured.length-1}] = ${measured[measured.length-1].toFixed(4)} (brightest)`);
    console.log(`  Last 10 measured values:`, measured.slice(-10).map(v => v.toFixed(4)));

    // 測定データが単調増加しているかチェック＆補正
    let nonMonotonic = 0;
    const correctedMeasured = [...measured];  // コピーして補正用に使う

    for (let i = 1; i < correctedMeasured.length; i++) {
      if (correctedMeasured[i] < correctedMeasured[i-1]) {
        nonMonotonic++;
        if (nonMonotonic <= 5) {
          console.warn(`  Non-monotonic at index ${i}: ${correctedMeasured[i-1].toFixed(4)} -> ${correctedMeasured[i].toFixed(4)}`);
        }

        // 逆転を補正: 前後の値から線形補間
        if (i < correctedMeasured.length - 1) {
          // 次の値が利用可能な場合: 前後の平均
          const prev = correctedMeasured[i-1];
          const next = correctedMeasured[i+1];
          correctedMeasured[i] = (prev + next) / 2;
          console.log(`    → 補正: ${correctedMeasured[i].toFixed(4)} (前後の平均)`);
        } else {
          // 最後の要素の場合: 前の値をわずかに増やす
          correctedMeasured[i] = correctedMeasured[i-1] + 0.0001;
          console.log(`    → 補正: ${correctedMeasured[i].toFixed(4)} (前の値+0.0001)`);
        }
      }
    }

    if (nonMonotonic > 0) {
      console.warn(`  Total non-monotonic points: ${nonMonotonic} (補正済み)`);
    }

    // 補正後、再度チェックして連続する逆転を処理
    let remainingIssues = 0;
    for (let i = 1; i < correctedMeasured.length; i++) {
      if (correctedMeasured[i] < correctedMeasured[i-1]) {
        // まだ逆転している場合: 前の値と同じにする（最低限の単調性保証）
        correctedMeasured[i] = correctedMeasured[i-1] + 0.00001;
        remainingIssues++;
      }
    }
    if (remainingIssues > 0) {
      console.warn(`  2nd pass: ${remainingIssues} points adjusted for monotonicity`);
    }

    // ペアを作成（入力デジタル値と実測濃度の対応）
    // 補正後のcorrectedMeasuredを使用
    const pairs = [];
    for (let i = 0; i < correctedMeasured.length; i++) {
      pairs.push({
        inputDigital: ideal[i],                // 元のデジタル値（0-1）
        measuredDensity: correctedMeasured[i]  // 補正済みの実測濃度
      });
    }

    // 補正LUTの構築
    // X軸: 元画像のデジタル値（0-1、線形）
    // Y軸: 補正後のデジタル値（プリントで線形濃度を得るための値）
    const x = [];  // 入力デジタル値（0-1、均等分割）
    const y = [];  // 補正後デジタル値

    const numPoints = this.settings.samplingPoints;

    // 測定データをソート（単調増加を保証）
    pairs.sort((a, b) => a.measuredDensity - b.measuredDensity);

    // 測定範囲を取得
    const minDensity = pairs[0].measuredDensity;
    const maxDensity = pairs[pairs.length - 1].measuredDensity;

    console.log(`  Density range: ${minDensity.toFixed(4)} to ${maxDensity.toFixed(4)}`);
    console.log(`  pairs[0]: density=${pairs[0].measuredDensity.toFixed(4)}, digital=${pairs[0].inputDigital.toFixed(4)}`);
    console.log(`  pairs[last]: density=${pairs[pairs.length-1].measuredDensity.toFixed(4)}, digital=${pairs[pairs.length-1].inputDigital.toFixed(4)}`);
    console.log(`  First 5 pairs:`, pairs.slice(0, 5).map(p => `[d:${p.measuredDensity.toFixed(4)}, i:${p.inputDigital.toFixed(4)}]`));
    console.log(`  Last 5 pairs:`, pairs.slice(-5).map(p => `[d:${p.measuredDensity.toFixed(4)}, i:${p.inputDigital.toFixed(4)}]`));

    // ステップ1: 通常のLUT生成（補正あり）
    for (let i = 0; i < numPoints; i++) {
      const targetDensity = i / (numPoints - 1);  // 目標濃度（0-1、線形）
      let correctedDigital;

      // 範囲外の処理
      if (targetDensity <= minDensity) {
        // 最も暗い濃度よりも暗い場合 → 最暗値を使用
        correctedDigital = pairs[0].inputDigital;

      } else if (targetDensity >= maxDensity) {
        // 最も明るい濃度よりも明るい場合 → 最明値を使用
        correctedDigital = pairs[pairs.length - 1].inputDigital;

      } else {
        // 範囲内の場合: 線形補間
        // targetDensityを実現するデジタル値を、pairsから補間で求める

        // targetDensityが入る区間を探す
        let foundInterval = false;
        for (let j = 0; j < pairs.length - 1; j++) {
          const d1 = pairs[j].measuredDensity;
          const d2 = pairs[j + 1].measuredDensity;

          if (targetDensity >= d1 && targetDensity <= d2) {
            // 線形補間
            if (d2 !== d1) {
              const t = (targetDensity - d1) / (d2 - d1);
              correctedDigital = pairs[j].inputDigital + t * (pairs[j + 1].inputDigital - pairs[j].inputDigital);
            } else {
              // d1 == d2 の場合（同じ濃度）
              correctedDigital = pairs[j].inputDigital;
            }
            foundInterval = true;
            break;
          }
        }

        // 万が一区間が見つからなかった場合（丸め誤差対策）
        if (!foundInterval) {
          console.warn(`  No interval found for targetDensity=${targetDensity.toFixed(4)}`);
          correctedDigital = targetDensity;  // フォールバック
        }
      }

      x.push(targetDensity);  // 入力: 目標濃度（0-1）
      y.push(correctedDigital);  // 出力: その濃度を実現するデジタル値
    }

    // ステップ2: LUT配列の逆転を検出して補正
    console.log('  LUT逆転チェック開始');
    let lutReversals = 0;
    for (let i = 1; i < y.length - 1; i++) {  // 両端（0とnumPoints-1）は後で固定するのでスキップ
      if (y[i] < y[i-1]) {
        lutReversals++;
        if (lutReversals <= 5) {
          console.warn(`  LUT reversal at index ${i}: ${y[i-1].toFixed(4)} -> ${y[i].toFixed(4)}`);
        }

        // 前後の平均で補正
        const prev = y[i-1];
        const next = y[i+1];
        y[i] = (prev + next) / 2;
        console.log(`    → LUT補正: ${y[i].toFixed(4)} (前後の平均)`);
      }
    }
    if (lutReversals > 0) {
      console.warn(`  Total LUT reversals: ${lutReversals} (補正済み)`);
    }

    // ステップ3: 2回目のパスで残存する逆転を処理
    let lutRemainingIssues = 0;
    for (let i = 1; i < y.length - 1; i++) {
      if (y[i] < y[i-1]) {
        y[i] = y[i-1] + 0.00001;
        lutRemainingIssues++;
      }
    }
    if (lutRemainingIssues > 0) {
      console.warn(`  LUT 2nd pass: ${lutRemainingIssues} points adjusted`);
    }

    // ステップ4: 両端を固定（入力0→出力0、入力1→出力1）
    y[0] = 0.0;                  // 完全な黒は補正不要
    y[numPoints - 1] = 1.0;      // 完全な白は補正不要
    console.log('  両端固定: y[0]=0.0, y[last]=1.0');

    // デバッグ: LUTの最後の10要素を確認
    console.log('  Last 10 LUT entries (input -> output):');
    for (let i = Math.max(0, numPoints - 10); i < numPoints; i++) {
      console.log(`    ${x[i].toFixed(4)} -> ${y[i].toFixed(4)} (8bit: ${Math.round(y[i]*255)})`);
    }

    return { x, y };
  }

  /**
   * 複数測定の平均化（中央値フィルタ）
   * @param {Array} measurementsList - 測定値の配列の配列
   * @returns {Array} 平均化された測定値
   */
  averageMultipleMeasurements(measurementsList) {
    const count = measurementsList.length;
    const steps = measurementsList[0].length;
    const averaged = [];

    for (let i = 0; i < steps; i++) {
      const values = measurementsList.map(m => m[i]);

      // RGB各チャンネルの中央値を取得
      const rValues = values.map(rgb => rgb[0]).sort((a, b) => a - b);
      const gValues = values.map(rgb => rgb[1]).sort((a, b) => a - b);
      const bValues = values.map(rgb => rgb[2]).sort((a, b) => a - b);

      const medianIndex = Math.floor(count / 2);
      averaged.push([
        rValues[medianIndex],
        gValues[medianIndex],
        bValues[medianIndex]
      ]);
    }

    return averaged;
  }

  /**
   * Dmax（最大濃度）を計算
   * @param {Array} measurements - 測定値
   * @returns {number} Dmax値
   */
  calculateDmax(measurements) {
    const labs = measurements.map(rgb => this.rgbToLab(rgb));
    const minL = Math.min(...labs.map(lab => lab[0]));

    // L*値から反射率Yへ変換
    // L* > 8 の場合: Y = ((L* + 16) / 116)^3
    // L* ≤ 8 の場合: Y = L* / 903.3
    let Y;
    if (minL > 8) {
      Y = Math.pow((minL + 16) / 116, 3);
    } else {
      Y = minL / 903.3;
    }

    // Dmax = -log10(Y) （反射濃度）
    const dmax = -Math.log10(Y);

    // プラチナプリントのDmaxは通常1.5-2.5程度、上限を5に設定
    return Math.min(dmax, 5);
  }
}
