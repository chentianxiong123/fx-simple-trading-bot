"""
策略 v3: 使用 fx_lib，详细日志
- 固定 2 个 pair: EUR/USD, GBP/USD
- 每 3 秒扫描一次，打印每个 pair 的动量
"""
import time
from bot import FXBot
from fx_lib import (
    select_pair, open_position, close_position,
    get_positions, get_pnl_pct, get_candles, momentum
)

PAIRS = ['EUR/USD']  # 只玩一个
MAX_SLOTS = 1        # 一个仓位
MARGIN = 500         # 小保证金（低风险）
LEVERAGE = 20        # 正常杠杆
TAKE_PROFIT_PCT = 0.01   # +1% 就卖（快速止盈）
SCAN_INTERVAL = 1        # 每 1 秒扫描（高频）
MOOMENTUM_WINDOW = 3     # 看 3 根 K 线（灵敏）


def check_close(bot, tracked):
    """检查是否应该平仓 - 只有 TP，没有 SL，没有时间限制"""
    for pair, meta in list(tracked.items()):
        pnl_pct = get_pnl_pct(bot, pair)
        if pnl_pct is None:
            tracked.pop(pair, None)
            continue
        
        # 只有盈利才卖，亏的永远等
        if pnl_pct >= TAKE_PROFIT_PCT:
            print(f"\n⏹ [{pair}] TP({pnl_pct*100:+.2f}%)")
            ok, pnl = close_position(bot, pair)
            if ok:
                tracked.pop(pair, None)
                return {'pair': pair, 'pnl': pnl, 'reason': f'TP({pnl_pct*100:+.2f}%)'}
    return None


def check_open(bot, tracked):
    """检查是否应该开仓，返回 (side, direction) 或 None"""
    positions = get_positions(bot)
    if len(positions) >= MAX_SLOTS:
        return None
    
    for pair in PAIRS:
        if pair in tracked:
            continue
        if pair in positions:
            continue
        
        candles = get_candles(bot, pair)
        direction = momentum(candles, MOOMENTUM_WINDOW)
        if direction == 0:
            continue
        
        side = 'long' if direction == 1 else 'short'
        return side, direction, pair
    
    return None


def run():
    bot = FXBot(headless=False)
    bot.reset()
    
    DURATION = 180
    
    print("=" * 60)
    print(f"策略: {PAIRS}")
    print(f"TP={TAKE_PROFIT_PCT*100:.1f}%  (无止损，亏的永远等)")
    print("=" * 60)
    
    initial = bot.state()
    initial_cash = initial['account']['cash']
    print(f"初始: ${initial_cash:.2f}\n")
    
    tracked = {}
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
            
            # 1. 检查平仓
            result = check_close(bot, tracked)
            if result:
                closed_log.append(result)
                print(f"   pnl=${result['pnl']:+.2f}")
            
            # 2. 检查开仓
            if now - last_scan >= SCAN_INTERVAL:
                positions = get_positions(bot)
                empty_slots = MAX_SLOTS - len(positions)
                
                if empty_slots > 0:
                    last_scan = now
                    print(f"\n🔍 扫描 (空位={empty_slots}):")
                    
                    # 打印所有 pair 的动量
                    for pair in PAIRS:
                        if pair in tracked:
                            print(f"   {pair}: 已持有")
                        else:
                            candles = get_candles(bot, pair)
                            d = momentum(candles, MOOMENTUM_WINDOW)
                            print(f"   {pair}: momentum={d}")
                    
                    # 尝试开仓
                    result = check_open(bot, tracked)
                    if result:
                        side, direction, pair = result
                        print(f"\n▶ 开仓: {pair} {side} (momentum={direction})")
                        ok, entry = open_position(bot, pair, side, MARGIN, LEVERAGE)
                        if ok:
                            tracked[pair] = {'opened_at': time.time(), 'side': side}
                            print(f"   ✓ @ {entry:.5f}")
                        else:
                            print(f"   ⚠ 失败")
            
            # 3. 状态
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
