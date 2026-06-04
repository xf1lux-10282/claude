/*
 * 32ステップチャート生成スクリプト
 * Precision EDN v2用 - ヘッダー・ラベル・トンボ付き
 *
 * 仕様:
 * - 32ステップ (0, 8, 16, 24, ..., 248の32値)
 * - グリッド: 4 × 8
 * - 高さ: 13cm (幅は自動計算)
 * - パッチサイズ: 150px × 150px (13cm / 8 rows @ 300DPI)
 * - パッチ間マージン: 10px
 * - 外側余白: 150px（天地左右）
 * - 上部ヘッダー: ファイル名とサイズ情報（Helvetica Medium 11pt）
 * - 右側ラベル: ステップ番号 (0, 32, 64, ...224) (Helvetica Medium 8pt)
 * - 下部ラベル: 列番号 (0, 1, 2, 3) (Helvetica Medium 8pt)
 * - トンボ: 四隅に配置
 * - 16bit RGB
 * - カラープロファイル: Adobe RGB (1998)
 * - 解像度: 300 dpi
 */

#target photoshop

// 設定
var config = {
    // サイズ設定
    heightInCM: 13,        // 高さ: 13cm
    dpi: 300,              // 解像度

    // グリッド設定
    gridCols: 4,           // 4列
    gridRows: 8,           // 8行
    totalSteps: 32,        // 32ステップ

    // パッチとマージン設定
    patchSize: 150,        // 各パッチのサイズ (px) - 13cm / 8 rows @ 300DPI
    margin: 10,            // パッチ間のマージン (px)

    // レイアウト余白
    topMargin: 150,        // 上部余白
    leftMargin: 150,       // 左側余白
    rightMargin: 150,      // 右側余白
    bottomMargin: 150,     // 下部余白

    // トンボ設定
    cropMarkLength: 30,    // トンボの長さ (px)
    cropMarkOffset: 15,    // トンボとキャンバス端の距離 (px)
    cropMarkWidth: 2,      // トンボの線幅 (px)

    // フォント設定
    fontSize: 8,           // ラベルフォントサイズ (Helvetica Medium 8pt)
    fontName: "Helvetica-Medium",  // フォント名: Helvetica Medium
    headerFontSize: 11,    // ヘッダーフォントサイズ

    // ビット深度とプロファイル
    bitDepth: 16,          // 16bit
    colorProfile: 'Adobe RGB (1998)'  // RGBカラースペース
};

// 32ステップの値リスト (0, 8, 16, 24, ..., 248)
var stepValues = [];
for (var i = 0; i < 32; i++) {
    stepValues.push(i * 8);
}

// 総サイズを計算
// パッチ領域: (150 + 10) × 4 + 10 = 650px (幅)
//            (150 + 10) × 8 + 10 = 1290px (高さ)
var gridWidthInPx = (config.patchSize + config.margin) * config.gridCols + config.margin;   // 650px
var gridHeightInPx = (config.patchSize + config.margin) * config.gridRows + config.margin;  // 1290px

var canvasWidth = config.leftMargin + gridWidthInPx + config.rightMargin;   // 150 + 650 + 150 = 950px
var canvasHeight = config.topMargin + gridHeightInPx + config.bottomMargin; // 150 + 1290 + 150 = 1590px

// 物理サイズを計算（px @ DPI → cm）
var patchAreaWidthCM = (gridWidthInPx / config.dpi * 2.54).toFixed(2);   // 650px @ 300DPI ≈ 5.50cm
var patchAreaHeightCM = (gridHeightInPx / config.dpi * 2.54).toFixed(2); // 1290px @ 300DPI ≈ 10.92cm
var canvasWidthCM = (canvasWidth / config.dpi * 2.54).toFixed(2);        // 950px @ 300DPI ≈ 8.04cm
var canvasHeightCM = (canvasHeight / config.dpi * 2.54).toFixed(2);      // 1590px @ 300DPI ≈ 13.46cm

// ドキュメント作成前の確認
var confirmMsg = "32ステップチャート（Precision EDN v2）を作成します\n\n";
confirmMsg += "キャンバスサイズ: " + canvasWidth + "px × " + canvasHeight + "px (" + canvasWidthCM + "cm × " + canvasHeightCM + "cm)\n";
confirmMsg += "パッチ領域: " + gridWidthInPx + "px × " + gridHeightInPx + "px (" + patchAreaWidthCM + "cm × " + patchAreaHeightCM + "cm)\n";
confirmMsg += "解像度: " + config.dpi + " DPI\n";
confirmMsg += "ビット深度: " + config.bitDepth + "bit\n";
confirmMsg += "グリッド: " + config.gridCols + "列 × " + config.gridRows + "行\n";
confirmMsg += "ステップ数: " + config.totalSteps + " (0, 8, 16, ..., 248)\n";
confirmMsg += "パッチサイズ: " + config.patchSize + "px × " + config.patchSize + "px\n\n";
confirmMsg += "機能:\n";
confirmMsg += "- 上部ヘッダー: ファイル名とサイズ (Helvetica Medium " + config.headerFontSize + "pt)\n";
confirmMsg += "- 右側ラベル: ステップ番号 (Helvetica Medium " + config.fontSize + "pt)\n";
confirmMsg += "- 下部ラベル: 列番号 (Helvetica Medium " + config.fontSize + "pt)\n";
confirmMsg += "- トンボ: 四隅に配置\n\n";
confirmMsg += "作成しますか？";

if (!confirm(confirmMsg)) {
    alert("キャンセルされました");
} else {
    try {
        createStepChart();
        alert("32ステップチャートの作成が完了しました！\n\n" +
              "次の手順:\n" +
              "1. ファイル > 別名で保存 > TIFF\n" +
              "2. 16bit、圧縮なしで保存\n" +
              "3. プリント設定: カラーマネジメントOFF");
    } catch (e) {
        alert("エラーが発生しました:\n" + e.message);
    }
}

/**
 * ステップチャートを作成
 */
function createStepChart() {
    // 新規ドキュメント作成
    var docRef = app.documents.add(
        canvasWidth,
        canvasHeight,
        config.dpi,
        "Precision_EDN_v2_32Step_" + getTimestamp(),
        NewDocumentMode.RGB,
        DocumentFill.WHITE,
        1,
        config.bitDepth === 16 ? BitsPerChannelType.SIXTEEN : BitsPerChannelType.EIGHT
    );

    // カラープロファイル設定
    try {
        docRef.convertProfile(config.colorProfile, Intent.RELATIVECOLORIMETRIC, true, false);
    } catch (e) {
        $.writeln("カラープロファイル設定エラー: " + e.message);
    }

    // 進捗表示
    $.writeln("\n=== 32ステップチャート作成開始 ===");
    $.writeln("キャンバスサイズ: " + canvasWidth + "px × " + canvasHeight + "px (" + canvasWidthCM + "cm × " + canvasHeightCM + "cm)");
    $.writeln("パッチ領域: " + gridWidthInPx + "px × " + gridHeightInPx + "px (" + patchAreaWidthCM + "cm × " + patchAreaHeightCM + "cm)");

    // 背景レイヤーを作成（白）
    var bgLayer = docRef.artLayers.add();
    bgLayer.name = "Background";
    docRef.activeLayer = bgLayer;

    // 全体を白で塗りつぶし
    docRef.selection.selectAll();
    var whiteColor = new SolidColor();
    whiteColor.rgb.red = 255;
    whiteColor.rgb.green = 255;
    whiteColor.rgb.blue = 255;
    docRef.selection.fill(whiteColor, ColorBlendMode.NORMAL, 100, false);
    docRef.selection.deselect();

    // パッチグリッドを描画（右上から左下: 0→31）
    drawPatches(docRef);

    // ヘッダーテキストを追加
    drawHeader(docRef);

    // 右側ラベルを追加（ステップ値: 0, 32, 64, ...224）
    drawRightLabels(docRef);

    // 下部ラベルを追加（列番号: 3, 2, 1, 0）
    drawBottomLabels(docRef);

    // トンボを追加
    drawCropMarks(docRef);

    // 選択解除
    docRef.selection.deselect();

    // レイヤー統合
    docRef.flatten();

    $.writeln("\n=== 完了 ===");
    $.writeln("ファイル名: " + docRef.name);
    $.writeln("サイズ: " + canvasWidth + "px × " + canvasHeight + "px");
}

/**
 * パッチグリッドを描画
 */
function drawPatches(docRef) {
    $.writeln("\n[1/5] パッチグリッド描画中...");

    var stepIndex = 0;

    for (var row = 0; row < config.gridRows; row++) {
        for (var col = config.gridCols - 1; col >= 0; col--) {  // 右から左へ
            if (stepIndex >= config.totalSteps) break;

            var grayValue = stepValues[stepIndex];

            // パッチの左上座標
            var x = config.leftMargin + config.margin + col * (config.patchSize + config.margin);
            var y = config.topMargin + config.margin + row * (config.patchSize + config.margin);

            // パッチ領域を選択
            var selectionBounds = [
                [x, y],
                [x + config.patchSize, y],
                [x + config.patchSize, y + config.patchSize],
                [x, y + config.patchSize]
            ];

            docRef.selection.deselect();
            docRef.selection.select(selectionBounds);

            // RGB グレー色を作成
            var grayColor = new SolidColor();
            grayColor.rgb.red = grayValue;
            grayColor.rgb.green = grayValue;
            grayColor.rgb.blue = grayValue;

            // 塗りつぶし
            docRef.selection.fill(grayColor, ColorBlendMode.NORMAL, 100, false);

            $.writeln("  ステップ " + stepIndex + ": RGB(" + grayValue + ")");

            stepIndex++;
        }
    }

    docRef.selection.deselect();
    $.writeln("  パッチ描画完了: " + config.totalSteps + "個");
}

/**
 * ヘッダーテキストを描画
 */
function drawHeader(docRef) {
    $.writeln("\n[2/5] ヘッダーテキスト追加中...");

    var headerText = "Precision EDN v2 • 32 Steps (" + canvasWidth + " x " + canvasHeight + ") / " + config.dpi + "dpi / RGB";

    var textLayer = docRef.artLayers.add();
    textLayer.kind = LayerKind.TEXT;
    textLayer.name = "Header";

    var textItem = textLayer.textItem;
    textItem.contents = headerText;
    textItem.position = [canvasWidth / 2, config.topMargin / 2];
    textItem.size = config.headerFontSize;
    textItem.font = config.fontName;  // Helvetica Medium
    textItem.justification = Justification.CENTER;

    var textColor = new SolidColor();
    textColor.rgb.red = 0;
    textColor.rgb.green = 0;
    textColor.rgb.blue = 0;
    textItem.color = textColor;

    $.writeln("  ヘッダー追加完了: " + headerText);
}

/**
 * 右側ラベルを描画（ステップ値: 0, 32, 64, ...224）
 */
function drawRightLabels(docRef) {
    $.writeln("\n[3/5] 右側ラベル追加中...");

    var labelX = config.leftMargin + gridWidthInPx + 20;

    for (var row = 0; row < config.gridRows; row++) {
        var stepValue = row * 32;  // 0, 32, 64, 96, 128, 160, 192, 224

        var labelY = config.topMargin + config.margin + row * (config.patchSize + config.margin) + config.patchSize / 2 + 3;

        var textLayer = docRef.artLayers.add();
        textLayer.kind = LayerKind.TEXT;
        textLayer.name = "RightLabel_" + stepValue;

        var textItem = textLayer.textItem;
        textItem.contents = String(stepValue);
        textItem.position = [labelX, labelY];
        textItem.size = config.fontSize;
        textItem.font = config.fontName;  // Helvetica Medium

        var textColor = new SolidColor();
        textColor.rgb.red = 0;
        textColor.rgb.green = 0;
        textColor.rgb.blue = 0;
        textItem.color = textColor;
    }

    $.writeln("  右側ラベル追加完了: " + config.gridRows + "個 (Helvetica Medium " + config.fontSize + "pt)");
}

/**
 * 下部ラベルを描画（列番号: 右から0, 1, 2, 3）
 */
function drawBottomLabels(docRef) {
    $.writeln("\n[4/5] 下部ラベル追加中...");

    var labelY = config.topMargin + gridHeightInPx + config.fontSize + 15;

    for (var col = 0; col < config.gridCols; col++) {
        var colValue = col;  // 右から左: 0, 1, 2, 3

        var labelX = config.leftMargin + config.margin + (config.gridCols - 1 - col) * (config.patchSize + config.margin) + config.patchSize / 2 - 3;

        var textLayer = docRef.artLayers.add();
        textLayer.kind = LayerKind.TEXT;
        textLayer.name = "BottomLabel_" + colValue;

        var textItem = textLayer.textItem;
        textItem.contents = String(colValue);
        textItem.position = [labelX, labelY];
        textItem.size = config.fontSize;
        textItem.font = config.fontName;  // Helvetica Medium

        var textColor = new SolidColor();
        textColor.rgb.red = 0;
        textColor.rgb.green = 0;
        textColor.rgb.blue = 0;
        textItem.color = textColor;
    }

    $.writeln("  下部ラベル追加完了: " + config.gridCols + "個 (Helvetica Medium " + config.fontSize + "pt)");
}

/**
 * トンボを描画（四隅）
 */
function drawCropMarks(docRef) {
    $.writeln("\n[5/5] トンボ追加中...");

    var offset = config.cropMarkOffset;
    var length = config.cropMarkLength;
    var lineWidth = config.cropMarkWidth;

    var blackColor = new SolidColor();
    blackColor.rgb.red = 0;
    blackColor.rgb.green = 0;
    blackColor.rgb.blue = 0;

    var corners = [
        {name: "左上", x: 0, y: 0, hDir: 1, vDir: 1},
        {name: "右上", x: canvasWidth, y: 0, hDir: -1, vDir: 1},
        {name: "左下", x: 0, y: canvasHeight, hDir: 1, vDir: -1},
        {name: "右下", x: canvasWidth, y: canvasHeight, hDir: -1, vDir: -1}
    ];

    for (var i = 0; i < corners.length; i++) {
        var corner = corners[i];

        // 水平トンボ
        var hLine = docRef.artLayers.add();
        hLine.kind = LayerKind.NORMAL;
        hLine.name = "CropMark_" + corner.name + "_H";

        var hStart = corner.x + offset * corner.hDir;
        var hEnd = hStart + length * corner.hDir;
        var hY = corner.y + offset * corner.vDir;

        drawLine(docRef, hLine, hStart, hY, hEnd, hY, lineWidth, blackColor);

        // 垂直トンボ
        var vLine = docRef.artLayers.add();
        vLine.kind = LayerKind.NORMAL;
        vLine.name = "CropMark_" + corner.name + "_V";

        var vX = corner.x + offset * corner.hDir;
        var vStart = corner.y + offset * corner.vDir;
        var vEnd = vStart + length * corner.vDir;

        drawLine(docRef, vLine, vX, vStart, vX, vEnd, lineWidth, blackColor);
    }

    $.writeln("  トンボ追加完了: 8本（四隅）");
}

/**
 * 直線を描画
 */
function drawLine(docRef, layer, x1, y1, x2, y2, width, color) {
    if (x1 === x2) {
        // 垂直線
        var rect = [
            [x1 - width/2, Math.min(y1, y2)],
            [x1 + width/2, Math.min(y1, y2)],
            [x1 + width/2, Math.max(y1, y2)],
            [x1 - width/2, Math.max(y1, y2)]
        ];
    } else {
        // 水平線
        var rect = [
            [Math.min(x1, x2), y1 - width/2],
            [Math.max(x1, x2), y1 - width/2],
            [Math.max(x1, x2), y1 + width/2],
            [Math.min(x1, x2), y1 + width/2]
        ];
    }

    docRef.selection.deselect();
    docRef.selection.select(rect);
    docRef.selection.fill(color, ColorBlendMode.NORMAL, 100, false);
    docRef.selection.deselect();
}

/**
 * タイムスタンプ取得
 */
function getTimestamp() {
    var now = new Date();
    var year = now.getFullYear();
    var month = padZero(now.getMonth() + 1);
    var day = padZero(now.getDate());
    var hour = padZero(now.getHours());
    var minute = padZero(now.getMinutes());
    return year + month + day + "_" + hour + minute;
}

/**
 * ゼロパディング
 */
function padZero(num) {
    return (num < 10 ? "0" : "") + num;
}
