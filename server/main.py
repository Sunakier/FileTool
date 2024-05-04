# ---- SOME THINGS ---- #
# WHEN U ARE READING THIS I WILL TAKIE GREATE PREASSURE THAT U TOOK YOUR EXP TIME TO READ MY CODE
# THIS PROJECT WSA RUSHED IN A REALLY REALLY REALLY REALLY HURRY HURRY HURRY TIME
# U ARE RIGHT IF U THINK IT WORST AND THERE UNCOUNTABLE TODOSSSSSS WITHIN THE PROJECT
# I THINK IT IS TRULY PITIFUL AND SAD WHEN I WAS ALONE IN FORESTS WITH ME, FO, FA THAT NO VAL!!!!!
# WRITTEN IN TERRIFYING, MAR. 4TH, 2024
# ----     BYE     ---- #

import time

import server
from log import *


def print_ascii_art():
    ascii_draw_name = """  ______ _ _         _____                     _____                          
 |  ____(_) |       / ____|                   / ____|                         
 | |__   _| | ___  | (___  _   _ _ __   ___  | (___   ___ _ ____   _____ _ __ 
 |  __| | | |/ _ \  \___ \| | | | '_ \ / __|  \___ \ / _ \ '__\ \ / / _ \ '__|
 | |    | | |  __/  ____) | |_| | | | | (__   ____) |  __/ |   \ V /  __/ |   
 |_|    |_|_|\___| |_____/ \__, |_| |_|\___| |_____/ \___|_|    \_/ \___|_|   
                            __/ |                                             
                           |___/                                              """

    for i in ascii_draw_name.split("\n"):
        print(i)
        time.sleep(0.25)
    time.sleep(0.5)
    print("File Sync Server - 文件同步工具服务端")
    print("参赛作品 完全原创")
    print("By Wuqibor 2024")
    if WEB_DEBUG_API:
        warn("!!! ---- >>> NOTICE >>> ---- !!!")
        warn("!!! 你启用了调试接口, 这个接口不应该在任何对外公开环境或者生产环境开启, 你应该知道你在干什么 !!!")
        warn("!!! ---- <<< NOTICE <<< ---- !!!")
    server.run_web()


def init():
    print_ascii_art()


if __name__ == "__main__":
    init()
