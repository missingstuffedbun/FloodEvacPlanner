from abc import ABC, abstractmethod

from src.utils.config import ConfigSingleton
from src.utils.log import LoggerSingleton
import os


class TaskContext:
    def __init__(self, config=None, config_path=None, env=None, algo=None):
        self.config = ConfigSingleton(config_path).get_config() if config_path else config
        self.config.save_config(os.path.join(self.config.output_path, 'config.yaml'))
        self.env = env
        self.algo = algo
        self.logger = LoggerSingleton(task_id=self.config.task_id, logs_path=self.config.logs_path)


class Task(ABC):
    def __init__(self, context: TaskContext, next_task=None):
        self.context = context
        self.next_task = next_task  # 链接下一个任务

    @abstractmethod
    def execute(self, context: TaskContext):
        if self.next_task:
            self.next_task.execute(context)  # 执行下一个任务

    def add_task(self, task: 'Task'):
        self.next_task = task  # 将当前任务的 next_task 设置为传入的 task


class LoadEnvironmentTask(Task):
    def execute(self, context: TaskContext):
        from src.envs.env import Environment
        
        self.context.env = Environment()
        self.context.env.preprocessing()
        super().execute(context)



class PathPlanningTask(Task):
    def execute(self, context: TaskContext):
        from src.algorithms.algorithm import AlgorithmFactory

        self.context.algo_name = self.context.config.tasks.get('RUN_ALGO', None)
        if not self.context.algo_name:
            raise ValueError("Algorithm name (algo_name) is required for PathPlanningTask.")
            
        algo = AlgorithmFactory.create_algorithm(self.context.algo_name, self.context.env, self.context.config)
        algo.preprocess()
        algo.run()
        algo.postprocess()
        self.context.algo = algo
        super().execute(context)


class RouteVisualizationTask(Task):
    def execute(self, context: TaskContext):
        from src.utils.visualize import Visualize, EnvironmentLayer, GraphLayer, RouteLayer
        from src.algorithms.routes import load_routes
        import os

        route_file = self.context.algo.route_file if self.context.algo else os.path.join(self.context.config.project_path, self.context.config.tasks.get('VIS_ROUTE'))
        self.context.route_file = route_file
        routes = load_routes(route_file)
        environment_layer = EnvironmentLayer(self.context.env)
        G = self.context.env.flooded_graph if self.context.env.flooded_graph else f"{self.context.env.graph}_env"
        graph_layer = GraphLayer(G=G)
        route_layer = RouteLayer(routes=routes)
        output_name = self.context.algo.route_file if self.context.algo else self.context.config.task_id
        vis = Visualize(environment_layer=environment_layer, graph_layer=graph_layer, route_layer=route_layer, output_name=output_name)
        vis.plot()
        super().execute(context)


class RouteTreeVisualizationTask(Task):
    def execute(self, context: TaskContext):
        from src.utils.visualize import Visualize, EnvironmentLayer, GraphLayer, RouteLayer
        from src.algorithms.routes import load_route_tree
        import os

        route_file = self.context.algo.routetree_file if self.context.algo else os.path.join(self.context.config.project_path, self.context.config.tasks.get('VIS_TREE'))
        self.context.route_file = route_file
        route_tree = load_route_tree(route_file)
        environment_layer = EnvironmentLayer(self.context.env)
        G = self.context.env.flooded_graph if self.context.env.flooded_graph else f"{self.context.env.graph}_env"
        graph_layer = GraphLayer(G=G, plot_set=['edges'])
        for node, tree in route_tree.items():
            route_layer = RouteLayer(route_tree=route_tree)
            output_name = self.context.algo.routetree_file if self.context.algo else self.context.config.task_id
            output_name = f"{output_name}_{node}"
            vis = Visualize(environment_layer=environment_layer, graph_layer=graph_layer, route_layer=route_layer, output_name=output_name)
            vis.plot()
        super().execute(context)



class EnvVisualizationTask(Task):
    def execute(self, context: TaskContext):
        from src.utils.visualize import Visualize, EnvironmentLayer, GraphLayer

        G = self.context.env.flooded_graph if self.context.env.flooded_graph else self.context.env.graph
        environment_layer = EnvironmentLayer(self.context.env)
        graph_layer = GraphLayer(G=G, plot_set=['edges', 'nodes'])
        output_name = self.context.algo.route_file if self.context.algo else self.context.config.task_id
        vis = Visualize(environment_layer=environment_layer, graph_layer=graph_layer, route_layer=None, output_name=output_name)
        vis.plot()
        super().execute(context)


class RouteAnalysisTask(Task):
    def execute(self, context: TaskContext):
        from src.algorithms.routes import load_routes
        from src.envs.graph import route_stats_with_graph, congestion_level_analysis
        import networkx as nx
        if self.context.config.tasks.get('ANAL_ROUTE') is True:
            route_file = self.context.route_file
        else:
            os.path.join(self.context.config.output_path, self.context.config.tasks.get('ANAL_ROUTE'))
        if route_file is None:
            raise ValueError("Route file (route_file) is required for RouteAnalysisTask.")
        routes = load_routes(route_file)
        G, route_stats = route_stats_with_graph(self.context.env.graph, routes)
        nx.write_gml(G, os.path.join(self.context.config.output_path, 'graph_route.gml'))
        route_stats.to_csv(os.path.join(self.context.config.output_path, 'route_stats.csv'), index=False)
        congestion_levels = congestion_level_analysis(G, bins=4)
        congestion_levels.to_csv(os.path.join(self.context.config.output_path, 'congestion_levels.csv'), index=False)




TASK_MAPPING = {
    'LOAD_ENV': LoadEnvironmentTask,
    'VIS_ENV': EnvVisualizationTask,
    'RUN_ALGO': PathPlanningTask,
    'VIS_ROUTE': RouteVisualizationTask,
    'VIS_TREE': RouteTreeVisualizationTask,
    'ANAL_ROUTE': RouteAnalysisTask,
}

# 根据配置动态生成任务链
def create_task_chain(task_types, context, **kwargs):
    head_task = None
    prev_task = None

    # 遍历任务类型配置，生成任务链
    for task_type in task_types:
        # 查找任务类型对应的任务类
        task_class = TASK_MAPPING.get(task_type)
        if task_class:
            # 实例化任务
            new_task = task_class(context=context, **kwargs)
            if not head_task:
                head_task = new_task  # 第一个任务
            if prev_task:
                prev_task.add_task(new_task)  # 将前一个任务的 next_task 设置为当前任务
            prev_task = new_task  # 更新 prev_task 为当前任务
    
    return head_task
