import networkx as nx
import numpy as np
import random


def heuristic(u, v, G):
    """
    u: 当前节点
    v: 目标节点
    G: 图对象
    """
    # 1. 基础欧式距离
    dist = ((u[0] - v[0])**2 + (u[1] - v[1])**2)**0.5

    # 2. 节点属性惩罚：special=None增加惩罚
    special_penalty = 0
    if len(G.nodes[u].get('special', ''))<1:
        special_penalty = 100  # 可以调整权重

    # 3. 边属性惩罚：max_speed<50增加惩罚
    min_edge_speed_penalty = 0
    for nbr in G.successors(u):
        edge_data = G.get_edge_data(u, nbr)
        if edge_data.get('max_speed', 100) < 50:
            min_edge_speed_penalty = 50  # 可以根据需求调整
            break  # 只考虑一条就行
    # 总启发值 = 欧式距离 + 节点惩罚 + 边惩罚
    return dist + special_penalty + min_edge_speed_penalty


class Planner:
    def __init__(self, env):
        self.G = env.G
        self.G_vehicle = env.G_vehicle
        self.G_pedestrian = env.G_pedestrian
        self.shelters = env.get_shelters()
        self.cache_vehicle = {}  # {(start_node, end_node): route}
        self.cache_pedestrian = {}  # {(start_node, end_node): route}

        random.seed(env.params.get('random_seed', 2025))
        self.sample_size = env.params.get('random_seed', 200)

    # -------- 阶段一：vehicle -----------
    def plan_vehicle(self, start, end, algo='dijkstra'):
        key = (start, end, 'vehicle')
        if key in self.cache_vehicle:
            return self.cache_vehicle[key]
        route = self._plan_vehicle(start, end, algo)
        stop_idx, stop_sig = self._execute_vehicle(route)
        self.cache_vehicle[key] = (route, stop_idx, stop_sig)
        return route, stop_idx, stop_sig

    # -------- 阶段二：pedestrian -----------
    def plan_pedestrian(self, start, end, algo='dijkstra'):
        key = (start, end, 'pedestrian')
        if key in self.cache_pedestrian:
            return self.cache_pedestrian[key]
        route = self._plan_pedestrian(start, end, algo)
        stop_idx, stop_sig = self._execute_pedestrian(route)
        self.cache_pedestrian[key] = (route, stop_idx, stop_sig)
        return route, stop_idx, stop_sig

    # -------- 阶段三：pedestrian → shelter -----------
    def plan_shelter(self, start, algo='multi-dijkstra'):
        key = (start, None, 'pedestrian')
        if key in self.cache_pedestrian:
            return self.cache_pedestrian[key]
        route = self._plan_shelter(start, algo)
        stop_idx, stop_sig = self._execute_pedestrian(route)
        self.cache_pedestrian[key] = (route, stop_idx, stop_sig)
        return route, stop_idx, stop_sig

    # ---- 具体每个阶段的算法 ----
    def _plan_vehicle(self, start, end, algo):
        # 可以是 RL / Dijkstra / A* 等
        pass


    def _plan_pedestrian(self, start, end, algo):
        H = self.G_pedestrian
        if not nx.has_path(H, start, end):
            return None
        if algo == 'dijkstra':
            route = nx.dijkstra_path(H, start, end, weight='weight')
        elif algo == 'astar':
            route = nx.astar_path(H, start, end, heuristic=lambda u, v=end: heuristic(u, v, H), weight='weight')
        else:
            raise ValueError(f"Unsupported algo: {algo}")
        return route


    def _plan_shelter(self, start, algo='multi-dijkstra'):
        """
        阶段三：步行到最近的 shelter
        - 输入: start (tuple)
        - 输出: best_path (list of nodes)
        """
        H = self.G_pedestrian  # 已经剔除 flooded 边的图
        if not hasattr(self, 'shelters') or len(self.shelters) == 0:
            raise ValueError("Shelters not defined in Planner.")

        # 多目标 Dijkstra
        if algo == 'multi-dijkstra':
            try:
                lengths, paths = nx.multi_target_dijkstra(H, sources=[start], targets=self.shelters,
                                                          weight='weight')
                if len(lengths) == 0:
                    return None
                nearest_shelter = min(lengths, key=lengths.get)
                best_path = paths[nearest_shelter]
            except nx.NetworkXNoPath:
                return None

        # RRT/PRM Hybrid 采样法
        elif algo == 'rrt-prm':
            # RRT 树初始化
            tree_nodes = [start]
            tree_edges = {}
            node_coords = np.array(list(H.nodes))

            def nearest_node(sample):
                return min(tree_nodes, key=lambda n: (n[0] - sample[0]) ** 2 + (n[1] - sample[1]) ** 2)
            # 随机采样扩展 RRT
            max_samples = min(self.sample_size, len(H.nodes))  # 限制采样数量
            for _ in range(max_samples):
                sample = tuple(random.choice(node_coords))
                nearest = nearest_node(sample)
                if H.has_edge(nearest, sample):
                    tree_nodes.append(sample)
                    tree_edges[sample] = nearest

            # 构建 PRM 局部图
            G_prm = nx.DiGraph()
            for n in tree_nodes:
                G_prm.add_node(n)
            for n in tree_nodes:
                # 最近 5 个邻居尝试连接
                dists = sorted(tree_nodes, key=lambda x: (x[0] - n[0]) ** 2 + (x[1] - n[1]) ** 2)
                for m in dists[1:6]:
                    if H.has_edge(n, m):
                        G_prm.add_edge(n, m, weight=H.edges[n, m]['weight'])

            # 寻找最近 shelter
            best_path, best_cost = None, float('inf')
            for s in self.shelters:
                if not nx.has_path(G_prm, start, s):
                    continue
                path = nx.dijkstra_path(G_prm, start, s, weight='weight')
                cost = nx.path_weight(G_prm, path, weight='weight')
                if cost < best_cost:
                    best_cost, best_path = cost, path
        else:
            raise ValueError(f"Unsupported algo: {algo}")

        return best_path

    # ---- 执行逻辑 ----
    def _execute_vehicle(self, route):
        # 遇到 flooded/crash 停下
        pass

    def _execute_pedestrian(self, route):
        if route:
            return len(route)-1, True
        else:
            return 0, True