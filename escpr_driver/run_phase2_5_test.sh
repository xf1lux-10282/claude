#!/bin/bash
# Phase 2.5 実機テスト自動実行スクリプト
#
# 使い方:
#   ./run_phase2_5_test.sh [USB|NETWORK] [device_or_ip]
#
# 例:
#   ./run_phase2_5_test.sh USB /dev/usb/lp0
#   ./run_phase2_5_test.sh NETWORK 192.168.1.100

set -e

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
OUTPUT_DIR="/tmp/phase2_5_results"
mkdir -p "$OUTPUT_DIR"

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

# 引数チェック
if [ $# -lt 2 ]; then
    log_error "Usage: $0 [USB|NETWORK] [device_or_ip]"
    echo ""
    echo "Examples:"
    echo "  $0 USB /dev/usb/lp0"
    echo "  $0 NETWORK 192.168.1.100"
    exit 1
fi

CONNECTION_TYPE="$1"
DEVICE="$2"

log_info "=== Phase 2.5: 実機テスト開始 ==="
log_info "接続方法: $CONNECTION_TYPE"
log_info "デバイス: $DEVICE"
log_info "出力先: $OUTPUT_DIR"
echo ""

# ==============================================================================
# Step 1: 事前確認
# ==============================================================================

log_info "Step 1: 事前確認"

# Pythonスクリプト確認
if [ ! -f "$SCRIPT_DIR/test_print_image.py" ]; then
    log_error "test_print_image.py が見つかりません: $SCRIPT_DIR"
    exit 1
fi
log_success "Pythonスクリプト: OK"

# テスト画像確認
if [ ! -f "/tmp/test_simple_rect.tiff" ]; then
    log_warning "test_simple_rect.tiff が見つかりません。生成します..."
    python3 -c "
from PIL import Image
import numpy as np
img = np.zeros((10, 10), dtype=np.uint8)
img[3:7, 3:7] = 255
Image.fromarray(img).save('/tmp/test_simple_rect.tiff')
"
    log_success "test_simple_rect.tiff 生成完了"
fi

# QuadToneRIPカーブファイル確認
CURVE_FILE="/Library/Printers/QTR/quadtone/QTR_P9550/P9550-PtPd-xf1-3ink.quad"
if [ ! -f "$CURVE_FILE" ]; then
    log_warning "カーブファイルが見つかりません: $CURVE_FILE"
    log_warning "代替カーブファイルを探しています..."

    CURVE_FILE=$(find /Library/Printers/QTR -name "*.quad" -type f 2>/dev/null | head -1)

    if [ -z "$CURVE_FILE" ]; then
        log_error "QuadToneRIPカーブファイルが見つかりません"
        exit 1
    fi

    log_success "代替カーブファイルを使用: $CURVE_FILE"
fi

# デバイス確認
if [ "$CONNECTION_TYPE" = "USB" ]; then
    if [ ! -e "$DEVICE" ]; then
        log_error "USBデバイスが見つかりません: $DEVICE"
        log_info "利用可能なデバイス:"
        ls -la /dev/usb/lp* 2>/dev/null || echo "  (なし)"
        exit 1
    fi
    log_success "USBデバイス: OK"
elif [ "$CONNECTION_TYPE" = "NETWORK" ]; then
    log_info "ネットワーク接続テスト: $DEVICE:9100"
    if ! nc -z -w 3 "$DEVICE" 9100 2>/dev/null; then
        log_warning "ポート9100に接続できません（プリンターがオフまたは設定が異なる可能性）"
    else
        log_success "ネットワーク接続: OK"
    fi
else
    log_error "接続方法は USB または NETWORK を指定してください"
    exit 1
fi

echo ""

# ==============================================================================
# Step 2: Test 1 - 最小テストパターン
# ==============================================================================

log_info "Step 2: Test 1 - 最小テストパターン（10x10ピクセル）"

TEST1_OUTPUT="$OUTPUT_DIR/test1_minimal.bin"

log_info "テストバイナリ生成中..."
python3 "$SCRIPT_DIR/test_print_image.py" \
    /tmp/test_simple_rect.tiff \
    "$CURVE_FILE" \
    -o "$TEST1_OUTPUT" \
    --dpi 720x720 \
    --paper 50x50

if [ ! -f "$TEST1_OUTPUT" ]; then
    log_error "テストバイナリ生成失敗"
    exit 1
fi

FILE_SIZE=$(stat -f%z "$TEST1_OUTPUT" 2>/dev/null || stat -c%s "$TEST1_OUTPUT" 2>/dev/null)
log_success "テストバイナリ生成完了: $TEST1_OUTPUT (${FILE_SIZE}バイト)"

# バイナリ内容確認
log_info "バイナリ内容確認（先頭20バイト）:"
hexdump -C "$TEST1_OUTPUT" | head -5

# 送信確認
echo ""
log_warning "プリンターにテストバイナリを送信します"
log_warning "プリンターの状態を確認してください:"
log_warning "  - 用紙がセットされているか"
log_warning "  - エラーランプが点灯していないか"
echo ""
read -p "送信してよろしいですか? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "送信をキャンセルしました"
    log_info "手動で送信する場合:"
    if [ "$CONNECTION_TYPE" = "USB" ]; then
        echo "  sudo cat $TEST1_OUTPUT > $DEVICE"
    else
        echo "  cat $TEST1_OUTPUT | nc $DEVICE 9100"
    fi
    exit 0
fi

log_info "送信中..."

if [ "$CONNECTION_TYPE" = "USB" ]; then
    # USB送信
    if [ "$EUID" -ne 0 ]; then
        log_info "sudo権限が必要です..."
        sudo cat "$TEST1_OUTPUT" > "$DEVICE"
    else
        cat "$TEST1_OUTPUT" > "$DEVICE"
    fi
elif [ "$CONNECTION_TYPE" = "NETWORK" ]; then
    # ネットワーク送信
    cat "$TEST1_OUTPUT" | nc "$DEVICE" 9100
fi

log_success "送信完了"
echo ""

log_info "プリンターの反応を確認してください:"
echo "  ✅ 成功のサイン:"
echo "    - 用紙が給紙される"
echo "    - 何かが印刷される"
echo "    - エラーランプが点灯しない"
echo ""
echo "  ❌ 失敗のサイン:"
echo "    - プリンターが無反応"
echo "    - エラーランプ点灯"
echo "    - エラーメッセージ表示"
echo ""

read -p "テスト1は成功しましたか? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_error "テスト1失敗"
    log_info "デバッグ情報:"
    echo "  1. プリンターのエラーメッセージを確認"
    echo "  2. CUPSログを確認: tail -f /var/log/cups/error_log"
    echo "  3. PHASE_2_5_TEST_GUIDE.md の「Step 3: エラー診断」を参照"
    exit 1
fi

log_success "Test 1: 成功"
echo ""

# ==============================================================================
# Step 3: Test 2 - より大きなテストパターン
# ==============================================================================

log_info "Step 3: Test 2 - チェッカーパターン（50x50ピクセル）"

# チェッカーパターン生成
log_info "チェッカーパターン生成中..."
python3 -c "
from PIL import Image
import numpy as np

img = np.zeros((50, 50), dtype=np.uint8)
img[::2, ::2] = 255
img[1::2, 1::2] = 255
Image.fromarray(img).save('/tmp/test_checker_50.tiff')
print('Created: /tmp/test_checker_50.tiff')
"

TEST2_OUTPUT="$OUTPUT_DIR/test2_checker.bin"

python3 "$SCRIPT_DIR/test_print_image.py" \
    /tmp/test_checker_50.tiff \
    "$CURVE_FILE" \
    -o "$TEST2_OUTPUT" \
    --dpi 720x720 \
    --paper 100x100

FILE_SIZE=$(stat -f%z "$TEST2_OUTPUT" 2>/dev/null || stat -c%s "$TEST2_OUTPUT" 2>/dev/null)
log_success "テスト2バイナリ生成完了: (${FILE_SIZE}バイト)"

read -p "Test 2を送信しますか? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "送信中..."

    if [ "$CONNECTION_TYPE" = "USB" ]; then
        if [ "$EUID" -ne 0 ]; then
            sudo cat "$TEST2_OUTPUT" > "$DEVICE"
        else
            cat "$TEST2_OUTPUT" > "$DEVICE"
        fi
    else
        cat "$TEST2_OUTPUT" | nc "$DEVICE" 9100
    fi

    log_success "Test 2送信完了"

    read -p "Test 2は成功しましたか? (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_success "Test 2: 成功"
    else
        log_warning "Test 2: 失敗（Test 1は成功）"
    fi
else
    log_info "Test 2をスキップ"
fi

echo ""

# ==============================================================================
# Step 4: Test 3 - グラデーション（実用テスト）
# ==============================================================================

log_info "Step 4: Test 3 - グラデーションパターン（実用テスト）"

read -p "Test 3（大きめの画像、時間がかかる）を実行しますか? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "A4グラデーション画像生成中（数秒かかります）..."

    python3 -c "
from PIL import Image, ImageDraw
import numpy as np

# A4 at 300 DPI
width, height = 2480, 3508
img = Image.new('L', (width, height), 255)
draw = ImageDraw.Draw(img)

# Gradient
for i in range(height):
    gray = int(255 * (1 - i / height))
    draw.line([(0, i), (width, i)], fill=gray)

img.save('/tmp/test_a4_gradient.tiff')
print(f'Created: {width}x{height} gradient')
"

    TEST3_OUTPUT="$OUTPUT_DIR/test3_a4_gradient.bin"

    log_info "ESC/P-Rバイナリ生成中（これは時間がかかります）..."
    python3 "$SCRIPT_DIR/test_print_image.py" \
        /tmp/test_a4_gradient.tiff \
        "$CURVE_FILE" \
        -o "$TEST3_OUTPUT" \
        --dpi 720x720 \
        --paper 210x297

    FILE_SIZE=$(stat -f%z "$TEST3_OUTPUT" 2>/dev/null || stat -c%s "$TEST3_OUTPUT" 2>/dev/null)
    log_success "Test 3バイナリ生成完了: (${FILE_SIZE}バイト)"

    log_warning "この送信は時間がかかる可能性があります"
    read -p "Test 3を送信しますか? (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "送信中（プログレスバーは表示されません）..."

        if [ "$CONNECTION_TYPE" = "USB" ]; then
            if [ "$EUID" -ne 0 ]; then
                sudo cat "$TEST3_OUTPUT" > "$DEVICE"
            else
                cat "$TEST3_OUTPUT" > "$DEVICE"
            fi
        else
            cat "$TEST3_OUTPUT" | nc "$DEVICE" 9100
        fi

        log_success "Test 3送信完了"

        read -p "Test 3は成功しましたか? (y/N): " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_success "Test 3: 成功"
        else
            log_warning "Test 3: 失敗"
        fi
    else
        log_info "Test 3をスキップ"
    fi
else
    log_info "Test 3をスキップ"
fi

echo ""

# ==============================================================================
# まとめ
# ==============================================================================

log_info "=== Phase 2.5 実機テスト完了 ==="
log_info "生成されたファイル:"
ls -lh "$OUTPUT_DIR"

echo ""
log_info "テスト結果を記録する場合:"
echo "  vim $OUTPUT_DIR/test_results.md"
echo ""
log_info "次のステップ:"
echo "  - エラーがあった場合: PHASE_2_5_TEST_GUIDE.md のトラブルシューティング参照"
echo "  - 成功した場合: Phase 2.5完了！"
echo ""
