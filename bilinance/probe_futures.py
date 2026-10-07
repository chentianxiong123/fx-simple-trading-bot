"""测合约: 填杠杆+保证金开多, 看 positions, 再平仓"""
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

def st(gf):
    return gf.evaluate("""() => {
        const s = JSON.parse(localStorage.getItem('binance-sim-v1'));
        return {usdt: s.usdt, positions: s.positions, closed: s.closedPositions.length, balances: s.balances, openOrders: s.openOrders.length};
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
        gf.evaluate("() => { const a = Array.from(document.querySelectorAll('.nav-links a')).find(x => x.textContent.trim()==='合约'); a.click(); }")
        time.sleep(2)

        # 设杠杆 10x
        set_input(gf, 'levInput', '10')
        time.sleep(0.5)
        # 保证金 50 USDT
        set_input(gf, 'fMargin', '50')
        time.sleep(0.5)
        print("开仓前:", json.dumps(st(gf), ensure_ascii=False)[:250])
        # 开多
        gf.evaluate("() => { document.getElementById('fLong').click(); }")
        time.sleep(1.5)
        print("开多后:", json.dumps(st(gf), ensure_ascii=False)[:400])
        md = gf.evaluate("""() => Array.from(document.querySelectorAll('[class*="toast"]')).filter(m=>m.offsetParent!==null).map(m=>m.textContent.trim().slice(0,90))""")
        print("toast:", json.dumps(md, ensure_ascii=False))

        # 看持仓 UI 结构 (当前持仓 tab)
        pos_ui = gf.evaluate("""() => {
            const rows = [];
            document.querySelectorAll('[class*="pos-row"], [class*="position"] tr, [class*="position"] li').forEach(r => {
                rows.push((r.textContent||'').trim().slice(0,100));
            });
            return rows.slice(0,10);
        }""")
        print("\n持仓UI:", json.dumps(pos_ui, ensure_ascii=False))
        time.sleep(4)
        # 尝试平仓: 找平仓按钮
        close_btns = gf.evaluate("""() => {
            const out = [];
            document.querySelectorAll('button').forEach(b => {
                if (b.offsetParent !== null && /平仓|平多|平空/.test(b.textContent))
                    out.push({id: b.id, cls: (b.className||'').toString().slice(0,35), txt: b.textContent.trim().slice(0,20)});
            });
            return out;
        }""")
        print("平仓按钮:", json.dumps(close_btns, ensure_ascii=False))

        browser.close()

if __name__ == '__main__':
    main()