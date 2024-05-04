import base64
import copy
import hashlib
import threading
import time
import traceback
from _thread import start_new_thread as st

import requests
from watchdog.events import *
from watchdog.observers import Observer

from log import *
from utils import *

# 加载数据 TODO: 对数据操作进行类的封装 优化代码结构
sync_data_cur = open("./sync_data.kjson", "a+", encoding="utf8")
try:
    sync_data_cur.seek(0)
    sync_list = json.loads(sync_data_cur.read())
except:
    info("加载同步任务列表出错 已自动重置")
    sync_list = {}

sync_hookevent_list = {}  # 用于存放文件事件的对象 分离是为了更好的转储 sync_list 为json文本
need_sync_init = True  # 判断是否需要初始化 用于添加了 Token 后或者刚刚启动初始化 注意这里可能有一个锁的问题 TODO: 同步初始化锁问题
changed_files = []  # 存储需要同步的改动的文件


class FileThread(threading.Thread):  # 全局同步线程

    def run(self):
        while True:
            global need_sync_init
            if need_sync_init:
                need_sync_init = False
                for sync_item in list(sync_list.values()):
                    token = sync_item["token"]
                    if not token in sync_hookevent_list:  # 需要同步列表有 观察线程列表没有 证明需要添加这个任务
                        # TODO: 初始化过程的错误处理
                        path = sync_item["path"]
                        if sync_item["mode"] == 0:
                            debug("添加事件钩子 " + token + " | Path: " + path)
                            observer = Observer()
                            event_handler = FileEventHandler()
                            # 文件事件在部分系统版本有可能抽风 暂无解决方案
                            # 升级最新系统 或者 考虑等待基于Win32Api自己实现文件检测服务 (或实现基于Everything的索引服务)
                            observer.schedule(event_handler, path, True)
                            observer.start()
                            sync_hookevent_list[token] = observer
                for sync_item_ed_token in list(sync_hookevent_list.keys()):
                    if not sync_item_ed_token in sync_list:  # 观察线程列表有 需要同步列表没有 证明已删除这个任务 需要删除
                        debug("删除事件钩子 " + sync_item_ed_token + " | Path: " + sync_list[sync_item_ed_token]['path'])
                        sync_hookevent_list[sync_item_ed_token].stop()
                        sync_hookevent_list[sync_item_ed_token].join()
                        del sync_hookevent_list[sync_item_ed_token]
            time.sleep(3)


class FileSyncThread(threading.Thread):
    def run(self):
        time.sleep(2)
        info("同步线程启动")
        time_1 = milliTime()
        file_caches.makeCaches()
        file_caches.saveCaches()
        time_2 = milliTime()
        debug("本次缓存用时: " + str(millisScondToTextTime(time_2 - time_1)))
        while True:
            time.sleep(10)
            try:
                post_data = []
                for token in list(sync_list.keys()):
                    post_data.append(token)
                rs = requests.post(SERVER_ADDR + "/apix/ping_keep", data=json.dumps(post_data))
                if rs.status_code == 200:
                    rs = json.loads(rs.text)
                else:
                    continue
                version_ser = rs['data']['version_ser']

                # if len(changed_files) > 0:
                changed_list = []
                try:
                    while True:
                        changed_list.append(pathFo(changed_files.pop(0)))
                except:
                    pass
                changed_list = list(set(changed_list))
                changed_list.sort()

                file_caches.comCaches(changed_list, version_ser)
            except Exception as e:
                error("同步线程错误 " + str(e.__traceback__.tb_lineno) + " E:" + str(e))
                debug("同步线程错误 " + str(traceback.format_exc()) + " E:" + str(e))
                continue


# 事件钩子
# 这里有个非常麻烦的问题 Win 下对于文件的类封装很麻烦 修改一个文件会触发多个监控 比如其父目录 并且复制文件等同时触发多个 比如要先创建然后修改
class FileEventHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)

    def on_moved(self, event):
        if event.is_directory:
            info(f"目录移动 {event.src_path} 到 {event.dest_path} 操作类型 {event.event_type}")
            p1 = pathFo(event.src_path)
            p2 = pathFo(event.dest_path)
            if not p1 in changed_files:
                changed_files.append(p1)
            if not p2 in changed_files:
                changed_files.append(p2)
        else:
            info(f"文件移动 {event.src_path} 到 {event.dest_path} 操作类型 {event.event_type}")
            p1 = pathFo(event.src_path)
            p2 = pathFo(event.dest_path)
            if not p1 in changed_files:
                changed_files.append(p1)
            if not p2 in changed_files:
                changed_files.append(p2)

    def on_created(self, event):
        if event.is_directory:
            info(f"目录创建 {event.src_path} 操作类型 {event.event_type}")
            p1 = pathFo(event.src_path)
            if not p1 in changed_files:
                changed_files.append(p1)

    def on_deleted(self, event):
        info(f"删除资源 {event.src_path} 操作类型 {event.event_type}")
        p1 = pathFo(event.src_path)
        if not p1 in changed_files:
            changed_files.append(p1)

    def on_modified(self, event):
        if not event.is_directory:
            info(f"文件修改 {event.src_path} 操作类型 {event.event_type}")
            p1 = pathFo(event.src_path)
            if not p1 in changed_files:
                changed_files.append(p1)


# 缓存封装类
class FileCaches:
    # 加载磁盘缓存
    def loadsDiskCaches(self):
        self.sync_data_caches_cur = open("./sync_data_caches.kjson", "a+", encoding="utf8")  # TODO: 预定义优化处理
        try:
            self.sync_data_caches_cur.seek(0)
            self.sync_data_caches = json.loads(self.sync_data_caches_cur.read())
        except:
            info("加载同步任务缓存出错 已自动重置")
            self.sync_data_caches = {}

    def walkFile(self, dir, cur, mtime):  # 传递需要扫描的文件夹和操作的变量  根目录 操作变量 主目录时间
        # mtime = getFileMTime13(dir)  # 自身文件夹修改时间 用于初始化
        # if 'time' in cur and cur['time'] == mtime:  # 判断是否当前文件夹为旧文件夹 这里文件夹如已经缓存 则判断时间跳过扫描 否则进入刷新缓存
        #     return  # 无需刷新 使用旧缓存 如果出现本地文件比缓存还新 那么 Fxxk You My User TODO: 缓存时间优化处理
        # else:  # 新文件夹 初始化然后加载缓存 此处 name 置空的应该由上级设置 注意根目录是没有name的
        if not 'dirs' in cur:
            cur['dirs'] = {}

        if 'files' in cur and not cur['files'] is None:
            file_x_list = copy.deepcopy(cur['files'])
        else:
            file_x_list = {}
            cur['files'] = {}
        for filename in os.listdir(dir):  # TODO: 使用 walk+topdown 提高性能
            filepath = pathFo(dir + "/" + filename)

            if os.path.isdir(filepath):  # 目录
                mtime = getFileMTime13(filepath)  # 取身文件夹修改时间 判断是否需要跳过

                dirpath = pathFo(filepath)  # 时间不对 需要传递具体参数
                dir_info = {filename: {
                    'name': filename,
                }}
                cur['dirs'].update(dir_info)  # 这里需要保留传递 dirs 参数
                self.walkFile(dirpath, cur['dirs'][filename], mtime)

            if os.path.isfile(filepath):  # 是文件
                file_md5 = None
                if 'time' in cur and cur['time'] == mtime:  # 通过判断上级目录修改时间获取下级文件是否有修改
                    continue  # 无修改
                file_stat = os.stat(filepath)  # 文件参数
                if filename in file_x_list and 'md5' in file_x_list[filename] and not file_x_list[filename]['md5'] is None:
                    # 有MD5了
                    file_md5 = file_x_list[filename]['md5']

                else:
                    with open(filepath, "rb") as f:
                        hash_s1 = hashlib.md5()
                        for block in iter(lambda: f.read(1024 * 1024 * 20), b''):
                            hash_s1.update(block)
                        file_md5 = hash_s1.hexdigest()
                        f.close()
                file_info = {
                    'name': filename,
                    'size': file_stat.st_size,  # 文件大小（字节）
                    'time': file_stat.st_mtime * 1000,  # 修改时间（时间戳）
                    'file_md5': file_md5
                }
                cur['files'][filename] = file_info

        cur['time'] = mtime

    # 全量的建立缓存 不应频繁使用 sync_data_caches.kjson # TODO: 数据库支持 更高效的内存缓存
    def makeCaches(self, token=None):
        if token is not None:
            path = sync_list[token]['path']
            if not sync_list[token]['token'] in self.sync_data_caches:  # 需要从零开始初始化 第一次判断
                self.sync_data_caches[token] = {'dirs': {}, 'files': {}}

            mtime = getFileMTime13(path)  # 取自身文件夹修改时间
            sync_data_bak = copy.deepcopy(self.sync_data_caches)
            self.walkFile(path, self.sync_data_caches[token], mtime)
            if not self.sync_data_caches == sync_data_bak:  # 本地有更改 修改时间戳
                sync_list[token]['version'] = milliTime()
                sync_data_cur.seek(0)  # 立刻写入磁盘 这里需要异步优化
                sync_data_cur.truncate()
                sync_data_cur.write(json.dumps(sync_list))
                sync_data_cur.flush()
        else:
            for sync_list_item in list(sync_list.values()):  # 循环为每个token都建立缓存

                token = sync_list_item['token']
                path = sync_list_item['path']
                if not sync_list_item['token'] in self.sync_data_caches:  # 需要从零开始初始化 第一次判断
                    self.sync_data_caches[token] = {'dirs': {}, 'files': {}}

                mtime = getFileMTime13(path)  # 取自身文件夹修改时间
                sync_data_bak = copy.deepcopy(self.sync_data_caches)
                self.walkFile(path, self.sync_data_caches[token], mtime)
                if not self.sync_data_caches == sync_data_bak:  # 本地有更改 修改时间戳
                    sync_list[token]['version'] = milliTime()
                    sync_data_cur.seek(0)  # 立刻写入磁盘 这里需要异步优化
                    sync_data_cur.truncate()
                    sync_data_cur.write(json.dumps(sync_list))
                    sync_data_cur.flush()

    def saveCaches(self):
        self.sync_data_caches_cur.seek(0)
        self.sync_data_caches_cur.truncate()
        self.sync_data_caches_cur.write(json.dumps(self.sync_data_caches))
        self.sync_data_caches_cur.flush()
        info("缓存写入磁盘完成")

    def comCaches(self, changed_list: list, version_ser: dict):  # 目前仅支持主/从分离模式
        global sync_list

        def upl(will_file):
            try:
                code, file_md5 = upload(will_file)
                if code == 9:
                    info("上传 秒传成功 Token: " + token + " | " + file_md5 + " " + will_file)
                else:
                    info("上传 全量成功 Token: " + token + " | " + file_md5 + " " + will_file)
                return file_md5
            except:
                error("上传出错 Token: " + token + " Path: " + will_file)
                return None

        for token in list(sync_list.keys()):
            debug("Key: " + json.dumps(sync_list[token]))
            if sync_list[token]['mode'] == 1 and version_ser[token] > sync_list[token]['version']:  # b模式 远端新于本地
                debug("同步b " + token)
                is_change = True
            else:
                # TODO: 屎山
                is_change = False  # 用于标识本token缓存的内容有没有更改
                base_path = sync_list[token]['path']
                base_path_len = len(base_path)
                for changed_item in changed_list:
                    is_exists = os.path.exists(changed_item)  # 文件是否存在 坑: 文件不存在永远是 False
                    is_files = os.path.isfile(changed_item)  # 是否为文件
                    debug("缓存比对 操作 : " + changed_item + "|" + str(is_files) + "|" + str(is_exists))
                    if changed_item[:base_path_len] == base_path and changed_item[base_path_len:base_path_len + 1] == "/":
                        # 源路径匹配成功 并且有文件分割符号
                        k_path = changed_item[base_path_len + 1:]  # 不带 / 的相对路径
                        k_path_s = k_path.split("/")
                        m_path = self.sync_data_caches[token]  # TODO: 此处资源占用大 需要优化 #T0
                        k_path_s_len = len(k_path_s)
                        for i_x1 in range(k_path_s_len):
                            if i_x1 == k_path_s_len - 1:  # 最后一个 判断 files 内
                                if is_files:
                                    if k_path_s[i_x1] in m_path['files']:  # 是文件
                                        # 缓存存在此文件
                                        if not is_exists:  # 实际不存在此文件 应该删除缓存内容
                                            if sync_list[token]['mode'] == 0:  # a模式 覆盖云端
                                                debug("缓存比对 : A 1 0")
                                                del m_path['files'][k_path_s[i_x1]]
                                                is_change = True
                                            elif token in version_ser and not version_ser[version_ser] is None:
                                                debug("缓存比对 : B 1 0")
                                                if version_ser[token] > sync_list[token]['version']:  # b模式远端新于本地版本 应该让远端覆盖本地
                                                    is_change = True
                                                    continue
                                        else:  # 实际存在此文件 # 这里是为混合同步而准备的
                                            # if m_path['files'][k_path_s[i_x1]]['time'] < getFileMTime13(changed_item):  # 比对修改时间
                                            #     is_change = True  # 本地的新 把本地同步到缓存
                                            #     file_stat = os.stat(changed_item)
                                            #     m_path['files'][k_path_s[i_x1]] = {
                                            #         'name': k_path_s[i_x1],
                                            #         "time": file_stat.st_mtime * 1000,
                                            #         "size": file_stat.st_size
                                            #     }
                                            # else:
                                            #     # 云端的新 下载到本地
                                            #     pass
                                            debug("缓存比对 : A 1 1")
                                            if sync_list[token]['mode'] == 0:  # 模式a
                                                file_stat = os.stat(changed_item)  # 本地同步云端
                                                m_path['files'][k_path_s[i_x1]] = {
                                                    'name': k_path_s[i_x1],
                                                    "time": file_stat.st_mtime * 1000,
                                                    "size": file_stat.st_size
                                                }
                                                if not 'md5' in m_path['files'][k_path_s[i_x1]]:
                                                    file_md5 = upl(changed_item)
                                                    m_path['files'][k_path_s[i_x1]]['md5'] = file_md5
                                                is_change = True
                                            else:
                                                is_change = True
                                                continue
                                    else:
                                        # 本地存在 但缓存不存在此文件
                                        if sync_list[token]['mode'] == 0:  # 模式a
                                            debug("缓存比对 : A 0 1")
                                            # 应该建立缓存 并且上传云端
                                            file_stat = os.stat(changed_item)
                                            m_path['files'][k_path_s[i_x1]] = {
                                                'name': k_path_s[i_x1],
                                                "time": file_stat.st_mtime * 1000,
                                                "size": file_stat.st_size
                                            }
                                            if not 'md5' in m_path['files'][k_path_s[i_x1]]:
                                                file_md5 = upl(changed_item)
                                                m_path['files'][k_path_s[i_x1]]['md5'] = file_md5
                                            is_change = True
                                        else:
                                            debug("缓存比对 : B 0 1")
                                            # 应该删除本地内容 但是应该由后面统一同步
                                            is_change = True
                                            continue
                                else:  # 是目录
                                    if k_path_s[i_x1] in m_path['dirs']:
                                        # 缓存存在此文件
                                        if sync_list[token]['mode'] == 0:  # 模式a
                                            if not is_exists:  # 实际不存在此文件 应该删除缓存内容
                                                debug("缓存比对 : D A 1 0")
                                                del m_path['dirs'][k_path_s[i_x1]]
                                                is_change = True
                                            else:  # 实际存在 跳过它
                                                debug("缓存比对 : D A 1 1")
                                                pass
                                                # self.walkFile(changed_item, m_path['dirs'][k_path_s[i_x1]], mtime=getFileMTime13(changed_item))
                                        else:  # 模式b
                                            if not is_exists:  # 实际不存在此文件 应该创建
                                                os.mkdir(changed_item)
                                            else:  # 实际存在 应该删除
                                                os.removedirs(changed_item)
                                    else:  # 缓存不存在
                                        if sync_list[token]['mode'] == 0:  # 模式a
                                            if not is_exists:  # 实际不存在 跳过 # 这里由两情况 文件不存在会指向这里
                                                if k_path_s[i_x1] in m_path['files']:
                                                    del m_path['files'][k_path_s[i_x1]]
                                                    is_change = True
                                                debug("缓存比对 : D A 0 0")
                                                pass
                                            else:  # 实际存在 添加到缓存
                                                debug("缓存比对 : D A 0 1")
                                                self.walkFile(changed_item, m_path['dirs'][k_path_s[i_x1]], mtime=getFileMTime13(changed_item))

                                                def getFilesOfDirs(cur, base_p):
                                                    if 'files' in cur:
                                                        for tmp_file in cur['files']:
                                                            tmp_path = pathFo(base_p + "/" + tmp_file)
                                                            debug("缓存比对 : D 添加 :" + tmp_path)
                                                        if 'dirs' in cur:
                                                            for tmp_dir in cur['dirs']:
                                                                getFilesOfDirs(cur['dirs'][tmp_dir], base_p + "/" + tmp_dir)

                                                getFilesOfDirs(m_path['dirs'][k_path_s[i_x1]], changed_item)

                                                is_change = True
                                        else:  # 模式b 缓存不存在
                                            if not is_exists:  # 实际不存在 跳过
                                                pass
                                            else:  # 实际存在 目录无需比对版本 删掉
                                                os.removedirs(changed_item)

                            else:  # 不是最后一级 继续递归
                                if k_path_s[i_x1] in m_path['dirs']:
                                    m_path = m_path['dirs'][k_path_s[i_x1]]  # 缓存存在目录 前往下级
                                else:
                                    pass  # 缓存不存在目录

            # 同步阶段
            if is_change:
                if sync_list[token]['mode'] == 0:
                    update_token(token, json.dumps(file_caches.sync_data_caches[token]))
                    info("同步完成 : " + token + " 模式: A-Only (覆盖云端)")
                    file_caches.saveCaches()
                else:
                    if sync_list[token]['version'] < version_ser[token]:
                        info("触发同步 : " + token + " 模式: B-Only (覆盖本地) 本地版本: " + str(sync_list[token]['version']) + " | 云版本: " + str(version_ser[token]))
                        sync_data = get_token(token)
                        debug("解析数据" + json.dumps(sync_data))
                        if sync_data is None:
                            error("无法完成同步 跳过")

                        # 执行同步流程

                        def syncDirSingle(dir, cur):
                            for tmp_file_x in list(cur['files'].values()):
                                qpath = dir + "/" + tmp_file_x['name']
                                if os.path.exists(qpath) is False or int(getFileMTime13(qpath)) < int(tmp_file_x['time']):  # 不同
                                    debug("下载文件 " + token + " | " + tmp_file_x['md5'] + " >> " + qpath)
                                    file_download(tmp_file_x['md5'], qpath)

                            for tmp_dir_x in list(cur['dirs'].values()):
                                qpath = dir + "/" + tmp_dir_x['name']
                                if not os.path.exists(qpath):
                                    debug("创建文件夹 " + token + " | " + qpath)
                                    os.mkdir(qpath)

                                syncDirSingle(qpath, cur['dirs'][tmp_dir_x['name']])

                        syncDirSingle(sync_list[token]['path'], sync_data)
                        sync_list[token]['dirs'] = sync_data['dirs']
                        sync_list[token]['files'] = sync_data['files']
                        sync_list[token]['version'] = version_ser[token]
                        info("同步完成 : " + token + " 模式: B-Only (覆盖本地)")

                        file_caches.saveCaches()


def get_token(token):
    url1 = SERVER_ADDR + "/apix/token"

    headers = {
        "X-API-X-TOKEN": token
    }
    rs = requests.get(url1, headers=headers)
    debug("下行同步: " + token + " " + str(rs.status_code) + " | " + rs.text.strip())

    if rs.status_code == 881:
        error("下行同步: Tokne 未有数据 " + token + " " + str(rs.status_code) + " | " + rs.text.strip())
        return None
    elif rs.status_code == 200:
        debug("下行同步: 获取数据完成 " + token + " ")
        sync_data_x = str(json.loads(rs.text)['data']['sync_data'])
        sync_data_x = base64.b64decode(sync_data_x.encode('utf-8')).decode('utf-8')
        sync_data_x = json.loads(sync_data_x)['sync_data']
        sync_data_x = json.loads(sync_data_x)
        return sync_data_x
    else:
        error("下行同步: 未知错误码 " + token + " " + str(rs.status_code) + " | " + rs.text.strip())


# TODO: 封装网络操作函数类 统一调用
# TODO: 多线程上传
def upload(file_path, file_md5=None):
    url1 = SERVER_ADDR + "/apix/file/create"
    url2 = SERVER_ADDR + "/apix/file/upload"
    block_size = 1024 * 1024 * 20  # 20MB

    if file_md5 is None:
        with open(file_path, "rb") as f:
            hash_s1 = hashlib.md5()
            for block in iter(lambda: f.read(block_size), b''):
                hash_s1.update(block)
            file_md5 = hash_s1.hexdigest()
            f.close()

    data = {
        "file_size": os.path.getsize(file_path),
        "file_md5": file_md5
    }

    rs = requests.post(url1, data=json.dumps([data]))
    debug("文件上传: " + file_path + " " + str(rs.status_code) + " | " + rs.text.strip())

    if rs.status_code == 998:  #
        return 9, file_md5  # 秒传

    with open(file_path, "rb") as f:
        for i, block in enumerate(iter(lambda: f.read(block_size), b'')):
            chunk_md5 = hashlib.md5(block).hexdigest()
            headers = {
                "X-API-X-FILE-UPLOAD-MD5": file_md5,
                "X-API-X-FILE-UPLOAD-MD5-CHUNK": chunk_md5,
                "X-API-X-FILE-UPLOAD-IN": str(i * block_size),
                "X-API-X-FILE-UPLOAD-LEN": str(len(block))
            }
            debug("文件上传 分片 (" + chunk_md5 + ") " + str(i + 1) + " -> " + str(i * block_size) + "-" + str(i * block_size + len(block)) + "/" + str(block_size) + " : " + file_path + " " + str(rs.status_code) + " | " + rs.text.strip())
            rs = requests.post(url2, data=block, headers=headers)
        f.close()

    return 0, file_md5


# 文件列表更新函数
def update_token(token, sync_data):
    url1 = SERVER_ADDR + "/apix/token"

    headers = {
        "X-API-X-TOKEN": token,
        "X-API-X-TIME": str(milliTime())
    }
    rs = requests.post(url1, data=json.dumps({'sync_data': sync_data}), headers=headers)
    debug("上行同步: " + token + " " + str(rs.status_code) + " | " + rs.text.strip())

    if rs.status_code == 752:
        debug("上行同步: 服务端错误 " + token + " " + str(rs.status_code) + " | " + rs.text.strip())
        return False

    if rs.status_code == 200:
        debug("上行同步: 完成 " + token + " " + str(rs.status_code) + " | " + rs.text.strip())
        return True


# 文件下载函数 TODO: 多线程下载
def file_download(file_md5, path):  # 文件md5 下载路径
    url1 = SERVER_ADDR + "/apix/file/get"
    headers = {
        "X-API-X-FILE-UPLOAD-MD5": file_md5
    }
    try:
        r = requests.get(url=url1, stream=True, headers=headers)  # 分块下载然后写入
    except Exception as e:
        error("文件下载 下载错误: " + str(e))
        return 1
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=2048):
            try:
                f.write(chunk)
            except Exception as e:
                error("文件下载 写入错误" + str(e))
                return 2
        f.close()
    info("文件下载 完成 " + file_md5 + " | " + path)


def addToken(token: str, path: str, mode: str):
    global need_sync_init
    # 校验 这里path需要解析出实际路径并且对其标准化 (在特殊情况下需要解析真实目录)
    token = str(token)
    mode = str(mode)
    if mode == "a":
        mode = 0
    elif mode == "b":
        mode = 1
    else:
        return 1  # 模式不允许的模式
    path = path.strip()
    debug(path)
    if re.search(r'[*?"<>|]', path):  # 屏蔽特殊字符
        debug("添加同步任务 路径非法 特殊字符 1")
        return 2  # 路径非法
    b_path = pathFo(path)  # 统一标准的路径
    if len(token) <= 0 or len(b_path) <= 0:  # 不允许置空
        debug("添加同步任务 路径非法 置空 2")
        return 2
    if not os.path.exists(b_path):
        return 3  # 路径不存在
    # type : 0 文件夹 / 1 文件
    # 这里需要判断传入的是路径还是文件夹 优先判断用户传入有没有 /
    # 如果有 / 优先判断为文件夹 遇到不存在进行回退
    is_path = os.path.isdir(b_path)  # TODO: 完成对于 挂载 和 链接 的支持
    if not is_path:
        debug("添加同步任务 路径非法 目录不存在 2")
        return 2
    # 以下一些内容是为了但文件同步而准备的 但是目前并不支持但文件同步 这可能导致一些问题 主要出现的远端 但是未来会考虑这个功能
    # TODO: 支持单文件同步 # UPDATE 4/5 此功能或许无期限搁置
    # is_file = os.path.isfile(b_path)
    # if b_path[-1:] == "/":  # 判断是否为原生文件夹
    #     is_path_user = True
    # else:
    #     is_path_user = False
    # if is_path_user:
    #     if is_path:
    #         type = 0  # 用户要求 文件夹 并且是 文件夹
    #     else:
    #         type = 1  # 用户要求 文件夹 但是是 文件
    #         return False
    # else:
    #     if is_file:
    #         type = 1  # 用户要求 文件 并且是 文件
    #         return False
    #     else:
    #         type = 0  # 用户要求 文件 但是是 文件夹
    # 校验 path 通过
    sync_list.update({token: {
        "token": token,
        "time": milliTime(),
        "status": 0,  # 0 需要初始化
        "path": b_path,
        "mode": mode,  # 0a 1b
        "version": 0  # 本地版本
    }})
    info("添加任务 " + token + " | Path: " + b_path)
    st(file_caches.makeCaches, (token,))
    need_sync_init = True
    sync_data_cur.seek(0)  # 立刻写入磁盘 这里需要异步优化
    sync_data_cur.truncate()
    sync_data_cur.write(json.dumps(sync_list))
    sync_data_cur.flush()
    return 0


file_caches = FileCaches()
file_sync_thread = FileSyncThread()


# 文件同步相关组件初始化
def file_init():
    info("加载同步数据完成")
    file_thread = FileThread()
    file_thread.start()
    info("加载同步线程完成")
    file_caches.loadsDiskCaches()
    file_sync_thread.start()


if __name__ == "__main__":
    pass
