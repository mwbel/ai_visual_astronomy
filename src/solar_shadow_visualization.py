# 目标：创建杆子影长变化的3D可视化，展示不同时间和纬度下垂直杆子的影长变化
# 依赖：numpy, plotly, skyfield
# 安装：pip install numpy plotly skyfield tzdata

import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from skyfield.api import load, Topos
from pathlib import Path

# =============== Skyfield 初始化 ===============
ephemeris = load('de421.bsp')
ts = load.timescale()

# =============== 工具函数 ===============
def _tofloat(x):
    """把 numpy array 或标量转为 float"""
    a = np.atleast_1d(x)
    return float(a[0])

def calculate_shadow_length(sun_altitude_deg, pole_height=1.0):
    """
    计算杆子影长
    sun_altitude_deg: 太阳高度角（度）
    pole_height: 杆子高度（米）
    返回: 影长（米）
    """
    if sun_altitude_deg <= 0:
        return float('inf')  # 太阳在地平线下，无影子或影子无限长
    
    sun_alt_rad = np.deg2rad(sun_altitude_deg)
    shadow_length = pole_height / np.tan(sun_alt_rad)
    return shadow_length

def get_sun_position(observer, time):
    """获取太阳的地平坐标"""
    sun = ephemeris['sun']
    alt, az, _ = observer.at(time).observe(sun).apparent().altaz()
    return alt.degrees, az.degrees

# =============== 主可视化函数 ===============
def create_shadow_visualization(latitude, longitude, date_time, tz_name='Asia/Shanghai', pole_height=1.0):
    """
    创建杆子影长变化的3D可视化
    """
    fig = go.Figure()
    
    # 设置观测者
    location = Topos(latitude_degrees=latitude, longitude_degrees=longitude)
    observer = ephemeris['earth'] + location
    
    local_tz = ZoneInfo(tz_name)
    if date_time.tzinfo is None:
        date_time = date_time.replace(tzinfo=local_tz)
    
    local_date = date_time.astimezone(local_tz).date()
    
    # 计算一天中每小时的影长变化
    times = []
    shadow_lengths = []
    sun_altitudes = []
    sun_azimuths = []
    hour_labels = []
    
    for hour in range(24):
        local_time = datetime(local_date.year, local_date.month, local_date.day, hour, 0, tzinfo=local_tz)
        utc_time = local_time.astimezone(ZoneInfo('UTC'))
        t = ts.utc(utc_time.year, utc_time.month, utc_time.day, utc_time.hour)
        
        sun_alt, sun_az = get_sun_position(observer, t)
        shadow_len = calculate_shadow_length(sun_alt, pole_height)
        
        times.append(hour)
        shadow_lengths.append(shadow_len if shadow_len != float('inf') else 0)
        sun_altitudes.append(sun_alt)
        sun_azimuths.append(sun_az)
        hour_labels.append(f"{hour:02d}:00")
    
    # 绘制影长变化曲线
    fig.add_trace(go.Scatter(
        x=times,
        y=shadow_lengths,
        mode='lines+markers',
        name='影长变化',
        line=dict(color='blue', width=3),
        marker=dict(size=6, color='blue'),
        text=hour_labels,
        hovertemplate='时间: %{text}<br>影长: %{y:.2f}米<extra></extra>'
    ))
    
    # 绘制太阳高度角变化
    fig.add_trace(go.Scatter(
        x=times,
        y=sun_altitudes,
        mode='lines+markers',
        name='太阳高度角',
        line=dict(color='orange', width=2),
        marker=dict(size=4, color='orange'),
        yaxis='y2',
        text=hour_labels,
        hovertemplate='时间: %{text}<br>太阳高度角: %{y:.1f}°<extra></extra>'
    ))
    
    # 创建3D影子可视化
    fig_3d = go.Figure()
    
    # 绘制地面
    ground_size = 5
    x_ground = np.linspace(-ground_size, ground_size, 20)
    y_ground = np.linspace(-ground_size, ground_size, 20)
    X_ground, Y_ground = np.meshgrid(x_ground, y_ground)
    Z_ground = np.zeros_like(X_ground)
    
    fig_3d.add_trace(go.Surface(
        x=X_ground, y=Y_ground, z=Z_ground,
        colorscale=[[0, 'lightgray'], [1, 'lightgray']],
        showscale=False,
        opacity=0.7,
        name='地面'
    ))
    
    # 绘制杆子
    fig_3d.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[0, pole_height],
        mode='lines+markers',
        line=dict(color='brown', width=8),
        marker=dict(size=4, color='brown'),
        name='杆子'
    ))
    
    # 选择几个关键时刻绘制影子
    key_hours = [6, 9, 12, 15, 18]
    colors = ['purple', 'blue', 'red', 'orange', 'darkblue']
    
    for i, hour in enumerate(key_hours):
        if hour < len(shadow_lengths) and shadow_lengths[hour] > 0 and shadow_lengths[hour] < 20:
            # 计算影子方向（与太阳方位角相反）
            shadow_azimuth = (sun_azimuths[hour] + 180) % 360
            shadow_az_rad = np.deg2rad(shadow_azimuth)
            
            # 影子终点坐标
            shadow_x = shadow_lengths[hour] * np.sin(shadow_az_rad)
            shadow_y = shadow_lengths[hour] * np.cos(shadow_az_rad)
            
            fig_3d.add_trace(go.Scatter3d(
                x=[0, shadow_x], y=[0, shadow_y], z=[0, 0],
                mode='lines+markers',
                line=dict(color=colors[i], width=4),
                marker=dict(size=3, color=colors[i]),
                name=f'{hour:02d}:00 影子'
            ))
    
    # 布局设置
    fig.update_layout(
        title=f'杆子影长变化 - {date_time.strftime("%Y年%m月%d日")} (纬度: {latitude}°)',
        xaxis_title='时间 (小时)',
        yaxis_title='影长 (米)',
        yaxis2=dict(
            title='太阳高度角 (度)',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        template='plotly_dark'
    )
    
    fig_3d.update_layout(
        title=f'3D影子可视化 - {date_time.strftime("%Y年%m月%d日")} (纬度: {latitude}°)',
        scene=dict(
            xaxis_title='东西方向 (米)',
            yaxis_title='南北方向 (米)',
            zaxis_title='高度 (米)',
            aspectmode='cube',
            bgcolor='rgb(0,0,0)'
        ),
        template='plotly_dark'
    )
    
    # 导出HTML文件
    project_root = Path(__file__).resolve().parent.parent
    
    # 2D图表
    out_html_2d = project_root / "app/modules/modern_astronomy/pages/solar_shadow_2d_plotly.html"
    out_html_2d.parent.mkdir(parents=True, exist_ok=True)
    config = dict(displaylogo=False, scrollZoom=True, responsive=True)
    fig.write_html(str(out_html_2d), include_plotlyjs='cdn', full_html=True, config=config)
    print(f"[ok] 2D影长图表导出: {out_html_2d}")
    
    # 3D图表
    out_html_3d = project_root / "app/modules/modern_astronomy/pages/solar_shadow_3d_plotly.html"
    fig_3d.write_html(str(out_html_3d), include_plotlyjs='cdn', full_html=True, config=config)
    print(f"[ok] 3D影子可视化导出: {out_html_3d}")
    
    fig.show()
    fig_3d.show()

def create_latitude_comparison(date_time, tz_name='Asia/Shanghai'):
    """
    创建不同纬度的影长对比可视化
    """
    fig = go.Figure()
    
    latitudes = [0, 23.5, 45, 60, 90]  # 赤道、北回归线、中纬度、高纬度、北极
    latitude_names = ['赤道', '北回归线', '中纬度', '高纬度', '北极']
    colors = ['red', 'orange', 'green', 'blue', 'purple']
    
    for i, (lat, name, color) in enumerate(zip(latitudes, latitude_names, colors)):
        location = Topos(latitude_degrees=lat, longitude_degrees=0)
        observer = ephemeris['earth'] + location
        
        times = []
        shadow_lengths = []
        
        for hour in range(24):
            local_time = datetime(date_time.year, date_time.month, date_time.day, hour, 0, tzinfo=ZoneInfo(tz_name))
            utc_time = local_time.astimezone(ZoneInfo('UTC'))
            t = ts.utc(utc_time.year, utc_time.month, utc_time.day, utc_time.hour)
            
            sun_alt, _ = get_sun_position(observer, t)
            shadow_len = calculate_shadow_length(sun_alt, 1.0)
            
            times.append(hour)
            shadow_lengths.append(shadow_len if shadow_len != float('inf') and shadow_len < 50 else None)
        
        fig.add_trace(go.Scatter(
            x=times,
            y=shadow_lengths,
            mode='lines+markers',
            name=f'{name} ({lat}°)',
            line=dict(color=color, width=2),
            marker=dict(size=4, color=color)
        ))
    
    fig.update_layout(
        title=f'不同纬度影长对比 - {date_time.strftime("%Y年%m月%d日")}',
        xaxis_title='时间 (小时)',
        yaxis_title='影长 (米)',
        template='plotly_dark',
        hovermode='x unified'
    )
    
    # 导出HTML
    project_root = Path(__file__).resolve().parent.parent
    out_html = project_root / "app/modules/modern_astronomy/pages/solar_shadow_latitude_comparison_plotly.html"
    out_html.parent.mkdir(parents=True, exist_ok=True)
    config = dict(displaylogo=False, scrollZoom=True, responsive=True)
    fig.write_html(str(out_html), include_plotlyjs='cdn', full_html=True, config=config)
    print(f"[ok] 纬度对比图表导出: {out_html}")
    
    fig.show()

# =============== 入口 ===============
if __name__ == "__main__":
    # 当前时间
    current_time = datetime.now()
    
    # 创建上海地区的影长可视化
    create_shadow_visualization(
        latitude=31.23, longitude=121.47,
        date_time=current_time, tz_name='Asia/Shanghai'
    )
    
    # 创建不同纬度对比
    create_latitude_comparison(current_time)