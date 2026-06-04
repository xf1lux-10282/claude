"""
Precision EDN v2 - カーブ解析モジュール

測定データの解析とグラフ可視化
"""

import numpy as np
from scipy import interpolate
from scipy.stats import linregress
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUIなし環境用
import matplotlib.font_manager as fm
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from typing import Tuple, List, Optional, Dict
import config
from data_input import MeasurementData

# 日本語フォント設定
try:
    # matplotlib font managerから利用可能な日本語フォントを探す
    from matplotlib import font_manager

    # 優先順位付きフォントリスト
    japanese_font_candidates = [
        'A-OTF Gothic MB101 Pro',
        'A-OTF Ryumin Pro',
        'Apple SD Gothic Neo',
        '07YasashisaGothic',
        'Hiragino Sans',
        'Hiragino Kaku Gothic Pro',
        'Yu Gothic',
    ]

    available_fonts = [f.name for f in font_manager.fontManager.ttflist]

    font_found = False
    for font_name in japanese_font_candidates:
        if font_name in available_fonts:
            plt.rcParams['font.family'] = font_name
            font_found = True
            if config.VERBOSE:
                print(f"日本語フォント設定成功: {font_name}")
            break

    if not font_found:
        # フォールバック: sans-serifに日本語フォントを追加
        plt.rcParams['font.sans-serif'] = japanese_font_candidates + plt.rcParams['font.sans-serif']
        if config.VERBOSE:
            print(f"フォント設定: sans-serifフォールバック")

    plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け対策

except Exception as e:
    print(f"日本語フォント設定エラー: {e}")
    import traceback
    traceback.print_exc()


class CurveAnalyzer:
    """カーブ解析クラス"""

    def __init__(self, data: MeasurementData):
        self.data = data
        self.negative_curve = None
        self.print_curve = None
        self.combined_curve = None
        self.analysis_results = {}

    def analyze_negative_curve(self):
        """
        入力値 → ネガ濃度カーブを解析

        - 線形領域の検出
        - Dmin/Dmax
        - 飽和領域の検出
        """
        input_vals, neg_dens = self.data.get_negative_curve_data()

        # 入力値でソート（CubicSplineは厳密に増加する必要がある）
        sorted_indices = np.argsort(input_vals)
        input_vals_sorted = [input_vals[i] for i in sorted_indices]
        neg_dens_sorted = [neg_dens[i] for i in sorted_indices]

        # 基本統計（元のデータで計算）
        dmin = min(neg_dens)
        dmax = max(neg_dens)
        density_range = dmax - dmin

        # スプライン補間（ソート済みデータを使用）
        self.negative_curve = interpolate.CubicSpline(input_vals_sorted, neg_dens_sorted)

        # 線形領域検出
        linear_region = self._detect_linear_region(input_vals, neg_dens)

        # 飽和領域検出
        saturation_regions = self._detect_saturation(input_vals, neg_dens)

        self.analysis_results['negative'] = {
            'dmin': dmin,
            'dmax': dmax,
            'range': density_range,
            'linear_region': linear_region,
            'saturation_regions': saturation_regions,
            'input_at_dmin': input_vals[neg_dens.index(dmin)],
            'input_at_dmax': input_vals[neg_dens.index(dmax)]
        }

        if config.VERBOSE:
            print("\n=== ネガ特性解析 ===")
            print(f"  Dmin: {dmin:.3f} (入力値 {self.analysis_results['negative']['input_at_dmin']})")
            print(f"  Dmax: {dmax:.3f} (入力値 {self.analysis_results['negative']['input_at_dmax']})")
            print(f"  濃度レンジ: {density_range:.3f}")
            if linear_region:
                print(f"  線形領域: 入力値 {linear_region['start']:.0f} - {linear_region['end']:.0f} (R²={linear_region['r_squared']:.4f})")

        return self.analysis_results['negative']

    def analyze_print_curve(self):
        """
        ネガ濃度 → プリント濃度カーブを解析
        """
        if not self.data.has_print_data:
            if config.VERBOSE:
                print("\n測定②(プリント濃度)データなし")
            return None

        neg_dens, print_dens = self.data.get_print_curve_data()

        if len(neg_dens) == 0:
            return None

        # ネガ濃度でソート（CubicSplineは厳密に増加する必要がある）
        sorted_indices = np.argsort(neg_dens)
        neg_dens_sorted = [neg_dens[i] for i in sorted_indices]
        print_dens_sorted = [print_dens[i] for i in sorted_indices]

        # 重複した値を処理（厳密に増加させる）
        neg_dens_unique = []
        print_dens_unique = []
        epsilon = 1e-6

        for i, (nd, pd) in enumerate(zip(neg_dens_sorted, print_dens_sorted)):
            if i == 0 or nd > neg_dens_unique[-1]:
                neg_dens_unique.append(nd)
                print_dens_unique.append(pd)
            else:
                # 重複している場合は微小値を加算
                neg_dens_unique.append(neg_dens_unique[-1] + epsilon)
                print_dens_unique.append(pd)
                epsilon += 1e-6

        # 基本統計（元のデータで計算）
        print_dmin = min(print_dens)
        print_dmax = max(print_dens)
        print_range = print_dmax - print_dmin

        # スプライン補間（外挿を防ぐためにextrapolate=Falseを指定）
        # 範囲外の値にはfill_valueで端点の値を使用
        original_spline = interpolate.CubicSpline(
            neg_dens_unique,
            print_dens_unique,
            extrapolate=False
        )

        # 範囲外の値を処理するためのラッパー関数
        def safe_print_curve(x):
            x_arr = np.atleast_1d(x)
            result = np.zeros_like(x_arr, dtype=float)
            for i, val in enumerate(x_arr):
                if val < neg_dens_unique[0]:
                    result[i] = print_dens_unique[0]
                elif val > neg_dens_unique[-1]:
                    result[i] = print_dens_unique[-1]
                else:
                    result[i] = original_spline(val)
            return result[0] if np.isscalar(x) else result

        # ラッパー関数を保存
        self._original_print_curve = original_spline
        self.print_curve = safe_print_curve

        # 露光レンジをEVで計算
        # ネガ濃度差 → 光量比 → EV
        neg_range = max(neg_dens) - min(neg_dens)
        exposure_ratio = 10 ** neg_range  # 10^D = 透過率の逆数比
        exposure_range_ev = np.log2(exposure_ratio)

        self.analysis_results['print'] = {
            'dmin': print_dmin,
            'dmax': print_dmax,
            'range': print_range,
            'negative_density_range': neg_range,
            'exposure_range_ev': exposure_range_ev,
            'neg_at_print_dmin': neg_dens[print_dens.index(print_dmin)],
            'neg_at_print_dmax': neg_dens[print_dens.index(print_dmax)]
        }

        if config.VERBOSE:
            print("\n=== プリント特性解析 ===")
            print(f"  Dmin: {print_dmin:.3f}")
            print(f"  Dmax: {print_dmax:.3f}")
            print(f"  濃度レンジ: {print_range:.3f}")
            print(f"  露光レンジ: {exposure_range_ev:.2f} EV")

        return self.analysis_results['print']

    def analyze_combined_curve(self):
        """
        入力値 → プリント濃度の合成カーブを解析
        """
        if not self.data.has_print_data:
            return None

        input_vals, print_dens = self.data.get_combined_curve_data()

        if len(input_vals) == 0:
            return None

        # 入力値でソート（CubicSplineは厳密に増加する必要がある）
        sorted_indices = np.argsort(input_vals)
        input_vals_sorted = [input_vals[i] for i in sorted_indices]
        print_dens_sorted = [print_dens[i] for i in sorted_indices]

        # 重複した値を処理（厳密に増加させる）
        input_vals_unique = []
        print_dens_unique = []
        epsilon = 1e-6

        for i, (iv, pd) in enumerate(zip(input_vals_sorted, print_dens_sorted)):
            if i == 0 or iv > input_vals_unique[-1]:
                input_vals_unique.append(iv)
                print_dens_unique.append(pd)
            else:
                # 重複している場合は微小値を加算
                input_vals_unique.append(input_vals_unique[-1] + epsilon)
                print_dens_unique.append(pd)
                epsilon += 1e-6

        # スプライン補間
        self.combined_curve = interpolate.CubicSpline(input_vals_unique, print_dens_unique)

        # 中間調(入力128)でのプリント濃度
        midtone_print_density = self.combined_curve(config.MIDTONE_INPUT)

        self.analysis_results['combined'] = {
            'midtone_input': config.MIDTONE_INPUT,
            'midtone_print_density': midtone_print_density
        }

        if config.VERBOSE:
            print("\n=== 合成特性解析 ===")
            print(f"  入力{config.MIDTONE_INPUT}でのプリント濃度: {midtone_print_density:.3f}")

        return self.analysis_results['combined']

    def _detect_linear_region(self, x, y):
        """
        線形領域を検出

        Returns:
            dict or None: {'start': float, 'end': float, 'r_squared': float}
        """
        if len(x) < 5:
            return None

        best_r2 = 0
        best_region = None

        # ウィンドウサイズを変えて線形性をチェック
        for window_size in range(max(5, len(x) // 2), len(x)):
            for start_idx in range(len(x) - window_size + 1):
                end_idx = start_idx + window_size

                x_window = x[start_idx:end_idx]
                y_window = y[start_idx:end_idx]

                slope, intercept, r_value, p_value, std_err = linregress(x_window, y_window)
                r2 = r_value ** 2

                if r2 > best_r2 and r2 > config.LINEAR_REGION_R2_THRESHOLD:
                    best_r2 = r2
                    best_region = {
                        'start': x_window[0],
                        'end': x_window[-1],
                        'r_squared': r2,
                        'slope': slope,
                        'intercept': intercept
                    }

        return best_region

    def _detect_saturation(self, x, y):
        """
        飽和領域を検出(傾きが小さい領域)
        """
        if len(x) < 3:
            return []

        saturation_regions = []

        # 各点での傾きを計算
        for i in range(1, len(x) - 1):
            slope = abs((y[i+1] - y[i-1]) / (x[i+1] - x[i-1]))

            if slope < config.SATURATION_SLOPE_THRESHOLD:
                saturation_regions.append({
                    'input': x[i],
                    'density': y[i],
                    'slope': slope
                })

        return saturation_regions

    def generate_graphs(self, output_dir: str = None):
        """
        解析グラフを生成

        - 入力値 → ネガ濃度
        - ネガ濃度 → プリント濃度
        - 入力値 → プリント濃度(合成)
        """
        if output_dir is None:
            output_dir = config.GRAPHS_DIR

        # スタイル設定
        plt.style.use('seaborn-v0_8-whitegrid')

        # フォント設定を再確認（グラフ生成直前）
        plt.rcParams['font.family'] = 'A-OTF Gothic MB101 Pro'
        plt.rcParams['axes.unicode_minus'] = False

        # 3つのサブプロット
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # --- グラフ1: 入力値 → ネガ濃度 ---
        ax1 = axes[0]
        input_vals, neg_dens = self.data.get_negative_curve_data()

        # 実測点
        ax1.scatter(input_vals, neg_dens, color=config.COLOR_NEGATIVE,
                   s=50, alpha=0.7, label='実測値', zorder=3)

        # 補間曲線
        if self.negative_curve is not None:
            x_smooth = np.linspace(min(input_vals), max(input_vals), 256)
            y_smooth = self.negative_curve(x_smooth)
            ax1.plot(x_smooth, y_smooth, color=config.COLOR_NEGATIVE,
                    linewidth=2, label='補間カーブ', alpha=0.8)

        # 線形領域のハイライト
        if 'negative' in self.analysis_results and self.analysis_results['negative']['linear_region']:
            lr = self.analysis_results['negative']['linear_region']
            ax1.axvspan(lr['start'], lr['end'], alpha=0.1, color='green',
                       label=f"線形領域 (R²={lr['r_squared']:.3f})")

        ax1.set_xlabel('入力値 (0-255)', fontsize=12)
        ax1.set_ylabel('ネガ濃度', fontsize=12)
        ax1.set_title('プリンター特性\n入力値 → ネガ濃度', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=10)
        # 軸反転を削除：下が0、上が大きい値で表示

        # --- グラフ2: ネガ濃度 → プリント濃度 ---
        ax2 = axes[1]

        if self.data.has_print_data:
            neg_dens_p, print_dens = self.data.get_print_curve_data()

            if len(neg_dens_p) > 0:
                # 実測点
                ax2.scatter(neg_dens_p, print_dens, color=config.COLOR_PRINT,
                           s=50, alpha=0.7, label='実測値', zorder=3)

                # 補間曲線
                if self.print_curve is not None:
                    x_smooth = np.linspace(min(neg_dens_p), max(neg_dens_p), 256)
                    y_smooth = self.print_curve(x_smooth)
                    ax2.plot(x_smooth, y_smooth, color=config.COLOR_PRINT,
                            linewidth=2, label='補間カーブ', alpha=0.8)

                ax2.set_xlabel('ネガ濃度', fontsize=12)
                ax2.set_ylabel('プリント濃度', fontsize=12)
                ax2.set_title('プラチナプリント特性\nネガ濃度 → プリント濃度', fontsize=14, fontweight='bold')
                ax2.grid(True, alpha=0.3)
                ax2.legend(fontsize=10)
        else:
            ax2.text(0.5, 0.5, 'プリントデータなし', ha='center', va='center',
                    transform=ax2.transAxes, fontsize=14, color='gray')
            ax2.set_xlabel('ネガ濃度', fontsize=12)
            ax2.set_ylabel('プリント濃度', fontsize=12)
            ax2.set_title('プラチナプリント特性', fontsize=14, fontweight='bold')

        # --- グラフ3: プリント濃度 → 入力値(合成、軸入れ替え) ---
        ax3 = axes[2]

        if self.data.has_print_data:
            input_vals_c, print_dens_c = self.data.get_combined_curve_data()

            if len(input_vals_c) > 0:
                # 単調性を保証: 濃度でソートして単調減少を確認
                sorted_pairs = sorted(zip(print_dens_c, input_vals_c), key=lambda p: p[0])
                print_dens_sorted = [p[0] for p in sorted_pairs]
                input_vals_sorted = [p[1] for p in sorted_pairs]

                # 単調減少を強制（入力値は濃度が増えると減少すべき）
                monotonic_print_dens = []
                monotonic_input_vals = []

                for i, (pd, iv) in enumerate(zip(print_dens_sorted, input_vals_sorted)):
                    if i == 0:
                        monotonic_print_dens.append(pd)
                        monotonic_input_vals.append(iv)
                    else:
                        # 入力値が前より小さい場合のみ採用（単調減少）
                        if iv < monotonic_input_vals[-1]:
                            monotonic_print_dens.append(pd)
                            monotonic_input_vals.append(iv)

                # 実測点（X軸=濃度、Y軸=入力値）
                ax3.scatter(monotonic_print_dens, monotonic_input_vals, color=config.COLOR_COMBINED,
                           s=50, alpha=0.7, label='実測値', zorder=3)

                # 補間曲線（単調減少を保証）
                if len(monotonic_print_dens) >= 3:
                    try:
                        # 濃度 → 入力値 の補間
                        combined_curve_swapped = interpolate.CubicSpline(
                            monotonic_print_dens, monotonic_input_vals
                        )
                        x_smooth = np.linspace(min(monotonic_print_dens),
                                              max(monotonic_print_dens), 256)
                        y_smooth = combined_curve_swapped(x_smooth)
                        ax3.plot(x_smooth, y_smooth, color=config.COLOR_COMBINED,
                                linewidth=2, label='補間カーブ', alpha=0.8)
                    except:
                        pass

                # 理想線（濃度が増えると入力値は線形に減少）
                ideal_min_dens = min(monotonic_print_dens)
                ideal_max_dens = max(monotonic_print_dens)
                ideal_min_input = 0
                ideal_max_input = 255

                x_ideal = np.linspace(ideal_min_dens, ideal_max_dens, 256)
                y_ideal = np.linspace(ideal_max_input, ideal_min_input, 256)
                ax3.plot(x_ideal, y_ideal, '--', color=config.COLOR_TARGET,
                        linewidth=1.5, label='理想(リニア)', alpha=0.6)

                ax3.set_xlabel('プリント濃度', fontsize=12)
                ax3.set_ylabel('入力値 (0-255)', fontsize=12)
                ax3.set_title('合成特性\nプリント濃度 → 入力値', fontsize=14, fontweight='bold')
                ax3.grid(True, alpha=0.3)
                ax3.legend(fontsize=10)
                ax3.invert_yaxis()  # Y軸を反転：255が上、0が下
        else:
            ax3.text(0.5, 0.5, 'プリントデータなし', ha='center', va='center',
                    transform=ax3.transAxes, fontsize=14, color='gray')
            ax3.set_xlabel('入力値', fontsize=12)
            ax3.set_ylabel('プリント濃度', fontsize=12)
            ax3.set_title('合成特性', fontsize=14, fontweight='bold')

        plt.tight_layout()

        # 保存（PDFとPNG両方）
        output_path_pdf = os.path.join(output_dir, 'analysis_curves.pdf')
        output_path_png = os.path.join(output_dir, 'analysis_curves.png')

        plt.savefig(output_path_pdf, dpi=config.GRAPH_DPI, bbox_inches='tight')
        plt.savefig(output_path_png, dpi=config.GRAPH_DPI, bbox_inches='tight')
        plt.close()

        if config.VERBOSE:
            print(f"\n✓ グラフを保存: {output_path_pdf}")
            print(f"✓ グラフを保存: {output_path_png}")

        return output_path_png  # Streamlit表示用にPNGパスを返す


def analyze_all(data: MeasurementData, generate_graphs: bool = True):
    """
    すべての解析を実行

    Args:
        data: 測定データ
        generate_graphs: グラフ生成するか

    Returns:
        CurveAnalyzer
    """
    analyzer = CurveAnalyzer(data)

    # 解析実行
    analyzer.analyze_negative_curve()
    analyzer.analyze_print_curve()
    analyzer.analyze_combined_curve()

    # グラフ生成
    if generate_graphs:
        analyzer.generate_graphs()

    return analyzer


def generate_preview_graph(analyzer: 'CurveAnalyzer', inverse_gen, output_dir: str = None):
    """
    LUT適用後のプレビューグラフを生成

    Args:
        analyzer: CurveAnalyzer
        inverse_gen: InverseCurveGenerator
        output_dir: 出力ディレクトリ

    Returns:
        str: 保存されたグラフのパス
    """
    if output_dir is None:
        output_dir = config.GRAPHS_DIR

    # スタイル設定
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.family'] = 'A-OTF Gothic MB101 Pro'
    plt.rcParams['axes.unicode_minus'] = False

    # 2つのサブプロット（合成特性のみ表示）
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # --- 左側: LUT適用前（元のグラフ、軸入れ替え） ---
    ax1 = axes[0]

    if analyzer.data.has_print_data:
        input_vals_c, print_dens_c = analyzer.data.get_combined_curve_data()

        if len(input_vals_c) > 0:
            # 単調性を保証
            sorted_pairs = sorted(zip(print_dens_c, input_vals_c), key=lambda p: p[0])
            print_dens_sorted = [p[0] for p in sorted_pairs]
            input_vals_sorted = [p[1] for p in sorted_pairs]

            monotonic_print_dens = []
            monotonic_input_vals = []

            for i, (pd, iv) in enumerate(zip(print_dens_sorted, input_vals_sorted)):
                if i == 0:
                    monotonic_print_dens.append(pd)
                    monotonic_input_vals.append(iv)
                else:
                    if iv < monotonic_input_vals[-1]:
                        monotonic_print_dens.append(pd)
                        monotonic_input_vals.append(iv)

            # 実測点（X軸=濃度、Y軸=入力値）
            ax1.scatter(monotonic_print_dens, monotonic_input_vals, color=config.COLOR_COMBINED,
                       s=50, alpha=0.7, label='実測値', zorder=3)

            # 補間曲線
            if len(monotonic_print_dens) >= 3:
                try:
                    curve_swapped = interpolate.CubicSpline(
                        monotonic_print_dens, monotonic_input_vals
                    )
                    x_smooth = np.linspace(min(monotonic_print_dens),
                                          max(monotonic_print_dens), 256)
                    y_smooth = curve_swapped(x_smooth)
                    ax1.plot(x_smooth, y_smooth, color=config.COLOR_COMBINED,
                            linewidth=2, label='実測カーブ', alpha=0.8)
                except:
                    pass

            # 理想線
            ideal_min_dens = min(monotonic_print_dens)
            ideal_max_dens = max(monotonic_print_dens)
            x_ideal = np.linspace(ideal_min_dens, ideal_max_dens, 256)
            y_ideal = np.linspace(255, 0, 256)
            ax1.plot(x_ideal, y_ideal, '--', color=config.COLOR_TARGET,
                    linewidth=1.5, label='理想(リニア)', alpha=0.6)

            ax1.set_xlabel('プリント濃度', fontsize=12)
            ax1.set_ylabel('入力値 (0-255)', fontsize=12)
            ax1.set_title('LUT適用前\nプリント濃度 → 入力値', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend(fontsize=10)
            ax1.invert_yaxis()  # Y軸を反転：255が上、0が下

    # --- 右側: LUT適用後（補正後の予測、軸入れ替え） ---
    ax2 = axes[1]

    if analyzer.data.has_print_data:
        input_vals_c, print_dens_c = analyzer.data.get_combined_curve_data()

        if len(input_vals_c) > 0:
            # LUTを適用した入力値を計算
            corrected_inputs = inverse_gen.apply_lut_to_values(input_vals_c)

            # デバッグ: LUT適用を確認（常に表示）
            import sys
            debug_msg = f"\n=== LUT適用プレビューグラフ デバッグ ===\n"
            debug_msg += f"LUT適用前: {input_vals_c[:5]}... → LUT適用後: {corrected_inputs[:5]}...\n"
            debug_msg += f"negative_curve存在: {analyzer.negative_curve is not None}\n"
            debug_msg += f"print_curve存在: {analyzer.print_curve is not None}\n"
            print(debug_msg, file=sys.stderr, flush=True)

            # ログファイルにも書き出し
            with open(config.OUTPUT_DIR + "/debug_log.txt", "a") as f:
                f.write(debug_msg)

            # 補正後の濃度を予測（ネガカーブから計算）
            corrected_neg_dens = []
            for corrected_input in corrected_inputs:
                if analyzer.negative_curve is not None:
                    neg_d = float(analyzer.negative_curve(corrected_input))
                    corrected_neg_dens.append(neg_d)
                else:
                    corrected_neg_dens.append(0)
                    if config.VERBOSE:
                        print(f"警告: negative_curveが None です")

            # プリントカーブから最終濃度を計算
            corrected_print_dens = []

            # ネガ濃度の有効範囲を取得（外挿を防ぐ）
            if analyzer.print_curve is not None and analyzer.data.has_print_data:
                try:
                    neg_dens_data, _ = analyzer.data.get_print_curve_data()
                    if len(neg_dens_data) > 0:
                        neg_d_min = min(neg_dens_data)
                        neg_d_max = max(neg_dens_data)
                        msg = f"ネガ濃度の測定範囲: {neg_d_min:.3f} - {neg_d_max:.3f}\n"
                        print(msg, file=sys.stderr, flush=True)
                        with open(config.OUTPUT_DIR + "/debug_log.txt", "a") as f:
                            f.write(msg)
                    else:
                        neg_d_min = 0
                        neg_d_max = 3.0
                        msg = f"ネガ濃度データが空のためデフォルト使用: {neg_d_min:.3f} - {neg_d_max:.3f}\n"
                        print(msg, file=sys.stderr, flush=True)
                        with open(config.OUTPUT_DIR + "/debug_log.txt", "a") as f:
                            f.write(msg)
                except Exception as e:
                    neg_d_min = 0
                    neg_d_max = 3.0
                    msg = f"ネガ濃度データ取得エラー({e})のためデフォルト使用: {neg_d_min:.3f} - {neg_d_max:.3f}\n"
                    print(msg, file=sys.stderr, flush=True)
                    with open(config.OUTPUT_DIR + "/debug_log.txt", "a") as f:
                        f.write(msg)
            else:
                neg_d_min = 0
                neg_d_max = 3.0
                msg = f"プリントカーブが存在しないためデフォルト使用: {neg_d_min:.3f} - {neg_d_max:.3f}\n"
                print(msg, file=sys.stderr, flush=True)
                with open(config.OUTPUT_DIR + "/debug_log.txt", "a") as f:
                    f.write(msg)

            # デバッグ: クリップ前後の値を記録
            clipping_count = 0
            for i, neg_d in enumerate(corrected_neg_dens):
                if analyzer.print_curve is not None:
                    try:
                        # ネガ濃度を測定範囲内にクリップ（外挿を防ぐ）
                        neg_d_clipped = np.clip(neg_d, neg_d_min, neg_d_max)
                        if neg_d != neg_d_clipped:
                            clipping_count += 1
                            if clipping_count <= 3:  # 最初の3個だけログ出力
                                msg = f"  クリップ: {neg_d:.4f} → {neg_d_clipped:.4f}\n"
                                print(msg, file=sys.stderr, flush=True)
                                with open(config.OUTPUT_DIR + "/debug_log.txt", "a") as f:
                                    f.write(msg)
                        print_d = float(analyzer.print_curve(neg_d_clipped))
                        corrected_print_dens.append(print_d)
                    except Exception as e:
                        if config.VERBOSE:
                            print(f"警告: print_curve計算エラー: {e}")
                        corrected_print_dens.append(print_dens_c[i] if i < len(print_dens_c) else 0)
                else:
                    corrected_print_dens.append(print_dens_c[i] if i < len(print_dens_c) else 0)
                    if config.VERBOSE:
                        print(f"警告: print_curveが None です")

            if clipping_count > 0:
                msg = f"合計 {clipping_count}個の値をクリップしました\n"
                print(msg, file=sys.stderr, flush=True)
                with open(config.OUTPUT_DIR + "/debug_log.txt", "a") as f:
                    f.write(msg)

            # デバッグ: 予測値を確認（常に表示）
            msg = f"補正後ネガ濃度: {corrected_neg_dens[:5]}...\n"
            msg += f"補正後プリント濃度: {corrected_print_dens[:5]}...\n"
            msg += f"補正後プリント濃度の数: {len(corrected_print_dens)}個\n"
            print(msg, file=sys.stderr, flush=True)
            with open(config.OUTPUT_DIR + "/debug_log.txt", "a") as f:
                f.write(msg)

            # 単調性を保証
            sorted_pairs = sorted(zip(corrected_print_dens, input_vals_c), key=lambda p: p[0])
            corr_print_dens_sorted = [p[0] for p in sorted_pairs]
            corr_input_vals_sorted = [p[1] for p in sorted_pairs]

            monotonic_corr_print_dens = []
            monotonic_corr_input_vals = []

            for i, (pd, iv) in enumerate(zip(corr_print_dens_sorted, corr_input_vals_sorted)):
                if i == 0:
                    monotonic_corr_print_dens.append(pd)
                    monotonic_corr_input_vals.append(iv)
                else:
                    if iv < monotonic_corr_input_vals[-1]:
                        monotonic_corr_print_dens.append(pd)
                        monotonic_corr_input_vals.append(iv)

            # デバッグ: 単調性フィルタ後のデータ数（常に表示）
            msg = f"単調性フィルタ前: {len(corrected_print_dens)}個\n"
            msg += f"単調性フィルタ後: {len(monotonic_corr_print_dens)}個\n"
            if len(monotonic_corr_print_dens) > 0:
                msg += f"  範囲: プリント濃度 {min(monotonic_corr_print_dens):.3f} - {max(monotonic_corr_print_dens):.3f}\n"
                msg += f"  範囲: 入力値 {min(monotonic_corr_input_vals):.1f} - {max(monotonic_corr_input_vals):.1f}\n"
            else:
                msg += f"  ⚠️ 警告: 単調性フィルタ後にデータが0個になりました！\n"
            msg += f"=== デバッグ終了 ===\n\n"
            print(msg, file=sys.stderr, flush=True)
            with open(config.OUTPUT_DIR + "/debug_log.txt", "a") as f:
                f.write(msg)

            # 予測点（X軸=濃度、Y軸=入力値）
            if len(monotonic_corr_print_dens) > 0:
                ax2.scatter(monotonic_corr_print_dens, monotonic_corr_input_vals, color='green',
                           s=50, alpha=0.7, label='補正後予測値', zorder=3)
            else:
                # データがない場合の警告表示
                ax2.text(0.5, 0.5, 'データなし\n(単調性フィルタ後に点が残りませんでした)',
                        ha='center', va='center', transform=ax2.transAxes,
                        fontsize=12, color='red')

            # 補間曲線（端点での振動を抑えるためbc_type='natural'を指定）
            if len(monotonic_corr_print_dens) >= 3:
                try:
                    corrected_spline = interpolate.CubicSpline(
                        monotonic_corr_print_dens, monotonic_corr_input_vals,
                        bc_type='natural'  # 端点で2次導関数=0にして振動を抑える
                    )
                    x_smooth = np.linspace(min(monotonic_corr_print_dens),
                                          max(monotonic_corr_print_dens), 256)
                    y_smooth = corrected_spline(x_smooth)
                    ax2.plot(x_smooth, y_smooth, color='green',
                            linewidth=2, label='補正後カーブ', alpha=0.8)
                except:
                    pass

            # 理想線
            ideal_min_dens = min(monotonic_corr_print_dens) if monotonic_corr_print_dens else min(print_dens_c)
            ideal_max_dens = max(monotonic_corr_print_dens) if monotonic_corr_print_dens else max(print_dens_c)
            x_ideal = np.linspace(ideal_min_dens, ideal_max_dens, 256)
            y_ideal = np.linspace(255, 0, 256)
            ax2.plot(x_ideal, y_ideal, '--', color=config.COLOR_TARGET,
                    linewidth=1.5, label='理想(リニア)', alpha=0.6)

            ax2.set_xlabel('プリント濃度', fontsize=12)
            ax2.set_ylabel('入力値 (0-255)', fontsize=12)
            ax2.set_title('LUT適用後（予測）\nプリント濃度 → 入力値', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend(fontsize=10)
            ax2.invert_yaxis()  # Y軸を反転：255が上、0が下

    plt.tight_layout()

    # 保存（PDFとPNG両方）
    output_path_pdf = os.path.join(output_dir, 'lut_preview.pdf')
    output_path_png = os.path.join(output_dir, 'lut_preview.png')

    plt.savefig(output_path_pdf, dpi=config.GRAPH_DPI, bbox_inches='tight')
    plt.savefig(output_path_png, dpi=config.GRAPH_DPI, bbox_inches='tight')
    plt.close()

    if config.VERBOSE:
        print(f"\n✓ プレビューグラフを保存: {output_path_pdf}")
        print(f"✓ プレビューグラフを保存: {output_path_png}")

    return output_path_png  # Streamlit表示用にPNGパスを返す


def generate_histogram_graph(analyzer: 'CurveAnalyzer', output_dir: str = None):
    """
    測定値の分布ヒストグラムを生成

    Args:
        analyzer: CurveAnalyzer
        output_dir: 出力ディレクトリ

    Returns:
        str: 保存されたグラフのパス
    """
    if output_dir is None:
        output_dir = config.GRAPHS_DIR

    # スタイル設定
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.family'] = 'A-OTF Gothic MB101 Pro'
    plt.rcParams['axes.unicode_minus'] = False

    # 2つのサブプロット
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # --- 左側: ネガ濃度の分布 ---
    ax1 = axes[0]
    input_vals, neg_dens = analyzer.data.get_negative_curve_data()

    ax1.hist(neg_dens, bins=20, color=config.COLOR_NEGATIVE, alpha=0.7, edgecolor='black')
    ax1.axvline(np.mean(neg_dens), color='red', linestyle='--', linewidth=2, label=f'平均: {np.mean(neg_dens):.3f}')
    ax1.axvline(np.median(neg_dens), color='green', linestyle='--', linewidth=2, label=f'中央値: {np.median(neg_dens):.3f}')

    ax1.set_xlabel('ネガ濃度', fontsize=12)
    ax1.set_ylabel('度数', fontsize=12)
    ax1.set_title('ネガ濃度の分布', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # --- 右側: プリント濃度の分布 ---
    ax2 = axes[1]

    if analyzer.data.has_print_data:
        _, print_dens = analyzer.data.get_print_curve_data()

        if len(print_dens) > 0:
            ax2.hist(print_dens, bins=20, color=config.COLOR_PRINT, alpha=0.7, edgecolor='black')
            ax2.axvline(np.mean(print_dens), color='red', linestyle='--', linewidth=2, label=f'平均: {np.mean(print_dens):.3f}')
            ax2.axvline(np.median(print_dens), color='green', linestyle='--', linewidth=2, label=f'中央値: {np.median(print_dens):.3f}')

            ax2.set_xlabel('プリント濃度', fontsize=12)
            ax2.set_ylabel('度数', fontsize=12)
            ax2.set_title('プリント濃度の分布', fontsize=14, fontweight='bold')
            ax2.legend(fontsize=10)
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'プリントデータなし', ha='center', va='center',
                    transform=ax2.transAxes, fontsize=14, color='gray')
    else:
        ax2.text(0.5, 0.5, 'プリントデータなし', ha='center', va='center',
                transform=ax2.transAxes, fontsize=14, color='gray')

    plt.tight_layout()

    # 保存
    output_path_png = os.path.join(output_dir, 'histogram.png')
    plt.savefig(output_path_png, dpi=config.GRAPH_DPI, bbox_inches='tight')
    plt.close()

    if config.VERBOSE:
        print(f"\n✓ ヒストグラムを保存: {output_path_png}")

    return output_path_png


def generate_error_graph(analyzer: 'CurveAnalyzer', inverse_gen, output_dir: str = None):
    """
    理想値との誤差グラフを生成

    Args:
        analyzer: CurveAnalyzer
        inverse_gen: InverseCurveGenerator
        output_dir: 出力ディレクトリ

    Returns:
        str: 保存されたグラフのパス
    """
    if output_dir is None:
        output_dir = config.GRAPHS_DIR

    # スタイル設定
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.family'] = 'A-OTF Gothic MB101 Pro'
    plt.rcParams['axes.unicode_minus'] = False

    # 2つのサブプロット
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # --- 左側: LUT適用前の誤差 ---
    ax1 = axes[0]

    if analyzer.data.has_print_data:
        input_vals_c, print_dens_c = analyzer.data.get_combined_curve_data()

        if len(input_vals_c) > 0:
            # 理想値（線形）を計算
            print_min = min(print_dens_c)
            print_max = max(print_dens_c)
            print_range = print_max - print_min

            ideal_dens = []
            errors_before = []

            for i, input_val in enumerate(input_vals_c):
                # 理想濃度（入力値に対して線形）
                normalized_input = input_val / 255.0
                ideal_d = print_max - normalized_input * print_range
                ideal_dens.append(ideal_d)

                # 誤差
                error = print_dens_c[i] - ideal_d
                errors_before.append(error)

            ax1.scatter(input_vals_c, errors_before, color=config.COLOR_COMBINED, s=50, alpha=0.7, label='誤差')
            ax1.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
            ax1.axhline(np.mean(errors_before), color='red', linestyle='--', linewidth=2, label=f'平均誤差: {np.mean(errors_before):.3f}')

            ax1.set_xlabel('入力値 (0-255)', fontsize=12)
            ax1.set_ylabel('誤差（実測 - 理想）', fontsize=12)
            ax1.set_title('LUT適用前の誤差\n理想線形カーブからのずれ', fontsize=14, fontweight='bold')
            ax1.legend(fontsize=10)
            ax1.grid(True, alpha=0.3)

    # --- 右側: LUT適用後の予測誤差 ---
    ax2 = axes[1]

    if analyzer.data.has_print_data:
        input_vals_c, print_dens_c = analyzer.data.get_combined_curve_data()

        if len(input_vals_c) > 0:
            # LUT適用後の濃度を予測
            corrected_inputs = inverse_gen.apply_lut_to_values(input_vals_c)

            corrected_neg_dens = []
            for corrected_input in corrected_inputs:
                if analyzer.negative_curve is not None:
                    neg_d = float(analyzer.negative_curve(corrected_input))
                    corrected_neg_dens.append(neg_d)
                else:
                    corrected_neg_dens.append(0)

            corrected_print_dens = []
            for neg_d in corrected_neg_dens:
                if analyzer.print_curve is not None:
                    try:
                        print_d = float(analyzer.print_curve(neg_d))
                        corrected_print_dens.append(print_d)
                    except:
                        corrected_print_dens.append(print_dens_c[len(corrected_print_dens)])
                else:
                    corrected_print_dens.append(print_dens_c[len(corrected_print_dens)])

            # 理想値と誤差を計算
            print_min = min(corrected_print_dens) if corrected_print_dens else min(print_dens_c)
            print_max = max(corrected_print_dens) if corrected_print_dens else max(print_dens_c)
            print_range = print_max - print_min

            errors_after = []
            for i, input_val in enumerate(input_vals_c):
                normalized_input = input_val / 255.0
                ideal_d = print_max - normalized_input * print_range
                error = corrected_print_dens[i] - ideal_d
                errors_after.append(error)

            ax2.scatter(input_vals_c, errors_after, color='green', s=50, alpha=0.7, label='補正後誤差')
            ax2.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
            ax2.axhline(np.mean(errors_after), color='red', linestyle='--', linewidth=2, label=f'平均誤差: {np.mean(errors_after):.3f}')

            ax2.set_xlabel('入力値 (0-255)', fontsize=12)
            ax2.set_ylabel('誤差（予測 - 理想）', fontsize=12)
            ax2.set_title('LUT適用後の予測誤差\n理想線形カーブからのずれ', fontsize=14, fontweight='bold')
            ax2.legend(fontsize=10)
            ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # 保存
    output_path_png = os.path.join(output_dir, 'error_analysis.png')
    plt.savefig(output_path_png, dpi=config.GRAPH_DPI, bbox_inches='tight')
    plt.close()

    if config.VERBOSE:
        print(f"\n✓ 誤差グラフを保存: {output_path_png}")

    return output_path_png


def generate_lut_curve_graph(inverse_gen, output_dir: str = None):
    """
    LUTカーブの可視化グラフを生成

    Args:
        inverse_gen: InverseCurveGenerator
        output_dir: 出力ディレクトリ

    Returns:
        str: 保存されたグラフのパス
    """
    if output_dir is None:
        output_dir = config.GRAPHS_DIR

    # スタイル設定
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.family'] = 'A-OTF Gothic MB101 Pro'
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    # LUTカーブを取得
    lut_array = inverse_gen.get_curve_as_lut(resolution=256)
    x_vals = np.linspace(0, 255, 256)

    # LUTカーブをプロット
    ax.plot(x_vals, lut_array, color='blue', linewidth=2, label='LUTカーブ')

    # 理想線（y=x）
    ax.plot([0, 255], [0, 255], '--', color='gray', linewidth=1.5, label='理想（y=x）', alpha=0.6)

    # 制御点をプロット
    if len(inverse_gen.control_points) > 0:
        control_x = [p[0] for p in inverse_gen.control_points]
        control_y = [p[1] for p in inverse_gen.control_points]
        ax.scatter(control_x, control_y, color='red', s=30, alpha=0.7, label='制御点', zorder=3)

    ax.set_xlabel('入力値 (0-255)', fontsize=12)
    ax.set_ylabel('出力値 (0-255)', fontsize=12)
    ax.set_title('LUTカーブ\n入力値 → 補正後の値', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 255)
    ax.set_ylim(0, 255)

    plt.tight_layout()

    # 保存
    output_path_png = os.path.join(output_dir, 'lut_curve.png')
    plt.savefig(output_path_png, dpi=config.GRAPH_DPI, bbox_inches='tight')
    plt.close()

    if config.VERBOSE:
        print(f"\n✓ LUTカーブを保存: {output_path_png}")

    return output_path_png


def generate_gamma_graph(analyzer: 'CurveAnalyzer', output_dir: str = None):
    """
    ガンマ特性グラフを生成

    Args:
        analyzer: CurveAnalyzer
        output_dir: 出力ディレクトリ

    Returns:
        str: 保存されたグラフのパス
    """
    if output_dir is None:
        output_dir = config.GRAPHS_DIR

    # スタイル設定
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.family'] = 'A-OTF Gothic MB101 Pro'
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    # 実測データ
    input_vals, neg_dens = analyzer.data.get_negative_curve_data()

    # 正規化（0-1）
    input_normalized = np.array(input_vals) / 255.0
    neg_dens_normalized = (np.array(neg_dens) - min(neg_dens)) / (max(neg_dens) - min(neg_dens))

    # 実測カーブをプロット
    ax.scatter(input_normalized, neg_dens_normalized, color=config.COLOR_NEGATIVE, s=50, alpha=0.7, label='実測値（正規化）', zorder=3)

    # 理想ガンマカーブ（γ=1.8）
    x_ideal = np.linspace(0, 1, 256)
    y_ideal_gamma = x_ideal ** config.NEGATIVE_GAMMA

    ax.plot(x_ideal, y_ideal_gamma, '--', color='red', linewidth=2, label=f'理想 γ={config.NEGATIVE_GAMMA}', alpha=0.8)

    # 参考: γ=1.0, 2.2も表示
    y_gamma_1 = x_ideal ** 1.0
    y_gamma_22 = x_ideal ** 2.2

    ax.plot(x_ideal, y_gamma_1, ':', color='gray', linewidth=1.5, label='γ=1.0（線形）', alpha=0.6)
    ax.plot(x_ideal, y_gamma_22, ':', color='purple', linewidth=1.5, label='γ=2.2（参考）', alpha=0.6)

    ax.set_xlabel('入力値（正規化 0-1）', fontsize=12)
    ax.set_ylabel('ネガ濃度（正規化 0-1）', fontsize=12)
    ax.set_title('ガンマ特性\nネガのガンマ応答', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    plt.tight_layout()

    # 保存
    output_path_png = os.path.join(output_dir, 'gamma_curve.png')
    plt.savefig(output_path_png, dpi=config.GRAPH_DPI, bbox_inches='tight')
    plt.close()

    if config.VERBOSE:
        print(f"\n✓ ガンマカーブを保存: {output_path_png}")

    return output_path_png


def generate_interactive_graphs(analyzer: 'CurveAnalyzer', inverse_gen, output_dir: str = None) -> Dict[str, str]:
    """
    Plotlyでインタラクティブグラフを生成

    Args:
        analyzer: CurveAnalyzer
        inverse_gen: InverseCurveGenerator
        output_dir: 出力ディレクトリ

    Returns:
        Dict[str, str]: グラフ名とHTMLパスの辞書
    """
    if output_dir is None:
        output_dir = config.GRAPHS_DIR

    output_paths = {}

    # --- 1. メインカーブのインタラクティブグラフ ---
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('プリンター特性<br>入力値 → ネガ濃度',
                       'プラチナプリント特性<br>ネガ濃度 → プリント濃度',
                       '合成特性<br>プリント濃度 → 入力値')
    )

    # グラフ1: 入力値 → ネガ濃度
    input_vals, neg_dens = analyzer.data.get_negative_curve_data()

    fig.add_trace(
        go.Scatter(x=input_vals, y=neg_dens, mode='markers', name='実測値',
                  marker=dict(size=8, color='blue'), legendgroup='negative'),
        row=1, col=1
    )

    if analyzer.negative_curve is not None:
        x_smooth = np.linspace(min(input_vals), max(input_vals), 256)
        y_smooth = analyzer.negative_curve(x_smooth)
        fig.add_trace(
            go.Scatter(x=x_smooth, y=y_smooth, mode='lines', name='補間カーブ',
                      line=dict(color='blue', width=2), legendgroup='negative'),
            row=1, col=1
        )

    # グラフ2: ネガ濃度 → プリント濃度
    if analyzer.data.has_print_data:
        neg_dens_p, print_dens = analyzer.data.get_print_curve_data()

        if len(neg_dens_p) > 0:
            fig.add_trace(
                go.Scatter(x=neg_dens_p, y=print_dens, mode='markers', name='実測値',
                          marker=dict(size=8, color='orange'), legendgroup='print'),
                row=1, col=2
            )

            if analyzer.print_curve is not None:
                x_smooth = np.linspace(min(neg_dens_p), max(neg_dens_p), 256)
                y_smooth = analyzer.print_curve(x_smooth)
                fig.add_trace(
                    go.Scatter(x=x_smooth, y=y_smooth, mode='lines', name='補間カーブ',
                              line=dict(color='orange', width=2), legendgroup='print'),
                    row=1, col=2
                )

    # グラフ3: プリント濃度 → 入力値（軸入れ替え）
    if analyzer.data.has_print_data:
        input_vals_c, print_dens_c = analyzer.data.get_combined_curve_data()

        if len(input_vals_c) > 0:
            # 単調性を保証
            sorted_pairs = sorted(zip(print_dens_c, input_vals_c), key=lambda p: p[0])
            print_dens_sorted = [p[0] for p in sorted_pairs]
            input_vals_sorted = [p[1] for p in sorted_pairs]

            monotonic_print_dens = []
            monotonic_input_vals = []

            for i, (pd, iv) in enumerate(zip(print_dens_sorted, input_vals_sorted)):
                if i == 0:
                    monotonic_print_dens.append(pd)
                    monotonic_input_vals.append(iv)
                else:
                    if iv < monotonic_input_vals[-1]:
                        monotonic_print_dens.append(pd)
                        monotonic_input_vals.append(iv)

            fig.add_trace(
                go.Scatter(x=monotonic_print_dens, y=monotonic_input_vals, mode='markers', name='実測値',
                          marker=dict(size=8, color='purple'), legendgroup='combined'),
                row=1, col=3
            )

            # 理想線
            ideal_min_dens = min(monotonic_print_dens) if monotonic_print_dens else min(print_dens_c)
            ideal_max_dens = max(monotonic_print_dens) if monotonic_print_dens else max(print_dens_c)
            x_ideal = [ideal_min_dens, ideal_max_dens]
            y_ideal = [255, 0]

            fig.add_trace(
                go.Scatter(x=x_ideal, y=y_ideal, mode='lines', name='理想(リニア)',
                          line=dict(color='green', width=2, dash='dash'), legendgroup='combined'),
                row=1, col=3
            )

    # レイアウト設定
    fig.update_xaxes(title_text="入力値 (0-255)", row=1, col=1)
    fig.update_yaxes(title_text="ネガ濃度", row=1, col=1)

    fig.update_xaxes(title_text="ネガ濃度", row=1, col=2)
    fig.update_yaxes(title_text="プリント濃度", row=1, col=2)

    fig.update_xaxes(title_text="プリント濃度", row=1, col=3)
    fig.update_yaxes(title_text="入力値 (0-255)", autorange="reversed", row=1, col=3)

    fig.update_layout(
        height=500,
        showlegend=True,
        title_text="Precision EDN v2 解析結果（インタラクティブ）",
        hovermode='closest'
    )

    # 保存
    output_path_html = os.path.join(output_dir, 'interactive_curves.html')
    fig.write_html(output_path_html)
    output_paths['curves'] = output_path_html

    if config.VERBOSE:
        print(f"\n✓ インタラクティブグラフを保存: {output_path_html}")

    # --- 2. LUTカーブのインタラクティブグラフ ---
    fig_lut = go.Figure()

    lut_array = inverse_gen.get_curve_as_lut(resolution=256)
    x_vals = np.linspace(0, 255, 256)

    fig_lut.add_trace(
        go.Scatter(x=x_vals, y=lut_array, mode='lines', name='LUTカーブ',
                  line=dict(color='blue', width=2))
    )

    # 理想線
    fig_lut.add_trace(
        go.Scatter(x=[0, 255], y=[0, 255], mode='lines', name='理想（y=x）',
                  line=dict(color='gray', width=1.5, dash='dash'))
    )

    # 制御点
    if len(inverse_gen.control_points) > 0:
        control_x = [p[0] for p in inverse_gen.control_points]
        control_y = [p[1] for p in inverse_gen.control_points]
        fig_lut.add_trace(
            go.Scatter(x=control_x, y=control_y, mode='markers', name='制御点',
                      marker=dict(size=6, color='red'))
        )

    fig_lut.update_layout(
        title="LUTカーブ（インタラクティブ）",
        xaxis_title="入力値 (0-255)",
        yaxis_title="出力値 (0-255)",
        hovermode='closest',
        height=600
    )

    output_path_lut_html = os.path.join(output_dir, 'interactive_lut.html')
    fig_lut.write_html(output_path_lut_html)
    output_paths['lut'] = output_path_lut_html

    if config.VERBOSE:
        print(f"✓ インタラクティブLUTグラフを保存: {output_path_lut_html}")

    return output_paths


if __name__ == "__main__":
    print("=== Precision EDN v2 - カーブ解析モジュール ===\n")
    print("このモジュールは main.py から呼び出されます")
