import os
import datetime
import shutil
from typing import Optional, Union, TextIO, BinaryIO, Any


def getFileName(key: str) -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    return f"{key}{timestamp}.data"


def writeFile(file_path: str, content: Union[str, bytes], mode: str = "w") -> None:
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    with open(file_path, mode) as f:
        f.write(content)


def getFile(file_path: str, mode: str = "r") -> Union[str, bytes]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, mode) as f:
        return f.read()


def deleteFile(file_path: str) -> bool:
    try:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            return True
        return False
    except Exception:
        return False
