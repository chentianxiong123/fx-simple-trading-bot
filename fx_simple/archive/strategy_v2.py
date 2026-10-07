"""
策略: 使用 fx_lib 的可靠函数
- 2 个仓位，固定 EUR/USD 和 GBP/USD
- 买入：动量信号
- 卖出：TP/SL/时间限制
"""
import time
from fx_lib import (
    select_pair, open_position, close_position,
    get_positions, get_pnl_pct, get_candles, momentum
)

PAIRS = ['EUR/USD', 'GBP/USD']
MAX_SLOTS = 2
MARGIN = 1000
LEVERAGE = 20
TAKE_PROFIT_PCT = 0.015   # +1.5%
STOP_LOSS_PCT = -0.05     # -5%
TIME_LIMIT_S = 60
SCAN_INTERVAL = 3
MOOMENTUM_WINDOW = 5


def should_close(pnl_pct, hold_s):
    """判断是否应该平仓"""
    if pnl_pct is None:
        return None
    if pnl_pct >= TAKE_PROFIT_PCT:
        return f'TP({pnl_pct*100:+.2f}%)'
    if pnl_pct <= STOP_LOSS_PCT:
        return f'SL({pnl_pct*100:+.2f}%)'
    if hold_s >= TIME_LIMIT_S:
        return f'TIME({hold_s:.0f}s)'
    return None


def should_open(bot, pair, tracked):
    """判断是否应该开仓"""
    if pair in tracked:
        return False
    positions = get_positions(bot)
    if pair in positions:
        return False
    
    candles = get_candles(bot, pair)
    direction = momentum(candles, MOOMENTUM_WINDOW)
    if direction == 0:
        return False
    
    side = 'long' if direction == 1 else 'short'
    return side, direction


def run():
    from bot import FXBot
    bot = FXBot(headless=False)
    bot.reset()
    
    DURATION = 180
    
    print("=" * 60)
    print(f"策略: {PAIRS}")
    print(f"TP={TAKE_PROFIT_PCT*100:.1f}%  SL={STOP_LOSS_PCT*100:.0f}%  TIME={TIME_LIMIT_S}s")
    print("=" * 60)
    
    initial = bot.state()
    initial_cash = initial['account']['cash']
    print(f"初始: ${initial_cash:.2f}\n")
    
    tracked = {}  # pair -> {'opened_at': t, 'side': 'long'/'short'}
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
            
            # ========== 1. 检查卖出 ==========
            for pair, meta in list(tracked.items()):
                pnl_pct = get_pnl_pct(bot, pair)
                if pnl_pct is None:
                    # 仓位不存在，移除
                    tracked.pop(pair, None)
                    continue
                
                hold_s = now - meta['opened_at']
                reason = should_close(pnl_pct, hold_s)
                
                if reason:
                    print(f"\n⏹ [{pair}] {reason}")
                    ok, pnl = close_position(bot, pair)
                    if ok:
                        tracked.pop(pair, None)
                        closed_log.append({'pair': pair, 'pnl': pnl, 'reason': reason})
                        print(f"   pnl=${pnl:+.2f}")
            
            # ========== 2. 检查买入 ==========
            if now - last_scan >= SCAN_INTERVAL:
                positions = get_positions(bot)
                if len(positions) < MAX_SLOTS:
                    last_scan = now
                    print(f"\n🔍 扫描 (空位={MAX_SLOTS - len(positions)}):")
                    
                    for pair in PAIRS:
                        result = should_open(bot, pair, tracked)
                        if result:
                            side, direction = result
                            print(f"   {pair}: momentum={direction}")
                            
                            ok, entry = open_position(bot, pair, side, MARGIN, LEVERAGE)
                            if ok:
                                tracked[pair] = {'opened_at': time.time(), 'side': side}
                                print(f"   ✓ 开仓成功 @ {entry:.5f}")
                            else:
                                print(f"   ⚠ 开仓失败")
                            break  # 一次只开一笔
                        else:
                            if pair in tracked:
                                print(f"   {pair}: 已持有")
                            else:
                                candles = get_candles(bot, pair)
                                d = momentum(candles, MOOMENTUM_WINDOW)
                                print(f"   {pair}: momentum={d}")
            
            # ========== 3. 状态打印 ==========
            if now - last_stats >= 30:
                last_stats = now
                wins = sum(1 for c in closed_log if c['pnl'] > 0)
                losses = sum(1 for c in closed_log if c['pnl'] <= 0)
                total = sum(c['pnl'] for c in closed_log)
                s = bot.state()
                print(f"\n── [{time.strftime('%H:%M:%S')}] cash=${s['account']['cash']:.2f}  "
                      f"active={len(tracked)}  closed={len(closed_log)}(W{wins}/L{losses}) "
                      f"sum=${total:+.2f}")
            
            time.sleep(0.2)
    
    except KeyboardInterrupt:
        pass
    
    # 收尾
    print("\n--- 收尾 ---")
    for pair in list(tracked.keys()):
        ok, pnl = close_position(bot, pair)
        if ok:
            closed_log.append({'pair': pair, 'pnl': pnl, 'reason': 'END'})
    
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
