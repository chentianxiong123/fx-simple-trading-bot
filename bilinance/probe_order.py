"""测试下单流程: 市价买入小额 + 看成交, 再进合约页摸按钮"""
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
        gf.evaluate("""() => {
            const skip = document.getElementById('welcomeSkip');
            if (skip && skip.offsetParent !== null) skip.click();
        }""")
        gf.evaluate("""() => {
            const links = document.querySelectorAll('.nav-links a');
            for (const a of links) if (a.textContent.trim() === '交易') a.click();
        }""")
        time.sleep(2)

        # 1. 市价买入 (fQty = 0.001 BTC)
        set_input(gf, 'fQty', '0.001')
        time.sleep(0.3)
        st_before = gf.evaluate("""() => {
            const s = JSON.parse(localStorage.getItem('binance-sim-v1'));
            return {usdt: s.usdt, openOrders: s.openOrders.length, balances: s.balances};
        }""")
        print("下单前:", json.dumps(st_before, ensure_ascii=False))

        # 点市价模式
        gf.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const mk = btns.find(b => b.textContent.trim() === '市价');
            if (mk) mk.click();
        }""")
        time.sleep(0.3)
        # 点 买入 BTC
        gf.evaluate("""() => {
            const b = document.getElementById('fSubmit');
            if (b) b.click();
        }""")
        time.sleep(1.5)

        # 看有没有弹窗
        modal = gf.evaluate("""() => {
            const modals = [];
            document.querySelectorAll('[class*="modal"], [class*="dialog"], [class*="toast"], [class*="overlay"]').forEach(m => {
                if (m.offsetParent !== null) modals.push({cls: (m.className||'').toString().slice(0,40), txt: (m.textContent||'').trim().slice(0,120)});
            });
            return modals;
        }""")
        print("\n弹窗:", json.dumps(modal, ensure_ascii=False))

        st_after = gf.evaluate("""() => {
            const s = JSON.parse(localStorage.getItem('binance-sim-v1'));
            return {usdt: s.usdt, openOrders: s.openOrders.length, balances: s.balances};
        }""")
        print("下单后:", json.dumps(st_after, ensure_ascii=False))

        # 2. 进合约页
        gf.evaluate("""() => {
            const links = document.querySelectorAll('.nav-links a');
            for (const a of links) if (a.textContent.trim() === '合约') a.click();
        }""")
        time.sleep(2)
        print("\n===== 合约页 =====")
        btns = gf.evaluate("""() => {
            const out = [];
            document.querySelectorAll('button').forEach(b => {
                if (b.offsetParent !== null)
                    out.push({id: b.id, cls: (b.className||'').toString().slice(0,40), text: (b.textContent||'').trim().slice(0,20)});
            });
            return out;
        }""")
        for b in btns:
            print(f"  [btn] id={b['id'][:16]:16s} cls={b['cls'][:38]:38s} txt={b['text']}")
        ins = gf.evaluate("""() => {
            const out = [];
            document.querySelectorAll('input').forEach(i => {
                if (i.offsetParent !== null)
                    out.push({id: i.id, ph: i.placeholder||'', cls: (i.className||'').toString().slice(0,30)});
            });
            return out;
        }""")
        for i in ins:
            print(f"  [inp] id={i['id'][:16]:16s} ph={i['ph']}")
        txt = gf.evaluate("() => document.body.innerText.slice(0, 500)")
        print("\n页面文本:", txt[:450])

        browser.close()

if __name__ == '__main__':
    main()