import secrets
import base64

def generate_encryption_key():
    """Generate a secure encryption key."""
    # Generate 32 random bytes
    key = secrets.token_bytes(32)
    # Convert to base64 for easy storage
    key_b64 = base64.b64encode(key).decode('utf-8')
    return key_b64

if __name__ == "__main__":
    key = generate_encryption_key()
    print("\nGenerated Encryption Key:")
    print(f"ENCRYPTION_KEY={key}")
    print("\nAdd this to your .env file") 