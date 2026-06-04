/**
 * Precision EDN - Densitometer Edition
 * 濃度計測定データからプリント特性曲線と逆補正カーブを生成
 */

// グローバル変数
let characteristicChartInstance = null;
let correctionChartInstance = null;
let currentData = null;
let correctionCurve = null;

/**
 * Chart.js Zoom プラグインを登録
 */
if (typeof Chart !== 'undefined') {
  let zoomPlugin = null;
  if (typeof window.zoomPlugin !== 'undefined') {
    zoomPlugin = window.zoomPlugin;
  } else if (typeof window.ChartZoom !== 'undefined') {
    zoomPlugin = window.ChartZoom;
  } else if (typeof ChartJSZoom !== 'undefined') {
    zoomPlugin = ChartJSZoom;
  } else if (typeof Chart.Zoom !== 'undefined') {
    zoomPlugin = Chart.Zoom;
  }

  if (zoomPlugin) {
    Chart.register(zoomPlugin);
    console.log('Chart.js Zoom plugin registered');
  }
}

/**
 * DOMContentLoaded
 */
document.addEventListener('DOMContentLoaded', () => {
  initializeUI();
  setupEventListeners();
  loadDarkModePreference();
});

/**
 * UI初期化
 */
function initializeUI() {
  // 初期状態では分析セクションを非表示
  document.getElementById('chartSection').classList.add('hidden');
  document.getElementById('analysisSection').classList.add('hidden');
  document.getElementById('correctionSection').classList.add('hidden');
  document.getElementById('downloadSection').classList.add('hidden');
}

/**
 * イベントリスナー設定
 */
function setupEventListeners() {
  // 分析ボタン
  document.getElementById('analyzeBtn').addEventListener('click', handleAnalyze);

  // クリアボタン
  document.getElementById('clearBtn').addEventListener('click', handleClear);

  // ファイル入力
  document.getElementById('fileInput').addEventListener('change', handleFileUpload);

  // サンプルデータボタン
  document.getElementById('sampleIdeal').addEventListener('click', () => loadSampleData('ideal'));
  document.getElementById('sampleWeak').addEventListener('click', () => loadSampleData('weak'));
  document.getElementById('sampleStrong').addEventListener('click', () => loadSampleData('strong'));

  // ダウンロードボタン
  document.getElementById('downloadCube256').addEventListener('click', () => downloadLUT(256));
  document.getElementById('downloadCube1024').addEventListener('click', () => downloadLUT(1024));
  document.getElementById('downloadCSV').addEventListener('click', downloadCSV);
  document.getElementById('downloadNote').addEventListener('click', downloadNote);

  // ダークモードトグル
  document.getElementById('darkModeToggle').addEventListener('click', toggleDarkMode);
}

/**
 * データ解析処理
 */
function handleAnalyze() {
  const input = document.getElementById('dataInput').value.trim();

  if (!input) {
    showStatus('データが入力されていません', 'error');
    return;
  }

  try {
    // データをパース
    let parsedData = parseInputData(input);

    if (parsedData.length < 3) {
      showStatus('最低3つ以上のデータポイントが必要です', 'error');
      return;
    }

    // チャートタイプを取得
    const chartType = document.getElementById('chartType').value;

    // EDN RGB256の場合、データを並び替え
    if (chartType === 'edn-rgb256') {
      parsedData = convertEdnRgb256Order(parsedData);
      showStatus('EDN RGB256形式でデータを並び替えました', 'info');
    }

    // グローバル変数に保存
    currentData = parsedData;

    // 特性曲線を描画
    renderCharacteristicCurve(parsedData);

    // 逆補正カーブを生成
    correctionCurve = generateCorrectionCurve(parsedData);

    // 補正カーブを描画
    renderCorrectionCurve(correctionCurve);

    // 分析結果を表示
    displayAnalysis(parsedData, correctionCurve);

    // セクションを表示
    document.getElementById('chartSection').classList.remove('hidden');
    document.getElementById('analysisSection').classList.remove('hidden');
    document.getElementById('correctionSection').classList.remove('hidden');
    document.getElementById('downloadSection').classList.remove('hidden');

    showStatus('分析が完了しました', 'success');

  } catch (error) {
    showStatus(`エラー: ${error.message}`, 'error');
    console.error('Analysis error:', error);
  }
}

/**
 * 入力データをパース
 * @param {string} input - 入力テキスト
 * @returns {Array} [{step: number, density: number}, ...]
 */
function parseInputData(input) {
  const lines = input.split('\n').filter(line => line.trim());
  const data = [];
  let autoStepCounter = 1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // コメント行をスキップ
    if (line.startsWith('#') || line.startsWith('//')) {
      continue;
    }

    let step = null;
    let density = null;

    // 形式1（優先）: "0.05" (濃度値のみ、ステップ番号は自動割り当て)
    const densityOnly = parseFloat(line);
    if (!isNaN(densityOnly) && !line.includes(',') && !line.toLowerCase().includes('step')) {
      step = autoStepCounter++;
      density = densityOnly;
    }

    // 形式2: "step 1  0.05" または "step 1 0.05"
    if (step === null) {
      const stepMatch = line.match(/step\s+(\d+)\s+([\d.]+)/i);
      if (stepMatch) {
        step = parseInt(stepMatch[1], 10);
        density = parseFloat(stepMatch[2]);
        autoStepCounter = Math.max(autoStepCounter, step + 1);
      }
    }

    // 形式3: "1,0.05" または "1  0.05" (CSV形式)
    if (step === null) {
      const csvMatch = line.match(/^(\d+)[,\s]+([.\d]+)/);
      if (csvMatch) {
        step = parseInt(csvMatch[1], 10);
        density = parseFloat(csvMatch[2]);
        autoStepCounter = Math.max(autoStepCounter, step + 1);
      }
    }

    if (step !== null && density !== null && !isNaN(density)) {
      data.push({ step, density });
    }
  }

  if (data.length === 0) {
    throw new Error('有効なデータが見つかりませんでした。形式を確認してください。');
  }

  // ステップ番号でソート
  data.sort((a, b) => a.step - b.step);

  return data;
}

/**
 * ファイルアップロード処理
 */
function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();

  reader.onload = (e) => {
    const content = e.target.result;
    document.getElementById('dataInput').value = content;
    showStatus(`ファイル "${file.name}" を読み込みました`, 'success');
  };

  reader.onerror = () => {
    showStatus('ファイルの読み込みに失敗しました', 'error');
  };

  reader.readAsText(file);
}

/**
 * クリア処理
 */
function handleClear() {
  document.getElementById('dataInput').value = '';
  document.getElementById('fileInput').value = '';

  document.getElementById('chartSection').classList.add('hidden');
  document.getElementById('analysisSection').classList.add('hidden');
  document.getElementById('correctionSection').classList.add('hidden');
  document.getElementById('downloadSection').classList.add('hidden');

  currentData = null;
  correctionCurve = null;

  if (characteristicChartInstance) {
    characteristicChartInstance.destroy();
    characteristicChartInstance = null;
  }

  if (correctionChartInstance) {
    correctionChartInstance.destroy();
    correctionChartInstance = null;
  }

  showStatus('データをクリアしました', 'info');
}

/**
 * サンプルデータ読み込み
 */
function loadSampleData(type) {
  let sampleText = '';

  if (type === 'ideal') {
    // 理想的な直線（完全に線形）
    sampleText = `# 理想的な直線データ（完全線形）
# 濃度値のみを入力（ステップ番号は自動割り当て）
0.10
0.20
0.30
0.40
0.50
0.60
0.70
0.80
0.90
1.00
1.10
1.20
1.30
1.40
1.50
1.60
1.70
1.80
1.90
2.00
2.10`;

  } else if (type === 'weak') {
    // 弱いS字カーブ
    sampleText = `# 弱いS字カーブ（軽度の非線形性）
# 濃度値のみを入力（ステップ番号は自動割り当て）
0.08
0.18
0.28
0.39
0.50
0.61
0.71
0.81
0.91
1.01
1.10
1.19
1.28
1.37
1.46
1.56
1.66
1.77
1.88
1.99
2.10`;

  } else if (type === 'strong') {
    // 強いS字カーブ
    sampleText = `# 強いS字カーブ（顕著な非線形性）
# 濃度値のみを入力（ステップ番号は自動割り当て）
0.05
0.12
0.22
0.35
0.48
0.62
0.76
0.88
0.98
1.06
1.14
1.22
1.31
1.42
1.55
1.70
1.85
1.98
2.08
2.15
2.20`;
  }

  document.getElementById('dataInput').value = sampleText;
  showStatus(`サンプルデータ「${type}」を読み込みました`, 'info');
}

/**
 * 特性曲線グラフを描画
 */
function renderCharacteristicCurve(data) {
  const ctx = document.getElementById('characteristicChart');

  // 既存のグラフを破棄
  if (characteristicChartInstance) {
    characteristicChartInstance.destroy();
  }

  // データポイント
  const dataPoints = data.map(d => ({ x: d.step, y: d.density }));

  // 理想的な直線（最小二乗法で計算）
  const idealLine = calculateIdealLine(data);

  characteristicChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [
        {
          label: '理想線（線形回帰）',
          data: idealLine,
          borderColor: 'rgba(0, 0, 0, 0.5)',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointRadius: 0
        },
        {
          label: '測定値（プリント特性）',
          data: dataPoints,
          borderColor: 'rgba(255, 99, 132, 0.8)',
          backgroundColor: 'rgba(255, 99, 132, 0.3)',
          borderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: 'linear',
          title: {
            display: true,
            text: '入力階調（Step）',
            font: { size: 14 }
          },
          grid: {
            color: 'rgba(128, 128, 128, 0.2)'
          }
        },
        y: {
          type: 'linear',
          title: {
            display: true,
            text: 'プリント濃度（Density）',
            font: { size: 14 }
          },
          grid: {
            color: 'rgba(128, 128, 128, 0.2)'
          }
        }
      },
      plugins: {
        zoom: {
          limits: {
            x: { min: 'original', max: 'original', minRange: 1 },
            y: { min: 0, max: 'original', minRange: 0.1 }
          },
          zoom: {
            wheel: {
              enabled: true,
              speed: 0.1
            },
            pinch: {
              enabled: true
            },
            drag: {
              enabled: false
            },
            mode: 'xy'
          },
          pan: {
            enabled: true,
            mode: 'xy'
          }
        },
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.dataset.label || '';
              return `${label}: Step ${context.parsed.x.toFixed(0)} → Density ${context.parsed.y.toFixed(3)}`;
            }
          }
        }
      },
      onClick: (event, elements, chart) => {
        // ダブルクリック検出
        const now = Date.now();
        const lastClick = chart._lastClickTime || 0;

        if (now - lastClick < 300) {
          chart.resetZoom();
        }

        chart._lastClickTime = now;
      }
    }
  });
}

/**
 * 理想的な直線を計算（最小二乗法）
 */
function calculateIdealLine(data) {
  const n = data.length;
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;

  for (const point of data) {
    sumX += point.step;
    sumY += point.density;
    sumXY += point.step * point.density;
    sumX2 += point.step * point.step;
  }

  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  const minStep = Math.min(...data.map(d => d.step));
  const maxStep = Math.max(...data.map(d => d.step));

  return [
    { x: minStep, y: slope * minStep + intercept },
    { x: maxStep, y: slope * maxStep + intercept }
  ];
}

/**
 * 逆補正カーブを生成
 */
function generateCorrectionCurve(data) {
  // 256ポイントの補正カーブを生成
  const curve = [];
  const minStep = Math.min(...data.map(d => d.step));
  const maxStep = Math.max(...data.map(d => d.step));
  const minDensity = Math.min(...data.map(d => d.density));
  const maxDensity = Math.max(...data.map(d => d.density));

  // 理想的な直線の傾きと切片
  const idealSlope = (maxDensity - minDensity) / (maxStep - minStep);
  const idealIntercept = minDensity - idealSlope * minStep;

  for (let i = 0; i <= 255; i++) {
    // 入力値を正規化（0-1）
    const normalizedInput = i / 255;

    // 実際のステップ値にマッピング
    const actualStep = minStep + normalizedInput * (maxStep - minStep);

    // 理想的な濃度値
    const idealDensity = idealSlope * actualStep + idealIntercept;

    // 実測の濃度値（補間）
    const measuredDensity = interpolateDensity(data, actualStep);

    // 逆補正: 理想濃度に対応する実ステップを求める
    const correctedStep = inverseLookup(data, idealDensity);

    // 0-1に正規化
    const normalizedOutput = (correctedStep - minStep) / (maxStep - minStep);

    curve.push({
      input: normalizedInput,
      output: Math.max(0, Math.min(1, normalizedOutput))
    });
  }

  return curve;
}

/**
 * 濃度値を補間
 */
function interpolateDensity(data, step) {
  // ステップが範囲外の場合
  if (step <= data[0].step) return data[0].density;
  if (step >= data[data.length - 1].step) return data[data.length - 1].density;

  // 線形補間
  for (let i = 0; i < data.length - 1; i++) {
    if (step >= data[i].step && step <= data[i + 1].step) {
      const ratio = (step - data[i].step) / (data[i + 1].step - data[i].step);
      return data[i].density + ratio * (data[i + 1].density - data[i].density);
    }
  }

  return data[data.length - 1].density;
}

/**
 * 濃度値から対応するステップを逆引き
 */
function inverseLookup(data, targetDensity) {
  // 濃度が範囲外の場合
  if (targetDensity <= data[0].density) return data[0].step;
  if (targetDensity >= data[data.length - 1].density) return data[data.length - 1].step;

  // 線形補間
  for (let i = 0; i < data.length - 1; i++) {
    const d1 = data[i].density;
    const d2 = data[i + 1].density;

    if ((targetDensity >= d1 && targetDensity <= d2) || (targetDensity >= d2 && targetDensity <= d1)) {
      const ratio = (targetDensity - d1) / (d2 - d1);
      return data[i].step + ratio * (data[i + 1].step - data[i].step);
    }
  }

  return data[data.length - 1].step;
}

/**
 * 補正カーブグラフを描画
 */
function renderCorrectionCurve(curve) {
  const ctx = document.getElementById('correctionChart');

  // 既存のグラフを破棄
  if (correctionChartInstance) {
    correctionChartInstance.destroy();
  }

  // データポイント
  const dataPoints = curve.map(c => ({ x: c.input, y: c.output }));

  // 理想線（y=x）
  const idealLine = [{ x: 0, y: 0 }, { x: 1, y: 1 }];

  correctionChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [
        {
          label: '理想線（y=x）',
          data: idealLine,
          borderColor: 'rgba(0, 0, 0, 0.5)',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointRadius: 0
        },
        {
          label: '逆補正カーブ',
          data: dataPoints,
          borderColor: 'rgba(54, 162, 235, 0.8)',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: 'linear',
          title: {
            display: true,
            text: '入力（正規化: 0-1）',
            font: { size: 14 }
          },
          min: 0,
          max: 1,
          grid: {
            color: 'rgba(128, 128, 128, 0.2)'
          }
        },
        y: {
          type: 'linear',
          title: {
            display: true,
            text: '出力（正規化: 0-1）',
            font: { size: 14 }
          },
          min: 0,
          max: 1,
          grid: {
            color: 'rgba(128, 128, 128, 0.2)'
          }
        }
      },
      plugins: {
        zoom: {
          limits: {
            x: { min: 0, max: 1, minRange: 0.05 },
            y: { min: 0, max: 1, minRange: 0.05 }
          },
          zoom: {
            wheel: {
              enabled: true,
              speed: 0.1
            },
            pinch: {
              enabled: true
            },
            drag: {
              enabled: false
            },
            mode: 'xy'
          },
          pan: {
            enabled: true,
            mode: 'xy'
          }
        },
        legend: {
          display: true,
          position: 'top'
        }
      },
      onClick: (event, elements, chart) => {
        const now = Date.now();
        const lastClick = chart._lastClickTime || 0;

        if (now - lastClick < 300) {
          chart.resetZoom();
        }

        chart._lastClickTime = now;
      }
    }
  });
}

/**
 * 分析結果を表示
 */
function displayAnalysis(data, curve) {
  // 基本統計
  const pointCount = data.length;
  const dmax = Math.max(...data.map(d => d.density));

  // 線形性スコア計算（R²決定係数）
  const rSquared = calculateRSquared(data);
  const linearityScore = (rSquared * 100).toFixed(1);

  // 補正必要性判定
  let correctionNeed = '不要';
  if (rSquared < 0.95) {
    correctionNeed = '強く推奨';
  } else if (rSquared < 0.98) {
    correctionNeed = '推奨';
  } else if (rSquared < 0.995) {
    correctionNeed = '軽微';
  }

  // 表示
  document.getElementById('pointCount').textContent = pointCount;
  document.getElementById('dmaxValue').textContent = dmax.toFixed(3);
  document.getElementById('linearityScore').textContent = `${linearityScore}%`;
  document.getElementById('correctionNeed').textContent = correctionNeed;

  // 推奨事項
  const recommendations = [];

  if (rSquared >= 0.995) {
    recommendations.push({
      type: 'success',
      message: '優れた線形性です。補正なしでも高品質なプリントが可能です。'
    });
  } else if (rSquared >= 0.98) {
    recommendations.push({
      type: 'info',
      message: '線形性は良好ですが、より高精度を求める場合は補正LUTの使用を推奨します。'
    });
  } else if (rSquared >= 0.95) {
    recommendations.push({
      type: 'warning',
      message: '中程度の非線形性が検出されました。補正LUTの使用を推奨します。'
    });
  } else {
    recommendations.push({
      type: 'error',
      message: '顕著な非線形性が検出されました。補正LUTの使用を強く推奨します。'
    });
  }

  if (pointCount < 10) {
    recommendations.push({
      type: 'info',
      message: `測定ポイント数が少なめです（${pointCount}点）。より高精度な補正には15-21点の測定を推奨します。'`
    });
  }

  // 推奨事項を表示
  const recContainer = document.getElementById('recommendations');
  recContainer.innerHTML = '<h3>推奨事項</h3>';

  recommendations.forEach(rec => {
    const div = document.createElement('div');
    div.className = `recommendation ${rec.type}`;
    div.textContent = rec.message;
    recContainer.appendChild(div);
  });
}

/**
 * R²決定係数を計算
 */
function calculateRSquared(data) {
  const n = data.length;
  const meanY = data.reduce((sum, d) => sum + d.density, 0) / n;

  // 理想線（最小二乗法）
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
  for (const point of data) {
    sumX += point.step;
    sumY += point.density;
    sumXY += point.step * point.density;
    sumX2 += point.step * point.step;
  }

  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  // SST（全変動）とSSR（回帰変動）
  let sst = 0, ssr = 0;
  for (const point of data) {
    const predicted = slope * point.step + intercept;
    sst += Math.pow(point.density - meanY, 2);
    ssr += Math.pow(predicted - meanY, 2);
  }

  return ssr / sst;
}

/**
 * LUTファイルをダウンロード
 */
function downloadLUT(points) {
  if (!correctionCurve) {
    showStatus('補正カーブが生成されていません', 'error');
    return;
  }

  // 0-1正規化カーブを取得
  const normalizedCurve = correctionCurve.map(c => c.output);

  const metadata = {
    paperName: 'Densitometer Measurement',
    dmax: Math.max(...currentData.map(d => d.density)),
    date: new Date().toISOString().split('T')[0],
    interpolation: 'linear'
  };

  const cubeContent = ExportManager.generateCube1D(normalizedCurve, points, metadata);
  const filename = `precision-edn-densitometer-${points}pt.cube`;

  ExportManager.downloadFile(filename, cubeContent, 'text/plain');
  showStatus(`${filename} をダウンロードしました`, 'success');
}

/**
 * CSVダウンロード
 */
function downloadCSV() {
  if (!currentData) {
    showStatus('データがありません', 'error');
    return;
  }

  let csv = 'Step,Density,Corrected\n';

  for (const point of currentData) {
    const correctedValue = correctionCurve[Math.round(point.step / currentData.length * 255)]?.output || 0;
    csv += `${point.step},${point.density.toFixed(4)},${correctedValue.toFixed(6)}\n`;
  }

  ExportManager.downloadFile('densitometer-data.csv', csv, 'text/csv');
  showStatus('CSVファイルをダウンロードしました', 'success');
}

/**
 * 測定メモをダウンロード
 */
function downloadNote() {
  if (!currentData) {
    showStatus('データがありません', 'error');
    return;
  }

  const now = new Date();
  const dateStr = now.toLocaleString('ja-JP');

  let note = '';
  note += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
  note += 'Precision EDN - Densitometer Edition\n';
  note += '濃度計測定データ 分析レポート\n';
  note += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n';

  note += `作成日時: ${dateStr}\n`;
  note += `測定ポイント数: ${currentData.length}\n`;
  note += `最大濃度 (Dmax): ${Math.max(...currentData.map(d => d.density)).toFixed(3)}\n`;
  note += `線形性スコア (R²): ${(calculateRSquared(currentData) * 100).toFixed(1)}%\n\n`;

  note += '【測定データ】\n';
  for (const point of currentData) {
    note += `Step ${String(point.step).padStart(3)} → Density ${point.density.toFixed(4)}\n`;
  }

  note += '\n【補正カーブ情報】\n';
  note += `- 補正ポイント数: 256\n`;
  note += `- 補正方法: 逆補正カーブ（線形化）\n`;
  note += `- 出力形式: .cube LUT (1D)\n\n`;

  note += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';

  ExportManager.downloadFile('densitometer-report.txt', note, 'text/plain');
  showStatus('測定メモをダウンロードしました', 'success');
}

/**
 * ステータスメッセージを表示
 */
function showStatus(message, type = 'info') {
  const statusEl = document.getElementById('status');
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  statusEl.style.display = 'block';

  setTimeout(() => {
    statusEl.style.display = 'none';
  }, 5000);
}

/**
 * ダークモード切り替え
 */
function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  const isDark = document.body.classList.contains('dark-mode');

  localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');

  document.getElementById('darkModeToggle').textContent = isDark ? '☀️ ライトモード' : '🌙 ダークモード';
}

/**
 * ダークモード設定を読み込み
 */
function loadDarkModePreference() {
  const darkMode = localStorage.getItem('darkMode');

  if (darkMode === 'enabled') {
    document.body.classList.add('dark-mode');
    document.getElementById('darkModeToggle').textContent = '☀️ ライトモード';
  }
}

/**
 * EDN RGB256チャートの読み込み順序を正しい値順に変換
 *
 * EDN RGB256チャートは右→左（値0→240）の配置だが、
 * 測定時に左→右で読み込んでしまった場合に、正しい順序に並び替える
 *
 * チャート配置:
 * 1行目: 右(0)→左(240)  = 16列 × 16段階 = 値 0,16,32,...,240
 * 2行目: 右(1)→左(241)  = 値 1,17,33,...,241
 * ...
 * 16行目: 右(15)→左(255) = 値 15,31,47,...,255
 *
 * @param {Array} data - [{step: number, density: number}, ...]
 * @returns {Array} 正しい値順に並び替えたデータ
 */
function convertEdnRgb256Order(data) {
  // 256ステップでない場合は警告
  if (data.length !== 256) {
    console.warn(`EDN RGB256は256ステップですが、${data.length}ステップのデータが入力されました`);
    // 256でない場合はそのまま返す
    return data;
  }

  // 新しい配列を作成（値順、0-255）
  const reorderedData = new Array(256);

  // EDN RGB256の配置ルール:
  // 値 = 行番号(0-15) + 列番号(0-15) × 16
  //
  // 左→右で測定した場合の入力順序:
  // 入力インデックス = 行番号 × 16 + (15 - 列番号)
  // つまり:
  //   1行目左端(列15,値240) = 入力インデックス0
  //   1行目左から2(列14,値224) = 入力インデックス1
  //   ...
  //   1行目右端(列0,値0) = 入力インデックス15
  //   2行目左端(列15,値241) = 入力インデックス16
  //   ...

  for (let inputIdx = 0; inputIdx < 256; inputIdx++) {
    // 入力インデックスから行と列を計算（左→右の測定順）
    const row = Math.floor(inputIdx / 16);          // 行番号(0-15)
    const posInRow = inputIdx % 16;                 // 行内位置(0-15)
    const col = 15 - posInRow;                      // 列番号(15→0, 左→右)

    // 実際の値を計算
    const actualValue = row + col * 16;             // 値(0-255)

    // データを正しい位置に配置
    reorderedData[actualValue] = {
      step: actualValue + 1,                        // ステップ番号（1始まり）
      density: data[inputIdx].density,              // 濃度値
      originalStep: inputIdx + 1                    // 元の入力順序（デバッグ用）
    };
  }

  return reorderedData;
}
