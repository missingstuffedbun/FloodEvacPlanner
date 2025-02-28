from src.algorithms.algorithm import Algorithm
from src.algorithms import convert_path_to_coordinates, convert_tree_to_coords
from src.algorithms.routes import save_routes, format_routes, save_route_tree
from src.utils.config import ConfigSingleton
from src.utils.log import LoggerSingleton
from src.envs.env import Environment

import os
import random
import networkx as nx


logger = LoggerSingleton().get_logger()

class RRTAlgorithm(Algorithm):
    def __init__(self, env: Environment, config: ConfigSingleton):
        self.config = config
        self.env = env
        self.algo = 'RRT'

    def preprocess(self, **kwargs):
        logger.info(f"Preprocessing...")
        self.tag = self.config.task_id
        self.route_file = os.path.join(self.config.output_path, f"routes_{self.algo}_{self.tag}.txt")
        self.routetree_file = os.path.join(self.config.output_path, f"routetree_{self.algo}_{self.tag}.json")
        if self.config.tags.get('shelter_tag')=='zz':
            self.end_nodes = [node for node, data in self.env.G.nodes(data=True) if data.get('node_code') == 8.0]
        elif self.config.tags.get('shelter_tag')=='plan':
            self.end_nodes = [node for node, data in self.env.G.nodes(data=True) if data.get('node_code') == 8.0 or data.get('node_code') == 171.0]
        self.start_nodes = [node for node, data in self.env.G.nodes(data=True) if data.get('node_code') == 1283.0]


    def run(self):
        logger.info(f"Start {self.algo} Algorithm...")
        route_tree_dict = {}
        for start in self.start_nodes:
            logger.debug(f"Start from node {start}")
            route, route_tree = self.plan_RRT(G=self.env.G, start=start, ends=self.end_nodes, max_iterations=500)
            save_routes(start_coords=start, route=convert_path_to_coordinates(route), file_path=self.route_file)
            route_tree_dict[start] = route_tree
        save_route_tree(route_tree=convert_tree_to_coords(route_tree), file_path=self.routetree_file)

    def plan_RRT(self, G, start=None, ends=None, max_iterations=1000):
        """
        RRT路径规划，目标是到达多个可能的终点中的任意一个附近
        :param start: 起点
        :param ends: 终点列表
        :param max_iterations: 最大迭代次数
        :return: 路径列表和route_tree
        """
        # 初始化树
        tree = {start: None}  # 树用一个字典表示，key是节点，value是父节点
        parent = {start: None}  # 记录每个节点的父节点
        route_tree = {}  # 用于记录整个搜索过程的树结构
        found = False

        for _ in range(max_iterations):
            # 随机选择一个节点（包括起点）
            random_node = random.choice(list(G.nodes))

            # 选择树中离随机节点最近的一个节点
            nearest_node = min(tree.keys(),
                               key=lambda n: nx.shortest_path_length(G, source=n, target=random_node))

            # 获取邻近节点
            neighbors = list(G.neighbors(nearest_node))

            # 随机选择一个邻近节点扩展
            next_node = random.choice(neighbors)

            # 将新节点加入树，并记录其父节点
            tree[next_node] = nearest_node
            parent[next_node] = nearest_node

            # 存储节点ID而不是坐标
            route_tree[next_node] = nearest_node  # 存储父节点关系

            # 如果找到任意一个终点，则回溯路径
            if next_node in ends:
                found = True
                break

        # 回溯路径
        if found:
            # 使用retrace_path函数回溯路径
            path = self.retrace_path(parent, next_node)
            return path, route_tree  # 返回路径和route_tree
        else:
            return None, route_tree  # 未找到路径，返回空路径和route_tree

    def retrace_path(self, parent, end):
        """
        从目标节点开始回溯路径，直到起点。
        :param parent: 存储每个节点父节点的字典
        :param end: 目标节点
        :return: 返回一条从起点到目标的路径
        """
        route = [end]
        current_node = end
        while parent[current_node] is not None:
            current_node = parent[current_node]
            route.append(current_node)
        route.reverse()
        return route

    def postprocess(self):
        logger.info(f"Postprocessing...")
        format_routes(self.route_file)
        format_routes(self.routetree_file)


