import os
from types import SimpleNamespace
from urllib.parse import urlsplit

from doujinshi_dl.core.downloader import Downloader
from doujinshi_dl_nhentai import plugin, constant


_DEFAULT_USER_AGENT = constant.CONFIG["useragent"]


class _Downloader(Downloader):
    async def download(self, url, **kwargs):
        # The library does not forward its configured proxy to image downloads.
        kwargs["proxy"] = constant.CONFIG["proxy"] or None
        return await super().download(url, **kwargs)

    async def save(self, filename, response):
        # The library otherwise saves HTTP error bodies as successful downloads.
        if response is None or response.status_code != 200:
            return False
        return await super().save(filename, response)


def Download(url, hostname, cookie, useragent, dir, proxy_a, proxy_b, target_dir=None):
    try:
        gallery_id = urlsplit(url).path.split("/")[2]
        import database
        token = database.GetNHentaiApiToken().strip()
        if not token:
            return False, "NHentai Missing API Token in download_auth (Site=nhentai)"
        proxy = proxy_a if not proxy_a or "://" in proxy_a else "http://" + proxy_a
        constant.CONFIG.update(token=token, cookie="", proxy=proxy,
                               useragent=useragent or _DEFAULT_USER_AGENT)
        plugin.configure(SimpleNamespace(retry=3))
        meta = plugin.create_parser().fetch(gallery_id)
        if meta is None:
            return False, "NHentai Could not parse gallery metadata"
        model = plugin.create_model(meta, name_format="[%a](%i)%s").doujinshi
        if target_dir:
            dir = os.path.dirname(target_dir)
            model.filename = os.path.basename(target_dir)
        downloader = _Downloader()
        # The library caches Downloader instances; reset options for each task.
        downloader.__init__(path=dir, exit_on_fail=True)
        model.downloader = downloader
        if model.download() is not True:
            return False, "NHentai Download failed"
        return True, ""
    except (Exception, SystemExit) as error:
        return False, "NHentai " + type(error).__name__
