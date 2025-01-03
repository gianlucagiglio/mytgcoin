from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
import os

# Configurazioni
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL_PRICE = "https://api.coingecko.com/api/v3/simple/price"
API_URL_MARKET = "https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
CURRENCY = "usd"
DEFAULT_COINS = ["pepe-unchained", "dogecoin", "shiba-inu", "bitcoin", "ethereum"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Messaggio di benvenuto con pulsanti."""
    buttons = [
        [InlineKeyboardButton(f"{coin.capitalize()} Price", callback_data=f"price {coin}"),
         InlineKeyboardButton(f"{coin.capitalize()} RSI", callback_data=f"rsi {coin}")]
        for coin in DEFAULT_COINS
    ]
    await update.message.reply_text(
        "Click a button to get the price or RSI for a coin:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce i clic sui pulsanti."""
    query = update.callback_query
    await query.answer()

    command, coin = query.data.split()
    if command == "price":
        price = await fetch_price(coin)
        print(f"clicked price for {coin}")
        message = f"{coin.capitalize()} Price: ${price}\n" if price else f"Could not fetch price for {coin}."
    elif command == "rsi":
        rsi = await fetch_rsi(coin)
        print(f"clicked rsi for {coin}")
        message = f"{coin.capitalize()} RSI: {rsi}\n" if rsi else f"Could not fetch RSI for {coin}."

    await query.edit_message_text(message)

async def fetch_price(coin: str) -> str:
    """Recupera il prezzo corrente di una coin."""
    try:
        response = requests.get(API_URL_PRICE, params={"ids": coin, "vs_currencies": CURRENCY}, timeout=10)
        response.raise_for_status()
        print(f"result price for {coin}")
        return response.json().get(coin, {}).get(CURRENCY)
    except Exception as e:
        print(f"Error fetching price for {coin}: {e}")
        return None

async def fetch_rsi(coin: str) -> str:
    """Calcola l'RSI di una coin."""
    try:
        response = requests.get(API_URL_MARKET.format(coin=coin), params={"vs_currency": CURRENCY, "days": 14}, timeout=10)
        response.raise_for_status()
        data = response.json()
        prices = [x[1] for x in data.get("prices", [])]
        if len(prices) < 14:  # Controllo per evitare errori nel calcolo RSI
            return None
        df = pd.Series(prices)
        delta = df.diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0.0).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 2)
    except Exception as e:
        print(f"Error fetching RSI for {coin}: {e}")
        return None

def main():
    """Avvia il bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", "8443")),
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL')}/{TELEGRAM_TOKEN}"
    )

if __name__ == "__main__":
    main()
