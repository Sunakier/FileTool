import hashlib
import shutil
from threading import Lock
from typing import IO

from clib import *
from log import *
from sql import sql
from utils import *

# TODO:处理同名文件问题

tmp_files = {}  # 上传 临时文件


def create_file(file_md5: str, file_size: int, ip: str):
    file_storage_path = os.path.join(FILES_STORAGE_PATH, file_md5)
    file_tmp_path = os.path.join(FILES_TMP_PATH, file_md5)
    is_in_sql = sql.read_file_id(file_md5)
    if is_in_sql is not None and os.path.exists(file_storage_path) and os.path.getsize(file_storage_path) == file_size:  # 存在
        info("FileCreate : 已有文件 " + str(file_md5) + " 秒传成功")
        return serverMsgJson(998, "File Matched")
    # info("FileCreate : " + str(file_path) + " " + str(os.path.exists(file_path)) + " " + str(os.path.getsize(file_path)) + " " + str(file_size))
    if file_md5 in tmp_files:  # 文件已存在
        return serverMsgJson(200, "File Existed", tmp_files[file_md5]['chunks'])
    else:
        info("FileCreate : 创建文件任务 " + str(file_md5))
        char = open(file_tmp_path, "wb+")
        lock = Lock()
        file_new = {file_md5: {'file_size': file_size, 'file_md5': file_md5, 'time': milliTime(), 'ip': ip, 'chunks': {}, 'char': char, 'lock': lock}}
        tmp_files.update(file_new)
        return serverMsgJson(200, "File Created")


def upload_file(file_md5: str, file_md5_chunk: str, file_length: int, file_start: int, data: bytes):
    if file_md5 not in tmp_files:
        error("FileUpload : 文件 " + file_md5 + " 未创建")
        return serverMsgJson(349, "File Not Register")

    file_length_real = len(data)
    if file_length_real != file_length:
        error("FileUpload : 文件 " + file_md5 + " 长度校验错误 R:" + str(file_length_real) + " G:" + str(file_length))
        return serverMsgJson(341, "File Length Error", {"file_length_real": file_length_real, "file_length": file_length})

    file_md5_real = hashlib.md5(data).hexdigest()
    if file_md5_real != file_md5_chunk:
        error("FileUpload : 文件 " + file_md5 + " 分块校验错误 R:" + str(file_md5_real) + " G:" + str(file_md5_chunk))
        return serverMsgJson(342, "File Hash Error", {"file_md5_real": file_md5_real, "file_md5_chunk": file_md5_chunk})

    char: IO[bytes] = tmp_files[file_md5]['char']

    with tmp_files[file_md5]['lock']:
        try:
            debug("FileUpload : 定位 " + str(file_start) + " 写入长度 " + str(len(data)))
            char.seek(file_start)
            char.write(data)
            char.flush()  # TODO:异步写入提高性能
            info("FileUpload : 文件 " + file_md5 + " 分块 " + str(file_start) + "-" + str(file_start + file_length) + " 写入")
        except Exception as e:
            error("FileUpload : 文件 " + file_md5 + " 分块 服务器保存错误 在写入 " + str(file_start) + "-" + str(file_start + file_length) + " 时")
            debug(str(e.__traceback__.tb_lineno) + " E:" + str(e))
            return serverMsgJson(533, 'Server Error', {"file_md5_real": file_md5_real, "file_md5_chunk": file_md5_chunk})

        t1 = tmp_files[file_md5]['chunks']  # 本文件原本的
        t2 = {file_start: file_length}
        out_chunks = bsort(list(t1.items()) + list(t2.items()))
        tmp_files[file_md5]['chunks'] = out_chunks

        tmp_chunks_list = list(tmp_files[file_md5]['chunks'].items())

        if len(tmp_chunks_list) == 1 and tmp_chunks_list[0][0] == 0 and tmp_chunks_list[0][1] >= tmp_files[file_md5]['file_size']:  # 上传完成
            info("FileUpload : 文件 " + file_md5 + " 上传完成 大小 : " + str(tmp_files[file_md5]['file_size']))
            tmp_files[file_md5]['char'].truncate()
            tmp_files[file_md5]['char'].close()
            file_path = os.path.join(FILES_TMP_PATH, file_md5)
            shutil.move(file_path, FILES_STORAGE_PATH + file_md5)
            sql.add_file_id(file_md5, tmp_files[file_md5]['file_size'], milliTime(), tmp_files[file_md5]['ip'])
            del tmp_files[file_md5]  # 删除缓存
            return serverMsgJson(990, 'File Update Ok')
    return serverMsgJson(200, 'File Chunk Update Ok')
