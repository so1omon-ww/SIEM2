# PowerShell скрипт для запуска Windows SIEM агента
# Требует права администратора

param(
    [string]$ServerUrl = "http://localhost:8000",
    [string]$ApiKey = "",
    [string]$HostId = ""
)

# Проверяем права администратора
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ОШИБКА: Этот скрипт требует права администратора!" -ForegroundColor Red
    Write-Host "Запустите PowerShell от имени администратора и попробуйте снова." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Нажмите любую клавишу для выхода..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "=== Windows SIEM Agent ===" -ForegroundColor Green
Write-Host ""

# Проверяем наличие Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python найден: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ОШИБКА: Python не найден!" -ForegroundColor Red
    Write-Host "Установите Python 3.8+ и добавьте его в PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Нажмите любую клавишу для выхода..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Проверяем наличие pip
try {
    $pipVersion = pip --version 2>&1
    Write-Host "pip найден: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "ОШИБКА: pip не найден!" -ForegroundColor Red
    Write-Host "Установите pip для Python" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Нажмите любую клавишу для выхода..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Устанавливаем зависимости если нужно
Write-Host "Проверяем зависимости..." -ForegroundColor Yellow
$dependencies = @("psutil", "requests", "wmi")
$missingDeps = @()

foreach ($dep in $dependencies) {
    try {
        python -c "import $dep" 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missingDeps += $dep
        }
    } catch {
        $missingDeps += $dep
    }
}

if ($missingDeps.Count -gt 0) {
    Write-Host "Устанавливаем недостающие зависимости: $($missingDeps -join ', ')" -ForegroundColor Yellow
    foreach ($dep in $missingDeps) {
        Write-Host "Устанавливаем $dep..." -ForegroundColor Yellow
        pip install $dep
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ОШИБКА: Не удалось установить $dep" -ForegroundColor Red
            Write-Host ""
            Write-Host "Нажмите любую клавишу для выхода..."
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            exit 1
        }
    }
}

Write-Host "Все зависимости установлены!" -ForegroundColor Green
Write-Host ""

# Запрашиваем API ключ если не указан
if (-not $ApiKey) {
    Write-Host "API ключ не указан. Получите его из веб-интерфейса:" -ForegroundColor Yellow
    Write-Host "1. Откройте http://localhost:3000/register" -ForegroundColor Cyan
    Write-Host "2. Зарегистрируйтесь или войдите" -ForegroundColor Cyan
    Write-Host "3. Скопируйте API ключ" -ForegroundColor Cyan
    Write-Host ""
    $ApiKey = Read-Host "Введите API ключ"
    
    if (-not $ApiKey) {
        Write-Host "ОШИБКА: API ключ не может быть пустым!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Нажмите любую клавишу для выхода..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

# Устанавливаем переменные окружения
$env:SERVER_URL = $ServerUrl
$env:API_KEY = $ApiKey
if ($HostId) {
    $env:HOST_ID = $HostId
}

Write-Host "Конфигурация:" -ForegroundColor Green
Write-Host "  Сервер: $ServerUrl" -ForegroundColor Cyan
Write-Host "  API ключ: $($ApiKey.Substring(0, 8))..." -ForegroundColor Cyan
Write-Host "  Хост: $($env:HOST_ID)" -ForegroundColor Cyan
Write-Host ""

# Получаем путь к скрипту агента
$scriptPath = Join-Path $PSScriptRoot "windows_agent.py"

if (-not (Test-Path $scriptPath)) {
    Write-Host "ОШИБКА: Файл агента не найден: $scriptPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Нажмите любую клавишу для выхода..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "Запускаем Windows SIEM агент..." -ForegroundColor Green
Write-Host "Нажмите Ctrl+C для остановки" -ForegroundColor Yellow
Write-Host ""

# Запускаем агент
try {
    python $scriptPath
} catch {
    Write-Host "ОШИБКА при запуске агента: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "Агент остановлен." -ForegroundColor Yellow
    Write-Host "Нажмите любую клавишу для выхода..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
