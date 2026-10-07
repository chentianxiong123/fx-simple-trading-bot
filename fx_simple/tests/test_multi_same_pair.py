"""
测试：同一个 pair 能不能开多个仓位
"""
import time
from bot import FXBot
from fx_lib import open_position, get_positions


def run():
    bot = FXBot(headless=False)
    bot.reset()
    
    print("=" * 60)
    print("测试：EUR/USD 开 3 个仓位")
    print("=" * 60)
    
    # 开第 1 个
    print("\n[1] 开第 1 个")
    ok, entry1 = open_position(bot, 'EUR/USD', 'long', 500, 20)
    print(f"  ok={ok}, entry={entry1}")
    time.sleep(0.3)
    
    positions = get_positions(bot)
    print(f"  仓位数: {len(positions)}")
    
    # 开第 2 个（不切换 pair，直接开）
    print("\n[2] 开第 2 个")
    ok, entry2 = open_position(bot, 'EUR/USD', 'long', 500, 20)
    print(f"  ok={ok}, entry={entry2}")
    time.sleep(0.3)
    
    positions = get_positions(bot)
    print(f"  仓位数: {len(positions)}")
    if len(positions) > 0:
        pairs = [p['pair'] for p in bot.state()['account']['positions']]
        print(f"  pair 列表: {pairs}")
    
    # 开第 3 个
    print("\n[3] 开第 3 个")
    ok, entry3 = open_position(bot, 'EUR/USD', 'long', 500, 20)
    print(f"  ok={ok}, entry={entry3}")
    time.sleep(0.3)
    
    positions = get_positions(bot)
    print(f"  仓位数: {len(positions)}")
    
    # 检查所有仓位
    print("\n[4] 检查所有仓位")
    s = bot.state()
    for i, p in enumerate(s['account']['positions']):
        print(f"  [{i}] pair={p['pair']}, side={p['side']}, entry={p['entry']:.5f}, margin={p['margin']}")
    
    print("\n✓ 完成")
    bot.close()


if __name__ == "__main__":
    run()
