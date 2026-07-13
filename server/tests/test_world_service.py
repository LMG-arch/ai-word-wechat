"""世界/地图服务单元测试（纯逻辑，无 IO）"""
import pytest
from models import Character
from services.world_service import (
    world_hour_of_day,
    plan_location_name_for_world_hour,
    compute_character_map_xy,
    _clamp_map_xy,
    normalize_world_map_payload,
)


class TestWorldTime:
    def test_hour_zero(self):
        assert world_hour_of_day(0) == 0.0

    def test_hour_wraps(self):
        # 24 小时为一个完整周期
        ms = 24 * 3600 * 1000
        assert world_hour_of_day(ms) == pytest.approx(0.0)

    def test_hour_midday(self):
        ms = 12 * 3600 * 1000
        assert world_hour_of_day(ms) == pytest.approx(12.0)


class TestPlanLocation:
    def test_daytime_office(self):
        assert plan_location_name_for_world_hour(10) == "办公室"

    def test_night_home(self):
        assert plan_location_name_for_world_hour(2) == "家中"
        assert plan_location_name_for_world_hour(23) == "家中"

    def test_edge_boundary(self):
        # [9,12) 为办公室
        assert plan_location_name_for_world_hour(9) == "办公室"


class TestMapXY:
    def test_clamp(self):
        assert _clamp_map_xy(200, -50) == (92.0, 8.0)
        assert _clamp_map_xy(50, 50) == (50.0, 50.0)

    def test_compute_in_bounds(self):
        c = Character(id="x", name="c", age=30, gender="男", occupation="工程师", personality="")
        x, y = compute_character_map_xy(c, 12 * 3600 * 1000, 0)
        assert 2.0 <= x <= 98.0
        assert 2.0 <= y <= 98.0


class TestNormalizeWorldMap:
    def test_empty(self):
        out = normalize_world_map_payload({})
        assert out["city_name"]
        assert isinstance(out["landmarks"], list) and len(out["landmarks"]) >= 1

    def test_keeps_valid_landmarks(self):
        payload = {
            "city_name": "测试城",
            "lore": "x",
            "landmarks": [{"name": "塔", "x": 30, "y": 40, "bind": "办公室"}],
        }
        out = normalize_world_map_payload(payload)
        assert out["city_name"] == "测试城"
        assert "塔" in [lm["name"] for lm in out["landmarks"]]
