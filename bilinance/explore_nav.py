"""找到主导航并进入交易页, 摸交易按钮"""
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
        gf.evaluate("""() => {
            const skip = document.getElementById('welcomeSkip');
            if (skip && skip.offsetParent !== null) skip.click();
        }""")
        time.sleep(0.5)

        # 找顶部导航: 文本包含 行情/交易/合约/资产/挑战 的元素
        nav = gf.evaluate("""() => {
            const labels = ['行情','交易','合约','资产','挑战'];
            const out = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.children.length > 0) return;  // 只要叶子节点
                const t = (el.textContent||'').trim();
                if (labels.includes(t)) {
                    out.push({tag: el.tagName, id: el.id, cls: (el.className||'').toString().slice(0,40), text: t, parentCls: (el.parentElement?.className||'').toString().slice(0,40), vis: el.offsetParent !== null});
                }
            });
            return out;
        }""")
        print("=== 导航叶子节点 ===")
        for n in nav:
            print(f"  tag={n['tag']} id={n['id'][:15]:15s} cls={n['cls'][:35]:35s} pCls={n['parentCls'][:35]:35s} txt={n['text']} vis={n['vis']}")

        browser.close()

if __name__ == '__main__':
    main()