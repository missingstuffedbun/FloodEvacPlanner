import yaml
import logging
import os

# 获取config.yaml文件的路径
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.yaml')

# 加载 YAML 配置文件并解析为字典
def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


# 读取配置文件
config = load_config(CONFIG_FILE_PATH)

# 将配置文件中的键值对提取为变量
project_path = os.path.abspath(config.get('project_path', '../..'))
input_path = os.path.join(project_path, config.get('input_path', '/input'))
output_path = os.path.join(project_path, config.get('output_path', '/output'))
logs_path = os.path.join(project_path, config.get('logs_path', '../logs'))

shp_files = config.get('shp_files', {})
gml_files = config.get('gml_files', {})

random_seed = config.get('random_seed', 2025)

tags = config.get('tags', {})

# 设置日志的格式
log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def get_logger(module_name):
    """
    为指定模块获取一个 logger 实例，并分别配置文件和控制台输出。

    :param module_name: 模块名，用于标识日志的来源
    :return: logger 实例
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)  # 设置默认日志级别为 DEBUG

    # 控制台输出，设置级别为 INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    # 文件输出，设置级别为 DEBUG
    log_file_path = os.path.join(logs_path, f"{module_name}.log")
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    return logger
