"""Explicit resin motion and layer settings; no unverified material presets."""

from dataclasses import replace

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)


def edit_settings(parent, settings):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Layer and motion settings")
    layout = QVBoxLayout(dialog)
    note = QLabel(
        "Values are not calibrated for your resin. Speeds below are millimetres per minute."
    )
    note.setWordWrap(True)
    layout.addWidget(note)
    form = QFormLayout()
    controls = {}
    for key, label, low, high, decimals in (
        ("layer_mm", "Layer height (mm)", 0.01, 0.2, 3),
        ("bottom_layers", "Bottom layers", 1, 20, 0),
        ("lift_mm", "Lift distance (mm)", 1, 20, 2),
        ("lift_mm_min", "Lift speed (mm/min)", 1, 300, 1),
        ("retract_mm_min", "Retract speed (mm/min)", 1, 300, 1),
        ("rest_s", "Rest before exposure (s)", 0, 120, 2),
    ):
        control = QSpinBox() if decimals == 0 else QDoubleSpinBox()
        if decimals:
            control.setDecimals(decimals)
        control.setRange(low, high)
        control.setValue(getattr(settings, key))
        form.addRow(label, control)
        controls[key] = control
    layout.addLayout(form)
    layout.addWidget(
        QLabel(
            "Antialiasing follows the saved project; default is off.\n"
            "Maximum 512 layers in this first desktop adapter."
        )
    )
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    result = replace(settings, **{key: control.value() for key, control in controls.items()})
    result.validate()
    return result
