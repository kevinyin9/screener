import datetime
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pandas as pd
import telebot

import mplfinance as mpf

BINANCE_PERP_URL = "https://fapi.binance.com/fapi/v1/"
TOKEN = "5943012661:AAG2_LfS73WDWz67fiffSzm1B7uoJ1jQOwk"  # tw_future_bot
CHAT_ID = -833718924

bot = telebot.TeleBot(TOKEN)

def candlestick(response):
    df = pd.DataFrame(
        response.json(),
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "ignore",
        ],
    )
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms") + pd.Timedelta(
        hours=8
    )
    df[["open", "high", "low", "close", "volume"]] = df[
        ["open", "high", "low", "close", "volume"]
    ].apply(pd.to_numeric)
    return df

def fetch_candlestick(url, symbol):
    try:
        response = requests.get(
            url + "klines",
            params={"symbol": symbol, "interval": "1h", "limit": 240},
        )
        df_1h = candlestick(response)
        original_df = df_1h
        df_1h = cal_big_volume(df_1h)
        
        return {"symbol": symbol,
                "original_df": original_df,
                "df_1h": df_1h}

    except Exception as e:
        print(f"Error fetching candlestick: {e}")
        return None


def cal_big_volume(df: pd.DataFrame):
    df["prev_volume"] = df["volume"].shift(1)
    df["big_volume"] = (df["volume"] > df["prev_volume"] * 2) & (
        df["open"] < df["close"]
    )
    return df

def gen_img(symbol, df, original_df_1h, current_time) -> bool:
    df = df[df["big_volume"]]
    df = df[df["timestamp"] == current_time]
    if df.empty:
        return False

    original_df_1h.index = original_df_1h["timestamp"]
    mpf.plot(
        original_df_1h,
        title=f"{symbol}_1h",
        type="candle",
        mav=(30, 45, 60),
        volume=True,
        savefig=f"./img/{symbol}_1h.png",
        style="charles",
        figratio=(32,20),
        tight_layout=True
    )

    bot.send_photo(CHAT_ID, open(f"./img/{symbol}_1h.png", "rb"))
    return True


def job(url):
    os.makedirs("img", exist_ok=True)

    current_time = (
        pd.to_datetime(time.time(), unit="s") + pd.Timedelta(hours=8)
    ).floor("s")
    current_time = current_time.replace(minute=0, second=0)

    with ThreadPoolExecutor(max_workers=20) as executor:
        future_tasks = [
            executor.submit(fetch_candlestick, url, symbol)
            for symbol in symbols
        ]
        results = [future.result() for future in as_completed(future_tasks)]
    
    for result in results:
        symbol = result["symbol"]
        original_df = result["original_df"]
        df_1h = result["df_1h"]
        is_big_volume = gen_img(symbol, original_df, df_1h, current_time)

job(BINANCE_PERP_URL)