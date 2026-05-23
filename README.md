# 🦙 Local LLaMA API Server

Run a **private AI API server** on your own laptop using a local LLaMA model — no OpenAI subscription, no cloud, no data leaving your machine. Includes a beautiful chat web UI and API key management.

---

## 📸 What It Looks Like

> A dark-themed chat interface running entirely off your local machine, accessible from anywhere via a public URL.

---

## 🧠 How It Works

```
Your Browser / Anyone on the Internet
        ↓  (HTTPS)
    ngrok / Cloudflare Tunnel       ← gives your laptop a public URL
        ↓
    server.py (FastAPI)             ← runs on your laptop, port 8000
        ↓
    GPT4All + LLaMA Model           ← the AI brain, runs 100% locally
        ↓
    Response sent back to user
```

1. The **LLaMA model** (a `.gguf` file) runs locally on your CPU using [GPT4All](https://github.com/nomic-ai/gpt4all)
2. **`server.py`** is a FastAPI web server that wraps the model with an HTTP API and API key authentication
3. **ngrok or Cloudflare Tunnel** punches a hole through your firewall and gives your local server a public HTTPS URL
4. **`chat.html`** is a standalone chat UI anyone can open in their browser to talk to your model

No data ever leaves your machine except through the tunnel you control. 100% private.

---

## 📦 Files in This Repo

| File | Description |
|---|---|
| `server.py` | The FastAPI API server — handles auth, model loading, and chat |
| `chat.html` | Standalone chat web UI — open in any browser, no install needed |
| `README.md` | This file |

> The AI model file is **not included** (too large for GitHub). See [Download the Model](#-download-the-model) below.

---

## ⚙️ Requirements

- Python 3.10+
- ~6GB free disk space (for the model)
- ~8GB RAM recommended
- Windows, macOS, or Linux

---

## 🚀 Setup Guide

### Step 1 — Install dependencies

```bash
pip install fastapi uvicorn gpt4all python-jose
```

### Step 2 — Download the AI model

See [Download the Model](#-download-the-model) below. Save the `.gguf` file to:

```
C:\Users\<YourUsername>\.cache\gpt4all\        ← Windows
~/.cache/gpt4all/                               ← macOS / Linux
```

### Step 3 — Configure `server.py`

Open `server.py` and update these lines at the top:

```python
MODEL_FILENAME = "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"   # your model filename
MODEL_PATH = r"C:\Users\YourUsername\.cache\gpt4all"        # path to model folder
ADMIN_SECRET = "your-strong-password-here"                  # change this!
```

### Step 4 — Run the server

```bash
python server.py
```

You should see:
```
Loading model: Meta-Llama-3-8B-Instruct.Q4_K_M.gguf ...
Model loaded and ready!
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Step 5 — Create your first API key

```bash
curl -X POST http://localhost:8000/generate-key \
  -H "Content-Type: application/json" \
  -d '{"name": "mykey", "admin_secret": "your-strong-password-here"}'
```

Response:
```json
{"api_key": "llama-abc123...", "name": "mykey"}
```

### Step 6 — Test it

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: llama-abc123..." \
  -d '{"message": "Hello, who are you?"}'
```

### Step 7 — Open the chat UI

Open `chat.html` in your browser. Click **Config**, enter:
- API URL: `http://localhost:8000`
- API Key: your generated key

---

## 🌐 Make It Public (Share with Others)

To give others access to your local server from anywhere on the internet:

**Option A — ngrok (free account required)**
```bash
ngrok http 8000
# → https://abc123.ngrok-free.app
```

**Option B — Cloudflare Tunnel (free, no account needed)**
```bash
cloudflared tunnel --url http://localhost:8000
# → https://something-random.trycloudflare.com
```

Share the public URL + an API key with anyone you want to give access. Update the API URL in `chat.html` Config to the public URL.

---

## 📥 Download the Model

### Recommended — Meta LLaMA 3 8B (best quality, ~5GB)

Direct download link:
```
https://huggingface.co/MaziyarPanahi/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf
```

Mirror:
```
https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf
```

### Lightweight — LLaMA 3.2 1B (faster, lower quality, ~800MB)

Available via the [GPT4All desktop app](https://www.nomic.ai/gpt4all) — search "Llama 3.2 1B" in the Models tab.

### Model Comparison

| Model | Size | RAM Needed | Quality |
|---|---|---|---|
| Llama 3.2 1B | ~800MB | 4GB | Basic |
| Llama 3.2 3B | ~2GB | 6GB | Decent |
| **Llama 3 8B (recommended)** | **~5GB** | **8GB** | **Good** |

---

## 🔑 API Reference

All endpoints except `/` and `/health` require an `x-api-key` header.

### `GET /`
Check server status.

**Response:**
```json
{"status": "running", "model": "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"}
```

### `POST /chat`
Send a message and get a response.

**Headers:** `x-api-key: llama-...`

**Body:**
```json
{
  "message": "Your question here",
  "max_tokens": 512,
  "temperature": 0.7,
  "stream": false
}
```

**Response:**
```json
{
  "response": "AI answer here...",
  "model": "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf",
  "user": "mykey",
  "tokens_generated": 85
}
```

### `POST /generate-key`
Create a new API key (requires admin secret).

**Body:**
```json
{"name": "friend_john", "admin_secret": "your-password"}
```

### `GET /keys?admin_secret=...`
List all API keys and usage stats.

### `DELETE /keys/{key}?admin_secret=...`
Disable an API key.

### `GET /health`
Simple health check — returns `{"status": "ok"}`.

> 💡 Visit `http://localhost:8000/docs` for an interactive API explorer (auto-generated by FastAPI).

---

## 🛡️ Security Notes

- Change `ADMIN_SECRET` in `server.py` before running — don't use the default
- API keys are stored in `api_keys.json` in the same folder as `server.py`
- The ngrok/Cloudflare URL is public — only share API keys with people you trust
- The model runs entirely on your machine — no conversation data is sent anywhere

---

## 🧩 Tech Stack

| Component | Technology |
|---|---|
| AI Runtime | [GPT4All](https://github.com/nomic-ai/gpt4all) |
| AI Model | Meta LLaMA 3 (GGUF quantized) |
| API Server | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Tunneling | [ngrok](https://ngrok.com) or [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) |
| Chat UI | Vanilla HTML/CSS/JS (no framework, no dependencies) |

---

## 📄 License

MIT — use it, modify it, share it freely.
