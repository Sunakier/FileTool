import datetime
import logging
import os
import sys
from config import *


def _setup_logger():
    # 创建一个日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # 确保日志文件夹存在
    log_folder = 'logs'
    os.makedirs(log_folder, exist_ok=True)

    # 创建一个文件处理器，将日志记录到/log文件夹中
    log_file = datetime.datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(log_folder, log_file)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 创建一个控制台处理器，将日志输出到控制台
    console_handler = logging.StreamHandler(sys.stdout)
    if LOG_DEBUG:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)

    # 定义日志格式
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 将处理器添加到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.getLogger("PIL.PngImagePlugin").disabled = True  # 屏蔽输出
    logging.getLogger("PIL.Image").disabled = True
    logging.getLogger("urllib3.connectionpool").disabled = True
    logging.getLogger("werkzeug").name = "WEB"
    logging.getLogger("root").name = "MAIN"

    return logger


logger = _setup_logger()

info = logger.info
error = logger.error
warn = logger.warning
debug = logger.debug
