"""探索交易界面: 导航tab/买卖按钮/杠杆/数量输入"""
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
        if not gf:
            print("❌ 无游戏 frame"); browser.close(); return

        # 关闭欢迎弹窗
        gf.evaluate("""() => {
            const skip = document.getElementById('welcomeSkip');
            if (skip && skip.offsetParent !== null) skip.click();
        }""")
        time.sleep(1)

        # 1. 所有导航 tab
        nav = gf.evaluate("""() => {
            const out = [];
            document.querySelectorAll('[class*="nav"] button, [class*="tab"] button, [class*="navItem"], [class*="nav-item"]').forEach(b => {
                out.push({id: b.id, cls: (b.className||'').toString().slice(0,35), text: (b.textContent||'').trim().slice(0,15), vis: b.offsetParent !== null});
            });
            return out;
        }""")
        print("=== 导航元素 ===")
        for n in nav:
            print(f"  id={n['id'][:18]:18s} cls={n['cls'][:30]:30s} txt={n['text']} vis={n['vis']}")

        # 2. 现在 visible 的所有按钮（交易界面）
        print("\n=== 全部可见按钮（欢迎已关）===")
        btns = gf.evaluate("""() => {
            const out = [];
            document.querySelectorAll('button').forEach(b => {
                if (b.offsetParent !== null)
                    out.push({id: b.id, cls: (b.className||'').toString().slice(0,35), text: (b.textContent||'').trim().slice(0,20)});
            });
            return out;
        }""")
        for b in btns:
            print(f"  id={b['id'][:18]:18s} cls={b['cls'][:35]:35s} txt={b['text']}")

        # 3. 输入框
        print("\n=== 输入框 ===")
        ins = gf.evaluate("""() => {
            const out = [];
            document.querySelectorAll('input').forEach(i => {
                if (i.offsetParent !== null)
                    out.push({id: i.id, cls: (i.className||'').toString().slice(0,30), ph: i.placeholder||'', type: i.type});
            });
            return out;
        }""")
        for i in ins:
            print(f"  {i}")

        # 4. 页面主区文本（看交易面板结构）
        txt = gf.evaluate("() => document.body.innerText.slice(0, 900)")
        print(f"\n=== 页面文本 ===")
        print(txt)

        browser.close()

if __name__ == '__main__':
    main()