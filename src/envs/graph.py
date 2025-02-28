import networkx as nx
import ast
from shapely.geometry import LineString
import pandas as pd
import numpy as np


from src.utils.log import LoggerSingleton
from src.utils.enums import NodeCodeMapping, EdgeCodeMapping

logger = LoggerSingleton().get_logger()


def build_road_graph(edges, nodes):
    # 创建 NetworkX 图
    G = nx.Graph()

    # 创建节点坐标字典
    node_dict = {(node.geometry.x, node.geometry.y): node["FID1"] for _, node in nodes.iterrows()}

    # 添加节点
    for _, node in nodes.iterrows():
        G.add_node(
            node["FID1"],
            pos=(node.geometry.x, node.geometry.y),
            node_code=node["Node_code"]
        )

    # 添加边
    for _, edge in edges.iterrows():
        start_coord = edge.geometry.coords[0]  # 线的起点 (x, y)
        end_coord = edge.geometry.coords[-1]   # 线的终点 (x, y)

        # 查找节点 ID
        start_id = node_dict.get(start_coord, None)
        end_id = node_dict.get(end_coord, None)
        if start_id is None or end_id is None or start_id==end_id:
            continue

        # 添加边
        G.add_edge(
            start_id, end_id,
            weight=edge["Shape_Leng"],
            edge_code=edge["Class"]
        )

    logger.info(f"Build graph with {len(G.nodes)} nodes and {len(G.edges)} edges")
    return G



def load_graph(file_path):
    """
    加载 GML 文件并返回图，如果文件不存在或加载失败，返回 None。
    :param file_path: 图文件名，不需要文件扩展名（.gml）
    :return: 网络图（NetworkX Graph）或 None
    """
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


def route_stats_with_graph(G, routes):
    """
    统计路径的相关信息，并更新图G的属性。
    :param G: networkx 图对象，图中包含节点和边。
    :param routes: 路径列表，每条路径是节点的坐标元组列表。
    :return: 更新后的图G以及每条路径的统计信息。
    """
    route_stats = []  # 存储每条路径的统计信息

    # 创建一个坐标到节点的映射字典
    pos_to_node = {v['pos']: node for node, v in G.nodes(data=True)}

    for route in routes:
        # 1. 把路径中的每个坐标转换成节点（list of nodes）
        node_route = []
        for coords in route:
            node = pos_to_node.get(coords)
            if node is not None:
                node_route.append(node)
            else:
                node_route = []  # 如果有坐标没有对应节点，则认为路径无效
                break

        # 2. 检查路径是否找到：如果路径的节点数大于1，则认为有路径
        path_found = len(node_route) > 1

        route_shelter = None
        route_weight = 0
        # 3. 计算路径的权重并更新图的属性
        if path_found:
            route_weight = 0
            route_shelter = node_route[-1]  # 终点是路径的最后一个节点

            for i in range(1, len(node_route)):
                start_node = node_route[i - 1]
                end_node = node_route[i]


                # 计算路径权重（edge weight）
                edge_weight = G[start_node][end_node].get(
                    'weight',
                    np.linalg.norm(np.array(start_node.get('pos')) - np.array(end_node.get('pos')))
                )
                route_weight += edge_weight

                # 4. 更新边的flow属性：每经过一条边，flow增加1
                G[start_node][end_node]['flow'] = G[start_node][end_node].get('flow', 0) + 1

                # 5. 更新edge_code属性：将edge_code映射为数值型，并存储到capacity中
                edge_code = G[start_node][end_node].get('edge_code', None)
                if edge_code is not None:
                    G[start_node][end_node]['capacity'] = EdgeCodeMapping.get_capacity(edge_code)

        # 将路径的统计信息添加到结果列表
        route_stats.append({
            'route': node_route,
            'route_len': len(route),
            'path_found': path_found,
            'route_shelter': route_shelter,
            'route_weight': route_weight
        })


    df = pd.DataFrame(route_stats)
    logger.info(f"{df.describe()}")

    return G, df


def congestion_level_analysis(G, bins=5):
    # 获取所有边的属性转换为 DataFrame
    df = pd.DataFrame(G.edges(data=True), columns=['start_node', 'end_node', 'attributes'])

    # 提取 flow 和 capacity，并计算 ratio (flow/capacity)
    df['flow'] = df['attributes'].apply(lambda x: x.get('flow', 0))  # 默认 flow 为 0
    df['capacity'] = df['attributes'].apply(lambda x: x.get('capacity', 1))  # 默认 capacity 为 1
    df['ratio'] = df['flow'] / (df['capacity'] * 5.0)  # 计算 flow/capacity 比值
    # 统计分析
    flow_zero_count = (df['flow'] == 0).sum()  # flow 为 0 的数量
    flow_zero_ratio = flow_zero_count / len(df)  # flow 为 0 的比例
    ratio_variance = df['ratio'].var()  # ratio 的方差
    ratio_mean = df['ratio'].mean()  # ratio 的均值
    ratio_std = df['ratio'].std()  # ratio 的标准差
    # 输出统计分析结果
    logger.info(f"Flow 为 0 的边的数量: {flow_zero_count}")
    logger.info(f"Flow 为 0 的比例: {flow_zero_ratio:.2f}")
    logger.info(f"Ratio 的方差: {ratio_variance:.4f}")
    logger.info(f"Ratio 的均值: {ratio_mean:.4f}")
    logger.info(f"Ratio 的标准差: {ratio_std:.4f}")

    # 使用 pd.qcut 按分位数进行分箱
    bin_labels = [f'Bin {i + 1}' for i in range(bins)]  # 分箱标签
    df['bin'] = pd.qcut(df['ratio'], q=bins, labels=bin_labels)  # 按 ratio 列进行分箱，并赋予标签
    # 分箱统计分析
    bin_stats = df.groupby('bin')['ratio'].agg(['mean', 'std', 'min', 'max', 'count'])
    bin_stats.columns = ['Bin Mean', 'Bin Std', 'Bin Min', 'Bin Max', 'Bin Count']
    logger.info(f"分箱统计分析：\n {bin_stats}")

    return df
