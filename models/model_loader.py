import os
import requests
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self):
        """Initialize Ollama client with host and model from environment variables."""
        self.host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'llama2')
        self.api_base = f"{self.host}/api"
        
    def check_model_availability(self) -> bool:
        """Check if the specified model is available in Ollama."""
        try:
            response = requests.get(f"{self.api_base}/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                for model in models:
                    if model.get('name') == self.model:
                        return True
            return False
        except Exception as e:
            logging.error(f"Error checking model availability: {e}")
            return False
    
    def pull_model(self) -> bool:
        """Pull the model if not already available."""
        try:
            if self.check_model_availability():
                logging.info(f"Model {self.model} is already available.")
                return True
                
            logging.info(f"Pulling model {self.model}...")
            response = requests.post(
                f"{self.api_base}/pull",
                json={"name": self.model}
            )
            
            if response.status_code == 200:
                logging.info(f"Successfully pulled model {self.model}")
                return True
            else:
                logging.error(f"Failed to pull model: {response.text}")
                return False
        except Exception as e:
            logging.error(f"Error pulling model: {e}")
            return False
    
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> Optional[str]:
        """Generate text using Ollama model."""
        try:
            response = requests.post(
                f"{self.api_base}/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                logging.error(f"Error generating text: {response.text}")
                return None
        except Exception as e:
            logging.error(f"Error calling Ollama API: {e}")
            return None
    
    def analyze_email(self, email_content: str) -> Dict[str, Any]:
        """Analyze email content using Ollama model."""
        prompt = f"""
        Analyze the following email content and provide:
        1. A brief summary (2-3 sentences)
        2. The sentiment (positive, negative, or neutral)
        3. The urgency level (high, medium, or low)
        4. Key points that need addressing
        
        Email content:
        {email_content}
        
        Format your response as JSON:
        {{
            "summary": "...",
            "sentiment": "...",
            "urgency": "...",
            "key_points": ["...", "..."]
        }}
        """
        
        try:
            response = self.generate_text(prompt)
            if not response:
                return {
                    "summary": "Failed to analyze email.",
                    "sentiment": "neutral",
                    "urgency": "medium",
                    "key_points": []
                }
            
            # Extract JSON from response
            import json
            import re
            
            # Find JSON pattern in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    logging.error("Failed to parse JSON from response")
            
            # Fallback to basic extraction
            lines = response.strip().split('\n')
            result = {
                "summary": "",
                "sentiment": "neutral",
                "urgency": "medium",
                "key_points": []
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith("summary:") or line.startswith("Summary:"):
                    result["summary"] = line.split(":", 1)[1].strip()
                elif line.startswith("sentiment:") or line.startswith("Sentiment:"):
                    result["sentiment"] = line.split(":", 1)[1].strip().lower()
                elif line.startswith("urgency:") or line.startswith("Urgency:"):
                    result["urgency"] = line.split(":", 1)[1].strip().lower()
                elif line.startswith("-") or line.startswith("*"):
                    result["key_points"].append(line[1:].strip())
            
            return result
        except Exception as e:
            logging.error(f"Error analyzing email: {e}")
            return {
                "summary": "Error analyzing email.",
                "sentiment": "neutral",
                "urgency": "medium",
                "key_points": []
            }

# Singleton instance
ollama_client = OllamaClient() 