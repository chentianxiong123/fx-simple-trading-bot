"""抓 app.js 源码，确认 sim 行情是本地生成还是服务器推送"""
import time, re
from playwright.sync_api import sync_playwright

IFRAME_URL = "https://www.bilibilitoy.com/toy/fx-simple/37279699568640-v21020/index.html"
APP_JS = "https://www.bilibilitoy.com/toy/fx-simple/37279699568640-v21020/app.js?v=3.0.1"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(IFRAME_URL, wait_until='domcontentloaded', timeout=30000)
        time.sleep(8)
        
        resp = page.request.get(APP_JS)
        if resp.ok:
            body = resp.text()
            print(f"app.js 大小: {len(body)}B\n")
            
            # 1. 检查是否连后端（排除 bilibili 公共 SDK 域名）
            print("=== 网络调用关键词 ===")
            for pat in [r'https?://[^"\'\s]+', r'XMLHttpRequest', r'WebSocket\s*\(', r'EventSource', r'\.fetch\s*\(', r'api\.', r'axios', r'setInterval']:
                ms = re.findall(pat, body)
                uniq = sorted(set(m[:100] for m in ms))
                print(f"\n  [{pat}]: {len(uniq)} 个")
                for u in uniq[:8]:
                    print(f"    {u}")
            
            # 2. 找 sim 数据生成逻辑
            print("\n=== sim/price/candle 相关 ===")
            for kw in ['sim', 'price', 'candle', 'heartbeat', 'random', 'Math.random', 'seed', 'tick']:
                cnt = body.count(kw)
                print(f"  '{kw}': {cnt} 处")
            
            # 3. 找交易提交逻辑
            print("\n=== 交易/下单相关 ===")
            for kw in ['open', 'close', 'addPosition', 'positions', 'order', 'submit', 'storage/set', 'set?']:
                cnt = body.count(kw)
                print(f"  '{kw}': {cnt} 处")
        else:
            print(f"抓取失败: {resp.status}")
        browser.close()

if __name__ == '__main__':
    main()