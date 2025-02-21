from abc import ABC, abstractmethod

class Algorithm(ABC):
    def __init__(self, env, config):
        """
        初始化算法，env 和 config 是必须的参数。
        :param env: 环境配置
        :param config: 配置参数
        """
        self.env = env
        self.config = config

    @abstractmethod
    def preprocess(self):
        """
        预处理步骤：子类可以覆盖此方法进行特定数据预处理。
        """
        pass

    @abstractmethod
    def run(self):
        """
        运行算法的核心步骤
        :return: None
        """
        pass

    @abstractmethod
    def postprocess(self):
        """
        后处理步骤：子类可以覆盖此方法进行结果的后处理。
        """
        pass


class AlgorithmFactory:
    @staticmethod
    def create_algorithm(algorithm_type, env, config):
        if algorithm_type == 'Dijkstra':
            from src.algorithms.Dijkstra import DijkstraAlgorithm
            return DijkstraAlgorithm(env, config)
        # elif algorithm_type == 'AStar':
        #     return AStarAlgorithm(env, config)
        else:
            raise ValueError("Unknown algorithm type")
