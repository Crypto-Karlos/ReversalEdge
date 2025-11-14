from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import aiohttp
from datetime import datetime
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
PAIRS = ["btcusdt", "ethusdt", "solusdt", "adausdt", "xrpusdt"]
VOLUME_WINDOW = 10
PRICE_CHANGE_THRESHOLD = 0.3  # %
VOLUME_SPIKE_THRESHOLD = 2.5  # 2.5x avg
price_history = {}

async def fetch_klines(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval=1m&limit={VOLUME_WINDOW + 1}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as resp:
                data = await resp.json()
                if not data or len(data) < 2:
                    return None, None
                closes = [float(k[4]) for k in data]
                volumes = [float(k[5]) for k in data]
                return closes, volumes
        except:
            return None, None

async def detect_reversal(symbol):
    closes, volumes = await fetch_klines(symbol)
    if not closes or len(closes) < 2:
        return None

    current_price = closes[-1]
    prev_price = closes[-2]
    current_vol = volumes[-1]
    avg_vol = np.mean(volumes[:-1]) if len(volumes) > 1 else current_vol

    price_change_pct = ((current_price - prev_price) / prev_price) * 100
    vol_spike = current_vol / avg_vol if avg_vol > 0 else 1

    if (abs(price_change_pct) >= PRICE_CHANGE_THRESHOLD and
        vol_spike >= VOLUME_SPIKE_THRESHOLD):

        confidence = min(98, int(70 + abs(price_change_pct) * 8 + (vol_spike - 1) * 15))
        signal_type = "buy" if price_change_pct > 0 else "sell"

        return {
            "pair": symbol.upper().replace("USDT", "/USDT"),
            "type": signal_type,
            "confidence": confidence,
            "time": datetime.now().isoformat(),
            "price": round(current_price, 6),
            "volume_spike": round(vol_spike, 2)
        }
    return None

async def signal_generator(websocket: WebSocket):
    await websocket.accept()
    while True:
        for symbol in PAIRS:
            signal = await detect_reversal(symbol)
            if signal:
                await websocket.send_text(json.dumps(signal))
        await asyncio.sleep(2)

@app.websocket("/ws")
async def stream(websocket: WebSocket):
    await signal_generator(websocket)

@app.get("/")
def home():
    return {
        "engine": "ReversalEdge v2",
        "data_source": "Binance API",
        "status": "LIVE",
        "pairs": len(PAIRS)
    }
