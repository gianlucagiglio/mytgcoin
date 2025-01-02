import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
from flask import Flask, request

# === CONFIGURATION ===
# CoinGecko and Yahoo Finance APIs
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
COINS = ["dogecoin", "shiba-inu","pepe-unchained","fartcoin", "kekius-maximus"]  # Add more meme coins here
CURRENCY = "usd"
RATE_LIMIT_DELAY = 60  # Delay in seconds to handle API rate limits

# Telegram Bot Configuration
TELEGRAM_TOKEN = "7641508342:AAFMHZKoyselK1GX12-azOdjb6rMNeHeEWk"
TELEGRAM_CHAT_ID = "19963832"

# Reddit API (Optional for Sentiment Analysis)
REDDIT_API_URL_TEMPLATE = "https://www.reddit.com/search.json?q={query}&sort=top&t=day"
HEADERS = {"User-Agent": "CryptoStockTrendBot"}

# Initialize Sentiment Analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()

# Initialize Flask App
app = Flask(__name__)

# === FUNCTIONS ===
# Check if a coin is supported by CoinGecko
def is_coin_supported(coin):
    try:
        response = requests.get(f"https://api.coingecko.com/api/v3/coins/list", timeout=10)
        response.raise_for_status()
        coins = response.json()
        return any(c["id"] == coin for c in coins)
    except requests.exceptions.RequestException as e:
        print(f"Error checking support for {coin}: {e}")
        return False

# Fetch Coin Prices from CoinGecko with Rate Limiting
def fetch_coin_prices():
    prices = {}
    for coin in COINS:
        if not is_coin_supported(coin):
            print(f"Coin not supported by CoinGecko: {coin}")
            prices[coin] = None
            continue

        try:
            response = requests.get(COINGECKO_URL, params={"ids": coin, "vs_currencies": CURRENCY}, timeout=10)
            if response.status_code == 429:  # Rate limit exceeded
                print("Rate limit hit. Waiting for cooldown...")
                time.sleep(RATE_LIMIT_DELAY)
                response = requests.get(COINGECKO_URL, params={"ids": coin, "vs_currencies": CURRENCY}, timeout=10)
            response.raise_for_status()
            prices[coin] = response.json().get(coin, {}).get(CURRENCY, None)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching price for {coin}: {e}")
            prices[coin] = None
    return prices

# Fetch Top Posts from Reddit for Sentiment Analysis
def fetch_reddit_posts(coin):
    query = coin.replace("-", " ")  # Adapt coin name for search
    try:
        response = requests.get(REDDIT_API_URL_TEMPLATE.format(query=query), headers=HEADERS, timeout=10)
        response.raise_for_status()
        posts = response.json().get("data", {}).get("children", [])
        return [post["data"].get("title", "") for post in posts]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Reddit posts for {coin}: {e}")
        return []

# Analyze Sentiment of Reddit Posts
def analyze_sentiment(posts):
    sentiment_scores = []
    for post in posts:
        score = sentiment_analyzer.polarity_scores(post)["compound"]
        sentiment_scores.append(score)
    return sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

# Send Notification to Telegram using requests
def send_telegram_message(message):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(telegram_url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")

# Handle Telegram Bot Commands
@app.route(f"/telegram/{TELEGRAM_TOKEN}", methods=["POST"])
def handle_telegram():
    data = request.json
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.startswith("/prices"):
            prices = fetch_coin_prices()
            message = "\U0001F4B0 Current Prices:\n"
            for coin, price in prices.items():
                if price is not None:
                    message += f"- {coin.capitalize()}: ${price}\n"
                else:
                    message += f"- {coin.capitalize()}: Price unavailable or unsupported\n"
            send_telegram_message(message)

        elif text.startswith("/sentiment"):
            coin = text.split(" ", 1)[1].lower() if len(text.split(" ")) > 1 else None
            if coin and is_coin_supported(coin):
                reddit_posts = fetch_reddit_posts(coin)
                sentiment_score = analyze_sentiment(reddit_posts)
                message = f"\U0001F4AC Sentiment for {coin.capitalize()}: {sentiment_score:.2f}"
            else:
                message = "Coin not supported or invalid."
            send_telegram_message(message)

    return "OK"

# Main Function
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
    
