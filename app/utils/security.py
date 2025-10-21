from cryptography.fernet import Fernet
import base64
import hashlib
from flask import current_app

def get_fernet():
    key = current_app.config['SECRET_KEY']
    # Derive a 32-byte key for Fernet
    hashed_key = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(hashed_key)
    return Fernet(fernet_key)

def encrypt_password(password):
    if not password:
        return None
    f = get_fernet()
    return f.encrypt(password.encode())

def decrypt_password(encrypted_password):
    if not encrypted_password:
        return None
    f = get_fernet()
    try:
        decrypted_bytes = f.decrypt(encrypted_password)
        return decrypted_bytes.decode()
    except Exception:
        # If decryption fails, it might be an old plain-text password or corrupted data
        return None

