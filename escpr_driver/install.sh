#!/bin/bash
# EPSON SC-P9550 ESC/P-Raster QuadToneRIP Driver Installation Script
#
# このスクリプトは以下を実行します:
# 1. CUPSフィルター（rastertop9550）をシステムにインストール
# 2. PPDファイルをシステムにインストール
# 3. 依存Pythonモジュールをインストール
# 4. プリンターキューを登録

set -e

# 色付きログ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 管理者権限確認
if [ "$EUID" -ne 0 ]; then
    log_error "このスクリプトはsudo権限で実行する必要があります"
    echo "実行方法: sudo ./install.sh"
    exit 1
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

log_info "=== EPSON SC-P9550 ESC/P-Raster QuadToneRIP Driver インストール ==="
echo ""

# ==============================================================================
# Step 1: 依存関係チェック
# ==============================================================================

log_info "Step 1: 依存関係チェック"

# Python3確認
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 が見つかりません"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
log_success "Python: $PYTHON_VERSION"

# PIL/Pillow確認
if ! python3 -c "import PIL" 2>/dev/null; then
    log_warning "Pillow がインストールされていません"
    log_info "Pillowをインストール中..."
    pip3 install Pillow
fi
log_success "Pillow: OK"

# NumPy確認
if ! python3 -c "import numpy" 2>/dev/null; then
    log_warning "NumPy がインストールされていません"
    log_info "NumPyをインストール中..."
    pip3 install numpy
fi
log_success "NumPy: OK"

echo ""

# ==============================================================================
# Step 2: ドライバーファイル確認
# ==============================================================================

log_info "Step 2: ドライバーファイル確認"

REQUIRED_FILES=(
    "escpr_commands.py"
    "escpr_driver.py"
    "quad_parser.py"
    "rastertop9550"
    "P9550_ESCPR_QTR.ppd"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$file" ]; then
        log_error "必要なファイルが見つかりません: $file"
        exit 1
    fi
    log_success "  ✓ $file"
done

echo ""

# ==============================================================================
# Step 3: システムディレクトリ作成
# ==============================================================================

log_info "Step 3: システムディレクトリ作成"

INSTALL_DIR="/Library/Printers/QTR/escpr_driver"
FILTER_DIR="/Library/Printers/QTR/filter"
PPD_DIR="/Library/Printers/PPDs/Contents/Resources"

mkdir -p "$INSTALL_DIR"
mkdir -p "$FILTER_DIR"

log_success "インストールディレクトリ: $INSTALL_DIR"

echo ""

# ==============================================================================
# Step 4: ドライバーファイルインストール
# ==============================================================================

log_info "Step 4: ドライバーファイルインストール"

# Pythonモジュールコピー
cp "$SCRIPT_DIR/escpr_commands.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/escpr_driver.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/quad_parser.py" "$INSTALL_DIR/"
log_success "Pythonモジュールをコピー"

# CUPSフィルターコピー
cp "$SCRIPT_DIR/rastertop9550" "$FILTER_DIR/"
chmod +x "$FILTER_DIR/rastertop9550"
log_success "CUPSフィルターをインストール: $FILTER_DIR/rastertop9550"

# フィルター内のパス参照を更新
sed -i '' "s|DRIVER_DIR = .*|DRIVER_DIR = \"$INSTALL_DIR\"|" "$FILTER_DIR/rastertop9550"
log_success "フィルターパス設定を更新"

# PPDファイルコピー
cp "$SCRIPT_DIR/P9550_ESCPR_QTR.ppd" "$PPD_DIR/"
gzip -f "$PPD_DIR/P9550_ESCPR_QTR.ppd"
log_success "PPDファイルをインストール: $PPD_DIR/P9550_ESCPR_QTR.ppd.gz"

# PPD内のフィルターパス更新
gunzip "$PPD_DIR/P9550_ESCPR_QTR.ppd.gz"
sed -i '' "s|/tmp/escpr_driver/rastertop9550|$FILTER_DIR/rastertop9550|" "$PPD_DIR/P9550_ESCPR_QTR.ppd"
gzip -f "$PPD_DIR/P9550_ESCPR_QTR.ppd"
log_success "PPDフィルターパスを更新"

echo ""

# ==============================================================================
# Step 5: プリンター検出
# ==============================================================================

log_info "Step 5: プリンター検出"

PRINTER_URI=""
PRINTER_NAME="P9550_QTR_ESCPR"

# USB接続確認
if lpstat -v | grep -q "SC-P9500"; then
    PRINTER_URI=$(lpstat -v | grep "SC-P9500" | head -1 | awk '{print $3}' | sed 's/:$//')
    log_success "プリンター検出 (USB): $PRINTER_URI"
elif lpstat -v | grep -q "SC-P9550"; then
    PRINTER_URI=$(lpstat -v | grep "SC-P9550" | head -1 | awk '{print $3}' | sed 's/:$//')
    log_success "プリンター検出 (USB): $PRINTER_URI"
else
    log_warning "自動検出できませんでした"
    log_info "手動でプリンターURIを入力してください"
    echo ""
    echo "USB接続の場合:"
    echo "  usb://EPSON/SC-P9500%20Series?serial=XXXXXXXX"
    echo ""
    echo "ネットワーク接続の場合:"
    echo "  ipp://192.168.1.100/ipp/print"
    echo "  socket://192.168.1.100:9100"
    echo ""
    read -p "プリンターURI: " PRINTER_URI

    if [ -z "$PRINTER_URI" ]; then
        log_error "プリンターURIが入力されませんでした"
        log_info "後で手動でプリンターキューを登録してください:"
        echo ""
        echo "  sudo lpadmin -p $PRINTER_NAME \\"
        echo "    -v 'usb://EPSON/SC-P9500%20Series?serial=XXXXXXXX' \\"
        echo "    -P $PPD_DIR/P9550_ESCPR_QTR.ppd.gz \\"
        echo "    -E"
        echo ""
        log_warning "プリンターキュー登録をスキップしました"
        exit 0
    fi
fi

echo ""

# ==============================================================================
# Step 6: プリンターキュー登録
# ==============================================================================

log_info "Step 6: プリンターキュー登録"

# 既存のキューを削除（存在する場合）
if lpstat -p "$PRINTER_NAME" &> /dev/null; then
    log_warning "既存のプリンターキュー '$PRINTER_NAME' を削除します"
    lpadmin -x "$PRINTER_NAME"
fi

# 新しいキューを登録
lpadmin -p "$PRINTER_NAME" \
    -v "$PRINTER_URI" \
    -P "$PPD_DIR/P9550_ESCPR_QTR.ppd.gz" \
    -D "EPSON SC-P9550 QuadToneRIP ESC/P-Raster" \
    -L "Local" \
    -E

log_success "プリンターキュー登録完了: $PRINTER_NAME"

# デフォルト設定
cupsenable "$PRINTER_NAME"
cupsaccept "$PRINTER_NAME"
log_success "プリンターを有効化"

echo ""

# ==============================================================================
# Step 7: 動作確認
# ==============================================================================

log_info "Step 7: 動作確認"

lpstat -p "$PRINTER_NAME"
lpstat -v "$PRINTER_NAME"

echo ""
log_success "=== インストール完了 ==="
echo ""

log_info "次のステップ:"
echo "  1. システム環境設定 → プリンタとスキャナ で '$PRINTER_NAME' を確認"
echo "  2. テストページを印刷:"
echo ""
echo "     macOS印刷ダイアログから:"
echo "       - プリンター: $PRINTER_NAME"
echo "       - カーブ選択: QuadTone RIP Curve 1 → P9550-PtPd-xf1-3ink"
echo ""
echo "  3. コマンドラインからテスト:"
echo ""
echo "     lpr -P $PRINTER_NAME -o ripCurve1=P9550-PtPd-xf1-3ink /path/to/image.pdf"
echo ""

log_info "トラブルシューティング:"
echo "  - CUPSログ確認: tail -f /var/log/cups/error_log"
echo "  - プリンター状態: lpstat -p $PRINTER_NAME"
echo "  - ジョブ確認: lpstat -o"
echo ""

log_info "アンインストール方法:"
echo "  sudo lpadmin -x $PRINTER_NAME"
echo "  sudo rm -rf $INSTALL_DIR"
echo "  sudo rm $FILTER_DIR/rastertop9550"
echo "  sudo rm $PPD_DIR/P9550_ESCPR_QTR.ppd.gz"
echo ""
