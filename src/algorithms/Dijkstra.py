from src.algorithms.algorithm import Algorithm
from src.algorithms import euclidean_distance
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
        self.env.graph_for_Dijkstra()
        self.tag = "_".join(str(value) for value in self.config.tags.values())
        self.route_file = os.path.join(self.config.output_path, f"routes_{self.algo}_{self.tag}.txt")

    def run(self):
        shelters_coords = self.env.shelters_coords
        spaces_coords = self.env.spaces_coords
        graph = self.env.graph_Dijkstra
    
        paths = dict()
        for space_coords in spaces_coords:
            nearest_shelter = find_nearest_shelter(coords=space_coords, shelters_coords=shelters_coords,
                                                   distance_threshold=100)
            if nearest_shelter:
                save_routes(start_coords=space_coords, route=[space_coords, nearest_shelter], file_path=self.route_file)
                continue
            start_nodes = find_nodes_nearby(G=graph, coords=space_coords, distance_threshold=100, ignore_flood=True)
            best_route = None
            best_route_weight = float('inf')
            best_shelter = None
            for start in start_nodes:
                for shelter_coords in shelters_coords:
                    end_nodes = find_nodes_nearby(G=graph, coords=shelter_coords, distance_threshold=100,
                                                  ignore_flood=True)
                    for end in end_nodes:
                        if (start, end) in paths.keys():
                            path_weight = paths[(start, end)]['weight']
                            if best_route_weight > path_weight:
                                best_route_weight = path_weight
                                best_route = paths[(start, end)]['path']
                                best_shelter = paths[(start, end)]['shelter']
                            continue
                        path, path_weight = plan_Dijkstra(G=graph, start=start, end=end)
                        paths[(start, end)] = {'path': path, 'weight': path_weight, 'shelter': shelter_coords}
                        if best_route_weight > path_weight:
                            best_route_weight = path_weight
                            best_route = path
                            best_shelter = shelter_coords
            route = convert_path_to_coordinates(G=graph, path=best_route, start_coords=space_coords,
                                                end_coords=best_shelter)
            save_routes(start_coords=space_coords, route=route, file_path=self.route_file)


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


def find_nearest_shelter(coords, shelters_coords, distance_threshold):
    """
    根据起点坐标找到最近的 shelter，且距离超过阈值的忽略
    :param coords: 起点坐标 (x, y)
    :param shelters_coords: shelter坐标列表 (x, y)
    :param distance_threshold: 距离阈值，超过该距离的 shelter 被忽略
    :return: 最近的 shelter 坐标或 None
    """
    min_distance = float('inf')
    nearest_shelter = None

    for shelter_coords in shelters_coords:
        # 计算起点与 shelter 的欧几里得距离
        distance = euclidean_distance(coords, shelter_coords)

        # 如果距离超过阈值，则忽略该 shelter
        if distance > distance_threshold:
            continue

        # 更新最近的 shelter
        if distance < min_distance:
            min_distance = distance
            nearest_shelter = shelter_coords

    return nearest_shelter



def find_nodes_nearby(G, coords, distance_threshold, ignore_flood=True):
    """
    找到给定坐标周围一定距离内的图节点
    :param G: networkx 图
    :param coords: 给定坐标 (x, y)
    :param distance_threshold: 距离阈值，单位与坐标一致
    :return: 一个包含附近节点ID的列表
    """
    nearby_nodes = []

    # 遍历所有节点
    for node, data in G.nodes(data=True):
        node_coords = data.get('pos')  # 假设节点的坐标保存在 'pos' 属性中
        if node_coords is None:
            continue

        # 计算节点和目标坐标的欧几里得距离
        distance = euclidean_distance(coords, node_coords)  # 计算两点之间的距离，单位：米
        if distance <= distance_threshold:  # 如果距离小于或等于阈值，则认为该节点在附近
            if not ignore_flood:    # 如果积水导致不联通，跳过
                if not is_connected(coords, node_coords):
                    continue
            nearby_nodes.append(node)

    return nearby_nodes
