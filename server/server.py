import strawberry
from fastapi import FastAPI, WebSocket, Request
from strawberry.fastapi import GraphQLRouter
import resolvers
import uvicorn
import jwt
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

async def get_context(websocket: WebSocket = None, request: Request = None) -> Dict[str, Any]:
    user = {"role": "guest"}
    token = None

    if request:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            print(f"Received token (HTTP): {token}")
    elif websocket:
        try:
            token = websocket.query_params.get("token")
            print(f"Received token (WS): {token}")
        except AttributeError:
            pass

    if token:
        try:
            user = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print(f"Decoded user: {user}")
        except jwt.ExpiredSignatureError:
            print("Token expired")
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
        except Exception as e:
            print(f"Token decoding error: {e}")

    return {"user": user}


schema = strawberry.Schema(
    query=resolvers.Query,
    mutation=resolvers.Mutation,
    subscription=resolvers.Subscription
)

app = FastAPI()
app.include_router(
    GraphQLRouter(
        schema,
        context_getter=get_context
    ),
    prefix="/graphql"
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)