from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import websockets
import json
import base64
import os

app = FastAPI()

SARVAM_KEY = "sk_capgtvqz_Jr1z0nm11QaF6nnCtehpPQJL"

@app.post("/sarvam-stream")
async def vapi_to_sarvam(request: Request):
    payload = await request.json()
    text_to_speak = payload.get("message", {}).get("text", "")

    # --- THE SAFETY NET ---
    # If Vapi sends an empty ping just to test the connection, 
    # instantly return an empty success response so Vapi doesn't crash.
    if not text_to_speak or text_to_speak.strip() == "":
        return StreamingResponse(iter([b""]), media_type="audio/wav")
    # ----------------------

    async def stream_audio():
        uri = "wss://api.sarvam.ai/text-to-speech-streaming"
        
        # FIX: The API key must be sent as an HTTP Header during the handshake
        headers = {
            "api-subscription-key": SARVAM_KEY
        }
        
        # Open the connection using the corrected headers
        async with websockets.connect(uri, additional_headers=headers) as ws:
            
            # 1. Send configuration (without the authorization key here)
            await ws.send(json.dumps({
                "target_language_code": "hi-IN",
                "speaker": "shubh",
                "model": "bulbul:v3",
                "speech_sample_rate": 16000,
                "enable_preprocessing": True
            }))
            
            # 2. Send the exact text Vapi generated
            await ws.send(json.dumps({
                "inputs": [text_to_speak]
            }))
            
            # 3. Catch the audio chunks and stream them instantly to Vapi
            while True:
                try:
                    response = await ws.recv()
                    data = json.loads(response)
                    
                    if data.get("is_completed"):
                        break
                        
                    if "audios" in data and data["audios"]:
                        # Decode the Base64 chunk and yield the raw audio bytes
                        chunk = base64.b64decode(data["audios"][0])
                        yield chunk
                except Exception as e:
                    print(f"Stream ended or error: {e}")
                    break

    # Return the live audio pipe back to Vapi
    return StreamingResponse(stream_audio(), media_type="audio/wav")
