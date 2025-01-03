from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import pandas as pd
import ta
import os

# Ottieni il token del bot dalle variabili d'ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
COIN_SYMBOL = "pepe-unchained"
API_URL_PRICE = f"https://api.coingecko.com/api/v3/simple/price?ids={COIN_SYMBOL}&vs_currencies=usd"
API_URL_MARKET = f"https://api.coingecko.com/api/v3/coins/{COIN_SYMBOL}/market_chart?vs_currency=usd&days=14"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome! Use /price to get the current price or /rsi to get the RSI of Pepe Unchained Coin."
    )

# ... (le funzioni price e rsi rimangono invariate)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("rsi", rsi))

    # Ottieni l'URL del tuo servizio su Render
    your_render_url = os.getenv("RENDER_EXTERNAL_URL")

    # Avvia l'applicazione utilizzando webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", "8443")),
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{your_render_url}/{TELEGRAM_TOKEN}"
    )

if __name__ == "__main__":
    main()
