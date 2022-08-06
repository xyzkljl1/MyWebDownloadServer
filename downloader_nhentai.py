import os,sys
import urllib.parse
sys.path.insert(0,os.getcwd()+"/lib/")
import lib.nhentai
import lib.nhentai.command


def Download(url, hostname, cookie, useragent, dir,proxy_a,proxy_b):
    if not os.path.exists(dir):
        os.makedirs(dir)
    try:
        res=urllib.parse.urlparse(url)
        id=res.path.split('/')[2]
        lib.nhentai.command.main(proxy_a, cookie, useragent, ["--id="+id, "--format", "[%a](%i)%s", "-o", dir, "--no-html"])
        return True,""
    except Exception as e:
        import traceback
        traceback.print_stack()
        return False,str(e)
