#!/bin/bash

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Starting Streamlit app..."
streamlit run app.py

echo ""
echo "Streamlit app has stopped." 