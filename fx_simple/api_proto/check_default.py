"""验证: 不设任何参数, 默认直调 openPosition, 看仓位参数"""
import time, json, sys
sys.path.insert(0, '/tmp/fxbot')
from api_proto.bot_inject import FXBot

def main():
    bot = FXBot(headless=False)
    time.sleep(2)

    r = bot.frame.evaluate("""() => {
        const g = window.__game;
        const st = g.getState();
        const ret = g.openPosition('long');
        const newPos = st.positions[st.positions.length - 1];
        return {
            ret: ret ? {side: ret.side, entry: ret.entry, margin: ret.margin, leverage: ret.leverage, notional: ret.notional, fee: ret.fee} : null,
            n_positions: st.positions.length,
            cash: st.cash,
        };
    }""")
    print("默认直调开仓:", json.dumps(r, ensure_ascii=False))

    time.sleep(5)
    r2 = bot.frame.evaluate("""() => {
        const g = window.__game;
        const st = g.getState();
        const p = st.positions[st.positions.length - 1];
        const before = st.positions.length;
        g.closePosition(p.id, false);
        return {before, after: g.getState().positions.length};
    }""")
    print("直调平仓:", json.dumps(r2, ensure_ascii=False))

    bot.close()

if __name__ == '__main__':
    main()