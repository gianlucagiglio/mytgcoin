import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
import pandas as pd
import os

# Configurazioni
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL_PRICE = "https://api.coingecko.com/api/v3/simple/price"
API_URL_MARKET = "https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
CURRENCY = "usd"
DEFAULT_COINS = ["pepe-unchained", "dogecoin", "shiba-inu", "bitcoin", "ethereum"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Messaggio di benvenuto con pulsanti per coin."""
    # Creazione pulsanti per coin e comandi globali
    buttons = [
        [InlineKeyboardButton(f"{coin.capitalize()} Price", callback_data=f"price {coin}"),
         InlineKeyboardButton(f"{coin.capitalize()} RSI", callback_data=f"rsi {coin}")]
        for coin in DEFAULT_COINS
    ]
    # Aggiungi i pulsanti per tutte le coin
    buttons.append([
        InlineKeyboardButton("All Prices", callback_data="all_prices"),
        InlineKeyboardButton("All RSI", callback_data="all_rsi")
    ])

    # Messaggio iniziale con pulsanti
    await update.message.reply_text(
        "Click a button to get the price or RSI for a specific coin, or get data for all coins:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce i clic sui pulsanti."""
    query = update.callback_query
    await query.answer()

    # Estrae il comando (price, rsi, all_prices, all_rsi)
    data = query.data.split()
    command = data[0]
    coin = data[1] if len(data) > 1 else None

    if command == "price" and coin:
        price = await fetch_price(coin)
        message = f"{coin.capitalize()} Price: ${price}" if price else f"Could not fetch price for {coin}."
    elif command == "rsi" and coin:
        rsi = await fetch_rsi(coin)
        message = f"{coin.capitalize()} RSI: {rsi}" if rsi else f"Could not fetch RSI for {coin}."
    elif command == "all_prices":
        message = await fetch_all_prices()
    elif command == "all_rsi":
        message = await fetch_all_rsi()
    else:
        message = "Invalid command."

    # Modifica il messaggio con il risultato
    await query.edit_message_text(message)

async def fetch_price(coin: str) -> str:
    """Recupera il prezzo corrente di una coin."""
    try:
        response = requests.get(API_URL_PRICE, params={"ids": coin, "vs_currencies": CURRENCY}, timeout=10)
        response.raise_for_status()
        return response.json().get(coin, {}).get(CURRENCY)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price for {coin}: {e}")
        return None

async def fetch_rsi(coin: str) -> str:
    """Calcola l'RSI per una coin."""
    try:
        response = requests.get(API_URL_MARKET.format(coin=coin), params={"vs_currency": CURRENCY, "days": 14}, timeout=10)
        response.raise_for_status()
        data = response.json()
        prices = [x[1] for x in data.get("prices", [])]
        if len(prices) < 14:
            return None
        df = pd.Series(prices)
        delta = df.diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0.0).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 2)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSI for {coin}: {e}")
        return None

async def fetch_all_prices() -> str:
    """Recupera i prezzi di tutte le coin con ritardo tra le richieste."""
    message = "Prices for all coins:\n"
    for coin in DEFAULT_COINS:
        price = await fetch_price(coin)
        message += f"{coin.capitalize()}: ${price}\n" if price else f"{coin.capitalize()}: Price unavailable\n"
        await asyncio.sleep(1)  # Ritardo di 1 secondo per rispettare i limiti API
    return message

async def fetch_all_rsi() -> str:
    """Recupera l'RSI di tutte le coin con ritardo tra le richieste."""
    message = "RSI for all coins:\n"
    for coin in DEFAULT_COINS:
        rsi = await fetch_rsi(coin)
        message += f"{coin.capitalize()}: RSI {rsi}\n" if rsi else f"{coin.capitalize()}: RSI unavailable\n"
        await asyncio.sleep(1)  # Ritardo di 1 secondo per rispettare i limiti API
    return message

def main():
    """Avvia il bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Aggiunge i gestori dei comandi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Avvia il webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", "8443")),
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL')}/{TELEGRAM_TOKEN}"
    )

if __name__ == "__main__":
    main()
