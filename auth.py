from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from config import JWT_SECRET

def hash_password(password: str):
    return generate_password_hash(password)

def verify_password(hash_: str, password: str):
    return check_password_hash(hash_, password)

def create_token(user_id: int, minutes=60*24):
    payload = {"sub": user_id, "exp": datetime.now(datetime.timezone.utc) + timedelta(minutes=minutes)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]
    except Exception:
        return None
