from skyfield.api import load, Topos, load_file
from pathlib import Path
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import numpy as np

# 检查 de421.bsp 文件是否存在
eph_file_name = 'de421.bsp'
eph_path = Path(__file__).parent / eph_file_name

if not eph_path.exists():
    print(f"错误：找不到文件 '{eph_file_name}'。请先把 {eph_file_name} 放在项目根目录。")
    exit()

# 从本地文件加载星历数据
eph = load(str(eph_path))

# 获取当前系统时间并设置为当日0点
ts = load.timescale()
now = datetime.now()
start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

# 生成当日24小时的时间点（从00:00到23:00）
times_dt = [start_of_day + timedelta(hours=h) for h in range(24)]
years = [t.year for t in times_dt]
months = [t.month for t in times_dt]
days = [t.day for t in times_dt]
hours = [t.hour for t in times_dt]
minutes = [t.minute for t in times_dt]
seconds = [t.second for t in times_dt]
t_skyfield = ts.utc(years, months, days, hours, minutes, seconds)

# 定义行星及其对应的 Skyfield 对象和点大小
planets_data = {
    '水星': {'obj': eph['mercury'], 'size': 5, 'color': 'lightgray'},
    '金星': {'obj': eph['venus'], 'size': 6, 'color': 'gold'},
    '地球': {'obj': eph['earth'], 'size': 7, 'color': 'blue'},
    '火星': {'obj': eph['mars'], 'size': 6, 'color': 'red'},
    '木星': {'obj': eph['jupiter barycenter'], 'size': 10, 'color': 'peru'},
    '土星': {'obj': eph['saturn barycenter'], 'size': 9, 'color': 'darkgoldenrod'},
    '天王星': {'obj': eph['uranus barycenter'], 'size': 8, 'color': 'cyan'},
    '海王星': {'obj': eph['neptune barycenter'], 'size': 8, 'color': 'darkblue'},
}

# 创建 Plotly 3D 图表
fig = go.Figure()

# 添加太阳
fig.add_trace(go.Scatter3d(
    x=[0], y=[0], z=[0],
    mode='markers',
    marker=dict(symbol='circle', size=15, color='orange'),
    name='太阳',
    hovertemplate='<b>太阳</b><br>x: %{x:.2f} AU<br>y: %{y:.2f} AU<br>z: %{z:.2f} AU<extra></extra>'
))

# 计算并添加行星轨迹和当前点
for name, data in planets_data.items():
    planet_obj = data['obj']
    size = data['size']
    color = data['color']

    # 计算行星相对于太阳在24小时内的位置
    positions = (planet_obj - eph['sun']).at(t_skyfield).position.au
    x_coords = positions[0]
    y_coords = positions[1]
    z_coords = positions[2]

    # 绘制当日24小时的轨迹线
    fig.add_trace(go.Scatter3d(
        x=x_coords, y=y_coords, z=z_coords,
        mode='lines+markers',
        marker=dict(size=size / 2, opacity=0.6, color=color),
        line=dict(color=color, width=2),
        name=f'{name}轨迹',
        hovertemplate=f'<b>{name}</b><br>时间: %{{text}}<br>x: %{{x:.2f}} AU<br>y: %{{y:.2f}} AU<br>z: %{{z:.2f}} AU<extra></extra>',
        text=[t.strftime('%H:%M') for t in times_dt]
    ))

    # 在当天最后一个整点（23:00）位置绘制高亮的 diamond 标记
    last_point_x = x_coords[-1]
    last_point_y = y_coords[-1]
    last_point_z = z_coords[-1]

    fig.add_trace(go.Scatter3d(
        x=[last_point_x], y=[last_point_y], z=[last_point_z],
        mode='markers',
        marker=dict(symbol='diamond', size=size * 1.5, color=color, line=dict(width=1, color='black')),
        name=f'{name}当前点',
        hovertemplate=f'<b>{name} (23:00)</b><br>x: %{{x:.2f}} AU<br>y: %{{y:.2f}} AU<br>z: %{{z:.2f}} AU<extra></extra>'
    ))

# 更新布局
fig.update_layout(
    title=f"{start_of_day.strftime('%Y-%m-%d')} 8大行星当日24小时轨迹 (相对太阳)",
    scene=dict(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=""),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=""),
        zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=""),
        aspectmode='data',  # 保持坐标比例一致
    ),
    showlegend=True,  # 保留图例
    margin=dict(l=0, r=0, b=0, t=40)
)

# 显示图表
fig.show()
