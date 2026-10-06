"""
最简单的策略: K 线动量
- 看最近 5 根 K 线, 涨则做多, 跌则做空
- 固定 30 秒平仓
- 2 个仓位
"""
import time
from bot import FXBot

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "EUR/CHF", "AUD/USD", "USD/CAD"]
MAX_SLOTS = 2
MARGIN = 1000
LEVERAGE = 20
HOLD_S = 30  # 固定持有 30 秒


def momentum(candles):
    """最近 5 根 K 线: 涨返回 1, 跌返回 -1, 平返回 0"""
    if len(candles) < 5:
        return 0
    recent = candles[-5:]
    first_close = recent[0]['close']
    last_close = recent[-1]['close']
    change = last_close - first_close
    if change > 0:
        return 1
    elif change < 0:
        return -1
    return 0


def close_pair(bot, pair_id):
    """关掉指定 pair 的仓位"""
    bot.frame.evaluate(r"""(pairId) => {
        const btns = Array.from(document.querySelectorAll('button'))
            .filter(b => b.textContent.trim() === '平仓');
        for (const btn of btns) {
            let el = btn.parentElement;
            for (let depth = 0; el && depth < 4; depth++) {
                if (el.textContent.includes(pairId)) {
                    btn.click();
                    return;
                }
                el = el.parentElement;
            }
        }
    }""", pair_id)
    time.sleep(0.5)
    bot.frame.evaluate(r"""() => {
        const c = document.getElementById('modalConfirm');
        if (c && c.offsetParent !== null) c.click();
    }""")
    time.sleep(0.3)


def run():
    bot = FXBot(headless=False)
    bot.reset()
    
    DURATION = 120
    
    print("=" * 60)
    print(f"K线动量策略 · {DURATION} 秒")
    print(f"{MAX_SLOTS} 仓位, {MARGIN}x margin, {LEVERAGE}x lever, 固定 {HOLD_S}s 平仓")
    print("=" * 60)
    
    # tracked: {pair_id: opened_at}
    tracked = {}
    closed_log = []
    
    initial = bot.state()
    initial_cash = initial['account']['cash']
    print(f"初始: ${initial_cash:.2f}\n")
    
    start = time.time()
    last_tick = 0
    
    try:
        while time.time() - start < DURATION:
            info = bot.tick_info()
            if info['last_tick_ms'] == last_tick:
                time.sleep(0.2)
                continue
            last_tick = info['last_tick_ms']
            now = time.time()
            s = bot.state()
            
            # 1. 到时间就平仓
            for pair_id, opened_at in list(tracked.items()):
                if now - opened_at >= HOLD_S:
                    print(f"\n⏱ [{pair_id}] 30s 到期平仓")
                    close_pair(bot, pair_id)
                    tracked.pop(pair_id, None)
                    # 读 pnl
                    time.sleep(0.2)
                    s2 = bot.state()
                    h = s2['account']['history']
                    if h:
                        closed_log.append({'pair': pair_id, 'pnl': h[0]['pnl']})
                        print(f"   pnl=${h[0]['pnl']:+.2f}")
            
            # 2. 有空位就开
            if len(s['account']['positions']) < MAX_SLOTS:
                for pair in PAIRS:
                    if pair in tracked:
                        continue
                    candles = s['candles'][pair]
                    direction = momentum(candles)
                    if direction == 0:
                        continue
                    
                    side = 'long' if direction == 1 else 'short'
                    print(f"\n▶ [{pair} {side}] momentum={direction}")
                    
                    bot.select_pair(pair)
                    time.sleep(0.15)
                    bot.set_margin(MARGIN)
                    time.sleep(0.05)
                    bot.set_leverage(LEVERAGE)
                    time.sleep(0.05)
                    bot.open_position(side)
                    time.sleep(0.4)
                    
                    # 确认
                    s2 = bot.state()
                    found = any(p['pair'] == pair for p in s2['account']['positions'])
                    if found:
                        tracked[pair] = time.time()
                    else:
                        print(f"   ⚠ open failed")
                    break  # 一次只开一笔
            
            # 状态
            if int(now - start) % 30 == 0 and (now - int(now - start)) < 1:
                wins = sum(1 for c in closed_log if c['pnl'] > 0)
                losses = sum(1 for c in closed_log if c['pnl'] <= 0)
                total = sum(c['pnl'] for c in closed_log)
                s3 = bot.state()
                print(f"\n── [{time.strftime('%H:%M:%S')}] cash=${s3['account']['cash']:.2f}  "
                      f"closed={len(closed_log)}(W{wins}/L{losses}) sum=${total:+.2f}")
            
            time.sleep(0.2)
    
    except KeyboardInterrupt:
        pass
    
    # 收尾
    print("\n--- 收尾 ---")
    for pair in list(tracked.keys()):
        close_pair(bot, pair)
        time.sleep(0.5)
        s = bot.state()
        h = s['account']['history']
        if h:
            closed_log.append({'pair': pair, 'pnl': h[0]['pnl']})
    
    final = bot.state()
    final_cash = final['account']['cash']
    
    print(f"\n{'='*60}")
    print(f"最终: ${final_cash:.2f}")
    print(f"盈亏: ${final_cash - initial_cash:+.2f} ({(final_cash/initial_cash-1)*100:+.2f}%)")
    if closed_log:
        wins = sum(1 for c in closed_log if c['pnl'] > 0)
        losses = sum(1 for c in closed_log if c['pnl'] <= 0)
        total = sum(c['pnl'] for c in closed_log)
        avg = total / len(closed_log)
        print(f"平仓: {len(closed_log)}  W{wins}/L{losses}  sum=${total:+.2f}  avg=${avg:+.2f}")
    
    bot.close()


if __name__ == "__main__":
    run()
