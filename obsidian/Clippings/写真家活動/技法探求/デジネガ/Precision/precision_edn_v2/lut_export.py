"""
Precision EDN v2 - LUT出力モジュール

各種フォーマットでLUT/カーブを出力
"""

import numpy as np
import csv
import os
from typing import List, Tuple
import config
from inverse_curve import InverseCurveGenerator


class LUTExporter:
    """LUT出力クラス"""

    def __init__(self, generator: InverseCurveGenerator):
        self.generator = generator
        self.output_files = []

    def export_all(self, output_dir: str = None, basename: str = "precision_edn_v2"):
        """
        すべての形式で出力

        Args:
            output_dir: 出力ディレクトリ
            basename: ファイル名のベース
        """
        if output_dir is None:
            output_dir = config.LUTS_DIR

        # 各形式で出力
        self.export_cube_lut(output_dir, basename)
        self.export_csv(output_dir, basename)
        self.export_photoshop_curve(output_dir, basename)
        self.export_acv(output_dir, basename)
        self.export_report(output_dir, basename)

        if config.VERBOSE:
            print(f"\n✓ すべてのLUT/カーブを出力しました")
            for filepath in self.output_files:
                print(f"  - {os.path.basename(filepath)}")

        return self.output_files

    def export_cube_lut(self, output_dir: str, basename: str):
        """
        CUBE LUT形式で出力

        Adobe製品、DaVinci Resolveなどで使用可能
        """
        filepath = os.path.join(output_dir, f"{basename}.cube")

        # LUT取得(256段階)
        lut = self.generator.get_curve_as_lut(resolution=config.LUT_RESOLUTION)

        with open(filepath, 'w') as f:
            # ヘッダー
            f.write("# Precision EDN v2 - Digital Negative Calibration LUT\n")
            f.write(f"# Version: {config.VERSION}\n")
            f.write(f"# Date: {config.CREATED_DATE}\n")
            f.write(f"# Target: {config.PAPER_TYPE} Platinum Print\n")
            f.write(f"# Printer: {config.PRINTER_MODEL}\n")
            f.write(f"# Media: {config.MEDIA_TYPE}\n")
            f.write("\n")
            f.write("LUT_1D_SIZE 256\n")
            f.write("\n")

            # LUTデータ
            for value in lut:
                # 0-1の範囲に正規化
                normalized = value / 255.0
                # グレースケールなのでR=G=B
                f.write(f"{normalized:.6f} {normalized:.6f} {normalized:.6f}\n")

        self.output_files.append(filepath)

        if config.VERBOSE:
            print(f"  ✓ CUBE LUT: {os.path.basename(filepath)}")

        return filepath

    def export_csv(self, output_dir: str, basename: str):
        """
        CSV形式で33点制御点を出力
        """
        filepath = os.path.join(output_dir, f"{basename}_curve.csv")

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # ヘッダー
            writer.writerow(['input', 'output', 'note'])

            # 制御点
            for input_val, output_val in self.generator.control_points:
                note = ""
                if input_val == 0:
                    note = "Dmax"
                elif input_val == 128:
                    note = "Midtone"
                elif input_val == 255:
                    note = "Dmin"

                writer.writerow([int(input_val), f"{output_val:.2f}", note])

        self.output_files.append(filepath)

        if config.VERBOSE:
            print(f"  ✓ CSV: {os.path.basename(filepath)}")

        return filepath

    def export_photoshop_curve(self, output_dir: str, basename: str):
        """
        Photoshop用カーブデータをテキストで出力

        使い方:
        1. Photoshopでトーンカーブを開く
        2. このファイルの値を手動で入力
        """
        filepath = os.path.join(output_dir, f"{basename}_photoshop_curve.txt")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Precision EDN v2 - Photoshop Tone Curve\n")
            f.write("# \n")
            f.write("# 使い方:\n")
            f.write("# 1. Photoshopでトーンカーブレイヤーを作成\n")
            f.write("# 2. 以下の制御点を追加\n")
            f.write("#    横軸(入力) → 縦軸(出力)\n")
            f.write("# \n")
            f.write("# 注: Photoshopは0-255の値を使用\n")
            f.write("# \n\n")

            f.write("制御点 (33点):\n")
            f.write("=" * 50 + "\n\n")

            for i, (input_val, output_val) in enumerate(self.generator.control_points):
                marker = ""
                if input_val == 0:
                    marker = "  ← Dmax"
                elif input_val == 128:
                    marker = "  ← Midtone (中間調)"
                elif input_val == 255:
                    marker = "  ← Dmin"

                f.write(f"点{i+1:2d}: 入力 {int(input_val):3d} → 出力 {int(round(output_val)):3d}{marker}\n")

            f.write("\n" + "=" * 50 + "\n\n")

            # グラデーションマップ用のRGB値
            f.write("グラデーションマップ用 (33ストップ):\n")
            f.write("=" * 50 + "\n\n")

            for i, (input_val, output_val) in enumerate(self.generator.control_points):
                # 入力値の位置(%)
                position = (input_val / 255.0) * 100

                # 出力値をRGB値に変換
                rgb = int(round(output_val))

                f.write(f"位置 {position:6.2f}%: RGB({rgb:3d}, {rgb:3d}, {rgb:3d})\n")

        self.output_files.append(filepath)

        if config.VERBOSE:
            print(f"  ✓ Photoshop用: {os.path.basename(filepath)}")

        return filepath

    def export_acv(self, output_dir: str, basename: str):
        """
        Photoshop ACV (Curves) ファイル形式で出力

        Photoshopのカーブツールで直接読み込み可能
        """
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"{basename}.acv")

        # InverseCurveGeneratorのsave_acv_fileメソッドを呼び出し
        self.generator.save_acv_file(filepath)

        self.output_files.append(filepath)

        if config.VERBOSE:
            print(f"  ✓ Photoshop ACV: {os.path.basename(filepath)}")

        return filepath

    def export_report(self, output_dir: str, basename: str):
        """
        解析レポートをテキストで出力
        """
        filepath = os.path.join(output_dir, f"{basename}_report.txt")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("  Precision EDN v2 - キャリブレーションレポート\n")
            f.write("=" * 70 + "\n\n")

            # バージョン情報
            f.write(f"バージョン: {config.VERSION}\n")
            f.write(f"作成日: {config.CREATED_DATE}\n\n")

            # 環境情報
            f.write("=== 環境設定 ===\n\n")
            f.write(f"プリンター: {config.PRINTER_MODEL}\n")
            f.write(f"メディア: {config.MEDIA_TYPE}\n")
            f.write(f"用紙: {config.PAPER_TYPE}\n")
            f.write(f"FO濃度: {config.FO_CONCENTRATION}\n")
            f.write(f"UV光源: {config.UV_SOURCE}\n\n")

            # Version 2設計パラメータ
            f.write("=== Version 2 設計パラメータ ===\n\n")
            f.write(f"ネガγ: {config.NEGATIVE_GAMMA}\n")
            f.write(f"ネガDmin: {config.NEGATIVE_DMIN}\n")
            f.write(f"ネガDmax: {config.NEGATIVE_DMAX}\n")
            f.write(f"ネガ濃度レンジ: {config.NEGATIVE_RANGE}\n")
            f.write(f"中間調基準: 入力{config.MIDTONE_INPUT} → ネガ濃度{config.MIDTONE_NEGATIVE_DENSITY}\n")
            f.write(f"シャドウ持ち上げ: 最大{config.SHADOW_LIFT_MAX}\n")
            f.write(f"ハイライト圧縮: 最大{config.HIGHLIGHT_COMPRESS_MAX}\n\n")

            # 測定結果
            if hasattr(self.generator.analyzer, 'analysis_results'):
                results = self.generator.analyzer.analysis_results

                if 'negative' in results:
                    f.write("=== ネガ特性(測定①) ===\n\n")
                    neg = results['negative']
                    f.write(f"Dmin: {neg['dmin']:.3f}\n")
                    f.write(f"Dmax: {neg['dmax']:.3f}\n")
                    f.write(f"濃度レンジ: {neg['range']:.3f}\n")

                    if neg['linear_region']:
                        lr = neg['linear_region']
                        f.write(f"線形領域: 入力{lr['start']:.0f} - {lr['end']:.0f} (R²={lr['r_squared']:.4f})\n")

                    f.write("\n")

                if 'print' in results and results['print']:
                    f.write("=== プリント特性(測定②) ===\n\n")
                    prt = results['print']
                    f.write(f"Dmin: {prt['dmin']:.3f}\n")
                    f.write(f"Dmax: {prt['dmax']:.3f}\n")
                    f.write(f"濃度レンジ: {prt['range']:.3f}\n")
                    f.write(f"露光レンジ: {prt['exposure_range_ev']:.2f} EV\n\n")

            # 制御点サマリー
            f.write("=== 補正カーブ(制御点) ===\n\n")
            f.write("重要なポイント:\n")

            for input_val, output_val in self.generator.control_points:
                if input_val in [0, 64, 128, 192, 255]:
                    correction = output_val - input_val
                    f.write(f"  入力{input_val:3d} → 出力{output_val:6.2f} (補正: {correction:+6.2f})\n")

            f.write("\n")

            # 使用方法
            f.write("=== 使用方法 ===\n\n")
            f.write("1. CUBE LUTを使用する場合:\n")
            f.write(f"   - {basename}.cube をPhotoshop/Lightroomに読み込み\n")
            f.write("   - カラールックアップで適用\n\n")

            f.write("2. Photoshopトーンカーブで使用する場合:\n")
            f.write(f"   - {basename}_photoshop_curve.txt を参照\n")
            f.write("   - 33点の制御点を手動で入力\n\n")

            f.write("3. 印刷設定:\n")
            f.write("   - カラーマネジメント: OFF\n")
            f.write("   - すべての補正: OFF\n")
            f.write("   - 16bit TIFFで出力\n\n")

            f.write("=" * 70 + "\n")

        self.output_files.append(filepath)

        if config.VERBOSE:
            print(f"  ✓ レポート: {os.path.basename(filepath)}")

        return filepath


def export_lut(generator: InverseCurveGenerator, output_dir: str = None, basename: str = "precision_edn_v2"):
    """
    LUT/カーブをすべての形式で出力

    Args:
        generator: InverseCurveGenerator
        output_dir: 出力ディレクトリ
        basename: ファイル名のベース

    Returns:
        出力ファイルパスのリスト
    """
    exporter = LUTExporter(generator)
    return exporter.export_all(output_dir, basename)


if __name__ == "__main__":
    print("=== Precision EDN v2 - LUT出力モジュール ===\n")
    print("このモジュールは main.py から呼び出されます")
