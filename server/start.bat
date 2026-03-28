@echo off
chcp 65001 >nul
echo ========================================
echo    AI 社交世界 - 后端服务
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] Python 已安装

REM 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo [信息] 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo [信息] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [信息] 检查并安装依赖...
pip install -r requirements.txt -q

echo.
echo ========================================
echo    启动服务器
echo ========================================
echo.
echo 访问地址：http://localhost:8080
echo 手机访问：http://你的 IP:8080
echo.
echo 按 Ctrl+C 停止服务器
echo.

REM 启动服务器
python main.py

pause
