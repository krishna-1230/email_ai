# AI-Powered Contextual Email Assistant

An intelligent email assistant that helps you manage your inbox by analyzing email threads, generating contextual replies, scheduling meetings, and more.

## Features

- 📧 Smart email thread analysis
- 🤖 AI-powered reply generation in multiple tones (formal, casual, direct)
- 📅 Meeting scheduling and calendar management
  - View upcoming meetings
  - Schedule new meetings with intelligent time selection
  - Edit and cancel existing meetings
  - Find available time slots based on your calendar
  - Auto-detect meeting requests in emails
  - Smart time zone handling
- 🌐 Language translation for emails
- 📊 Sentiment and urgency analysis
- 🔒 Secure credential management
- 🚀 Local LLM support with Llama 2
- 🗄️ Serverless vector storage with Pinecone
- ✉️ Direct email sending via SMTP

## Prerequisites

- Python 3.8 or higher
- Ollama with Llama 2 installed
- Gmail account
- Google Cloud Project with Gmail API and Google Calendar API enabled
- Gemini API key
- Pinecone serverless account with existing index

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/krishna-1230/email_ai.git
cd email_ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Linux/macOS
source venv/bin/activate
# On Windows
venv\Scripts\activate
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
# On Windows
run_email_ai.bat
# On Linux/macOS
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
   - Add the necessary scopes: 
     - `.../auth/gmail.readonly` (Read Gmail messages)
     - `.../auth/gmail.send` (Send Gmail messages)
     - `.../auth/calendar` (Read/write calendar data)
     - `.../auth/calendar.events` (Manage calendar events)
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
2. Pull the Llama 2 model:
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
PINECONE_HOST=your_pinecone_host
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
TIMEZONE=UTC

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
# On Windows
run_email_ai.bat
# On Linux/macOS
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Authenticate with your Gmail account when prompted

4. Email Management Features:
   - View and select email threads
   - Generate AI-powered replies in different tones (formal, casual, direct)
   - Analyze email sentiment and urgency
   - Translate emails to different languages

5. Calendar Management:
   - Use the navigation menu in the sidebar to switch to the Calendar Management view
   - View your upcoming meetings and appointments
   - Schedule new meetings with intelligent time slot suggestions
   - Find available meeting slots based on your calendar
   - Edit existing meetings (change time, attendees, description)
   - Cancel meetings with optional notifications to attendees

6. Meeting Scheduling from Emails:
   - When analyzing an email thread, the system detects meeting requests
   - The system suggests available meeting times based on your calendar and the email context
   - You can select a suggested time slot and provide meeting details
   - Calendar invites are automatically sent to all participants

## Testing Calendar Functionality

You can test the calendar features separately using the test script:

```bash
python test_calendar.py
```

This script will:
- Verify authentication with the Google Calendar API
- Display your upcoming meetings
- Find available time slots for scheduling
- (Optionally) Test creating and cancelling a meeting

## Calendar API Features Reference

The calendar management system provides the following capabilities:

### Meeting Extraction from Email

- Detects meeting requests through language patterns
- Extracts dates, times, and days mentioned in emails
- Identifies contextual meeting-related content

### Time Slot Management

- Finds available meeting slots based on your Google Calendar
- Intelligently avoids times when you're busy
- Limits suggestions to business hours (9 AM - 5 PM, Monday-Friday)
- Takes time zone into account

### Calendar Operations

- Create new meetings with titles, descriptions, and attendee lists
- Schedule meetings with notification settings
- Update existing meetings (time, attendees, description, location)
- Cancel meetings with optional attendee notifications
- View list of upcoming meetings

## Security Considerations

- API keys and credentials are stored in the `.env` file (not committed to version control)
- The application uses encryption for sensitive data
- Session timeouts are implemented for security
- Ollama runs locally on your machine, keeping your data private
- Pinecone serverless provides secure vector storage

## Project Structure

```
email_ai/
  - app.py                  # Main Streamlit application
  - backend/                # Core functionality modules
    - calendar_manager.py   # Calendar operations
    - context_analyzer.py   # Email analysis
    - email_reader.py       # Email retrieval
    - reply_generator.py    # AI reply generation
    - scheduler.py          # Meeting scheduling
    - simple_email_sender.py # Email sending
    - translator.py         # Language translation
  - config/                 # Configuration
    - prompts.py            # AI prompt templates
  - models/                 # AI model interfaces
    - model_loader.py       # Load and manage AI models
  - scripts/                # Utility scripts
    - generate_key.py       # Generate encryption key
    - setup.py              # Setup environment
  - utils/                  # Utility functions
    - auth.py               # Authentication
    - config.py             # Configuration management
    - embeddings.py         # Vector embeddings
```

## Troubleshooting

### Gmail Authorization Issues

If you encounter authorization issues:
1. Click "Reauthorize with Send Permission" button if shown
2. Or manually delete `token.pickle` file and restart the application
3. Make sure you've granted all required permissions during authorization

### Calendar API Permissions

If calendar features aren't working:
1. Ensure you've enabled Google Calendar API in Google Cloud Console
2. Verify you've granted the required calendar scopes during authentication
3. Check the `.env` file for proper TIMEZONE setting (e.g., "America/New_York")
4. Run `python test_calendar.py` to diagnose specific issues

### Email Sending Problems

If emails aren't sending:
1. Verify your SMTP settings in the `.env` file
2. For Gmail, you'll need an App Password if you have 2FA enabled
3. Check the logs for specific errors

## Additional Information

* Time zone handling: The app uses your Google Calendar time zone settings
* Business hours: Default is 9 AM - 5 PM Monday-Friday, but can be customized
* Meeting duration: Default is 30 minutes, but can be adjusted for each meeting
* Email reply tones: Choose between formal, casual, or direct tones

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Cloud Platform for Gmail and Calendar APIs
- Gemini API for advanced language processing
- Pinecone for vector database capabilities
- Ollama for local LLM support
- Streamlit for the user interface
- LangChain for AI orchestration
