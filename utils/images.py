from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def create_thumbnail(image_file):
    """Return a PNG thumbnail fitting within 256 x 256 without upscaling."""
    image_file.seek(0)
    with Image.open(image_file) as source:
        image = ImageOps.exif_transpose(source)
        image.thumbnail((256, 256), Image.Resampling.LANCZOS)
        image = image.convert("RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB")
        output = BytesIO()
        image.save(output, format="PNG")
    return ContentFile(output.getvalue(), name=f"{Path(image_file.name).stem}.png")
