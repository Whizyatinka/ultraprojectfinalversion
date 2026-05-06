import logging
import os

import aiofiles
from PIL import Image
import img2pdf

from app.config import config

logger = logging.getLogger(__name__)


class FileHandler:
    def __init__(self, downloads_dir: str = "downloads"):
        self.downloads_dir = downloads_dir
        os.makedirs(downloads_dir, exist_ok=True)

    async def save_temp_file(self, content: bytes, filename: str) -> str:
        filepath = os.path.join(self.downloads_dir, filename)
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
        return filepath

    async def images_to_pdf(self, image_paths: list[str], output_filename: str) -> str:
        output_path = os.path.join(self.downloads_dir, output_filename)
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_paths))
        return output_path

    async def compress_image(self, image_path: str, quality: int = None) -> str:
        if quality is None:
            quality = config.COMPRESSION_QUALITY

        output_path = image_path.replace(".jpg", "_compressed.jpg")

        with Image.open(image_path) as img:
            if max(img.size) > config.MAX_IMAGE_DIMENSION:
                img.thumbnail((config.MAX_IMAGE_DIMENSION, config.MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

            img.save(output_path, "JPEG", quality=quality, optimize=True)

        return output_path

    def check_file_size(self, filepath: str) -> int:
        return os.path.getsize(filepath)

    async def cleanup_temp_files(self, filepaths: list[str]):
        for path in filepaths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Failed to cleanup {path}: {e}")