@echo off
REM Batch файл для запуска Windows SIEM агента
REM Требует права администратора

echo === Windows SIEM Agent ===
echo.

REM Проверяем права администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ОШИБКА: Этот скрипт требует права администратора!
    echo Запустите командную строку от имени администратора и попробуйте снова.
    echo.
    pause
    exit /b 1
)

REM Запускаем PowerShell скрипт
powershell -ExecutionPolicy Bypass -File "%~dp0run_windows_agent.ps1" %*

pause
