import networkx as nx


class Planner:
    def __init__(self, env):
        self.G = env.G
        self.G_vehicle = env.G_vehicle
        self.G_pedestrian = env.G_pedestrian
        self.shelters = env.get_shelters()
        self.cache_vehicle = {}  # {(start_node, end_node): route}
        self.cache_pedestrian = {}  # {(start_node, end_node): route}

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
    def plan_shelter(self, start, algo='dijkstra'):
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
        # 确定性最短路
        pass

    def _plan_shelter(self, start, algo):
        # 找最近 shelter 的最短路
        pass

    # ---- 执行逻辑 ----
    def _execute_vehicle(self, route):
        # 遇到 flooded/crash 停下
        pass

    def _execute_pedestrian(self, route):
        if route:
            return len(route)-1, True
        else:
            return 0, True