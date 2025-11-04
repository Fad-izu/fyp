@echo off
cd backend
start cmd /k "call ..\.venv\Scripts\activate && python app.py"
timeout /t 5 >nul
cd ..
cd camera_client
start cmd /k "call ..\.venv\Scripts\activate && python detect_and_post_yolov8_mkgoud.py"
echo All systems started!
pause
