# Screener

# 啟動下單系統
```
python3 binance_server.py
```
啟動兩個Thread
    第1個Thread: 每8小時更新一次白名單，(白名單就是4h, 8h, 24h各取top N個標的, 目前N = 5)
    第2個Thread: 每1小時整點會抓每一個標的的最新K棒，丟進策略判斷是否產生進出場訊號 -> 下單 -> 記錄倉位



下載美股和加密貨幣的歷史數據並透過自己的策略去找到強勢標的

The purpose of this project is to download historical data for US stocks and cryptocurrencies, and use different strategies to identify strong performing assets.

## Installation

```bash
pip3 install -r requirements.txt
```

API keys are needed for [Tiingo](https://tiingo.com/) and [Stocksymbol](https://stock-symbol.herokuapp.com) (Not a requirement for Crypto usage)

## Strategy Usage

1. Crypto relative strength

Identify strong performing assets by comparing SMA-30, SMA-45 and SMA-60

```bash
python3 crypto_relative_strength.py
```

Set the config.ini file to your own preference.

```ini
timeframe = 1h          # 3m, 5m, 15m, 30m, 1h, 2h, 4h
total_days = 1          # Calculation duration in days (max: 1440 bars), e.g. 1440 / (24 bars per day in 1h) = 60
history = True          # Whether to calculate relative strength for specific past date
start_date = 2024-02-03 # Must set the date if history is True
end_date = 2024-02-07   # Must set the date if history is True
exclude_symbols = LSKUSDT,JUPUSDT,ZETAUSDT,ALTUSDT,RONINUSDT,DYMUSDT
```

* Change CURRENT_TIMEZONE in the file if timezone is essential to you.

2. US stock trend template

Utilize Mark Minervini's trend template to filter out strong performing stocks.

```bash
python3 stock_trend_template.py
```

Both scripts will generate a TXT file that can be imported into [TradingView](https://www.tradingview.com/)'s watchlist.

## Crypto Relative Strength Formula 
$$ bars = 4 \times 24 \times days  \text{  (15m time frame)} $$

$$ W = \frac{(bars-i)\times days}{bars} + 1 $$

$$ \begin{align*}
N_i & = \left [ (P_i - MA30_i) + (P_i - MA45_i) + (P_i - MA60_i) \right ]\times W\\  
                       & +(MA30_i - MA60_i) +(MA30_i - MA45_i) + (MA45_i - MA60_i)\\  
\end{align*} $$

$$ Score = \sum_{i=1}^{bars} \frac{N_i} {MA60_i} \times (bars - i)  \\ \text{where i=1 means the closest bar} $$


## Download historical data only
To import crypto or stock downloader for your own usage, simply include the following line in your Python code:

```python3
from src.downloader import StockDownloader
from src.downloader import CryptoDownloader
```