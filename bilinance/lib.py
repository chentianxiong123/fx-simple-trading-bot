"""
BILINANCE 交易函数库
- 现货: 市价买(USDT金额)/市价卖(币数量)/限价挂单
- 合约: 开多/开空(杠杆+保证金) / 平仓(全平或按比例)
"""
import time


def _set_input(bot, sel, val):
    return bot.frame.evaluate("""(args) => {
        const el = document.getElementById(args.sel);
        if (!el) return false;
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(args.val));
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        return true;
    }""", {'sel': sel, 'val': val})


def _click_text(bot, text):
    return bot.frame.evaluate("""(t) => {
        const b = Array.from(document.querySelectorAll('button'))
            .find(x => x.textContent.trim() === t && x.offsetParent !== null);
        if (b) { b.click(); return true; }
        return false;
    }""", text)


def _click_sel(bot, sel):
    return bot.frame.evaluate("""(s) => {
        const el = document.querySelector(s);
        if (el && el.offsetParent !== null) { el.click(); return true; }
        return false;
    }""", sel)


# ============================================================
# 现货
# ============================================================

def spot_buy_market(bot, usdt_amount):
    """市价买入, usdt_amount 为 USDT 金额(≥1)"""
    bot.nav('交易')
    _click_text(bot, '市价')
    time.sleep(0.3)
    _set_input(bot, 'fQty', usdt_amount)
    time.sleep(0.2)
    _click_sel(bot, '#fSubmit')
    time.sleep(0.8)
    return True


def spot_sell_market(bot, base_qty):
    """市价卖出, base_qty 为币数量"""
    bot.nav('交易')
    _click_text(bot, '卖出')
    time.sleep(0.3)
    _click_text(bot, '市价')
    time.sleep(0.3)
    _set_input(bot, 'fQty', base_qty)
    time.sleep(0.2)
    _click_sel(bot, '#fSubmit')
    time.sleep(0.8)
    return True


def spot_limit(bot, price, qty, side='buy'):
    """限价挂单, side: buy/sell"""
    bot.nav('交易')
    if side == 'sell':
        _click_text(bot, '卖出')
        time.sleep(0.3)
    _click_text(bot, '限价')
    time.sleep(0.3)
    _set_input(bot, 'fPrice', price)
    _set_input(bot, 'fQty', qty)
    time.sleep(0.2)
    _click_sel(bot, '#fSubmit')
    time.sleep(0.8)
    return True


# ============================================================
# 合约
# ============================================================

def fut_open(bot, sym, side, lev, margin, pair='BTCUSDT'):
    """开合约仓, side: 'long'/'short', lev 杠杆, margin 保证金(≥5)"""
    bot.nav('合约')
    bot.nav_sym('futures', pair)
    _set_input(bot, 'levInput', lev)
    time.sleep(0.3)
    _set_input(bot, 'fMargin', margin)
    time.sleep(0.3)
    btn = 'fLong' if side == 'long' else 'fShort'
    bot.frame.evaluate(f"() => document.getElementById('{btn}').click()")
    time.sleep(0.8)
    return True


def fut_close(bot, pos_id):
    """按仓位 id 全平"""
    return bot.frame.evaluate("""(id) => {
        const b = document.querySelector('[data-close="' + id + '"]');
        if (b) { b.click(); return true; }
        return false;
    }""", pos_id)


def fut_close_pct(bot, pos_id, pct):
    """按比例平仓, pct: 1-100"""
    return bot.frame.evaluate("""(args) => {
        const slider = document.querySelector('[data-slider="' + args.id + '"]');
        if (!slider) return false;
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(slider, String(args.pct));
        slider.dispatchEvent(new Event('input', {bubbles: true}));
        slider.dispatchEvent(new Event('change', {bubbles: true}));
        const b = document.querySelector('[data-close="' + args.id + '"]');
        if (b) { b.click(); return true; }
        return false;
    }""", {'id': pos_id, 'pct': pct})


def fut_positions(bot):
    """当前合约持仓列表"""
    s = bot.state()
    return s['positions']


# ============================================================
# 工具
# ============================================================

def toast(bot):
    """当前 toast 消息"""
    return bot.frame.evaluate("""() => Array.from(document.querySelectorAll('[class*="toast"]'))
        .filter(m => m.offsetParent !== null).map(m => m.textContent.trim())""")
