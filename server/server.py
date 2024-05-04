import base64
import os.path
import re

import simplejson as json
from flask import Flask, request, send_file, Response

from clib import *
from file import *
from utils import *

# TODO: 使用生产环境的 HTTP 框架
app = Flask(__name__)

# TODO: 用户管理体系 商业化架构体系 权限体系

tmp_version_time = {}  # 缓存不同token的版本


@app.errorhandler(404)
def not_found_error(error_x):
    if request.method == 'GET':
        return serverMsgText(404, "This is File Sync Server. There is nothing :(")
    if request.method == 'POST':
        return serverMsgJson(404, "No Web")


# TODO: 更加完整的错误处理
@app.errorhandler(500)
def internal_error(error_x):
    error(str(error_x))
    if request.method == 'GET':
        return serverMsgText(500, "There is a error in this server. Please report it! :(</p>")
    if request.method == 'POST':
        return serverMsgJson(500, "Server Error")


# TODO: WEB 控制台页面
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return serverMsgText(404, "<h1>This is main web page of File Sync Server</h1><p>But There is nothing :(</p>")
    if request.method == 'POST':
        return serverMsgJson(404, "No Web")


@app.route("/apix/ping", methods=['GET', 'POST'])
def pingpong():
    if request.method == 'GET':
        return serverMsgText(200, "Pong!")
    if request.method == 'POST':
        return serverMsgJson(200, "Pong!")


@app.route('/apix/file/create', methods=['POST'])
def file_create():
    try:
        datas = json.loads(request.data)
        for data in datas:
            file_size = int(data['file_size'])  # TODO: 去除传入请求的非法字符
            file_md5 = str(data['file_md5']).lower().strip()  # TODO: 完成多种HASH适配 但是使用MD5可以降低资源消耗
            if file_size != 0:
                if len(file_md5) != 32:
                    raise Exception
            return create_file(file_md5, file_size, request.remote_addr)
    except Exception as e:
        error("FileCreate : 加载传入参数失败 L:" + str(e.__traceback__.tb_lineno) + " E:" + str(e))
        try:
            debug("FileCreate : " + str(request.data.decode('utf-8')))
        except:
            pass
        return serverMsgJson(399, "Input Error")


# TODO: 多存储支持 云存储支持 集群支持 异步上传支持
@app.route('/apix/file/upload', methods=['POST'])
def file_upload():
    try:
        # TODO: 请求头判断长度 丢弃恶意包
        if len(request.data) == 0:
            return serverMsgJson(400, "Empty File")
        file_md5 = str(request.headers['X-API-X-FILE-UPLOAD-MD5']).strip()
        file_md5_chunk = str(request.headers['X-API-X-FILE-UPLOAD-MD5-CHUNK']).strip()
        file_start = int(request.headers['X-API-X-FILE-UPLOAD-IN'])
        if file_start < 0:
            raise
        file_length = int(request.headers['X-API-X-FILE-UPLOAD-LEN'])
    except:
        error("FileUpload : 加载传入参数失败")
        try:
            debug("FileUpload : " + str(request.data.decode('utf-8')))
        except:
            pass
        return serverMsgJson(399, "Input Error")

    return upload_file(file_md5, file_md5_chunk, file_length, file_start, request.data)


# TODO: 更加完善的方法支持 转移分离函数代码
@app.route('/apix/file/get', methods=['GET', 'HEAD'])  # 已经支持HEAD方法
def file_get():
    debug(json.dumps(list(request.args.items())))
    try:
        file_md5 = request.headers.get('X-API-X-FILE-UPLOAD-MD5')
        if file_md5 is None or len(str(file_md5).lower().strip()) != 32:
            file_md5 = request.args.get("file_md5")
            if file_md5 is None or len(str(file_md5).lower().strip()) != 32:
                raise Exception
    except:
        error("FileGet : 加载传入参数失败")
        try:
            debug("FileGet : " + str(request.data.decode('utf-8')))
        except:
            pass
        return serverMsgJson(399, "Input Error")

    file_path = os.path.join(FILES_STORAGE_PATH, file_md5)
    file_size = os.path.getsize(file_path)

    is_in_sql = sql.read_file_id(file_md5)
    if is_in_sql is None or not os.path.exists(file_path):  # 不存在
        return serverMsgJson(404, "No File")

    resp = Response(status=200)
    resp.headers.set('Content-Disposition', f'attachment;filename*=utf-8"{file_md5}"')
    resp.headers.set("ServerX", 'FileSyncTool/' + str(VERSION))
    if request.method == 'HEAD':
        is_head = True
    else:
        is_head = False

    if request.range is None:  # 无Range头, 返回整个文件
        resp.headers.set('Content-Length', str(file_size))
        if is_head:
            resp.headers.set('Content-Type', "application/octet-stream")
            return resp
        else:
            return send_file(file_path)

    debug(request.range.ranges)
    start, end = request.range.ranges[0]  # 按照HTTP规范走206

    start = int(start) if start is not None and int(start) <= file_size else 0
    end = int(end) if end is not None and int(end) <= file_size else file_size - start - 1

    length = end - start + 1
    debug(start, end, length)
    data = None
    with open(file_path, 'rb') as f:
        f.seek(start)
        data = f.read(length)

    resp = Response(data,
                    206,
                    mimetype='application/octet-stream',
                    direct_passthrough=True)
    resp.headers.set('Content-Length', str(length))
    resp.headers.set('Content-Range', f'bytes {start}-{end}/{file_size}')
    resp.headers.set("ServerX", 'FileSyncTool/' + str(VERSION))
    return resp


# TODO: Token 数据库化
@app.route('/apix/token', methods=['POST', 'GET'])  # GET方法为获取 POST方法为提交
def file_token():
    if request.method == 'GET':
        try:
            sync_token = request.headers.get('X-API-X-TOKEN')
            sync_token = re.sub(r'[^a-zA-Z0-9]', '', sync_token)
            if sync_token is None or sync_token == "":
                sync_token = request.args.get("token")
                if sync_token is None or sync_token == "":
                    raise Exception
        except:
            error("UpdateToken : 加载传入参数失败")
            return serverMsgJson(399, "Input Error")

        result = sql.read_token(sync_token)
        if result is None:
            return serverMsgJson(881, "No Token", {})
        else:
            debug(result)
            qdata = {'sync_data': base64.b64encode(result[1]).decode("utf8"), "version_time": result[2]}
            debug(qdata)
            return serverMsgJson(200, "Check Ok", qdata)
    if request.method == 'POST':
        try:
            sync_token = request.headers.get('X-API-X-TOKEN')
            sync_token = re.sub(r'[^a-zA-Z0-9]', '', sync_token)
            if len(request.data) == 0:
                return serverMsgJson(400, "Empty Contant")
            if sync_token is None or sync_token == "":
                raise Exception
            version_time = request.headers.get('X-API-X-TIME')
            try:
                version_time = float(version_time)
            except:
                raise Exception
        except:
            error("UpdateToken : 加载传入参数失败")
            try:
                debug("UpdateToken : " + str(request.data.decode('utf-8')))
            except:
                pass
            return serverMsgJson(399, "Input Error")

        try:
            result = sql.write_token(sync_token, request.data, version_time)  # TODO: 做压缩入库处理和防炸弹等
            tmp_version_time[sync_token] = version_time
        except Exception as e:
            error("WriteToken : 写入同步数据失败 L:" + str(e.__traceback__.tb_lineno) + " E:" + str(e))
            return serverMsgJson(752, "Server Error", {})
        return serverMsgJson(200, "Write Ok", {'sync_data': result})


# TODO: 使用 Redis 缓存
@app.route('/apix/ping_keep', methods=['POST'])  # 保存链接的同时检查版本
def ping_keep():
    try:
        if len(request.data) == 0:
            return serverMsgJson(399, "Input Error")
        data = json.loads(request.data)
    except:
        error("UpdateToken : 加载传入参数失败")
        try:
            debug("UpdateToken : " + str(request.data.decode('utf-8')))
        except:
            pass
        return serverMsgJson(399, "Input Error")

    version_ser = {}
    for token in list(data):
        if token in tmp_version_time:
            version_ser[token] = tmp_version_time[token]
        else:
            result = sql.read_token(token)
            if not result is None:
                version_ser[token] = result[2]
            else:
                version_ser[token] = None
    return serverMsgJson(200, "GetOk", {"version_ser": version_ser})


# TODO: 友好的调试日志支持和 WEB 控制台支持
if WEB_DEBUG_API:
    @app.route('/apix/debug/tmp_files', methods=['POST', 'GET'])
    def debug_files():
        output_text = "<div><h3>TMP FILES:</h3>"
        if len(tmp_files) > 0:
            for tmp_file in tmp_files.values():
                output_text = output_text + "<li>" + str(milliSecondToTime(tmp_file['time'])) + " | " + str(tmp_file['file_size']) + " | " + tmp_file['file_md5'] + "</li>\n"
        else:
            output_text = output_text + "NO TMP FILES"
        output_text = output_text + "</div>"
        return output_text


    @app.route('/apix/debug/files', methods=['POST', 'GET'])
    def debug_file():
        output_text = "<div><h3>FILES:</h3>"
        debug_x_files = sql.debug_read_all_files()
        if debug_x_files is not None and len(debug_x_files) > 0:
            for debug_x_file in debug_x_files:
                output_text = output_text + "<li>" + str(milliSecondToTime(int(debug_x_file[2]))) + " | " + str(debug_x_file[1]) + " | " + debug_x_file[0] + " | " + debug_x_file[3] + "</li>\n"
        else:
            output_text = output_text = output_text + "NO FILES"
        output_text = output_text + "</div>"
        return output_text


def run_web():
    app.run(WEB_HOST, WEB_PORT)


if __name__ == '__main__':
    app.run(debug=False)
