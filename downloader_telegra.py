# -*- coding: utf-8 -*-
import os
import urllib.parse
import re
import requests
import html.parser
import locale
import subprocess


class MyHTMLParser(html.parser.HTMLParser):
    def __init__(self):
        html.parser.HTMLParser.__init__(self)
        self.data=[]

    def handle_starttag(self, tag, attrs):
        if tag=="img":
            for pair in attrs:
                if pair[0] == 'src':
                    self.data.append(pair[1])


def Download(url,hostname,cookie,useragent, dir,proxy_a,proxy_b):
    if not os.path.exists(dir):
        os.makedirs(dir)
    try:
        id=urllib.parse.urlparse(url).path.split('/')[1]
        #去掉非法字符
        id=re.sub('[\/:*?"<>|]','_',id)
        if id=='':
            id="empty"
        tmp=requests.get(url,proxies={"http":proxy_a,"https":proxy_a})
        tmp=tmp.content
        page=str(tmp)
        parser=MyHTMLParser()
        parser.feed(page)
        parser.close()
        ct=1
        sub_dir=os.path.join(dir,id)
        for p in parser.data:
            #有站内路径和站外路径两种
            if p.startswith("http://") or p.startswith("https://"):
                img_url=p
            else:
                img_url="https://telegra.ph"+p
            ext=os.path.splitext(p)[1]
            filename=str(ct).zfill(4)+ext
            cmd = ["aria2c.exe",img_url,
                   "--dir",sub_dir,
                   "--all-proxy",proxy_a,
                   "--out",filename,
                   "--allow-overwrite=true",
                   "--check-certificate=false"
                   ]
            print("Start Download ",img_url)
            process = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            _, stderr = process.communicate()
            if process.returncode != 0:
                print('Fail', stderr, stderr.decode(locale.getpreferredencoding()))
                return False, stderr.decode(locale.getpreferredencoding())
            else:
                print('Done')
            ct+=1
        print("All Done",ct-1)
        return True,""
    except Exception as e:
        import traceback
        traceback.print_stack()
        return False,str(e)
