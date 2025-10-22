import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime, timedelta
import requests
import math

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] # 尝试使用Arial Unicode MS，macOS上通常可用
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题


# Helper functions for degree-based trigonometric operations
def sind(angle_deg):
    return math.sin(math.radians(angle_deg))

def cosd(angle_deg):
    return math.cos(math.radians(angle_deg))

def tand(angle_deg):
    return math.tan(math.radians(angle_deg))

def asind(value):
    return math.degrees(math.asin(value))

def atan2d(y, x):
    return math.degrees(math.atan2(y, x))

def vecnorm(v):
    return np.linalg.norm(v, axis=0)

# %% 输入参数
# 设置观测点（半球、经度、纬度)
hemisphere = '北半球'  # 北半球
# hemisphere = '南半球'  # 南半球
longitude = 121.47  # 当地经度,单位为度,e.g, 北京
latitude = 31.23  # 当地纬度，单位为度
if hemisphere == '南半球':
    latitude = -latitude  # 南半球纬度为负

# 查询日期（年月日）
dates_str = '2025-01-21'
dt = datetime.strptime(dates_str, '%Y-%m-%d')

year = dt.year
month = dt.month
day = dt.day

# 方式二：直接调用API 获取当地日落日出时间和赤纬角，目前需用到两个API：Sunrise-Sunset API和 NASA JPL Horizons API

# Sunrise-Sunset API 有日出日落数据，但没有正午赤纬角数据
url = f'https://api.sunrise-sunset.org/json?lat={latitude:.2f}&lng={longitude:.2f}&date={dates_str}&formatted=0'

# 读取 sunrise-sunset API 数据
try:
    response = requests.get(url)
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"Error fetching data from Sunrise-Sunset API: {e}")
    data = None

sunrise_UTC_str = data['results']['sunrise'] if data else None
sunset_UTC_str = data['results']['sunset'] if data else None

# 处理时区转换
timezone_offset = 8  # 例如，北京时间（GMT+8）

if sunrise_UTC_str and sunset_UTC_str:
    sunrise_UTC = datetime.strptime(sunrise_UTC_str.replace('+00:00', ''), '%Y-%m-%dT%H:%M:%S').replace(tzinfo=None)
    sunset_UTC = datetime.strptime(sunset_UTC_str.replace('+00:00', ''), '%Y-%m-%dT%H:%M:%S').replace(tzinfo=None)

    # 日照时长
    duration = sunset_UTC - sunrise_UTC

    # 计算太阳中天时间 (UTC) —— 使用 duration 进行计算
    solar_noon_UTC = sunrise_UTC + duration / 2

    # 以上结果是格林威治时间（UTC时间)
    # 加上时区偏移量，将结果转换为地方时间(LT)
    # 转换为地方时间 (UTC+8)
    sunrise_LT = sunrise_UTC + timedelta(hours=timezone_offset)
    sunset_LT = sunset_UTC + timedelta(hours=timezone_offset)
    solar_noon_LT = solar_noon_UTC + timedelta(hours=timezone_offset)
else:
    print("Could not retrieve sunrise/sunset data. Using dummy values.")
    sunrise_LT = datetime(year, month, day, 6, 0, 0) + timedelta(hours=timezone_offset)
    sunset_LT = datetime(year, month, day, 18, 0, 0) + timedelta(hours=timezone_offset)
    solar_noon_LT = datetime(year, month, day, 12, 0, 0) + timedelta(hours=timezone_offset)
    duration = sunset_LT - sunrise_LT


# 调用API，获得月出和月落时间，目前是直接查的Swiss Ephemeris
# Matlab代码中是硬编码的，这里也硬编码
moonrise_LT_str = '2025-02-04 10:06'
moonrise_LT = datetime.strptime(moonrise_LT_str, '%Y-%m-%d %H:%M')
moonset_LT_str = '2025-02-04 23:50'
moonset_LT = datetime.strptime(moonset_LT_str, '%Y-%m-%d %H:%M')

# 输出结果
print(f'观测地点：经度: {longitude:.2f}°, 纬度: {latitude:.2f}°')
print(f'观测日期: {dates_str}')
print(f'日出时间 (当地时间): {sunrise_LT.strftime("%H:%M:%S")}')
print(f'日落时间 (当地时间): {sunset_LT.strftime("%H:%M:%S")}')
print(f'日照时长: {str(duration).split(".")[0]}') # Remove microseconds
print(f'太阳中天时间 (当地时间): {solar_noon_LT.strftime("%H:%M:%S")}')
print(f'月出时间: {moonrise_LT.strftime("%H:%M:%S")}')
print(f'月落时间: {moonset_LT.strftime("%H:%M:%S")}')

# 这一版本中，运用更高精度的天文学计算来计算赤纬角
# δ=arcsin(sin(epsilon)×sin(L_sun))
# 其中：
# epsilon = 23.4393° − 0.0000004 × T (黄赤交角，T为儒略世纪)
# L0 为 太阳的平均黄经，计算方法如下
# L0 =280.46646+36000.76983×T+0.0003032×T^2
# 其中，280.46646° 是 2000.0 纪元的太阳黄经

# 计算UTC 12:00 时刻的儒略日 JD
# Matlab的JD计算公式：367 * year - floor((7 * (year + floor((month + 9) / 12))) / 4) + floor((275 * month) / 9) + day + 1721013.5;
# Python datetime to Julian Day
def date_to_jd(year, month, day, hour=12, minute=0, second=0):
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    JD = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5
    # Add fractional day for UTC 12:00
    JD += (hour - 12) / 24 + minute / 1440 + second / 86400
    return JD

JD = date_to_jd(year, month, day)

# 计算儒略世纪数 T,即从 2000 年 1 月 1 日 12:00 UTC 开始计算
T = (JD - 2451545.0) / 36525  # 2451545是2000年1月1日UT12:00的儒略日。

# NASA / NOAA 标准计算太阳黄经 (L_sun)
L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T**2  # 平均黄经
M = 357.52911 + 35999.05029 * T - 0.0001537 * T**2  # 平均近点角

# 地球轨道偏心率修正
C = (1.914602 - 0.004817 * T - 0.000014 * T**2) * sind(M) \
  + (0.019993 - 0.000101 * T) * sind(2*M) \
  + 0.000289 * sind(3*M)

L_sun = L0 + C  # 太阳的真实黄经
L_sun = L_sun % 360  # 归一化到 0-360°

# 计算黄赤交角 (epsilon)
epsilon = 23.4393 - 0.0000004 * T

# 计算太阳赤纬角 (delta)
delta = asind(sind(epsilon) * sind(L_sun))
print(f'更精确的太阳赤纬角: {delta:.6f}°')

# %% 绘制地平坐标系
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect([1,1,1]) # Equal aspect ratio

# 设置坐标轴范围
ax.set_xlim([-1.3, 1.3])
ax.set_ylim([-1.3, 1.3])
ax.set_zlim([-1.3, 1.3])

#ax.set_xlabel('X')
#ax.set_ylabel('Y')
#ax.set_zlabel('Z')
ax.grid(True)

# 绘制基本坐标轴
# ax.quiver(-1.5, 0, 0, 3, 0, 0, color='c', linewidth=2) # X 轴（东）
# ax.quiver(0, -1.5, 0, 0, 3, 0, color='g', linewidth=2) # Y 轴（北）
ax.quiver(0, 0, -1.5, 0, 0, 3, color='r', linewidth=2) # Z 轴（天顶）
ax.text(0, 0, 1.6, '天顶', fontsize=12, color='r')
ax.text(0, 0, -1.6, '天底', fontsize=12, color='r')

# 添加坐标轴标签 x, y, z
#ax.text(1.4, 0, 0, 'X', fontsize=12, color='c') # X 轴（东）
#ax.text(0, 1.4, 0, 'Y', fontsize=12, color='g') # Y 轴（北）
#ax.text(0, 0, 1.4, 'Z', fontsize=12, color='r') # Z 轴（上）

# 添加图示标题，位置靠近左侧天球
title_text = f'{hemisphere} (经度: {longitude:.2f}°, 纬度: {latitude:.2f}°) - {year} 年 {month} 月 {day} 日 太阳周日视运动图'
ax.set_title(title_text, fontsize=14, fontweight='bold', color='y', y=0.95) # Adjust y to move title up

# %% 创建一个高分辨率的单位球面
n = 20  # 生成的点数，增加点数可以提高分辨率
u = np.linspace(0, 2 * np.pi, n)
v = np.linspace(0, np.pi, n)
x = np.outer(np.cos(u), np.sin(v))
y = np.outer(np.sin(u), np.sin(v))
z = np.outer(np.ones(np.size(u)), np.cos(v))
ax.plot_surface(x, y, z, color='none', edgecolor=[0.2, 0.2, 0.2], alpha=0)

# 设置背景为黑色
ax.set_facecolor((0, 0, 0))
fig.patch.set_facecolor((0, 0, 0))

# 隐藏坐标轴和刻度
ax.set_xticks([])
ax.set_yticks([])
ax.set_zticks([])
ax.set_xticklabels([])
ax.set_yticklabels([])
ax.set_zticklabels([])

# 隐藏坐标轴线
ax.xaxis.line.set_color((0,0,0,0))
ax.yaxis.line.set_color((0,0,0,0))
ax.zaxis.line.set_color((0,0,0,0))

# 隐藏坐标面
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False
ax.xaxis.pane.set_edgecolor('none')
ax.yaxis.pane.set_edgecolor('none')
ax.zaxis.pane.set_edgecolor('none')

# %% 绘制地平坐标系中的地平面
theta_circle = np.linspace(2 * np.pi, 0, 360)  # 从2π到0（逆时针/自西向东)生成参数化角度
r = 1  # 单位球的半径
x_plane = r * np.cos(theta_circle)
y_plane = r * np.sin(theta_circle)
z_plane = np.zeros_like(theta_circle)

# 填充赤道面为浅灰色
ax.plot_surface(x_plane.reshape(1, -1), y_plane.reshape(1, -1), z_plane.reshape(1, -1), color=[0.4, 0.4, 0.4], alpha=0.4)
# 画地平圈
ax.plot(x_plane, y_plane, z_plane, color=[0.8, 0.8, 0.8], linewidth=5)

# %% 赤道大圆上绘制8个方位点
orientation_divisions = 8
theta_divisions = np.linspace(0, 2 * np.pi, orientation_divisions + 1)[:-1] # Exclude last point to avoid duplicate 0/360
orientation_labels = ['东', '东北', '北', '西北', '西', '西南', '南', '东南']

for i in range(orientation_divisions):
    x_point = r * np.cos(theta_divisions[i])
    y_point = r * np.sin(theta_divisions[i])
    z_point = 0
    ax.plot([x_point], [y_point], [z_point], 'co', markersize=8, markerfacecolor='w')
    ax.text(1.2 * x_point, 1.2 * y_point, z_point, orientation_labels[i], fontsize=12, color='w', ha='center')

# %% 绘制天极
north_pole_vec = np.array([0, sind(latitude), cosd(latitude)]) # Matlab's north_pole was 1.5*[0, cosd(latitude), sind(latitude)]
# Adjusting to unit vector for rotation calculation, then scaling for plotting
north_pole_plot = 1.5 * north_pole_vec / np.linalg.norm(north_pole_vec)
south_pole_plot = -north_pole_plot

# 绘制天轴（球心到北天极的连线）
ax.plot([south_pole_plot[0], north_pole_plot[0]],
        [south_pole_plot[1], north_pole_plot[1]],
        [south_pole_plot[2], north_pole_plot[2]], 'w--', linewidth=2)

# 标注北天极
ax.plot([north_pole_plot[0]], [north_pole_plot[1]], [north_pole_plot[2]], 'wo', markersize=8, markerfacecolor='w')
ax.text(north_pole_plot[0] * 1.1, north_pole_plot[1] * 1.1, north_pole_plot[2] * 1.1, '北天极', fontsize=12, color='w')
# 标注南天极
ax.plot([south_pole_plot[0]], [south_pole_plot[1]], [south_pole_plot[2]], 'wo', markersize=8, markerfacecolor='w')
ax.text(south_pole_plot[0] * 1.1, south_pole_plot[1] * 1.1, south_pole_plot[2] * 1.1, '南天极', fontsize=12, color='w')

# %% 绘制当地当日太阳周日视运动轨迹
seconds_division = 86400
time_theta = np.linspace(2 * np.pi, 0, seconds_division)
d = r * sind(delta)  # 纬圈的垂直偏移量
circle_radius = math.sqrt(r**2 - d**2) if r**2 - d**2 >= 0 else 0 # Ensure non-negative for sqrt

x_circle = circle_radius * np.cos(time_theta)
y_circle = circle_radius * np.sin(time_theta)
z_circle = np.full_like(time_theta, d)

# 计算旋转矩阵，使纬圈垂直于天轴
z_axis = np.array([0, 0, 1])
# Use the unit vector for north_pole for rotation calculation
north_pole_unit = north_pole_vec / np.linalg.norm(north_pole_vec)

axis_rotation = np.cross(z_axis, north_pole_unit)
if np.linalg.norm(axis_rotation) != 0:
    axis_rotation = axis_rotation / np.linalg.norm(axis_rotation)
else: # If z_axis and north_pole_unit are parallel (e.g., at poles)
    axis_rotation = np.array([1, 0, 0]) # Arbitrary axis, rotation_angle will be 0 or pi

rotation_angle = np.arccos(np.dot(z_axis, north_pole_unit))

# Rodrigues 旋转公式
K = np.array([[0, -axis_rotation[2], axis_rotation[1]],
              [axis_rotation[2], 0, -axis_rotation[0]],
              [-axis_rotation[1], axis_rotation[0], 0]])
R = np.eye(3) + np.sin(rotation_angle) * K + (1 - np.cos(rotation_angle)) * (K @ K)

# 旋转纬圈
circle_coords = np.vstack([x_circle, y_circle, z_circle])
rotated_circle = R @ circle_coords
x_circle_rotated = rotated_circle[0, :]
y_circle_rotated = rotated_circle[1, :]
z_circle_rotated = rotated_circle[2, :]

# 纬圈圆心
rotated_center = R @ np.array([0, 0, d])

# 可见性判断
visible_idx = z_circle_rotated >= 0
invisible_idx = ~visible_idx

# 绘制太阳周日视运动轨迹
ax.plot(x_circle_rotated[visible_idx], y_circle_rotated[visible_idx], z_circle_rotated[visible_idx], 'y-', linewidth=2.5)
ax.plot(x_circle_rotated[invisible_idx], y_circle_rotated[invisible_idx], z_circle_rotated[invisible_idx], 'y--', linewidth=2.5)

# 绘制纬圈最高点（z 值最大点）---太阳上中天，正午最高点
max_z_idx = np.argmax(z_circle_rotated)
highest_point = np.array([x_circle_rotated[max_z_idx], y_circle_rotated[max_z_idx], z_circle_rotated[max_z_idx]])
ax.plot([highest_point[0]], [highest_point[1]], [highest_point[2]], 'ro', markersize=8, markerfacecolor='r')

# 绘制纬圈最低点（z 值最小点）---太阳下中天，午夜12点
min_z_idx = np.argmin(z_circle_rotated)
lowest_point = np.array([x_circle_rotated[min_z_idx], y_circle_rotated[min_z_idx], z_circle_rotated[min_z_idx]])
ax.plot([lowest_point[0]], [lowest_point[1]], [lowest_point[2]], 'ro', markersize=8, markerfacecolor='r')

# 绘制纬圈圆心到最高点的连线
ax.plot([rotated_center[0], highest_point[0]],
        [rotated_center[1], highest_point[1]],
        [rotated_center[2], highest_point[2]], 'w--', linewidth=2)

# 绘制球心到纬圈最高点的连线 (Matlab code seems to connect lowest to highest, which is a diameter)
ax.plot([lowest_point[0], highest_point[0]],
        [lowest_point[1], highest_point[1]],
        [lowest_point[2], highest_point[2]], 'y--', linewidth=2)

# %% 计算日出日落点，即纬圈上 z=0 的两个点
# Find indices where z_circle_rotated crosses zero
# Using a simple threshold for finding points near zero
z_zero_indices = np.where(np.abs(z_circle_rotated) < 1e-4)[0]

if len(z_zero_indices) >= 2:
    # Sort by absolute z value to get the closest two points to z=0
    sorted_indices = z_zero_indices[np.argsort(np.abs(z_circle_rotated[z_zero_indices]))]
    
    # Select the two points closest to z=0
    selected_z_zero_indices = sorted_indices[:2]

    x_zero = x_circle_rotated[selected_z_zero_indices]
    y_zero = y_circle_rotated[selected_z_zero_indices]
    z_zero = z_circle_rotated[selected_z_zero_indices]

    sunrise_point = None
    sunset_point = None

    for i in range(len(x_zero)):
        if x_zero[i] > 0: # East is positive X
            sunrise_point = np.array([x_zero[i], y_zero[i], z_zero[i]])
            ax.plot([x_zero[i]], [y_zero[i]], [z_zero[i]], 'go', markersize=8, markerfacecolor='g')
            ax.text(x_zero[i] * 1.1, y_zero[i] * 1.1, z_zero[i], '日出点', fontsize=12, color='g')
        else: # West is negative X
            sunset_point = np.array([x_zero[i], y_zero[i], z_zero[i]])
            ax.plot([x_zero[i]], [y_zero[i]], [z_zero[i]], 'ro', markersize=8, markerfacecolor='r')
            ax.text(x_zero[i] * 1.1, y_zero[i] * 1.1, z_zero[i], '日落点', fontsize=12, color='r')
else:
    print("Could not find distinct sunrise/sunset points for the sun.")
    sunrise_point = np.array([0,0,0]) # Dummy
    sunset_point = np.array([0,0,0]) # Dummy


# %% 计算并标记太阳轨迹上的整点：以日出点为起算点
if sunrise_point is not None:
    sunrise_hours = sunrise_LT.hour + sunrise_LT.minute / 60 + sunrise_LT.second / 3600
    start_hour = math.ceil(sunrise_hours)
    hour_labels = np.array([(start_hour + i) % 24 for i in range(24)])

    delta_T = start_hour - sunrise_hours
    delta_HA = delta_T * 15 # 每小时太阳时角变化 15°

    # 找到日出点的索引
    # Matlab's vecnorm([x_circle_rotated - sunrise(1); ...]) is equivalent to np.linalg.norm(coords - sunrise_point.reshape(-1,1), axis=0)
    coords_for_norm = np.vstack([x_circle_rotated, y_circle_rotated, z_circle_rotated])
    first_index = np.argmin(np.linalg.norm(coords_for_norm - sunrise_point.reshape(-1, 1), axis=0))

    num_samples = len(x_circle_rotated)
    samples_per_degree = num_samples / 360
    offset = round(delta_HA * samples_per_degree)

    hour_step = round(15 * samples_per_degree)
    hour_indices = (first_index + offset + np.arange(24) * hour_step) % num_samples

    for i in range(24):
        idx = int(hour_indices[i])
        ax.plot([x_circle_rotated[idx]], [y_circle_rotated[idx]], [z_circle_rotated[idx]], 'ro', markersize=10, markerfacecolor='y')

        # if hour_labels[i] == 0:
        #    time_label = '12 AM'
        # elif hour_labels[i] < 12:
        #    time_label = f'{int(hour_labels[i])} AM'
        # elif hour_labels[i] == 12:
        #    time_label = '12 PM'
        # else:
        #    time_label = f'{int(hour_labels[i]) - 12} PM'
        time_label = f'{int(hour_labels[i])} h'

        ax.text(x_circle_rotated[idx] * 1.2, y_circle_rotated[idx] * 1.2, z_circle_rotated[idx], time_label,
                fontsize=10, color='w', ha='center')
else:
    print("Sunrise point not found, skipping hourly markers for sun.")

# %% 2️⃣ **计算月亮赤纬角 (δ_moon)**
# 月球的平均轨道参数
L_moon = 218.316 + 481267.8813 * T  # 月球的平均黄经
M_moon = 134.963 + 477198.8676 * T  # 月球的平近点角
D_moon = 297.850 + 445267.1115 * T  # 日月角距
F_moon = 93.272 + 483202.0175 * T   # 月球升交点距

# 计算月球黄经的摄动修正
L_moon_corr = L_moon \
    + 6.289 * sind(M_moon) \
    + 1.274 * sind(2*D_moon - M_moon) \
    + 0.658 * sind(2*D_moon) \
    + 0.214 * sind(2*M_moon) \
    + 0.11 * sind(D_moon)

# 黄赤交角 (epsilon already calculated)

# 计算月球赤纬角 δ_moon
delta_moon = asind(sind(epsilon) * sind(L_moon_corr))
print(f'更精确的月亮赤纬角: {delta_moon:.6f}°')

# %% 绘制当地当日月亮周日视运动轨迹
seconds_division_moon = 86400
time_theta_moon = np.linspace(2 * np.pi, 0, seconds_division_moon)
d_moon = r * sind(delta_moon)
circle_radius_moon = math.sqrt(r**2 - d_moon**2) if r**2 - d_moon**2 >= 0 else 0

x_circle_moon = circle_radius_moon * np.cos(time_theta_moon)
y_circle_moon = circle_radius_moon * np.sin(time_theta_moon)
z_circle_moon = np.full_like(time_theta_moon, d_moon)

# 旋转纬圈，使其垂直于天轴 (using the same R matrix as for the sun, as the celestial pole is the same)
circle_coords_moon = np.vstack([x_circle_moon, y_circle_moon, z_circle_moon])
rotated_circle_moon = R @ circle_coords_moon
x_circle_rotated_moon = rotated_circle_moon[0, :]
y_circle_rotated_moon = rotated_circle_moon[1, :]
z_circle_rotated_moon = rotated_circle_moon[2, :]

# 纬圈圆心
rotated_center_moon = R @ np.array([0, 0, d_moon])

# 可见性判断
visible_idx_moon = z_circle_rotated_moon >= 0
invisible_idx_moon = ~visible_idx_moon

# 绘制月亮周日视运动轨迹
ax.plot(x_circle_rotated_moon[visible_idx_moon], y_circle_rotated_moon[visible_idx_moon], z_circle_rotated_moon[visible_idx_moon], 'g-', linewidth=2.5)
ax.plot(x_circle_rotated_moon[invisible_idx_moon], y_circle_rotated_moon[invisible_idx_moon], z_circle_rotated_moon[invisible_idx_moon], 'g--', linewidth=2.5)

# 绘制纬圈最高点（z 值最大点）---月亮上中天
max_z_idx_moon = np.argmax(z_circle_rotated_moon)
highest_point_moon = np.array([x_circle_rotated_moon[max_z_idx_moon], y_circle_rotated_moon[max_z_idx_moon], z_circle_rotated_moon[max_z_idx_moon]])
ax.plot([highest_point_moon[0]], [highest_point_moon[1]], [highest_point_moon[2]], 'ro', markersize=8, markerfacecolor='r')

# 绘制纬圈最低点（z 值最小点）---月亮下中天
min_z_idx_moon = np.argmin(z_circle_rotated_moon)
lowest_point_moon = np.array([x_circle_rotated_moon[min_z_idx_moon], y_circle_rotated_moon[min_z_idx_moon], z_circle_rotated_moon[min_z_idx_moon]])
ax.plot([lowest_point_moon[0]], [lowest_point_moon[1]], [lowest_point_moon[2]], 'ro', markersize=8, markerfacecolor='r')

# 绘制纬圈圆心到最高点的连线
ax.plot([rotated_center_moon[0], highest_point_moon[0]],
        [rotated_center_moon[1], highest_point_moon[1]],
        [rotated_center_moon[2], highest_point_moon[2]], 'w--', linewidth=2)

# 绘制球心到纬圈最高点的连线 (Matlab code seems to connect lowest to highest, which is a diameter)
ax.plot([lowest_point_moon[0], highest_point_moon[0]],
        [lowest_point_moon[1], highest_point_moon[1]],
        [lowest_point_moon[2], highest_point_moon[2]], 'y--', linewidth=2)

# %% 计算月出月落点
z_zero_indices_moon = np.where(np.abs(z_circle_rotated_moon) < 1e-4)[0]

if len(z_zero_indices_moon) >= 2:
    sorted_indices_moon = z_zero_indices_moon[np.argsort(np.abs(z_circle_rotated_moon[z_zero_indices_moon]))]
    selected_z_zero_indices_moon = sorted_indices_moon[:2]

    x_zero_moon = x_circle_rotated_moon[selected_z_zero_indices_moon]
    y_zero_moon = y_circle_rotated_moon[selected_z_zero_indices_moon]
    z_zero_moon = z_circle_rotated_moon[selected_z_zero_indices_moon]

    moonrise_point = None
    moonset_point = None

    for i in range(len(x_zero_moon)):
        if x_zero_moon[i] > 0: # East is positive X
            moonrise_point = np.array([x_zero_moon[i], y_zero_moon[i], z_zero_moon[i]])
            ax.plot([x_zero_moon[i]], [y_zero_moon[i]], [z_zero_moon[i]], 'go', markersize=8, markerfacecolor='g')
            ax.text(x_zero_moon[i] * 1.1, y_zero_moon[i] * 1.1, z_zero_moon[i], '月出点', fontsize=12, color='g')
        else: # West is negative X
            moonset_point = np.array([x_zero_moon[i], y_zero_moon[i], z_zero_moon[i]])
            ax.plot([x_zero_moon[i]], [y_zero_moon[i]], [z_zero_moon[i]], 'ro', markersize=8, markerfacecolor='r')
            ax.text(x_zero_moon[i] * 1.1, y_zero_moon[i] * 1.1, z_zero_moon[i], '月落点', fontsize=12, color='r')
else:
    print("Could not find distinct moonrise/moonset points for the moon.")
    moonrise_point = np.array([0,0,0]) # Dummy
    moonset_point = np.array([0,0,0]) # Dummy

# %% 计算并标记月亮轨迹上的整点：以月出点为起算点
if moonrise_point is not None:
    moonrise_hours = moonrise_LT.hour + moonrise_LT.minute / 60 + moonrise_LT.second / 3600
    start_hour_moon = math.ceil(moonrise_hours)
    hour_labels_moon = np.array([(start_hour_moon + i) % 24 for i in range(24)])

    delta_T_moon = start_hour_moon - moonrise_hours
    delta_HA_moon = delta_T_moon * 15

    coords_for_norm_moon = np.vstack([x_circle_rotated_moon, y_circle_rotated_moon, z_circle_rotated_moon])
    first_index_moon = np.argmin(np.linalg.norm(coords_for_norm_moon - moonrise_point.reshape(-1, 1), axis=0))

    num_samples_moon = len(x_circle_rotated_moon)
    samples_per_degree_moon = num_samples_moon / 360
    offset_moon = round(delta_HA_moon * samples_per_degree_moon)

    hour_step_moon = round(15 * samples_per_degree_moon)
    hour_indices_moon = (first_index_moon + offset_moon + np.arange(24) * hour_step_moon) % num_samples_moon

    for i in range(24):
        idx_moon = int(hour_indices_moon[i])
        ax.plot([x_circle_rotated_moon[idx_moon]], [y_circle_rotated_moon[idx_moon]], [z_circle_rotated_moon[idx_moon]], 'ro', markersize=10, markerfacecolor='g')

        # if hour_labels_moon[i] == 0:
        #    time_label_moon = '12 AM'
        # elif hour_labels_moon[i] < 12:
        #    time_label_moon = f'{int(hour_labels_moon[i])} AM'
        # elif hour_labels_moon[i] == 12:
        #    time_label_moon = '12 PM'
        #else:
        #    time_label_moon = f'{int(hour_labels_moon[i]) - 12} PM'
        time_label_moon = f'{int(hour_labels_moon[i])} h'

        ax.text(x_circle_rotated_moon[idx_moon] * 1.2, y_circle_rotated_moon[idx_moon] * 1.2, z_circle_rotated_moon[idx_moon], time_label_moon,
                fontsize=10, color='w', ha='center')
else:
    print("Moonrise point not found, skipping hourly markers for moon.")


# %% 设置观察角
ax.view_init(elev=20, azim=90) # elev is elevation, azim is azimuth

# Use camzoom to zoom in (matplotlib equivalent is setting limits or adjusting figure size)
# For a fixed view, adjusting limits or figure size is more direct.
# ax.set_xlim([-0.8, 0.8])
# ax.set_ylim([-0.8, 0.8])
# ax.set_zlim([-0.8, 0.8])

plt.show()
