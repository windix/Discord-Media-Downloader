import os
import re

from utils import convert_discord_timestamp


def create_format_variables(message: dict, attachment: dict, index: int = 0) -> dict:
    variables = {
        "filename": os.path.splitext(attachment["filename"])[0],
        "ext": os.path.splitext(attachment["filename"])[1][1:],
        "message_id": message["id"],
        "id": attachment["id"],
        "date": convert_discord_timestamp(message["timestamp"]),
        "username": message["author"]["username"],
        "user_id": message["author"]["id"],
    }
    return variables


def create_filepath(
    variables: dict,
    path: str,
    channel_format_template: str,
    dm_format_template: str,
    win_filenames: bool,
    restrict_filenames: bool,
) -> str:
    format_template = (
        channel_format_template if "server_id" in variables else dm_format_template
    )
    components = []
    first = True
    while format_template:
        head, tail = os.path.split(format_template)
        if first:
            components.insert(
                0,
                sanitize_filename(
                    tail.format(**variables), win_filenames, restrict_filenames
                ),
            )
            first = False
        else:
            components.insert(
                0,
                sanitize_foldername(
                    tail.format(**variables), win_filenames, restrict_filenames
                ),
            )
        format_template = head
    components.insert(0, path)
    filepath = os.path.join(*components)
    return filepath


def sanitize_filename(string, windows_naming, restrict_filenames):
    string = re.sub(r"[/]", "_", string)
    string = re.sub(r"[\x00-\x1f]", "", string)
    if os.name == "nt" or windows_naming:
        string = re.sub(r"[<>:\"/\\\|\?\*]", "_", string)
    if restrict_filenames:
        string = re.sub(r"[^\x21-\x7f]", "_", string)
    return string


def sanitize_foldername(string, windows_naming, restrict_filenames):
    string = sanitize_filename(string, windows_naming, restrict_filenames)
    # windows folder names can not end with spaces (" ") or periods (".")
    if os.name == "nt" or windows_naming:
        string = string.strip(" .")
    return string
