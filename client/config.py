#  ______ _ _         _____
# |  ____(_) |       / ____|
# | |__   _| | ___  | (___  _   _ _ __   ___
# |  __| | | |/ _ \  \___ \| | | | '_ \ / __|
# | |    | | |  __/  ____) | |_| | | | | (__
# |_|    |_|_|\___| |_____/ \__, |_| |_|\___|
#                            __/ |
#                           |___/

# THIS IS THE VERSION OF CLIENT
# DO NOT TOUCH THIS PLZ!!!
VERSION = 1

# FOR CLIENT
SERVER_ADDR = "http://192.168.2.13:5204"  # 服务端地址
LOG_DEBUG = False  # 是否输出DEBUG日志
FILES_TMP_PATH = "./files_tmp/"  # 临时文件目录
WEB_PORT = 9229  # 绑定端口
WEB_HOST = "0.0.0.0"  # 绑定地址

# 同步模式 目前仅支持主从分离模式 即一台设备的Token只能为一种 a/b 模式的一种
# a (Only-A 强制覆盖云端) / b (Only-B 强制云端同步本地)
# TODO: 支持多方向同步
