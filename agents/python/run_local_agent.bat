@echo off
echo Setting environment variables...
set API_KEY=cd3f4dcc53ea3cf6f31cf4b4e2907c84b499c0d54b2084c50575c00f8db24f58
set SERVER_URL=http://localhost:8000

echo API_KEY: %API_KEY:~0,8%...
echo SERVER_URL: %SERVER_URL%
echo Starting agent...

python agent.py
pause
