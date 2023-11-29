from datetime import datetime
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.downloader import CryptoDownloader


##################### CONFIGURATIONS #####################
CURRENT_TIMEZONE = "America/Los_Angeles"
##########################################################


def calc_total_bars(time_interval, days):
    bars_dict = {
        "1m": 60 * 24 * days,
        "3m": 20 * 24 * days,
        "5m": 12 * 24 * days,
        "15m": 4 * 24 * days,
        "30m": 2 * 24 * days,
        "1h":  24 * days,
        "2h": 12 * days,
        "4h": 6 * days,
    }
    return bars_dict.get(time_interval)


def test_strategy(symbol: str, time_interval: str, days: int):
    try:
        cd = CryptoDownloader()
        crypto, status, crypto_data = cd.get_crypto(symbol, time_interval=time_interval, timezone=CURRENT_TIMEZONE)
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
    print(bars)
    if bars > 1500 - 60:
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

def main(timeframe, total_days):
    crypto_downloader = CryptoDownloader()
    crypto_downloader.check_crypto_table()
    # all_cryptos = crypto_downloader.get_all_symbols()
    all_cryptos = crypto_downloader.get_volume_rank()

    with ThreadPoolExecutor(max_workers=20) as executor:
        future_tasks = [executor.submit(test_strategy, crypto, timeframe, total_days) for crypto in all_cryptos]
        results = [future.result() for future in as_completed(future_tasks)]

    failed_targets = []     # Failed to download data or error happened
    target_score = {}
    for result in results:
        if result["rs_score"] != 0:
            target_score[result["crypto"]] = result["rs_score"]
        else:
            failed_targets.append(result["crypto"])
    targets = [x for x in target_score.keys()]
    targets.sort(key=lambda x: target_score[x], reverse=True)
    # Show results
    print("Failed targets: %s" % ", ".join(failed_targets))
    print("\n=========================== Target : Score (TOP 20) ===========================")
    result = ""
    for crypto in targets[:20]:
        score = target_score[crypto]
        result += f"{crypto}: {score}\n"
        print(f"{crypto}: {score}")
    print("===============================================================================")
    # Write to txt file
    # txt_content = "###BTCETH\nBINANCE:BTCUSDT.P,BINANCE:ETHUSDT\n###Targets (Sort by score)\n"
    # for crypto in targets:
    #     txt_content += f",BINANCE:{crypto}.P"
    # date_str = datetime.now().strftime("%Y-%m-%d %H%M")
    # with open(f"{date_str}_crypto_relative_strength_{timeframe}.txt", "w") as f:
    #     f.write(txt_content)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--timeframe', type=str, help='Time frame (3m, 5m, 15m, 30m, 1h, 2h, 4h)', default="15m")
    parser.add_argument('-d', '--total_days', type=int, help='Calculation duration in days (default 7 days)', default=7)
    args = parser.parse_args()
    timeframe = args.timeframe
    total_days = args.total_days
    main(timeframe, total_days)
    