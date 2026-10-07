"""监控行情: 记录每秒所有币价格变动, 看新闻冲击跳变 vs 普通波动分布"""
import time, json, sys
sys.path.insert(0, '/tmp/fxbot/bilinance')
from bot import BILBot

def main():
    bot = BILBot(headless=False)
    bot.nav('行情')
    time.sleep(1)

    print("采样 90 秒所有币价格变动(每秒)...")
    prev = bot.all_prices()
    max_jumps = {}   # sym -> (max_pct, time)
    jump_hist = []   # 所有 >0.15% 的跳变
    start = time.time()

    while time.time() - start < 90:
        time.sleep(1.0)
        cur = bot.all_prices()
        if not cur or not prev:
            prev = cur
            continue
        for sym, p in cur.items():
            if sym in prev and prev[sym] > 0:
                chg = (p / prev[sym] - 1) * 100
                if abs(chg) > 0.15:
                    jump_hist.append((time.strftime('%H:%M:%S'), sym, round(chg, 3)))
                    if sym not in max_jumps or abs(chg) > abs(max_jumps[sym][0]):
                        max_jumps[sym] = (chg, time.strftime('%H:%M:%S'))
        prev = cur

    print(f"\n=== 最大单秒跳变 (>0.15%) ===")
    for sym, (chg, t) in sorted(max_jumps.items(), key=lambda x: -abs(x[1][0])):
        print(f"  {sym:10s} {chg:+6.3f}% @ {t}")

    big = [j for j in jump_hist if abs(j[2]) > 0.5]
    print(f"\n全部 >0.15% 跳变: {len(jump_hist)} 次")
    print(f">0.5% (疑似新闻冲击): {len(big)} 次")
    for j in big[:15]:
        print(f"  {j}")
    bot.close()

if __name__ == '__main__':
    main()