"""
Generate a test JWT token for testing the deployed Railway service.

This script creates a valid JWT signed with the test secret set in Railway.
Use the generated token to test authenticated endpoints.
"""
import jwt
import time
import sys

# This must match the SUPABASE_JWT_SECRET set in Railway
SECRET = "test-jwt-secret-for-railway-deployment-testing-do-not-use-in-production-replace-with-real-supabase-secret"

def generate_jwt(user_id="test-user-123", email="test@example.com", role="authenticated", valid_hours=1):
    """Generate a JWT token valid for the specified number of hours."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + (valid_hours * 3600),
    }

    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return token

if __name__ == "__main__":
    token = generate_jwt()
    print("\nGenerated Test JWT Token:")
    print("=" * 80)
    print(token)
    print("=" * 80)
    print("\nToken details:")
    print(f"  User ID: test-user-123")
    print(f"  Email: test@example.com")
    print(f"  Role: authenticated")
    print(f"  Valid for: 1 hour")
    print("\nTest the /me endpoint with:")
    print(f'  curl -H "Authorization: Bearer {token}" https://geology-engine-production.up.railway.app/me')
    print()
