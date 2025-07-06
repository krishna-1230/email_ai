@echo off
echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Starting Streamlit app...
streamlit run app.py

echo.
echo Streamlit app has stopped.
pause
