import os
import http
import http.server
import urllib.parse
import re
import time
import database
import _thread
import downloader_youtubedl
import downloader_nhentai

PROXY_A="127.0.0.1:1196"
PROXY_B="127.0.0.1:8000"

def Run():
    http_server=http.server.HTTPServer(('localhost',4000),HTTPHandler)
    _thread.start_new_thread(Processor,())
    http_server.serve_forever()

def Processor():
    while True:
        queue=database.GetQueue()

        for (id,url,cookie) in queue:
            print('Try Start Task {0}:{1}'.format(id,url))
            res = urllib.parse.urlparse(url)

            if "nhentai" in res.hostname:
                dir = os.path.join("G:/DL_Pic/", res.hostname.split('.')[-2])
                success,msg=downloader_nhentai.Download(url,res.hostname,cookie,dir,PROXY_A,PROXY_B)
            else:
                dir = os.path.join("E:/VideoDownload/", res.hostname.split('.')[-2])
                success,msg=downloader_youtubedl.Download(url,res.hostname,cookie,dir,PROXY_A,PROXY_B)

            if success:
                database.RemoveRow(id)
            else:
                database.UpdateRow(id,msg)
        time.sleep(30)


class HTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if len(self.path)<=2:
            return
        text=self.path[2:]
        text=urllib.parse.parse_qs(text)
        if text.__contains__('url'):
            url=urllib.parse.unquote(text['url'][0])
        else:
            return
        if text.__contains__('cookie'):
            cookie=urllib.parse.unquote(text['cookie'][0])
        else:
            cookie=''
        res=urllib.parse.urlparse(url)
        if res.scheme!='http' and res.scheme!='https':
            return
        database.InsertURL(url,cookie)
