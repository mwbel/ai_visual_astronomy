import numpy as np # 导入 NumPy 库，用于数值计算
import plotly.graph_objects as go # 导入 Plotly 的 graph_objects 模块，用于创建交互式图表
from datetime import datetime, timedelta # 导入 datetime 和 timedelta 模块，用于处理日期和时间
from zoneinfo import ZoneInfo # 导入 ZoneInfo，用于处理时区
from skyfield.api import load, Topos, EarthSatellite, utc # 导入 Skyfield 库，用于天文计算，包括加载星历表、定义观测点、处理卫星和UTC时区
from skyfield.framelib import itrs # 导入 Skyfield 的 framelib 模块中的 itrs，用于地球固定坐标系
from skyfield import almanac # 导入 almanac，用于计算日出日落

# 加载星历表
# 确保 de421.bsp 文件在当前目录或 skyfield_data 目录中
try:
    ephemeris = load('de421.bsp') # 尝试加载 JPL DE421 星历表文件
except FileNotFoundError: # 如果文件未找到
    print("de421.bsp not found. Attempting to download...") # 打印提示信息
    load('de421.bsp') # 尝试下载 de421.bsp 文件
    ephemeris = load('de421.bsp') # 再次加载星历表

ts = load.timescale() # 初始化 Skyfield 的时间尺度对象，用于创建时间点

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

def _generate_celestial_sphere_grid(radius=1):
    """
    生成天球的经纬网格数据（地平坐标系）。
    """
    # 纬线 (平行于地平面的小圆)
    latitudes = np.arange(-80, 90, 10) # 生成从-80到80，每10度一条纬线的高度角数组
    longitudes = np.arange(0, 360, 15) # 生成从0到345，每15度一条经线的方位角数组

    grid_traces = [] # 用于存储网格线的 Plotly 轨迹

    # 绘制纬线
    # 除了地平圈（alt=0°）加粗为白色，其它网格浅灰
    for alt_deg in latitudes: # 遍历每个纬度（高度角）
        if alt_deg == 0: # 如果是地平圈
            color = 'white' # 设置颜色为白色
            width = 2 # 设置线宽为2
        else: # 其他纬线
            color = 'lightgray' # 设置颜色为浅灰色
            width = 1.5 # 设置线宽为1.5
        
        azimuths = np.linspace(0, 360, 100) # 生成从0到360度的100个方位角
        x, y, z = _spherical_to_cartesian(azimuths, alt_deg, radius) # 将地平坐标转换为笛卡尔坐标
        grid_traces.append(go.Scatter3d( # 添加 3D 散点图轨迹
            x=x, y=y, z=z, # 坐标数据
            mode='lines', # 模式为线条
            line=dict(color=color, width=width), # 设置线条颜色和宽度
            hoverinfo='none', # 鼠标悬停时不显示提示信息
            hovertemplate=None, # 去掉点击时的3D方框
            showlegend=False # 图例里不显示这条线
        ))
    
    # 绘制经线
    for az_deg in longitudes: # 遍历每个经度（方位角）
        altitudes = np.linspace(-90, 90, 100) # 生成从-90到90度的100个高度角
        x, y, z = _spherical_to_cartesian(az_deg, altitudes, radius) # 将地平坐标转换为笛卡尔坐标
        grid_traces.append(go.Scatter3d( # 添加 3D 散点图轨迹
            x=x, y=y, z=z, # 坐标数据
            mode='lines', # 模式为线条
            line=dict(color='lightgray', width=0.5), # 设置线条颜色和宽度
            hoverinfo='none', # 鼠标悬停时不显示提示信息
            hovertemplate=None, # 去掉点击时的3D方框
            showlegend=False # 图例里不显示这条线
        ))
    
    return grid_traces # 返回所有网格线的轨迹

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

    # 1. 天球建模：透明球体
    u = np.linspace(0, 2 * np.pi, 100) # 生成 u 坐标，从 0 到 2π
    v = np.linspace(0, np.pi, 100) # 生成 v 坐标，从 0 到 π
    x_sphere = 1 * np.outer(np.cos(u), np.sin(v)) # 计算球体的 x 坐标
    y_sphere = 1 * np.outer(np.sin(u), np.sin(v)) # 计算球体的 y 坐标
    z_sphere = 1 * np.outer(np.ones(np.size(u)), np.cos(v)) # 计算球体的 z 坐标

    fig.add_trace(go.Surface( # 添加一个表面轨迹来表示天球
        x=x_sphere, y=y_sphere, z=z_sphere, # 球体坐标数据
        colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']], # 设置完全透明的颜色刻度
        opacity=0.2, # 设置透明度
        showscale=False, # 不显示颜色刻度
        hoverinfo='none', # 鼠标悬停时不显示提示信息
        name='天球' # 轨迹名称
    ))

    # 绘制地平面 (实心圆)
    theta = np.linspace(0, 2 * np.pi, 100) # 生成地平面的角度，从 0 到 2π
    r = np.linspace(0, 1, 2) # 生成地平面的半径，从中心到半径1
    T, R = np.meshgrid(theta, r) # 创建网格
    x_plane = R * np.cos(T) # 计算地平面的 x 坐标
    y_plane = R * np.sin(T) # 计算地平面的 y 坐标
    z_plane = np.zeros_like(x_plane) # 地平面在 z=0，所有 z 坐标为 0

    fig.add_trace(go.Surface( # 添加一个表面轨迹来表示地平面
        x=x_plane, y=y_plane, z=z_plane, # 地平面坐标数据
        colorscale=[[0, 'rgba(50,50,50,0.5)'], [1, 'rgba(50,50,50,0.5)']], # 设置半透明灰色颜色刻度
        opacity=0.5, # 设置透明度
        showscale=False, # 不显示颜色刻度
        hoverinfo='none', # 鼠标悬停时不显示提示信息
        name='地平面' # 轨迹名称
    ))

    # 绘制经纬网格
    grid_traces = _generate_celestial_sphere_grid() # 调用函数生成天球网格线
    for trace in grid_traces: # 遍历所有网格线轨迹
        fig.add_trace(trace) # 将网格线添加到图中

    # 1.1 地平面方向标注
    # 正北 (N): 方位角 0°, 高度角 0°
    n_x, n_y, n_z = _spherical_to_cartesian(0, 0, radius=1.05) # 稍微超出地平面，避免遮挡
    # 正东 (E): 方位角 90°, 高度角 0°
    e_x, e_y, e_z = _spherical_to_cartesian(90, 0, radius=1.05)
    # 正南 (S): 方位角 180°, 高度角 0°
    s_x, s_y, s_z = _spherical_to_cartesian(180, 0, radius=1.05)
    # 正西 (W): 方位角 270°, 高度角 0°
    w_x, w_y, w_z = _spherical_to_cartesian(270, 0, radius=1.05)

    fig.add_trace(go.Scatter3d(
        x=[n_x[0], e_x[0], s_x[0], w_x[0]],
        y=[n_y[0], e_y[0], s_y[0], w_y[0]],
        z=[n_z[0], e_z[0], s_z[0], w_z[0]],
        mode='text',
        text=['北', '东', '南', '西'],
        textfont=dict(color='white', size=12),
        textposition='middle center',
        showlegend=False,
        name='方向标注'
    ))

    # 2. 地平坐标系：南北天极
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
    hour_labels_local = [dt.strftime("%H:%M") for dt in hours_local]  # 用于轨迹点文本

    # 转 UTC 喂给 Skyfield
    hours_utc = [dt.astimezone(ZoneInfo("UTC")) for dt in hours_local]
    years  = [dt.year for dt in hours_utc]
    months = [dt.month for dt in hours_utc]
    days   = [dt.day for dt in hours_utc]
    dec_hours = [dt.hour + dt.minute/60 + dt.second/3600 for dt in hours_utc]
    times = ts.utc(years, months, days, dec_hours)

    # 太阳轨迹
    sun = ephemeris['sun'] # 获取太阳的星历数据
    sun_altitudes = [] # 存储太阳高度角
    sun_azimuths = [] # 存储太阳方位角
    for t in times: # 遍历每个时间点
        astrometric = observer.at(t).observe(sun) # 观测太阳
        alt, az, _ = astrometric.apparent().altaz() # 获取太阳的视高度角和方位角
    sun_altitudes_arr = np.array(sun_altitudes)
    sun_azimuths_arr = np.array(sun_azimuths)

    # 区分白天和夜晚轨迹
    sun_x, sun_y, sun_z = _spherical_to_cartesian(sun_azimuths_arr, sun_altitudes_arr)

    # 白天轨迹 (alt >= 0)
    sun_x_day = np.where(sun_altitudes_arr >= 0, sun_x, np.nan)
    sun_y_day = np.where(sun_altitudes_arr >= 0, sun_y, np.nan)
    sun_z_day = np.where(sun_altitudes_arr >= 0, sun_z, np.nan)

    # 夜晚轨迹 (alt < 0)
    sun_x_night = np.where(sun_altitudes_arr < 0, sun_x, np.nan)
    sun_y_night = np.where(sun_altitudes_arr < 0, sun_y, np.nan)
    sun_z_night = np.where(sun_altitudes_arr < 0, sun_z, np.nan)

    # 添加太阳白天轨迹
    fig.add_trace(go.Scatter3d(
        x=sun_x_day, y=sun_y_day, z=sun_z_day,
        mode='lines+markers+text',
        line=dict(color='orange', width=3),
        marker=dict(size=3, color='orange'),
        text=[f"{h}:00" for h in range(24)], # 每个整点打标
        textfont=dict(color='orange', size=12),
        textposition='top center',
        name='太阳轨迹 (白天)',
        hoverinfo='none',
        hovertemplate=None, # 去掉点击时的3D方框
        hovertext=[f'太阳<br>时间: {h}<br>方位: {az:.1f}°<br>高度: {alt:.1f}°' for h, az, alt in zip(hour_labels_local, sun_azimuths, sun_altitudes)]
    ))

    # 添加太阳夜晚轨迹
    fig.add_trace(go.Scatter3d(
        x=sun_x_night, y=sun_y_night, z=sun_z_night,
        mode='lines+markers+text',
        line=dict(color='blue', width=3),
        marker=dict(size=3, color='blue'),
        text=[f"{h}:00" for h in range(24)], # 每个整点打标
        textfont=dict(color='blue', size=12),
        textposition='top center',
        name='太阳轨迹 (夜晚)',
        hoverinfo='none',
        hovertemplate=None, # 去掉点击时的3D方框
        hovertext=[f'太阳<br>时间: {h}<br>方位: {az:.1f}°<br>高度: {alt:.1f}°' for h, az, alt in zip(hour_labels_local, sun_azimuths, sun_altitudes)]
    ))

    # 月亮轨迹
    moon = ephemeris['moon'] # 获取月亮的星历数据
    moon_altitudes = [] # 存储月亮高度角
    moon_azimuths = [] # 存储月亮方位角
    for t in times: # 遍历每个时间点
        astrometric = observer.at(t).observe(moon) # 观测月亮
        alt, az, _ = astrometric.apparent().altaz() # 获取月亮的视高度角和方位角
        moon_altitudes.append(alt.degrees) # 将高度角（度）添加到列表
        moon_azimuths.append(az.degrees) # 将方位角（度）添加到列表

    moon_altitudes_arr = np.array(moon_altitudes)
    moon_azimuths_arr = np.array(moon_azimuths)

    # 区分白天和夜晚轨迹
    moon_x, moon_y, moon_z = _spherical_to_cartesian(moon_azimuths_arr, moon_altitudes_arr)

    # 白天轨迹 (alt >= 0)
    moon_x_day = np.where(moon_altitudes_arr >= 0, moon_x, np.nan)
    moon_y_day = np.where(moon_altitudes_arr >= 0, moon_y, np.nan)
    moon_z_day = np.where(moon_altitudes_arr >= 0, moon_z, np.nan)

    # 夜晚轨迹 (alt < 0)
    moon_x_night = np.where(moon_altitudes_arr < 0, moon_x, np.nan)
    moon_y_night = np.where(moon_altitudes_arr < 0, moon_y, np.nan)
    moon_z_night = np.where(moon_altitudes_arr < 0, moon_z, np.nan)

    # 添加月亮白天轨迹
    fig.add_trace(go.Scatter3d(
        x=moon_x_day, y=moon_y_day, z=moon_z_day,
        mode='lines+markers+text',
        line=dict(color='lightblue', width=3),
        marker=dict(size=3, color='lightblue'),
        text=[f"{h}:00" for h in range(24)], # 每个整点打标
        textfont=dict(color='lightblue', size=12),
        textposition='top center',
        name='月亮轨迹 (白天)',
        hoverinfo='none',
        hovertemplate=None, # 去掉点击时的3D方框
        hovertext=[f'月亮<br>时间: {h}<br>方位: {az:.1f}°<br>高度: {alt:.1f}°' for h, az, alt in zip(hour_labels_local, moon_azimuths, moon_altitudes)]
    ))

    # 添加月亮夜晚轨迹
    fig.add_trace(go.Scatter3d(
        x=moon_x_night, y=moon_y_night, z=moon_z_night,
        mode='lines+markers+text',
        line=dict(color='blue', width=3),
        marker=dict(size=3, color='blue'),
        text=[f"{h}:00" for h in range(24)], # 每个整点打标
        textfont=dict(color='blue', size=12),
        textposition='top center',
        name='月亮轨迹 (夜晚)',
        hoverinfo='none',
        hovertemplate=None, # 去掉点击时的3D方框
        hovertext=[f'月亮<br>时间: {h}<br>方位: {az:.1f}°<br>高度: {alt:.1f}°' for h, az, alt in zip(hour_labels_local, moon_azimuths, moon_altitudes)]
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
        marker=dict(size=5, color='orange', symbol='circle'),
        text=[f"太阳(实时 {now_local.strftime('%H:%M')})"],
        textfont=dict(color='orange', size=12),
        textposition='top center',
        name='太阳(实时)',
        hoverinfo='none', # 鼠标悬停时不显示提示信息
        hovertemplate=None, # 去掉点击时的3D方框
    ))

    # 月亮实时点
    alt_m, az_m, _ = (observer.at(t_now).observe(ephemeris['moon']).apparent().altaz())
    mx, my, mz = _spherical_to_cartesian(az_m.degrees, alt_m.degrees)
    fig.add_trace(go.Scatter3d(
        x=[mx[0]], y=[my[0]], z=[mz[0]],
        mode='markers+text',
        marker=dict(size=5, color='white', symbol='circle'),
        text=[f"月亮(实时 {now_local.strftime('%H:%M')})"],
        textfont=dict(color='white', size=12),
        textposition='top center',
        name='月亮(实时)',
        hoverinfo='none', # 鼠标悬停时不显示提示信息
        hovertemplate=None, # 去掉点击时的3D方框
    ))

    # 5. 日出日落标记
    if show_rise_set:
        t0 = ts.utc(local_midnight.astimezone(ZoneInfo("UTC")).year,
                    local_midnight.astimezone(ZoneInfo("UTC")).month,
                    local_midnight.astimezone(ZoneInfo("UTC")).day, 0)
        t1 = ts.utc(next_midnight.astimezone(ZoneInfo("UTC")).year,
                    next_midnight.astimezone(ZoneInfo("UTC")).month,
                    next_midnight.astimezone(ZoneInfo("UTC")).day, 0)

        f = almanac.sunrise_sunset(ephemeris, location)
        t_events, events = almanac.find_discrete(t0, t1, f)
        for t_e, ev in zip(t_events, events):
            alt_e, az_e, _ = (observer.at(t_e).observe(ephemeris['sun']).apparent().altaz())
            # 取地平高度(0°)附近的方位角，验证应接近 东(90°)/西(270°)
            ex, ey, ez = _spherical_to_cartesian(az_e.degrees, 0.0)
            label = '日出' if ev == 1 else '日落'  # almanac: 1=rise, 0=set
            local_e = t_e.utc_datetime().astimezone(local_tz)
            fig.add_trace(go.Scatter3d(
                x=[ex[0]], y=[ey[0]], z=[ez[0]],
                mode='markers+text',
                marker=dict(size=3.5, color='green' if ev==1 else 'red'),
                text=[f"{label} {local_e.strftime('%H:%M')}"],
                textfont=dict(color='green' if ev==1 else 'red', size=9),
                textposition='top center',
                name=label,
                hoverinfo='none', # 鼠标悬停时不显示提示信息
                hovertemplate=None, # 去掉点击时的3D方框
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
            bgcolor='black' # 设置 3D 场景背景颜色为黑色
        ),
        paper_bgcolor='black', # 设置图表纸张背景颜色为黑色
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
