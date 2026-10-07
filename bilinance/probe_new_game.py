"""探查新游戏: 是什么游戏, 网络架构, 数据真实性初步判断"""
import time, json, re
from playwright.sync_api import sync_playwright

URL = "https://www.bilibili.com/toy/IjaLS8zTiK58TTNZ/index.html"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        seen = set()
        js_srcs = []

        def on_response(resp):
            u = resp.url
            if u not in seen and ('bilibili' in u or 'hdslb' in u or 'toy' in u):
                seen.add(u)
                try:
                    ct = resp.headers.get('content-type', '')[:30]
                except: ct = ''
                print(f"[resp] {ct:30s} {u[:140]}")

        page.on('response', on_response)
        page.goto(URL, wait_until='domcontentloaded', timeout=40000)
        time.sleep(12)

        # 页面标题/内容
        for f in page.frames:
            try:
                t = f.evaluate("() => document.title")
                txt = f.evaluate("() => document.body?.innerText?.slice(0,150) || ''")
                if txt.strip():
                    print(f"\n[frame] url={f.url[:80]}")
                    print(f"  title: {t}")
                    print(f"  text: {txt[:150].replace(chr(10), ' | ')}")
            except Exception:
                pass

        # JS 文件
        for f in page.frames:
            try:
                srcs = f.evaluate("""() => Array.from(document.querySelectorAll('script[src]')).map(s => s.src)""")
                for s in srcs:
                    if 'sdk' not in s and s not in js_srcs:
                        js_srcs.append(s)
            except Exception:
                pass
        print(f"\n=== 核心 JS 文件 ({len(js_srcs)}) ===")
        for s in js_srcs[:10]:
            print(s)

        # 本地存储检查（常见游戏标志）
        for f in page.frames:
            try:
                keys = f.evaluate("""() => Array.from({length: localStorage.length}, (_, i) => localStorage.key(i))""")
                if keys:
                    print(f"\n[localStorage] {f.url[:60]}: {keys}")
            except Exception:
                pass

        browser.close()

if __name__ == '__main__':
    main()