import logging
from logging.handlers import RotatingFileHandler
import os

# 创建日志目录（如果不存在）
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# 创建一个日志记录器
logger = logging.getLogger(__name__)

# 设置日志的最低级别
logger.setLevel(logging.DEBUG)

# 创建控制台处理器（StreamHandler），将日志输出到控制台
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # 设置控制台日志级别

# 创建文件处理器（RotatingFileHandler），将日志输出到文件
log_file = os.path.join(LOG_DIR, 'RoutePlanning.log')
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)  # 最大5MB，最多保留3个备份
file_handler.setLevel(logging.DEBUG)  # 设置文件日志级别

# 设置日志格式
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 将处理器添加到logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 示例日志
if __name__ == "__main__":
    logger.debug("这是一个调试级别的日志")
    logger.info("这是一个信息级别的日志")
    logger.warning("这是一个警告级别的日志")
    logger.error("这是一个错误级别的日志")
    logger.critical("这是一个严重级别的日志")
