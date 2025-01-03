from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import pandas as pd
import ta

# Inserisci il token del bot di Telegram
TELEGRAM_TOKEN = "7641508342:AAFMHZKoyselK1GX12-azOdjb6rMNeHeEWk"
COIN_SYMBOL = "pepe-unchained"
API_URL_PRICE = f"https://api.coingecko.com/api/v3/simple/price?ids={COIN_SYMBOL}&vs_currencies=usd"
API_URL_MARKET = f"https://api.coingecko.com/api/v3/coins/{COIN_SYMBOL}/market_chart?vs_currency=usd&days=1"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Messaggio di benvenuto."""
    await update.message.reply_text(
        "Welcome! Use /price to get the current price or /rsi to get the RSI of Pepe Unchained Coin."
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Invia il prezzo corrente."""
    try:
        response = requests.get(API_URL_PRICE)
        response.raise_for_status()
        data = response.json()
        current_price = data[COIN_SYMBOL]["usd"]
        await update.message.reply_text(f"The current price of Pepe Unchained Coin is ${current_price}")
    except Exception as e:
        await update.message.reply_text(f"Error fetching price data: {e}")

async def rsi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Invia l'RSI corrente."""
    try:
        response = requests.get(API_URL_MARKET)
        response.raise_for_status()
        data = response.json()
        prices = [x[1] for x in data["prices"]]
        df = pd.DataFrame(prices, columns=["close"])
        rsi = ta.momentum.RSIIndicator(df["close"]).rsi()
        current_rsi = round(rsi.iloc[-1], 2)
        await update.message.reply_text(f"The RSI of Pepe Unchained Coin is {current_rsi}")
    except Exception as e:
        await update.message.reply_text(f"Error fetching RSI data: {e}")

def main():
    """Avvia il bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Aggiungi i gestori dei comandi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("rsi", rsi))

    # Avvia il bot in polling
    application.run_polling()

if __name__ == "__main__":
    main()
