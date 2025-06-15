import os
import google.generativeai as genai

# Get the Gemini API key from environment variable
gemini_api_key = os.getenv('GEMINI_API_KEY')

if not gemini_api_key:
    print("Error: GEMINI_API_KEY environment variable not set.")
    exit(1)

try:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    prompt = "Say hello from Gemini!"
    response = model.generate_content(prompt)
    print("Gemini API call successful! Response:")
    print(response.text)
except Exception as e:
    print("Error communicating with Gemini API:")
    print(e) 