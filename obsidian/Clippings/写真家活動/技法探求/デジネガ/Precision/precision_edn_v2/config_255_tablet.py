"""
Precision EDN v2 - 255ステップタブレット用設定

110mm × 110mmの255ステップタブレットのための読み取り座標設定
"""

import numpy as np

# ===== タブレット仕様 =====

TABLET_SIZE_MM = 110  # タブレットサイズ (mm)
TABLET_DPI = 300       # 解像度
GRID_SIZE = 16         # 16 × 16グリッド
TOTAL_STEPS = 256      # 0-255の256ステップ

# mmをピクセルに変換
TABLET_SIZE_PX = int(TABLET_SIZE_MM / 25.4 * TABLET_DPI)  # 1299 px

# 各ステップのサイズ（ピクセル）
STEP_WIDTH_PX = TABLET_SIZE_PX // GRID_SIZE   # 81 px
STEP_HEIGHT_PX = TABLET_SIZE_PX // GRID_SIZE  # 81 px

# 各ステップのサイズ（mm）
STEP_WIDTH_MM = TABLET_SIZE_MM / GRID_SIZE   # 6.875 mm
STEP_HEIGHT_MM = TABLET_SIZE_MM / GRID_SIZE  # 6.875 mm

# ===== 読み取り座標の生成 =====

def generate_reading_coordinates():
    """
    255ステップタブレットの読み取り座標を生成

    Returns:
        list of dict: [{'step': 0, 'x_mm': x, 'y_mm': y, 'x_px': x_px, 'y_px': y_px}, ...]
    """
    coordinates = []

    for step_index in range(TOTAL_STEPS):
        # グリッド位置を計算
        row = step_index // GRID_SIZE
        col = step_index % GRID_SIZE

        # 各ステップの中心座標を計算（ピクセル単位）
        x_center_px = col * STEP_WIDTH_PX + STEP_WIDTH_PX // 2
        y_center_px = row * STEP_HEIGHT_PX + STEP_HEIGHT_PX // 2

        # mm単位に変換
        x_center_mm = x_center_px * 25.4 / TABLET_DPI
        y_center_mm = y_center_px * 25.4 / TABLET_DPI

        coordinates.append({
            'step': step_index,
            'input_value': step_index,  # 0-255の入力値
            'grid_row': row,
            'grid_col': col,
            'x_mm': round(x_center_mm, 2),
            'y_mm': round(y_center_mm, 2),
            'x_px': x_center_px,
            'y_px': y_center_px
        })

    return coordinates


def generate_reading_coordinates_for_densitometer(margin_mm=1.0):
    """
    濃度計用の読み取り座標を生成（エッジから余白を確保）

    Parameters:
        margin_mm: 各ステップのエッジからの余白（mm）

    Returns:
        list of dict: 読み取り座標のリスト
    """
    coordinates = []

    for step_index in range(TOTAL_STEPS):
        # グリッド位置を計算
        row = step_index // GRID_SIZE
        col = step_index % GRID_SIZE

        # 各ステップの開始位置（mm単位）
        x_start_mm = col * STEP_WIDTH_MM
        y_start_mm = row * STEP_HEIGHT_MM

        # 中心座標（余白を考慮）
        x_center_mm = x_start_mm + STEP_WIDTH_MM / 2
        y_center_mm = y_start_mm + STEP_HEIGHT_MM / 2

        # ピクセル単位
        x_center_px = int(x_center_mm / 25.4 * TABLET_DPI)
        y_center_px = int(y_center_mm / 25.4 * TABLET_DPI)

        # 測定可能領域（余白を除く）
        measurement_area_width_mm = STEP_WIDTH_MM - 2 * margin_mm
        measurement_area_height_mm = STEP_HEIGHT_MM - 2 * margin_mm

        coordinates.append({
            'step': step_index,
            'input_value': step_index,
            'grid_row': row,
            'grid_col': col,
            'x_mm': round(x_center_mm, 2),
            'y_mm': round(y_center_mm, 2),
            'x_px': x_center_px,
            'y_px': y_center_px,
            'measurement_area_width_mm': round(measurement_area_width_mm, 2),
            'measurement_area_height_mm': round(measurement_area_height_mm, 2)
        })

    return coordinates


def export_coordinates_csv(filepath, margin_mm=1.0):
    """
    読み取り座標をCSVファイルとして出力

    Parameters:
        filepath: 出力CSVファイルのパス
        margin_mm: 測定時の余白（mm）
    """
    import csv

    coordinates = generate_reading_coordinates_for_densitometer(margin_mm)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'step', 'input_value', 'grid_row', 'grid_col',
            'x_mm', 'y_mm', 'x_px', 'y_px',
            'measurement_area_width_mm', 'measurement_area_height_mm'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(coordinates)

    print(f"✓ 読み取り座標をCSVで保存: {filepath}")


def create_measurement_template_255(filepath):
    """
    255ステップタブレット用の測定テンプレートCSVを作成

    Parameters:
        filepath: 出力CSVファイルのパス
    """
    import csv

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'step', 'input_value', 'grid_row', 'grid_col',
            'negative_density', 'print_density'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()

        for step_index in range(TOTAL_STEPS):
            row = step_index // GRID_SIZE
            col = step_index % GRID_SIZE

            writer.writerow({
                'step': step_index,
                'input_value': step_index,
                'grid_row': row,
                'grid_col': col,
                'negative_density': '',
                'print_density': ''
            })

    print(f"✓ 255ステップ測定テンプレートを作成: {filepath}")


def print_tablet_info():
    """タブレット仕様を表示"""
    print("=" * 70)
    print("255ステップタブレット仕様")
    print("=" * 70)
    print(f"サイズ: {TABLET_SIZE_MM}mm × {TABLET_SIZE_MM}mm")
    print(f"解像度: {TABLET_DPI} DPI")
    print(f"ピクセルサイズ: {TABLET_SIZE_PX}px × {TABLET_SIZE_PX}px")
    print(f"グリッド: {GRID_SIZE} × {GRID_SIZE}")
    print(f"ステップ数: {TOTAL_STEPS} (0-255)")
    print(f"各ステップサイズ: {STEP_WIDTH_MM:.2f}mm × {STEP_HEIGHT_MM:.2f}mm")
    print(f"各ステップサイズ: {STEP_WIDTH_PX}px × {STEP_HEIGHT_PX}px")
    print("=" * 70)


def print_reading_guide():
    """読み取りガイドを表示"""
    print("\n" + "=" * 70)
    print("濃度計での読み取りガイド")
    print("=" * 70)
    print("1. タブレットの配置")
    print("   - タブレットを濃度計の下に水平に配置")
    print("   - 左上隅が原点(0,0)になるように調整")
    print("")
    print("2. 読み取り順序")
    print("   - 左上から右へ、1行ずつ下へ")
    print("   - Step 0: 左上隅 (0, 0)")
    print(f"   - Step 15: 右上隅 ({GRID_SIZE-1}, 0)")
    print(f"   - Step 240: 左下隅 (0, {GRID_SIZE-1})")
    print(f"   - Step 255: 右下隅 ({GRID_SIZE-1}, {GRID_SIZE-1})")
    print("")
    print("3. 読み取り精度")
    print("   - 各ステップの中心を測定")
    print("   - エッジから1mm以上離す")
    print(f"   - 有効測定エリア: 約{STEP_WIDTH_MM-2:.1f}mm × {STEP_HEIGHT_MM-2:.1f}mm")
    print("")
    print("4. 測定プロトコル")
    print("   - 各ステップを3箇所測定して平均")
    print("   - 測定環境: 温度20-25℃、湿度40-60%")
    print("=" * 70)


if __name__ == "__main__":
    import os

    # タブレット情報を表示
    print_tablet_info()

    # 読み取りガイドを表示
    print_reading_guide()

    # 出力ディレクトリ
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    # 読み取り座標をエクスポート
    print("\n" + "=" * 70)
    print("ファイル生成")
    print("=" * 70)

    coords_file = os.path.join(data_dir, "255_tablet_reading_coordinates.csv")
    export_coordinates_csv(coords_file, margin_mm=1.0)

    # 測定テンプレートを作成
    template_file = os.path.join(data_dir, "255_tablet_measurement_template.csv")
    create_measurement_template_255(template_file)

    print("\n" + "=" * 70)
    print("完了")
    print("=" * 70)
    print(f"読み取り座標: {coords_file}")
    print(f"測定テンプレート: {template_file}")
    print("\n次のステップ:")
    print("1. タブレットをプリント")
    print("2. 読み取り座標CSVを参照して濃度測定")
    print("3. 測定テンプレートCSVに結果を記録")
    print("=" * 70)
