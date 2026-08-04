@echo off
chcp 65001 >nul
echo ========================================
echo UI自动化测试链路文档生成器
echo ========================================
echo.

REM 切换到项目根目录
cd /d %~dp0\..\..

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import docx" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装 python-docx...
    python -m pip install python-docx
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo.
)

python -c "import yaml" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装 PyYAML...
    python -m pip install PyYAML
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo.
)

echo 请选择操作：
echo 1. 生成登录链路文档（示例）
echo 2. 从自定义配置文件生成
echo 3. 批量生成所有配置
echo 4. 查看配置模板
echo 5. 退出
echo.
set /p choice=请输入选项 (1-5): 

if "%choice%"=="1" goto example
if "%choice%"=="2" goto custom
if "%choice%"=="3" goto batch
if "%choice%"=="4" goto template
if "%choice%"=="5" goto end
goto menu

:example
echo.
echo [生成] 使用登录链路示例配置生成文档...
echo.
python -m ui_automation.tools.doc_generator.cli -c ui_automation/tools/doc_generator/configs/login_chain.yaml
if errorlevel 1 (
    echo.
    echo [错误] 文档生成失败
) else (
    echo.
    echo [成功] 文档已生成到 output 目录
)
pause
goto end

:custom
echo.
set /p configfile=请输入配置文件路径（相对或绝对路径）: 
if "%configfile%"=="" (
    echo [错误] 未输入配置文件路径
    pause
    goto end
)

set /p headless=是否使用无头模式？(y/n，默认为n): 
if /i "%headless%"=="y" (
    python -m ui_automation.tools.doc_generator.cli -c "%configfile%" --headless
) else (
    python -m ui_automation.tools.doc_generator.cli -c "%configfile%"
)
pause
goto end

:batch
echo.
echo [批量生成] 正在处理 configs 目录下的所有YAML配置文件...
echo.
python -m ui_automation.tools.doc_generator.cli --batch ui_automation/tools/doc_generator/configs/*.yaml
pause
goto end

:template
echo.
echo [查看] 配置模板内容：
echo ========================================
type ui_automation\tools\doc_generator\configs\_template.yaml
echo ========================================
pause
goto end

:end
echo.
echo 感谢使用！
