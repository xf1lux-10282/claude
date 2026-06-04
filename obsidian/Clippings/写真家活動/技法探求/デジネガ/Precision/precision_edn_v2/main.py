#!/usr/bin/env python3
"""
Precision EDN v2 - メインプログラム

デジタルネガ キャリブレーション・解析ツール

使い方:
    python3 main.py --input data/measurement.csv
    python3 main.py --create-template
"""

import argparse
import os
import sys
from datetime import datetime

import config
from data_input import read_csv, create_template_csv, validate_data
from curve_analyzer import analyze_all
from inverse_curve import generate_inverse_curve
from lut_export import export_lut


def print_banner():
    """バナー表示"""
    print("=" * 70)
    print("  Precision EDN v2 - Digital Negative Calibration System")
    print("  プラチナプリント用デジタルネガ キャリブレーション")
    print("=" * 70)
    print(f"  Version: {config.VERSION}")
    print(f"  Date: {config.CREATED_DATE}")
    print("=" * 70)
    print()


def main():
    """メイン処理"""

    # コマンドライン引数
    parser = argparse.ArgumentParser(
        description="Precision EDN v2 - デジタルネガ キャリブレーション",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # テンプレートCSVを作成
  python3 main.py --create-template

  # 測定データを解析
  python3 main.py --input data/measurement.csv

  # 出力先を指定
  python3 main.py --input data/measurement.csv --output my_calibration

  # グラフ生成をスキップ
  python3 main.py --input data/measurement.csv --no-graphs
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        help='測定データCSVファイル'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='precision_edn_v2',
        help='出力ファイル名のベース (デフォルト: precision_edn_v2)'
    )

    parser.add_argument(
        '--create-template',
        action='store_true',
        help='測定データ入力用テンプレートCSVを作成'
    )

    parser.add_argument(
        '--no-graphs',
        action='store_true',
        help='グラフ生成をスキップ'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細な出力'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='最小限の出力'
    )

    args = parser.parse_args()

    # Verboseフラグ設定
    if args.verbose:
        config.VERBOSE = True
    if args.quiet:
        config.VERBOSE = False

    # バナー表示
    if not args.quiet:
        print_banner()

    # テンプレート作成モード
    if args.create_template:
        template_path = create_template_csv()
        print(f"\n✓ テンプレートCSVを作成しました:")
        print(f"  {template_path}")
        print("\nこのファイルに測定データを入力してください。")
        print("  - input: 入力値 (0-255)")
        print("  - negative_density: ネガ濃度")
        print("  - print_density: プリント濃度 (測定②完了後)")
        return 0

    # 入力ファイルチェック
    if not args.input:
        parser.print_help()
        print("\nエラー: --input または --create-template を指定してください")
        return 1

    if not os.path.exists(args.input):
        print(f"エラー: 入力ファイルが見つかりません: {args.input}")
        return 1

    try:
        # === 1. データ読み込み ===
        print("=== Step 1: データ読み込み ===\n")
        data = read_csv(args.input)

        # データ検証
        is_valid, warnings = validate_data(data)

        if warnings:
            print("\n⚠ 警告:")
            for warning in warnings:
                print(f"  - {warning}")
            print()

        # === 2. カーブ解析 ===
        print("\n=== Step 2: カーブ解析 ===")
        analyzer = analyze_all(data, generate_graphs=(not args.no_graphs))

        # === 3. 逆カーブ生成 ===
        print("\n=== Step 3: 逆カーブ生成 ===")
        generator = generate_inverse_curve(analyzer)

        # === 4. LUT/カーブ出力 ===
        print("\n=== Step 4: 出力 ===")
        output_files = export_lut(generator, basename=args.output)

        # === 完了 ===
        print("\n" + "=" * 70)
        print("  ✓ すべての処理が完了しました")
        print("=" * 70)

        print("\n出力ファイル:")
        for filepath in output_files:
            print(f"  - {filepath}")

        if not args.no_graphs:
            graphs_dir = config.GRAPHS_DIR
            print(f"\nグラフ:")
            print(f"  - {os.path.join(graphs_dir, 'analysis_curves.pdf')}")

        print("\n次のステップ:")
        print("  1. グラフで測定データを確認")
        print("  2. CUBE LUTまたはPhotoshopカーブを使用")
        print("  3. テストプリントで検証")
        print()

        return 0

    except FileNotFoundError as e:
        print(f"エラー: {e}")
        return 1

    except ValueError as e:
        print(f"エラー: {e}")
        return 1

    except Exception as e:
        print(f"予期しないエラー: {e}")
        if config.DEBUG:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
