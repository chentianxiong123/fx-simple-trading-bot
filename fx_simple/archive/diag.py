"""
诊断: 开 1 个仓位, 每 tick 打 PnL, 看 TP/SL 到底哪个触发
"""
import time
import math
from bot import FXBot

bot = FXBot(headless=False)
bot.reset()

print("=" * 60)
print("诊断: 20x + $1000 margin, 1 个仓位")
print("每 tick 打 PnL, 看 TP(+1.5%) / SL(-3%) 到底触发哪个")
print("=" * 60)

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "EUR/CHF", "AUD/USD", "USD/CAD"]

def drift(pair_idx):
    return math.sin(time.time() * 1000 / 13000 + pair_idx * 2) * 0.00036

# 选漂移最大的 pair
pair = max(PAIRS, key=lambda p: abs(drift(PAIRS.index(p))))
d = drift(PAIRS.index(pair))
direction = 1 if d > 0 else -1
side = 'long' if direction == 1 else 'short'
print(f"\n选 pair={pair}, drift={d*10000:+.2f}bp, direction={side}")

# 开仓
bot.select_pair(pair)
time.sleep(0.2)
bot.set_margin(1000)
time.sleep(0.1)
bot.set_leverage(20)
time.sleep(0.1)
bot.open_position(side)
time.sleep(0.5)

s = bot.state()
pos = s['account']['positions'][0]
entry = pos['entry']
margin = pos['margin']
notional = pos['notional']
print(f"入场: {entry:.5f}  margin=${margin}  notional=${notional}")
print(f"当前价格: {s['prices'][pair]:.5f}")
print(f"每 1bp 价格变动 = {notional * 0.0001 / margin * 100:.3f}% margin")
print()

# 每 tick 监控
last_tick = 0
start = time.time()
max_pnl = 0
min_pnl = 0
ticks = 0

try:
    while time.time() - start < 40:
        info = bot.tick_info()
        if info['last_tick_ms'] != last_tick:
            last_tick = info['last_tick_ms']
            ticks += 1
            s = bot.state()
            if not s['account']['positions']:
                print(f"\n[tick #{ticks}] 仓位已消失（可能是 TP/SL 触发）")
                h = s['account']['history']
                if h:
                    print(f"  最后 PnL: ${h[0]['pnl']:.2f}  reason={h[0].get('reason','?')}")
                break
            pos = s['account']['positions'][0]
            curr = s['prices'][pair]
            move_bp = (curr / entry - 1) * 10000 * direction
            pnl_pct = (notional * direction * (curr / entry - 1) / margin) * 100
            
            max_pnl = max(max_pnl, pnl_pct)
            min_pnl = min(min_pnl, pnl_pct)
            
            flag = ""
            if pnl_pct >= 1.5: flag = " ⬆ TP!"
            if pnl_pct <= -3.0: flag = " ⬇ SL!"
            
            print(f"[t+{time.time()-start:5.1f}s #{ticks:2d}] "
                  f"price={curr:.5f}  move={move_bp:+6.2f}bp  "
                  f"pnl={pnl_pct:+6.2f}%{flag}")
        time.sleep(0.2)
except KeyboardInterrupt:
    pass

print(f"\n40s 结束: max_pnl={max_pnl:+.2f}%  min_pnl={min_pnl:+.2f}%")
print(f"  TP 阈值 +1.5%  SL 阈值 -3%")

# 收尾平仓
s = bot.state()
if s['account']['positions']:
    bot.frame.evaluate("""() => {
        const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '平仓');
        if (btn) btn.click();
    }""")
    time.sleep(0.5)
    bot.frame.evaluate("""() => {
        const c = document.getElementById('modalConfirm');
        if (c && c.offsetParent !== null) c.click();
    }""")
    time.sleep(0.3)

final = bot.state()
print(f"\n最终 cash: ${final['account']['cash']:.2f}")

bot.close()
