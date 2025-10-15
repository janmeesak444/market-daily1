import os, sys, datetime as dt, requests
import yfinance as yf
from pytz import timezone, utc

def log(*a): print("[LOG]", *a, flush=True)

# --- Time gate: only post at 16:35 Europe/Tallinn ---
ee = timezone("Europe/Tallinn")
now_ee = dt.datetime.now(utc).astimezone(ee)
if not (now_ee.hour == 16 and now_ee.minute == 35):
    log(f"Skipping run at {now_ee:%Y-%m-%d %H:%M} (Tallinn) — not 16:35 yet.")
    sys.exit(0)
# ----------------------------------------------------

WH = os.environ.get("DISCORD_WEBHOOK")
if not WH:
    log("Missing DISCORD_WEBHOOK secret")
    sys.exit(2)

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
    try:
        return (a/b - 1) * 100
    except Exception as e:
        log("pct calc error:", e)
        return 0.0

lines = []
for name, t in tickers.items():
    try:
        d = yf.download(t, period="5d", interval="1d", progress=False)
        if d is None or d.empty:
            lines.append(f"{name}: n/a")
            continue
        last = float(d["Close"].iloc[-1])
        prev = float(d["Close"].iloc[-2]) if len(d) >= 2 else last
        change = pct(last, prev)
        fmt = f"{last:,.0f}" if abs(last) >= 1000 else f"{last:,.2f}"
        lines.append(f"{name}: {fmt} ({change:+.2f}%)")
    except Exception as e:
        log(f"Failed {name} ({t}):", repr(e))
        lines.append(f"{name}: n/a")

heat = 0.0
try:
    heat = sum([float(s.split()[-1].strip("()%")) for s in lines if "(" in s])
except Exception as e:
    log("heat calc error:", e)

tone = "Risk-on vibes" if heat > 0 else "Risk-off tone" if heat < 0 else "Flat day"

content = (
    f"**Daily Market Review — {now_ee:%Y-%m-%d %H:%M} (Tallinn)**\n"
    + "\n".join(lines) + f"\n\n_{tone}_"
)

log("Posting to Discord...")
resp = requests.post(WH, json={"content": content}, timeout=30)
log("Discord status:", resp.status_code)
if resp.status_code >= 300:
    log("Discord response text:", resp.text)
    sys.exit(2)

log("Done.")
