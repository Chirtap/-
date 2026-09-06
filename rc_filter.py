# -*- coding: utf-8 -*-
"""
rc_filter.py —— RC 低通滤波电路 · 交流扫频分析

电路结构：
    V_in —— R (1 kΩ) —— V_out
                          |
                        C (100 nF)
                          |
                         GND

仿真内容：
    交流小信号扫频分析（10 Hz ~ 1 MHz），计算幅频响应 / 相频响应，
    绘制 Bode 图并保存为 rc_filter_response.png。

运行方式：
    python rc_filter.py
"""

import math

import numpy as np
import matplotlib.pyplot as plt

import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging()

from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *


# ============================ 元件参数 ============================
R_VAL = 1.0e3      # 1 kΩ
C_VAL = 100.0e-9   # 100 nF

# 理论截止频率：fc = 1 / (2 * pi * R * C)
fc_theory = 1.0 / (2.0 * math.pi * R_VAL * C_VAL)
print('RC 低通滤波器截止频率(理论) fc = {:.1f} Hz'.format(fc_theory))

# ============================ 搭建电路 ============================
circuit = Circuit('RC Low-Pass Filter')

# 正弦电压源：默认交流幅值 ac = 1，直接作为交流扫频的激励（输入幅值 = 1 V）
circuit.SinusoidalVoltageSource('input', 'input', circuit.gnd, amplitude=1@u_V)
circuit.R('filter', 'input', 'output', R_VAL)
circuit.C('filter', 'output', circuit.gnd, C_VAL)

# ============================ 交流扫频分析 ============================
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.ac(
    start_frequency=10@u_Hz,          # 10 Hz
    stop_frequency=1@u_MHz,           # 1 MHz
    number_of_points=10,
    variation='dec',                  # 每十倍频程 10 个点
)

frequency = np.array(analysis.frequency)

# 先把 analysis 返回的节点电压转换成普通 numpy 数组，再做运算与绘图
vout = np.array(analysis['output'])              # 复数电压（输入幅值=1，|Vout| 即增益）
gain_db = 20.0 * np.log10(np.abs(vout))          # 幅频响应
phase_deg = np.angle(vout, deg=True)             # 相频响应

# 距理论截止频率最近的数据点
idx_fc = int(np.argmin(np.abs(frequency - fc_theory)))
print('fc 附近实测增益: {:.2f} dB (理论 -3.01 dB)'.format(gain_db[idx_fc]))

# ============================ 绘图并保存 ============================
fig, (ax_gain, ax_phase) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

# 幅频响应曲线
ax_gain.semilogx(frequency, gain_db, 'b.-', label='Magnitude response (simulated)')
ax_gain.axvline(fc_theory, color='red', linestyle='--', linewidth=1)
ax_gain.axhline(-3.0, color='gray', linestyle=':', linewidth=1)
ax_gain.plot(frequency[idx_fc], gain_db[idx_fc], 'ro')
ax_gain.annotate(
    'fc = {:.0f} Hz\n({:.2f} dB)'.format(fc_theory, gain_db[idx_fc]),
    xy=(fc_theory, gain_db[idx_fc]),
    xytext=(fc_theory * 0.35, gain_db[idx_fc] - 14),
    arrowprops=dict(arrowstyle='->'),
    fontsize=9,
)
ax_gain.set_ylabel('Gain [dB]')
ax_gain.set_title('RC Low-Pass Filter - Frequency Response (R = 1 kOhm, C = 100 nF)')
ax_gain.grid(True, which='both', alpha=0.4)
ax_gain.legend(loc='lower left')

# 相频响应曲线
ax_phase.semilogx(frequency, phase_deg, 'g.-')
ax_phase.axvline(fc_theory, color='red', linestyle='--', linewidth=1)
ax_phase.set_xlabel('Frequency [Hz]')
ax_phase.set_ylabel('Phase [deg]')
ax_phase.grid(True, which='both', alpha=0.4)

plt.tight_layout()
plt.savefig('rc_filter_response.png', dpi=150)
print('幅频/相频响应曲线已保存为 rc_filter_response.png')
plt.show()
