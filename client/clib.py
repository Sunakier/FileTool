#  -- clib --  v2.0 Update 2024/3/16 20:07 By Wuqibor Mail: 1722302509@qq.com

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


# 时间到文本 eg: 1d2h3m4s5ms
def millisScondToTextTime(millis):
    s, l = divmod(millis, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d == 0:
        c_d = ""
        if h == 0:
            c_h = ""
            if m == 0:
                c_m = ""
                if s == 0:
                    c_s = ""
                    if l == 0:
                        c_l = ""
                    else:
                        c_l = "%dms" % l
                else:
                    c_s = "%ds:" % s
                    c_l = "%dms" % l

            else:
                c_m = "%dm:" % m
                c_s = "%ds:" % s
                c_l = "%dms" % l

        else:
            c_h = "%dh:" % h
            c_m = "%dm:" % m
            c_s = "%ds:" % s
            c_l = "%dms" % l

    else:
        c_d = "%dd:" % d
        c_h = "%dh:" % h
        c_m = "%dm:" % m
        c_s = "%ds:" % s
        c_l = "%dms" % l

    return c_d + c_h + c_m + c_s + c_l
    # return "%dh:%dm:%ds:%dms" % (h, m, s, l)


# 十分简易的文件下载模块
def downloadAllInOne(files, url, fileid):  # 下载路径 文件路径 文件提示id
    import requests
    try:
        r = requests.get(url=url, stream=True)  # 分块下载然后写入
    except Exception as error:
        print("Error [DOWNLOAD] [HTTP] " + str(error))
        return 1
    with open(files, "wb") as f:
        for chunk in r.iter_content(chunk_size=2048):
            try:
                f.write(chunk)
            except Exception as error:
                print("Error [DOWNLOAD] [WRITE] " + str(error))
                return 2
        f.close()
    print("Downloaded " + fileid)


# QQ空间老版本skey算法
def getGtk(skey):
    e = 5381
    for i in range(len(skey)):
        e = e + (e << 5) + ord(skey[i])
    return str(2147483647 & e)


# 遍历文件夹和子文件夹的所有文件
def getFiles(filedir):
    from os import walk
    d_file = []
    for filepath, dirnames, filenames in walk(filedir):
        for filename in filenames:
            d_file.append(str(filepath + "/" + filename).replace("///", "/").replace("\\", "/").replace("//", "/").replace("//", "/"))
    return d_file


# 遍历文件夹和子文件夹的所有文件夹
def getDirs(filedir):
    from os import walk
    d_file = []
    for filepath, dirnames, filenames in walk(filedir):
        for dir in dirnames:
            d_file.append(filepath + "/" + dir)
    return d_file


# 获取文件大小
def calcFileSize(filename):
    import os
    return os.stat(filename).st_size


# 获取文件sha256
def calcFileSha256(filname):
    from hashlib import sha256
    with open(filname, "rb") as f:
        sha256obj = sha256()
        sha256obj.update(f.read())
        hash_value = sha256obj.hexdigest()
        return hash_value


# 获取文件sha1
def calcFileSha1(filname):
    from hashlib import sha1
    with open(filname, "rb") as f:
        sha1obj = sha1()
        sha1obj.update(f.read())
        hash_value = sha1obj.hexdigest()
        return hash_value


# 获取文件md5
def calcFileMd5(filname):
    from hashlib import md5
    with open(filname, "rb") as f:
        md5obj = md5()
        md5obj.update(f.read())
        hash_value = md5obj.hexdigest()
        return hash_value


# 获取文件后缀名 使用split分割实现
def getFileSuffix(name):
    suffix = name.split(".")
    sc = suffix[len(suffix) - 1]
    return sc


# 删除文本指定符号中间字符  传入: 源文本 被删除前缀 被删除后最
# 示例: 源: hi<js>123</js>bye  前缀: <js>  后缀: </js>  结果: hibye
def removeMiddle(text: str, removea: str, removeb: str):
    b = text
    a = b.find(removea)
    while a != -1:
        c = b[:a]
        f = b[a + len(removea):]
        d = f.find(removeb)
        if d != -1:
            e = f[d + len(removeb):]
            b = c + e
            a = b.find(removea)
        else:
            break
    return b


# 获取硬件id
def getHwid():
    from hashlib import sha1
    from wmi import WMI
    try:
        c = WMI()
        cpuid = None
        boardid = None
        for cpu in c.Win32_Processor():
            cpuid = cpu.ProcessorId.strip()
            break
        for board_id in c.Win32_BaseBoard():
            boardid = board_id.SerialNumber
            break
        if cpuid is None or boardid is None:
            return None
        return sha1((str(cpuid) + str(boardid)).encode("utf8")).hexdigest()
    except:
        return None


# 排序 dict
def sortDict(dictx: dict):
    return dict(sorted(dictx.items(), key=lambda item: item[0]))
