import talib
import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None

def long_atr_tp(df):
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20)

    # 计算ATR
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)

    # 初始化信号和仓位
    df['signal'] = 0
    df['position'] = 0
    df['take_profit'] = np.nan
    df['stop_loss'] = np.nan
    df['strategy_return'] = 0
    entry_price = 0

   # 生成交易信号和止损条件
    for i in range(1, len(df)):
        if df['volume'].iloc[i] > df['volume'].iloc[i-1] * 2 and df['close'].iloc[i] < df['lower_band'].iloc[i] and df.at[df.index[i], 'can_entry'] == 1 and df['position'].iloc[i-1] == 0:
            df.at[df.index[i], 'signal'] = 1  # 開多頭倉位
            entry_price = df['close'].iloc[i]
            df.at[df.index[i], 'take_profit'] = df['close'].iloc[i] + 6 * df['ATR'].iloc[i]  # 設置止盈價格
            df.at[df.index[i], 'stop_loss'] = df['close'].iloc[i] - 2 * df['ATR'].iloc[i]  # 設置止损價格
        elif df['position'].iloc[i-1] == 1 and df['close'].iloc[i] > df['upper_band'].iloc[i]:
            df.at[df.index[i], 'signal'] = -1  # 平仓
            # df.at[df.index[i], 'strategy_return']= df['close'].iloc[i] / entry_price - 1
            entry_price = 0
        else:
            df.at[df.index[i], 'take_profit'] = df['take_profit'].iloc[i-1]
            df.at[df.index[i], 'stop_loss'] = df['stop_loss'].iloc[i-1]
            
        if df['position'].iloc[i-1] == 1 and df['close'].iloc[i] > entry_price + 2 * df['ATR'].iloc[i]:
            df.at[df.index[i], 'stop_loss'] = entry_price

        # 止盈
        if df['position'].iloc[i-1] == 1 and df['high'].iloc[i] > df['take_profit'].iloc[i-1]:
            df.at[df.index[i], 'signal'] = -1  # 平仓
            df.at[df.index[i], 'strategy_return']= df['take_profit'].iloc[i] / entry_price - 1
            entry_price = 0

        # 止損
        if df['position'].iloc[i-1] == 1 and df['low'].iloc[i] < df['stop_loss'].iloc[i-1]:
            df.at[df.index[i], 'signal'] = -1  # 平仓
            # df.at[df.index[i], 'strategy_return']= df['stop_loss'].iloc[i] / entry_price - 1
            entry_price = 0

        # 更新倉位
        if df['position'].iloc[i-1] == 1 and df['signal'].iloc[i] == 1:
            df.at[df.index[i], 'position'] = df['position'].iloc[i-1]
        else:
            df.at[df.index[i], 'position'] = df['position'].iloc[i-1] + df['signal'].iloc[i]
            
    return df
            
def long_bband_tp_backtest(df):
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20)

    # 计算ATR
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)

    # 初始化信号和仓位
    df['signal'] = 0
    df['position'] = 0
    df['take_profit'] = np.nan
    df['stop_loss'] = np.nan

    # df.loc[(df['close'] > df['upper_band']) & (df['can_entry'] == 1), 'singal'] = -1
    # 生成交易信号和止损条件
    for i in range(1, len(df)):
        # 沒爆量條件，碰下軌
        # if df['close'].iloc[i] < df['lower_band'].iloc[i] and df.at[df.index[i], 'can_entry'] == 1 and df['position'].iloc[i-1] == 0:
        
        # 爆量，碰下軌
        if df['volume'].iloc[i] > df['volume'].iloc[i-1] * 2 and df['close'].iloc[i] < df['lower_band'].iloc[i] and df.loc[df.index[i], 'can_entry'] == 1 and df['position'].iloc[i-1] == 0:
            df.loc[df.index[i], 'signal'] = 1  # 開多頭倉位
            df.loc[df.index[i], 'stop_loss'] = df['close'].iloc[i] - 2 * df['ATR'].iloc[i]  # 設置止损價格
        elif df['position'].iloc[i-1] == 1 and df['close'].iloc[i] > df['upper_band'].iloc[i]:
            df.loc[df.index[i], 'signal'] = -1  # 平仓
        else:
            df.loc[df.index[i], 'stop_loss'] = df['stop_loss'].iloc[i-1]

        # 止損
        if df['position'].iloc[i-1] == 1 and df['low'].iloc[i] < df['stop_loss'].iloc[i-1]:
            df.loc[df.index[i], 'signal'] = -1  # 平仓

        # 更新倉位
        if df['position'].iloc[i-1] == 1 and df['signal'].iloc[i] == 1:
            df.loc[df.index[i], 'position'] = df['position'].iloc[i-1]
        else:
            df.loc[df.index[i], 'position'] = df['position'].iloc[i-1] + df['signal'].iloc[i]
            
    return df

def long_bband_tp(df, position):
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20)

    # 计算ATR
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)

    # 初始化信号和仓位
    df = df.assign(signal = 0)
    df = df.assign(can_entry = 1)
    df = df.assign(take_profit = np.nan)
    df = df.assign(stop_loss = np.nan)

    # 生成交易信号和止损条件
    for i in range(1, len(df)):
        # 沒爆量條件，碰下軌
        # if df['close'].iloc[i] < df['lower_band'].iloc[i] and df.at[df.index[i], 'can_entry'] == 1 and df['position'].iloc[i-1] == 0:
        
        # 爆量，碰下軌
        if df['volume'].iloc[i] > df['volume'].iloc[i-1] * 2 and df['close'].iloc[i] < df['lower_band'].iloc[i] and df.loc[df.index[i], 'can_entry'] == 1 and position == 0:
            df.loc[df.index[i], 'signal'] = 1  # 開多頭倉位
            df.loc[df.index[i], 'stop_loss'] = df['close'].iloc[i] - 2 * df['ATR'].iloc[i]  # 設置止损價格
        elif position == 1 and df['close'].iloc[i] > df['upper_band'].iloc[i]:
            df.loc[df.index[i], 'signal'] = -1  # 平仓
        else:
            df.loc[df.index[i], 'stop_loss'] = df['stop_loss'].iloc[i-1]

        # 止損
        if position == 1 and df['low'].iloc[i] < df['stop_loss'].iloc[i-1]:
            df.loc[df.index[i], 'signal'] = -1  # 平仓
            
    return df

def long_big_red(df, symbol):
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20)

    # 计算ATR
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    
    df['volume_sma'] = talib.SMA(df['volume'], 60)

    # 初始化信号和仓位
    df['signal'] = 0
    df['position'] = 0
    df['take_profit'] = np.nan
    df['stop_loss'] = np.nan
    df['highest_price'] = np.nan
    df['trailing_stop'] = np.nan

    # df.loc[(df['close'] > df['upper_band']) & (df['can_entry'] == 1), 'singal'] = -1
    # 生成交易信号和止损条件
    for i in range(1, len(df)):
        if df['position'].iloc[i-1] == 1 and symbol == 'CHRUSDT':
            print(df['datetime'].iloc[i], df['low'].iloc[i], df['stop_loss'].iloc[i-1], df['trailing_stop'].iloc[i-1])
        if df['close'].iloc[i] / df['open'].iloc[i] >= 0.03 and \
           df['close'].iloc[i] > df['close'].iloc[i-1] and \
           df['volume'].iloc[i] > df['volume'].iloc[i-1] * 2.5 and \
           df['volume'].iloc[i] > df['volume_sma'].iloc[i-1] and \
           df.at[df.index[i], 'can_entry'] == 1 and \
           df['position'].iloc[i-1] == 0:
               
            df.at[df.index[i], 'signal'] = 1  # 開多頭倉位
            # df.at[df.index[i], 'stop_loss'] = df['close'].iloc[i] - 2 * df['ATR'].iloc[i]  # 設置止损價格
            df.at[df.index[i], 'stop_loss'] = df['open'].iloc[i]  # 設置止损價格
            df.at[df.index[i], 'highest_price'] = df['close'].iloc[i]
            df.at[df.index[i], 'trailing_stop'] = df['highest_price'].iloc[i] - 2 * df['ATR'].iloc[i]   # Trailing Stop
        # elif df['position'].iloc[i-1] == 1 and df['close'].iloc[i] > df['upper_band'].iloc[i]: # 碰上軌 止盈
        elif df['position'].iloc[i-1] == 1 and (df['low'].iloc[i] < df['stop_loss'].iloc[i-1] or df['low'].iloc[i] < df['trailing_stop'].iloc[i-1]): # trailing_stop 止盈
            df.at[df.index[i], 'signal'] = -1  # 平仓
        else:
            df.at[df.index[i], 'stop_loss'] = df['stop_loss'].iloc[i-1]
            if df['high'].iloc[i] > df['highest_price'].iloc[i-1]:
                df.at[df.index[i], 'highest_price'] = df['high'].iloc[i]
                df.at[df.index[i], 'trailing_stop'] = df['highest_price'].iloc[i] - 2 * df['ATR'].iloc[i]   # Trailing Stop
            else:
                df.at[df.index[i], 'highest_price'] = df['highest_price'].iloc[i]
                df.at[df.index[i], 'trailing_stop'] = df['trailing_stop'].iloc[i-1]

        # 止損
        # if df['position'].iloc[i-1] == 1 and df['low'].iloc[i] < df['stop_loss'].iloc[i-1]:
        # if df['position'].iloc[i-1] == 1 and df['low'].iloc[i] < df['trailing_stop'].iloc[i-1]:
        #     df.at[df.index[i], 'signal'] = -1  # 平仓

        # 更新倉位
        if df['position'].iloc[i-1] == 1 and df['signal'].iloc[i] == 1:
            df.at[df.index[i], 'position'] = df['position'].iloc[i-1]
        else:
            df.at[df.index[i], 'position'] = df['position'].iloc[i-1] + df['signal'].iloc[i]
            
    return df