from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import pandas as pd
import os

# Configurazioni
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL_PRICE = "https://api.coingecko.com/api/v3/simple/price"
API_URL_MARKET = "https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
CURRENCY = "usd"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Messaggio di benvenuto."""
    await update.message.reply_text(
        "Welcome! Use /info <coin> to get price, 24h change percentage, and RSI of a cryptocurrency.\n"
        "Example: /info bitcoin"
    )

async def fetch_coin_info(coin: str) -> dict:
    """Recupera prezzo corrente, variazione percentuale e RSI per una coin."""
    try:
        # Recupera prezzo e variazione percentuale
        price_response = requests.get(API_URL_PRICE, params={"ids": coin, "vs_currencies": CURRENCY, "include_24hr_change": "true"}, timeout=10)
        price_response.raise_for_status()
        price_data = price_response.json().get(coin, {})
        price = price_data.get(CURRENCY)
        change_24h = round(price_data.get(f"{CURRENCY}_24h_change", 0), 2)

        # Recupera RSI
        rsi_response = requests.get(API_URL_MARKET.format(coin=coin), params={"vs_currency": CURRENCY, "days": 14}, timeout=10)
        rsi_response.raise_for_status()
        market_data = rsi_response.json()
        prices = [x[1] for x in market_data.get("prices", [])]
        if len(prices) >= 14:
            df = pd.Series(prices)
            delta = df.diff()
            gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0.0).rolling(window=14).mean()
            rs = gain / loss
            rsi = round(100 - (100 / (1 + rs.iloc[-1])), 2)
        else:
            rsi = None

        return {"price": price, "change_24h": change_24h, "rsi": rsi}
    except Exception as e:
        print(f"Error fetching info for {coin}: {e}")
        return None

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce il comando /info <coin>."""
    coin = " ".join(context.args).lower()
    if not coin:
        await update.message.reply_text("Please specify a coin. Example: /info bitcoin")
        return

    info = await fetch_coin_info(coin)
    if not info or info.get("price") is None:
        await update.message.reply_text(f"Could not fetch data for {coin}. Please check the coin name.")
        return

    price = info.get("price")
    change_24h = info.get("change_24h")
    rsi = info.get("rsi", "Unavailable")
    await update.message.reply_text(
        f"Information for {coin.capitalize()}:\n"
        f"Price: ${price}\n"
        f"24h Change: {change_24h}%\n"
        f"RSI: {rsi}"
    )

def main():
    """Avvia il bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Aggiunge i gestori dei comandi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info))

    # Avvia il webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", "8443")),
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL')}/{TELEGRAM_TOKEN}"
    )

if __name__ == "__main__":
    main()
