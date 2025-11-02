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
        self.reached_destination = False
        self.reached_shelter = False
        self.failed = False      # 不再继续进行
        self.history = []        # 记录每一步节点，用于可视化或统计 {mode, exec_route, stop_sig}
        self.attempts = 0        # 尝试重新规划次数（针对 shelter）

    def add_history(self, mode, exec_route, stop_sig):
        self.history.append({'mode':mode, 'exec_route':exec_route, 'stop_sig':stop_sig})

    def add_attempts(self):
        self.attempts += 1

    def __getattribute__(self, __name):
        return super().__getattribute__(__name)