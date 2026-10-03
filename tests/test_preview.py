import io
import zipfile

import pytest
from PIL import Image

from seesaw.model import MONO4
from seesaw.preview import LayerPreview


def archive(path, size=MONO4.resolution_px):
    data = io.BytesIO()
    picture = Image.new("L", size)
    picture.paste(255, (0, 0, size[0] // 2, size[1] // 2))
    picture.save(data, format="PNG")
    with zipfile.ZipFile(path, "w") as source:
        source.writestr("layer00000.png", data.getvalue())


def test_thumbnail_bounded_orientation_and_index(tmp_path):
    source = tmp_path / "readback.sl1"
    archive(source)
    preview = LayerPreview(source, 1)
    with Image.open(io.BytesIO(preview.thumbnail(0))) as picture:
        assert picture.width <= 900 and picture.height <= 512
        assert picture.getpixel((1, 1)) == 255
        assert picture.getpixel((picture.width - 2, picture.height - 2)) == 0
    for invalid in (-1, 1, True, "0"):
        with pytest.raises(ValueError):
            preview.thumbnail(invalid)


def test_wrong_count_and_raster_rejected(tmp_path):
    source = tmp_path / "readback.sl1"
    archive(source, (10, 10))
    with pytest.raises(ValueError, match="count"):
        LayerPreview(source, 2)
    with pytest.raises(ValueError, match="raster"):
        LayerPreview(source, 1).thumbnail(0)
