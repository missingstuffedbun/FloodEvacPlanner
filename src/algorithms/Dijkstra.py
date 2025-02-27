from src.algorithms.algorithm import Algorithm
from src.algorithms import convert_path_to_coordinates
from src.algorithms.routes import save_routes, format_routes
from src.utils.config import ConfigSingleton
from src.utils.log import LoggerSingleton
from src.envs.env import Environment

import networkx as nx
import os



logger = LoggerSingleton().get_logger()

class DijkstraAlgorithm(Algorithm):
    def __init__(self, env: Environment, config: ConfigSingleton):
        self.config = config
        self.env = env
        self.algo = 'Dijkstra'

    def preprocess(self):
        logger.info(f"Preprocessing...")
        self.tag = "_".join(str(value) for value in self.config.tags.values())
        self.route_file = os.path.join(self.config.output_path, f"routes_{self.algo}_{self.tag}.txt")
        if self.config.tags.get('shelter_tag')=='zz':
            self.end_nodes = [node for node, data in self.env.G.nodes(data=True) if data.get('node_code') == 8.0]
        elif self.config.tags.get('shelter_tag')=='plan':
            self.end_nodes = [node for node, data in self.env.G.nodes(data=True) if data.get('node_code') == 8.0 or data.get('node_code') == 171.0]
        self.start_nodes = [node for node, data in self.env.G.nodes(data=True) if data.get('node_code') == 1283.0]

    def run(self):
        logger.info(f"Start {self.algo} Algorithm...")
        graph = self.env.G

        paths = dict()
        for start in self.start_nodes:
            logger.debug(f"Start from node{start}")
            best_route = None
            best_route_weight = float('inf')
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
        logger.info(f"Postprocessing...")
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



