# Read this stack overflow post: https://stackoverflow.com/questions/71525132/how-to-write-a-custom-fastapi-middleware-class
# Basically to use the `app.add_middleware` method, you need to create a class that inherits from `BaseHTTPMiddleware`

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError
from jwt import ImmatureSignatureError, InvalidAlgorithmError, InvalidAudienceError, InvalidKeyError, InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN


class JWTMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app,
            jwt_authenticator
    ):
        super().__init__(app)
        self.jwt_authenticator = jwt_authenticator
        self.allowed_paths = ["/user/initialize-verification",
                              "/user/complete-verification",
                              "/receipts/receive-receipt",
                              "/docs",
                              "/openapi.json"]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        
        if request.url.path in self.allowed_paths:
            return await call_next(request)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        bearer_token = request.headers.get("Authorization")
        if not bearer_token:
            return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={
                "detail": "Missing access token",
                "body": "Missing access token"
            })
        
        try:
            auth_token = bearer_token.split(" ")[1].strip()
            is_valid = self.jwt_authenticator.verify_access_token(auth_token)
            if not is_valid:
                return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={
                "detail": "Access token invalid",
                "body": "Access token invalid"
            })
            token_payload = self.jwt_authenticator.decode_access_token(auth_token)
        except (ExpiredSignatureError,
                ImmatureSignatureError,
                InvalidAlgorithmError,
                InvalidTokenError,
                InvalidAudienceError,
                InvalidKeyError) as error:
            return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={
                "detail": str(error),
                "body": str(error)
                })
        else:
            request.state.user = token_payload["usr"]
            response = await call_next(request)
        return response