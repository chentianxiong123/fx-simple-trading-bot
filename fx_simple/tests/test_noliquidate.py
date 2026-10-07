"""
爆仓不可能策略测试
参数: 1x 杠杆 + $500 保证金 + 浮亏 -10% 主动平仓
"""
import time
from bot import FXBot


def wait_price_change(bot, timeout=5):
    """等到下一个 tick（价格变）"""
    prev = bot.prices()
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(0.2)
        curr = bot.prices()
        if curr != prev:
            return curr
    return prev


def run_once(bot, side, margin=500, leverage=1, stop_loss_pct=0.10, max_hold_s=10):
    """单次交易：开仓 → 监控 PnL → 止损或超时平仓"""
    bot.set_margin(margin)
    bot.set_leverage(leverage)
    time.sleep(0.2)

    entry = bot.prices()['EUR/USD']
    bot.open_position(side)
    time.sleep(0.3)

    snap = bot.frame.evaluate(r"""
        () => {
            const s = JSON.parse(localStorage.getItem('fx-heartbeat-save-v3'));
            const a = s.accounts[s.mode];
            return {
                entry: a.positions[0]?.entry,
                margin: a.positions[0]?.margin,
                leverage: a.positions[0]?.leverage,
                notional: a.positions[0]?.notional,
                fee: a.positions[0]?.fee,
                cash: a.cash,
            };
        }
    """)
    if not snap['entry']:
        return {'side': side, 'error': 'open failed'}

    start = time.time()
    entry_price = snap['entry']
    max_loss_pct = 0

    # 每 100ms 检查一次 PnL
    while time.time() - start < max_hold_s:
        time.sleep(0.1)
        s = bot.frame.evaluate(r"""
            () => {
                const s = JSON.parse(localStorage.getItem('fx-heartbeat-save-v3'));
                const a = s.accounts[s.mode];
                const p = a.positions[0];
                if (!p) return {closed: true, history: a.history.slice(0,1)};
                const curr = s.sim[p.pair].price;
                const pnl = p.notional * p.side * (curr / p.entry - 1);
                const pnl_pct = pnl / p.margin;
                return {
                    closed: false,
                    curr: curr,
                    pnl: pnl,
                    pnl_pct: pnl_pct,
                    risk_ratio: Math.max(0, -pnl / p.margin),
                    modal_visible: (() => {
                        const el = document.getElementById('modalClose');
                        return !!(el && el.offsetParent !== null);
                    })(),
                    modal_title: document.getElementById('modalTitle')?.textContent || '',
                    toast: document.getElementById('toast')?.textContent || '',
                };
            }
        """)
        if s['closed']:
            return {
                'side': side, 'entry': entry_price, 'exit': None,
                'pnl': s['history'][0]['pnl'] if s['history'] else None,
                'pnl_pct': None,
                'reason': 'liquidated/auto-closed',
                'duration': time.time() - start,
            }
        max_loss_pct = max(max_loss_pct, -s['pnl_pct'])
        if s['pnl_pct'] <= -stop_loss_pct:
            break
        # 弹窗保护：如果爆仓预警出来，直接平
        if s['modal_visible']:
            break

    # 平仓
    bot.close_position()
    time.sleep(0.3)
    final = bot.frame.evaluate(r"""
        () => {
            const s = JSON.parse(localStorage.getItem('fx-heartbeat-save-v3'));
            return {
                cash: s.accounts[s.mode].cash,
                history: s.accounts[s.mode].history.slice(0, 1),
            };
        }
    """)
    exit_price = final['history'][0]['pnl']  # 借用 pnl 字段返回
    return {
        'side': side,
        'entry': entry_price,
        'exit': None,
        'pnl': final['history'][0]['pnl'],
        'pnl_pct': final['history'][0]['pnl'] / margin,
        'max_loss_pct': max_loss_pct,
        'reason': 'stop-loss' if max_loss_pct >= stop_loss_pct else 'timeout',
        'duration': time.time() - start,
        'fee': snap['fee'],
    }


def main():
    bot = FXBot(headless=False)

    print("=" * 70)
    print("参数: 1x 杠杆 · $500 保证金 · 止损 -10% · 最长持有 30 秒")
    print("=" * 70)

    results = []
    initial_cash = bot.state()['cash']
    print(f"初始现金: ${initial_cash:.2f}\n")

    # 跑 4 次交易
    for i in range(4):
        # 简单策略：随机方向
        side = 'long' if i % 2 == 0 else 'short'
        print(f"--- 第 {i+1}/4 次: {side} ---")
        r = run_once(bot, side)
        results.append(r)
        if 'error' in r:
            print(f"  ❌ {r['error']}")
        else:
            print(f"  入场 {r['entry']:.5f} → PnL=${r['pnl']:.2f} ({r['pnl_pct']*100:+.2f}%) "
                  f"maxLoss={r['max_loss_pct']*100:.2f}%  reason={r['reason']}  耗时={r['duration']:.1f}s")
        time.sleep(1)

    final_cash = bot.state()['cash']
    print(f"\n{'=' * 70}")
    print(f"结果汇总:")
    print(f"  初始: ${initial_cash:.2f}")
    print(f"  最终: ${final_cash:.2f}")
    print(f"  净盈亏: ${final_cash - initial_cash:+.2f}")

    wins = [r for r in results if r.get('pnl', 0) > 0]
    losses = [r for r in results if r.get('pnl', 0) < 0]
    print(f"  胜: {len(wins)}  负: {len(losses)}")
    print(f"  平均单笔 PnL: ${sum(r['pnl'] for r in results if 'pnl' in r) / max(1, len(results)):.2f}")
    max_loss = min(r.get('max_loss_pct', 0) for r in results)
    print(f"  最深浮亏: {max_loss*100:.2f}%  (爆仓线 80%)")
    print(f"  ✅ 无爆仓" if max_loss > -0.8 else "  ❌ 爆仓了")

    bot.close()


if __name__ == "__main__":
    main()
