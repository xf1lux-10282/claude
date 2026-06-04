#!/bin/bash

# QTRライブラリ更新スクリプト
# 新しいカーブファイルをPrint-Toolに認識させる

echo "=== QTRライブラリ更新開始 ==="
echo ""

# 方法1: Print-Toolのキャッシュをクリア
echo "1. Print-Toolのキャッシュをクリア中..."
defaults delete com.quadtonerip.Print-Tool 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ キャッシュをクリアしました"
else
    echo "   ℹ キャッシュが存在しないか、既にクリア済みです"
fi
echo ""

# 方法2: QTRカーブデータベースを更新（マニュアル推奨）
echo "2. QTRカーブデータベースを更新中..."
/Library/Printers/QTR/bin/quadcurves QuadP700
echo ""

# 方法3: インストールされているカーブファイルを確認
echo "3. インストールされているxf1カーブを確認..."
ls -1 /Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-xf1-*.quad 2>/dev/null | while read file; do
    basename "$file" .quad
done
echo ""

# 方法4: 最新カーブファイルの内容を検証
echo "4. v9-SMカーブファイルの検証..."
if [ -f "/Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-xf1-v9-SM.quad" ]; then
    echo "   ✓ ファイルが存在します"

    # 行数チェック
    LINES=$(wc -l < /Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-xf1-v9-SM.quad)
    echo "   行数: $LINES"

    # K-valueの主要ポイントをチェック
    echo "   主要K-values:"
    awk '/^# K curve$/ {start=NR} start && NR>start && NR<=start+257' /Library/Printers/QTR/quadtone/QuadP700/PX1V-PtPd-xf1-v9-SM.quad | \
    awk 'NR==1 {printf "     Input 0: %s\n", $0}
         NR==25 {printf "     Input 24: %s\n", $0}
         NR==233 {printf "     Input 232: %s\n", $0}
         NR==256 {printf "     Input 255: %s\n", $0}'
else
    echo "   ✗ ファイルが見つかりません"
fi
echo ""

echo "=== 完了 ==="
echo ""
echo "次の手順:"
echo "1. Print-Toolアプリケーションを完全に終了してください"
echo "2. Print-Toolを再度起動してください"
echo "3. プリンター選択で「PX1V-PtPd-xf1-v9-SM」が表示されるか確認してください"
echo ""
