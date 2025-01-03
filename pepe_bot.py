import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from flask import Flask, request
import pandas as pd
import os

# === CONFIGURATION ===
# CoinGecko API
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
COINS = ["pepe-unchained", "fartcoin", "dogecoin", "shiba-inu"]  # Add more meme coins
CURRENCY = "usd"

# Telegram Bot Configuration
TELEGRAM_TOKEN = "7641508342:AAFMHZKoyselK1GX12-azOdjb6rMNeHeEWk"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
RATE_LIMIT_DELAY = 60  # Delay in seconds for API rate limits

# Initialize Sentiment Analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()

# Initialize Flask App
app = Flask(__name__)

# === FUNCTIONS ===
def fetch_coin_price(coin):
    """Fetch the current price of a coin from CoinGecko."""
    try:
        response = requests.get(COINGECKO_URL, params={"ids": coin, "vs_currencies": CURRENCY}, timeout=10)
        response.raise_for_status()
        return response.json().get(coin, {}).get(CURRENCY)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price for {coin}: {e}")
        return None

def fetch_historical_data(coin):
    """Fetch historical price data for RSI calculation."""
    try:
        response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart",
            params={"vs_currency": CURRENCY, "days": "14", "interval": "daily"},
            timeout=10
        )
        response.raise_for_status()
        prices = [point[1] for point in response.json().get("prices", [])]
        return prices
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical data for {coin}: {e}")
        return [100] * 14  # Default fallback

def calculate_rsi(prices, window=14):
    """Calculate the RSI value from price data."""
    prices_series = pd.Series(prices)
    delta = prices_series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]  # Most recent RSI value

def send_telegram_message(chat_id, message):
    """Send a message to Telegram."""
    try:
        response = requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

# === TELEGRAM WEBHOOK HANDLER ===
@app.route(f"/telegram/{TELEGRAM_TOKEN}", methods=["POST"])
def handle_telegram():
    """Handle incoming updates from Telegram."""
    data = request.json
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.startswith("/price"):
            coin = text.split(" ", 1)[1].lower() if len(text.split(" ")) > 1 else None
            if coin:
                price = fetch_coin_price(coin)
                if price is not None:
                    prices = fetch_historical_data(coin)
                    rsi = calculate_rsi(prices)
                    message = f"Price of {coin}: ${price}\nRSI: {rsi:.2f}"
                else:
                    message = f"Could not fetch data for {coin}. Ensure it's supported."
            else:
                message = "Please specify a coin. Example: /price pepe-unchained"
            send_telegram_message(chat_id, message)

    return "OK"

# === MAIN FUNCTION ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default port for Flask
    app.run(host="0.0.0.0", port=port)
