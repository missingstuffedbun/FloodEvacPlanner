import yaml
import os

# 获取config.yaml文件的路径
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.yaml')


# 加载 YAML 配置文件并解析为字典
def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)

    # 转换为绝对路径
    if 'input_path' in config:
        config['input_path'] = os.path.abspath(config['input_path'])
    if 'output_path' in config:
        config['output_path'] = os.path.abspath(config['output_path'])

    return config


# 读取配置文件
config = load_config(CONFIG_FILE_PATH)

# 将配置文件中的键值对提取为变量
input_path = config.get('input_path')
output_path = config.get('output_path')

files = config.get('files', {})

# 获取文件配置，若键不存在，返回 None
spaces = files.get('spaces', None)
shelters = files.get('shelters', None)
map_file = files.get('map', None)
buildings = files.get('buildings', None)
rivers = files.get('rivers', None)
roads = files.get('roads', None)
road_nodes = files.get('road_nodes', None)
floods = files.get('floods', None)

