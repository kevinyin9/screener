import json
from binance import Client
import pandas as pd

clients = Client(
    "btEOnrzsmGItMxybiZMl7sKWljUZp3ODTnioSREmbUjCHsPiBY3FlN0jbc5LneUG", 
    "gd8R3joGzUrkkuBkufLSIsMAIIAnzAaFClhNw3dPaWZePcSTXZTPGEnswtTpM42L"
)

# get now unix datetime
datetime_now = int(pd.Timestamp.now().timestamp() * 1000)
print(datetime_now)

df_list = []
for _ in range(10):
    df_list.append(pd.DataFrame(clients.futures_account_trades(endTime=datetime_now)))
    datetime_now = datetime_now - 7 * 24 * 60 * 60 * 1000
df = pd.concat(df_list)
df.drop(columns=['positionSide', 'orderId', 'buyer', 'maker', 'commissionAsset', 'marginAsset'], inplace=True)
print(df.to_string())

# for i in clients.futures_account_trades():
#     print(i)