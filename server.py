import os
import secrets
import json
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from gpt4all import GPT4All

# === CONFIGURATION ===
MODEL_FILENAME = "Llama-3.2-1B-Instruct-Q4_0.gguf"
MODEL_PATH = r"C:\Users\smitk\.cache\gpt4all"
KEYS_FILE = r"D:\Ai_serv\api_keys.json"

# === SET YOUR ADMIN PASSWORD HERE ===
ADMIN_SECRET = "Smit@2007_9879828458"

SYSTEM_PROMPT = """You are a helpful, knowledgeable, and concise AI assistant.
- Answer clearly and directly.
- If you don't know something, say so honestly.
- Use bullet points or numbered lists when explaining steps or multiple points.
- Keep responses focused and avoid unnecessary filler phrases."""

LLAMA3_STOP_TOKENS = [
    "<|eot_id|>",
    "<|start_header_id|>",
    "<|end_header_id|>",
    "<|begin_of_text|>",
]
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(title="Local LLaMA API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# === Load model once at startup ===
print(f"Loading model: {MODEL_FILENAME} ...")
try:
    model = GPT4All(MODEL_FILENAME, model_path=MODEL_PATH, allow_download=False, device='cpu')
    print("Model loaded and ready!\n")
except Exception as e:
    print(f"Failed to load model: {e}")
    exit(1)

# === API Key Helpers ===
def load_keys() -> dict:
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_keys(keys: dict):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

def validate_key(api_key: str) -> dict:
    keys = load_keys()
    if api_key not in keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not keys[api_key].get("active", True):
        raise HTTPException(status_code=403, detail="API key is disabled")
    return keys[api_key]

# === Request Models ===
class ChatRequest(BaseModel):
    message: str
    stream: Optional[bool] = False
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7

class GenerateKeyRequest(BaseModel):
    name: str
    admin_secret: str

# === ROUTES ===

@app.get("/")
def root():
    return {
        "status": "running",
        "model": MODEL_FILENAME,
        "docs": "Visit /docs for full API documentation"
    }

@app.post("/generate-key")
def generate_key(req: GenerateKeyRequest):
    """Create a new API key. Requires admin secret."""
    if req.admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Wrong admin secret")

    new_key = "llama-" + secrets.token_hex(24)
    keys = load_keys()
    keys[new_key] = {
        "name": req.name,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active": True,
        "request_count": 0
    }
    save_keys(keys)
    return {"api_key": new_key, "name": req.name}

@app.post("/chat")
def chat(req: ChatRequest, x_api_key: str = Header(...)):
    """Send a message, get a response. Pass your API key in x-api-key header."""
    key_data = validate_key(x_api_key)

    # Track usage
    keys = load_keys()
    keys[x_api_key]["request_count"] += 1
    keys[x_api_key]["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_keys(keys)

    if req.stream:
        def generate():
            with model.chat_session(system_prompt=SYSTEM_PROMPT):
                buffer = ""
                for token in model.generate(
                    req.message,
                    max_tokens=req.max_tokens,
                    temp=req.temperature,
                    top_k=40,
                    top_p=0.9,
                    repeat_penalty=1.18,
                    streaming=True,
                ):
                    buffer += token
                    if any(stop in buffer for stop in LLAMA3_STOP_TOKENS):
                        break
                    yield token
        return StreamingResponse(generate(), media_type="text/plain")

    else:
        full_response = []
        buffer = ""
        with model.chat_session(system_prompt=SYSTEM_PROMPT):
            for token in model.generate(
                req.message,
                max_tokens=req.max_tokens,
                temp=req.temperature,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.18,
                streaming=True,
            ):
                buffer += token
                if any(stop in buffer for stop in LLAMA3_STOP_TOKENS):
                    break
                full_response.append(token)

        return {
            "response": "".join(full_response).strip(),
            "model": MODEL_FILENAME,
            "user": key_data["name"],
            "tokens_generated": len(full_response)
        }

@app.get("/keys")
def list_keys(admin_secret: str):
    """List all API keys and usage stats."""
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Wrong admin secret")
    return load_keys()

@app.delete("/keys/{key}")
def disable_key(key: str, admin_secret: str):
    """Disable an API key."""
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Wrong admin secret")
    keys = load_keys()
    if key not in keys:
        raise HTTPException(status_code=404, detail="Key not found")
    keys[key]["active"] = False
    save_keys(keys)
    return {"status": "disabled", "key": key}
@app.get("/health")
def health():
    """Check if server is alive."""
    return {"status": "ok", "model_loaded": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)