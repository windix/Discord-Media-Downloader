import os
import time

import requests
from logger import logger
from utils import calculate_md5

# def download_file(
#     session: requests.Session, url: str, filepath: str, simulate=False
# ) -> None:
#     file_path, filename = os.path.split(filepath)
#     logger.info(f"Downloading: {filename}")
#     logger.debug(f"Path: {file_path}")
#     logger.debug(f"URL: {url}")

#     local_md5 = calculate_md5(filepath) if os.path.exists(filepath) else None
#     with session.get(url, stream=True) as r:
#         if r.status_code != 200:
#             return r.status_code
#         server_md5 = r.headers.get("ETag", "")
#         content_length = int(r.headers.get("Content-Length", "0"))
#         if not server_md5:
#             logger.warning(
#                 "No server hash found for attachment. Comparing Content-Length"
#             )
#             if content_length == 0:
#                 logger.error("No Content-Length header given.")
#             if os.path.getsize(filepath) == content_length:
#                 return 1
#         if server_md5 == f'"{local_md5}"':
#             return 1
#         total = int(r.headers.get("content-length", 0))
#         if not os.path.exists(file_path):
#             logger.debug("Creating Path because it did not exist")
#             os.makedirs(file_path)
#         start = time.time()
#         if simulate:
#             print_download_bar(1, 1, start, 0)
#             print()
#             return 200
#         with open(filepath, "wb") as f:
#             bar_len = 0
#             downloaded = 0
#             for chunk in r.iter_content(chunk_size=8192):
#                 downloaded += len(chunk)
#                 f.write(chunk)
#                 bar_len = print_download_bar(total, downloaded, start, bar_len)
#         print()
#     return r.status_code


def download_file(
    session: requests.Session,
    url: str,
    filepath: str,
    temp_file=True,
    resume=True,
    simulate=False,
) -> tuple[int, str]:
    file_path, filename = os.path.split(filepath)
    temp_filepath = filepath + ".part"
    file = temp_filepath if temp_file else filepath

    logger.info(f"Downloading: {filename}")
    logger.debug(f"Path: {file_path}")
    logger.debug(f"URL: {url}")

    range_header = {}
    if resume and os.path.exists(file):
        file_size = os.path.getsize(file)
        range_header = {"Range": f"bytes={file_size}-"}
        logger.info(f"Trying to resume download from byte {file_size}")

    # does not like when the session is passed. keeps giving 401 Unauthorized
    with requests.get(url, stream=True, headers=range_header) as r:
        start = time.time()
        bar_len = 0
        prev = (0, start)
        if r.status_code != 200 and r.status_code != 206:
            return r.status_code, r.reason

        downloaded = os.path.getsize(file) if resume and os.path.exists(file) else 0
        content_length = int(r.headers.get("content-length", 0))
        total = content_length + downloaded

        local_md5 = calculate_md5(filepath) if os.path.exists(filepath) else None
        server_md5 = r.headers.get("ETag", "")
        if local_md5:
            if server_md5 == f'"{local_md5}"':
                return 1, "File already exists and has correct hash"

            if server_md5 == "" and os.path.getsize(filepath) == total:
                return (
                    1,
                    "File already exists but no server hash was given but content-length matches",
                )

        if temp_file and os.path.exists(filepath):
            return 1, "File already exists but has incorrect hash"

        if simulate:
            print_download_bar(1, 1, start, prev, bar_len)
            print()
            return r.status_code, r.reason

        if not os.path.exists(file_path):
            logger.debug("Creating Path because it did not exist")
            os.makedirs(file_path)
        logger.debug(f"Writing response contents to {file}")
        mode = "ab" if resume and os.path.exists(file) else "wb"
        with open(file, mode) as f:
            print(f"[{' '*50}] 0/0 B at 0 B/s ETA 00:00:00", end="\r")
            for chunk in r.iter_content(chunk_size=8192):
                downloaded += len(chunk)
                f.write(chunk)
                bar_len, prev = print_download_bar(
                    total, downloaded, start, prev, bar_len
                )
        print()

    local_md5 = calculate_md5(file)
    if server_md5 != "" and server_md5 != f'"{local_md5}"':
        return (
            2,
            f"File completed with incorrect hash | expected: {server_md5} got: {local_md5}",
        )
    if total != downloaded:
        return (
            2,
            f"File completed with incorrect file size | total: {total} downloaded: {downloaded}",
        )
    if temp_file:
        os.rename(temp_filepath, filepath)
    return r.status_code, r.reason


def calculate_bytes(bytes: int):
    if bytes / 2**10 < 100:
        return (round(bytes / 2**10, 1), "KB")
    if bytes / 2**20 < 100:
        return (round(bytes / 2**20, 1), "MB")
    if bytes / 2**30 < 100:
        return (round(bytes / 2**30, 1), "GB")
    if bytes / 2**40 < 100:
        return (round(bytes / 2**40, 1), "TB")


def convert_bytes(bytes: int, size: str):
    if size == "KB":
        return round(bytes / 2**10, 1)
    elif size == "MB":
        return round(bytes / 2**20, 1)
    elif size == "GB":
        return round(bytes / 2**30, 1)
    elif size == "TB":
        return round(bytes / 2**40, 1)


# this is so messy
def print_download_bar(total, downloaded, start, prev, bar_len) -> None:
    now = time.time()
    td = now - start
    td2 = now - prev[1]
    if td < 0.1:
        return bar_len, prev

    rate, rate_size = calculate_bytes((downloaded) / td)

    progress = 0
    if total:
        progress = int(100 * downloaded / total)
        done = int(50 * downloaded / total)
        bar_fill = "=" * done
        bar_empty = " " * (50 - done)
        total, size = calculate_bytes(total)
        downloaded = convert_bytes(downloaded, size)
        eta = "00:00:00"
        # eta = time.strftime(
        #     "%H:%M:%S", time.gmtime((total - downloaded) / (downloaded / td))
        # )
    else:
        done = 50
        bar_fill = "?" * done
        bar_empty = " " * (50 - done)
        total = "???"
        downloaded, size = calculate_bytes(downloaded)
        eta = "00:00:00"

    progress_bar = f"[{bar_fill}{bar_empty}] {downloaded}/{total} {size} at {rate} {rate_size}/s ETA {eta}"
    overlap = bar_len - len(progress_bar)
    overlap_buffer = " " * overlap if overlap > 0 else ""
    # print(f"progress {progress} | prev[0] {prev[0]} | int(td2) {int(td2)}")
    # should make the amount of time before refreshing a ratio of prev eta and current eta
    if progress - prev[0] > 2 or (int(td2) > 10 and progress > 1):
        print(f"{progress_bar}{overlap_buffer}", end="\r")
        return len(progress_bar), (progress, now)
    return bar_len, prev
