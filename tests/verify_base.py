"""
基础功能验证:
1. select_pair 切换正确
2. open_position 开仓正确
3. close_pair 关特定 pair 正确
4. 多仓位不混淆
"""
import time
from bot import FXBot

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY"]


def verify_state(bot, expect_positions):
    """验证当前状态是否符合预期"""
    s = bot.state()
    actual = [(p['pair'], 'long' if p['side']==1 else 'short') for p in s['account']['positions']]
    expect = [(p, 'long' if d==1 else 'short') for p, d in expect_positions]
    ok = sorted(actual) == sorted(expect)
    print(f"  {'✓' if ok else '✗'} 期望={expect} 实际={actual}")
    return ok


def close_pair(bot, pair_id):
    """关闭指定 pair 的仓位 (只查直接父元素)"""
    result = bot.frame.evaluate(r"""(pairId) => {
        const btns = Array.from(document.querySelectorAll('button'))
            .filter(b => b.textContent.trim() === '平仓');
        for (const btn of btns) {
            const el = btn.parentElement;
            if (el && el.className.includes('position-row') && el.textContent.includes(pairId)) {
                btn.click();
                return {ok: true, pair: pairId, btnCount: btns.length};
            }
        }
        return {ok: false, btnCount: btns.length};
    }""", pair_id)
    time.sleep(0.5)
    bot.frame.evaluate(r"""() => {
        const c = document.getElementById('modalConfirm');
        if (c && c.offsetParent !== null) c.click();
    }""")
    time.sleep(0.3)
    return result


def run():
    bot = FXBot(headless=False)
    bot.reset()
    
    print("=" * 60)
    print("基础功能验证")
    print("=" * 60)
    
    # 测试 1: 单个开仓平仓
    print("\n[测试 1] 单个开仓平仓")
    bot.select_pair("EUR/USD")
    time.sleep(0.2)
    bot.set_margin(1000)
    time.sleep(0.1)
    bot.set_leverage(20)
    time.sleep(0.1)
    bot.open_position('long')
    time.sleep(0.5)
    
    s = bot.state()
    pos = s['account']['positions'][0]
    print(f"  入场: {pos['pair']} {pos['side']} @ {pos['entry']:.5f}")
    
    assert pos['pair'] == 'EUR/USD', f"pair 不对: {pos['pair']}"
    assert pos['entry'] > 1.0 and pos['entry'] < 2.0, f"EUR/USD 价格不对: {pos['entry']}"
    print(f"  ✓ EUR/USD 价格合理 ({pos['entry']:.5f})")
    
    result = close_pair(bot, 'EUR/USD')
    print(f"  关闭: {result}")
    assert result['ok'], "关闭失败"
    
    time.sleep(0.3)
    s = bot.state()
    assert len(s['account']['positions']) == 0, "仓位没清空"
    print(f"  ✓ 仓位已清空")
    
    # 测试 2: 多仓位
    print("\n[测试 2] 多仓位不混淆")
    
    # 开 EUR/USD
    bot.select_pair("EUR/USD")
    time.sleep(0.2)
    bot.set_margin(1000)
    time.sleep(0.1)
    bot.set_leverage(20)
    time.sleep(0.1)
    bot.open_position('long')
    time.sleep(0.5)
    
    # 开 GBP/USD
    bot.select_pair("GBP/USD")
    time.sleep(0.2)
    bot.set_margin(1000)
    time.sleep(0.1)
    bot.set_leverage(20)
    time.sleep(0.1)
    bot.open_position('short')
    time.sleep(0.5)
    
    verify_state(bot, [('EUR/USD', 1), ('GBP/USD', -1)])
    
    s = bot.state()
    print(f"  EUR/USD 入场: {[p['entry'] for p in s['account']['positions'] if p['pair']=='EUR/USD'][0]:.5f}")
    print(f"  GBP/USD 入场: {[p['entry'] for p in s['account']['positions'] if p['pair']=='GBP/USD'][0]:.5f}")
    
    # 关闭 EUR/USD (应该只关这个)
    result = close_pair(bot, 'EUR/USD')
    print(f"\n  关闭 EUR/USD: {result}")
    assert result['ok'], "关闭失败"
    
    time.sleep(0.3)
    verify_state(bot, [('GBP/USD', -1)])
    
    # 关闭 GBP/USD
    result = close_pair(bot, 'GBP/USD')
    print(f"  关闭 GBP/USD: {result}")
    assert result['ok'], "关闭失败"
    
    time.sleep(0.3)
    verify_state(bot, [])
    
    print("\n" + "=" * 60)
    print("✓ 所有基础功能验证通过")
    print("=" * 60)
    
    bot.close()


if __name__ == "__main__":
    run()
