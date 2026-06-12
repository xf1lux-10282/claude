from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_step_wedge(steps=21, width_per_step=200, height=1000, dpi=300):
    """
    ステップウェッジ画像を生成

    Parameters:
    - steps: ステップ数（デフォルト21 = 5%刻みで0-100%）
    - width_per_step: 各ステップの幅（ピクセル）
    - height: 画像の高さ（ピクセル）
    - dpi: 解像度
    """
    # K値を0%から100%まで等間隔で分割
    k_values = np.linspace(0, 100, steps)

    # RGB値に変換（K% → RGB値）
    # K=0% → RGB(255,255,255) 白
    # K=100% → RGB(0,0,0) 黒
    rgb_values = [int(255 - k * 2.55) for k in k_values]

    # 画像作成（ラベル用のスペースを追加）
    label_height = 100
    total_width = width_per_step * steps
    total_height = height + label_height
    img = Image.new('RGB', (total_width, total_height), color='white')
    draw = ImageDraw.Draw(img)

    # 各ステップを描画
    for i, (k, rgb) in enumerate(zip(k_values, rgb_values)):
        x_start = i * width_per_step
        # グレーステップ部分
        draw.rectangle(
            [(x_start, 0), (x_start + width_per_step, height)],
            fill=(rgb, rgb, rgb)
        )

        # ラベルを追加（K値を表示）
        label = f"{k:.1f}%"
        # 簡易的にテキストを追加（フォント指定なし）
        text_color = 'black' if k < 50 else 'white'
        draw.text(
            (x_start + width_per_step // 2 - 20, height + 20),
            label,
            fill=text_color
        )

    return img, k_values, rgb_values

# ステップウェッジを生成
print("ステップウェッジ画像を生成中...")
img, k_values, rgb_values = create_step_wedge(steps=21, width_per_step=200, height=1000)

# 画像を保存
output_path = '/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents/step_wedge_21steps.png'
img.save(output_path, dpi=(300, 300))
print(f"✓ 画像を保存しました: {output_path}")

# K値とRGB値のリストを出力
print("\n=== ステップウェッジ詳細 ===")
print(f"ステップ数: {len(k_values)}")
print(f"画像サイズ: {img.width} x {img.height} pixels")
print(f"解像度: 300 DPI")
print("\n各ステップの値:")
print("-" * 50)
for i, (k, rgb) in enumerate(zip(k_values, rgb_values), 1):
    print(f"Step {i:2d}: K={k:5.1f}% → RGB({rgb:3d}, {rgb:3d}, {rgb:3d})")
print("-" * 50)

print("\n=== プリント推奨設定 ===")
print("1. 用紙: OHPフィルム（デジタルネガ用）")
print("2. カラーマネジメント: オフ")
print("3. グレースケール: ブラックインクのみ使用")
print("4. 印刷品質: 最高画質")
print("5. 用紙サイズ: A4またはレター")
print("\n=== 使用方法 ===")
print("1. 上記設定でプリント")
print("2. 各ステップを濃度計で測定")
print("3. K値(%)と濃度(D)の関係をグラフ化")
print("4. 目的の濃度を得るためのK値を逆算")
