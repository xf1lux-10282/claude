/**
 * Precision EDN - ファイル出力機能
 * 16bit対応LUT、Adobe形式、ZIP一括ダウンロード
 */

class ExportManager {
  /**
   * 1D LUT (.cube) を生成（Adobe Photoshop互換）
   * @param {Array} curve - カーブデータ
   * @param {number} points - ポイント数（デフォルト256）
   * @param {Object} metadata - メタデータ
   * @returns {string} .cube ファイルの内容
   */
  static generateCube1D(curve, points = 256, metadata = {}) {
    let output = '';

    // デバッグ: カーブの状態をチェック
    if (!curve || curve.length === 0) {
      console.error('generateCube1D: Invalid curve array');
      throw new Error('カーブデータが無効です');
    }

    console.log('═══════════════════════════════════════');
    console.log(`📊 LUT 1D 生成開始`);
    console.log(`  出力ポイント数: ${points} (${Math.log2(points).toFixed(1)}bit相当)`);
    console.log(`  カーブ解像度: ${curve.length}点`);
    console.log(`  カーブ範囲: ${curve[0].toFixed(6)} → ${curve[curve.length-1].toFixed(6)}`);

    // NaN値の存在をチェック
    const nanCount = curve.filter(v => isNaN(v) || v === undefined).length;
    if (nanCount > 0) {
      console.warn(`  ⚠️ NaN/undefined値: ${nanCount}個検出`);
    }

    // ヘッダー（Adobe Photoshop完全互換形式）
    output += 'TITLE "Precision EDN First Correction"\n';
    output += `LUT_1D_SIZE ${points}\n`;
    output += 'DOMAIN_MIN 0.0 0.0 0.0\n';
    output += 'DOMAIN_MAX 1.0 1.0 1.0\n';

    // コメント行（メタデータ）
    output += '#Created by Precision EDN\n';
    if (metadata.dmax) {
      output += `#Dmax ${metadata.dmax.toFixed(3)}\n`;
    }
    if (metadata.mae) {
      output += `#MAE ${(metadata.mae * 100).toFixed(2)}%\n`;
    }
    if (metadata.date) {
      output += `#Date ${metadata.date}\n`;
    }
    if (metadata.interpolation) {
      output += `#Interpolation ${metadata.interpolation}\n`;
    }

    // カーブを指定ポイント数にリサンプリング
    const resampled = this.resampleCurve(curve, points);

    // リサンプリング後もNaNチェック
    const resampledNanCount = resampled.filter(v => isNaN(v) || v === undefined).length;
    if (resampledNanCount > 0) {
      console.error(`generateCube1D: resampled curve contains ${resampledNanCount} NaN/undefined values`);
      // 最初の数個の値を表示
      console.log('First 10 resampled values:', resampled.slice(0, 10));
    }

    // データポイント（グレースケールなので R=G=B）
    for (let i = 0; i < resampled.length; i++) {
      const rawValue = resampled[i];

      // NaNの場合は警告して安全な値を使用
      if (isNaN(rawValue) || rawValue === undefined) {
        console.error(`generateCube1D: resampled[${i}] is NaN/undefined, using 0.0`);
        output += `0.000000 0.000000 0.000000\n`;
        continue;
      }

      const value = Math.max(0.0, Math.min(1.0, rawValue));  // 0-1にクランプ
      output += `${value.toFixed(6)} ${value.toFixed(6)} ${value.toFixed(6)}\n`;
    }

    // 最後の10エントリを8bit値で表示
    console.log(`  最後の10エントリ（8bit表示）:`);
    for (let i = Math.max(0, resampled.length - 10); i < resampled.length; i++) {
      const input8bit = Math.round((i / (resampled.length - 1)) * 255);
      const output8bit = Math.round(resampled[i] * 255);
      console.log(`    入力 ${input8bit} → 出力 ${output8bit}`);
    }

    const fileSize = (output.length / 1024).toFixed(1);
    console.log(`✅ LUT生成完了: ${fileSize} KB`);
    console.log('═══════════════════════════════════════');

    return output;
  }

  /**
   * 3D LUT (.cube) を生成（Photoshop互換）
   * @param {Array} curve - カーブデータ
   * @param {number} size - 3D LUTのサイズ（デフォルト32、Photoshop推奨）
   * @param {Object} metadata - メタデータ
   * @returns {string} .cube ファイルの内容
   */
  static generateCube3D(curve, size = 32, metadata = {}) {
    let output = '';

    // デバッグ: カーブの状態をチェック
    if (!curve || curve.length === 0) {
      console.error('generateCube3D: Invalid curve array');
      throw new Error('カーブデータが無効です');
    }

    console.log(`generateCube3D: curve length=${curve.length}, first=${curve[0]}, last=${curve[curve.length-1]}`);

    // ヘッダー（Adobe Photoshop完全互換形式）
    // 重要: TITLE, LUT_3D_SIZE, DOMAIN_MIN/MAXの順序が重要
    output += 'TITLE "Precision EDN First Correction"\n';
    output += `LUT_3D_SIZE ${size}\n`;
    output += 'DOMAIN_MIN 0.0 0.0 0.0\n';
    output += 'DOMAIN_MAX 1.0 1.0 1.0\n';

    // コメント行（メタデータ、#で始める）
    output += '#Created by Precision EDN\n';
    if (metadata.dmax) {
      output += `#Dmax ${metadata.dmax.toFixed(3)}\n`;
    }
    if (metadata.mae) {
      output += `#MAE ${(metadata.mae * 100).toFixed(2)}%\n`;
    }
    if (metadata.date) {
      output += `#Date ${metadata.date}\n`;
    }

    // 3D LUT生成（グレースケール: R=G=Bで同一カーブを適用）
    // Adobe形式: Blue→Green→Redの順でネストループ
    for (let b = 0; b < size; b++) {
      for (let g = 0; g < size; g++) {
        for (let r = 0; r < size; r++) {
          // グレースケールなので、R値のみでカーブ適用（G,Bは無視）
          const inputValue = r / (size - 1);

          // カーブから出力値を取得
          const outputValue = this.lookupCurve(curve, inputValue);

          // NaNチェック
          if (isNaN(outputValue) || outputValue === undefined) {
            console.error(`generateCube3D: lookupCurve returned NaN/undefined for input ${inputValue}`);
            output += `0.000000 0.000000 0.000000\n`;
            continue;
          }

          // 0-1にクランプして精度6桁で出力
          const clamped = Math.max(0.0, Math.min(1.0, outputValue));

          // Adobe形式: スペース区切りで3つの値を出力
          output += `${clamped.toFixed(6)} ${clamped.toFixed(6)} ${clamped.toFixed(6)}\n`;
        }
      }
    }

    return output;
  }

  /**
   * Adobe Photoshop カーブ (.acv) を生成
   * @param {Array} curve - カーブデータ
   * @returns {Uint8Array} .acv ファイルのバイナリデータ
   */
  static generateACV(curve) {
    // Photoshop カーブは最大16ポイント
    // 戦略: カーブの変化点を優先的に抽出し、同一出力領域は端点のみ使用

    console.log('═══════════════════════════════════════');
    console.log('📈 Photoshop Curve (.acv) 生成開始');
    console.log(`  カーブ解像度: ${curve.length}点`);

    // ステップ1: 全256点の入出力ペアを作成
    const allPoints = [];
    for (let i = 0; i < 256; i++) {
      const inputValue = i / 255;
      const outputValue = this.lookupCurve(curve, inputValue);
      const output8bit = Math.round(outputValue * 255);
      allPoints.push({ input: i, output: output8bit });
    }

    // ステップ2: 同一出力値の範囲を検出し、各範囲の端点のみを制御点として使用
    const keyPoints = [allPoints[0]];  // 最初の点(0,0)は必須

    let rangeStart = 0;
    let currentRangeOutput = allPoints[0].output;

    for (let i = 1; i < allPoints.length; i++) {
      const currentOutput = allPoints[i].output;

      // 出力値が変化した場合
      if (currentOutput !== currentRangeOutput) {
        // 前の範囲の終点を追加（範囲が1点以上ある場合）
        if (i - 1 > rangeStart) {
          keyPoints.push(allPoints[i - 1]);
        }

        // 新しい範囲の開始点を追加
        keyPoints.push(allPoints[i]);

        rangeStart = i;
        currentRangeOutput = currentOutput;
      }
    }

    // 最後の点は必ず追加（まだ追加されていない場合）
    if (keyPoints[keyPoints.length - 1].input !== 255) {
      keyPoints.push(allPoints[255]);
    }

    console.log(`  検出された変化点: ${keyPoints.length}点`);

    // ステップ3: 16点に削減（必要な場合）
    let selectedPoints = keyPoints;
    if (keyPoints.length > 16) {
      // 重要度に基づいてダウンサンプリング
      selectedPoints = this.selectKeyPointsForCurve(keyPoints, 16);
      console.log(`  16点に最適化: ${selectedPoints.length}点`);
    }

    // ステップ4: Photoshop形式に変換
    const points = selectedPoints.map(p => p.input);
    const values = selectedPoints.map(p => p.output);

    console.log('  選択された制御点 (入力 → 出力):');
    for (let i = 0; i < Math.min(selectedPoints.length, 10); i++) {
      console.log(`    ${selectedPoints[i].input} → ${selectedPoints[i].output}`);
    }
    if (selectedPoints.length > 10) {
      console.log(`    ... (残り${selectedPoints.length - 10}点)`);
    }

    const numPoints = selectedPoints.length;

    // ACVファイル形式（バイナリ）
    // ArrayBufferとDataViewを使用して正確なバイナリデータを生成
    const bufferSize = 6 + (numPoints * 4);  // ヘッダー6バイト + 各ポイント4バイト
    const buffer = new ArrayBuffer(bufferSize);
    const view = new DataView(buffer);
    let offset = 0;

    // ヘッダー
    view.setUint16(offset, 4, false);  // バージョン 4 (big-endian)
    offset += 2;
    view.setUint16(offset, 1, false);  // カーブ数 1 (RGB合成カーブ)
    offset += 2;
    view.setUint16(offset, numPoints, false);  // ポイント数
    offset += 2;

    // カーブデータ（Photoshop形式: 出力値, 入力値の順）
    for (let i = 0; i < numPoints; i++) {
      view.setUint16(offset, values[i], false);  // 出力値（big-endian）
      offset += 2;
      view.setUint16(offset, points[i], false);  // 入力値（big-endian）
      offset += 2;
    }

    const fileSize = (bufferSize / 1024).toFixed(2);
    console.log(`✅ Photoshop Curve生成完了: ${fileSize} KB (${numPoints}点)`);
    console.log('═══════════════════════════════════════');

    return new Uint8Array(buffer);
  }

  /**
   * 設定メモを生成
   * @param {Object} settings - 設定情報
   * @param {Object} analysis - 分析結果
   * @returns {string} テキスト形式のメモ
   */
  static generateSettingsNote(settings, analysis) {
    const now = new Date();
    const dateStr = now.toLocaleString('ja-JP');

    let note = '';
    note += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
    note += 'Precision EDN 補正設定メモ\n';
    note += '16bit デジタルネガティブ補正ツール\n';
    note += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n';

    note += `作成日時: ${dateStr}\n`;
    note += `用紙: ${settings.paperName || '未設定'}\n`;
    note += `プリンター: ${settings.printer || '未設定'}\n\n`;

    // 薬品調合情報
    if (settings.chemicals) {
      note += '【薬品調合情報】\n';
      note += `- FO: ${settings.chemicals.FO} cc\n`;
      note += `- Pd: ${settings.chemicals.Pd} cc\n`;
      note += `- Pt: ${settings.chemicals.Pt} cc\n`;
      note += `- Na2: ${settings.chemicals.Na2} cc\n`;
      note += `- Tween: ${settings.chemicals.Tween} drop\n\n`;
    }

    note += '【測定条件】\n';
    note += `- テストチャート: ${settings.chartType}\n`;
    note += `- スキャン枚数: ${settings.scanCount || 1}枚`;
    if (settings.scanCount > 1) {
      note += '（中央値フィルタで平均化）';
    }
    note += '\n';
    note += `- サンプリングポイント: ${settings.samplingPoints}\n`;
    note += `- 補間方法: ${settings.interpolation.toUpperCase()}\n`;
    note += `- ビット深度: ${settings.bitDepth}bit\n\n`;

    if (analysis) {
      note += '【測定結果】\n';
      note += `- 最大濃度 (Dmax): ${analysis.summary.dmax}\n`;
      note += `- 平均絶対誤差 (MAE): ${analysis.summary.mae}\n`;
      note += `- 二乗平均平方根誤差 (RMSE): ${analysis.summary.rmse}\n`;
      note += `- 最大誤差: ${analysis.summary.maxError.value} (${analysis.summary.maxError.position})\n\n`;

      note += '【品質スコア】\n';
      note += `- 滑らかさ: ${analysis.qualityScore.smoothness}点\n`;
      note += `- 線形性: ${analysis.qualityScore.linearity}点\n`;
      note += `- 測定精度: ${analysis.qualityScore.precision}点\n`;
      note += `- 総合評価: ${analysis.qualityScore.overall}点（${analysis.qualityScore.rating}）\n\n`;

      if (analysis.recommendations.length > 0) {
        note += '【推奨事項】\n';
        analysis.recommendations.forEach((rec, i) => {
          note += `${i + 1}. ${rec.message}\n`;
        });
        note += '\n';
      }
    }

    note += '【推奨プリント設定】\n';
    note += '- 解像度: 1440×1440 dpi（または 5760×1440 dpi）\n';
    note += '- カラー処理: Photoshopによるカラー管理\n';
    note += '- プロファイル: 一般 RGB プロファイル\n';
    note += '- Black Enhance: OFF\n';
    note += '- 双方向印刷: OFF\n';
    note += '- スムージング: OFF\n';
    note += '- 色補正: なし（プリンター側）\n\n';

    note += '【備考】\n';
    note += settings.notes || 'なし';
    note += '\n\n';
    note += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';

    return note;
  }

  /**
   * CSV形式で測定データを出力
   * @param {Array} measured - 測定値
   * @param {Array} ideal - 理想値
   * @returns {string} CSV形式の文字列
   */
  static generateCSV(measured, ideal) {
    let csv = 'Step,Ideal,Measured,Error(%)\n';

    for (let i = 0; i < measured.length; i++) {
      const error = ((measured[i] - ideal[i]) * 100).toFixed(2);
      csv += `${i},${ideal[i].toFixed(6)},${measured[i].toFixed(6)},${error}\n`;
    }

    return csv;
  }

  /**
   * カーブの重要な制御点を選択（16点制限用）
   * @param {Array} keyPoints - 全変化点 [{input, output}, ...]
   * @param {number} maxPoints - 最大ポイント数（通常16）
   * @returns {Array} 選択された制御点
   */
  static selectKeyPointsForCurve(keyPoints, maxPoints) {
    // 両端は必須なので、中間から maxPoints-2 個を選択
    const first = keyPoints[0];
    const last = keyPoints[keyPoints.length - 1];
    const middle = keyPoints.slice(1, -1);

    if (middle.length <= maxPoints - 2) {
      return keyPoints;  // 削減不要
    }

    // 重要度スコアを計算（勾配の変化が大きい点ほど重要）
    const scored = middle.map((point, i) => {
      const prev = i > 0 ? middle[i - 1] : first;
      const next = i < middle.length - 1 ? middle[i + 1] : last;

      // 前後の勾配の差分（大きいほど重要）
      const slopeBefore = (point.output - prev.output) / (point.input - prev.input);
      const slopeAfter = (next.output - point.output) / (next.input - point.input);
      const importance = Math.abs(slopeAfter - slopeBefore);

      return { point, importance, index: i };
    });

    // 重要度でソートして上位を選択
    scored.sort((a, b) => b.importance - a.importance);
    const selectedMiddle = scored.slice(0, maxPoints - 2)
      .sort((a, b) => a.index - b.index)  // 元の順序に戻す
      .map(s => s.point);

    return [first, ...selectedMiddle, last];
  }

  /**
   * カーブをリサンプリング
   * @param {Array} curve - 元のカーブ
   * @param {number} targetPoints - 目標ポイント数
   * @returns {Array} リサンプリングされたカーブ
   */
  static resampleCurve(curve, targetPoints) {
    const resampled = [];
    const step = (curve.length - 1) / (targetPoints - 1);

    for (let i = 0; i < targetPoints; i++) {
      const index = i * step;
      const value = this.interpolateLinear(curve, index);
      resampled.push(value);
    }

    // 重要: 両端を元のカーブの両端値に強制固定（補間による誤差を防ぐ）
    if (resampled.length > 0) {
      resampled[0] = curve[0];                        // 最初の要素を固定
      resampled[resampled.length - 1] = curve[curve.length - 1];  // 最後の要素を固定
    }

    return resampled;
  }

  /**
   * 線形補間でカーブから値を取得
   * @param {Array} curve - カーブデータ
   * @param {number} index - インデックス（小数可）
   * @returns {number} 補間された値
   */
  static interpolateLinear(curve, index) {
    // 防御的チェック: curveが無効な場合
    if (!curve || curve.length === 0) {
      console.error('interpolateLinear: Invalid curve array');
      return 0.0;
    }

    const i = Math.floor(index);
    const fraction = index - i;

    // インデックスが範囲外の場合
    if (i < 0) {
      return curve[0];
    }
    if (i >= curve.length - 1) {
      return curve[curve.length - 1];
    }

    // 現在と次の値を取得
    const current = curve[i];
    const next = curve[i + 1];

    // NaNチェック: どちらかがNaNの場合
    if (isNaN(current) || current === undefined) {
      console.warn(`interpolateLinear: curve[${i}] is NaN or undefined`);
      return isNaN(next) || next === undefined ? 0.0 : next;
    }
    if (isNaN(next) || next === undefined) {
      console.warn(`interpolateLinear: curve[${i+1}] is NaN or undefined`);
      return current;
    }

    // 正常な線形補間
    return current + fraction * (next - current);
  }

  /**
   * カーブから値をルックアップ
   * @param {Array} curve - カーブデータ
   * @param {number} inputValue - 入力値（0-1）
   * @returns {number} 出力値
   */
  static lookupCurve(curve, inputValue) {
    const index = inputValue * (curve.length - 1);
    return this.interpolateLinear(curve, index);
  }

  /**
   * ファイルをダウンロード
   * @param {string} filename - ファイル名
   * @param {string|Uint8Array} content - ファイル内容
   * @param {string} mimeType - MIMEタイプ
   */
  static downloadFile(filename, content, mimeType = 'text/plain') {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * 複数ファイルをZIPでダウンロード（JSZip使用）
   * @param {Object} files - ファイル名をキー、内容を値とするオブジェクト
   * @param {string} zipFilename - ZIPファイル名
   */
  static async downloadZip(files, zipFilename) {
    if (typeof JSZip === 'undefined') {
      throw new Error('JSZipライブラリが読み込まれていません');
    }

    const zip = new JSZip();

    // ファイルをZIPに追加
    for (const [filename, content] of Object.entries(files)) {
      zip.file(filename, content);
    }

    // ZIP生成とダウンロード
    const blob = await zip.generateAsync({ type: 'blob' });
    this.downloadFile(zipFilename, blob, 'application/zip');
  }

  /**
   * .cubeファイルを読み込んでカーブデータに変換
   * @param {string} cubeContent - .cubeファイルの内容
   * @returns {Array} カーブデータ
   */
  static parseCubeFile(cubeContent) {
    const lines = cubeContent.split('\n');
    const curve = [];
    let inDataSection = false;

    for (const line of lines) {
      const trimmed = line.trim();

      // データセクション開始
      if (trimmed === '#LUT data points') {
        inDataSection = true;
        continue;
      }

      // データセクション終了
      if (trimmed === '#END data') {
        break;
      }

      // データ行を処理
      if (inDataSection && trimmed && !trimmed.startsWith('#')) {
        const values = trimmed.split(/\s+/);
        if (values.length >= 3) {
          // R=G=Bなのでどれか1つを取得
          curve.push(parseFloat(values[0]));
        }
      }
    }

    return curve;
  }

  /**
   * 2つのLUTを結合
   * @param {Array} lut1 - 1次補正LUT
   * @param {Array} lut2 - 2次補正LUT
   * @returns {Array} 結合されたLUT
   */
  static combineLUTs(lut1, lut2) {
    if (lut1.length !== lut2.length) {
      // サイズが異なる場合はリサンプリング
      const targetSize = Math.max(lut1.length, lut2.length);
      lut1 = this.resampleCurve(lut1, targetSize);
      lut2 = this.resampleCurve(lut2, targetSize);
    }

    const combined = [];

    for (let i = 0; i < lut1.length; i++) {
      // LUT1の出力をLUT2の入力として使用
      const intermediate = lut1[i];
      const index = intermediate * (lut2.length - 1);
      const finalValue = this.interpolateLinear(lut2, index);
      combined.push(finalValue);
    }

    return combined;
  }
}
