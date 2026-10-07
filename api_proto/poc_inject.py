"""PoC: route 篡改 app.js, 暴露内部函数, 直接 JS 调用开仓/平仓"""
import time, json
import gzip
from playwright.sync_api import sync_playwright

SHELL_URL = "https://www.bilibilitoy.com/toy/fx-simple/37279699568640-v21020/index.html"
APP_JS_PATTERN = "**/fx-simple/**/app.js?v=3.0.1"
EXPOSE_SUFFIX = """
window.__game = {
    openPosition: openPosition,
    closePosition: closePosition,
    getState: () => state,
    getSim: () => sim,
    save: save,
    setPair: (id) => { state.pair = id; save(); render(); },
};
"""

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()

        def intercept(route):
            # 用 urllib 同步抓取并篡改（避免 sync API 的 response dispose 问题）
            import urllib.request as ureq
            req = ureq.Request(route.request.url, headers={'Accept-Encoding': 'gzip', 'User-Agent': 'Mozilla/5.0'})
            raw = ureq.urlopen(req, timeout=15).read()
            body = gzip.decompress(raw).decode('utf-8', errors='replace')
            if body.rstrip().endswith('})();'):
                idx = body.rfind('})();')
                body = body[:idx] + EXPOSE_SUFFIX + '})();'
                print(f"✅ 已篡改 app.js, 注入 __game 暴露")
            route.fulfill(status=200, content_type='application/javascript', body=body)

        ctx.route(APP_JS_PATTERN, intercept)
        page = ctx.new_page()
        page.on('console', lambda msg: print(f"[console] {msg.type}: {msg.text[:120]}") if msg.type == 'error' else None)
        page.on('pageerror', lambda e: print(f"[pageerror] {e}"))
        page.goto(SHELL_URL, wait_until='domcontentloaded', timeout=40000)
        time.sleep(15)

        # 找游戏 iframe
        game_frame = None
        for f in page.frames:
            try:
                has_key = f.evaluate("() => !!localStorage.getItem('fx-heartbeat-save-v3')")
                print(f"[frame] {f.url[:90]}  has_key={has_key}")
                if 'bilibilitoy.com' in f.url:
                    game_frame = f
            except Exception as ex:
                print(f"[frame] {f.url[:90]}  eval_error={str(ex)[:60]}")
        if not game_frame:
            print("❌ 没找到游戏 iframe")
            browser.close()
            return

        # 调试: 游戏 frame 内部状态
        dbg = game_frame.evaluate("""() => {
            const ls = {};
            for (let i = 0; i < localStorage.length; i++) {
                const k = localStorage.key(i);
                ls[k] = String(localStorage.getItem(k)).slice(0, 80);
            }
            return {
                has_game_api: typeof window.__game !== 'undefined',
                ls_keys: ls,
                body_text: document.body?.innerText?.slice(0, 200) || '',
            };
        }""")
        print("\n[游戏frame调试]")
        print(json.dumps(dbg, ensure_ascii=False, indent=2)[:1200])


        r = game_frame.evaluate("""() => {
            const g = window.__game;
            if (!g) return {exposed: false};
            return {exposed: true, has_open: typeof g.openPosition, has_close: typeof g.closePosition};
        }""")
        print("暴露检查:", json.dumps(r, ensure_ascii=False))

        if not r.get('exposed'):
            browser.close()
            return

        # 直接调用开仓
        r2 = game_frame.evaluate("""() => {
            const g = window.__game;
            const st = g.getState();
            const before = st.positions.length;
            const ok = g.openPosition('long');
            const after = g.getState().positions.length;
            const pos = g.getState().positions[g.getState().positions.length-1];
            return {before, after, ok, side: pos?.side, entry: pos?.entry, margin: pos?.margin, cash: g.getState().cash};
        }""")
        print("直调开仓:", json.dumps(r2, ensure_ascii=False))

        # 等一下 tick 然后直接平仓
        time.sleep(6)
        r3 = game_frame.evaluate("""() => {
            const g = window.__game;
            const st = g.getState();
            const pos = st.positions[st.positions.length-1];
            if (!pos) return {no_position: true};
            const before = st.positions.length;
            g.closePosition(pos.id, false);
            return {before, after: g.getState().positions.length, closed_id: pos.id};
        }""")
        print("直调平仓:", json.dumps(r3, ensure_ascii=False))

        browser.close()

if __name__ == '__main__':
    main()