import numpy as np


# 计算两个点之间的欧几里得距离
def euclidean_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))



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


def convert_tree_to_coords(G, route_tree):
    """
    将route_tree中的节点ID和父节点ID直接转换为坐标，返回一个新的字典，节点ID和父节点ID都用坐标表示。
    :param G: networkx 图，包含节点坐标
    :param route_tree: 存储节点父节点关系的树结构
    :return: 一个字典，包含节点坐标（键）及其父节点坐标（值）
    """
    coords_tree = {}  # 用来存储节点坐标
    for node, parent in route_tree.items():
        node_coord = G.nodes[node].get('pos')  # 获取节点的坐标
        parent_coord = G.nodes[parent].get('pos') if parent else None  # 获取父节点的坐标，根节点的父节点为 None
        coords_tree[node_coord] = parent_coord  # 直接将节点坐标和父节点坐标关联
    return coords_tree

