# 1. screener cal: 1h, 4h. duration=5days.
# 5days / 4h = 30 kbars.

# 2. 1h + bollinger band, select top-N pairs.

# 3. stop loss: ATR


# another
# - -> +

import numpy as np
import pandas as pd
import talib
import matplotlib.pyplot as plt
import os.path

def run_backtest(symbol, dates):
    if symbol == '1INCHUSDT' or symbol == 'GMXUSDT' or symbol == 'USTCUSDT':
        return 0
    
    filename = f'./data/UPERP/1h/{symbol}_UPERP_1h.csv'
    if not os.path.isfile(filename):
        print('{symbol} csv not found')
        return 0
    df = pd.read_csv(filename) # datetime,open,high,low,close,volume
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date

    date_list = pd.to_datetime(dates).date
    df.loc[df['date'].isin(date_list), 'can_entry'] = 1
    df.reset_index(drop=True, inplace=True)
    # print(symbol, df.to_string())

    # 计算布林带
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20)

    # 计算ATR
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)

    # 初始化信号和仓位
    df['signal'] = 0
    df['position'] = 0
    df['take_profit'] = np.nan
    df['stop_loss'] = np.nan

    # 生成交易信号和止损条件
    for i in range(1, len(df)):
        if df['close'].iloc[i] > df['upper_band'].iloc[i] and df.at[df.index[i], 'can_entry'] == 1 and df['position'].iloc[i-1] == 0:
            df.at[df.index[i], 'signal'] = -1  # 開空頭倉位
            df.at[df.index[i], 'take_profit'] = df['close'].iloc[i] - 2 * df['ATR'].iloc[i]  # 設置止盈價格
            df.at[df.index[i], 'stop_loss'] = df['close'].iloc[i] + df['ATR'].iloc[i]  # 設置止损價格
        elif df['position'].iloc[i-1] == -1 and df['close'].iloc[i] < df['lower_band'].iloc[i]:
            df.at[df.index[i], 'signal'] = 1  # 平仓
        else:
            df.at[df.index[i], 'take_profit'] = df['take_profit'].iloc[i-1]
            df.at[df.index[i], 'stop_loss'] = df['stop_loss'].iloc[i-1]

        # 止盈
        if df['position'].iloc[i-1] == -1 and df['low'].iloc[i] < df['take_profit'].iloc[i-1]:
            df.at[df.index[i], 'signal'] = 1  # 平仓

        # 止損
        if df['position'].iloc[i-1] == -1 and df['high'].iloc[i] > df['stop_loss'].iloc[i-1]:
            df.at[df.index[i], 'signal'] = 1  # 平仓

        # 更新倉位
        if df['position'].iloc[i-1] == -1 and df['signal'].iloc[i] == -1:
            df.at[df.index[i], 'position'] = df['position'].iloc[i-1]
        else:
            df.at[df.index[i], 'position'] = df['position'].iloc[i-1] + df['signal'].iloc[i]

    # 计算每日回报
    df['daily_return'] = df['close'].pct_change()
    df['strategy_return'] = df['daily_return'] * df['position'].shift(1)

    # 计算累计回报
    df['cumulative_market_return'] = (1 + df['daily_return']).cumprod()
    df['cumulative_strategy_return'] = (1 + df['strategy_return']).cumprod()

    # 绘制回报曲线
    # print(df[['datetime','close','signal','position', 'take_profit', 'stop_loss', 'upper_band','daily_return','strategy_return']].to_string())
    # plt.figure(figsize=(12, 6))
    # plt.plot(df['cumulative_market_return'], label='Market Return')
    # plt.plot(df['cumulative_strategy_return'], label='Strategy Return')
    # plt.legend()
    # plt.title('Cumulative Returns')
    # plt.show()

    # 分析回测结果
    total_return = df['cumulative_strategy_return'].iloc[-1] - 1
    # annualized_return = df['strategy_return'].mean() * 252
    # annualized_volatility = df['strategy_return'].std() * (252 ** 0.5)
    # sharpe_ratio = annualized_return / annualized_volatility

    # print(f'{symbol}: {total_return:.2%}')
    # print(f'Annualized Return: {annualized_return:.2%}')
    # print(f'Annualized Volatility: {annualized_volatility:.2%}')
    # print(f'Sharpe Ratio: {sharpe_ratio:.2f}')
    return total_return

def get_top_n(n):
    df = pd.read_csv('abc1.csv', index_col=0)

    def extract_symbol_quantity(cell_value):
        symbol, rs_value = cell_value.split('_')
        return symbol, float(rs_value)

    top_n_dict = {}

    for _, row in df.iterrows():
        date = row['date']
        for column in df.columns[1:n+2]: # get top-n
            cell = row[column]
            symbol, rs_value = extract_symbol_quantity(cell)
            if symbol not in top_n_dict:
                top_n_dict[symbol] = []
            top_n_dict[symbol].append(date)
    return top_n_dict

if __name__ == '__main__':
    n = 5
    top_n_dict = get_top_n(n)
    total_profit = 0
    for symbol, dates in top_n_dict.items():
        total_profit += run_backtest(symbol, dates)
        print(f'{total_profit:.2%}')