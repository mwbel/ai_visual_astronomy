import matplotlib.pyplot as plt
import numpy as np

# 月相名称与对应的符号
phases = [
    ("新月", "🌑"),
    ("娥眉月", "🌒"),
    ("上弦月", "🌓"),
    ("盈凸月", "🌔"),
    ("满月", "🌕"),
    ("亏凸月", "🌖"),
    ("下弦月", "🌗"),
    ("残月", "🌘")
]

# 环形布局参数
num_phases = len(phases)
theta = np.linspace(0, 2 * np.pi, num_phases, endpoint=False)

# 圆圈坐标
r = 5
x = r * np.cos(theta)
y = r * np.sin(theta)

# 绘制
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_aspect("equal")
ax.axis("off")

# 在圆周上绘制月相
for i, ((name, emoji), (xi, yi)) in enumerate(zip(phases, zip(x, y))):
    ax.text(xi, yi, emoji, fontsize=28, ha="center", va="center")
    ax.text(xi, yi - 1, name, fontsize=12, ha="center", va="center")

# 添加中心文字
ax.text(0, 0, "月相变化", fontsize=16, ha="center", va="center", weight="bold")

plt.show()
