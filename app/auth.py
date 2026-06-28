import hmac
import hashlib
import os
# pyrefly: ignore [missing-import]
import jwt
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def validate_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """
    Validates the GitHub webhook signature using HMAC-SHA256.
    
    Args:
        payload_body: Raw bytes of the request body
        signature_header: The X-Hub-Signature-256 header value
        secret: The webhook secret configured in GitHub App settings
    
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header:
        return False
    
    # GitHub sends signatures as "sha256=..."
    # Extract the actual hex digest after the "sha256=" prefix
    parts = signature_header.split("=")
    if len(parts) != 2 or parts[0] != "sha256":
        return False
    
    # Compute HMAC-SHA256 of the raw payload body
    expected = hmac.new(
        secret.encode("utf-8"),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected, parts[1])

def generate_app_jwt(app_id: str, private_key_path: str) -> str:
    """
    Generates a JWT for GitHub App authentication.
    The JWT is valid for 10 minutes and is used to request installation access tokens.
    """
    # Load the RSA private key from the file
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    
    # Build the JWT payload
    now = int(time.time())
    payload = {
        "iat": now - 60,   # Issued at: 60 seconds ago to account for clock drift
        "exp": now + 540,  # Expires in 9 minutes (maximum allowed is 10 minutes)
        "iss": app_id      # The GitHub App ID
    }
    
    # Encode and sign the JWT using RS256
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token

