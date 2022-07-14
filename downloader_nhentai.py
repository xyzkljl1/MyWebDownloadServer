import os,sys
import urllib.parse
sys.path.insert(0,os.getcwd()+"/lib/")
import lib.nhentai
import lib.nhentai.command


def Download(url,hostname,cookie,dir,proxy_a,proxy_b):
    if not os.path.exists(dir):
        os.makedirs(dir)
    try:
        res=urllib.parse.urlparse(url)
        id=res.path.split('/')[2]
        lib.nhentai.command.main(proxy_a,cookie,["--id="+id,"--format","[%a](%i)%s","-o",dir,"--no-html","--useragent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"])
        return True,""
    except Exception as e:
        import traceback
        traceback.print_stack()
        return False,str(e)
