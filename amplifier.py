import PySpice.Logging.Logging as Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

logger = Logging.setup_logging()

circuit = Circuit('NMOS Amplifier')
Vdd = 5@u_V
Rg1 = 60@u_kΩ
Rg2 = 40@u_kΩ
Rd = 2@u_kΩ

circuit.model('NMOS', 'nmos', level=1, kp=1.6e-3, vto=1, lambda_=0.02)
circuit.V('DD', 'Vdd', circuit.gnd, Vdd)
circuit.R('g1', 'Vdd', 'G', Rg1)
circuit.R('g2', 'G', circuit.gnd, Rg2)
circuit.R('d', 'Vdd', 'D', Rd)
circuit.M('1', 'D', 'G', circuit.gnd, circuit.gnd, model='NMOS')

circuit.V('Vin', 'G', circuit.gnd, 'DC 2 AC 10mV SIN(0 10mV 1kHz)')

simulator = circuit.simulator()
op = simulator.operating_point()

# === 万能取值方式：尝试多种方法 ===
def get_voltage(node):
    try:
        # 方法1: 直接取标量
        return float(op[node])
    except:
        try:
            # 方法2: 用 .magnitude
            return op[node].magnitude
        except:
            try:
                # 方法3: 转成数组再取第一个
                return np.array(op[node])[0]
            except:
                # 方法4: 从 nodes 里取
                return float(op.nodes[node])
                # 如果还不行，返回 None

Vg = get_voltage('g')
Vd = get_voltage('d')

if Vg is None or Vd is None:
    print("无法读取节点电压，请检查 SPICE 输出")
    exit()

Id = (5.0 - Vd) / 2e3
Vth = 1.0
Vgs = Vg
Vds = Vd

print(f"V_GS = {Vgs:.3f} V")
print(f"I_D = {Id*1000:.3f} mA")
print(f"V_DS = {Vds:.3f} V")
if Vgs > Vth and Vds > (Vgs - Vth):
    print("结论: NMOS 工作在饱和区 ✓")
else:
    print("结论: NMOS 不在饱和区")

gm = 2 * 0.8e-3 * (Vgs - Vth)
Av = -gm * 2e3
print(f"gm = {gm*1000:.3f} mS")
print(f"理论电压增益 Av = {Av:.2f}")

# 瞬态仿真
tran = simulator.transient(step_time=0.01@u_ms, end_time=5@u_ms)
time = np.array(tran.time)
vin = np.array(tran['G'])
vout = np.array(tran['D'])

plt.figure()
plt.plot(time, vin, label='Input (Gate)')
plt.plot(time, vout, label='Output (Drain)')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.legend()
plt.grid()
plt.savefig('amplifier_wave.png')
plt.show()
print("瞬态波形图已保存为 amplifier_wave.png")
