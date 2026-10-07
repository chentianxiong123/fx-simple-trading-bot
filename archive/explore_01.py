"""
Phase 1: 探索页面 DOM + JS 环境，看能拿到什么
- 加载 FX 简单!
- 探测 state/sim/PAIRS 是否全局可访问
- 探测 tickSim 是不是 setInterval 调用
- 尝试拦截 fetch 到 Frankfurter 的调用（虽然 sim 模式不用）
"""
import asyncio
import json
from playwright.async_api import async_playwright

URL = "https://www.bilibili.com/toy/fx-simple/index.html"

JS_PROBE = """
() => {
  const iframe = document.querySelector('iframe');
  const r = {top: {}, iframe: null};
  // 顶层探测
  for (const k of ['state','sim','PAIRS','BATTLES','tickSim','openPosition','closePosition','account','riskRatio','__TOY_META__','__TOY_PERF__','toy','reporterPb']) {
    try { r.top[k] = typeof window[k]; } catch(e) { r.top[k] = 'err:' + e.message; }
  }
  if (iframe) {
    try {
      const w = iframe.contentWindow;
      r.iframe = {src: iframe.src};
      for (const k of ['state','sim','challengeSim','PAIRS','BATTLES','tickSim','openPosition','closePosition','account','riskRatio','positionPnl','fetchFrankfurter','tradeFee','LOAN_MAX']) {
        try { r.iframe[k] = typeof w[k]; } catch(e) { r.iframe[k] = 'err:' + e.message; }
      }
    } catch(e) { r.iframe = {error: e.message}; }
  }
  return r;
}
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        # 拦截所有网络请求，看清前端调用了什么
        all_reqs = []
        page.on("request", lambda req: all_reqs.append((req.method, req.url)) if 'api.frankfurter' in req.url or 'toy' in req.url or 'bilibilitoy' in req.url else None)

        await page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        # 等 iframe 加载
        await page.wait_for_timeout(4000)

        probe = await page.evaluate(JS_PROBE)
        print("=== JS 全局探测 ===")
        print(json.dumps(probe, indent=2, ensure_ascii=False))

        print("\n=== 网络请求 (前 20) ===")
        for method, url in all_reqs[:20]:
            print(f"  {method} {url[:120]}")

        # 拿 iframe URL，直接加载 iframe 内容绕过 sandbox
        iframe = await page.query_selector("iframe")
        if iframe:
            src = await iframe.get_attribute("src")
            print(f"\n=== iframe src ===")
            print(src)

        await browser.close()

asyncio.run(main())
