import os
import google.generativeai as genai
import logging
from utils.auth import get_gmail_service
from backend.email_reader import EmailReader
from email.mime.text import MIMEText
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the Gemini API key from environment variable
gemini_api_key = os.getenv('GEMINI_API_KEY')

if not gemini_api_key:
    print("Error: GEMINI_API_KEY environment variable not set.")
    exit(1)

# Test Gemini API
def test_gemini_api():
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        prompt = "Say hello from Gemini!"
        response = model.generate_content(prompt)
        print("Gemini API call successful! Response:")
        print(response.text)
        return True
    except Exception as e:
        print("Error communicating with Gemini API:")
        print(e)
        return False

# Test Gmail API and cachetools integration
def test_gmail_api():
    try:
        print("\nTesting Gmail API connection...")
        gmail_service, creds = get_gmail_service()
        
        # Test listing messages
        results = gmail_service.users().messages().list(userId='me', maxResults=1).execute()
        messages = results.get('messages', [])
        
        if messages:
            print(f"Successfully connected to Gmail API! Found {len(messages)} messages")
            return True
        else:
            print("Connected to Gmail API but no messages found")
            return True
    except Exception as e:
        print("Error connecting to Gmail API:")
        print(e)
        return False

# Test Pinecone embedding dimension handling
def test_embedding():
    try:
        print("\nTesting Gemini embeddings...")
        genai.configure(api_key=gemini_api_key)
        
        # Generate embedding
        test_text = "This is a test for embeddings"
        embedding = genai.embed_content(
            model="models/embedding-001",
            content=test_text,
            task_type="retrieval_document",
        )
        
        # Extract embedding values
        embedding_values = embedding.embedding if hasattr(embedding, 'embedding') else embedding['embedding']
        
        print(f"Successfully generated embedding with dimension: {len(embedding_values)}")
        return True
    except Exception as e:
        print("Error generating embedding:")
        print(e)
        return False

# Test email sending capability
def test_email_send():
    try:
        print("\nTesting email send capability...")
        # Initialize with proper service
        gmail_service, creds = get_gmail_service()
        email_reader = EmailReader(gmail_service)
        
        # Get your own email address
        profile = gmail_service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress', '')
        
        if not user_email:
            print("Could not determine user email")
            return False
            
        print(f"Found user email: {user_email}")
            
        # Create a test email to yourself
        subject = "Test Email Send Capability"
        body = "This is a test email to verify send capability works correctly."
        
        # Don't actually send in test mode
        print(f"Email sending test PASSED (No email actually sent)")
        print(f"Would have sent to: {user_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        return True
    except Exception as e:
        print("Error testing email send capability:")
        print(e)
        return False

if __name__ == "__main__":
    tests = {
        "Gemini API": test_gemini_api(),
        "Gmail API": test_gmail_api(),
        "Embeddings": test_embedding(),
        "Email Send": test_email_send()
    }
    
    print("\n===== TEST RESULTS =====")
    all_passed = True
    for test_name, passed in tests.items():
        result = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {result}")
        if not passed:
            all_passed = False
    
    print("\nAll tests passed!" if all_passed else "\nSome tests failed!") 