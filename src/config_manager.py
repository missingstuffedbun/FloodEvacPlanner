# config_manager.py
import shutil
from datetime import datetime
import yaml
import os

class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self, path):
        if not self._initialized:
            with open(path, 'r', encoding='utf-8') as f:
                self.data = yaml.safe_load(f)

            # ---- 新增：创建带时间戳的输出文件夹 ----
            base_output_path = self.data.get('output_path', 'output')
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            self.data['timestamp'] = timestamp
            run_output_dir = os.path.join(base_output_path, timestamp)
            os.makedirs(run_output_dir, exist_ok=True)

            # ---- 复制 config 文件过去 ----
            shutil.copy(path, os.path.join(run_output_dir, os.path.basename(path)))

            # ---- 初始化完成标记 ----
            self._initialized = True

    def get(self, key, default=None):
        return self.data.get(key, default) if self._initialized else default

    def __getitem__(self, key):
        if not self._initialized:
            raise ValueError("Config not initialized yet")
        return self.data[key]


# 全局函数，方便直接使用
_config = Config()

def init_config(path):
    _config.initialize(path)
    return _config

def get_config():
    return _config
