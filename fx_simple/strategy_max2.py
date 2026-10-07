"""
拉满玩法 v2: 借满20万 + 50x + 低频率趋势跟随 + 硬止损
解决测试9三个黑洞:
- 低频率(动量窗口22s确认+持仓90s) → 手续费降95%
- 硬止损 -1% (50x = -50%保证金, 封顶) → 浮亏可控
- TP +2% (50x = +100%保证金) → 盈亏比2:1
"""
import time, sys
sys.path.insert(0, '/tmp/fxbot/fx_simple')
from bot import FXBot
from fx_lib import open_position, close_position, get_positions, get_candles, momentum

PAIR = 'EUR/USD'
MARGIN = 10000
LEVERAGE = 50
TP = 0.02        # +2% 价格 → +100% 保证金
SL = -0.01       # -1% 价格 → -50% 保证金, 硬止损
TIME_LIMIT = 90  # 秒
MOM_WINDOW = 15  # ~22s 趋势确认
MAX_POS = 3
SCAN = 3         # 秒, 低频率扫描
DURATION = 600   # 10 分钟
LOAN = 200000


def borrow(bot, amount):
    bot.frame.evaluate("() => document.getElementById('borrowBtn').click()")
    time.sleep(0.8)
    bot.frame.evaluate("""(a) => {
        const el = document.getElementById('modalInput');
        if (!el) return false;
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(a));
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
        return true;
    }""", amount)
    time.sleep(0.3)
    bot.frame.evaluate("() => { const c = document.getElementById('modalConfirm'); if (c) c.click(); }")
    time.sleep(1.0)


def set_panel(bot, lev, margin):
    bot.frame.evaluate("""(v) => {
        const el = document.getElementById('leverageRange');
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(v)); el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
    }""", lev)
    time.sleep(0.3)
    bot.frame.evaluate("""(v) => {
        const el = document.getElementById('marginInput');
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(v)); el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
    }""", margin)
    time.sleep(0.3)


def run():
    bot = FXBot(headless=False)
    bot.reset()
    borrow(bot, LOAN)
    set_panel(bot, LEVERAGE, MARGIN)
    st = bot.state()
    print("=" * 60)
    print(f"拉满v2: 借${LOAN:,} + {LEVERAGE}x + ${MARGIN:,}/仓 × {MAX_POS}")
    print(f"cash=${st['account']['cash']:,.0f}  TP+2% SL-1% 持仓{TIME_LIMIT}s 动量{MOM_WINDOW}根")
    print("=" * 60)

    pos_times = {}
    closed = []
    start = time.time()
    last_scan = 0
    last_stats = 0

    try:
        while time.time() - start < DURATION:
            now = time.time()
            positions = get_positions(bot)

            # 持仓管理: TP / SL / TIME
            for i, pos in enumerate(positions):
                if i not in pos_times:
                    continue
                st2 = bot.state()
                pnl_pct = (pos['notional'] * pos['side'] * (st2['prices'][pos['pair']] / pos['entry'] - 1)) / pos['margin']
                reason = None
                if pnl_pct <= SL:
                    reason = 'SL'
                elif pnl_pct >= TP:
                    reason = 'TP'
                elif now - pos_times[i] >= TIME_LIMIT:
                    reason = 'TIME'
                if reason:
                    ok, pnl = close_position(bot, PAIR, i)
                    closed.append({'pnl': pnl, 'reason': reason, 'pct': pnl_pct})
                    print(f"⏹ [{reason}] {pnl_pct*100:+.2f}% → ${pnl:+,.0f} ({(now-pos_times[i]):.0f}s)")
                    # 位置下移
                    new_times = {}
                    for idx, t in pos_times.items():
                        new_times[idx - 1 if idx > i else idx] = t
                    pos_times = new_times
                    positions = get_positions(bot)
                    break

            # 开仓: 低频率动量
            if now - last_scan >= SCAN and len(positions) < MAX_POS:
                last_scan = now
                candles = get_candles(bot, PAIR, 20)
                d = momentum(candles, MOM_WINDOW)
                if d != 0:
                    side = 'long' if d == 1 else 'short'
                    ok, entry = open_position(bot, PAIR, side, MARGIN, LEVERAGE)
                    if ok:
                        new_pos = get_positions(bot)
                        pos_times[len(new_pos) - 1] = time.time()
                        print(f"▶ 开{side} @ {entry:.5f} 仓={len(new_pos)}")

            if now - last_stats >= 60:
                last_stats = now
                st3 = bot.state()
                wins = sum(1 for c in closed if c['pnl'] > 0)
                tot = sum(c['pnl'] for c in closed)
                print(f"── [{time.strftime('%H:%M:%S')}] cash=${st3['account']['cash']:,.0f} "
                      f"仓={len(positions)} 平仓={len(closed)}(W{wins}/L{len(closed)-wins}) 净=${tot:+,.0f}")
            time.sleep(0.5)
    finally:
        for i in range(len(get_positions(bot))):
            close_position(bot, PAIR, 0)
            time.sleep(0.5)

    st = bot.state()
    wins = sum(1 for c in closed if c['pnl'] > 0)
    tot = sum(c['pnl'] for c in closed)
    print("\n" + "=" * 60)
    print(f"最终 cash: ${st['account']['cash']:,.2f}  已实现净: ${tot:+,.0f}")
    print(f"平仓: {len(closed)}  W{wins}/L{len(closed)-wins}  debt=${st['account']['debt']:,.0f}")
    for c in closed:
        print(f"   [{c['reason']}] {c['pct']*100:+.2f}% ${c['pnl']:+,.0f}")
    bot.close()


if __name__ == '__main__':
    run()