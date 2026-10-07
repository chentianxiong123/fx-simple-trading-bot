"""验证 __game API: margin/leverage 生效, getSim 结构, closePosition 返回值"""
import time, json, sys
sys.path.insert(0, '/tmp/fxbot')
from api_proto.bot_inject import FXBot

def main():
    bot = FXBot(headless=False)
    
    # 1. 查看 __game API 和 getSim 结构
    r = bot.frame.evaluate("""() => {
        const g = window.__game;
        if (!g) return {error: 'no __game'};
        const sim = g.getSim()['EUR/USD'];
        const st = g.getState();
        return {
            api_keys: Object.keys(g),
            sim_keys: Object.keys(sim || {}),
            has_candles: !!sim?.candles,
            n_candles: sim?.candles?.length || 0,
            sim_price: sim?.price,
            mode: st.mode,
            cash: st.cash,
            margin_ui: st.margin,
            leverage_ui: st.leverage,
            positions: st.positions.length,
        };
    }""")
    print("API 检查:", json.dumps(r, ensure_ascii=False))
    
    # 2. 设置 margin/leverage 后开仓
    r2 = bot.frame.evaluate("""() => {
        const g = window.__game;
        const st = g.getState();
        st.margin = 500;
        st.leverage = 20;
        const before = st.positions.length;
        const ret = g.openPosition('long');
        const newPos = st.positions[st.positions.length - 1];
        return {
            before, after: st.positions.length, ret_keys: Object.keys(ret || {}),
            pos: newPos ? {side: newPos.side, entry: newPos.entry, margin: newPos.margin, leverage: newPos.leverage, notional: newPos.notional, fee: newPos.fee, id: newPos.id} : null,
        };
    }""")
    print("\n设置 500/20 后开仓:", json.dumps(r2, ensure_ascii=False))
    
    time.sleep(5)
    
    # 3. 平仓, 看 closePosition 返回什么
    r3 = bot.frame.evaluate("""() => {
        const g = window.__game;
        const st = g.getState();
        const p = st.positions[st.positions.length - 1];
        if (!p) return {error: 'no pos'};
        const before = st.positions.length;
        const ret = g.closePosition(p.id, false);
        return {before, after: g.getState().positions.length, ret};
    }""")
    print("\n平仓返回:", json.dumps(r3, ensure_ascii=False, default=str))
    
    bot.close()

if __name__ == '__main__':
    main()