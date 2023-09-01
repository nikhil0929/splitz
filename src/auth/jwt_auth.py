from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import timedelta, datetime

class JWTAuthenticator:
    def __init__(self, secret_key, algorithm):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, payload: dict, expires_delta=None) -> str:
        to_encode = payload.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=30)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> dict:
        try:
            # print("TOKEN: ", token, self.secret_key, self.algorithm)
            decoded_token = jwt.decode(token, key=self.secret_key, algorithms=[self.algorithm])
            return decoded_token
        except JWTError as error:
            print(error)
            return None
    
    ## check if JWT is still valid. Check if its expired or not
    def verify_access_token(self, token: str) -> bool:
        try:
            decoded = self.decode_access_token(token)
            # print(decoded)
            decoded_exp = decoded["exp"]
            current_time = datetime.utcnow()
            if current_time > datetime.fromtimestamp(decoded_exp):
                return False
            return True
        except JWTError:
            return False