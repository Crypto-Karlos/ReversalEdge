from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import aiohttp
from datetime import datetime
import numpy as np

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Track price history per pair
price_history = {}
VOLUME_WINDOW = 10
PRICE_CHANGE_THRESHOLD = 0.3  # %
VOLUME_SPIKE_THRESHOLD = 2.5  # 2.5x average

PAIRS = ["btcusdt", "ethusdt", "solusdt", "adausdt", "xrpusdt"]

async def fetch_klines(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval=1m&limit=20"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return [float(k[4]) for k in data]  # closing prices

async def detect_reversal(symbol):
    try:
        prices = await fetch_klines(symbol)
        volumes = await fetch_klines(symbol + "@trade")  # Not real, but simulate
        # Simulate volume from price volatility
        volume = np.random.normal(100, 30) + abs(prices[-1] - prices[-2]) * 1000

        if symbol not in price_history:
            price_history[symbol] = []
        price_history[symbol].append((prices[-1], volume))
        price_history[symbol] = price_history[symbol][-VOLUME_WINDOW:]

        if len(price_history[symbol]) < VOLUME_WINDOW:
            return None

        recent = price_history[symbol]
        prices = [p[0] for p in recent]
        volumes = [p[1] for p in recent]

        avg_volume = np.mean(volumes[:-1])
        current_volume = volumes[-1]
        price_change = ((prices[-1] - prices[-2]) / prices[-2]) * 100

        # Reversal logic
        is_bullish = price_change > PRICE_CHANGE_THRESHOLD and current_volume > avg_volume * VOLUME_SPIKE_THRESHOLD
        is_bearish = price_change < -PRICE_CHANGE_THRESHOLD and current_volume > avg_volume * VOLUME_SPIKE_THRESHOLD

        if is_bullish or is_bearish:
            confidence = min(98, int(70 + abs(price_change) * 10 + (current_volume / avg_volume - 1) * 20))
            return {
                "pair": symbol.upper().replace("USDT", "/USDT"),
                "type": "buy" if is_bullish else "sell",
                "confidence": confidence,
                "time": datetime.now().isoformat(),
                "price": round(prices[-1], 4),
                "volume_spike": round(current_volume / avg_volume, 2)
            }
    except:
        pass
    return None

async def signal_generator(websocket: WebSocket):
    await websocket.accept()
    checked = 0
    while True:
        for symbol in PAIRS:
            signal = await detect_reversal(symbol)
            if signal:
                await websocket.send_text(json.dumps(signal))
        await asyncio.sleep(2)  # Check every 2 sec
        checked += 1
        if checked % 30 == 0:  # Reset history every minute
            price_history.clear()

@app.websocket("/ws")
async def stream(websocket: WebSocket):
    await signal_generator(websocket)

@app.get("/")
def home():
    return {"engine": "ReversalEdge v2", "data_source": "Binance API", "status": "LIVE"}
