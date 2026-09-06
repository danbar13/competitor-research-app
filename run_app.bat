@echo off
chcp 65001 >nul
title מנוע מחקר ומיצוב מתחרים - דנבר
cd /d "%~dp0"

echo ========================================================
echo   מפעיל את אפליקציית מחקר ומיצוב מתחרים בלינקדאין...
echo ========================================================
echo.
echo האפליקציה תיפתח בדפדפן בכתובת: http://localhost:8501
echo כדי לעצור את האפליקציה, סגור חלון זה.
echo.

python -m streamlit run streamlit_app.py --browser.gatherUsageStats false

pause
