import os
import logging
from typing import Dict, Any, List

import google.generativeai as genai
from dotenv import load_dotenv
from pinecone import Pinecone

from config.prompts import REPLY_GENERATION_PROMPT, SENTIMENT_ANALYSIS_PROMPT

load_dotenv()
logging.basicConfig(level=logging.INFO)

class ReplyGenerator:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        # Initialize Pinecone
        try:
            self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            self.index = self.pc.Index(os.getenv("PINECONE_INDEX"))
            self.use_pinecone = True
        except Exception as e:
            logging.error(f"Error initializing Pinecone: {e}")
            self.pc = None
            self.index = None
            self.use_pinecone = False
            logging.info("Pinecone vector storage will not be available")

    def generate_replies(self, thread_analysis: Dict[str, Any]) -> Dict[str, str]:
        try:
            formatted_analysis = self._format_thread_analysis(thread_analysis)
            response = self.model.generate_content(
                REPLY_GENERATION_PROMPT.format(thread_analysis=formatted_analysis)
            )
            raw_text = response.text.strip() if response and hasattr(response, "text") else ""
            if not raw_text:
                raise ValueError("Empty response from Gemini.")
            replies = self._parse_replies(raw_text)
            if self.use_pinecone:
                self._store_replies(replies, thread_analysis)
            return replies
        except Exception as e:
            logging.error(f"Error generating replies: {e}")
            return {
                'formal': "I apologize, but I couldn't generate a reply at this time.",
                'casual': "Sorry, I'm having trouble generating a response right now.",
                'direct': "Unable to generate reply."
            }

    def _format_thread_analysis(self, analysis: Dict[str, Any]) -> str:
        return (
            f"Thread Analysis:\n{analysis['thread_analysis']}\n\n"
            f"Sentiment: {analysis['sentiment']['sentiment']}\n"
            f"Tone: {analysis['sentiment'].get('tone', 'unknown')}\n"
            f"Urgency: {analysis['urgency']}\n\n"
            f"Key Points:\n" + "\n".join(f"- {point}" for point in analysis['key_points'])
        )

    def _parse_replies(self, response: str) -> Dict[str, str]:
        replies = {'formal': '', 'casual': '', 'direct': ''}
        current_tone = None
        current_reply = []

        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith('formal'):
                if current_tone and current_reply:
                    replies[current_tone] = '\n'.join(current_reply)
                current_tone = 'formal'
                current_reply = []
            elif line.lower().startswith('casual'):
                if current_tone and current_reply:
                    replies[current_tone] = '\n'.join(current_reply)
                current_tone = 'casual'
                current_reply = []
            elif line.lower().startswith('direct'):
                if current_tone and current_reply:
                    replies[current_tone] = '\n'.join(current_reply)
                current_tone = 'direct'
                current_reply = []
            elif current_tone:
                current_reply.append(line)

        if current_tone and current_reply:
            replies[current_tone] = '\n'.join(current_reply)

        # Check if any replies are empty and provide defaults
        for tone in replies:
            if not replies[tone].strip():
                replies[tone] = f"I apologize, but I couldn't generate a {tone} reply at this time."

        return replies

    def _store_replies(self, replies: Dict[str, str], thread_analysis: Dict[str, Any]):
        try:
            if not self.use_pinecone or not self.index:
                logging.warning("Pinecone index not initialized, skipping reply storage")
                return
                
            for tone, reply in replies.items():
                if not reply.strip():
                    logging.warning(f"Skipping Pinecone upsert for tone '{tone}': empty reply.")
                    continue

                self.index.upsert([
                    {
                        'id': f"{tone}_{hash(reply)}",
                        'values': {"text": reply},  # Let Pinecone embed it
                        'metadata': {
                            'tone': tone,
                            'reply': reply,
                            'sentiment': thread_analysis['sentiment']['sentiment'],
                            'urgency': thread_analysis['urgency']
                        }
                    }
                ])
        except Exception as e:
            logging.error(f"Error storing replies in Pinecone: {e}")

    def get_similar_replies(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        try:
            if not self.use_pinecone or not self.index:
                logging.warning("Pinecone index not initialized, skipping similarity search")
                return []
                
            if not query.strip():
                logging.warning("Skipping similarity search: query is empty.")
                return []

            results = self.index.query(
                vector={"text": query},  # Let Pinecone embed it
                top_k=k,
                include_metadata=True
            )

            return [
                {
                    'tone': match.metadata['tone'],
                    'reply': match.metadata['reply'],
                    'score': match.score
                }
                for match in results.matches
            ]
        except Exception as e:
            logging.error(f"Error retrieving similar replies: {e}")
            return []

    def generate_reply(self, email_thread: List[Dict[str, Any]], tone: str = "formal") -> str:
        """Generate a reply for an email thread with specified tone."""
        try:
            thread_content = "\n\n".join([
                f"From: {email['sender']}\nSubject: {email['subject']}\n\n{email['body']}"
                for email in email_thread
            ])
            prompt = f"""
            Please generate a {tone} reply to the following email thread:
            {thread_content}
            Reply ({tone} tone):
            """
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logging.error(f"Error generating reply: {e}")
            return f"I apologize, but I couldn't generate a {tone} reply at this time."

    def analyze_sentiment(self, email_thread: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment of an email thread."""
        try:
            thread_content = "\n\n".join([
                f"From: {email['sender']}\nSubject: {email['subject']}\n\n{email['body']}"
                for email in email_thread
            ])
            response = self.model.generate_content(
                SENTIMENT_ANALYSIS_PROMPT.format(text=thread_content)
            )
            sentiment = "neutral"
            tone = "unknown"
            response_text = response.text.lower()
            if "positive" in response_text:
                sentiment = "positive"
            elif "negative" in response_text:
                sentiment = "negative"
            tone_keywords = ["formal", "casual", "urgent", "friendly", "professional"]
            for keyword in tone_keywords:
                if keyword in response_text:
                    tone = keyword
                    break
            return {
                "sentiment": sentiment,
                "tone": tone,
                "analysis": response.text
            }
        except Exception as e:
            logging.error(f"Error analyzing sentiment: {e}")
            return {
                "sentiment": "neutral",
                "tone": "unknown",
                "analysis": "Unable to analyze sentiment."
            }

    def get_similar_emails(self, email_content: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar emails in the vector database."""
        try:
            if not self.use_pinecone or not self.index:
                logging.warning("Pinecone index not initialized, skipping similarity search")
                return []
                
            if not email_content.strip():
                logging.warning("Skipping similarity search: email content is empty.")
                return []
            
            # Query Pinecone for similar emails
            results = self.index.query(
                vector={"text": email_content},
                top_k=limit,
                include_metadata=True
            )
            
            # Format results
            similar_emails = []
            for match in results.matches:
                similar_emails.append({
                    'reply': match.metadata.get('reply', ''),
                    'tone': match.metadata.get('tone', 'unknown'),
                    'sentiment': match.metadata.get('sentiment', 'neutral'),
                    'similarity_score': match.score
                })
            
            return similar_emails
        except Exception as e:
            logging.error(f"Error finding similar emails: {e}")
            return []
