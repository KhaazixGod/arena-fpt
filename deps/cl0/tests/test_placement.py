"""Tờ đặt vật: chữ, ảnh (chiều yaw!) và đọc CSV sắp xếp."""
import math

import numpy as np
import pytest

from cl0.arrangements import Arrangement, Item, read_arrangements
from cl0.placement import draw_placement, placement_text


def _arr(yaw):
    return Arrangement("1", "CL0", [Item(1, "bar18x60", 0.0, 50.0, yaw)])


def _red_pixels(img):
    r = (img[:, :, 2] > 150) & (img[:, :, 1] < 60) & (img[:, :, 0] < 60)
    ys, xs = np.nonzero(r)
    return xs, ys


@pytest.mark.parametrize("yaw", [30.0, 60.0, 90.0, 150.0])
def test_positive_yaw_points_toward_the_left_belt_edge(yaw):
    """Quy ước: yaw dương = ngược chiều kim đồng hồ nhìn từ trên xuống, belt chạy sang PHẢI, mép trái ở TRÊN => đầu vạch phải đi LÊN."""
    img = draw_placement(_arr(yaw), belt_width_mm=120.0, diam_mm={"bar18x60": 60.0}, px_per_mm=3.0)
    xs, ys = _red_pixels(img)
    assert len(xs) > 20
    # tâm vật ở x = 60 mm * 3 + 10 px, y = 20 + 50 * 3 px
    cx, cy = 10 + 60.0 * 3.0, 20 + 50.0 * 3.0
    # điểm xa tâm nhất của vạch đỏ cho hướng
    d = np.hypot(xs - cx, ys - cy)
    far = int(np.argmax(d))
    ang = math.degrees(math.atan2(-(ys[far] - cy), xs[far] - cx))                   # y ảnh hướng xuống => đổi dấu để có góc CCW
    diff = (ang - yaw + 180) % 360 - 180
    assert abs(diff) < 6.0, (yaw, ang)


def test_placement_text_mentions_conventions_and_all_items():
    arr = Arrangement("7", "CL0", [Item(1, "disc30", 0, 60, 0), Item(2, "box25x50", 140.0, 30.0, 45.0)])
    txt = placement_text(arr)
    assert "mép TRÁI" in txt and "ngược chiều kim đồng hồ" in txt
    assert "disc30" in txt and "box25x50" in txt and "140.0" in txt


def test_read_arrangements_parses_sorts_and_skips_comments(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("# chú thích\n"
                 "arrangement_id,first_method,idx,object,x_mm,y_mm,yaw_deg\n"
                 "1,CL0,2,disc22,150,80,0\n"
                 "1,CL0,1,disc30,0,60,10\n"
                 "\n"
                 "2,I2,1,box25x50,0,45,30\n", encoding="utf-8")
    arrs = read_arrangements(str(p))
    assert list(arrs) == ["1", "2"]
    assert [it.obj for it in arrs["1"].items] == ["disc30", "disc22"]
    assert arrs["1"].first_method == "CL0" and arrs["2"].first_method == "I2"
    assert arrs["1"].items[0].yaw_deg == 10.0 and arrs["2"].items[0].y_mm == 45.0
