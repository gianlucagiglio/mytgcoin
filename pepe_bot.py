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
    """Messaggio di benvenuto con pulsanti per info di ogni coin."""
    # Creazione pulsanti per ogni coin
    buttons = [
        [InlineKeyboardButton(f"{coin.capitalize()} Info", callback_data=f"info {coin}")]
        for coin in DEFAULT_COINS
    ]

    # Messaggio iniziale con pulsanti
    await update.message.reply_text(
        "Click a button to get detailed info (Price, 24h Change, RSI) for a specific coin, "
        "or type /info <coin> to get data manually.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce i clic sui pulsanti."""
    query = update.callback_query
    await query.answer()

    # Estrae il comando "info" e la coin
    data = query.data.split()
    if len(data) == 2 and data[0] == "info":
        coin = data[1]
        message = await fetch_info(coin)
    else:
        message = "Invalid command."

    # Modifica il messaggio con il risultato
    await query.edit_message_text(message)

async def fetch_info(coin: str) -> str:
    """Recupera il prezzo, il cambio percentuale e l'RSI per una coin."""
    try:
        # Ottieni prezzo e cambio percentuale
        response = requests.get(
            API_URL_PRICE,
            params={"ids": coin, "vs_currencies": CURRENCY, "include_24hr_change": "true"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json().get(coin, {})
        price = data.get(CURRENCY)
        change_24h = data.get(f"{CURRENCY}_24h_change")

        # Calcola RSI
        rsi = await fetch_rsi(coin)

        # Costruisci il messaggio di risposta
        if price is not None and change_24h is not None and rsi is not None:
            return (f"**{coin.capitalize()} Info:**\n"
                    f"Price: ${price:.2f}\n"
                    f"24h Change: {change_24h:.2f}%\n"
                    f"RSI: {rsi:.2f}")
        else:
            return f"Could not fetch complete info for {coin}."
    except requests.exceptions.RequestException as e:
        print(f"Error fetching info for {coin}: {e}")
        return f"Could not fetch info for {coin}."

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

async def manual_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce il comando manuale /info <coin>."""
    coin = " ".join(context.args).lower()
    if not coin:
        await update.message.reply_text("Please specify a coin. Example: /info bitcoin")
        return

    message = await fetch_info(coin)
    await update.message.reply_text(message)

def main():
    """Avvia il bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Aggiunge i gestori dei comandi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", manual_info))
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
