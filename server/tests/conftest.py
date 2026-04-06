"""pytest 配置 - 修复 Windows stdout wrapper 冲突"""
import sys
import os
import io

# 在 pytest 启动时恢复原始 stdout
# 这必须在导入 main.py/config.py 之前执行
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# 确保 PYTEST_CURRENT_TEST 环境变量存在（pytest 通常已设置）
if not os.environ.get("PYTEST_CURRENT_TEST"):
    os.environ["PYTEST_CURRENT_TEST"] = "pytest_setup"

# 尝试恢复原始 stdout（如果被包装了）
if hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = sys.stdout.buffer
    except (AttributeError, ValueError):
        sys.stdout = _original_stdout

if hasattr(sys.stderr, 'buffer'):
    try:
        sys.stderr = sys.stderr.buffer
    except (AttributeError, ValueError):
        sys.stderr = _original_stderr
