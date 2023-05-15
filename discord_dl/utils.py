import hashlib
import random
import re
import time
from datetime import datetime

from logger import logger


def mysleep(sleep_base: int, sleep_range: list):
    if sleep_base or (sleep_range[0] != 0 and sleep_range[1] != 0):
        sleep = sleep_base + random.uniform(sleep_range[0], sleep_range[1])
        logger.info(f"Sleeping for {sleep} seconds")
        time.sleep(sleep)


def convert_discord_timestamp(timestamp):
    try:
        return datetime.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        return datetime.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S%z")


def calculate_md5(file_path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def extract_channel_ids(channel_ids):
    pattern = r"(\d+)|(https://discord.com/channels/[^/]+/(\d+))"
    results = []
    for channel_id in channel_ids:
        match = re.search(pattern, channel_id)
        if match:
            results.append(match.group(1) if match.group(1) else match.group(3))
        else:
            logger.warning(f"Could not find discord channel id in: {channel_id}")
    return results
