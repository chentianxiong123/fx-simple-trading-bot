"""打开游戏, 截图几个画面充实仓库文档"""
import time, sys, os
sys.path.insert(0, '/tmp/fxbot')
from bot import FXBot
from fx_lib import open_position, get_positions

OUT = '/tmp/fxbot/docs/screenshots'
os.makedirs(OUT, exist_ok=True)

def main():
    bot = FXBot(headless=False)
    time.sleep(6)

    # 1. 主界面（模拟账户 + 盘面）
    bot.frame.frame_element().screenshot(path=f"{OUT}/01_main.png")
    print("✅ 01_main.png 主界面")

    # 2. 打开一个多单
    ok, entry = open_position(bot, 'EUR/USD', 'long', 500, 20)
    print(f"开仓 long @ {entry} ok={ok}")
    time.sleep(3)
    bot.frame.frame_element().screenshot(path=f"{OUT}/02_position_long.png")
    print("✅ 02_position_long.png 持仓中")

    # 3. 再开一个空单
    ok2, entry2 = open_position(bot, 'EUR/USD', 'short', 500, 20)
    print(f"开仓 short @ {entry2} ok={ok2}")
    time.sleep(3)
    bot.frame.frame_element().screenshot(path=f"{OUT}/03_two_positions.png")
    print("✅ 03_two_positions.png 双仓位")

    # 4. 显示当前持仓统计
    pos = get_positions(bot)
    print(f"当前持仓: {len(pos)} 个")
    for p in pos:
        print(f"  {p['pair']} side={p['side']} entry={p['entry']:.5f} margin={p['margin']}")

    bot.close()
    print(f"\n截图已保存到 {OUT}/")

if __name__ == '__main__':
    main()