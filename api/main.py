from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import random
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data generator
PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT", "XRP/USDT"]

async def generate_signals(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            pair = random.choice(PAIRS)
            signal_type = random.choice(["buy", "sell"])
            confidence = random.randint(70, 98)
           
            data = {
                "pair": pair,
                "type": signal_type,
                "confidence": confidence,
                "time": datetime.now().isoformat()
            }
           
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(random.uniform(1.5, 4.0))  # Real-time pace
    except:
        pass

@app.websocket("/ws")
async def stream_signals(websocket: WebSocket):
    await generate_signals(websocket)

@app.get("/")
def home():
    return {"status": "ReversalEdge Engine LIVE", "signals_per_minute": "~20"}
