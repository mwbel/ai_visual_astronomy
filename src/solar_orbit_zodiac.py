import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from mpl_toolkits.mplot3d import Axes3D
import random

# 导入 Skyfield 库
from skyfield.api import load, Topos, EarthSatellite
from skyfield.timelib import Time

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC'] # 尝试使用Arial Unicode MS或苹方
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

# 加载星历数据
# 确保 de421.bsp 文件在当前目录或 skyfield_data 目录中
try:
    ephemeris = load('de421.bsp')
except FileNotFoundError:
    print("de421.bsp not found. Please download it from https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/ and place it in the current directory or skyfield_data/.")
    exit()

earth = ephemeris['earth']
sun = ephemeris['sun']
moon = ephemeris['moon']

def plot_geocentric_celestial_sphere(
    date=None,
    latitude=30.0,  # 默认观测地点：北纬30度
    longitude=120.0 # 默认观测地点：东经120度
):
    """
    绘制地心天球示意图，包含黄道、白道、太阳和月亮的周日视运动轨迹，以及星空背景。
    """
    if date is None:
        date = datetime.now()

    # Skyfield 时间对象
    ts = load.timescale()
    t = ts.utc(date.year, date.month, date.day, date.hour, date.minute, date.second)

    # 观测地点
    observer = earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude)

    # 设置图像风格
    fig = plt.figure(figsize=(12, 12))
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

    # 绘制星空背景 (随机星星)
    num_stars = 300
    star_radius = 1.5 # 星星的半径，略大于天球半径
    star_coords = np.random.rand(num_stars, 3) * 2 - 1 # 生成-1到1的随机坐标
    star_coords = star_coords / np.linalg.norm(star_coords, axis=1)[:, np.newaxis] * star_radius # 归一化并缩放到天球表面
    ax.scatter(star_coords[:, 0], star_coords[:, 1], star_coords[:, 2], s=1, color='white', alpha=0.7)

    # 天球半径 (简化为1)
    celestial_radius = 1.0
    theta = np.linspace(0, 2 * np.pi, 1000)

    # 绘制黄道 (白色圆环，作为天球赤道的参考)
    # 在地心天球视角下，黄道是太阳在天球上的路径
    # 简化：黄道在天球赤道面上，或者说我们以黄道面为参考平面
    # 实际上，黄道是地球公转轨道在天球上的投影，这里我们将其视为一个围绕地球的圆
    ecliptic_x = celestial_radius * np.cos(theta)
    ecliptic_y = celestial_radius * np.sin(theta)
    ecliptic_z = np.zeros_like(theta)
    ax.plot(ecliptic_x, ecliptic_y, ecliptic_z, color='white', linestyle='-', linewidth=1, label='黄道')

    # 绘制白道 (黄色圆环，相对黄道有 ~5.14° 倾角)
    lunar_path_radius = celestial_radius * 1.05 # 略大于黄道半径，避免重叠
    inclination_rad = np.deg2rad(5.14)
    
    # 白道在黄道面上的投影
    lunar_path_x = lunar_path_radius * np.cos(theta)
    lunar_path_y = lunar_path_radius * np.cos(inclination_rad) * np.sin(theta)
    lunar_path_z = lunar_path_radius * np.sin(inclination_rad) * np.sin(theta)
    ax.plot(lunar_path_x, lunar_path_y, lunar_path_z, color='yellow', linestyle='-', linewidth=1, label='白道')

    # 在白道上标注 28 星宿 (与之前 solar_orbit_zodiac_with_planets.py 中的逻辑相同)
    constellations_28 = [
        "角", "亢", "氐", "房", "心", "尾", "箕", "斗", "牛", "女", "虚", "危", "室", "壁",
        "奎", "娄", "胃", "昴", "毕", "觜", "参", "井", "鬼", "柳", "星", "张", "翼", "轸"
    ]
    num_constellations = len(constellations_28)
    
    for i, constellation in enumerate(constellations_28):
        angle_deg = (i / num_constellations) * 360 + (360 / num_constellations / 2)
        angle_rad = np.deg2rad(angle_deg)
        
        const_x = lunar_path_radius * np.cos(angle_rad)
        const_y = lunar_path_radius * np.cos(inclination_rad) * np.sin(angle_rad)
        const_z = lunar_path_radius * np.sin(inclination_rad) * np.sin(angle_rad)
        
        ax.plot([const_x], [const_y], [const_z], '.', color='white', markersize=4)
        ax.text(const_x * 1.02, const_y * 1.02, const_z * 1.02, constellation, color='white', fontsize=8, ha='center', va='center')

    # 计算太阳和月亮的周日视运动轨迹
    # 获取当天24小时的时间点
    times = [ts.utc(date.year, date.month, date.day, hour) for hour in range(24)]

    sun_ra_path = []
    sun_dec_path = []
    moon_ra_path = []
    moon_dec_path = []

    for current_time in times:
        # 计算太阳的地心位置
        sun_pos = observer.at(current_time).observe(sun).apparent()
        sun_ra, sun_dec, _ = sun_pos.radec()
        sun_ra_path.append(sun_ra.hours * 15) # 转换为度
        sun_dec_path.append(sun_dec.degrees)

        # 计算月亮的地心位置
        moon_pos = observer.at(current_time).observe(moon).apparent()
        moon_ra, moon_dec, _ = moon_pos.radec()
        moon_ra_path.append(moon_ra.hours * 15) # 转换为度
        moon_dec_path.append(moon_dec.degrees)

    # 将赤经赤纬转换为3D笛卡尔坐标
    # x = R * cos(dec) * cos(ra)
    # y = R * cos(dec) * sin(ra)
    # z = R * sin(dec)
    # 注意：这里ra是黄经，dec是黄纬。在天球坐标系中，通常用赤经赤纬。
    # Skyfield 提供了赤经赤纬，我们直接使用。
    # 为了在图上显示，我们需要将赤经转换为从0到360度的角度，并调整方向。
    # 假设天球的X轴指向春分点，Y轴指向春分点以东90度，Z轴指向北天极。
    # 赤经 (RA) 从0到360度，赤纬 (Dec) 从-90到90度。

    # 太阳轨迹
    sun_path_x = celestial_radius * np.cos(np.deg2rad(sun_dec_path)) * np.cos(np.deg2rad(sun_ra_path))
    sun_path_y = celestial_radius * np.cos(np.deg2rad(sun_dec_path)) * np.sin(np.deg2rad(sun_ra_path))
    sun_path_z = celestial_radius * np.sin(np.deg2rad(sun_dec_path))
    ax.plot(sun_path_x, sun_path_y, sun_path_z, color='orange', linestyle='-', linewidth=1.5, label='太阳轨迹')

    # 月亮轨迹
    moon_path_x = celestial_radius * np.cos(np.deg2rad(moon_dec_path)) * np.cos(np.deg2rad(moon_ra_path))
    moon_path_y = celestial_radius * np.cos(np.deg2rad(moon_dec_path)) * np.sin(np.deg2rad(moon_ra_path))
    moon_path_z = celestial_radius * np.sin(np.deg2rad(moon_dec_path)) # 修正：月亮z坐标
    ax.plot(moon_path_x, moon_path_y, moon_path_z, color='lightblue', linestyle='-', linewidth=1.5, label='月亮轨迹')

    # 标注当前时刻的太阳和月亮位置
    current_sun_pos = observer.at(t).observe(sun).apparent()
    current_sun_ra, current_sun_dec, _ = current_sun_pos.radec()
    current_sun_x = celestial_radius * np.cos(current_sun_dec.radians) * np.cos(current_sun_ra.radians)
    current_sun_y = celestial_radius * np.cos(current_sun_dec.radians) * np.sin(current_sun_ra.radians)
    current_sun_z = celestial_radius * np.sin(current_sun_dec.radians)
    ax.plot([current_sun_x], [current_sun_y], [current_sun_z], 'o', color='orange', markersize=10)
    ax.text(current_sun_x * 1.1, current_sun_y * 1.1, current_sun_z * 1.1, '太阳', color='orange', fontsize=12, ha='center', va='center')

    current_moon_pos = observer.at(t).observe(moon).apparent()
    current_moon_ra, current_moon_dec, _ = current_moon_pos.radec()
    current_moon_x = celestial_radius * np.cos(current_moon_dec.radians) * np.cos(current_moon_ra.radians)
    current_moon_y = celestial_radius * np.cos(current_moon_dec.radians) * np.sin(current_moon_ra.radians)
    current_moon_z = celestial_radius * np.sin(current_moon_dec.radians)
    ax.plot([current_moon_x], [current_moon_y], [current_moon_z], 'o', color='white', markersize=7) # 月亮颜色为白色
    ax.text(current_moon_x * 1.1, current_moon_y * 1.1, current_moon_z * 1.1, '月亮', color='white', fontsize=10, ha='center', va='center')

    # 调整图像范围，确保所有元素可见
    ax.set_xlim([-celestial_radius * 1.6, celestial_radius * 1.6])
    ax.set_ylim([-celestial_radius * 1.6, celestial_radius * 1.6])
    ax.set_zlim([-celestial_radius * 1.6, celestial_radius * 1.6])
    ax.set_box_aspect([1,1,1]) # 保持3D视图的比例

    # 设置初始视角
    ax.view_init(elev=30, azim=-90) # 调整视角，使其更像从侧面俯视天球

    plt.title(f'地心天球示意图 ({date.strftime("%Y年%m月%d日 %H:%M:%S")})\n观测地点: {latitude}°N, {longitude}°E', color='white', fontsize=14)
    plt.show()

if __name__ == "__main__":
    # 示例：绘制当天实时时间，默认经纬度
    plot_geocentric_celestial_sphere()

    # 示例：指定日期和经纬度
    # plot_geocentric_celestial_sphere(datetime(2024, 7, 15, 12, 0, 0), latitude=34.0, longitude=108.0)
