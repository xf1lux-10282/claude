"""
Precision EDN v2 - データ入力モジュール

測定データの読み込みと検証
"""

import csv
import os
from typing import Dict, List, Tuple
import config


class MeasurementData:
    """測定データを格納するクラス"""

    def __init__(self):
        self.input_values = []
        self.negative_densities = []
        self.print_densities = []
        self.has_print_data = False

    def __len__(self):
        return len(self.input_values)

    def add_measurement(self, input_val, neg_density, print_density=None):
        """測定データを追加"""
        self.input_values.append(input_val)
        self.negative_densities.append(neg_density)
        if print_density is not None:
            self.print_densities.append(print_density)
            self.has_print_data = True
        else:
            self.print_densities.append(None)

    def get_negative_curve_data(self) -> Tuple[List[float], List[float]]:
        """入力値 → ネガ濃度のデータを取得"""
        return self.input_values, self.negative_densities

    def get_print_curve_data(self) -> Tuple[List[float], List[float]]:
        """ネガ濃度 → プリント濃度のデータを取得"""
        if not self.has_print_data:
            return [], []

        # Noneを除外
        neg_dens = []
        print_dens = []
        for nd, pd in zip(self.negative_densities, self.print_densities):
            if pd is not None:
                neg_dens.append(nd)
                print_dens.append(pd)
        return neg_dens, print_dens

    def get_combined_curve_data(self) -> Tuple[List[float], List[float]]:
        """入力値 → プリント濃度のデータを取得"""
        if not self.has_print_data:
            return [], []

        # Noneを除外
        input_vals = []
        print_dens = []
        for iv, pd in zip(self.input_values, self.print_densities):
            if pd is not None:
                input_vals.append(iv)
                print_dens.append(pd)
        return input_vals, print_dens


def read_csv(filepath: str) -> MeasurementData:
    """
    CSVファイルから測定データを読み込む

    CSVフォーマット:
    input,negative_density,print_density
    0,1.55,0.05
    8,1.52,0.08
    ...

    print_densityは省略可能(測定①のみの場合)
    """

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSVファイルが見つかりません: {filepath}")

    data = MeasurementData()

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # ヘッダー検証
        required_fields = ['input', 'negative_density']
        for field in required_fields:
            if field not in reader.fieldnames:
                raise ValueError(f"必須フィールドがありません: {field}")

        has_print = 'print_density' in reader.fieldnames

        # データ読み込み
        for row in reader:
            try:
                input_val = int(row['input'])
                neg_density = float(row['negative_density'])

                # プリント濃度は省略可能
                print_density = None
                if has_print and row['print_density'].strip():
                    print_density = float(row['print_density'])

                data.add_measurement(input_val, neg_density, print_density)

            except ValueError as e:
                print(f"警告: 行をスキップ: {row} ({e})")
                continue

    if len(data) == 0:
        raise ValueError("有効なデータが読み込めませんでした")

    if config.VERBOSE:
        print(f"✓ データ読み込み完了: {len(data)}点")
        if data.has_print_data:
            print(f"  - 測定①(ネガ濃度): {len(data)}点")
            print(f"  - 測定②(プリント濃度): {len([p for p in data.print_densities if p is not None])}点")
        else:
            print(f"  - 測定①(ネガ濃度)のみ")

    return data


def create_template_csv(filepath: str = None):
    """
    測定データ入力用のテンプレートCSVを作成
    """

    if filepath is None:
        filepath = os.path.join(config.DATA_DIR, "measurement_template.csv")

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # ヘッダー
        writer.writerow(['input', 'negative_density', 'print_density'])

        # 33ステップのテンプレート
        for step in config.STEP_VALUES:
            writer.writerow([step, '', ''])

    print(f"✓ テンプレートCSVを作成: {filepath}")
    return filepath


def validate_data(data: MeasurementData) -> Tuple[bool, List[str]]:
    """
    測定データの妥当性を検証

    Returns:
        (検証OK, 警告メッセージリスト)
    """

    warnings = []

    # 1. データ点数チェック
    if len(data) < 10:
        warnings.append(f"データ点数が少ない: {len(data)}点 (推奨: 16点以上)")

    # 2. ネガ濃度範囲チェック
    neg_min = min(data.negative_densities)
    neg_max = max(data.negative_densities)

    if neg_min < 0.05:
        warnings.append(f"ネガDminが異常に低い: {neg_min:.2f} (期待: 0.10前後)")
    if neg_min > 0.20:
        warnings.append(f"ネガDminが高い: {neg_min:.2f} (期待: 0.10前後)")

    if neg_max < 1.30:
        warnings.append(f"ネガDmaxが低い: {neg_max:.2f} (期待: 1.50以上)")
    if neg_max > 2.00:
        warnings.append(f"ネガDmaxが高すぎる: {neg_max:.2f} (期待: 1.50-1.60)")

    # 3. プリント濃度範囲チェック
    if data.has_print_data:
        print_vals = [p for p in data.print_densities if p is not None]
        if print_vals:
            print_min = min(print_vals)
            print_max = max(print_vals)

            if print_max < 1.80:
                warnings.append(f"プリントDmaxが低い: {print_max:.2f} (目標: 2.1)")
            if print_max > 2.50:
                warnings.append(f"プリントDmaxが高すぎる: {print_max:.2f} (期待: 2.1前後)")

    # 4. 単調性チェック(ネガ濃度は入力値が増えると減少すべき)
    for i in range(len(data) - 1):
        if data.input_values[i] < data.input_values[i+1]:
            if data.negative_densities[i] < data.negative_densities[i+1]:
                warnings.append(f"ネガ濃度の単調性違反: input {data.input_values[i]} → {data.input_values[i+1]}")

    is_valid = len(warnings) == 0

    return is_valid, warnings


if __name__ == "__main__":
    # テスト用
    print("=== Precision EDN v2 - データ入力モジュール ===\n")

    # テンプレート作成
    template_path = create_template_csv()
    print(f"\nテンプレートを作成しました: {template_path}")
    print("\nこのファイルを編集して測定データを入力してください。")
