from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import websockets
import json
import base64
import os

app = FastAPI()

SARVAM_KEY = os.getenv("SARVAM_API_KEY")

@app.post("/sarvam-stream")
async def vapi_to_sarvam(request: Request):
    payload = await request.json()
    text_to_speak = payload.get("message", {}).get("text", "")

    async def stream_audio():
        uri = "wss://api.sarvam.ai/text-to-speech-streaming"
        
        async with websockets.connect(uri) as ws:
            # 1. Send configuration with your API Key
            await ws.send(json.dumps({
                "target_language_code": "hi-IN",
                "speaker": "shubh",
                "model": "bulbul:v3",
                "speech_sample_rate": 16000,
                "enable_preprocessing": True,
                "authorization": SARVAM_KEY
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
