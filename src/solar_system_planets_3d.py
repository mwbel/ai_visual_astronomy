# solar_system_planets_3d.py

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from mpl_toolkits.mplot3d import Axes3D # 导入3D绘图模块
from skyfield.api import load, Topos, EarthSatellite # 导入skyfield库
from skyfield.framelib import ecliptic_frame # 导入黄道坐标系

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] # 尝试使用Arial Unicode MS，macOS上通常可用
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

# 加载星历数据
eph = load('de421.bsp') # 确保de421.bsp文件存在于当前目录或skyfield数据目录

def calculate_ecliptic_longitude(date):
    """
    计算给定日期对应的地球黄经 L_E 和太阳视黄经 L_S。
    这里使用简化公式，假设地球轨道为圆形，且一年365天。
    春分点为黄经0度。
    """
    # 简化：假设春分点为3月21日
    vernal_equinox = datetime(date.year, 3, 21)
    days_since_vernal_equinox = (date - vernal_equinox).days

    # 调整为正值，确保在0到365之间
    if days_since_vernal_equinox < 0:
        days_since_vernal_equinox += 365.25 # 考虑闰年

    # 每天约0.986度 (360 / 365.25)
    # 地球黄经 L_E (以春分点为0度，逆时针增加)
    L_E = (days_since_vernal_equinox / 365.25) * 360

    # 太阳视黄经 L_S (与地球黄经相差180度)
    L_S = (L_E + 180) % 360
    
    return L_E, L_S

def plot_solar_system_planets_3d(date=None):
    """
    绘制太阳系行星公转示意图 (3D 交互式)。
    """
    if date is None:
        date = datetime.now()

    L_E, L_S = calculate_ecliptic_longitude(date)

    # 天文常数 (简化)
    AU = 1.0  # 地球轨道半径，单位：天文单位

    # 获取当前时间
    ts = load.timescale()
    t = ts.utc(date.year, date.month, date.day)

    # 定义行星
    sun = eph['sun']
    mercury = eph['mercury']
    venus = eph['venus']
    earth = eph['earth']
    mars = eph['mars']
    jupiter = eph['jupiter']
    saturn = eph['saturn']
    uranus = eph['uranus']
    neptune = eph['neptune']

    # 设置图像风格
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')

    # 隐藏坐标轴和网格
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])
    ax.grid(False) # 隐藏网格

    # 使坐标面透明
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('none')
    ax.yaxis.pane.set_edgecolor('none')
    ax.zaxis.pane.set_edgecolor('none')

    # 太阳 (红色圆点，居中)
    ax.plot([0], [0], [0], 'o', color='red', markersize=15, label='太阳')
    ax.text(0.05, 0.05, 0.05, '太阳', color='white', fontsize=12, ha='left', va='bottom')

    # 七大行星数据 (使用skyfield获取实时位置)
    planets_data = {
        '水星': {'obj': mercury, 'color': 'gray', 'size': 0.05},
        '金星': {'obj': venus, 'color': 'orange', 'size': 0.08},
        '地球': {'obj': earth, 'color': 'blue', 'size': 0.1},
        '火星': {'obj': mars, 'color': 'brown', 'size': 0.06},
        '木星': {'obj': jupiter, 'color': 'peru', 'size': 0.2},
        '土星': {'obj': saturn, 'color': 'goldenrod', 'size': 0.18},
        '天王星': {'obj': uranus, 'color': 'lightseagreen', 'size': 0.15},
        '海王星': {'obj': neptune, 'color': 'royalblue', 'size': 0.14}
    }

    # 绘制行星轨道和当前位置
    theta = np.linspace(0, 2 * np.pi, 1000)
    max_display_radius = 0 # 用于调整视图范围

    for planet_name, data in planets_data.items():
        planet_obj = data['obj']
        color = data['color']
        planet_size = data['size']

        # 获取行星相对于太阳的位置 (J2000坐标系)
        # 使用ecliptic_frame将坐标转换为黄道坐标系
        position = sun.at(t).observe(planet_obj).frame_xyz(ecliptic_frame).au
        
        # 行星当前位置
        planet_x, planet_y, planet_z = position.value
        
        # 计算轨道半径 (简化为当前距离)
        radius = np.sqrt(planet_x**2 + planet_y**2 + planet_z**2)
        
        # 绘制轨道 (简化为圆形轨道，实际skyfield计算的是瞬时位置)
        orbit_x = radius * np.cos(theta)
        orbit_y = radius * np.sin(theta)
        orbit_z = np.zeros_like(theta) # 假设轨道在xy平面
        ax.plot(orbit_x, orbit_y, orbit_z, color=color, linestyle=':', linewidth=0.5, label=f'{planet_name}轨道')
        
        # 绘制行星小球
        u = np.linspace(0, 2 * np.pi, 20)
        v = np.linspace(0, np.pi, 20)
        sphere_x = planet_size * np.outer(np.cos(u), np.sin(v)) + planet_x
        sphere_y = planet_size * np.outer(np.sin(u), np.sin(v)) + planet_y
        sphere_z = planet_size * np.outer(np.ones_like(u), np.cos(v)) + planet_z
        ax.plot_surface(sphere_x, sphere_y, sphere_z, color=color, alpha=0.8)
        
        # 标注行星名称
        ax.text(planet_x + planet_size * 1.5, planet_y + planet_size * 1.5, planet_z + planet_size * 1.5, planet_name, color=color, fontsize=8, ha='left', va='bottom')

        # 更新最大显示半径
        if radius > max_display_radius:
            max_display_radius = radius

    # 太阳-地球连线 (使用skyfield计算的地球实时位置)
    earth_pos = sun.at(t).observe(earth).frame_xyz(ecliptic_frame).au
    earth_x, earth_y, earth_z = earth_pos.value
    
    # 延长到黄道外圈 (这里黄道外圈将是黄道十二宫的半径)
    zodiac_outer_radius = max_display_radius * 1.1 # 黄道十二宫在最外层
    line_x = [0, zodiac_outer_radius * np.cos(np.deg2rad(L_E))] # L_E是地球黄经
    line_y = [0, zodiac_outer_radius * np.sin(np.deg2rad(L_E))]
    line_z = [0, 0]
    ax.plot(line_x, line_y, line_z, color='gray', linestyle='--', linewidth=0.8)

    # 黄道十二宫 (12个等分点，标记为中文宫名)
    zodiac_signs_cn = [
        "白羊宫", "金牛宫", "双子宫", "巨蟹宫", "狮子宫", "处女宫",
        "天秤宫", "天蝎宫", "射手宫", "摩羯宫", "水瓶宫", "双鱼宫"
    ]
    # 黄经0度对应白羊宫起点
    for i, sign in enumerate(zodiac_signs_cn):
        # 每个星座30度，从0度开始
        angle_deg = i * 30 + 15 # 标记在每个星座的中间
        angle_rad = np.deg2rad(angle_deg)
        
        text_x = zodiac_outer_radius * 1.05 * np.cos(angle_rad)
        text_y = zodiac_outer_radius * 1.05 * np.sin(angle_rad)
        text_z = 0 # 3D模式下z坐标为0
        ax.text(text_x, text_y, text_z, sign, color='yellow', fontsize=10, ha='center', va='center')
        
        # 绘制黄道上的小标记点
        marker_x = zodiac_outer_radius * np.cos(angle_rad)
        marker_y = zodiac_outer_radius * np.sin(angle_rad)
        marker_z = 0 # 3D模式下z坐标为0
        ax.plot([marker_x], [marker_y], [marker_z], '.', color='yellow', markersize=3)

    # 调整图像范围，确保所有元素可见
    max_radius = zodiac_outer_radius * 1.2 # 稍微留出一些边距
    ax.set_xlim(-max_radius, max_radius)
    ax.set_ylim(-max_radius, max_radius)
    ax.set_zlim(-max_radius * 0.1, max_radius * 0.1) # z轴可以小一些，因为轨道在xy平面
    ax.set_box_aspect([1,1,0.1]) # 保持3D视图的比例，z轴压缩

    # 设置初始视角
    ax.view_init(elev=20, azim=-60) # 调整视角，使其更像俯视

    plt.title(f'太阳系行星公转示意图 ({date.strftime("%Y年%m月%d日")})', color='white', fontsize=14)
    plt.show()

if __name__ == "__main__":
    # 可以指定日期，例如：
    # plot_solar_system_planets_3d(datetime(2024, 7, 15))
    # 默认绘制当天日期
    plot_solar_system_planets_3d()
