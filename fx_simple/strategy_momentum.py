"""
动量延续: 看到涨赌它涨N个tick, 到点就卖
- 信号: 连续2tick同向(涨→做多, 跌→做空) = "看到涨"
- 预测: 持仓 N tick 到点卖(不管盈亏, 吃惯性)
- 保护: 反向超 -5%margin 提前走
- 依据: FX 正弦drift平滑, 相邻tick相关, 动量短期有惯性
"""
import time, sys
sys.path.insert(0, '/tmp/fxbot/fx_simple')
from bot import FXBot
from playwright._impl._errors import TargetClosedError, Error as PWError

PAIR = 'EUR/USD'
MARGIN = 500
LEVERAGE = 20
CONFIRM = 2          # 连续几tick同向 = 看到涨
PREDICT = 4          # 预测涨 N tick 后卖
SL_PCT = -5.0        # 反向 -5% margin 提前走
DURATION = 900


def setup_panel(bot):
    bot.frame.evaluate(r"""(o) => {
        const el = document.getElementById('marginInput');
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(o.margin));
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        const el2 = document.getElementById('leverageRange');
        const s2 = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s2.call(el2, String(o.leverage));
        el2.dispatchEvent(new Event('input', {bubbles: true}));
        el2.dispatchEvent(new Event('change', {bubbles: true}));
    }""", {'margin': MARGIN, 'leverage': LEVERAGE})
    time.sleep(0.5)


def fast_open(bot, side):
    btn = 'longBtn' if side == 'long' else 'shortBtn'
    return bot.frame.evaluate("""(id) => {
        const b = document.getElementById(id);
        if (!b) return false;
        b.click();
        return true;
    }""", btn)


def fast_close(bot):
    return bot.frame.evaluate(r"""() => {
        const btns = Array.from(document.querySelectorAll('button'))
            .filter(b => b.textContent.trim() === '平仓');
        if (!btns.length) return false;
        btns[0].click();
        const c = document.getElementById('modalConfirm');
        if (c && c.offsetParent !== null) c.click();
        return true;
    }""")


def read_state(bot):
    s = bot.state()
    return s['prices'][PAIR], s['account']['positions']


def safe(fn, bot):
    try:
        return fn(bot)
    except (TargetClosedError, PWError):
        return 'RECONNECT'


def run():
    for attempt in range(1, 4):
        try:
            bot = FXBot(headless=False)
            bot.reset()
            setup_panel(bot)
            print("=" * 60)
            print(f"⚡ 动量延续(第{attempt}次): 连续{CONFIRM}tick同向进场, 预测涨{PREDICT}tick卖")
            print(f"   margin${MARGIN}×{LEVERAGE}x 保护SL{SL_PCT}%margin")
            print(f"   cash=${bot.state()['account']['cash']:,.0f}")
            print("=" * 60)

            prices = []
            pos = None
            hold = 0          # 已持仓tick数
            closed = []
            start = time.time()
            last_stats = 0

            while time.time() - start < DURATION:
                now = time.time()
                r = safe(read_state, bot)
                if r == 'RECONNECT':
                    raise TargetClosedError('断开')
                price, positions = r

                if pos:
                    # 价格变化才算新tick
                    if price != prices[-1] if prices else True:
                        hold += 1
                        pct = (price / pos['entry'] - 1) * pos['side'] * LEVERAGE * 100
                        reason = None
                        if pct <= SL_PCT:
                            reason = '反向保护'
                        elif hold >= PREDICT:
                            reason = '预测tick到'
                        if reason:
                            fast_close(bot)
                            closed.append({'pnl': pct, 'reason': reason, 'hold': hold})
                            print(f"⏹ [{reason}] {pct:+.1f}%margin 持{hold}tick")
                            pos = None
                            prices = []
                else:
                    if not prices or price != prices[-1]:
                        prices.append(price)
                    # 连续CONFIRM tick同向 = 看到涨/跌
                    if len(prices) >= CONFIRM + 1:
                        ups = sum(1 for i in range(1, CONFIRM + 1) if prices[-i] > prices[-i - 1])
                        down = CONFIRM - ups
                        if ups == CONFIRM:
                            ok = fast_open(bot, 'long')
                            side_now = 'long'
                        elif down == CONFIRM:
                            ok = fast_open(bot, 'short')
                            side_now = 'short'
                        else:
                            ok = False
                        if ok:
                            pos = {'entry': price, 'side': 1 if side_now == 'long' else -1}
                            hold = 0
                            prices = []
                            print(f"▶ 连{CONFIRM}tick {side_now} @ {price:.5f}")

                if now - last_stats >= 60:
                    last_stats = now
                    wins = sum(1 for c in closed if c['pnl'] > 0)
                    tot = sum(c['pnl'] for c in closed)
                    st2 = bot.state()
                    print(f"── [{time.strftime('%H:%M:%S')}] cash=${st2['account']['cash']:,.0f} "
                          f"笔={len(closed)}(W{wins}/L{len(closed)-wins}) 净=${tot:+.0f}margin")
                time.sleep(0.4)
            break
        except (TargetClosedError, PWError):
            print(f"⚠ 断开, 20s后重建...")
            try:
                bot.close()
            except Exception:
                pass
            time.sleep(20)

    wins = sum(1 for c in closed if c['pnl'] > 0)
    tot = sum(c['pnl'] for c in closed)
    print("\n" + "=" * 60)
    print(f"笔数: {len(closed)}  W{wins}/L{len(closed)-wins} 胜率{(wins/len(closed)*100) if closed else 0:.0f}%")
    print(f"累计margin: {tot:+.1f}% (×$500 = ${tot/100*500:+.0f})")
    for c in closed[:30]:
        print(f"   [{c['reason']}] {c['pnl']:+.1f}% 持{c['hold']}tick")
    try:
        bot.close()
    except Exception:
        pass


if __name__ == '__main__':
    run()