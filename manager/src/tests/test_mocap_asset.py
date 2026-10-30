import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOCAP = ROOT / "assets" / "mocap"


def test_mocap_asset_has_verified_license_and_source():
    license_text = " ".join((MOCAP / "LICENSE.txt").read_text(encoding="utf-8").split())
    assert "CMU Graphics Lab Motion Capture Database" in license_text
    assert "copied, modified, or redistributed without permission" in license_text
    assert "http://mocap.cs.cmu.edu/faqs.php" in license_text
    assert (MOCAP / "source" / "09.asf").exists()
    assert (MOCAP / "source" / "09_01.amc").exists()


def test_mocap_clip_has_frames_and_metadata():
    data = json.loads((MOCAP / "cmu_09_01_run.json").read_text(encoding="utf-8"))
    assert data["source"] == "CMU Graphics Lab Motion Capture Database"
    assert data["subject"] == 9
    assert data["trial"] == 1
    assert data["motion"] == "run"
    assert data["license"] == "free for all uses"
    assert data["playback_fps"] == 60
    assert len(data["frames"]) >= 60
    frame = data["frames"][0]
    assert {"lb", "lf", "lt", "rf", "rt", "lfoot", "rfoot"} <= set(frame)
    assert len(frame["lb"]) == 3
