"""
FX 简单! 游戏自动化 —— 事件驱动版

事件驱动架构:
1. 在游戏 iframe 里装 hook，每次 localStorage 变化就更新 __fx_last_tick
2. Python 侧只 poll 一个整数计数器（不是整个 JSON），250ms 一次
3. 计数器变了才触发 callback，没变就空跑

好处: 不用反复 parse 100KB 的 JSON，CPU 消耗极低
"""
import time
from playwright.sync_api import sync_playwright

GAME_URL = "https://www.bilibilitoy.com/toy/fx-simple/37279699568640-v21020/index.html"
SHELL_URL = "https://www.bilibili.com/toy/fx-simple/index.html"


# ============================================================
# 游戏事件 hook (注入到 iframe)
# ============================================================

INSTALL_HOOK_JS = r"""
() => {
    if (window.__fxHooked) return 'already';
    window.__fx_events = [];
    window.__fx_last_tick = 0;
    window.__fx_last_account_tick = 0;
    window.__fx_last_snapshot = null;
    
    // MutationObserver: 监听 storage event（跨 tab 才触发 storage 事件，同 tab 内用这个变通）
    // 但 localStorage.setItem 不产生 DOM mutation，所以我们 hook setItem
    const origSetItem = window.localStorage.setItem.bind(window.localStorage);
    window.localStorage.setItem = function(key, value) {
        const result = origSetItem(key, value);
        if (key === 'fx-heartbeat-save-v3') {
            window.__fx_last_tick = performance.now();
            try {
                const s = JSON.parse(value);
                const accountSignature = JSON.stringify({
                    cash: s.accounts[s.mode]?.cash,
                    pos: s.accounts[s.mode]?.positions,
                });
                // 只在账户变了的时候算 account tick
                if (window.__fx_last_account_sig !== accountSignature) {
                    window.__fx_last_account_sig = accountSignature;
                    window.__fx_last_account_tick = performance.now();
                }
                window.__fx_last_snapshot = s;
                window.__fx_events.push({
                    t: performance.now(),
                    prices: Object.fromEntries(
                        Object.entries(s.sim).map(([k, v]) => [k, v.price])
                    ),
                });
                if (window.__fx_events.length > 100) {
                    window.__fx_events = window.__fx_events.slice(-50);
                }
            } catch(e) {}
        }
        return result;
    };
    window.__fxHooked = true;
    return 'installed';
}
"""


# ============================================================
# FXBot
# ============================================================

class FXBot:
    def __init__(self, headless=False):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(
            headless=headless,
            channel="chrome",
            args=["--start-maximized"],
        )
        self.page = self.browser.new_page()
        self.page.goto(SHELL_URL, wait_until="domcontentloaded")
        
        # 等游戏 iframe 加载
        self.frame = None
        for _ in range(30):
            time.sleep(0.5)
            for f in self.page.frames:
                try:
                    if f.evaluate("() => !!localStorage.getItem('fx-heartbeat-save-v3')"):
                        self.frame = f
                        break
                except Exception:
                    pass
            if self.frame:
                break
        if not self.frame:
            raise RuntimeError("游戏未加载")
        
        # 安装事件 hook
        status = self.frame.evaluate(INSTALL_HOOK_JS)
        if status != 'already':
            # hook 装完，等第一个 tick 事件
            for _ in range(20):
                if self.frame.evaluate("() => window.__fx_last_tick > 0"):
                    break
                time.sleep(0.2)
        
        self._last_seen_tick = 0
        
        # 事件队列：Python 侧维护的 (timestamp_ms, kind, data)
        self._event_queue = []
    
    # ---------- 读 ----------
    
    def state(self):
        """读取一次完整状态（不依赖 hook，直接读 localStorage）"""
        return self.frame.evaluate(r"""
            () => {
                const s = JSON.parse(localStorage.getItem('fx-heartbeat-save-v3'));
                const a = s.accounts[s.mode] || {};
                const prices = {};
                const candles = {};
                for (const [k, v] of Object.entries(s.sim)) {
                    prices[k] = v.price;
                    candles[k] = v.candles.slice(-30);
                }
                const dom = {};
                const get = (id) => document.getElementById(id);
                const vis = (id) => {
                    const el = get(id);
                    return !!(el && el.offsetParent !== null);
                };
                dom.modal_visible = vis('modalClose');
                dom.modal_title = get('modalTitle')?.textContent || '';
                dom.modal_message = get('modalMessage')?.textContent || '';
                dom.toast = get('toast')?.textContent || '';
                dom.news_visible = vis('newsTicker');
                return {
                    mode: s.mode,
                    account: {
                        cash: a.cash,
                        debt: a.debt,
                        pair: a.pair,
                        leverage: a.leverage,
                        margin: a.margin,
                        fees_paid: a.feesPaid,
                        positions: a.positions,
                        history: (a.history || []).slice(0, 5),
                        equity_trail: a.equityTrail,
                    },
                    prices: prices,
                    candles: candles,
                    dom: dom,
                };
            }
        """)
    
    def tick_info(self):
        """只读 hook 里的时间戳（很轻量）"""
        return self.frame.evaluate(r"""
            () => ({
                last_tick_ms: window.__fx_last_tick,
                last_account_tick_ms: window.__fx_last_account_tick,
                event_count: window.__fx_events.length,
                now: performance.now(),
            })
        """)
    
    def wait_for_tick(self, timeout=5.0):
        """阻塞等到下一个 tick（用 Playwright 的 wait_for_function）"""
        self.frame.wait_for_function(
            "() => window.__fx_last_tick > " + str(self._last_seen_tick),
            timeout=timeout * 1000,
        )
        self._last_seen_tick = self.frame.evaluate("() => window.__fx_last_tick")
        return self.state()
    
    def wait_for_account_change(self, timeout=5.0):
        """等到账户变化（开/平仓/补仓等）"""
        self.frame.wait_for_function(
            "() => window.__fx_last_account_tick > " + str(getattr(self, '_last_seen_account_tick', 0)),
            timeout=timeout * 1000,
        )
        self._last_seen_account_tick = self.frame.evaluate("() => window.__fx_last_account_tick")
        return self.state()
    
    # ---------- 写 ----------
    
    def select_pair(self, pair_id):
        self.frame.evaluate(r"""(id) => {
            const btn = Array.from(document.querySelectorAll('button'))
                .find(b => b.textContent.includes(id.replace('/', ' / ')));
            if (btn) btn.click();
        }""", pair_id)
    
    def set_margin(self, margin):
        self.frame.evaluate(r"""(v) => {
            const el = document.getElementById('marginInput');
            const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            s.call(el, String(v));
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        }""", margin)
    
    def set_leverage(self, lv):
        self.frame.evaluate(r"""(v) => {
            const el = document.getElementById('leverageRange');
            const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            s.call(el, String(v));
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        }""", lv)
    
    def open_position(self, side):
        btn_id = 'longBtn' if side == 'long' else 'shortBtn'
        self.frame.evaluate(f"document.getElementById('{btn_id}').click()")
    
    def close_position(self, index=0):
        self.frame.evaluate(r"""(idx) => {
            const btns = Array.from(document.querySelectorAll('button'))
                .filter(b => b.textContent.trim() === '平仓');
            if (btns[idx]) btns[idx].click();
        }""", index)
        time.sleep(0.3)
        # 关闭确认弹窗
        self.frame.evaluate(r"""() => {
            const c = document.getElementById('modalConfirm');
            if (c && c.offsetParent !== null) c.click();
        }""")
    
    # ---------- 主循环 ----------
    
    def run(self, on_tick, on_account, on_dom, interval=0.25, max_duration=None):
        """
        事件驱动主循环：
          on_tick(state)     每次 tick（价格变）时调用
          on_account(state)  每次账户变化时调用
          on_dom(state)      每次 DOM 弹窗/通知变化时调用
          interval           检查间隔（默认 250ms）
          max_duration       最大运行时长（秒），None 为无限
        """
        start = time.time()
        last_tick = 0
        last_account_tick = 0
        last_dom_sig = ''
        
        while True:
            if max_duration and time.time() - start > max_duration:
                break
            
            info = self.tick_info()
            state = self.state()
            
            # 价格变化 → on_tick
            if info['last_tick_ms'] != last_tick:
                last_tick = info['last_tick_ms']
                on_tick(state)
            
            # 账户变化 → on_account
            if info['last_account_tick_ms'] != last_account_tick:
                last_account_tick = info['last_account_tick_ms']
                on_account(state)
            
            # DOM 状态变化 → on_dom
            dom_sig = f"{state['dom']['modal_visible']}|{state['dom']['modal_title']}|{state['dom']['toast']}"
            if dom_sig != last_dom_sig:
                last_dom_sig = dom_sig
                on_dom(state)
            
            time.sleep(interval)
    
    def close(self):
        self.browser.close()
        self.p.stop()


# ============================================================
# 演示
# ============================================================

def demo():
    bot = FXBot(headless=False)
    
    print("=" * 60)
    print("事件驱动演示 - 30 秒")
    print("=" * 60)
    
    tick_count = [0]
    account_count = [0]
    dom_count = [0]
    prices_seen = []
    
    def on_tick(s):
        tick_count[0] += 1
        prices_seen.append(s['prices']['EUR/USD'])
        if tick_count[0] <= 3 or tick_count[0] % 10 == 0:
            print(f"  [tick #{tick_count[0]:3d}] EUR/USD = {s['prices']['EUR/USD']:.5f}")
    
    def on_account(s):
        account_count[0] += 1
        print(f"  [account change #{account_count[0]}] cash=${s['account']['cash']:.2f}  positions={len(s['account']['positions'])}")
    
    def on_dom(s):
        dom_count[0] += 1
        if s['dom']['modal_visible']:
            print(f"  [DOM] 弹窗: {s['dom']['modal_title']}")
        elif s['dom']['toast']:
            print(f"  [DOM] toast: {s['dom']['toast']}")
    
    bot.run(on_tick, on_account, on_dom, interval=0.25, max_duration=30)
    
    print("\n" + "=" * 60)
    print("结果:")
    print(f"  收到 tick 事件: {tick_count[0]} 次")
    print(f"  收到账户变化: {account_count[0]} 次")
    print(f"  收到 DOM 变化: {dom_count[0]} 次")
    if prices_seen:
        print(f"  EUR/USD 价格范围: {min(prices_seen):.5f} → {max(prices_seen):.5f}")
    
    bot.close()


if __name__ == "__main__":
    demo()
