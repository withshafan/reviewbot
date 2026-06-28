import os
from dotenv import load_dotenv
from app.auth import generate_app_jwt

# Load environment variables
load_dotenv()

# Get credentials from .env
app_id = os.getenv("GITHUB_APP_ID")
private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")

print(f"App ID: {app_id}")
print(f"Private key path: {private_key_path}")

# Check if private key file exists
if not os.path.exists(private_key_path):
    print(f"[ERROR] Private key file not found at {private_key_path}")
    print("Make sure you renamed the .pem file to 'private_key.pem' and placed it in the project root.")
    exit(1)

# Try to generate a JWT
try:
    jwt_token = generate_app_jwt(app_id, private_key_path)
    print(f"[SUCCESS] JWT generated successfully!")
    print(f"JWT (first 50 characters): {jwt_token[:50]}...")
    print(f"JWT length: {len(jwt_token)} characters")
except Exception as e:
    print(f"[ERROR] generating JWT: {e}")

