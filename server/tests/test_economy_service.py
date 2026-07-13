"""经济服务单元测试（纯逻辑，无 IO）"""
from models import Character
from services.economy_service import economic_stress_multiplier


def _char(money: float = 100.0, **kw) -> Character:
    return Character(
        name="测试", age=30, gender="男", occupation="工程师",
        personality="", money=money, **kw,
    )


class TestEconomicStressMultiplier:
    """经济压力乘数：越缺钱越高，驱动任务接取概率。"""

    def test_broke(self):
        assert economic_stress_multiplier(_char(money=0)) == 3.0
        assert economic_stress_multiplier(_char(money=-5)) == 3.0

    def test_low(self):
        assert economic_stress_multiplier(_char(money=30)) == 2.0

    def test_mid(self):
        assert economic_stress_multiplier(_char(money=80)) == 1.5

    def test_normal(self):
        assert economic_stress_multiplier(_char(money=200)) == 1.0

    def test_monotonic(self):
        # 金额越高，乘数不增（压力递减）
        assert economic_stress_multiplier(_char(money=10)) >= economic_stress_multiplier(_char(money=80))
        assert economic_stress_multiplier(_char(money=80)) >= economic_stress_multiplier(_char(money=300))
