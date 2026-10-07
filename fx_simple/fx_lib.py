"""
基础函数库 - 每个函数独立，可单独测试
"""
import time
from bot import FXBot


# ============================================================
# 核心函数
# ============================================================

def select_pair(bot, pair_id):
    """切换币种，返回 True/False"""
    result = bot.frame.evaluate(r"""(id) => {
        const btn = Array.from(document.querySelectorAll('button'))
            .find(b => b.textContent.includes(id) && b.className.includes('pair-row'));
        if (btn) {
            btn.click();
            return true;
        }
        return false;
    }""", pair_id)
    time.sleep(0.15)
    return result


def open_position(bot, pair, side, margin=1000, leverage=20):
    """开仓，返回 (success, entry_price)"""
    select_pair(bot, pair)
    bot.frame.evaluate(r"""(v) => {
        const el = document.getElementById('marginInput');
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(v));
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
    }""", margin)
    time.sleep(0.05)
    bot.frame.evaluate(r"""(v) => {
        const el = document.getElementById('leverageRange');
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(v));
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
    }""", leverage)
    time.sleep(0.05)
    btn_id = 'longBtn' if side == 'long' else 'shortBtn'
    bot.frame.evaluate(f"document.getElementById('{btn_id}').click()")
    time.sleep(0.4)
    
    # 确认
    s = bot.state()
    for p in s['account']['positions']:
        if p['pair'] == pair:
            expected_side = 1 if side == 'long' else -1
            if p['side'] == expected_side:
                return True, p['entry']
    return False, None


def close_position(bot, pair_id, index=None):
    """关闭指定 pair 的仓位。如果指定 index，关闭第几个；否则关闭第一个"""
    # 先获取要关闭的仓位信息
    positions = get_positions(bot)
    
    # 找到要关闭的仓位
    pos_to_close = None
    target_index = 0
    
    if index is not None:
        # 按 index 关闭
        for i, p in enumerate(positions):
            if i == index and p['pair'] == pair_id:
                pos_to_close = p
                target_index = i
                break
    else:
        # 关闭第一个匹配的
        for i, p in enumerate(positions):
            if p['pair'] == pair_id:
                pos_to_close = p
                target_index = i
                break
    
    if not pos_to_close:
        return False, 0
    
    # 计算当前 PnL（在关闭前）
    s = bot.state()
    curr = s['prices'][pair_id]
    # notional 已经包含了 leverage * margin，不需要再乘 margin
    pnl_before = (pos_to_close['notional'] * pos_to_close['side'] * 
                  (curr / pos_to_close['entry'] - 1))
    
    # 关闭第 target_index 个平仓按钮
    result = bot.frame.evaluate(r"""(args) => {
        const [pairId, index] = args;
        const btns = Array.from(document.querySelectorAll('button'))
            .filter(b => b.textContent.trim() === '平仓');
        
        // 找到第 index 个匹配的仓位
        let count = 0;
        for (const btn of btns) {
            const el = btn.parentElement;
            if (el && el.className.includes('position-row') && el.textContent.includes(pairId)) {
                if (count === index) {
                    btn.click();
                    return {ok: true};
                }
                count++;
            }
        }
        return {ok: false};
    }""", [pair_id, target_index])
    time.sleep(0.5)
    bot.frame.evaluate(r"""() => {
        const c = document.getElementById('modalConfirm');
        if (c && c.offsetParent !== null) c.click();
    }""")
    time.sleep(0.3)
    
    if not result.get('ok'):
        return False, 0
    
    return True, pnl_before


def get_positions(bot):
    """获取当前所有仓位，返回列表（支持同一 pair 多个仓位）"""
    s = bot.state()
    return s['account']['positions']


def get_positions_dict(bot):
    """获取当前所有仓位，返回 {pair: position_dict}（每个 pair 只保留最后一个）"""
    s = bot.state()
    return {p['pair']: p for p in s['account']['positions']}


def get_pnl_pct(bot, pair_id):
    """获取指定 pair 的 PnL 百分比（相对 margin）"""
    positions = get_positions(bot)
    if pair_id not in positions:
        return None
    pos = positions[pair_id]
    s = bot.state()
    curr = s['prices'][pair_id]
    pnl_pct = (pos['notional'] * pos['side'] * (curr / pos['entry'] - 1)) / pos['margin']
    return pnl_pct


def get_candles(bot, pair_id, limit=20):
    """获取指定 pair 的最近 N 根 K 线"""
    s = bot.state()
    return s['candles'][pair_id][-limit:] if pair_id in s['candles'] else []


def momentum(candles, window=5):
    """计算动量：最近 window 根 K 线，涨返回 1，跌返回 -1，平返回 0"""
    if len(candles) < window:
        return 0
    recent = candles[-window:]
    change = recent[-1]['close'] - recent[0]['close']
    if change > 0:
        return 1
    elif change < 0:
        return -1
    return 0


# ============================================================
# 测试
# ============================================================

def test_all():
    bot = FXBot(headless=False)
    bot.reset()
    
    print("=" * 60)
    print("基础函数测试")
    print("=" * 60)
    
    # 测试 1: select_pair
    print("\n[1] select_pair")
    ok = select_pair(bot, 'EUR/USD')
    print(f"  切换 EUR/USD: {ok}")
    time.sleep(0.2)
    s = bot.state()
    print(f"  当前选中: {s['account']['pair']}")
    assert s['account']['pair'] == 'EUR/USD', "切换失败"
    print("  ✓ 通过")
    
    # 测试 2: open_position
    print("\n[2] open_position")
    ok, entry = open_position(bot, 'EUR/USD', 'long', 1000, 20)
    print(f"  开多 EUR/USD: success={ok}, entry={entry}")
    assert ok and entry and entry > 1.0 and entry < 2.0, "开仓失败或价格错误"
    print(f"  ✓ 通过 (entry={entry:.5f})")
    
    # 测试 3: get_positions
    print("\n[3] get_positions")
    positions = get_positions(bot)
    print(f"  当前仓位: {list(positions.keys())}")
    assert 'EUR/USD' in positions, "仓位不存在"
    print("  ✓ 通过")
    
    # 测试 4: get_pnl_pct
    print("\n[4] get_pnl_pct")
    pnl = get_pnl_pct(bot, 'EUR/USD')
    print(f"  EUR/USD PnL: {pnl*100:.2f}%")
    assert pnl is not None, "PnL 计算失败"
    print("  ✓ 通过")
    
    # 测试 5: get_candles
    print("\n[5] get_candles")
    candles = get_candles(bot, 'EUR/USD')
    print(f"  EUR/USD K 线数量: {len(candles)}")
    assert len(candles) > 0, "K 线为空"
    print(f"  最新 K 线: close={candles[-1]['close']:.5f}")
    print("  ✓ 通过")
    
    # 测试 6: momentum
    print("\n[6] momentum")
    mom = momentum(candles, 5)
    print(f"  5 根 K 线动量: {mom}")
    print("  ✓ 通过")
    
    # 测试 7: close_position
    print("\n[7] close_position")
    ok, pnl = close_position(bot, 'EUR/USD')
    print(f"  关闭 EUR/USD: success={ok}, pnl=${pnl:.2f}")
    assert ok, "关闭失败"
    time.sleep(0.3)
    positions = get_positions(bot)
    assert len(positions) == 0, "仓位没清空"
    print("  ✓ 通过")
    
    # 测试 8: 多仓位
    print("\n[8] 多仓位测试")
    open_position(bot, 'EUR/USD', 'long', 1000, 20)
    time.sleep(0.3)
    open_position(bot, 'GBP/USD', 'short', 1000, 20)
    time.sleep(0.3)
    
    positions = get_positions(bot)
    print(f"  当前仓位: {list(positions.keys())}")
    assert len(positions) == 2, "仓位数量错误"
    print("  ✓ 通过")
    
    # 测试 9: 关闭指定 pair
    print("\n[9] 关闭指定 pair")
    ok, pnl = close_position(bot, 'EUR/USD')
    print(f"  关闭 EUR/USD: success={ok}, pnl=${pnl:.2f}")
    assert ok, "关闭失败"
    time.sleep(0.3)
    positions = get_positions(bot)
    print(f"  剩余仓位: {list(positions.keys())}")
    assert 'GBP/USD' in positions and 'EUR/USD' not in positions, "关闭错误"
    print("  ✓ 通过")
    
    # 清理
    close_position(bot, 'GBP/USD')
    
    print("\n" + "=" * 60)
    print("✓ 所有基础函数测试通过")
    print("=" * 60)
    
    bot.close()


if __name__ == "__main__":
    test_all()
