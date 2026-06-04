#!/usr/bin/env python3
"""
Test Print Image with QuadToneRIP Curve

TIFFファイルを読み込み、QuadToneRIPカーブを適用して、
ESC/P-Rasterバイナリとして出力
"""

import sys
import argparse
import numpy as np
from PIL import Image

from escpr_driver import ESCPRDriver
from quad_parser import QuadCurveApplier


def load_image_as_grayscale(image_path):
    """
    画像をグレースケールとして読み込み

    Args:
        image_path: 画像ファイルパス

    Returns:
        numpy array, shape=(height, width), dtype=uint8
    """
    img = Image.open(image_path)

    # グレースケールに変換
    img_gray = img.convert('L')

    # numpy arrayに変換
    img_array = np.array(img_gray, dtype=np.uint8)

    return img_array


def print_image_with_curve(image_path, curve_file, output_file=None,
                           dpi_x=720, dpi_y=720,
                           width_mm=210, height_mm=297):
    """
    画像をQuadToneRIPカーブ適用して印刷

    Args:
        image_path: 入力画像ファイルパス
        curve_file: QuadToneRIP .quadファイルパス
        output_file: 出力先（Noneの場合はstdout）
        dpi_x: 水平解像度
        dpi_y: 垂直解像度
        width_mm: 用紙幅
        height_mm: 用紙高さ
    """
    print(f"Loading image: {image_path}", file=sys.stderr)
    img_data = load_image_as_grayscale(image_path)
    height, width = img_data.shape
    print(f"Image size: {width}x{height} pixels", file=sys.stderr)

    # QuadToneRIPカーブ読み込み
    print(f"Loading curve: {curve_file}", file=sys.stderr)
    curve_applier = QuadCurveApplier(curve_file)
    print(f"Available channels: {curve_applier.get_available_channels()}", file=sys.stderr)

    # カーブ適用
    print("Applying curve to image...", file=sys.stderr)
    img_curved = curve_applier.apply(img_data, channel='K')

    # ESC/P-Rドライバーで印刷
    print(f"Generating ESC/P-R data (output: {output_file or 'stdout'})...", file=sys.stderr)

    with ESCPRDriver(output_file) as driver:
        # 初期化
        driver.initialize()

        # ジョブ開始
        driver.start_job(width_mm=width_mm, height_mm=height_mm,
                        dpi_x=dpi_x, dpi_y=dpi_y,
                        color_mode=1, color_plane=1)

        # ページ開始
        driver.start_page()

        # 画像データ送信（行ごと）
        print(f"Sending {height} lines...", file=sys.stderr)
        for i, line in enumerate(img_curved):
            if i % 100 == 0:
                print(f"  Line {i}/{height}", file=sys.stderr)
            driver.print_line(line.tobytes())

        # ページ終了
        driver.end_page()

        # ジョブ終了
        driver.end_job()

    print("Done!", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='Print image with QuadToneRIP curve applied',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate binary to file
  python3 test_print_image.py input.tiff curve.quad -o output.bin

  # Generate binary to stdout (pipe to printer)
  python3 test_print_image.py input.tiff curve.quad > output.bin

  # Use specific DPI and paper size
  python3 test_print_image.py input.tiff curve.quad -o output.bin \\
    --dpi 2880x1440 --paper 210x297
        """
    )

    parser.add_argument('image', help='Input image file (TIFF, PNG, JPEG, etc.)')
    parser.add_argument('curve', help='QuadToneRIP .quad curve file')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)',
                       default=None)
    parser.add_argument('--dpi', help='Resolution as WIDTHxHEIGHT (default: 720x720)',
                       default='720x720')
    parser.add_argument('--paper', help='Paper size in mm as WIDTHxHEIGHT (default: 210x297 = A4)',
                       default='210x297')

    args = parser.parse_args()

    # DPI解析
    try:
        dpi_parts = args.dpi.split('x')
        dpi_x = int(dpi_parts[0])
        dpi_y = int(dpi_parts[1])
    except:
        print(f"Error: Invalid DPI format: {args.dpi}", file=sys.stderr)
        print("Expected format: WIDTHxHEIGHT (e.g., 2880x1440)", file=sys.stderr)
        sys.exit(1)

    # 用紙サイズ解析
    try:
        paper_parts = args.paper.split('x')
        width_mm = float(paper_parts[0])
        height_mm = float(paper_parts[1])
    except:
        print(f"Error: Invalid paper size format: {args.paper}", file=sys.stderr)
        print("Expected format: WIDTHxHEIGHT in mm (e.g., 210x297)", file=sys.stderr)
        sys.exit(1)

    # 印刷実行
    print(f"Settings:", file=sys.stderr)
    print(f"  DPI: {dpi_x}x{dpi_y}", file=sys.stderr)
    print(f"  Paper: {width_mm}x{height_mm} mm", file=sys.stderr)
    print("", file=sys.stderr)

    try:
        print_image_with_curve(args.image, args.curve, args.output,
                              dpi_x, dpi_y, width_mm, height_mm)
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
