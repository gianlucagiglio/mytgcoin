from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import pandas as pd
import ta
import os

# Token di Telegram e configurazioni API
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL_PRICE = "https://api.coingecko.com/api/v3/simple/price"
API_URL_MARKET = "https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
CURRENCY = "usd"

# Lista di coin predefinite
DEFAULT_COINS = ["pepe-unchained", "dogecoin", "shiba-inu", "bitcoin", "ethereum"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Messaggio di benvenuto con collegamenti per ciascuna coin."""
    # Creare pulsanti per ciascuna coin
    buttons = [
        [
            InlineKeyboardButton(f"{coin.capitalize()} Price", callback_data=f"price {coin}"),
            InlineKeyboardButton(f"{coin.capitalize()} RSI", callback_data=f"rsi {coin}")
        ]
        for coin in DEFAULT_COINS
    ]

    # Messaggio iniziale
    await update.message.reply_text(
        "Welcome! Use the buttons below to get the price or RSI for each default coin.\n"
        "You can also type /price <coin> or /rsi <coin> manually.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restituisce il prezzo di una o più coin."""
    coin = " ".join(context.args).lower() if context.args else None
    if not coin:
        message = "Fetching prices for all default coins:\n"
        for coin in DEFAULT_COINS:
            price = await fetch_price(coin)
            message += f"{coin.capitalize()}: ${price}\n" if price else f"{coin.capitalize()}: Price unavailable\n"
    else:
        price = await fetch_price(coin)
        message = f"{coin.capitalize()}: ${price}\n" if price else f"Coin '{coin}' not found or price unavailable."
    
    await update.message.reply_text(message)

async def rsi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restituisce l'RSI di una o più coin."""
    coin = " ".join(context.args).lower() if context.args else None
    if not coin:
        message = "Fetching RSI for all default coins:\n"
        for coin in DEFAULT_COINS:
            rsi = await fetch_rsi(coin)
            message += f"{coin.capitalize()}: RSI {rsi}\n" if rsi else f"{coin.capitalize()}: RSI unavailable\n"
    else:
        rsi = await fetch_rsi(coin)
        message = f"{coin.capitalize()}: RSI {rsi}\n" if rsi else f"Coin '{coin}' not found or RSI unavailable."
    
    await update.message.reply_text(message)

async def fetch_price(coin: str) -> str:
    """Recupera il prezzo corrente di una coin."""
    try:
        response = requests.get(API_URL_PRICE, params={"ids": coin, "vs_currencies": CURRENCY}, timeout=10)
        response.raise_for_status()
        return response.json().get(coin, {}).get(CURRENCY)
    except Exception as e:
        print(f"Error fetching price for {coin}: {e}")
        return None

async def fetch_rsi(coin: str) -> str:
    """Calcola l'RSI per una coin."""
    try:
        response = requests.get(API_URL_MARKET.format(coin=coin), params={"vs_currency": CURRENCY, "days": 14}, timeout=10)
        response.raise_for_status()
        data = response.json()
        prices = [x[1] for x in data.get("prices", [])]
        df = pd.DataFrame(prices, columns=["close"])
        rsi = ta.momentum.RSIIndicator(df["close"]).rsi()
        return round(rsi.iloc[-1], 2)
    except Exception as e:
        print(f"Error fetching RSI for {coin}: {e}")
        return None

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce i pulsanti cliccati."""
    query = update.callback_query
    await query.answer()

    command, coin = query.data.split()
    if command == "price":
        price = await fetch_price(coin)
        message = f"{coin.capitalize()} Price: ${price}\n" if price else f"Coin '{coin}' not found or price unavailable."
    elif command == "rsi":
        rsi = await fetch_rsi(coin)
        message = f"{coin.capitalize()} RSI: {rsi}\n" if rsi else f"Coin '{coin}' not found or RSI unavailable."
    
    await query.edit_message_text(message)

def main():
    """Avvia il bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("rsi", rsi))
    application.add_handler(CommandHandler("callback", handle_callback))

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", "8443")),
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL')}/{TELEGRAM_TOKEN}"
    )

if __name__ == "__main__":
    main()
