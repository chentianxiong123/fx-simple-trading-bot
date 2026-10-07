"""验证: 游戏内部函数 openPosition/closePosition 能否从外部直接调用"""
import time, json
from playwright.sync_api import sync_playwright

IFRAME_URL = "https://www.bilibilitoy.com/toy/fx-simple/37279699568640-v21020/index.html"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(IFRAME_URL, wait_until='domcontentloaded', timeout=30000)
        time.sleep(10)
        
        # 1. 检查全局可达性
        r = page.frames[0].evaluate("""() => ({
            typeof_openPosition: typeof openPosition,
            typeof_closePosition: typeof closePosition,
            typeof_state: typeof state,
            typeof_tickSim: typeof tickSim,
            typeof_seedSim: typeof seedSim,
        })""")
        print("=== 全局可达性 ===")
        print(json.dumps(r, indent=2))
        
        # 2. 看按钮 ID 和内部状态
        r2 = page.frames[0].evaluate("""() => {
            const btns = [];
            document.querySelectorAll('button').forEach(b => {
                btns.push({id: b.id, text: b.textContent.trim().slice(0,15), visible: b.offsetParent !== null});
            });
            const inputs = [];
            document.querySelectorAll('input').forEach(i => {
                inputs.push({id: i.id, value: i.value});
            });
            const saved = JSON.parse(localStorage.getItem('fx-heartbeat-save-v3') || 'null');
            return {btns: btns.slice(0,25), inputs: inputs.slice(0,10), sim_price: saved?.sim?.['EUR/USD']?.price};
        }""")
        print("\n=== 按钮/输入框 ===")
        for b in r2['btns']:
            if b['visible']: print(f"  [{b['id']}] {b['text']}")
        print("inputs:", r2['inputs'])
        print("sim EUR/USD price:", r2['sim_price'])
        
        browser.close()

if __name__ == '__main__':
    main()