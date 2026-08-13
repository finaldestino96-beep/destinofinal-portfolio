#!/usr/bin/env python3
"""Fifty consecutive BTC 5m adaptive PAPER_ONLY decisions using public live data."""
import json, subprocess, time
from pathlib import Path

NOW=int(time.time())
START=NOW-NOW%300+300
WINDOWS=[START+300*i for i in range(50)]
OUT=Path("btc_5m_training_runs48_97"); OUT.mkdir(exist_ok=True)

def fetch(url):
 r=subprocess.run(["curl","-fsSL","--max-time","15",url],capture_output=True,text=True,check=True)
 return json.loads(r.stdout)
def market(epoch):
 slug=f"btc-updown-5m-{epoch}"
 for _ in range(12):
  x=fetch(f"https://gamma-api.polymarket.com/markets?slug={slug}")
  if x:return x[0]
  time.sleep(5)
 raise RuntimeError("market_not_available")
def book(token):
 x=fetch(f"https://clob.polymarket.com/book?token_id={token}")
 bids=[(float(v['price']),float(v['size'])) for v in x.get('bids',[])]
 asks=[(float(v['price']),float(v['size'])) for v in x.get('asks',[])]
 return {"bid":max((p for p,_ in bids),default=None),"ask":min((p for p,_ in asks),default=None),
         "bid_size":sum(s for _,s in bids),"ask_size":sum(s for _,s in asks)}
def coinbase_snapshot(epoch):
 depth=fetch("https://api.exchange.coinbase.com/products/BTC-USD/book?level=2")
 bids=[(float(v[0]),float(v[1])) for v in depth['bids']];asks=[(float(v[0]),float(v[1])) for v in depth['asks']]
 bn=sum(p*q for p,q in bids);an=sum(p*q for p,q in asks); imbalance=(bn-an)/(bn+an) if bn+an else 0
 trades=fetch("https://api.exchange.coinbase.com/products/BTC-USD/trades?limit=500")
 buy=sum(float(t['size'])*float(t['price']) for t in trades if t['side']=='sell')
 sell=sum(float(t['size'])*float(t['price']) for t in trades if t['side']=='buy')
 flow=(buy-sell)/(buy+sell) if buy+sell else 0
 candles=sorted(fetch("https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=60"),key=lambda v:v[0])
 eligible=[v for v in candles if int(v[0])>=epoch];ref=float((eligible or candles)[0][3]);current=float(candles[-1][4]);delta=current-ref
 top_bid=max(q for _,q in bids);top_ask=max(q for _,q in asks); large_ratio=(top_bid+1e-9)/(top_ask+1e-9)
 return {"source":"coinbase","reference":ref,"current":current,"delta":delta,"depth_imbalance":imbalance,"aggressor_flow":flow,
         "buy_notional":buy,"sell_notional":sell,"largest_bid_btc":top_bid,"largest_ask_btc":top_ask,"large_order_ratio":large_ratio}
def kraken_snapshot(epoch):
 depth=fetch("https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=100")['result']; pair=next(iter(depth.values()))
 bids=[(float(v[0]),float(v[1])) for v in pair['bids']];asks=[(float(v[0]),float(v[1])) for v in pair['asks']]
 bn=sum(p*q for p,q in bids);an=sum(p*q for p,q in asks);imbalance=(bn-an)/(bn+an) if bn+an else 0
 tr=fetch("https://api.kraken.com/0/public/Trades?pair=XBTUSD")['result'];rows=next(v for k,v in tr.items() if k!='last')
 buy=sum(float(v[0])*float(v[1]) for v in rows if v[3]=='b');sell=sum(float(v[0])*float(v[1]) for v in rows if v[3]=='s');flow=(buy-sell)/(buy+sell) if buy+sell else 0
 oh=fetch(f"https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1&since={epoch}")['result'];rows=next(v for k,v in oh.items() if k!='last')
 ref=float(rows[0][1]);current=float(rows[-1][4]);delta=current-ref
 top_bid=max(q for _,q in bids);top_ask=max(q for _,q in asks);large_ratio=(top_bid+1e-9)/(top_ask+1e-9)
 return {"source":"kraken","reference":ref,"current":current,"delta":delta,"depth_imbalance":imbalance,"aggressor_flow":flow,
         "buy_notional":buy,"sell_notional":sell,"largest_bid_btc":top_bid,"largest_ask_btc":top_ask,"large_order_ratio":large_ratio}
def spot_snapshot(epoch):
 try:return coinbase_snapshot(epoch)
 except Exception:return kraken_snapshot(epoch)
def save(state):
 tmp=OUT/"checkpoint.json.tmp"
 tmp.write_text(json.dumps(state,indent=2))
 tmp.replace(OUT/"checkpoint.json")
def resolve(slug):
 for _ in range(30):
  try:
   ev=fetch(f"https://gamma-api.polymarket.com/events?slug={slug}")
   ms=ev[0].get('markets',[]) if ev else []
   if not ms:
    ms=fetch(f"https://gamma-api.polymarket.com/markets?slug={slug}")
   if ms:
    pr=[float(v) for v in json.loads(ms[0]['outcomePrices'])]
    if pr[0]>=.99:return "UP",pr
    if pr[1]>=.99:return "DOWN",pr
  except Exception:pass
  time.sleep(10)
 return None,[]

def settle_and_train(o,state):
 if o.get('trained'):return
 winner,prices=resolve(o['slug']);o['winner']=winner;o['final_outcome_prices']=prices
 if not winner:return
 target=1 if winner=="UP" else -1
 before=list(state['signal_weights'])
 for i,sig in enumerate(o['signals']):
  if sig:state['signal_weights'][i]=round(min(2.,max(.25,state['signal_weights'][i]+(.08 if sig==target else -.08))),4)
 o['trained']=True
 state['training_history'].append({'run':o['run'],'winner':winner,'weights_before':before,'weights_after':list(state['signal_weights'])})
 if o['selection']=="NO_TRADE":o.update(result="no_trade",gross_pnl=0);return
 payout=o['shares'] if winner==o['selection'] else 0.;state['capital']+=payout
 o['result']="won" if payout else "lost";o['gross_pnl']=payout-o['stake']

state={"mode":"PAPER_ONLY","initial_capital":100.,"capital":100.,"orders":[],"errors":[],"real_orders":0,
       "signal_names":["btc_delta","depth_imbalance","aggressor_flow","polymarket_probability"],
       "signal_weights":[1.,1.,1.,1.],"training_history":[]}
for run,epoch in enumerate(WINDOWS,48):
 while time.time()<epoch+30:time.sleep(min(5,max(.2,epoch+30-time.time())))
 for prior in state['orders']:
  if not prior.get('trained') and time.time()>=prior['epoch']+315:
   settle_and_train(prior,state);save(state)
 slug=f"btc-updown-5m-{epoch}"
 try:
  m=market(epoch); tokens=json.loads(m['clobTokenIds']); probs=[float(v) for v in json.loads(m['outcomePrices'])]
  snap=spot_snapshot(epoch)
  signals=[]
  signals.append(1 if snap['delta']>3 else -1 if snap['delta']<-3 else 0)
  signals.append(1 if snap['depth_imbalance']>.05 else -1 if snap['depth_imbalance']<-.05 else 0)
  signals.append(1 if snap['aggressor_flow']>.05 else -1 if snap['aggressor_flow']<-.05 else 0)
  signals.append(1 if probs[0]>.54 else -1 if probs[1]>.54 else 0)
  weighted_score=sum(s*w for s,w in zip(signals,state['signal_weights']));score=sum(signals)
  side="UP" if weighted_score>0 else "DOWN" if weighted_score<0 else "NO_TRADE"
  confidence=abs(weighted_score)
  stake=5. if confidence>=3.4 else 3. if confidence>=2.5 else 2. if confidence>=1.9 else 0.
  if stake==0:side="NO_TRADE"
  token=tokens[0] if side=="UP" else tokens[1] if side=="DOWN" else None
  pmbook=book(token) if token else {}; entry=pmbook.get('ask')
  # Avoid expensive entries and never risk more simulated cash than remains.
  if not entry or entry>.62: side="NO_TRADE";stake=0.
  stake=min(stake,max(0.,state['capital']))
  order={"run":run,"epoch":epoch,"slug":slug,"market":m['question'],"selection":side,"stake":stake,"entry_price":entry,
         "shares":stake/entry if stake and entry else 0,"confidence_score":score,"weighted_score":weighted_score,
         "weights_used":list(state['signal_weights']),"signals":signals,
         "polymarket_up":probs[0],"polymarket_down":probs[1],"spot":snap,"polymarket_book":pmbook,"locked_at":time.time()}
  state['orders'].append(order);state['capital']-=stake;save(state)
 except Exception as e:
  state['errors'].append({"run":run,"stage":"entry","error":type(e).__name__,"detail":str(e)[:500]});save(state);continue
 # Low-frequency surveillance, persisted. Entry stays locked.
 order['surveillance']=[]
 while time.time()<epoch+305:
  try: order['surveillance'].append({"ts":time.time(),**spot_snapshot(epoch)});save(state)
  except Exception as e:state['errors'].append({"run":run,"stage":"monitor","error":type(e).__name__});save(state)
  time.sleep(30)

# Resolve remaining outcomes and finish adaptive training.
for o in state['orders']:
 settle_and_train(o,state)
 if not o.get('winner'):
  state['capital']+=o['stake'];o['result']="unresolved";o['gross_pnl']=0.
 save(state)
state['gross_pnl']=state['capital']-state['initial_capital'];state['completed_at']=time.time();save(state)
(OUT/"paper_result.json").write_text(json.dumps(state,indent=2));print(json.dumps(state,indent=2))
