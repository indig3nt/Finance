from decouple import config
from binance.client import Client
import pandas as pd
import pandas_ta as ta
import json
import os
import time
import sys
import datetime

asset = "BTCUSDT"
quantity = 0.001

client = Client(config("API_KEY"), config("SECRET_KEY"), testnet=True)

def fetch_klines(asset):

    klines = client.get_historical_klines(asset, Client.KLINE_INTERVAL_1MINUTE, "1 HOURS AGO UTC")

    klines = [ [x[0], float(x[4])] for x in klines]

    klines = pd.DataFrame(klines, columns = ["time", "price"])

    klines["time"] = pd.to_datetime(klines["time"], unit = "ms")

    return klines


def get_rsi(asset): 

    klines = fetch_klines(asset)
    klines["rsi"] = ta.rsi( close = klines["price"], length=14)

    return klines["rsi"].iloc[-1]


def get_mas(asset):

    klines = fetch_klines(asset)
    klines["short_ma"] = ta.sma(close=klines["price"], length=46)
    klines["long_ma"] = ta.sma(close=klines["price"], length=50)

    return klines["short_ma"].iloc[-1], klines[ "long_ma"].iloc[-1]

 
def create_account():

    account = { "is_buying":True, "price_paid":None, }
    
    with open("bot_account.json", "w") as f:
        f.write(json.dumps(account))
        f.close()


def log(msg):

    print(f"LOG: {msg}")

    if not os.path.isdir("logs"):
        os.mkdir("logs")

    now = datetime.datetime.now()
    date = now.strftime("%d-%m-%Y")
    time = now.strftime("%H:%M:%S")

    with open(f"logs/{date}.txt", "a+") as log_file:
        log_file.write(f"{time} : {msg}\n")
        log_file.close()


    print(date)
    print(time)

def trade_log(sym, side, price, amount):

    log(f"{side} {amount} of {sym} for {price} per")

    if not os.path.isdir("trades"):

        os.mkdir("trades")

    now = datetime.datetime.now()
    date = now.strftime("%d-%m-%Y")

    if not os.path.isfile(f"trades/{date}.cvs"):

        with open(f"trades/{date}.cvs", "w") as trade_file:

            trade_file.write(f"{sym}, {side}, {price}, {amount}\n")



def do_trade(account, client, asset, side, quantity):

    if side == "buy":

        order = client.order_market_buy(
                symbol = asset,
                quantity = quantity)
        
        account["is_buying"] = False
    
    else:

        order = client.order_market_sell(
                symbol = asset,
                quantity = quantity)
        
        account["is_buying"] = True

    order_id = order["orderId"]

    while order["status"] != "FILLED":

        order = client.get_order(
                symbol = asset,
                orderId = order_id)
        
        time.sleep(1)

    print(order)

    price_paid = sum([ float(fill["price"]) * float(fill["qty"]) for fill in order["fills"] ])
    
    trade_log(asset, side, price_paid, quantity)

    print(f"Paid : {price_paid}")
    
    with open("bot_account.json", "w") as f:

        f.write(json.dumps(account))
        f.close()

    return price_paid        

rsi = get_rsi(asset)
old_rsi = rsi

short_ma, long_ma = get_mas(asset)
old_short, old_long = short_ma, long_ma
        
rsi_buy_signal = 43.33
rsi_sells_signal = 70


while True:

    try:

        if not os.path.exists("bot_account.json"):
            create_account()

        with open("bot_account.json") as f:
            account = json.load(f)
            

        print(account)

        old_rsi = rsi
        rsi = get_rsi(asset)

        old_short, old_long = short_ma, long_ma
        short_ma, long_ma = get_mas(asset)

        print(rsi)
        print(short_ma, long_ma)

        if account["is_buying"] == True:

            if rsi < rsi_buy_signal and old_rsi > rsi_buy_signal \
                and old_short > old_long and short_ma < long_ma:
                    
                price_paid = do_trade(account, client, asset, "buy", quantity)

                account["price_paid"] = price_paid

                with open("bot_account.json", "w") as f:

                    f.write(json.dumps(account))
                    f.close()

        else:
            

            price_paid = account.get("price_paid", None)

            if price_paid is None:

                raise ValueError("No price paid stored for the current position.")

            elif rsi > rsi_sells_signal and old_rsi < rsi_sells_signal \
                and old_short < old_long and short_ma > long_ma:

                do_trade(account, client, asset, "sell", quantity)
            
            else:

                stop_loss_pct = 0.3

                current_price = float(client.get_symbol_ticker(symbol=asset)["price"])

                stop_loss_price = (1 - stop_loss_pct) * price_paid

                if current_price <= stop_loss_price:

                    print("Stop-Loss triggered. Selling...")

                    order = client.order_market_sell(
                    symbol = asset,
                    quantity = quantity)

                    account["is_buying"] = True

                    order_id = order["orderId"]

                    while order["status"] != "FILLED":

                        order = client.get_order(
                                symbol = asset,
                                orderId = order_id)
                    
                        time.sleep(1)

                    print(f"Sold due to stop-loss at price: {current_price}")

                print(order)

        time.sleep(7)  

    except Exception as e:
        
        log("ERROR" + str(e))
        sys.exit()