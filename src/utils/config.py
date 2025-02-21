import os
import yaml
from datetime import datetime
import random


class ConfigSingleton:
    _instance = None  # 类变量，用于存储唯一实例

    def __new__(cls, config_file_path=None):
        # 只在第一次创建实例时初始化
        if not cls._instance:
            if config_file_path is None:
                raise ValueError("config_file_path must be provided during first initialization")
            cls._instance = super(ConfigSingleton, cls).__new__(cls)
            cls._instance._initialize(config_file_path)
        return cls._instance

    def _initialize(self, config_file_path):
        # 初始化配置
        self.config_file_path = config_file_path
        self.config = self.load_config(config_file_path)

        # 提取常用配置项
        self.task_id = self.config.get('tasks_id', datetime.now().strftime('%Y%m%d%H%M%S'))
        self.tasks = self.config.get('tasks', {})
        
        self.project_path = os.path.abspath(self.config.get('project_path', '../..'))
        self.logs_path = os.path.join(self.project_path, self.config.get('logs_path', 'logs'))
        self.input_path = os.path.join(self.project_path, self.config.get('input_path', 'input'))
        self.output_path = os.path.join(self.project_path, self.config.get('output_path', 'output'), self.task_id)
        
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        self.shp_files = self.config.get('shp_files', {})
        self.gml_files = self.config.get('gml_files', {})

        self.random_seed = self.config.get('random_seed', 2025)
        random.seed(self.random_seed)
        
        self.tags = self.config.get('tags', {})

        

    def load_config(self, file_path):
        """
        读取配置文件并返回配置内容
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found at {file_path}")

        with open(file_path, 'r') as file:
            return yaml.safe_load(file)

    def get(self, key, default=None):
        """
        获取配置文件中的值，若不存在则返回默认值
        """
        return self.config.get(key, default)

    def __getattr__(self, item):
        """
        动态获取配置项的值。如果项不存在，返回 None。
        :param item: 配置项的名称（如 'tags'等）
        :return: 配置项的值，如果不存在则返回 None
        """
        return self.files_data.get(item, None)

    def get_config(self):
        """返回已初始化的logger"""
        return self._instance

