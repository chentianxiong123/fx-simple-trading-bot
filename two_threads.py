"""
两线程策略:
- 买入线程: 扫描动量信号, 有空位就开仓
- 卖出线程: 实时监控所有仓位, 赚了就卖 (TP/SL)
"""
import time
import threading
from bot import FXBot

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "EUR/CHF", "AUD/USD", "USD/CAD"]
MAX_SLOTS = 2
MARGIN = 1000
LEVERAGE = 20

# 卖出参数
TAKE_PROFIT_PCT = 0.015   # 浮盈 1.5% 就卖
STOP_LOSS_PCT = -0.08     # 浮亏 8% 止损
TIME_LIMIT_S = 60         # 60 秒超时兜底

# 买入参数
SCAN_INTERVAL = 3         # 买入线程每 3 秒扫一次
MOOMENTUM_WINDOW = 5      # 看最近 5 根 K 线


lock = threading.Lock()
tracked = {}  # pair_id -> {'opened_at': t, 'side': 1/-1}
closed_log = []
stop_flag = threading.Event()


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


def buyer(bot):
    """买入线程: 扫描动量, 有空位就开"""
    print("🔴 买入线程启动")
    while not stop_flag.is_set():
        try:
            with lock:
                active = set(tracked.keys())
            
            # 有空位才扫
            if len(active) >= MAX_SLOTS:
                time.sleep(SCAN_INTERVAL)
                continue
            
            s = bot.state()
            for pair in PAIRS:
                if pair in active:
                    continue
                # 再次确认 game 里没有这个仓位
                if any(p['pair'] == pair for p in s['account']['positions']):
                    continue
                
                candles = s['candles'][pair]
                direction = momentum(candles)
                if direction == 0:
                    continue
                
                side = 'long' if direction == 1 else 'short'
                print(f"\n▶ 买入线程: [{pair} {side}] momentum={direction}")
                
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
                    with lock:
                        tracked[pair] = {'opened_at': time.time(), 'side': direction}
                    print(f"   ✓ 开仓成功")
                else:
                    print(f"   ⚠ 开仓失败")
                break  # 一次只开一笔
            
            time.sleep(SCAN_INTERVAL)
        except Exception as e:
            print(f"   ❌ 买入线程错误: {e}")
            time.sleep(2)


def seller(bot):
    """卖出线程: 实时监控, 触发 TP/SL/超时 就平"""
    print("🟢 卖出线程启动")
    while not stop_flag.is_set():
        try:
            with lock:
                pairs_to_check = list(tracked.keys())
            
            if not pairs_to_check:
                time.sleep(0.5)
                continue
            
            s = bot.state()
            positions = {p['pair']: p for p in s['account']['positions']}
            
            for pair in pairs_to_check:
                pos = positions.get(pair)
                if not pos:
                    # 仓位不见了 (可能爆仓或被手动平)
                    with lock:
                        tracked.pop(pair, None)
                    continue
                
                now = time.time()
                entry_time = tracked[pair]['opened_at']
                hold_s = now - entry_time
                
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
                    print(f"\n⏹ 卖出线程: [{pair}] {reason}")
                    close_pair(bot, pair)
                    with lock:
                        tracked.pop(pair, None)
                    time.sleep(0.3)
                    s2 = bot.state()
                    h = s2['account']['history']
                    if h:
                        with lock:
                            closed_log.append({'pair': pair, 'pnl': h[0]['pnl'], 'reason': reason})
                        print(f"   pnl=${h[0]['pnl']:+.2f}")
            
            time.sleep(0.5)  # 卖出线程每 0.5 秒扫一次
        except Exception as e:
            print(f"   ❌ 卖出线程错误: {e}")
            time.sleep(2)


def stats_printer(bot):
    """每 15 秒打印一次状态"""
    while not stop_flag.is_set():
        time.sleep(15)
        if stop_flag.is_set():
            break
        with lock:
            wins = sum(1 for c in closed_log if c['pnl'] > 0)
            losses = sum(1 for c in closed_log if c['pnl'] <= 0)
            total = sum(c['pnl'] for c in closed_log)
            n_active = len(tracked)
        s = bot.state()
        print(f"\n── [{time.strftime('%H:%M:%S')}] cash=${s['account']['cash']:.2f}  "
              f"active={n_active}  closed={len(closed_log)}(W{wins}/L{losses}) "
              f"sum=${total:+.2f}")


def run():
    bot = FXBot(headless=False)
    bot.reset()
    
    DURATION = 180
    
    print("=" * 60)
    print(f"两线程策略 · {DURATION} 秒")
    print(f"{MAX_SLOTS} 仓位, margin=${MARGIN}, lever={LEVERAGE}x")
    print(f"TP={TAKE_PROFIT_PCT*100:.1f}%  SL={STOP_LOSS_PCT*100:.0f}%  TIME={TIME_LIMIT_S}s")
    print("=" * 60)
    
    initial = bot.state()
    initial_cash = initial['account']['cash']
    print(f"初始: ${initial_cash:.2f}\n")
    
    buyer_t = threading.Thread(target=buyer, args=(bot,), daemon=True)
    seller_t = threading.Thread(target=seller, args=(bot,), daemon=True)
    stats_t = threading.Thread(target=stats_printer, args=(bot,), daemon=True)
    
    buyer_t.start()
    seller_t.start()
    stats_t.start()
    
    start = time.time()
    while time.time() - start < DURATION:
        time.sleep(1)
    
    stop_flag.set()
    buyer_t.join(timeout=5)
    seller_t.join(timeout=5)
    stats_t.join(timeout=2)
    
    # 收尾
    print("\n--- 收尾 ---")
    with lock:
        remaining = list(tracked.keys())
    for pair in remaining:
        close_pair(bot, pair)
        time.sleep(0.5)
        s = bot.state()
        h = s['account']['history']
        if h:
            with lock:
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
        # 按 reason 分组
        from collections import defaultdict
        by_reason = defaultdict(list)
        for c in closed_log:
            r = c['reason'].split('(')[0]
            by_reason[r].append(c['pnl'])
        print(f"按原因: ", end='')
        for r, pnls in by_reason.items():
            print(f"{r}: {len(pnls)}笔 sum=${sum(pnls):+.2f} ", end='')
        print()
    
    bot.close()


if __name__ == "__main__":
    run()
