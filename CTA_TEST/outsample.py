import os 
import sys
import importlib
import pandas as pd
from tqdm import tqdm
import gc
import json
import random

# from src.strategy.Analyzer import Analyzer
    
def get_data(df_dict, coin):
    return df_dict[coin]    
        
strategy_path = os.path.join(sys.path[0], 'Crypto')
# strategy_folders = [folder for folder in os.listdir(strategy_path) if os.path.isdir(os.path.join(strategy_path, folder))]
strategy_folders = ['bband_squeeze','weekend', 'donchian_ma', 'bband', 'keltner','ma_triple','kd_smoother']
strategy_folders = ['kd_smoother']

start = '2022-01-01'

symbol_list = ['ETH','BTC','BNB','SOL','MATIC','XRP','DYDX','AVAX','LINK','GAS','DOGE','ORDI','TRB','WLD','ADA','OP','FIL','ZRX','LTC','RUNE','ATOM','ARB','GMT','ETC','ARK','BCH','DOT','LDO','SUI','GALA','CAKE','APE','INJ','FTM','APT','YFI','OMG','SEI','EOS','1000SHIB','NEAR','MKR','CYBER','UNI','BLUR','SUSHI','WAVES','MASK','MANA','EGLD','AAVE','NEO','FET','TRX','GRT','ALGO','STX','XLM']

# df_dict = {}
# for coin in symbol_list:
#     print(f'loading {coin}...')
#     df = pd.read_hdf(f'/Users/johnsonhsiao/Desktop/data/{coin}USDT_PERPETUAL.h5')
#     df_dict[coin] = df

# outsample_result = {"config": {"freq": "5min","fee": 0.0003},"params": {}}

for strategy_name in strategy_folders:
    module_name = f'Crypto.{strategy_name}.{strategy_name}'
    strategy_module = importlib.import_module(module_name)
    Strategy = getattr(strategy_module, 'Strategy')
    with open(f'{strategy_path}/{strategy_name}/params.json', 'r') as file:
        params_dict = json.load(file)
        for freq in params_dict.keys():
            outsample_result = {}
            outsample_result['params'] = {}
            for coin in params_dict[freq].keys():
                outsample_result['params'][coin] = {}
                for direction in ['long','short']:
                    outsample_result['params'][coin][direction] = {}
                    i = 0
                    keys = list(params_dict[freq][coin][direction].keys())
                    if len(keys) >= 100:
                        random_keys = random.sample(keys, 100)
                        keys = random_keys
                    for idx in tqdm(keys):
                        param = eval(params_dict[freq][coin][direction][idx].replace("'", '"'))
                        config = {'freq':freq, 'lag':1, 'fee': 0.0003, 'weekend_filter': False, 'rv_filter':False}
                        coin = coin
                        df = pd.read_hdf(f'/Users/johnsonhsiao/Desktop/data/{coin}USDT_PERPETUAL.h5')
                        strategy = Strategy(df=df.loc[start:], configs=config)
                        pf = strategy.strategy(side=direction,params=param)
                        stat = pf.stats()
                        sharpe_ratio = stat['Sharpe Ratio']
                        if sharpe_ratio > 1.8:
                            outsample_result['params'][coin][direction][str(i)] = param  
                            i += 1
                        del df
                        del strategy
                        gc.collect
                if str(1) not in outsample_result['params'][coin]['long'].keys() and str(1) not in outsample_result['params'][coin]['short'].keys():
                    outsample_result['params'].pop(coin)
            os.makedirs(f'{strategy_path}/{strategy_name}/opt/', exist_ok=True)
            with open(f'{strategy_path}/{strategy_name}/opt/{freq}_outsample.json', 'w') as file:
                json.dump(outsample_result, file, indent=4)
                
                
                
                    # for idx in (params_dict[freq][coin]['short'].keys()):
                    #     short_param = eval(params_dict[freq][coin]['short'][idx].replace("'", '"'))
                    #     config = {'freq':freq, 'lag':1, 'fee': 0.0003, 'weekend_filter': False, 'rv_filter':False}
                    #     coin = coin
                    #     df = df_dict[coin]
                    #     strategy = Strategy(df=df.loc[start:], configs=config)
                    #     pf = strategy.strategy(side='long',params=short_param)
                    #     short_value = pf.value
                    #     short_df = short_value.to_frame()
                        
                    #     result = long_df.add(short_df, fill_value=None)
                    #     result = result.dropna()
                    #     result.columns = ['value']
                    #     result = result.resample('1D').max()
                    #     result['return'] = result['value'].pct_change()
                    #     mean_return = result['return'].mean()
                    #     std_dev = result['return'].std()
                    #     sharpe_ratio = (mean_return) / std_dev * (365 ** 0.5) 
                    #     if sharpe_ratio > 1.5:
                    #         result_list.append[param, short_param, sharpe_ratio]
                
            
                
                



