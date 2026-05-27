import uuid
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from config import settings

PROFILE_PICS_DIR = Path("media/profile_pics")


class StorageService(ABC):
    @abstractmethod
    def upload(self, filename: str, content: bytes) -> None:
        pass

    @abstractmethod
    def delete(self, filename: str) -> None:
        pass

    @abstractmethod
    def download(self, filename: str) -> bytes:
        pass


class LocalStorage(StorageService):
    def upload(self, filename: str, content: bytes) -> None:
        filepath = PROFILE_PICS_DIR / filename
        PROFILE_PICS_DIR.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(content)

    def delete(self, filename: str) -> None:
        if filename is None:
            return
        filepath = PROFILE_PICS_DIR / filename
        if filepath.exists():
            filepath.unlink()

    def download(self, filename: str) -> bytes:
        filepath = PROFILE_PICS_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Image {filename} not found")
        with open(filepath, "rb") as f:
            return f.read()


class AzureStorage(StorageService):
    def __init__(self):
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError:
            raise ImportError("azure-storage-blob is required for Azure storage. Install it with: pip install azure-storage-blob")

        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.azure_storage_account_key
        )
        self.container_client = self.blob_service_client.get_container_client(
            settings.azure_storage_container_name
        )

    def upload(self, filename: str, content: bytes) -> None:
        self.container_client.upload_blob(name=filename, data=content, overwrite=True)

    def delete(self, filename: str) -> None:
        if filename is None:
            return
        try:
            self.container_client.delete_blob(filename)
        except Exception:
            pass

    def download(self, filename: str) -> bytes:
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=settings.azure_storage_container_name,
                blob=filename
            )
            return blob_client.download_blob().readall()
        except Exception as e:
            raise FileNotFoundError(f"Image {filename} not found in Azure") from e


def get_storage_service() -> StorageService:
    if settings.storage_type == "azure":
        return AzureStorage()
    return LocalStorage()


def process_profile_image_bytes(content: bytes) -> tuple[bytes, str]:
    with Image.open(BytesIO(content)) as original:
        img = ImageOps.exif_transpose(original)
        img = ImageOps.fit(img, (300, 300), method=Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        filename = f"{uuid.uuid4().hex}.jpg"
        output = BytesIO()
        img.save(output, "JPEG", quality=85, optimize=True)
        return output.getvalue(), filename


def process_profile_image(content: bytes) -> str:
    image_bytes, filename = process_profile_image_bytes(content)
    storage = get_storage_service()
    storage.upload(filename, image_bytes)
    return filename


def delete_profile_image(filename: str | None) -> None:
    if filename is None:
        return
    storage = get_storage_service()
    storage.delete(filename)
