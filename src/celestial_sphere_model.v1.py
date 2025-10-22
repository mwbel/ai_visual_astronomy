import numpy as np # 导入 NumPy 库，用于数值计算
import plotly.graph_objects as go # 导入 Plotly 的 graph_objects 模块，用于创建交互式图表
from datetime import datetime, timedelta # 导入 datetime 和 timedelta 模块，用于处理日期和时间
from zoneinfo import ZoneInfo # 导入 ZoneInfo，用于处理时区
from skyfield.api import load, Topos, EarthSatellite, utc # 导入 Skyfield 库，用于天文计算，包括加载星历表、定义观测点、处理卫星和UTC时区
from skyfield.framelib import itrs # 导入 Skyfield 的 framelib 模块中的 itrs，用于地球固定坐标系
from skyfield import almanac # 导入 almanac，用于计算日出日落
from skyfield.api import load
import math # 导入 math 库，用于数学函数

ephemeris = load('de421.bsp')

ts = load.timescale() # 初始化 Skyfield 的时间尺度对象，用于创建时间点

# Helper functions for degree-based trigonometric operations (from daily_motion_plot.py)
def sind(angle_deg):
    return math.sin(math.radians(angle_deg))

def cosd(angle_deg):
    return math.cos(math.radians(angle_deg))

def tand(angle_deg):
    return math.tan(math.radians(angle_deg))

def asind(value):
    # Ensure value is within [-1, 1] for asin
    if value > 1:
        value = 1
    elif value < -1:
        value = -1
    return math.degrees(math.asin(value))

def atan2d(y, x):
    return math.degrees(math.atan2(y, x))

def date_to_jd(year, month, day, hour=12, minute=0, second=0):
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    JD = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5
    JD += (hour - 12) / 24 + minute / 1440 + second / 86400
    return JD

def _spherical_to_cartesian(azimuth_deg, altitude_deg, radius: float = 1): # 明确 radius 为浮点数类型
    """
    将地平坐标（方位角、高度角）转换为 3D 笛卡尔坐标。
    方位角 (azimuth): 从正北顺时针方向测量，0度为正北，90度为正东。
    高度角 (altitude): 从地平线向上测量，0度为地平线，90度为天顶。
    """
    # 确保输入是 NumPy 数组，即使是单个值
    azimuth_deg = np.atleast_1d(azimuth_deg) # 将方位角转换为至少一维数组
    altitude_deg = np.atleast_1d(altitude_deg) # 将高度角转换为至少一维数组

    azimuth_rad = np.deg2rad(azimuth_deg) # 将方位角从度转换为弧度
    altitude_rad = np.deg2rad(altitude_deg) # 将高度角从度转换为弧度

    # 笛卡尔坐标系约定：
    # x轴：指向正东
    # y轴：指向正北
    # z轴：指向天顶
    x = radius * np.cos(altitude_rad) * np.sin(azimuth_rad) # 计算 x 坐标
    y = radius * np.cos(altitude_rad) * np.cos(azimuth_rad) # 计算 y 坐标
    z = radius * np.sin(altitude_rad) # 计算 z 坐标
    return x, y, z # 返回笛卡尔坐标

def plot_geocentric_celestial_sphere(latitude, longitude, date_time, tz_name: str = 'Asia/Shanghai', show_rise_set: bool = True):
    """
    绘制交互式 3D 地心天球模型（地平坐标系），显示太阳和月亮的周日视运动轨迹。
    参数:
        latitude (float): 观测点的纬度。
        longitude (float): 观测点的经度。
        date_time (datetime): 观测的日期和时间。
        tz_name (str): 时区名称，默认为 'Asia/Shanghai'。
        show_rise_set (bool): 是否显示日出日落标记，默认为 True。
    """
    fig = go.Figure() # 创建一个 Plotly 图形对象

    # 如果 date_time 是 naive，将其视为 tz_name 时区的本地时间
    if date_time.tzinfo is None:
        date_time = date_time.replace(tzinfo=ZoneInfo(tz_name))

    # 1. 天球建模：透明球体 (修改为线框效果)
    n_sphere = 20 # 增加点数以获得更平滑的线框
    u_sphere = np.linspace(0, 2 * np.pi, n_sphere)
    v_sphere = np.linspace(0, np.pi, n_sphere)

    # 绘制经线
    for i in range(n_sphere):
        x_meridian = np.cos(u_sphere[i]) * np.sin(v_sphere)
        y_meridian = np.sin(u_sphere[i]) * np.sin(v_sphere)
        z_meridian = np.cos(v_sphere)
        fig.add_trace(go.Scatter3d(
            x=x_meridian, y=y_meridian, z=z_meridian,
            mode='lines',
            line=dict(color='rgba(200,200,200,0.2)', width=0.5),
            showlegend=False,
            hoverinfo='none'
        ))
    # 绘制纬线
    for i in range(n_sphere):
        x_parallel = np.cos(u_sphere) * np.sin(v_sphere[i])
        y_parallel = np.sin(u_sphere) * np.sin(v_sphere[i])
        z_parallel = np.full_like(u_sphere, np.cos(v_sphere[i]))
        fig.add_trace(go.Scatter3d(
            x=x_parallel, y=y_parallel, z=z_parallel,
            mode='lines',
            line=dict(color='rgba(200,200,200,0.2)', width=0.5),
            showlegend=False,
            hoverinfo='none'
        ))

    # 绘制地平面 (实心圆)
    theta = np.linspace(0, 2 * np.pi, 100) # 生成地平面的角度，从 0 到 2π
    r_plane = 1 # 地平面半径
    x_plane_circle = r_plane * np.cos(theta)
    y_plane_circle = r_plane * np.sin(theta)
    z_plane_circle = np.zeros_like(theta)

    fig.add_trace(go.Scatter3d(
        x=x_plane_circle, y=y_plane_circle, z=z_plane_circle,
        mode='lines',
        line=dict(color='rgba(150,150,150,0.8)', width=9),
        showlegend=False,
        hoverinfo='none',
        name='地平圈'
    ))
    # 填充地平面 (圆形，浅灰色，透明度 0.4)
    num_points_fill = 50
    theta_fill = np.linspace(0, 2 * np.pi, num_points_fill)
    r_grid_fill = np.linspace(0, r_plane, 2) # 从中心到边缘，2个点足够形成表面

    X_fill = np.outer(r_grid_fill, np.cos(theta_fill))
    Y_fill = np.outer(r_grid_fill, np.sin(theta_fill))
    Z_fill = np.zeros_like(X_fill)

    fig.add_trace(go.Surface(
        x=X_fill, y=Y_fill, z=Z_fill,
        colorscale=[[0, 'rgba(270,270,270,0.4)'], [1, 'rgba(270,270,270,0.4)']],
        opacity=0.4,
        showscale=False,
        hoverinfo='none',
        name='地平面填充'
    ))

    # 1.1 地平面方向标注 (保留)
    # 正北 (N): 方位角 0°, 高度角 0°
    n_x, n_y, n_z = _spherical_to_cartesian(0, 0, radius=1.05) # 稍微超出地平面，避免遮挡
    # 东北 (NE): 方位角 45°, 高度角 0°
    ne_x, ne_y, ne_z = _spherical_to_cartesian(45, 0, radius=1.05)
    # 正东 (E): 方位角 90°, 高度角 0°
    e_x, e_y, e_z = _spherical_to_cartesian(90, 0, radius=1)
    # 东南 (SE): 方位角 135°, 高度角 0°
    se_x, se_y, se_z = _spherical_to_cartesian(135, 0, radius=1.05)
    # 正南 (S): 方位角 180°, 高度角 0°
    s_x, s_y, s_z = _spherical_to_cartesian(180, 0, radius=1.05)
    # 西南 (SW): 方位角 225°, 高度角 0°
    sw_x, sw_y, sw_z = _spherical_to_cartesian(225, 0, radius=1.05)
    # 正西 (W): 方位角 270°, 高度角 0°
    w_x, w_y, w_z = _spherical_to_cartesian(270, 0, radius=1)
    # 西北 (NW): 方位角 315°, 高度角 0°
    nw_x, nw_y, nw_z = _spherical_to_cartesian(315, 0, radius=1.05)
    fig.add_trace(go.Scatter3d(
        x=[n_x[0], ne_x[0], 1.05*e_x[0], se_x[0], s_x[0], sw_x[0], 1.05*w_x[0], nw_x[0] ],
        y=[n_y[0], ne_y[0], 1.05*e_y[0], se_y[0], s_y[0], sw_y[0], w_y[0], nw_y[0] ],
        z=[n_z[0], ne_z[0], e_z[0], se_z[0], s_z[0], sw_z[0], w_z[0], nw_z[0] ],
        mode='text',
        text=['北', '东北', '东', '东南', '南', '西南', '西', '西北'],
        textfont=dict(color='white', size=12),
        textposition='middle center',
        showlegend=False,
        name='方向标注'
    ))

    # 绘制东西方位点的连线
    fig.add_trace(go.Scatter3d(
        x=[e_x[0], w_x[0]],
        y=[e_y[0], w_y[0]],
        z=[e_z[0], w_z[0]],
        mode='lines',
        line=dict(color='lightgray', width=9),
        name='东西连线',
        hoverinfo='none',
        showlegend=False
    ))

    # 2. 地平坐标系：南北天极 (保留)
    # 北天极：高度角 = 观测地纬度，方位角 = 0 (正北)
    # 南天极：高度角 = -观测地纬度，方位角 = 180 (正南)
    
    # 北天极
    np_x_arr, np_y_arr, np_z_arr = _spherical_to_cartesian(0, latitude) # 计算北天极的笛卡尔坐标
    np_x, np_y, np_z = np_x_arr[0], np_y_arr[0], np_z_arr[0] # 取出浮点数值

    # 南天极
    sp_x_arr, sp_y_arr, sp_z_arr = _spherical_to_cartesian(180, -latitude) # 计算南天极的笛卡尔坐标
    sp_x, sp_y, sp_z = sp_x_arr[0], sp_y_arr[0], sp_z_arr[0] # 取出浮点数值

    # 延长南北天极连线
    extension_factor = 1.2 # 延长比例，使天极线稍微超出天球
    extended_np_x = np_x * extension_factor # 延长北天极 x 坐标
    extended_np_y = np_y * extension_factor # 延长北天极 y 坐标
    extended_np_z = np_z * extension_factor # 延长北天极 z 坐标
    extended_sp_x = sp_x * extension_factor # 延长南天极 x 坐标
    extended_sp_y = sp_y * extension_factor # 延长南天极 y 坐标
    extended_sp_z = sp_z * extension_factor # 延长南天极 z 坐标

    fig.add_trace(go.Scatter3d( # 添加北天极标记
        x=[extended_np_x], y=[extended_np_y], z=[extended_np_z], # 延长后的北天极坐标
        mode='markers', # 模式为标记点
        marker=dict(size=1, color='red'), # 设置标记点大小和颜色
        name='北天极', # 轨迹名称
        # hoverinfo='text', # 鼠标悬停时显示文本信息
        hoverinfo='none', # 鼠标悬停时不显示提示信息
        text=f'北天极<br>高度: {latitude:.1f}°' # 悬停文本
    ))
    fig.add_trace(go.Scatter3d( # 添加北天极文本标签
        x=[extended_np_x], y=[extended_np_y], z=[extended_np_z], # 延长后的北天极坐标
        mode='text', # 模式为文本
        text=['北天极'], # 文本内容
        textfont=dict(color='white', size=12), # 文本字体颜色和大小
        textposition='top center', # 文本位置
        showlegend=False # 不显示图例
    ))

    fig.add_trace(go.Scatter3d( # 添加南天极标记
        x=[extended_sp_x], y=[extended_sp_y], z=[extended_sp_z], # 延长后的南天极坐标
        mode='markers', # 模式为标记点
        marker=dict(size=1, color='red'), # 设置标记点大小和颜色
        name='南天极', # 轨迹名称
        #hoverinfo='text', # 鼠标悬停时显示文本信息
        hoverinfo='none', # 鼠标悬停时不显示提示信息
        text=f'南天极<br>高度: {-latitude:.1f}°' # 悬停文本
    ))
    fig.add_trace(go.Scatter3d( # 添加南天极文本标签
        x=[extended_sp_x], y=[extended_sp_y], z=[extended_sp_z], # 延长后的南天极坐标
        mode='text', # 模式为文本
        text=['南天极'], # 文本内容
        textfont=dict(color='white', size=12), # 文本字体颜色和大小
        textposition='bottom center', # 文本位置
        showlegend=False # 不显示图例
    ))

    # 连接延长后的南北天极的连线
    fig.add_trace(go.Scatter3d( # 添加连接南北天极的线条
        x=[extended_np_x, extended_sp_x], y=[extended_np_y, extended_sp_y], z=[extended_np_z, extended_sp_z], # 延长后的南北天极坐标
        mode='lines', # 模式为线条
        line=dict(color='red', width=3), # 设置线条颜色和宽度
        name='天极连线', # 轨迹名称
        hoverinfo='none', # 鼠标悬停时不显示提示信息
        showlegend=False # 不显示图例
    ))

    # 2.2 天顶和天底 (修改为固定Z轴)
    # 天顶：Z轴正方向
    zenith_x, zenith_y, zenith_z = 0, 0, 1.2 # 稍微超出天球
    # 天底：Z轴负方向
    nadir_x, nadir_y, nadir_z = 0, 0, -1.2 # 稍微超出天球

    fig.add_trace(go.Scatter3d( # 添加天顶标记
        x=[zenith_x], y=[zenith_y], z=[zenith_z],
        mode='markers',
        marker=dict(size=1, color='red'),
        name='天顶',
        hoverinfo='none',
    ))
    fig.add_trace(go.Scatter3d( # 添加天顶文本标签
        x=[zenith_x], y=[zenith_y], z=[zenith_z],
        mode='text',
        text=['天顶'],
        textfont=dict(color='red', size=12),
        textposition='top center',
        showlegend=False
    ))

    fig.add_trace(go.Scatter3d( # 添加天底标记
        x=[nadir_x], y=[nadir_y], z=[nadir_z],
        mode='markers',
        marker=dict(size=1, color='red'),
        name='天底',
        hoverinfo='none',
    ))
    fig.add_trace(go.Scatter3d( # 添加天底文本标签
        x=[nadir_x], y=[nadir_y], z=[nadir_z],
        mode='text',
        text=['天底'],
        textfont=dict(color='red', size=12),
        textposition='bottom center',
        showlegend=False
    ))

    # 连接天顶和天底的连线 (当地垂直线)
    fig.add_trace(go.Scatter3d(
        x=[zenith_x, nadir_x], y=[zenith_y, nadir_y], z=[zenith_z, nadir_z],
        mode='lines',
        line=dict(color='red', width=3, dash='dash'), # 使用虚线
        name='天顶天底连线',
        hoverinfo='none',
        showlegend=False
    ))

    # 3. 周日视运动轨迹 (太阳和月亮)
    # 观测地点
    location = Topos(latitude_degrees=latitude, longitude_degrees=longitude) # 定义观测点
    observer = ephemeris['earth'] + location # 定义观测者，地球加上指定经纬度

    # 当地当天的本地午夜与次日午夜
    local_tz = ZoneInfo(tz_name)
    local_date = date_time.astimezone(local_tz).date()
    local_midnight = datetime(local_date.year, local_date.month, local_date.day, 0, 0, tzinfo=local_tz)
    next_midnight = local_midnight + timedelta(days=1)

    # 每小时本地时间（0..23h）
    hours_local = [local_midnight + timedelta(hours=h) for h in range(24)]
    hour_labels_local_arr = np.array([dt.strftime("%H:%M") for dt in hours_local])  # 用于轨迹点文本，转换为 NumPy 数组

    # 转 UTC 喂给 Skyfield
    hours_utc = [dt.astimezone(ZoneInfo("UTC")) for dt in hours_local]
    years_arr  = np.array([dt.year for dt in hours_utc])
    months_arr = np.array([dt.month for dt in hours_utc])
    days_arr   = np.array([dt.day for dt in hours_utc])
    dec_hours_arr = np.array([dt.hour + dt.minute/60 + dt.second/3600 for dt in hours_utc])
    times = ts.utc(years_arr, months_arr, days_arr, dec_hours_arr)


    # 太阳轨迹 (Skyfield 计算并绘制)
    sun = ephemeris['sun']
    sun_altitudes = []
    sun_azimuths = []
    for t in times:
        astrometric = observer.at(t).observe(sun)
        alt, az, _ = astrometric.apparent().altaz()
        sun_altitudes.append(alt.degrees)
        sun_azimuths.append(az.degrees)
    sun_altitudes_arr = np.array(sun_altitudes)
    sun_azimuths_arr = np.array(sun_azimuths) # 转换为 NumPy 数组
    sun_x, sun_y, sun_z = _spherical_to_cartesian(sun_azimuths_arr, sun_altitudes_arr)

    # 区分白天和夜晚轨迹 (不使用 np.nan 断开，而是通过索引区分)
    visible_idx_sun_skyfield = sun_altitudes_arr >= 0
    invisible_idx_sun_skyfield = ~visible_idx_sun_skyfield

    # 添加太阳白天轨迹 (地平线以上)
    fig.add_trace(go.Scatter3d(
        x=sun_x[visible_idx_sun_skyfield], y=sun_y[visible_idx_sun_skyfield], z=sun_z[visible_idx_sun_skyfield],
        mode='lines+markers', # 移除 text，单独绘制
        line=dict(color='orange', width=3),
        marker=dict(size=3, color='orange'),
        name='太阳轨迹 (白天)',
        hoverinfo='none',
        hovertext=[f'太阳<br>时间: {h}<br>方位: {az:.1f}°<br>高度: {alt:.1f}°' for h, az, alt in zip(hour_labels_local_arr[visible_idx_sun_skyfield], sun_azimuths_arr[visible_idx_sun_skyfield], sun_altitudes_arr[visible_idx_sun_skyfield])]
    ))

    # 添加太阳夜晚轨迹 (地平线以下)
    fig.add_trace(go.Scatter3d(
        x=sun_x[invisible_idx_sun_skyfield], y=sun_y[invisible_idx_sun_skyfield], z=sun_z[invisible_idx_sun_skyfield],
        mode='lines+markers', # 移除 text，单独绘制
        line=dict(color='orange', width=3, dash='dash'),
        marker=dict(size=3, color='orange'),
        name='太阳轨迹 (夜晚)',
        hoverinfo='none',
        hovertext=[f'太阳<br>时间: {h}<br>方位: {az:.1f}°<br>高度: {alt:.1f}°' for h, az, alt in zip(hour_labels_local_arr[invisible_idx_sun_skyfield], sun_azimuths_arr[invisible_idx_sun_skyfield], sun_altitudes_arr[invisible_idx_sun_skyfield])]
    ))

    # 添加太阳轨迹整点标记
    fig.add_trace(go.Scatter3d(
        x=sun_x, y=sun_y, z=sun_z,
        mode='text',
        text=[f"{h} h" for h in range(24)],
        textfont=dict(color='orange', size=12),
        textposition='top center',
        showlegend=False,
        hoverinfo='none'
    ))

    # 月亮轨迹 (Skyfield 计算并绘制)
    moon = ephemeris['moon']
    moon_altitudes = []
    moon_azimuths = []
    for t in times:
        astrometric = observer.at(t).observe(moon)
        alt, az, _ = astrometric.apparent().altaz()
        moon_altitudes.append(alt.degrees)
        moon_azimuths.append(az.degrees)
    moon_altitudes_arr = np.array(moon_altitudes)
    moon_azimuths_arr = np.array(moon_azimuths) # 转换为 NumPy 数组
    moon_x, moon_y, moon_z = _spherical_to_cartesian(moon_azimuths_arr, moon_altitudes_arr)

    # 区分白天和夜晚轨迹 (不使用 np.nan 断开，而是通过索引区分)
    visible_idx_moon_skyfield = moon_altitudes_arr >= 0
    invisible_idx_moon_skyfield = ~visible_idx_moon_skyfield

    # 添加月亮白天轨迹 (地平线以上)
    fig.add_trace(go.Scatter3d(
        x=moon_x[visible_idx_moon_skyfield], y=moon_y[visible_idx_moon_skyfield], z=moon_z[visible_idx_moon_skyfield],
        mode='lines+markers', # 移除 text，单独绘制
        line=dict(color='lightblue', width=3),
        marker=dict(size=3, color='lightblue'),
        name='月亮轨迹 (白天)',
        hoverinfo='none',
        hovertext=[f'月亮<br>时间: {h}<br>方位: {az:.1f}°<br>高度: {alt:.1f}°' for h, az, alt in zip(hour_labels_local_arr[visible_idx_moon_skyfield], moon_azimuths_arr[visible_idx_moon_skyfield], moon_altitudes_arr[visible_idx_moon_skyfield])]
    ))

    # 添加月亮夜晚轨迹 (地平线以下)
    fig.add_trace(go.Scatter3d(
        x=moon_x[invisible_idx_moon_skyfield], y=moon_y[invisible_idx_moon_skyfield], z=moon_z[invisible_idx_moon_skyfield],
        mode='lines+markers', # 移除 text，单独绘制
        line=dict(color='lightblue', width=3, dash='dash'), # 使银色虚线，与太阳夜晚轨迹颜色一致
        marker=dict(size=3, color='lightblue'),
        name='月亮轨迹 (夜晚)',
        hoverinfo='none',
        hovertext=[f'月亮<br>时间: {h}<br>方位: {az:.1f}°<br>高度: {alt:.1f}°' for h, az, alt in zip(hour_labels_local_arr[invisible_idx_moon_skyfield], moon_azimuths_arr[invisible_idx_moon_skyfield], moon_altitudes_arr[invisible_idx_moon_skyfield])]
    ))

    # 添加月亮轨迹整点标记
    fig.add_trace(go.Scatter3d(
        x=moon_x, y=moon_y, z=moon_z,
        mode='text',
        text=[f"{h} h" for h in range(24)],
        textfont=dict(color='lightblue', size=12),
        textposition='top center',
        showlegend=False,
        hoverinfo='none'
    ))

    # 2.1 纬度标注
    if latitude >= 0:
        latitude_text = f"北纬 {latitude:.1f}°"
    else:
        latitude_text = f"南纬 {-latitude:.1f}°"

    # 3. 太阳和月亮实时位置
    now_local = date_time.astimezone(local_tz)   # 当前本地时刻（或传入的本地参照时刻）
    now_utc = now_local.astimezone(ZoneInfo("UTC"))
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day,
                   now_utc.hour + now_utc.minute/60 + now_utc.second/3600)

    # 太阳实时点
    alt_s, az_s, _ = (observer.at(t_now).observe(ephemeris['sun']).apparent().altaz())
    sx, sy, sz = _spherical_to_cartesian(az_s.degrees, alt_s.degrees)
    fig.add_trace(go.Scatter3d(
        x=[sx[0]], y=[sy[0]], z=[sz[0]],
        mode='markers+text',
        marker=dict(size=9, color='orange', symbol='circle'),
        text=[f"太阳(实时 {now_local.strftime('%H:%M')})"],
        textfont=dict(color='orange', size=12),
        textposition='top center',
        name='太阳(实时)',
        hoverinfo='none', # 鼠标悬停时不显示提示信息
        #hovertemplate=None, # 去掉点击时的3D方框
    ))

    # 月亮实时点
    alt_m, az_m, _ = (observer.at(t_now).observe(ephemeris['moon']).apparent().altaz())
    mx, my, mz = _spherical_to_cartesian(az_m.degrees, alt_m.degrees)
    fig.add_trace(go.Scatter3d(
        x=[mx[0]], y=[my[0]], z=[mz[0]],
        mode='markers+text',
        marker=dict(size=9, color='lightblue', symbol='circle'),
        text=[f"月亮(实时 {now_local.strftime('%H:%M')})"],
        textfont=dict(color='white', size=12),
        textposition='top center',
        name='月亮(实时)',
        hoverinfo='none', # 鼠标悬停时不显示提示信息
        #hovertemplate=None, # 去掉点击时的3D方框
    ))

    # 5. 日出日落标记
    if show_rise_set:
        t0 = ts.utc(local_midnight.astimezone(ZoneInfo("UTC")).year,
                    local_midnight.astimezone(ZoneInfo("UTC")).month,
                    local_midnight.astimezone(ZoneInfo("UTC")).day, 0)
        t1 = ts.utc(next_midnight.astimezone(ZoneInfo("UTC")).year,
                    next_midnight.astimezone(ZoneInfo("UTC")).month,
                    next_midnight.astimezone(ZoneInfo("UTC")).day, 0)

        # 太阳日出日落
        f_sun = almanac.sunrise_sunset(ephemeris, location)
        t_events_sun, events_sun = almanac.find_discrete(t0, t1, f_sun)
        for t_e, ev in zip(t_events_sun, events_sun):
            alt_e, az_e, _ = (observer.at(t_e).observe(ephemeris['sun']).apparent().altaz())
            ex, ey, ez = _spherical_to_cartesian(az_e.degrees, 0.0)
            label = '日出' if ev == 1 else '日落'
            local_e = t_e.utc_datetime().astimezone(local_tz)
            fig.add_trace(go.Scatter3d(
                x=[ex[0]], y=[ey[0]], z=[ez[0]],
                #mode='markers+text',
                #marker=dict(symbol ='circle', size=9, color='orange'),
                mode='text',
                text=[f"{label} {local_e.strftime('%H:%M')}"],
                textfont=dict(color='orange', size=12),
                textposition='top center',
                name=label,
                hoverinfo='none',
            ))
        
        # --- 太阳日出日落时刻 ---
        f_sun = almanac.sunrise_sunset(ephemeris, location)
        t_events_sun, events_sun = almanac.find_discrete(t0, t1, f_sun)

        extra_times, extra_alts, extra_azs = [], [], []
        for t_e, ev in zip(t_events_sun, events_sun):
            alt_e, az_e, _ = observer.at(t_e).observe(ephemeris['sun']).apparent().altaz()
            extra_times.append(t_e.utc_datetime())
            extra_alts.append(0.0)             # 强制高度角=0
            extra_azs.append(az_e.degrees)     # 方位角保持计算值

        # --- 合并整点与日出日落点，排序 ---
        all_times = list(hours_utc) + extra_times
        all_alts  = list(sun_altitudes) + extra_alts
        all_azs   = list(sun_azimuths) + extra_azs

        all_times_sorted, all_alts_sorted, all_azs_sorted = zip(*sorted(zip(all_times, all_alts, all_azs)))

        sun_altitudes_arr = np.array(all_alts_sorted)
        sun_azimuths_arr  = np.array(all_azs_sorted)
        sun_x, sun_y, sun_z = _spherical_to_cartesian(sun_azimuths_arr, sun_altitudes_arr)
        
        # --- 绘制连续曲线 ---
        fig.add_trace(go.Scatter3d(
            x=sun_x, y=sun_y, z=sun_z,
            mode='lines+markers',
            line=dict(color='orange', width=3),
            marker=dict(size=3, color='orange'),
            name='太阳轨迹',
            hoverinfo='none'
        ))

        # 月亮月出月落
        # Skyfield 使用 risings_and_settings 来计算月出月落
        f_moon = almanac.risings_and_settings(ephemeris, ephemeris['moon'], location)
        t_events_moon, events_moon = almanac.find_discrete(t0, t1, f_moon)
        for t_e, ev in zip(t_events_moon, events_moon):
            alt_e, az_e, _ = (observer.at(t_e).observe(ephemeris['moon']).apparent().altaz())
            ex, ey, ez = _spherical_to_cartesian(az_e.degrees, 0.0)
            label = '月出' if ev == 1 else '月落'
            local_e = t_e.utc_datetime().astimezone(local_tz)
            fig.add_trace(go.Scatter3d(
                x=[ex[0]], y=[ey[0]], z=[ez[0]],
                # mode='markers+text',
                # marker=dict(size=4, color='lightblue'),
                mode='text',
                text=[f"{label} {local_e.strftime('%H:%M')}"],
                textfont=dict(color='lightblue', size=12),
                textposition='top center',
                name=label,
                hoverinfo='none',
            ))
        
        # --- 绘制连续曲线 ---
        fig.add_trace(go.Scatter3d(
            x=moon_x, y=moon_y, z=moon_z,
            mode='lines+markers',
            line=dict(color='lightblue', width=3),
            marker=dict(size=3, color='lightblue'),
            name='月亮轨迹',
            hoverinfo='none'
        ))

    # 6. 可视化要求
    fig.update_layout( # 更新图表布局
        title=f"地心天球模型 - {date_time.astimezone(local_tz).strftime('%Y年%m月%d日 %H:%M')}  ({tz_name})  观测点: 纬度{latitude}°, 经度{longitude}°)", # 设置图表标题
        annotations=[
            dict(
                text=latitude_text,
                xref="paper", yref="paper",
                x=0.05, y=0.95, # 放置在左上角
                showarrow=False,
                font=dict(color="white", size=12)
            )
        ],
        scene=dict( # 设置 3D 场景布局
            xaxis=dict(showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''), # 隐藏 x 轴背景、刻度标签、零线和网格线
            yaxis=dict(showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''), # 隐藏 y 轴背景、刻度标签、零线和网格线
            zaxis=dict(showbackground=False, showticklabels=False, zeroline=False, showgrid=False, title=''), # 隐藏 z 轴背景、刻度标签、零线和网格线
            aspectmode='cube', # 保持 x,y,z 轴比例一致，使球体看起来是圆的
            bgcolor='rgb(0,0,0)', # 设置 3D 场景背景颜色为纯黑色
            camera=dict(
                eye=dict(x=np.cos(np.deg2rad(20))*np.cos(np.deg2rad(90)), y=np.cos(np.deg2rad(20))*np.sin(np.deg2rad(90)), z=np.sin(np.deg2rad(20))) # 匹配 view(90,20)
            )
        ),
        paper_bgcolor='rgb(0,0,0)', # 设置图表纸张背景颜色为纯黑色
        font=dict(color='white', family="SimHei, Arial, sans-serif"), # 设置字体颜色为白色，并指定中文字体
        showlegend=True # 显示图例
    )

    fig.show() # 显示图表

if __name__ == "__main__": # 如果作为主程序运行
    # 示例用法
    # 观测地点：上海 (纬度 31.23, 经度 121.47)
    # 观测日期时间：当前时间
    current_time = datetime.now() # 获取当前日期和时间
    plot_geocentric_celestial_sphere(latitude=31.23, longitude=121.47, date_time=current_time, tz_name='Asia/Shanghai') # 调用函数绘制地心天球模型

    # 另一个示例：伦敦 (纬度 51.5, 经度 -0.1)
    # plot_geocentric_celestial_sphere(latitude=51.5, longitude=-0.1, date_time=current_time) # 调用函数绘制伦敦的地心天球模型
