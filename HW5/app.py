from flask import Flask, render_template, request

app = Flask(__name__)

crypto_db = {
    'BTC': {'name': 'Bitcoin', 'price': 65000, 'desc': 'Золотой стандарт криптовалют.'},
    'ETH': {'name': 'Ethereum', 'price': 3500, 'desc': 'Король смарт-контрактов и децентрализованных приложений.'},
    'SOL': {'name': 'Solana', 'price': 140, 'desc': 'Сверхбыстрый блокчейн для масштабируемых приложений.'},
    'BNB': {'name': 'Binance Coin', 'price': 600, 'desc': 'Токен крупнейшей криптобиржи Binance.'},
    'TON': {'name': 'Toncoin', 'price': 7.5, 'desc': 'Криптовалюта, интегрированная в экосистему Telegram.'},
    'DOGE': {'name': 'Dogecoin', 'price': 0.15, 'desc': 'Любимая мем-монета Илона Маска.'},
    'ADA': {'name': 'Cardano', 'price': 0.45, 'desc': 'Блокчейн, построенный на научных исследованиях.'},
    'DOT': {'name': 'Polkadot', 'price': 7.2, 'desc': 'Протокол для объединения разных блокчейнов.'}
}

@app.get("/")
def draw_index():
    return render_template("index.html",coins = crypto_db)

@app.get("/coins")
def draw_coins():
    return render_template("coins.html", coins = crypto_db)

@app.get("/coins/<coin_name>")
def draw_one_coin(coin_name):
    data = crypto_db.get(coin_name.upper())
    if data:
        return render_template('coin.html', coin_name=coin_name.upper(), info=data)

@app.route("/exchanger",methods=["GET", "POST"])
def exchanger():
    result = None
    num = None
    currency = None
    if request.method == "POST":
        new_num = request.form["num"]
        currency = request.form["currency"]

        if new_num:
            num= float(new_num)
            if currency in crypto_db and num > 0:
                result = round(num/crypto_db[currency]["price"],10)

    return render_template("exchanger.html", result=result, currency=currency, coins=crypto_db)

if __name__ == '__main__':
    app.run(debug=True)