import webbrowser
import json
import pystray
from PIL import Image
from flask import *
from pystray import MenuItem as item

from file import *


class SyncAppGUI(threading.Thread):  # 托盘图标
    def __init__(self):
        super().__init__()
        # 初始化系统托盘图标
        icon_image = Image.open("./static/icon.png")
        menu = (item('显示主界面', self.show_window),
                item('退出', self.quit_app))
        self.tray_icon = pystray.Icon("文件同步工具", icon_image, "文件同步工具", menu)

    def run(self):
        self.tray_icon.run()

    def show_window(self, icon, item):
        webbrowser.open("http://127.0.0.1:9229")

    def quit_app(self, icon, item):
        pass


app = Flask(__name__)  # WEBUI
sync_gui = SyncAppGUI()  # 托盘图标


@app.route("/", methods=['GET'])
def index():
    return app.send_static_file("index.html")


@app.route("/apix/sync_list", methods=['GET', 'POST'])
def get_sync_list():
    if request.method == "GET":
        sync_list_s = list(sync_list.values())
        data = {"count": len(sync_list_s), "data": sync_list_s}  # 这里 sync_list 需要响应为一个 list 需要包含 token time status
        if len(sync_list_s) == 0:
            msg = "无同步任务"
        else:
            msg = "Ok"
        return serverMsgJson(200, msg, data)
    else:
        try:
            data = json.loads(request.data)
        except:
            return serverMsgJson(808, "Input Error")
        if not "token" in data or not "path" in data:
            return serverMsgJson(808, "Input Error")
        token = str(data['token'])
        mode = str(data['mode'])
        path = str(data['path'])
        result_add = addToken(token, path, mode)
        if result_add == 0:
            return serverMsgJson(200, "Success", {"v_code": 0})
        else:
            return serverMsgJson(200, "Error", {"v_code": result_add})


def run_gui():
    sync_gui.start()
    app.run(WEB_HOST, WEB_PORT)


if __name__ == "__main__":
    run_gui()
