from src.algorithms.algorithm import Algorithm
from src.algorithms.routes import save_routes, format_routes
from src.utils.config import ConfigSingleton
from src.envs.env import Environment

import networkx as nx
import os


class DijkstraAlgorithm(Algorithm):
    def __init__(self, env: Environment, config: ConfigSingleton):
        self.config = config
        self.env = env
        self.algo = 'Dijkstra'

    def preprocess(self):
        self.tag = "_".join(str(value) for value in self.config.tags.values())
        self.route_file = os.path.join(self.config.output_path, f"routes_{self.algo}_{self.tag}.txt")
        if self.config.tags.get('shelter_tag')=='zz':
            self.end_nodes = [node for node, data in self.env.G.nodes(data=True) if data.get('node_code') == 8.0]
        elif self.config.tags.get('shelter_tag')=='plan':
            self.end_nodes = [node for node, data in self.env.G.nodes(data=True) if data.get('node_code') == 8.0 or data.get('node_code') == 171.0]
        self.start_nodes = [node for node, data in self.env.G.nodes(data=True) if data.get('node_code') == 1283.0]

    def run(self):
        graph = self.env.G

        paths = dict()
        best_route = None
        best_route_weight = float('inf')

        for start in self.start_nodes:
            for end in self.end_nodes:
                if (start, end) in paths.keys():
                    path_weight = paths[(start, end)]['weight']
                    if best_route_weight > path_weight:
                        best_route_weight = path_weight
                        best_route = paths[(start, end)]['path']
                    continue
                path, path_weight = plan_Dijkstra(G=graph, start=start, end=end)
                paths[(start, end)] = {'path': path, 'weight': path_weight}
                if best_route_weight > path_weight:
                    best_route_weight = path_weight
                    best_route = path

        route = convert_path_to_coordinates(G=graph, path=best_route)
        save_routes(start_coords=self.env.G.nodes[start].get('pos'), route=route, file_path=self.route_file)

    def postprocess(self):
        format_routes(self.route_file)

        
def plan_Dijkstra(G, start, end):
    """
    计算最短路径，并返回最短路径及其权重
    :param G: networkx 图
    :param start: 起点坐标 (x, y) 或节点 ID
    :param end: 终点坐标 (x, y) 或节点 ID
    :return: tuple, (shortest_path, path_weight)
    """
    try:
        # 计算最短路径
        path = nx.shortest_path(G, source=start, target=end, weight="weight")
        path_weight = nx.path_weight(G, path, weight="weight")

        return path, path_weight

    except nx.NetworkXNoPath:
        # 如果没有路径
        return None, float("inf")


def convert_path_to_coordinates(G, path, start_coords=None, end_coords=None):
    """
    将路径中的节点ID转换为坐标点，并插入起点和终点的坐标
    :param G: networkx 图
    :param path: 由节点ID组成的路径
    :param start_coords: 起点坐标，若为 None，则不插入
    :param end_coords: 终点坐标，若为 None，则不插入
    :return: 路径对应的坐标点列表
    """
    if path is None or len(path)==0:
        return None
    coordinates = []
    # 如果有起点坐标，则先加入起点坐标
    if start_coords:
        coordinates.append(start_coords)
    # 遍历路径中的每个节点，获取其坐标
    for node in path:
        if node in G.nodes:
            coordinates.append(G.nodes[node].get('pos'))  # 假设坐标保存在 'pos' 属性中
    # 如果有终点坐标，则加入终点坐标
    if end_coords:
        coordinates.append(end_coords)
    return coordinates


