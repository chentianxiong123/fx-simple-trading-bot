"""
拼手速策略: 看到动立即进, 1个tick立即出
- FX tick 1.5s, 无滑点(看到价=成交价)
- 检测单tick跳变 >0.10% → 立即开对应方向
- 持仓 1 tick (1.5s) → 立即平, 吃正弦平滑drift的延续
- 开仓1次evaluate, 平仓2次evaluate, 全程~200ms
"""
import time, sys
sys.path.insert(0, '/tmp/fxbot/fx_simple')
from bot import FXBot

PAIR = 'EUR/USD'
MARGIN = 1000
LEVERAGE = 20
JUMP = 0.0010       # 单tick阈值 0.10%
MAX_HOLD = 2        # 最多持有 tick 数
DURATION = 600

# 一次性设置面板(之后保留)
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
    return bot.frame.evaluate(f"() => {{ const b = document.getElementById('{btn}'); if (!b) return false; b.click(); return true; }}")

def fast_close(bot):
    """平第一个仓位, 返回是否成功"""
    return bot.frame.evaluate(r"""() => {
        const btns = Array.from(document.querySelectorAll('button'))
            .filter(b => b.textContent.trim() === '平仓');
        if (!btns.length) return false;
        btns[0].click();
        const c = document.getElementById('modalConfirm');
        if (c && c.offsetParent !== null) c.click();
        return true;
    }""")

def read_price(bot):
    s = bot.state()
    return s['prices'][PAIR]

def pnl_of(bot, pos):
    curr = bot.state()['prices'][pos['pair']]
    return pos['notional'] * pos['side'] * (curr / pos['entry'] - 1)

def run():
    bot = FXBot(headless=False)
    bot.reset()
    setup_panel(bot)
    st = bot.state()
    print("=" * 60)
    print(f"⚡ 拼手速: {PAIR} 阈值{JUMP*100:.2f}% 杠杆{LEVERAGE}x margin${MARGIN} 持仓1tick")
    print(f"cash=${st['account']['cash']:,.0f}")
    print("=" * 60)

    prev = None
    hold_ticks = 0
    pos = None
    closed = []
    start = time.time()
    last_stats = 0

    try:
        while time.time() - start < DURATION:
            cur = read_price(bot)

            if pos and hold_ticks >= 1:
                # 持仓≥1tick → 立即平
                pnl = pnl_of(bot, pos)
                fast_close(bot)
                closed.append({'pnl': pnl, 'entry': pos['entry'], 'exit': cur})
                pos = None
                hold_ticks = 0

            if pos is None and prev is not None and prev > 0:
                chg = (cur - prev) / prev
                if chg > JUMP:
                    fast_open(bot, 'long')
                    pos = _find_pos(bot)
                    hold_ticks = 0
                elif chg < -JUMP:
                    fast_open(bot, 'short')
                    pos = _find_pos(bot)
                    hold_ticks = 0
                # 同一 tick 可能已开仓又被平? 保护:
                if pos is not None:
                    hold_ticks += 1

            prev = cur

            # 统计(1分钟)
            now = time.time()
            if now - last_stats >= 60:
                last_stats = now
                wins = sum(1 for c in closed if c['pnl'] > 0)
                tot = sum(c['pnl'] for c in closed)
                st2 = bot.state()
                print(f"── [{time.strftime('%H:%M:%S')}] cash=${st2['account']['cash']:,.0f} "
                      f"笔={len(closed)}(W{wins}/L{len(closed)-wins}) 净=${tot:+,.0f}")
            time.sleep(0.5)  # 每0.5s读一次, tick 1.5s 内必读到新价
    finally:
        if pos and _find_pos(bot):
            fast_close(bot)
        time.sleep(0.3)
        bot.close()

    wins = sum(1 for c in closed if c['pnl'] > 0)
    tot = sum(c['pnl'] for c in closed)
    stf = bot.state()
    print("\n" + "=" * 60)
    print(f"最终 cash: ${stf['account']['cash']:,.2f}  (需减贷款0)")
    print(f"笔数: {len(closed)}  W{wins}/L{len(closed)-wins}  胜率{wins/len(closed)*100:.0f}%")
    print(f"净盈亏: ${tot:+,.2f}")
    bot.close()

def _find_pos(bot):
    s = bot.state()
    for p in s['account']['positions']:
        if p['pair'] == PAIR:
            return p
    return None

if __name__ == '__main__':
    run()