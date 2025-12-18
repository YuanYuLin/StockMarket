# 自動抓取加權指數 (^TWII)，判斷是否符合短波段交易條件
# 加權指數條件：
# 1. 連續 2 天收盤價在 MA20 之上
# 2. MA20 走平或向上
'''
Docstring for check_market
台積電(2330-TW) — 半導體核心, AI↑需求支撐
鴻海(2317-TW) — 供應鏈、訂單消息波動大
聯發科(2454-TW) — 5G/AI SoC 題材
長榮(2603-TW) — 航運消息與運價波動
緯創(3231-TW) — 供應鏈訂單消息容易短期放量
'''


import yfinance as yf
import pandas as pd
import requests
import os
import matplotlib.pyplot as plt

# ===== LINE Messaging API 設定 =====
CHANNEL_ACCESS_TOKEN = ""
USER_ID = ""

def broadcast_message(message: str):
  url = "https://api.line.me/v2/bot/message/broadcast"
  headers = {
    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json"
  }
  payload = {
    "messages": [
    {
      "type": "text",
      "text": message
    }
    ]
  }

  r = requests.post(url, headers=headers, json=payload)
  if r.status_code != 200:
    raise RuntimeError(f"Broadcast failed: {r.text}")
    
def send_line_message(message: str) -> None:
  url = "https://api.line.me/v2/bot/message/push"
  headers = {
    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json"
  }
  payload = {
    "to": USER_ID,
    "messages": [
    {
      "type": "text",
      "text": message
    }
    ]
  }
  r = requests.post(url, headers=headers, json=payload)
  if r.status_code != 200:
    raise RuntimeError(f"LINE push failed: {r.text}")

def check_breakout(symbol, recent):

    today = recent.iloc[-1]
    base = recent.iloc[:-1]  # 前 5 天

    high = base["High"].max()
    low = base["Low"].min()

    # 整理區震幅
    range_pct = (high - low) / low
    today_close = int(today["Close"].item())
    breakout_price = recent["High"].max()
    support_price = recent["Low"].min()

    distance_pct = (breakout_price - today_close) / breakout_price * 100
    distance_pct = round(distance_pct.item(), 2)

    if distance_pct > 0:
      distance_msg = f"距離突破還差 {distance_pct}%"
    else:
      distance_msg = f"已突破 {abs(distance_pct)}%"

    # 成交量條件
    avg_vol = base["Volume"].mean()

    is_breakout = (today["Close"] > high).item()
    is_consolidating = (range_pct <= 0.08).item()
    is_volume_ok = (today["Volume"] >= avg_vol * 1.3).item()

    res = {
        "date": today.name.date(),
        "close": round(today["Close"].item(), 2),
        "breakout_price": round(high.item(), 2),
        "buy_price": round(breakout_price.item() * 1.003, 2),
        "take_profit": round(breakout_price.item() * 1.10, 2),
        "stop_loss": round(support_price.item() * 0.997, 2),
        "range_pct": round(range_pct * 100, 2),
        "volume_ratio": round((today["Volume"] / avg_vol).item(), 2),
        "is_consolidating": is_consolidating,
        "is_breakout": is_breakout,
        "is_volume_ok": is_volume_ok,
        "signal": is_consolidating and is_breakout and is_volume_ok,
        "distance_msg": distance_msg
    }
    return res

def getMsg(symbol, res):
    stock_name = get_stock_name(symbol)
    msg = "✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦\n"
    if res["signal"]:
      msg += (
          f"【{symbol}-{stock_name} 突破訊號】\n"
          f"日期：{res['date']}\n"
          f"收盤價：{res['close']}\n"
          f"突破價：{res['breakout_price']}\n"
          f"建議買價:{res['buy_price']}\n"
          f"停利價：{res['take_profit']}\n"
          f"停損價:{res['stop_loss']}\n"
          f"整理震幅：{res['range_pct']}%\n"
          f"量能倍數：{res['volume_ratio']}x\n"
          f"{res['distance_msg']}\n"
          f"👉 可觀察短波段買點\n"
      )
    else:
      msg += (
          f"【{symbol}-{stock_name} 無突破】\n"
          f"日期：{res['date']}\n"
          f"整理：{res['is_consolidating']}\n"
          f"突破：{res['is_breakout']}\n"
          f"量能：{res['is_volume_ok']}\n"
          f"收盤價：{res['close']}\n"
          f"突破價：{res['breakout_price']}\n"
          f"{res['distance_msg']}\n"
      )
    msg += f"可以買？{'✅ 可以' if res["signal"] else '❌ 不行'}\n"
    return msg

def fetch_taiex(days: int = 40) -> pd.DataFrame:

  """抓取加權指數最近 days 個交易日資料"""
  ticker = yf.Ticker("^TWII")  # 加權指數
  df = ticker.history(period=f"{days}d")
  df = df[['Close']].rename(columns={'Close': 'close'})
  df['ma20'] = df['close'].rolling(20).mean()
  df = df.dropna()
  return df

def check_taiex_monthline(df: pd.DataFrame) -> None:

  """檢查是否允許進行短波段交易"""
  today = df.iloc[-1]
  yesterday = df.iloc[-2]
  before = df.iloc[-3]

  cond_price_today = today['close'] > today['ma20']
  cond_price_yesterday = yesterday['close'] > yesterday['ma20']
  cond_ma20_trend = today['ma20'] >= yesterday['ma20'] >= before['ma20']

  msg = "📋 加權指數（月線）檢查結果" 
  msg += os.linesep
  msg += f"1️⃣ 今日收盤({int(round(today['close']))}) > MA20({int(round(today['ma20']))})：{cond_price_today}"
  msg += os.linesep
  msg += f"2️⃣ 昨日收盤({int(round(yesterday['close']))}) > MA20({int(round(yesterday['ma20']))})：{cond_price_yesterday}"
  msg += os.linesep
  msg += f"3️⃣ MA20 走平或向上：{cond_ma20_trend}"
  msg += os.linesep


  if cond_price_today and cond_price_yesterday and cond_ma20_trend:
    msg += "✅ 結論：允許做短波段交易"
  else:
    msg += "❌ 結論：短波段暫停，維持空手"
  msg += os.linesep
  return msg

def get_stock_name(symbol):
    # 1) 嘗試yfinance
    '''
    try:
        info = yf.Ticker(symbol).info or {}
        name = info.get("longName") or info.get("shortName")
        if name:
            return name
    except Exception:
        pass
    '''
    # 2) 嘗試證交所 MIS API
    try:
        ex = "tse" if ".TW" in symbol.upper() else "otc"
        code = symbol.split(".")[0]
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ex}_{code}.tw&json=1"
        r = requests.get(url, timeout=5)
        data = r.json()
        msg = data.get("msgArray", [])
        if msg:
            # 回傳中文名稱或公司全名
            return msg[0].get("n") or msg[0].get("nf")
    except Exception:
        pass

    # 3) fallback
    return symbol

def backtest_check_breakout(symbol, months=6):
    df = yf.download(symbol, period=f"{months}mo", interval="1d", auto_adjust=False, progress=False)
    df = df.dropna()

    lookback = 5
    df['Signal'] = False
    df['Take_Profit'] = 0.0
    df['Stop_Loss'] = 0.0
    df['Buy_Price'] = 0.0
    df['Position'] = 0
    df['Daily_Return'] = 0.0
    df['Cumulative_Return'] = 0.0

    for i in range(lookback, len(df)):
        recent = df.iloc[i-lookback:i+1]  # 前 5 天 + 今天
        res = check_breakout(symbol, recent)
        
        df.at[df.index[i], 'Signal'] = res['signal']
        df.at[df.index[i], 'Buy_Price'] = res['buy_price']
        df.at[df.index[i], 'Stop_Loss'] = res['stop_loss']
        df.at[df.index[i], 'Take_Profit'] = res['take_profit']

        # 持倉模擬
        if res['signal']:
            df.at[df.index[i], 'Position'] = 1
        elif df['Position'].iloc[i-1] == 1:
            stop_loss = (df['Stop_Loss'].iloc[i-1]).item()
            take_profit = (df['Take_Profit'].iloc[i-1]).item()
            close_price = (df['Close'].iloc[i]).item()

            if close_price <= stop_loss or close_price >= take_profit:
              df.at[df.index[i], 'Position'] = 0
            else:
              df.at[df.index[i], 'Position'] = 1
        else:
            df.at[df.index[i], 'Position'] = 0

        # 每日報酬
        if i > 0:
            df.at[df.index[i], 'Daily_Return'] = (df['Close'].iloc[i] - df['Close'].iloc[i-1]) / df['Close'].iloc[i-1] * df['Position'].iloc[i-1]

    # 策略績效
    df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
    total_signals = df['Signal'].sum()
    wins = df[(df['Daily_Return'] > 0) & (df['Signal'] == True)].shape[0]
    win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
    cumulative_return = df['Cumulative_Return'].iloc[-1] * 100

    result = {
        "symbol": symbol,
        "months": months,
        "total_signals": int(total_signals),
        "win_rate_pct": round(win_rate, 2),
        "cumulative_return_pct": round(cumulative_return, 2)
    }

    max_drawdown = (df['Cumulative_Return'].cummax() - df['Cumulative_Return']).max() * 100
    report = f"""
📊 回測報告 - {symbol}
期間：{months} 個月
總訊號次數：{total_signals}
wins:{wins}
勝率：{win_rate:.2f}%
累積報酬：{cumulative_return:.2f}%
最大回撤：{max_drawdown:.2f}%
"""
    print(report)

    # 畫圖
    plt.figure(figsize=(14,6))
    plt.plot(df.index, df['Close'], label='收盤價', color='blue')
    plt.plot(df.index, df['Close'].rolling(20).mean(), label='MA20', color='orange')
    plt.scatter(df.index[df['Signal']], df['Buy_Price'][df['Signal']], marker='^', color='green', label='突破買點', s=100)
    plt.scatter(df.index[df['Position']==0], df['Close'][df['Position']==0], marker='v', color='red', label='停損/停利出場', s=100)
    plt.title(f'{symbol} 突破交易回測')
    plt.xlabel('日期')
    plt.ylabel('股價')
    plt.legend()
    plt.grid(True)
    plt.show()
    return df, result

if __name__ == "__main__":
  msg = ""
  df = fetch_taiex()
  msg += check_taiex_monthline(df)  

  symbol_list = ["0050.TW", "2317.TW"]
  test = True
  
  for symbol in symbol_list :
    if test == False :
      # 抓近 30 天資料
      df = yf.download(symbol, period="1mo", interval="1d", auto_adjust=False, progress=False)
      df = df.dropna()

      # 取最近 6 天（5 天整理 + 今天）
      recent = df.iloc[-6:]
      res = check_breakout(symbol, recent)
      msg += getMsg(symbol, res)
    else:
      df_backtest, result = backtest_check_breakout(symbol, 12)
      print("回測結果：", result)
      print(f"\n最近 {result['total_signals']} 個信號：")
      print(df_backtest[df_backtest['Signal']].tail(result['total_signals'])[['Close','Buy_Price','Stop_Loss','Take_Profit']])
  print(msg)
  broadcast_message(msg)
