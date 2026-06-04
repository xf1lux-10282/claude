"""
Precision EDN v2 - 逆カーブ生成モジュール

測定データから逆カーブ(補正カーブ)を自動生成
"""

import numpy as np
from scipy import interpolate
from typing import List, Tuple, Dict
import struct
import config
from curve_analyzer import CurveAnalyzer


class InverseCurveGenerator:
    """逆カーブ生成クラス"""

    def __init__(self, analyzer: CurveAnalyzer):
        self.analyzer = analyzer
        self.inverse_curve = None
        self.control_points = []

    def generate_inverse_curve(self) -> List[Tuple[int, float]]:
        """
        逆カーブを生成

        Version 2設計:
        - γ = 1.8
        - 弱い逆Sカーブ
        - 中間調基準: 入力128 → ネガ濃度0.70

        Returns:
            [(入力値, ネガ濃度), ...] の33点リスト
        """

        if not self.analyzer.data.has_print_data:
            # プリントデータがない場合は、ネガカーブのみから逆カーブを生成
            return self._generate_from_negative_only()

        # プリントデータがある場合は、完全な逆カーブを生成
        return self._generate_from_combined()

    def _generate_from_negative_only(self) -> List[Tuple[int, float]]:
        """
        ネガ濃度データのみから補正カーブを生成

        目標: プリンターの非線形を補正し、Version 2設計に近づける
        """
        input_vals, neg_dens = self.analyzer.data.get_negative_curve_data()

        # 実測カーブから逆関数を作成
        # ネガ濃度 → 入力値 の関係
        inverse_func = interpolate.CubicSpline(neg_dens[::-1], input_vals[::-1])

        # Version 2の理想カーブを生成
        ideal_curve = self._create_ideal_curve_v2()

        # 33点の制御点を生成
        control_points = []

        for step in config.STEP_VALUES:
            # この入力値が出すべき理想ネガ濃度
            ideal_density = ideal_curve(step)

            # 実際にその濃度を出すために必要な入力値
            try:
                corrected_input = float(inverse_func(ideal_density))
                corrected_input = np.clip(corrected_input, 0, 255)
            except:
                # 範囲外の場合はそのまま
                corrected_input = step

            control_points.append((step, corrected_input))

        # 端点を強制的に固定（0→0, 255→255）
        control_points[0] = (0, 0.0)
        control_points[-1] = (255, 255.0)

        # 単調性を強制（非単調な点を前の点と同じ値に修正）
        control_points = self._enforce_monotonicity(control_points)

        self.control_points = control_points

        if config.VERBOSE:
            print("\n=== 逆カーブ生成(ネガのみ) ===")
            print(f"  制御点数: {len(control_points)}")
            print(f"  入力0 → {control_points[0][1]:.1f}")
            print(f"  入力128 → {control_points[16][1]:.1f}")
            print(f"  入力255 → {control_points[-1][1]:.1f}")

        return control_points

    def _generate_from_combined(self) -> List[Tuple[int, float]]:
        """
        合成カーブ(入力→プリント)から完全な逆カーブを生成

        正しいロジック:
        - 入力デジタル値ごとに処理
        - 各入力値に対して、理想濃度を実現する補正値を求める
        """
        input_vals, print_dens = self.analyzer.data.get_combined_curve_data()

        if len(input_vals) == 0:
            return self._generate_from_negative_only()

        # 濃度範囲を取得
        print_min = min(print_dens)
        print_max = max(print_dens)
        print_range = print_max - print_min

        # 測定値を (inputDigital, measuredDensity) のペアに整理
        pairs = []
        for i, input_val in enumerate(input_vals):
            pairs.append({
                'inputDigital': input_val / 255.0,  # 正規化 (0-1)
                'measuredDensity': print_dens[i]
            })

        # 測定濃度でソート（逆補間のため）
        pairs.sort(key=lambda p: p['measuredDensity'])

        # 33点の制御点を生成
        control_points = []

        for step in config.STEP_VALUES:
            # 入力デジタル値（0-1）
            input_digital = step / 255.0

            # 目標濃度 = 入力値（線形）
            target_density_normalized = input_digital

            # 実際の濃度範囲にマッピング
            target_density = print_max - target_density_normalized * print_range

            # この濃度を実現する補正デジタル値を逆補間で求める
            corrected_digital = self._inverse_interpolate(pairs, target_density)

            # 0-255スケールに戻す
            corrected_input = corrected_digital * 255.0
            corrected_input = np.clip(corrected_input, 0, 255)

            control_points.append((step, corrected_input))

        # Version 2の弱逆S補正を適用
        control_points = self._apply_inverse_s_correction(control_points)

        # 端点を強制的に固定（0→0, 255→255）
        # 最初と最後の制御点を上書き
        control_points[0] = (0, 0.0)
        control_points[-1] = (255, 255.0)

        # 単調性を強制（非単調な点を前の点と同じ値に修正）
        control_points = self._enforce_monotonicity(control_points)

        self.control_points = control_points

        if config.VERBOSE:
            print("\n=== 逆カーブ生成(完全版) ===")
            print(f"  制御点数: {len(control_points)}")
            print(f"  入力0 → {control_points[0][1]:.1f}")
            print(f"  入力128 → {control_points[16][1]:.1f}")
            print(f"  入力255 → {control_points[-1][1]:.1f}")

        return control_points

    def _create_ideal_curve_v2(self):
        """
        Version 2の理想ネガ濃度カーブを生成

        - γ = 1.8
        - Dmin = 0.10
        - Dmax = 1.55
        - 中間調: 入力128 → 0.70
        """

        def ideal_curve(x):
            """入力値 → 理想ネガ濃度"""
            normalized = x / 255.0
            density = config.NEGATIVE_DMAX - config.NEGATIVE_RANGE * (normalized ** config.NEGATIVE_GAMMA)
            return density

        return ideal_curve

    def _inverse_interpolate(self, pairs: List[Dict], target_density: float) -> float:
        """
        目標濃度を実現するデジタル値を逆補間で求める

        Args:
            pairs: [{'inputDigital': float, 'measuredDensity': float}, ...]
                   measuredDensity でソート済み
            target_density: 目標濃度

        Returns:
            補正後のデジタル値（0-1）
        """
        if len(pairs) == 0:
            return 0.0

        min_density = pairs[0]['measuredDensity']
        max_density = pairs[-1]['measuredDensity']

        # 範囲外チェック
        if target_density <= min_density:
            return pairs[0]['inputDigital']
        if target_density >= max_density:
            return pairs[-1]['inputDigital']

        # 線形補間で逆算
        for i in range(len(pairs) - 1):
            d1 = pairs[i]['measuredDensity']
            d2 = pairs[i + 1]['measuredDensity']

            if d1 <= target_density <= d2:
                # 補間係数
                t = (target_density - d1) / (d2 - d1) if d2 != d1 else 0.0

                # デジタル値を補間
                v1 = pairs[i]['inputDigital']
                v2 = pairs[i + 1]['inputDigital']

                return v1 + t * (v2 - v1)

        # フォールバック（範囲内のはずだが念のため）
        return np.clip(target_density / max_density, 0.0, 1.0)

    def _apply_inverse_s_correction(self, control_points: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        弱い逆Sカーブ補正を適用

        Version 2設計:
        - シャドウ(0-64): わずかに持ち上げ
        - 中間調(64-192): 直線維持
        - ハイライト(192-255): 軽い圧縮
        """

        corrected = []

        for input_val, output_val in control_points:
            correction = 0

            if input_val <= 64:
                # シャドウ持ち上げ
                # 0→最大, 64→0 の線形補間
                factor = (64 - input_val) / 64.0
                correction = config.SHADOW_LIFT_MAX * factor

            elif input_val >= 192:
                # ハイライト圧縮
                # 192→0, 255→最大 の線形補間
                factor = (input_val - 192) / 63.0
                correction = -config.HIGHLIGHT_COMPRESS_MAX * factor

            # 補正適用
            corrected_output = output_val + correction
            corrected_output = np.clip(corrected_output, 0, 255)

            corrected.append((input_val, corrected_output))

        return corrected

    def _enforce_monotonicity(self, control_points: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        制御点の単調性を強制（線形補間による滑らかな修正）

        非単調な領域を検出し、その領域を線形補間で置き換え
        階調を保ちながら単調増加を保証
        """
        if len(control_points) <= 1:
            return control_points

        # まず非単調な領域を検出
        monotonic = list(control_points)

        i = 0
        while i < len(monotonic) - 1:
            # 非単調な領域の開始を検出
            if monotonic[i + 1][1] < monotonic[i][1]:
                # 非単調領域の終わりを見つける
                start_idx = i
                end_idx = i + 1

                # 次の単調増加点を見つける
                while end_idx < len(monotonic) - 1:
                    if monotonic[end_idx + 1][1] > monotonic[start_idx][1]:
                        break
                    end_idx += 1

                # 線形補間で非単調領域を置き換え
                start_input, start_output = monotonic[start_idx]
                end_input, end_output = monotonic[end_idx]

                # 線形補間
                for j in range(start_idx + 1, end_idx + 1):
                    inp = monotonic[j][0]
                    # 線形補間で値を計算
                    ratio = (inp - start_input) / (end_input - start_input)
                    interpolated = start_output + ratio * (end_output - start_output)
                    monotonic[j] = (inp, interpolated)

                if config.VERBOSE:
                    print(f"  単調性修正: 入力{start_input}-{end_input}を線形補間")

                i = end_idx
            else:
                i += 1

        return monotonic

    def get_curve_as_dict(self) -> Dict[int, float]:
        """制御点を辞書形式で取得"""
        return {int(inp): float(out) for inp, out in self.control_points}

    def get_curve_as_lut(self, resolution: int = 256) -> np.ndarray:
        """
        LUT(Look-Up Table)として取得

        Args:
            resolution: LUTの解像度 (デフォルト256)

        Returns:
            shape (resolution,) のnumpy配列
        """
        if len(self.control_points) == 0:
            return np.arange(resolution)

        # 制御点から補間
        inputs = [p[0] for p in self.control_points]
        outputs = [p[1] for p in self.control_points]

        # PCHIP補間（単調性を自動的に保証）
        # CubicSplineは振動を起こすため、PCHIPに変更
        pchip = interpolate.PchipInterpolator(inputs, outputs)

        # 0-255の範囲で補間
        x = np.linspace(0, 255, resolution)
        lut = pchip(x)

        # クリップ
        lut = np.clip(lut, 0, 255)

        return lut

    def save_acv_file(self, filepath: str):
        """
        Adobe Photoshop ACV (Curves) ファイルとして保存

        precision-ednと同じアルゴリズムを使用:
        1. 全256点の入出力ペアを作成
        2. 同一出力値の範囲を検出し、範囲の端点のみを制御点として使用
        3. 16点を超える場合は均等にダウンサンプリング
        4. Photoshop形式: (出力値, 入力値) の順でbig-endian

        Args:
            filepath: 保存先ファイルパス (.acv)
        """
        if len(self.control_points) == 0:
            raise ValueError("制御点が生成されていません")

        # ステップ1: 全256点の入出力ペアを作成
        lut = self.get_curve_as_lut(256)
        all_points = []
        for i in range(256):
            output_8bit = int(np.clip(lut[i], 0, 255))
            all_points.append({'input': i, 'output': output_8bit})

        # ステップ2: 同一出力値の範囲を検出し、各範囲の端点のみを制御点として使用
        key_points = [all_points[0]]  # 最初の点(0,0)は必須

        range_start = 0
        current_range_output = all_points[0]['output']

        for i in range(1, len(all_points)):
            current_output = all_points[i]['output']

            # 出力値が変化した場合
            if current_output != current_range_output:
                # 前の範囲の終点を追加（範囲が1点以上ある場合）
                if i - 1 > range_start:
                    key_points.append(all_points[i - 1])

                # 新しい範囲の開始点を追加
                key_points.append(all_points[i])

                range_start = i
                current_range_output = current_output

        # 最後の点は必ず追加（まだ追加されていない場合）
        if key_points[-1]['input'] != 255:
            key_points.append(all_points[255])

        # ステップ3: 16点に削減（Photoshopの制限）
        selected_points = key_points
        if len(key_points) > 16:
            # 均等にダウンサンプリング
            indices = np.linspace(0, len(key_points) - 1, 16).astype(int)
            selected_points = [key_points[i] for i in indices]
            # 最初と最後の点は必ず含める
            if selected_points[0]['input'] != 0:
                selected_points[0] = key_points[0]
            if selected_points[-1]['input'] != 255:
                selected_points[-1] = key_points[-1]

        # ACVフォーマット: バイナリ形式
        num_points = len(selected_points)

        with open(filepath, 'wb') as f:
            # Version 4 (Photoshop CS以降)
            f.write(struct.pack('>H', 4))

            # カーブ数: 1 (RGBマスターカーブのみ)
            f.write(struct.pack('>H', 1))

            # ポイント数
            f.write(struct.pack('>H', num_points))

            # カーブデータ（Photoshop形式: 出力値, 入力値の順）
            for point in selected_points:
                f.write(struct.pack('>HH', point['output'], point['input']))

    def apply_lut_to_values(self, input_values: List[float]) -> List[float]:
        """
        入力値のリストにLUTを適用

        Args:
            input_values: 入力値のリスト (0-255)

        Returns:
            LUT適用後の値のリスト
        """
        if len(self.control_points) == 0:
            return input_values

        # 制御点から補間関数を作成（PCHIP: 単調性を自動的に保証）
        inputs = [p[0] for p in self.control_points]
        outputs = [p[1] for p in self.control_points]
        pchip = interpolate.PchipInterpolator(inputs, outputs)

        # 各入力値にLUTを適用
        corrected_values = []
        for val in input_values:
            corrected = float(pchip(val))
            corrected = np.clip(corrected, 0, 255)
            corrected_values.append(corrected)

        return corrected_values


def generate_inverse_curve(analyzer: CurveAnalyzer) -> InverseCurveGenerator:
    """
    逆カーブを生成

    Args:
        analyzer: CurveAnalyzer

    Returns:
        InverseCurveGenerator
    """
    generator = InverseCurveGenerator(analyzer)
    generator.generate_inverse_curve()

    return generator


if __name__ == "__main__":
    print("=== Precision EDN v2 - 逆カーブ生成モジュール ===\n")
    print("このモジュールは main.py から呼び出されます")
