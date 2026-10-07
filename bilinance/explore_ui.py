"""探索 BILINANCE: 按钮/输入框/localStorage/内部函数"""
import time, json
from playwright.sync_api import sync_playwright

SHELL_URL = "https://www.bilibili.com/toy/IjaLS8zTiK58TTNZ/index.html"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(SHELL_URL, wait_until='domcontentloaded', timeout=40000)
        time.sleep(10)

        # 找游戏 frame
        gf = None
        for f in page.frames:
            try:
                if f.evaluate("() => !!localStorage.getItem('binance-sim-v1')"):
                    gf = f
                    break
            except Exception:
                pass
        if not gf:
            print("❌ 未找到游戏 frame")
            browser.close()
            return
        print(f"✅ 游戏 frame: {gf.url[:90]}\n")

        # 1. localStorage 结构
        ls = gf.evaluate("""() => {
            const s = JSON.parse(localStorage.getItem('binance-sim-v1'));
            const keys = Object.keys(s);
            const preview = {};
            for (const k of keys.slice(0, 15)) {
                const v = s[k];
                preview[k] = (typeof v === 'object') ? (Array.isArray(v)? `arr[${v.length}]` : Object.keys(v).slice(0,8)) : v;
            }
            return {keys, preview};
        }""")
        print("=== localStorage binance-sim-v1 ===")
        print(json.dumps(ls, ensure_ascii=False)[:800], "\n")

        # 2. 所有按钮
        btns = gf.evaluate("""() => {
            const out = [];
            document.querySelectorAll('button, [role="button"], .btn, [class*="tab"], [class*="menu"]').forEach(b => {
                out.push({tag: b.tagName, id: b.id || '', cls: (b.className||'').toString().slice(0,40), text: (b.textContent||'').trim().slice(0,25), vis: b.offsetParent !== null});
            });
            return out;
        }""")
        print(f"=== 按钮/可点元素 ({len(btns)}) ===")
        for b in btns[:60]:
            if b['vis'] or b['id']:
                print(f"  [{b['tag']}] id={b['id'][:20]:20s} cls={b['cls'][:30]:30s} txt={b['text']}")

        # 3. 输入框
        inputs = gf.evaluate("""() => {
            const out = [];
            document.querySelectorAll('input, select, [contenteditable]').forEach(i => {
                out.push({tag: i.tagName, id: i.id || '', cls: (i.className||'').toString().slice(0,30), placeholder: i.placeholder || '', value: i.value || ''});
            });
            return out;
        }""")
        print(f"\n=== 输入框 ({len(inputs)}) ===")
        for i in inputs[:15]:
            print(f"  {i}")

        # 4. 全局变量探测
        globs = gf.evaluate("""() => {
            const cands = ['Store','store','Engine','engine','Game','game','UI','App','app','State','state','S','tick','price','symbols','orders','position'];
            const out = {};
            for (const c of cands) {
                try { out[c] = typeof window[c]; } catch(e) { out[c] = 'err'; }
            }
            return out;
        }""")
        print(f"\n=== 全局变量 ===")
        print(json.dumps(globs, ensure_ascii=False))

        browser.close()

if __name__ == '__main__':
    main()