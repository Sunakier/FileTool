from file import *
from gui import run_gui


def print_ascii_art():
    ascii_draw_name = """  ______ _ _         _____                          
 |  ____(_) |       / ____|
 | |__   _| | ___  | (___  _   _ _ __   ___
 |  __| | | |/ _ \  \___ \| | | | '_ \ / __|
 | |    | | |  __/  ____) | |_| | | | | (__
 |_|    |_|_|\___| |_____/ \__, |_| |_|\___|
                            __/ |
                           |___/"""

    for i in ascii_draw_name.split("\n"):
        print(i)
        time.sleep(0.25)
    time.sleep(0.5)
    print("File Sync Client - 文件同步工具客户端")
    print("参赛作品 完全原创")
    print("By Wuqibor 2024")



def init():
    print_ascii_art()
    file_init()
    run_gui()


if __name__ == "__main__":
    init()
