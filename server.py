import sys,os
import http
import urllib.parse
import subprocess
import re
import time
import database
import locale
import _thread
sys.path.append('./lib/')
import youtube_dl
download_dir="E:/VideoDownload/"

def Run():
    http_server=http.server.HTTPServer(('localhost',4000),HTTPHandler)
    _thread.start_new_thread(Processor,())
    http_server.serve_forever()

def Processor():
    while True:
        queue=database.GetQueue()
        for (id,url) in queue:
            print('Try Start Task {0}:{1}'.format(id,url))
            #get title
            res = urllib.parse.urlparse(url)
            dir =os.path.join(download_dir,res.hostname.split('.')[-2])
            cmd = GetCmd(url, res.hostname)
            cmd.append('-e')

            if not os.path.exists(dir):
                os.makedirs(dir)
            #download
            cmd = GetCmd(url, res.hostname)
            cmd.append(["-o","\"{0}/%(title)s[{1}].%(ext)s\"".format(dir,id)])
            """
            ！！：需要在pycharm的setting的File Encodings里把encoding设置成System Default
            不设置Popen的encoding时返回bytes，设置后返回str，但是实际上只是对bytes做了decode而已，并不会更改进程实际返回的内容，设置的encoding不正确时会抛出异常
            使用pycharm的运行/调试运行时，实际编码使用pycharm的设置，而locale.getdefaultlocale()的值并不会随之变化，十分坑爹
            为了避免代码随IDE配置变化，只能将其设为System Default
            """
            p = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            _, stderr = p.communicate()
            if p.returncode != 0:
                print('Fail',id,stderr,stderr.decode(locale.getpreferredencoding()))
                database.UpdateRow(id,stderr.decode(locale.getpreferredencoding()))
            else:
                database.RemoveRow(id)
                print('Success', id)
        time.sleep(30)

def GetCmd(url:str,hostname):
    cmd = ["python", "./lib/youtube_dl/__main__.py",
                "--external-downloader", "aria2c",
                "--no-playlist",
                url]
    if 'xnxx' in hostname or 'xvideos' in hostname or 'pornhub' in hostname:
        cmd.append(["--proxy=127.0.0.1:1196"])
    elif 'youtube' in hostname :
        cmd.append(["--proxy=127.0.0.1:8000"])
    return cmd

class HTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if len(self.path)<=2:
            return
        url=self.path[2:]
        res=urllib.parse.urlparse(url)
        if res.scheme!='http' and res.scheme!='https':
            return
        database.InsertURL(url)
