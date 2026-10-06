"""
FX 简单! 游戏自动化 —— 最小化版本

只用一个模式 (sim) + 一个币种 (EUR/USD)
所有操作封装成 5 个函数，跑通就能扩
"""
import time
import json
from playwright.sync_api import sync_playwright

GAME_URL = "https://www.bilibilitoy.com/toy/fx-simple/37279699568640-v21020/index.html"
SHELL_URL = "https://www.bilibili.com/toy/fx-simple/index.html"


class FXBot:
    """所有 API 都在这一层，业务逻辑只看这里。"""

    def __init__(self, headless=False, pair="EUR/USD"):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(
            headless=headless,
            channel="chrome",
            args=["--start-maximized"],
        )
        self.page = self.browser.new_page()
        # 直接打开 shell（它会自动 iframe 到游戏）
        self.page.goto(SHELL_URL, wait_until="domcontentloaded")
        # 等 iframe 里的存档写好
        for _ in range(30):
            time.sleep(0.5)
            for f in self.page.frames:
                if f.url.startswith("about:"):
                    continue
                try:
                    s = f.evaluate("() => localStorage.getItem('fx-heartbeat-save-v3')")
                    if s and 'accounts' in s:
                        self.frame = f
                        return
                except Exception:
                    pass
        raise RuntimeError("游戏未加载好")
        self._sleep_js = "ms => new Promise(r => setTimeout(r, ms))"

    # ---------- 读 ----------
    def state(self):
        """账户 + 当前价格"""
        return self.frame.evaluate("""
            () => {
                const s = JSON.parse(localStorage.getItem('fx-heartbeat-save-v3'));
                const a = s.accounts[s.mode] || {};
                const prices = {};
                for (const [k, v] of Object.entries(s.sim)) prices[k] = v.price;
                return {
                    mode: s.mode,
                    cash: a.cash, debt: a.debt,
                    positions: a.positions,
                    pair: a.pair, leverage: a.leverage, margin: a.margin,
                    prices: prices,
                    candles: Object.fromEntries(
                        Object.entries(s.sim).map(([k, v]) => [k, v.candles.slice(-30)])
                    ),
                };
            }
        """)

    def prices(self):
        """只要价格"""
        return self.frame.evaluate("""
            () => Object.fromEntries(
                Object.entries(JSON.parse(localStorage.getItem('fx-heartbeat-save-v3')).sim)
                    .map(([k, v]) => [k, v.price])
            )
        """)

    # ---------- 写 ----------
    def select_pair(self, pair_id):
        """切换币种，pair_id 例如 'EUR/USD', 'USD/JPY'"""
        self.frame.evaluate("""(id) => {
            const btn = Array.from(document.querySelectorAll('button'))
                .find(b => b.textContent.includes(id.replace('/', ' / ')) || b.textContent.startsWith(id));
            if (btn) btn.click();
        }""", pair_id)

    def set_margin(self, margin):
        """设保证金"""
        self.frame.evaluate("""(v) => {
            const el = document.getElementById('marginInput');
            const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            s.call(el, String(v));
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        }""", margin)

    def set_leverage(self, lv):
        """设杠杆 (1-100)"""
        self.frame.evaluate("""(v) => {
            const el = document.getElementById('leverageRange');
            const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            s.call(el, String(v));
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        }""", lv)

    def open_position(self, side):
        """开仓 side='long' 或 'short'"""
        btn_id = 'longBtn' if side == 'long' else 'shortBtn'
        self.frame.evaluate(f"document.getElementById('{btn_id}').click()")

    def close_position(self, position_id=None):
        """平仓（第一个仓位，或指定 id）"""
        self.frame.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'))
                .filter(b => b.textContent.trim() === '平仓');
            if (btns.length) btns[0].click();
        }""")
        # 平仓后有弹窗，关掉它
        time.sleep(0.3)
        self.frame.evaluate("""() => {
            const c = document.getElementById('modalConfirm');
            if (c && c.offsetParent !== null) c.click();
        }""")

    def close(self):
        self.browser.close()
        self.p.stop()


# ============================================================
# 验证脚本
# ============================================================

def smoke_test():
    bot = FXBot(headless=False)

    print("=" * 60)
    print("初始状态:")
    s = bot.state()
    print(f"  mode={s['mode']}  pair={s['pair']}  cash=${s['cash']:.2f}")
    print(f"  持仓数: {len(s['positions'])}")
    print(f"  价格: EUR/USD={s['prices']['EUR/USD']:.5f}  USD/JPY={s['prices']['USD/JPY']:.3f}")

    print("\n--- 执行一系列操作 ---")

    # 1. 设杠杆 30x
    bot.set_leverage(30)
    time.sleep(0.2)

    # 2. 设保证金 1000
    bot.set_margin(1000)
    time.sleep(0.2)

    # 3. 做多 EUR/USD
    bot.open_position('long')
    time.sleep(0.3)

    s = bot.state()
    print(f"开多后: cash=${s['cash']:.2f}  持仓={len(s['positions'])}")
    if s['positions']:
        p = s['positions'][0]
        print(f"  仓位: {p['pair']} {p['side']} @{p['entry']:.5f}  margin={p['margin']}  lev={p['leverage']}x  fee=${p['fee']:.2f}")

    # 4. 等 3 秒看价格变化
    print("\n--- 等 3 秒，读价格变化 ---")
    price_history = []
    for _ in range(3):
        time.sleep(1.5)  # 一个 tick
        prices = bot.prices()
        price_history.append({'EUR/USD': prices['EUR/USD'], 'ts': time.time()})
        print(f"  t={len(price_history)*1.5:.1f}s  EUR/USD={prices['EUR/USD']:.5f}")

    # 5. 读当前 PnL
    s = bot.state()
    if s['positions']:
        p = s['positions'][0]
        current_price = s['prices']['EUR/USD']
        pnl = p['notional'] * p['side'] * (current_price / p['entry'] - 1)
        print(f"\n当前 PnL: ${pnl:.2f}  (入场 {p['entry']:.5f} → 现在 {current_price:.5f})")

    # 6. 平仓
    print("\n--- 平仓 ---")
    bot.close_position()
    time.sleep(0.5)

    s = bot.state()
    print(f"平仓后: cash=${s['cash']:.2f}  持仓={len(s['positions'])}")
    if s.get('history'):
        h = s['history'][0]
        print(f"  记录: {h['pair']} {h['side']} pnl=${h['pnl']:.2f}")

    bot.close()
    print("\n✅ 完成")


if __name__ == "__main__":
    smoke_test()
