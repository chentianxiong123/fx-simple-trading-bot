"""
演示：获取真实 PnL
"""
import time
from bot import FXBot
from fx_lib import open_position, close_position, get_positions, get_pnl_pct, get_candles, momentum


def run():
    bot = FXBot(headless=False)
    bot.reset()
    
    print("=" * 60)
    print("演示：获取真实 PnL")
    print("=" * 60)
    
    # 开 2 个仓位
    print("\n[1] 开 2 个仓位")
    open_position(bot, 'EUR/USD', 'long', 1000, 20)
    time.sleep(0.3)
    open_position(bot, 'GBP/USD', 'short', 1000, 20)
    time.sleep(0.5)
    
    # 获取 PnL
    print("\n[2] 获取 PnL")
    positions = get_positions(bot)
    print(f"  当前仓位: {list(positions.keys())}")
    
    for pair in ['EUR/USD', 'GBP/USD']:
        pnl = get_pnl_pct(bot, pair)
        print(f"  {pair}: {pnl*100:+.2f}%")
    
    # 监控 10 秒
    print("\n[3] 监控 10 秒")
    for i in range(20):
        time.sleep(0.5)
        pnls = {}
        for pair in ['EUR/USD', 'GBP/USD']:
            pnl = get_pnl_pct(bot, pair)
            if pnl is not None:
                pnls[pair] = pnl
        
        if pnls:
            print(f"  t={i*0.5:5.1f}s  " + "  ".join(f"{k}={v*100:+.2f}%" for k, v in pnls.items()))
    
    # 平仓
    print("\n[4] 平仓")
    for pair in ['EUR/USD', 'GBP/USD']:
        ok, pnl = close_position(bot, pair)
        if ok:
            print(f"  {pair}: pnl=${pnl:+.2f}")
    
    print("\n✓ 完成")
    bot.close()


if __name__ == "__main__":
    run()
