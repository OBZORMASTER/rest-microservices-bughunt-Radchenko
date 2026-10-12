from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

app = FastAPI(title="AuthService")

USERS = {
    "alice@example.com": {"password": "alice123", "id": 1},
    "bob@example.com": {"password": "bob123", "id": 2},
}

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/login")
async def login(credentials: LoginRequest):
    user = USERS.get(credentials.email)
    if not user or user["password"] != credentials.password:
        return JSONResponse({"message": "invalid credentials"}, status_code=status.HTTP_401_UNAUTHORIZED)

    token = f"fake-token-for-{credentials.email}"
    return {"accessToken": token, "userId": user["id"]}

@app.get("/whoami")
async def whoami(authorization: str | None = None):
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse({"error": "missing or invalid token"}, status_code=status.HTTP_401_UNAUTHORIZED)

    token = authorization.removeprefix("Bearer ")
    email = token.replace("fake-token-for-", "")

    if email not in USERS:
        return JSONResponse({"error": "user not found"}, status_code=status.HTTP_401_UNAUTHORIZED)

    return {"email": email}
