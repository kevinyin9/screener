# 1. screener cal: 1h, 4h. duration=5days.
# 5days / 4h = 30 kbars.

# 2. 1h + bollinger band, select top-N pairs.

# 3. stop loss: ATR


# another
# - -> +
import traceback
import telebot

TOKEN = "5943012661:AAG2_LfS73WDWz67fiffSzm1B7uoJ1jQOwk"  # tw_future_bot
CHAT_ID = -833718924
bot = telebot.TeleBot(TOKEN)

import json
import time
import pandas as pd
import matplotlib.pyplot as plt
import os.path
import websocket
import json
import requests
import numpy as np
from threading import Thread
from datetime import datetime

from strategy_long import long_atr_tp, long_bband_tp
from strategy_short import short_atr_tp, short_bband_tp

def run_strategy(symbol, dates):
    df = pd.read_csv(filename) # datetime,open,high,low,close,volume

    df['can_entry'] = 1
    df.reset_index(drop=True, inplace=True)
    df = long_atr_tp(df)
    

def get_top_n(n):
    df = pd.read_csv('rs_value.csv', index_col=0)

    def extract_symbol_quantity(cell_value):
        symbol, rs_value = cell_value.split('_')
        return symbol, float(rs_value)

    top_n_dict = {}

    len_col = len(df.columns)
    for _, row in df.iterrows():
        date = row['date']
        # for column in df.columns[1:n+2]: # get weakest top-n
        for column in df.columns[len_col - n:len_col]: # get strongest top-n
            cell = row[column]
            symbol, rs_value = extract_symbol_quantity(cell)
            if symbol not in top_n_dict:
                top_n_dict[symbol] = []
            top_n_dict[symbol].append(date)
    return top_n_dict

os.makedirs('data', exist_ok=True)
os.makedirs('data/UPERP', exist_ok=True)
os.makedirs('data/UPERP/1h', exist_ok=True)

# Define the whitelist of symbols

s = """BINANCE:BTCUSDT.P,BINANCE:ETHUSDT.P
###1D
,BINANCE:PEOPLEUSDT.P,BINANCE:JASMYUSDT.P,BINANCE:HIGHUSDT.P,BINANCE:ONDOUSDT.P,BINANCE:ENSUSDT.P,BINANCE:1000PEPEUSDT.P,BINANCE:TRUUSDT.P,BINANCE:MYROUSDT.P,BINANCE:1000FLOKIUSDT.P,BINANCE:FRONTUSDT.P
###8H
,BINANCE:PEOPLEUSDT.P,BINANCE:JASMYUSDT.P,BINANCE:ENSUSDT.P,BINANCE:TRUUSDT.P,BINANCE:1000PEPEUSDT.P,BINANCE:EDUUSDT.P,BINANCE:HIGHUSDT.P,BINANCE:ONDOUSDT.P,BINANCE:MYROUSDT.P,BINANCE:ALICEUSDT.P
###4H
,BINANCE:ALICEUSDT.P,BINANCE:JASMYUSDT.P,BINANCE:PEOPLEUSDT.P,BINANCE:HIGHUSDT.P,BINANCE:OMUSDT.P,BINANCE:STGUSDT.P,BINANCE:SPELLUSDT.P,BINANCE:LINAUSDT.P,BINANCE:GTCUSDT.P,BINANCE:TNSRUSDT.P
###1H
,BINANCE:ALICEUSDT.P,BINANCE:NOTUSDT.P,BINANCE:LINAUSDT.P,BINANCE:KASUSDT.P,BINANCE:PORTALUSDT.P,BINANCE:SPELLUSDT.P,BINANCE:OMUSDT.P,BINANCE:AGLDUSDT.P,BINANCE:COTIUSDT.P,BINANCE:YGGUSDT.P"""

tmp = set()
for line in [s.replace('BINANCE:', '').replace('.P', '') for x in s.split('\n')]:
    for symbol in line.split('USDT'):
        tmp.add(symbol[symbol.find(',')+1:] + 'USDT')

whitelist = list(tmp)
alert_list = {}
print(f"whitelist: {whitelist}")
# Dictionary to hold data in memory
data_in_memory = {symbol: None for symbol in whitelist}

# Function to calculate Bollinger Bands
def calculate_bollinger_bands(df, window=20, num_std_dev=2):
    df['SMA'] = df['close'].rolling(window=window).mean()
    df['STD'] = df['close'].rolling(window=window).std()
    df['Upper Band'] = df['SMA'] + (df['STD'] * num_std_dev)
    df['Lower Band'] = df['SMA'] - (df['STD'] * num_std_dev)
    return df

# Function to fetch kline data from Binance
def fetch_klines(symbol, interval, start_time=None, end_time=None):
    url = f"https://fapi.binance.com/fapi/v1/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1000
    }
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    return df

# Function to load local kline data
def load_local_data(symbol):
    # print(f"{symbol} load_local_data")
    filepath = os.path.join("data/UPERP/1h/", f"{symbol}_UPERP_1h.csv")
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, parse_dates=True)
        df['datetime'] = pd.to_datetime(df['datetime'])
        # print(df)
        # print('df')
    else:
        df = pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    return df

# Function to save local kline data
def save_local_data(symbol, df):
    print(f"{symbol} save_local_data")
    filepath = os.path.join("data/UPERP/1h/", f"{symbol}_UPERP_1h.csv")
    df.to_csv(filepath, index=False)

# Function to update local kline data and load into memory
def update_local_data():
    # print(f"update_local_data")
    for symbol in whitelist:
        df_local = load_local_data(symbol)
        if not df_local.empty:
            last_timestamp = df_local['datetime'].iloc[-1].to_pydatetime()
            last_timestamp_ms = int(time.mktime(last_timestamp.timetuple()) * 1000)
        else:
            last_timestamp_ms = None
        
        df_new = fetch_klines(symbol, "1h", start_time=last_timestamp_ms)
        # print(df_new)
        # print('df_new')
        df_updated = pd.concat([df_local, df_new])
        # df_updated = df_updated.tail(20)  # Keep only the latest 20 rows
        save_local_data(symbol, df_updated)
        data_in_memory[symbol] = df_updated
        print(data_in_memory[symbol])
        print("data_in_memory[symbol]")
        print(f"Updated {symbol} kline data")

# Function to handle incoming websocket messages
def on_message(ws, message):
    data = json.loads(message)
    if 'k' in data:
        symbol = data['s']
        if symbol in whitelist:
            kline = data['k']
            df = pd.DataFrame([[
                pd.to_datetime(kline['t'], unit='ms'),
                float(kline['o']),
                float(kline['h']),
                float(kline['l']),
                float(kline['c']),
                float(kline['v'])
            ]], columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
            
            # print(data_in_memory[symbol])
            # print()
            # print(df)
            # print(data_in_memory[symbol]['datetime'].iloc[-1] == df['datetime'].iloc[-1])
            if data_in_memory[symbol]['datetime'].iloc[-1] == df['datetime'].iloc[-1]:
                df_updated = pd.concat([data_in_memory[symbol].iloc[:-1], df])
            else: # 跨過整點的第一筆新資料，時間就會不同，e.g.:16:59->17:00
                df_updated = pd.concat([data_in_memory[symbol], df])
            # df_updated = df_updated.tail(20)  # Keep only the latest 20 rows
            # print(df_updated)
            df_updated = calculate_bollinger_bands(df_updated)
            # print(df_updated)
            last_row = df_updated.iloc[-1]
            if last_row.close < last_row['Lower Band'] and alert_list[symbol] == False:
                alert_list[symbol] = True
                bot.send_message(CHAT_ID, f"{symbol} touches lower band.")
            # save_local_data(symbol, df_updated)
            # print(df.tail(2))
            # print('---')
            # print(f"{symbol} Bollinger Bands:\n", df[['SMA', 'Upper Band', 'Lower Band']].tail(1))

def on_error(ws, error):
    print("Error: ", error)
    print(traceback.format_exc())
    bot.send_message(CHAT_ID, f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Closed connection")

def on_open(ws):
    print("Opened connection")
    ws.send(json.dumps({
        "method": "SUBSCRIBE",
        "params": [f"{symbol.lower()}@kline_1h" for symbol in whitelist],
        "id": 1
    }))

# Get all symbols from Binance
def get_all_symbols():
    response = requests.get("https://fapi.binance.com/api/v3/exchangeInfo")
    data = response.json()
    symbols = [symbol['symbol'] for symbol in data['symbols'] if symbol['symbol'][-4:] == 'USDT']
    return symbols

# Start websocket connection
def start_websocket():
    ws = websocket.WebSocketApp("wss://fstream.binance.com/ws",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()

def reset_alert_list():
    while True:
        now = datetime.now()
        if now.minute == 0 and now.second < 5:
            for symbol in whitelist:
                alert_list[symbol] = False
        time.sleep(1)

if __name__ == '__main__':
    
    update_local_data()

    # Run websocket in a separate thread
    t1 = Thread(target=start_websocket)
    t1.daemon = True
    t1.start()
    
    for symbol in whitelist:
        alert_list[symbol] = False
    t2 = Thread(target=reset_alert_list)
    t2.daemon = True
    t2.start()
    
    t1.join()
    t2.join()
    
    

    # thread = Thread(target=get_top_n, args=(5, ))
    # thread.daemon = True
    # thread.start()

    # run_backtest(symbol, dates)