# coding: utf-8
import os,sys
import subprocess
import locale


def Download(url,hostname,cookie,dir,proxy_a,proxy_b):
    if not os.path.exists(dir):
        os.makedirs(dir)
    # download
    cmd = GetCmd(url, hostname,proxy_a,proxy_b)
    cmd.append(["-o", "\"{0}/%(title)s[{1}].%(ext)s\"".format(dir, id)])
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
        print('Fail', id, stderr, stderr.decode(locale.getpreferredencoding()))
        return False,stderr.decode(locale.getpreferredencoding())
    else:
        print('Success', id)
        return True,""

def GetCmd(url:str,hostname,proxy_a,proxy_b):
    cmd = ["python", "./lib/youtube_dl/__main__.py",
                "--external-downloader", "aria2c",
                "--no-playlist",
                url]
    if 'xnxx' in hostname or 'xvideos' in hostname or 'pornhub' in hostname:
        cmd.append(["--proxy="+proxy_a])
    elif 'youtube' in hostname :
        cmd.append(["--proxy="+proxy_b])
    return cmd
