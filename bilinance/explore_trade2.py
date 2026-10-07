"""进入交易页, 摸交易面板按钮/输入"""
import time, json
from playwright.sync_api import sync_playwright

SHELL_URL = "https://www.bilibili.com/toy/IjaLS8zTiK58TTNZ/index.html"

def dump(gf, label):
    print(f"\n===== {label} =====")
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
                out.push({id: i.id, cls: (i.className||'').toString().slice(0,35), ph: i.placeholder||'', type: i.type});
        });
        return out;
    }""")
    for i in ins:
        print(f"  [inp] id={i['id'][:16]:16s} cls={i['cls'][:35]:35s} ph={i['ph']}")
    txt = gf.evaluate("() => document.body.innerText.slice(0, 700)")
    print("  --- 页面文本 ---")
    print(txt[:650])

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
        time.sleep(0.5)

        # 点 交易 tab
        gf.evaluate("""() => {
            const links = document.querySelectorAll('.nav-links a');
            for (const a of links) {
                if (a.textContent.trim() === '交易') { a.click(); break; }
            }
        }""")
        time.sleep(2)
        dump(gf, "交易页")

        browser.close()

if __name__ == '__main__':
    main()