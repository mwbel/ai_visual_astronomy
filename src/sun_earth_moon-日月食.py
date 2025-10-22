import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from mpl_toolkits.mplot3d import Axes3D


# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] # 尝试使用Arial Unicode MS，macOS上通常可用
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

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

def calculate_lunar_ecliptic_longitude(date):
    """
    计算给定日期对应的月亮黄经。
    这里使用简化公式，假设月亮绕地球周期为27.32天。
    月亮黄经以地球为中心，相对于黄道面上的春分点。
    """
    # 简化：假设新月在春分点时与太阳同黄经 (0度)
    # 实际计算复杂，这里仅为示意
    synodic_month_days = 29.53 # 朔望月周期，用于月相
    sidereal_month_days = 27.32 # 恒星月周期，用于轨道位置

    # 假设某个基准日期（例如2000年1月1日）月亮黄经为0度
    base_date = datetime(2000, 1, 1)
    days_since_base = (date - base_date).days

    # 月亮每天约13.176度 (360 / 27.32)
    L_M = (days_since_base / sidereal_month_days) * 360
    L_M = L_M % 360
    
    return L_M

def plot_solar_orbit_zodiac(date=None):
    """
    绘制地球公转轨道示意图，包含黄道十二宫、节气、月份、月亮轨道和白道。
    """
    if date is None:
        date = datetime.now()

    L_E, L_S = calculate_ecliptic_longitude(date)
    L_M = calculate_lunar_ecliptic_longitude(date)

    # 天文常数 (简化)
    AU = 1.0  # 地球轨道半径，单位：天文单位
    MOON_ORBIT_RADIUS_SCALED = 0.27 # 月亮绕地球轨道半径，缩放后显示

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

    # 太阳 (红色圆点，居中)
    ax.plot([0], [0], [0], 'o', color='red', markersize=20, label='太阳')
    ax.text(0.05, 0.05, 0.05, '太阳', color='white', fontsize=12, ha='left', va='bottom')

    theta = np.linspace(0, 2 * np.pi, 1000)

    # 地球圆形轨道 (半径 1 AU，淡蓝色圆环)
    earth_orbit_x = AU * np.cos(theta)
    earth_orbit_y = AU * np.sin(theta)
    earth_orbit_z = np.zeros_like(theta)
    ax.plot(earth_orbit_x, earth_orbit_y, earth_orbit_z, color='lightblue', linestyle='-', linewidth=1, label='地球轨道')

    # 黄道 (黄色圆环，略大于地球轨道)
    zodiac_radius = AU * 1.2
    zodiac_x = zodiac_radius * np.cos(theta)
    zodiac_y = zodiac_radius * np.sin(theta)
    zodiac_z = np.zeros_like(theta)
    ax.plot(zodiac_x, zodiac_y, zodiac_z, color='yellow', linestyle='-', linewidth=0.5, label='黄道')

    # 当天地球所在位置 (蓝色大点标记，加文字 “地球”)
    earth_lon_rad = np.deg2rad(L_E)
    earth_x = AU * np.cos(earth_lon_rad)
    earth_y = AU * np.sin(earth_lon_rad)
    earth_z = 0
    ax.plot([earth_x], [earth_y], [earth_z], 'o', color='blue', markersize=10)
    ax.text(earth_x + 0.05, earth_y + 0.05, earth_z + 0.05, '地球', color='blue', fontsize=12, ha='left', va='bottom')

    # 太阳-地球连线，并延长到黄道外圈
    line_x = [0, zodiac_radius * np.cos(earth_lon_rad)]
    line_y = [0, zodiac_radius * np.sin(earth_lon_rad)]
    line_z = [0, 0]
    ax.plot(line_x, line_y, line_z, color='gray', linestyle='--', linewidth=0.8)

    # 月亮绕地球的轨道 (以地球为中心)
    moon_orbit_x_relative = MOON_ORBIT_RADIUS_SCALED * np.cos(theta)
    moon_orbit_y_relative = MOON_ORBIT_RADIUS_SCALED * np.sin(theta)
    moon_orbit_z_relative = np.zeros_like(theta) # 假设月亮轨道在黄道面上

    # 将月亮轨道平移到地球位置
    moon_orbit_x = earth_x + moon_orbit_x_relative
    moon_orbit_y = earth_y + moon_orbit_y_relative
    moon_orbit_z = earth_z + moon_orbit_z_relative
    ax.plot(moon_orbit_x, moon_orbit_y, moon_orbit_z, color='darkgray', linestyle=':', linewidth=0.7, label='月亮轨道')

    # 月亮实时位置 (白色点标记，加文字 “月亮”)
    # 月亮黄经 L_M 是相对于地球的，但这里为了简化，我们将其视为相对于太阳-地球连线的角度
    # 实际月亮黄经是相对于春分点，但为了在图上直观显示绕地球，我们用一个相对角度
    # 这里 L_M 已经是一个黄经，我们直接用它来定位月亮在地球轨道上的位置
    # 月亮位置的计算需要考虑地球的黄经 L_E
    moon_lon_rad = np.deg2rad(L_M) # 月亮黄经
    
    # 月亮相对于地球的位置，然后加上地球的绝对位置
    moon_x_relative = MOON_ORBIT_RADIUS_SCALED * np.cos(moon_lon_rad)
    moon_y_relative = MOON_ORBIT_RADIUS_SCALED * np.sin(moon_lon_rad)
    
    # 考虑白道倾角，月亮位置会有z轴偏移
    # 简化处理：月亮在白道上，白道相对于黄道有5.14度倾角
    # 月亮在黄道面上的投影位置
    moon_x_proj = earth_x + moon_x_relative
    moon_y_proj = earth_y + moon_y_relative
    
    # 计算月亮在白道上的z坐标
    # 假设白道倾角为5.14度，月亮在白道上的位置由L_M决定
    # 月亮在白道上的实际位置需要考虑倾角
    # 这里的L_M是月亮在黄道上的投影黄经，我们需要计算它在倾斜白道上的实际位置
    # 简化：月亮在白道上的z坐标由其在白道上的角度决定
    # 假设月亮在白道上的角度与L_M相同，但z坐标受倾角影响
    inclination_rad = np.deg2rad(5.14)
    moon_z = earth_z + MOON_ORBIT_RADIUS_SCALED * np.sin(moon_lon_rad) * np.sin(inclination_rad)
    
    # 重新计算月亮在倾斜轨道上的x, y坐标
    # 月亮在白道上的位置，以地球为中心
    # 假设月亮在白道上的角度是phi，那么x = R * cos(phi), y = R * cos(inclination) * sin(phi), z = R * sin(inclination) * sin(phi)
    # 这里我们简化为：月亮在黄道面上的投影是圆形，z轴是倾角造成的偏移
    moon_x = earth_x + MOON_ORBIT_RADIUS_SCALED * np.cos(moon_lon_rad)
    moon_y = earth_y + MOON_ORBIT_RADIUS_SCALED * np.cos(inclination_rad) * np.sin(moon_lon_rad)
    moon_z = earth_z + MOON_ORBIT_RADIUS_SCALED * np.sin(inclination_rad) * np.sin(moon_lon_rad)

    ax.plot([moon_x], [moon_y], [moon_z], 'o', color='white', markersize=7)
    ax.text(moon_x + 0.03, moon_y + 0.03, moon_z + 0.03, '月亮', color='white', fontsize=12, ha='left', va='bottom')

        # ================== 食相阴影演示 ==================
    # 阴影参数（简化）：取一条灰色圆锥体，延伸到 2AU
    shadow_length = 2.0   # 阴影延长长度（天文单位）
    shadow_radius = 0.2   # 阴影底面半径（示意用）

    # --- 日食情形：太阳 -> 月亮 阴影 ---
    # 如果月亮和太阳几乎同黄经（即新月附近），画日食阴影
    diff_angle = abs((L_M - L_S + 180) % 360 - 180)  # 日月黄经差，度
    if diff_angle < 10:  # 阈值：10° 内认为是新月食相
        # 阴影方向：太阳(0,0,0) → 月亮(moon_x, moon_y, moon_z)
        dx, dy, dz = moon_x, moon_y, moon_z
        norm = np.sqrt(dx**2 + dy**2 + dz**2)
        dx, dy, dz = dx/norm, dy/norm, dz/norm  # 单位向量

        # 圆锥底面圆心
        cx = moon_x + dx * shadow_length
        cy = moon_y + dy * shadow_length
        cz = moon_z + dz * shadow_length

        # 画圆锥侧面（用 parametric surface）
        phi = np.linspace(0, 2*np.pi, 30)
        zeta = np.linspace(0, 1, 2)
        X = np.outer(np.cos(phi), shadow_radius*zeta) + cx*np.outer(np.ones_like(phi), 1-zeta)
        Y = np.outer(np.sin(phi), shadow_radius*zeta) + cy*np.outer(np.ones_like(phi), 1-zeta)
        Z = np.outer(np.ones_like(phi), shadow_radius*zeta) + cz*np.outer(np.ones_like(phi), 1-zeta)

        ax.plot_surface(X, Y, Z, color='gray', alpha=0.3, linewidth=0)

    # --- 月食情形：太阳 -> 地球 阴影延伸到月亮 ---
    if diff_angle > 170:  # 阈值：满月附近
        dx, dy, dz = earth_x, earth_y, earth_z
        norm = np.sqrt(dx**2 + dy**2 + dz**2)
        dx, dy, dz = dx/norm, dy/norm, dz/norm

        cx = earth_x + dx * shadow_length
        cy = earth_y + dy * shadow_length
        cz = earth_z + dz * shadow_length

        phi = np.linspace(0, 2*np.pi, 30)
        zeta = np.linspace(0, 1, 2)
        X = np.outer(np.cos(phi), shadow_radius*zeta) + cx*np.outer(np.ones_like(phi), 1-zeta)
        Y = np.outer(np.sin(phi), shadow_radius*zeta) + cy*np.outer(np.ones_like(phi), 1-zeta)
        Z = np.outer(np.ones_like(phi), shadow_radius*zeta) + cz*np.outer(np.ones_like(phi), 1-zeta)

        ax.plot_surface(X, Y, Z, color='darkred', alpha=0.3, linewidth=0)

    # 绘制白道 (Lunar Path)
    # 白道相对于黄道有 ~5.14° 倾角
    # 白道以地球为中心，但其投影在太阳系坐标系中是围绕太阳的椭圆
    # 为了简化，我们将其绘制为围绕太阳的椭圆，并带有倾角
    lunar_path_radius = AU * 1.1 # 略小于黄道半径，避免重叠
    inclination_rad = np.deg2rad(5.14)
    
    ## 白道在黄道面上的投影
    #lunar_path_x_proj = lunar_path_radius * np.cos(theta)
    #lunar_path_y_proj = lunar_path_radius * np.sin(theta)
    
    ## 考虑倾角，计算z坐标
    ## 假设白道升交点在黄经0度 (春分点)
    ## 那么z坐标的变化与sin(theta)成正比
    #lunar_path_z = lunar_path_radius * np.sin(theta) * np.sin(inclination_rad)
    
    # 参数化角度 θ，代表月亮在白道上的位置
    # 黄道上的圆：x = R*cosθ, y = R*sinθ, z = 0
    # 白道上的圆：y 和 z 轴方向需要旋转倾角 i
    lunar_path_x = lunar_path_radius * np.cos(theta)
    lunar_path_y = lunar_path_radius * np.cos(inclination_rad) * np.sin(theta)
    lunar_path_z = lunar_path_radius * np.sin(inclination_rad) * np.sin(theta)
    
    # 确保等比例显示
    ax.set_box_aspect([1,1,1])
    # 改相机角度
    ax.view_init(elev=10, azim=120)

    # 绘制白道
    #ax.plot(lunar_path_x_proj, lunar_path_y_proj, lunar_path_z, color='lightgray', linestyle='-', linewidth=0.8, label='白道')
    ax.plot(
    lunar_path_x, lunar_path_y, lunar_path_z,
    color='lightgray', linestyle='-', linewidth=0.8, label='白道'
    )   
    
    # 在白道上标注 28 星宿
    constellations_28 = [
        "角", "亢", "氐", "房", "心", "尾", "箕", "斗", "牛", "女", "虚", "危", "室", "壁",
        "奎", "娄", "胃", "昴", "毕", "觜", "参", "井", "鬼", "柳", "星", "张", "翼", "轸"
    ]
    num_constellations = len(constellations_28)
    
    for i, constellation in enumerate(constellations_28):
        # 平均分布在 360° 上
        angle_deg = (i / num_constellations) * 360 + (360 / num_constellations / 2) # 标记在每个星宿的中间
        angle_rad = np.deg2rad(angle_deg)
        
        # 计算星宿在白道上的位置
        # x = R * cos(angle)
        # y = R * cos(inclination) * sin(angle)
        # z = R * sin(inclination) * sin(angle)
        
        const_x = lunar_path_radius * np.cos(angle_rad)
        const_y = lunar_path_radius * np.cos(inclination_rad) * np.sin(angle_rad)
        const_z = lunar_path_radius * np.sin(inclination_rad) * np.sin(angle_rad)
        
        ax.plot([const_x], [const_y], [const_z], '.', color='white', markersize=4)
        ax.text(const_x * 1.02, const_y * 1.02, const_z * 1.02, constellation, color='white', fontsize=8, ha='center', va='center')


    # 黄道十二宫 (12个等分点，标记为中文宫名)
    zodiac_signs_cn = [
        "白羊宫", "金牛宫", "双子宫", "巨蟹宫", "狮子宫", "处女宫",
        "天秤宫", "天蝎宫", "射手宫", "摩羯宫", "水瓶宫", "双鱼宫"
    ]
    for i, sign in enumerate(zodiac_signs_cn):
        angle_deg = i * 30 + 15
        angle_rad = np.deg2rad(angle_deg)
        
        text_x = zodiac_radius * 1.05 * np.cos(angle_rad)
        text_y = zodiac_radius * 1.05 * np.sin(angle_rad)
        text_z = 0
        ax.text(text_x, text_y, text_z, sign, color='yellow', fontsize=8, ha='center', va='center')
        
        marker_x = zodiac_radius * np.cos(angle_rad)
        marker_y = zodiac_radius * np.sin(angle_rad)
        marker_z = 0
        ax.plot([marker_x], [marker_y], [marker_z], '.', color='yellow', markersize=3)

    ## 节气点 (春分、夏至、秋分、冬至)
    #solstices_equinoxes = {
    #    '春分': (0, 'green'),
    #    '夏至': (90, 'red'),
    #    '秋分': (180, 'purple'),
    #    '冬至': (270, 'cyan')
    #}
    #for name, (angle_deg, color) in solstices_equinoxes.items():
    #    angle_rad = np.deg2rad(angle_deg)
    #    point_x = AU * np.cos(angle_rad)
    #    point_y = AU * np.sin(angle_rad)
    #    point_z = 0
    #    ax.plot([point_x], [point_y], [point_z], 'o', color=color, markersize=8)
    #    ax.text(point_x + 0.05, point_y + 0.05, point_z + 0.05, name, color=color, fontsize=10, ha='left', va='bottom')

    # 12个月份的大致位置
    months = [
        (3, '三月'), (4, '四月'), (5, '五月'), (6, '六月'),
        (7, '七月'), (8, '八月'), (9, '九月'), (10, '十月'),
        (11, '十一月'), (12, '十二月'), (1, '一月'), (2, '二月')
    ]
    
    month_angles_deg = {
        1: 300, 2: 330, 3: 0, 4: 30, 5: 60, 6: 90,
        7: 120, 8: 150, 9: 180, 10: 210, 11: 240, 12: 270
    }

    for month_num, month_name in months:
        angle_deg = month_angles_deg[month_num]
        angle_rad = np.deg2rad(angle_deg)
        
        text_x = AU * 0.9 * np.cos(angle_rad)
        text_y = AU * 0.9 * np.sin(angle_rad)
        text_z = 0
        ax.text(text_x, text_y, text_z, month_name, color='white', fontsize=9, ha='center', va='center')

    # 调整图像范围，确保所有元素可见
    # 根据黄道半径和白道倾角来设置范围
    max_radius = max(zodiac_radius, lunar_path_radius)
    ax.set_xlim(-max_radius * 1.3, max_radius * 1.3)
    ax.set_ylim(-max_radius * 1.3, max_radius * 1.3)
    ax.set_zlim(-max_radius * 1.3, max_radius * 1.3) # 将z轴范围设置为与x,y轴相同，以确保等比例显示
    ax.set_box_aspect([1,1,1]) # 保持3D视图的比例

    # 设置初始视角
    ax.view_init(elev=20, azim=-60) # 调整视角，使其更像俯视

    plt.title(f'日-地-月实时位置示意图 ({date.strftime("%Y年%m月%d日")})', color='white', fontsize=9)
    plt.show()

if __name__ == "__main__":
    # 可以指定日期，例如：
    # plot_solar_orbit_zodiac(datetime(2024, 7, 15))
    # 默认绘制当天日期
    plot_solar_orbit_zodiac()
   
    # 试试接近日食的日期（2024-04-08 是一次日全食）
    plot_solar_orbit_zodiac(datetime(2024, 4, 8))

    # 试试接近月食的日期（2025-09-07 有一次月全食）
    plot_solar_orbit_zodiac(datetime(2025, 9, 7))
