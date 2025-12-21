# auth.py
import hashlib
import secrets

# --- ŞİFRELEME FONKSİYONLARI ---
def get_password_hash(password: str) -> str:
    salt = secrets.token_hex(8)
    return salt + "$" + hashlib.sha256((salt + password).encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, stored_hash = hashed_password.split("$")
        verify_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
        return verify_hash == stored_hash
    except ValueError:
        return False