# -*- coding: utf-8 -*-
"""
celestial_sphere_slider.py

一个交互式 3D 天球模型，动态展示太阳与月亮相对地球的位置，并提供日期滑块。
"""

import numpy as np
import plotly.graph_objects as go
from skyfield.api import load, load_file, Topos, EarthSatellite
from skyfield.timelib import Time
from datetime import datetime, timedelta, date
import pytz
import argparse
import math

# --- 可配置参数区 ---
DEFAULT_LATITUDE = 31.23  # 默认观测纬度 (上海)
DEFAULT_LONGITUDE = 121.47 # 默认观测经度 (上海)
DEFAULT_TIMEZONE = 'Asia/Shanghai' # 默认时区
DEFAULT_YEAR = datetime.now().year # 默认年份为当前年份
DEFAULT_HOUR = datetime.now().hour # 默认观测小时为当前小时
DEFAULT_MINUTE = datetime.now().minute # 默认观测分钟为当前分钟
DEFAULT_RADIUS = 1.0 # 天球半径

PLANE_EXTEND  = 1.10  # 地平面外扩倍数（你在 draw_scene 里用的 1.1）
LABEL_EXTEND  = 1.05  # 方位文字外扩倍数（你在 draw_scene 里用的 1.05）
ZENITH_EXTEND = 1.50  # 天顶/天底外扩倍数（你想要 1.5）

# --- 工具函数区 ---

def _spherical_to_cartesian(az_deg, alt_deg, radius=DEFAULT_RADIUS):
    """
    将球面坐标 (方位角, 高度角) 转换为笛卡尔坐标 (x, y, z)。
    约定：az=0 北, 90 东 (与 Skyfield altaz 一致)。
    x = r * cos(alt) * sin(az) (东)
    y = r * cos(alt) * cos(az) (北)
    z = r * sin(alt) (天顶)
    """
    az_rad = np.radians(az_deg)
    alt_rad = np.radians(alt_deg)

    x = radius * np.cos(alt_rad) * np.sin(az_rad)
    y = radius * np.cos(alt_rad) * np.cos(az_rad)
    z = radius * np.sin(alt_rad)
    return x, y, z

def get_ephem_body(ephemeris, name):
    """
    从星历中获取天体对象。
    如果直接获取失败，尝试 "{name} barycenter"。
    """
    try:
        return ephemeris[name]
    except KeyError:
        try:
            return ephemeris[f"{name} barycenter"]
        except KeyError:
            raise ValueError(f"无法在星历中找到天体: {name} 或 {name} barycenter")

# --- 绘图场景区 ---

def draw_scene(fig, latitude, radius=DEFAULT_RADIUS, zenith_extend: float = 1.5):
    """
    绘制天球的静态场景元素：天球经纬网、地平圈、地平面、八方位文本、天极、天顶等。
    zenith_extend: 天顶/天底相对球半径的放大倍数（>1 表示超出球面）
    """
    # 天球经纬网 (细线，半透明)
    lons = np.linspace(-180, 180, 37)
    lats = np.linspace(-90, 90, 19)

    for lat in lats:
        x_lat = radius * np.cos(np.radians(lat)) * np.sin(np.radians(lons))
        y_lat = radius * np.cos(np.radians(lat)) * np.cos(np.radians(lons))
        z_lat = radius * np.sin(np.radians(lat)) * np.ones_like(lons)
        fig.add_trace(go.Scatter3d(x=x_lat, y=y_lat, z=z_lat, mode='lines',
                                   line=dict(color='rgba(100, 100, 100, 0.3)', width=1),
                                   hoverinfo='none', showlegend=False))

    for lon in lons:
        x_lon = radius * np.cos(np.radians(lats)) * np.sin(np.radians(lon))
        y_lon = radius * np.cos(np.radians(lats)) * np.cos(np.radians(lon))
        z_lon = radius * np.sin(np.radians(lats))
        fig.add_trace(go.Scatter3d(x=x_lon, y=y_lon, z=z_lon, mode='lines',
                                   line=dict(color='rgba(100, 100, 100, 0.3)', width=1),
                                   hoverinfo='none', showlegend=False))

    # 地平圈 (粗线)
    az_horizon = np.linspace(0, 360, 100)
    # 调用 _spherical_to_cartesian 获取 x 和 y 坐标，忽略返回的 z (因为它是标量)
    x_horizon, y_horizon, _ = _spherical_to_cartesian(az_horizon, 0, radius)
    # 显式创建 z_horizon 为一个与 x_horizon 长度相同的零数组，以满足 Plotly 的要求
    z_horizon = np.zeros_like(x_horizon)
    fig.add_trace(go.Scatter3d(x=x_horizon, y=y_horizon, z=z_horizon, mode='lines',
                               line=dict(color='white', width=3),
                               hoverinfo='none', showlegend=False, name='地平圈'))

    # 地平面 (浅灰填充，半透明)
    # 使用一个平面来表示地平面，可以是一个大的圆形或方形
    theta = np.linspace(0, 2 * np.pi, 100)
    r_plane = radius * 1.1 # 稍微大一点，覆盖地平圈
    x_plane = r_plane * np.cos(theta)
    y_plane = r_plane * np.sin(theta)
    z_plane = np.zeros_like(theta)
    fig.add_trace(go.Mesh3d(x=x_plane, y=y_plane, z=z_plane,
                            alphahull=0, # 自动计算凸包
                            color='rgba(100, 100, 100, 0.2)',
                            opacity=0.5,
                            hoverinfo='none', showlegend=False, name='地平面'))
    
    # 八方位文本
    cardinal_points = {
        '北': (0, 0), '东北': (45, 0), '东': (90, 0), '东南': (135, 0),
        '南': (180, 0), '西南': (225, 0), '西': (270, 0), '西北': (315, 0)
    }
    for label, (az, alt) in cardinal_points.items():
        # 稍微外扩避免遮挡
        text_x, text_y, text_z = _spherical_to_cartesian(az, alt, radius * 1.05)
        fig.add_trace(go.Scatter3d(x=[text_x], y=[text_y], z=[text_z], mode='text',
                                   text=[label], textfont=dict(color='white', size=10),
                                   hoverinfo='none', showlegend=False))

    # 天极与天极轴
    # 北天极 (alt=纬度)
    np_x, np_y, np_z = _spherical_to_cartesian(0, latitude, radius*zenith_extend)
    fig.add_trace(go.Scatter3d(x=[np_x], y=[np_y], z=[np_z], mode='markers',
                               marker=dict(color='cyan', size=2),
                               hoverinfo='text', text=['北天极'], showlegend=False))
    # 南天极 (alt=-纬度)
    sp_x, sp_y, sp_z = _spherical_to_cartesian(180, -latitude, radius*zenith_extend)
    fig.add_trace(go.Scatter3d(x=[sp_x], y=[sp_y], z=[sp_z], mode='markers',
                               marker=dict(color='cyan', size=2),
                               hoverinfo='text', text=['南天极'], showlegend=False))
    # 天极轴 (连接北天极和南天极，穿过球心)
    fig.add_trace(go.Scatter3d(x=[np_x, -np_x], y=[np_y, -np_y], z=[np_z, -np_z], mode='lines',
                               line=dict(color='cyan', width=2, dash='dot'),
                               hoverinfo='none', showlegend=False, name='天极轴'))
    
    # 天顶/天底与铅垂线（超出球面一些）
    # 天顶 (alt=90)
    zenith_x, zenith_y, zenith_z = _spherical_to_cartesian(0, 90, radius* zenith_extend)
    fig.add_trace(go.Scatter3d(x=[zenith_x], y=[zenith_y], z=[zenith_z], mode='markers',
                               marker=dict(color='red', size=3),
                               hoverinfo='text', text=['天顶'],  textposition='top center', showlegend=False))
    # 天底 (alt=-90)
    nadir_x, nadir_y, nadir_z = _spherical_to_cartesian(0, -90, radius* zenith_extend)
    fig.add_trace(go.Scatter3d(x=[nadir_x], y=[nadir_y], z=[nadir_z], mode='markers',
                               marker=dict(color='red', size=3),
                               hoverinfo='text', text=['天底'], textposition='bottom center', showlegend=False))
    # 铅垂线 (连接天顶和天底)
    fig.add_trace(go.Scatter3d(x=[zenith_x, nadir_x], y=[zenith_y, nadir_y], z=[zenith_z, nadir_z], mode='lines',
                               line=dict(color='red', width=2, dash='dash'),
                               hoverinfo='none', showlegend=False, name='铅垂线'))
# --- 天体位置计算区 ---
def add_sun_noon_annual_track(fig, ephemeris, observer, ts, all_dates, tz_name,
                              hour=12, minute=0, color='orange', radius=DEFAULT_RADIUS):
    """
    计算并添加“太阳周年视运动轨迹（每天固定本地时间 hour:minute）”到 fig，
    返回该轨迹在 fig.data 中的索引（便于 updatemenus 控制）。
    """
    xs, ys, zs = [], [], []

    sun = ephemeris['sun']
    for d in all_dates:
        x, y, z, _ = compute_body_point_for_date(
            sun, observer, ts, d, tz_name, hour, minute,
            radius=radius, body_key="sun", ephemeris=ephemeris
        )
        # 注意：compute_body_point_for_date 返回的是标量 float
        xs.append(float(x)); ys.append(float(y)); zs.append(float(z))

    sun_annual_trace = go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode='lines',
        line=dict(color=color, width=3),
        name=f'太阳周年轨迹（{hour:02d}:{minute:02d}）',
        hoverinfo='skip',
        visible=True,
        legendgroup='sun_annual'
    )
    fig.add_trace(sun_annual_trace)
    return len(fig.data) - 1

def compute_body_point_for_date(body, observer, ts, local_date, tz_name, hour, minute,
                                radius=DEFAULT_RADIUS, body_key="", ephemeris=None):
    """
    计算指定日期和固定本地时刻下天体的位置，并返回笛卡尔坐标和 hover 文本。
    - body_key: 'sun' 或 'moon'（用于判断是否计算月相）
    - ephemeris: 必传，用于月相计算
    """
    # 组成本地时间 → UTC
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime(local_date.year, local_date.month, local_date.day, hour, minute, 0))
    utc_dt = local_dt.astimezone(pytz.utc)
    t = ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second)

    # 观测得到的 alt/az
    app = observer.at(t).observe(body).apparent()
    alt, az, _ = app.altaz()

    # 转笛卡尔
    x, y, z = _spherical_to_cartesian(az.degrees, alt.degrees, radius)

    # 地平线信息
    horizon_status = "地平线上" if alt.degrees >= 0 else "地平线下"

    # （可选）月相计算：只在 body_key=='moon' 时进行；用传入的 ephemeris
    moon_phase_text = ""
    if ephemeris is not None and str(body_key).lower() == "moon":
        sun_obj = ephemeris['sun']
        earth_obj = ephemeris['earth']
        # 向量：从月亮指向地球、从月亮指向太阳
        v_me = (earth_obj - body).at(t).position.km
        v_ms = (sun_obj   - body).at(t).position.km
        # 夹角
        cosang = np.dot(v_me, v_ms) / (np.linalg.norm(v_me) * np.linalg.norm(v_ms))
        cosang = np.clip(cosang, -1.0, 1.0)
        phase_angle_deg = float(np.degrees(np.arccos(cosang)))
        # 简易月相标签
        if   0   <= phase_angle_deg <  45: moon_phase = "新月"
        elif 45  <= phase_angle_deg <  90: moon_phase = "娥眉月"
        elif 90  <= phase_angle_deg < 135: moon_phase = "上弦月"
        elif 135 <= phase_angle_deg < 180: moon_phase = "盈凸月"
        elif 180 <= phase_angle_deg < 225: moon_phase = "满月"
        elif 225 <= phase_angle_deg < 270: moon_phase = "亏凸月"
        elif 270 <= phase_angle_deg < 315: moon_phase = "下弦月"
        else:                               moon_phase = "残月"
        moon_phase_text = f"月相: {moon_phase} ({phase_angle_deg:.1f}°)"

    hover_text = (
        f"日期: {local_date.strftime('%Y-%m-%d')}<br>"
        f"高度角: {alt.degrees:.2f}°<br>"
        f"方位角: {az.degrees:.2f}° ({horizon_status})"
    )
    if moon_phase_text:
        hover_text += f"<br>{moon_phase_text}"

    return x, y, z, hover_text


# --- 主逻辑区 ---

def main():
    parser = argparse.ArgumentParser(description="交互式 3D 天球模型，展示太阳与月亮位置。")
    parser.add_argument("--lat", type=float, default=DEFAULT_LATITUDE,
                        help=f"观测纬度 (默认: {DEFAULT_LATITUDE})")
    parser.add_argument("--lon", type=float, default=DEFAULT_LONGITUDE,
                        help=f"观测经度 (默认: {DEFAULT_LONGITUDE})")
    parser.add_argument("--tz", type=str, default=DEFAULT_TIMEZONE,
                        help=f"时区 (例如: Asia/Shanghai, 默认: {DEFAULT_TIMEZONE})")
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR,
                        help=f"年份 (默认: {DEFAULT_YEAR})")
    parser.add_argument("--hour", type=int, default=DEFAULT_HOUR,
                        help=f"观测时刻-小时 (0-23, 默认: {DEFAULT_HOUR})")
    parser.add_argument("--minute", type=int, default=DEFAULT_MINUTE,
                        help=f"观测时刻-分钟 (0-59, 默认: {DEFAULT_MINUTE})")
    parser.add_argument("--bsp", type=str, default=None,
                    help="本地 de421.bsp 文件路径（可选，提供时将只从本地加载）")
    args = parser.parse_args()

    latitude = args.lat
    longitude = args.lon
    tz_name = args.tz
    year = args.year
    fixed_hour = args.hour
    fixed_minute = args.minute

    # 检查时区是否有效
    try:
        pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        print(f"错误: 未知的时区 '{tz_name}'. 请使用有效的 IANA 时区名称 (例如 'Asia/Shanghai').")
        return

    # 加载星历
    ts = load.timescale()
    if args.bsp:
        print(f"正在从本地加载星历: {args.bsp}")
        ephemeris = load_file(args.bsp)
    else:
        print("正在加载本地缓存的星历 de421.bsp （若首次运行会自动下载一次）...")
        ephemeris = load('de421.bsp')
    earth = ephemeris['earth']
    sun = get_ephem_body(ephemeris, 'sun')
    moon = get_ephem_body(ephemeris, 'moon')

    # 观测者位置
    observer = earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude)

    # 生成日期列表 (1月1日到12月31日)
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    delta = timedelta(days=1)
    all_dates = []
    current_date = start_date
    while current_date <= end_date:
        all_dates.append(current_date)
        current_date += delta

    # 初始化 Plotly 图形
    fig = go.Figure()

    # 绘制静态场景
    # draw_scene(fig, latitude)
    draw_scene(fig, latitude, radius=DEFAULT_RADIUS, zenith_extend=ZENITH_EXTEND)


    # === 在添加“每日点”之前，先叠加【太阳周年轨迹（正午12:00）】 ===
    sun_annual_idx = add_sun_noon_annual_track(
        fig, ephemeris, observer, ts, all_dates, tz_name,
        hour=fixed_hour, minute=fixed_minute,  # 你现在就是 12:00；也可固定写 hour=12, minute=0
        color='orange'
    )

    # 存储所有天体位置的 trace
    all_sun_traces = []
    all_moon_traces = []

    # 默认激活项为今天所在年份的相应日期，若不在范围则为 6 月 21 日
    today = date.today()
    initial_date_index = 0
    if start_date.year == today.year and start_date <= today <= end_date:
        initial_date_index = (today - start_date).days
    else:
        # 默认 6 月 21 日
        try:
            initial_date_index = (date(year, 6, 21) - start_date).days
        except ValueError: # 如果年份没有6月21日 (理论上不会发生)
            initial_date_index = len(all_dates) // 2 # 取中间日期

    # 为每个日期计算太阳和月亮的位置，并添加到图形中
    for i, current_date in enumerate(all_dates):
        # 太阳
        sun_x, sun_y, sun_z, sun_hover_text = compute_body_point_for_date(
            sun, observer, ts, current_date, tz_name, fixed_hour, fixed_minute,
            body_key="sun", ephemeris=ephemeris
        )
        sun_trace = go.Scatter3d(
            x=[sun_x], y=[sun_y], z=[sun_z],
            mode='markers',
            marker=dict(color='orange', size=8, symbol='circle'),
            name=f'太阳 ({fixed_hour:02d}:{fixed_minute:02d})',
            hoverinfo='text',
            hovertext=sun_hover_text,
            visible=(i == initial_date_index) # 初始只显示默认日期
        )
        fig.add_trace(sun_trace)
        all_sun_traces.append(sun_trace)

        # 月亮
        moon_x, moon_y, moon_z, moon_hover_text = compute_body_point_for_date(
            moon, observer, ts, current_date, tz_name, fixed_hour, fixed_minute,
            body_key="moon", ephemeris=ephemeris
        )
        moon_trace = go.Scatter3d(
            x=[moon_x], y=[moon_y], z=[moon_z],
            mode='markers',
            marker=dict(color='silver', size=6, symbol='circle'),
            name=f'月亮 ({fixed_hour:02d}:{fixed_minute:02d})',
            hoverinfo='text',
            hovertext=moon_hover_text,
            visible=(i == initial_date_index) # 初始只显示默认日期
        )
        fig.add_trace(moon_trace)
        all_moon_traces.append(moon_trace)
    
    # === 计算“静态 trace 数量”：场景 + 太阳周年轨迹 ===
    # 这里 all_sun_traces/all_moon_traces 是每个日期的单点（动态）
    num_static_traces = len(fig.data) - (len(all_sun_traces) + len(all_moon_traces))

     # === 创建滑块步骤 ===
    steps = []
    for i, current_date in enumerate(all_dates):
        # 前面 num_static_traces 个 trace（含太阳周年轨迹）始终可见
        visible_array = [True] * num_static_traces

        # 然后为每个日期追加 “太阳单点 + 月亮单点” 的可见性
        for j in range(len(all_sun_traces)):
            is_current = (j == i)
            visible_array.append(is_current)  # 太阳点
            visible_array.append(is_current)  # 月亮点

        step = dict(
            method="update",
            args=[{"visible": visible_array},
                  {"title.text": f"周年视运动 (日期可调)<br>"
                                 f"观测点: 纬度 {latitude:.1f}°, 经度 {longitude:.1f}° ({tz_name})<br>"
                                 f"观测时刻: 每天 {fixed_hour:02d}:{fixed_minute:02d} "
                                 f"(滑块切换日期: {current_date.strftime('%Y-%m-%d')})"}],
            label=current_date.strftime("%Y-%m-%d")
        )
        steps.append(step)

    sliders = [dict(
        active=initial_date_index,
        currentvalue={"prefix": "日期: "},
        pad={"t": 50},
        steps=steps
    )]

    # 可选增强：下拉菜单切换显示天体
    updatemenus = [
        dict(
            type="buttons",
            direction="right",
            x=0.0,
            y=1.1,
            showactive=True,
            buttons=list([
                dict(label="全部显示",
                     method="update",
                     args=[{"visible": [True] * num_static_traces + [True for _ in range(len(all_dates) * 2)]}, # 所有太阳和月亮 trace 都可见
                           {"showlegend": True}]),
                dict(label="仅显示太阳",
                     method="update",
                     args=[{"visible": [True] * num_static_traces + [True if j % 2 == 0 else False for j in range(len(all_dates) * 2)]}, # 仅太阳 trace 可见
                           {"showlegend": True}]),
                dict(label="仅显示月亮",
                     method="update",
                     args=[{"visible": [True] * num_static_traces + [False if j % 2 == 0 else True for j in range(len(all_dates) * 2)]}, # 仅月亮 trace 可见
                           {"showlegend": True}]),
            ]),
        )
    ] # 添加缺失的闭合方括号

    max_extend = max(PLANE_EXTEND, LABEL_EXTEND, ZENITH_EXTEND)
    L = DEFAULT_RADIUS * max_extend * 1.02  # 略留余量

    # 布局设置
    fig.update_layout(
        title_text=f"地心模型下的周年视运动 (日期可调)<br>"
                   f"观测点: 纬度 {latitude:.1f}°, 经度 {longitude:.1f}° ({tz_name})<br>"
                   f"观测时刻: 每天 {fixed_hour:02d}:{fixed_minute:02d} (滑块切换日期: {all_dates[initial_date_index].strftime('%Y-%m-%d')})",
        title_x=0.5,
        scene=dict(
            xaxis=dict(range=[-L, L], showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''),
            yaxis=dict(range=[-L, L], showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''),
            zaxis=dict(range=[-L, L], showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''),
            aspectmode='cube',   # 1:1:1 的显示比例
            # 你的相机设置可以保留
            # camera=dict(eye=dict(x=..., y=..., z=...)),
            bgcolor='rgb(0,0,0)'
        ),
        sliders=sliders,
        updatemenus=updatemenus, # 添加下拉菜单
        template='plotly_dark', # 黑色背景
        showlegend=True,
        legend=dict(x=0.0, y=0.9, bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)', font=dict(color='white'))
    )

    # 显示图形
    fig.show()

if __name__ == "__main__":
    main()
