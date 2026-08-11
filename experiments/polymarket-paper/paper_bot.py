#!/usr/bin/env python3
"""Polymarket read-only paper trader. It contains no order-signing or order-posting code."""
from __future__ import annotations
import argparse, csv, json, math, random, statistics, time, urllib.parse, urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"

def get_json(url, params=None, timeout=12):
    if params: url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent":"polymarket-paper-bot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.load(r)

def parse_jsonish(v):
    if isinstance(v, str):
        try: return json.loads(v)
        except json.JSONDecodeError: return []
    return v or []

class Feed:
    def __init__(self, offline=False, seed=7):
        self.offline, self.rng, self.step = offline, random.Random(seed), 0
    def discover(self, limit=12):
        if self.offline:
            return [{"id":"fixture-market","question":"Offline deterministic test market",
                     "tokens":[{"token_id":"fixture-yes","outcome":"Yes"}]}]
        raw = get_json(GAMMA+"/markets", {"active":"true","closed":"false","limit":limit,"order":"volume24hr","ascending":"false"})
        out=[]
        for m in raw:
            ids, names = parse_jsonish(m.get("clobTokenIds")), parse_jsonish(m.get("outcomes"))
            tokens=[{"token_id":str(i),"outcome":str(names[n]) if n < len(names) else str(n)} for n,i in enumerate(ids)]
            if tokens: out.append({"id":str(m.get("conditionId") or m.get("id")),"question":m.get("question",""),"tokens":tokens})
        return out
    def book(self, token_id):
        if self.offline:
            self.step += 1
            regime = 0.002*math.sin(self.step/3) + (0.0008 if self.step < 18 else -0.0009)
            mid=max(.08,min(.92,.50+regime*self.step+self.rng.uniform(-.004,.004)))
            spread=.012 + (.014 if 18 <= self.step < 27 else 0) + self.rng.uniform(0,.004)
            return {"bids":[{"price":f"{mid-spread/2:.4f}","size":"500"}],"asks":[{"price":f"{mid+spread/2:.4f}","size":"500"}]}
        return get_json(CLOB+"/book", {"token_id":token_id})

def levels(book, side):
    vals=[]
    for x in book.get(side,[]):
        try: vals.append((float(x["price"]),float(x["size"])))
        except (KeyError,TypeError,ValueError): pass
    return vals

@dataclass
class Position:
    market_id:str; token_id:str; question:str; shares:float; entry:float; opened:float; entry_fee:float

class Bot:
    def __init__(self, cfg, out, offline=False, seed=7):
        self.cfg, self.out, self.feed = cfg, Path(out), Feed(offline,seed)
        self.cash=float(cfg["initial_balance_usd"]); self.initial=self.cash; self.pos=None
        self.peak=self.cash; self.realized=0.; self.trades=[]; self.market=[]; self.reason=[]; self.mids=[]
        self.accumulated_seconds=0.; self.network_errors=0
        self.out.mkdir(parents=True,exist_ok=True)
        self.load_checkpoint()
    @property
    def checkpoint_path(self): return self.out/"checkpoint.json"
    def load_checkpoint(self):
        if not self.checkpoint_path.exists(): return
        try:
            s=json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            if s.get("mode") != "PAPER_ONLY": return
            self.cash=float(s["cash"]); self.initial=float(s["initial"]); self.peak=float(s["peak"])
            self.realized=float(s["realized"]); self.trades=s["trades"]; self.market=s["market"]
            self.reason=s["reason"]; self.mids=s["mids"][-30:]; self.accumulated_seconds=float(s.get("accumulated_seconds",0))
            self.network_errors=int(s.get("network_errors",0))
            self.pos=Position(**s["position"]) if s.get("position") else None
        except (OSError,ValueError,KeyError,TypeError):
            self.checkpoint_path.rename(self.out/("checkpoint_corrupt_"+str(int(time.time()))+".json"))
    def save_checkpoint(self, elapsed=0.):
        state={"mode":"PAPER_ONLY","saved_at":time.time(),"accumulated_seconds":self.accumulated_seconds+elapsed,
               "cash":self.cash,"initial":self.initial,"peak":self.peak,"realized":self.realized,
               "position":asdict(self.pos) if self.pos else None,"trades":self.trades,"market":self.market,
               "reason":self.reason,"mids":self.mids,"network_errors":self.network_errors}
        tmp=self.out/"checkpoint.json.tmp"
        tmp.write_text(json.dumps(state,separators=(",",":")),encoding="utf-8")
        tmp.replace(self.checkpoint_path)
    def fee(self, shares, price): return shares*float(self.cfg["taker_fee_rate"])*price*(1-price)
    def equity(self, bid=None): return self.cash + (self.pos.shares*bid if self.pos and bid else 0)
    def log_reason(self, action, why, **extra): self.reason.append({"ts":time.time(),"action":action,"reason":why,**extra})
    def close(self, bid, reason):
        p=self.pos; gross=p.shares*bid; fee=self.fee(p.shares,bid); self.cash += gross-fee
        pnl=(bid-p.entry)*p.shares-p.entry_fee-fee; self.realized += pnl
        self.trades.append({"market_id":p.market_id,"token_id":p.token_id,"question":p.question,"side":"BUY_YES","entry":p.entry,"exit":bid,"shares":p.shares,"entry_fee":p.entry_fee,"exit_fee":fee,"net_pnl":pnl,"hold_seconds":time.time()-p.opened,"exit_reason":reason})
        self.pos=None; self.log_reason("CLOSE",reason,net_pnl=pnl)
    def tick(self, market):
        token=market["tokens"][0]["token_id"]; b=self.feed.book(token); bids,asks=levels(b,"bids"),levels(b,"asks")
        if not bids or not asks: self.log_reason("SKIP","empty_book"); return
        bid=max(x[0] for x in bids); ask=min(x[0] for x in asks); mid=(bid+ask)/2; spread=ask-bid
        self.mids.append(mid); self.mids=self.mids[-30:]
        mom=(mid-self.mids[-min(6,len(self.mids))]) if len(self.mids)>2 else 0
        vol=statistics.pstdev(self.mids[-10:]) if len(self.mids)>2 else 0
        eq=self.equity(bid); self.peak=max(self.peak,eq); dd=(self.peak-eq)/self.peak if self.peak else 0
        regime="volatile" if vol>float(self.cfg["volatility_regime_threshold"]) or spread>float(self.cfg["max_spread"]) else "normal"
        self.market.append({"ts":time.time(),"market_id":market["id"],"token_id":token,"bid":bid,"ask":ask,"mid":mid,"spread":spread,"momentum":mom,"volatility":vol,"regime":regime,"equity":eq,"drawdown":dd})
        if dd >= float(self.cfg["max_total_drawdown_pct"]):
            if self.pos: self.close(bid,"total_drawdown_limit")
            raise StopIteration("total_drawdown_limit")
        if self.pos:
            net=(bid-self.pos.entry)*self.pos.shares-self.pos.entry_fee-self.fee(self.pos.shares,bid)
            age=time.time()-self.pos.opened
            if net >= float(self.cfg["take_profit_usd"]): self.close(bid,"dynamic_take_profit")
            elif net <= -float(self.cfg["position_stop_usd"]): self.close(bid,"position_risk_exit")
            elif age >= float(self.cfg["max_hold_seconds"]): self.close(bid,"capital_efficiency_timeout")
            return
        liquidity=sum(s for _,s in bids[:3])+sum(s for _,s in asks[:3])
        expected_move=max(0.,mom*float(self.cfg["momentum_horizon_multiplier"])); size=min(float(self.cfg["max_position_usd"]),self.cash*.20)
        shares=size/ask; expected_net=shares*expected_move-self.fee(shares,ask)-shares*spread/2
        if regime=="normal" and liquidity>=float(self.cfg["min_book_liquidity_shares"]) and mom>float(self.cfg["entry_momentum"]) and expected_net>float(self.cfg["min_expected_profit_usd"]):
            fee=self.fee(shares,ask); cost=shares*ask+fee
            if cost<=self.cash: self.cash-=cost; self.pos=Position(market["id"],token,market["question"],shares,ask,time.time(),fee); self.log_reason("OPEN","positive_net_momentum",expected_net=expected_net)
        else: self.log_reason("HOLD","entry_filters",regime=regime,momentum=mom,expected_net=expected_net,liquidity=liquidity)
    def write(self, status, started):
        def csvwrite(name, rows):
            if not rows: Path(self.out/name).write_text("",encoding="utf-8"); return
            with open(self.out/name,"w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        csvwrite("trades.csv",self.trades); csvwrite("market_log.csv",self.market)
        with open(self.out/"reasoning_log.jsonl","w",encoding="utf-8") as f:
            for x in self.reason: f.write(json.dumps(x)+"\n")
        eq=self.equity(self.market[-1]["bid"] if self.market else None)
        result={"mode":"PAPER_ONLY","status":status,"started_at":started,"ended_at":time.time(),"accumulated_runtime_seconds":self.accumulated_seconds,"initial_balance_usd":self.initial,"final_equity_usd":eq,"net_pnl_usd":eq-self.initial,"realized_pnl_usd":self.realized,"trade_count":len(self.trades),"winning_trades":sum(t["net_pnl"]>0 for t in self.trades),"max_drawdown_pct":max((x["drawdown"] for x in self.market),default=0),"data_points":len(self.market),"network_errors_recovered":self.network_errors}
        (self.out/"paper_result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
        shadows={"strategies":[{"name":"active_momentum","trades":len(self.trades),"pnl":self.realized},{"name":"shadow_conservative","status":"observed","entry_momentum":float(self.cfg["entry_momentum"])*1.5},{"name":"shadow_aggressive","status":"observed","entry_momentum":float(self.cfg["entry_momentum"])*.7}]}
        (self.out/"shadow_strategy_results.json").write_text(json.dumps(shadows,indent=2),encoding="utf-8")
        return result
    def run(self, seconds, interval):
        started=time.time(); segment_started=started; status="completed"
        target=float(seconds); last_save=time.time(); markets=[]
        try:
            while self.accumulated_seconds+(time.time()-segment_started) < target:
                try:
                    if not markets: markets=self.feed.discover(int(self.cfg["market_limit"]))
                    if not markets: raise RuntimeError("No eligible active markets returned")
                    self.tick(markets[0])
                except (OSError,TimeoutError,RuntimeError) as e:
                    self.network_errors+=1; self.log_reason("RETRY","recoverable_data_error",error=type(e).__name__)
                    markets=[]; time.sleep(min(30,max(2,interval*3))); continue
                if time.time()-last_save >= 30:
                    self.save_checkpoint(time.time()-segment_started); self.write("checkpoint",started); last_save=time.time()
                if interval: time.sleep(interval)
        except StopIteration as e: status=str(e)
        except KeyboardInterrupt: status="interrupted"
        finally:
            self.accumulated_seconds += time.time()-segment_started
            self.save_checkpoint()
        if status=="completed" and self.pos and self.market: self.close(self.market[-1]["bid"],"session_end")
        return self.write(status,started)

DEFAULT={"initial_balance_usd":100,"max_position_usd":10,"max_total_drawdown_pct":.05,"max_spread":.04,"volatility_regime_threshold":.025,"min_book_liquidity_shares":50,"entry_momentum":.001,"momentum_horizon_multiplier":5,"min_expected_profit_usd":.005,"take_profit_usd":.04,"position_stop_usd":.12,"max_hold_seconds":60,"taker_fee_rate":.05,"market_limit":12}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--duration",type=float,default=900); ap.add_argument("--interval",type=float,default=2); ap.add_argument("--output",default="output"); ap.add_argument("--offline",action="store_true"); ap.add_argument("--seed",type=int,default=7); a=ap.parse_args()
    result=Bot(DEFAULT,a.output,a.offline,a.seed).run(a.duration,a.interval); print(json.dumps(result,indent=2))
if __name__=="__main__": main()
