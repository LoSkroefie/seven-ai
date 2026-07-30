from pathlib import Path

from PIL import Image

from seven.ui.avatar import SevenAvatar


def test_avatar_pose_sheet_is_packaged_and_transparent():
    path = SevenAvatar._sheet_path()
    assert path.is_file()
    image = Image.open(path).convert("RGBA")
    assert image.width >= 1200
    assert image.height >= 700
    alpha = image.getchannel("A")
    assert alpha.getextrema()[0] == 0
    assert alpha.getbbox() is not None
