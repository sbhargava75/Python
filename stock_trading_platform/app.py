from flask import Flask, render_template, request, jsonify
import requests

from database import get_db, init_db

app = Flask(__name__)

YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_quote(symbol):
    """Fetch the current market price for a US equity ticker via Yahoo Finance."""
    try:
        resp = requests.get(
            YAHOO_QUOTE_URL.format(symbol=symbol.upper()),
            params={"interval": "1d", "range": "1d"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        data = resp.json()
        result = data["chart"]["result"][0]
        meta = result["meta"]
        price = meta.get("regularMarketPrice", 0)
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose") or price
        change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0
        return {
            "symbol": meta.get("symbol", symbol).upper(),
            "price": round(float(price), 2),
            "name": meta.get("shortName") or meta.get("symbol", symbol).upper(),
            "change": change_pct,
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# API – Quote
# ---------------------------------------------------------------------------

@app.route("/api/quote/<symbol>")
def api_quote(symbol):
    quote = get_quote(symbol)
    if quote is None:
        return jsonify({"error": f"Could not fetch quote for {symbol.upper()}"}), 404
    return jsonify(quote)


# ---------------------------------------------------------------------------
# API – Portfolio
# ---------------------------------------------------------------------------

@app.route("/api/portfolio")
def api_portfolio():
    db = get_db()
    cash = db.execute("SELECT cash FROM portfolio WHERE id = 1").fetchone()["cash"]
    rows = db.execute("SELECT symbol, shares, avg_cost FROM holdings WHERE shares > 0").fetchall()

    holdings = []
    total_market_value = 0.0
    for r in rows:
        quote = get_quote(r["symbol"])
        price = quote["price"] if quote else r["avg_cost"]
        market_value = round(price * r["shares"], 2)
        gain = round((price - r["avg_cost"]) * r["shares"], 2)
        total_market_value += market_value
        holdings.append({
            "symbol": r["symbol"],
            "shares": r["shares"],
            "avg_cost": round(r["avg_cost"], 2),
            "price": round(price, 2),
            "market_value": market_value,
            "gain": gain,
        })

    db.close()
    return jsonify({
        "cash": round(cash, 2),
        "holdings": holdings,
        "total_value": round(cash + total_market_value, 2),
    })


# ---------------------------------------------------------------------------
# API – Place Order
# ---------------------------------------------------------------------------

@app.route("/api/order", methods=["POST"])
def api_order():
    data = request.get_json(force=True)
    symbol = data.get("symbol", "").upper().strip()
    side = data.get("side", "").upper().strip()
    try:
        shares = int(data.get("shares", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid share quantity"}), 400

    if not symbol or side not in ("BUY", "SELL") or shares <= 0:
        return jsonify({"error": "Invalid order parameters"}), 400

    quote = get_quote(symbol)
    if quote is None:
        return jsonify({"error": f"Could not fetch price for {symbol}"}), 404
    price = quote["price"]
    total = round(price * shares, 2)

    db = get_db()
    cash = db.execute("SELECT cash FROM portfolio WHERE id = 1").fetchone()["cash"]

    if side == "BUY":
        if total > cash:
            db.close()
            return jsonify({"error": "Insufficient funds"}), 400
        # Update cash
        db.execute("UPDATE portfolio SET cash = cash - ? WHERE id = 1", (total,))
        # Update or insert holding
        existing = db.execute("SELECT shares, avg_cost FROM holdings WHERE symbol = ?", (symbol,)).fetchone()
        if existing:
            new_shares = existing["shares"] + shares
            new_avg = round(
                (existing["avg_cost"] * existing["shares"] + price * shares) / new_shares, 4
            )
            db.execute(
                "UPDATE holdings SET shares = ?, avg_cost = ? WHERE symbol = ?",
                (new_shares, new_avg, symbol),
            )
        else:
            db.execute(
                "INSERT INTO holdings (symbol, shares, avg_cost) VALUES (?, ?, ?)",
                (symbol, shares, price),
            )
    else:  # SELL
        existing = db.execute("SELECT shares FROM holdings WHERE symbol = ?", (symbol,)).fetchone()
        if not existing or existing["shares"] < shares:
            db.close()
            return jsonify({"error": "Not enough shares to sell"}), 400
        db.execute("UPDATE portfolio SET cash = cash + ? WHERE id = 1", (total,))
        new_shares = existing["shares"] - shares
        if new_shares == 0:
            db.execute("DELETE FROM holdings WHERE symbol = ?", (symbol,))
        else:
            db.execute("UPDATE holdings SET shares = ? WHERE symbol = ?", (new_shares, symbol))

    # Record the order
    db.execute(
        "INSERT INTO orders (symbol, side, shares, price, total) VALUES (?, ?, ?, ?, ?)",
        (symbol, side, shares, price, total),
    )
    db.commit()

    new_cash = db.execute("SELECT cash FROM portfolio WHERE id = 1").fetchone()["cash"]
    db.close()

    return jsonify({
        "message": f"{side} {shares} shares of {symbol} @ ${price:,.2f}",
        "order": {
            "symbol": symbol,
            "side": side,
            "shares": shares,
            "price": price,
            "total": total,
        },
        "cash_remaining": round(new_cash, 2),
    })


# ---------------------------------------------------------------------------
# API – Order History
# ---------------------------------------------------------------------------

@app.route("/api/orders")
def api_orders():
    db = get_db()
    rows = db.execute(
        "SELECT symbol, side, shares, price, total, timestamp FROM orders ORDER BY id DESC"
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
