from django.core.management.utils import get_random_secret_key
import secrets
import string

def generate_jwt_secret():
    """Generate a secure JWT secret key"""
    return get_random_secret_key()

def generate_strong_secret(length=64):
    """Generate a cryptographically strong secret"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print("🔐 JWT Secret Key Options:")
    print("=" * 50)
    print(f"Option 1 (Django style): {generate_jwt_secret()}")
    print(f"Option 2 (Strong 64-char): {generate_strong_secret()}")
    print(f"Option 3 (Extra strong): {generate_strong_secret(128)}")