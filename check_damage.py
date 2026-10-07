"""只读检查:游戏存档是否有污染(null/异常值), 以及 UI 显示"""
import time, json, sys
sys.path.insert(0, '/tmp/fxbot')
from bot import FXBot

def find_bad(obj, path=''):
    bad = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            bad += find_bad(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad += find_bad(v, f"{path}[{i}]")
    elif obj is None:
        bad.append(f"{path}=null")
    elif isinstance(obj, float) and (obj != obj or obj in (float('inf'), float('-inf'))):
        bad.append(f"{path}={obj}")
    return bad

def main():
    bot = FXBot(headless=False)
    time.sleep(3)
    s = bot.state()
    
    print("=== 存档检查 ===")
    print(f"mode: {s['mode']}")
    print(f"cash: {s['account']['cash']}")
    print(f"positions: {len(s['account']['positions'])}")
    print(f"margin(UI): {s['account']['margin']}, leverage: {s['account']['leverage']}")
    print(f"debt: {s['account']['debt']}")
    print(f"fees_paid: {s['account']['fees_paid']}")
    
    # 深度检查异常值
    bad = find_bad(s['account'])
    print(f"\n异常值: {len(bad)} 个")
    for b in bad[:20]:
        print(f"  ⚠ {b}")
    
    # UI 显示
    print(f"\n=== UI ===")
    print(bot.frame.evaluate("() => document.body?.innerText?.slice(0, 300) || ''").replace('\\n', '\n'))
    bot.close()

if __name__ == '__main__':
    main()