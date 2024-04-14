import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import timedelta, datetime
from sqlalchemy.orm import Session

from db.models.user import User

class JWTAuthenticator:
    def __init__(self, splitz_db, secret_key, algorithm):
        self.splitz_db = splitz_db
        self.secret_key = secret_key
        self.algorithm = algorithm

    def get_splitz_user(
            self, 
            session: Session = Depends(lambda: JWTAuthenticator.splitz_db.get_db),
            token: str = Depends(OAuth2PasswordBearer(tokenUrl='token'))
        ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, key=self.secret_key,
                                 algorithms=[self.algorithm])

            decoded_exp = payload["exp"]
            current_time = datetime.utcnow()
            if current_time > datetime.fromtimestamp(decoded_exp):
                raise credentials_exception
            if not payload["phone_number"] or not payload["id"]:
                raise credentials_exception

        except JWTError:
            raise credentials_exception

        user = session.query(User).filter(User.id == payload["id"])
        if user is None:
            raise credentials_exception
        return user

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
            decoded_token = jwt.decode(
                token, key=self.secret_key, algorithms=[self.algorithm])
            return decoded_token
        except JWTError as error:
            logging.warning(f'Unable to decode access token: {error}')
            return None

    def verify_access_token(self, token: str) -> bool:
        '''
        check if JWT is still valid. Check if its expired or not
        '''
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
