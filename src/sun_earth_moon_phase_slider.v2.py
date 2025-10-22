# -*- coding: utf-8 -*-
"""
sun_earth_moon_phase_slider.py
两个子图：
- 左：太阳固定在原点的三体公转轨道（Sun=0, Earth heliocentric, Moon geocentric+Earth）
- 右：以地球视角渲染的月相2D明暗盘
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from skyfield.api import load
from datetime import date, timedelta, datetime

# ------------------ 参数 ------------------
YEAR = datetime.now().year         # 可改年份
SLIDER_DAYS = 365                  # 365天滑块
MOON_DISC_RES = 256                # 月相图像分辨率（越大越细）
AU_RANGE = 1.2                      # 轨道图坐标范围（单位：AU），1.4 够看全地球轨道
# AU_RANGE = 0.3                     # 轨道图坐标范围（单位：AU），1.4 够看全地球轨道
# -----------------------------------------

ts = load.timescale()
eph = load('de421.bsp')
sun, earth, moon = eph['sun'], eph['earth'], eph['moon']

# =============== 工具函数 ===============

def unit(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n < 1e-12:
        return v*0.0
    return v / n

def earth_helio(t):
    """地球相对太阳的位置（AU）"""
    return sun.at(t).observe(earth).position.au  # vector Sun->Earth

def moon_geo(t):
    """月亮相对地球的位置（AU）"""
    return earth.at(t).observe(moon).position.au  # vector Earth->Moon

def moon_helio(t):
    """月亮的日心坐标（AU）"""
    e = earth_helio(t)
    m = moon_geo(t)
    return e + m

def make_moon_phase_image(t, N=MOON_DISC_RES):
    """生成月相二维明暗盘（地球视角）"""
    e2m = moon_geo(t)                 
    m2s = -moon_helio(t)              

    k = unit(e2m)                     
    s = unit(m2s)                     

    s_perp = s - np.dot(s, k) * k
    if np.linalg.norm(s_perp) < 1e-9:     
        s_perp = np.array([1.0, 0.0, 0.0]) if abs(k[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        s_perp -= np.dot(s_perp, k) * k
    i_axis = unit(s_perp)
    j_axis = unit(np.cross(k, i_axis))

    sx, sy, sz = np.dot(s, i_axis), np.dot(s, j_axis), np.dot(s, k)

    lin = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(lin, lin)
    R2 = X*X + Y*Y
    mask = R2 <= 1.0
    Z = np.zeros_like(X)
    Z[mask] = np.sqrt(1.0 - R2[mask])        

    I = np.full_like(X, np.nan, dtype=float)
    I[mask] = np.clip(sx*X[mask] + sy*Y[mask] + sz*Z[mask], 0.0, 1.0)

    return lin, lin, I

# 预先计算：一年中每天的地球、月亮位置（AU）
start_date = date(YEAR, 1, 1)
days = [start_date + timedelta(days=i) for i in range(SLIDER_DAYS)]
ts_list = [ts.utc(d.year, d.month, d.day) for d in days]

earth_xyz     = np.array([earth_helio(t) for t in ts_list])    # 地球（日心）
moon_geo_xyz  = np.array([moon_geo(t)   for t in ts_list])     # 月球（地心）

# 注：月球轨道已放大 50 倍，以便可视化。
#MOON_SCALE = 50  # 放大月球轨道 50
MOON_SCALE = 30
moon_xyz = earth_xyz + moon_geo_xyz * MOON_SCALE # 月球（日心 = 地心 + 地球位置                   

earth_orbit = earth_xyz.T
moon_orbit  = moon_xyz.T

# 初始索引
idx0 = 0
ex0, ey0, ez0 = earth_xyz[idx0]
mx0, my0, mz0 = moon_xyz[idx0]
x_lin, y_lin, I0 = make_moon_phase_image(ts_list[idx0])

# =============== 画布与初始图 ===============
fig = make_subplots(
    rows=1, cols=2,
    column_widths=[0.9, 0.1],
    specs=[[{"type": "scene"}, {"type": "xy"}]],
    horizontal_spacing=0.04,
    subplot_titles=("公转轨道图（Sun@0，AU）", "月相（地球视角）")
)

# 左：静态轨道参考线
fig.add_trace(go.Scatter3d(
    x=earth_orbit[0], y=earth_orbit[1], z=earth_orbit[2],
    mode="lines", line=dict(width=2, color="rgba(100,160,255,0.35)"),
    name="地球轨道", showlegend=True
), row=1, col=1)

# 左：月球轨道（静态，日心系）
fig.add_trace(go.Scatter3d(
    x=moon_orbit[0], y=moon_orbit[1], z=moon_orbit[2],
    mode="lines", line=dict(width=3, color="rgba(255,255,255,0.8)"), # 加粗+白色
    name="月球轨道", showlegend=True
), row=1, col=1)

# 左：太阳固定在原点
fig.add_trace(go.Scatter3d(
    x=[0], y=[0], z=[0],
    mode="markers", marker=dict(size=9, color="orange"),
    name="太阳"
), row=1, col=1)

# 左：地球、月亮（当天，动态 trace）
fig.add_trace(go.Scatter3d(
    x=[ex0], y=[ey0], z=[ez0],
    mode="markers", marker=dict(size=5, color="deepskyblue"), # 地球稍大
    name="地球"
), row=1, col=1)

fig.add_trace(go.Scatter3d(
    x=[mx0], y=[my0], z=[mz0],
    mode="markers", marker=dict(size=3.5, color="white"),     # 月亮放大
    name="月亮"
), row=1, col=1)

# 右：月相二维盘（热图渲染）
fig.add_trace(go.Heatmap(
    z=I0, x=x_lin, y=y_lin, zmin=0, zmax=1,
    colorscale=[[0, "rgb(22,22,22)"], [1, "rgb(235,235,235)"]],
    showscale=False
), row=1, col=2)

# =============== 帧更新 ===============
frames = []
for i, t in enumerate(ts_list):
    ex, ey, ez = earth_xyz[i]
    # 用和静态轨道完全一致的公式来算月亮（地球位置 + 放大后的地月向量）
    mgx, mgy, mgz = moon_geo_xyz[i]
    mx = ex + MOON_SCALE * mgx
    my = ey + MOON_SCALE * mgy
    mz = ez + MOON_SCALE * mgz

    _, _, I = make_moon_phase_image(t, N=MOON_DISC_RES)
    _, _, I = make_moon_phase_image(t, N=MOON_DISC_RES)

    frame = go.Frame(
        name=str(days[i]),
        data=[
            go.Scatter3d(x=[ex], y=[ey], z=[ez],
                         mode="markers", marker=dict(size=6, color="rgba(0,191,255,0.6)"),
                         name="地球"),
            go.Scatter3d(x=[mx], y=[my], z=[mz],
                         mode="markers", marker=dict(size=3.5, color="white"),
                         name="月亮"),
            go.Heatmap(z=I, x=x_lin, y=y_lin, zmin=0, zmax=1,
                       colorscale=[[0, "rgb(22,22,22)"], [1, "rgb(235,235,235)"]],
                       showscale=False)
        ],
        traces=[3, 4, 5]  # ✅ 对应 地球, 月亮, 月相
    )
    frames.append(frame)

fig.update(frames=frames)

# =============== 外观 ===============
fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1, row=1, col=2)
fig.update_yaxes(visible=False, row=1, col=2)

fig.update_layout(
    scene=dict(
        xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
        bgcolor="black",
        camera=dict(eye=dict(x=0, y=-2.0, z=1.5)) # 从北极上方看
    ),
    scene_aspectmode="data",
    paper_bgcolor="black",
    plot_bgcolor="black",
    font=dict(color="white"),

    # 播放 / 暂停按钮位置：放到进度条上方
    updatemenus=[{
        "type": "buttons",
        "direction": "left",
        "type": "buttons", "direction": "left",
        "x": 0.25, "y": -0.05, "xanchor": "left", "yanchor": "top",
        "showactive": False,
        "buttons": [
            {"label": "▶ Play", "method": "animate",
            "args": [None, {"frame": {"duration": 80, "redraw": True},
                             "fromcurrent": True, "transition": {"duration": 0}}]},
            {"label": "⏸ Pause", "method": "animate",
            "args": [[None], {"frame": {"duration": 0, "redraw": True},
                               "mode": "immediate", "transition": {"duration": 0}}]}
        ]
    }],

    # 时间进度条
    sliders=[{
        "active": 0, "x": 0.25, "y": -0.20, "len": 0.6,   # 下移一点
        "currentvalue": {"prefix": "日期：", "visible": True},
        "steps": [{"args": [[f.name], {"mode": "immediate",
                                       "frame": {"duration": 0, "redraw": True},
                                       "transition": {"duration": 0}}],
                   "label": f.name, "method": "animate"} for f in frames]
    }]
)

# 右图锁定缩放，左图可缩放
fig.update_xaxes(fixedrange=True, row=1, col=2)
fig.update_yaxes(fixedrange=True, row=1, col=2)
fig.update_layout(scene_dragmode="orbit")

fig.update_scenes(xaxis_range=[-AU_RANGE, AU_RANGE],
                  yaxis_range=[-AU_RANGE, AU_RANGE],
                  zaxis_range=[-AU_RANGE, AU_RANGE])

fig.show()
