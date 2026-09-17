from pathlib import Path
import re

SOURCE = Path(__file__).resolve().parents[1] / "assets/pack_v1/source/player_rework_v2.py"


def read() -> str:
    return SOURCE.read_text()


def test_player_rework_v2_declares_eight_views_and_core_clips():
    text = read()
    assert "DIRS = ['e','se','s','sw','w','nw','n','ne']" in text
    assert "'ready':(4,6,True)" in text
    assert "'walk':(8,12,True)" in text
    assert "'fire':(4,18,False)" in text


def test_rifle_is_shoulder_mounted_with_explicit_sockets():
    text = read()
    match = re.search(r"BUTT = np\.array\(\[([0-9.]+),([0-9.]+),([0-9.]+)\]\)", text)
    assert match, "Shoulder-stock anchor missing"
    z = float(match.group(3))
    assert z >= 1.35, "Rifle stock is too low to read as shoulder-mounted"
    for socket in ["muzzle", "stock", "trigger_grip", "support_grip", "shoulder", "eye"]:
        assert f"'{socket}':" in text


def test_source_keeps_incomplete_actions_explicit():
    text = read()
    for item in ["hit", "death", "strafe", "reverse"]:
        assert item in text
    assert "owner_approval':None" in text


def test_source_does_not_import_locked_player_frames():
    text = read()
    forbidden = ["selected_baseline", "human_atlas.png", "human_e.png", "human_s.png", "human_w.png", "human_n.png"]
    for item in forbidden:
        assert item not in text
