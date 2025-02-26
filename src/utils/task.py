from abc import ABC, abstractmethod

from src.utils.config import ConfigSingleton
from src.utils.log import LoggerSingleton


class TaskContext:
    def __init__(self, config=None, config_path=None, env=None, algo=None):
        self.config = ConfigSingleton(config_path).get_config() if config_path else config
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
        routes = load_routes(route_file)
        environment_layer = EnvironmentLayer(self.context.env)
        G = self.context.env.flooded_graph if self.context.env.flooded_graph else self.context.env.graph
        graph_layer = GraphLayer(G=G)
        route_layer = RouteLayer(routes=routes)
        output_name = self.context.algo.route_file if self.context.algo else None
        vis = Visualize(environment_layer=environment_layer, graph_layer=graph_layer, route_layer=route_layer, output_name=output_name)
        vis.plot()
        super().execute(context)


class EnvVisualizationTask(Task):
    def execute(self, context: TaskContext):
        from src.utils.visualize import Visualize, EnvironmentLayer, GraphLayer

        G = self.context.env.flooded_graph if self.context.env.flooded_graph else self.context.env.graph
        environment_layer = EnvironmentLayer(self.context.env)
        graph_layer = GraphLayer(G=G, plot_set=['edges', 'nodes'])
        output_name = self.context.algo.route_file if self.context.algo else None
        vis = Visualize(environment_layer=environment_layer, graph_layer=graph_layer, route_layer=None, output_name=output_name)
        vis.plot()
        super().execute(context)


TASK_MAPPING = {
    'LOAD_ENV': LoadEnvironmentTask,
    'VIS_ENV': EnvVisualizationTask,
    'RUN_ALGO': PathPlanningTask,
    'VIS_ROUTE': RouteVisualizationTask,
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
