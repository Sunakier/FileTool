#  -- blic - from - clib --  v2.0 Update 2024/3/16 20:07 By Wuqibor Mail: 1722302509@qq.com
from flask import jsonify, make_response

from config import *


# 时间戳 支持给定时间 默认13位 最大16位
def milliTime(time=None, longx=13):
    if time is None:
        from time import time as timex
        time = timex()
    return int(str(time * 1000000)[:longx])


# 13位时间戳转换为日期格式字符串
def milliSecondToTime(millis):
    from time import strftime, localtime
    return strftime('%Y-%m-%d %H:%M:%S', localtime(millis / 1000))


# 排序 dict
def sortDict(dictx: dict):
    return dict(sorted(dictx.items(), key=lambda item: item[0]))


# 用于上传区块进度的合并 进度去重 传入dict转的list 传入的dict格式: {起始进度1: 长度1, 起始进度2: 长度2}
def bsort(dictx):
    dictx = list(sortDict(dict(dictx)).items())
    n = dictx.copy()  # 和上传的比对留档
    k = dictx.copy()  # 本次操作结果
    while True:
        t = 0  # 数组索引
        h = 0  # 全局控制
        while h != len(k):
            if t + 1 >= len(k):
                return dict(k)
            if k[t][0] + k[t][1] >= k[t + 1][0] + k[t + 1][1]:  # 前大于后的全部 - 后是前的子集
                del k[t + 1]
            elif k[t][0] + k[t][1] >= k[t + 1][0]:  # 前大于后的首 - 取交 前首+后尾
                k[t] = (k[t][0], k[t + 1][0] + k[t + 1][1] - k[t][0])
                del k[t + 1]
            else:
                t = t + 1  # 前的全部小于后的首 交集为空 pass
            h = h + 1
        if n == dict(k):
            print(n)
            return dict(n)
        else:
            n = k  # 同步
            k = k


def serverMsgJson(code: int, msg: str, data={}):
    response = make_response(jsonify({'code': code, 'msg': msg, 'data': data}), code)
    response.headers.set("ServerX", 'FileSyncTool/' + str(VERSION))
    # response = make_response(jsonify({'code': code, 'msg': msg, data: data, 'server': VERSION}), code, {"ServerX": 'FileSyncTool/' + str(VERSION)})
    return response


def serverMsgText(code: int, msg: str):
    response = make_response(msg, code)
    response.headers.set("ServerX", 'FileSyncTool/' + str(VERSION))
    return response
