import os.path

from environment import Environment
from config_manager import init_config, get_config
from agent import AgentFactory
from src.planner import Planner
import numpy as np

# Environment → Planner → Agent
#                  ↑
#              Simulator → Visualizer

def destination_or_shelter(current, destination, shelters, max_distance=3000):
    # 计算到 destination 的直线距离
    dest_dist = np.linalg.norm(np.array(current) - np.array(destination))
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
    # 配置 YAML 文件路径
    config_file = "config.yaml"
    init_config(config_file)
    config = get_config()

    env = Environment()
    planner = Planner(env)

    factory = AgentFactory()
    agents = factory.create_agents()

    for agent in agents:
        # -------- 阶段一：开车 ----------
        max_replan = config['params']['max_replan']
        while not agent.reached_destination and max_replan > 0:
            route, stop_node_id, stop_sig = planner.plan_vehicle(agent.origin, agent.destination)
            agent.current_node = route[stop_node_id]
            agent.history.append('vehicle', route[:stop_node_id+1], stop_sig)
            max_replan -= 1
            if stop_sig:
                agent.reached_destination = True
                break

        if destination_or_shelter(agent.current_node, agent.destination, agent.shelters) == 'destination':
            # -------- 阶段二：步行到原 destination ----------
            pedestrian_route, stop_node_id, stop_sig = planner.plan_pedestrian(agent.current_node, agent.destination)
            agent.current_node = route[stop_node_id]
            agent.history.append('pedestrian', route[:stop_node_id+1], stop_sig)
            if stop_sig:
                agent.reached_destination = True
                continue
        else:
            # -------- 阶段三：步行到附近 shelter ----------
            shelter_route, stop_node_id, stop_sig = planner.plan_shelter(agent.current_node)
            agent.current_node = route[stop_node_id]
            agent.history.append('pedestrian', route[:stop_node_id+1], stop_sig)
            if stop_sig:
                agent.reached_shelter = True
                continue

        agent.failed = True
        agent.save_history(os.path.join(config.get('output_path'), config.get('timestamp'), 'history.txt'))

