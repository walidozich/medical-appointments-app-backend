import os
import uuid
from pathlib import Path
from typing import BinaryIO


class StorageClient:
    """Abstraction to allow swapping local storage with S3 later."""

    def save(self, file_obj: BinaryIO, filename: str) -> str:  # returns URL/path
        raise NotImplementedError


class LocalStorage(StorageClient):
    def __init__(self, base_dir: str = "uploads/chat", base_url: str | None = None):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # base_url can be used to serve files via static hosting; fallback to path
        self.base_url = base_url

    def save(self, file_obj: BinaryIO, filename: str) -> str:
        name = f"{uuid.uuid4()}_{filename}"
        dest = self.base_dir / name
        with open(dest, "wb") as f:
            f.write(file_obj.read())
        if self.base_url:
            return f"{self.base_url.rstrip('/')}/{name}"
        return str(dest.resolve())
