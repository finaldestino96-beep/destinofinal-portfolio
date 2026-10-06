import json, math, os, subprocess, sys
from collections import deque
import pyarrow.parquet as pq
import pandas as pd

DATA_DIR = "polymarket-data/bitcoin-5m-15m-hourly-2026-06-15"
INITIAL_CASH = 100.0
STAKE_FRACTION = 0.10
TARGET_NET = 0.10
TAKER_RATE = 0.07          # Polymarket crypto taker fee used for the June-2026 BTC sample
MAX_COMPLETED = 10000
MOMENTUM_WINDOW = 5
MOMENTUM_THRESHOLD = 0.005
IMBALANCE_THRESHOLD = 0.10

def fee(shares, price):
    return shares * TAKER_RATE * price * (1.0 - price)

def target_exit_price(stake, entry_price, target_net=TARGET_NET):
    # stake includes the entry cost and entry taker fee.
    shares = stake / (entry_price + TAKER_RATE * entry_price * (1-entry_price))
    target_value = stake * (1 + target_net)
    lo, hi = entry_price, 0.999999
    for _ in range(80):
        mid = (lo + hi) / 2
        net = shares * (mid - TAKER_RATE * mid * (1-mid))
        if net >= target_value:
            hi = mid
        else:
            lo = mid
    return hi, shares

def best_book(bids, asks):
    bid = max(bids) if bids else None
    ask = min(asks) if asks else None
    return bid, ask

def imbalance(bids, asks):
    if not bids or not asks:
        return 0.0
    bid_depth = sum(v for p, v in bids.items() if p >= max(bids) - 0.02)
    ask_depth = sum(v for p, v in asks.items() if p <= min(asks) + 0.02)
    den = bid_depth + ask_depth
    return 0.0 if den == 0 else (bid_depth - ask_depth) / den

markets = pd.read_csv(f"{DATA_DIR}/markets.csv")
markets = markets[markets["series"] == "btc-up-or-down-5m"].sort_values("open_time")
if markets.empty:
    raise SystemExit("No BTC 5m markets found")

cash = INITIAL_CASH
completed = []
entries = 0
forced_settlements = 0
processed_events = 0

for _, m in markets.iterrows():
    if len(completed) >= MAX_COMPLETED:
        break
    path = f"{DATA_DIR}/{m['file']}"
    bids, asks = {}, {}
    prices = deque(maxlen=MOMENTUM_WINDOW + 1)
    position = None

    pf = pq.ParquetFile(path)
    for batch in pf.iter_batches(batch_size=10000):
        cols = batch.to_pydict()
        n = len(cols["t"])
        for i in range(n):
            processed_events += 1
            et = cols["event_type"][i]
            p = cols["price"][i]
            s = cols["size"][i]
            side = cols["side"][i]

            if et == "snapshot":
                try:
                    bl = json.loads(cols["bids"][i] or "[]")
                    al = json.loads(cols["asks"][i] or "[]")
                except Exception:
                    bl, al = [], []
                bids = {float(x["price"]): float(x["size"]) for x in bl if float(x["size"]) > 0}
                asks = {float(x["price"]): float(x["size"]) for x in al if float(x["size"]) > 0}

            elif et == "delta":
                px = float(p)
                sz = float(s or 0)
                book = bids if side == "BUY" else asks
                if sz <= 0:
                    book.pop(px, None)
                else:
                    book[px] = sz

            elif et == "trade":
                if p is None:
                    continue
                trade_p = float(p)
                prices.append(trade_p)
                bid, ask = best_book(bids, asks)
                if bid is None or ask is None or ask <= bid:
                    continue

                imb = imbalance(bids, asks)
                mom = 0.0
                if len(prices) >= MOMENTUM_WINDOW + 1 and prices[0] > 0:
                    mom = (prices[-1] / prices[0]) - 1.0

                if position is not None:
                    if position["token"] == "YES":
                        exit_bid = bid
                    else:
                        exit_bid = 1.0 - ask
                    if exit_bid >= position["target_price"]:
                        proceeds = position["shares"] * exit_bid
                        exit_fee = fee(position["shares"], exit_bid)
                        cash += proceeds - exit_fee
                        pnl = cash - position["cash_before"]
                        completed.append({
                            "market_id": m["market_id"], "token": position["token"],
                            "entry": position["entry_price"], "exit": exit_bid,
                            "pnl": pnl, "cash_after": cash, "reason": "target"
                        })
                        position = None
                        if len(completed) >= MAX_COMPLETED:
                            break
                    continue

                if abs(mom) < MOMENTUM_THRESHOLD or abs(imb) < IMBALANCE_THRESHOLD:
                    continue

                # Positive momentum buys YES; negative momentum buys NO.
                token = "YES" if mom > 0 else "NO"
                entry = ask if token == "YES" else 1.0 - bid
                if not (0.01 < entry < 0.99):
                    continue

                stake = cash * STAKE_FRACTION
                target_price, shares = target_exit_price(stake, entry)
                entry_fee = fee(shares, entry)
                total_entry = shares * entry + entry_fee
                if total_entry > cash:
                    continue

                cash_before = cash
                cash -= total_entry
                position = {
                    "token": token, "entry_price": entry, "target_price": target_price,
                    "shares": shares, "cash_before": cash_before
                }
                entries += 1

    # A remaining position is settled at the documented market outcome.
    if position is not None:
        outcome = str(m["winning_outcome"]).strip().lower()
        win = (position["token"].lower() == outcome)
        settlement = 1.0 if win else 0.0
        proceeds = position["shares"] * settlement
        exit_fee = fee(position["shares"], settlement) if settlement > 0 else 0.0
        cash += proceeds - exit_fee
        pnl = cash - position["cash_before"]
        completed.append({
            "market_id": m["market_id"], "token": position["token"],
            "entry": position["entry_price"], "exit": settlement,
            "pnl": pnl, "cash_after": cash, "reason": "settlement"
        })
        forced_settlements += 1

pd.DataFrame(completed).to_csv("backtest_results.csv", index=False)
wins = sum(1 for x in completed if x["pnl"] > 0)
losses = sum(1 for x in completed if x["pnl"] <= 0)
target_exits = sum(1 for x in completed if x["reason"] == "target")
total_pnl = cash - INITIAL_CASH
win_rate = wins / len(completed) if completed else 0.0

with open("backtest_summary.txt", "w") as f:
    f.write(f"initial_cash={INITIAL_CASH:.2f}\n")
    f.write(f"final_cash={cash:.8f}\n")
    f.write(f"total_pnl={total_pnl:.8f}\n")
    f.write(f"completed_operations={len(completed)}\n")
    f.write(f"entries={entries}\n")
    f.write(f"target_exits={target_exits}\n")
    f.write(f"settlements={forced_settlements}\n")
    f.write(f"wins={wins}\n")
    f.write(f"losses={losses}\n")
    f.write(f"win_rate={win_rate:.6%}\n")
    f.write(f"processed_events={processed_events}\n")
    f.write(f"fee_model=crypto taker rate {TAKER_RATE:.2f}, formula shares*rate*p*(1-p)\n")
    f.write(f"strategy=10% balance stake; +10% net target after taker fees; momentum+book-imbalance filter\n")

print(open("backtest_summary.txt").read())
