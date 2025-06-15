SYSTEM_PROMPT = """You are an AI email assistant that helps users manage their emails effectively. 
Your role is to analyze email threads, understand context, and generate appropriate responses.
You should maintain professionalism while being helpful and concise."""

THREAD_ANALYSIS_PROMPT = """Analyze the following email thread and provide:
1. A brief summary of the conversation
2. The overall sentiment (positive/negative/neutral)
3. The urgency level (high/medium/low)
4. Key points that need to be addressed

Thread:
{thread_content}"""

REPLY_GENERATION_PROMPT = """Based on the following email thread analysis, generate three different reply suggestions.

Thread Analysis:
{thread_analysis}

Format your response exactly as below:

Formal:
<your formal reply here>

Casual:
<your casual reply here>

Direct:
<your direct reply here>
"""

SENTIMENT_ANALYSIS_PROMPT = """Analyze the sentiment of the following text and classify it as:
- Positive
- Negative
- Neutral

Also identify the emotional tone (e.g., formal, casual, urgent, etc.)

Text:
{text}"""

URGENCY_ANALYSIS_PROMPT = """Analyze the following text and determine its urgency level:
- High: Requires immediate attention
- Medium: Important but not time-critical
- Low: Can be addressed when convenient

Consider:
- Time-sensitive language
- Requested actions
- Consequences of delay

Text:
{text}""" 