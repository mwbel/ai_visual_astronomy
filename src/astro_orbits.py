from skyfield.api import load # Skyfield 提供的加载器，用来读取星历文件（bsp 文件）
from pathlib import Path
import plotly.graph_objects as go  #Plotly 绘图库，用 go.Figure() 创建交互图。
# import os #暂时不用 

## 检查 星历文件名 de421.bsp 文件是否存在
eph_file_name = 'de421.bsp'  
eph_path = Path(__file__).parent / eph_file_name
# 为了避免 Skyfield 自动联网下载失败的情况，如果找不到 de421.bsp，就打印错误信息并退出程序。
if not eph_path.exists():
    print(f"错误：找不到文件 '{eph_file_name}'。请先把 {eph_file_name} 放在项目根目录。")
    exit()

## 从本地文件加载星历数据
planets = load(str(eph_path))
# 取出地球、火星、太阳的轨道数据。
earth, mars, sun = planets['earth'], planets['mars'], planets['sun']
# 加载时间刻度对象（Skyfield 用它来表示时间）
ts = load.timescale()

## 计算 2024 年每个月的地球和火星相对太阳的位置
# 生成 2024 年 1 月到 12 月的日期（每月 1 日）
times = ts.utc(2024, list(range(1, 13)), 1)
# 计算 地球相对太阳 在这些时间点的位置， 得到以 天文单位（AU） 表示的坐标向量（x,y,z）
earth_positions = (earth - sun).at(times).position.au  # 单位：AU
# 计算 火星相对太阳 在这些时间点的位置， 得到以 天文单位（AU） 表示的坐标向量（x,y,z）
mars_positions = (mars - sun).at(times).position.au    # 单位：AU

## 创建 Plotly 图表
fig = go.Figure()

## 添加地球轨道
fig.add_trace(go.Scatter(
    # 取出地球轨道的 X、Y 坐标
    x=earth_positions[0], y=earth_positions[1],
    # 轨迹用折线连接，并在每个点上加标记
    mode='lines+markers',
    name='地球 (每月)',
    # 鼠标悬停时显示详细信息（带单位）
    hovertemplate='<b>地球</b><br>x: %{x:.2f} AU<br>y: %{y:.2f} AU<extra></extra>'
))

## 添加火星轨道
fig.add_trace(go.Scatter(
    x=mars_positions[0], y=mars_positions[1],
    mode='lines+markers',
    name='火星 (每月)',
    hovertemplate='<b>火星</b><br>x: %{x:.2f} AU<br>y: %{y:.2f} AU<extra></extra>'
))

## 添加太阳
# 在原点 (0,0) 画一个橙色星形，表示太阳
fig.add_trace(go.Scatter(
    x=[0], y=[0],
    mode='markers',
    marker=dict(symbol='star', size=20, color='orange'),
    name='太阳',
    hovertemplate='<b>太阳</b><br>x: %{x:.2f} AU<br>y: %{y:.2f} AU<extra></extra>'
))

## 更新布局
# 设置标题、坐标轴标签、等比例缩放、网格、图例
# scaleanchor="y" 和 scaleratio=1 → 确保 x 和 y 的比例一致（轨道不被拉伸变形）
fig.update_layout(
    title="地球与火星轨道投影 (2024)",
    xaxis_title="x (AU)",
    yaxis_title="y (AU)",
    xaxis=dict(scaleanchor="y", scaleratio=1, showgrid=True), # 确保坐标等比例并显示网格
    yaxis=dict(showgrid=True),
    legend_title="天体",
    hovermode="closest"
)

## 显示图表
# 打开交互式图表（会在浏览器中显示，可缩放、悬浮查看数据）。
fig.show()
