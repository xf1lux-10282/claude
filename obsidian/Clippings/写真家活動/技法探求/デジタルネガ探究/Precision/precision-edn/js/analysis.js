/**
 * Precision EDN - 分析機能
 * トーンジャンプ検出・誤差分析・品質スコア
 */

class Analysis {
  /**
   * トーンジャンプを検出
   * @param {Array} curve - カーブデータ
   * @param {number} threshold - しきい値（デフォルト: 0.02 = 2%）
   * @returns {Array} 検出された問題箇所の配列
   */
  static detectToneJumps(curve, threshold = 0.02) {
    const jumps = [];
    const n = curve.length;

    // 勾配を計算
    const gradients = [];
    for (let i = 1; i < n; i++) {
      gradients.push(curve[i] - curve[i - 1]);
    }

    // 平均勾配を計算
    const avgGradient = gradients.reduce((a, b) => a + b, 0) / gradients.length;

    // 異常な勾配を検出
    for (let i = 0; i < gradients.length; i++) {
      const deviation = Math.abs(gradients[i] - avgGradient);

      if (deviation > threshold) {
        const position = (i / n) * 100;  // パーセント位置
        const severity = deviation > threshold * 2 ? 'high' : 'medium';

        jumps.push({
          index: i,
          position: position.toFixed(1),
          gradient: gradients[i],
          avgGradient: avgGradient,
          deviation: deviation,
          severity: severity,
          message: `${position.toFixed(1)}% 付近でトーンジャンプを検出（偏差: ${(deviation * 100).toFixed(2)}%）`
        });
      }
    }

    return jumps;
  }

  /**
   * 単調性をチェック
   * @param {Array} curve - カーブデータ
   * @returns {Object} 単調性チェック結果
   */
  static checkMonotonicity(curve) {
    let isMonotonic = true;
    const violations = [];

    for (let i = 1; i < curve.length; i++) {
      if (curve[i] < curve[i - 1]) {
        isMonotonic = false;
        violations.push({
          index: i,
          position: ((i / curve.length) * 100).toFixed(1),
          message: `${((i / curve.length) * 100).toFixed(1)}% で単調性違反`
        });
      }
    }

    return {
      isMonotonic: isMonotonic,
      violations: violations,
      message: isMonotonic ? '単調増加を維持しています' : `${violations.length}箇所で単調性違反`
    };
  }

  /**
   * 平均絶対誤差（MAE）を計算
   * @param {Array} measured - 測定値
   * @param {Array} ideal - 理想値
   * @returns {number} MAE (0-1)
   */
  static calculateMAE(measured, ideal) {
    if (measured.length !== ideal.length) {
      throw new Error('測定値と理想値の長さが一致しません');
    }

    let sum = 0;
    for (let i = 0; i < measured.length; i++) {
      sum += Math.abs(measured[i] - ideal[i]);
    }

    return sum / measured.length;
  }

  /**
   * 二乗平均平方根誤差（RMSE）を計算
   * @param {Array} measured - 測定値
   * @param {Array} ideal - 理想値
   * @returns {number} RMSE (0-1)
   */
  static calculateRMSE(measured, ideal) {
    if (measured.length !== ideal.length) {
      throw new Error('測定値と理想値の長さが一致しません');
    }

    let sum = 0;
    for (let i = 0; i < measured.length; i++) {
      const diff = measured[i] - ideal[i];
      sum += diff * diff;
    }

    return Math.sqrt(sum / measured.length);
  }

  /**
   * ステップごとの誤差を計算
   * @param {Array} measured - 測定値
   * @param {Array} ideal - 理想値
   * @returns {Array} 誤差データの配列
   */
  static calculateStepErrors(measured, ideal) {
    const errors = [];

    for (let i = 0; i < measured.length; i++) {
      const error = measured[i] - ideal[i];
      const errorPercent = error * 100;

      errors.push({
        step: i,
        measured: measured[i],
        ideal: ideal[i],
        error: error,
        errorPercent: errorPercent,
        absError: Math.abs(error)
      });
    }

    return errors;
  }

  /**
   * 最大誤差を見つける
   * @param {Array} errors - ステップごとの誤差
   * @returns {Object} 最大誤差の情報
   */
  static findMaxError(errors) {
    let maxError = errors[0];

    for (let i = 1; i < errors.length; i++) {
      if (errors[i].absError > maxError.absError) {
        maxError = errors[i];
      }
    }

    return maxError;
  }

  /**
   * 問題領域を特定（連続する大きな誤差）
   * @param {Array} errors - ステップごとの誤差
   * @param {number} threshold - しきい値（デフォルト: 0.03 = 3%）
   * @returns {Array} 問題領域の配列
   */
  static identifyProblemRegions(errors, threshold = 0.03) {
    const regions = [];
    let currentRegion = null;

    for (let i = 0; i < errors.length; i++) {
      if (errors[i].absError > threshold) {
        if (!currentRegion) {
          // 新しい問題領域の開始
          currentRegion = {
            start: i,
            end: i,
            maxError: errors[i].absError,
            avgError: errors[i].absError
          };
        } else {
          // 問題領域を拡張
          currentRegion.end = i;
          currentRegion.maxError = Math.max(currentRegion.maxError, errors[i].absError);
        }
      } else {
        if (currentRegion) {
          // 問題領域の終了
          const regionErrors = errors.slice(currentRegion.start, currentRegion.end + 1);
          currentRegion.avgError = regionErrors.reduce((sum, e) => sum + e.absError, 0) / regionErrors.length;

          const startPercent = Math.round(currentRegion.start / errors.length * 100);
          const endPercent = Math.round(currentRegion.end / errors.length * 100);

          currentRegion.message = `${startPercent}% - ${endPercent}% で大きな誤差（最大: ${Math.round(currentRegion.maxError * 100)}%）`;

          regions.push(currentRegion);
          currentRegion = null;
        }
      }
    }

    // 最後の領域を追加
    if (currentRegion) {
      const regionErrors = errors.slice(currentRegion.start, currentRegion.end + 1);
      currentRegion.avgError = regionErrors.reduce((sum, e) => sum + e.absError, 0) / regionErrors.length;

      const startPercent = Math.round(currentRegion.start / errors.length * 100);
      const endPercent = Math.round(currentRegion.end / errors.length * 100);

      currentRegion.message = `${startPercent}% - ${endPercent}% で大きな誤差（最大: ${Math.round(currentRegion.maxError * 100)}%）`;

      regions.push(currentRegion);
    }

    return regions;
  }

  /**
   * カーブの滑らかさを評価（2次微分）
   * @param {Array} curve - カーブデータ
   * @returns {number} 滑らかさスコア (0-100)
   */
  static evaluateSmoothness(curve) {
    const n = curve.length;
    const secondDerivatives = [];

    // 2次微分を計算
    for (let i = 1; i < n - 1; i++) {
      const d2 = curve[i + 1] - 2 * curve[i] + curve[i - 1];
      secondDerivatives.push(Math.abs(d2));
    }

    // 平均絶対2次微分
    const avgSecondDerivative = secondDerivatives.reduce((a, b) => a + b, 0) / secondDerivatives.length;

    // スコアに変換（小さいほど滑らか）
    // 0.0001未満: 100点、0.001以上: 0点
    const smoothness = Math.max(0, Math.min(100, 100 - (avgSecondDerivative / 0.001) * 100));

    return smoothness;
  }

  /**
   * 線形性を評価
   * @param {Array} measured - 測定値
   * @param {Array} ideal - 理想値
   * @returns {number} 線形性スコア (0-100)
   */
  static evaluateLinearity(measured, ideal) {
    const mae = this.calculateMAE(measured, ideal);

    // MAE が小さいほど高スコア
    // 0.01未満: 100点、0.1以上: 0点
    const linearity = Math.max(0, Math.min(100, 100 - (mae / 0.1) * 100));

    return linearity;
  }

  /**
   * 測定精度を評価（複数測定の場合の標準偏差）
   * @param {Array} measurementsList - 複数の測定値
   * @returns {number} 精度スコア (0-100)
   */
  static evaluatePrecision(measurementsList) {
    if (measurementsList.length < 2) {
      return 100;  // 単一測定の場合は評価不可
    }

    const steps = measurementsList[0].length;
    let totalStdDev = 0;

    for (let i = 0; i < steps; i++) {
      const values = measurementsList.map(m => m[i]);
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
      const stdDev = Math.sqrt(variance);
      totalStdDev += stdDev;
    }

    const avgStdDev = totalStdDev / steps;

    // 標準偏差が小さいほど高スコア
    // 0.01未満: 100点、0.1以上: 0点
    const precision = Math.max(0, Math.min(100, 100 - (avgStdDev / 0.1) * 100));

    return precision;
  }

  /**
   * 総合品質スコアを計算
   * @param {Object} analysisData - 分析データ
   * @returns {Object} 品質スコア
   */
  static calculateQualityScore(analysisData) {
    const smoothness = this.evaluateSmoothness(analysisData.curve);
    const linearity = this.evaluateLinearity(analysisData.measured, analysisData.ideal);
    const precision = analysisData.measurementsList
      ? this.evaluatePrecision(analysisData.measurementsList)
      : 100;

    // 一次補正では滑らかさを品質評価から除外
    // （プリンターの非線形性を正確に測定することが目的のため）
    const isFirstCorrection = analysisData.mode === 'first_correction';
    const overall = isFirstCorrection
      ? (linearity + precision) / 2  // 一次補正: 線形性と精度のみ
      : (smoothness + linearity + precision) / 3;  // 二次補正: 全要素

    let rating;
    if (overall >= 90) {
      rating = '優秀（後補正不要）';
    } else if (overall >= 80) {
      rating = '良好';
    } else if (overall >= 70) {
      rating = '可（一部手動調整推奨）';
    } else {
      rating = '要再測定';
    }

    return {
      smoothness: isFirstCorrection ? null : smoothness.toFixed(1),  // 一次補正では非表示
      linearity: linearity.toFixed(1),
      precision: precision.toFixed(1),
      overall: overall.toFixed(1),
      rating: rating
    };
  }

  /**
   * 完全な分析レポートを生成
   * @param {Object} data - 分析対象データ
   * @returns {Object} 分析レポート
   */
  static generateReport(data) {
    const { measured, ideal, curve, measurementsList, dmax, mode } = data;

    const mae = this.calculateMAE(measured, ideal);
    const rmse = this.calculateRMSE(measured, ideal);
    const stepErrors = this.calculateStepErrors(measured, ideal);
    const maxError = this.findMaxError(stepErrors);
    const problemRegions = this.identifyProblemRegions(stepErrors);
    const toneJumps = this.detectToneJumps(curve);
    const monotonicity = this.checkMonotonicity(curve);
    const qualityScore = this.calculateQualityScore({
      curve: curve,
      measured: measured,
      ideal: ideal,
      measurementsList: measurementsList
    });

    return {
      summary: {
        mae: (mae * 100).toFixed(2) + '%',
        rmse: (rmse * 100).toFixed(2) + '%',
        dmax: dmax ? dmax.toFixed(3) : 'N/A',
        maxError: {
          position: ((maxError.step / measured.length) * 100).toFixed(1) + '%',
          value: (maxError.errorPercent).toFixed(2) + '%'
        }
      },
      qualityScore: qualityScore,
      stepErrors: stepErrors,
      problemRegions: problemRegions,
      toneJumps: toneJumps,
      monotonicity: monotonicity,
      recommendations: this.generateRecommendations({
        mae: mae,
        problemRegions: problemRegions,
        toneJumps: toneJumps,
        monotonicity: monotonicity,
        qualityScore: qualityScore,
        mode: mode
      })
    };
  }

  /**
   * 推奨事項を生成
   * @param {Object} analysisResults - 分析結果
   * @returns {Array} 推奨事項の配列
   */
  static generateRecommendations(analysisResults) {
    const recommendations = [];
    const mode = analysisResults.mode || 'first_correction';

    // MAEが大きい場合 - モード別のメッセージ
    if (analysisResults.mae > 0.05) {
      let message = '';

      if (mode === 'first_correction') {
        // 1次補正: プリント品質やスキャン精度が原因の可能性
        message = '全体的な誤差が大きいです。プリント品質やスキャン精度を確認してください。';
      } else if (mode === 'second_correction') {
        // 2次補正: 1次補正LUTの精度が不十分な可能性
        message = '全体的な誤差が大きいです。1次補正LUTの精度が不十分な可能性があります。1次補正からやり直すことを検討してください。';
      } else {
        // combine_luts または不明なモード
        message = '全体的な誤差が大きいです。補正LUTの精度を確認してください。';
      }

      recommendations.push({
        type: 'warning',
        message: message
      });
    }

    // 問題領域は推奨事項に含めず、別セクションで表示するためスキップ

    // トーンジャンプがある場合
    if (analysisResults.toneJumps.length > 0) {
      recommendations.push({
        type: 'warning',
        message: `${analysisResults.toneJumps.length}箇所でトーンジャンプを検出しました。補間方法を変更するか、サンプリングポイント数を増やしてください。`
      });
    }

    // 単調性違反がある場合
    if (!analysisResults.monotonicity.isMonotonic) {
      recommendations.push({
        type: 'error',
        message: '単調性違反が検出されました。測定データに問題がある可能性があります。'
      });
    }

    // 品質スコアに基づく推奨
    const overallScore = parseFloat(analysisResults.qualityScore.overall);
    if (overallScore >= 90) {
      recommendations.push({
        type: 'success',
        message: '優秀な品質です。Photoshopでの後補正は不要です。'
      });
    } else if (overallScore >= 80) {
      recommendations.push({
        type: 'success',
        message: '良好な品質です。そのまま使用できます。'
      });
    } else if (overallScore >= 70) {
      recommendations.push({
        type: 'info',
        message: '可の品質です。必要に応じてPhotoshopで微調整してください。'
      });
    } else {
      recommendations.push({
        type: 'error',
        message: '品質が不十分です。測定をやり直すことを強く推奨します。'
      });
    }

    return recommendations;
  }
}
