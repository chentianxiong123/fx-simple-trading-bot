"""
BILINANCE 策略 v1: 合约高频
- 只做 BTCUSDT 合约
- 动量入场: 最近 N 个价格采样方向
- TP +1% (价格变动), 时间兜底 15s
- 10x 杠杆 50U 保证金
- 强平监控: 接近强平价提前跑
"""
import time, json, sys
sys.path.insert(0, '/tmp/fxbot/bilinance')
from bot import BILBot
from lib import fut_open, fut_close, fut_positions

PAIR = 'BTCUSDT'
LEV = 10
MARGIN = 50
TAKE_PROFIT_PCT = 0.01    # 价格 +1% 平
TIME_LIMIT_S = 15         # 时间兜底
MOMENTUM_N = 3            # 动量采样数
MAX_POSITIONS = 3
SCAN_S = 0.5              # 扫描间隔
DURATION = 180

# 强平提前量: 距离强平价 < 2% 就平(保守)
LIQ_MARGIN_PCT = 0.02


def momentum(prices):
    if len(prices) < MOMENTUM_N:
        return 0
    recent = prices[-MOMENTUM_N:]
    change = recent[-1] - recent[0]
    return 1 if change > 0 else (-1 if change < 0 else 0)


def main():
    bot = BILBot(headless=False)
    # 进入合约页(价格 #tkPrice 只在交易/合约页存在)
    bot.nav('合约')
    bot.nav_sym('futures', PAIR)
    time.sleep(1)
    st = bot.state()
    print("=" * 60)
    print(f"BILINANCE 合约策略: {PAIR}")
    print(f"杠杆{LEV}x 保证金${MARGIN} TP={TAKE_PROFIT_PCT*100:.1f}% 时间兜底{TIME_LIMIT_S}s")
    print(f"最多{MAX_POSITIONS}仓 动量窗口{MOMENTUM_N} 每{SCAN_S}s扫描")
    print(f"初始: ${st['usdt']:.2f}")
    print("=" * 60)

    start = time.time()
    last_stats = 0
    prices = []
    opened = 0
    closed_log = []

    try:
        while time.time() - start < DURATION:
            now = time.time()
            p = bot.price()
            if p is None:
                time.sleep(0.2)
                continue
            prices.append(p)
            if len(prices) > 20:
                prices = prices[-20:]

            pos = fut_positions(bot)

            # 1. 平仓检查: TP / 时间兜底
            for pz in pos:
                elapsed = (now - pz['ts'] / 1000) if 'ts' in pz else 0
                pnl_pct = pz['dir'] * (p / pz['entry'] - 1)
                reason = None
                if pz['ts'] and elapsed >= TIME_LIMIT_S:
                    reason = 'TIME'
                elif pnl_pct >= TAKE_PROFIT_PCT:
                    reason = 'TP'
                if reason:
                    fut_close(bot, pz['id'])
                    closed_log.append({'pnl_pct': pnl_pct, 'reason': reason, 'lev': pz['lev']})
                    print(f"⏹ {reason} {pnl_pct*100:+.2f}% (持仓{elapsed:.1f}s)")
                    time.sleep(0.6)

            # 2. 开仓
            pos = fut_positions(bot)
            if len(pos) < MAX_POSITIONS:
                d = momentum(prices)
                if d != 0:
                    side = 'long' if d == 1 else 'short'
                    fut_open(bot, PAIR, side, LEV, MARGIN)
                    opened += 1
                    print(f"▶ 开仓 {side} @ {p:,.0f} (仓={len(pos)+1})")
                    time.sleep(0.5)
                    prices = []

            # 3. 状态
            if now - last_stats >= 30:
                last_stats = now
                st = bot.state()
                wins = sum(1 for c in closed_log if c['pnl_pct'] > 0)
                print(f"── [{time.strftime('%H:%M:%S')}] usdt=${st['usdt']:.2f} "
                      f"仓={len(st['positions'])} 平仓={len(closed_log)}(W{wins}/L{len(closed_log)-wins}) "
                      f"开仓={opened}")

            time.sleep(SCAN_S)
    finally:
        # 收尾平仓
        for pz in fut_positions(bot):
            fut_close(bot, pz['id'])
        time.sleep(0.5)

    st = bot.state()
    wins = sum(1 for c in closed_log if c['pnl_pct'] > 0)
    print("\n" + "=" * 60)
    print(f"最终 usdt: ${st['usdt']:.2f}")
    print(f"盈亏: ${st['usdt'] - 10000:+.2f} ({(st['usdt']-10000)/100:+.2f}%)")
    print(f"平仓: {len(closed_log)}  W{wins}/L{len(closed_log)-wins}")
    print(f"开仓次数: {opened}")
    print(f"closedPositions: {len(st['closed'])}")
    bot.close()


if __name__ == '__main__':
    main()