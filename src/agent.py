from config_manager import get_config
import geopandas as gpd
import os


class AgentFactory:
    def __init__(self):
        # 使用全局 singleton config
        config = get_config()
        self.params = config.get('params', {})

        # 加载起点交通点
        traffic_path = os.path.join(
            config.get('project_path'),
            config.get('input_path'),
            config.get('files')['traffic']
        )
        self.traffic = gpd.read_file(traffic_path)
        # 解析 origins/destinations
        self.origins, self.destinations = self._parse_traffic()
        print(f"Parsed {len(self.origins)} origin-destination pairs.")

    def _parse_traffic(self):
        origins_np = self.traffic[['ORIGIN_X', 'ORIGIN_Y']].to_numpy()
        destinations_np = self.traffic.geometry.apply(lambda p: (p.x, p.y)).to_numpy()
        origins = [tuple(x) for x in origins_np]
        destinations = [tuple(x) for x in destinations_np]
        return origins, destinations

    def create_agents(self):
        agents = []
        for i, (origin, destination) in enumerate(zip(self.origins, self.destinations), start=1):
            agent = Agent(agent_id=i, origin=origin, destination=destination)
            agents.append(agent)
        return agents


class Agent:
    def __init__(self, agent_id, origin, destination):
        self.id = agent_id
        self.origin = origin
        self.destination = destination
        self.current_node = origin
        self.route = []          # 当前规划路线（节点列表）
        self.mode = 'vehicle'    # 当前移动方式：'vehicle' 或 'pedestrian'
        self.reached_destination = False
        self.reached_shelter = False
        self.failed = False      # 不再继续进行
        self.history = []        # 记录每一步节点，用于可视化或统计 {mode, route, exec_route}
        self.attempts = 0        # 尝试重新规划次数（针对 shelter）


    def plan_route(self):
        # 调用 Planner 计算 route（vehicle/pedestrian/shelter）
        pass

    def execute_route(self):
        pass

    def is_finished(self):
        # 返回是否已经到达 destination/shelter/失败
        pass