from datetime import timezone, datetime, timedelta
import random
import jwt

JWT_SECRET = "secret_key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = timedelta(minutes=10)

def generate_otp(length=6):
    return str(random.randint(10**(length-1), (10**length)-1))

def create_otp_token(payload):
    now = datetime.now(timezone.utc)

    if isinstance(payload, dict):
        token_data = payload.copy()

        if "user_id" in token_data:
            token_data["user_id"] = str(token_data["user_id"])
    else:
        token_data = {"user_id": str(payload)}

    token_data.update({
        "exp": now + JWT_EXPIRATION_DELTA,
        "iat": now,
        "nbf": now,
    })

    return jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_otp_token(token):
    if not token:
        return None
        
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  
    except jwt.InvalidTokenError:
        return None 
    except Exception:
        return None
