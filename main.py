from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import websockets
import json
import base64
import os

app = FastAPI()

SARVAM_KEY = os.getenv("sk_kmkrqgbm_BQUP7MnQOqLyiRzo1utR3E8p", "")

@app.post("/sarvam-stream")
async def vapi_to_sarvam(request: Request):
    payload = await request.json()
    text_to_speak = payload.get("message", {}).get("text", "")

    # Safety Net for empty Vapi pings
    if not text_to_speak or text_to_speak.strip() == "":
        return StreamingResponse(iter([b""]), media_type="audio/wav")

    async def stream_audio():
        # FIX: The API key must be injected directly into the WebSocket URL 
        # for Sarvam's streaming authentication.
        uri = f"wss://api.sarvam.ai/text-to-speech-streaming?api-subscription-key={SARVAM_KEY}"
        
        # Connect to the new URI (removed additional_headers)
        async with websockets.connect(uri) as ws:
            
            # 1. Send configuration
            await ws.send(json.dumps({
                "target_language_code": "hi-IN",
                "speaker": "shubh",
                "model": "bulbul:v3",
                "speech_sample_rate": 16000,
                "enable_preprocessing": True
            }))
            
            # 2. Send text
            await ws.send(json.dumps({
                "inputs": [text_to_speak]
            }))
            
            # 3. Stream audio back
            while True:
                try:
                    response = await ws.recv()
                    data = json.loads(response)
                    
                    if data.get("is_completed"):
                        break
                        
                    if "audios" in data and data["audios"]:
                        chunk = base64.b64decode(data["audios"][0])
                        yield chunk
                except Exception as e:
                    print(f"Stream ended or error: {e}")
                    break

    return StreamingResponse(stream_audio(), media_type="audio/wav")
