from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import pandas as pd
import ta
import threading
import time


# Inserisci il token del bot di Telegram
TELEGRAM_TOKEN = "7641508342:AAFMHZKoyselK1GX12-azOdjb6rMNeHeEWk"
COIN_SYMBOL = "pepe-unchained"
API_URL_PRICE = f"https://api.coingecko.com/api/v3/simple/price?ids={COIN_SYMBOL}&vs_currencies=usd"
API_URL_MARKET = f"https://api.coingecko.com/api/v3/coins/{COIN_SYMBOL}/market_chart?vs_currency=usd&days=1"

# Variabili globali per prezzo e RSI
latest_price = None
latest_rsi = None

def fetch_data():
    global latest_price, latest_rsi
    while True:
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

        # Attendi 60 secondi prima di aggiornare di nuovo
        time.sleep(60)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome! Use /price to get the current price or /rsi to get the RSI of Pepe Unchained Coin.")

def price(update: Update, context: CallbackContext) -> None:
    if latest_price is not None:
        update.message.reply_text(f"The current price of Pepe Unchained Coin is ${latest_price}")
    else:
        update.message.reply_text("Price data is not available at the moment. Please try again later.")

def rsi(update: Update, context: CallbackContext) -> None:
    if latest_rsi is not None:
        update.message.reply_text(f"The RSI of Pepe Unchained Coin is {latest_rsi}")
    else:
        update.message.reply_text("RSI data is not available at the moment. Please try again later.")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("price", price))
    dispatcher.add_handler(CommandHandler("rsi", rsi))

    # Thread separato per aggiornare i dati periodicamente
    data_thread = threading.Thread(target=fetch_data, daemon=True)
    data_thread.start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
