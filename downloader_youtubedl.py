# coding: utf-8
import os,sys
import subprocess
import locale
import re

def Download(url, hostname, cookie, useragent, dir, proxy_a, proxy_b, id):
    if not os.path.exists(dir):
        os.makedirs(dir)
    # download
    cmd = GetCmd(url, hostname, proxy_a, proxy_b, dir, id)
    """
    ！！：需要在pycharm的setting的File Encodings里把encoding设置成System Default
    不设置Popen的encoding时返回bytes，设置后返回str，但是实际上只是对bytes做了decode而已，并不会更改进程实际返回的内容，设置的encoding不正确时会抛出异常
    使用pycharm的运行/调试运行时，实际编码使用pycharm的设置，而locale.getdefaultlocale()的值并不会随之变化，十分坑爹
    为了避免代码随IDE配置变化，只能将其设为System Default
    """
    p = subprocess.Popen(cmd)#, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    _, stderr = p.communicate()
    if p.returncode != 0:
        print('Fail', id, stderr, stderr.decode(locale.getpreferredencoding()))
        return False,stderr.decode(locale.getpreferredencoding())
    else:
        print('Success', id)
        return True,""

"""
由于youtubedl对youtube/bilibili等网站均已无法下载，改用yt-dlp
下载youtube需要登录，由于use-cookies-from-browser功能有问题,需要在chrome上用Get cookies.txt LOCALLY插件导出txt格式cookies传入yt-dlp
注意命令行调用时，网址要加引号
"""
def GetCmd(url:str,hostname,proxy_a,proxy_b, dir, id):
    cmd = [".\yt-dlp.exe",
            url,
           "-o",f"{dir}\\%(title)s.%(ext)s",
           "--no-playlist"]
    if 'xnxx' in hostname or 'xvideos' in hostname or 'pornhub' in hostname:
        cmd.extend(["--proxy",proxy_a])
    elif 'youtube' in hostname :
        #go可以下载一些视频如https://www.youtube.com/watch?v=ckSf025flMU，但是对于某些视频会出现403如https://www.youtube.com/watch?v=20-PLhHNpGw
        cmd.extend(["--proxy",proxy_a,
                    "--cookies","www.youtube.com_cookies.txt"])
    elif 'bilibili' in hostname:
        cmd.extend(["--proxy",""])
        #分P视频
        #if re.search(r'\\?p=\d+',url) is not None:
        #    cmd.append(["-o", "\"{0}/%(title)s P%(sub_index)s %(sub_title)s[{1}].%(ext)s\"".format(dir, id)])
        #else:
        #    cmd.append(["-o", "\"{0}/%(title)s[{1}].%(ext)s\"".format(dir, id)])
    else:
        cmd.extend(["--proxy", ""])
        #cmd.extend(["-o", "\"{0}/%(title)s[{1}].%(ext)s\"".format(dir, id)])
    return cmd
