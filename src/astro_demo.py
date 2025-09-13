from skyfield.api import load
from pathlib import Path
import matplotlib.pyplot as plt

# 从本地文件加载（确保 de421.bsp 在和 astro_demo.py 同一个目录）
eph_path = Path(__file__).parent / 'de421.bsp'
planets = load(str(eph_path))

earth, sun = planets['earth'], planets['sun']
ts = load.timescale()

# 计算 2024 年每个月的地球相对太阳的位置
times = ts.utc(2024, range(1, 13), 1)
positions = (earth - sun).at(times).position.au  # 单位：AU

# 绘制轨道
plt.figure(figsize=(6, 6))
plt.plot(positions[0], positions[1], 'o-', label='Earth (monthly)')
plt.scatter(0, 0, color='orange', marker='*', s=200, label='Sun')
plt.title("Earth Orbit Projection (2024)")
plt.xlabel("x (AU)")
plt.ylabel("y (AU)")
plt.axis("equal")
plt.legend()
plt.grid(True)
plt.show()
