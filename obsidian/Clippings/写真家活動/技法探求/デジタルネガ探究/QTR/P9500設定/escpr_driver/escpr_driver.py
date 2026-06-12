#!/usr/bin/env python3
"""
ESC/P-R Driver

EPSON SC-P9500/P9550向け最小限のESC/P-Rasterドライバー
"""

import sys
from escpr_commands import *


class ESCPRDriver:
    """ESC/P-R最小ドライバー"""

    def __init__(self, output_file=None):
        """
        Args:
            output_file: 出力先（Noneの場合はstdout.buffer）
        """
        if output_file:
            self.file = open(output_file, 'wb')
            self.auto_close = True
        else:
            self.file = sys.stdout.buffer
            self.auto_close = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.auto_close:
            self.close()

    def close(self):
        """プリンターデバイスを閉じる"""
        if self.file and self.auto_close:
            self.file.close()

    def send(self, data):
        """
        データ送信

        Args:
            data: bytes, 送信するデータ
        """
        self.file.write(data)
        self.file.flush()

    def initialize(self):
        """初期化シーケンス送信"""
        self.send(get_full_init_sequence())

    def start_job(self, width_mm=210, height_mm=297, dpi_x=2880, dpi_y=1440,
                  color_mode=1, color_plane=1):
        """
        ジョブ開始

        Args:
            width_mm: 用紙幅（mm）
            height_mm: 用紙高さ（mm）
            dpi_x: 水平解像度
            dpi_y: 垂直解像度
            color_mode: 1=Grayscale, 2=Color
            color_plane: 1=Mono, 3=RGB, 4=CMYK
        """
        self.send(make_size_command(width_mm, height_mm))
        self.send(make_quality_command(dpi_x, dpi_y))
        self.send(make_job_command(color_mode, color_plane))

    def start_page(self):
        """ページ開始（将来拡張用）"""
        pass

    def print_band(self, band_data):
        """
        バンドデータ印刷

        Args:
            band_data: numpy array or list of bytes, shape=(height, width)
                      各行は1行分のピクセルデータ（bytes）
        """
        for line in band_data:
            # numpy arrayの場合はbytesに変換
            if hasattr(line, 'tobytes'):
                line_bytes = line.tobytes()
            else:
                line_bytes = bytes(line)

            self.send(send_raster_line(line_bytes))

    def print_line(self, line_data):
        """
        1行分のデータ印刷

        Args:
            line_data: bytes, 1行分のピクセルデータ
        """
        self.send(send_raster_line(line_data))

    def end_page(self):
        """ページ終了"""
        self.send(END_PAGE)

    def end_job(self):
        """ジョブ終了"""
        self.send(END_JOB)


# ==============================================================================
# 便利関数
# ==============================================================================

def print_simple_test_pattern(output_file=None):
    """
    シンプルなテストパターン印刷

    Args:
        output_file: 出力先ファイル（Noneの場合はstdout）
    """
    with ESCPRDriver(output_file) as driver:
        # 初期化
        driver.initialize()

        # ジョブ開始（A4, 720x720 DPI でテスト）
        driver.start_job(width_mm=210, height_mm=297,
                        dpi_x=720, dpi_y=720,
                        color_mode=1, color_plane=1)

        # ページ開始
        driver.start_page()

        # 簡単なテストパターン: 10行 x 100バイト
        # 各行: 白→黒→白のパターン
        for i in range(10):
            # 最初の30バイトは白（0xFF）、次の40バイトは黒（0x00）、最後の30バイトは白
            line = bytes([0xFF] * 30 + [0x00] * 40 + [0xFF] * 30)
            driver.print_line(line)

        # ページ終了
        driver.end_page()

        # ジョブ終了
        driver.end_job()


# ==============================================================================
# テスト用
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='ESC/P-R Driver Test')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)',
                       default=None)
    parser.add_argument('--test', action='store_true',
                       help='Print simple test pattern')

    args = parser.parse_args()

    if args.test:
        print(f"Generating test pattern to: {args.output or 'stdout'}", file=sys.stderr)
        print_simple_test_pattern(args.output)
        print("Done!", file=sys.stderr)
    else:
        print("Usage: python3 escpr_driver.py --test [-o output.bin]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Example:", file=sys.stderr)
        print("  python3 escpr_driver.py --test -o test_output.bin", file=sys.stderr)
        print("  python3 escpr_driver.py --test > test_output.bin", file=sys.stderr)
