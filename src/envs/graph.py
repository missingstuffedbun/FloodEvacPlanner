from . import output_path, logger

import networkx as nx
from shapely.geometry import Point
import os
import ast
from shapely.geometry import LineString


def build_road_graph(edges, nodes):
    # 创建 NetworkX 图
    G = nx.Graph()

    # 创建节点坐标字典
    node_dict = { (node.geometry.x, node.geometry.y): node["OBJECTID"] for _, node in nodes.iterrows() }

    # 添加节点
    for _, node in nodes.iterrows():
        G.add_node(node["OBJECTID"], pos=(node.geometry.x, node.geometry.y))

    # 添加边
    for _, edge in edges.iterrows():
        start_coord = edge.geometry.coords[0]  # 线的起点 (x, y)
        end_coord = edge.geometry.coords[-1]   # 线的终点 (x, y)
        if start_coord == end_coord:
            continue

        # 查找节点 ID
        start_id = node_dict.get(start_coord, None)
        end_id = node_dict.get(end_coord, None)

        # 如果找不到确切匹配的节点，则尝试最近匹配
        if start_id is None:
            start_id = min(node_dict, key=lambda k: Point(k).distance(Point(start_coord)))
            start_id = node_dict[start_id]

        if end_id is None:
            end_id = min(node_dict, key=lambda k: Point(k).distance(Point(end_coord)))
            end_id = node_dict[end_id]

        # 添加边
        G.add_edge(start_id, end_id, weight=edge["Shape_Leng"])  # 使用 Shape_Leng 作为权重

    logger.info(f"Build graph with {len(G.nodes)} nodes and {len(G.edges)} edges")
    return G



def load_graph(file_name):
    """
    加载 GML 文件并返回图，如果文件不存在或加载失败，返回 None。
    :param file_name: 图文件名，不需要文件扩展名（.gml）
    :return: 网络图（NetworkX Graph）或 None
    """
    file_path = os.path.join(output_path, file_name)

    try:
        # 尝试读取 GML 文件
        graph = nx.read_gml(file_path)

        # 创建新的空图
        new_graph = nx.Graph()

        # 重新添加节点
        for node, attributes in graph.nodes(data=True):
            new_node = ast.literal_eval(node)  # 解析字符串格式的元组
            new_graph.add_node(new_node, **attributes)

        # 重新添加边
        for u, v, attributes in graph.edges(data=True):
            new_u = ast.literal_eval(u)
            new_v = ast.literal_eval(v)
            new_graph.add_edge(new_u, new_v, **attributes)

        logger.info(f"Loaded graph with {len(new_graph.nodes)} nodes and {len(new_graph.edges)} edges")
        return new_graph

    except FileNotFoundError:
        logger.error(f"File {file_path} not found.")
    except nx.NetworkXException as e:
        logger.error(f"Error while reading the GML file {file_path}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading the graph: {e}")

    # 如果发生任何异常或文件未找到，返回 None
    return None



def remove_flooded_edges(G, floods):
    """
    删除与洪水区域相交的所有边
    :param G: networkx Graph, 包含道路的图
    :param floods: GeoDataFrame, 包含洪水区域的多边形
    :return: 修改后的 networkx Graph
    """
    edges_to_remove = []

    # 遍历所有边，检查是否与洪水区域相交
    for u, v, data in G.edges(data=True):
        if "geometry" in data:  # 确保边有几何信息
            edge_geom = data["geometry"]
        else:
            # 如果没有geometry信息，尝试用节点坐标生成 LineString
            pos = nx.get_node_attributes(G, "pos")
            edge_geom = LineString([pos[u], pos[v]])

        # 判断边是否与洪水区域相交
        if floods.geometry.intersects(edge_geom).any():
            edges_to_remove.append((u, v))

    # 从图中删除受影响的边
    G.remove_edges_from(edges_to_remove)

    logger.info(f"Remove {len(edges_to_remove)} edges")
    return G