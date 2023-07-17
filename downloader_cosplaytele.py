# -*- coding: utf-8 -*-
import os
import urllib.parse
import re
import requests
from lxml import etree
import locale
import subprocess
import re

def unicodetostr( s ):
    strTobytes = []
    for i in s.split('\\x'):
        if i != '':
            num = int(i,16)
            strTobytes.append(num)
    a = bytes(strTobytes).decode()
    return a
def ti(m):
    s = str(m.group())
    a = unicodetostr(s)
    return a


def Download(url,hostname,cookie,useragent, dir,proxy_a,proxy_b):
    tmp_dir=os.path.join(dir,"tmp")
    if not os.path.exists(dir):
        os.makedirs(dir)
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    try:
        #id=urllib.parse.urlparse(url).path.split('/')[1]
        #去掉非法字符
        #id=re.sub('[\/:*?"<>|]','_',id)
        #if id=='':
        #    id="empty"
        #获取页面
        page=str(requests.get(url).content)
        tree = etree.HTML(page)
        title = tree.xpath('//h1[@class="entry-title"]/text()')[0]
        pat = re.compile(r'(\\x[0-9a-fA-F][0-9a-fA-F])+')
        title = re.sub(pat, ti, title)
        title = re.sub('[\/:*?"<>|“”–-]','_',title)
        #密码似乎是固定的
        password='cosplaytele'
        #获取第三方下载页
        download_page_url = tree.xpath('//*[@class="fas fa-download"]/../../..//a/@href')[2]
        if 'mediafire.com' in download_page_url:
            # 从mediafire下载压缩包
            download_page = str(requests.get(download_page_url).content)
            tree = etree.HTML(download_page)
            download_url = str(tree.xpath('//a[@aria-label="Download file"]/@href')[0])
            filename = title + ".rar"  # 似乎固定是rar
            filepath = os.path.join(tmp_dir,filename)
            cmd = ["aria2c.exe", download_url,
                   "--dir", tmp_dir,
                   #"--all-proxy", proxy_b,
                   "--out", filename,
                   "--allow-overwrite=true",
                   "--split",'20',
                   ]
            print("Start Download ", download_url)
            process = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            _, stderr = process.communicate()
            if process.returncode != 0:
                print('Fail', stderr, stderr.decode(locale.getpreferredencoding()))
                return False, stderr.decode(locale.getpreferredencoding())
            else:
                print('Done')
            #解压
            sub_dir = os.path.join(dir, title)
            #7z的选项和参数间没有空格
            cmd = ["7z", "x",
                   filepath,
                   "-p"+password,
                   "-aos",#跳过已有文件
                   "-o"+sub_dir#路径里有空格不影响
                   ]
            print("Start Extract")
            process = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                print('Fail', stderr, stderr.decode(locale.getpreferredencoding()))
                return False, "Extract Error:"+stderr.decode(locale.getpreferredencoding())
            if "No files to process" in str(stdout):
                print('Fail', stdout, stdout.decode(locale.getpreferredencoding()))
                return False, "Extract None Files"
            os.remove(filepath)
            return True, ""
        else:
            return False,"Unknow Download Web:"+download_url
    except Exception as e:
        import traceback
        traceback.print_stack()
        return False,str(e)
