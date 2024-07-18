import asyncio
import json

import requests
from pluto.exchange import BinanceExchange

import telebot
TOKEN = "5943012661:AAG2_LfS73WDWz67fiffSzm1B7uoJ1jQOwk"  # tw_future_bot
CHAT_ID = -4218798338 # 加密強弱勢
bot = telebot.TeleBot(TOKEN)

class BinanceServer:
    
    def __init__(self):
        self.whitelist = []
        self.data_in_memory = {}
        self.fetch_white_list_flag = False
        self.current_subscriptions = set()

        self.binance_exchange = BinanceExchange(api_key="tnXg5o95Zu8wrpaRdy7xslZ9qWiR7Esb3DX4GAPpQZn1tg9Z9P2mNtiK6H4ldT87",
                                          secret="PAkEQ0qEr8khxLjEyB5oZdUHwhmqCEgrqp9DXoReBRt8l2MzTRtOZvo05SGHdeZ2")

        print(f"Current balance: {asyncio.run(self.binance_exchange.get_balance())}\n")
        # response = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo')
        # # Check if the request was successful (status code 200)
        # if response.status_code == 200:
        #     # Parse and print the response
        #     data = response.json()
        #     for item in data['symbols']:
        #         if item['symbol'] in 'BNBUSDT':
        #             for i in item:
        #                 print(i, item[i])
        # asyncio.run(self.binance_exchange.set_hedge_mode(True))

        # 0.164
        # 0.0043
        
        # 0.0086 SL
        # 0.0258 TP
        
        # 0.1554 SL
        # 0.1898 TP
        # order = asyncio.run(self.binance_exchange.place_order('1000SATSUSDT', "MARKET", "LONG", "SELL", "", "5755913"))
        # print(order)
        # order = asyncio.run(self.binance_exchange.place_order('1000SATSUSDT', "LIMIT", "LONG", "SELL", "0.00028", "7510222"))
        # print(order)
        
        # 市價止損單
        # order = asyncio.run(self.binance_exchange.place_stop_loss_market_order('DARUSDT', "SELL", "LONG", "9150", "0.1554"))
        # print(order)
        
        # cancel_order = asyncio.run(self.binance_exchange.cancel_order('DARUSDT', '1910544972'))
        # print(cancel_order)
        
        # trade_list = asyncio.run(self.binance_exchange.fetch_trade_list('1000SATSUSDT'))
        # for trade in trade_list:
        #     print(trade)
        
        
        open_order = asyncio.run(self.binance_exchange.fetch_open_orders(symbol=None))
        for order in open_order:
            print(order, '\n')

        #{'symbol': '1000SATSUSDT', 'positionAmt': '360750', 'entryPrice': '2.771E-4', 
        # 'breakEvenPrice': '2.7723855E-4', 'markPrice': '0.00028520', 'unRealizedProfit': '2.92207500',
        # 'liquidationPrice': '0', 'leverage': '1', 'maxNotionalValue': '8000000.0', 
        # 'marginType': 'cross', 'isolatedMargin': '0.00000000', 'isAutoAddMargin': 'false', 
        # 'positionSide': 'LONG', 'notional': '102.88590000', 'isolatedWallet': '0', 
        # 'updateTime': 1721217600344, 'isolated': False, 'adlQuantile': 1}
        open_position = asyncio.run(self.binance_exchange.fetch_position())
        for position in open_position:
            if float(position['positionAmt']) != 0:
                msg = '{}  \n{:<20} {:>20} \n{:<20} {:>20} \n{:<20} {:>20} \n{:<20} {:>20}\n'.format(position['symbol'], "positionAmt:", position['positionAmt'], "entryPrice:", float(position['entryPrice']), "unRealizedProfit:", position['unRealizedProfit'], "notional:", position['notional'])
                print(msg)
        
        # bot.send_message(CHAT_ID, f"?")
        
    
if __name__ == '__main__':
    binanceServer = BinanceServer()