#  ______ _ _         _____                     _____
# |  ____(_) |       / ____|                   / ____|
# | |__   _| | ___  | (___  _   _ _ __   ___  | (___   ___ _ ____   _____ _ __
# |  __| | | |/ _ \  \___ \| | | | '_ \ / __|  \___ \ / _ \ '__\ \ / / _ \ '__|
# | |    | | |  __/  ____) | |_| | | | | (__   ____) |  __/ |   \ V /  __/ |
# |_|    |_|_|\___| |_____/ \__, |_| |_|\___| |_____/ \___|_|    \_/ \___|_|
#                            __/ |
#                           |___/

# THIS IS THE VERSION OF SERVER
# DO NOT TOUCH THIS PLZ!!!
VERSION = 1

# FOR SERVER
WEB_PORT = 5204  # 绑定端口
WEB_HOST = "0.0.0.0"  # 绑定地址 # TODO: 多网络协议支持
FILES_STORAGE_PATH = "./files/"  # 文件存储目录
FILES_TMP_PATH = "./files_tmp/"  # 临时文件目录
LOG_DEBUG = True  # 是否输出DEBUG日志
WEB_DEBUG_API = True  # 注册WEB的调试接口

DB_TYPE = "SQLITE"  # Only Sqlite Now TODO: 支持更多数据库
