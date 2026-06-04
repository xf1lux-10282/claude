#!/usr/bin/env python3
"""
QuadToneRIP Curve Parser

QuadToneRIP .quadファイルの読み込みとカーブ適用
"""

import numpy as np


class QuadCurveApplier:
    """QuadToneRIPカーブファイル適用"""

    def __init__(self, curve_file):
        """
        Args:
            curve_file: .quadファイルパス
        """
        self.curve_file = curve_file
        self.curves = self.load_curve(curve_file)

    def load_curve(self, curve_file):
        """
        .quadファイル読込

        Returns:
            dict: {'K': [0-255 LUT], 'C': [...], 'M': [...], ...}

        QuadToneRIP .quad形式:
            # K curve
            0
            1
            2
            ...
            255

            # C curve
            0
            1
            ...
        """
        curves = {}

        with open(curve_file, 'r') as f:
            lines = f.readlines()

        current_channel = None
        values = []

        for line in lines:
            line = line.strip()

            # 空行またはコメント（チャンネル名以外）
            if not line or (line.startswith('#') and 'curve' not in line.lower()):
                continue

            # チャンネル名検出
            if line.startswith('#') and 'curve' in line.lower():
                # 前のチャンネルを保存
                if current_channel and values:
                    curves[current_channel] = np.array(values, dtype=np.uint8)

                # 新しいチャンネル開始
                # 例: "# K curve" → "K"
                parts = line.split()
                if len(parts) >= 2:
                    current_channel = parts[1].upper()
                    values = []
                continue

            # 数値データ
            try:
                val = int(line)
                if 0 <= val <= 255:
                    values.append(val)
            except ValueError:
                pass

        # 最後のチャンネル
        if current_channel and values:
            curves[current_channel] = np.array(values, dtype=np.uint8)

        # カーブが256要素でない場合は警告
        for channel, curve in curves.items():
            if len(curve) != 256:
                print(f"Warning: {channel} curve has {len(curve)} values (expected 256)")

        return curves

    def apply(self, image_data, channel='K'):
        """
        カーブ適用

        Args:
            image_data: numpy array, 0-255 grayscale
            channel: 適用するチャンネル（デフォルト: 'K' = Gray）

        Returns:
            numpy array, カーブ適用後
        """
        if channel not in self.curves:
            print(f"Warning: Channel '{channel}' not found, using linear curve")
            return image_data

        curve = self.curves[channel]

        # カーブが256要素でない場合はリニア補間
        if len(curve) != 256:
            curve = np.linspace(0, 255, 256).astype(np.uint8)

        # LUTを使って変換
        return curve[image_data]

    def get_available_channels(self):
        """
        利用可能なチャンネル一覧取得

        Returns:
            list: チャンネル名のリスト
        """
        return list(self.curves.keys())


# ==============================================================================
# テスト用
# ==============================================================================

if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='QuadToneRIP Curve Parser Test')
    parser.add_argument('curve_file', help='.quad file to parse')
    parser.add_argument('--test', action='store_true',
                       help='Test curve application')

    args = parser.parse_args()

    print(f"Loading curve file: {args.curve_file}")
    applier = QuadCurveApplier(args.curve_file)

    print(f"\nAvailable channels: {applier.get_available_channels()}")

    for channel, curve in applier.curves.items():
        print(f"\n{channel} curve ({len(curve)} values):")
        print(f"  First 10: {curve[:10].tolist()}")
        print(f"  Last 10: {curve[-10:].tolist()}")
        print(f"  Min: {curve.min()}, Max: {curve.max()}, Mean: {curve.mean():.1f}")

    if args.test:
        print("\n=== Curve Application Test ===")
        # テストデータ: 0-255 の直線
        test_data = np.arange(256, dtype=np.uint8)
        print(f"Input (first 10): {test_data[:10].tolist()}")

        # Kチャンネル適用
        if 'K' in applier.curves:
            result = applier.apply(test_data, 'K')
            print(f"Output (first 10): {result[:10].tolist()}")
            print(f"Output (last 10): {result[-10:].tolist()}")

            # 差分確認
            diff = result.astype(int) - test_data.astype(int)
            print(f"Difference: min={diff.min()}, max={diff.max()}, mean={diff.mean():.2f}")
