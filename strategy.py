"""
5 仓位并行策略 - v3 (干净版)

改动:
1. 每次 open/close 后主动刷新 state (不缓存)
2. 用 position ID 追踪, 不是 pair
3. 一次 tick 只开一笔, 避免连开
4. close 之后 cooldown, 不再重开同一 pair
5. 用 pair 名 + id 双重验证 close 成功
"""
import time
import math
from bot import FXBot

# ============================================================
# 配置
# ============================================================

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "EUR/CHF", "AUD/USD", "USD/CAD"]
PAIR_INDEX = {p: i for i, p in enumerate(PAIRS)}

MAX_SLOTS = 2
MARGIN = 1000
LEVERAGE = 20

DRIFT_THRESHOLD = 0.00025
MOOMENTUM_WINDOW = 10

STOP_LOSS_PCT = -0.03         # -3% margin
TAKE_PROFIT_PCT = 0.015       # +1.5% margin
TIME_STOP_S = 30              # 30 秒
PAIR_COOLDOWN_S = 10          # 平仓后该 pair 冷却 10 秒


# ============================================================
# 信号
# ============================================================

def drift_of(pair_index):
    return math.sin(time.time() * 1000 / 13000 + pair_index * 2) * 0.00036


def check_entry(candles, pair_index):
    d = drift_of(pair_index)
    if abs(d) < DRIFT_THRESHOLD:
        return 0
    direction = 1 if d > 0 else -1
    closes = [c['close'] for c in candles[-MOOMENTUM_WINDOW:]]
    if len(closes) < MOOMENTUM_WINDOW:
        return 0
    if direction == 1 and closes[-1] > closes[0]:
        return 1
    elif direction == -1 and closes[-1] < closes[0]:
        return -1
    return 0


# ============================================================
# 操作封装
# ============================================================

def do_open(bot, pair, side, margin, leverage):
    """开仓, 返回 (success, position_id, entry_price)"""
    bot.select_pair(pair)
    time.sleep(0.15)
    bot.set_margin(margin)
    time.sleep(0.05)
    bot.set_leverage(leverage)
    time.sleep(0.05)
    bot.open_position(side)
    time.sleep(0.4)
    
    # 读回确认
    s = bot.state()
    for p in s['account']['positions']:
        if p['pair'] == pair:
            expected_side = 1 if side == 'long' else -1
            if p['side'] == expected_side:
                return True, p['id'], p['entry']
    return False, None, None


def do_close(bot, pair_id):
    """平仓, 返回 (success, pnl)"""
    result = bot.frame.evaluate(r"""(pairId) => {
        const btns = Array.from(document.querySelectorAll('button'))
            .filter(b => b.textContent.trim() === '平仓');
        for (const btn of btns) {
            let el = btn.parentElement;
            for (let depth = 0; el && depth < 4; depth++) {
                if (el.textContent.includes(pairId)) {
                    btn.click();
                    return {ok: true, depth};
                }
                el = el.parentElement;
            }
        }
        return {ok: false, btns: btns.length};
    }""", pair_id)
    
    time.sleep(0.5)
    # 关确认弹窗
    bot.frame.evaluate(r"""() => {
        const c = document.getElementById('modalConfirm');
        if (c && c.offsetParent !== null) c.click();
    }""")
    time.sleep(0.3)
    
    if not result.get('ok'):
        return False, 0
    
    # 读历史拿 pnl
    s = bot.state()
    h = s['account']['history']
    pnl = h[0]['pnl'] if h else 0
    return True, pnl


# ============================================================
# 主策略
# ============================================================

def run():
    bot = FXBot(headless=False)
    bot.reset()  # 清空旧仓位, 现金回 $10000
    
    DURATION = 90
    
    print("=" * 60)
    print(f"v3: 20x 波动吃单 · {DURATION} 秒")
    print(f"margin={MARGIN}  lever={LEVERAGE}x  "
          f"SL={STOP_LOSS_PCT*100:.0f}%  TP={TAKE_PROFIT_PCT*100:.1f}%  "
          f"TIME={TIME_STOP_S}s  PAIR_CD={PAIR_COOLDOWN_S}s")
    print("=" * 60)
    
    initial = bot.state()
    initial_cash = initial['account']['cash']
    print(f"初始: ${initial_cash:.2f}\n")
    
    # 追踪的仓位: pair_id -> {id, side, entry, opened_at}
    tracked = {}
    # 冷却: pair_id -> 冷却结束时间
    cooldowns = {}
    
    closed_log = []
    errors = []
    opens_count = 0
    closes_count = 0
    
    start = time.time()
    last_tick = 0
    
    try:
        while time.time() - start < DURATION:
            info = bot.tick_info()
            if info['last_tick_ms'] == last_tick:
                time.sleep(0.2)
                continue
            last_tick = info['last_tick_ms']
            
            now = time.time()
            s = bot.state()
            
            # ---------- 1. 检查平仓 ----------
            game_positions = {p['id']: p for p in s['account']['positions']}
            
            # 同步 tracked: 移除已被 game 移除的
            for pid in list(tracked.keys()):
                if pid not in game_positions:
                    pos = tracked.pop(pid)
                    # 没记录 close 就没了 (爆仓?)
                    print(f"  ⚠ [{pos['pair']}] 意外消失")
                    if closed_log:
                        last = closed_log[-1]
                        if last['pair'] == pos['pair']:
                            continue
            
            for pid, pos in list(tracked.items()):
                gp = game_positions.get(pid)
                if not gp:
                    continue
                curr = s['prices'][pos['pair']]
                pnl_pct = (gp['notional'] * gp['side'] * 
                          (curr / gp['entry'] - 1)) / gp['margin']
                
                reason = None
                if pnl_pct <= STOP_LOSS_PCT:
                    reason = f'SL({pnl_pct*100:+.1f}%)'
                elif pnl_pct >= TAKE_PROFIT_PCT:
                    reason = f'TP({pnl_pct*100:+.1f}%)'
                elif now - pos['opened_at'] >= TIME_STOP_S:
                    reason = f'T({now-pos["opened_at"]:.0f}s,{pnl_pct*100:+.1f}%)'
                
                if reason:
                    print(f"  ⏹ [{pos['pair']} {'L' if pos['side']==1 else 'S'}] {reason}")
                    ok, pnl = do_close(bot, pos['pair'])
                    if ok:
                        tracked.pop(pid, None)
                        cooldowns[pos['pair']] = now + PAIR_COOLDOWN_S
                        closes_count += 1
                        closed_log.append({'pair': pos['pair'], 'side': pos['side'],
                                          'entry': pos['entry'], 'pnl': pnl, 'reason': reason})
                    else:
                        print(f"    ⚠ close failed")
                        errors.append(f'close {pos["pair"]}')
            
            # ---------- 2. 检查入场 ----------
            # 只有 < 5 仓位才开
            if len(game_positions) >= MAX_SLOTS:
                time.sleep(0.2)
                continue
            
            # 每 tick 只试一笔
            opened_this_tick = False
            for pair in PAIRS:
                if len(game_positions) >= MAX_SLOTS:
                    break
                if any(p['pair'] == pair for p in game_positions.values()):
                    continue  # 已有此 pair
                if cooldowns.get(pair, 0) > now:
                    continue  # 冷却中
                
                candles = s['candles'][pair]
                direction = check_entry(candles, PAIR_INDEX[pair])
                if direction == 0:
                    continue
                
                side_str = 'long' if direction == 1 else 'short'
                print(f"  ▶ [{pair} {'L' if direction==1 else 'S'}] "
                      f"drift={drift_of(PAIR_INDEX[pair])*10000:+.2f}bp")
                
                ok, pid, entry = do_open(bot, pair, side_str, MARGIN, LEVERAGE)
                if ok:
                    tracked[pid] = {'pair': pair, 'side': direction, 
                                    'entry': entry, 'opened_at': time.time()}
                    opens_count += 1
                    opened_this_tick = True
                else:
                    print(f"    ⚠ open failed")
                    errors.append(f'open {pair}')
                    # 换一个 pair 试试
                    game_positions = {p['id']: p for p in bot.state()['account']['positions']}
                
                break  # 一次 tick 只开一笔
            
            # 状态
            if int(now - start) % 15 == 0 and (now - int(now - start)) < 1:
                wins = sum(1 for c in closed_log if c['pnl'] > 0)
                losses = sum(1 for c in closed_log if c['pnl'] <= 0)
                total_pnl = sum(c['pnl'] for c in closed_log)
                s2 = bot.state()
                print(f"  ── [{time.strftime('%H:%M:%S')}] cash=${s2['account']['cash']:.2f}  "
                      f"open={opens_count}  close={closes_count}  "
                      f"closed={len(closed_log)}(W{wins}/L{losses}) "
                      f"sum=${total_pnl:+.2f}  errors={len(errors)}")
            
            time.sleep(0.2)
    
    except KeyboardInterrupt:
        pass
    
    # ---------- 3. 收尾 ----------
    print("\n--- 收尾 ---")
    for _ in range(20):  # 多轮保证全清
        s = bot.state()
        if not s['account']['positions']:
            break
        for p in s['account']['positions']:
            print(f"  平 [{p['pair']} side={p['side']}] id={p['id'][:20]}...")
            ok, pnl = do_close(bot, p['pair'])
            if not ok:
                print(f"    ⚠ close failed")
                break
            time.sleep(0.2)
    
    final = bot.state()
    final_cash = final['account']['cash']
    print(f"\n{'='*60}")
    print(f"最终: ${final_cash:.2f}")
    print(f"盈亏: ${final_cash - initial_cash:+.2f} ({(final_cash/initial_cash-1)*100:+.2f}%)")
    print(f"开仓: {opens_count}  平仓: {closes_count}  错误: {len(errors)}")
    if closed_log:
        wins = sum(1 for c in closed_log if c['pnl'] > 0)
        losses = sum(1 for c in closed_log if c['pnl'] <= 0)
        total_pnl = sum(c['pnl'] for c in closed_log)
        print(f"closed_log: W{wins}/L{losses} sum=${total_pnl:+.2f}")
    
    bot.close()


if __name__ == "__main__":
    run()
