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
- ✉️ Direct email sending via SMTP

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

# SMTP Email Settings (for simpler email sending)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
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

### Gmail Authorization Issues

If you encounter authorization issues:
1. Click "Reauthorize with Send Permission" button if shown
2. Ensure you've granted both read and send permissions to the application
3. Delete the token.pickle file to force reauthorization

### Email Sending Issues

If replies aren't appearing in the sender/recipient inboxes:
1. Check your Gmail spam folder
2. Verify that you've configured the correct SMTP settings in the .env file
3. For Gmail, make sure you're using an App Password if you have 2FA enabled
4. Look in your Sent folder to ensure the email was sent

#### Using SMTP Email Sending

For email sending using SMTP:
1. Set up your SMTP credentials in the `.env` file:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```
2. For Gmail, you'll need to create an App Password:
   - Go to your Google Account > Security > 2-Step Verification
   - At the bottom, click "App passwords"
   - Select "Mail" and "Other (Custom name)"
   - Enter "Email AI Assistant" and generate
   - Copy the 16-character password to your `.env` file

### API Limits and Quotas

- The Gemini API has rate limits that may affect reply generation
- Gmail API also has quotas to prevent abuse

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

## Email Sending Features

The application now provides two main ways to send emails:

### 1. AI-Generated Replies
After analyzing an email thread, you can send AI-generated replies in different tones:
1. Select an email thread from the dropdown
2. Click "Analyze Thread"
3. Review the suggested replies in the "Formal", "Casual", or "Direct" tabs
4. Click "Use [tone] Reply" to send the reply immediately to the original sender

### 2. Direct Email Sending
The "Send Reply" section in the sidebar allows you to send custom emails directly:
1. Enter the recipient's email address
2. Write your message
3. Set a subject line
4. Click "Send Email"

Both methods use the secure SMTP connection configured in your .env file.

### Notes on Email Addresses

- The app automatically extracts the original sender's email address from the "From" field
- This works for various email formats like "Name <email@example.com>" or simple "email@example.com"
- The recipient's address is clearly shown in the success message after sending

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
