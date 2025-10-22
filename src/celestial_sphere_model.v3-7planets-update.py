# 目标：以地球为球心，构建交互式 3D 天球模型，并绘制太阳/月亮的周日视运动轨迹与实时位置
# 依赖：numpy, plotly, skyfield（会自动下载de421.bsp星历文件）
# 安装：pip install numpy plotly skyfield tzdata

import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from skyfield.api import load, Topos
from skyfield import almanac

# =============== Skyfield 初始化 ===============
# 加载星历表（de421），包含太阳、月亮等天体的历元数据；第一次会下载到本地缓存
ephemeris = load('de421.bsp')
# 构造时间刻度对象（将UTC年月日时分秒转为skyfield的Time）
ts = load.timescale()

# =============== 工具函数 ===============
def _tofloat(x):
    """把 numpy array 或标量转为 float（plotly期望原生标量；便于从数组中取出单个值）"""
    a = np.atleast_1d(x) # 如果是标量也包装成一维数组
    return float(a[0])   # 取第一个元素并转 float

def _spherical_to_cartesian(azimuth_deg, altitude_deg, radius: float = 1.0):
    """ 
    地平坐标 (az, alt) → 笛卡尔 (x, y, z)
    约定：x轴=东，y轴=北，z轴=天顶 （符合常见地平坐标右手系可视化）
    """
    az = np.deg2rad(np.atleast_1d(azimuth_deg)) # 方位角（度→弧度），0°=北，90°=东（skyfield返回亦如此）
    alt = np.deg2rad(np.atleast_1d(altitude_deg)) # 高度角（度→弧度），0°=地平，90°=天顶
    # 球坐标→直角坐标：注意这里用的是地平坐标的常见投影
    x = radius * np.cos(alt) * np.sin(az)  # 东向分量
    y = radius * np.cos(alt) * np.cos(az)  # 北向分量
    z = radius * np.sin(alt)               # 向上（天顶）分量
    return x, y, z

# =============== 场景（天球/地平面/天极/天顶等） ===============
def draw_scene(fig, latitude):
    """绘制静态场景：天球网格、地平圈与地平面、八方位标签、东西线、南北天极与天极轴、天顶/天底与铅垂线"""
    # --- 天球线框（经纬网） ---
    n_sphere = 20
    u = np.linspace(0, 2*np.pi, n_sphere)  # 经线参数
    v = np.linspace(0, np.pi, n_sphere)    # 纬线参数（0=北天极，pi=南天极）

    # 经线：固定u[i]，扫v
    for i in range(n_sphere):
        x = np.cos(u[i]) * np.sin(v)
        y = np.sin(u[i]) * np.sin(v)
        z = np.cos(v)
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z, mode='lines',
            line=dict(color='rgba(200,200,200,0.2)', width=0.5),
            hoverinfo='none', showlegend=False
        ))
    # 纬线：固定v[i]，扫u
    for i in range(n_sphere):
        x = np.cos(u) * np.sin(v[i])
        y = np.sin(u) * np.sin(v[i])
        z = np.full_like(u, np.cos(v[i]))
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z, mode='lines',
            line=dict(color='rgba(200,200,200,0.2)', width=0.5),
            hoverinfo='none', showlegend=False
        ))

    # --- 地平圈 + 地平面填充（低透明） ---
    theta = np.linspace(0, 2*np.pi, 200) # 地平圈参数角
    r_plane = 1.0                        # 地平圈半径（与天球半径一致以便投影）
    x_c = r_plane * np.cos(theta)
    y_c = r_plane * np.sin(theta)
    z_c = np.zeros_like(theta)           # 地平面 z=0

    # 地平圈粗线表示
    fig.add_trace(go.Scatter3d(
        x=x_c, y=y_c, z=z_c, mode='lines',
        line=dict(color='rgba(150,150,150,0.85)', width=9),
        hoverinfo='none', showlegend=False, name='地平圈'
    ))

    # 地平面填充
    theta_fill = np.linspace(0, 2*np.pi, 80)
    r_fill = np.linspace(0, r_plane, 2)
    Xf = np.outer(r_fill, np.cos(theta_fill))
    Yf = np.outer(r_fill, np.sin(theta_fill))
    Zf = np.zeros_like(Xf)
    fig.add_trace(go.Surface(
        x=Xf, y=Yf, z=Zf, opacity=0.8, showscale=False,
        colorscale=[[0,'rgba(220,220,220,0.35)'], [1,'rgba(220,220,220,0.35)']],
        hoverinfo='none', name='地平面'
    ))

    # --- 八方位文字 ---
    dirs = [(0,'北'), (45,'东北'), (90,'东'), (135,'东南'),
            (180,'南'), (225,'西南'), (270,'西'), (315,'西北')]
    dx, dy, dz = [], [], []
    labels = []
    for az, name in dirs:
        # 在地平线上（alt=0）以半径>1稍微外扩，避免被地平圈遮挡
        x, y, z = _spherical_to_cartesian(az, 0, radius=1.08)
        dx.append(_tofloat(x)); dy.append(_tofloat(y)); dz.append(_tofloat(z))
        labels.append(name)
    fig.add_trace(go.Scatter3d(
        x=dx, y=dy, z=dz, mode='text',
        text=labels, textfont=dict(color='white', size=12),
        textposition='middle center', showlegend=False, name='方向'
    ))

    # --- 东西连线（x:东-西） ---
    e_x, e_y, e_z = _spherical_to_cartesian(90, 0, 1.0)
    w_x, w_y, w_z = _spherical_to_cartesian(270, 0, 1.0)
    fig.add_trace(go.Scatter3d(
        x=[_tofloat(e_x), _tofloat(w_x)],
        y=[_tofloat(e_y), _tofloat(w_y)],
        z=[_tofloat(e_z), _tofloat(w_z)],
        mode='lines',
        line=dict(color='rgba(150,150,150,0.85)', width=9),
        hoverinfo='none', showlegend=False, name='东西连线'
    ))

    # --- 南北天极（方位0/180，高度±纬度） + 天极连线 ---
    np_x, np_y, np_z = _spherical_to_cartesian(0,  latitude)
    sp_x, sp_y, sp_z = _spherical_to_cartesian(180, -latitude)
    ext = 1.2
    fig.add_trace(go.Scatter3d(
        x=[_tofloat(np_x)*ext], y=[_tofloat(np_y)*ext], z=[_tofloat(np_z)*ext],
        mode='markers+text', marker=dict(size=2, color='red'),
        text=['北天极'], textfont=dict(color='white', size=12),
        textposition='top center', name='北天极', hoverinfo='none',showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[_tofloat(sp_x)*ext], y=[_tofloat(sp_y)*ext], z=[_tofloat(sp_z)*ext],
        mode='markers+text', marker=dict(size=2, color='red'),
        text=['南天极'], textfont=dict(color='white', size=12),
        textposition='bottom center', name='南天极', hoverinfo='none',showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[_tofloat(np_x)*ext, _tofloat(sp_x)*ext],
        y=[_tofloat(np_y)*ext, _tofloat(sp_y)*ext],
        z=[_tofloat(np_z)*ext, _tofloat(sp_z)*ext],
        mode='lines', line=dict(color='red', width=2),
        hoverinfo='none', showlegend=False, name='天极连线'
    ))

    # --- 天顶/天底 + 当地铅垂线 （竖直方向）---
    zenith = (0.0, 0.0, 1.2)   # 天顶（稍微超出球半径）
    nadir  = (0.0, 0.0, -1.2)  # 天底
    fig.add_trace(go.Scatter3d(
        x=[zenith[0]], y=[zenith[1]], z=[zenith[2]],
        mode='markers+text', marker=dict(size=2, color='red'),
        text=['天顶'], textfont=dict(color='red', size=12),
        textposition='top center', hoverinfo='none', showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[nadir[0]], y=[nadir[1]], z=[nadir[2]],
        mode='markers+text', marker=dict(size=2, color='red'),
        text=['天底'], textfont=dict(color='red', size=12),
        textposition='bottom center', hoverinfo='none', showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[zenith[0], nadir[0]], y=[zenith[1], nadir[1]], z=[zenith[2], nadir[2]],
        mode='lines', line=dict(color='red', width=2, dash='dash'),
        hoverinfo='none', showlegend=False, name='当地铅垂线'
    ))

#-----行星对象获取助手--------
def get_ephem_body(name: str):
    """
    从de421里稳健地拿到天体对象。
    例如：'jupiter' 找不到时回退到 'jupiter barycenter'。
    """
    candidates = [
        name, name.lower(),
        f"{name} barycenter", f"{name.lower()} barycenter"
    ]
    for key in candidates:
        try:
            return ephemeris[key]
        except KeyError:
            continue
    raise KeyError(f"在星历中找不到天体：{name}（已尝试：{candidates}）")


# =============== 绘制天体周日视运动轨迹（通用） ===============
def plot_body_daily_motion(fig, body, body_name, 
                           color_day, color_night,
                           observer, location_topos, ts,
                           local_midnight, next_midnight,
                           tz_name='Asia/Shanghai',
                           show_rise_set=True, show_realtime=True,
                           highlight_color=None):
    """
    绘制天体的周日视运动
    - 主轨迹：当天 0..24h（共25点），独立于升/落/实时点，避免错误“跨天连线”
    - 夜间覆盖：将 alt<0 的段以虚线/淡色单独叠加（通过 NaN 断开实现）
    - 升/落点与实时点：单独计算与标注，不参与主轨迹连线
    """
    local_tz = ZoneInfo(tz_name)

    # 1) 固定网格 0..24h（25个点，包含第二天的 0:00，用于“24h→0h”闭合）
    base_local_times = [local_midnight + timedelta(hours=h) for h in range(25)]
    # 转UTC（Skyfield内部用UTC时间）
    base_utc = [dt.astimezone(ZoneInfo('UTC')) for dt in base_local_times]
    # 构造 Skyfield 时间对象（小时=时+分/60+秒/3600）
    base_ts = ts.utc([dt.year for dt in base_utc],
                     [dt.month for dt in base_utc],
                     [dt.day for dt in base_utc],
                     [dt.hour + dt.minute/60 + dt.second/3600 for dt in base_utc])
    
    # 批量计算 alt/az（每个时刻一次）
    base_alt, base_az = [], []
    for t in base_ts:
        alt, az, _ = observer.at(t).observe(body).apparent().altaz()
        base_alt.append(alt.degrees)
        base_az.append(az.degrees)

    # 2) 主轨迹（白天主色；不包含升/落/实时点;轨迹本身不区分昼夜，昼夜区分在下一步叠加））
    x_all, y_all, z_all = _spherical_to_cartesian(np.array(base_az), np.array(base_alt))
    fig.add_trace(go.Scatter3d(
        x=x_all, y=y_all, z=z_all,
        mode="lines",
        line=dict(color=color_day, width=4),
        name=f"{body_name}轨迹",
        legendgroup=body_name,   
        hoverinfo="none"
    ))

    # 3) 夜间覆盖（高度<0 的点：仅在这些点上绘制“夜间样式”；其余点设为NaN切断）
    alt_arr = np.array(base_alt)
    night_x = np.where(alt_arr < 0, x_all, np.nan)
    night_y = np.where(alt_arr < 0, y_all, np.nan)
    night_z = np.where(alt_arr < 0, z_all, np.nan)
    fig.add_trace(go.Scatter3d(
        x=night_x, y=night_y, z=night_z,
        mode="lines",
        line=dict(color=color_night, width=2, dash="dash"),
        name=f"{body_name}轨迹(夜间)",
        hoverinfo="none",
        showlegend=False,
        legendgroup=body_name
    ))
    
    # 新增：夜晚高亮轨迹（点划线），默认用日间主色；可外部自定义
    if highlight_color is None:
        highlight_color = color_day
    fig.add_trace(go.Scatter3d(
        x=night_x, y=night_y, z=night_z,
        mode="lines",
        line=dict(color=highlight_color, width=2, dash="dot"),
        name=f"{body_name}夜晚高亮",
        hoverinfo="none",
        showlegend=False,
        legendgroup=body_name
    ))

    # 4) 整点标记（0..24 共25个点；24:00是次日0:00，标签自然显示为0h）
    hourly_x, hourly_y, hourly_z, hourly_labels = [], [], [], []
    for i, dt_local in enumerate(base_local_times):  # 0..24 共25个点
        cx, cy, cz = _spherical_to_cartesian(base_az[i], base_alt[i])
        hourly_x.append(_tofloat(cx))
        hourly_y.append(_tofloat(cy))
        hourly_z.append(_tofloat(cz))
        # 关键：用 datetime 的小时，而不是用循环索引 i
        hourly_labels.append(f"{dt_local.hour}h")   # 关键点：直接取datetime.hour，24:00→0h
    
    fig.add_trace(go.Scatter3d(
        x=hourly_x, y=hourly_y, z=hourly_z,
        mode="markers+text",
        marker=dict(size=2, color=color_day, symbol="circle"),
        text=hourly_labels,
        textfont=dict(color=color_day, size=10),
        textposition="top center",
        showlegend=False,
        legendgroup=body_name, 
        hoverinfo="none"
    ))

    # 5) 升/落点（独立计算并只做文字标注，不插入主轨迹，避免“跨越地平线”的错误连线）
    if show_rise_set:
        # 将“当天本地午夜”与“次日本地午夜”转换为UTC，作为搜索窗口
        t0_utc = ts.utc(local_midnight.astimezone(ZoneInfo("UTC")).year,
                        local_midnight.astimezone(ZoneInfo("UTC")).month,
                        local_midnight.astimezone(ZoneInfo("UTC")).day, 0)
        t1_utc = ts.utc(next_midnight.astimezone(ZoneInfo("UTC")).year,
                        next_midnight.astimezone(ZoneInfo("UTC")).month,
                        next_midnight.astimezone(ZoneInfo("UTC")).day, 0)
        # 太阳用专用的 sunrise_sunset；月亮/其他用通用的 risings_and_settings
        if body_name == "太阳":
            f_event = almanac.sunrise_sunset(ephemeris, location_topos)
        else:
            f_event = almanac.risings_and_settings(ephemeris, body, location_topos)
        # 在[t0, t1]内寻找离散事件（升=1 / 落=0）
        t_events, events = almanac.find_discrete(t0_utc, t1_utc, f_event)

        rs_x, rs_y, rs_z, rs_text = [], [], [], []
        for t_e, ev in zip(t_events, events):
            # 事件瞬时的方位角（用于把标注放在地平线上更直观）
            alt_e, az_e, _ = observer.at(t_e).observe(body).apparent().altaz()
            ex, ey, ez = _spherical_to_cartesian(az_e.degrees, 0.0)
            rs_x.append(_tofloat(ex)); rs_y.append(_tofloat(ey)); rs_z.append(_tofloat(ez))
            label = "升起" if int(ev) == 1 else "落下"
            local_e = t_e.utc_datetime().astimezone(local_tz)
            rs_text.append(f"{body_name}{label} {local_e.strftime('%H:%M')}")
        if rs_x:
            fig.add_trace(go.Scatter3d(
                x=rs_x, y=rs_y, z=rs_z,
                mode="text",
                text=rs_text,
                textfont=dict(color=color_day, size=10),
                textposition="top center",
                showlegend=False,
                legendgroup=body_name,  
                hoverinfo="none"
            ))

    # 6) 实时点（独立计算，当前本地时间 → UTC → alt/az，再单独标注）
    if show_realtime:
        now_local = datetime.now(local_tz)               # 当前本地时刻
        now_utc = now_local.astimezone(ZoneInfo("UTC"))  # 转UTC
        t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day,
                       now_utc.hour + now_utc.minute/60 + now_utc.second/3600)
        alt_now, az_now, _ = observer.at(t_now).observe(body).apparent().altaz()
        rx, ry, rz = _spherical_to_cartesian(az_now.degrees, alt_now.degrees)
        fig.add_trace(go.Scatter3d(
            x=[_tofloat(rx)], y=[_tofloat(ry)], z=[_tofloat(rz)],
            mode="markers+text",
            marker=dict(size=6, color=color_day, symbol="circle-open"),
            text=[f"{body_name}(实时 {now_local.strftime('%H:%M')})"],
            textfont=dict(color="red", size=9),
            textposition="top center",
            name=f"{body_name}(实时)",
            hoverinfo="none",
            showlegend=False,
            legendgroup=body_name
        ))

# =============== 主函数 ===============
def plot_geocentric_celestial_sphere(latitude, longitude, date_time,
                                     tz_name: str = 'Asia/Shanghai',
                                     show_rise_set: bool = True):
    """封装整体流程：搭场景→设观测者→计算时间窗口→绘太阳/月亮→美化布局"""
    fig = go.Figure()

     # 若输入的 datetime 无时区信息（naive），补上指定时区
    if date_time.tzinfo is None:
        date_time = date_time.replace(tzinfo=ZoneInfo(tz_name))

    # 场景框架（天球网格、地平面、方位、极点、铅垂线等）
    draw_scene(fig, latitude)

    # 观测者（地球 + 观测点 Topos）
    # 注：新版 skyfield 可用 wgs84.latlon 代替 Topos，这里保持 Topos 以兼容原代码
    location = Topos(latitude_degrees=latitude, longitude_degrees=longitude)
    observer = ephemeris['earth'] + location

    # 当地当天 0:00 与次日 0:00（定义“当天”的时间窗口）
    local_tz = ZoneInfo(tz_name)
    local_date = date_time.astimezone(local_tz).date()
    local_midnight = datetime(local_date.year, local_date.month, local_date.day, 0, 0, tzinfo=local_tz)
    next_midnight = local_midnight + timedelta(days=1)

    # === 统一配置各天体：键、显示名、日间色、夜间色、高亮色 ===
    bodies_cfg = [
        ("sun",     "太阳",  "orange",   "darkorange", "orange"),
        ("moon",    "月亮",  "silver",   "gray",       "silver"),
        ("mercury", "水星",  "#3A7BD5",  "#2C5AA0",    "#3A7BD5"),  # 蓝色
        ("venus",   "金星",  "#FFD700",  "#B8860B",    "#FFD700"),  # 黄色
        ("mars",    "火星",  "#FF4500",  "#8B0000",    "#FF4500"),  # 红色
        ("jupiter", "木星",  "#3CB371",  "#2E8B57",    "#3CB371"),  # 绿色
        ("saturn",  "土星",  "#C2B280",  "#8B7D6B",    "#C2B280"),  # 土黄
    ]

    # 逐个天体绘制（自动处理极昼/极夜提示、升落时刻与实时点）
    for key, cname, day_col, night_col, hl_col in bodies_cfg:
        body_obj = get_ephem_body(key)
        plot_body_daily_motion(
            fig, body_obj, cname,
            day_col, night_col,
            observer, location, ts,
            local_midnight, next_midnight,
            tz_name=tz_name, show_rise_set=show_rise_set, show_realtime=True,
            highlight_color=hl_col
        )

    # 角标：显示纬度的文字（直观提示观测地的“天空倾角”）
    latitude_text = f"北纬 {latitude:.1f}°" if latitude >= 0 else f"南纬 {-latitude:.1f}°"

    # 计算统一外延 L（包含地平面1.0、文字1.08、天顶/天底1.2、以及天极ext=1.2 的情况）
    L = 1.2 * 1.02  # 2% 余量，避免裁切

    # 布局与主题（暗底、隐藏坐标轴、固定相机视角等）
    fig.update_layout(
        title=f"地心天球模型 - {date_time.astimezone(local_tz).strftime('%Y年%m月%d日 %H:%M')} ({tz_name}) 观测点: 纬度{latitude}°, 经度{longitude}°",
        annotations=[dict(
            text=latitude_text, xref="paper", yref="paper",
            x=0.05, y=0.95, showarrow=False,
            font=dict(color="white", size=12)
        )],
        scene=dict(
            xaxis=dict(range=[-L, L], showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''),
            yaxis=dict(range=[-L, L], showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''),
            zaxis=dict(range=[-L, L], showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''),
            aspectmode='cube',
            bgcolor='rgb(0,0,0)',
            camera=dict(eye=dict(
                x=np.cos(np.deg2rad(20))*np.cos(np.deg2rad(30)),
                y=np.cos(np.deg2rad(20))*np.sin(np.deg2rad(30)),
                z=np.sin(np.deg2rad(20))
            ))
        ),
        paper_bgcolor='rgb(0,0,0)',
        font=dict(color='white', family="SimHei, Arial, sans-serif"),
        showlegend=True
    )

    fig.show()   # 打开交互视图（Jupyter/Notebook内联，或浏览器窗口）

# =============== 入口 ===============
if __name__ == "__main__":
    # 使用当前时间作为“当天”的参照（用于标题/实时点）
    current_time = datetime.now()
    # 指定时间（例如 2025年3月21日 18:00）
    custom_time = datetime(2025, 3, 21, 18, 0, 0)
    
    plot_geocentric_celestial_sphere(
        latitude=31.23, longitude=121.47,
        date_time=current_time, tz_name='Asia/Shanghai'
        # date_time=custom_time, tz_name='Asia/Shanghai'
        # latitude=51.5, longitude=-0.1,
        # date_time=custom_time, tz_name='Europe/London'
    )