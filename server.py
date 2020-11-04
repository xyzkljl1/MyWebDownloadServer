import sys,os
import http
import urllib.parse
import subprocess
import re
import time
import database
import _thread
sys.path.append('./lib/')
import youtube_dl
download_dir="D:/VideoDownload/"

def Run():
    http_server=http.server.HTTPServer(('localhost',4000),HTTPHandler)
    _thread.start_new_thread(Processor)
    http_server.serve_forever()

def Processor():
    while True:
        queue=database.GetQueue()
        for (id,url) in queue:
            #get title
            res = urllib.parse.urlparse(url)
            dir =os.path.join(download_dir,res.hostname.split('.')[-2])
            cmd = GetCmd(url, res.hostname)
            cmd.append('-e')
            p = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            title, stderr = p.communicate()
            if p.returncode != 0:
                print(stderr.decode('utf-8', 'replace'))
                continue
            name = re.sub("[\/\\\:\*\?\"\<\>\|]", "_", title[:-1].decode()) + "[{0}]".format(id)
            path=os.path.join(dir,name)
            if not os.path.exists(dir):
                os.makedirs(dir)
            if os.path.exists(path):
                os.remove(path)
            #download
            cmd = GetCmd(url, res.hostname)
            cmd.append(["-o","\"{0}\"".format(path)])
            p = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            _, stderr = p.communicate()
            if p.returncode != 0:
                print(stderr.decode('utf-8', 'replace'))
                continue
            if os.path.exists(path):
                database.RemoveRow(id)
        time.sleep(30)

def GetCmd(url:str,hostname):
    cmd = ["python", "./lib/youtube_dl/__main__.py",
                "--external-downloader", "aria2c",
                "--no-playlist",
                url]
    if 'youtube' in hostname or 'xnxx' in hostname or 'xvideos' in hostname:
        cmd.append(["--proxy", "127.0.0.1:1081"])
    else:
        cmd.append([])
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
