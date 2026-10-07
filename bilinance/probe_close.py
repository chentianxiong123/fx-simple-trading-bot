"""测平仓流程 + 找价格读取方式(DOM/Engine)"""
import time, json
from playwright.sync_api import sync_playwright

SHELL_URL = "https://www.bilibili.com/toy/IjaLS8zTiK58TTNZ/index.html"

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

        # 持仓 UI 全貌
        ui = gf.evaluate("""() => {
            const pos = document.querySelector('[class*="position"]');
            const tabs = [];
            document.querySelectorAll('[class*="pos"], [class*="hold"] button, [class*="tab"] button').forEach(b => {
                if (b.offsetParent !== null) tabs.push(b.textContent.trim().slice(0,15));
            });
            const body = document.body.innerText;
            const idx = body.indexOf('当前持仓');
            return {tabs: [...new Set(tabs)], posSection: body.slice(idx, idx+400)};
        }""")
        print("持仓区:", json.dumps(ui, ensure_ascii=False)[:600])

        # 点 平仓 按钮
        gf.evaluate("""() => {
            const b = Array.from(document.querySelectorAll('button')).find(x => x.className.includes('danger') && /平仓/.test(x.textContent));
            if (b) b.click();
        }""")
        time.sleep(1.2)
        md = gf.evaluate("""() => Array.from(document.querySelectorAll('[class*="modal"],[class*="toast"]')).filter(m=>m.offsetParent!==null).map(m=>({cls:(m.className||'').toString().slice(0,30), txt:(m.textContent||'').trim().slice(0,150)}))""")
        print("\n点平仓后弹窗:", json.dumps(md, ensure_ascii=False))

        # 如果有确认按钮(确认/取消)点确认
        gf.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('[class*="modal"] button, [class*="dialog"] button'));
            const confirm = btns.find(b => /确认|确定|平仓/.test(b.textContent) && b.offsetParent !== null);
            if (confirm) confirm.click();
        }""")
        time.sleep(1.5)
        print("\n确认后 positions:", json.dumps(gf.evaluate("""() => { const s = JSON.parse(localStorage.getItem('binance-sim-v1')); return {positions: s.positions, closed: s.closedPositions.length, lastClosed: s.closedPositions[s.closedPositions.length-1], usdt: s.usdt}; }"""), ensure_ascii=False)[:350])

        # 找价格显示元素: 行情列表
        prices = gf.evaluate("""() => {
            const rows = [];
            document.querySelectorAll('.mkt-table tbody tr, [class*="mkt-table"] tr').forEach(r => {
                rows.push((r.textContent||'').trim().replace(/\\s+/g,' ').slice(0,60));
            });
            return rows.slice(0,5);
        }""")
        print("\n行情行:", json.dumps(prices, ensure_ascii=False))

        browser.close()

if __name__ == '__main__':
    main()