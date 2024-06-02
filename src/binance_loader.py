import os
import sys
from datetime import datetime
import argparse
from pathlib import Path
from tqdm import tqdm

sys.path.append(".")
sys.path.append("../")
sys.path.insert(1, os.path.dirname(__file__) + "/../..")

user_home_path = str(Path.home())

import ccxt
from src.loader_utils import *

"""

SPOT
-s all_spot -t 1m --type SPOT

UPERP
-s all -t 1m --type UPERP

CPERP
-s all -t 1m --type CPERP

"""


class BinanceLoader:
    def __init__(self):
        pass

    def download(self, pair_type, symbol=None):
        timeframe = '1h' # always download 1h, and resample to other timeframe.
        SINCE = datetime(2020, 1, 1)
        TO = datetime.now()

        data_center_path = "./data"
        os.makedirs(data_center_path, exist_ok=True)

        if pair_type == "SPOT":
            data_path = f"{data_center_path}/SPOT"
            client = ccxt.binance()
        elif pair_type == "UPERP":
            data_path = f"{data_center_path}/UPERP"
            client = ccxt.binanceusdm()
        elif pair_type == "CPERP":
            data_path = f"{data_center_path}/CPERP"
            client = ccxt.binancecoinm()

        data_path += "/" + timeframe
        os.makedirs(data_path, exist_ok=True)

        if symbol == None:
            symbol_details = client.fetch_markets()
            for i in tqdm(symbol_details):
                symbol_ = i["symbol"]
                symbol_onboard_date = datetime.fromtimestamp(
                    int(i["info"]["onboardDate"]) / 1000 - 1000
                )
                start_dt = symbol_onboard_date if symbol_onboard_date > SINCE else SINCE
                # print(f"Getting data: {start_dt}, {symbol_}, {timeframe}")
                paginate(client, symbol_, timeframe, data_path, pair_type, start_dt, TO)

        else:
            symbol_details = client.fetch_markets()
            symbols = [i["symbol"].replace('/', '').split(':')[0] for i in symbol_details]
            
            if symbol not in symbols:
                print(f"{symbol} not in current market.")
                return

            symbol_onboard_date = datetime.fromtimestamp(
                int(symbol_details[0]["info"]["onboardDate"]) / 1000 - 1000
            )
            start_dt = symbol_onboard_date if symbol_onboard_date > SINCE else SINCE
            # print(f"Getting data: {start_dt}, {symbol}, {timeframe}")
            # print(symbol)
            paginate(client, symbol, timeframe, data_path, pair_type, start_dt, TO)
        # print("Saved data.")

    def uperp_data_import(self, timeframe, training_pair_list=None):
        df_list = []
        id_list = []
        path = f"./data/UPERP/{timeframe}/"
        all_symbols_path = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and "USDT_UPERP_1h" in f]

        # get training id from training_pair_list
        training_pair_id_list = [s.replace("/", "").split(":")[0] for s in training_pair_list]

        # get all training symbol's data
        for symbol_path in all_symbols_path:
            if any(s in symbol_path for s in training_pair_id_list) == False:
                continue
            
            print(symbol_path)
            data = pd.read_csv(path + symbol_path, index_col='datetime', parse_dates=True)
            data.index = pd.to_datetime(data.index, format='%Y-%m-%d %H:%M:%S')

            # add a column
            id = symbol_path.split("_")[0]
            id_list.append(id)
            data['id'] = id
            df_list.append(data)
        
        df = pd.concat(df_list)
        df.set_index(['id'], append=True, inplace=True)
        df = df.sort_index()
        pd.set_option('display.max_rows', 5000)
        pd.set_option('display.max_columns', 5000)
        pd.set_option('display.width', 5000)
        # print(df)
        # print(df['open'])
        # To get rows where the 'id' is 'BTCUSDT'
        # btcusdt_rows = df.loc[df.index.get_level_values('id') == 'BTCUSDT']
        # print(btcusdt_rows)
        # raise
        return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="symbol and timeframe")
    parser.add_argument("--training_pair_list", nargs='+', help="Symbol or all")
    parser.add_argument("-t", help="Timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d)")
    parser.add_argument(
        "--type", help="SPOT, UPERP, CPERP"
    )
    args = parser.parse_args()

    binance_loader = BinanceLoader()
    binance_loader.download(args.t, args.type, args.training_pair_list)
