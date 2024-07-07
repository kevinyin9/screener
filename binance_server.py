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

import config
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
import crypto_relative_strength

# def run_strategy(symbol, dates):
#     df = pd.read_csv(filename) # datetime,open,high,low,close,volume

#     df['can_entry'] = 1
#     df.reset_index(drop=True, inplace=True)
#     df = long_atr_tp(df)

class BinanceServer:
    
    def __init__(self):
        self.whitelist, self.data_in_memory = [], {}
        self.fetch_white_list_flag = False
        self.alert_list = {}
        self.current_subscriptions = set()
        self.new_whitelist_flag = False
        self.base_url = "http://43.207.214.219"

        os.makedirs('data', exist_ok=True)
        os.makedirs('data/UPERP', exist_ok=True)
        os.makedirs('data/UPERP/1h', exist_ok=True)

    def get_top_n(self, n):
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


    # Function to calculate Bollinger Bands
    def calculate_bollinger_bands(self, df, window=20, num_std_dev=2):
        df['SMA'] = df['close'].rolling(window=window).mean()
        df['STD'] = df['close'].rolling(window=window).std()
        df['Upper Band'] = df['SMA'] + (df['STD'] * num_std_dev)
        df['Lower Band'] = df['SMA'] - (df['STD'] * num_std_dev)
        return df

    # Function to fetch kline data from Binance
    def fetch_klines(self, symbol, interval, start_time=None, end_time=None):
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
    def load_local_data(self, symbol):
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
    def save_local_data(self, symbol, df):
        print(f"{symbol} save_local_data")
        filepath = os.path.join("data/UPERP/1h/", f"{symbol}_UPERP_1h.csv")
        df.to_csv(filepath, index=False)

    # Function to update local kline data and load into memory
    def update_local_data(self):
        # print(f"update_local_data")
        for symbol in self.whitelist:
            df_local = self.load_local_data(symbol)
            if not df_local.empty:
                last_timestamp = df_local['datetime'].iloc[-1].to_pydatetime()
                last_timestamp_ms = int(time.mktime(last_timestamp.timetuple()) * 1000)
            else:
                last_timestamp_ms = None
            
            df_new = self.fetch_klines(symbol, "1h", start_time=last_timestamp_ms)
            # print(df_new)
            # print('df_new')
            df_updated = pd.concat([df_local, df_new])
            # df_updated = df_updated.tail(20)  # Keep only the latest 20 rows
            self.save_local_data(symbol, df_updated)
            self.data_in_memory[symbol] = df_updated
            # print(data_in_memory[symbol])
            print(f"Updated {symbol} kline data")

# Function to handle incoming websocket messages
    def on_message(self, ws, message):
        data = json.loads(message)
        print(data)
        if 'k' in data:
            symbol = data['s']
            if symbol in self.whitelist:
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
                # print(df)
                # print(data_in_memory[symbol]['datetime'].iloc[-1] == df['datetime'].iloc[-1])
                if self.data_in_memory[symbol]['datetime'].iloc[-1] == df['datetime'].iloc[-1]:
                    df_updated = pd.concat([self.data_in_memory[symbol].iloc[:-1], df])
                else: # 跨過整點的第一筆新資料，時間就會不同，e.g.:16:59->17:00
                    df_updated = pd.concat([self.data_in_memory[symbol], df])
                # df_updated = df_updated.tail(20)  # Keep only the latest 20 rows
                # print(df_updated)
                df_updated = self.calculate_bollinger_bands(df_updated)
                # print(df_updated)
                last_row = df_updated.iloc[-1]
                if last_row.close < last_row['Lower Band'] and self.alert_list[symbol] == False:
                    self.alert_list[symbol] = True
                    requests.post(f"{self.base_url}/web_hook", data={
                        "strategy": "Reletive Strength - Long",
                        "ticker": f"{symbol.upper()}.P",
                        "price": last_row.close,
                        "action": "open long",
                        "leverage": 1,
                        "margin": 15,
                    })
                    print("WEBHOOK POST:", {
                        "strategy": "Reletive Strength - Long",
                        "ticker": f"{symbol.upper()}.P",
                        "price": last_row.close,
                        "action": "open long",
                        "leverage": 1,
                        "margin": 15,
                    })
                    bot.send_message(CHAT_ID, f"{symbol} touches lower band.")
                # save_local_data(symbol, df_updated)
                # print(df.tail(2))
                # print('---')
                # print(f"{symbol} Bollinger Bands:\n", df[['SMA', 'Upper Band', 'Lower Band']].tail(1))

    def on_error(self, ws, error):
        print("Error: ", error)
        print(traceback.format_exc())
        bot.send_message(CHAT_ID, f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("Closed connection")

    def on_open(self, ws):
        print("Opened connection")

    # Get all symbols from Binance
    def get_all_symbols(self):
        response = requests.get("https://fapi.binance.com/api/v3/exchangeInfo")
        data = response.json()
        symbols = [symbol['symbol'] for symbol in data['symbols'] if symbol['symbol'][-4:] == 'USDT']
        return symbols

    # Start websocket connection
    def start_websocket(self):
        while self.fetch_white_list_flag == False:
            continue

        ws = websocket.WebSocketApp("wss://fstream.binance.com/ws",
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        t = Thread(target=self.subscribe_new_pair, args=(ws, ))
        t.start()
        ws.run_forever()
        print('over')

    def subscribe_new_pair(self, ws):
        while True:
            if self.new_whitelist_flag:
                # Determine pairs to unsubscribe and subscribe
                new_subscriptions = set(f"{symbol.lower()}@kline_1h" for symbol in self.whitelist)
                pairs_to_unsubscribe = self.current_subscriptions - new_subscriptions
                pairs_to_subscribe = new_subscriptions - self.current_subscriptions
                
                ws.send(json.dumps({
                    "method": "UNSUBSCRIBE",
                    "params": list(pairs_to_unsubscribe),
                    "id": 312
                }))

                ws.send(json.dumps({
                    "method": "SUBSCRIBE",
                    "params": list(pairs_to_subscribe),
                    "id": 1
                }))
                
                # Update the current subscriptions
                self.current_subscriptions = new_subscriptions
                
                self.new_whitelist_flag = False
            
            time.sleep(0.5)


    def reset_alert_list(self):
        while True:
            now = datetime.now()
            if now.minute == 0 and now.second == 1:
                for symbol in self.whitelist:
                    self.alert_list[symbol] = False
            time.sleep(0.5)

    def update_whitelist(self):
        def extract_symbol_quantity(cell_value):
            symbol, rs_value = cell_value.split('_')
            return symbol, float(rs_value)

        ini = config.Config()
        ini.read('{0}/ini/server_config.ini'.format(os.getcwd()))

        start_date = ini["Base"]["start_date"]
        end_date = ini["Base"]["end_date"]
        no_download = ini["Base"].getboolean("no_download")
        exclude_symbols = ini["Base"]["exclude_symbols"]

        while True:
            now = datetime.now()
            if now.minute == 52 and now.second < 30:
                tmp = set()
                crypto_relative_strength.main(False, start_date, end_date, no_download, exclude_symbols, send_msg=True)
                
                for time_interval in ['4h', '8h', '24h']:
                    df = pd.read_csv(f'rs_value_{time_interval}.csv', index_col=0)

                    len_col = len(df.columns)
                    for _, row in df.iterrows():
                        date = row['date']
                        # for column in df.columns[1:n+2]: # get weakest top-n
                        for column in df.columns[len_col - 10:len_col]: # get strongest top-n
                            cell = row[column]
                            symbol, rs_value = extract_symbol_quantity(cell)
                            tmp.add(symbol)
                
                self.whitelist = list(tmp)
                print(f"whitelist: {self.whitelist}")
                self.data_in_memory = {symbol: None for symbol in self.whitelist}
                bot.send_message(CHAT_ID, f"whitelist: {self.whitelist}")
                self.update_local_data()
                self.fetch_white_list_flag = True
                self.new_whitelist_flag = True
            time.sleep(0.5)

if __name__ == '__main__':

    binanceServer = BinanceServer()
    t1 = Thread(target=binanceServer.update_whitelist)
    t1.daemon = True
    t1.start()

    # Run websocket in a separate thread
    t2 = Thread(target=binanceServer.start_websocket)
    t2.daemon = True
    t2.start()
    
    for symbol in binanceServer.whitelist:
        binanceServer.alert_list[symbol] = False
    t3 = Thread(target=binanceServer.reset_alert_list)
    t3.daemon = True
    t3.start()
    
    t1.join()
    t2.join()
    t3.join()
    
    

    # thread = Thread(target=get_top_n, args=(5, ))
    # thread.daemon = True
    # thread.start()