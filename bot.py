import telebot
from crypto_relative_strength import main

bot = telebot.TeleBot("5863822927:AAG6A3qpxUFaqHoM3Kp50cTejT1V7beH1pE")
room_id = -833718924

@bot.message_handler(commands=['ping'])
def ping(message):
    bot.reply_to(message, "I am online!")

@bot.message_handler(commands=['rs'])
def rs(message):
    try:
        rs = message.text.split()[1:]
        print(*rs)
        result = main(*rs)
        print("wtf")
        print(result)
        bot.reply_to(message, result)
    except:
        pass

bot.polling()
