from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import pandas as pd
import ta

# Inserisci il token del bot di Telegram
TELEGRAM_TOKEN = "YOUR_TELEGRAM_TOKEN"
COIN_SYMBOL = "pepe-unchained"
API_URL = f"https://api.coingecko.com/api/v3/coins/{COIN_SYMBOL}/market_chart?vs_currency=usd&days=1"

def get_price():
    response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={COIN_SYMBOL}&vs_currencies=usd")
    data = response.json()
    return data[COIN_SYMBOL]["usd"]

def get_rsi():
    response = requests.get(API_URL)
    data = response.json()
    prices = [x[1] for x in data["prices"]]  # Estrai i prezzi
    df = pd.DataFrame(prices, columns=["close"])
    rsi = ta.momentum.RSIIndicator(df["close"]).rsi()  # Calcola RSI
    return round(rsi.iloc[-1], 2)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome! Use /price to get the current price or /rsi to get the RSI of Pepe Unchained Coin.")

def price(update: Update, context: CallbackContext) -> None:
    price = get_price()
    update.message.reply_text(f"The current price of Pepe Unchained Coin is ${price}")

def rsi(update: Update, context: CallbackContext) -> None:
    rsi = get_rsi()
    update.message.reply_text(f"The RSI of Pepe Unchained Coin is {rsi}")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("price", price))
    dispatcher.add_handler(CommandHandler("rsi", rsi))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
