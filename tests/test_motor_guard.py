"""Guards against the motor ever running the project pipeline on itself.

Regression test for the root cause of this repo's historical duplicate-commit /
duplicate-CHANGELOG spam: main.py used to happily run against its own
directory, writing generated-project artifacts into the motor's own repo.
"""

from pathlib import Path
import main


def test_motor_directory_itself_is_detected():
    assert main._is_motor_directory(main.MOTOR_DIR) is True


def test_subdirectory_of_motor_is_detected(tmp_path, monkeypatch):
    fake_motor = tmp_path / "ai-sd-os"
    fake_motor.mkdir()
    sub = fake_motor / "kernel"
    sub.mkdir()
    monkeypatch.setattr(main, "MOTOR_DIR", fake_motor.resolve())
    assert main._is_motor_directory(sub) is True


def test_sibling_project_directory_is_not_detected(tmp_path, monkeypatch):
    fake_motor = tmp_path / "ai-sd-os"
    fake_motor.mkdir()
    sibling_project = tmp_path / "webarchivum"
    sibling_project.mkdir()
    monkeypatch.setattr(main, "MOTOR_DIR", fake_motor.resolve())
    assert main._is_motor_directory(sibling_project) is False
