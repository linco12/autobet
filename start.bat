@echo off
echo Starting AutoBet...

:: Backend
cd backend
pip install -r requirements.txt >nul 2>&1
start "AutoBet Backend" cmd /k "cd .. && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080"

:: Frontend
cd ..\frontend
call npm install >nul 2>&1
start "AutoBet Frontend" cmd /k "npm run dev"

echo.
echo Backend: http://localhost:8080
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8080/docs
echo.
pause
