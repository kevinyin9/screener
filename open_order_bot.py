import threading
import time
import pandas as pd 
import numpy as np
import talib as ta
import datetime
import telebot
import requests
from binance.client import Client
client = Client("5ERjx6TcrmAmwH9w6lAu6RxqPgXxeB4xiDhZ9jJZqW5gm3YC3x3NyDyxXkluBI5o", "P3XMM1jDlfx1f3gUcvNBXEEqiBMafp8kdU2kbFzU2kVL228vR2LtgHRxQEb3I7uV")

bot = telebot.TeleBot("5863822927:AAG6A3qpxUFaqHoM3Kp50cTejT1V7beH1pE")
room_id = -833718924

def open_order(symbol, start_price, end_price, separation, quantity):
    start_price = float(start_price)
    end_price = float(end_price)
    separation = int(separation)
    
    price_list = [start_price + i * (end_price - start_price) / (separation - 1) for i in range(separation)]
    print(price_list)
    for price in price_list:
        a = client.futures_create_order(
                symbol=symbol,
                side="BUY",
                type="LIMIT",
                timeInForce="GTX",
                quantity=quantity,
                price=price
            )
        time.sleep(0.1)
        print(a)
    
        
@bot.message_handler(commands=['ping'])
def ping(message):
    bot.reply_to(message, "I am online!")

@bot.message_handler(commands=['order'])
def append_stock(message):
    try:
        stock = message.text.split()[1:]
        print(stock)
        open_order(*stock)
    except:
        pass

bot.polling()
