import os
import json
import http
import http.server
import sys
import urllib.parse
import re
import time
import database
import download_paths
import _thread
import downloader_youtubedl
import downloader_nhentai
import downloader_telegra
import downloader_cosplaytele

PROXY_A="127.0.0.1:1196"
PROXY_B="127.0.0.1:8000"

def Run():
    http_server=http.server.HTTPServer(('localhost',4000),HTTPHandler)
    _thread.start_new_thread(Processor,())
    http_server.serve_forever()

def Processor():
    while True:
        queue=database.GetQueue()

        for task in queue:
            ProcessTask(*task[:5], target_dir=task[5])
        time.sleep(30)


def ProcessTask(id, url, cookie, useragent, ignore_error, update_queue=True, target_dir=None):
    try:
        success,msg=DownloadTask(id, url, cookie, useragent, ignore_error, target_dir=target_dir)
        if update_queue:
            if success:
                database.RemoveRow(id)
            else:
                database.UpdateRow(id,msg)
        return success,msg
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        print('Task failed {0}:{1} {2}'.format(id,url,msg))
        if update_queue:
            database.UpdateRow(id,msg)
        return False,msg


def DownloadTask(id, url, cookie, useragent, ignore_error, target_dir=None):
    print('Try Start Task {0}:{1}'.format(id,url))
    res = urllib.parse.urlparse(url)
    options = {}
    if target_dir is not None:
        target_dir = download_paths.validate_target(url, target_dir)
        os.makedirs(target_dir, exist_ok=True)
        download_paths.validate_target(url, target_dir)
        options["target_dir"] = target_dir

    if "nhentai" in res.hostname:
        dir = os.path.join("G:/DL_Pic/", res.hostname.split('.')[-2])
        return downloader_nhentai.Download(url, res.hostname, cookie, useragent, dir, PROXY_A, PROXY_B, **options)
    elif "telegra.ph" in res.hostname:
        dir = "G:/DL_Pic/telegram_auto/org/"
        #dir = os.path.join("G:/DL_Pic/", res.hostname.split('.')[-2])
        return downloader_telegra.Download(url, res.hostname, cookie, useragent, dir, PROXY_A, PROXY_B, ignore_error, **options)
    elif "cosplaytele.com" in res.hostname:
        dir = "G:/DL_Pic/telegram_auto/org/"
        return downloader_cosplaytele.Download(url, res.hostname, cookie, useragent, dir, PROXY_A, PROXY_B, **options)
    elif res.hostname in ("anime1.me", "www.anime1.me"):
        import downloader_anime1
        return downloader_anime1.Download(url, "E:/VideoDownload/anime1", useragent, **options)
    else:
        dir = target_dir or os.path.join("E:/VideoDownload/", res.hostname.split('.')[-2])
        return downloader_youtubedl.Download(url, res.hostname, cookie, useragent, dir, PROXY_A, PROXY_B, id)

class HTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            text = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query,
                                        keep_blank_values=True)
            url = urllib.parse.unquote(text.get('url', [''])[0])
            cookie = urllib.parse.unquote(text.get('cookie', [''])[0])
            useragent = self.headers.get('user-agent', '')
            res = urllib.parse.urlparse(url)
            if res.scheme not in ('http', 'https') or not res.hostname:
                raise ValueError("A valid HTTP/HTTPS url is required")
            if len(text.get('dir', [])) > 1:
                raise ValueError("Only one dir parameter is allowed")
            # parse_qs has already decoded dir; do not decode literal '%' twice.
            relative_dir = text.get('dir', [''])[0] or None
            task_id, target = database.InsertURL(url, cookie, useragent, relative_dir)
        except ValueError as error:
            self.send_error(400, str(error))
            return
        except Exception as error:
            print("Fail To Add Task to Queue:", error)
            self.send_error(500, "Could not add download task")
            return
        body = (json.dumps({"id": task_id, "target_dir": target}, ensure_ascii=False).encode('utf-8')
                if target is not None else b'')
        self.send_response(200)
        if body:
            self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    #HTTPServer默认把error和message都写到stderr，非常坑爹
    def log_error(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))
        return

    def log_message(self, format, *args):
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))
