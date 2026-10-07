"""
拼手速 v2: 等真实信号, 不碰噪声
- FX tick 1.5s: 噪声 ±0.21%/tick, drift 平滑 0.036%/tick
- 信号1: 单 tick 冲击 >0.5% (1.8%概率, ~80秒一次) → 顺势
- 信号2: 3 tick 累计同向 >0.3% (滤噪声后确认方向) → 顺势
- 无信号: 空仓等 (不碰 0.1% 的普通抖动)
- 有信号: 顺势开仓, 持仓 2 tick 平
"""
import time, sys
sys.path.insert(0, '/tmp/fxbot/fx_simple')
from bot import FXBot
from playwright._impl._errors import TargetClosedError, Error as PWError

PAIR = 'EUR/USD'
MARGIN = 1000
LEVERAGE = 20
SHOCK = 0.003        # 单tick冲击阈值 0.3% (噪声极限±0.21%, 只有shock/news能触发)
TREND = 0.0015       # 3tick累计阈值 0.15% (滤噪声后确认方向)
HOLD_TICKS = 2       # 持仓 tick 数
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


def pnl_of(bot, pos, price):
    return pos['notional'] * pos['side'] * (price / pos['entry'] - 1)


def safe_eval(bot, fn, *args):
    try:
        return fn(bot, *args)
    except (TargetClosedError, PWError) as e:
        print(f"⚠ 页面断开: {type(e).__name__} → 重建浏览器")
        return 'RECONNECT'


def run():
    attempts = 0
    while attempts < 5:  # 最多重建5次
        attempts += 1
        try:
            bot = FXBot(headless=False)
            bot.reset()
            setup_panel(bot)
            st = bot.state()
            print("=" * 60)
            print(f"⚡ 拼手速v3: 等信号(SHOCK>{SHOCK*100:.1f}% / 3tick>{TREND*100:.1f}%)  第{attempts}次连接")
            print(f"   杠杆{LEVERAGE}x margin${MARGIN} 持仓{HOLD_TICKS}tick 无信号空仓等")
            print(f"cash=${st['account']['cash']:,.0f}")
            print("=" * 60)

            prices = []
            pos = None
            hold = 0
            closed = []
            start = time.time()
            last_stats = 0

            while time.time() - start < DURATION:
                now = time.time()
                r = safe_eval(bot, read_state)
                if r == 'RECONNECT':
                    raise TargetClosedError('页面断开, 重建')
                price, positions = r

                if pos:
                    hold += 1
                    if hold >= HOLD_TICKS:
                        pnl = pnl_of(bot, pos, price)
                        fast_close(bot)
                        closed.append({'pnl': pnl, 'hold': hold, 'entry': pos['entry']})
                        pos = None
                        hold = 0
                        prices = []
                else:
                    prices.append(price)
                    if len(prices) > 4:
                        prices.pop(0)
                    signal = None
                    if len(prices) >= 2 and abs(prices[-1] / prices[-2] - 1) > SHOCK:
                        signal = 'SHOCK' if prices[-1] > prices[-2] else 'SHOCK-S'
                    if signal is None and len(prices) >= 4 and abs(prices[-1] / prices[-4] - 1) > TREND:
                        signal = 'TREND' if prices[-1] > prices[-4] else 'TREND-S'
                    if signal:
                        side = 'long' if signal in ('SHOCK', 'TREND') else 'short'
                        ok = fast_open(bot, side)
                        if ok:
                            pos = _find_pos(bot, positions)
                            hold = 0
                            prices = []
                            print(f"▶ [{signal}] 开{side} @ {price:.5f}")

                if now - last_stats >= 60:
                    last_stats = now
                    wins = sum(1 for c in closed if c['pnl'] > 0)
                    tot = sum(c['pnl'] for c in closed)
                    st2 = bot.state()
                    print(f"── [{time.strftime('%H:%M:%S')}] cash=${st2['account']['cash']:,.0f} "
                          f"笔={len(closed)}(W{wins}/L{len(closed)-wins}) 净=${tot:+,.0f}")
                time.sleep(0.5)

            # 正常结束统计
            wins = sum(1 for c in closed if c['pnl'] > 0)
            tot = sum(c['pnl'] for c in closed)
            print("\n" + "=" * 60)
            print(f"笔数: {len(closed)}  W{wins}/L{len(closed)-wins}  "
                  f"胜率{(wins/len(closed)*100) if closed else 0:.0f}%")
            print(f"净盈亏: ${tot:+,.2f}")
            try:
                print(f"最终cash: ${bot.state()['account']['cash']:,.2f}")
            except Exception:
                pass
            try:
                bot.close()
            except Exception:
                pass
            return
        except (TargetClosedError, PWError) as e:
            print(f"⚠ 第{attempts}次连接断开: {type(e).__name__}, 20s 后重建...")
            try:
                bot.close()
            except Exception:
                pass
            time.sleep(20)
    print("❌ 多次重建失败, 退出")


def _find_pos(bot, positions):
    for p in positions:
        if p['pair'] == PAIR:
            return p
    return None


if __name__ == '__main__':
    run()