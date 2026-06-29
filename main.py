from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

EMAIL = "24f1000791@ds.study.iitm.ac.in"

RATE_LIMIT = 13
WINDOW = 10

ALLOWED_ORIGINS = [
    "https://app-ammivz.example.com",
    "https://exam.sanand.workers.dev" 
]

app = FastAPI()

# Make sure this dictionary is defined so the rate limiter can use it!
CLIENT_BUCKETS = {}

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestContextMiddleware)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        client = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()
        bucket = CLIENT_BUCKETS.setdefault(client, [])
        bucket[:] = [t for t in bucket if now - t < WINDOW]

        if len(bucket) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        bucket.append(now)
        return await call_next(request)

app.add_middleware(RateLimitMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }