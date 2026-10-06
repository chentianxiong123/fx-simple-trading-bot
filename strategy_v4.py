"""
策略 v4: 疯狂持仓
- 只玩 EUR/USD
- 高频开仓（每 1 秒）
- 只有 TP，没有 SL
- 亏的永远等，赚钱才卖
"""
import time
from bot import FXBot
from fx_lib import (
    open_position, close_position,
    get_positions, get_positions_dict,
    get_pnl_pct, get_candles, momentum
)

PAIR = 'EUR/USD'
MARGIN = 500
LEVERAGE = 20
TAKE_PROFIT_PCT = 0.01   # +1% 就卖
SCAN_INTERVAL = 1
MOOMENTUM_WINDOW = 3
MAX_POSITIONS = 5        # 最多 5 个仓位


def get_total_pnl(bot, positions):
    """计算所有仓位的总 PnL"""
    s = bot.state()
    total = 0
    for pos in positions:
        curr = s['prices'][pos['pair']]
        pnl = (pos['notional'] * pos['side'] * (curr / pos['entry'] - 1)) / pos['margin']
        total += pnl
    return total


def check_tp(bot, positions):
    """检查是否有仓位达到 TP，返回 (position, pnl_pct, index) 或 (None, None, None)"""
    for i, pos in enumerate(positions):
        curr = bot.state()['prices'][pos['pair']]
        pnl_pct = (pos['notional'] * pos['side'] * (curr / pos['entry'] - 1)) / pos['margin']
        if pnl_pct >= TAKE_PROFIT_PCT:
            return pos, pnl_pct, i
    return None, None, None


def run():
    bot = FXBot(headless=False)
    bot.reset()
    
    DURATION = 180
    
    print("=" * 60)
    print(f"策略: 疯狂持仓 {PAIR}")
    print(f"margin=${MARGIN}, lever={LEVERAGE}x, TP={TAKE_PROFIT_PCT*100:.1f}%")
    print(f"最多 {MAX_POSITIONS} 个仓位，每 {SCAN_INTERVAL}s 扫描")
    print("=" * 60)
    
    initial = bot.state()
    initial_cash = initial['account']['cash']
    print(f"初始: ${initial_cash:.2f}\n")
    
    closed_log = []
    last_scan = 0
    open_count = 0
    
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
            
            # 1. 检查 TP
            positions = get_positions(bot)
            pos_to_close, pnl_pct, close_index = check_tp(bot, positions)
            if pos_to_close:
                print(f"\n⏹ TP {pnl_pct*100:+.2f}% (index={close_index})")
                ok, pnl = close_position(bot, PAIR, close_index)
                if ok:
                    closed_log.append({'pair': PAIR, 'pnl': pnl, 'reason': f'TP({pnl_pct*100:+.2f}%)'})
                    print(f"   pnl=${pnl:+.2f}")
                # 关闭后重新获取
                positions = get_positions(bot)
            
            # 2. 检查开仓
            if now - last_scan >= SCAN_INTERVAL:
                if len(positions) < MAX_POSITIONS:
                    last_scan = now
                    
                    # 检查动量
                    candles = get_candles(bot, PAIR)
                    direction = momentum(candles, MOOMENTUM_WINDOW)
                    
                    if direction != 0:
                        side = 'long' if direction == 1 else 'short'
                        print(f"\n▶ 开仓: {PAIR} {side} (momentum={direction}, 仓位数={len(positions)})")
                        
                        ok, entry = open_position(bot, PAIR, side, MARGIN, LEVERAGE)
                        if ok:
                            open_count += 1
                            print(f"   ✓ @ {entry:.5f}")
                        else:
                            print(f"   ⚠ 失败")
            
            # 3. 状态
            if now - last_stats >= 30:
                last_stats = now
                positions = get_positions(bot)
                wins = sum(1 for c in closed_log if c['pnl'] > 0)
                losses = sum(1 for c in closed_log if c['pnl'] <= 0)
                total = sum(c['pnl'] for c in closed_log)
                s = bot.state()
                print(f"\n── [{time.strftime('%H:%M:%S')}] cash=${s['account']['cash']:.2f}  "
                      f"active={len(positions)}/{MAX_POSITIONS}  "
                      f"closed={len(closed_log)}(W{wins}/L{losses}) "
                      f"sum=${total:+.2f}  opened={open_count}")
            
            time.sleep(0.2)
    
    except KeyboardInterrupt:
        pass
    
    # 收尾
    print("\n--- 收尾 ---")
    positions = get_positions(bot)
    for pos in positions[:]:
        ok, pnl = close_position(bot, PAIR)
        if ok:
            closed_log.append({'pair': PAIR, 'pnl': pnl, 'reason': 'END'})
            positions = get_positions(bot)
        time.sleep(0.3)
    
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
    print(f"开仓次数: {open_count}")
    
    bot.close()


if __name__ == "__main__":
    run()
