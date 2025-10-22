# -*- coding: utf-8 -*-
"""
sun_earth_moon_phase_slider.py
两个子图：
- 左：太阳固定在原点的三体公转轨道（Sun=0, Earth heliocentric, Moon geocentric+Earth）
- 右：以地球视角渲染的月相2D明暗盘
"""

import numpy as np
import plotly.graph_objects as go
import os
from plotly.subplots import make_subplots
from skyfield.api import load
from datetime import date, timedelta, datetime
from PIL import Image
from scipy.ndimage import map_coordinates

# ------------------ 参数 ------------------
YEAR = datetime.now().year         # 可改年份
SLIDER_DAYS = 365                  # 365天滑块   闰年需要多一天（需要可改进）
MOON_DISC_RES = 256              # 月相图像分辨率（越大越细）
AU_RANGE = 1.2                      # 3D视景范围---轨道图坐标范围（单位：AU），1.4 够看全地球轨道
# AU_RANGE = 0.3                     # 轨道图坐标范围（单位：AU），1.4 够看全地球轨道
# -----------------------------------------

ts = load.timescale()
eph = load('de421.bsp')
sun, earth, moon = eph['sun'], eph['earth'], eph['moon']

# 载入月球表面纹理（灰度或彩色均可）
moon_texture = Image.open("src/moon_texture_map.tif").convert("L")  # 灰度
moon_texture = np.array(moon_texture) / 255.0  # 归一化到 [0,1]

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
    """生成带纹理+光照并带 alpha 的月相 RGBA 图（用于 go.Image）"""
    # 向量
    e2m = moon_geo(t)            # Earth->Moon (AU)
    m2s = -moon_helio(t)         # Moon->Sun  (Sun at origin)
    k = unit(e2m)                # 观察方向
    s = unit(m2s)                # 入射光方向

    # 观察坐标系 (i, j, k)
    s_perp = s - np.dot(s, k) * k
    if np.linalg.norm(s_perp) < 1e-9:
        s_perp = np.array([1, 0, 0]) if abs(k[0]) < 0.9 else np.array([0, 1, 0])
        s_perp -= np.dot(s_perp, k) * k
    i_axis = unit(s_perp)
    j_axis = unit(np.cross(k, i_axis))

    # sx, sy, sz = np.dot(s, i_axis), np.dot(s, j_axis), np.dot(s, k)

    # 单位圆盘网格
    lin = np.linspace(-1, 1, N, endpoint=False)
    X, Y = np.meshgrid(lin, lin)
    R2 = X*X + Y*Y
    # 缩一点点，避免边缘锯齿/外圈
    mask = R2 <= (1.0 - 1e-6)
    Z = np.zeros_like(X)
    Z[mask] = np.sqrt(1.0 - R2[mask])

    ## === 计算月球自转: 保证同一面朝地球 ===

    # 单位球面坐标 (lon, lat)
    Xs = X[mask]
    Ys = Y[mask]
    Zs = Z[mask]
    lon = np.arctan2(Ys, Xs)         # 经度， [-π, π]
    lat = np.arcsin(Zs)             # 纬度   [-π/2, π/2]

    # 同步自转：保持始终同一面对地球
    theta = np.arctan2(e2m[1], e2m[0])   # 月球在轨道上的角度 (地心参考系)
    lon = lon - theta

    # 映射到纹理坐标 [0,1]
    H, W = moon_texture.shape
    u = ((lon + np.pi) / (2*np.pi)) * (W - 1)
    v = ((np.pi/2 - lat) / np.pi) * (H - 1)

    # 修正：必须转换为 int
    u = np.clip(u.round().astype(int), 0, W-1)
    v = np.clip(v.round().astype(int), 0, H-1)

    # 从纹理取灰度，逐点索引， 确保 tex_val 保持 (N, N)
    # 生成 tex_val，与 X,Y 同尺寸
    tex_val = np.zeros_like(X, dtype=float)
    tex_val[mask] = moon_texture[v, u]

    # Lambert 光照
    # 给光照加一个 微弱的底光（ambient light），这样即使新月也能看到月球表面暗纹。
    ambient = 0.08   # 环境光强度 (0.05~0.15 建议)
    I = np.zeros_like(X, dtype=float)
    I[mask] = np.clip( ambient + s[0]*X[mask] + s[1]*Y[mask] + s[2]*Z[mask], ambient, 1.0)

    # 纹理融合（灰度）
    # tex = moon_texture[:N, :N]           # [0,1]
    val = np.zeros_like(X, dtype=float)
    val[mask] = tex_val[mask] * I[mask]      # 纹理 × 光照 → 明暗
    
    # gamma 校正：让暗部更亮
    gamma = 0.6   # <1 提亮暗部, >1 压暗暗部
    val[mask] = val[mask] ** gamma
    
    # 生成 RGBA（0~255）
    img = np.zeros((N, N, 4), dtype=np.uint8)
    g = (val * 255).astype(np.uint8)
    img[..., 0] = g
    img[..., 1] = g
    img[..., 2] = g
    img[..., 3] = (mask.astype(np.uint8) * 255)  # 圆外完全透明

    return img

# 预先计算：一年中每天的地球、月亮位置（AU）
start_date = date(YEAR, 1, 1)
FRAME_STEP = 5   # 每 5 天一个帧
days = [start_date + timedelta(days=i*1) for i in range(0,SLIDER_DAYS,FRAME_STEP)]
ts_list = [ts.utc(d.year, d.month, d.day) for d in days]

earth_xyz     = np.array([earth_helio(t) for t in ts_list])    # 地球（日心）
moon_geo_xyz  = np.array([moon_geo(t)   for t in ts_list])     # 月球（地心）

# 注：月球轨道已放大 50 倍，以便可视化。
#MOON_SCALE = 50  # 放大月球轨道 50
MOON_SCALE = 27
moon_xyz = earth_xyz + moon_geo_xyz * MOON_SCALE # 月球（日心 = 地心 + 地球位置                   

earth_orbit = earth_xyz.T
moon_orbit  = moon_xyz.T

# 初始索引
idx0 = 0
ex0, ey0, ez0 = earth_xyz[idx0]
mx0, my0, mz0 = moon_xyz[idx0]
# x_lin, y_lin, texI0 
img0 = make_moon_phase_image(ts_list[idx0])

earth_orbit_dense = earth_xyz.T
moon_orbit_dense  = moon_xyz.T
# =============== 画布与初始图 ===============
fig = make_subplots(
    rows=1, cols=2,
    column_widths=[0.7, 0.3],
    specs=[[{"type": "scene"}, {"type": "xy"}]],
    horizontal_spacing=0.04,
    subplot_titles=("公转轨道图（Sun@0，AU）", "月相（地球视角）")
)

# ========= 高密度采样：只画轨道用 =========
# days_dense = [start_date + timedelta(days=i*(SLIDER_DAYS/2000)) for i in range(2000)]
days_dense = [start_date + timedelta(days=i*0.1) for i in range(SLIDER_DAYS*10)]
ts_dense   = [ts.utc(d.year, d.month, d.day) for d in days_dense]

earth_orbit_dense = np.array([earth_helio(t) for t in ts_dense]).T
moon_orbit_dense  = np.array([(earth_helio(t) + moon_geo(t) * MOON_SCALE) for t in ts_dense]).T

# 左：静态地球轨道（高密度，光滑）
fig.add_trace(go.Scatter3d(
    x=earth_orbit_dense[0], y=earth_orbit_dense[1], z=earth_orbit_dense[2],
    mode="lines", line=dict(width=2, color="rgba(100,160,255,0.35)"),
    name="地球轨道", showlegend=True
), row=1, col=1)

# 左：静态月球轨道（高密度，光滑）
fig.add_trace(go.Scatter3d(
    x=moon_orbit_dense[0], y=moon_orbit_dense[1], z=moon_orbit_dense[2],
    mode="lines", line=dict(width=3, color="rgba(255,255,255,0.8)"),
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

# 右：月相二维盘（图像渲染，带透明边）
img0 = make_moon_phase_image(ts_list[idx0])
fig.add_trace(go.Image(z=img0), row=1, col=2)

# =============== 帧更新 ===============
frames = []
for i, t in enumerate(ts_list):
    ex, ey, ez = earth_xyz[i]
    # 用和静态轨道完全一致的公式来算月亮（地球位置 + 放大后的地月向量）
    mgx, mgy, mgz = moon_geo_xyz[i]
    mx = ex + MOON_SCALE * mgx
    my = ey + MOON_SCALE * mgy
    mz = ez + MOON_SCALE * mgz

    img = make_moon_phase_image(t, N=MOON_DISC_RES)

    frame = go.Frame(
        name=str(days[i]),
        data=[
            go.Scatter3d(x=[ex], y=[ey], z=[ez],
                         mode="markers", marker=dict(size=6, color="rgba(0,191,255,0.6)"),
                         name="地球"),
            go.Scatter3d(x=[mx], y=[my], z=[mz],
                         mode="markers", marker=dict(size=3.5, color="white"),
                         name="月亮"),
            go.Image(z=img)
        ],
        traces=[3, 4, 5]  # ✅ 对应 地球, 月亮, 月相
    )
    frames.append(frame)

fig.update(frames=frames)

# =============== 外观 ===============
fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1, row=1, col=2)
fig.update_yaxes(visible=False, row=1, col=2)
fig.update_layout(plot_bgcolor="black", paper_bgcolor="black")

# 年份下拉按钮
year_buttons = [
    {
        "label": str(y),
        "method": "update",
        "args": [
            {"visible": [True] * len(fig.data)},  # 控制 trace 可见性
            {"title": f"公转轨道图 - {y}"}
        ]
    }
    for y in range(2023, 2027)
]

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
        ],
        "direction": "left",
        "x": 0.25, "y": -0.05
    },
    {  # 年份下拉框
        "buttons": year_buttons,
        "direction": "down",
        "x": 0.05, "y": 1.15,
        "xanchor": "left", "yanchor": "top"
    }
    ],

    # 时间进度条
    sliders=[{
        "active": 0, "x": 0.25, "y": -0.20, "len": 0.6,   # 下移一点
        "currentvalue": {"prefix": "日期：", "visible": True},
        "steps": [{"args": [[f.name], {"mode": "immediate",
                                       "frame": {"duration": 0, "redraw": True},
                                       "transition": {"duration": 0}}],
                   "label": f.name[5:],  #  只显示 "MM-DD"，避免和下拉框年份冲突
                   "method": "animate"} for f in frames]
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