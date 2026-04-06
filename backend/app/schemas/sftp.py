from pydantic import BaseModel, Field
from typing import Optional


class FileItem(BaseModel):
    name: str
    is_dir: bool
    size: int = 0
    mtime: str = ""
    permissions: str = ""


class FileListResponse(BaseModel):
    path: str
    files: list[FileItem]


class MkdirRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=4096)


class RenameRequest(BaseModel):
    old_path: str = Field(..., min_length=1, max_length=4096)
    new_path: str = Field(..., min_length=1, max_length=4096)
