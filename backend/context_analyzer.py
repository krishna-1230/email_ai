import google.generativeai as genai
from typing import Dict, Any, List
import os
import logging
from dotenv import load_dotenv
from config.prompts import (
    THREAD_ANALYSIS_PROMPT,
    SENTIMENT_ANALYSIS_PROMPT,
    URGENCY_ANALYSIS_PROMPT
)

load_dotenv()
logging.basicConfig(level=logging.INFO)

class ContextAnalyzer:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

    def analyze_thread(self, thread: Dict[str, Any]) -> Dict[str, Any]:
        try:
            thread_content = self._format_thread_content(thread)
            thread_analysis = self._analyze_thread_content(thread_content)
            sentiment = self._analyze_sentiment(thread_content)
            urgency = self._analyze_urgency(thread_content)
            return {
                'thread_analysis': thread_analysis,
                'sentiment': sentiment,
                'urgency': urgency,
                'key_points': self._extract_key_points(thread_analysis)
            }
        except Exception as e:
            logging.error(f"Error analyzing thread: {e}")
            return {
                'thread_analysis': "Unable to analyze thread content.",
                'sentiment': {'sentiment': 'neutral', 'tone': 'unknown'},
                'urgency': 'medium',
                'key_points': ["Please review the email thread manually."]
            }

    def _format_thread_content(self, thread: Dict[str, Any]) -> str:
        """Format thread content for analysis."""
        formatted_content = []
        
        for message in thread['messages']:
            formatted_content.append(
                f"From: {message['sender']}\n"
                f"Date: {message['date']}\n"
                f"Subject: {message['subject']}\n"
                f"Body: {message['body']}\n"
                f"{'='*50}\n"
            )
        
        return "\n".join(formatted_content)
    
    def _analyze_thread_content(self, thread_content: str) -> str:
        try:
            response = self.model.generate_content(
                THREAD_ANALYSIS_PROMPT.format(thread_content=thread_content)
            )
            return response.text
        except Exception as e:
            logging.error(f"Error analyzing thread content with Gemini: {e}")
            return "Unable to analyze thread content."
    
    def _analyze_sentiment(self, text: str) -> Dict[str, str]:
        try:
            response = self.model.generate_content(
                SENTIMENT_ANALYSIS_PROMPT.format(text=text)
            )
            return self._parse_sentiment_response(response.text)
        except Exception as e:
            logging.error(f"Error analyzing sentiment with Gemini: {e}")
            return {"sentiment": "neutral", "tone": "unknown"}
    
    def _analyze_urgency(self, text: str) -> str:
        try:
            response = self.model.generate_content(
                URGENCY_ANALYSIS_PROMPT.format(text=text)
            )
            return self._parse_urgency_response(response.text)
        except Exception as e:
            logging.error(f"Error analyzing urgency with Gemini: {e}")
            return "medium"
    
    def _parse_sentiment_response(self, response: str) -> Dict[str, str]:
        """Parse sentiment analysis response."""
        # Basic parsing - can be enhanced based on actual response format
        sentiment = "neutral"
        tone = "unknown"
        
        if "positive" in response.lower():
            sentiment = "positive"
        elif "negative" in response.lower():
            sentiment = "negative"
        
        # Extract tone
        tone_keywords = ["formal", "casual", "urgent", "friendly", "professional"]
        for keyword in tone_keywords:
            if keyword in response.lower():
                tone = keyword
                break
        
        return {"sentiment": sentiment, "tone": tone}
    
    def _parse_urgency_response(self, response: str) -> str:
        """Parse urgency analysis response."""
        response_lower = response.lower()
        
        if "high" in response_lower:
            return "high"
        elif "medium" in response_lower:
            return "medium"
        else:
            return "low"
    
    def _extract_key_points(self, analysis: str) -> List[str]:
        """Extract key points from thread analysis."""
        # Basic extraction - can be enhanced based on actual analysis format
        points = []
        lines = analysis.split('\n')
        
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('*'):
                points.append(line.strip()[1:].strip())
        
        if not points:
            # Try to find numbered points
            for line in lines:
                if line.strip() and any(line.strip().startswith(f"{i}.") for i in range(1, 10)):
                    points.append(line.strip()[2:].strip())
        
        return points 