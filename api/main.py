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
        # Fetch real 1m klines
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}&interval=1m&limit=11"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if len(data) < 11:
                    return None
                prices = [float(k[4]) for k in data]  # close prices
                volumes = [float(k[5]) for k in data]  # volumes

        if symbol not in price_history:
            price_history[symbol] = []
        price_history[symbol].append((prices[-1], volumes[-1]))
        price_history[symbol] = price_history[symbol][-VOLUME_WINDOW:]

        if len(price_history[symbol]) < VOLUME_WINDOW:
            return None

        recent = price_history[symbol]
        hist_prices = [p[0] for p in recent[:-1]]
        hist_vols = [p[1] for p in recent[:-1]]
        curr_price = recent[-1][0]
        curr_vol = recent[-1][1]

        avg_vol = sum(hist_vols) / len(hist_vols)
        price_change = ((curr_price - hist_prices[-1]) / hist_prices[-1]) * 100

        if curr_vol > avg_vol * VOLUME_SPIKE_THRESHOLD and abs(price_change) > PRICE_CHANGE_THRESHOLD:
            confidence = min(98, int(70 + abs(price_change) * 8 + (curr_vol / avg_vol - 1) * 15))
            signal_type = "buy" if price_change > 0 else "sell"

            return {
                "pair": symbol.upper().replace("USDT", "/USDT"),
                "type": signal_type,
                "confidence": confidence,
                "time": datetime.now().isoformat(),
                "price": round(curr_price, 4),
                "volume_spike": round(curr_vol / avg_vol, 2)
            }
    except Exception as e:
        print(f"Error: {e}")
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
