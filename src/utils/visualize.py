from src.envs.env import Environment
from src.utils.config import ConfigSingleton
from src.utils.log import LoggerSingleton


import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.cm as cm
from datetime import datetime
import os

logger = LoggerSingleton().get_logger()

# 环境图层类
class EnvironmentLayer:
    def __init__(self, env: Environment, 
                 plot_set=None,
                 plot_include=['map', 'shelters', 'spaces','buildings', 'floods', 'rivers', 'roads', 'road_nodes'],
                 plot_exclude=['shelters', 'spaces', 'roads', 'road_nodes']
                ):
        self.env = env
        self.plot_set = plot_set if plot_set is not None else set(plot_include).difference(set(plot_exclude))
        self.handlers = []
        logger.info(f"Plot Environment Layer: {self.plot_set}")

    
    def plot(self, ax=None):
        if ax is None:
            ax = plt.gca()
            
        plt.axis('equal')
        if 'map' in self.plot_set:
            self.env.map.boundary.plot(ax=ax, color='black', linewidth=1, zorder=1)
            self.env.map.plot(ax=ax, color='gray', alpha=0.1)

        # if 'shelters' in self.plot_set:
        #     self.env.shelters.plot(marker='o', color='green', markersize=10, alpha=0.4, label='Shelter', zorder=32)
        #     self.handlers.append(Line2D([0], [0], marker='o', color='green', markerfacecolor='green', markersize=10, label='Shelter'))

        # if 'spaces' in self.plot_set:
        #     self.env.spaces.plot(marker='o', color='red', markersize=10, alpha=0.4, label='Underground Space', zorder=31)
        #     self.handlers.append(Line2D([0], [0], marker='o', color='red', markerfacecolor='red', markersize=10, label='Underground Space'))

        if 'buildings' in self.plot_set:
            self.env.buildings.plot(ax=ax, color='brown', alpha=0.6, label='Building', zorder=2)
            self.handlers.append(Patch(color='brown', alpha=0.6, label='Building'))


        if 'floods' in self.plot_set:
            self.env.floods.plot(ax=ax, color='purple', alpha=0.4, label='Flood', zorder=6)
            self.handlers.append(Patch(color='purple', alpha=0.4, label='Flood'))

        if 'rivers' in self.plot_set:
            self.env.rivers.plot(ax=ax, color='blue', alpha=0.4, label='River', zorder=5)
            self.handlers.append(Patch(color='blue', alpha=0.4, label='River'))

        
        if 'roads' in self.plot_set:
            self.env.roads.plot(ax=ax, color='blue', linewidth=1, label='Road', zorder=4)
            self.handlers.append(Line2D([0], [0], color='blue', lw=2, label='Road'))
        
        if 'road_nodes' in self.plot_set:
            self.env.road_nodes.plot(ax=ax, color='red', marker='o', markersize=5, label='Intersection', zorder=3)
            self.handlers.append(Line2D([0], [0], marker='o', color='red', markerfacecolor='red', markersize=5, label='Intersection'))

            

# 图结构图层类
class GraphLayer:
    def __init__(self, G, plot_set=['edges']):
        self.G = G
        self.plot_set = plot_set
        self.handlers = []
        logger.info(f"Plot Graph Layer: {self.plot_set}")

    def plot(self, ax=None):
        if ax is None:
            ax = plt.gca()

        pos = nx.get_node_attributes(self.G, "pos")  # 获取节点位置
        if 'edges' in self.plot_set:
            nx.draw_networkx_edges(self.G, pos, ax=ax, edge_color="gray", alpha=0.3, width=0.5)
            self.handlers.append(Line2D([0], [0], color='gray', lw=2, alpha=0.3, label="Road"))
        if 'nodes' in self.plot_set:
            nx.draw_networkx_nodes(self.G, pos, ax=ax, node_color="gray", node_size=10, alpha=0.6)
            self.handlers.append(Line2D([0], [0], marker='o', color='gray', markerfacecolor='blue', markersize=8, label="Intersection"))



# 路径图层类
class RouteLayer:
    def __init__(self, routes=None, route_tree=None):
        if routes:
            self.routes = routes
            self.route_number = len(routes)
        elif route_tree:
            self.route_tree = route_tree
            self.route_number = 1
        self.handlers = []
        logger.info(f"Plot Route Layer: {self.route_number} route(s)")

    def plot(self, ax=None):
        if ax is None:
            ax = plt.gca()

        if self.routes is not None:
            colormap = cm.viridis  # 使用 viridis colormap
            ends_set = set([route[-1] for route in self.routes])  # 终点数量
            ends_colors = [colormap(i / len(ends_set)) for i in range(len(ends_set))]  # 为不同终点路径分配不同的颜色
            route_colors = dict(zip(ends_set, ends_colors))
            for route in self.routes:
                if len(route)==1:
                    scatter = ax.scatter(route[0][0], route[0][1], color='grey', label='Non-Accessible Underground Space', alpha=0.4, s=10, zorder=21)
                    self.handlers.append(scatter)
                    continue
                route_x, route_y = zip(*route)
                ax.plot(route_x, route_y, color=route_colors[route[-1]], label='Route', linewidth=1, zorder=23)
                self.handlers.append(Line2D([0], [0], color='green', lw=2, label="Route"))
                scatter = ax.scatter(route[0][0], route[0][1], color='red', label='Accessible Underground Space', alpha=0.4, s=10, zorder=21)
                self.handlers.append(scatter)
                scatter = ax.scatter(route[-1][0], route[-1][1], color='green', label='Shelter', alpha=0.4, s=10, zorder=22)
                self.handlers.append(scatter)
        
        # self.handlers.append(Line2D([0], [0], marker='o', color='grey', lw=2, alpha=0.4, label="Non-Accessible Underground Space"))
        # self.handlers.append(Line2D([0], [0], marker='o', color='red', lw=2, alpha=0.4, label="Accessible Underground Space"))
        # self.handlers.append(Line2D([0], [0], marker='o', color='green', lw=2, alpha=0.4, label="Shelter"))



# 可视化类
class Visualize:
    def __init__(self, environment_layer=None, graph_layer=None, route_layer=None, **kwargs):
        self.environment_layer = environment_layer
        self.graph_layer = graph_layer
        self.route_layer = route_layer
        # 遍历所有命名参数（kwargs），并将其赋值为类的属性
        for key, value in kwargs.items():
            setattr(self, key, value)

    def plot(self):
        # 创建一个新的图形
        fig, ax = plt.subplots(figsize=(10, 8))
        handlers = []

        # 绘制各个图层
        if self.environment_layer:
            self.environment_layer.plot(ax=ax)
            handlers.extend(self.environment_layer.handlers)
        if self.graph_layer:
            self.graph_layer.plot(ax=ax)
            handlers.extend(self.graph_layer.handlers)
        if self.route_layer:
            self.route_layer.plot(ax=ax)
            handlers.extend(self.route_layer.handlers)
        ax.legend(handles=list({h.get_label(): h for h in handlers}.values()))
        
        # 设置标题和标签
        ax.set_title(getattr(self, 'title', None))
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(getattr(self, 'grid', True))
        plt.axis('equal')

        output_name = getattr(self, 'output_name', datetime.now().strftime('%Y%m%d%H%M%S'))
        config = ConfigSingleton()
        output_file = os.path.join(config.output_path, f"{output_name}.jpg")
        plt.savefig(output_file, dpi=600, bbox_inches='tight')
        logger.info(f"Save fig: {output_file}")
