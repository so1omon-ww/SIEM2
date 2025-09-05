# PowerShell script for running local agent with API key
$env:API_KEY = "690023318602ee078fb6d5cbe2a17f8bd5d99a8e4899d8765c5ad23828938beb"
$env:SERVER_URL = "http://localhost:8000"

Write-Host "API_KEY set: $($env:API_KEY.Substring(0,8))..." -ForegroundColor Green
Write-Host "SERVER_URL: $env:SERVER_URL" -ForegroundColor Green
Write-Host "Starting agent..." -ForegroundColor Yellow

python agent.py
