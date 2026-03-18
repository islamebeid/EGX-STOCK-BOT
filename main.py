import os
import re
import time
import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup

CHECK_INTERVAL_SECONDS = 300

# More sensitive move alerts
WATCHLIST_MOVE_ALERT_PCT = 2.5
PORTFOLIO_MOVE_ALERT_PCT = 3.0

PORTFOLIO_FILE = "portfolio.json"
STATE_FILE = "state.json"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

WATCHLIST = {

    # ===== PORTFOLIO =====

    "BSB": {
        "buy_price": 1.91,
        "quantity": 265,
        "target_pct": 12,
        "stop_loss_pct": 6,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/BSB/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/BSB/news",
    },

    "ISPH": {
        "buy_price": 12.42,
        "quantity": 415,
        "target_pct": 12,
        "stop_loss_pct": 7,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/ISPH/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/ISPH/news",
    },

    "OLFI": {
        "buy_price": 21.80,
        "quantity": 136,
        "target_pct": 10,
        "stop_loss_pct": 6,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/OLFI/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/OLFI/news",
    },

    "RMDA": {
        "buy_price": 4.69,
        "quantity": 1073,
        "target_pct": 12,
        "stop_loss_pct": 6,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/RMDA/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/RMDA/news",
    },

    "TMGH": {
        "buy_price": 85.93,
        "quantity": 29,
        "target_pct": 10,
        "stop_loss_pct": 6,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/TMGH/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/TMGH/news",
    },

    # ===== WATCHING ONLY =====

    "AMOC": {
        "buy_price": 0,
        "quantity": 0,
        "target_pct": 10,
        "stop_loss_pct": 5,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/AMOC/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/AMOC/news",
    },

    "ATLC": {
        "buy_price": 0,
        "quantity": 0,
        "target_pct": 10,
        "stop_loss_pct": 5,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/ATLC/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/ATLC/news",
    },

    "CSAG": {
        "buy_price": 0,
        "quantity": 0,
        "target_pct": 10,
        "stop_loss_pct": 5,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/CSAG/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/CSAG/news",
    },

    "HELI": {
        "buy_price": 0,
        "quantity": 0,
        "target_pct": 10,
        "stop_loss_pct": 5,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/HELI/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/HELI/news",
    },

    "MFPC": {
        "buy_price": 0,
        "quantity": 0,
        "target_pct": 10,
        "stop_loss_pct": 5,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/MFPC/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/MFPC/news",
    },

    "MICH": {
        "buy_price": 0,
        "quantity": 0,
        "target_pct": 10,
        "stop_loss_pct": 5,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/MICH/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/MICH/news",
    },

    "NHPS": {
        "buy_price": 0,
        "quantity": 0,
        "target_pct": 10,
        "stop_loss_pct": 5,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/NHPS/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/NHPS/news",
    },

    "ORAS": {
        "buy_price": 0,
        "quantity": 0,
        "target_pct": 10,
        "stop_loss_pct": 5,
        "mubasher_url": "https://english.mubasher.info/markets/EGX/stocks/ORAS/",
        "news_url": "https://english.mubasher.info/markets/EGX/stocks/ORAS/news",
    },
}


def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing Telegram secrets.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}

    try:
        r = requests.post(url, data=payload, timeout=20)
        print("Telegram:", r.status_code)
        print(r.text)
        return r.status_code == 200
    except Exception as e:
        print("Telegram send error:", e)
        return False


def get_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def clean_num(x):
    return float(str(x).replace(",", "").replace("%", "").strip())


def parse_mubasher_price(url):
    soup = get_soup(url)
    text = soup.get_text("\n", strip=True)

    pattern = re.compile(
        r"Last update:\s*(.*?)\s+market time\.\s*"
        r"([\d,]+(?:\.\d+)?)\s*"
        r"([+-]?[\d,]+(?:\.\d+)?)\s*"
        r"([+-]?[\d,]+(?:\.\d+)?%)",
        re.IGNORECASE | re.DOTALL
    )
    m = pattern.search(text)
    if not m:
        raise ValueError("Mubasher price block not found")

    return {
        "source": "mubasher",
        "price": clean_num(m.group(2)),
        "change": clean_num(m.group(3)),
        "pct_change": m.group(4),
        "last_update": m.group(1).strip(),
    }


def get_price(symbol, stock):
    try:
        quote = parse_mubasher_price(stock["mubasher_url"])
        return {
            "price": quote["price"],
            "raw": [quote]
        }
    except Exception as e:
        print(symbol, "Mubasher error:", e)
        return None


def fetch_news_items(symbol, news_url):
    soup = get_soup(news_url)
    items = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(" ", strip=True)

        if not title or len(title) < 15:
            continue
        if "/news/" not in href:
            continue

        if href.startswith("/"):
            href = "https://english.mubasher.info" + href
        elif not href.startswith("https://"):
            continue

        item_id = f"{symbol}|{href}"
        items.append({
            "id": item_id,
            "title": title,
            "url": href
        })

    unique = []
    seen = set()
    for item in items:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    return unique[:10]


def calculate_levels(stock, current_price):
    buy_price = stock.get("buy_price", 0.0)
    quantity = stock.get("quantity", 0)
    target_pct = stock.get("target_pct", 0.0)
    stop_loss_pct = stock.get("stop_loss_pct", 0.0)

    target_price = buy_price * (1 + target_pct / 100) if buy_price else 0
    stop_price = buy_price * (1 - stop_loss_pct / 100) if buy_price else 0

    cost = buy_price * quantity
    value = current_price * quantity
    pnl = value - cost
    pnl_pct = (pnl / cost * 100) if cost else 0

    return {
        "target_price": target_price,
        "stop_price": stop_price,
        "pnl": pnl,
        "pnl_pct": pnl_pct
    }


def is_portfolio_stock(stock):
    return stock.get("quantity", 0) > 0 and stock.get("buy_price", 0) > 0


def calc_move_pct(current_price, prev_price):
    if prev_price and prev_price > 0:
        return ((current_price - prev_price) / prev_price) * 100
    return 0


def check_portfolio_alerts(symbol, stock, state, current_price, prev_price):
    levels = calculate_levels(stock, current_price)
    last_signal = state.get(symbol, {}).get("last_signal", "")
    move_pct = calc_move_pct(current_price, prev_price)

    signal = ""

    if stock.get("buy_price", 0) > 0 and current_price >= levels["target_price"] > 0:
        signal = "TARGET"
    elif stock.get("buy_price", 0) > 0 and current_price <= levels["stop_price"] > 0:
        signal = "STOP"
    elif abs(move_pct) >= PORTFOLIO_MOVE_ALERT_PCT:
        signal = "MOVE"

    if not signal:
        state.setdefault(symbol, {})["last_signal"] = ""
        return

    if last_signal == signal:
        return

    msg = (
        f"EGX Portfolio Alert: {symbol}\n"
        f"Price: {current_price:.2f} EGP\n"
        f"Move vs last check: {move_pct:.2f}%\n"
        f"Buy: {stock['buy_price']:.2f}\n"
        f"Qty: {stock['quantity']}\n"
        f"Target: {levels['target_price']:.2f}\n"
        f"Stop: {levels['stop_price']:.2f}\n"
        f"P/L: {levels['pnl']:.2f} EGP ({levels['pnl_pct']:.2f}%)\n"
        f"Signal: {signal}"
    )
    send_telegram(msg)
    state.setdefault(symbol, {})["last_signal"] = signal


def check_watchlist_opportunity_alerts(symbol, stock, state, current_price, prev_price):
    symbol_state = state.setdefault(symbol, {})
    move_pct = calc_move_pct(current_price, prev_price)

    last_move_signal = symbol_state.get("last_watch_signal", "")
    last_buy_signal = symbol_state.get("last_buy_signal", "")

    # Sensitive move alert
    if abs(move_pct) >= WATCHLIST_MOVE_ALERT_PCT:
        move_signal = "WATCH_MOVE_UP" if move_pct > 0 else "WATCH_MOVE_DOWN"
        if last_move_signal != move_signal:
            msg = (
                f"EGX Watchlist Move: {symbol}\n"
                f"Price: {current_price:.2f} EGP\n"
                f"Move vs last check: {move_pct:.2f}%\n"
                f"Signal: {move_signal}"
            )
            send_telegram(msg)
            symbol_state["last_watch_signal"] = move_signal
    else:
        symbol_state["last_watch_signal"] = ""

    # Simple buy-opportunity detection
    # Needs at least 3 saved prices
    recent_prices = symbol_state.get("recent_prices", [])
    if len(recent_prices) < 3:
        return

    p1, p2, p3 = recent_prices[-3], recent_prices[-2], recent_prices[-1]

    rising_3_checks = p1 < p2 < p3
    rebound_signal = p1 > p2 < p3
    positive_break = move_pct >= WATCHLIST_MOVE_ALERT_PCT

    buy_signal = ""
    if rising_3_checks and positive_break:
        buy_signal = "BUY_BREAKOUT"
    elif rebound_signal and positive_break:
        buy_signal = "BUY_REBOUND"

    if buy_signal and last_buy_signal != buy_signal:
        msg = (
            f"EGX Watchlist Opportunity: {symbol}\n"
            f"Price: {current_price:.2f} EGP\n"
            f"Move vs last check: {move_pct:.2f}%\n"
            f"Recent prices: {p1:.2f} -> {p2:.2f} -> {p3:.2f}\n"
            f"Signal: {buy_signal}"
        )
        send_telegram(msg)
        symbol_state["last_buy_signal"] = buy_signal
    elif not buy_signal:
        symbol_state["last_buy_signal"] = ""


def check_news_alerts(symbol, stock, state):
    try:
        news_items = fetch_news_items(symbol, stock["news_url"])
    except Exception as e:
        print(symbol, "news error:", e)
        return

    seen_ids = set(state.setdefault(symbol, {}).get("seen_news_ids", []))
    fresh = [item for item in news_items if item["id"] not in seen_ids]

    if not seen_ids:
        state[symbol]["seen_news_ids"] = [item["id"] for item in news_items]
        return

    for item in fresh[:3]:
        send_telegram(f"News: {symbol}\n{item['title']}\n{item['url']}")

    merged = list(seen_ids.union({item["id"] for item in news_items}))
    state[symbol]["seen_news_ids"] = merged[-50:]


def update_recent_prices(symbol, state, current_price):
    symbol_state = state.setdefault(symbol, {})
    recent_prices = symbol_state.get("recent_prices", [])
    recent_prices.append(round(current_price, 4))
    symbol_state["recent_prices"] = recent_prices[-5:]


def monitor_once(portfolio, state):
    print("\n" + "=" * 60)
    print("EGX watcher:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    for symbol, stock in portfolio.items():
        quote = get_price(symbol, stock)
        if not quote:
            print(symbol, "no valid price")
            continue

        current_price = quote["price"]
        prev_price = state.setdefault(symbol, {}).get("last_price", 0)

        print(f"{symbol}: {current_price:.2f}")
        for raw in quote["raw"]:
            print("  ", raw["source"], raw["price"])

        update_recent_prices(symbol, state, current_price)

        if is_portfolio_stock(stock):
            check_portfolio_alerts(symbol, stock, state, current_price, prev_price)
        else:
            check_watchlist_opportunity_alerts(symbol, stock, state, current_price, prev_price)

        check_news_alerts(symbol, stock, state)

        state[symbol]["last_price"] = current_price
        portfolio[symbol]["current_price"] = current_price

    save_json(PORTFOLIO_FILE, portfolio)
    save_json(STATE_FILE, state)


def run_watcher():
    portfolio = load_json(PORTFOLIO_FILE, WATCHLIST)
    state = load_json(STATE_FILE, {})

    send_telegram("EGX watcher + news started.")

    while True:
        try:
            monitor_once(portfolio, state)
            print(f"\nSleeping {CHECK_INTERVAL_SECONDS} seconds...")
            print("Press Ctrl+C in console to stop watcher.\n")
            time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nWatcher stopped by user.")
            send_telegram("EGX watcher stopped.")
            break
        except Exception as e:
            print("Runtime error:", e)
            time.sleep(10)


def show_portfolio():
    portfolio = load_json(PORTFOLIO_FILE, WATCHLIST)
    print("\n=== SAVED PORTFOLIO ===")
    print(json.dumps(portfolio, indent=2))


def show_state():
    state = load_json(STATE_FILE, {})
    print("\n=== SAVED STATE ===")
    print(json.dumps(state, indent=2))


def change_interval():
    global CHECK_INTERVAL_SECONDS

    print(f"\nCurrent interval: {CHECK_INTERVAL_SECONDS} seconds")
    new_value = input("Enter new interval in seconds: ").strip()

    try:
        seconds = int(new_value)
        if seconds < 10:
            print("Please use 10 seconds or more.")
            return
        CHECK_INTERVAL_SECONDS = seconds
        print(f"Interval updated to {CHECK_INTERVAL_SECONDS} seconds.")
    except ValueError:
        print("Invalid number.")


def test_telegram():
    print("\nTesting Telegram...")
    ok = send_telegram("Test message from EGX watcher.")
    if ok:
        print("Telegram test sent successfully.")
    else:
        print("Telegram test failed.")


def show_menu():
    while True:
        print("\n=== EGX WATCHER MENU ===")
        print("1. Run one check now")
        print("2. Start continuous watcher")
        print("3. Test Telegram")
        print("4. Show saved portfolio")
        print("5. Show saved state")
        print("6. Change interval")
        print("7. Stop / Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            portfolio = load_json(PORTFOLIO_FILE, WATCHLIST)
            state = load_json(STATE_FILE, {})
            try:
                monitor_once(portfolio, state)
                print("\nOne check completed.")
            except Exception as e:
                print("Error during single check:", e)

        elif choice == "2":
            run_watcher()

        elif choice == "3":
            test_telegram()

        elif choice == "4":
            show_portfolio()

        elif choice == "5":
            show_state()

        elif choice == "6":
            change_interval()

        elif choice == "7":
            print("Exiting program.")
            break

        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    show_menu()
