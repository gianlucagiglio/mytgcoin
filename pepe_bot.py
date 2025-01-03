from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
import requests
import pandas as pd
import ta

# Inserisci il token del bot di Telegram
TELEGRAM_TOKEN = "7641508342:AAFMHZKoyselK1GX12-azOdjb6rMNeHeEWk"
COIN_SYMBOL = "pepe-unchained"
API_URL_PRICE = f"https://api.coingecko.com/api/v3/simple/price?ids={COIN_SYMBOL}&vs_currencies=usd"
API_URL_MARKET = f"https://api.coingecko.com/api/v3/coins/{COIN_SYMBOL}/market_chart?vs_currency=usd&days=1"

# Variabili globali per prezzo e RSI
latest_price = None
latest_rsi = None

def fetch_data(context):
    global latest_price, latest_rsi
    try:
        # Aggiorna il prezzo
        response_price = requests.get(API_URL_PRICE)
        latest_price = response_price.json()[COIN_SYMBOL]["usd"]

        # Aggiorna RSI
        response_market = requests.get(API_URL_MARKET)
        data = response_market.json()
        prices = [x[1] for x in data["prices"]]
        df = pd.DataFrame(prices, columns=["close"])
        latest_rsi = round(ta.momentum.RSIIndicator(df["close"]).rsi().iloc[-1], 2)
    except Exception as e:
        print(f"Error fetching data: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome! Use /price to get the current price or /rsi to get the RSI of Pepe Unchained Coin.")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if latest_price is not None:
        await update.message.reply_text(f"The current price of Pepe Unchained Coin is ${latest_price}")
    else:
        await update.message.reply_text("Price data is not available at the moment. Please try again later.")

async def rsi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if latest_rsi is not None:
        await update.message.reply_text(f"The RSI of Pepe Unchained Coin is {latest_rsi}")
    else:
        await update.message.reply_text("RSI data is not available at the moment. Please try again later.")

def main():
    # Crea l'applicazione del bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Aggiungi i gestori dei comandi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("rsi", rsi))

    # Configura JobQueue per fetch_data
    job_queue = application.job_queue
    job_queue.run_repeating(fetch_data, interval=60, first=0)

    # Avvia il bot
    application.run_polling()

if __name__ == "__main__":
    main()
