import json
import os
import re
import subprocess
import time
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

import subprocess_cleanup


MAX_EPISODES = 500
API_URL = "https://v.anime1.me/api"
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
TITLE_PATTERN = re.compile(
    r"^(.+?)\s*\[(\d+(?:\.\d+)?|(?:OVA|OAD|SP)(?:\s*\d+)?)\]$", re.I)
# Extensions, MIME types and the corresponding ffprobe demuxer name.
VIDEO_FORMATS = (
    ((".mp4", ".m4v", ".f4v"), ("video/mp4", "video/x-m4v", "video/x-f4v"), "mov"),
    ((".mov", ".qt"), ("video/quicktime",), "mov"),
    ((".3gp",), ("video/3gpp",), "mov"),
    ((".3g2",), ("video/3gpp2",), "mov"),
    ((".webm",), ("video/webm",), "matroska"),
    ((".mkv",), ("video/x-matroska", "video/matroska"), "matroska"),
    ((".avi",), ("video/x-msvideo", "video/avi"), "avi"),
    ((".flv",), ("video/x-flv",), "flv"),
    ((".ts", ".mts", ".m2ts"), ("video/mp2t",), "mpegts"),
    ((".mpg", ".mpeg", ".mpe"), ("video/mpeg",), "mpeg"),
    ((".ogv", ".ogg"), ("video/ogg",), "ogg"),
    ((".wmv", ".asf"), ("video/x-ms-wmv", "video/x-ms-asf"), "asf"),
)


@dataclass(frozen=True)
class Episode:
    url: str
    title: str
    series: str
    number: str
    category: str


@dataclass(frozen=True)
class Series:
    title: str
    category: str
    episodes: tuple


def _text(value):
    return " ".join(unicodedata.normalize("NFC", value).split())


def _site_url(url):
    parts = urlsplit(url)
    if (parts.scheme not in ("http", "https") or parts.hostname not in
            ("anime1.me", "www.anime1.me") or parts.username or
            parts.password or parts.port not in (None, 80, 443)):
        raise ValueError("Unexpected Anime1 page host")
    path = unquote(parts.path).rstrip("/")
    if not re.fullmatch(r"/\d+|/category/[^?#]+", path):
        raise ValueError("Expected an Anime1 episode or category page")
    if any(segment in (".", "..") for segment in path.split("/")):
        raise ValueError("Invalid page path")
    return urlunsplit(("https", "anime1.me", quote(path, safe="/-._~"), "", ""))


def _category_url(url):
    url = _site_url(url)
    if not urlsplit(url).path.startswith("/category/"):
        raise ValueError("Missing series category")
    return re.sub(r"/page/[1-9]\d*$", "", url)


class Client:
    def __init__(self, useragent=""):
        self.session = requests.Session()
        self.session.trust_env = False
        if useragent:
            self.session.headers["User-Agent"] = useragent

    def close(self):
        self.session.close()

    def request(self, method, url, **kwargs):
        for attempt in range(3):
            try:
                response = self.session.request(
                    method, url, timeout=(10, 20), allow_redirects=False, **kwargs)
            except (requests.ConnectionError, requests.Timeout):
                if attempt == 2:
                    raise
                time.sleep(1)
                continue
            if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                response.close()
                time.sleep(1)
                continue
            return response

    def page(self, url):
        url = _site_url(url)
        for _ in range(5):
            with self.request("GET", url) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    url = _site_url(urljoin(url, response.headers["Location"]))
                    continue
                response.raise_for_status()
                return BeautifulSoup(response.content, "html.parser")
        raise ValueError("Too many page redirects")

    def media(self, episode):
        soup = self.page(episode.url)
        articles = soup.select("article")
        if len(articles) != 1 or _episode(articles[0], episode.url) != episode:
            raise ValueError("Episode title/category changed after validation")
        payload = articles[0].select_one("video")["data-apireq"]
        with self.request("POST", API_URL, data="d=" + payload, headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://anime1.me", "Referer": episode.url}) as response:
            response.raise_for_status()
            sources = response.json().get("s", [])
        # Multiple sources could be qualities or different videos; do not guess.
        if len(sources) != 1 or not sources[0].get("src"):
            raise ValueError("Expected exactly one video source")
        url = urljoin(API_URL, sources[0]["src"])
        parts = urlsplit(url)
        host = parts.hostname or ""
        if (any(c in url for c in "\r\n") or parts.scheme != "https" or
                parts.username or parts.password or parts.port not in (None, 443) or not
                (host == "v.anime1.me" or host.endswith(".v.anime1.me"))):
            raise ValueError("Unexpected video source host")
        prepared = self.session.prepare_request(requests.Request("GET", url))
        cookie = prepared.headers.get("Cookie", "")
        if not cookie or any(c in cookie for c in "\r\n"):
            raise ValueError("Missing or invalid playback cookies")
        return url, cookie, self.session.headers["User-Agent"], sources[0].get("type", "")


def _episode(article, page_url):
    heading = article.select_one(".entry-title")
    if heading is None:
        raise ValueError("Article has no episode title")
    title = _text(heading.get_text(" ", strip=True))
    match = TITLE_PATTERN.fullmatch(title)
    if match is None:
        raise ValueError("Unrecognized episode title: " + ascii(title))
    series, number = _text(match[1]), match[2].upper()
    link = heading.select_one("a[href]")
    url = _site_url(urljoin(page_url, link["href"])) if link else _site_url(page_url)
    post_id = re.fullmatch(r"post-(\d+)", article.get("id", ""))
    if post_id is None or urlsplit(url).path != "/" + post_id[1]:
        raise ValueError("Episode URL does not match its article ID")
    categories = {_category_url(urljoin(page_url, a["href"]))
                  for a in article.select(".cat-links a[href], a[rel~=category][href]")
                  if _text(a.get_text(" ", strip=True)) == series}
    if len(categories) != 1:
        raise ValueError("Cannot identify a unique category matching episode title")
    videos = article.select("video")
    if len(videos) != 1 or not videos[0].get("data-apireq"):
        raise ValueError("Expected exactly one playable video per episode")
    return Episode(url, title, series, number, next(iter(categories)))


def _sort_episode(episode):
    if re.fullmatch(r"\d+(?:\.\d+)?", episode.number):
        return (0, Decimal(episode.number), "")
    match = re.fullmatch(r"(OVA|OAD|SP)\s*(\d*)", episode.number)
    return (1, Decimal(match[2] or "0"), match[1])


def Discover(url, client):
    url = _site_url(url)
    anchor = None
    if not urlsplit(url).path.startswith("/category/"):
        articles = client.page(url).select("article")
        if len(articles) != 1:
            raise ValueError("Expected a single episode article")
        anchor = _episode(articles[0], url)
        category = anchor.category
    else:
        category = _category_url(url)
    pending, visited, episodes = [category], set(), {}
    series = anchor.series if anchor else None
    while pending:
        page_url = pending.pop(0)
        if page_url in visited:
            continue
        if len(visited) >= MAX_EPISODES:
            raise ValueError("Category pagination exceeds safety limit")
        visited.add(page_url)
        soup = client.page(page_url)
        heading = soup.select_one(".page-title")
        if heading is None:
            raise ValueError("Missing category title")
        page_title = _text(heading.get_text(" ", strip=True))
        if series is None:
            series = page_title
        if page_title != series:
            raise ValueError("Category title mismatch")
        articles = soup.select("article")
        if not articles:
            raise ValueError("Empty category page; refusing incomplete series")
        for article in articles:
            episode = _episode(article, page_url)
            if episode.series != series or episode.category != category:
                raise ValueError("Mixed episode title prefixes or categories")
            if episode.url in episodes and episodes[episode.url] != episode:
                raise ValueError("Conflicting duplicate episode")
            episodes[episode.url] = episode
            if len(episodes) > MAX_EPISODES:
                raise ValueError("Video count exceeds 500")
        for link in soup.select(".nav-links a[href], .nav-previous a[href], "
                                ".pagination a[href], .wp-pagenavi a[href], "
                                "a.page-numbers[href], a[rel~=next][href], link[rel~=next][href]"):
            target = _site_url(urljoin(page_url, link["href"]))
            if (_category_url(target) != category or
                    (target != category and not re.fullmatch(
                        re.escape(category) + r"/page/[1-9]\d*", target))):
                raise ValueError("Pagination leaves the selected category")
            is_next = ("next" in link.get("rel", []) or "next" in link.get("class", []) or
                       link.find_parent(class_="nav-previous") is not None)
            if is_next and target in visited:
                raise ValueError("Category pagination loop")
            if target not in visited and target not in pending:
                pending.append(target)
    if anchor and episodes.get(anchor.url) != anchor:
        raise ValueError("Starting episode is missing from its category")
    ordered = tuple(sorted(episodes.values(), key=_sort_episode))
    if len({_sort_episode(e) for e in ordered}) != len(ordered):
        raise ValueError("Duplicate episode numbers")
    return Series(series, category, ordered)


def _safe_name(value):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).rstrip(" .")
    if not name or name in (".", ".."):
        raise ValueError("Empty output name")
    if re.fullmatch(r"CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]", name.split(".")[0], re.I):
        name = "_" + name
    return name


def _checked_path(root, *parts):
    root = os.path.abspath(root)
    path = os.path.abspath(os.path.join(root, *parts))
    if (os.path.normcase(os.path.realpath(root)) != os.path.normcase(root) or
            os.path.normcase(os.path.commonpath([root, os.path.realpath(path)])) !=
            os.path.normcase(root)):
        raise ValueError("Output path escapes download directory")
    if len((path + ".part.aria2").encode("utf-16-le")) // 2 >= 260:
        raise ValueError("Output path is too long")
    return path


def _video_extension(url, *content_types):
    extension = os.path.splitext(unquote(urlsplit(url).path))[1].lower()
    if any(extension in extensions for extensions, _, _ in VIDEO_FORMATS):
        return extension
    for content_type in content_types:
        mime = (content_type or "").split(";", 1)[0].strip().lower()
        for extensions, mime_types, _ in VIDEO_FORMATS:
            if mime in mime_types:
                return extensions[0]
    raise ValueError("Cannot determine video file extension")


def _media_info(url, cookie, useragent, referer, media_type):
    with requests.Session() as session:
        session.trust_env = False
        with session.get(url, headers={"Cookie": cookie, "User-Agent": useragent,
                "Referer": referer, "Range": "bytes=0-0"}, timeout=(10, 20),
                stream=True, allow_redirects=False) as response:
            response.raise_for_status()
            if response.status_code == 206:
                match = re.fullmatch(r"bytes 0-0/(\d+)", response.headers.get("Content-Range", ""))
                size = int(match[1]) if match else 0
            elif response.status_code == 200:
                size = int(response.headers.get("Content-Length", "0"))
            else:
                size = 0
            if size <= 0:
                raise ValueError("Video server returned no valid video size")
            return size, _video_extension(url, response.headers.get("Content-Type", ""), media_type)


def _valid_video(path, size, extension):
    if not os.path.isfile(path) or os.path.getsize(path) != size:
        return False
    process = subprocess_cleanup.popen_in_cleanup_job(
        [os.path.join(TOOLS_DIR, "ffprobe.exe"), "-v", "error", "-show_entries",
         "format=duration,format_name:stream=codec_type", "-of", "json", path],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        output, _ = process.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        return False
    try:
        data = json.loads(output)
        formats = data["format"]["format_name"].split(",")
        return (process.returncode == 0 and float(data["format"]["duration"]) > 0 and
                any(extension in extensions and name in formats
                    for extensions, _, name in VIDEO_FORMATS) and
                any(s.get("codec_type") == "video" for s in data.get("streams", [])))
    except (ValueError, KeyError, TypeError):
        return False


def _aria2(url, cookie, useragent, episode, partial):
    env = {k: v for k, v in os.environ.items() if k.lower() not in
           ("http_proxy", "https_proxy", "all_proxy", "ftp_proxy", "no_proxy")}
    cmd = [os.path.join(TOOLS_DIR, "aria2c.exe"), "--no-conf=true",
           "--all-proxy=", "--http-proxy=", "--https-proxy=",
           "--split=4", "--max-connection-per-server=4", "--min-split-size=1M",
           "--continue=true", "--auto-file-renaming=false", "--allow-overwrite=false",
           "--file-allocation=none", "--auto-save-interval=5",
           "--connect-timeout=10", "--timeout=20", "--max-tries=3", "--retry-wait=2",
           "--console-log-level=warn", "--summary-interval=0", "--show-console-readout=false",
           "--dir=" + os.path.dirname(partial),
           "--referer=" + episode.url, "--user-agent=" + useragent, "--input-file=-"]
    # Keep short-lived cookies off the process command line and disk.
    download_input = (url + "\n  out=" + os.path.basename(partial) +
                      "\n  header=Cookie: " + cookie + "\n")
    process = subprocess_cleanup.popen_in_cleanup_job(
        cmd, env=env, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    process.communicate(download_input.encode("utf-8"))
    return process.returncode


def _download_episode(client, episode, output):
    for attempt in range(2):
        try:
            url, cookie, useragent, media_type = client.media(episode)
            size, extension = _media_info(url, cookie, useragent, episode.url, media_type)
            folder = os.path.dirname(output)
            final = _checked_path(folder, os.path.basename(output) + extension)
            partial = _checked_path(folder, os.path.basename(final) + ".part")
            _checked_path(folder, os.path.basename(partial) + ".aria2")
            if not os.path.exists(final + ".aria2") and _valid_video(final, size, extension):
                return
            if not os.path.exists(partial + ".aria2") and _valid_video(partial, size, extension):
                os.replace(partial, final)
                return
            result = _aria2(url, cookie, useragent, episode, partial)
            if result != 0:
                raise RuntimeError("aria2 exit code %s" % result)
            if os.path.exists(partial + ".aria2") or not _valid_video(partial, size, extension):
                raise ValueError("Downloaded video failed size/media/container validation")
            os.replace(partial, final)
            return
        except (requests.RequestException, RuntimeError):
            if attempt == 1:
                raise
            # Retry with a fresh page, media URL and playback cookies.
            time.sleep(1)


def Download(url, dir, useragent=""):
    client = Client(useragent)
    try:
        series = Discover(url, client)
        folder = _checked_path(dir, _safe_name(series.title))
        outputs = [_checked_path(dir, _safe_name(series.title), _safe_name(e.title))
                   for e in series.episodes]
        if len({p.casefold() for p in outputs}) != len(outputs):
            raise ValueError("Episode filenames collide")
        os.makedirs(folder, exist_ok=True)
        failures = []
        for index, (episode, output) in enumerate(zip(series.episodes, outputs), 1):
            print("Anime1: episode %s/%s [%s]" % (index, len(outputs), episode.number))
            try:
                _checked_path(dir, os.path.relpath(output, dir))
                _download_episode(client, episode, output)
            except Exception as error:
                failures.append("[%s] %s: %s" % (episode.number, type(error).__name__, str(error)[:200]))
        if failures:
            return False, "Anime1 Fail:%s/%s %s" % (len(failures), len(outputs), "; ".join(failures[:10]))
        return True, ""
    except Exception as error:
        return False, "Anime1 %s: %s" % (type(error).__name__, str(error)[:1000])
    finally:
        client.close()
