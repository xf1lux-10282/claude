/*
 * 255ステップタブレット生成スクリプト（110mm × 110mm）
 * Precision EDN Version 2 用
 *
 * 仕様:
 * - 256ステップ (0-255の全値)
 * - グリッド: 16 × 16
 * - サイズ: 110mm × 110mm
 * - 各ステップサイズ: 約6.9mm × 6.9mm
 * - 16bit グレースケール
 * - カラープロファイル: Gray Gamma 2.2
 * - 解像度: 300 dpi
 */

#target photoshop

// 設定
var config = {
    // サイズ設定
    sizeInMM: 110,         // 110mm × 110mm
    dpi: 300,              // 解像度

    // グリッド設定
    gridSize: 16,          // 16 × 16グリッド
    totalSteps: 256,       // 0-255の256ステップ

    // パッチとマージン設定（EDN_RGB_256と同じ構造）
    patchSize: 74,         // 各パッチのサイズ (px)
    margin: 7,             // パッチ間のマージン (px) - 白い境界線
    outerMargin: 5,        // 外側の余白 (px) - EDN_RGB_256と同じ

    // ビット深度とプロファイル
    bitDepth: 16,          // 16bit
    colorProfile: 'Adobe RGB (1998)'  // RGBカラースペース
};

// 総サイズを計算（EDN_RGB_256と同じ方式）
// グリッド部分: (patchSize + margin) × 16 + margin = (74 + 7) × 16 + 7 = 1303px
// 外側余白を追加: 1303 + 5×2 = 1313px
var gridSizeInPx = (config.patchSize + config.margin) * config.gridSize + config.margin;  // 1303px
var sizeInPx = gridSizeInPx + config.outerMargin * 2;  // 1313px

// ドキュメント作成前の確認
var confirmMsg = "255ステップタブレット（110mm × 110mm）を作成します\n\n";
confirmMsg += "物理サイズ: " + config.sizeInMM + "mm × " + config.sizeInMM + "mm\n";
confirmMsg += "ピクセルサイズ: " + sizeInPx + "px × " + sizeInPx + "px (1313×1313)\n";
confirmMsg += "解像度: " + config.dpi + " dpi\n";
confirmMsg += "ビット深度: " + config.bitDepth + "bit\n";
confirmMsg += "グリッド: " + config.gridSize + " × " + config.gridSize + "\n";
confirmMsg += "ステップ数: " + config.totalSteps + " (0-255)\n";
confirmMsg += "パッチサイズ: " + config.patchSize + "px × " + config.patchSize + "px\n";
confirmMsg += "パッチ間マージン: " + config.margin + "px\n";
confirmMsg += "外側余白: " + config.outerMargin + "px (EDN_RGB_256と同じ)\n\n";
confirmMsg += "作成しますか？";

if (!confirm(confirmMsg)) {
    alert("キャンセルされました");
} else {
    try {
        createStepTablet();
        alert("255ステップタブレットの作成が完了しました！\n\nデスクトップに保存してください。");
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
        sizeInPx,
        sizeInPx,
        config.dpi,
        "255Step_Tablet_110mm_" + getTimestamp(),
        NewDocumentMode.RGB,  // RGBモード
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

    // 進捗表示用
    $.writeln("\n=== 255ステップタブレット作成開始 ===");
    $.writeln("グリッドサイズ: " + config.gridSize + " × " + config.gridSize);
    $.writeln("パッチサイズ: " + config.patchSize + "px × " + config.patchSize + "px");
    $.writeln("マージン: " + config.margin + "px");

    // 各ステップを描画（右上から左下に向かって0→255）
    var stepIndex = 0;
    for (var row = 0; row < config.gridSize; row++) {  // 上から下へ
        for (var col = config.gridSize - 1; col >= 0; col--) {  // 右から左へ
            if (stepIndex >= config.totalSteps) break;

            // グレー値（0-255）
            var grayValue = stepIndex;
            var normalizedValue = grayValue / 255.0;  // 0.0 ~ 1.0

            // パッチの左上座標（外側余白 + マージンを考慮）
            var x = config.outerMargin + config.margin + col * (config.patchSize + config.margin);
            var y = config.outerMargin + config.margin + row * (config.patchSize + config.margin);

            // パッチ領域を選択
            var selectionBounds = [
                [x, y],                                    // 左上
                [x + config.patchSize, y],                 // 右上
                [x + config.patchSize, y + config.patchSize],  // 右下
                [x, y + config.patchSize]                  // 左下
            ];

            // 前の選択を解除してから新しい選択を作成
            docRef.selection.deselect();
            docRef.selection.select(selectionBounds);

            // RGB グレー色を作成（R=G=B）
            var grayColor = new SolidColor();
            grayColor.rgb.red = grayValue;    // 0-255
            grayColor.rgb.green = grayValue;  // 0-255
            grayColor.rgb.blue = grayValue;   // 0-255

            // 塗りつぶし（各パッチを独立して塗りつぶす）
            docRef.selection.fill(grayColor, ColorBlendMode.NORMAL, 100, false);

            // 進捗表示（16の倍数ごと）
            if (stepIndex % 16 === 0) {
                $.writeln("ステップ " + stepIndex + "/255: Gray=" + grayValue + " (" + (normalizedValue * 100).toFixed(1) + "%)");
            }

            stepIndex++;
        }
    }

    // 選択解除
    docRef.selection.deselect();

    // レイヤー名を設定
    docRef.activeLayer.name = "255 Steps (0-255)";

    $.writeln("\n=== 255ステップタブレット作成完了 ===");
    $.writeln("総サイズ: " + sizeInPx + "px × " + sizeInPx + "px (" + config.sizeInMM + "mm × " + config.sizeInMM + "mm)");
    $.writeln("ステップ数: " + config.totalSteps);
    $.writeln("グリッド: " + config.gridSize + " × " + config.gridSize);
    $.writeln("\n次のステップ:");
    $.writeln("1. ファイル > 別名で保存 > TIFF");
    $.writeln("2. オプション: 16bit、圧縮なし");
    $.writeln("3. プリンター設定: カラーマネジメントOFF");
    $.writeln("4. 用紙: ピクトリコOHPフィルム");
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
