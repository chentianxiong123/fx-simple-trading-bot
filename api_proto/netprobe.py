"""网络探针：hook fetch/WebSocket，看游戏数据通道"""
import time, json
from playwright.sync_api import sync_playwright

IFRAME_URL = "https://www.bilibilitoy.com/toy/fx-simple/37279699568640-v21020/index.html"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        ctx = browser.new_context()
        page = ctx.new_page()
        
        # hook fetch
        page.add_init_script("""
            window.__netlog = [];
            const _origFetch = window.fetch;
            window.fetch = function(url, opts) {
                try {
                    window.__netlog.push({type:'fetch', url: String(url), method: opts?.method||'GET'});
                } catch(e) {}
                return _origFetch.apply(this, arguments);
            };
            // hook WebSocket
            const _origWS = window.WebSocket;
            window.WebSocket = function(url, protocols) {
                try {
                    window.__netlog.push({type:'ws', url: String(url)});
                } catch(e) {}
                const ws = protocols ? new _origWS(url, protocols) : new _origWS(url);
                const origSend = ws.send;
                ws.send = function(data) {
                    try { window.__netlog.push({type:'ws-send', data: String(data).slice(0,200)}); } catch(e) {}
                    return origSend.call(this, data);
                };
                ws.addEventListener('message', (ev) => {
                    try { window.__netlog.push({type:'ws-msg', data: String(ev.data).slice(0,200)}); } catch(e) {}
                });
                return ws;
            };
            window.WebSocket.prototype = _origWS.prototype;
        """)
        
        page.goto(IFRAME_URL, wait_until='domcontentloaded', timeout=30000)
        time.sleep(15)
        
        netlog = page.evaluate("() => JSON.stringify(window.__netlog || [])")
        logs = json.loads(netlog)
        print(f"=== 捕获 {len(logs)} 条网络记录 ===\n")
        seen = set()
        for l in logs:
            key = (l['type'], l['url'])
            if key not in seen:
                seen.add(key)
                print(f"[{l['type']}] {l.get('url','')[:150]}")
            if l['type'] == 'ws-msg':
                print(f"    <- {l['data'][:150]}")
            if l['type'] == 'ws-send':
                print(f"    -> {l['data'][:150]}")
        
        browser.close()

if __name__ == '__main__':
    main()
