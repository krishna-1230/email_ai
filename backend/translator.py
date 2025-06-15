import google.generativeai as genai
from typing import Dict, Any, List
import os
import logging
from dotenv import load_dotenv
from langdetect import detect
import re

load_dotenv()
logging.basicConfig(level=logging.INFO)

class EmailTranslator:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

    def detect_language(self, text: str) -> str:
        """Detect the language of the text."""
        try:
            return detect(text)
        except Exception as e:
            logging.error(f"Error detecting language: {e}")
            return "en"  # Default to English
    
    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to target language using Gemini."""
        try:
            # Get language name for the target language code
            language_name = next((lang['name'] for lang in self.get_supported_languages() 
                                 if lang['code'] == target_language), target_language)
            
            prompt = f"""Translate the following text to {language_name}. 
            Maintain the original tone and formatting.
            
            Text:
            {text}
            
            Translation:"""
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error translating text: {e}")
            return text
    
    def translate_email(self, email: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Translate an entire email to target language."""
        try:
            # Detect original language
            original_language = self.detect_language(email['body'])
            
            if original_language == target_language:
                return email
            
            # Translate subject and body
            translated_subject = self.translate_text(email['subject'], target_language)
            translated_body = self.translate_text(email['body'], target_language)
            
            return {
                **email,
                'subject': translated_subject,
                'body': translated_body,
                'original_language': original_language,
                'translated_language': target_language
            }
        except Exception as e:
            logging.error(f"Error translating email: {e}")
            return email
    
    def translate_thread(self, thread: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Translate an entire email thread to target language."""
        try:
            translated_messages = []
            
            for message in thread['messages']:
                translated_message = self.translate_email(message, target_language)
                translated_messages.append(translated_message)
            
            return {
                **thread,
                'messages': translated_messages
            }
        except Exception as e:
            logging.error(f"Error translating thread: {e}")
            return thread
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages."""
        return [
            {'code': 'en', 'name': 'English'},
            {'code': 'es', 'name': 'Spanish'},
            {'code': 'fr', 'name': 'French'},
            {'code': 'de', 'name': 'German'},
            {'code': 'it', 'name': 'Italian'},
            {'code': 'pt', 'name': 'Portuguese'},
            {'code': 'ru', 'name': 'Russian'},
            {'code': 'zh', 'name': 'Chinese'},
            {'code': 'ja', 'name': 'Japanese'},
            {'code': 'ko', 'name': 'Korean'},
            {'code': 'ar', 'name': 'Arabic'},
            {'code': 'hi', 'name': 'Hindi'}
        ]
    
    def format_translation(self, original: str, translated: str, 
                          original_lang: str, target_lang: str) -> str:
        """Format translation with original and translated text."""
        return f"""Original ({original_lang}):
{original}

Translation ({target_lang}):
{translated}""" 