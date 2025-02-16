from . import logger

import re



def save_routes(start_coords, route, file_path):
    with open(file_path, "a") as file:
        if route:
            logger.info(f"Succeed from {start_coords} to {route[-1]} \n")
            file.write(",".join(map(str, route)) + "\n")
        else:
            logger.info(f"Failed at {start_coords}\n")
            file.write(f"No valid path found for start point {start_coords} \n")


def load_routes(file_path):
    logger.info(f"Read routes from {file_path}")
    paths = []
    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            line = line.replace('[', '(').replace(']', ')')  # 替换方括号为圆括号
            if not line:
                continue
            if line.startswith("No valid path"):
                continue
            # 如果路径有效，将每个坐标点拆分并转换为数字
            try:
                points = re.findall(r'\((-?\d*\.?\d+),\s*(-?\d*\.?\d+)\)', line)
                route = [(float(x), float(y)) for x, y in points]
                # 添加有效的路径
                if route:
                    # logger.debug(f"Extract Route: {route}")
                    paths.append(route)
            except Exception as e:
                logger.error(f"Error processing line: {line}. Error: {e}")
    return paths

