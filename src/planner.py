import networkx as nx
import numpy as np
import random

def compute_vehicle_weights(G):
    for u, v, data in G.edges(data=True):
        length = data.get('length', 0)
        speed = data.get('max_speed', 30)
        lane = data.get('lane', 2)
        special = data.get('special_ro', None)

        flooded = G.nodes[u].get('flooded', False)
        crash = G.nodes[u].get('crash', False)

        # 基础行驶时间（分钟）
        base_time = length / (speed * 1000 / 60)  # km/h → min
        lane_penalty = 0.02 * max(lane - 2, 0)
        crash_penalty = 0.3 if crash else 0
        flood_penalty = 0.6 if flooded else 0
        special_penalty = 0.1 if special else 0

        vehicle_time = base_time * (1.0 + lane_penalty + crash_penalty + flood_penalty + special_penalty)
        vehicle_length = length * (1.0 + crash_penalty + flood_penalty)
        data['vehicle_time'] = vehicle_time
        data['vehicle_length'] = vehicle_length

    return G


def compute_pedestrian_weights(G):
    for u, v, data in G.edges(data=True):
        # 节点坐标（若没有则用length代替）
        dist = data.get('length', None)
        if dist is None:
            dist = ((u[0] - v[0])**2 + (u[1] - v[1])**2)**0.5

        # 属性惩罚
        special = data.get('special_ro', None)
        special_penalty = 0.3 if special else 0

        # 附近高限速道路惩罚
        max_speed_penalty = 0
        for nbr in G.neighbors(u):
            edge_data = G.get_edge_data(u, nbr)
            if edge_data and edge_data.get('max_speed', 100) > 50:
                max_speed_penalty = 0.2
                break

        # 按照 1.5m/s 步行速度计算
        pedestrian_time = dist * (1.0 + special_penalty + max_speed_penalty) / 90
        pedestrian_length = dist
        data['pedestrian_time'] = pedestrian_time
        data['pedestrian_length'] = pedestrian_length

    return G



class Planner:
    def __init__(self, env):
        self.G = env.G
        self.G_vehicle = compute_vehicle_weights(env.G_vehicle)
        self.G_pedestrian = compute_pedestrian_weights(env.G_pedestrian)
        self.shelters = env.get_shelters()
        self.cache_vehicle = {}  # {(start_node, end_node): route}
        self.cache_pedestrian = {}  # {(start_node, end_node): route}

        random.seed(env.params.get('random_seed', 2025))
        self.sample_size = env.params.get('random_seed', 200)


    # -------- 阶段一：vehicle -----------
    def plan_vehicle(self, start: tuple[float], end: tuple[float], algo: str='dijkstra'):
        key = (start, end, 'vehicle')
        if key in self.cache_vehicle:
            return self.cache_vehicle[key]
        route = self._plan_vehicle(start, end, algo)
        if not route:
            return None, 0, False
        stop_idx, stop_sig = self._execute_vehicle(route)
        self.cache_vehicle[key] = (route, stop_idx, stop_sig)
        return route, stop_idx, stop_sig

    # -------- 阶段二：pedestrian -----------
    def plan_pedestrian(self, start: tuple[float], end: tuple[float], algo: str='dijkstra'):
        key = (start, end, 'pedestrian')
        if key in self.cache_pedestrian:
            return self.cache_pedestrian[key]
        route = self._plan_pedestrian(start, end, algo)
        if not route:
            return None, 0, False
        stop_idx, stop_sig = self._execute_pedestrian(route)
        self.cache_pedestrian[key] = (route, stop_idx, stop_sig)
        return route, stop_idx, stop_sig

    # -------- 阶段三：pedestrian → shelter -----------
    def plan_shelter(self, start: tuple[float], algo: str='multi-dijkstra'):
        key = (start, None, 'pedestrian')
        if key in self.cache_pedestrian:
            return self.cache_pedestrian[key]
        route = self._plan_shelter(start, algo)
        if not route:
            return None, 0, False
        stop_idx, stop_sig = self._execute_pedestrian(route)
        self.cache_pedestrian[key] = (route, stop_idx, stop_sig)
        return route, stop_idx, stop_sig

    # ---- 具体每个阶段的算法 ----

    def _plan_vehicle(self, start, end, algo='dijkstra', weight='time'):
        """
        Phase 1 planning: 基于期望代价的 Dijkstra
        返回 route: list of nodes 或 None
        """
        H = self.G_vehicle
        print(start, end)
        if not (H.has_node(start) and H.has_node(end)):
            print("Node not found")
            return None
        if not nx.has_path(H, start, end):
            return None
        if algo == 'dijkstra':
            route = nx.dijkstra_path(H, start, end, weight=f'vehicle_{weight}')
        elif algo == 'astar':
            route = nx.astar_path(
                H, start, end,
                heuristic=lambda u=start, v=end: ((u[0] - v[0])**2 + (u[1] - v[1])**2)**0.5,
                weight=f'vehicle_{weight}'
            )
        else:
            raise ValueError(f"Unsupported algo: {algo}")
        return route


    def _execute_vehicle(self, route):
        if not route:
            return 0, False
        H = self.G_vehicle
        # route 是节点序列，边是 route[i] -> route[i+1]
        for i in range(len(route)-1):
            u = route[i]
            v = route[i+1]
            if H.edges[u,v].get('blocked', False):
                return i, False
            if H.edges[u,v].get('flooded', False) or H.nodes[v].get('crash', False):
                self.G_vehicle.edges[u,v]['blocked'] = True
                return i, False
        return len(route)-1, True

    def _plan_pedestrian(self, start, end, algo='dijkstra', weight='time'):
        H = self.G_pedestrian
        if not nx.has_path(H, start, end):
            return None
        if algo == 'dijkstra':
            route = nx.dijkstra_path(H, start, end, weight=f'pedestrian_{weight}')
        elif algo == 'astar':
            route = nx.astar_path(
                H, start, end,
                heuristic=lambda u=start, v=end: ((u[0] - v[0])**2 + (u[1] - v[1])**2)**0.5,
                weight=f'pedestrian_{weight}'
            )
        else:
            raise ValueError(f"Unsupported algo: {algo}")
        return route


    def _plan_shelter(self, start, algo='multi-dijkstra', weight='time'):
        """
        阶段三：步行到最近的 shelter
        - 输入: start (tuple)
        - 输出: best_path (list of nodes)
        """
        H = self.G_pedestrian  # 已经剔除 flooded 边的图
        # 多目标 Dijkstra
        if algo == 'multi-dijkstra':
            try:
                lengths, paths = nx.multi_target_dijkstra(
                    H, sources=[start], targets=self.shelters,
                    weight=f'pedestrian_{weight}'
                )
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
                        G_prm.add_edge(n, m, weight=H.edges[n, m][f'pedestrian_{weight}'])

            # 寻找最近 shelter
            best_path, best_cost = None, float('inf')
            for s in self.shelters:
                if not nx.has_path(G_prm, start, s):
                    continue
                path = nx.dijkstra_path(G_prm, start, s, weight=f'pedestrian_{weight}')
                cost = nx.path_weight(G_prm, path, weight=f'pedestrian_{weight}')
                if cost < best_cost:
                    best_cost, best_path = cost, path
        else:
            raise ValueError(f"Unsupported algo: {algo}")

        return best_path


    def _execute_pedestrian(self, route):
        if route:
            return len(route)-1, True
        else:
            return 0, True