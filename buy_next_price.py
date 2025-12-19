import yfinance as yf

# -------------------------------
# 參數設定
# -------------------------------
ticker = "2887.TW"      
lookback_days = 120     # 過去半年計算均價
buy_threshold = 0.95    # 股價低於均價 95% 才買入

# -------------------------------
# 取得股價資料
# -------------------------------
data = yf.download(ticker, period="6mo")  # 過去半年
data = data[['Close']]

# -------------------------------
# 計算過去半年的均價
# -------------------------------
average_price = (data['Close'].mean()).item()

# -------------------------------
# 計算下一次買入價格
# -------------------------------
next_buy_price = average_price * buy_threshold

# -------------------------------
# 取得最近價格與日期
# -------------------------------
latest_date = data.index[-1].strftime("%Y-%m-%d")
latest_price = (data['Close'].iloc[-1]).item()

# -------------------------------
# 輸出結果
# -------------------------------
print(f"最近收盤日期: {latest_date}")
print(f"最近收盤價格: {latest_price:.2f}")
print(f"過去半年的均價: {average_price:.2f}")
print(f"建議下一次低接買入價格: {next_buy_price:.2f}")
