# 1. screener cal: 1h, 4h. duration=5days.
# 5days / 4h = 30 kbars.

# 2. 1h + bollinger band, select top-N pairs.

# 3. stop loss: ATR


# another
# - -> +

import json
import time
import pandas as pd
import matplotlib.pyplot as plt
import os.path

from strategy_long import long_atr_tp, long_bband_tp_backtest, long_big_red
from strategy_short import short_atr_tp, short_bband_tp

def run_backtest(symbol, dates):    
    filename = f'./data/UPERP/1h/{symbol}_UPERP_1h.csv'
    if not os.path.isfile(filename):
        print('{symbol} csv not found')
        return pd.DataFrame()

    df = pd.read_csv(filename) # datetime,open,high,low,close,volume
    df['datetime'] = pd.to_datetime(df['datetime']) # format=2024/05/04 12:00:00

    df['date'] = df['datetime'].dt.date # format=2024/05/04
    date_list = pd.to_datetime(dates).date
    # print(date_list[0])
    df = df[df['date'] >= date_list[0]]
    # print(symbol, df)
    # pd.to_datetime(dates)       => format=2024/05/04 12:00:00
    # pd.to_datetime(dates).date  => format=2024/05/04
    df['can_entry'] = 0
    df.loc[df['date'].isin(date_list), 'can_entry'] = 1
    df.reset_index(drop=True, inplace=True)
    # print(symbol, df.to_string())

    # df = short_atr_tp(df)
    # df = short_bband_tp(df)
    # df = long_bband_tp_backtest(df) # 40.48%, 2.8
    df = long_atr_tp(df) # 42.86%, 6.3 因為都沒出場
    # df = long_big_red(df, symbol)
    # if symbol == 'CHRUSDT':
    #     print(df.to_string())
    #     df.to_csv('./CHRUSDT.csv')
    #     raise
    
    # 计算累计回报
    # df['cumulative_strategy_return'] = (1 + df['strategy_return']).cumprod()

    # 绘制回报曲线
    # print(df[['datetime','close','signal','position', 'take_profit', 'stop_loss', 'upper_band','daily_return','strategy_return']].to_string())
    # plt.figure(figsize=(12, 6))
    # plt.plot(df['cumulative_market_return'], label='Market Return')
    # plt.plot(df['cumulative_strategy_return'], label='Strategy Return')
    # plt.legend()
    # plt.title('Cumulative Returns')
    # plt.show()

    # 分析回测结果
    # total_return = df['cumulative_strategy_return'].iloc[-1] - 1
    # annualized_return = df['strategy_return'].mean() * 252
    # annualized_volatility = df['strategy_return'].std() * (252 ** 0.5)
    # sharpe_ratio = annualized_return / annualized_volatility

    # print(f'{symbol}: {total_return:.2%}')
    # print(f'Annualized Return: {annualized_return:.2%}')
    # print(f'Annualized Volatility: {annualized_volatility:.2%}')
    # print(f'Sharpe Ratio: {sharpe_ratio:.2f}')
    # df.to_csv(f"{symbol}.csv")
    return df

def get_top_n(n):
    def extract_symbol_quantity(cell_value):
        symbol, rs_value = cell_value.split('_')
        return symbol, float(rs_value)

    n_dict = {}
    for time_interval in ['4h', '8h', '24h']:
        df = pd.read_csv(f'rs_value_{time_interval}.csv', index_col=0)

        len_col = len(df.columns)
        for _, row in df.iterrows():
            date = row['date']
            # for column in df.columns[1:n+2]: # get weakest top-n
            for column in df.columns[len_col - n:len_col]: # get strongest top-n
                cell = row[column]
                symbol, rs_value = extract_symbol_quantity(cell)
                if rs_value <= 0: # 0 means no data
                    continue
                if symbol not in n_dict:
                    n_dict[symbol] = set() # prevent duplicate date
                n_dict[symbol].add(date)
    return n_dict

def get_weakest_n(n):
    def extract_symbol_quantity(cell_value):
        symbol, rs_value = cell_value.split('_')
        return symbol, float(rs_value)

    n_dict = {}
    for time_interval in ['4h']:
        df = pd.read_csv(f'rs_value_{time_interval}.csv', index_col=0)

        len_col = len(df.columns)
        for _, row in df.iterrows():
            date = row['date']
            for column in df.columns[1:n+1]: # get weakest top-n
                cell = row[column]
                symbol, rs_value = extract_symbol_quantity(cell)
                if rs_value == 0: # 0 means no data
                    continue
                if symbol not in n_dict:
                    n_dict[symbol] = set() # prevent duplicate date
                n_dict[symbol].add(date)
    return n_dict

if __name__ == '__main__':
    start = time.time()
    n = 5
    top_n_dict = get_top_n(n)
    # weakest_symbol = get_weakest_n(1)
    backtest_result_dict = {}
    for symbol, dates in top_n_dict.items():
        dates = sorted(list(dates)) # convert set to list
        backtest_result_dict[symbol] = run_backtest(symbol, dates).to_json()

    with open('backtest_result.json', 'w') as fp:
        json.dump(backtest_result_dict, fp)
    
    print(f"Time Cost: {time.time() - start}")