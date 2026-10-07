"""验证 bot 库: 现货买→合约开多→读价→平仓 全闭环"""
import time, json, sys
sys.path.insert(0, '/tmp/fxbot/bilinance')
from bot import BILBot
from lib import (spot_buy_market, spot_sell_market, fut_open, fut_close,
                 fut_close_pct, fut_positions, toast)

def main():
    bot = BILBot(headless=False)
    st = bot.state()
    print(f"初始: usdt=${st['usdt']:.2f}, 持仓={len(st['positions'])}")

    # 1. 现货市价买入 20U BTC
    spot_buy_market(bot, 20)
    st = bot.state()
    print(f"\n① 现货买 20U: usdt=${st['usdt']:.2f} balances={json.dumps(st['balances'])}")
    print(f"   toast={toast(bot)}")

    # 2. 现货市价卖出全部 BTC
    btc = st['balances'].get('BTC', 0)
    if btc > 0:
        spot_sell_market(bot, btc)
        st2 = bot.state()
        print(f"\n② 卖出 BTC: usdt=${st2['usdt']:.2f} (回来约{st2['usdt']-st['usdt']:+.2f}) balances={json.dumps(st2['balances'])}")

    # 3. 合约开多 5x 30U
    fut_open(bot, 'BTCUSDT', 'long', 5, 30)
    pos = fut_positions(bot)
    print(f"\n③ 开多 5x 30U: positions={json.dumps([{ 'id':p['id'], 'dir':p['dir'], 'margin':p['margin'], 'lev':p['lev'], 'entry':round(p['entry'],2) } for p in pos], ensure_ascii=False)}")
    print(f"   toast={toast(bot)}")

    # 4. 读价格
    time.sleep(2)
    p1 = bot.price()
    bid = bot.book_bid()
    print(f"\n④ 价格: #tkPrice={p1} 订单簿买一={bid}")

    # 5. 等几秒看强平价与标记价(UI), 然后平仓
    time.sleep(3)
    pos_ui = bot.frame.evaluate("""() => {
        const rows = [];
        document.querySelectorAll('[data-posrow]').forEach(r => {
            const txt = (r.textContent || '').trim().replace(/\\s+/g, ' ');
            const close = r.querySelector('[data-close]');
            rows.push({id: r.dataset.posrow, txt: txt.slice(0, 80), can_close: !!close});
        });
        return rows;
    }""")
    print(f"\n⑤ 持仓UI: {json.dumps(pos_ui, ensure_ascii=False)}")

    pid = pos[0]['id'] if pos else None
    if pid:
        # 部分平 50%
        fut_close_pct(bot, pid, 50)
        time.sleep(1.2)
        pos2 = fut_positions(bot)
        print(f"\n⑥ 平仓50%后: 持仓数={len(pos2)}")
        if pos2:
            print(f"   剩余 margin={pos2[0]['margin']:.2f} (50%平仓应剩约15)")
        # 全平剩余
        fut_close(bot, pos2[0]['id'])
        time.sleep(1.2)
        pos3 = fut_positions(bot)
        st3 = bot.state()
        print(f"\n⑦ 全平后: 持仓={len(pos3)} usdt=${st3['usdt']:.2f}")
        print(f"   closed={len(st3['closed'])} 最后一条={json.dumps(st3['closed'][-1] if st3['closed'] else None, ensure_ascii=False)}")
        print(f"   toast={toast(bot)}")

    bot.close()

if __name__ == '__main__':
    main()