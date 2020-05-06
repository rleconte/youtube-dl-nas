import json
import subprocess
from queue import Queue

import time
from bottle import run, Bottle, request, static_file, response, redirect, template, get
from threading import Thread
from bottle_websocket import GeventWebSocketServer
from bottle_websocket import websocket
from socket import error

class WSAddr:
    def __init__(self):
        self.wsClassVal = ''

app = Bottle()

port = 8080

@get('/')
def dl_queue_list():
    return template("./static/template/login.tpl", msg="")


@get('/login', method='POST')
def dl_queue_login():
    with open('Auth.json') as data_file:
        data = json.load(data_file)  # Auth info, when docker run making file
        req_id = request.forms.get("username")
        req_pw = request.forms.get("password")

        if (req_id == data["USERNAME"] and req_pw == data["PASSWORD"]):
            response.set_cookie("account", req_id, secret="34y823423b23b4234#$@$@#be")
            redirect("/youtube-dl")
        else:
            return template("./static/template/login.tpl", msg="id or password is not correct")


@get('/youtube-dl')
def dl_queue_list():
    with open('Auth.json') as data_file:
        data = json.load(data_file)

    userName = request.get_cookie("account", secret="34y823423b23b4234#$@$@#be")
    print("CHK : ", userName)

    if (userName == data["USERNAME"]):
        return template("./static/template/index.tpl", userName=userName)
    else:
        print("no cookie or fail login")
        redirect("/")


@get('/websocket', apply=[websocket])
def echo(ws):
    while True:
        WSAddr.wsClassVal = ws
        msg = WSAddr.wsClassVal.receive()

        if msg is not None:
            a = '[MSG], Started downloading  : '
            a = a + msg
            WSAddr.wsClassVal.send(a)
        else:
            break

@get('/youtube-dl/static/:filename#.*#')
def server_static(filename):
    return static_file(filename, root='./static')


@get('/youtube-dl/q', method='GET')
def q_size():
    return {"success": True, "size": json.dumps(list(dl_q.queue))}


@get('/youtube-dl/q', method='POST')
def q_put():
    url = request.json.get("url")
    resolution = request.json.get("resolution")

    if "" != url:
        box = (url, WSAddr.wsClassVal, resolution, "web")
        dl_q.put(box)

        if (Thr.dl_thread.isAlive() == False):
            thr = Thr()
            thr.restart()

        return {"success": True, "msg": '[MSG], We received your download. Please wait.'}
    else:
        return {"success": False, "msg": "[MSG], download queue somethings wrong."}



@get('/youtube-dl/rest', method='POST')
def q_put_rest():
    url = request.json.get("url")
    resolution = request.json.get("resolution")

    with open('Auth.json') as data_file:
        data = json.load(data_file)  # Auth info, when docker run making file
        req_id = request.json.get("username")
        req_pw = request.json.get("password")

        if (req_id != data["USERNAME"] or req_pw != data["PASSWORD"]):
            return {"success": False, "msg": "Invalid password or account."}
        else:
            box = (url, "", resolution, "api")
            dl_q.put(box)
            return {"success": True, "msg": 'download has started', "Remaining downloading count": json.dumps(dl_q.qsize()) }


def dl_worker():
    while not done:
        item = dl_q.get()
        if(item[3]=="web"):
            download(item)
        else:
            download_rest(item)
        dl_q.task_done()


def download(url):
    # url[1].send("[MSG], [Started] downloading   " + url[0] + "  resolution below " + url[2])
    result=""
    if (url[2] == "best"):
        result = subprocess.run(["youtube-dl", "-o", "./downfolder/%(title)s.%(ext)s", url[0]])
    elif (url[2] == "audio"):
         result = subprocess.run(["youtube-dl", "-o", "./downfolder/.incomplete/%(title)s.%(ext)s", "-f", "bestaudio[ext=m4a]", "--exec", "touch {} && mv {} ./downfolder/", url[0]])
    else:
        resolution = url[2][:-1]
        result = subprocess.run(["youtube-dl", "-o", "./downfolder/.incomplete/%(title)s.%(ext)s", "-f", "bestvideo[height<="+resolution+"]+bestaudio[ext=m4a]", "--exec", "touch {} && mv {} ./downfolder/",  url[0]])

    try:
        if(result.returncode==0):
            url[1].send("[MSG], [Finished] " + url[0] + "  resolution below " + url[2]+", Remain download Count "+ json.dumps(dl_q.qsize()))
            url[1].send("[QUEUE], Remaining download Count : " + json.dumps(dl_q.qsize()))
            url[1].send("[COMPLETE]," + url[2] + "," + url[0])
        else:
            url[1].send("[MSG], [Finished] downloading  failed  " + url[0])
            url[1].send("[COMPLETE]," + "url access failure" + "," + url[0])
    except error:
        print("Be Thread Safe")


def download_rest(url):
    result=""
    if (url[2] == "best"):
        result = subprocess.run(["youtube-dl", "-o", "./downfolder/%(title)s.%(ext)s", url[0]])
    elif (url[2] == "best-mp4"):
        result = subprocess.run(["youtube-dl", "-o", "./downfolder/.incomplete/%(title)s.%(ext)s", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]", "--exec", "touch {} && mv {} ./downfolder/", "--merge-output-format", "mp4", url[0]])
    elif (url[2] == "audio"):
         result = subprocess.run(["youtube-dl", "-o", "./downfolder/.incomplete/%(title)s.%(ext)s", "-f", "bestaudio[ext=m4a]", "--exec", "touch {} && mv {} ./downfolder/", url[0]])
    else:
        resolution = url[2][:-1]
        result = subprocess.run(["youtube-dl", "-o", "./downfolder/.incomplete/%(title)s.%(ext)s", "-f", "bestvideo[height<="+resolution+"]+bestaudio[ext=m4a]", "--exec", "touch {} && mv {} ./downfolder/",  url[0]])

class Thr:
    def __init__(self):
        self.dl_thread = ''

    def restart(self):
        self.dl_thread = Thread(target=dl_worker)
        self.dl_thread.start()


dl_q = Queue()
done = False
Thr.dl_thread = Thread(target=dl_worker)
Thr.dl_thread.start()

with open('Auth.json') as env_file:
    data = json.load(env_file)  # Auth info, when docker run making file

if (data['APP_PORT'] !=''):
    port = data['APP_PORT']

run(host='0.0.0.0', port=port, server=GeventWebSocketServer)

done = True

Thr.dl_thread.join()

