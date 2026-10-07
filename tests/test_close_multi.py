"""
验证 close_position 在 3+ 仓位时能正确关闭指定 pair
"""
import time
from bot import FXBot
from fx_lib import select_pair, open_position, close_position, get_positions, get_pnl_pct


def run():
    bot = FXBot(headless=False)
    bot.reset()
    
    print("=" * 60)
    print("验证: 3 个仓位，关闭中间那个")
    print("=" * 60)
    
    # 开 3 个仓位
    print("\n[1] 开 3 个仓位")
    ok, entry1 = open_position(bot, 'EUR/USD', 'long', 1000, 20)
    print(f"  EUR/USD: ok={ok}, entry={entry1:.5f}")
    time.sleep(0.3)
    
    ok, entry2 = open_position(bot, 'GBP/USD', 'short', 1000, 20)
    print(f"  GBP/USD: ok={ok}, entry={entry2:.5f}")
    time.sleep(0.3)
    
    ok, entry3 = open_position(bot, 'USD/JPY', 'long', 1000, 20)
    print(f"  USD/JPY: ok={ok}, entry={entry3:.5f}")
    time.sleep(0.5)
    
    # 验证 3 个仓位都在
    positions = get_positions(bot)
    print(f"\n[2] 当前仓位: {list(positions.keys())}")
    assert len(positions) == 3, f"仓位数量错误: {len(positions)}"
    print("  ✓ 通过")
    
    # 验证 get_pnl_pct 能获取每个仓位的 PnL
    print("\n[3] 获取每个仓位的 PnL")
    for pair in ['EUR/USD', 'GBP/USD', 'USD/JPY']:
        pnl = get_pnl_pct(bot, pair)
        print(f"  {pair}: {pnl*100:.2f}%" if pnl else f"  {pair}: None")
        assert pnl is not None, f"{pair} PnL 获取失败"
    print("  ✓ 通过")
    
    # 关闭中间的 GBP/USD
    print("\n[4] 关闭 GBP/USD (中间的)")
    ok, pnl = close_position(bot, 'GBP/USD')
    print(f"  关闭结果: ok={ok}, pnl=${pnl:.2f}")
    assert ok, "关闭失败"
    time.sleep(0.3)
    
    # 验证只有 EUR/USD 和 USD/JPY 还在
    positions = get_positions(bot)
    print(f"\n[5] 剩余仓位: {list(positions.keys())}")
    assert 'EUR/USD' in positions, "EUR/USD 不应该消失"
    assert 'USD/JPY' in positions, "USD/JPY 不应该消失"
    assert 'GBP/USD' not in positions, "GBP/USD 应该被关闭"
    print("  ✓ 通过 (GBP/USD 被正确关闭)")
    
    # 验证 history 里最后一条是 GBP/USD
    print("\n[6] 验证 history")
    s = bot.state()
    h = s['account']['history']
    print(f"  最新 history: pair={h[0]['pair']}, pnl=${h[0]['pnl']:.2f}")
    assert h[0]['pair'] == 'GBP/USD', "history 里最后一条不是 GBP/USD"
    print("  ✓ 通过")
    
    # 清理
    close_position(bot, 'EUR/USD')
    time.sleep(0.3)
    close_position(bot, 'USD/JPY')
    
    print("\n" + "=" * 60)
    print("✓ 3 仓位关闭测试通过")
    print("=" * 60)
    
    bot.close()


if __name__ == "__main__":
    run()
