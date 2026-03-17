import cloudinary.uploader
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
import os


@deconstructible
class CloudinaryStorage(Storage):

    def _save(self, name, content):
        # Subir a Cloudinary
        result = cloudinary.uploader.upload(
            content,
            public_id=os.path.splitext(name)[0],
            overwrite=True,
            resource_type='auto'
        )
        return result['public_id']

    def url(self, name):
        if not name:
            return ''
        # Si ya es una URL completa de Cloudinary, devolverla
        if name.startswith('http'):
            return name
        # Generar URL desde el public_id
        return cloudinary.CloudinaryImage(name).build_url()

    def exists(self, name):
        return False  # Siempre permitir subir

    def delete(self, name):
        try:
            cloudinary.uploader.destroy(name, resource_type='auto')
        except Exception:
            pass

    def _open(self, name, mode='rb'):
        raise NotImplementedError("No se puede abrir archivos de Cloudinary directamente")

    def size(self, name):
        return 0