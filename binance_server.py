import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import traceback
import telebot
import config
import json
import time
import math
import pandas as pd
import websocket
import json
import requests
import talib
import os

from threading import Thread
from datetime import datetime

from strategy_long import long_atr_tp, long_bband_tp
from strategy_short import short_atr_tp, short_bband_tp
import crypto_relative_strength
from pluto.exchange import BinanceExchange
from utils import setup_logger

pd.set_option('display.precision', 8) # 1000SATSUSDT print df的精准度不夠? 是顯示問題還是實際上就不太準?

os.makedirs('log', exist_ok=True)

current_time = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
logger_name = f"{current_time}.txt"
logger = setup_logger(name=logger_name,
                      file_dir='log',
                      is_file_handled=True)
    
TOKEN = "5943012661:AAG2_LfS73WDWz67fiffSzm1B7uoJ1jQOwk"  # tw_future_bot
CHAT_ID = -4218798338 # 加密強弱勢
bot = telebot.TeleBot(TOKEN)

class BinanceServer:
    
    def __init__(self):
        self.whitelist = []
        self.data_in_memory = {}
        self.fetch_white_list_flag = False
        self.current_subscriptions = set()
        self.base_url = "http://43.207.214.219"
        self.position = {}
        self.precision_map = {} # price precision and qty precision
        self.margin_per_trade = 100.0 # float
        self.strategy_list = {long_bband_tp}

        os.makedirs('data', exist_ok=True)
        os.makedirs('data/UPERP', exist_ok=True)
        os.makedirs('data/UPERP/1h', exist_ok=True)
        
        self.binance_exchange = BinanceExchange(api_key="tnXg5o95Zu8wrpaRdy7xslZ9qWiR7Esb3DX4GAPpQZn1tg9Z9P2mNtiK6H4ldT87",
                                          secret="PAkEQ0qEr8khxLjEyB5oZdUHwhmqCEgrqp9DXoReBRt8l2MzTRtOZvo05SGHdeZ2")
        
        asyncio.run(self.binance_exchange.set_hedge_mode(True))

        logger.info(f"Current balance: {asyncio.run(self.binance_exchange.get_balance())}")
        open_order = asyncio.run(self.binance_exchange.fetch_open_orders(symbol=None))
        for order in open_order:
            print(order, '\n')
            # if float(order['positionAmt']) != 0:
            #     logger.info(f"{order}\n")
                
        # logger.info(f"All Order: 
        
        open_position = asyncio.run(self.binance_exchange.fetch_position())
        logger.info("Current Position: ")
        for position in open_position:
            if float(position['positionAmt']) != 0:
                symbol = position['symbol']
                self.position[symbol] = position['positionAmt']
                logger.info(f"{symbol}: {position['positionAmt']}")

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

    # Update kline data and load into memory
    def update_kline_data(self):
        def get_kline(symbol):
            if not self.data_in_memory[symbol].empty:
                last_timestamp = self.data_in_memory[symbol]['datetime'].iloc[-1].to_pydatetime()
                last_timestamp_ms = int(time.mktime(last_timestamp.timetuple()) * 1000)
            else:
                last_timestamp_ms = None
            
            df_new = self.fetch_klines(symbol, "1h", start_time=last_timestamp_ms)
            self.data_in_memory[symbol] = pd.concat([self.data_in_memory[symbol], df_new])
            self.run_strategy(symbol)
            logger.info(f"Updated {symbol} kline data")

        while self.fetch_white_list_flag == False:
            continue
    
        for symbol in self.whitelist:
            self.data_in_memory[symbol] = self.load_local_data(symbol)

        update_kline_flag = False # 避免get kline兩次，whitelist全部update可能不到一秒就完成了
        while self.fetch_white_list_flag:
            now = datetime.now()
            if (now.minute == 0 and now.second == 0) and not update_kline_flag:
                update_kline_flag = True
                logger.info("start update kline data")
                with ThreadPoolExecutor(max_workers=len(self.whitelist)) as executor:
                    future_tasks = [executor.submit(get_kline, symbol) for symbol in self.whitelist]
                    results = [future.result() for future in as_completed(future_tasks)]
            if (now.minute == 0 and now.second > 5): 
                update_kline_flag = False

    # Function to handle incoming websocket messages
    # def on_message(self, ws, message):
    #     data = json.loads(message)
    #     # logger.debug(data)
    #     if 'k' in data:
    #         symbol = data['s']
    #         if symbol in self.whitelist:
    #             kline = data['k']
    #             df = pd.DataFrame([[
    #                 pd.to_datetime(kline['t'], unit='ms'),
    #                 float(kline['o']),
    #                 float(kline['h']),
    #                 float(kline['l']),
    #                 float(kline['c']),
    #                 float(kline['v'])
    #             ]], columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
                
    #             # print(data_in_memory[symbol])
    #             # print(df)
    #             # print(data_in_memory[symbol]['datetime'].iloc[-1] == df['datetime'].iloc[-1])
    #             if self.data_in_memory[symbol]['datetime'].iloc[-1] == df['datetime'].iloc[-1]:
    #                 df_updated = pd.concat([self.data_in_memory[symbol].iloc[:-1], df])
    #             else: # 跨過整點的第一筆新資料，時間就會不同，e.g.:16:59->17:00
    #                 df_updated = pd.concat([self.data_in_memory[symbol], df])
    #             # df_updated = df_updated.tail(20)  # Keep only the latest 20 rows
    #             # print(df_updated)
    #             df_updated = long_bband_tp(df_updated[-25:], self.position[symbol])
    #             logger.debug(f"{symbol} {df_updated.iloc[-2:]}")
    #             signal = df_updated['signal'].iloc[-1]
    #             if signal != 0:
    #                 current_position = self.position[symbol]
    #                 logger.info(f"{symbol}: {signal}, position: {current_position}, close: {df['close'].iloc[-1]}")
    #                 close_price = round(df['close'].iloc[-1], self.precision_map[symbol]['price_precision'])
    #                 if current_position == 0 and signal == 1:
    #                     logger.info(f"qty: {self.margin_per_trade / close_price}")
    #                     qty = round(self.margin_per_trade / close_price, self.precision_map[symbol]['qty_precision'])
    #                     logger.info(f"after round: close: {close_price}, qty: {qty}")
    #                     logger.info(f"{symbol} LIMIT LONG BUY {qty}@{close_price}")
    #                     order = asyncio.run(self.binance_exchange.place_order(symbol, "LIMIT", "LONG", "BUY", close_price, qty))
    #                     logger.info(f"create new order: {order}")
    #                     bot.send_message(CHAT_ID, f"{symbol} buy long order.")
    #                     with open('position.csv', 'a', newline='') as csvfile:
    #                         writer = csv.writer(csvfile)
    #                         # datetime,symbol,price,qty,side
    #                         writer.writerow([datetime.now(), symbol, close_price, qty, "BUY"])
    #                     self.position[symbol] = qty
    #                     # TODO: filled user ws, change self.position
    #                 elif current_position > 0 and signal == -1:
    #                     qty = current_position
    #                     logger.info(f"{symbol} LIMIT LONG SELL {qty}@{close_price}")
    #                     order = asyncio.run(self.binance_exchange.place_order(symbol, "LIMIT", "LONG", "SELL", close_price, qty))
    #                     logger.info(f"create new order: {order}")
    #                     bot.send_message(CHAT_ID, f"{symbol} sell long order.")
    #                     with open('position.csv', 'a', newline='') as csvfile:
    #                         writer = csv.writer(csvfile)
    #                         # datetime,symbol,price,qty,side
    #                         writer.writerow([datetime.now(), symbol, close_price, qty, "SELL"])
    #                     self.position[symbol] == 0
                        
    def run_strategy(self, symbol):
        df_updated = self.data_in_memory[symbol]
        # df_updated = df_updated.tail(20)  # Keep only the latest 20 rows
        # print(df_updated)
        for strategy in self.strategy_list:
            df_updated = strategy(df_updated[-25:], self.position[symbol])
            logger.debug(f"{symbol} {df_updated.iloc[-1]}")
            signal = df_updated['signal'].iloc[-1]
            if signal != 0:
                logger.info(f"{symbol}: {signal}, position: {self.position[symbol]}, close: {df_updated['close'].iloc[-1]}")
                close_price = round(df_updated['close'].iloc[-1], self.precision_map[symbol]['price_precision'])
                logger.info(f"qty: {self.margin_per_trade / close_price}")
                qty = round(self.margin_per_trade / close_price, self.precision_map[symbol]['qty_precision'])
                logger.info(f"after round: close: {close_price}, qty: {qty}")
                if self.position[symbol] == 0 and signal == 1:
                    logger.info(f"{symbol} LIMIT LONG BUY {qty}@{close_price}")
                    order = asyncio.run(self.binance_exchange.place_order(symbol, "LIMIT", "LONG", "BUY", close_price, qty))
                    logger.info(f"create new order: {order}")
                    bot.send_message(CHAT_ID, f"{strategy.__name__}: {symbol} buy long order.")
                    self.position[symbol] == 1
                    # TODO: filled user ws, change self.position
                elif self.position[symbol] == 1 and signal == -1:
                    logger.info(f"{symbol} LIMIT LONG SELL {qty}@{close_price}")
                    order = asyncio.run(self.binance_exchange.place_order(symbol, "LIMIT", "LONG", "SELL", close_price, qty))
                    logger.info(f"create new order: {order}")
                    bot.send_message(CHAT_ID, f"{strategy.__name__}: {symbol} sell long order.")
                    self.position[symbol] == -1

    # def on_error(self, ws, error):
    #     print("Error: ", error)
    #     print(traceback.format_exc())
    #     bot.send_message(CHAT_ID, f"Error: {error}")

    # def on_close(self, ws, close_status_code, close_msg):
    #     print("Closed connection")

    # def on_open(self, ws):
    #     print("Opened connection")
    #     self.subscribe_new_pair()

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
                            self.precision_map[symbol]['price_precision'] = int(math.log(float(filter['tickSize']), 10)) * -1
                        if(filter['filterType'] == 'MARKET_LOT_SIZE'):
                            self.precision_map[symbol]['qty_precision'] = int(math.log(float(filter['stepSize']), 10)) * -1
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
    # def start_websocket(self):
    #     while self.fetch_white_list_flag == False:
    #         continue

    #     self.ws = websocket.WebSocketApp("wss://fstream.binance.com/ws",
    #                                 on_open=self.on_open,
    #                                 on_message=self.on_message,
    #                                 on_error=self.on_error,
    #                                 on_close=self.on_close)
    #     self.ws.run_forever()
    #     print('over')

    # def subscribe_new_pair(self):
    #     # Determine pairs to unsubscribe and subscribe
    #     new_subscriptions = set(f"{symbol.lower()}@kline_1h" for symbol in self.whitelist)
    #     logger.info(f"new_subscriptions: {new_subscriptions}")
    #     pairs_to_unsubscribe = self.current_subscriptions - new_subscriptions
    #     pairs_to_subscribe = new_subscriptions - self.current_subscriptions
        
    #     logger.info(f"pairs_to_unsubscribe: {pairs_to_unsubscribe}")
    #     if len(pairs_to_unsubscribe) != 0:
    #         self.ws.send(json.dumps({
    #             "method": "UNSUBSCRIBE",
    #             "params": list(pairs_to_unsubscribe),
    #             "id": 312
    #         }))
        
    #     time.sleep(1)
        
    #     logger.info(f"pairs_to_subscribe: {pairs_to_subscribe}")
    #     if len(pairs_to_subscribe) != 0:
    #         self.ws.send(json.dumps({
    #             "method": "SUBSCRIBE",
    #             "params": list(pairs_to_subscribe),
    #             "id": 1
    #         }))
        
    #     time.sleep(1)
        
    #     self.ws.send(json.dumps({
    #         "method": "LIST_SUBSCRIPTIONS",
    #         "id": 3
    #     }))
        
    #     # Update the current subscriptions
    #     self.current_subscriptions = new_subscriptions

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
            # if first_update_whitelist or (now.minute == 35 and now.second < 3):
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
                            if symbol not in self.position: # 如果position已經有這個symbol，有可能已經正在持有倉位，就不可修改
                                self.position[symbol] = 0
                            asyncio.run(self.binance_exchange.set_leverage(symbol, 1))
                
                self.whitelist = list(tmp)
                self.get_precision(self.whitelist)
                print(f"whitelist: {self.whitelist}")
                bot.send_message(CHAT_ID, f"whitelist: {self.whitelist}")
                self.fetch_white_list_flag = True
            time.sleep(0.5)

if __name__ == '__main__':

    binanceServer = BinanceServer()
    t1 = Thread(target=binanceServer.update_whitelist)
    t1.daemon = True
    t1.start()

    t3 = Thread(target=binanceServer.update_kline_data)
    t3.daemon = True
    t3.start()

    # t2 = Thread(target=binanceServer.start_websocket)
    # t2.daemon = True
    # t2.start()
    
    t1.join()
    # t2.join()
    t3.join()