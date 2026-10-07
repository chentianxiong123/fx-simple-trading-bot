"""调试现货下单: 市价/限价都试, 看模式切换后的输入框和提交文本"""
import time, json
from playwright.sync_api import sync_playwright

SHELL_URL = "https://www.bilibili.com/toy/IjaLS8zTiK58TTNZ/index.html"

def set_input(gf, sel, val):
    return gf.evaluate("""(args) => {
        const el = document.getElementById(args.sel);
        if (!el) return false;
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(el, String(args.val));
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        return true;
    }""", {'sel': sel, 'val': val})

def state_short(gf):
    return gf.evaluate("""() => {
        const s = JSON.parse(localStorage.getItem('binance-sim-v1'));
        return {usdt: s.usdt, openOrders: s.openOrders.length, balances: s.balances, history: (s.history||[]).length, lastHist: (s.history||[])[(s.history||[]).length-1] || null};
    }""")

def mode_check(gf):
    return gf.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const sub = btns.find(b => b.id === 'fSubmit') || btns.find(b => b.className.includes('sub-btn'));
        const inputs = [];
        document.querySelectorAll('input').forEach(i => { if (i.offsetParent !== null) inputs.push(i.id); });
        return {submit: sub ? {id: sub.id, txt: sub.textContent.trim(), cls: sub.className} : null, inputs};
    }""")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(SHELL_URL, wait_until='domcontentloaded', timeout=40000)
        time.sleep(8)
        gf = None
        for f in page.frames:
            try:
                if f.evaluate("() => !!localStorage.getItem('binance-sim-v1')"):
                    gf = f
                    break
            except Exception:
                pass
        gf.evaluate("() => { const s = document.getElementById('welcomeSkip'); if (s && s.offsetParent !== null) s.click(); }")
        gf.evaluate("() => { const a = Array.from(document.querySelectorAll('.nav-links a')).find(x => x.textContent.trim()==='交易'); a.click(); }")
        time.sleep(2)

        # 默认状态
        print("初始:", json.dumps(mode_check(gf), ensure_ascii=False))

        # 市价模式
        gf.evaluate("() => { const b = Array.from(document.querySelectorAll('button')).find(x => x.textContent.trim()==='市价'); if (b) b.click(); }")
        time.sleep(0.5)
        print("切市价后:", json.dumps(mode_check(gf), ensure_ascii=False))

        # 市价模式填低点数(0.0002 BTC ≈ 14U)提交
        set_input(gf, 'fQty', '0.0002')
        time.sleep(0.3)
        st1 = state_short(gf)
        gf.evaluate("() => { const b = document.getElementById('fSubmit'); if (b) b.click(); }")
        time.sleep(1.5)
        st2 = state_short(gf)
        print(f"\n市价 0.0002BTC:\n  前={json.dumps(st1, ensure_ascii=False)[:150]}\n  后={json.dumps(st2, ensure_ascii=False)[:200]}")

        # 弹窗
        md = gf.evaluate("""() => Array.from(document.querySelectorAll('[class*="toast"]')).filter(m=>m.offsetParent!==null).map(m=>m.textContent.trim().slice(0,80))""")
        print("toast:", json.dumps(md, ensure_ascii=False))

        # 限价模式: 价格=当前价, 数量0.0002
        gf.evaluate("() => { const b = Array.from(document.querySelectorAll('button')).find(x => x.textContent.trim()==='限价'); if (b) b.click(); }")
        time.sleep(0.5)
        price = gf.evaluate("""() => {
            const s = JSON.parse(localStorage.getItem('binance-sim-v1'));
            return s.lastSym?.trade ? null : null;
        }""")
        # 读当前 BTC 价
        cur_price = gf.evaluate("() => { const el = document.querySelector('.mkt-table') ? null : null; return null; }")
        set_input(gf, 'fQty', '0.0002')
        gf.evaluate("""() => {
            const s = JSON.parse(localStorage.getItem('binance-sim-v1'));
            window.__testCur = s.lastSym;
        }""")
        print("debug lastSym:", end=" ")
        gf.evaluate("() => { }")
        set_input(gf, 'fPrice', '1')
        time.sleep(0.3)
        st3 = state_short(gf)
        gf.evaluate("() => { const b = document.getElementById('fSubmit'); if (b) b.click(); }")
        time.sleep(1.5)
        st4 = state_short(gf)
        print(f"\n限价 fPrice=1, fQty=0.0002:\n  前={json.dumps(st3, ensure_ascii=False)[:120]}\n  后={json.dumps(st4, ensure_ascii=False)[:220]}")
        md2 = gf.evaluate("""() => Array.from(document.querySelectorAll('[class*="toast"]')).filter(m=>m.offsetParent!==null).map(m=>m.textContent.trim().slice(0,80))""")
        print("toast:", json.dumps(md2, ensure_ascii=False))

        browser.close()

if __name__ == '__main__':
    main()