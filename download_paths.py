import ntpath
import os
import re
import stat
from urllib.parse import urlsplit


def root_for_url(url):
    host = urlsplit(url).hostname or ""
    if host in ("anime1.me", "www.anime1.me"):
        return os.path.abspath("E:/VideoDownload/anime1")
    if "nhentai" in host:
        return os.path.abspath("G:/DL_Pic/nhentai")
    if "telegra.ph" in host or "cosplaytele.com" in host:
        return os.path.abspath("G:/DL_Pic/telegram_auto/org")
    return os.path.abspath("E:/VideoDownload")


def _parts(relative_dir):
    if (not relative_dir or ntpath.splitdrive(relative_dir)[0] or
            relative_dir.startswith(("/", "\\"))):
        raise ValueError("dir must be a nonempty relative path")
    parts = relative_dir.replace("/", "\\").split("\\")
    for part in parts:
        if (not part or part in (".", "..") or part.endswith((" ", ".")) or
                re.search(r'[<>:"|?*\x00-\x1f\x7f]', part) or
                re.match(r"^(CON|PRN|AUX|NUL|CLOCK\$|CONIN\$|CONOUT\$|"
                         r"COM[1-9\u00b9\u00b2\u00b3]|LPT[1-9\u00b9\u00b2\u00b3]) *(?:\.|$)",
                         part, re.I)):
            raise ValueError("dir contains an invalid directory name")
        if len(part.encode("utf-16-le")) // 2 > 255:
            raise ValueError("Directory name is too long")
    return parts


def _check_path(root, path, include_target):
    if (os.path.normcase(os.path.commonpath([root, path])) != os.path.normcase(root)
            or os.path.normcase(path) == os.path.normcase(root)):
        raise ValueError("Target directory escapes download root")
    # Leave room for numbered images and partial-download control files.
    if len(path.encode("utf-16-le")) // 2 >= 240:
        raise ValueError("Target directory is too long")
    current = path if include_target else os.path.dirname(path)
    while True:
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            pass
        else:
            if (stat.S_ISLNK(info.st_mode) or
                    getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise ValueError("Download path contains a link or junction")
            if not stat.S_ISDIR(info.st_mode):
                raise ValueError("Download path is not a directory")
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent


def candidate(url, relative_dir, suffix=0):
    parts = _parts(relative_dir)
    if suffix:
        parts[-1] += "_" + str(suffix)
    root = root_for_url(url)
    path = os.path.join(root, *parts)
    _check_path(root, path, False)
    # Canonicalize existing parents without following an occupied leaf junction.
    path = os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path))
    _check_path(root, path, False)
    return path


def occupied(path):
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    return True


def validate_target(url, target_dir):
    root = root_for_url(url)
    if not ntpath.isabs(target_dir) or not ntpath.splitdrive(target_dir)[0]:
        raise ValueError("Stored target directory must be absolute")
    path = os.path.abspath(target_dir)
    _parts(os.path.relpath(path, root))
    _check_path(root, path, True)
    return path
