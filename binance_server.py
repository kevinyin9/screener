import asyncio
import traceback
import telebot
import config
import json
import time
import math
import pandas as pd
import os.path
import websocket
import json
import requests
import talib
from threading import Thread
from datetime import datetime

from strategy_long import long_atr_tp, long_bband_tp
from strategy_short import short_atr_tp, short_bband_tp
import crypto_relative_strength
from pluto.exchange import BinanceExchange
from utils import setup_logger

os.makedirs('log', exist_ok=True)
logger_path = f".\log\log.txt"
logger = setup_logger(name=__name__,
                      file_dir=logger_path,
                      is_file_handled=True)
    
TOKEN = "5943012661:AAG2_LfS73WDWz67fiffSzm1B7uoJ1jQOwk"  # tw_future_bot
CHAT_ID = -833718924
bot = telebot.TeleBot(TOKEN)

class BinanceServer:
    
    def __init__(self):
        self.whitelist = []
        self.data_in_memory = {}
        self.fetch_white_list_flag = False
        self.current_subscriptions = set()
        self.new_whitelist_flag = False # if has new whitelist, update websocket subscription.
        self.base_url = "http://43.207.214.219"
        self.position = {}
        self.precision_map = {} # price precision and qty precision
        self.margin_per_trade = 50

        os.makedirs('data', exist_ok=True)
        os.makedirs('data/UPERP', exist_ok=True)
        os.makedirs('data/UPERP/1h', exist_ok=True)
        
        self.binance_exchange = BinanceExchange(api_key="tnXg5o95Zu8wrpaRdy7xslZ9qWiR7Esb3DX4GAPpQZn1tg9Z9P2mNtiK6H4ldT87",
                                          secret="PAkEQ0qEr8khxLjEyB5oZdUHwhmqCEgrqp9DXoReBRt8l2MzTRtOZvo05SGHdeZ2")
        
        logger.info(f"Current balance: {asyncio.run(self.binance_exchange.get_balance())}")

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
        logger.info("start update_local_data")
        for symbol in self.whitelist:
            df_local = self.load_local_data(symbol)

            if not df_local.empty:
                last_timestamp = df_local['datetime'].iloc[-1].to_pydatetime()
                last_timestamp_ms = int(time.mktime(last_timestamp.timetuple()) * 1000)
            else:
                last_timestamp_ms = None
            
            df_new = self.fetch_klines(symbol, "1h", start_time=last_timestamp_ms)
            df_updated = pd.concat([df_local, df_new])
            self.data_in_memory[symbol] = df_updated
            logger.info(f"Updated {symbol} kline data")

# Function to handle incoming websocket messages
    def on_message(self, ws, message):
        data = json.loads(message)
        logger.debug(data)
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
                df_updated = long_bband_tp(df_updated[-25:], self.position[symbol])
                signal = df_updated['signal'].iloc[-1]
                if signal != 0:
                    close_price = round(df['close'].iloc[-1], self.precision_map[symbol]['price_presicion'])
                    qty = round(self.margin_per_trade / close_price, self.precision_map[symbol]['qty_presicion'])
                    if self.position[symbol] == 0 and signal == 1:
                        order = asyncio.run(self.binance_exchange.place_order(symbol, "LIMIT", "LONG", "BUY", close_price, qty))
                        logger.info(f"create new order: {order}")
                        bot.send_message(CHAT_ID, f"{symbol} buy long order.")
                        # TODO: filled user ws, change self.position
                    elif self.position[symbol] == 1 and signal == -1:
                        order = asyncio.run(self.binance_exchange.place_order(symbol, "LIMIT", "LONG", "SELL", close_price, qty))
                        logger.info(f"create new order: {order}")
                        bot.send_message(CHAT_ID, f"{symbol} sell long order.")

    def on_error(self, ws, error):
        print("Error: ", error)
        print(traceback.format_exc())
        bot.send_message(CHAT_ID, f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("Closed connection")

    def on_open(self, ws):
        print("Opened connection")

    def get_precision(self, symbols):
        response = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo')
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse and print the response
            data = response.json()
            for item in data['symbols']:
                if item['symbol'] in symbols:
                    symbol = item['symbol']
                    self.precision_map[symbol] = {}
                    for filter in item['filters']:
                        if(filter['filterType'] == 'PRICE_FILTER'):
                            self.precision_map[symbol]['price_precision'] = math.log(float(filter['tickSize']), 10)
                        if(filter['filterType'] == 'MARKET_LOT_SIZE'):
                            self.precision_map[symbol]['qty_precision'] = math.log(float(filter['stepSize']), 10)
                    logger.info(f"{symbol} price precision: {self.precision_map[symbol]['price_precision']}, qty precision: {self.precision_map[symbol]['qty_precision']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

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
                
                logger.info(f"pairs_to_unsubscribe: {pairs_to_unsubscribe}")
                if len(pairs_to_unsubscribe) != 0:
                    ws.send(json.dumps({
                        "method": "UNSUBSCRIBE",
                        "params": list(pairs_to_unsubscribe),
                        "id": 312
                    }))
                
                time.sleep(1)
                
                logger.info(f"pairs_to_subscribe: {pairs_to_subscribe}")
                ws.send(json.dumps({
                    "method": "SUBSCRIBE",
                    "params": list(pairs_to_subscribe),
                    "id": 1
                }))
                
                time.sleep(1)
                
                ws.send(json.dumps({
                    "method": "LIST_SUBSCRIPTIONS",
                    "id": 3
                }))
                
                # Update the current subscriptions
                self.current_subscriptions = new_subscriptions
                
                self.new_whitelist_flag = False
            
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
        
        first_update_whitelist = True

        while True:
            now = datetime.now()
            if first_update_whitelist or (now.hour % 8 == 0 and now.minute == 0 and now.second < 3):
                first_update_whitelist = False
                tmp = set()
                crypto_relative_strength.main(False, start_date, end_date, no_download, exclude_symbols, send_msg=False)
                
                for time_interval in ['4h', '8h', '24h']:
                    df = pd.read_csv(f'rs_value_{time_interval}.csv', index_col=0)

                    len_col = len(df.columns)
                    for _, row in df.iterrows():
                        # for column in df.columns[1:n+2]: # get weakest top-n
                        for column in df.columns[len_col - 5:len_col]: # get strongest top-n
                            cell = row[column]
                            symbol, rs_value = extract_symbol_quantity(cell)
                            if rs_value == 0:
                                continue
                            tmp.add(symbol)
                            self.position[symbol] = 0
                
                self.whitelist = list(tmp)
                self.get_precision(self.whitelist)
                print(f"whitelist: {self.whitelist}")
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

    t2 = Thread(target=binanceServer.start_websocket)
    t2.daemon = True
    t2.start()
    
    t1.join()
    t2.join()