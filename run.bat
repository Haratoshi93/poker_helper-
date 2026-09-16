@echo off
chcp 65001 > nul
echo Starting Streamlit App...
call venv\Scripts\activate.bat
streamlit run app.py
pause
