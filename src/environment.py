import geopandas as gpd
import networkx as nx
import numpy as np
from scipy.spatial import cKDTree
from config_manager import get_config
import os


class Environment:

    def __init__(self):
        config = get_config()
        self.params = config.get('params', {})
        print("Environment parameters:", self.params)

        print("Environment initialisation:")
        # 加载路网
        self.edges_all = gpd.read_file(os.path.join(config['project_path'], config['input_path'], config['files']['edges_all']))
        self.edges_flood = gpd.read_file(os.path.join(config['project_path'], config['input_path'], config['files']['edges_flood']))
        # 只看 geometry 是否是子集
        edges_all_set = set(self.edges_all.geometry.apply(lambda g: g.wkt))
        edges_flood_set = set(self.edges_flood.geometry.apply(lambda g: g.wkt))
        is_subset = edges_flood_set.issubset(edges_all_set)
        if not is_subset:
            assert f"{config['files']['edges_flood']} is not the subset of {config['files']['edges_all']}"

        # 加载事故点
        self.crash_points = gpd.read_file(os.path.join(config['project_path'], config['input_path'], config['files']['crash']))
        # 加载避难所
        self.shelter_points = gpd.read_file(os.path.join(config['project_path'], config['input_path'], config['files']['shelter']))
        # 初始化图
        self.G = self._build_graph()
        self.G_vehicle = nx.subgraph_view(self.G, filter_edge=lambda u, v, d: d.get('car_access', True))
        G_pedestrian = nx.subgraph_view(self.G, filter_edge=lambda u, v, d: not d.get('flooded', False))
        self.G_pedestrian = G_pedestrian.to_undirected(as_view=True)
        print('Graph loaded.')


    def _build_graph(self):
        # 构造 DataFrame 的起终点列
        edges_df = self.edges_all.copy()
        edges_df['start'] = edges_df.geometry.apply(lambda g: g.coords[0])
        edges_df['end'] = edges_df.geometry.apply(lambda g: g.coords[-1])

        # 自动保留所有列（除了 geometry）作为 edge_attr
        edge_attr_cols = [col for col in edges_df.columns if col not in ['start', 'end', 'geometry']]
        # 用 from_pandas_edgelist 先生成单边图
        G = nx.from_pandas_edgelist(
            edges_df,
            source='start',
            target='end',
            edge_attr=edge_attr_cols,
            create_using=nx.DiGraph()
        )
        # 批量处理双向道路
        two_way_edges = edges_df[edges_df['oneway'] == False]
        if len(two_way_edges) > 0:
            # 构造反向边 DataFrame
            reversed_edges = two_way_edges.rename(columns={'start': 'end', 'end': 'start'})
            G = nx.from_pandas_edgelist(
                reversed_edges,
                source='start',
                target='end',
                edge_attr=edge_attr_cols,
                create_using=G  # 将反向边加入已有图
            )

        # 初始化 flooded=False
        for u, v in G.edges:
            G.edges[u, v]['flooded'] = False
        for geom in self.edges_flood.geometry:
            start = tuple(geom.coords[0])
            end = tuple(geom.coords[-1])
            if G.has_edge(start, end):
                G.edges[start, end]['flooded'] = True
            else:
                pass

        G = self._mark_shelters(G)
        self.shelters = [n for n, attr in G.nodes(data=True) if attr.get('shelter', False)]

        G = self._mark_crash(G)

        return G

    def _mark_shelters(self, G):
        """
        给图上对应节点添加 shelter=True 属性
        假设节点是 (x, y) 坐标元组
        """
        for n in G.nodes:
            G.nodes[n]['shelter'] = False

        node_coords = np.array(list(G.nodes))
        tree = cKDTree(node_coords)
        for pt in self.shelter_points.geometry:
            _, idx = tree.query([pt.x, pt.y])
            nearest_node = tuple(node_coords[idx])
            # 给节点添加 shelter 属性
            if 'shelter' not in G.nodes[nearest_node]:
                G.nodes[nearest_node]['shelter'] = True
        return G


    def _mark_crash(self, G):
        """
        给图上部分节点标记 crash=True，其他节点 crash=False
        crash_ratio: float 0~1，控制标记比例
        """
        np.random.seed(self.params.get('random_seed', 2025))
        crash_ratio = self.params.get('crash_ratio', 0.5)

        for n in G.nodes:
            G.nodes[n]['crash'] = False

        node_coords = np.array(list(G.nodes))
        tree = cKDTree(node_coords)
        # 随机选择 crash_gdf 中的部分点
        num_crash = int(len(self.crash_points) * crash_ratio)
        selected_idx = np.random.choice(len(self.crash_points), num_crash, replace=False)

        for i in selected_idx:
            pt = self.crash_points.geometry.iloc[i]
            _, idx = tree.query([pt.x, pt.y])
            nearest_node = tuple(node_coords[idx])
            G.nodes[nearest_node]['crash'] = True
        return G

