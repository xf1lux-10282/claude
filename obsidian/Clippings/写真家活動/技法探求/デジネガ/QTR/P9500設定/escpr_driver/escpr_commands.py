#!/usr/bin/env python3
"""
ESC/P-R Command Generator

EPSON SC-P9500/P9550向けESC/P-Rasterコマンド生成モジュール
"""

import struct


# ==============================================================================
# 基本的な初期化・終了コマンド
# ==============================================================================

# プリンター初期化
INIT_PRINTER = bytes([0x1B, 0x40])  # ESC @

# リモートモード開始
ENTER_REMOTE_MODE = bytes([
    0x1B, 0x28, 0x52,           # ESC ( R
    0x08, 0x00, 0x00, 0x00,     # データ長 (8バイト, little-endian 32bit)
    ord('R'), ord('E'), ord('M'), ord('O'), ord('T'), ord('E'), ord('1')
])

# ESC/P-Rモード設定
ESCPR_MODE = bytes([
    0x1B, ord('('), ord('R'),   # ESC ( R
    0x06, 0x00, 0x00, 0x00,     # データ長 (6バイト, little-endian 32bit)
    ord('E'), ord('S'), ord('C'), ord('P'), ord('R')
])

# ページ終了
END_PAGE = bytes([
    0x1B, ord('p'),             # ESC p
    0x01, 0x00, 0x00, 0x00,     # データ長 (1バイト)
    ord('e'), ord('n'), ord('d'), ord('p'),  # "endp"
    0x00
])

# ジョブ終了
END_JOB = bytes([
    0x1B, ord('j'),             # ESC j
    0x00, 0x00, 0x00, 0x00,     # データ長 (0バイト)
    ord('e'), ord('n'), ord('d'), ord('j')   # "endj"
])


# ==============================================================================
# ヘルパー関数
# ==============================================================================

def _make_escpr_command(cmd_char, cmd_name, data=b''):
    """
    ESC/P-Rコマンド生成のヘルパー関数

    Args:
        cmd_char: コマンド文字 (例: 'j', 'q', 'd')
        cmd_name: コマンド名 (例: "sets", "setq", "dsnd")
        data: コマンドデータ (bytes)

    Returns:
        bytes: 完全なESC/P-Rコマンド

    コマンド形式:
        ESC <cmd_char> <len_low> <len_high> 0x00 0x00 <cmd_name> <data>
    """
    cmd_name_bytes = cmd_name.encode('ascii')
    data_len = len(cmd_name_bytes) + len(data)

    # データ長を32bit little-endianで格納
    len_bytes = struct.pack('<I', data_len)

    cmd = bytearray([0x1B, ord(cmd_char)])
    cmd.extend(len_bytes)
    cmd.extend(cmd_name_bytes)
    cmd.extend(data)

    return bytes(cmd)


# ==============================================================================
# 用紙サイズ設定コマンド
# ==============================================================================

def make_size_command(width_mm, height_mm):
    """
    用紙サイズ設定コマンド生成

    Args:
        width_mm: 用紙幅（mm）
        height_mm: 用紙高さ（mm）

    Returns:
        bytes: ESC j "sets" コマンド

    Note:
        実際のデータ形式は暫定実装。
        実機テストで調整が必要な可能性あり。
    """
    # 単位: 0.01mm (例: 210mm = 21000)
    width_units = int(width_mm * 100)
    height_units = int(height_mm * 100)

    # 暫定実装: width, height を32bit little-endianで格納
    data = struct.pack('<II', width_units, height_units)

    return _make_escpr_command('j', 'sets', data)


# ==============================================================================
# 解像度・品質設定コマンド
# ==============================================================================

def make_quality_command(dpi_x, dpi_y, quality=1):
    """
    解像度・品質設定コマンド生成

    Args:
        dpi_x: 水平解像度（例: 2880）
        dpi_y: 垂直解像度（例: 1440）
        quality: 品質レベル（0=Draft, 1=Normal, 2=High）

    Returns:
        bytes: ESC q "setq" コマンド

    Note:
        実際のデータ形式は暫定実装。
        実機テストで調整が必要な可能性あり。
    """
    # 暫定実装: dpi_x, dpi_y, quality を格納
    data = struct.pack('<HHB', dpi_x, dpi_y, quality)

    return _make_escpr_command('q', 'setq', data)


# ==============================================================================
# ジョブ属性設定コマンド
# ==============================================================================

def make_job_command(color_mode=1, color_plane=1):
    """
    ジョブ属性設定コマンド生成

    Args:
        color_mode: 1=Grayscale, 2=Color
        color_plane: 1=Mono, 3=RGB, 4=CMYK

    Returns:
        bytes: ESC j "setj" コマンド

    Note:
        実際のデータ形式は暫定実装。
        実機テストで調整が必要な可能性あり。
    """
    # 暫定実装: color_mode, color_plane を格納
    data = struct.pack('<BB', color_mode, color_plane)

    return _make_escpr_command('j', 'setj', data)


# ==============================================================================
# ラスターデータ送信コマンド
# ==============================================================================

def send_raster_line(line_data):
    """
    1行分のラスターデータ送信コマンド生成

    Args:
        line_data: bytes, 1行分のピクセルデータ

    Returns:
        bytes: ESC d "dsnd" コマンド

    Note:
        非圧縮モード。将来的にRLE圧縮を実装予定。
    """
    return _make_escpr_command('d', 'dsnd', line_data)


# ==============================================================================
# 完全な初期化シーケンス
# ==============================================================================

def get_full_init_sequence():
    """
    完全な初期化シーケンス取得

    Returns:
        bytes: INIT_PRINTER + ENTER_REMOTE_MODE + ESCPR_MODE
    """
    return INIT_PRINTER + ENTER_REMOTE_MODE + ESCPR_MODE


# ==============================================================================
# テスト用
# ==============================================================================

if __name__ == '__main__':
    print("=== ESC/P-R Command Generator Test ===\n")

    # 初期化シーケンス
    init_seq = get_full_init_sequence()
    print(f"初期化シーケンス ({len(init_seq)} bytes):")
    print(init_seq.hex(' '))
    print()

    # 用紙サイズ設定（A4: 210mm x 297mm）
    size_cmd = make_size_command(210, 297)
    print(f"用紙サイズコマンド ({len(size_cmd)} bytes):")
    print(size_cmd.hex(' '))
    print()

    # 解像度設定（2880x1440 DPI）
    quality_cmd = make_quality_command(2880, 1440)
    print(f"解像度コマンド ({len(quality_cmd)} bytes):")
    print(quality_cmd.hex(' '))
    print()

    # ジョブ属性設定（Grayscale）
    job_cmd = make_job_command(color_mode=1, color_plane=1)
    print(f"ジョブ属性コマンド ({len(job_cmd)} bytes):")
    print(job_cmd.hex(' '))
    print()

    # ラスターデータ送信（10バイトのテストデータ）
    test_line = bytes([0xFF] * 10)
    raster_cmd = send_raster_line(test_line)
    print(f"ラスターデータコマンド ({len(raster_cmd)} bytes):")
    print(raster_cmd.hex(' '))
    print()

    # 終了コマンド
    print(f"ページ終了コマンド ({len(END_PAGE)} bytes):")
    print(END_PAGE.hex(' '))
    print()

    print(f"ジョブ終了コマンド ({len(END_JOB)} bytes):")
    print(END_JOB.hex(' '))
