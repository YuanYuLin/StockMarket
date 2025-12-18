# 自動抓取加權指數 (^TWII)，判斷是否符合短波段交易條件
# 條件：
# 1. 連續 2 天收盤價在 MA20 之上
# 2. MA20 走平或向上


import yfinance as yf
import pandas as pd
import requests
import os

# ===== LINE Messaging API 設定 =====
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
    broadcast_message(msg)
    print(msg)
  else:
    msg += "❌ 結論：短波段暫停，維持空手"
    broadcast_message(msg)
    print(msg)

if __name__ == "__main__":
  df = fetch_taiex()
  check_taiex_monthline(df)
