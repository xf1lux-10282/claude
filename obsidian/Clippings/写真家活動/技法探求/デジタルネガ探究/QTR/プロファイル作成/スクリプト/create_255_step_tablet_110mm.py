from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_255_step_tablet(size_mm=110, dpi=300):
    """
    255ステップタブレット画像を生成（110mm × 110mm）

    Parameters:
    - size_mm: タブレットのサイズ（mm単位）
    - dpi: 解像度

    Returns:
    - img: PIL Image object
    - step_values: 各ステップの値（0-255）
    """
    # mmをピクセルに変換
    size_px = int(size_mm / 25.4 * dpi)
    print(f"タブレットサイズ: {size_mm}mm × {size_mm}mm = {size_px}px × {size_px}px @ {dpi}DPI")

    # 255ステップの値（0から255まで）
    step_values = np.arange(256)  # 0-255の256個の値

    # 16 × 16グリッドでステップを配置
    grid_size = 16
    step_width = size_px // grid_size
    step_height = size_px // grid_size

    print(f"グリッド: {grid_size} × {grid_size}")
    print(f"各ステップサイズ: {step_width}px × {step_height}px")

    # 16bit配列を作成
    img_array = np.zeros((size_px, size_px), dtype=np.uint16)

    # 各ステップを描画
    for i, value in enumerate(step_values):
        if i >= grid_size * grid_size:  # 256個のうち255個まで
            break

        row = i // grid_size
        col = i % grid_size

        y_start = row * step_height
        y_end = y_start + step_height
        x_start = col * step_width
        x_end = x_start + step_width

        # 16bit値に変換（0-255を0-65535にスケール）
        value_16bit = int(value * 257)  # 255 * 257 = 65535

        # 配列に均一な値を設定
        img_array[y_start:y_end, x_start:x_end] = value_16bit

    # NumPy配列からPIL Imageに変換
    img = Image.fromarray(img_array, mode='I;16')

    return img, step_values

def create_255_step_tablet_8bit(size_mm=110, dpi=300):
    """
    255ステップタブレット画像を生成（8bit版、互換性確保用）

    Parameters:
    - size_mm: タブレットのサイズ（mm単位）
    - dpi: 解像度

    Returns:
    - img: PIL Image object
    - step_values: 各ステップの値（0-255）
    """
    # mmをピクセルに変換
    size_px = int(size_mm / 25.4 * dpi)
    print(f"\n8bit版タブレットサイズ: {size_mm}mm × {size_mm}mm = {size_px}px × {size_px}px @ {dpi}DPI")

    # 255ステップの値（0から255まで）
    step_values = np.arange(256)  # 0-255の256個の値

    # 16 × 16グリッドでステップを配置
    grid_size = 16
    step_width = size_px // grid_size
    step_height = size_px // grid_size

    print(f"グリッド: {grid_size} × {grid_size}")
    print(f"各ステップサイズ: {step_width}px × {step_height}px")

    # 8bit配列を作成
    img_array = np.zeros((size_px, size_px), dtype=np.uint8)

    # 各ステップを描画
    for i, value in enumerate(step_values):
        if i >= grid_size * grid_size:  # 256個のうち255個まで
            break

        row = i // grid_size
        col = i % grid_size

        y_start = row * step_height
        y_end = y_start + step_height
        x_start = col * step_width
        x_end = x_start + step_width

        # 配列に均一な値を設定
        img_array[y_start:y_end, x_start:x_end] = int(value)

    # NumPy配列からPIL Imageに変換
    img = Image.fromarray(img_array, mode='L')

    return img, step_values

# ===== メイン処理 =====

print("=" * 70)
print("255ステップタブレット生成 - Precision EDN Version 2")
print("=" * 70)

# 16bit版を生成
print("\n[1] 16bit TIFF版を生成中...")
img_16bit, step_values = create_255_step_tablet(size_mm=110, dpi=300)

# 16bit TIFFとして保存
output_16bit = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/255_step_tablet_110mm_16bit.tif'
img_16bit.save(output_16bit, dpi=(300, 300), compression='none')
print(f"✓ 16bit TIFF保存完了: {output_16bit}")

# 8bit版も生成（プレビュー用）
print("\n[2] 8bit PNG版を生成中（プレビュー用）...")
img_8bit, _ = create_255_step_tablet_8bit(size_mm=110, dpi=300)

# 8bit PNGとして保存
output_8bit = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/255_step_tablet_110mm_8bit.png'
img_8bit.save(output_8bit, dpi=(300, 300))
print(f"✓ 8bit PNG保存完了: {output_8bit}")

# タブレット情報を出力
print("\n" + "=" * 70)
print("タブレット仕様")
print("=" * 70)
print(f"サイズ: 110mm × 110mm")
print(f"解像度: 300 DPI")
print(f"ステップ数: 256 (0-255)")
print(f"グリッド配置: 16 × 16")
print(f"各ステップサイズ: 約6.9mm × 6.9mm")
print(f"")
print(f"16bit TIFF: {output_16bit}")
print(f"8bit PNG: {output_8bit}")

print("\n" + "=" * 70)
print("使用方法")
print("=" * 70)
print("1. プリント準備")
print("   - 用紙: ピクトリコOHPフィルム")
print("   - プリンター: EPSON PX-1V")
print("   - 設定: カラーマネジメントOFF、16bit TIFF使用")
print("")
print("2. 測定（Precision EDN Version 2 測定プロトコル）")
print("   - 各ステップ中央部を濃度計で測定")
print("   - 各ステップ3箇所測定して平均")
print("   - 測定環境: 温度20-25℃、湿度40-60%")
print("")
print("3. データ記録")
print("   - 入力値(0-255) → ネガ濃度(D)の関係を記録")
print("   - プリンター特性曲線を作成")
print("")
print("4. プラチナプリント測定")
print("   - このネガでコンタクトプリント")
print("   - プリント濃度を測定")
print("   - ネガ濃度 → プリント濃度の関係を記録")

print("\n" + "=" * 70)
print("測定完了！")
print("次のステップ: Precision_EDN_Version2_設計書.md の「5. 測定プロトコル」を参照")
print("=" * 70)
