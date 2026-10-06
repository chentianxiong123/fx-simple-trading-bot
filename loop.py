"""
单线程双职责:
- 每个循环先检查卖出 (TP/SL/超时)
- 再检查买入 (动量信号)
"""
import time
from bot import FXBot

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "EUR/CHF", "AUD/USD", "USD/CAD"]
MAX_SLOTS = 2
MARGIN = 1000
LEVERAGE = 20

TAKE_PROFIT_PCT = 0.015   # +1.5% 卖
STOP_LOSS_PCT = -0.05     # -5% 止损
TIME_LIMIT_S = 60
SCAN_EVERY = 3            # 每 3 秒扫一次买入
MOOMENTUM_WINDOW = 5


def momentum(candles):
    if len(candles) < MOOMENTUM_WINDOW:
        return 0
    recent = candles[-MOOMENTUM_WINDOW:]
    change = recent[-1]['close'] - recent[0]['close']
    if change > 0:
        return 1
    elif change < 0:
        return -1
    return 0


def close_pair(bot, pair_id):
    """关闭指定 pair 的仓位。只检查直接父元素 (position-row), 不向上爬。"""
    bot.frame.evaluate(r"""(pairId) => {
        const btns = Array.from(document.querySelectorAll('button'))
            .filter(b => b.textContent.trim() === '平仓');
        for (const btn of btns) {
            // 只查直接父元素 (position-row)
            const el = btn.parentElement;
            if (el && el.className.includes('position-row') && el.textContent.includes(pairId)) {
                btn.click();
                return {ok: true, pair: pairId};
            }
        }
        return {ok: false};
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
    
    DURATION = 180
    
    print("=" * 60)
    print(f"单线程双职责 · {DURATION} 秒")
    print(f"{MAX_SLOTS} 仓位, margin=${MARGIN}, lever={LEVERAGE}x")
    print(f"TP={TAKE_PROFIT_PCT*100:.1f}%  SL={STOP_LOSS_PCT*100:.0f}%  TIME={TIME_LIMIT_S}s")
    print("=" * 60)
    
    initial = bot.state()
    initial_cash = initial['account']['cash']
    print(f"初始: ${initial_cash:.2f}\n")
    
    tracked = {}  # pair -> {'opened_at': t, 'side': 1/-1}
    closed_log = []
    last_scan = 0
    
    start = time.time()
    last_tick = 0
    last_stats = 0
    
    try:
        while time.time() - start < DURATION:
            info = bot.tick_info()
            if info['last_tick_ms'] == last_tick:
                time.sleep(0.2)
                continue
            last_tick = info['last_tick_ms']
            now = time.time()
            s = bot.state()
            
            # ========== 1. 检查卖出 ==========
            for pair, meta in list(tracked.items()):
                pos = next((p for p in s['account']['positions'] if p['pair'] == pair), None)
                if not pos:
                    tracked.pop(pair, None)
                    continue
                
                hold_s = now - meta['opened_at']
                curr = s['prices'][pair]
                pnl_pct = (pos['notional'] * pos['side'] * 
                          (curr / pos['entry'] - 1)) / pos['margin']
                
                reason = None
                if pnl_pct >= TAKE_PROFIT_PCT:
                    reason = f'TP({pnl_pct*100:+.2f}%)'
                elif pnl_pct <= STOP_LOSS_PCT:
                    reason = f'SL({pnl_pct*100:+.2f}%)'
                elif hold_s >= TIME_LIMIT_S:
                    reason = f'TIME({hold_s:.0f}s, pnl={pnl_pct*100:+.2f}%)'
                
                if reason:
                    print(f"\n⏹ [{pair}] {reason}")
                    close_pair(bot, pair)
                    tracked.pop(pair, None)
                    time.sleep(0.2)
                    s2 = bot.state()
                    h = s2['account']['history']
                    if h:
                        closed_log.append({'pair': pair, 'pnl': h[0]['pnl'], 'reason': reason})
                        print(f"   pnl=${h[0]['pnl']:+.2f}")
                    s = s2  # 刷新 state
            
            # ========== 2. 检查买入 (每 SCAN_EVERY 秒) =========="
            if now - last_scan >= SCAN_EVERY and len(s['account']['positions']) < MAX_SLOTS:
                last_scan = now
                # 打印所有 pair 的动量
                print(f"\n🔍 扫描 (空位={MAX_SLOTS - len(s['account']['positions'])}):")
                for pair in PAIRS:
                    if pair in tracked:
                        print(f"   {pair}: 已在持有")
                        continue
                    if any(p['pair'] == pair for p in s['account']['positions']):
                        print(f"   {pair}: game 里已有")
                        continue
                    candles = s['candles'][pair]
                    direction = momentum(candles)
                    print(f"   {pair}: momentum={direction}")
                
                for pair in PAIRS:
                    if pair in tracked:
                        continue
                    if any(p['pair'] == pair for p in s['account']['positions']):
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
                    
                    s2 = bot.state()
                    found = any(p['pair'] == pair for p in s2['account']['positions'])
                    if found:
                        tracked[pair] = {'opened_at': time.time(), 'side': direction}
                        print(f"   ✓ 开仓成功")
                    else:
                        print(f"   ⚠ 开仓失败")
                    s = s2
                    break
            
            # ========== 3. 状态打印 ==========
            if now - last_stats >= 30:
                last_stats = now
                wins = sum(1 for c in closed_log if c['pnl'] > 0)
                losses = sum(1 for c in closed_log if c['pnl'] <= 0)
                total = sum(c['pnl'] for c in closed_log)
                print(f"\n── [{time.strftime('%H:%M:%S')}] cash=${s['account']['cash']:.2f}  "
                      f"active={len(tracked)}  closed={len(closed_log)}(W{wins}/L{losses}) "
                      f"sum=${total:+.2f}")
            
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
            closed_log.append({'pair': pair, 'pnl': h[0]['pnl'], 'reason': 'END'})
    
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
        print(f"平仓: {len(closed_log)}  W{wins}/L{losses}  "
              f"sum=${total:+.2f}  avg=${avg:+.2f}")
    
    bot.close()


if __name__ == "__main__":
    run()
