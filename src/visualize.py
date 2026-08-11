"""Reads output/<timestamp>/history.txt and renders an interactive HTML map.

Each line of history.txt is a JSON array of one or more segments:
    [{"mode": "vehicle"|"pedestrian", "exec_route": [[lon, lat], ...], "stop_sig": bool}, ...]

The full trajectory of each agent is the concatenation of its segments.
Shelters (green) and crash points (red) are loaded from the input shapefiles
listed in config.yaml so they appear on the map for context.
"""
import json
import os

import geopandas as gpd
import yaml

import folium

# 颜色：按到达结果区分 agent 轨迹
COLOR_REACHED_DEST = "#1f77b4"   # 蓝：到达目的地
COLOR_REACHED_SHELTER = "#2ca02c"  # 绿：到达避难所
COLOR_FAILED = "#d62728"          # 红：失败


def load_history(path):
    """Return list of (segments, full_route) tuples."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            segs = json.loads(line)
            full = []
            for seg in segs:
                route = seg.get("exec_route") or []
                if not full:
                    full.extend(route)
                else:
                    # 避免相邻段首尾重复节点
                    full.extend(route[1:] if route and full[-1] == route[0] else route)
            records.append((segs, full))
    return records


def classify(segs):
    """根据各段 mode/stop_sig 判断 agent 最终状态。"""
    modes = [s.get("mode") for s in segs]
    if any(s.get("mode") == "vehicle" for s in segs) and all(
        s.get("stop_sig") for s in segs if s.get("mode") == "vehicle"
    ):
        # 含 vehicle 段且都 stop_sig -> 到达目的地
        if any(s.get("mode") == "vehicle" for s in segs):
            return "dest"
    # 步行段且 stop_sig -> 到达避难所（无 vehicle 或 vehicle 未达）
    if any(s.get("mode") == "pedestrian" and s.get("stop_sig") for s in segs):
        return "shelter"
    if any(s.get("mode") == "failed" for s in segs):
        return "failed"
    return "failed"


def build_map(history_path, config_path, output_html):
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    base = cfg.get("project_path", os.path.dirname(os.path.dirname(history_path)))
    input_path = cfg.get("input_path", "input")
    in_dir = input_path if os.path.isabs(input_path) else os.path.join(base, input_path)

    records = load_history(history_path)

    # 计算所有轨迹点的边界，用于初始化地图
    lats, lons = [], []
    for _, full in records:
        for lon, lat in full:
            lats.append(lat)
            lons.append(lon)

    if not lats:
        # 退而求其次：用避难所边界
        shelter_file = os.path.join(in_dir, cfg["files"]["shelter"])
        if os.path.exists(shelter_file):
            g = gpd.read_file(shelter_file)
            lats = list(g.geometry.y)
            lons = list(g.geometry.x)

    if not lats:
        center = [-27.41, 152.96]
    else:
        center = [sum(lats) / len(lats), sum(lons) / len(lons)]

    m = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")

    # ---- 绘制 agent 轨迹 ----
    counts = {"dest": 0, "shelter": 0, "failed": 0}
    for segs, full in records:
        if not full:
            counts["failed"] += 1
            continue
        status = classify(segs)
        counts[status] += 1
        color = {
            "dest": COLOR_REACHED_DEST,
            "shelter": COLOR_REACHED_SHELTER,
            "failed": COLOR_FAILED,
        }[status]
        folium.PolyLine(
            locations=[[lat, lon] for lon, lat in full],
            color=color,
            weight=2,
            opacity=0.7,
        ).add_to(m)

    # ---- 绘制避难所（绿点）----
    shelter_file = os.path.join(in_dir, cfg["files"]["shelter"])
    if os.path.exists(shelter_file):
        sg = gpd.read_file(shelter_file)
        fg_shelter = folium.FeatureGroup(name="Shelters", show=True)
        for _, row in sg.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=4,
                color="#2ca02c",
                fill=True,
                fill_color="#2ca02c",
                fill_opacity=0.8,
                weight=1,
            ).add_to(fg_shelter)
        fg_shelter.add_to(m)

    # ---- 绘制事故点（红点）----
    crash_file = os.path.join(in_dir, cfg["files"]["crash"])
    if os.path.exists(crash_file):
        cg = gpd.read_file(crash_file)
        fg_crash = folium.FeatureGroup(name="Crash points", show=True)
        for _, row in cg.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=5,
                color="#d62728",
                fill=True,
                fill_color="#d62728",
                fill_opacity=0.9,
                weight=1,
            ).add_to(fg_crash)
        fg_crash.add_to(m)

    # ---- 图例 ----
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; width: 220px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size: 13px; padding: 8px;">
      <b>Evacuation routes</b><br>
      <i style="background:{dest};">&nbsp;&nbsp;&nbsp;</i> Reached destination<br>
      <i style="background:{shelter};">&nbsp;&nbsp;&nbsp;</i> Reached shelter<br>
      <i style="background:{failed};">&nbsp;&nbsp;&nbsp;</i> Failed / no route<br>
      <span style="color:#2ca02c;">&#9679;</span> Shelter &nbsp;
      <span style="color:#d62728;">&#9679;</span> Crash
    </div>
    """.format(
        dest=COLOR_REACHED_DEST,
        shelter=COLOR_REACHED_SHELTER,
        failed=COLOR_FAILED,
    )
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl().add_to(m)

    os.makedirs(os.path.dirname(output_html), exist_ok=True)
    m.save(output_html)

    total = sum(counts.values())
    print(
        f"Map saved -> {output_html}\n"
        f"Agents: {total} | reached destination: {counts['dest']} | "
        f"reached shelter: {counts['shelter']} | failed: {counts['failed']}"
    )


if __name__ == "__main__":
    import sys

    # 用法：python visualize.py [history.txt] [config.yaml] [output.html]
    # 默认读取最新的 output/<timestamp>/history.txt 与项目根目录 config.yaml
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    default_history = None
    out_dir = os.path.join(root, "output")
    if os.path.isdir(out_dir):
        subdirs = sorted(
            [d for d in os.listdir(out_dir) if os.path.isdir(os.path.join(out_dir, d))],
            reverse=True,
        )
        for sd in subdirs:
            cand = os.path.join(out_dir, sd, "history.txt")
            if os.path.exists(cand):
                default_history = cand
                break

    history_arg = sys.argv[1] if len(sys.argv) > 1 else default_history
    config_arg = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "config.yaml"
    )
    out_arg = sys.argv[3] if len(sys.argv) > 3 else (
        os.path.join(os.path.dirname(history_arg), "evacuation_map.html")
        if history_arg else os.path.join(out_dir, "evacuation_map.html")
    )

    if not history_arg or not os.path.exists(history_arg):
        raise SystemExit("history.txt not found. Pass it as the first argument.")

    build_map(history_arg, config_arg, out_arg)
