/* ============ 账户系统:余额 / 订单 / 简化合约 / 成就 / 签到 ============ */
'use strict';

const FEE = 0.001;      // 现货手续费 0.1%
const FEE_FUT = 0.0005; // 合约手续费 0.05%
const MAINT_MARGIN = 0.05; // 维持保证金率(简化)
const START_USDT = 10000;

const ACH = [
  { id: 'first',    icon: '🎯', name: '初来乍到', desc: '完成第一笔交易' },
  { id: 'ten',      icon: '🔥', name: '小试牛刀', desc: '完成 10 笔交易' },
  { id: 'fifty',    icon: '⚡', name: '高频玩家', desc: '完成 50 笔交易' },
  { id: 'divers',   icon: '🧺', name: '多元配置', desc: '同时持有 4 种币' },
  { id: 'heavy',    icon: '🐋', name: '满仓一战', desc: '单笔名义投入超过总资产一半' },
  { id: 'lever',    icon: '🎢', name: '杠杆勇士', desc: '开一张 20x 及以上的合约' },
  { id: 'survivor', icon: '🛡️', name: '刀口舔血', desc: '单笔合约 ROE 超过 +50% 平仓' },
  { id: 'profit1k', icon: '💰', name: '落袋为安', desc: '合约累计盈利 1,000 USDT' },
  { id: 'loss500',  icon: '🧊', name: '交点学费', desc: '单笔亏损 500 USDT 以上' },
  { id: 'rich',     icon: '👑', name: '十万身家', desc: '总资产达到 100,000 USDT' },
  { id: 'grad',     icon: '🎓', name: '新手毕业', desc: '完成新手教程' },
];

const Store = {
  KEY: 'binance-sim-v1',
  data: null,

  default() {
    return {
      v: 1,
      usdt: START_USDT,
      balances: {},
      openOrders: [],      // {id,ts,sym,side,price,qty}
      history: [],         // 同上 + {status,doneTs}
      positions: [],       // {id,ts,sym,dir,entry,qty,margin,lev}
      closedPositions: [], // + {closeTs,closePrice,pnl,liq}
      favorites: { BTCUSDT: 1, ETHUSDT: 1 },
      achievements: {},
      stats: { trades: 0, wins: 0, losses: 0, realized: 0, fees: 0, volume: 0, dailyPnl: 0, day: todayStr() },
      settings: { sound: true, vibrate: true, theme: 'dark', swapColor: false },
      challenge: { date: '', remaining: 3, active: false, usdt: 10000, balances: {}, coin: 'DOGEUSDT', startedAt: 0, best: 0, runs: 0, history: [] },
      lastSym: { trade: 'BTCUSDT', futures: 'BTCUSDT' },
      lastMode: 'trade',
      lastSignin: '',
      welcomed: false,
      events: []           // {t,kind,text}
    };
  },

  load() {
    let d = null;
    try {
      const raw = localStorage.getItem(this.KEY);
      if (raw) d = JSON.parse(raw);
    } catch (e) { /* ignore */ }
    const def = this.default();
    this.data = Object.assign(def, d || {});
    this.data.stats = Object.assign(this.default().stats, this.data.stats);
    this.data.settings = Object.assign(this.default().settings, this.data.settings);
    this.data.challenge = Object.assign(this.default().challenge, this.data.challenge || {});
    this.data.lastSym = Object.assign({ trade: 'BTCUSDT', futures: 'BTCUSDT' }, this.data.lastSym || {});
    this.data.lastMode = this.data.lastMode === 'futures' ? 'futures' : 'trade';
    if (this.data.stats.day !== todayStr()) {
      this.data.stats.day = todayStr();
      this.data.stats.dailyPnl = 0;
    }
    /* 迁移:币安币 BNB 更名为哔哩币 BILI */
    const sd = this.data;
    if (sd.balances.BNB) {
      sd.balances.BILI = (sd.balances.BILI || 0) + sd.balances.BNB;
      delete sd.balances.BNB;
    }
    const fixSym = o => { if (o.sym === 'BNBUSDT') o.sym = 'BILIUSDT'; };
    sd.openOrders.forEach(fixSym);
    sd.history.forEach(fixSym);
    sd.positions.forEach(fixSym);
    sd.closedPositions.forEach(fixSym);
    if (sd.favorites.BNBUSDT) { delete sd.favorites.BNBUSDT; sd.favorites.BILIUSDT = 1; }
  },
  save() {
    try { localStorage.setItem(this.KEY, JSON.stringify(this.data)); } catch (e) { /* ignore */ }
  },
  reset() {
    const keep = { settings: this.data.settings, welcomed: this.data.welcomed };
    this.data = this.default();
    this.data.settings = keep.settings;
    this.data.welcomed = keep.welcomed;
    this.save();
  },

  pushEvent(kind, text) {
    this.data.events.unshift({ t: Date.now(), kind, text });
    if (this.data.events.length > 60) this.data.events.length = 60;
  },

  price(sym) { const st = Engine.get(sym); return st ? st.price : NaN; },

  /* 总权益 = 可用U + 挂单冻结 + 币折合 + 合约保证金+浮动盈亏 */
  equity() {
    let e = this.data.usdt;
    for (const o of this.data.openOrders) {
      if (o.side === 'buy') e += o.price * o.qty;
      else { const st = Engine.get(o.sym); if (st) e += o.qty * st.price; }
    }
    for (const [b, q] of Object.entries(this.data.balances)) {
      const st = Engine.get(b + 'USDT');
      if (st && q > 0) e += q * st.price;
    }
    for (const p of this.data.positions) e += p.margin + this.pnl(p);
    return e;
  },
  pnl(p) { return p.dir * (this.price(p.sym) - p.entry) * p.qty; },
  /* 维持保证金率随杠杆分层:杠杆越高越贴近开仓价强平(500x 时约 0.1% 距离) */
  effMM(lev) { return Math.min(MAINT_MARGIN, 0.5 / lev); },
  liqPrice(p) {
    const mm = this.effMM(p.lev);
    return p.dir > 0
      ? p.entry * (1 - 1 / p.lev + mm)
      : p.entry * (1 + 1 / p.lev - mm);
  },
  todayPnl() {
    let e = this.data.stats.dailyPnl;
    for (const p of this.data.positions) e += this.pnl(p);
    return e;
  },

  /* ---- 现货 ---- */
  buyMarket(sym, quoteUsdt) {
    const st = Engine.get(sym);
    let usdt = +quoteUsdt;
    if (!(usdt > 0)) return err('请输入买入金额');
    if (usdt < 1) return err('最小下单额 1 USDT');
    if (usdt > this.data.usdt) {
      // 输入额与可用额的舍入误差内,直接按可用全额买入(支持 100% 一键满仓)
      if (usdt - this.data.usdt <= 0.01) usdt = this.data.usdt;
      else return err('可用 USDT 不足');
    }
    const qty = usdt / st.price * (1 - FEE);
    this.data.usdt -= usdt;
    this.data.balances[st.cfg.base] = (this.data.balances[st.cfg.base] || 0) + qty;
    this.data.stats.trades++;
    this.data.stats.volume += usdt;
    this.data.stats.fees += usdt * FEE;
    this._afterTrade(sym, '买入', st.price, qty, usdt);
    return ok(`买入成功 ${fmt(qty, st.cfg.qprec)} ${st.cfg.base}`);
  },
  sellMarket(sym, baseQty) {
    const st = Engine.get(sym);
    let qty = +baseQty;
    if (!(qty > 0)) return err('请输入卖出数量');
    const have = this.data.balances[st.cfg.base] || 0;
    if (qty > have) {
      // 数量与可用量的舍入误差内,直接按可用全额卖出(支持 100% 一键清仓)
      if (qty - have <= Math.max(have * 1e-6, 1e-9)) qty = have;
      else return err(`可用 ${st.cfg.base} 不足`);
    }
    const gross = qty * st.price;
    if (gross < 1) return err('最小下单额 1 USDT');
    const net = gross * (1 - FEE);
    this.data.balances[st.cfg.base] = have - qty;
    if (this.data.balances[st.cfg.base] * st.price < 0.01) delete this.data.balances[st.cfg.base];
    this.data.usdt += net;
    this.data.stats.trades++;
    this.data.stats.volume += gross;
    this.data.stats.fees += gross * FEE;
    this._afterTrade(sym, '卖出', st.price, qty, gross);
    return ok(`卖出成功 +${fmt(net, 2)} USDT`);
  },
  placeLimit(sym, side, price, qty) {
    const st = Engine.get(sym);
    price = +price; qty = +qty;
    if (!(price > 0) || !(qty > 0)) return err('请输入价格和数量');
    const notional = price * qty;
    if (notional < 1) return err('最小下单额 1 USDT');
    if (price < st.price * 0.7 || price > st.price * 1.3) return err('委托价偏离市价过大(±30%)');
    if (side === 'buy') {
      if (notional > this.data.usdt) {
        if (notional - this.data.usdt <= 0.01) notional = this.data.usdt;
        else return err('可用 USDT 不足');
      }
      this.data.usdt -= notional;
    } else {
      const have = this.data.balances[st.cfg.base] || 0;
      if (qty > have) {
        if (qty - have <= Math.max(have * 1e-6, 1e-9)) qty = have;
        else return err(`可用 ${st.cfg.base} 不足`);
      }
      this.data.balances[st.cfg.base] = have - qty;
    }
    this.data.openOrders.push({ id: uid(), ts: Date.now(), sym, side, price, qty });
    this.save();
    return ok('挂单成功,成交后将收到通知');
  },
  cancelOrder(id) {
    const i = this.data.openOrders.findIndex(o => o.id === id);
    if (i < 0) return;
    const o = this.data.openOrders[i];
    const st = Engine.get(o.sym);
    if (o.side === 'buy') this.data.usdt += o.price * o.qty;
    else this.data.balances[st.cfg.base] = (this.data.balances[st.cfg.base] || 0) + o.qty;
    this.data.openOrders.splice(i, 1);
    o.status = '已撤销'; o.doneTs = Date.now();
    this.data.history.unshift(o);
    if (this.data.history.length > 120) this.data.history.length = 120;
    this.pushEvent('system', `已撤销 ${o.sym} ${o.side === 'buy' ? '买入' : '卖出'}委托 @ ${fmtAdaptive(o.price)}`);
    this.save();
  },
  checkOrders() {
    if (!this.data.openOrders.length) return;
    const fills = [];
    for (const o of this.data.openOrders) {
      const st = Engine.get(o.sym);
      if (o.side === 'buy' ? st.price <= o.price : st.price >= o.price) fills.push(o);
    }
    for (const o of fills) {
      this.data.openOrders = this.data.openOrders.filter(x => x.id !== o.id);
      const st = Engine.get(o.sym);
      this.data.stats.trades++;
      if (o.side === 'buy') {
        const qty = o.qty * (1 - FEE);
        this.data.balances[st.cfg.base] = (this.data.balances[st.cfg.base] || 0) + qty;
        this.data.stats.volume += o.price * o.qty;
        this.data.stats.fees += o.price * o.qty * FEE;
        this._afterTrade(o.sym, '限价买入', o.price, qty, o.price * o.qty);
      } else {
        const net = o.price * o.qty * (1 - FEE);
        this.data.usdt += net;
        this.data.stats.volume += o.price * o.qty;
        this.data.stats.fees += o.price * o.qty * FEE;
        this._afterTrade(o.sym, '限价卖出', o.price, o.qty, o.price * o.qty);
      }
      o.status = '已成交'; o.doneTs = Date.now();
      this.data.history.unshift(o);
      if (this.data.history.length > 120) this.data.history.length = 120;
    }
  },

  _afterTrade(sym, verb, price, qty, notional) {
    const st = Engine.get(sym);
    this.pushEvent('fill', `${verb} ${st.cfg.base} 成交 @ ${fmtAdaptive(price)}`);
    this.checkAchievements('trade', { notional });
    this.save();
    Sfx.fill(); vibrate(20);
  },

  /* ---- 简化合约 ---- */
  openPosition(sym, dir, marginUsdt, lev) {
    const st = Engine.get(sym);
    let margin = +marginUsdt;
    if (!(margin >= 5)) return err('最低保证金 5 USDT');
    if (margin > this.data.usdt) {
      // 输入与可用的舍入误差内,直接按可用全额开仓(支持 100% 一键满仓)
      if (margin - this.data.usdt <= 0.01) margin = this.data.usdt;
      else return err('可用 USDT 不足');
    }
    if (this.data.positions.length >= 8) return err('最多同时持有 8 个仓位');
    const notional = margin * lev;
    const fee = notional * FEE_FUT;
    const qty = (notional - fee) / st.price;
    this.data.usdt -= margin;
    this.data.positions.push({ id: uid(), ts: Date.now(), sym, dir, entry: st.price, qty, margin, lev });
    this.data.stats.volume += notional;
    this.data.stats.fees += fee;
    this.pushEvent('fut', `开${dir > 0 ? '多' : '空'} ${st.cfg.base} ${lev}x @ ${fmtAdaptive(st.price)}`);
    this.checkAchievements('open', { notional, lev });
    this.save();
    Sfx.fill(); vibrate(20);
    return ok(`开${dir > 0 ? '多' : '空'}成功 ${lev}x`);
  },
  /* 平仓:frac 为平仓比例(0,1];剩余部分保留仓位 */
  closePosition(id, frac = 1) {
    const i = this.data.positions.findIndex(p => p.id === id);
    if (i < 0) return err('仓位不存在');
    const p = this.data.positions[i];
    frac = clamp(+frac || 1, 0.01, 1);
    if (p.margin * (1 - frac) < 1) frac = 1; // 剩余保证金不足 1 U 时一键全平
    const st = Engine.get(p.sym);
    const closeQty = p.qty * frac;
    const closeMargin = p.margin * frac;
    const pnlRaw = this.pnl(p) * frac;
    const realized = Math.max(pnlRaw, -closeMargin);
    this.data.usdt += closeMargin + realized;
    if (frac >= 1) this.data.positions.splice(i, 1);
    else { p.qty -= closeQty; p.margin -= closeMargin; }
    this.data.stats.realized += realized;
    this.data.stats.dailyPnl += realized;
    if (realized >= 0) this.data.stats.wins++; else this.data.stats.losses++;
    this.data.closedPositions.unshift({ ...p, qty: closeQty, margin: closeMargin, closeTs: Date.now(), closePrice: st.price, pnl: realized, frac, liq: false });
    if (this.data.closedPositions.length > 120) this.data.closedPositions.length = 120;
    this.pushEvent(realized >= 0 ? 'fill' : 'fut', `平仓 ${st.cfg.base}${frac < 1 ? `(${Math.round(frac * 100)}%)` : ''} ${realized >= 0 ? '盈利' : '亏损'} ${fmt(Math.abs(realized), 2)} USDT`);
    this.checkAchievements('close', { roe: realized / closeMargin, realized });
    this.save();
    Sfx.fill(); vibrate(20);
    return ok(`平仓成功 ${realized >= 0 ? '盈利' : '亏损'} ${fmt(Math.abs(realized), 2)} USDT`);
  },
  checkLiquidations() {
    for (const p of this.data.positions.slice()) {
      const thresh = 1 - this.effMM(p.lev) * p.lev;
      if (this.pnl(p) <= -p.margin * thresh) {
        this.data.positions = this.data.positions.filter(x => x.id !== p.id);
        this.data.stats.realized -= p.margin;
        this.data.stats.dailyPnl -= p.margin;
        this.data.stats.losses++;
        this.data.closedPositions.unshift({ ...p, closeTs: Date.now(), closePrice: this.price(p.sym), pnl: -p.margin, liq: true });
        if (this.data.closedPositions.length > 120) this.data.closedPositions.length = 120;
        this.pushEvent('fut', `⚠️ ${Engine.get(p.sym).cfg.base} 仓位爆仓,保证金 ${fmt(p.margin, 2)} USDT 全部损失`);
        this.save();
        Sfx.error(); vibrate([60, 40, 60]);
        if (UI.liquidated) UI.liquidated(p);
      }
    }
  },

  /* ---- 签到 ---- */
  signin() {
    const today = todayStr();
    if (this.data.lastSignin === today) return err('今天已经签到过啦');
    this.data.lastSignin = today;
    this.data.usdt += 1000;
    this.pushEvent('system', '每日签到 +1,000 USDT');
    this.save();
    Sfx.achievement();
    return ok('签到成功 +1,000 USDT');
  },

  /* ---- 成就 ---- */
  award(id) {
    const A = this.data.achievements;
    if (A[id]) return;
    A[id] = Date.now();
    const a = ACH.find(x => x.id === id);
    if (a) {
      if (UI.toast) UI.toast(`🏆 成就解锁「${a.name}」${a.icon}`, 'gold');
      Sfx.achievement();
      this.pushEvent('ach', `解锁成就「${a.name}」`);
    }
    this.save();
  },
  checkAchievements(kind, extra = {}) {
    const d = this.data;
    const unlock = (id) => this.award(id);
    if (d.stats.trades >= 1) unlock('first');
    if (d.stats.trades >= 10) unlock('ten');
    if (d.stats.trades >= 50) unlock('fifty');
    if (Object.values(d.balances).filter(q => q > 1e-12).length >= 4) unlock('divers');
    if (kind === 'trade' && extra.notional > this.equity() * 0.5) unlock('heavy');
    if (kind === 'open') {
      if (extra.notional > this.equity() * 0.5) unlock('heavy');
      if (extra.lev >= 20) unlock('lever');
    }
    if (kind === 'close') {
      if (extra.roe >= 0.5) unlock('survivor');
      if (extra.realized <= -500) unlock('loss500');
    }
    if (kind === 'liq' && extra.realized <= -500) unlock('loss500');
    if (d.stats.realized >= 1000) unlock('profit1k');
    if (this.equity() >= 100000) unlock('rich');
  }
};
