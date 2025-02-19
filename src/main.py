from src.utils.config import get_logger, tags, output_path
from src.envs.env import Environment
from src.algorithms.Dijkstra import find_nearest_shelter, find_nodes_nearby, plan_Dijkstra, convert_path_to_coordinates
from src.algorithms.routes import save_routes

import os


tag = "_".join(str(value) for value in tags.values())
# 获取当前模块的 logger
logger = get_logger(tag)


def main():
    logger.info(f"Load environment for {tag}")
    env = Environment()
    env.preprocessing()
    env.graph_for_Dijkstra()

    shelters_coords = env.shelters_coords
    spaces_coords = env.spaces_coords
    graph = env.graph_Dijkstra

    route_file = os.path.join(output_path, f"routes_Dijkstra_{tag}.txt")
    paths = dict()
    for space_coords in spaces_coords:
        nearest_shelter = find_nearest_shelter(coords=space_coords, shelters_coords=shelters_coords, distance_threshold=100)
        if nearest_shelter:
            save_routes(start_coords=space_coords, route=[space_coords, nearest_shelter], file_path=route_file)
            continue
        start_nodes = find_nodes_nearby(G=graph, coords=space_coords, distance_threshold=100, ignore_flood=True)
        best_route = None
        best_route_weight = float('inf')
        best_shelter = None
        for start in start_nodes:
            for shelter_coords in env.shelters_coords:
                end_nodes = find_nodes_nearby(G=graph, coords=shelter_coords, distance_threshold=100, ignore_flood=True)
                for end in end_nodes:
                    if (start, end) in paths.keys():
                        path_weight = paths[(start, end)]['weight']
                        if best_route_weight > path_weight:
                            best_route_weight = path_weight
                            best_route = paths[(start, end)]['path']
                            best_shelter = paths[(start, end)]['shelter']
                        continue
                    path, path_weight = plan_Dijkstra(G=graph, start=start, end=end)
                    paths[(start, end)] = {'path': path, 'weight': path_weight, 'shelter': shelter_coords}
                    if best_route_weight > path_weight:
                        best_route_weight = path_weight
                        best_route = path
                        best_shelter = shelter_coords
        route = convert_path_to_coordinates(G=graph, path=best_route, start_coords=space_coords, end_coords=best_shelter)
        save_routes(start_coords=space_coords, route=route, file_path=route_file)
    logger.info(f"================= THE END =================")


if __name__ == "__main__":
    main()