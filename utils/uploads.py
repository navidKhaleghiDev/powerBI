from pathlib import Path
from uuid import uuid4


def database_image_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"databases/{instance._meta.model_name}/{uuid4().hex}{extension}"
