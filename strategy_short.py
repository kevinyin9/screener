import talib
import numpy as np

def short_atr_tp(df):
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
            
    return df
            
def short_bband_tp(df):
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
            df.at[df.index[i], 'stop_loss'] = df['close'].iloc[i] + df['ATR'].iloc[i]  # 設置止损價格
        elif df['position'].iloc[i-1] == -1 and df['close'].iloc[i] < df['lower_band'].iloc[i]:
            df.at[df.index[i], 'signal'] = 1  # 平仓
        else:
            df.at[df.index[i], 'stop_loss'] = df['stop_loss'].iloc[i-1]

        # 止損
        if df['position'].iloc[i-1] == -1 and df['high'].iloc[i] > df['stop_loss'].iloc[i-1]:
            df.at[df.index[i], 'signal'] = 1  # 平仓

        # 更新倉位
        if df['position'].iloc[i-1] == -1 and df['signal'].iloc[i] == -1:
            df.at[df.index[i], 'position'] = df['position'].iloc[i-1]
        else:
            df.at[df.index[i], 'position'] = df['position'].iloc[i-1] + df['signal'].iloc[i]
    
    return df