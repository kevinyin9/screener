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
CHAT_ID = -833718924
bot = telebot.TeleBot(TOKEN)

##################### CONFIGURATIONS #####################
CURRENT_TIMEZONE = "America/Los_Angeles"
##########################################################


def calc_day_bars(time_interval):
    bars_dict = {
        "1m": 1440,
        "3m": 380,
        "5m": 288,
        "15m": 96,
        "30m": 48,
        "1h":  24,
        "2h": 12,
        "4h": 6,
    }
    return bars_dict.get(time_interval)

def calc_total_bars(time_interval, days):
    bars_dict = {
        "1m": 60 * 24 * days, # 1440
        "3m": 20 * 24 * days,
        "5m": 12 * 24 * days,
        "15m": 4 * 24 * days,
        "30m": 2 * 24 * days,
        "1h":  24 * days,
        "2h": 12 * days,
        "4h": 6 * days,
    }
    return bars_dict.get(time_interval)


def calc_current_rs(symbol: str, time_interval: str, days: int, no_download=False):
    try:
        cd = CryptoDownloader()
        crypto, status, crypto_data = cd.get_crypto(symbol, time_interval=time_interval, timezone=CURRENT_TIMEZONE, no_download=no_download)
        if status == 0:
            if crypto_data:
                print(f"{symbol} fails to get data -> {crypto_data}")
            return {"crypto": symbol, "rs_score": 0}
        if crypto_data.empty:
            return {"crypto": symbol, "rs_score": 0}
    except Exception as e:
        print(f"Error in getting {symbol} info: {e}")
        return {"crypto": symbol, "rs_score": 0}

    bars = calc_total_bars(time_interval, days)
    if bars > 1440:
        raise ValueError(f"Requesting too many bars. Limitation: 1440 bars. Your are requesting {bars} bars. Please decrease total days.")
    if len(crypto_data) < bars + 60:
        return {"crypto": symbol, "rs_score": 0}

    rs_score = 0.0
    for i in range(1, bars+1):
        current_close = crypto_data['Close Price'].values[-i]
        moving_average_30 = crypto_data['SMA_30'].values[-i]
        moving_average_45 = crypto_data['SMA_45'].values[-i]
        moving_average_60 = crypto_data['SMA_60'].values[-i]
        weight = (((current_close - moving_average_30) + (current_close - moving_average_45) + (current_close - moving_average_60)) * (((bars - i) * days / bars) + 1) + (moving_average_30 - moving_average_45) + (moving_average_30 - moving_average_60) + (moving_average_45 - moving_average_60)) / moving_average_60
        rs_score += weight * (bars - i)

    return {"crypto": symbol, "rs_score": rs_score}

def calc_history_rs(symbol: str, time_interval: str, days: int, start_date: str, end_date: str, no_download=False):
    try:
        cd = CryptoDownloader()
        crypto, status, crypto_data = cd.get_crypto(symbol, time_interval=time_interval, timezone=CURRENT_TIMEZONE, no_download=no_download)
        if status == 0:
            if crypto_data:
                print(f"{symbol} fails to get data -> {crypto_data}")
            return {"crypto": symbol, "rs_score": 0}
        if crypto_data.empty:
            return {"crypto": symbol, "rs_score": 0}
    except Exception as e:
        print(f"Error in getting {symbol} info: {e}")
        return {"crypto": symbol, "rs_score": 0}

    bars = calc_total_bars(time_interval, days)
    if bars > 1440:
        raise ValueError(f"Requesting too many bars. Limitation: 1440 bars. Your are requesting {bars} bars. Please decrease total days.")
    if len(crypto_data) < bars + 60:
        return {"crypto": symbol, "rs_score": 0}

    day_bars = calc_day_bars(time_interval)

    rs_score_list = []
    current_date = start_date
    while current_date <= end_date:
        current_date_dt64 = np.datetime64(current_date.date())
        df_tmp = crypto_data[crypto_data['Datetime'] <= current_date_dt64]
        rs_score = 0.0
        # print(df_tmp['Close Price'].values)
        for i in range(1, bars+1):
            if i > len(df_tmp):
                break
            current_close = df_tmp['Close Price'].values[-i] 
            moving_average_30 = df_tmp['SMA_30'].values[-i]
            moving_average_45 = df_tmp['SMA_45'].values[-i]
            moving_average_60 = df_tmp['SMA_60'].values[-i]
            if np.isnan(moving_average_30) or np.isnan(moving_average_45) or np.isnan(moving_average_60):
                print(f"{symbol} nan fk")
                rs_score = 0
                break
            weight = (((current_close - moving_average_30) + (current_close - moving_average_45) + (current_close - moving_average_60)) * (((bars - i) * days / bars) + 1) + (moving_average_30 - moving_average_45) + (moving_average_30 - moving_average_60) + (moving_average_45 - moving_average_60)) / moving_average_60
            # if symbol == 'ARUSDT':
                # print(weight, current_close, moving_average_30, moving_average_45, moving_average_60)
            rs_score += weight * (bars - i)
        rs_score_list.append(rs_score)
        current_date += timedelta(days=1)

    return {"crypto": symbol, "rs_score_list": rs_score_list}

if __name__ == '__main__':
    ini = config.Config()
    ini.read('{0}/ini/config.ini'.format(os.getcwd()))

    timeframe = ini["Base"]["timeframe"]      # Time frame: 3m, 5m, 15m, 30m, 1h, 2h, 4h
    total_days = int(ini["Base"]["total_days"])    # Calculation duration in days
    no_download = ini["Base"].getboolean("no_download")
    history = ini["Base"].getboolean("history")
    start_date = ini["Base"]["start_date"]
    end_date = ini["Base"]["end_date"]
    
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    crypto_downloader = CryptoDownloader()
    crypto_downloader.check_crypto_table()
    # all_cryptos = crypto_downloader.get_all_symbols()
    all_cryptos = crypto_downloader.get_volume_rank()
    
    # remove specfic symbols in all_cryptos
    if ini["Base"]["exclude_symbols"]:
        exclude_symbols = ini["Base"]["exclude_symbols"].split(",")
        all_cryptos = [x for x in all_cryptos if x not in exclude_symbols and x.find('USDT') != -1]

    with ThreadPoolExecutor(max_workers=20) as executor:
        if history:
            future_tasks = [executor.submit(calc_history_rs, crypto, timeframe, total_days, start_date, end_date, no_download) for crypto in all_cryptos]
        else:
            future_tasks = [executor.submit(calc_current_rs, crypto, timeframe, total_days, no_download) for crypto in all_cryptos]
        results = [future.result() for future in as_completed(future_tasks)]

    failed_targets = []     # Failed to download data or error happened
    target_score = {}
    # print(results)
    if history:
        for result in results:
            if "rs_score_list" in result and result["rs_score_list"] != []:
                target_score[result["crypto"]] = result["rs_score_list"]
            else:
                failed_targets.append(result["crypto"])
        
        number_of_target = 15
        current_date = start_date
        
        df_list = []
        i = 0
        while current_date <= end_date:
            row = {}
            row['date'] = current_date
            current_date += timedelta(days=1)

            values = {symbol: target_score[symbol][i] for symbol in target_score}
            sorted_values = {k: v for k, v in sorted(values.items(), key=lambda item: item[1])}
            print(current_date, sorted_values)
            for idx, v in enumerate(sorted_values.keys()):
                row[idx] = str(v) + '_' + str(sorted_values[v])
            df_list.append(row)
            i += 1
        df = pd.DataFrame(df_list)
        df.to_csv('abc1.csv')
        # raise
        print(f"\n=========================== Target : Score (TOP {number_of_target}) ===========================")
        all_data = []
        while current_date <= end_date:
            row = {}
            print([x for x in target_score.keys()])
            symbols = [x for x in target_score.keys() if not math.isnan(target_score[x][current_date])]
            symbols.sort(key=lambda x: target_score[x][current_date], reverse=True)
            print(current_date)
            row['date'] = current_date
            for idx, crypto in enumerate(symbols[:number_of_target]):
                score = target_score[crypto][current_date]
                print(f"{crypto}: {score}")
                row[idx] = crypto
            print("===============================================================================")
            all_data.append(row)
            current_date += timedelta(days=1)
        
        df = pd.DataFrame(all_data)
        df.to_csv('abc.csv')
    else:
        for result in results:
            if "rs_score" in result:
                target_score[result["crypto"]] = result["rs_score"]
            else:
                failed_targets.append(result["crypto"])
        print(target_score)
        number_of_target = 15
        symbols = [x for x in target_score.keys()]
        symbols.sort(key=lambda x: target_score[x], reverse=True)
        print("Failed targets: %s" % ", ".join(failed_targets))
        print(f"\n=========================== Target : Score (TOP {number_of_target}) ===========================")
        msg = ""
        for crypto in symbols[:number_of_target]:
            score = target_score[crypto]
            print(f"{crypto}: {round(score, 2)}")
            msg += f"{crypto}: {round(score, 2)}"
        print("===============================================================================")

        bot.send_message(CHAT_ID, msg)
    # Write to txt file
    # txt_content = "###BTCETH\nBINANCE:BTCUSDT.P,BINANCE:ETHUSDT\n###Targets (Sort by score)\n"
    # for crypto in symbols:
    #     txt_content += f",BINANCE:{crypto}.P"
    # date_str = datetime.now().strftime("%Y-%m-%d %H%M")
    # with open(f"{date_str}_crypto_relative_strength_{timeframe}.txt", "w") as f:
    #     f.write(txt_content)
