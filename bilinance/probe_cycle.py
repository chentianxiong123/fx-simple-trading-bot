"""完整闭环: 开仓→读价格→平仓, 找价格元素"""
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

        # 开多 50U 10x
        set_input(gf, 'levInput', '10')
        time.sleep(0.4)
        set_input(gf, 'fMargin', '50')
        time.sleep(0.4)
        gf.evaluate("() => { document.getElementById('fLong').click(); }")
        time.sleep(1.5)
        pos = gf.evaluate("() => { const s = JSON.parse(localStorage.getItem('binance-sim-v1')); return s.positions[0]; }")
        print("持仓:", json.dumps(pos, ensure_ascii=False))

        # 找价格显示元素（盘面大字价格/图表上方）
        price_els = gf.evaluate("""() => {
            const out = [];
            // 1. 各种疑似价格元素
            document.querySelectorAll('[class*="price"],[class*="last"],[class*="px"],[class*="quote"],[class*="cur"] span,[id*="price"],[id*="last"]').forEach(el => {
                const t = (el.textContent||'').trim();
                if (/^[\\d,.]+$/.test(t.replace(/\\s/g,''))) out.push({tag: el.tagName, id: el.id, cls: (el.className||'').toString().slice(0,30), txt: t.slice(0,15)});
            });
            return out.slice(0,15);
        }""")
        print("\n价格元素:", json.dumps(price_els, ensure_ascii=False))

        # 订单簿买一价
        book = gf.evaluate("""() => {
            const rows = [];
            document.querySelectorAll('[class*="book"] [class*="row"], [class*="orderbook"] [class*="row"]').forEach(r => {
                rows.push((r.textContent||'').trim().replace(/\\s+/g,' ').slice(0,50));
            });
            return rows.slice(0,6);
        }""")
        print("\n订单簿:", json.dumps(book, ensure_ascii=False))

        # 平仓: 找持仓行里的 平仓 按钮
        gf.evaluate("""() => {
            const b = Array.from(document.querySelectorAll('button')).find(x => x.className.includes('danger') && /平仓/.test(x.textContent));
            if (b) b.click();
        }""")
        time.sleep(1.2)
        modal = gf.evaluate("""() => {
            const out = [];
            document.querySelectorAll('[class*="modal"],[class*="toast"]').forEach(m => {
                if (m.offsetParent !== null) out.push({cls: (m.className||'').toString().slice(0,30), txt: (m.textContent||'').trim().slice(0,160)});
            });
            return out;
        }""")
        print("\n平仓弹窗:", json.dumps(modal, ensure_ascii=False))

        # 弹窗按钮
        modal_btns = gf.evaluate("""() => {
            const out = [];
            document.querySelectorAll('[class*="modal"] button, [class*="dialog"] button').forEach(b => {
                if (b.offsetParent !== null) out.push({cls: (b.className||'').toString().slice(0,30), txt: b.textContent.trim().slice(0,20)});
            });
            return out;
        }""")
        print("弹窗按钮:", json.dumps(modal_btns, ensure_ascii=False))

        browser.close()

if __name__ == '__main__':
    main()