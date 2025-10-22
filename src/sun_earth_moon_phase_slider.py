# -*- coding: utf-8 -*-
"""
sun_earth_moon_phase_slider.py

交互式 3D 模型，展示太阳、地球和带月相效果的月亮。
"""

import numpy as np
import plotly.graph_objects as go
from skyfield.api import load, Topos
from datetime import datetime, date, timedelta
import pytz
import argparse

DEFAULT_LATITUDE = 31.23
DEFAULT_LONGITUDE = 121.47
DEFAULT_TIMEZONE = 'Asia/Shanghai'
DEFAULT_YEAR = datetime.now().year
DEFAULT_HOUR = datetime.now().hour
DEFAULT_MINUTE = datetime.now().minute
DEFAULT_RADIUS = 1.0


# --- 工具函数 ---
def _spherical_to_cartesian(az_deg, alt_deg, radius=DEFAULT_RADIUS):
    az_rad = np.radians(az_deg)
    alt_rad = np.radians(alt_deg)
    x = radius * np.cos(alt_rad) * np.sin(az_rad)
    y = radius * np.cos(alt_rad) * np.cos(az_rad)
    z = radius * np.sin(alt_rad)
    return x, y, z


def get_ephem_body(ephemeris, name):
    try:
        return ephemeris[name]
    except KeyError:
        return ephemeris[f"{name} barycenter"]


def compute_body_point_for_date(body, observer, ts, local_date, tz_name, hour, minute,
                                radius=DEFAULT_RADIUS):
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime(local_date.year, local_date.month, local_date.day, hour, minute))
    utc_dt = local_dt.astimezone(pytz.utc)
    t = ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)

    pos = sun.at(t).observe(body).position.au  # 相对太阳的坐标
    x, y, z = pos
    return x, y, z


# --- 月亮球体绘制函数（带月相） ---
def add_moon_with_phase(fig, moon_pos, sun_pos, radius=0.08, resolution=40):
    u = np.linspace(0, 2*np.pi, resolution)
    v = np.linspace(0, np.pi, resolution)
    xs = radius * np.outer(np.cos(u), np.sin(v)) + moon_pos[0]
    ys = radius * np.outer(np.sin(u), np.sin(v)) + moon_pos[1]
    zs = radius * np.outer(np.ones_like(u), np.cos(v)) + moon_pos[2]

    sun_dir = np.array(sun_pos) - np.array(moon_pos)
    sun_dir = sun_dir / np.linalg.norm(sun_dir)

    normals = np.stack([xs - moon_pos[0], ys - moon_pos[1], zs - moon_pos[2]], axis=-1)
    norms = np.linalg.norm(normals, axis=-1, keepdims=True)
    normals = normals / np.clip(norms, 1e-8, None)

    intensity = np.sum(normals * sun_dir, axis=-1)
    intensity = np.clip(intensity, 0, 1)

    colorscale = [[0, "rgb(20,20,20)"], [1, "rgb(230,230,230)"]]

    fig.add_surface(
        x=xs, y=ys, z=zs,
        surfacecolor=intensity,
        colorscale=colorscale,
        cmin=0, cmax=1,
        showscale=False,
        name="月亮(月相)",
    )


# --- 主逻辑 ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, default=DEFAULT_LATITUDE)
    parser.add_argument("--lon", type=float, default=DEFAULT_LONGITUDE)
    parser.add_argument("--tz", type=str, default=DEFAULT_TIMEZONE)
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument("--hour", type=int, default=DEFAULT_HOUR)
    parser.add_argument("--minute", type=int, default=DEFAULT_MINUTE)
    args = parser.parse_args()

    ts = load.timescale()
    ephemeris = load('de421.bsp')
    earth = ephemeris['earth']
    sun = get_ephem_body(ephemeris, 'sun')
    moon = get_ephem_body(ephemeris, 'moon')
    observer = earth + Topos(latitude_degrees=args.lat, longitude_degrees=args.lon)

    today = date.today()

    fig = go.Figure()

    t = ts.utc(args.year, today.month, today.day, args.hour, args.minute)

    # 太阳固定在原点
    sun_x, sun_y, sun_z = 0, 0, 0
    fig.add_trace(go.Scatter3d(
        x=[sun_x], y=[sun_y], z=[sun_z],
        mode='markers',
        marker=dict(color='orange', size=10),
        name="太阳"
    ))

    # 地球相对太阳
    earth_pos = sun.at(t).observe(earth).position.au
    ex, ey, ez = earth_pos
    fig.add_trace(go.Scatter3d(
        x=[ex], y=[ey], z=[ez],
        mode='markers',
        marker=dict(color='blue', size=8),
        name="地球"
    ))

    # 月球相对地球
    moon_rel = earth.at(t).observe(moon).position.au
    mx, my, mz = ex + moon_rel[0], ey + moon_rel[1], ez + moon_rel[2]
    add_moon_with_phase(fig, (mx, my, mz), (sun_x, sun_y, sun_z))

    frames = []
    for i in range(365):
        d = date(args.year, 1, 1) + timedelta(days=i)
        t = ts.utc(d.year, d.month, d.day, args.hour, args.minute)

        earth_pos = sun.at(t).observe(earth).position.au
        ex, ey, ez = earth_pos
        moon_rel = earth.at(t).observe(moon).position.au
        mx, my, mz = ex + moon_rel[0], ey + moon_rel[1], ez + moon_rel[2]

        frames.append(go.Frame(
            data=[
                go.Scatter3d(x=[0], y=[0], z=[0],
                             mode='markers', marker=dict(color="orange", size=12), name="太阳"),
                go.Scatter3d(x=[ex], y=[ey], z=[ez],
                             mode='markers', marker=dict(color="blue", size=8), name="地球"),
                go.Scatter3d(x=[mx], y=[my], z=[mz],
                             mode='markers', marker=dict(color="white", size=4), name="月亮")
            ],
            name=str(d)
        ))

    fig.update(frames=frames)

    fig.update_layout(
        sliders=[{
            "steps": [
                {"method": "animate", "args": [[str(date(args.year, 1, 1) + timedelta(days=i))],
                {"mode": "immediate", "frame": {"duration": 100, "redraw": True}, "transition": {"duration": 0}}],
                "label": str(date(args.year, 1, 1) + timedelta(days=i))}
                for i in range(365)
            ],
            "x": 0.1, "y": -0.1
        }]
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode='cube',
            bgcolor="black"
        ),
        paper_bgcolor="black",
        plot_bgcolor="black",
        title="太阳、地球与带月相效果的月亮",
    )

    fig.show()


if __name__ == "__main__":
    main()
