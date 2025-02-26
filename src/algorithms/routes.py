import ast
import os

from src.utils.log import LoggerSingleton


logger = LoggerSingleton().get_logger()


def save_routes(start_coords, route, file_path):
    with open(file_path, "a") as file:
        if route:
            logger.debug(f"Succeed from {route[0]} to {route[-1]} \n")
            file.write(",".join(map(str, route)) + "\n")
        else:
            logger.debug(f"Failed at {start_coords}\n")
            file.write(f"{start_coords} \n")


def format_routes(file_path):
    """格式化路径文件，将路径转换为list of tuples"""
    if not os.path.exists(file_path):
        return

    processed_paths = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            # 使用 ast.literal_eval 解析路径字符串
            try:
                # 尝试将整个路径字符串解析为列表的坐标元组
                # 首先去除路径中的多余空格
                path_coords = ast.literal_eval('[' + line.replace('),[', '), (').replace('[', '(').replace(']', ')') + ']')
                # 检查解析后的内容是否为有效路径
                if isinstance(path_coords, list) and all(isinstance(pt, tuple) and len(pt) == 2 for pt in path_coords):
                    processed_paths.append(path_coords)
            except (ValueError, SyntaxError) as e:
                # 如果解析失败，输出错误日志（可选）
                logger.error(f"Error processing line: {line}. Error: {e}")

    # 输出处理后的路径，可以保存为新的文件或替换原文件
    with open(file_path, 'w') as file:
        for path in processed_paths:
            file.write(f"{path}\n")  # 写入处理后的路径


def load_routes(file_path):
    # logger.info(f"Reading routes from {file_path}")
    paths = []

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            
            try:
                # 使用 ast.literal_eval 安全地解析路径字符串为 Python 数据结构
                route = ast.literal_eval(line)
                # 确保 route 中每个元素都是元组形式的坐标
                if all(isinstance(coord, tuple) and len(coord) == 2 for coord in route):
                    paths.append(route)
                else:
                    pass
                    # logger.warning(f"Invalid route format in line: {line}")
            except (ValueError, SyntaxError) as e:
                pass
                # logger.error(f"Error processing line: {line}. Error: {e}")
    return paths


