# utils/storage.py
from cloudinary_storage.storage import MediaCloudinaryStorage, RawMediaCloudinaryStorage

class MediaOrVideoCloudinaryStorage(MediaCloudinaryStorage):
    """
    Usa MediaCloudinaryStorage para imágenes y RawMediaCloudinaryStorage para videos.
    """
    VIDEO_EXTENSIONS = ['.mp4', '.webm', '.flv', '.mov', '.ogv', '.avi', '.wmv']

    def _save(self, name, content):
        ext = '.' + name.split('.')[-1].lower() if '.' in name else ''
        if ext in self.VIDEO_EXTENSIONS:
            # Delegar al storage de archivos crudos para videos
            raw_storage = RawMediaCloudinaryStorage()
            return raw_storage._save(name, content)
        return super()._save(name, content)

    def url(self, name):
        ext = '.' + name.split('.')[-1].lower() if name and '.' in name else ''
        if ext in self.VIDEO_EXTENSIONS:
            raw_storage = RawMediaCloudinaryStorage()
            return raw_storage.url(name)
        return super().url(name)