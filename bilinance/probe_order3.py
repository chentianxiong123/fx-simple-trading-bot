"""验证: 市价买入按 USDT 金额, 填 10 试试"""
import time, json
from playwright.sync_api import sync_playwright

SHELL_URL = "https://www.bilibili.com/toy/IjaLS8zTiK58TTNZ/index.html"

def set_input(gf, sel, val):
    gf.evaluate("""(args) => {
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
        return {usdt: s.usdt, balances: s.balances, openOrders: s.openOrders.length, history: s.history.length, last: s.history[s.history.length-1]};
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

        # 市价模式 + 填 10 USDT
        gf.evaluate("() => { const b = Array.from(document.querySelectorAll('button')).find(x => x.textContent.trim()==='市价'); if (b) b.click(); }")
        time.sleep(0.5)
        set_input(gf, 'fQty', '10')
        time.sleep(0.3)
        print("下单前:", json.dumps(state_short(gf), ensure_ascii=False)[:200])
        gf.evaluate("() => { document.getElementById('fSubmit').click(); }")
        time.sleep(1.5)
        print("下单后:", json.dumps(state_short(gf), ensure_ascii=False)[:260])
        md = gf.evaluate("""() => Array.from(document.querySelectorAll('[class*="toast"]')).filter(m=>m.offsetParent!==null).map(m=>m.textContent.trim().slice(0,90))""")
        print("toast:", json.dumps(md, ensure_ascii=False))

        # 然后限价模式测试: 价格输入当前市价附近
        gf.evaluate("() => { const b = Array.from(document.querySelectorAll('button')).find(x => x.textContent.trim()==='限价'); if (b) b.click(); }")
        time.sleep(0.5)
        # 读当前价
        cur = gf.evaluate("""() => {
            const el = document.querySelector('.mkt-table tbody tr .px, .price');
            return el ? el.textContent : null;
        }""")
        set_input(gf, 'fPrice', '65000')
        set_input(gf, 'fQty', '0.0002')
        time.sleep(0.3)
        print("\n限价下单前:", json.dumps(state_short(gf), ensure_ascii=False)[:200])
        gf.evaluate("() => { document.getElementById('fSubmit').click(); }")
        time.sleep(1.5)
        print("限价下单后:", json.dumps(state_short(gf), ensure_ascii=False)[:260])
        md2 = gf.evaluate("""() => Array.from(document.querySelectorAll('[class*="toast"]')).filter(m=>m.offsetParent!==null).map(m=>m.textContent.trim().slice(0,90))""")
        print("toast:", json.dumps(md2, ensure_ascii=False))

        browser.close()

if __name__ == '__main__':
    main()