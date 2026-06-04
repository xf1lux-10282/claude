"""
Precision EDN v2 - LUTマージングモジュール

CUBE形式のLUTを読み込み、合成する機能を提供
"""

import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import re


class LUTMerger:
    """CUBE LUTマージングクラス"""

    def __init__(self):
        self.lut_size = 256
        self.base_lut = None
        self.correction_lut = None
        self.merged_lut = None

    def read_cube_lut(self, cube_path: str) -> np.ndarray:
        """
        CUBE LUTファイルを読み込む

        Args:
            cube_path: CUBEファイルのパス

        Returns:
            shape (256,) のLUT配列 (0-255の値)
        """
        cube_path = Path(cube_path)
        if not cube_path.exists():
            raise FileNotFoundError(f"CUBEファイルが見つかりません: {cube_path}")

        lut_data = []
        lut_size = None

        with open(cube_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # コメント行をスキップ
                if line.startswith('#'):
                    continue

                # LUT_3D_SIZE を取得
                if line.startswith('LUT_3D_SIZE'):
                    match = re.search(r'LUT_3D_SIZE\s+(\d+)', line)
                    if match:
                        lut_size = int(match.group(1))
                    continue

                # DOMAIN_MIN, DOMAIN_MAX をスキップ
                if line.startswith('DOMAIN_'):
                    continue

                # TITLE をスキップ
                if line.startswith('TITLE'):
                    continue

                # 空行をスキップ
                if not line:
                    continue

                # RGB値を読み込む
                parts = line.split()
                if len(parts) == 3:
                    try:
                        r, g, b = float(parts[0]), float(parts[1]), float(parts[2])
                        # グレースケールLUTなのでR値を使用（R=G=Bのはず）
                        lut_data.append(r)
                    except ValueError:
                        continue

        if lut_size is None:
            raise ValueError("LUT_3D_SIZEが見つかりません")

        if len(lut_data) != lut_size ** 3:
            raise ValueError(f"LUTデータサイズが不正です: {len(lut_data)} (期待値: {lut_size ** 3})")

        # 1D LUTを抽出（対角線の値）
        lut_1d = []
        for i in range(lut_size):
            # (i, i, i)の位置 = i * (lut_size^2 + lut_size + 1)
            index = i * (lut_size * lut_size + lut_size + 1)
            if index < len(lut_data):
                lut_1d.append(lut_data[index] * 255.0)  # 0-1 を 0-255 に変換

        # 256点にリサンプリング（必要な場合）
        if len(lut_1d) != 256:
            x_old = np.linspace(0, 255, len(lut_1d))
            x_new = np.arange(256)
            lut_1d = np.interp(x_new, x_old, lut_1d)
        else:
            lut_1d = np.array(lut_1d)

        return lut_1d

    def merge_luts(
        self,
        base_lut: np.ndarray,
        correction_lut: np.ndarray
    ) -> np.ndarray:
        """
        2つのLUTを合成（base → correction の順に適用）

        処理:
        1. 入力値に base_lut を適用 → 中間値
        2. 中間値に correction_lut を適用 → 出力値

        Args:
            base_lut: 既存のLUT (256 values, 0-255)
            correction_lut: 補正用LUT (256 values, 0-255)

        Returns:
            merged_lut: 合成されたLUT (256 values, 0-255)
        """
        if len(base_lut) != 256 or len(correction_lut) != 256:
            raise ValueError("LUTは256要素である必要があります")

        # 入力値 0-255
        input_values = np.arange(256)

        # Step 1: base_lut を適用
        intermediate_values = np.interp(input_values, np.arange(256), base_lut)

        # Step 2: correction_lut を適用
        output_values = np.interp(intermediate_values, np.arange(256), correction_lut)

        # クリップ
        output_values = np.clip(output_values, 0, 255)

        return output_values

    def merge_from_files(
        self,
        base_cube_path: str,
        correction_cube_path: str,
        output_cube_path: Optional[str] = None
    ) -> np.ndarray:
        """
        CUBEファイルから読み込んで合成

        Args:
            base_cube_path: ベースLUTのCUBEファイルパス
            correction_cube_path: 補正LUTのCUBEファイルパス
            output_cube_path: 出力CUBEファイルパス（Noneの場合は保存しない）

        Returns:
            merged_lut: 合成されたLUT (256 values)
        """
        # LUTを読み込む
        self.base_lut = self.read_cube_lut(base_cube_path)
        self.correction_lut = self.read_cube_lut(correction_cube_path)

        # 合成
        self.merged_lut = self.merge_luts(self.base_lut, self.correction_lut)

        # 保存（指定された場合）
        if output_cube_path:
            self.save_cube_lut(self.merged_lut, output_cube_path)

        return self.merged_lut

    def save_cube_lut(
        self,
        lut: np.ndarray,
        output_path: str,
        title: str = "Precision EDN v2 - Merged LUT"
    ):
        """
        LUTをCUBE形式で保存

        Args:
            lut: LUT配列 (256 values, 0-255)
            output_path: 出力ファイルパス
            title: LUTタイトル
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # LUT_3D_SIZE (64が一般的)
        lut_3d_size = 64

        with open(output_path, 'w', encoding='utf-8') as f:
            # ヘッダー
            f.write(f"TITLE \"{title}\"\n")
            f.write(f"LUT_3D_SIZE {lut_3d_size}\n")
            f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
            f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
            f.write("\n")

            # 256点のLUTを64x64x64の3D LUTに変換
            # グレースケールなので対角線上に値を配置
            for r_idx in range(lut_3d_size):
                for g_idx in range(lut_3d_size):
                    for b_idx in range(lut_3d_size):
                        # グレースケールなのでR=G=Bの場合のみ実際の値を使用
                        if r_idx == g_idx == b_idx:
                            # 0-255の入力値にマッピング
                            input_val = int(r_idx * 255.0 / (lut_3d_size - 1))
                            output_val = lut[input_val] / 255.0  # 0-1に正規化
                        else:
                            # 対角線以外は補間（単純化のためニュートラル値を使用）
                            r_norm = r_idx / (lut_3d_size - 1)
                            g_norm = g_idx / (lut_3d_size - 1)
                            b_norm = b_idx / (lut_3d_size - 1)

                            # 各チャンネルでLUTを適用
                            r_in = int(r_norm * 255)
                            g_in = int(g_norm * 255)
                            b_in = int(b_norm * 255)

                            r_out = lut[r_in] / 255.0
                            g_out = lut[g_in] / 255.0
                            b_out = lut[b_in] / 255.0

                            output_val = (r_out + g_out + b_out) / 3.0

                        # RGB値を書き込み（グレースケールなのですべて同じ値）
                        if isinstance(output_val, (int, float)):
                            f.write(f"{output_val:.6f} {output_val:.6f} {output_val:.6f}\n")
                        else:
                            f.write(f"{output_val:.6f} {output_val:.6f} {output_val:.6f}\n")


def merge_cube_luts(
    base_cube_path: str,
    correction_cube_path: str,
    output_cube_path: str
) -> np.ndarray:
    """
    便利関数: CUBE LUTファイルを読み込んで合成・保存

    Args:
        base_cube_path: ベースLUTのCUBEファイルパス
        correction_cube_path: 補正LUTのCUBEファイルパス
        output_cube_path: 出力CUBEファイルパス

    Returns:
        merged_lut: 合成されたLUT (256 values)
    """
    merger = LUTMerger()
    return merger.merge_from_files(base_cube_path, correction_cube_path, output_cube_path)


if __name__ == "__main__":
    print("=== Precision EDN v2 - LUTマージングモジュール ===\n")
    print("このモジュールは app.py から呼び出されます")
    print("\n使用例:")
    print("  from lut_merger import merge_cube_luts")
    print("  merged = merge_cube_luts('base.cube', 'correction.cube', 'merged.cube')")
