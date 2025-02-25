from src.algorithms.algorithm import Algorithm
from src.algorithms import euclidean_distance 
from src.algorithms.routes import save_routes, format_routes, save_route_tree
from src.utils.config import ConfigSingleton
from src.envs.env import Environment

import os
from datetime import datetime
from shapely import LineString
import numpy as np



class RRTAlgorithm(Algorithm):
    def __init__(self, env: Environment, config: ConfigSingleton):
        self.config = config
        self.env = env
        self.algo = 'RRT'

    def preprocess(self, **kwargs):
        self.tag = "_".join(str(value) for value in self.config.tags.values())
        self.route_file = os.path.join(self.config.output_path, f"routes_{self.algo}_{self.tag}.txt")
        self.routetree_file = os.path.join(self.config.output_path, f"routetree_{self.algo}_{self.tag}.txt")
        params = {
            "step_size": 100,
            "max_iter": 3000,
            "debug": True,
        }
        params.update(kwargs)
        self.params = params

    def run(self):
        for start in self.env.spaces_coords:
            route, route_tree = self.plan_RRT(start_coords=start, **self.params)
            save_routes(start_coords=start, route=route, file_path=self.route_file)
            save_route_tree(start_coords=start, route_tree=route_tree, file_path=self.routetree_file)

    def postprocess(self):
        format_routes(self.route_file)
        format_routes(self.routetree_file)

    def retrace_path(self, parent, end):
        """
        从目标节点开始回溯路径，直到起点。
        :param parent: 存储每个节点父节点的字典
        :param end: 目标节点
        :return: 返回一条从起点到目标的路径
        """
        route = [end]
        current_node = end
        while parent[tuple(current_node)]:
            current_node = parent[tuple(current_node)]
            route.append(current_node)
        route.reverse()
        return route
        
    def plan_RRT(self, **kwargs):
        """
        RRT路径规划，目标是到达多个可能的终点中的任意一个附近
        :param kwargs: 其他参数，如步长、最大迭代次数等
        :return: 路径列表
        """
        start = np.array(self.env.start_coords)
        
        nodes = [start]
        parent = {tuple(start): None}
        route_found = False
        all_routes = []
    
        step_size = kwargs.get('step_size', 50)  # 步长
        max_iter = kwargs.get('max_iter', 1000)  # 最大迭代次数

        
        file_path=datetime.now().strftime('%Y%m%d%H%M%S')
    
        for i in range(max_iter):
            # 随机生成一个点
            rand_point = self.env.generate_random_point()
    
            # 找到距离随机点最近的节点
            nearest_node = min(nodes, key=lambda node: euclidean_distance(node, rand_point))
    
            # 计算从最近节点到随机点的单位向量
            direction = np.array(rand_point) - np.array(nearest_node)
            distance = np.linalg.norm(direction)
            direction /= distance  # 单位化
    
            # 如果距离太远，则按步长限制扩展的长度
            step = min(step_size, distance)
            new_node = np.array(nearest_node) + direction * step
    
            # 判断路径段是否经过障碍物或避难所
            condition, obj = self.env.step_condition(nearest_node, new_node)
            if condition in ["river", "flood", "map"]: # building穿过去也合理，太多building了
                continue
    
            if condition == "shelter":
                new_node = (obj.centroid.x, obj.centroid.y)
                route_found = True
                end = new_node
    
                # 将新节点加入到树中
                nodes.append(tuple(new_node))
                parent[tuple(new_node)] = tuple(nearest_node)
                # 保存所有路径
                all_routes.append([nearest_node, new_node])
                lines = [LineString(route) for route in all_routes]
    
            # 将新节点加入到树中
            nodes.append(tuple(new_node))
            parent[tuple(new_node)] = tuple(nearest_node)
            all_routes.append([nearest_node, new_node])
            lines = [LineString(route) for route in all_routes]
            
        route = self.retrace_path(parent, end) if route_found else None
        return route, all_routes

        
