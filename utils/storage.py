# utils/storage.py
import os
from cloudinary_storage.storage import MediaCloudinaryStorage
import cloudinary.uploader

class MediaOrVideoCloudinaryStorage(MediaCloudinaryStorage):
    VIDEO_EXTENSIONS = ['.mp4', '.webm', '.flv', '.mov', '.ogv', '.avi', '.wmv']

    def _get_extension(self, name):
        ext = os.path.splitext(name)[-1].lower() if name else ''
        return ext

    def _save(self, name, content):
        ext = self._get_extension(name)
        if ext in self.VIDEO_EXTENSIONS:
            # Subir video directamente con cloudinary como raw
            response = cloudinary.uploader.upload(
                content,
                resource_type='video',
                public_id=os.path.splitext(name)[0],
                overwrite=True,
            )
            return response['public_id'] + ext
        return super()._save(name, content)

    def url(self, name):
        if not name:
            return ''
        ext = self._get_extension(name)
        if ext in self.VIDEO_EXTENSIONS:
            import cloudinary
            return cloudinary.CloudinaryVideo(name).build_url()
        return super().url(name)