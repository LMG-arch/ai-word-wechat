"""生命周期服务：导入与职责委托冒烟测试"""
import storage
import services.lifecycle_service as lifecycle


def test_module_imports_without_circular_dependency():
    # 若 services 间存在循环依赖，此处导入会失败
    assert hasattr(lifecycle, "process_age_growth")
    assert hasattr(lifecycle, "process_social_autorun")
    assert hasattr(lifecycle, "add_log")


def test_add_log_delegates_to_storage(monkeypatch):
    # 验证 lifecycle.add_log 统一委托 storage.add_log，未自行实现日志写入
    captured = {}

    def fake_add_log(name, action, desc):
        captured["hit"] = (name, action, desc)

    monkeypatch.setattr(storage, "add_log", fake_add_log)
    lifecycle.add_log("角色X", "test", "描述")
    assert captured["hit"] == ("角色X", "test", "描述")
