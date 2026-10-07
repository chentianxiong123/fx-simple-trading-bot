"""调试 all_prices: 打印行情表 DOM 结构"""
import time, json, sys
sys.path.insert(0, '/tmp/fxbot/bilinance')
from bot import BILBot

def main():
    bot = BILBot(headless=False)
    bot.nav('行情')
    time.sleep(2)

    # raw HTML of mkt-table
    html = bot.frame.evaluate("""() => {
        const t = document.querySelector('.mkt-table');
        if (!t) return 'no .mkt-table';
        return t.outerHTML.slice(0, 1200);
    }""")
    print("=== .mkt-table HTML ===")
    print(html)

    # 其他可能的价格容器
    prices = bot.all_prices()
    print("\n=== all_prices() ===")
    print(json.dumps(prices, ensure_ascii=False))

    # 直接看页面顶部价格区
    txt = bot.frame.evaluate("() => document.body.innerText.slice(0, 400)")
    print("\n=== 页面文本 ===")
    print(txt)

    # 再采样 10 秒看价格动没动
    p1 = bot.all_prices()
    time.sleep(10)
    p2 = bot.all_prices()
    print("\n=== 10秒后对比 ===")
    if p1 and p2:
        for k in list(p1.keys())[:5]:
            print(f"  {k}: {p1[k]} -> {p2[k]}")
    bot.close()

if __name__ == '__main__':
    main()