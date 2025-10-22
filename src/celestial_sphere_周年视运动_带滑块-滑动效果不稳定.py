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

def plot_body_annual_track(fig, body, body_name,
                           color,
                           observer, ts,
                           year: int,
                           tz_name='Asia/Shanghai'):
    """
    绘制天体的周年视运动轨迹（每天一个点，连成细线）
    - 取每天固定时刻（例如 12:00 本地时）
    - 一年下来形成一条线
    """
    local_tz = ZoneInfo(tz_name)

    xs, ys, zs = [], [], []
    labels = []

    for month in range(1, 13):
        for day in range(1, 32):
            try:
                local_time = datetime(year, month, day, 12, 0, tzinfo=local_tz)  # 固定每天12:00
            except ValueError:
                continue  # 跳过无效日期

            # 转UTC
            utc_time = local_time.astimezone(ZoneInfo('UTC'))
            t = ts.utc(utc_time.year, utc_time.month, utc_time.day, utc_time.hour)

            # alt/az
            alt, az, _ = observer.at(t).observe(body).apparent().altaz()
            x, y, z = _spherical_to_cartesian(az.degrees, alt.degrees)

            xs.append(_tofloat(x))
            ys.append(_tofloat(y))
            zs.append(_tofloat(z))
            labels.append(local_time.strftime("%m-%d"))

    # 连成细线
    fig.add_trace(go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode="lines+markers",
        line=dict(color=color, width=3),
        marker=dict(size=2, color=color),
        text=labels,
        name=f"{body_name}周年轨迹"
    ))

# =============== 主函数 ===============
def plot_geocentric_celestial_sphere_with_slider(latitude, longitude, year,
                                                 tz_name: str = 'Asia/Shanghai',
                                                 bodies_cfg=None):
    """
    绘制天球 + 周年视运动（带滑块控制观测时刻）
    - latitude, longitude: 观测点坐标
    - year: 年份
    - tz_name: 时区
    - bodies_cfg: [(ephem_key, 中文名, color)] 列表
    """
    fig = go.Figure()

    # 场景框架
    draw_scene(fig, latitude)

    # 观测点
    location = Topos(latitude_degrees=latitude, longitude_degrees=longitude)
    observer = ephemeris['earth'] + location

    # 默认只画太阳和月亮
    if bodies_cfg is None:
        bodies_cfg = [
            ("sun",  "太阳", "orange"),
            #("moon", "月亮", "silver"),
        ]

    steps = []
    n_traces_per_body = 24   # 每个天体 24 条曲线（每小时一条）

    for b_idx, (key, cname, color) in enumerate(bodies_cfg):
        body_obj = get_ephem_body(key)

        for h in range(24):
            xs, ys, zs = [], [], []
            labels = []

            # 每天固定 h:00
            for month in range(1, 13):
                for day in range(1, 32):
                    try:
                        local_time = datetime(year, month, day, h, 0, tzinfo=ZoneInfo(tz_name))
                    except ValueError:
                        continue
                    utc_time = local_time.astimezone(ZoneInfo("UTC"))
                    t = ts.utc(utc_time.year, utc_time.month, utc_time.day,
                               utc_time.hour + utc_time.minute/60.0)
                    alt, az, _ = observer.at(t).observe(body_obj).apparent().altaz()
                    x, y, z = _spherical_to_cartesian(az.degrees, alt.degrees)

                    xs.append(_tofloat(x))
                    ys.append(_tofloat(y))
                    zs.append(_tofloat(z))
                    labels.append(local_time.strftime("%m-%d"))

            # 每小时一条轨迹（初始仅 12:00 可见）
            fig.add_trace(go.Scatter3d(
                x=xs, y=ys, z=zs,
                mode="lines+markers",
                line=dict(color=color, width=3),
                marker=dict(size=2, color=color),
                text=labels,
                name=f"{cname} {h:02d}:00",
                visible=(h == 12)  # 默认显示 12:00
            ))

        # slider steps（控制可见性）
        for h in range(24):
            step = dict(
                method="update",
                args=[{"visible": [False] * len(fig.data)}],  # 全部隐藏
                label=f"{h:02d}:00"
            )
            # 当前天体的第 h 条轨迹设为 True
            for b2 in range(len(bodies_cfg)):
                step["args"][0]["visible"][b2 * n_traces_per_body + h] = True
            steps.append(step)

    # slider 控件
    sliders = [dict(
        active=12,
        currentvalue={"prefix": "观测时刻: "},
        pad={"t": 30},
        steps=steps
    )]

    # 布局
    fig.update_layout(
        title=(
            f"周年视运动轨迹<br>"
            f"观测点: 纬度 {latitude:.1f}°, 经度 {longitude:.1f}° ({tz_name})<br>"
            f"观测时刻: 每天固定本地时 (滑块 0–23h 可切换)"
        ),
        sliders=sliders,
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, showgrid=False, zeroline=False),
            yaxis=dict(showbackground=False, showticklabels=False, showgrid=False, zeroline=False),
            zaxis=dict(showbackground=False, showticklabels=False, showgrid=False, zeroline=False),
            aspectmode='cube',
            bgcolor='rgb(0,0,0)'
        ),
        paper_bgcolor='rgb(0,0,0)',
        font=dict(color='white'),
        showlegend=True
    )

    fig.show()

    

# =============== 入口 ===============
if __name__ == "__main__":
    plot_geocentric_celestial_sphere_with_slider(
        latitude=31.23, longitude=121.47,
        year=2025,
        tz_name='Asia/Shanghai'
    )
