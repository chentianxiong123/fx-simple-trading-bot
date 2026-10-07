"""
拐点策略: 赚钱等期望值, 亏钱马上卖
- 入场: 检测趋势拐点(最新tick方向与前2tick相反=刚转头), 带预判
- 出场: 盈利≥TP 等到了期望值才卖; 亏损≤SL 马上卖; 超时保底平
- 盈亏比: TP+1%价格(+20%margin, +$200) vs SL-0.25%价格(-5%margin, -$50) = 4:1
- 正弦drift半周40s≈0.5-1%, 给盈利单30-60s奔跑
"""
import time, sys
sys.path.insert(0, '/tmp/fxbot/fx_simple')
from bot import FXBot
from playwright._impl._errors import TargetClosedError, Error as PWError

PAIR = 'EUR/USD'
MARGIN = 1000
LEVERAGE = 20
TP_PCT = 15.0        # +15% margin (价格+0.75%) → 等到的期望值
SL_PCT = -15.0       # -15% margin (价格-0.75%) → 真实反转才砍
MAX_HOLD_S = 90      # 正弦半周40s, 90s保底
COOLDOWN_S = 25      # 平仓后冷却
WINDOW = 20          # 大窗口: 20tick(30s)判断正弦半周方向
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


def safe(fn, bot, *args):
    try:
        return fn(bot, *args)
    except (TargetClosedError, PWError):
        return 'RECONNECT'


def pnl_pct(pos, price):
    """价格变动×杠杆 = margin百分比"""
    return (price / pos['entry'] - 1) * pos['side'] * pos['leverage'] * 100


def run():
    for attempt in range(1, 6):
        try:
            bot = FXBot(headless=False)
            bot.reset()
            setup_panel(bot)
            st = bot.state()
            print("=" * 60)
            print(f"🔄 拐点策略(第{attempt}次): TP+{TP_PCT:.0f}%margin / SL{SL_PCT:.0f}%margin / 超时{MAX_HOLD_S}s")
            print(f"   杠杆{LEVERAGE}x margin${MARGIN} 期望+${MARGIN*TP_PCT/100:.0f} 止损-${MARGIN*abs(SL_PCT)/100:.0f}")
            print(f"   cash=${st['account']['cash']:,.0f}")
            print("=" * 60)

            prices = []       # 最近 WINDOW+1 个tick
            pos = None
            pos_time = 0
            cooldown_until = 0
            closed = []
            start = time.time()
            last_stats = 0

            while time.time() - start < DURATION:
                now = time.time()
                r = safe(read_state, bot)
                if r == 'RECONNECT':
                    raise TargetClosedError('断开')
                price, positions = r

                # 持仓: 赚等期望值, 亏马上卖
                if pos:
                    pct = pnl_pct(pos, price)
                    reason = None
                    if pct >= TP_PCT:
                        reason = 'TP(期望达成)'
                    elif pct <= SL_PCT:
                        reason = 'SL(马上卖)'
                    elif now - pos_time >= MAX_HOLD_S:
                        reason = '超时'
                    if reason:
                        fast_close(bot)
                        closed.append({'pnl': pct, 'reason': reason})
                        pos = None
                        prices = []
                        cooldown_until = now + COOLDOWN_S
                        print(f"⏹ [{reason}] {pct:+.1f}%margin ({(now-pos_time):.0f}s)")

                # 空仓+冷却结束: 大窗口拐点(正弦半周启动)
                elif now >= cooldown_until:
                    # 只记录价格变化(真实tick序列, 去重)
                    if not prices or price != prices[-1]:
                        prices.append(price)
                    if len(prices) > WINDOW + 1:
                        prices.pop(0)
                    if len(prices) == WINDOW + 1:
                        s_prev = prices[-2] / prices[-WINDOW - 1] - 1   # 上tick的20tick累计
                        s_cur = prices[-1] / prices[-WINDOW - 1] - 1    # 本tick的20tick累计
                        if s_prev < 0 and s_cur > 0:
                            # 大窗口由跌转涨 = 正弦正半周启动
                            ok = fast_open(bot, 'long')
                            if ok:
                                pos = {'entry': price, 'side': 1, 'leverage': LEVERAGE}
                                pos_time = now
                                prices = []
                                print(f"▶ 大拐头向上(20tick:{s_prev*100:+.2f}%→{s_cur*100:+.2f}%) → 开long @ {price:.5f}")
                        elif s_prev > 0 and s_cur < 0:
                            # 大窗口由涨转跌 = 正弦负半周启动
                            ok = fast_open(bot, 'short')
                            if ok:
                                pos = {'entry': price, 'side': -1, 'leverage': LEVERAGE}
                                pos_time = now
                                prices = []
                                print(f"▶ 大拐头向下(20tick:{s_prev*100:+.2f}%→{s_cur*100:+.2f}%) → 开short @ {price:.5f}")

                if now - last_stats >= 60:
                    last_stats = now
                    wins = sum(1 for c in closed if c['pnl'] > 0)
                    tot = sum(c['pnl'] for c in closed)
                    st2 = bot.state()
                    print(f"── [{time.strftime('%H:%M:%S')}] cash=${st2['account']['cash']:,.0f} "
                          f"笔={len(closed)}(W{wins}/L{len(closed)-wins}) 净=${tot:+,.0f}margin")
                time.sleep(0.5)

            wins = sum(1 for c in closed if c['pnl'] > 0)
            tot = sum(c['pnl'] for c in closed)
            print("\n" + "=" * 60)
            print(f"笔数: {len(closed)}  W{wins}/L{len(closed)-wins} 胜率{(wins/len(closed)*100) if closed else 0:.0f}%")
            print(f"累计margin: {tot:+.1f}% (×${MARGIN} = ${tot/100*MARGIN:+.0f})")
            for c in closed:
                print(f"   [{c['reason']}] {c['pnl']:+.1f}%")
            try:
                bot.close()
            except Exception:
                pass
            return
        except (TargetClosedError, PWError):
            print(f"⚠ 连接断开, 20s后重建(第{attempt}次)...")
            try:
                bot.close()
            except Exception:
                pass
            time.sleep(20)
    print("❌ 多次重建失败")


def _find(bot, positions):
    for p in positions:
        if p['pair'] == PAIR:
            return p
    return None


if __name__ == '__main__':
    run()