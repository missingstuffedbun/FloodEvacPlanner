import logging
import os

class LoggerSingleton:
    _instance = None
    _task_id = None
    _logs_path = None

    def __new__(cls, task_id=None, logs_path=None):
        if not cls._instance:
            if not task_id or not logs_path:
                raise ValueError("Logger requires 'task_id' and 'logs_path' for the first time initialization.")
            # 记录下第一次传入的参数
            cls._task_id = task_id
            cls._logs_path = logs_path
            cls._instance = super(LoggerSingleton, cls).__new__(cls)
            cls._instance.logger = cls._create_logger(task_id, logs_path)
        return cls._instance

    @staticmethod
    def _create_logger(task_id, logs_path):
        log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        logger = logging.getLogger(task_id)
        logger.setLevel(logging.DEBUG)

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler(os.path.join(logs_path, f"{task_id}.log"))
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)

        return logger

    def get_logger(self):
        """返回已初始化的logger"""
        return self._instance.logger
