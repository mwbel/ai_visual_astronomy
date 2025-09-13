from skyfield.api import load, Topos, load_file
from pathlib import Path
import plotly.graph_objects as go
from datetime import datetime
import os

# 检查 de421.bsp 文件是否存在
eph_file_name = 'de421.bsp'
eph_path = Path(__file__).parent / eph_file_name

if not eph_path.exists():
    print(f"错误：找不到文件 '{eph_file_name}'。请先把 {eph_file_name} 放在项目根目录。")
    exit()

## 从本地文件加载星历数据
eph = load(str(eph_path))

## 获取当前系统时间
ts = load.timescale()
t = ts.now()

## 定义行星及其对应的 Skyfield 对象和点大小
planets_data = {
    '水星': {'obj': eph['mercury'], 'size': 5},
    '金星': {'obj': eph['venus'], 'size': 6},
    '地球': {'obj': eph['earth'], 'size': 7},
    '火星': {'obj': eph['mars'], 'size': 6},
    '木星': {'obj': eph['jupiter barycenter'], 'size': 10}, # 木星使用质心
    '土星': {'obj': eph['saturn barycenter'], 'size': 9},  # 土星使用质心
    '天王星': {'obj': eph['uranus barycenter'], 'size': 8}, # 天王星使用质心
    '海王星': {'obj': eph['neptune barycenter'], 'size': 8}, # 海王星使用质心
}

## 创建 Plotly 3D 图表
fig = go.Figure()

## 添加太阳
fig.add_trace(go.Scatter3d(
    x=[0], y=[0], z=[0],
    mode='markers',
    marker=dict(symbol='circle', size=20, color='orange'),
    name='太阳',
    hovertemplate='<b>太阳</b><br>x: %{x:.2f} AU<br>y: %{y:.2f} AU<br>z: %{z:.2f} AU<extra></extra>'
))

# 计算并添加行星位置
for name, data in planets_data.items():
    planet_obj = data['obj']
    size = data['size']

    # 计算行星相对于太阳的位置
    position = (planet_obj - eph['sun']).at(t).position.au

    fig.add_trace(go.Scatter3d(
        x=[position[0]], y=[position[1]], z=[position[2]],
        mode='markers',
        marker=dict(size=size, opacity=0.8),
        name=name,
        hovertemplate=f'<b>{name}</b><br>x: %{{x:.2f}} AU<br>y: %{{y:.2f}} AU<br>z: %{{z:.2f}} AU<extra></extra>'
    ))

# 更新布局
fig.update_layout(
    title=f"太阳系行星三维位置 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
    scene=dict(
        xaxis_title="x (AU)",
        yaxis_title="y (AU)",
        zaxis_title="z (AU)",
        aspectmode='data', # 保持坐标比例一致
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        zaxis=dict(showgrid=True),
    ),
    margin=dict(l=0, r=0, b=0, t=40)
)

# 显示图表
fig.show()
