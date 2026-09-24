import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.config import STATIC_URL, UPLOAD_DIR
from app.deps import require_admin

router = APIRouter(prefix="/api/admin/upload", tags=["admin-upload"])

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg", "ico"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024


def _save_upload(file: UploadFile, subdir: str = "icons") -> str:
    upload_path = Path(UPLOAD_DIR) / subdir
    upload_path.mkdir(parents=True, exist_ok=True)

    ext = (file.filename or "image.png").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型：{ext}")

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件超过 2MB 限制")

    date_str = datetime.now().strftime("%Y%m")
    subdir_path = upload_path / date_str
    subdir_path.mkdir(parents=True, exist_ok=True)

    file_name = f"{uuid.uuid4().hex}.{ext}"
    dest = subdir_path / file_name

    content = file.file.read()
    dest.write_bytes(content)

    url_path = f"{STATIC_URL}/{subdir}/{date_str}/{file_name}"
    return url_path


@router.post("/icon")
async def upload_icon(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin),
):
    url = _save_upload(file, subdir="icons")
    return {"url": url, "file_name": file.filename}