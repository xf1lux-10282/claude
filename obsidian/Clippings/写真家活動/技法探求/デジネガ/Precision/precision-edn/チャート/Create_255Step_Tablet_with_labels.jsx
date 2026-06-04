/*
 * 255ステップタブレット生成スクリプト
 * Precision EDN用 - ヘッダー・ラベル・トンボ付き
 *
 * 仕様:
 * - 256ステップ (0-255の全値)
 * - グリッド: 16 × 16
 * - キャンバス: 1507px × 1507px (110mm × 110mm @ 300DPI)
 * - パッチサイズ: 79px × 79px
 * - パッチ間マージン: 5px
 * - 外側余白: 79px（天地左右）
 * - 上部ヘッダー: ファイル名とサイズ情報（Helvetica Regular 11pt）
 * - 右側ラベル: ステップ番号 (0, 16, 32, ...240) (Helvetica Regular 8pt)
 * - 下部ラベル: 列番号 (0, 1, 2, ...15) (Helvetica Regular 8pt)
 * - トンボ: 四隅に配置
 * - 16bit RGB
 * - カラープロファイル: Adobe RGB (1998)
 * - 解像度: 300 dpi
 */

#target photoshop

// 設定
var config = {
    // サイズ設定
    sizeInMM: 110,         // 110mm × 110mm (パッチ領域)
    dpi: 300,              // 解像度

    // グリッド設定
    gridSize: 16,          // 16 × 16グリッド
    totalSteps: 256,       // 0-255の256ステップ

    // パッチとマージン設定（ユーザー指定）
    patchSize: 79,         // 各パッチのサイズ (px)
    margin: 5,             // パッチ間のマージン (px)

    // レイアウト余白（1507×1507px対応）
    topMargin: 79,         // 上部余白
    leftMargin: 79,        // 左側余白
    rightMargin: 79,       // 右側余白
    bottomMargin: 79,      // 下部余白

    // トンボ設定
    cropMarkLength: 20,    // トンボの長さ (px)
    cropMarkOffset: 10,    // トンボとキャンバス端の距離 (px)
    cropMarkWidth: 1,      // トンボの線幅 (px)

    // フォント設定（ユーザー指定）
    fontSize: 8,           // ラベルフォントサイズ (Helvetica Regular 8pt)
    fontName: "Helvetica",  // フォント名
    headerFontSize: 11,    // ヘッダーフォントサイズ

    // ビット深度とプロファイル
    bitDepth: 16,          // 16bit
    colorProfile: 'Adobe RGB (1998)'  // RGBカラースペース
};

// 総サイズを計算
// パッチ領域: (79 + 5) × 16 + 5 = 1349px
var gridSizeInPx = (config.patchSize + config.margin) * config.gridSize + config.margin;  // 1349px
var canvasWidth = config.leftMargin + gridSizeInPx + config.rightMargin;   // 79 + 1349 + 79 = 1507px

// グラデーションバー用に下部を500px拡張
var gradientBarHeight = 300;
var gradientBarSpacing = 200;  // トンボとグラデーションバーの間隔（数字を避けるため200pxに拡大）
var canvasHeight = config.topMargin + gridSizeInPx + config.bottomMargin + gradientBarSpacing + gradientBarHeight;  // 1507 + 500 = 2007px

// 物理サイズを計算（px @ DPI → mm）
var patchAreaMM = (gridSizeInPx / config.dpi * 25.4).toFixed(1);  // 1349px @ 300DPI = 114.2mm

// ドキュメント作成前の確認
var confirmMsg = "255ステップタブレット（EDN_RGB_256形式）を作成します\n\n";
confirmMsg += "キャンバスサイズ: " + canvasWidth + "px × " + canvasHeight + "px (1507×2007px)\n";
confirmMsg += "パッチ領域: " + gridSizeInPx + "px × " + gridSizeInPx + "px (" + patchAreaMM + "mm × " + patchAreaMM + "mm @ " + config.dpi + "DPI)\n";
confirmMsg += "解像度: " + config.dpi + " DPI\n";
confirmMsg += "ビット深度: " + config.bitDepth + "bit\n";
confirmMsg += "グリッド: " + config.gridSize + " × " + config.gridSize + "\n";
confirmMsg += "ステップ数: " + config.totalSteps + " (0-255)\n\n";
confirmMsg += "機能:\n";
confirmMsg += "- 上部ヘッダー: ファイル名とサイズ\n";
confirmMsg += "- 右側ラベル: ステップ番号 (0, 16, 32, ...240)\n";
confirmMsg += "- 下部ラベル: 列番号 (0-15)\n";
confirmMsg += "- トンボ: 四隅に配置（1507×1507px領域）\n";
confirmMsg += "- グラデーションバー: " + gradientBarHeight + "px（トンボ外側、下部）\n\n";
confirmMsg += "作成しますか？";

if (!confirm(confirmMsg)) {
    alert("キャンセルされました");
} else {
    try {
        createStepTablet();
        alert("255ステップタブレットの作成が完了しました！\n\n" +
              "次の手順:\n" +
              "1. ファイル > 別名で保存 > TIFF\n" +
              "2. 16bit、圧縮なしで保存\n" +
              "3. プリント設定: カラーマネジメントOFF");
    } catch (e) {
        alert("エラーが発生しました:\n" + e.message);
    }
}

/**
 * ステップタブレットを作成
 */
function createStepTablet() {
    // 新規ドキュメント作成
    var docRef = app.documents.add(
        canvasWidth,
        canvasHeight,
        config.dpi,
        "255Step_Tablet_" + getTimestamp(),
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
    $.writeln("\n=== 255ステップタブレット作成開始 ===");
    $.writeln("キャンバスサイズ: " + canvasWidth + "px × " + canvasHeight + "px");
    $.writeln("パッチ領域: " + gridSizeInPx + "px × " + gridSizeInPx + "px");

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

    // パッチグリッドを描画（右上から左下: 0→255）
    drawPatches(docRef);

    // ヘッダーテキストを追加
    drawHeader(docRef);

    // 右側ラベルを追加（ステップ番号: 0, 16, 32, ...240）
    drawRightLabels(docRef);

    // 下部ラベルを追加（列番号: 15, 14, 13, ...0）
    drawBottomLabels(docRef);

    // トンボを追加
    drawCropMarks(docRef);

    // グラデーションバーを追加（トンボの外側、下部）
    drawGradientBar(docRef);

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
    $.writeln("\n[1/4] パッチグリッド描画中...");

    var stepIndex = 0;

    for (var row = 0; row < config.gridSize; row++) {
        for (var col = config.gridSize - 1; col >= 0; col--) {  // 右から左へ
            if (stepIndex >= config.totalSteps) break;

            var grayValue = stepIndex;

            // パッチの左上座標（core.jsと完全一致）
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

            // 進捗表示
            if (stepIndex % 16 === 0) {
                $.writeln("  ステップ " + stepIndex + "/255");
            }

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
    $.writeln("\n[2/4] ヘッダーテキスト追加中...");

    // EDN_RGB_256と同じ形式: "EDN • RGB256 (1473 x 1473) / 300dpi / RGB"
    var headerText = "EDN • RGB256 (" + canvasWidth + " x " + canvasHeight + ") / " + config.dpi + "dpi / RGB";

    var textLayer = docRef.artLayers.add();
    textLayer.kind = LayerKind.TEXT;
    textLayer.name = "Header";

    var textItem = textLayer.textItem;
    textItem.contents = headerText;
    // ヘッダーテキストの位置: 上部余白の中央
    textItem.position = [canvasWidth / 2, config.topMargin / 2];
    textItem.size = config.headerFontSize;
    textItem.justification = Justification.CENTER;  // 中央揃え

    // テキスト色を黒に設定
    var textColor = new SolidColor();
    textColor.rgb.red = 0;
    textColor.rgb.green = 0;
    textColor.rgb.blue = 0;
    textItem.color = textColor;

    $.writeln("  ヘッダー追加完了: " + headerText);
}

/**
 * 右側ラベルを描画（ステップ番号: 0, 16, 32, ...240）
 */
function drawRightLabels(docRef) {
    $.writeln("\n[3/4] 右側ラベル追加中...");

    // 右側ラベルはパッチ領域の外側（右余白内）
    var labelX = config.leftMargin + gridSizeInPx + 10;  // パッチ終了後 + 余白

    for (var row = 0; row < config.gridSize; row++) {
        var stepValue = row * 16;  // 0, 16, 32, ...240

        // 各行の中央に配置（パッチ座標と一致）
        var labelY = config.topMargin + config.margin + row * (config.patchSize + config.margin) + config.patchSize / 2 + 3;

        var textLayer = docRef.artLayers.add();
        textLayer.kind = LayerKind.TEXT;
        textLayer.name = "RightLabel_" + stepValue;

        var textItem = textLayer.textItem;
        textItem.contents = String(stepValue);
        textItem.position = [labelX, labelY];
        textItem.size = config.fontSize;
        textItem.font = config.fontName;  // Helvetica Regular

        var textColor = new SolidColor();
        textColor.rgb.red = 0;
        textColor.rgb.green = 0;
        textColor.rgb.blue = 0;
        textItem.color = textColor;
    }

    $.writeln("  右側ラベル追加完了: 16個 (Helvetica Regular 8pt)");
}

/**
 * 下部ラベルを描画（列番号: 右から0, 1, 2, ...15）
 */
function drawBottomLabels(docRef) {
    $.writeln("\n[4/4] 下部ラベル追加中...");

    // 下部ラベルはパッチ領域の外側（下余白内）
    var labelY = config.topMargin + gridSizeInPx + config.fontSize + 10;  // パッチ終了後 + フォントサイズ + 余白

    for (var col = 0; col < config.gridSize; col++) {
        var colValue = col;  // 右から左: 0, 1, 2, ...15

        // 各列の中央に配置（右から左なので col の位置は config.gridSize - 1 - col）
        var labelX = config.leftMargin + config.margin + (config.gridSize - 1 - col) * (config.patchSize + config.margin) + config.patchSize / 2 - 3;

        var textLayer = docRef.artLayers.add();
        textLayer.kind = LayerKind.TEXT;
        textLayer.name = "BottomLabel_" + colValue;

        var textItem = textLayer.textItem;
        textItem.contents = String(colValue);
        textItem.position = [labelX, labelY];
        textItem.size = config.fontSize;
        textItem.font = config.fontName;  // Helvetica Regular

        var textColor = new SolidColor();
        textColor.rgb.red = 0;
        textColor.rgb.green = 0;
        textColor.rgb.blue = 0;
        textItem.color = textColor;
    }

    $.writeln("  下部ラベル追加完了: 16個 (Helvetica Regular 8pt)");
}

/**
 * トンボを描画（四隅）- 1507×1507px領域を基準に配置
 */
function drawCropMarks(docRef) {
    $.writeln("\n[5/5] トンボ追加中...");

    var offset = config.cropMarkOffset;
    var length = config.cropMarkLength;
    var lineWidth = config.cropMarkWidth;

    // 黒色設定
    var blackColor = new SolidColor();
    blackColor.rgb.red = 0;
    blackColor.rgb.green = 0;
    blackColor.rgb.blue = 0;

    // トンボは1507×1507pxの領域を基準（グラデーションバーを含まない）
    var cropAreaHeight = config.topMargin + gridSizeInPx + config.bottomMargin;  // 1507px

    // 四隅のトンボを描画
    var corners = [
        {name: "左上", x: 0, y: 0, hDir: 1, vDir: 1},
        {name: "右上", x: canvasWidth, y: 0, hDir: -1, vDir: 1},
        {name: "左下", x: 0, y: cropAreaHeight, hDir: 1, vDir: -1},
        {name: "右下", x: canvasWidth, y: cropAreaHeight, hDir: -1, vDir: -1}
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
    // 選択範囲を作成（線として）
    var points = [];

    if (x1 === x2) {
        // 垂直線
        for (var y = Math.min(y1, y2); y <= Math.max(y1, y2); y++) {
            points.push([x1, y]);
        }
    } else {
        // 水平線
        for (var x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
            points.push([x, y1]);
        }
    }

    // 線を描画（矩形として）
    if (x1 === x2) {
        // 垂直線: 幅を持たせる
        var rect = [
            [x1 - width/2, Math.min(y1, y2)],
            [x1 + width/2, Math.min(y1, y2)],
            [x1 + width/2, Math.max(y1, y2)],
            [x1 - width/2, Math.max(y1, y2)]
        ];
    } else {
        // 水平線: 高さを持たせる
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
 * グラデーションバーを描画（トンボの外側、下部）
 */
function drawGradientBar(docRef) {
    $.writeln("\n[6/6] グラデーションバー追加中...");

    // トンボの下部位置を計算
    var cropAreaHeight = config.topMargin + gridSizeInPx + config.bottomMargin;  // 1507px

    // グラデーションバーの設定
    var barWidth = gridSizeInPx;  // パッチ領域と同じ幅（1349px）
    var barHeight = gradientBarHeight;  // 300px
    var barX = config.leftMargin;  // 左余白と同じ位置から開始
    var barY = cropAreaHeight + gradientBarSpacing;  // 1507 + 200 = 1707px（トンボの外側）

    // 新しいレイヤーを作成
    var gradientLayer = docRef.artLayers.add();
    gradientLayer.name = "Gradient Bar (0-255)";

    // 0-255の各値を1400pxに分散（約5.49px/ステップ）
    var stepWidth = barWidth / 256;  // 約5.47px

    for (var i = 0; i < 256; i++) {
        var grayValue = i;
        var x = barX + i * stepWidth;

        // 垂直ストライプを描画
        var stripeBounds = [
            [x, barY],
            [x + stepWidth, barY],
            [x + stepWidth, barY + barHeight],
            [x, barY + barHeight]
        ];

        docRef.selection.select(stripeBounds);

        var grayColor = new SolidColor();
        grayColor.rgb.red = grayValue;
        grayColor.rgb.green = grayValue;
        grayColor.rgb.blue = grayValue;

        docRef.selection.fill(grayColor, ColorBlendMode.NORMAL, 100, false);
        docRef.selection.deselect();

        // 進捗表示（32の倍数ごと）
        if (i % 32 === 0) {
            $.writeln("  グラデーション: " + i + "/255");
        }
    }

    // ラベルを追加（0, 128, 255）
    var labelY = barY + barHeight + 20;

    // ラベル: 0
    var label0 = docRef.artLayers.add();
    label0.kind = LayerKind.TEXT;
    label0.name = "GradientLabel_0";
    var text0 = label0.textItem;
    text0.contents = "0";
    text0.position = [barX, labelY];
    text0.size = 12;
    text0.font = config.fontName;
    var textColor0 = new SolidColor();
    textColor0.rgb.red = 0;
    textColor0.rgb.green = 0;
    textColor0.rgb.blue = 0;
    text0.color = textColor0;

    // ラベル: 128
    var label128 = docRef.artLayers.add();
    label128.kind = LayerKind.TEXT;
    label128.name = "GradientLabel_128";
    var text128 = label128.textItem;
    text128.contents = "128";
    text128.position = [barX + barWidth / 2 - 10, labelY];
    text128.size = 12;
    text128.font = config.fontName;
    var textColor128 = new SolidColor();
    textColor128.rgb.red = 0;
    textColor128.rgb.green = 0;
    textColor128.rgb.blue = 0;
    text128.color = textColor128;

    // ラベル: 255
    var label255 = docRef.artLayers.add();
    label255.kind = LayerKind.TEXT;
    label255.name = "GradientLabel_255";
    var text255 = label255.textItem;
    text255.contents = "255";
    text255.position = [barX + barWidth - 20, labelY];
    text255.size = 12;
    text255.font = config.fontName;
    var textColor255 = new SolidColor();
    textColor255.rgb.red = 0;
    textColor255.rgb.green = 0;
    textColor255.rgb.blue = 0;
    text255.color = textColor255;

    $.writeln("  グラデーションバー追加完了: " + barWidth + "px × " + barHeight + "px (0-255)");
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
