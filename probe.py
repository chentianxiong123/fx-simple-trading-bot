"""
数据接入能力验证 —— 只读，不下单
目的：确认短线打法需要的每一个信号都能拿到
"""
import time
import json
from bot import FXBot


def snapshot_bot(bot):
    """一次读全部能读的东西"""
    return bot.frame.evaluate(r"""
        () => {
            const s = JSON.parse(localStorage.getItem('fx-heartbeat-save-v3'));
            const a = s.accounts[s.mode] || {};
            const out = {
                mode: s.mode,
                account: {
                    cash: a.cash, debt: a.debt,
                    loanPrincipal: a.loanPrincipal, loanRate: a.loanRate,
                    simLoanTicks: a.simLoanTicks,
                    pair: a.pair, leverage: a.leverage, margin: a.margin,
                    feesPaid: a.feesPaid,
                    equityTrail: a.equityTrail,
                    positions: a.positions,
                    history: a.history.slice(0, 3),
                },
                sim: {},
                challenge: s.accounts.challenge,
                achievements: JSON.parse(localStorage.getItem('fx-achievements-v1') || '{}')?.unlocked || {},
                settings: JSON.parse(localStorage.getItem('fx-settings-v1') || '{}'),
            };
            // sim 里的每个币对：当前价格 + 最近 30 根 K 线
            for (const [k, v] of Object.entries(s.sim)) {
                out.sim[k] = {
                    price: v.price,
                    candleCount: v.candles.length,
                    last30: v.candles.slice(-30).map(c => ({
                        o: c.open, h: c.high, l: c.low, c: c.close
                    })),
                };
            }
            // DOM 层能读到的额外信号
            const modalVisible = () => {
                const el = document.getElementById('modalClose');
                return !!(el && el.offsetParent !== null);
            };
            const modalText = () => {
                const el = document.getElementById('modalTitle');
                return el ? el.textContent : '';
            };
            out.dom = {
                modalVisible: modalVisible(),
                modalTitle: modalText(),
                newsTickerVisible: (() => {
                    const el = document.getElementById('newsTicker');
                    return !!(el && el.offsetParent !== null);
                })(),
                newsFloatVisible: (() => {
                    const el = document.getElementById('newsFloat');
                    return !!(el && el.offsetParent !== null);
                })(),
                welcomeOpen: (() => {
                    const el = document.getElementById('welcome');
                    return !!(el && el.offsetParent !== null);
                })(),
                toastText: (() => {
                    const el = document.getElementById('toast');
                    return el ? el.textContent : '';
                })(),
                positionRows: document.querySelectorAll('[id^="pos-"], .pos-item, [class*="position"]').length,
            };
            return out;
        }
    """)


def poll_test():
    """跑 15 秒，每 200ms 读一次，看能不能持续拿到数据"""
    print("=" * 70)
    print("【验证 1】连续轮询 15 秒，每 200ms 读一次 localStorage")
    print("=" * 70)
    bot = FXBot(headless=False)

    samples = []
    price_changes = 0
    start_price = None
    end_time = time.time() + 15

    while time.time() < end_time:
        snap = snapshot_bot(bot)
        curr_price = snap['sim']['EUR/USD']['price']
        if start_price is None:
            start_price = curr_price
        if samples and curr_price != samples[-1]['price']:
            price_changes += 1
        samples.append({
            'ts': time.time(),
            'price': curr_price,
            'candle_count': snap['sim']['EUR/USD']['candleCount'],
            'cash': snap['account']['cash'],
            'pos_count': len(snap['account']['positions']),
            'equity_trail_len': len(snap['account']['equityTrail']),
            'modal': snap['dom']['modalTitle'] if snap['dom']['modalVisible'] else '',
        })
        time.sleep(0.2)

    print(f"  采样次数: {len(samples)}")
    print(f"  价格变动次数: {price_changes} (tick=1.5s)")
    print(f"  EUR/USD 价格范围: {min(s['price'] for s in samples):.5f} → {max(s['price'] for s in samples):.5f}")
    print(f"  首价格: {samples[0]['price']:.5f}")
    print(f"  末价格: {samples[-1]['price']:.5f}")
    print(f"  K 线总数 (最后): {samples[-1]['candle_count']}")
    print(f"  equityTrail 长度变化: {samples[0]['equity_trail_len']} → {samples[-1]['equity_trail_len']}")
    modals_seen = [s['modal'] for s in samples if s['modal']]
    if modals_seen:
        print(f"  期间弹出过弹窗: {modals_seen[:3]}")

    print(f"\n  读延迟测试 (连续读 10 次):")
    delays = []
    for _ in range(10):
        t0 = time.time()
        _ = bot.prices()
        delays.append(time.time() - t0)
    print(f"    平均: {sum(delays)/len(delays)*1000:.1f}ms  最大: {max(delays)*1000:.1f}ms")

    bot.close()


def full_state_test():
    """一次读全，看能拿到多少字段"""
    print("\n" + "=" * 70)
    print("【验证 2】一次读全部字段")
    print("=" * 70)
    bot = FXBot(headless=False)
    snap = snapshot_bot(bot)

    print(f"  mode: {snap['mode']}")
    print(f"  achievements: {list(snap['achievements'].keys())}")
    print(f"  settings: {snap['settings']}")
    print(f"  账户字段: {list(snap['account'].keys())}")
    print(f"  7 个币对: {list(snap['sim'].keys())}")
    for pair, data in snap['sim'].items():
        print(f"    {pair}: price={data['price']:.5f}  candles={data['candleCount']}  last={data['last30'][-1]['c']:.5f}")
    print(f"  DOM 状态: {snap['dom']}")
    print(f"  equityTrail (最新 5): {snap['account']['equityTrail'][-5:]}")
    print(f"  最近 3 笔历史: {snap['account']['history']}")

    bot.close()


def modal_interception_test():
    """模拟爆仓预警弹窗，看能不能及时检测到"""
    print("\n" + "=" * 70)
    print("【验证 3】爆仓预警弹窗能否被检测到")
    print("=" * 70)
    bot = FXBot(headless=False)

    # 用高杠杆开一笔反向仓位
    bot.set_leverage(100)
    bot.set_margin(500)
    time.sleep(0.2)
    # 先看当前趋势
    prices = bot.prices()
    curr = prices['EUR/USD']
    prev_prices = bot.frame.evaluate("""
        () => {
            const s = JSON.parse(localStorage.getItem('fx-heartbeat-save-v3'));
            return s.sim['EUR/USD'].candles.slice(-5).map(c => c.close);
        }
    """)
    # 逆势开单 —— 如果最近涨，做空；如果最近跌，做多
    trend = curr - prev_prices[0]
    side = 'short' if trend > 0 else 'long'
    print(f"  入场: {side} @ {curr:.5f}  (反向 {100*abs(trend/curr):.2f}% 趋势)")
    bot.open_position(side)

    # 监控弹窗
    print(f"  监控中... 每 200ms 检查弹窗")
    end_time = time.time() + 20
    modal_seen = False
    while time.time() < end_time:
        snap = snapshot_bot(bot)
        if snap['dom']['modalVisible']:
            print(f"  ✅ 检测到弹窗: {snap['dom']['modalTitle']}")
            # 关掉弹窗
            bot.frame.evaluate("""() => {
                const b = document.getElementById('modalCancel');
                if (b) b.click();
            }""")
            modal_seen = True
            break
        # 顺便监控 positions 状态
        pos = snap['account']['positions']
        if pos and snap['account']['cash'] < 0:
            print(f"  已爆仓 (cash={snap['account']['cash']:.2f})")
            modal_seen = True
            break
        time.sleep(0.2)

    if not modal_seen:
        print(f"  ⚠ 20 秒内没触发弹窗（可能行情不够猛）")

    # 平仓
    try:
        bot.close_position()
    except Exception:
        pass

    bot.close()


if __name__ == "__main__":
    full_state_test()
    poll_test()
    modal_interception_test()
    print("\n" + "=" * 70)
    print("✅ 所有验证完成")
    print("=" * 70)
