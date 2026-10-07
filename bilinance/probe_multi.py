"""探查持仓行 DOM 结构(多持仓时平仓按钮对应关系)"""
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
        time.sleep(1)

        # 开两个多仓(50U 和 30U)
        for margin in ['50', '30']:
            set_input(gf, 'levInput', '5')
            time.sleep(0.3)
            set_input(gf, 'fMargin', margin)
            time.sleep(0.3)
            gf.evaluate("() => { document.getElementById('fLong').click(); }")
            time.sleep(1.2)
        pos = gf.evaluate("() => { const s = JSON.parse(localStorage.getItem('binance-sim-v1')); return s.positions.map(p=>({id:p.id, margin:p.margin, entry:p.entry.toFixed(2)})); }")
        print("2 个持仓:", json.dumps(pos, ensure_ascii=False))

        # 当前持仓 tab 的 DOM 结构
        dom = gf.evaluate("""() => {
            // 找平仓按钮所在的行结构
            const rows = [];
            document.querySelectorAll('button').forEach(b => {
                if (b.className.includes('danger') && /平仓/.test(b.textContent)) {
                    let el = b;
                    let html = '';
                    for (let i = 0; i < 4 && el; i++) {
                        html = el.outerHTML.slice(0, 300) + ' ||LEVEL' + i + '|| ' + html;
                        el = el.parentElement;
                    }
                    rows.push(html);
                }
            });
            return rows;
        }""")
        print("\n=== 平仓按钮 DOM 结构 ===")
        for r in dom[:2]:
            print(r, "\n---")

        # 持仓区文本(每行内容)
        txt = gf.evaluate("""() => {
            const body = document.body.innerText;
            const i = body.indexOf('当前持仓');
            return body.slice(i, i + 500);
        }""")
        print("\n=== 当前持仓区文本 ===")
        print(txt)

        browser.close()

if __name__ == '__main__':
    main()