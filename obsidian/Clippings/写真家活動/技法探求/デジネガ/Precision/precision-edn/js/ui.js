/**
 * Precision EDN - UI制御
 * グラフ表示、ユーザーインタラクション
 */

class UIController {
  constructor() {
    this.edn = new PrecisionEDN();
    this.chart = null;
    this.uploadedFiles = [];
    this.currentPaper = this.loadPaperSettings();
    this.analysisResult = null;
    this.lut1Curve = null;  // 1次補正LUT
    this.lut2Curve = null;  // 2次補正LUT
    this.editableLUT = null;  // 編集可能なLUT
    this.originalLUT = null;  // オリジナルLUT（リセット用）
    this.linearityDisplayMode = 'rgb';  // 'rgb' or 'normalized'
    this.curveDisplayMode = 'normalized';  // 'normalized' or 'digital'
    this.individualRgbNormalized = [];  // 個別ファイルのRGB正規化データ
    this.fileNames = [];  // ファイル名
  }

  /**
   * 初期化
   */
  init() {
    this.initializePresetPapers();
    this.setupEventListeners();
    this.loadSettings();
    this.updatePaperSelect();
    this.updateUI();
  }

  /**
   * イベントリスナーを設定
   */
  setupEventListeners() {
    // グラフタブ切り替え
    document.querySelectorAll('.chart-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const chartType = e.target.dataset.chart;
        this.switchChartTab(chartType);
      });
    });

    // モード選択
    document.getElementById('modeSelect')?.addEventListener('change', (e) => {
      this.edn.settings.mode = e.target.value;
      this.updateModeDescription();
      this.saveSettings();
    });

    // ファイルアップロード
    const fileInput = document.getElementById('fileInput');
    const fileInputLUT1 = document.getElementById('fileInputLUT1');
    const fileInputLUT2 = document.getElementById('fileInputLUT2');
    const dropZone = document.getElementById('dropZone');

    if (fileInput) {
      fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
    }

    if (fileInputLUT1) {
      fileInputLUT1.addEventListener('change', (e) => this.handleLUTFileSelect(e, 'lut1'));
    }

    if (fileInputLUT2) {
      fileInputLUT2.addEventListener('change', (e) => this.handleLUTFileSelect(e, 'lut2'));
    }

    if (dropZone) {
      // ドラッグ&ドロップ
      dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
      });

      dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
      });

      dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        this.handleFileSelect(e);
      });

      dropZone.addEventListener('click', () => {
        fileInput.click();
      });
    }

    // 設定変更
    document.getElementById('samplingPoints')?.addEventListener('change', (e) => {
      this.edn.settings.samplingPoints = parseInt(e.target.value);
      this.saveSettings();
      if (this.uploadedFiles.length > 0) {
        this.processFiles();
      }
    });

    document.getElementById('interpolation')?.addEventListener('change', (e) => {
      this.edn.settings.interpolation = e.target.value;
      this.saveSettings();
      if (this.uploadedFiles.length > 0) {
        this.processFiles();
      }
    });


    // グラフ表示モード切り替え
    document.getElementById('linearityDisplayMode')?.addEventListener('change', (e) => {
      this.linearityDisplayMode = e.target.value;
      this.saveSettings();
      if (this.edn.curve) {
        this.updateChart(this.edn.curve, this.edn.curve.raw, this.individualRgbNormalized, this.fileNames);
      }
    });

    document.getElementById('curveDisplayMode')?.addEventListener('change', (e) => {
      this.curveDisplayMode = e.target.value;
      this.saveSettings();
      if (this.edn.curve) {
        this.updateChart(this.edn.curve, this.edn.curve.raw, this.individualRgbNormalized, this.fileNames);
      }
    });

    // 用紙管理
    document.getElementById('paperSelect')?.addEventListener('change', (e) => {
      this.loadPaper(e.target.value);
    });

    document.getElementById('addPaper')?.addEventListener('click', () => {
      this.showAddPaperDialog();
    });

    // 薬品調合情報
    ['chemFO', 'chemPd', 'chemPt', 'chemNa2', 'chemTween'].forEach(id => {
      document.getElementById(id)?.addEventListener('change', (e) => {
        this.updateChemicalValue(id, parseFloat(e.target.value) || 0);
      });
    });

    // LUT結合用ファイル選択
    document.getElementById('fileInputLUT1')?.addEventListener('change', (e) => {
      this.handleLUTFileSelect(e, 'lut1');
    });

    document.getElementById('fileInputLUT2')?.addEventListener('change', (e) => {
      this.handleLUTFileSelect(e, 'lut2');
    });

    // LUT結合ボタン
    document.getElementById('combineLUTsBtn')?.addEventListener('click', () => {
      this.combineLUTs();
    });

    // LUT編集用ファイル選択
    document.getElementById('fileInputLUTEdit')?.addEventListener('change', (e) => {
      this.loadLUTForEditing(e);
    });

    // LUT編集用ドロップゾーン
    const lutDropZone = document.getElementById('lutDropZone');
    if (lutDropZone) {
      lutDropZone.addEventListener('click', (e) => {
        // ファイルステータス以外の領域をクリックした場合のみファイル選択を開く
        if (e.target.id !== 'lutEditFileStatus') {
          document.getElementById('fileInputLUTEdit').click();
        }
      });

      lutDropZone.addEventListener('dragenter', (e) => {
        e.preventDefault();
        e.stopPropagation();
        lutDropZone.classList.add('dragover');
      });

      lutDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
      });

      lutDropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        // ドロップゾーンの外に出た場合のみクラスを削除
        if (e.target === lutDropZone) {
          lutDropZone.classList.remove('dragover');
        }
      });

      lutDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        lutDropZone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].name.endsWith('.cube')) {
          this.loadLUTForEditingFromDrop(files[0]);
        } else {
          this.showStatus('.cubeファイルをドロップしてください', 'error');
        }
      });
    }

    // プリントスキャンデータ編集用ドロップゾーン
    const scanDropZone = document.getElementById('scanDropZone');
    const fileInputScanEdit = document.getElementById('fileInputScanEdit');
    if (scanDropZone && fileInputScanEdit) {
      scanDropZone.addEventListener('click', (e) => {
        if (e.target.id !== 'scanEditFileStatus') {
          fileInputScanEdit.click();
        }
      });

      scanDropZone.addEventListener('dragenter', (e) => {
        e.preventDefault();
        e.stopPropagation();
        scanDropZone.classList.add('dragover');
      });

      scanDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
      });

      scanDropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.target === scanDropZone) {
          scanDropZone.classList.remove('dragover');
        }
      });

      scanDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        scanDropZone.classList.remove('dragover');
        this.handleScanDataForManualEdit(e.dataTransfer.files);
      });

      fileInputScanEdit.addEventListener('change', (e) => {
        this.handleScanDataForManualEdit(e.target.files);
      });
    }

    // LUT編集ボタン
    document.getElementById('showLUTEditor')?.addEventListener('click', () => {
      this.toggleLUTEditor();
    });

    document.getElementById('resetLUTBtn')?.addEventListener('click', () => {
      this.resetLUT();
    });

    document.getElementById('lutEditRange')?.addEventListener('change', () => {
      this.updateLUTEditorTable();
    });

    // ダウンロードボタン
    document.getElementById('downloadCube1D')?.addEventListener('click', () => {
      this.downloadCube1D();
    });

    document.getElementById('downloadCube3D')?.addEventListener('click', () => {
      this.downloadCube3D();
    });

    document.getElementById('downloadACV')?.addEventListener('click', () => {
      this.downloadACV();
    });

    document.getElementById('downloadReportPDF')?.addEventListener('click', () => {
      this.downloadReportPDF();
    });

    document.getElementById('downloadAll')?.addEventListener('click', () => {
      this.downloadAll();
    });

    // ダークモード切り替え
    document.getElementById('darkModeToggle')?.addEventListener('click', () => {
      this.toggleDarkMode();
    });
  }

  /**
   * モード説明を更新
   */
  updateModeDescription() {
    const mode = this.edn.settings.mode;
    const desc = document.getElementById('modeDescription');
    if (!desc) return;

    const descriptions = {
      'first_correction': '【1次補正】デジネガでプリントした結果をスキャンして、初回の補正LUTを作成します。',
      'second_correction': '【2次補正】1次補正を適用したデジネガでプリントした結果をスキャンして、微調整LUTを作成します。',
      'combine_luts': '【LUT結合】1次補正LUTと2次補正LUTを結合して、最終的な補正LUTを作成します。',
      'manual_edit': '【手動補正】保存済みのLUTファイルを読み込んで、数値を手動で微調整します。'
    };

    desc.textContent = descriptions[mode] || '';

    // UI表示切り替え
    const imageUploadSection = document.getElementById('imageUploadSection');
    const lutCombineSection = document.getElementById('lutCombineSection');
    const lutEditSection = document.getElementById('lutEditSection');

    if (mode === 'combine_luts') {
      imageUploadSection.style.display = 'none';
      lutCombineSection.style.display = 'block';
      lutEditSection.style.display = 'none';
    } else if (mode === 'manual_edit') {
      imageUploadSection.style.display = 'none';
      lutCombineSection.style.display = 'none';
      lutEditSection.style.display = 'block';
    } else {
      imageUploadSection.style.display = 'block';
      lutCombineSection.style.display = 'none';
      lutEditSection.style.display = 'none';
    }
  }

  /**
   * LUTファイル選択処理
   */
  async handleLUTFileSelect(e, lutType) {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const content = await this.readFileAsText(file);
      const curve = ExportManager.parseCubeFile(content);

      if (lutType === 'lut1') {
        this.lut1Curve = curve;
        document.getElementById('lut1Status').textContent = `✓ ${file.name} (${curve.length}ポイント)`;
      } else {
        this.lut2Curve = curve;
        document.getElementById('lut2Status').textContent = `✓ ${file.name} (${curve.length}ポイント)`;
      }

      // 両方読み込まれたら結合ボタンを有効化
      if (this.lut1Curve && this.lut2Curve) {
        document.getElementById('combineLUTsBtn').disabled = false;
      }
    } catch (error) {
      this.showStatus(`エラー: ${error.message}`, 'error');
    }
  }

  /**
   * LUT結合処理
   */
  async combineLUTs() {
    if (!this.lut1Curve || !this.lut2Curve) {
      this.showStatus('両方のLUTファイルを選択してください', 'error');
      return;
    }

    try {
      this.showStatus('LUTを結合中...', 'info');

      const combined = ExportManager.combineLUTs(this.lut1Curve, this.lut2Curve);

      // 結合結果をカーブとして設定
      this.edn.curve = {
        raw: this.lut1Curve,
        ideal: this.lut2Curve,
        interpolated: combined,
        points: combined.length
      };

      // グラフ更新
      this.updateChart(this.edn.curve, this.lut1Curve);

      this.showStatus('LUT結合完了！「LUT手動編集」セクションで結合済みLUTをダウンロード、または読み込んで微調整できます。', 'success');
      this.enableDownloadButtons();
    } catch (error) {
      this.showStatus(`エラー: ${error.message}`, 'error');
      console.error(error);
    }
  }

  /**
   * ファイルをテキストとして読み込み
   */
  readFileAsText(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => reject(new Error('ファイル読み込みエラー'));
      reader.readAsText(file);
    });
  }

  /**
   * LUTファイルを読み込んで編集可能にする
   */
  async loadLUTForEditing(e) {
    const file = e.target.files[0];
    if (!file) return;
    await this.processLUTFile(file);
  }

  /**
   * ドロップされたLUTファイルを読み込んで編集可能にする
   */
  async loadLUTForEditingFromDrop(file) {
    await this.processLUTFile(file);
  }

  /**
   * LUTファイルを処理する共通メソッド
   */
  async processLUTFile(file) {
    try {
      this.showStatus('LUTファイルを読み込み中...', 'info');

      const content = await this.readFileAsText(file);
      const curve = ExportManager.parseCubeFile(content);

      if (!curve || curve.length === 0) {
        throw new Error('LUTファイルの解析に失敗しました');
      }

      // 編集可能なLUTとして保存
      this.editableLUT = [...curve];  // コピーを作成
      this.originalLUT = [...curve];  // リセット用にオリジナルを保存

      // カーブとして設定（グラフ表示用）
      this.edn.curve = {
        raw: curve,
        ideal: curve,
        interpolated: curve,
        points: curve.length
      };

      // グラフ更新（測定値はまだないのでnull）
      this.updateChart(this.edn.curve, null);

      // ファイル名を表示
      document.getElementById('lutEditFileStatus').textContent = `✓ ${file.name} (${curve.length}ポイント)`;

      // 編集コントロールを表示
      document.getElementById('lutEditControls').style.display = 'block';

      this.showStatus(`LUT読み込み完了！プリントスキャンデータも読み込むとリニアリティ検証ができます。`, 'success');
      this.enableDownloadButtons();
    } catch (error) {
      this.showStatus(`エラー: ${error.message}`, 'error');
      console.error(error);
    }
  }

  /**
   * 手動補正モード用のスキャンデータ処理
   */
  async handleScanDataForManualEdit(files) {
    if (!this.editableLUT) {
      this.showStatus('先にLUTファイルを読み込んでください', 'warning');
      return;
    }

    if (files.length === 0) {
      return;
    }

    try {
      this.showStatus(`${files.length}ファイルを読み込み中...`, 'info');

      const measurementsList = [];
      const fileNames = [];

      // 各ファイルを読み込み
      for (const file of files) {
        try {
          const result = await this.edn.loadImage(file);
          measurementsList.push(result.measurements);
          fileNames.push(file.name);
        } catch (error) {
          throw new Error(`${file.name}: ${error.message}`);
        }
      }

      // ファイル名を表示
      document.getElementById('scanEditFileStatus').textContent = `✓ ${files.length}ファイル`;

      // 平均化された測定値を取得
      const avgMeasurements = measurementsList.length > 1
        ? this.edn.averageMultipleMeasurements(measurementsList)
        : measurementsList[0];

      const normalized = this.edn.normalizeMeasurements(avgMeasurements);

      // 個別ファイルの正規化測定値を保存
      const normalizedList = measurementsList.map(m => this.edn.normalizeMeasurements(m));

      // グラフ表示用とMAE計算用: RGB値をそのまま正規化（反転なし）
      const rgbNormalized = this.edn.normalizeRgbForGraph(avgMeasurements);
      const rgbNormalizedList = measurementsList.map(m => this.edn.normalizeRgbForGraph(m));

      // Dmaxを計算
      const dmax = this.edn.calculateDmax(measurementsList[0]);

      // 分析（editableLUTを補正カーブとして使用、MAE計算にはRGB値を使用）
      this.analysisResult = Analysis.generateReport({
        measured: rgbNormalized,  // RGB値（反転なし）を使用
        ideal: this.editableLUT,  // LUTを理想値として扱う
        curve: this.editableLUT,
        measurementsList: measurementsList.length > 1 ? rgbNormalizedList : null,
        dmax: dmax,
        mode: 'manual_edit'
      });

      // 個別データを保存（グラフ更新時に使用）
      this.individualRgbNormalized = rgbNormalizedList;
      this.fileNames = fileNames;

      // UI更新
      this.updateAnalysisDisplay();

      // グラフ更新（LUTと測定値を両方表示）
      this.updateChart(this.edn.curve, normalized, rgbNormalizedList, fileNames);

      this.showStatus('スキャンデータ読み込み完了！リニアリティ検証でズレを確認できます。', 'success');
    } catch (error) {
      this.showStatus(`エラー: ${error.message}`, 'error');
      console.error(error);
    }
  }

  /**
   * ファイル選択処理
   */
  async handleFileSelect(e) {
    e.preventDefault();

    const files = e.dataTransfer ? e.dataTransfer.files : e.target.files;

    if (files.length === 0) {
      return;
    }

    this.uploadedFiles = Array.from(files);
    this.showStatus(`${files.length}ファイルを読み込み中...`, 'info');

    try {
      await this.processFiles();
      this.showStatus('処理完了！', 'success');
    } catch (error) {
      this.showStatus(`エラー: ${error.message}`, 'error');
      console.error(error);
    }
  }

  /**
   * ファイルを処理
   */
  async processFiles() {
    const measurementsList = [];
    const fileNames = [];

    // 各ファイルを読み込み
    for (const file of this.uploadedFiles) {
      try {
        const result = await this.edn.loadImage(file);
        measurementsList.push(result.measurements);
        fileNames.push(file.name);
      } catch (error) {
        throw new Error(`${file.name}: ${error.message}`);
      }
    }

    // カーブを生成
    const curve = this.edn.generateLinearizationCurve(measurementsList);
    const dmax = this.edn.calculateDmax(measurementsList[0]);

    // 平均化された測定値を取得
    const avgMeasurements = measurementsList.length > 1
      ? this.edn.averageMultipleMeasurements(measurementsList)
      : measurementsList[0];

    const normalized = this.edn.normalizeMeasurements(avgMeasurements);

    // 個別ファイルの正規化測定値を保存
    const normalizedList = measurementsList.map(m => this.edn.normalizeMeasurements(m));

    // グラフ表示用とMAE計算用: RGB値をそのまま正規化（反転なし）
    const rgbNormalized = this.edn.normalizeRgbForGraph(avgMeasurements);
    const rgbNormalizedList = measurementsList.map(m => this.edn.normalizeRgbForGraph(m));

    // 分析（MAE計算にはRGB値を使用）
    this.analysisResult = Analysis.generateReport({
      measured: rgbNormalized,  // RGB値（反転なし）を使用
      ideal: curve.ideal,
      curve: curve.interpolated,
      measurementsList: measurementsList.length > 1 ? rgbNormalizedList : null,
      dmax: dmax,
      mode: this.edn.settings.mode
    });

    // 個別データを保存（グラフ更新時に使用）
    this.individualRgbNormalized = rgbNormalizedList;
    this.fileNames = fileNames;

    // UI更新
    this.updateAnalysisDisplay();
    this.updateChart(curve, normalized, rgbNormalizedList, fileNames);
    this.enableDownloadButtons();
  }

  /**
   * 分析結果を表示
   */
  updateAnalysisDisplay() {
    const result = this.analysisResult;

    // サマリー
    document.getElementById('dmaxValue').textContent = result.summary.dmax;
    document.getElementById('maeValue').textContent = result.summary.mae;
    document.getElementById('rmseValue').textContent = result.summary.rmse;

    // 品質スコア
    document.getElementById('smoothnessScore').textContent = result.qualityScore.smoothness;
    document.getElementById('linearityScore').textContent = result.qualityScore.linearity;
    document.getElementById('precisionScore').textContent = result.qualityScore.precision;
    document.getElementById('overallScore').textContent = result.qualityScore.overall;
    document.getElementById('qualityRating').textContent = result.qualityScore.rating;

    // 品質評価に応じて色を変更
    const overallScore = parseFloat(result.qualityScore.overall);
    const scoreElement = document.getElementById('overallScore');
    if (overallScore >= 90) {
      scoreElement.className = 'score excellent';
    } else if (overallScore >= 80) {
      scoreElement.className = 'score good';
    } else if (overallScore >= 70) {
      scoreElement.className = 'score fair';
    } else {
      scoreElement.className = 'score poor';
    }

    // 推奨事項
    const recommendationsDiv = document.getElementById('recommendations');
    recommendationsDiv.innerHTML = '';

    result.recommendations.forEach(rec => {
      const div = document.createElement('div');
      div.className = `recommendation ${rec.type}`;
      div.textContent = rec.message;
      recommendationsDiv.appendChild(div);
    });

    // 問題領域
    if (result.problemRegions.length > 0) {
      const problemDiv = document.getElementById('problemRegions');
      problemDiv.innerHTML = '<h4>問題領域:</h4>';

      result.problemRegions.forEach(region => {
        const p = document.createElement('p');
        p.textContent = region.message;
        problemDiv.appendChild(p);
      });
    }
  }

  /**
   * タブを切り替え
   */
  switchChartTab(chartType) {
    // タブボタンのアクティブ状態を切り替え
    document.querySelectorAll('.chart-tab').forEach(tab => {
      if (tab.dataset.chart === chartType) {
        tab.classList.add('active');
      } else {
        tab.classList.remove('active');
      }
    });

    // グラフコンテナの表示を切り替え
    document.querySelectorAll('.chart-container').forEach(container => {
      container.classList.remove('active');
    });

    if (chartType === 'linearity') {
      document.getElementById('linearityChartContainer').classList.add('active');
    } else if (chartType === 'correction') {
      document.getElementById('curveChartContainer').classList.add('active');
    }
  }

  /**
   * グラフを更新（両方のグラフを更新）
   */
  updateChart(curve, measured, measurementsList = [], fileNames = []) {
    this.updateCorrectionChart(curve, measured);
    this.updateLinearityChart(curve, measured, measurementsList, fileNames);
  }

  /**
   * 補正カーブグラフを更新
   */
  updateCorrectionChart(curve, measured) {
    const ctx = document.getElementById('curveChart');
    if (!ctx) {
      console.error('curveChart要素が見つかりません');
      return;
    }

    // 既存のチャートを破棄
    if (this.correctionChart) {
      this.correctionChart.destroy();
    }

    // 表示モードに応じてスケールを決定
    const displayMode = this.curveDisplayMode || 'normalized';
    const scale = displayMode === 'normalized' ? 1 : 65535;

    // 軸ラベルを更新
    const xAxisLabel = displayMode === 'normalized' ? '入力 (0-1)' : '入力 (0-65535)';
    const yAxisLabel = displayMode === 'normalized' ? '出力 (0-1)' : '出力 (0-65535)';
    const xLabelElement = document.getElementById('curveXAxisLabel');
    const yLabelElement = document.getElementById('curveYAxisLabel');
    if (xLabelElement) {
      xLabelElement.textContent = xAxisLabel;
    }
    if (yLabelElement) {
      yLabelElement.textContent = yAxisLabel;
    }

    // データ準備
    // 理想線: y = x の直線（左下から右上）
    const idealData = curve.ideal.map((y, i) => ({
      x: (i / (curve.ideal.length - 1)) * scale,
      y: (i / (curve.ideal.length - 1)) * scale  // y = x
    }));

    // measuredがnullの場合は空配列を使用
    const measuredData = measured ? measured.map((y, i) => ({
      x: (i / (measured.length - 1)) * scale,
      y: y * scale
    })) : [];

    const interpolatedData = curve.interpolated.map((y, i) => ({
      x: (i / (curve.interpolated.length - 1)) * scale,
      y: y * scale
    }));

    // データセットを構築（測定値がある場合のみ追加）
    const datasets = [
      {
        label: '理想線（y=x）',
        data: idealData,
        borderColor: 'rgba(0, 0, 0, 0.7)',
        backgroundColor: 'transparent',
        borderWidth: 1.5,
        pointRadius: 0,
        order: 3
      }
    ];

    // 測定値がある場合のみ追加
    if (measuredData.length > 0) {
      datasets.push({
        label: '測定値平均（補正前）',
        data: measuredData,
        borderColor: 'rgba(255, 99, 132, 0.8)',
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: 'rgba(255, 99, 132, 1)',
        order: 2
      });
    }

    datasets.push({
      label: '補正カーブ（LUT）',
      data: interpolatedData,
      borderColor: 'rgba(75, 192, 192, 0.8)',
      backgroundColor: 'transparent',
      borderWidth: 2,
      pointRadius: 0,
      order: 1
    });

    // Chart.js設定（補正カーブグラフ）
    const isNormalized = displayMode === 'normalized';

    this.correctionChart = new Chart(ctx, {
      type: 'line',
      data: {
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'linear',
            title: {
              display: true,
              text: xAxisLabel
            },
            min: 0,
            max: scale,
            ticks: {
              stepSize: isNormalized ? 0.1 : 6553,
              callback: function(value) {
                return isNormalized ? value.toFixed(1) : Math.round(value);
              }
            }
          },
          y: {
            type: 'linear',
            title: {
              display: true,
              text: yAxisLabel
            },
            min: 0,
            max: scale,
            ticks: {
              stepSize: isNormalized ? 0.1 : 6553,
              callback: function(value) {
                return isNormalized ? value.toFixed(1) : Math.round(value);
              }
            }
          }
        },
        plugins: {
          zoom: {
            limits: {
              x: {min: 0, max: scale, minRange: isNormalized ? 0.05 : 3276},
              y: {min: 0, max: scale, minRange: isNormalized ? 0.05 : 3276}
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
            mode: 'index',
            intersect: false,
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                label += Math.round(context.parsed.y * 255);
                return label;
              }
            }
          }
        },
        onClick: (event, elements, chart) => {
          // ダブルクリック検出用のタイムスタンプ
          const now = Date.now();
          const lastClick = chart._lastClickTime || 0;

          if (now - lastClick < 300) {
            // ダブルクリック: ズームをリセット
            chart.resetZoom();
          }

          chart._lastClickTime = now;
        }
      }
    });
  }

  /**
   * リニアリティ検証グラフを更新（0-255スケール）
   */
  updateLinearityChart(curve, measured, measurementsList = [], fileNames = []) {
    const ctx = document.getElementById('linearityChart');
    if (!ctx) return;

    // 既存のチャートを破棄
    if (this.linearityChart) {
      this.linearityChart.destroy();
    }

    // 表示モードに応じてスケールを決定
    const displayMode = this.linearityDisplayMode || 'rgb';
    const yScale = displayMode === 'rgb' ? 255 : 1;

    // Y軸ラベルを更新
    const yAxisLabel = displayMode === 'rgb' ? 'RGB値 (0-255)' : '相対値 (0-1)';
    const labelElement = document.getElementById('linearityYAxisLabel');
    if (labelElement) {
      labelElement.textContent = yAxisLabel;
    }

    // データ準備（横軸=入力、縦軸=出力）
    // 理想線: y = x
    const idealData = [];
    for (let i = 0; i <= 255; i++) {
      idealData.push({ x: i, y: i * yScale / 255 });
    }

    // リニアリティ検証グラフ用のデータを取得
    // curve.rawRgb: RGB値をそのまま正規化（反転なし）
    const rgbData = curve.rawRgb || measured;

    // デバッグ: 測定データの最初の16要素を確認
    if (rgbData) {
      console.log('グラフ描画: rgbData配列の長さ=', rgbData.length);
      console.log('グラフ描画: rgbData[0-15]=', rgbData.slice(0, 16).map((v, i) => `[${i}]:${v.toFixed(3)}`));
    }

    // 測定値平均: 入力(x) = インデックス, 出力(y) = 測定RGB値（正規化、反転なし）
    // rgbDataがnullの場合は空配列を使用
    const measuredData = rgbData ? rgbData.map((measuredValue, i) => ({
      x: i,                                 // 入力: インデックス = 値 (0-255)
      y: measuredValue * yScale             // 出力: 測定されたRGB値（表示モードに応じたスケール）
    })) : [];

    // ファイル名を短縮する関数
    const truncateFileName = (fileName, maxLength = 20) => {
      if (fileName.length <= maxLength) return fileName;
      const ext = fileName.lastIndexOf('.') > 0 ? fileName.substring(fileName.lastIndexOf('.')) : '';
      const nameWithoutExt = ext ? fileName.substring(0, fileName.lastIndexOf('.')) : fileName;
      const truncated = nameWithoutExt.substring(0, maxLength - ext.length - 3) + '...';
      return truncated + ext;
    };

    // 個別ファイルのデータセットを作成
    const colors = [
      'rgba(80, 80, 80, 0.8)',       // K 70% (ダークグレー)
      'rgba(0, 180, 200, 0.8)',      // C 70% (ターコイズブルー)
      'rgba(220, 80, 180, 0.8)',     // M 70% (マゼンタ)
      'rgba(200, 180, 0, 0.8)',      // Y 70% (ゴールド)
      'rgba(0, 140, 140, 0.8)',      // CY 70% (ティール)
      'rgba(150, 80, 150, 0.8)',     // CM 70% (パープル)
      'rgba(160, 140, 60, 0.8)',     // MY 70% (オリーブ)
      'rgba(60, 120, 200, 0.8)'      // その他 (ブルー)
    ];

    const individualDatasets = measurementsList.map((fileMeasured, fileIndex) => {
      const dashPattern = [5 + fileIndex * 2, 3 + fileIndex * 2]; // [5,3], [7,5], [9,7]...
      const fullName = fileNames[fileIndex] || `ファイル${fileIndex + 1}`;
      const shortName = truncateFileName(fullName);
      const color = colors[fileIndex % colors.length];

      return {
        label: shortName,
        fullName: fullName, // ツールチップ用に完全なファイル名を保存
        data: fileMeasured.map((measuredValue, i) => ({
          x: i,                      // 入力: インデックス = 値 (0-255)
          y: measuredValue * yScale  // 出力: 表示モードに応じたスケール
        })),
        borderColor: color,
        backgroundColor: 'transparent',
        borderWidth: 1,
        borderDash: dashPattern,
        pointRadius: 0,
        order: 3 + fileIndex
      };
    });

    // データセットを構築（測定値がある場合のみ追加）
    const linearityDatasets = [
      {
        label: '理想線（y=x）',
        data: idealData,
        borderColor: 'rgba(0, 0, 0, 0.7)',
        backgroundColor: 'transparent',
        borderWidth: 1.5,
        pointRadius: 0,
        order: 2
      }
    ];

    // 測定値がある場合のみ追加
    if (measuredData.length > 0) {
      linearityDatasets.push({
        label: '測定値（平均）',
        data: measuredData,
        borderColor: 'rgba(255, 99, 132, 0.8)',
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 1,  // ドットサイズを小さく（3→1）
        pointBackgroundColor: 'rgba(255, 99, 132, 1)',
        order: 1
      });
    }

    // 個別ファイルのデータセットを追加
    linearityDatasets.push(...individualDatasets);

    // Chart.js設定（リニアリティ検証グラフ）
    const isRgbMode = displayMode === 'rgb';

    this.linearityChart = new Chart(ctx, {
      type: 'line',
      data: {
        datasets: linearityDatasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'linear',
            title: {
              display: true,
              text: '入力（デジタル値 0-255）'
            },
            min: 0,
            max: 255,
            ticks: {
              display: true,
              stepSize: 32,
              autoSkip: false,
              maxRotation: 0,
              minRotation: 0,
              callback: function(value) {
                return Math.round(value);
              }
            }
          },
          y: {
            type: 'linear',
            title: {
              display: true,
              text: isRgbMode ? '出力（RGB値 0-255）' : '出力（相対値 0-1）'
            },
            min: 0,
            max: yScale,
            ticks: {
              display: true,
              stepSize: isRgbMode ? 32 : 0.125,
              callback: function(value) {
                return isRgbMode ? Math.round(value) : value.toFixed(2);
              }
            }
          }
        },
        plugins: {
          zoom: {
            limits: {
              x: {min: 0, max: 255, minRange: 10},
              y: {min: 0, max: yScale, minRange: isRgbMode ? 10 : 0.04}
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
            position: 'top',
            labels: {
              generateLabels: function(chart) {
                const original = Chart.defaults.plugins.legend.labels.generateLabels;
                const labels = original.call(this, chart);

                // 各ラベルに完全なファイル名を title として追加
                labels.forEach((label, index) => {
                  const dataset = chart.data.datasets[index];
                  if (dataset.fullName) {
                    label.text = dataset.label + ' ⓘ';
                  }
                });

                return labels;
              }
            },
            onHover: function(event, legendItem, legend) {
              const chart = legend.chart;
              const dataset = chart.data.datasets[legendItem.datasetIndex];
              if (dataset.fullName) {
                chart.canvas.title = dataset.fullName;
              } else {
                chart.canvas.title = dataset.label;
              }
            },
            onLeave: function(event, legendItem, legend) {
              legend.chart.canvas.title = '';
            }
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: function(context) {
                let label = context.dataset.fullName || context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                label += Math.round(context.parsed.y);
                return label;
              }
            }
          }
        },
        onClick: (event, elements, chart) => {
          // ダブルクリック検出用のタイムスタンプ
          const now = Date.now();
          const lastClick = chart._lastClickTime || 0;

          if (now - lastClick < 300) {
            // ダブルクリック: ズームをリセット
            chart.resetZoom();
          }

          chart._lastClickTime = now;
        }
      }
    });
  }

  /**
   * ダウンロードボタンを有効化
   */
  enableDownloadButtons() {
    document.getElementById('downloadCube1D').disabled = false;
    document.getElementById('downloadCube3D').disabled = false;
    document.getElementById('downloadACV').disabled = false;
    document.getElementById('downloadReportPDF').disabled = false;
    document.getElementById('downloadAll').disabled = false;
  }

  /**
   * 1D LUTをダウンロード
   */
  downloadCube1D() {
    const points = this.edn.settings.samplingPoints;
    // 編集されたLUTがあればそれを使用、なければ元のカーブを使用
    const curve = this.editableLUT || this.edn.curve.interpolated;
    const metadata = this.getMetadata();

    const content = ExportManager.generateCube1D(curve, points, metadata);
    const filename = this.generateFilename('LUT_1D', 'cube');

    ExportManager.downloadFile(filename, content);
  }

  /**
   * 3D LUTをダウンロード
   */
  downloadCube3D() {
    const curve = this.editableLUT || this.edn.curve.interpolated;
    const metadata = this.getMetadata();

    const content = ExportManager.generateCube3D(curve, 21, metadata);
    const filename = this.generateFilename('Screen_Proof_3D', 'cube');

    ExportManager.downloadFile(filename, content);
  }

  /**
   * Adobe Curveをダウンロード
   */
  downloadACV() {
    const curve = this.editableLUT || this.edn.curve.interpolated;
    const content = ExportManager.generateACV(curve);
    const filename = this.generateFilename('Photoshop_Curve', 'acv');

    ExportManager.downloadFile(filename, content, 'application/octet-stream');
  }

  /**
   * PDFレポートをダウンロード
   */
  async downloadReportPDF() {
    if (!this.analysisResult) {
      alert('分析データがありません。まず測定ファイルをアップロードしてください。');
      return;
    }

    // グラフ画像を取得
    const chartImages = this.captureChartImages();

    // PDF生成
    const pdfBlob = await ReportGenerator.generatePDFReport(
      this.analysisResult,
      this.edn.settings,
      this.fileNames || [],
      chartImages
    );

    const filename = this.generateFilename('Analysis_Report', 'pdf');
    const url = URL.createObjectURL(pdfBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  /**
   * グラフ画像をキャプチャ
   * @returns {Object} {linearity: base64, correction: base64}
   */
  captureChartImages() {
    const images = {};

    try {
      // リニアリティ検証グラフ
      const linearityCanvas = document.getElementById('linearityChart');
      if (linearityCanvas) {
        images.linearity = linearityCanvas.toDataURL('image/png');
      }

      // 補正カーブグラフ
      const correctionCanvas = document.getElementById('curveChart');
      if (correctionCanvas) {
        images.correction = correctionCanvas.toDataURL('image/png');
      }
    } catch (error) {
      console.warn('グラフ画像のキャプチャに失敗しました:', error);
    }

    return images;
  }

  /**
   * 全ファイルをZIPでダウンロード
   */
  async downloadAll() {
    const curve = this.edn.curve.interpolated;
    const metadata = this.getMetadata();
    const settings = this.getSettings();

    const files = {};

    // 各種LUT
    files[this.generateFilename('LUT_1D_1024pt', 'cube')] =
      ExportManager.generateCube1D(curve, 1024, metadata);

    files[this.generateFilename('LUT_1D_256pt', 'cube')] =
      ExportManager.generateCube1D(curve, 256, metadata);

    files[this.generateFilename('LUT_1D_52pt', 'cube')] =
      ExportManager.generateCube1D(curve, 52, metadata);

    files[this.generateFilename('Screen_Proof_3D', 'cube')] =
      ExportManager.generateCube3D(curve, 21, metadata);

    files[this.generateFilename('Photoshop_Curve', 'acv')] =
      ExportManager.generateACV(curve);

    // 測定データCSV
    files[this.generateFilename('Measurement_Data', 'csv')] =
      ExportManager.generateCSV(this.edn.curve.raw, this.edn.curve.ideal);

    // 設定メモ
    files['設定メモ.txt'] =
      ExportManager.generateSettingsNote(settings, this.analysisResult);

    // 分析レポート (PDF)
    if (this.analysisResult) {
      const chartImages = this.captureChartImages();
      const pdfBlob = await ReportGenerator.generatePDFReport(
        this.analysisResult,
        settings,
        this.fileNames || [],
        chartImages
      );
      // BlobをBase64に変換してZIPに含める
      const pdfBase64 = await this.blobToBase64(pdfBlob);
      files[this.generateFilename('Analysis_Report', 'pdf')] = pdfBase64;
    }

    const zipFilename = this.generateFilename('Complete_Set', 'zip');

    await ExportManager.downloadZip(files, zipFilename);
  }

  /**
   * BlobをBase64に変換
   */
  blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * ファイル名を生成
   */
  generateFilename(type, ext) {
    const paper = this.currentPaper.name.replace(/\s+/g, '_');
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const interp = this.edn.settings.interpolation.toUpperCase();

    return `${paper}_${date}_${interp}_${type}.${ext}`;
  }

  /**
   * メタデータを取得
   */
  getMetadata() {
    return {
      paperName: this.currentPaper.name,
      dmax: this.analysisResult ? parseFloat(this.analysisResult.summary.dmax) : null,
      mae: this.analysisResult ? parseFloat(this.analysisResult.summary.mae) / 100 : null,
      date: new Date().toLocaleDateString('ja-JP'),
      interpolation: this.edn.settings.interpolation.toUpperCase()
    };
  }

  /**
   * 設定を取得
   */
  getSettings() {
    const settings = {
      paperName: this.currentPaper.name,
      printer: this.currentPaper.printer || '未設定',
      chartType: this.edn.settings.chartType,
      scanCount: this.uploadedFiles.length,
      samplingPoints: this.edn.settings.samplingPoints,
      interpolation: this.edn.settings.interpolation,
      bitDepth: this.edn.settings.bitDepth,
      notes: this.currentPaper.notes || ''
    };

    // 薬品調合情報を追加
    if (this.currentPaper.chemicals) {
      settings.chemicals = {
        FO: this.currentPaper.chemicals.FO || 0,
        Pd: this.currentPaper.chemicals.Pd || 0,
        Pt: this.currentPaper.chemicals.Pt || 0,
        Na2: this.currentPaper.chemicals.Na2 || 0,
        Tween: this.currentPaper.chemicals.Tween || 0
      };
    }

    return settings;
  }

  /**
   * ステータスメッセージを表示
   */
  showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('status');
    if (!statusDiv) return;

    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
    statusDiv.style.display = 'block';

    if (type === 'success' || type === 'info') {
      setTimeout(() => {
        statusDiv.style.display = 'none';
      }, 5000);
    }
  }

  /**
   * 用紙設定を読み込み
   */
  loadPaperSettings() {
    const saved = localStorage.getItem('precisionEDN_papers');
    if (saved) {
      const papers = JSON.parse(saved);
      const currentId = localStorage.getItem('precisionEDN_currentPaper') || 'default_paper';
      return papers[currentId] || papers['default_paper'] || this.getDefaultPaper();
    }
    return this.getDefaultPaper();
  }

  /**
   * デフォルト用紙設定
   */
  getDefaultPaper() {
    return {
      id: 'default_paper',
      name: 'デフォルト支持体',
      type: 'プリント支持体',
      printer: '',
      notes: 'プリント支持体を登録してください',
      chemicals: {
        FO: 0,
        Pd: 0,
        Pt: 0,
        Na2: 0,
        Tween: 0
      }
    };
  }

  /**
   * 初期プリセット用紙を取得
   */
  getPresetPapers() {
    return {
      'default_paper': this.getDefaultPaper(),
      'revia_platinum': {
        id: 'revia_platinum',
        name: 'レビア・プラチナ・ペーパー (320 g/m²)',
        type: 'プラチナプリント用紙',
        printer: '',
        notes: '320 g/m²',
        chemicals: {
          FO: 0,
          Pd: 0,
          Pt: 0,
          Na2: 0,
          Tween: 0
        }
      },
      'tosa_hakkin_2': {
        id: 'tosa_hakkin_2',
        name: '土佐白金紙 2号',
        type: 'プラチナプリント用紙',
        printer: '',
        notes: '土佐白金紙 2号',
        chemicals: {
          FO: 0,
          Pd: 0,
          Pt: 0,
          Na2: 0,
          Tween: 0
        }
      }
    };
  }

  /**
   * プリセット用紙を初期化
   */
  initializePresetPapers() {
    const saved = localStorage.getItem('precisionEDN_papers');
    if (!saved) {
      // 初回起動時のみプリセットを保存
      const presets = this.getPresetPapers();
      localStorage.setItem('precisionEDN_papers', JSON.stringify(presets));
    }
  }

  /**
   * 用紙を読み込み
   */
  loadPaper(paperId) {
    const saved = localStorage.getItem('precisionEDN_papers');
    if (saved) {
      const papers = JSON.parse(saved);
      this.currentPaper = papers[paperId] || this.getDefaultPaper();
      localStorage.setItem('precisionEDN_currentPaper', paperId);
      this.updateUI();
    }
  }

  /**
   * 用紙選択を更新
   */
  updatePaperSelect() {
    const select = document.getElementById('paperSelect');
    if (!select) return;

    const saved = localStorage.getItem('precisionEDN_papers');
    const papers = saved ? JSON.parse(saved) : { default_paper: this.getDefaultPaper() };

    select.innerHTML = '';
    for (const [id, paper] of Object.entries(papers)) {
      const option = document.createElement('option');
      option.value = id;
      option.textContent = paper.name;
      if (id === this.currentPaper.id) {
        option.selected = true;
      }
      select.appendChild(option);
    }
  }

  /**
   * UIを更新
   */
  updateUI() {
    document.getElementById('currentPaperName').textContent = this.currentPaper.name;

    // 薬品調合情報を更新
    if (this.currentPaper.chemicals) {
      document.getElementById('chemFO').value = this.currentPaper.chemicals.FO || 0;
      document.getElementById('chemPd').value = this.currentPaper.chemicals.Pd || 0;
      document.getElementById('chemPt').value = this.currentPaper.chemicals.Pt || 0;
      document.getElementById('chemNa2').value = this.currentPaper.chemicals.Na2 || 0;
      document.getElementById('chemTween').value = this.currentPaper.chemicals.Tween || 0;
    }
  }

  /**
   * 薬品調合値を更新
   */
  updateChemicalValue(fieldId, value) {
    const chemicalKey = fieldId.replace('chem', '');

    if (!this.currentPaper.chemicals) {
      this.currentPaper.chemicals = { FO: 0, Pd: 0, Pt: 0, Na2: 0, Tween: 0 };
    }

    this.currentPaper.chemicals[chemicalKey] = value;

    // LocalStorageに保存
    const saved = localStorage.getItem('precisionEDN_papers');
    const papers = saved ? JSON.parse(saved) : {};
    papers[this.currentPaper.id] = this.currentPaper;
    localStorage.setItem('precisionEDN_papers', JSON.stringify(papers));
  }

  /**
   * 設定を保存
   */
  saveSettings() {
    const settings = {
      ...this.edn.settings,
      linearityDisplayMode: this.linearityDisplayMode,
      curveDisplayMode: this.curveDisplayMode
    };
    localStorage.setItem('precisionEDN_settings', JSON.stringify(settings));
  }

  /**
   * 設定を読み込み
   */
  loadSettings() {
    const saved = localStorage.getItem('precisionEDN_settings');
    if (saved) {
      const settings = JSON.parse(saved);
      this.edn.settings = { ...this.edn.settings, ...settings };

      // グラフ表示モードを復元
      if (settings.linearityDisplayMode) {
        this.linearityDisplayMode = settings.linearityDisplayMode;
      }
      if (settings.curveDisplayMode) {
        this.curveDisplayMode = settings.curveDisplayMode;
      }

      // UIに反映
      document.getElementById('samplingPoints').value = this.edn.settings.samplingPoints;
      document.getElementById('interpolation').value = this.edn.settings.interpolation;
      if (document.getElementById('linearityDisplayMode')) {
        document.getElementById('linearityDisplayMode').value = this.linearityDisplayMode;
      }
      if (document.getElementById('curveDisplayMode')) {
        document.getElementById('curveDisplayMode').value = this.curveDisplayMode;
      }
    }
  }

  /**
   * ダークモード切り替え
   */
  toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('precisionEDN_darkMode', isDark);
  }

  /**
   * 用紙追加ダイアログを表示
   */
  showAddPaperDialog() {
    const name = prompt('プリント支持体名を入力してください:\n（例：コットマン水彩紙、イルフォード銀塩印画紙など）');
    if (!name) return;

    const id = name.toLowerCase().replace(/\s+/g, '_');
    const printer = prompt('プリンター名を入力してください（オプション）:', 'PX-1V');
    const notes = prompt('備考（オプション）:\n（例：露光時間、現像条件など）');

    // 薬品調合情報を入力
    const chemFO = parseFloat(prompt('FO (cc):', '0')) || 0;
    const chemPd = parseFloat(prompt('Pd (cc):', '0')) || 0;
    const chemPt = parseFloat(prompt('Pt (cc):', '0')) || 0;
    const chemNa2 = parseFloat(prompt('Na2 (cc):', '0')) || 0;
    const chemTween = parseFloat(prompt('Tween (drop):', '0')) || 0;

    const newPaper = {
      id: id,
      name: name,
      type: 'プリント支持体',
      printer: printer || '',
      notes: notes || '',
      chemicals: {
        FO: chemFO,
        Pd: chemPd,
        Pt: chemPt,
        Na2: chemNa2,
        Tween: chemTween
      }
    };

    const saved = localStorage.getItem('precisionEDN_papers');
    const papers = saved ? JSON.parse(saved) : {};
    papers[id] = newPaper;

    localStorage.setItem('precisionEDN_papers', JSON.stringify(papers));
    this.updatePaperSelect();
    this.loadPaper(id);
  }

  /**
   * LUT編集テーブルの表示/非表示を切り替え
   */
  toggleLUTEditor() {
    const container = document.getElementById('lutEditorContainer');
    const btn = document.getElementById('showLUTEditor');

    if (container.style.display === 'none') {
      container.style.display = 'block';
      btn.textContent = '📊 編集を閉じる';
      this.updateLUTEditorTable();
    } else {
      container.style.display = 'none';
      btn.textContent = '📊 LUT値を編集';
    }
  }

  /**
   * LUT編集テーブルを更新
   */
  updateLUTEditorTable() {
    if (!this.editableLUT) return;

    const tbody = document.getElementById('lutEditTableBody');
    const range = document.getElementById('lutEditRange').value;

    let startIdx = 0;
    let endIdx = this.editableLUT.length - 1;

    // 表示範囲を設定
    if (range !== 'all') {
      const [start, end] = range.split('-').map(Number);
      startIdx = Math.floor((start / 255) * (this.editableLUT.length - 1));
      endIdx = Math.floor((end / 255) * (this.editableLUT.length - 1));
    }

    tbody.innerHTML = '';

    for (let i = startIdx; i <= endIdx; i++) {
      const inputNorm = i / (this.editableLUT.length - 1);
      const input255 = Math.round(inputNorm * 255);
      const outputNorm = this.editableLUT[i];
      const output255 = Math.round(outputNorm * 255);

      const row = document.createElement('tr');
      row.style.borderBottom = '1px solid var(--border-color)';
      row.innerHTML = `
        <td style="padding: 6px; font-size: 11px;">${input255}</td>
        <td style="padding: 6px; font-size: 11px;">${inputNorm.toFixed(6)}</td>
        <td style="padding: 6px;">
          <input type="number"
                 class="lut-edit-input"
                 data-index="${i}"
                 value="${outputNorm.toFixed(6)}"
                 step="0.000001"
                 min="0"
                 max="1"
                 style="width: 100px; padding: 4px; font-size: 11px; border: 1px solid var(--border-color); border-radius: 3px;">
        </td>
        <td style="padding: 6px; font-size: 11px;">${output255}</td>
        <td style="padding: 6px; text-align: center;">
          <button class="lut-adjust-btn" data-index="${i}" data-action="decrease" style="padding: 2px 8px; margin: 0 2px; font-size: 11px;">−</button>
          <button class="lut-adjust-btn" data-index="${i}" data-action="increase" style="padding: 2px 8px; margin: 0 2px; font-size: 11px;">+</button>
        </td>
      `;

      tbody.appendChild(row);
    }

    // イベントリスナーを追加
    tbody.querySelectorAll('.lut-edit-input').forEach(input => {
      input.addEventListener('change', (e) => this.handleLUTEdit(e));
    });

    tbody.querySelectorAll('.lut-adjust-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.handleLUTAdjust(e));
    });
  }

  /**
   * LUT値の手動編集を処理
   */
  handleLUTEdit(event) {
    const index = parseInt(event.target.dataset.index);
    let newValue = parseFloat(event.target.value);

    // 0-1の範囲にクランプ
    newValue = Math.max(0, Math.min(1, newValue));
    event.target.value = newValue.toFixed(6);

    // 編集可能なLUTを更新
    this.editableLUT[index] = newValue;

    // グラフを更新
    this.updateChartWithEditedLUT();
  }

  /**
   * ± ボタンでのLUT値調整を処理
   */
  handleLUTAdjust(event) {
    const index = parseInt(event.target.dataset.index);
    const action = event.target.dataset.action;
    const step = parseFloat(document.getElementById('lutEditStep').value);

    let currentValue = this.editableLUT[index];

    if (action === 'increase') {
      currentValue += step;
    } else {
      currentValue -= step;
    }

    // 0-1の範囲にクランプ
    currentValue = Math.max(0, Math.min(1, currentValue));

    // 更新
    this.editableLUT[index] = currentValue;

    // テーブルの該当行を更新
    const input = document.querySelector(`input[data-index="${index}"]`);
    if (input) {
      input.value = currentValue.toFixed(6);
    }

    // グラフを更新
    this.updateChartWithEditedLUT();
  }

  /**
   * 編集されたLUTでグラフを更新
   */
  updateChartWithEditedLUT() {
    if (!this.editableLUT || !this.edn.curve) return;

    // カーブを更新
    this.edn.curve.interpolated = [...this.editableLUT];

    // グラフを再描画
    this.updateChart(this.edn.curve, this.lut1Curve);
  }

  /**
   * LUTをリセット
   */
  resetLUT() {
    if (!this.originalLUT) return;

    if (confirm('編集内容を破棄してオリジナルに戻しますか？')) {
      this.editableLUT = [...this.originalLUT];
      this.updateChartWithEditedLUT();
      this.updateLUTEditorTable();
      this.showStatus('LUTをリセットしました', 'info');
    }
  }
}

// ページ読み込み時に初期化
let uiController;
document.addEventListener('DOMContentLoaded', () => {
  uiController = new UIController();
  uiController.init();

  // ダークモード設定を復元
  const isDark = localStorage.getItem('precisionEDN_darkMode') === 'true';
  if (isDark) {
    document.body.classList.add('dark-mode');
  }
});
