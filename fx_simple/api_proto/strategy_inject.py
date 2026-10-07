"""
直调版策略: JS 注入 window.__game, 直接调用游戏内部函数
- 同一个策略参数 (15s 时间兜底 + TP 1% + 3 candles 动量 + MAX 5 仓)
- 交易走 __game.openPosition / __game.closePosition (一次 evaluate)
- 状态走 __game.getSim / __game.getState (一次 evaluate 拿全)
- 对比主线 DOM 模拟点击版本的性能差异
"""
import time, sys
sys.path.insert(0, '/tmp/fxbot')
from api_proto.bot_inject import FXBot

PAIR = 'EUR/USD'
MARGIN = 500
LEVERAGE = 20
TAKE_PROFIT_PCT = 0.01   # +1% 就卖
TIME_LIMIT_S = 15        # 15 秒时间兜底
SCAN_INTERVAL = 1
MOOMENTUM_WINDOW = 3
MAX_POSITIONS = 5        # 最多 5 个仓位

SNAPSHOT_JS = r"""() => {
    const g = window.__game;
    if (!g) return null;
    const sim = g.getSim();
    const st = g.getState();
    const prices = {};
    const candles = {};
    for (const [k, v] of Object.entries(sim)) {
        prices[k] = v.price;
        candles[k] = v.candles.slice(-20);
    }
    return {
        mode: st.mode,
        cash: st.cash,
        positions: st.positions.map(p => ({
            id: p.id, pair: p.pair, side: p.side === 'long' ? 1 : -1, entry: p.entry,
            margin: p.margin, leverage: p.leverage, notional: p.notional, opened: p.opened,
        })),
        prices, candles,
    };
}"""

OPEN_JS = r"""(m) => {
    const g = window.__game;
    const ret = g.openPosition(m.side);
    if (!ret) return null;
    return {id: ret.id, entry: ret.entry, side: ret.side};
}"""

CLOSE_JS = r"""(id) => {
    window.__game.closePosition(id, false);
    return true;
}"""


def snapshot(bot):
    return bot.frame.evaluate(SNAPSHOT_JS)


def open_fast(bot, side, margin, leverage):
    return bot.frame.evaluate(OPEN_JS, {'side': side, 'margin': margin, 'leverage': leverage})


def close_fast(bot, pos_id):
    bot.frame.evaluate(CLOSE_JS, pos_id)


def momentum(candles, window=3):
    if not candles or len(candles) < window:
        return 0
    recent = candles[-window:]
    change = recent[-1]['close'] - recent[0]['close']
    return 1 if change > 0 else (-1 if change < 0 else 0)


def pnl_pct(pos, price):
    return (pos['notional'] * pos['side'] * (price / pos['entry'] - 1)) / pos['margin']


def main():
    bot = FXBot(headless=False)
    # 不开 reset(): 每次启动都是全新干净账户($10000/0仓), reset 的 page.reload 反而引发 NaN 中间态

    DURATION = 180
    print("=" * 60)
    print(f"直调版策略: {PAIR}")
    print(f"margin=${MARGIN}, lever={LEVERAGE}x, TP={TAKE_PROFIT_PCT*100:.1f}%")
    print(f"最多 {MAX_POSITIONS} 个仓位, 15s 兜底, __game 直调")
    print("=" * 60)

    initial_cash = snapshot(bot)['cash']
    print(f"初始: ${initial_cash:.2f}\n")

    closed_log = []
    open_count = 0
    position_times = {}  # pos_id -> opened_at
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

            snap = snapshot(bot)
            if not snap:
                time.sleep(0.2)
                continue
            positions = snap['positions']

            # 1. TP / 时间兜底
            closed_any = False
            for pos in positions:
                price = snap['prices'].get(pos['pair'])
                if not price:
                    continue
                pp = pnl_pct(pos, price)
                reason = None
                opened_at = position_times.get(pos['id'])
                if opened_at and (now - opened_at) >= TIME_LIMIT_S:
                    reason = 'TIME'
                elif pp >= TAKE_PROFIT_PCT:
                    reason = 'TP'

                if reason:
                    closed_any = True
                    close_fast(bot, pos['id'])
                    pnl_dollars = pos['notional'] * pos['side'] * (price / pos['entry'] - 1)
                    closed_log.append({'pair': pos['pair'], 'pnl': pnl_dollars, 'reason': reason})
                    print(f"⏹ {reason} {pp*100:+.2f}% pnl=${pnl_dollars:+.2f}")
                    position_times.pop(pos['id'], None)
                else:
                    # 新仓位记录开仓时间（snapshot 没有 opened_at, 第一次见到就记）
                    if pos['id'] not in position_times:
                        position_times[pos['id']] = now

            if closed_any:
                snap = snapshot(bot)
                positions = snap['positions']

            # 2. 开仓
            if len(positions) < MAX_POSITIONS:
                candles = snap['candles'].get(PAIR, [])
                direction = momentum(candles, MOOMENTUM_WINDOW)
                if direction != 0:
                    side = 'long' if direction == 1 else 'short'
                    ret = open_fast(bot, side, MARGIN, LEVERAGE)
                    if ret:
                        open_count += 1
                        position_times[ret['id']] = time.time()
                        print(f"▶ 开仓 {side} @ {ret['entry']:.5f} (仓={len(positions)}+1)")
                    time.sleep(0.05)

            # 3. 状态
            if now - last_stats >= 30:
                last_stats = now
                snap2 = snapshot(bot)
                wins = sum(1 for c in closed_log if c['pnl'] > 0)
                losses = sum(1 for c in closed_log if c['pnl'] <= 0)
                total = sum(c['pnl'] for c in closed_log)
                print(f"── [{time.strftime('%H:%M:%S')}] cash=${snap2['cash']:.2f}  "
                      f"active={len(snap2['positions'])}/{MAX_POSITIONS}  "
                      f"closed={len(closed_log)}(W{wins}/L{losses}) sum=${total:+.2f} opened={open_count}")

            time.sleep(0.2)
    finally:
        # 收尾平仓
        snap = snapshot(bot)
        for pos in snap['positions']:
            close_fast(bot, pos['id'])
        time.sleep(0.5)

    wins = sum(1 for c in closed_log if c['pnl'] > 0)
    losses = sum(1 for c in closed_log if c['pnl'] <= 0)
    total = sum(c['pnl'] for c in closed_log)
    final = snapshot(bot)
    print("\n" + "=" * 60)
    print(f"最终: ${final['cash']:.2f}")
    print(f"盈亏: ${final['cash'] - initial_cash:+.2f} ({(final['cash'] - initial_cash) / initial_cash * 100:+.2f}%)")
    print(f"平仓: {len(closed_log)}  W{wins}/L{losses}  sum=${total:+.2f}  avg=${total/max(len(closed_log),1):+.2f}")
    print(f"开仓次数: {open_count}")
    bot.close()


if __name__ == '__main__':
    main()