/**
 * Precision EDN - レポート生成モジュール
 * 測定結果・品質分析の包括的なレポートを生成
 */

class ReportGenerator {
  /**
   * テキストレポートを生成
   * @param {Object} analysisResult - 分析結果
   * @param {Object} settings - 設定
   * @param {Array} fileNames - ファイル名リスト
   * @returns {string} マークダウン形式のレポート
   */
  static generateTextReport(analysisResult, settings, fileNames = []) {
    const date = new Date().toLocaleString('ja-JP');

    let report = '';

    // ヘッダー
    report += '# Precision EDN - 測定分析レポート\n\n';
    report += `**生成日時**: ${date}\n\n`;
    report += '---\n\n';

    // 測定ファイル情報
    report += '## 📁 測定ファイル情報\n\n';
    if (fileNames.length > 0) {
      report += `**測定ファイル数**: ${fileNames.length}枚\n\n`;
      fileNames.forEach((name, i) => {
        report += `${i + 1}. ${name}\n`;
      });
    } else {
      report += '**測定ファイル数**: 1枚\n';
    }
    report += '\n';

    // 設定情報
    report += '## ⚙️ 設定情報\n\n';
    report += `| 項目 | 値 |\n`;
    report += `|------|----|\n`;
    report += `| **補正モード** | ${this._getModeLabel(settings.mode)} |\n`;
    report += `| **チャート種類** | ${settings.chartType} |\n`;
    report += `| **サンプリングポイント** | ${settings.samplingPoints}点 |\n`;
    report += `| **補間方法** | ${settings.interpolation.toUpperCase()} |\n`;
    report += `| **Bit深度** | ${settings.bitDepth}bit |\n`;
    report += `| **Dmax (L*)** | ${settings.dmaxLStar} |\n`;
    report += '\n';

    // 品質スコア
    report += '## 🎯 品質スコア\n\n';
    const qs = analysisResult.qualityScore;
    report += `### 総合評価: ${qs.rating}\n\n`;
    report += `| 項目 | スコア |\n`;
    report += `|------|--------|\n`;
    if (qs.smoothness !== null) {
      report += `| **滑らかさ (Smoothness)** | ${qs.smoothness}/100 |\n`;
    }
    report += `| **線形性 (Linearity)** | ${qs.linearity}/100 |\n`;
    report += `| **精度 (Precision)** | ${qs.precision}/100 |\n`;
    report += `| **総合スコア** | **${qs.overall}/100** |\n`;
    report += '\n';

    // 測定サマリー
    report += '## 📊 測定サマリー\n\n';
    const sum = analysisResult.summary;
    report += `| 指標 | 値 |\n`;
    report += `|------|----|\n`;
    report += `| **MAE (平均絶対誤差)** | ${sum.mae} |\n`;
    report += `| **RMSE (二乗平均平方根誤差)** | ${sum.rmse} |\n`;
    report += `| **Dmax (濃度最大値)** | ${sum.dmax} |\n`;
    report += `| **最大誤差位置** | ${sum.maxError.position} |\n`;
    report += `| **最大誤差値** | ${sum.maxError.value} |\n`;
    report += '\n';

    // 単調性チェック
    report += '## 🔍 単調性チェック\n\n';
    const mono = analysisResult.monotonicity;
    if (mono.isMonotonic) {
      report += '✅ **単調増加を維持しています**\n\n';
    } else {
      report += `❌ **${mono.violations.length}箇所で単調性違反を検出**\n\n`;
      mono.violations.forEach(v => {
        report += `- ${v.message}\n`;
      });
      report += '\n';
    }

    // トーンジャンプ検出
    report += '## ⚠️ トーンジャンプ検出\n\n';
    const jumps = analysisResult.toneJumps;
    if (jumps.length === 0) {
      report += '✅ **トーンジャンプは検出されませんでした**\n\n';
    } else {
      report += `⚠️ **${jumps.length}箇所でトーンジャンプを検出**\n\n`;
      jumps.forEach(jump => {
        const severity = jump.severity === 'high' ? '🔴 高' : '🟡 中';
        report += `- **${severity}**: ${jump.message}\n`;
      });
      report += '\n';
    }

    // 問題領域
    report += '## 📍 問題領域\n\n';
    const regions = analysisResult.problemRegions;
    if (regions.length === 0) {
      report += '✅ **大きな誤差領域は検出されませんでした**\n\n';
    } else {
      report += `⚠️ **${regions.length}箇所で大きな誤差領域を検出**\n\n`;
      regions.forEach((region, i) => {
        report += `### 領域 ${i + 1}\n\n`;
        report += `- ${region.message}\n`;
        report += `- 平均誤差: ${Math.round(region.avgError * 100)}%\n\n`;
      });
    }

    // 推奨事項
    report += '## 💡 推奨事項\n\n';
    const recs = analysisResult.recommendations;
    if (recs.length === 0) {
      report += '✅ **特に問題はありません**\n\n';
    } else {
      recs.forEach(rec => {
        const icon = this._getRecommendationIcon(rec.type);
        report += `${icon} **${rec.type.toUpperCase()}**: ${rec.message}\n\n`;
      });
    }

    // ステップごとの誤差（上位10件）
    report += '## 📈 ステップごとの誤差（上位10件）\n\n';
    const errors = [...analysisResult.stepErrors]
      .sort((a, b) => b.absError - a.absError)
      .slice(0, 10);

    report += `| ステップ | 測定値 | 理想値 | 誤差 |\n`;
    report += `|---------|--------|--------|------|\n`;
    errors.forEach(e => {
      report += `| ${e.step} | ${e.measured.toFixed(3)} | ${e.ideal.toFixed(3)} | ${e.errorPercent.toFixed(2)}% |\n`;
    });
    report += '\n';

    // フッター
    report += '---\n\n';
    report += '**Precision EDN** - Digital Negative Linearization Tool\n';
    report += `Version: 20260311p\n`;

    return report;
  }

  /**
   * HTMLレポートを生成
   * @param {Object} analysisResult - 分析結果
   * @param {Object} settings - 設定
   * @param {Array} fileNames - ファイル名リスト
   * @param {Object} chartImages - グラフ画像 {linearity: base64, correction: base64}
   * @returns {string} HTML形式のレポート
   */
  static generateHTMLReport(analysisResult, settings, fileNames = [], chartImages = null) {
    const date = new Date().toLocaleString('ja-JP');
    const qs = analysisResult.qualityScore;
    const sum = analysisResult.summary;

    let html = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Precision EDN - 測定分析レポート</title>
  <style>
    body {
      font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
      max-width: 900px;
      margin: 0 auto;
      padding: 20px;
      background-color: #f5f5f5;
      color: #333;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      border-radius: 8px;
      margin-bottom: 20px;
    }
    .header h1 {
      margin: 0 0 10px 0;
      font-size: 28px;
    }
    .header .date {
      opacity: 0.9;
      font-size: 14px;
    }
    .section {
      background: white;
      padding: 20px;
      margin-bottom: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .section h2 {
      color: #667eea;
      border-bottom: 2px solid #667eea;
      padding-bottom: 10px;
      margin-top: 0;
    }
    .score-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin: 20px 0;
    }
    .score-card {
      background: #f8f9fa;
      padding: 15px;
      border-radius: 6px;
      text-align: center;
    }
    .score-card .label {
      font-size: 12px;
      color: #666;
      margin-bottom: 5px;
    }
    .score-card .value {
      font-size: 32px;
      font-weight: bold;
      color: #667eea;
    }
    .rating {
      display: inline-block;
      padding: 10px 20px;
      border-radius: 20px;
      font-weight: bold;
      font-size: 18px;
      margin: 10px 0;
    }
    .rating.excellent {
      background-color: #4CAF50;
      color: white;
    }
    .rating.good {
      background-color: #8BC34A;
      color: white;
    }
    .rating.fair {
      background-color: #ff9800;
      color: white;
    }
    .rating.poor {
      background-color: #f44336;
      color: white;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 15px 0;
    }
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    th {
      background-color: #f8f9fa;
      font-weight: bold;
      color: #667eea;
    }
    .status-ok {
      color: #4CAF50;
      font-weight: bold;
    }
    .status-warning {
      color: #ff9800;
      font-weight: bold;
    }
    .status-error {
      color: #f44336;
      font-weight: bold;
    }
    .recommendation {
      padding: 12px;
      margin: 10px 0;
      border-left: 4px solid;
      border-radius: 4px;
    }
    .recommendation.success {
      background-color: rgba(76, 175, 80, 0.1);
      border-color: #4CAF50;
    }
    .recommendation.info {
      background-color: rgba(33, 150, 243, 0.1);
      border-color: #2196F3;
    }
    .recommendation.warning {
      background-color: rgba(255, 152, 0, 0.1);
      border-color: #ff9800;
    }
    .recommendation.error {
      background-color: rgba(244, 67, 54, 0.1);
      border-color: #f44336;
    }
    .chart-image {
      width: 100%;
      max-width: 800px;
      height: auto;
      border-radius: 4px;
      border: 1px solid #ddd;
      margin: 15px 0;
    }
    .footer {
      text-align: center;
      color: #999;
      margin-top: 40px;
      padding: 20px;
      border-top: 1px solid #ddd;
    }
    @media print {
      body {
        background-color: white;
      }
      .section {
        box-shadow: none;
        page-break-inside: avoid;
      }
      .chart-image {
        max-width: 100%;
        page-break-inside: avoid;
      }
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>📊 Precision EDN - 測定分析レポート</h1>
    <div class="date">生成日時: ${date}</div>
  </div>
`;

    // ファイル情報
    html += `
  <div class="section">
    <h2>📁 測定ファイル情報</h2>
    <p><strong>測定ファイル数:</strong> ${fileNames.length || 1}枚</p>`;

    if (fileNames.length > 0) {
      html += '<ul>';
      fileNames.forEach(name => {
        html += `<li>${name}</li>`;
      });
      html += '</ul>';
    }
    html += `</div>`;

    // 品質スコア
    const ratingClass = this._getRatingClass(qs.rating);
    html += `
  <div class="section">
    <h2>🎯 品質スコア</h2>
    <div class="rating ${ratingClass}">${qs.rating}</div>
    <div class="score-grid">`;

    if (qs.smoothness !== null) {
      html += `
      <div class="score-card">
        <div class="label">滑らかさ</div>
        <div class="value">${qs.smoothness}</div>
      </div>`;
    }

    html += `
      <div class="score-card">
        <div class="label">線形性</div>
        <div class="value">${qs.linearity}</div>
      </div>
      <div class="score-card">
        <div class="label">精度</div>
        <div class="value">${qs.precision}</div>
      </div>
      <div class="score-card">
        <div class="label">総合スコア</div>
        <div class="value">${qs.overall}</div>
      </div>
    </div>
  </div>
`;

    // 測定サマリー
    html += `
  <div class="section">
    <h2>📊 測定サマリー</h2>
    <table>
      <tr><th>指標</th><th>値</th></tr>
      <tr><td>MAE (平均絶対誤差)</td><td>${sum.mae}</td></tr>
      <tr><td>RMSE (二乗平均平方根誤差)</td><td>${sum.rmse}</td></tr>
      <tr><td>Dmax (濃度最大値)</td><td>${sum.dmax}</td></tr>
      <tr><td>最大誤差位置</td><td>${sum.maxError.position}</td></tr>
      <tr><td>最大誤差値</td><td>${sum.maxError.value}</td></tr>
    </table>
  </div>
`;

    // グラフセクション
    if (chartImages && (chartImages.linearity || chartImages.correction)) {
      html += `
  <div class="section">
    <h2>📈 グラフ</h2>`;

      if (chartImages.linearity) {
        html += `
    <h3 style="font-size: 16px; margin-top: 20px; margin-bottom: 10px;">リニアリティ検証グラフ</h3>
    <img src="${chartImages.linearity}" alt="リニアリティ検証グラフ" class="chart-image">`;
      }

      if (chartImages.correction) {
        html += `
    <h3 style="font-size: 16px; margin-top: 20px; margin-bottom: 10px;">補正カーブ (LUT)</h3>
    <img src="${chartImages.correction}" alt="補正カーブグラフ" class="chart-image">`;
      }

      html += `
  </div>`;
    }

    // 推奨事項
    html += `
  <div class="section">
    <h2>💡 推奨事項</h2>`;

    if (analysisResult.recommendations.length === 0) {
      html += '<p class="status-ok">✅ 特に問題はありません</p>';
    } else {
      analysisResult.recommendations.forEach(rec => {
        html += `<div class="recommendation ${rec.type}">${rec.message}</div>`;
      });
    }
    html += `</div>`;

    // フッター
    html += `
  <div class="footer">
    <p><strong>Precision EDN</strong> - Digital Negative Linearization Tool</p>
    <p>Version: 20260311p</p>
  </div>
</body>
</html>`;

    return html;
  }

  /**
   * モードラベルを取得
   */
  static _getModeLabel(mode) {
    const labels = {
      'first_correction': '1次補正',
      'second_correction': '2次補正',
      'combine_luts': 'LUT結合'
    };
    return labels[mode] || mode;
  }

  /**
   * 推奨事項のアイコンを取得
   */
  static _getRecommendationIcon(type) {
    const icons = {
      'success': '✅',
      'info': 'ℹ️',
      'warning': '⚠️',
      'error': '❌'
    };
    return icons[type] || '•';
  }

  /**
   * 評価クラスを取得
   */
  static _getRatingClass(rating) {
    if (rating.includes('優秀')) return 'excellent';
    if (rating.includes('良好')) return 'good';
    if (rating.includes('可')) return 'fair';
    return 'poor';
  }

  /**
   * PDFレポートを生成
   * @param {Object} analysisResult - 分析結果
   * @param {Object} settings - 設定
   * @param {Array} fileNames - ファイル名リスト
   * @param {Object} chartImages - グラフ画像 {linearity: base64, correction: base64}
   * @returns {Promise<Blob>} PDF Blob
   */
  static async generatePDFReport(analysisResult, settings, fileNames = [], chartImages = null) {
    // jsPDFライブラリを確認
    if (typeof window.jspdf === 'undefined') {
      throw new Error('jsPDFライブラリが読み込まれていません');
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 15;
    const contentWidth = pageWidth - 2 * margin;
    let yPos = margin;

    const qs = analysisResult.qualityScore;
    const sum = analysisResult.summary;
    const date = new Date().toLocaleString('ja-JP');

    // フォント設定（日本語対応）
    // 注: 日本語表示には制限があるため、英数字で代替
    doc.setFont('helvetica');

    // ヘッダー
    doc.setFontSize(20);
    doc.setTextColor(102, 126, 234);
    doc.text('Precision EDN - Analysis Report', margin, yPos);
    yPos += 8;

    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.text(`Generated: ${date}`, margin, yPos);
    yPos += 10;

    // 区切り線
    doc.setDrawColor(102, 126, 234);
    doc.setLineWidth(0.5);
    doc.line(margin, yPos, pageWidth - margin, yPos);
    yPos += 8;

    // ファイル情報
    doc.setFontSize(14);
    doc.setTextColor(0, 0, 0);
    doc.text('Measurement Files', margin, yPos);
    yPos += 6;

    doc.setFontSize(10);
    doc.text(`Number of files: ${fileNames.length || 1}`, margin + 5, yPos);
    yPos += 5;

    if (fileNames.length > 0) {
      fileNames.forEach((name, i) => {
        if (yPos > pageHeight - margin) {
          doc.addPage();
          yPos = margin;
        }
        doc.text(`${i + 1}. ${name}`, margin + 10, yPos);
        yPos += 5;
      });
    }
    yPos += 5;

    // 品質スコア
    doc.setFontSize(14);
    doc.setTextColor(0, 0, 0);
    doc.text('Quality Score', margin, yPos);
    yPos += 6;

    doc.setFontSize(12);
    doc.setTextColor(102, 126, 234);
    doc.text(`Rating: ${qs.rating}`, margin + 5, yPos);
    yPos += 7;

    doc.setFontSize(10);
    doc.setTextColor(0, 0, 0);
    doc.text(`Smoothness:  ${qs.smoothness}/100`, margin + 5, yPos);
    yPos += 5;
    doc.text(`Linearity:   ${qs.linearity}/100`, margin + 5, yPos);
    yPos += 5;
    doc.text(`Precision:   ${qs.precision}/100`, margin + 5, yPos);
    yPos += 5;
    doc.text(`Overall:     ${qs.overall}/100`, margin + 5, yPos);
    yPos += 10;

    // 測定サマリー
    doc.setFontSize(14);
    doc.text('Measurement Summary', margin, yPos);
    yPos += 6;

    doc.setFontSize(10);
    doc.text(`MAE:                ${sum.mae}`, margin + 5, yPos);
    yPos += 5;
    doc.text(`RMSE:               ${sum.rmse}`, margin + 5, yPos);
    yPos += 5;
    doc.text(`Dmax:               ${sum.dmax}`, margin + 5, yPos);
    yPos += 5;
    doc.text(`Max Error Position: ${sum.maxError.position}`, margin + 5, yPos);
    yPos += 5;
    doc.text(`Max Error Value:    ${sum.maxError.value}`, margin + 5, yPos);
    yPos += 10;

    // グラフ画像
    if (chartImages && (chartImages.linearity || chartImages.correction)) {
      if (yPos > pageHeight - 100) {
        doc.addPage();
        yPos = margin;
      }

      doc.setFontSize(14);
      doc.text('Charts', margin, yPos);
      yPos += 6;

      if (chartImages.linearity) {
        doc.setFontSize(11);
        doc.text('Linearity Verification Chart', margin + 5, yPos);
        yPos += 5;

        const imgWidth = contentWidth;
        const imgHeight = imgWidth * 0.5; // アスペクト比2:1

        if (yPos + imgHeight > pageHeight - margin) {
          doc.addPage();
          yPos = margin;
        }

        doc.addImage(chartImages.linearity, 'PNG', margin, yPos, imgWidth, imgHeight);
        yPos += imgHeight + 10;
      }

      if (chartImages.correction) {
        if (yPos > pageHeight - 100) {
          doc.addPage();
          yPos = margin;
        }

        doc.setFontSize(11);
        doc.text('Correction Curve (LUT)', margin + 5, yPos);
        yPos += 5;

        const imgWidth = contentWidth;
        const imgHeight = imgWidth * 0.5;

        if (yPos + imgHeight > pageHeight - margin) {
          doc.addPage();
          yPos = margin;
        }

        doc.addImage(chartImages.correction, 'PNG', margin, yPos, imgWidth, imgHeight);
        yPos += imgHeight + 10;
      }
    }

    // 推奨事項
    if (yPos > pageHeight - 50) {
      doc.addPage();
      yPos = margin;
    }

    doc.setFontSize(14);
    doc.setTextColor(0, 0, 0);
    doc.text('Recommendations', margin, yPos);
    yPos += 6;

    doc.setFontSize(10);
    if (analysisResult.recommendations.length === 0) {
      doc.text('No issues detected', margin + 5, yPos);
      yPos += 5;
    } else {
      analysisResult.recommendations.forEach(rec => {
        if (yPos > pageHeight - margin - 10) {
          doc.addPage();
          yPos = margin;
        }

        const icon = rec.type === 'success' ? '[OK]' :
                     rec.type === 'warning' ? '[!]' :
                     rec.type === 'error' ? '[X]' : '[-]';

        const lines = doc.splitTextToSize(`${icon} ${rec.message}`, contentWidth - 10);
        lines.forEach(line => {
          doc.text(line, margin + 5, yPos);
          yPos += 5;
        });
        yPos += 2;
      });
    }

    // フッター
    const totalPages = doc.internal.pages.length - 1;
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150, 150, 150);
      doc.text(
        `Precision EDN v20260311q - Page ${i}/${totalPages}`,
        pageWidth / 2,
        pageHeight - 10,
        { align: 'center' }
      );
    }

    return doc.output('blob');
  }
}
