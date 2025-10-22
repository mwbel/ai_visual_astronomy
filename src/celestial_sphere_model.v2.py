import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from skyfield.api import load, Topos
from skyfield import almanac

# =============== Skyfield 初始化 ===============
# 加载星历表
ephemeris = load('de421.bsp')
ts = load.timescale()

# =============== 工具函数 ===============
def _tofloat(x):
    """把 numpy array 或标量转为 float"""
    a = np.atleast_1d(x)
    return float(a[0])

def _spherical_to_cartesian(azimuth_deg, altitude_deg, radius: float = 1.0):
    """
    地平坐标 (az, alt) → 笛卡尔 (x, y, z)
    约定：x轴=东，y轴=北，z轴=天顶
    """
    az = np.deg2rad(np.atleast_1d(azimuth_deg))
    alt = np.deg2rad(np.atleast_1d(altitude_deg))
    x = radius * np.cos(alt) * np.sin(az)
    y = radius * np.cos(alt) * np.cos(az)
    z = radius * np.sin(alt)
    return x, y, z

# =============== 场景（天球/地平面/天极/天顶等） ===============
def draw_scene(fig, latitude):
    # --- 天球线框（经纬网） ---
    n_sphere = 20
    u = np.linspace(0, 2*np.pi, n_sphere)
    v = np.linspace(0, np.pi, n_sphere)

    # 经线
    for i in range(n_sphere):
        x = np.cos(u[i]) * np.sin(v)
        y = np.sin(u[i]) * np.sin(v)
        z = np.cos(v)
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z, mode='lines',
            line=dict(color='rgba(200,200,200,0.2)', width=0.5),
            hoverinfo='none', showlegend=False
        ))
    # 纬线
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
    theta = np.linspace(0, 2*np.pi, 200)
    r_plane = 1.0
    x_c = r_plane * np.cos(theta)
    y_c = r_plane * np.sin(theta)
    z_c = np.zeros_like(theta)

    fig.add_trace(go.Scatter3d(
        x=x_c, y=y_c, z=z_c, mode='lines',
        line=dict(color='rgba(150,150,150,0.85)', width=9),
        hoverinfo='none', showlegend=False, name='地平圈'
    ))

    # 填充
    theta_fill = np.linspace(0, 2*np.pi, 80)
    r_fill = np.linspace(0, r_plane, 2)
    Xf = np.outer(r_fill, np.cos(theta_fill))
    Yf = np.outer(r_fill, np.sin(theta_fill))
    Zf = np.zeros_like(Xf)
    fig.add_trace(go.Surface(
        x=Xf, y=Yf, z=Zf, opacity=0.35, showscale=False,
        colorscale=[[0,'rgba(220,220,220,0.35)'], [1,'rgba(220,220,220,0.35)']],
        hoverinfo='none', name='地平面'
    ))

    # --- 八方位文字 ---
    dirs = [(0,'北'), (45,'东北'), (90,'东'), (135,'东南'),
            (180,'南'), (225,'西南'), (270,'西'), (315,'西北')]
    dx, dy, dz = [], [], []
    labels = []
    for az, name in dirs:
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
        line=dict(color='lightgray', width=9),
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
        textposition='top center', name='北天极', hoverinfo='none'
    ))
    fig.add_trace(go.Scatter3d(
        x=[_tofloat(sp_x)*ext], y=[_tofloat(sp_y)*ext], z=[_tofloat(sp_z)*ext],
        mode='markers+text', marker=dict(size=2, color='red'),
        text=['南天极'], textfont=dict(color='white', size=12),
        textposition='bottom center', name='南天极', hoverinfo='none'
    ))
    fig.add_trace(go.Scatter3d(
        x=[_tofloat(np_x)*ext, _tofloat(sp_x)*ext],
        y=[_tofloat(np_y)*ext, _tofloat(sp_y)*ext],
        z=[_tofloat(np_z)*ext, _tofloat(sp_z)*ext],
        mode='lines', line=dict(color='red', width=2),
        hoverinfo='none', showlegend=False, name='天极连线'
    ))

    # --- 天顶/天底 + 当地铅垂线 ---
    zenith = (0.0, 0.0, 1.2)
    nadir  = (0.0, 0.0, -1.2)
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


# =============== 绘制天体周日视运动轨迹（通用） ===============
def plot_body_daily_motion(fig, body, body_name, 
                           color_day, color_night,
                           observer, location_topos, ts,
                           local_midnight, next_midnight,
                           tz_name='Asia/Shanghai',
                           show_rise_set=True, show_realtime=True):
    """
    绘制天体的周日视运动（主轨迹=0..24h；夜间覆盖=NaN 断开；升/落点与实时点独立）
    """
    local_tz = ZoneInfo(tz_name)

    # 1) 固定网格 0..24h（25个点，闭合且不混入其它事件，避免错误连线）
    base_local_times = [local_midnight + timedelta(hours=h) for h in range(25)]
    base_utc = [dt.astimezone(ZoneInfo('UTC')) for dt in base_local_times]
    base_ts = ts.utc([dt.year for dt in base_utc],
                     [dt.month for dt in base_utc],
                     [dt.day for dt in base_utc],
                     [dt.hour + dt.minute/60 + dt.second/3600 for dt in base_utc])

    base_alt, base_az = [], []
    for t in base_ts:
        alt, az, _ = observer.at(t).observe(body).apparent().altaz()
        base_alt.append(alt.degrees)
        base_az.append(az.degrees)

    # 2) 主轨迹（白天主色；不包含升/落/实时点）
    x_all, y_all, z_all = _spherical_to_cartesian(np.array(base_az), np.array(base_alt))
    fig.add_trace(go.Scatter3d(
        x=x_all, y=y_all, z=z_all,
        mode="lines",
        line=dict(color=color_day, width=4),
        name=f"{body_name}轨迹",
        hoverinfo="none"
    ))

    # 3) 夜间覆盖（高度<0 的点，用 NaN 断开片段）
    alt_arr = np.array(base_alt)
    night_x = np.where(alt_arr < 0, x_all, np.nan)
    night_y = np.where(alt_arr < 0, y_all, np.nan)
    night_z = np.where(alt_arr < 0, z_all, np.nan)
    fig.add_trace(go.Scatter3d(
        x=night_x, y=night_y, z=night_z,
        mode="lines",
        line=dict(color=color_night, width=2, dash="dash"),
        name=f"{body_name}轨迹(夜间)",
        hoverinfo="none"
    ))
    
    # 新增：夜晚高亮轨迹
    highlight_color = "purple" if body_name == "太阳" else "green"
    fig.add_trace(go.Scatter3d(
        x=night_x, y=night_y, z=night_z,
        mode="lines",
        line=dict(color=highlight_color, width=2, dash="dot"),
        name=f"{body_name}夜晚高亮",
        hoverinfo="none"
    ))

    # 4) 整点标记（仅取0..23h）
    hourly_x, hourly_y, hourly_z, hourly_labels = [], [], [], []
    for h in range(24):
        cx, cy, cz = _spherical_to_cartesian(base_az[h], base_alt[h])
        hourly_x.append(_tofloat(cx))
        hourly_y.append(_tofloat(cy))
        hourly_z.append(_tofloat(cz))
        hourly_labels.append(f"{h}h")
    fig.add_trace(go.Scatter3d(
        x=hourly_x, y=hourly_y, z=hourly_z,
        mode="markers+text",
        marker=dict(size=4, color=color_day, symbol="circle"),
        text=hourly_labels,
        textfont=dict(color=color_day, size=10),
        textposition="top center",
        showlegend=False,
        hoverinfo="none"
    ))

    # 5) 升/落点（独立计算并只做文字标注，不插入主轨迹）
    if show_rise_set:
        t0_utc = ts.utc(local_midnight.astimezone(ZoneInfo("UTC")).year,
                        local_midnight.astimezone(ZoneInfo("UTC")).month,
                        local_midnight.astimezone(ZoneInfo("UTC")).day, 0)
        t1_utc = ts.utc(next_midnight.astimezone(ZoneInfo("UTC")).year,
                        next_midnight.astimezone(ZoneInfo("UTC")).month,
                        next_midnight.astimezone(ZoneInfo("UTC")).day, 0)
        if body_name == "太阳":
            f_event = almanac.sunrise_sunset(ephemeris, location_topos)
        else:
            f_event = almanac.risings_and_settings(ephemeris, body, location_topos)
        t_events, events = almanac.find_discrete(t0_utc, t1_utc, f_event)

        rs_x, rs_y, rs_z, rs_text = [], [], [], []
        for t_e, ev in zip(t_events, events):
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
                hoverinfo="none"
            ))

    # 6) 实时点（独立计算，不影响主轨迹连线）
    if show_realtime:
        now_local = datetime.now(local_tz)
        now_utc = now_local.astimezone(ZoneInfo("UTC"))
        t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day,
                       now_utc.hour + now_utc.minute/60 + now_utc.second/3600)
        alt_now, az_now, _ = observer.at(t_now).observe(body).apparent().altaz()
        rx, ry, rz = _spherical_to_cartesian(az_now.degrees, alt_now.degrees)
        fig.add_trace(go.Scatter3d(
            x=[_tofloat(rx)], y=[_tofloat(ry)], z=[_tofloat(rz)],
            mode="markers+text",
            marker=dict(size=8, color="red", symbol="circle-open"),
            text=[f"{body_name}(实时 {now_local.strftime('%H:%M')})"],
            textfont=dict(color="red", size=12),
            textposition="top center",
            name=f"{body_name}(实时)",
            hoverinfo="none"
        ))

# =============== 主函数 ===============
def plot_geocentric_celestial_sphere(latitude, longitude, date_time,
                                     tz_name: str = 'Asia/Shanghai',
                                     show_rise_set: bool = True):
    fig = go.Figure()

    if date_time.tzinfo is None:
        date_time = date_time.replace(tzinfo=ZoneInfo(tz_name))

    # 场景框架
    draw_scene(fig, latitude)

    # 观测者
    location = Topos(latitude_degrees=latitude, longitude_degrees=longitude)
    observer = ephemeris['earth'] + location

    # 当地当天 0:00 与次日 0:00
    local_tz = ZoneInfo(tz_name)
    local_date = date_time.astimezone(local_tz).date()
    local_midnight = datetime(local_date.year, local_date.month, local_date.day, 0, 0, tzinfo=local_tz)
    next_midnight = local_midnight + timedelta(days=1)

    # 太阳 & 月亮
    plot_body_daily_motion(fig, ephemeris['sun'],  "太阳", "orange",    "darkorange",
                           observer, location, ts, local_midnight, next_midnight,
                           tz_name=tz_name, show_rise_set=show_rise_set, show_realtime=True)
    plot_body_daily_motion(fig, ephemeris['moon'], "月亮", "lightblue", "gray",
                           observer, location, ts, local_midnight, next_midnight,
                           tz_name=tz_name, show_rise_set=show_rise_set, show_realtime=True)

    # 文字角标（纬度）
    latitude_text = f"北纬 {latitude:.1f}°" if latitude >= 0 else f"南纬 {-latitude:.1f}°"

    # 布局
    fig.update_layout(
        title=f"地心天球模型 - {date_time.astimezone(local_tz).strftime('%Y年%m月%d日 %H:%M')} ({tz_name}) 观测点: 纬度{latitude}°, 经度{longitude}°",
        annotations=[dict(
            text=latitude_text, xref="paper", yref="paper",
            x=0.05, y=0.95, showarrow=False,
            font=dict(color="white", size=12)
        )],
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''),
            yaxis=dict(showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''),
            zaxis=dict(showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''),
            aspectmode='cube',
            bgcolor='rgb(0,0,0)',
            camera=dict(eye=dict(x=np.cos(np.deg2rad(20))*np.cos(np.deg2rad(30)),
                                 y=np.cos(np.deg2rad(20))*np.sin(np.deg2rad(30)),
                                 z=np.sin(np.deg2rad(20))))
        ),
        paper_bgcolor='rgb(0,0,0)',
        font=dict(color='white', family="SimHei, Arial, sans-serif"),
        showlegend=True
    )

    fig.show()

# =============== 入口 ===============
if __name__ == "__main__":
    current_time = datetime.now()
    plot_geocentric_celestial_sphere(
        latitude=31.23, longitude=121.47,
        date_time=current_time, tz_name='Asia/Shanghai'
    )
