"""
狠家伙策略: 借贷20万 + 杠杆100x + 满仓梭哈 + 一直玩
- reset 干净账户 → 借 $200,000 (cash→21万)
- 杠杆 100x, 保证金 $10,000/仓, 开满 5 仓
- TP +1% / 15s 时间兜底 / 动量开仓
- 长跑 DURATION 可配
"""
import time, sys
sys.path.insert(0, '/tmp/fxbot/fx_simple')
from bot import FXBot
from fx_lib import open_position, close_position, get_positions, get_candles, momentum

PAIR = 'EUR/USD'
MARGIN = 10000        # 每仓保证金 1万
LEVERAGE = 100        # 杠杆拉满
TAKE_PROFIT_PCT = 0.01
TIME_LIMIT_S = 15
SCAN_INTERVAL = 1
MOOMENTUM_WINDOW = 3
MAX_POSITIONS = 5
DURATION = 1800       # 30 分钟一直玩

LOAN_AMOUNT = 200000  # 借 20 万


def borrow(bot, amount):
    """通过游戏弹窗借贷款"""
    bot.frame.evaluate("() => document.getElementById('borrowBtn').click()")
    time.sleep(0.8)
    ok = bot.frame.evaluate("""(a) => {
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
    return ok


def check_tp(bot, positions, position_times):
    now = time.time()
    for i, pos in enumerate(positions):
        curr = bot.state()['prices'][pos['pair']]
        pnl_pct = (pos['notional'] * pos['side'] * (curr / pos['entry'] - 1)) / pos['margin']
        if pos.get('opened_at') and (now - pos['opened_at']) >= TIME_LIMIT_S:
            return pos, pnl_pct, i, 'TIME'
        if pnl_pct >= TAKE_PROFIT_PCT:
            return pos, pnl_pct, i, 'TP'
    return None, None, None, None


def run():
    bot = FXBot(headless=False)
    bot.reset()

    print("=" * 60)
    print("🔥 狠家伙: 借贷20万 + 100x + 梭哈")
    print(f"margin=${MARGIN}/仓 × {MAX_POSITIONS}仓, 杠杆{LEVERAGE}x, TP={TAKE_PROFIT_PCT*100:.0f}%")
    print("=" * 60)

    # 1. 借贷
    borrow(bot, LOAN_AMOUNT)
    st = bot.state()
    cash = st['account']['cash']
    print(f"借贷后 cash=${cash:,.2f} (含贷款)")
    if cash < 100000:
        print(f"⚠ 借贷失败? cash=${cash}")
        bot.close()
        return

    # 2. 设置面板: 杠杆 + 保证金
    bot.frame.evaluate("""(v) => {
        const el = document.getElementById('leverageRange');
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(v)); el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
    }""", LEVERAGE)
    time.sleep(0.3)
    bot.frame.evaluate("""(v) => {
        const el = document.getElementById('marginInput');
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(v)); el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
    }""", MARGIN)
    time.sleep(0.3)
    print(f"面板: 杠杆{LEVERAGE}x, 保证金${MARGIN}\n")

    closed_log = []
    last_scan = 0
    open_count = 0
    position_times = {}
    start = time.time()
    last_tick = 0
    last_stats = 0
    interest_paid = 0

    try:
        while time.time() - start < DURATION:
            info = bot.tick_info()
            if info['last_tick_ms'] == last_tick:
                time.sleep(0.2)
                continue
            last_tick = info['last_tick_ms']
            now = time.time()

            # 持仓 + 平仓检查
            positions = get_positions(bot)
            for i, pos in enumerate(positions):
                if i in position_times:
                    pos['opened_at'] = position_times[i]

            pos_to_close, pnl_pct, close_index, reason = check_tp(bot, positions, position_times)
            if pos_to_close:
                if reason == 'TIME':
                    print(f"\n⏹ TIME {pnl_pct*100:+.2f}% (index={close_index}, {TIME_LIMIT_S}s)")
                else:
                    print(f"\n⏹ TP {pnl_pct*100:+.2f}% (index={close_index})")
                ok, pnl = close_position(bot, PAIR, close_index)
                if ok:
                    closed_log.append({'pnl': pnl, 'reason': reason})
                    print(f"   pnl=${pnl:+.2f} (100x)")
                    del position_times[close_index]
                    new_times = {}
                    for idx, t in position_times.items():
                        new_times[idx - 1 if idx > close_index else idx] = t
                    position_times = new_times
                positions = get_positions(bot)

            # 开仓
            if now - last_scan >= SCAN_INTERVAL and len(positions) < MAX_POSITIONS:
                last_scan = now
                candles = get_candles(bot, PAIR)
                direction = momentum(candles, MOOMENTUM_WINDOW)
                if direction != 0:
                    side = 'long' if direction == 1 else 'short'
                    ok, entry = open_position(bot, PAIR, side, MARGIN, LEVERAGE)
                    if ok:
                        open_count += 1
                        new_pos = get_positions(bot)
                        position_times[len(new_pos) - 1] = time.time()
                        print(f"▶ 开仓 {side} @ {entry:.5f} (仓={len(new_pos)})")

            # 状态
            if now - last_stats >= 60:
                last_stats = now
                st2 = bot.state()
                acct = st2['account']
                wins = sum(1 for c in closed_log if c['pnl'] > 0)
                total = sum(c['pnl'] for c in closed_log)
                print(f"\n── [{time.strftime('%H:%M:%S')}] cash=${acct['cash']:,.0f} "
                      f"仓位={len(positions)}/{MAX_POSITIONS} 平仓={len(closed_log)}(W{wins}/L{len(closed_log)-wins}) "
                      f"盈亏=${total:+,.0f} 利息日利率={acct.get('loan_rate') or 0}")

            time.sleep(0.2)
    finally:
        for pz in get_positions(bot):
            close_position(bot, PAIR)
            time.sleep(0.5)

    st = bot.state()
    acct = st['account']
    wins = sum(1 for c in closed_log if c['pnl'] > 0)
    total = sum(c['pnl'] for c in closed_log)
    print("\n" + "=" * 60)
    print(f"最终 cash: ${acct['cash']:,.2f}")
    print(f"贷款余额: ${acct['debt']:,.2f}")
    print(f"已实现盈亏(平仓): ${total:+,.2f}")
    print(f"平仓: {len(closed_log)}  W{wins}/L{len(closed_log)-wins}")
    print(f"开仓次数: {open_count}")
    bot.close()


if __name__ == '__main__':
    run()