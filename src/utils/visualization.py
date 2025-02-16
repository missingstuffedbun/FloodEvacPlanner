import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import cm
from datetime import datetime
from src.utils.config import output_path
from . import logger
import os


def plot_graph(G, **kwargs):
    # 绘制地图边界
    fig, ax = plt.subplots(figsize=(10, 10))
    map_data = kwargs.get('map_data', None)
    if map_data is not None:
        map_data.boundary.plot(ax=ax, color='black', linewidth=1)
        map_data.plot(ax=ax, color='gray', alpha=0.1)

    pos = nx.get_node_attributes(G, "pos")  # 获取节点位置
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="gray", alpha=0.3, width=0.5)

    # 绘制其他环境信息
    draw_buildings = kwargs.get('draw_buildings', None)
    draw_rivers = kwargs.get('draw_rivers', None)
    draw_floods = kwargs.get('draw_floods', None)
    if draw_buildings is not None:
        draw_buildings.plot(ax=ax, color='brown', alpha=0.6, label='Buildings')
    if draw_rivers is not None:
        draw_rivers.plot(ax=ax, color='blue', alpha=0.4, label='Rivers')
    if draw_floods is not None:
        draw_floods.plot(ax=ax, color='purple', alpha=0.4, label='Floods')

    # 绘制路线
    routes = kwargs.get('routes', None)
    if routes:
        # 使用colormap设置路径颜色
        colormap = cm.viridis  # 使用 viridis colormap
        ends_set = set([route[-1] for route in routes])  # 终点数量
        ends_colors = [colormap(i / len(ends_set)) for i in range(len(ends_set))]  # 为不同终点路径分配不同的颜色
        route_colors = dict(zip(ends_set, ends_colors))
        # 绘制路径
        for route in routes:
            if route:
                if len(route)==1:
                    ax.scatter(route[0][0], route[0][1], color='red', label='Start', alpha=0.4, zorder=6, s=10)
                    continue
                route_x, route_y = zip(*route)
                ax.plot(route_x, route_y, color=route_colors[route[-1]], label='Route', linewidth=1, zorder=4)

                # 绘制起点和终点
                ax.scatter(route[0][0], route[0][1], color='red', label='Start', alpha=0.4, zorder=6, s=10)
                ax.scatter(route[-1][0], route[-1][1], color='green', label='End', alpha=0.4, zorder=6, s=10)

    ax.set_title(kwargs.get('title', ''))
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.grid(True)
    plt.axis('equal')

    saveFig = kwargs.get('saveFig', False)
    output_name = kwargs.get('file_name', datetime.now().strftime('%Y%m%d%H%M%S'))
    if saveFig:
        output_file = os.path.join(output_path, f"{output_name}.jpg")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"Save Fig {output_file}")

    plt.show()