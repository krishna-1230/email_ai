import os
from dotenv import load_dotenv
from typing import Dict, List

def load_config() -> Dict[str, str]:
    """Load and validate environment variables."""
    # Load .env file
    load_dotenv()
    
    # Required environment variables
    required_vars = [
        'GMAIL_CLIENT_ID',
        'GMAIL_CLIENT_SECRET',
        'GEMINI_API_KEY',
        'PINECONE_API_KEY',
        'PINECONE_ENVIRONMENT'
    ]
    
    # Optional environment variables with defaults
    optional_vars = {
        'DEBUG': 'False',
        'LOG_LEVEL': 'INFO',
        'DEFAULT_REPLY_TONE': 'formal',
        'MAX_THREADS_TO_FETCH': '10',
        'MEETING_DURATION_MINUTES': '30',
        'DAYS_AHEAD_FOR_SCHEDULING': '7',
        'DEFAULT_TARGET_LANGUAGE': 'en',
        'ENABLE_AUTO_TRANSLATION': 'False',
        'SESSION_TIMEOUT_MINUTES': '60',
        'OLLAMA_HOST': 'http://localhost:11434',
        'OLLAMA_MODEL': 'llama2'
    }
    
    # Check required variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Get all environment variables
    config = {}
    
    # Add required variables
    for var in required_vars:
        config[var] = os.getenv(var)
    
    # Add optional variables with defaults
    for var, default in optional_vars.items():
        config[var] = os.getenv(var, default)
    
    return config

def validate_config(config: Dict[str, str]) -> List[str]:
    """Validate configuration values."""
    errors = []
    
    # Validate boolean values
    bool_vars = ['DEBUG', 'ENABLE_AUTO_TRANSLATION']
    for var in bool_vars:
        if config[var].lower() not in ['true', 'false']:
            errors.append(f"{var} must be 'true' or 'false'")
    
    # Validate numeric values
    numeric_vars = {
        'MAX_THREADS_TO_FETCH': (1, 100),
        'MEETING_DURATION_MINUTES': (15, 480),
        'DAYS_AHEAD_FOR_SCHEDULING': (1, 30),
        'SESSION_TIMEOUT_MINUTES': (5, 1440)
    }
    
    for var, (min_val, max_val) in numeric_vars.items():
        try:
            value = int(config[var])
            if not min_val <= value <= max_val:
                errors.append(f"{var} must be between {min_val} and {max_val}")
        except ValueError:
            errors.append(f"{var} must be a number")
    
    # Validate tone
    if config['DEFAULT_REPLY_TONE'] not in ['formal', 'casual', 'direct']:
        errors.append("DEFAULT_REPLY_TONE must be 'formal', 'casual', or 'direct'")
    
    # Validate language code
    if not config['DEFAULT_TARGET_LANGUAGE'].isalpha() or len(config['DEFAULT_TARGET_LANGUAGE']) != 2:
        errors.append("DEFAULT_TARGET_LANGUAGE must be a 2-letter language code")
    
    return errors

def get_config() -> Dict[str, str]:
    """Get validated configuration."""
    config = load_config()
    errors = validate_config(config)
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))
    
    return config 