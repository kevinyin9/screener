import math
import os
import numpy as np
import pandas as pd
import config
from datetime import datetime
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.downloader import CryptoDownloader
from datetime import datetime, timedelta
import telebot

TOKEN = "5943012661:AAG2_LfS73WDWz67fiffSzm1B7uoJ1jQOwk"  # tw_future_bot
# CHAT_ID = -833718924 # 母牛飛上天
CHAT_ID = -4218798338 # 加密強弱勢
bot = telebot.TeleBot(TOKEN)

##################### CONFIGURATIONS #####################
CURRENT_TIMEZONE = "America/Los_Angeles"
##########################################################

def calc_total_bars(time_interval, days):
    bars_dict = {
        "1m":   60 * 24 * days, # 1440
        "3m":   20 * 24 * days,
        "5m":   12 * 24 * days,
        "15m":  4 * 24 * days,
        "30m":  2 * 24 * days,
        "1h":   24 * days,
        "2h":   12 * days,
        "4h":   6 * days,
        "8h":   3 * days,
        "24h":  1 * days,
    }
    return bars_dict.get(time_interval)

def calc_total_bar_fixed(time_interval):
    bars_dict = {
        "1h":   60,
        "4h":   45,
        "8h":   30,
        "24h":  10,
    }
    return bars_dict.get(time_interval)

def calc_rs(symbol: str, time_interval, days, start_date: str, end_date: str):
    try:
        cd = CryptoDownloader()
        crypto, status, crypto_data = cd.get_crypto(symbol, time_interval=time_interval, timezone=CURRENT_TIMEZONE)
        if status == 0 or crypto_data.empty:
            # if crypto_data:
            print(f"{symbol} status:{status}, fails to get data -> {crypto_data}")
            return {"crypto": symbol, "rs_score": 0}
    except Exception as e:
        print(f"Error in getting {symbol} info: {e}")
        return {"crypto": symbol, "rs_score": 0}

    bars = calc_total_bars(time_interval, days) # 這個bar的數量是寫死的，需要tune?
    if len(crypto_data) < bars:                # 若資料數量太少，就不算了
        print(crypto_data)
        print(f"{symbol} {time_interval} bar to less, {bars}")
        return {"crypto": symbol, "rs_score": 0}

    # def calculate_weight(row, i, bars, days):
    #     current_close = row['close']
    #     moving_average_30 = row['SMA_30']
    #     moving_average_45 = row['SMA_45']
    #     moving_average_60 = row['SMA_60']

    #     weight = (((current_close - moving_average_30) + 
    #             (current_close - moving_average_45) + 
    #             (current_close - moving_average_60)) * 
    #             (((bars - i) * days / bars) + 1) + 
    #             (moving_average_30 - moving_average_45) + 
    #             (moving_average_30 - moving_average_60) + 
    #             (moving_average_45 - moving_average_60)) / moving_average_60
    #     return weight * (bars - i)
    
    rs_score_list = []
    current_date = start_date
    while current_date <= end_date:
        current_date_dt64 = np.datetime64(current_date)
        df_tmp = crypto_data[crypto_data['datetime'] <= current_date_dt64]
        df_tmp.fillna(0)
        rs_score = 0.0
        for i in range(1, bars+1):
            if i > len(df_tmp):
                break
            current_close = df_tmp['close'].values[-i]
            moving_average_30 = df_tmp['SMA_30'].values[-i]
            moving_average_45 = df_tmp['SMA_45'].values[-i]
            moving_average_60 = df_tmp['SMA_60'].values[-i]
            if np.isnan(moving_average_30) or np.isnan(moving_average_45) or np.isnan(moving_average_60):
                print(f"{symbol} {current_date} is nan")
                rs_score = 0
                break
            weight = (((current_close - moving_average_30) + (current_close - moving_average_45) + (current_close - moving_average_60)) * (((bars - i) * days / bars) + 1) + (moving_average_30 - moving_average_45) + (moving_average_30 - moving_average_60) + (moving_average_45 - moving_average_60)) / moving_average_60
            rs_score += weight * (bars - i)

        # df_tmp = df_tmp.iloc[-bars:]  # 取最后bars行数据
        # df_tmp = df_tmp.reset_index(drop=True)  # 重置索引

        # # 创建一个新的列来保存计算结果
        # df_tmp['rs_value'] = df_tmp.apply(lambda row: calculate_weight(row, df_tmp.index.get_loc(row.name) + 1, bars, days), axis=1)

        # # 计算rs_score
        # rs_score = df_tmp['rs_value'].sum()
        
        rs_score_list.append(rs_score)
        current_date += timedelta(days=1)

    return {"crypto": symbol, "rs_score_list": rs_score_list}

def main(history, start_date, end_date, no_download):
    if history:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        start_date = datetime.now().date()
        end_date = datetime.now().date()

    crypto_downloader = CryptoDownloader()
    if not no_download:
        crypto_downloader.download_all()
    # crypto_downloader.check_crypto_table()
    all_cryptos = crypto_downloader.get_all_symbols()
    # all_cryptos = crypto_downloader.get_volume_rank()
    
    # remove specfic symbols in all_cryptos
    if ini["Base"]["exclude_symbols"]:
        exclude_symbols = ini["Base"]["exclude_symbols"].split(",")
        all_cryptos = [x for x in all_cryptos if x not in exclude_symbols] #and x.find('USDT') != -1]

    time_interval_to_days = {
        "1h": 5,  # 120 bars
        "4h": 10, # 60 bars
        "8h": 15, # 45 bars
        "24h": 20 # 20 bars 
    }

    for time_interval, days in time_interval_to_days.items():
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_tasks = [executor.submit(calc_rs, crypto, time_interval, days, start_date, end_date) for crypto in all_cryptos]
            results = [future.result() for future in as_completed(future_tasks)]

        print(results)
        df_list = []
        failed_targets = []     # Failed to download data or error happened
        target_score = {}
        for result in results:
            if "rs_score_list" in result and result["rs_score_list"] != []:
                target_score[result["crypto"]] = result["rs_score_list"]
            else:
                failed_targets.append(result["crypto"])
            
        if len(failed_targets) != 0:
            print(f"Failed targets: {failed_targets}")

        current_date = start_date
        i = 0
        while current_date <= end_date:
            row = {}
            row['date'] = current_date

            values = {symbol: target_score[symbol][i] for symbol in target_score}
            sorted_values = {k: v for k, v in sorted(values.items(), key=lambda item: item[1])}
            print(current_date, sorted_values)
            for idx, v in enumerate(sorted_values.keys()):
                row[idx] = f"{v}_{str(sorted_values[v])}"
            print("row: ", row)
            df_list.append(row)
            i += 1
            current_date += timedelta(days=1)
        df = pd.DataFrame(df_list)
        df.to_csv(f'rs_value_{time_interval}.csv')
    # msg = ""
    # bot.send_message(CHAT_ID, msg)

if __name__ == '__main__':
    ini = config.Config()
    ini.read('{0}/ini/config.ini'.format(os.getcwd()))

    total_days = int(ini["Base"]["total_days"])    # Calculation duration in days
    history = ini["Base"].getboolean("history")
    start_date = ini["Base"]["start_date"]
    end_date = ini["Base"]["end_date"]
    no_download = ini["Base"].getboolean("no_download")
        
    main(history, start_date, end_date, no_download)