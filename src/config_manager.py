# config_manager.py
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
            with open(path, 'r') as f:
                self.data = yaml.safe_load(f)
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
