"""
BILINANCE 模拟盘 bot 引擎
- 打开游戏, 定位 iframe
- 读状态: localStorage binance-sim-v1
- 读价格: #tkPrice 盘面价 / 行情表 / 订单簿
"""
import time, json
from playwright.sync_api import sync_playwright

SHELL_URL = "https://www.bilibili.com/toy/IjaLS8zTiK58TTNZ/index.html"
LS_KEY = 'binance-sim-v1'


class BILBot:
    def __init__(self, headless=False):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(
            headless=headless, channel="chrome", args=["--start-maximized"])
        self.page = self.browser.new_page()
        self.page.goto(SHELL_URL, wait_until="domcontentloaded", timeout=40000)

        # 找游戏 iframe
        self.frame = None
        for _ in range(30):
            time.sleep(0.5)
            for f in self.page.frames:
                try:
                    if f.evaluate(f"() => !!localStorage.getItem('{LS_KEY}')"):
                        self.frame = f
                        break
                except Exception:
                    pass
            if self.frame:
                break
        if not self.frame:
            raise RuntimeError("BILINANCE 未加载")

        # 关欢迎弹窗
        self.frame.evaluate("""() => {
            const s = document.getElementById('welcomeSkip');
            if (s && s.offsetParent !== null) s.click();
        }""")
        time.sleep(0.5)

    # ---------- 导航 ----------
    def nav(self, name):
        """name: 行情/交易/合约/资产/挑战"""
        self.frame.evaluate("""(n) => {
            const a = Array.from(document.querySelectorAll('.nav-links a'))
                .find(x => x.textContent.trim() === n);
            if (a) a.click();
        }""", name)
        time.sleep(0.8)

    def nav_sym(self, page, sym):
        """page: trade/futures; sym: BTCUSDT 等; 直接改 hash 路由"""
        self.frame.evaluate("""(args) => {
            location.hash = '#/' + args.page + '/' + args.sym;
        }""", {'page': page, 'sym': sym})
        time.sleep(1.0)

    # ---------- 读状态 ----------
    def state(self):
        return self.frame.evaluate("""() => {
            const s = JSON.parse(localStorage.getItem('binance-sim-v1'));
            return {
                usdt: s.usdt,
                balances: s.balances,
                open_orders: s.openOrders,
                positions: s.positions,
                closed: s.closedPositions,
                history: s.history,
                stats: s.stats,
                challenge: s.challenge,
                favorites: s.favorites,
                achievements: s.achievements,
                last_sym: s.lastSym,
            };
        }""")

    def price(self):
        """读盘面大字价 #tkPrice (当前页面货币对)"""
        r = self.frame.evaluate("""() => {
            const el = document.getElementById('tkPrice');
            if (!el) return null;
            const t = (el.textContent || '').trim().replace(/,/g, '');
            const v = parseFloat(t);
            return Number.isFinite(v) ? v : null;
        }""")
        return r

    def book_bid(self):
        """订单簿买一价"""
        r = self.frame.evaluate("""() => {
            const rows = document.querySelectorAll('[class*="book"] [class*="row"]');
            if (!rows.length) return null;
            const t = (rows[0].textContent || '').trim().split(/\\s+/)[0];
            return parseFloat(t) || null;
        }""")
        return r

    def all_prices(self):
        """行情表全部价格 {BTCUSDT: price}"""
        return self.frame.evaluate("""() => {
            const out = {};
            document.querySelectorAll('.mkt-table tbody tr').forEach(r => {
                const sym = r.dataset?.sym;
                const tds = r.querySelectorAll('td');
                if (sym && tds.length > 1) {
                    const v = parseFloat((tds[1].textContent || '').replace(/,/g, ''));
                    if (Number.isFinite(v)) out[sym] = v;
                }
            });
            return out;
        }""")

    def close(self):
        try:
            self.browser.close()
        except Exception:
            pass
        self.p.stop()
