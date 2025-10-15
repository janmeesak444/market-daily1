import os, datetime as dt, requests, yfinance as yf
from pytz import timezone, utc

WH = os.environ["DISCORD_WEBHOOK"]

tickers = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow": "^DJI",
    "Gold": "GC=F",
    "Crude": "CL=F",
    "EURUSD": "EURUSD=X",
    "BTC": "BTC-USD"
}

def pct(a, b):
    try: return (a/b - 1) * 100
    except Exception: return 0.0

lines = []
for name, t in tickers.items():
    d = yf.download(t, period="5d", interval="1d", progress=False)
    if d.empty:
        lines.append(f"{name}: n/a")
        continue
    last = float(d["Close"].iloc[-1])
    prev = float(d["Close"].iloc[-2]) if len(d) >= 2 else last
    change = pct(last, prev)
    fmt = f"{last:,.0f}" if abs(last) >= 1000 else f"{last:,.2f}"
    lines.append(f"{name}: {fmt} ({change:+.2f}%)")

heat = sum([float(s.split()[-1].strip("()%")) for s in lines if "(" in s])
tone = "Risk-on vibes" if heat > 0 else "Risk-off tone" if heat < 0 else "Flat day"

ee = timezone("Europe/Tallinn")
now_ee = dt.datetime.now(utc).astimezone(ee)

msg = {
  "content": (
    f"**Daily Market Review — {now_ee:%Y-%m-%d %H:%M} (Tallinn)**\n"
    + "\n".join(lines) + f"\n\n_{tone}_"
  )
}

requests.post(WH, json=msg, timeout=20)
