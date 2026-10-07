"""深入探针：抓所有网络响应 URL + 检查 JS 源码中的 API 调用"""
import time, json, re
from playwright.sync_api import sync_playwright

IFRAME_URL = "https://www.bilibilitoy.com/toy/fx-simple/37279699568640-v21020/index.html"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        seen_urls = set()
        js_srcs = []

        def on_response(resp):
            u = resp.url
            if 'bilibili' in u or 'bilibilitoy' in u:
                if u not in seen_urls:
                    seen_urls.add(u)
                    try:
                        ct = resp.headers.get('content-type', '')
                    except: ct = ''
                    print(f"[resp] {ct[:40]:40s} {u[:160]}")

        page.on('response', on_response)
        page.goto(IFRAME_URL, wait_until='domcontentloaded', timeout=30000)
        time.sleep(12)

        # 收集 iframe 里的 JS 文件列表
        js_srcs = page.evaluate("""() => {
            const out = [];
            document.querySelectorAll('script[src]').forEach(s => out.push(s.src));
            return out;
        }""")
        print(f"\n=== iframe JS 文件 ({len(js_srcs)}) ===")
        for s in js_srcs[:20]:
            print(s)

        # 检查有没有 WebSocket / EventSource 使用
        ws_check = page.evaluate("""() => ({
            has_ws_class: typeof WebSocket !== 'undefined',
            ws_in_use: !!window.__netlog?.filter(l => l.type.startsWith('ws')).length,
            service_worker: !!navigator.serviceWorker,
        })""")
        print(f"\n=== WS 检查 ===")
        print(json.dumps(ws_check, indent=2))

        # 抓一个主 JS 分析 API 调用
        print(f"\n=== 主 JS 中的网络调用分析 ===")
        for src in js_srcs:
            if 'index' in src or 'main' in src or '.js' in src:
                r = None
                try:
                    r = page.request.get(src)
                except Exception:
                    r = None
                if r and r.ok:
                    body = r.text()
                    if len(body) > 100:
                        hits = set()
                        for pat in [r'https?://[^"\'\s]+', r'/x/[a-z_/]+', r'WebSocket', r'EventSource', r'fetch\(', r'XMLHttpRequest', r'toy/storage', r'heartbeat', r'sim']:
                            for m in re.findall(pat, body)[:5]:
                                hits.add(m)
                        print(f"\n--- {src.split('/')[-1][:60]} ({len(body)}B) ---")
                        for h in sorted(hits)[:15]:
                            print(f"  {h[:120]}")
                        break

        browser.close()

if __name__ == '__main__':
    main()
