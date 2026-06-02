import requests

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# Prevent duplicate alerts
sent_signals = set()


def send_telegram_alert(symbol, signal, confidence):

    key = f"{symbol}_{signal}_{round(confidence)}"

    # Skip duplicate alert
    if key in sent_signals:
        return

    sent_signals.add(key)

    msg = f"""
🚨 AI TRADING SIGNAL

Symbol: {symbol}
Signal: {signal}
Confidence: {confidence:.2f}%
"""

    try:

        response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=10
        )

        if response.status_code == 200:
            print(f"Telegram alert sent for {symbol}")
        else:
            print(
                f"Telegram API Error: "
                f"{response.status_code}"
            )

    except Exception as e:

        print("Telegram Error:", e)