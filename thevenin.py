# -*- coding: utf-8 -*-
"""
thevenin.py —— 戴维南定理验证电路

电路拓扑（一端口网络，端口为节点 b 对地）:

   Vs(12V) ── R1(4kΩ) ── a ── R2(6kΩ) ── b（端口）──o
                                            │
                                          R3(12kΩ)
                                            │
                                           GND

   （R3 属于一端口网络的内部支路，跨接在端口 b 与地之间；
     验证时可外接负载 Rload，与 R3 并联在端口上。）

仿真方法：
    1) 开路电压 Voc：端口开路（不接负载），直流工作点仿真直接读出 V(b)；
    2) 等效电阻 Rth：端口短接到地，直流工作点仿真算出短路电流 Isc，
       由 Rth = Voc / Isc 得到；
    3) 等效验证：在端口接入负载 RL = Rth，理论负载电压应为 Voc / 2。

理论手算：
    Voc_th = Vs * R3 / (R1 + R2 + R3)
    Rth_th = R3 * (R1 + R2) / (R1 + R2 + R3)

运行方式：
    python thevenin.py
"""

import numpy as np
import matplotlib.pyplot as plt

import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging()

from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *


# ============================ 电路参数 ============================
VS = 12.0        # 电源电压 V
R1 = 4.0e3       # 4 kΩ
R2 = 6.0e3       # 6 kΩ
R3 = 12.0e3      # 12 kΩ


def build_network(short_port=False, load_resistance=None):
    """搭建待验证的一端口网络。

    short_port=True          : 在端口 b 上并联 0 V 电压源实现“短路”；
    load_resistance 非 None  : 在端口 b 上接入该阻值的负载。
    """
    circuit = Circuit('Thevenin Network')
    circuit.V('src', 'rail', circuit.gnd, VS)
    circuit.R('r1', 'rail', 'a', R1)
    circuit.R('r2', 'a', 'b', R2)
    circuit.R('r3', 'b', circuit.gnd, R3)
    if short_port:
        circuit.V('short', 'b', circuit.gnd, 0.0)   # 短路电流测试
    if load_resistance is not None:
        circuit.R('load', 'b', circuit.gnd, load_resistance)
    return circuit


def node_voltage(op, name):
    """从工作点结果中读取某节点电压（V）。"""
    try:
        return float(getattr(op, name))
    except (AttributeError, TypeError):
        pass
    try:
        return float(op[name])
    except Exception:
        return float(op.nodes[name])


def run_operating_point(**kwargs):
    """创建电路并做直流工作点仿真。"""
    circuit = build_network(**kwargs)
    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    return simulator.operating_point()


# ============================ 理论值（手算） ============================
voc_th = VS * R3 / (R1 + R2 + R3)            # 12 * 12 / 22 ≈ 6.545 V
rth_th = R3 * (R1 + R2) / (R1 + R2 + R3)     # 12k || 10k ≈ 5.455 kΩ
print('---- 理论手算 ----')
print('开路电压 Voc = {:.4f} V'.format(voc_th))
print('等效电阻 Rth = {:.4f} kΩ'.format(rth_th / 1e3))

# ============================ 1. 开路电压（仿真） ============================
op_open = run_operating_point()
voc_sim = node_voltage(op_open, 'b')
print('---- 仿真：端口开路 ----')
print('端口电压 V(b) = Voc = {:.4f} V'.format(voc_sim))

# ============================ 2. 短路电流 -> 等效电阻 ============================
op_short = run_operating_point(short_port=True)
va_short = node_voltage(op_short, 'a')
vb_short = node_voltage(op_short, 'b')
# 端口短路后，短路电流即流过 R2 进入端口 b 的电流（V(b) = 0）
isc = (va_short - vb_short) / R2
rth_sim = voc_sim / isc
print('---- 仿真：端口短路 ----')
print('端口短路电流 Isc = {:.4f} mA'.format(isc * 1e3))
print('等效电阻 Rth = Voc / Isc = {:.4f} kΩ'.format(rth_sim / 1e3))

# ============================ 3. 负载验证戴维南等效 ============================
# 端口接入负载 RL = Rth，戴维南等效分压应为 Voc / 2
op_load = run_operating_point(load_resistance=rth_sim)
v_load_sim = node_voltage(op_load, 'b')
v_half_theory = voc_sim / 2.0
print('---- 验证：接入负载 RL = Rth = {:.4f} kΩ ----'.format(rth_sim / 1e3))
print('仿真负载电压 V(load) = {:.4f} V，戴维南等效预测 Voc/2 = {:.4f} V'.format(
    v_load_sim, v_half_theory))

# ============================ 误差检查 ============================
err_voc = abs(voc_sim - voc_th) / voc_th * 100.0
err_rth = abs(rth_sim - rth_th) / rth_th * 100.0
print('---- 误差检查 ----')
print('Voc 仿真 vs 理论  误差 = {:.3f}%'.format(err_voc))
print('Rth 仿真 vs 理论  误差 = {:.3f}%'.format(err_rth))

# ============================ 绘图并保存 ============================
v_axis = np.linspace(0.0, voc_sim, 300)
i_load_line = (voc_sim - v_axis) / rth_sim * 1e3     # 戴维南等效负载线，单位 mA
i_at_load = (voc_sim - v_load_sim) / rth_sim * 1e3

fig, ax = plt.subplots(figsize=(7.5, 5.5))
ax.plot(v_axis, i_load_line, 'b-', label='Load line of Thevenin equivalent')
ax.plot(voc_sim, 0.0, 'go', markersize=9,
        label='Open circuit ({:.3f} V, 0 mA)'.format(voc_sim))
ax.plot(0.0, isc * 1e3, 'ro', markersize=9,
        label='Short circuit (0 V, {:.3f} mA)'.format(isc * 1e3))
ax.plot(v_load_sim, i_at_load, 'm^', markersize=9,
        label='Load point V(Rload=Rth) = {:.3f} V'.format(v_load_sim))
ax.set_xlabel('Port voltage V [V]')
ax.set_ylabel('Port current I [mA]')
ax.set_title('Thevenin Theorem Verification\n'
             'Voc = {:.4f} V,  Rth = {:.4f} kOhm'.format(voc_sim, rth_sim / 1e3))
ax.grid(True, alpha=0.4)
ax.legend(loc='upper right', fontsize=9)
plt.tight_layout()
plt.savefig('thevenin_verify.png', dpi=150)
print('验证结果图已保存为 thevenin_verify.png')
plt.show()
