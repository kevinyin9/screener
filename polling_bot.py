import asyncio
from pluto.exchange.exchange import BinanceExchange
import telebot

TOKEN = "5943012661:AAG2_LfS73WDWz67fiffSzm1B7uoJ1jQOwk"  # tw_future_bot
# CHAT_ID = -4218798338 # 加密強弱勢
bot = telebot.TeleBot(TOKEN)

binance_exchange = BinanceExchange(api_key="tnXg5o95Zu8wrpaRdy7xslZ9qWiR7Esb3DX4GAPpQZn1tg9Z9P2mNtiK6H4ldT87",
                                    secret="PAkEQ0qEr8khxLjEyB5oZdUHwhmqCEgrqp9DXoReBRt8l2MzTRtOZvo05SGHdeZ2")


@bot.message_handler(commands=['balance'])
def get_balance(message):
    msg = f"Current balance: {asyncio.run(binance_exchange.get_balance())}"
    bot.reply_to(message, msg)
    
@bot.message_handler(commands=['close'])
def send_order(message):
    text = message.text.split()
    if len(text) >= 2:
        symbol = text[1]
        if 'USDT' not in symbol:
            bot.reply_to(message, f"Invalid Symbol: {symbol}")
            return    
        qty = text[2]
        order = asyncio.run(binance_exchange.place_order(symbol, "MARKET", "LONG", "SELL", "", qty))
        bot.reply_to(message, f"{order}")
    else:
        bot.reply_to(message, f"Invalid Command: {message.text}")
        
    # 市價止損單
    # order = asyncio.run(binance_exchange.place_stop_loss_market_order('DARUSDT', "SELL", "LONG", "9150", "0.1554"))
    # print(order)
    
    # cancel_order = asyncio.run(binance_exchange.cancel_order('DARUSDT', '1964982650'))
    # print(cancel_order)
    
    # trade_list = asyncio.run(binance_exchange.fetch_trade_list('1000SATSUSDT'))
    # for trade in trade_list:
    #     print(trade)
        
@bot.message_handler(commands=['order'])
def get_order(message):
    open_order = asyncio.run(binance_exchange.fetch_open_orders(symbol=None))
    for order in open_order:
        print(order, '\n')
        
@bot.message_handler(commands=['position'])
def get_position(message):
    #{'symbol': '1000SATSUSDT', 'positionAmt': '360750', 'entryPrice': '2.771E-4', 
    # 'breakEvenPrice': '2.7723855E-4', 'markPrice': '0.00028520', 'unRealizedProfit': '2.92207500',
    # 'liquidationPrice': '0', 'leverage': '1', 'maxNotionalValue': '8000000.0', 
    # 'marginType': 'cross', 'isolatedMargin': '0.00000000', 'isAutoAddMargin': 'false', 
    # 'positionSide': 'LONG', 'notional': '102.88590000', 'isolatedWallet': '0', 
    # 'updateTime': 1721217600344, 'isolated': False, 'adlQuantile': 1}
    msg = ""
    open_position = asyncio.run(binance_exchange.fetch_position())
    for position in open_position:
        if float(position['positionAmt']) != 0:
            msg += '{}  \n{:<20} {:>20} \n{:<20} {:>20} \n{:<20} {:>20} \n{:<20} {:>20}\n'.format(position['symbol'], "positionAmt:", position['positionAmt'], "entryPrice:", float(position['entryPrice']), "unRealizedProfit:", position['unRealizedProfit'], "notional:", position['notional'])
            msg += '-----------------------\n'
    print(msg)
    bot.reply_to(message, msg)

@bot.message_handler(commands=['hi'])
def send_welcome(message):
    bot.reply_to(message, "hi")

bot.polling()