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
                 plot_include=['map','buildings', 'floods', 'rivers', 'roads', 'road_nodes'],
                 plot_exclude=['roads', 'road_nodes']
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

        # 绘制网络
        if 'edges' in self.plot_set:
            edge_code_widths = {
                'motorway': 7.0,  # 高速公路 (7倍于 footway)
                'trunk_link': 6.0,  # 干线连接
                'footway': 1.0,  # 步道 (基准，宽度为1)
                'living_street': 2.0,  # 生活街道
                'primary': 5.0,  # 主路
                'unclassified': 1,  # 未分类道路
                'primary_link': 4.0,  # 主路连接
                'motorway_link': 6.0,  # 高速公路连接
                'residential': 2.0,  # 住宅区道路
                'cycleway': 1.2,  # 自行车道
                'trunk': 6.0,  # 干线
                'secondary': 3.0,  # 次要道路
                'pedestrian': 0.8,  # 步行道
                'path': 1.0,  # 小路
                'service': 1.5,  # 服务道路
                'tertiary': 2.2,  # 第三级道路
                'steps': 0.3,  # 台阶
                'secondary_link': 3.0,  # 次要路连接
                'tertiary_link': 2.5  # 第三级路连接
            }
            edge_widths = [
                1.0+edge_code_widths.get(edge_data.get('edge_code', 'unclassified'))/10.0
                for u, v, edge_data in self.G.edges(data=True)
            ]

            nx.draw_networkx_edges(
                self.G, pos, ax=ax, edge_color="gray", alpha=0.3, width=edge_widths
            )
            self.handlers.append(Line2D([0], [0], color='gray', lw=2, alpha=0.3, label="Road"))

        if 'nodes' in self.plot_set:
            # 定义每种 node_code 对应的颜色和大小
            node_code_colors = {
                1.0: 'gray', # intersection
                2.0: 'gray', # intersection - new
                1283.0: 'red', # space
                8.0: 'green', # shelter - zz
                171.0: 'green', # shelter - plan
            }
            node_code_sizes = {
                1.0: 0.5,
                2.0: 0.5,
                1283.0: 4,
                8.0: 8,
                171.0: 8,
            }
            # 获取每个节点的颜色和大小
            node_colors = [node_code_colors.get(data.get('node_code', 1.0), 'gray') for node, data in self.G.nodes(data=True)]
            node_sizes = [node_code_sizes.get(data.get('node_code', 1.0), 1) for node, data in self.G.nodes(data=True)]

            nx.draw_networkx_nodes(self.G, pos, ax=ax, node_color=node_colors, node_size=node_sizes, alpha=0.6)

            self.handlers.append(Line2D([0], [0], marker='o', color='gray', markerfacecolor='gray', markersize=0.5, label="Intersection"))
            self.handlers.append(Line2D([0], [0], marker='o', color='gray', markerfacecolor='red', markersize=4, label="Underground Space"))
            self.handlers.append(Line2D([0], [0], marker='o', color='gray', markerfacecolor='green', markersize=8, label="Shelter"))



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

        if self.route_tree is not None:
            print(self.route_tree)
            for start, end in self.route_tree.items():
                start_x, start_y = start
                end_x, end_y = end
                plt.plot([start_x, end_x], [start_y, end_y], marker='o')  # 绘制线段，并标记节点


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
        import matplotlib
        matplotlib.use('TkAgg')

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
