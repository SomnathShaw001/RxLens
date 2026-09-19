import os
import uuid
from typing import Tuple
from fastapi import UploadFile
from app.core.config import settings


class StorageService:
    @staticmethod
    def ensure_local_dir():
        if not os.path.exists(settings.LOCAL_STORAGE_DIR):
            os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)

    @classmethod
    async def save_upload_file(cls, file: UploadFile) -> Tuple[str, str]:
        """
        Saves an uploaded image file.
        Returns: (file_id, file_path_or_url)
        """
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename or "")[1] or ".jpg"
        filename = f"{file_id}{ext}"

        cls.ensure_local_dir()
        dest_path = os.path.join(settings.LOCAL_STORAGE_DIR, filename)

        contents = await file.read()
        with open(dest_path, "wb") as f:
            f.write(contents)

        return file_id, dest_path
