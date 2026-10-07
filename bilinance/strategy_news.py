"""
BILINANCE 策略 v3: 新闻冲击跟随
- 监控行情页全部币价, 检测单秒跳变 > 阈值(冲击开始)
- 跟随方向开那个币的合约(快路径: hash 直达 + 直开)
- 持仓吃冲击后半段, TP 2% / 时间兜底 6s
- 机制依据: 新闻冲击 shockDrift=mag/8 持续8秒, 单币 5-14% 单向行情
"""
import time, sys
sys.path.insert(0, '/tmp/fxbot/bilinance')
from bot import BILBot

JUMP_PCT = 1.0        # 单秒跳变阈值 % (冲击大概率 >1%)
LEV = 10
MARGIN = 50
TP_PCT = 0.02         # 价格 +2% 平 (10x → 20% ROE)
TIME_LIMIT_S = 6      # 冲击8秒, 6s 兜底
HOLD_AFTER = 3        # 平仓后冷却秒数(防重复触发)
DURATION = 180

# 合约页快路径: 直接改 hash 到期货页
def goto_futures(bot, sym):
    bot.frame.evaluate("""(s) => { location.hash = '#/futures/' + s; }""", sym)

def quick_open(bot, side, lev, margin):
    """合约页已就绪时快速开仓(3 次 evaluate)"""
    bot.frame.evaluate("""(v) => {
        const el = document.getElementById('levInput');
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(v)); el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
    }""", lev)
    bot.frame.evaluate("""(v) => {
        const el = document.getElementById('fMargin');
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(v)); el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
    }""", margin)
    bot.frame.evaluate("""(b) => { document.getElementById(b).click(); }""", 'fLong' if side == 'long' else 'fShort')

def quick_close(bot, pos_id):
    bot.frame.evaluate("""(id) => {
        const b = document.querySelector('[data-close="' + id + '"]');
        if (b) { b.click(); return true; }
        return false;
    }""", pos_id)

def main():
    bot = BILBot(headless=False)
    bot.nav('行情')
    time.sleep(2)

    print("=" * 60)
    print(f"BILINANCE 新闻冲击策略")
    print(f"跳变阈值>{JUMP_PCT}% 杠杆{LEV}x 保证金${MARGIN} TP={TP_PCT*100:.0f}% 兜底{TIME_LIMIT_S}s")
    print(f"初始: $10000")
    print("=" * 60)

    start = time.time()
    quiet_until = 0       # 冷却
    prev = None
    last_stats = 0
    trades = []

    try:
        while time.time() - start < DURATION:
            now = time.time()
            cur = bot.all_prices()
            if not cur or not prev:
                prev = cur
                time.sleep(0.5)
                continue

            # 检测跳变
            jump = None
            for sym, p in cur.items():
                if sym in prev and prev[sym] > 0:
                    chg = (p / prev[sym] - 1) * 100
                    if abs(chg) >= JUMP_PCT:
                        jump = (sym, chg)
                        break

            # 交易
            if jump and now >= quiet_until and now - start > 5:
                sym, chg = jump
                side = 'long' if chg > 0 else 'short'
                print(f"\n🔔 冲击! {sym} {chg:+.2f}% → 开{side}")
                goto_futures(bot, sym)
                time.sleep(0.8)
                entry_price = bot.price()
                quick_open(bot, side, LEV, MARGIN)
                time.sleep(0.5)
                pos = bot.state()['positions']
                pid = pos[-1]['id'] if pos else None
                entry = pos[-1]['entry'] if pos else entry_price
                print(f"   ✓ 开仓 {side} @ {entry:,.2f} (id={pid})")
                t0 = time.time()

                # 持仓: 看 TP/时间, 吃冲击尾巴
                if pid:
                    while time.time() - t0 < TIME_LIMIT_S:
                        p = bot.price()
                        if p:
                            pnl = (1 if side == 'long' else -1) * (p / entry - 1)
                            if pnl >= TP_PCT:
                                print(f"   ⏹ TP {pnl*100:+.2f}%")
                                break
                            if pnl <= -0.03:
                                print(f"   ⏹ 止损 {pnl*100:+.2f}%")
                                break
                        time.sleep(0.4)
                    quick_close(bot, pid)
                    time.sleep(0.6)
                    p_end = bot.price() or entry
                    pnl = (1 if side == 'long' else -1) * (p_end / entry - 1)
                    trades.append({'sym': sym, 'pnl': pnl, 'side': side})
                    print(f"   ⏹ 平仓 {pnl*100:+.2f}% ({(time.time()-t0):.1f}s)")
                    quiet_until = time.time() + HOLD_AFTER
                # 回行情页
                bot.nav('行情')
                time.sleep(1.0)
                prev = bot.all_prices()
                continue

            prev = cur
            if now - last_stats >= 30:
                last_stats = now
                wins = sum(1 for t in trades if t['pnl'] > 0)
                total = sum(t['pnl'] for t in trades)
                st = bot.state()
                print(f"── [{time.strftime('%H:%M:%S')}] usdt=${st['usdt']:.2f} 交易={len(trades)}(W{wins}/L{len(trades)-wins}) 累计pnl={total*100:+.1f}%")
            time.sleep(0.6)
    finally:
        # 收尾平仓(不 close, 统计在后面)
        for pz in bot.state()['positions']:
            quick_close(bot, pz['id'])
        time.sleep(0.5)

    wins = sum(1 for t in trades if t['pnl'] > 0)
    total = sum(t['pnl'] for t in trades)
    st = bot.state()
    print("\n" + "=" * 60)
    print(f"最终 usdt: ${st['usdt']:.2f}  盈亏 ${st['usdt']-10000:+.2f}")
    print(f"交易: {len(trades)}  W{wins}/L{len(trades)-wins}  累计 {total*100:+.1f}%")
    for t in trades:
        print(f"   {t['sym']} {t['side']} {t['pnl']*100:+.2f}%")
    bot.close()

if __name__ == '__main__':
    main()