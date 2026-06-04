"""
Precision EDN v2 - 設定ファイル

Version 2の設計パラメータと定数を定義
"""

# ===== Version 2 設計パラメータ =====

# 印刷モード設定
PRINT_MODE = "Color"  # "Color" (RGB, Dmax 2.1) or "Grayscale" (Dmax 1.55)

# ネガ設計値
NEGATIVE_GAMMA = 1.8
NEGATIVE_DMIN = 0.10

# Dmaxは印刷モードにより変わる
if PRINT_MODE == "Color":
    NEGATIVE_DMAX = 2.10  # カラーモード実測値
    WORKFLOW_TYPE = "RGB + Color Blocker"
else:
    NEGATIVE_DMAX = 1.55  # グレースケールモード
    WORKFLOW_TYPE = "Grayscale"

NEGATIVE_RANGE = NEGATIVE_DMAX - NEGATIVE_DMIN

# 中間調基準点
MIDTONE_INPUT = 128
MIDTONE_NEGATIVE_DENSITY = 0.70

# プリント目標値
TARGET_PRINT_DMAX = 2.1
EXPECTED_EXPOSURE_RANGE_EV = 6.6

# 逆Sカーブ補正の強度
SHADOW_LIFT_MAX = 0.05      # シャドウ持ち上げ最大値
HIGHLIGHT_COMPRESS_MAX = 0.05  # ハイライト圧縮最大値

# ===== 測定設定 =====

# 33ステップの入力値
STEP_VALUES = [
    0, 8, 16, 24, 32, 40, 48, 56,
    64, 72, 80, 88, 96, 104, 112, 120,
    128, 136, 144, 152, 160, 168, 176, 184,
    192, 200, 208, 216, 224, 232, 240, 248, 255
]

# 出力カーブの制御点数
OUTPUT_CURVE_POINTS = 33  # 33点カーブ

# ===== プリンター設定 =====

PRINTER_MODEL = "EPSON PX-1V"
MEDIA_TYPE = "Pictorico OHP TPS100"
MEDIA_SIZE = "A4"

# ===== プラチナプリント設定 =====

PAPER_TYPE = "和紙"
FO_CONCENTRATION = "高濃度"
UV_SOURCE = "蛍光UV"
PROCESS_TYPE = "プラチナ/パラジウム"

# ===== カーブ解析設定 =====

# 線形領域検出の閾値
LINEAR_REGION_R2_THRESHOLD = 0.99  # R²値の閾値

# 飽和検出の閾値
SATURATION_SLOPE_THRESHOLD = 0.5  # 傾きがこの値以下で飽和と判定

# ===== 出力設定 =====

# グラフ設定
GRAPH_DPI = 300
GRAPH_STYLE = "seaborn-v0_8-darkgrid"

# LUT設定
LUT_RESOLUTION = 256  # 256段階

# ===== ファイルパス =====

import os

# ベースディレクトリ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# データディレクトリ
DATA_DIR = os.path.join(BASE_DIR, "data")

# 出力ディレクトリ
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
GRAPHS_DIR = os.path.join(OUTPUT_DIR, "graphs")
LUTS_DIR = os.path.join(OUTPUT_DIR, "luts")
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")

# ディレクトリ作成
for directory in [DATA_DIR, OUTPUT_DIR, GRAPHS_DIR, LUTS_DIR, REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ===== カラー設定 =====

# グラフのカラー
COLOR_NEGATIVE = "#2E86AB"  # ネガカーブ: 青
COLOR_PRINT = "#A23B72"     # プリントカーブ: 紫
COLOR_COMBINED = "#F18F01"  # 合成カーブ: オレンジ
COLOR_INVERSE = "#C73E1D"   # 逆カーブ: 赤
COLOR_TARGET = "#6A994E"    # 目標: 緑

# ===== バージョン情報 =====

VERSION = "2.0"
CREATED_DATE = "2026-03-09"
AUTHOR = "Precision EDN Project"

# ===== デバッグ設定 =====

DEBUG = False
VERBOSE = True

# ===== 数学定数 =====

import math

# 対数の底
LOG_BASE = 10

# EV計算用
EV_MULTIPLIER = math.log(2, LOG_BASE)  # log10(2) ≈ 0.301
