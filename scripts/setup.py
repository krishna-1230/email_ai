import os
import json
from pathlib import Path
from generate_key import generate_encryption_key

def create_env_file():
    """Create .env file with user input."""
    env_path = Path('.env')
    
    if env_path.exists():
        print(".env file already exists. Skipping creation.")
        return
    
    print("\nSetting up environment variables...")
    
    # Gmail API
    gmail_client_id = input("Enter Gmail Client ID: ").strip()
    gmail_client_secret = input("Enter Gmail Client Secret: ").strip()
    
    # Gemini API
    gemini_api_key = input("Enter Gemini API Key: ").strip()
    
    # Pinecone Serverless
    print("\nPinecone Serverless Setup:")
    print("Using your existing Pinecone index:")
    print("- Index: emailai")
    print("- Dimensions: 1024")
    print("- Metric: cosine")
    print("- Model: llama-text-embed-v2")
    pinecone_api_key = input("Enter Pinecone API Key: ").strip()
    
    # Ollama Setup
    print("\nOllama Setup:")
    print("Using Llama 3.2 for email analysis and reply generation")
    print("This model is excellent for:")
    print("- Understanding email context and tone")
    print("- Generating professional replies")
    print("- Analyzing sentiment and urgency")
    print("- Assisting with meeting scheduling")
    ollama_model = "llama2"  # Using llama2 as the model name for Llama 3.2
    
    # Generate encryption key
    encryption_key = generate_encryption_key()
    
    # Create .env content
    env_content = f"""# Gmail API Credentials
GMAIL_CLIENT_ID={gmail_client_id}
GMAIL_CLIENT_SECRET={gmail_client_secret}

# Gemini API
GEMINI_API_KEY={gemini_api_key}

# Pinecone Vector Database
PINECONE_API_KEY={pinecone_api_key}
PINECONE_INDEX=emailai
PINECONE_HOST=https://emailai-xod54xm.svc.aped-4627-b74a.pinecone.io
PINECONE_DIMENSIONS=1024
PINECONE_METRIC=cosine
PINECONE_EMBEDDING_MODEL=llama-text-embed-v2
PINECONE_ENVIRONMENT=aws-us-east-1

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL={ollama_model}

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
ENCRYPTION_KEY={encryption_key}
SESSION_TIMEOUT_MINUTES=60
"""
    
    # Write .env file
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("\n.env file created successfully!")
    print("\nYour setup is complete with:")
    print("1. Llama 3.2 for email analysis and reply generation")
    print("2. Pinecone's llama-text-embed-v2 for vector embeddings")

def setup_gmail_credentials():
    """Set up Gmail credentials file."""
    creds_path = Path('credentials.json')
    
    if creds_path.exists():
        print("credentials.json already exists. Skipping creation.")
        return
    
    print("\nSetting up Gmail credentials...")
    print("Please download your OAuth 2.0 credentials from Google Cloud Console")
    print("and save them as 'credentials.json' in the project root directory.")
    
    # Wait for user to create the file
    while not creds_path.exists():
        input("Press Enter once you've created credentials.json...")
    
    print("Gmail credentials set up successfully!")

def main():
    """Main setup function."""
    print("Welcome to the Email Assistant Setup!")
    print("This script will help you configure the application.")
    
    # Create .env file
    create_env_file()
    
    # Set up Gmail credentials
    setup_gmail_credentials()
    
    print("\nSetup complete! You can now run the application with:")
    print("streamlit run app.py")

if __name__ == "__main__":
    main() 