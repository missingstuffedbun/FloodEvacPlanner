import os
import os.path
import logging

from environment import Environment
from config_manager import init_config, get_config
from agent import AgentFactory
from planner import Planner
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Environment → Planner → Agent
#                  ↑
#              Simulator → Visualizer

def destination_or_shelter(current, destination, shelters, max_distance=3000):
    # 计算到 destination 的直线距离
    dest_dist = np.linalg.norm(np.array(current) - np.array(destination))
    # 若没有任何 shelter，只能前往 destination
    if not shelters:
        return 'destination'
    # 计算到最近 shelter 的直线距离
    shelter_array = np.array(shelters)
    cur_array = np.array(current)
    dists = np.linalg.norm(shelter_array - cur_array, axis=1)
    min_idx = np.argmin(dists)
    nearest_shelter = tuple(shelter_array[min_idx])
    shelter_dist = dists[min_idx]
    # 比较距离
    if dest_dist<max_distance or dest_dist <= shelter_dist:
        return 'destination'
    else:
        return 'shelter'


if __name__ == "__main__":
    # 配置 YAML 文件路径（相对于脚本所在目录，避免运行时工作目录问题）
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
    init_config(config_file)
    config = get_config()

    env = Environment()
    planner = Planner(env)

    factory = AgentFactory()
    agents = factory.create_agents()

    # 将每个 agent 的 origin/destination 吸附到最近的路网节点（交通点坐标不保证恰好落在图上）
    node_coords = np.array(list(env.G.nodes))
    tree = env._tree if hasattr(env, '_tree') else None
    if tree is None:
        from scipy.spatial import cKDTree
        tree = cKDTree(node_coords)

    def snap(node):
        _, idx = tree.query([node[0], node[1]])
        return tuple(node_coords[idx])

    shelters = env.get_shelters()
    for agent in agents:
        agent.origin = snap(agent.origin)
        agent.destination = snap(agent.destination)
        agent.current_node = agent.origin
        agent.shelters = shelters

    for agent in agents:
        # -------- 阶段一：开车 ----------
        max_replan = config['params']['max_replan']
        while not agent.reached_destination and max_replan > 0:
            route, stop_node_id, stop_sig = planner.plan_vehicle(agent.current_node, agent.destination)
            if route is None:
                break  # 无可行驾车路径，转入 shelter 阶段
            agent.current_node = route[stop_node_id]
            agent.add_history('vehicle', route[:stop_node_id+1], stop_sig)
            max_replan -= 1
            if stop_sig:
                agent.reached_destination = True
                break

        if destination_or_shelter(agent.current_node, agent.destination, agent.shelters) == 'destination':
            # -------- 阶段二：步行到原 destination ----------
            pedestrian_route, stop_node_id, stop_sig = planner.plan_pedestrian(agent.current_node, agent.destination)
            if pedestrian_route is not None:
                agent.current_node = pedestrian_route[stop_node_id]
                agent.add_history('pedestrian', pedestrian_route[:stop_node_id+1], stop_sig)
                if stop_sig:
                    agent.reached_destination = True
        else:
            # -------- 阶段三：步行到附近 shelter ----------
            shelter_route, stop_node_id, stop_sig = planner.plan_shelter(agent.current_node)
            if shelter_route is not None:
                agent.current_node = shelter_route[stop_node_id]
                agent.add_history('pedestrian', shelter_route[:stop_node_id+1], stop_sig)
                if stop_sig:
                    agent.reached_shelter = True

        # 若全程没有任何路径记录（如起点就无路可走），补一条失败记录，避免 history 为 []
        if not agent.history:
            agent.failed = True
            agent.add_history('failed', [], False)

        # 每个 agent 都保存历史（成功/避难/失败），便于统一统计与可视化
        agent.save_history(os.path.join(config.get('output_path'), config.get('timestamp'), 'history.txt'))

