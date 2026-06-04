#!/bin/bash
# PX1V-PtPd-v20 インストールスクリプト

set -e

echo "========================================="
echo "PX1V-PtPd-v20 インストール"
echo "========================================="
echo ""

# ステップ1: .quadファイルをコピー
echo "ステップ1: .quadファイルをQTRディレクトリにコピー"
sudo cp ~/Desktop/PX1V-PtPd-v20.quad /Library/Printers/QTR/quadtone/QuadP700/
echo "✓ コピー完了"
echo ""

# ステップ2: QTR curvesを更新
echo "ステップ2: QTR curvesを更新"
/Library/Printers/QTR/bin/quadcurves QuadP700
echo "✓ curves更新完了"
echo ""

# ステップ3: QTR Print-Toolの設定をリセット
echo "ステップ3: QTR Print-Toolの設定をリセット"
defaults delete com.quadtonerip.QTR-Print-Tool 2>/dev/null || echo "設定なし（初回起動）"
echo "✓ 設定リセット完了"
echo ""

echo "========================================="
echo "インストール完了！"
echo "========================================="
echo ""
echo "次のステップ:"
echo "  1. QTR Print-Toolを起動"
echo "  2. 'PX1V-PtPd-v20'を選択"
echo "  3. テストプリントを実行"
echo "  4. 境界線の確認（特にInput 230-240、濃度1.1-1.2D付近）"
echo "  5. ハイライト階調の確認（240-255が分離して見えるか）"
echo ""

