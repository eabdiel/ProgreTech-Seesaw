import io
import zipfile
from dataclasses import replace
from threading import Event

import pytest
from PIL import Image

from seesaw.issues import Island, parse_islands, repair_properties, verify_repair
from seesaw.preview import LayerPreview


def test_native_findings_reject_unknown_duplicate_and_out_of_bounds():
    line = "Island, 0, 1px², {X=10,Y=20,Width=1,Height=1}\n"
    assert parse_islands("Issues: 1\n" + line, 1) == [Island(0, 1, 10, 20, 1, 1)]
    for report in (
        "",
        "Issues: 0\n" + line,
        "Issues: 2\n" + line * 2,
        "Issues: 1\n" + line.replace("X=10", "X=9024"),
        "Issues: 1\nUnknown finding\n",
    ):
        with pytest.raises(ValueError):
            parse_islands(report, 1)


def archive(path, points):
    picture = Image.new("L", (9024, 5120))
    for point in points:
        picture.putpixel(point, 255)
    stream = io.BytesIO()
    picture.save(stream, format="PNG")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("model00000.png", stream.getvalue())


def test_repair_allows_only_reported_removal_and_focus_is_bounded(tmp_path):
    before, after = tmp_path / "before.sl1", tmp_path / "after.sl1"
    archive(before, [(10, 20), (30, 40)])
    archive(after, [(30, 40)])
    island = Island(0, 1, 10, 20, 1, 1)
    result = verify_repair(before, after, [island], 1, Event())
    assert result["removed_pixels"] == 1
    with Image.open(io.BytesIO(LayerPreview(before, 1, focus=island).thumbnail(0))) as im:
        assert im.width <= 900 and im.height <= 512 and im.mode == "RGB"
    with pytest.raises(ValueError, match="unauthorized"):
        verify_repair(before, after, [replace(island, x=11)], 1, Event())
    with pytest.raises(ValueError, match="exactly"):
        verify_repair(before, before, [island], 1, Event())
    cancel = Event()
    cancel.set()
    with pytest.raises(ValueError, match="cancelled"):
        verify_repair(before, after, [island], 1, cancel)


def test_native_repair_disables_broad_mutations():
    properties = repair_properties()
    assert properties["RepairResinTraps"] == properties["RemoveEmptyLayers"] == "false"
    assert properties["GapClosingIterations"] == properties["AttachIslandsBelowLayers"] == "0"
    assert properties["RemoveIslandsBelowEqualPixelCount"] == "1"
    assert properties["RemoveIslandsRecursiveIterations"] == "1"
