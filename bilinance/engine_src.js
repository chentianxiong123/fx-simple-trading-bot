/* ============ 行情模拟引擎 ============
 * 每个币种:几何随机游走 + 趋势状态机 + 均值回归 + 突发新闻冲击。
 * K线按时间桶聚合,盘口/成交流围绕最新价合成。所有数据仅存在于内存。 */
'use strict';

const TICK_MS = 400;
const TF_LIST = [['1s', 1, '1秒'], ['5s', 5, '5秒'], ['15s', 15, '15秒'], ['1m', 60, '1分'], ['5m', 300, '5分']];

/* 币种图标:真实币按官方标志风格绘制,虚构币用与名称相关的图案 */
const LOGOS = {
  btc: '<circle cx="16" cy="16" r="16" fill="#F7931A"/><g fill="#fff"><text x="16" y="21.2" text-anchor="middle" font-family="Arial,sans-serif" font-size="15" font-weight="800">B</text><rect x="13.4" y="6.6" width="1.8" height="4.6" rx="0.8"/><rect x="16.8" y="6.6" width="1.8" height="4.6" rx="0.8"/><rect x="13.4" y="20.8" width="1.8" height="4.6" rx="0.8"/><rect x="16.8" y="20.8" width="1.8" height="4.6" rx="0.8"/></g>',
  eth: '<circle cx="16" cy="16" r="16" fill="#627EEA"/><g fill="#fff"><polygon points="16,5 16,13.6 9.7,16.4" opacity=".65"/><polygon points="16,5 16,13.6 22.3,16.4"/><polygon points="16,17.8 16,27 9.7,17.6" opacity=".65"/><polygon points="16,27 16,17.8 22.3,17.6" opacity=".9"/><polygon points="9.7,17.6 16,14.8 16,17.8" opacity=".25"/><polygon points="16,14.8 22.3,17.6 16,17.8" opacity=".45"/></g>',
  bili: '<circle cx="16" cy="16" r="16" fill="#FB7299"/><g stroke="#fff" stroke-width="2" stroke-linecap="round" fill="none"><line x1="10.5" y1="6.5" x2="13.5" y2="10.5"/><line x1="21.5" y1="6.5" x2="18.5" y2="10.5"/><rect x="7.5" y="11.5" width="17" height="12.5" rx="3"/><line x1="12.8" y1="15.6" x2="12.8" y2="19.6"/><line x1="19.2" y1="15.6" x2="19.2" y2="19.6"/></g>',
  sol: '<circle cx="16" cy="16" r="16" fill="#141416"/><defs><linearGradient id="solG" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#00FFA3"/><stop offset="1" stop-color="#DC1FFF"/></linearGradient></defs><g fill="url(#solG)"><path d="M11.2 9.3h9.6c.5 0 .9.5.6 1l-1.6 1.7c-.2.2-.4.3-.7.3H9.6c-.5 0-.9-.5-.6-1l1.6-1.7c.1-.2.4-.3.6-.3z"/><path d="M20.8 14.3h-9.6c-.5 0-.9.5-.6 1l1.6 1.7c.2.2.4.3.7.3h9.5c.5 0 .9-.5.6-1l-1.6-1.7c-.1-.2-.4-.3-.6-.3z"/><path d="M11.2 19.3h9.6c.5 0 .9.5.6 1l-1.6 1.7c-.2.2-.4.3-.7.3H9.6c-.5 0-.9-.5-.6-1l1.6-1.7c.1-.2.4-.3.6-.3z"/></g>',
  xrp: '<circle cx="16" cy="16" r="16" fill="#23292F"/><path fill="#fff" d="M10.6 9h3.2l2.2 2.7L18.2 9h3.2l-3.9 4.8c-.7.9-.7 1.5 0 2.4L21.4 21h-3.2l-2.2-2.7L13.8 21h-3.2l3.9-4.8c.7-.9.7-1.5 0-2.4z"/>',
  doge: '<circle cx="16" cy="16" r="16" fill="#C2A633"/><text x="17" y="21.3" text-anchor="middle" font-family="Arial,sans-serif" font-size="15" font-weight="800" fill="#fff">D</text><rect x="9.5" y="14.9" width="9.5" height="2.1" rx="0.5" fill="#fff"/>',
  ada: '<circle cx="16" cy="16" r="16" fill="#0D3C8E"/><g fill="#fff"><circle cx="16" cy="16" r="2.2"/><circle cx="16" cy="8.6" r="1.4"/><circle cx="16" cy="23.4" r="1.4"/><circle cx="9.5" cy="12.3" r="1.4"/><circle cx="22.5" cy="12.3" r="1.4"/><circle cx="9.5" cy="19.7" r="1.4"/><circle cx="22.5" cy="19.7" r="1.4"/><circle cx="10.9" cy="8" r="0.9"/><circle cx="21.1" cy="8" r="0.9"/><circle cx="10.9" cy="24" r="0.9"/><circle cx="21.1" cy="24" r="0.9"/></g>',
  link: '<circle cx="16" cy="16" r="16" fill="#2A5ADA"/><path d="M16 7.5l7.4 4.3v8.4L16 24.5l-7.4-4.3v-8.4z" fill="none" stroke="#fff" stroke-width="2.6" stroke-linejoin="round"/>',
  wif: '<circle cx="16" cy="16" r="16" fill="#D9A066"/><path d="M8.5 15.5c0-4.4 3.4-7.5 7.5-7.5s7.5 3.1 7.5 7.5v1.2h-15z" fill="#E4573D"/><rect x="8.5" y="15.5" width="15" height="2.6" rx="1.3" fill="#C23F28"/><circle cx="16" cy="7.6" r="2" fill="#E4573D"/><circle cx="12.4" cy="21.8" r="1.3" fill="#3B2B20"/><circle cx="19.6" cy="21.8" r="1.3" fill="#3B2B20"/><path d="M13.5 25.4c1.6 1.2 3.4 1.2 5 0" stroke="#3B2B20" stroke-width="1.3" fill="none" stroke-linecap="round"/>',
  pepe: '<circle cx="16" cy="16" r="16" fill="#3C9E4A"/><circle cx="11.8" cy="12" r="3.1" fill="#7ACB63"/><circle cx="20.2" cy="12" r="3.1" fill="#7ACB63"/><circle cx="11.8" cy="12.4" r="1.2" fill="#173A1E"/><circle cx="20.2" cy="12.4" r="1.2" fill="#173A1E"/><path d="M8 19.5c2.8 2.2 5.3 3 8 3s5.2-.8 8-3" stroke="#173A1E" stroke-width="1.6" fill="none" stroke-linecap="round"/>',
  nailong: '<circle cx="16" cy="16" r="16" fill="#FFD84D"/><path d="M10.6 9c.3-1.9 1.4-3.2 2.9-3.7l.7 3.2z" fill="#F5A623"/><path d="M21.4 9c-.3-1.9-1.4-3.2-2.9-3.7l-.7 3.2z" fill="#F5A623"/><circle cx="12" cy="15" r="3.3" fill="#fff"/><circle cx="20" cy="15" r="3.3" fill="#fff"/><circle cx="12.4" cy="15.5" r="1.5" fill="#2B2B2B"/><circle cx="19.6" cy="15.5" r="1.5" fill="#2B2B2B"/><path d="M12.3 21.8c2.2 1.9 5.2 1.9 7.4 0" stroke="#C98A00" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
  kurumi: '<circle cx="16" cy="16" r="16" fill="#8E6FD8"/><circle cx="8.8" cy="9.8" r="3.4" fill="#5E49B8"/><circle cx="23.2" cy="9.8" r="3.4" fill="#5E49B8"/><ellipse cx="16" cy="18.2" rx="7.5" ry="7" fill="#FFE8D6"/><path d="M8.8 17.2c.4-4.8 3.4-7.6 7.2-7.6s6.8 2.8 7.2 7.6c-2.2-2-4.6-3-7.2-3s-5 1-7.2 3z" fill="#5E49B8"/><circle cx="13" cy="18.8" r="1.2" fill="#333"/><circle cx="19" cy="18.8" r="1.2" fill="#333"/><circle cx="10.8" cy="20.9" r="1.1" fill="#FF9EAE" opacity=".85"/><circle cx="21.2" cy="20.9" r="1.1" fill="#FF9EAE" opacity=".85"/><path d="M14.8 22.6c.8.6 1.6.6 2.4 0" stroke="#C46A5A" stroke-width="1" fill="none" stroke-linecap="round"/>',
  hafu: '<circle cx="16" cy="16" r="16" fill="#FF7A45"/><path d="M10.3 13.4q2.2-2.4 4.4 0" stroke="#4A1D00" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M17.3 13.4q2.2-2.4 4.4 0" stroke="#4A1D00" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M11 17.3h10c-.4 4-2.5 6.1-5 6.1s-4.6-2.1-5-6.1z" fill="#5C2400"/><path d="M13.2 17.3h5.6c-.2 1.2-.8 1.9-1.6 1.9h-2.4c-.8 0-1.4-.7-1.6-1.9z" fill="#fff"/>',
  usdt: '<circle cx="16" cy="16" r="16" fill="#26A17B"/><g fill="#fff"><text x="16" y="19.3" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" font-weight="800">T</text><rect x="9.5" y="19.8" width="13" height="1.8" rx="0.6"/><rect x="9.5" y="22.4" width="13" height="1.8" rx="0.6"/></g>'
};
function logoSvg(name) {
  return `<svg viewBox="0 0 32 32" width="100%" height="100%">${LOGOS[name]}</svg>`;
}

const SYMBOLS = [
  { s: 'BTCUSDT',  base: 'BTC',  name: '比特币', p0: 68250,      vol: 1.0,  prec: 2, qprec: 4, color: '#F7931A', logo: 'btc' },
  { s: 'ETHUSDT',  base: 'ETH',  name: '以太坊', p0: 3512,       vol: 1.25, prec: 2, qprec: 3, color: '#627EEA', logo: 'eth' },
  { s: 'BILIUSDT', base: 'BILI', name: '哔哩币', p0: 612.4,      vol: 1.0,  prec: 2, qprec: 2, color: '#FB7299', logo: 'bili' },
  { s: 'SOLUSDT',  base: 'SOL',  name: 'Solana', p0: 158.7,      vol: 1.9,  prec: 2, qprec: 2, color: '#14F195', logo: 'sol' },
  { s: 'XRPUSDT',  base: 'XRP',  name: '瑞波币', p0: 0.5243,     vol: 1.6,  prec: 4, qprec: 1, color: '#23292F', logo: 'xrp' },
  { s: 'DOGEUSDT', base: 'DOGE', name: '狗狗币', p0: 0.1248,     vol: 2.4,  prec: 5, qprec: 0, color: '#C2A633', logo: 'doge' },
  { s: 'ADAUSDT',  base: 'ADA',  name: '艾达币', p0: 0.4521,     vol: 1.7,  prec: 4, qprec: 0, color: '#0D3C8E', logo: 'ada' },
  { s: 'LINKUSDT', base: 'LINK', name: '链环',   p0: 14.52,      vol: 1.9,  prec: 3, qprec: 1, color: '#2A5ADA', logo: 'link' },
  { s: 'NAILONGUSDT', base: 'NAILONG', name: '奶龙币', p0: 0.0852,  vol: 3.6, prec: 5, qprec: 0, color: '#FFD84D', logo: 'nailong', img: './img/nailong.png' },
  { s: 'KURUMIUSDT',  base: 'KURUMI',  name: '久留美', p0: 1.374,   vol: 3.8, prec: 4, qprec: 0, color: '#8E6FD8', logo: 'kurumi', img: './img/kurumi.webp' },
  { s: 'HAFUUSDT',    base: 'HAFU',    name: '哈夫币', p0: 0.4218,  vol: 4.0, prec: 4, qprec: 0, color: '#FF7A45', logo: 'hafu', img: './img/hafu.webp' },
  { s: 'WIFUSDT',  base: 'WIF',  name: '狗戴帽', p0: 1.864,      vol: 3.0,  prec: 4, qprec: 0, color: '#D9A066', logo: 'wif' },
  { s: 'PEPEUSDT', base: 'PEPE', name: '佩佩',   p0: 0.00000852, vol: 3.4,  prec: 8, qprec: 0, color: '#3C9E4A', logo: 'pepe' },
];

const NEWS_TPL = [
  { t: '{n} 现货ETF获批,机构资金疯狂涌入', d: 1 },
  { t: '马斯克发推:考虑用 {n} 支付火星船票', d: 1 },
  { t: '{n} 主网重磅升级,性能提升十倍', d: 1 },
  { t: '小国宣布将 {n} 纳入国家储备', d: 1 },
  { t: '减半临近,{n} 供应冲击预期升温', d: 1 },
  { t: '{n} 生态大会官宣重磅合作', d: 1 },
  { t: '做空机构发布 {n} 做空报告', d: -1 },
  { t: '巨鲸地址凌晨抛售 {n},市场恐慌蔓延', d: -1 },
  { t: '监管风声收紧,{n} 应声跳水', d: -1 },
  { t: '某大型矿场抛售 {n} 支付电费', d: -1 },
  { t: '黑客攻击事件引发抛压,{n} 短线急跌', d: -1 },
];

class SymState {
  constructor(cfg) {
    this.cfg = cfg;
    this.price = cfg.p0 * rand(0.97, 1.03);
    this.prevPrice = this.price;
    this.open24 = this.price / (1 + rand(-0.06, 0.06));
    this.high24 = Math.max(this.price, this.open24);
    this.low24 = Math.min(this.price, this.open24);
    this.volPerSec = 6e4 / cfg.p0;               // 基础币每秒成交(用于量感)
    this.vol24 = this.volPerSec * cfg.p0 * 86400 * rand(0.3, 0.8); // USDT计
    this.trend = 0; this.trendLeft = 0;
    this.shockDrift = 0; this.shockTicks = 0;
    this.trades = [];                            // {t,p,q,side}
    this.bids = []; this.asks = [];
    this.candles = {};
    this._backfill();
    this._genBook(true);
  }
  get sigma() { return this.cfg.vol * 5.2e-4; }

  /* 从 p0 向前模拟一段历史,再整体缩放使最后一根收盘 == 当前价 */
  _backfill() {
    const n = 360, tickSec = TICK_MS / 1000;
    const nowSec = Math.floor(Date.now() / 1000);
    for (const [tf, sec] of TF_LIST) {
      const sc = this.sigma * Math.sqrt(sec / tickSec);
      let c = this.cfg.p0;
      const arr = [];
      const t0 = Math.floor(nowSec / sec) * sec - (n - 1) * sec;
      for (let i = 0; i < n; i++) {
        const o = c;
        c = o * Math.exp(randn() * sc * 0.9);
        const h = Math.max(o, c) * Math.exp(Math.abs(randn()) * sc * 0.35);
        const l = Math.min(o, c) * Math.exp(-Math.abs(randn()) * sc * 0.35);
        const v = this.volPerSec * sec * Math.exp(randn() * 0.6);
        arr.push({ t: (t0 + i * sec) * 1000, o, h, l, c, v });
      }
      const k = this.price / arr[n - 1].c;
      for (const cd of arr) { cd.o *= k; cd.h *= k; cd.l *= k; cd.c *= k; }
      const last = arr[n - 1];
      last.c = this.price;
      last.h = Math.max(last.h, this.price);
      last.l = Math.min(last.l, this.price);
      this.candles[tf] = arr;
    }
  }

  /* 盘口:围绕最新价生成 16 档,新旧尺寸平滑混合避免跳变 */
  _genBook(init) {
    const step = Math.max(this.price * 3e-5, Math.pow(10, -this.cfg.prec));
    const n = 16;
    if (this.bids.length !== n) {
      this.bids = []; this.asks = [];
      for (let i = 0; i < n; i++) { this.bids.push({ p: 0, q: 0 }); this.asks.push({ p: 0, q: 0 }); }
    }
    for (let i = 0; i < n; i++) {
      const b = this.bids[i], a = this.asks[i];
      b.p = this.price - (i + 1) * step * (1 + i * 0.2);
      a.p = this.price + (i + 1) * step * (1 + i * 0.2);
      const target = this.volPerSec * 2.5 * (1 + i * 0.5) * Math.exp(randn() * 0.7);
      if (init) { b.q = target; a.q = target; }
      else {
        b.q = b.q * 0.5 + target * 0.5 * rand(0.4, 1.6);
        a.q = a.q * 0.5 + target * 0.5 * rand(0.4, 1.6);
      }
    }
  }

  tick(now) {
    const cfg = this.cfg;
    this.prevPrice = this.price;
    // 趋势状态机
    if (--this.trendLeft <= 0) {
      this.trend = [-1, -0.5, 0, 0.5, 1][Math.floor(Math.random() * 5)];
      this.trendLeft = Math.round(rand(50, 220));
    }
    let drift = this.trend * cfg.vol * 1.6e-4;
    if (this.shockTicks > 0) { drift += this.shockDrift; this.shockTicks--; }
    drift += -8e-5 * Math.log(this.price / cfg.p0); // 温和均值回归
    this.price *= Math.exp(drift + this.sigma * randn());
    this.price = Math.max(this.price, cfg.p0 * 0.01);

    this.high24 = Math.max(this.high24, this.price);
    this.low24 = Math.min(this.low24, this.price);

    // 成交流
    const k = Math.floor(rand(0, 3.4));
    const buyBias = this.price >= this.prevPrice ? 0.62 : 0.38;
    for (let i = 0; i < k; i++) {
      const p = this.price * (1 + rand(-1.2e-4, 1.2e-4));
      const q = this.volPerSec * (TICK_MS / 1000) / Math.max(k, 1) * Math.exp(randn() * 0.8) * rand(0.3, 1.7);
      if (q > 0) this.trades.unshift({ t: now, p, q, side: Math.random() < buyBias ? 'buy' : 'sell' });
    }
    if (this.trades.length > 40) this.trades.length = 40;

    // K线聚合
    for (const [tf, sec] of TF_LIST) {
      const arr = this.candles[tf];
      const bucket = Math.floor(now / (sec * 1000)) * sec * 1000;
      let last = arr[arr.length - 1];
      if (bucket > last.t) {
        last = { t: bucket, o: this.price, h: this.price, l: this.price, c: this.price, v: 0 };
        arr.push(last);
        if (arr.length > 420) arr.shift();
      }
      last.c = this.price;
      if (this.price > last.h) last.h = this.price;
      if (this.price < last.l) last.l = this.price;
      last.v += this.volPerSec * (TICK_MS / 1000) * rand(0.6, 1.4);
    }
    this._genBook(false);
  }
  chg24() { return this.price / this.open24 - 1; }
}

const Engine = {
  syms: new Map(),
  lastNews: null,
  init() { for (const cfg of SYMBOLS) this.syms.set(cfg.s, new SymState(cfg)); },
  get(s) { return this.syms.get(s); },
  list() { return SYMBOLS.map(c => this.syms.get(c.s)); },
  tick() {
    const now = Date.now();
    if (Math.random() < 0.0045) this._fireNews(now); // 平均约 90 秒一条
    for (const st of this.syms.values()) st.tick(now);
  },
  _fireNews(now) {
    const sts = this.list();
    const st = sts[Math.floor(Math.random() * sts.length)];
    const tpl = NEWS_TPL[Math.floor(Math.random() * NEWS_TPL.length)];
    const mag = rand(0.05, 0.14);
    st.shockDrift = (mag / 8) * tpl.d;
    st.shockTicks = 8;
    this.lastNews = {
      t: now,
      text: tpl.t.replace('{n}', st.cfg.base + '(' + st.cfg.name + ')'),
      sym: st.cfg.s,
      dir: tpl.d,
      mag
    };
  }
};
