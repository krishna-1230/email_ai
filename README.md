# AI-Powered Contextual Email Assistant

An intelligent email assistant that helps you manage your inbox by analyzing email threads, generating contextual replies, scheduling meetings, and more.

## Features

- 📧 Smart email thread analysis
- 🤖 AI-powered reply generation in multiple tones
- 📅 Meeting scheduling and calendar management
- 🌐 Language translation
- 📊 Sentiment and urgency analysis
- 🔒 Secure credential management
- 🚀 Local LLM support with Llama 3.2
- 🗄️ Serverless vector storage with Pinecone

## Prerequisites

- Python 3.8 or higher
- Ollama with Llama 3.2 installed
- Gmail account
- Google Cloud Project with Gmail API enabled
- Gemini API key
- Pinecone serverless account with existing index

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd email_assist
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your credentials:
   - Copy `credentials.json.sample` to `credentials.json` and fill in your Google API credentials
   - Run the setup script to create your `.env` file: `python scripts/setup.py`

5. Launch the application:
```bash
streamlit run app.py
```

## Detailed Setup

### 1. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API and Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and "Google Calendar API"
   - Enable both APIs
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place it in the project root
5. Configure OAuth consent screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" user type
   - Fill in the required information (app name, user support email, developer contact)
   - Add the necessary scopes: `.../auth/gmail.readonly` and `.../auth/calendar`
   - Add your email as a test user

### 2. Gemini API Setup

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key for use in the setup script

### 3. Pinecone Setup

1. Create a [Pinecone account](https://www.pinecone.io/) if you don't have one
2. Create a new serverless index with the following configuration:
   - Index Name: emailai
   - Dimensions: 1024
   - Metric: cosine
   - Cloud Provider: AWS
   - Region: us-east-1
3. Copy your Pinecone API key from the dashboard

### 4. Ollama Setup

1. Install [Ollama](https://ollama.ai/) following the instructions for your platform
2. Pull the Llama 3.2 model:
```bash
ollama pull llama2
```
3. Verify the model is working:
```bash
ollama run llama2 "Hello, world!"
```

### 5. Environment Configuration

Run the setup script to create your `.env` file:
```bash
python scripts/setup.py
```

The script will prompt you for:
- Gmail API credentials
- Gemini API key
- Pinecone API key
- Ollama configuration

You can also create the `.env` file manually with the following variables:

```
# Gmail API Credentials
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret

# Gemini API
GEMINI_API_KEY=your_api_key

# Pinecone Vector Database
PINECONE_API_KEY=your_api_key
PINECONE_INDEX=emailai
PINECONE_HOST=https://emailai-xod54xm.svc.aped-4627-b74a.pinecone.io
PINECONE_DIMENSIONS=1024
PINECONE_METRIC=cosine
PINECONE_EMBEDDING_MODEL=llama-text-embed-v2
PINECONE_ENVIRONMENT=aws-us-east-1

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
DEFAULT_REPLY_TONE=formal
MAX_THREADS_TO_FETCH=10
MEETING_DURATION_MINUTES=30
DAYS_AHEAD_FOR_SCHEDULING=7
DEFAULT_TARGET_LANGUAGE=en
ENABLE_AUTO_TRANSLATION=False

# Security Settings
ENCRYPTION_KEY=your_encryption_key
SESSION_TIMEOUT_MINUTES=60
```

You can generate an encryption key using:
```bash
python scripts/generate_key.py
```

## Usage

1. Launch the application:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Authenticate with your Gmail account when prompted

4. Features available in the web interface:
   - View and select email threads
   - Generate AI-powered replies in different tones (formal, casual, direct)
   - Schedule meetings based on email content
   - Translate emails to different languages
   - Analyze email sentiment and urgency

## Security Considerations

- API keys and credentials are stored in the `.env` file (not committed to version control)
- The application uses encryption for sensitive data
- Session timeouts are implemented for security
- Ollama runs locally on your machine, keeping your data private
- Pinecone serverless provides secure vector storage

## Troubleshooting

### Gmail API Authentication Issues

- **Error**: "The client_secrets.json file is missing or invalid."
  - **Solution**: Ensure `credentials.json` is in the project root and has the correct format.

- **Error**: "Access Not Configured. Gmail API has not been used in project..."
  - **Solution**: Make sure you've enabled the Gmail API in the Google Cloud Console.

- **Error**: "Error 403: Access Denied"
  - **Solution**: Verify that your OAuth consent screen is configured correctly and your email is added as a test user.

### Pinecone Connection Issues

- **Error**: "API key is invalid"
  - **Solution**: Double-check your Pinecone API key in the `.env` file.

- **Error**: "Index not found"
  - **Solution**: Verify that you've created the index with the correct name and configuration.

- **Error**: "Dimension mismatch"
  - **Solution**: Ensure your index is configured with 1024 dimensions.

### Ollama Issues

- **Error**: "Failed to connect to Ollama server"
  - **Solution**: Make sure Ollama is running with `ollama serve`.

- **Error**: "Model not found"
  - **Solution**: Pull the model with `ollama pull llama2`.

- **Error**: "Connection refused"
  - **Solution**: Check if Ollama is accessible at http://localhost:11434.

### Gemini API Issues

- **Error**: "API key not valid"
  - **Solution**: Verify your Gemini API key in the `.env` file.

- **Error**: "Quota exceeded"
  - **Solution**: Check your usage in the Google AI Studio dashboard.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Cloud Platform
- Gemini API
- Pinecone
- Ollama
- Streamlit
- LangChain "# email_ai" 
