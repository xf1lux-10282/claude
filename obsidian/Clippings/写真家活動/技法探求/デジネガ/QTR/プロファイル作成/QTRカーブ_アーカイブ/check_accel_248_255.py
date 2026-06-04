#!/usr/bin/env python3
import numpy as np

def read_quad_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    quad_values = []
    for line in lines:
        line = line.strip()
        if line.isdigit():
            quad_values.append(int(line))
    return np.array(quad_values[:256])

v7 = read_quad_file('PX1V-PtPd-SP1v7.quad')
v16 = read_quad_file('PX1V-PtPd-SP1v16.quad')

print('Input 248-255の詳細分析:')
print('Input | V7    | V16   | Δ調整  | V16前との差 | V7前との差 | 加速比')
print('------|-------|-------|--------|-------------|------------|-------')
for i in range(248, 256):
    adj = v16[i] - v7[i]
    if i > 248:
        v16_diff = v16[i] - v16[i-1]
        v7_diff = v7[i] - v7[i-1]
        accel_ratio = v16_diff / v7_diff if v7_diff != 0 else 1.0
        print(f'{i:3d}   | {v7[i]:5d} | {v16[i]:5d} | {adj:+6d} | {v16_diff:+11d} | {v7_diff:+10d} | {accel_ratio:6.3f}')
    else:
        print(f'{i:3d}   | {v7[i]:5d} | {v16[i]:5d} | {adj:+6d} | ---         | ---        | ---')

print('\n加速比が徐々に大きくなっていれば加速カーブ成功')
print('1.0未満: 減速、1.0: 等速、1.0超: 加速')
