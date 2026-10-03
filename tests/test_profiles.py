from dataclasses import replace

import pytest

from seesaw.material_store import builtins, read_material, save_material, settings_for
from seesaw.profiles import MaterialProfile, materials_for_printer, printer_by_id


def resin(parameters=None):
    return MaterialProfile("test-resin", "Test resin", "resin", "mono4", parameters or {})


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), 0, -1])
def test_invalid_build_dimensions(value):
    with pytest.raises(ValueError):
        replace(printer_by_id("mono4"), build_mm=(value, 20, 30))


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), "2"])
def test_invalid_parameter_types(value):
    with pytest.raises(ValueError):
        resin({"exposure_s": value})


def test_association_and_schema_are_strict():
    with pytest.raises(ValueError):
        replace(resin(), printer_id="mk3s")
    with pytest.raises(ValueError):
        replace(resin(), printer_id="unknown")
    with pytest.raises(ValueError):
        replace(resin(), revision=True)
    with pytest.raises(ValueError):
        resin({"post_process": 1})
    data = resin().to_dict()
    data["unexpected"] = 1
    with pytest.raises(ValueError):
        MaterialProfile.from_dict(data)


def test_defensive_copy_and_frozen_parameters():
    values = {"exposure_s": 2.5, "bottom_exposure_s": 25}
    profile = resin(values)
    values["exposure_s"] = 90
    assert profile.parameters["exposure_s"] == 2.5
    with pytest.raises(TypeError):
        profile.parameters["exposure_s"] = 90
    data = profile.to_dict()
    restored = MaterialProfile.from_dict(data)
    data["parameters"]["exposure_s"] = 90
    assert restored.parameters["exposure_s"] == 2.5
    assert settings_for(restored).exposure_s == 2.5


def test_technology_filter_and_uncalibrated_resin():
    profiles = builtins()
    assert all(p.technology == "resin" for p in materials_for_printer(profiles, "mono4"))
    assert all(p.technology == "fdm" for p in materials_for_printer(profiles, "mk3s"))
    assert settings_for(profiles[0]) is None
    assert settings_for(profiles[-1]).nozzle_c == 210


def test_atomic_material_roundtrip_and_bad_ranges(tmp_path):
    path = tmp_path / "resin.json"
    profile = resin({"exposure_s": 2.5, "bottom_exposure_s": 25, "rest_s": 0})
    save_material(profile, path)
    assert read_material(path).to_dict() == profile.to_dict()
    old = path.read_bytes()
    with pytest.raises(ValueError):
        save_material(resin({"exposure_s": -1, "bottom_exposure_s": 25}), path)
    assert path.read_bytes() == old
    path.write_text('{"schema":"x","schema":"y"}')
    with pytest.raises(ValueError, match="Duplicate"):
        read_material(path)
