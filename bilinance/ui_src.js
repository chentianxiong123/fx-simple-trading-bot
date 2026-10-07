/* ============ UI:页面渲染与交互 ============ */
'use strict';

const ICONS = {
  search: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>',
  star: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3l2.7 5.8 6.3.7-4.7 4.3 1.3 6.2L12 16.9 6.4 20l1.3-6.2L3 9.5l6.3-.7z"/></svg>',
  starFill: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" stroke="none"><path d="M12 3l2.7 5.8 6.3.7-4.7 4.3 1.3 6.2L12 16.9 6.4 20l1.3-6.2L3 9.5l6.3-.7z"/></svg>',
  chevD: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>',
  gift: '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#FCD535" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-8M12 8v13"/><path d="M12 8s-4.5.2-5.5-2C5.7 4.2 7.5 3 8.8 3 11 3 12 8 12 8zm0 0s4.5.2 5.5-2C18.3 4.2 16.5 3 15.2 3 13 3 12 8 12 8z"/></svg>',
  sound: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5L6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/></svg>',
  vib: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="3" width="8" height="18" rx="2"/><path d="M4 9v6M20 9v6"/></svg>',
  reset: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 2.6-6.3"/><path d="M3 4v5h5"/></svg>'
};

function coinIcon(cfg, size = 28) {
  let body;
  if (cfg.img) body = `<img class="coin-img" src="${cfg.img}" alt="${cfg.base || ''}">`;
  else if (cfg.logo) body = logoSvg(cfg.logo);
  else body = `<svg viewBox="0 0 32 32" width="100%" height="100%"><circle cx="16" cy="16" r="16" fill="${cfg.color || '#848E9C'}"/></svg>`;
  return `<span class="coin-icon" style="width:${size}px;height:${size}px">${body}</span>`;
}
function sparkSVG(closes, w = 84, h = 30) {
  if (!closes || closes.length < 2) return '';
  let min = Infinity, max = -Infinity;
  for (const c of closes) { if (c < min) min = c; if (c > max) max = c; }
  const rng = max - min || max * 0.001 || 1;
  const pts = closes.map((c, i) =>
    `${(i / (closes.length - 1) * (w - 2) + 1).toFixed(1)},${(h - 3 - (c - min) / rng * (h - 6)).toFixed(1)}`
  ).join(' ');
  const col = closes[closes.length - 1] >= closes[0] ? C.green : C.red;
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><polyline fill="none" stroke="${col}" stroke-width="1.5" points="${pts}"/></svg>`;
}
function emptyBox(txt) { return `<div class="empty">${txt}</div>`; }

const UI = {
  lastSeenT: 0,

  /* ---------- 通用组件 ---------- */
  toast(msg, type = 'info') {
    const box = $('#toasts'); if (!box) return;
    const el = document.createElement('div');
    el.className = 'toast ' + type;
    el.innerHTML = msg;
    box.appendChild(el);
    while (box.children.length > 4) box.firstChild.remove();
    setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 350); }, 2800);
  },
  modal(html, opts = {}) {
    const root = $('#modal-root');
    root.innerHTML = `<div class="modal-mask"><div class="modal ${opts.cls || ''}">${html}</div></div>`;
    const mask = root.firstElementChild;
    if (opts.dismissible !== false) {
      mask.addEventListener('click', e => { if (e.target === mask) UI.closeModal(); });
    }
    return mask;
  },
  closeModal() { $('#modal-root').innerHTML = ''; },
  confirm({ title, body, okText = '确定', danger = false, onOk }) {
    const mask = UI.modal(`
      <h3 class="${danger ? 'danger' : ''}">${title}</h3>
      <div class="m-body">${body}</div>
      <div class="m-btns">
        <button class="btn-ghost" id="cfCancel">取消</button>
        <button class="${danger ? 'btn-red' : 'btn-gold'}" id="cfOk">${okText}</button>
      </div>`, { cls: 'small' });
    $('#cfCancel', mask).onclick = () => UI.closeModal();
    $('#cfOk', mask).onclick = () => { UI.closeModal(); onOk && onOk(); };
  },

  welcomeModal() {
    const mask = UI.modal(`
      <div class="m-logo">
        <svg viewBox="0 0 24 24" width="44" height="44"><g fill="#FCD535"><path d="M12 9.4 14.6 12 12 14.6 9.4 12z"/><path d="M12 2.6 15 5.6 12 8.6 9 5.6z"/><path d="M12 15.4 15 18.4 12 21.4 9 18.4z"/><path d="M5.6 9 8.6 12 5.6 15 2.6 12z"/><path d="M18.4 9 21.4 12 18.4 15 15.4 12z"/></g></svg>
      </div>
      <h2>欢迎来到 BILINANCE 模拟盘</h2>
      <p class="m-sub">1:1 复刻交易体验 · 行情为本地模拟引擎驱动</p>
      <ul class="m-rules">
        <li>🎁 已赠送 <b>10,000 USDT</b>,亏光可随时重置</li>
        <li>⚡ 行情秒秒跳动,突发新闻引爆暴涨暴跌</li>
        <li>🟢 现货:一键买卖 / 限价自动撮合</li>
        <li>🔴 合约:选杠杆开多/开空,一键平仓</li>
        <li>🏆 挑战模式:独立本金冲每日排行榜</li>
        <li>🏅 11 个成就 + 每日签到领 1,000 U</li>
      </ul>
      <button class="btn-gold big" id="welcomeTour">📖 60 秒新手教程</button>
      <button class="btn-ghost big" id="welcomeSkip">跳过,直接开始交易</button>
      <p class="m-foot">所有资金均为虚拟数据,仅供娱乐,不构成任何投资建议</p>
    `, { cls: 'welcome', dismissible: false });
    const accept = () => { Store.data.welcomed = true; Store.save(); UI.closeModal(); };
    $('#welcomeTour', mask).onclick = () => { Sfx.click(); accept(); UI.tour.start(0); };
    $('#welcomeSkip', mask).onclick = () => { Sfx.click(); accept(); };
  },

  liquidated(p) {
    const cfg = Engine.get(p.sym).cfg;
    UI.modal(`
      <div class="liq-icon">💥</div>
      <h2 class="danger">爆仓</h2>
      <div class="m-body">
        你的 <b>${cfg.base}/USDT</b> ${p.dir > 0 ? '多' : '空'}单(${p.lev}x)触发强制平仓,<br>
        保证金 <b class="down">${fmt(p.margin, 2)} USDT</b> 全部损失。
      </div>
      <div class="m-btns"><button class="btn-ghost" onclick="UI.closeModal()">知道了</button></div>
    `, { cls: 'small' });
  },

  /* ---------- 顶部/底部导航 ---------- */
  initShell() {
    $('#navEquity').onclick = () => { location.hash = '#/assets'; };
    $('#avatarBtn').onclick = (e) => { e.stopPropagation(); UI.toggleUser(); };
    $('#bellBtn').onclick = (e) => { e.stopPropagation(); UI.toggleBell(); };
    $('#ddAch').onclick = () => { location.hash = '#/assets'; UI.hideDds(); };
    $('#ddTour').onclick = () => { UI.hideDds(); UI.tour.start(0); };
    $('#ddUp').onclick = () => { UI.hideDds(); UI.goUpSpace(true); };
    $('#ddReset').onclick = () => { UI.hideDds(); UI.askReset(); };
    /* UP 主主页:Toy 环境走原生跳转,浏览器新标签打开(fx 同款模式) */
    $('#authorHomeBtn').addEventListener('click', (e) => {
      if (!(window.toy && typeof window.toy.navigate === 'function')) return;
      e.preventDefault();
      const fallback = e.currentTarget.href;
      try {
        Promise.resolve(window.toy.navigate({ type: 'space', id: '443211651' }))
          .catch(() => { window.location.assign(fallback); });
      } catch (err) { window.location.assign(fallback); }
    });
    $('#bellClear').onclick = () => {
      Store.data.events = [];
      Store.save();
      UI.renderBell();
      UI.tickCommon();
    };
    document.addEventListener('click', (e) => {
      if (!e.target.closest('#bellBtn') && !e.target.closest('#bellPanel')) $('#bellPanel').hidden = true;
      if (!e.target.closest('#avatarBtn') && !e.target.closest('#userPanel')) $('#userPanel').hidden = true;
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        UI.hideDds();
        if (UI.tour.active) { UI.tour.close(); return; }
        const m = $('#modal-root .modal');
        if (m && !m.classList.contains('welcome')) UI.closeModal();
      }
    });
  },
  setTheme(theme) {
    theme = theme === 'light' ? 'light' : 'dark';
    Store.data.settings.theme = theme;
    Store.save();
    document.documentElement.dataset.theme = theme;
    $$('#themeSeg button').forEach(b => b.classList.toggle('on', b.dataset.theme === theme));
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = theme === 'light' ? '#EAECEF' : '#0B0E11';
    if (App.page && App.page.onThemeChange) App.page.onThemeChange();
    Sfx.click();
  },
  setSwapColor(swap) {
    Store.data.settings.swapColor = !!swap;
    Store.save();
    if (swap) document.documentElement.dataset.swapup = '1';
    else delete document.documentElement.dataset.swapup;
    $$('#colorSeg button').forEach(b => b.classList.toggle('on', (b.dataset.swap === '1') === !!swap));
    if (App.page && App.page.onThemeChange) App.page.onThemeChange();
    Sfx.click();
  },

  /* ---------- 新手教程(分步聚光灯指引) ---------- */
  tour: {
    active: false, i: 0,
    steps: [
      { hash: '#/markets', sel: null, icon: '🎓', title: '欢迎来到 BILINANCE 模拟盘',
        body: '接下来 8 步,60 秒带你认识全部面板。<br>你已拥有 <b>10,000 USDT</b> 虚拟资金,怎么亏都不心疼,资产页可随时一键重置。' },
      { hash: '#/markets', sel: '.mkt-table', icon: '📈', title: '行情页:挑选你的标的',
        body: '每个币种展示最新价、24h 涨跌、成交额与走势缩略图。<br>点 ☆ 收藏进「自选」;顶部可切<b>涨幅榜 / 跌幅榜 / 成交额</b>排名;搜索框支持中文名和代码。<br>点任意一行 → 进入该币种的交易页。' },
      { hash: '#/trade/BTCUSDT', sel: '.chart-panel', icon: '🕯️', title: 'K 线图:看懂多空博弈',
        body: '绿涨红跌,每根蜡烛记录该时间段的开/收/高/低。<br>桌面:<b>拖拽平移、滚轮缩放</b>;手机:<b>双指捏合缩放</b>。<br>顶部切换 1秒~5分 周期,「MA」开关均线,「复位」回到最新。' },
      { hash: '#/trade/BTCUSDT', sel: '.book-panel', icon: '📖', title: '订单簿:市场的胃口',
        body: '上半部分红色是<b>卖盘</b>、下半部分绿色是<b>买盘</b>,色条越长代表挂单越厚。<br>中间大字是最新成交价;点任意一档价格会自动填进下单框。<br>切到「成交记录」可看实时逐笔成交。' },
      { hash: '#/trade/BTCUSDT', sel: '.form-panel', icon: '🛒', title: '现货下单:先买一单试试',
        body: '<b>限价</b>指定价格挂单等成交,<b>市价</b>立即按当前价成交;买入花 USDT,卖出收 USDT,手续费 0.1%。<br>点 <b>100%</b> 一键按可用余额填满数量,再点下方绿色按钮即可成交。<br>限价单挂出后,在下方面板随时可撤销。' },
      { hash: '#/trade/BTCUSDT', sel: '.bottom-panel', icon: '🧾', title: '委托管理:你的成交回执',
        body: '「当前委托」列出等待成交的限价单,可一键撤销;<br>「历史委托」保留每一笔成交与撤单记录,市价单会直接出现在历史里。<br>成交后右上角 🔔 消息中心也会收到回报。' },
      { hash: '#/futures/BTCUSDT', sel: '.form-panel', icon: '⚡', title: '简化合约:心跳加速的地方',
        body: '选杠杆(5x~50x)→ 输入保证金 → <b>开多(看涨) / 开空(看跌)</b>。<br>开仓后在下方面板实时显示<b>盈亏(ROE)与强平价</b>,浮亏达到保证金的 95% 会自动爆仓。<br>「平仓」一键落袋,盈利单可「平一半」。杠杆越高,心跳越快。' },
      { hash: '#/assets', sel: '.signin-card', icon: '🎁', title: '资产页:领钱与毕业',
        body: '总权益、今日盈亏、胜率都汇总在这里;<br><b>每天签到白拿 1,000 U</b>;成就墙等你点亮;<br>下方设置里还能切换 <b>亮色 / 暗色主题</b>、一键重置账户。' },
      { hash: '#/challenge', sel: '.ch-side', icon: '🏆', title: '挑战模式:冲榜!',
        body: '独立本金 <b>10,000 USDT</b>,与主资产完全隔离;挑战行情<b>波动 ×4</b>,随时「金盆洗手」结算。<br>收益率自动提交 <b>B站每日排行榜</b>,每天 3 次机会,进度云端同步。' },
      { hash: '#/assets', sel: null, icon: '🚀', title: '教程完成,开工!',
        body: '行情每秒都在跳动,<b>突发新闻</b>随时引爆暴涨暴跌 —— 盯紧右上角的小铃铛 🔔。<br>现在去行情页挑一个币,完成你的第一笔交易吧!<br><small>完成教程已获得成就「新手毕业」🎓</small>', last: true }
    ],
    start(i = 0) {
      this.active = true;
      this.i = 0;
      if (!$('#tour-root')) {
        const root = document.createElement('div');
        root.id = 'tour-root';
        document.body.appendChild(root);
      }
      this.go(i || 0);
    },
    go(i) {
      if (!this.active) return;
      this.i = clamp(i, 0, this.steps.length - 1);
      const s = this.steps[this.i];
      if (s.hash && location.hash !== s.hash) {
        /* 立即移除旧提示框,避免导航过渡期点到旧按钮跳步 */
        const root = $('#tour-root');
        if (root) root.innerHTML = '';
        location.hash = s.hash;
        setTimeout(() => this._place(), 780); // 等待路由渲染与图表初始化
      } else {
        this._place();
      }
    },
    _place() {
      if (!this.active) return;
      const s = this.steps[this.i];
      const root = $('#tour-root');
      const n = this.steps.length;
      let rect = null;
      if (s.sel) {
        const el = document.querySelector(s.sel);
        if (el) {
          el.scrollIntoView({ block: 'center' });
          const r = el.getBoundingClientRect();
          if (r.width > 30 && r.height > 24 && r.bottom > 70 && r.top < window.innerHeight - 30) {
            rect = { top: r.top - 6, left: r.left - 6, width: r.width + 12, height: r.height + 12 };
          }
        }
      }
      const last = this.i === n - 1;
      root.innerHTML = `
        ${rect ? `<div class="tour-hole" style="top:${rect.top}px;left:${rect.left}px;width:${rect.width}px;height:${rect.height}px"></div>` : ''}
        <div class="tour-tip">
          <div class="tour-head"><span class="tour-ic">${s.icon}</span><h4>${s.title}</h4></div>
          <p>${s.body}</p>
          <div class="tour-foot">
            <span class="tour-dots">${this.steps.map((_, j) => `<i class="${j <= this.i ? 'on' : ''}"></i>`).join('')}</span>
            <span class="tour-step">${this.i + 1}/${n}</span>
            <span class="tour-btns">
              <button class="link-btn" id="tourSkip">跳过</button>
              ${this.i > 0 ? '<button class="btn-ghost" id="tourPrev">上一步</button>' : ''}
              <button class="btn-gold" id="tourNext">${last ? '完成 🎓' : '下一步'}</button>
            </span>
          </div>
        </div>`;
      const tip = $('.tour-tip', root);
      const tw = tip.offsetWidth, th = tip.offsetHeight;
      if (rect) {
        const below = rect.top + rect.height + 12;
        const above = rect.top - th - 12;
        let top;
        if (below + th < window.innerHeight - 66) top = below;
        else if (above > 60) top = above;
        else top = clamp(window.innerHeight - th - 76, 60, window.innerHeight - th - 12);
        tip.style.top = top + 'px';
        tip.style.left = clamp(rect.left + rect.width / 2 - tw / 2, 12, window.innerWidth - tw - 12) + 'px';
      } else {
        tip.style.top = Math.max(70, (window.innerHeight - th) / 2 - 20) + 'px';
        tip.style.left = Math.max(12, (window.innerWidth - tw) / 2) + 'px';
      }
      $('#tourSkip', root).onclick = () => this.close();
      $('#tourNext', root).onclick = () => { if (last) this.finish(); else this.go(this.i + 1); };
      const prev = $('#tourPrev', root);
      if (prev) prev.onclick = () => this.go(this.i - 1);
      Sfx.click();
    },
    finish() {
      Store.award('grad');
      this.close();
    },
    close() {
      this.active = false;
      const r = $('#tour-root');
      if (r) r.remove();
    }
  },
  hideDds() { $('#bellPanel').hidden = true; $('#userPanel').hidden = true; },
  goUpSpace(fromDropdown) {
    const url = 'https://space.bilibili.com/443211651';
    if (window.toy && typeof window.toy.navigate === 'function') {
      Promise.resolve(window.toy.navigate({ type: 'space', id: '443211651' }))
        .catch(() => window.open(url, '_blank', 'noopener'));
      return;
    }
    window.open(url, '_blank', 'noopener');
  },
  toggleBell() {
    const p = $('#bellPanel');
    $('#userPanel').hidden = true;
    if (p.hidden) { UI.renderBell(); UI.lastSeenT = Date.now(); p.hidden = false; }
    else p.hidden = true;
  },
  toggleUser() {
    const p = $('#userPanel');
    $('#bellPanel').hidden = true;
    if (p.hidden) {
      $('#ddEquity').textContent = fmt(Store.equity(), 2) + ' USDT';
      const n = Object.keys(Store.data.achievements).length;
      $('#ddAchCount').textContent = `${n}/${ACH.length}`;
      p.hidden = false;
    } else p.hidden = true;
  },
  renderBell() {
    const evs = Store.data.events.slice(0, 25);
    $('#bellList').innerHTML = evs.length ? evs.map(e => `
      <div class="ev-row">
        <i class="dot ${e.kind}"></i>
        <div class="ev-txt"><p>${esc(e.text)}</p><time>${hhmmss(e.t)}</time></div>
      </div>`).join('') : emptyBox('暂无消息<br><small>成交回报与突发新闻会出现在这里</small>');
  },
  tickCommon() {
    flash($('#navEquity'), Store.equity(), v => fmt(v, 2) + ' U');
    const n = Store.data.events.filter(e => e.t > UI.lastSeenT).length;
    const badge = $('#bellBadge');
    badge.hidden = n === 0;
    badge.textContent = n > 9 ? '9+' : n;
  },
  askReset() {
    UI.confirm({
      title: '重置账户?',
      body: '将清空所有持仓、订单、成就与统计,<br>重新获得 <b>10,000 USDT</b> 模拟资金。',
      okText: '确认重置', danger: true,
      onOk() {
        Store.reset();
        UI.toast('账户已重置,重新获得 10,000 USDT', 'ok');
        location.hash = '#/markets';
        App.route();
      }
    });
  },

  /* ================= 行情页 ================= */
  marketsPage() {
    let tab = 'all', q = '', tickN = 0;
    const chg = st => st.chg24();
    const html = `
    <div class="page markets-page">
      <div class="page-head">
        <h1>行情</h1>
        <div class="search-box">${ICONS.search}<input id="mktSearch" placeholder="搜索 BTC、DOGE…" inputmode="search"></div>
      </div>
      <div class="tabs" id="mktTabs">
        ${[['fav', '自选'], ['all', '全部'], ['up', '涨幅榜'], ['down', '跌幅榜'], ['vol', '成交额']]
          .map(([k, l]) => `<button data-k="${k}" class="${k === tab ? 'on' : ''}">${l}</button>`).join('')}
      </div>
      <div class="mkt-table panel">
        <div class="mkt-head"><span></span><span></span><span class="col-sym">币种</span><span class="num">最新价</span><span class="num">24h涨跌</span><span class="num hide-sm">24h成交额</span><span class="num">走势</span></div>
        <div id="mktList"></div>
      </div>
    </div>`;

    function renderList() {
      let arr = Engine.list();
      if (tab === 'fav') arr = arr.filter(s => Store.data.favorites[s.cfg.s]);
      else if (tab === 'up') arr = arr.slice().sort((a, b) => chg(b) - chg(a));
      else if (tab === 'down') arr = arr.slice().sort((a, b) => chg(a) - chg(b));
      else if (tab === 'vol') arr = arr.slice().sort((a, b) => b.vol24 - a.vol24);
      if (q) arr = arr.filter(s => (s.cfg.base + s.cfg.name + s.cfg.s).toLowerCase().includes(q));
      $('#mktList').innerHTML = arr.map(st => {
        const cfg = st.cfg, pc = chg(st);
        const closes = (st.candles['1m'] || []).slice(-40).map(c => c.c);
        const fav = Store.data.favorites[cfg.s];
        return `<div class="mkt-row" data-sym="${cfg.s}">
          <button class="star ${fav ? 'on' : ''}" data-star="${cfg.s}" aria-label="自选">${fav ? ICONS.starFill : ICONS.star}</button>
          ${coinIcon(cfg)}
          <div class="mkt-name"><b>${cfg.base}<i>/USDT</i></b><small>${cfg.name}</small></div>
          <div class="mkt-price" data-price>${fmtAdaptive(st.price)}</div>
          <div class="chip ${pc >= 0 ? 'up' : 'down'}" data-pct>${fmtPct(pc)}</div>
          <div class="mkt-vol hide-sm" data-vol>${fmtCompact(st.vol24)}</div>
          <div class="mkt-spark">${sparkSVG(closes)}</div>
        </div>`;
      }).join('') || emptyBox(tab === 'fav' ? '还没有自选,点击 ☆ 添加' : '没有匹配的币种');
    }
    function updateCells() {
      $$('#mktList .mkt-row').forEach(row => {
        const st = Engine.get(row.dataset.sym); if (!st) return;
        const pc = st.chg24();
        flash($('[data-price]', row), st.price);
        const pct = $('[data-pct]', row);
        pct.textContent = fmtPct(pc);
        pct.className = 'chip ' + (pc >= 0 ? 'up' : 'down');
        const vol = $('[data-vol]', row);
        if (vol) vol.textContent = fmtCompact(st.vol24);
      });
    }

    const page = {
      name: 'markets', html,
      bind() {
        $('#mktSearch').addEventListener('input', (e) => { q = e.target.value.trim().toLowerCase(); renderList(); });
        $('#mktTabs').addEventListener('click', (e) => {
          const btn = e.target.closest('button'); if (!btn) return;
          tab = btn.dataset.k;
          $$('#mktTabs button').forEach(b => b.classList.toggle('on', b === btn));
          Sfx.click();
          renderList();
        });
        $('#mktList').addEventListener('click', (e) => {
          const star = e.target.closest('[data-star]');
          if (star) {
            const s = star.dataset.star;
            if (Store.data.favorites[s]) delete Store.data.favorites[s]; else Store.data.favorites[s] = 1;
            Store.save(); Sfx.click();
            renderList();
            return;
          }
          const row = e.target.closest('.mkt-row');
          if (row) {
            /* 回到上次的交易模式(现货/合约),不丢上下文 */
            const mode = Store.data.lastMode === 'futures' ? 'futures' : 'trade';
            location.hash = '#/' + mode + '/' + row.dataset.sym;
          }
        });
        renderList();
      },
      update() {
        tickN++;
        updateCells();
        if ((tab === 'up' || tab === 'down' || tab === 'vol') && tickN % 8 === 0) renderList();
        else if (tickN % 25 === 0) $$('#mktList .mkt-spark').forEach((el, i) => {
          const row = el.closest('.mkt-row');
          const st = Engine.get(row.dataset.sym);
          if (st) el.innerHTML = sparkSVG((st.candles['1m'] || []).slice(-40).map(c => c.c));
        });
      }
    };
    return page;
  },

  /* ================= 交易页(现货/合约共用) ================= */
  tradePage(symIn, fut) {
    const sym = Engine.syms.has(symIn) ? symIn : 'BTCUSDT';
    let st = Engine.get(sym);
    const cfg = st.cfg;
    let chart = null, side = 'buy', type = 'limit', lev = 10, bookTab = 'book';
    let botTab = fut ? 'pos' : 'open';
    let tickN = 0;

    const html = `
    <div class="page trade-page">
      <div class="ticker-bar">
        <a class="sym-sel" href="#/markets">${coinIcon(cfg, 30)}<span class="sym-names"><b>${cfg.base}/USDT</b><small>${cfg.name}</small></span>${ICONS.chevD}</a>
        <div class="tk-price" id="tkPrice">--</div>
        <div class="tk-stats">
          <div class="tk-stat"><label>24h涨跌</label><b id="tkChg">--</b></div>
          <div class="tk-stat"><label>24h最高</label><b id="tkHigh">--</b></div>
          <div class="tk-stat"><label>24h最低</label><b id="tkLow">--</b></div>
          <div class="tk-stat hide-sm"><label>24h成交额</label><b id="tkVol">--</b></div>
        </div>
      </div>
      <div class="trade-grid">
        <section class="panel chart-panel">
          <div class="chart-toolbar">
            <div class="tf-group" id="tfGroup">
              ${TF_LIST.map(([tf, , l], i) => `<button data-tf="${tf}" class="${i === 2 ? 'on' : ''}">${l}</button>`).join('')}
            </div>
            <div class="chart-tools">
              <button id="maBtn" class="on">MA</button>
              <button id="viewReset">复位</button>
            </div>
          </div>
          <div class="chart-wrap"><canvas id="kchart"></canvas></div>
        </section>
        <aside class="panel side-panel book-panel">
          <div class="book-top">
            <div class="tabs small" id="bookTabs">
              <button data-t="book" class="on">订单簿</button>
              <button data-t="trades">成交记录</button>
            </div>
            <button class="fold-btn" id="bookFold" aria-label="折叠/展开">${ICONS.chevD}</button>
          </div>
          <div class="book-scroll">
            <div id="bookView"></div>
            <div id="tradesView" hidden></div>
          </div>
        </aside>
        <aside class="panel side-panel form-panel" id="formPanel"></aside>
      </div>
      <section class="panel bottom-panel">
        <div class="tabs small" id="botTabs">${fut
          ? `<button data-t="pos" class="on">当前持仓 <i id="cntPos"></i></button><button data-t="closed">平仓记录</button>`
          : `<button data-t="open" class="on">当前委托 <i id="cntOpen"></i></button><button data-t="hist">历史委托</button><button data-t="hold">持有 <i id="cntHold"></i></button>`}</div>
        <div class="bot-view" id="botView"></div>
      </section>
    </div>`;

    /* ---- 下单表单 ---- */
    function renderForm() {
      $('#formPanel').innerHTML = fut ? `
        <div class="form-head"><b>${cfg.base}USDT 永续</b><span class="sim-tag">简化模式</span></div>
        <div class="field lev-field">
          <label>杠杆 <b id="levVal">${lev}x</b><span> · 1 ~ 500x</span></label>
          <div class="lev-ctrl">
            <input type="range" id="levSlider" min="1" max="500" step="1" value="${lev}">
            <div class="inp lev-num"><input id="levInput" inputmode="numeric" value="${lev}"></div>
          </div>
        </div>
        <div class="field"><label>保证金 <span>USDT</span></label>
          <div class="inp"><input id="fMargin" inputmode="decimal" placeholder="≥ 5 USDT"></div>
        </div>
        <div class="pct-row">${[25, 50, 75, 100].map(p => `<button data-pct="${p}" data-for="margin">${p}%</button>`).join('')}</div>
        <div class="hint-line">可用 <b id="fAvail">--</b></div>
        <div class="hint-line">名义价值 ≈ <b id="fNotional">0.00 USDT</b></div>
        <div class="hint-line">预估强平价 <b id="fLiq">--</b></div>
        <div class="fut-btns">
          <button class="sub-btn buy" id="fLong">开多 · 看涨</button>
          <button class="sub-btn sell" id="fShort">开空 · 看跌</button>
        </div>
        <p class="fee-note">简化合约:仅市价单,吃单费 0.05%。维持保证金率随杠杆分层(最高 5%),杠杆越高强平价越近;浮亏触及即自动强平。</p>
      ` : `
        <div class="side-switch">
          <button data-side="buy" class="${side === 'buy' ? 'on' : ''}">买入</button>
          <button data-side="sell" class="${side === 'sell' ? 'on' : ''}">卖出</button>
        </div>
        <div class="type-tabs">
          <button data-type="limit" class="${type === 'limit' ? 'on' : ''}">限价</button>
          <button data-type="market" class="${type === 'market' ? 'on' : ''}">市价</button>
        </div>
        <div class="field" id="rowPrice" ${type === 'market' ? 'hidden' : ''}>
          <label>价格 <span>USDT</span></label>
          <div class="inp">
            <button class="step" data-step="-1" aria-label="减">−</button>
            <input id="fPrice" inputmode="decimal" placeholder="0.00">
            <button class="step" data-step="1" aria-label="加">+</button>
          </div>
        </div>
        <div class="field"><label id="qtyLabel">数量 <span>${type === 'market' && side === 'buy' ? 'USDT' : cfg.base}</span></label>
          <div class="inp"><input id="fQty" inputmode="decimal" placeholder="0.00"></div>
        </div>
        <div class="pct-row">${[25, 50, 75, 100].map(p => `<button data-pct="${p}">${p}%</button>`).join('')}</div>
        <div class="hint-line">可用 <b id="fAvail">--</b></div>
        <div class="hint-line"><span id="estLabel">成交额</span> ≈ <b id="fEst">0.00 USDT</b><span class="fee">手续费 0.1%</span></div>
        <button class="sub-btn ${side}" id="fSubmit">${side === 'buy' ? '买入' : '卖出'} ${cfg.base}</button>
      `;
      bindForm();
      updForm(true);
    }

    function bindForm() {
      if (fut) {
        const applyLev = (v, silent) => {
          lev = clamp(Math.round(+v) || 10, 1, 500);
          const s = $('#levSlider'), n = $('#levInput');
          if (s) s.value = lev;
          if (n) n.value = lev;
          $('#levVal').textContent = lev + 'x';
          if (!silent) Sfx.click();
          updForm(true);
        };
        $('#levSlider').addEventListener('input', e => applyLev(e.target.value, true));
        $('#levSlider').addEventListener('change', () => {
          if (lev >= 100) UI.toast(`⚡ ${lev}x 高杠杆:强平价近在咫尺,方向错就秒爆`, 'info');
        });
        $('#levInput').addEventListener('input', e => {
          const v = parseInt(e.target.value, 10);
          if (v >= 1 && v <= 500) { lev = v; $('#levSlider').value = v; $('#levVal').textContent = v + 'x'; updForm(true); }
        });
        $('#levInput').addEventListener('change', e => applyLev(e.target.value));
        $('#fLong').onclick = () => submitFut(1);
        $('#fShort').onclick = () => submitFut(-1);
        $('#formPanel').oninput = () => updForm(true);
        $$('#formPanel [data-pct]').forEach(b => b.onclick = () => {
          const m = $('#fMargin');
          m.value = floorQty(Store.data.usdt * (+b.dataset.pct) / 100, 2);
          Sfx.click(); updForm(true);
        });
        return;
      }
      $$('#formPanel [data-side]').forEach(b => b.onclick = () => {
        side = b.dataset.side;
        $$('#formPanel [data-side]').forEach(x => x.classList.toggle('on', x === b));
        $('#fSubmit').className = 'sub-btn ' + side;
        $('#fSubmit').textContent = (side === 'buy' ? '买入 ' : '卖出 ') + cfg.base;
        if (type === 'market') $('#qtyLabel span').textContent = side === 'buy' ? 'USDT' : cfg.base;
        Sfx.click(); updForm(true);
      });
      $$('#formPanel [data-type]').forEach(b => b.onclick = () => {
        type = b.dataset.type;
        $$('#formPanel [data-type]').forEach(x => x.classList.toggle('on', x === b));
        $('#rowPrice').hidden = type === 'market';
        $('#qtyLabel span').textContent = (type === 'market' && side === 'buy') ? 'USDT' : cfg.base;
        $('#estLabel').textContent = (type === 'market' && side === 'buy') ? '买入金额' : '成交额';
        Sfx.click(); updForm(true);
      });
      $$('#formPanel .step').forEach(b => b.onclick = () => {
        const inp = $('#fPrice');
        const tick = Math.pow(10, -cfg.prec);
        let v = parseFloat(inp.value);
        if (!isFinite(v)) v = st.price;
        v = Math.max(tick, v + tick * (+b.dataset.step) * (e => e)(1));
        inp.value = trimNum(v, cfg.prec);
        updForm(true);
      });
      $('#formPanel').oninput = () => updForm(true);
      $$('#formPanel [data-pct]').forEach(b => b.onclick = () => {
        const pct = +b.dataset.pct / 100;
        if (side === 'buy') {
          const price = type === 'limit' ? (parseFloat($('#fPrice').value) || st.price) : st.price;
          if (type === 'market') $('#fQty').value = floorQty(Store.data.usdt * pct, 2);
          else $('#fQty').value = floorQty(Store.data.usdt * pct / price, cfg.qprec);
        } else {
          // 卖出向下取整避免舍入超出可用;100% 时直接填精确全量,实现一键清仓
          const have = Store.data.balances[cfg.base] || 0;
          $('#fQty').value = pct >= 1 ? String(have) : floorQty(have * pct, cfg.qprec);
        }
        Sfx.click(); updForm(true);
      });
      $('#fSubmit').onclick = () => {
        let r;
        const qty = parseFloat($('#fQty').value);
        if (type === 'market') {
          r = side === 'buy' ? Store.buyMarket(sym, qty) : Store.sellMarket(sym, qty);
        } else {
          const price = parseFloat($('#fPrice').value);
          r = Store.placeLimit(sym, side, price, qty);
        }
        if (r.ok) { UI.toast(r.msg, 'ok'); $('#fQty').value = ''; }
        else { UI.toast(r.msg, 'err'); Sfx.error(); }
        updForm(true);
        renderBot();
      };
    }
    function submitFut(dir) {
      const margin = parseFloat($('#fMargin').value);
      const r = Store.openPosition(sym, dir, margin, lev);
      if (r.ok) { UI.toast(r.msg, 'ok'); $('#fMargin').value = ''; }
      else { UI.toast(r.msg, 'err'); Sfx.error(); }
      updForm(true);
      renderBot();
    }
    function updForm(force) {
      const avail = $('#fAvail'); if (!avail) return;
      if (fut) {
        avail.textContent = fmt(Store.data.usdt, 2) + ' USDT';
        const m = parseFloat($('#fMargin') && $('#fMargin').value) || 0;
        $('#fNotional').textContent = fmt(m * lev, 2) + ' USDT';
        const mm = Store.effMM(lev);
        const long = st.price * (1 - 1 / lev + mm);
        const short = st.price * (1 + 1 / lev - mm);
        $('#fLiq').textContent = m > 0 ? `多 ${fmtAdaptive(long)} / 空 ${fmtAdaptive(short)}` : '--';
      } else {
        avail.textContent = side === 'buy'
          ? fmt(Store.data.usdt, 2) + ' USDT'
          : fmt(Store.data.balances[cfg.base] || 0, cfg.qprec) + ' ' + cfg.base;
        const qty = parseFloat($('#fQty').value) || 0;
        const price = type === 'limit' ? (parseFloat($('#fPrice').value) || st.price) : st.price;
        const est = (type === 'market' && side === 'buy') ? qty : qty * price;
        $('#fEst').textContent = fmt(est, 2) + ' USDT';
      }
    }

    /* ---- 订单簿 / 成交 ---- */
    function bookHtml() {
      const n = 12;
      const asks = st.asks.slice(0, n).reverse();
      const bids = st.bids.slice(0, n);
      let maxQ = 0; for (const a of asks) maxQ = Math.max(maxQ, a.q); for (const b of bids) maxQ = Math.max(maxQ, b.q);
      let cum = 0;
      const askRows = asks.map(a => {
        cum += a.q;
        return `<div class="bk-row ask" data-p="${a.p}"><i style="width:${(a.q / maxQ * 100).toFixed(1)}%"></i><span class="p">${fmtAdaptive(a.p)}</span><span>${fmt(a.q, cfg.qprec)}</span><span>${fmt(cum, cfg.qprec)}</span></div>`;
      }).join('');
      cum = 0;
      const bidRows = bids.map(b => {
        cum += b.q;
        return `<div class="bk-row bid" data-p="${b.p}"><i style="width:${(b.q / maxQ * 100).toFixed(1)}%"></i><span class="p">${fmtAdaptive(b.p)}</span><span>${fmt(b.q, cfg.qprec)}</span><span>${fmt(cum, cfg.qprec)}</span></div>`;
      }).join('');
      const dir = st.price >= st.prevPrice;
      return `
        <div class="bk-head"><span>价格(USDT)</span><span>数量(${cfg.base})</span><span>合计(${cfg.base})</span></div>
        ${askRows}
        <div class="bk-mid"><b class="${dir ? 'up' : 'down'}">${fmtAdaptive(st.price)}</b><span>≈ $${fmtAdaptive(st.price)}</span></div>
        ${bidRows}`;
    }
    function tradesHtml() {
      const rows = st.trades.slice(0, 22).map(t => `
        <div class="td-row"><span class="p ${t.side === 'buy' ? 'up' : 'down'}">${fmtAdaptive(t.p)}</span><span>${fmt(t.q, cfg.qprec)}</span><span class="t">${hhmmss(t.t)}</span></div>`).join('');
      return `<div class="bk-head"><span>价格(USDT)</span><span>数量(${cfg.base})</span><span>时间</span></div>${rows}`;
    }

    /* ---- 底部面板 ---- */
    const closePct = {}; // 每个仓位的平仓百分比(滑动条记忆)
    let posSig = null;
    function posRowHtml(p) {
      const cst = Engine.get(p.sym);
      const liq = Store.liqPrice(p);
      const pct = closePct[p.id] || 100;
      const pnl = Store.pnl(p), roe = pnl / p.margin;
      return `<div class="bot-row pos" data-posrow="${p.id}">
        <span class="b-sym">${coinIcon(cst.cfg, 24)}<div><b>${cst.cfg.base}</b><small><i class="dirchip ${p.dir > 0 ? 'up' : 'down'}">${p.dir > 0 ? '多' : '空'} ${p.lev}x</i> ${fmt(p.qty, cst.cfg.qprec)}</small></div></span>
        <span class="hide-sm">${fmt(p.margin, 2)}</span>
        <span>${fmtAdaptive(p.entry)}</span>
        <span data-mark>${fmtAdaptive(cst.price)}</span>
        <span class="hide-sm">${fmtAdaptive(liq)}</span>
        <span data-pnl class="${pnl >= 0 ? 'up' : 'down'}">${fmt(pnl, 2)}<small> ${fmtPct(roe)}</small></span>
        <span class="b-act">
          <span class="pos-slider"><input type="range" min="1" max="100" step="1" value="${pct}" data-slider="${p.id}" aria-label="平仓比例"><i id="slbl-${p.id}">${pct}%</i></span>
          <button class="mini danger" data-close="${p.id}">平仓</button>
        </span>
      </div>`;
    }
    function updatePosCells() {
      for (const p of Store.data.positions) {
        const row = document.querySelector(`[data-posrow="${p.id}"]`);
        if (!row) continue;
        const mark = $('[data-mark]', row);
        if (mark) mark.textContent = fmtAdaptive(Engine.get(p.sym).price);
        const cell = $('[data-pnl]', row);
        if (cell) {
          const pnl = Store.pnl(p), roe = pnl / p.margin;
          cell.innerHTML = `${fmt(pnl, 2)}<small> ${fmtPct(roe)}</small>`;
          cell.className = pnl >= 0 ? 'up' : 'down';
        }
      }
    }
    function renderPos() {
      const el = $('#botView'); if (!el) return;
      const positions = Store.data.positions;
      const cntP = document.getElementById('cntPos');
      if (cntP) cntP.textContent = positions.length ? `(${positions.length})` : '';
      if (!positions.length) {
        if (posSig !== 'empty') {
          posSig = 'empty';
          el.innerHTML = emptyBox(fut ? '暂无持仓,去右侧开一笔合约吧' : '暂无合约持仓,去「合约」页开一笔');
        }
        return;
      }
      const sig = positions.map(p => `${p.id}:${p.qty.toFixed(10)}:${p.margin.toFixed(4)}`).join('|');
      if (posSig !== sig) {
        posSig = sig;
        el.innerHTML = `<div class="bot-head"><span>合约</span><span class="hide-sm">保证金</span><span>开仓价</span><span>标记价</span><span class="hide-sm">强平价</span><span>盈亏(ROE)</span><span>平仓比例</span></div>`
          + positions.map(posRowHtml).join('');
      } else {
        updatePosCells();
      }
    }
    function holdHtml() {
      const have = Store.data.balances[cfg.base] || 0;
      const pc = st.chg24();
      if (!(have > 0)) return emptyBox(`暂未持有 ${cfg.base},在上方买入后,持仓会显示在这里`);
      const val = have * st.price;
      return `<div class="hold-box">
        ${coinIcon(cfg, 40)}
        <div class="hold-cell main"><label>持有数量</label><b>${fmt(have, cfg.qprec)}<small> ${cfg.base}</small></b></div>
        <div class="hold-cell"><label>折合价值</label><b>≈ ${fmt(val, 2)} USDT</b></div>
        <div class="hold-cell"><label>24h涨跌</label><b class="${pc >= 0 ? 'up' : 'down'}">${fmtPct(pc)}</b></div>
      </div>`;
    }
    function botHtml() {
      if (fut) {
        if (!Store.data.closedPositions.length) return emptyBox('还没有平仓记录');
        return `<div class="bot-head"><span>合约</span><span class="hide-sm">开仓价</span><span>平仓价</span><span>保证金</span><span>盈亏</span><span>结果</span></div>`
          + Store.data.closedPositions.slice(0, 40).map(p => {
            const cst = Engine.get(p.sym);
            return `<div class="bot-row">
              <span class="b-sym">${coinIcon(cst.cfg, 24)}<div><b>${cst.cfg.base}</b><small><i class="dirchip ${p.dir > 0 ? 'up' : 'down'}">${p.dir > 0 ? '多' : '空'} ${p.lev}x</i> ${hhmmss(p.closeTs)}</small></div></span>
              <span class="hide-sm">${fmtAdaptive(p.entry)}</span>
              <span>${fmtAdaptive(p.closePrice)}</span>
              <span>${fmt(p.margin, 2)}</span>
              <span class="${p.pnl >= 0 ? 'up' : 'down'}">${fmt(p.pnl, 2)}</span>
              <span>${p.liq ? '<b class="down">💥 爆仓</b>' : `<b class="${p.pnl >= 0 ? 'up' : 'down'}">${p.pnl >= 0 ? '止盈' : '止损'}</b>`}</span>
            </div>`;
          }).join('');
      }
      if (botTab === 'open') {
        const orders = Store.data.openOrders.filter(o => o.sym === sym);
        $('#cntOpen') && ($('#cntOpen').textContent = orders.length ? `(${orders.length})` : '');
        if (!orders.length) return emptyBox('暂无当前委托');
        return `<div class="bot-head"><span>时间</span><span>方向</span><span>价格</span><span>数量</span><span>金额</span><span></span></div>`
          + orders.map(o => `<div class="bot-row">
              <span>${hhmmss(o.ts)}</span>
              <span class="${o.side === 'buy' ? 'up' : 'down'}">${o.side === 'buy' ? '买入' : '卖出'}<small> 限价</small></span>
              <span>${fmtAdaptive(o.price)}</span>
              <span>${fmt(o.qty, cfg.qprec)}</span>
              <span>${fmt(o.price * o.qty, 2)}</span>
              <span class="b-act"><button class="mini danger" data-cancel="${o.id}">撤销</button></span>
            </div>`).join('');
      }
      const hist = Store.data.history.filter(o => o.sym === sym);
      if (!hist.length) return emptyBox('暂无历史委托');
      return `<div class="bot-head"><span>时间</span><span>方向</span><span>价格</span><span>数量</span><span>状态</span></div>`
        + hist.slice(0, 40).map(o => `<div class="bot-row">
            <span>${hhmmss(o.doneTs || o.ts)}</span>
            <span class="${o.side === 'buy' ? 'up' : 'down'}">${o.side === 'buy' ? '买入' : '卖出'}<small> 限价</small></span>
            <span>${fmtAdaptive(o.price)}</span>
            <span>${fmt(o.qty, cfg.qprec)}</span>
            <span class="${o.status === '已成交' ? 'up' : 'muted'}">${o.status}</span>
          </div>`).join('');
    }
    function renderBot() {
      const el = $('#botView'); if (!el) return;
      if (botTab === 'pos') { renderPos(); return; }
      if (botTab === 'hold') {
        const have = Store.data.balances[cfg.base] || 0;
        const cntH = document.getElementById('cntHold');
        if (cntH) cntH.textContent = have > 1e-9 ? `(${have >= 1e4 ? fmtCompact(have) : trimNum(have, Math.min(cfg.qprec, 4))})` : '';
        el.innerHTML = holdHtml();
        return;
      }
      posSig = null;
      el.innerHTML = botHtml();
    }

    function getOverlays() {
      if (fut) {
        const out = [];
        for (const p of Store.data.positions.filter(p => p.sym === sym)) {
          out.push({ price: p.entry, text: `${p.dir > 0 ? '开多' : '开空'} ${fmtAdaptive(p.entry)} · ${p.lev}x`, color: p.dir > 0 ? C.green : C.red });
          out.push({ price: Store.liqPrice(p), text: `强平 ${fmtAdaptive(Store.liqPrice(p))}`, color: '#848E9C' });
        }
        return out;
      }
      return Store.data.openOrders.filter(o => o.sym === sym).map(o => ({
        price: o.price, text: `${o.side === 'buy' ? '买' : '卖'} ${fmtAdaptive(o.price)}`,
        color: o.side === 'buy' ? C.green : C.red
      }));
    }

    const page = {
      name: fut ? 'futures' : 'trade', html,
      bind() {
        chart = new CandleChart($('#kchart'), {
          getSym: () => Engine.get(sym),
          tf: '15s',
          getOverlays
        });
        /* 币种下拉切换:合约页换币不跳出现货 */
        $('.sym-sel').addEventListener('click', (e) => {
          e.preventDefault();
          UI.symbolSwitcher(sym, fut);
        });
        $('#tfGroup').addEventListener('click', (e) => {
          const b = e.target.closest('button'); if (!b) return;
          $$('#tfGroup button').forEach(x => x.classList.toggle('on', x === b));
          chart.setTf(b.dataset.tf);
          Sfx.click();
        });
        $('#maBtn').onclick = (e) => { chart.showMA = !chart.showMA; e.target.classList.toggle('on', chart.showMA); chart.invalidate(); };
        $('#viewReset').onclick = () => chart.resetView();
        $('#bookTabs').addEventListener('click', (e) => {
          const b = e.target.closest('button'); if (!b) return;
          bookTab = b.dataset.t;
          $$('#bookTabs button').forEach(x => x.classList.toggle('on', x === b));
          $('#bookView').hidden = bookTab !== 'book';
          $('#tradesView').hidden = bookTab !== 'trades';
          Sfx.click();
        });
        $('#bookFold').onclick = () => {
          $('.book-panel').classList.toggle('collapsed');
          Sfx.click();
        };
        $('#botTabs').addEventListener('click', (e) => {
          const b = e.target.closest('button'); if (!b) return;
          botTab = b.dataset.t;
          $$('#botTabs button').forEach(x => x.classList.toggle('on', x === b));
          renderBot();
          Sfx.click();
        });
        $('#botView').addEventListener('click', (e) => {
          const c = e.target.closest('[data-close]');
          if (c) {
            const s = document.querySelector(`[data-slider="${c.dataset.close}"]`);
            const frac = s ? (+s.value / 100) : 1;
            const r = Store.closePosition(c.dataset.close, frac);
            UI.toast(r.msg, r.ok ? 'ok' : 'err');
            if (!r.ok) Sfx.error();
            else closePct[c.dataset.close] = 100;
            renderBot();
            chart.invalidate();
            return;
          }
          const cc = e.target.closest('[data-cancel]');
          if (cc) { Store.cancelOrder(cc.dataset.cancel); UI.toast('已撤销委托', 'ok'); renderBot(); chart.invalidate(); }
        });
        /* 平仓比例滑动条(按钮文字恒定,避免宽度变化引起滑条抖动) */
        $('#botView').addEventListener('input', (e) => {
          const s = e.target.closest('[data-slider]');
          if (!s) return;
          const id = s.dataset.slider;
          const lbl = document.getElementById('slbl-' + id);
          if (lbl) lbl.textContent = s.value + '%';
          closePct[id] = +s.value;
        });
        /* 点击盘口价格 → 填入限价 */
        $('#bookView').addEventListener('click', (e) => {
          const row = e.target.closest('.bk-row'); if (!row || fut) return;
          if (type !== 'limit') { type = 'limit'; renderForm(); }
          const inp = $('#fPrice');
          if (inp) { inp.value = trimNum(+row.dataset.p, cfg.prec); updForm(true); }
        });
        renderForm();
        renderBot();
      },
      update() {
        tickN++;
        flash($('#tkPrice'), st.price);        const pc = st.chg24();
        const ch = $('#tkChg');
        ch.textContent = fmtPct(pc); ch.className = pc >= 0 ? 'up' : 'down';
        $('#tkHigh').textContent = fmtAdaptive(st.high24);
        $('#tkLow').textContent = fmtAdaptive(st.low24);
        $('#tkVol').textContent = fmtCompact(st.vol24);

        if (bookTab === 'book') $('#bookView').innerHTML = bookHtml();
        else $('#tradesView').innerHTML = tradesHtml();

        updForm();
        if (tickN % 2 === 0) renderBot();
      },
      onThemeChange() { chart && (chart.dirty = true); },
      invalidateChart() { chart && (chart.dirty = true); },
      destroy() { chart && chart.destroy(); }
    };
    return page;
  },

  /* ================= 资产页 ================= */
  assetsPage() {
    let tickN = 0;
    const html = `
    <div class="page assets-page">
      <div class="page-head"><h1>资产</h1><span class="sim-tag">模拟资金</span></div>
      <div class="asset-cards">
        <div class="a-card main"><label>总资产折合 (USDT)</label><b id="aTotal">--</b><small id="aTotalUsd">--</small></div>
        <div class="a-card"><label>今日盈亏</label><b id="aToday">--</b><small>含浮动盈亏</small></div>
        <div class="a-card"><label>合约累计盈亏</label><b id="aReal">--</b><small id="aFee">手续费 --</small></div>
        <div class="a-card"><label>交易次数</label><b id="aTrades">--</b><small id="aWinrate">胜率 --</small></div>
      </div>
      <div class="panel signin-card">
        <div class="si-left">${ICONS.gift}<div><b>每日签到</b><small>领取 1,000 USDT 模拟金,今天记得来</small></div></div>
        <button class="btn-gold" id="signinBtn">签到</button>
      </div>
      <div class="panel asset-sec">
        <div class="sec-head"><h3>我的钱包</h3><span class="sec-hint" id="futHint"></span></div>
        <div id="walletList"></div>
      </div>
      <div class="panel asset-sec">
        <div class="sec-head"><h3>成就</h3><span class="sec-hint" id="achCount"></span></div>
        <div class="ach-grid" id="achGrid"></div>
      </div>
      <div class="panel asset-sec">
        <div class="sec-head"><h3>设置</h3></div>
        <div class="set-row"><div class="set-l"><span class="set-emoji">🎨</span><span>主题<small>暗色 / 亮色,随时切换</small></span></div>
          <div class="theme-seg" id="themeSeg">
            <button data-theme="dark">🌙 暗色</button>
            <button data-theme="light">☀️ 亮色</button>
          </div>
        </div>
        <div class="set-row"><div class="set-l"><span class="set-emoji">📈</span><span>涨跌颜色<small>交换K线的涨跌配色</small></span></div>
          <div class="theme-seg" id="colorSeg">
            <button data-swap="0">🟢 绿涨红跌</button>
            <button data-swap="1">🔴 红涨绿跌</button>
          </div>
        </div>
        <div class="set-row"><div class="set-l">${ICONS.sound}<span>音效</span></div><button class="switch" id="swSound" aria-label="音效开关"></button></div>
        <div class="set-row"><div class="set-l">${ICONS.vib}<span>震动反馈</span></div><button class="switch" id="swVib" aria-label="震动开关"></button></div>
        <div class="set-row"><div class="set-l"><span class="set-emoji">📖</span><span>新手教程<small>重新查看分步指引</small></span></div><button class="btn-ghost" id="tourBtn">进入</button></div>
        <div class="set-row"><div class="set-l">${ICONS.reset}<span>重置账户<small>清空持仓与成就,重新获得 10,000 USDT</small></span></div><button class="btn-danger" id="resetBtn">重置</button></div>
      </div>
      <p class="disclaimer">本页面为的模拟交易网页:行情由本地随机引擎模拟,资金均为虚拟数据;不构成任何投资建议。</p>
    </div>`;

    function renderWallet() {
      const d = Store.data;
      const futMargin = d.positions.reduce((s, p) => s + p.margin, 0);
      const hint = $('#futHint');
      hint.textContent = futMargin > 0 ? `合约占用 ${fmt(futMargin, 2)} USDT · ${d.positions.length} 仓` : '';
      const rows = [];
      rows.push(`<div class="w-row">
        ${coinIcon({ logo: 'usdt' }, 32)}
        <div class="w-name"><b>USDT</b><small>泰达币(模拟)</small></div>
        <div class="w-amt"><b>${fmt(d.usdt, 2)}</b><small>可用</small></div>
        <div class="w-val">≈ ${fmt(d.usdt, 2)}</div>
        <a class="mini gold" href="#/trade/BTCUSDT">交易</a>
      </div>`);
      const bases = Object.keys(d.balances).filter(b => d.balances[b] > 1e-12);
      for (const b of bases) {
        const st = Engine.get(b + 'USDT'); if (!st) continue;
        const q = d.balances[b];
        const val = q * st.price;
        rows.push(`<div class="w-row">
          ${coinIcon(st.cfg, 32)}
          <div class="w-name"><b>${b}</b><small>${st.cfg.name}</small></div>
          <div class="w-amt"><b>${fmt(q, st.cfg.qprec)}</b><small>可用</small></div>
          <div class="w-val">≈ ${fmt(val, 2)}<small class="${st.chg24() >= 0 ? 'up' : 'down'}"> ${fmtPct(st.chg24())}</small></div>
          <a class="mini gold" href="#/trade/${st.cfg.s}">交易</a>
        </div>`);
      }
      $('#walletList').innerHTML = rows.join('');
    }
    function renderAch() {
      const A = Store.data.achievements;
      const n = Object.keys(A).length;
      $('#achCount').textContent = `${n}/${ACH.length}`;
      $('#achGrid').innerHTML = ACH.map(a => `
        <div class="ach ${A[a.id] ? 'on' : ''}">
          <span class="ach-ic">${A[a.id] ? a.icon : '🔒'}</span>
          <b>${a.name}</b>
          <small>${a.desc}</small>
        </div>`).join('');
    }
    function updateStatics() {
      const signed = Store.data.lastSignin === todayStr();
      const btn = $('#signinBtn');
      btn.disabled = signed;
      btn.textContent = signed ? '已签到' : '签到';
      $('#swSound').classList.toggle('on', Store.data.settings.sound);
      $('#swVib').classList.toggle('on', Store.data.settings.vibrate);
      $$('#themeSeg button').forEach(b => b.classList.toggle('on', b.dataset.theme === (Store.data.settings.theme === 'light' ? 'light' : 'dark')));
      $$('#colorSeg button').forEach(b => b.classList.toggle('on', (b.dataset.swap === '1') === !!Store.data.settings.swapColor));
    }

    const page = {
      name: 'assets', html,
      bind() {
        $('#signinBtn').onclick = () => {
          const r = Store.signin();
          UI.toast(r.msg, r.ok ? 'gold' : 'err');
          if (!r.ok) Sfx.error();
          updateStatics();
        };
        $('#swSound').onclick = (e) => { Store.data.settings.sound = !Store.data.settings.sound; Store.save(); e.currentTarget.classList.toggle('on', Store.data.settings.sound); Sfx.click(); };
        $('#swVib').onclick = (e) => { Store.data.settings.vibrate = !Store.data.settings.vibrate; Store.save(); e.currentTarget.classList.toggle('on', Store.data.settings.vibrate); Sfx.click(); vibrate(30); };
        $$('#themeSeg button').forEach(b => b.onclick = () => UI.setTheme(b.dataset.theme));
        $$('#colorSeg button').forEach(b => b.onclick = () => UI.setSwapColor(b.dataset.swap === '1'));
        $('#tourBtn').onclick = () => UI.tour.start(0);
        $('#resetBtn').onclick = () => UI.askReset();
        renderWallet(); renderAch(); updateStatics();
      },
      update() {
        tickN++;
        const eq = Store.equity();
        flash($('#aTotal'), eq, v => fmt(v, 2));
        $('#aTotalUsd').textContent = '≈ $' + fmt(eq, 2);
        const today = Store.todayPnl();
        const t = $('#aToday');
        t.textContent = (today >= 0 ? '+' : '') + fmt(today, 2);
        t.className = today >= 0 ? 'up' : 'down';
        const real = Store.data.stats.realized;
        const r = $('#aReal');
        r.textContent = (real >= 0 ? '+' : '') + fmt(real, 2);
        r.className = real >= 0 ? 'up' : 'down';
        $('#aFee').textContent = `手续费 ${fmt(Store.data.stats.fees, 2)}`;
        $('#aTrades').textContent = Store.data.stats.trades;
        const w = Store.data.stats.wins + Store.data.stats.losses;
        $('#aWinrate').textContent = w ? `胜率 ${(Store.data.stats.wins / w * 100).toFixed(0)}%` : '胜率 --';
        if (tickN % 2 === 0) renderWallet();
        if (tickN % 10 === 0) renderAch();
      }
    };
    return page;
  }
};

  /* 币种下拉切换菜单(交易/合约页左上角),选择后保持在当前模式 */
  UI.symbolSwitcher = function(currentSym, fut) {
    const old = $('#symPanel');
    if (old) { old.remove(); return; }
    const bar = document.querySelector('.ticker-bar');
    if (!bar) return;
    const panel = document.createElement('div');
    panel.id = 'symPanel';
    panel.className = 'dropdown sym-panel';
    panel.innerHTML = Engine.list().map(st => {
      const pc = st.chg24();
      return `<div class="sym-row ${st.cfg.s === currentSym ? 'on' : ''}" data-sym="${st.cfg.s}">
        ${coinIcon(st.cfg, 26)}
        <div class="sym-name"><b>${st.cfg.base}/USDT</b><small>${st.cfg.name}</small></div>
        <div class="sym-p"><span class="${pc >= 0 ? 'up' : 'down'}">${fmtAdaptive(st.price)}</span><small class="${pc >= 0 ? 'up' : 'down'}">${fmtPct(pc)}</small></div>
      </div>`;
    }).join('');
    bar.appendChild(panel);
    panel.addEventListener('click', (e) => {
      const r = e.target.closest('.sym-row');
      if (!r) return;
      const s = r.dataset.sym;
      panel.remove();
      if (s !== currentSym) location.hash = (fut ? '#/futures/' : '#/trade/') + s;
    });
    setTimeout(() => {
      const closer = (ev) => {
        if (!ev.target.closest('#symPanel') && !ev.target.closest('.sym-sel')) {
          panel.remove();
          document.removeEventListener('click', closer);
        }
      };
      document.addEventListener('click', closer);
    }, 0);
  },

  /* ================= 挑战模式页 ================= */
  UI.challengePage = function() {
    let chart = null, tickN = 0, side = 'buy';
    const coin = () => Store.data.challenge.coin;
    const cfgOf = () => Challenge.cfg(coin());

    const html = `
    <div class="page challenge-page">
      <div class="page-head"><h1>挑战模式</h1><span class="sim-tag">独立账户 · 不影响主资产</span></div>
      <div class="ch-grid">
        <aside class="panel ch-side">
          <div class="ch-hero">
            <span class="ch-trophy">🏆</span>
            <b>每日挑战</b>
            <small>独立本金 10,000 USDT,挑战行情波动 ×4。<br>随时「金盆洗手」结算,收益率计入今日榜。<br>每天 3 次机会,进度云端同步。</small>
          </div>
          <div class="ch-meta">
            <div><label>今日剩余</label><b id="chRemaining">读取中…</b></div>
            <div><label>我的最佳</label><b id="chBest">--</b></div>
            <div><label>挑战状态</label><b id="chStatus">--</b></div>
          </div>
          <div class="ch-coins">
            <label>挑战币种${'('}挑战中切换会自动清仓)</label>
            <div class="ch-coin-chips" id="chCoins"></div>
          </div>
        <button class="btn-gold big" id="chStartBtn">开始挑战</button>
        <div class="ch-btns">
          <button class="btn-ghost" id="chRankBtn">♛ 今日榜单</button>
        </div>
          <p class="fee-note">成绩 = 结算总权益 − 10,000(即收益基点)。榜单按自然日刷新,仅手动打开时读取;需 B站 Toy 环境,本地预览记录本机战绩。</p>
        </aside>
        <section class="panel ch-main">
          <div class="ch-status">
            <div class="ch-eq main"><label>挑战总权益</label><b id="chEquity">10,000.00</b></div>
            <div class="ch-eq"><label>挑战收益</label><b id="chPnl">+0.00</b></div>
            <div class="ch-eq"><label>已进行</label><b id="chTime">--</b></div>
            <button class="btn-danger" id="chFinishBtn" hidden>🛁 金盆洗手 · 结算上榜</button>
          </div>
          <div class="chart-toolbar">
            <div class="tf-group" id="chTf">
              ${TF_LIST.filter(t => t[1] >= 5).map(([tf, , l], i) => `<button data-tf="${tf}" class="${i === 0 ? 'on' : ''}">${l}</button>`).join('')}
            </div>
            <div class="chart-tools"><button id="chReset">复位</button></div>
          </div>
          <div class="chart-wrap ch-chart"><canvas id="chChart"></canvas></div>
          <div class="ch-form">
            <div class="side-switch">
              <button data-side="buy" class="on">买入</button>
              <button data-side="sell">卖出</button>
            </div>
            <div class="field"><label id="chQtyLabel">买入金额 <span>USDT</span></label>
              <div class="inp"><input id="chQty" inputmode="decimal" placeholder="0.00"></div>
            </div>
            <div class="pct-row">${[25, 50, 75, 100].map(p => `<button data-pct="${p}">${p}%</button>`).join('')}</div>
            <div class="hint-line"><span id="chAvailLabel">挑战可用</span> <b id="chAvail">--</b></div>
            <div class="fut-btns">
              <button class="sub-btn buy" id="chBuyBtn">市价买入</button>
              <button class="sub-btn sell" id="chSellBtn">市价卖出</button>
            </div>
            <p class="fee-note" id="chHoldLine">--</p>
          </div>
        </section>
      </div>
    </div>`;

    function renderCoins() {
      $('#chCoins').innerHTML = Engine.list().map(st =>
        `<button data-sym="${st.cfg.s}" class="${st.cfg.s === coin() ? 'on' : ''}">${st.cfg.base}</button>`).join('');
    }
    function updSide() {
      $$('.ch-form [data-side]').forEach(b => b.classList.toggle('on', b.dataset.side === side));
      $('#chQtyLabel').innerHTML = side === 'buy'
        ? `买入金额 <span>USDT</span>`
        : `卖出数量 <span>${cfgOf().base}</span>`;
    }
    function updForm() {
      const d = Store.data.challenge;
      const cfg = cfgOf();
      const active = d.active;
      $('#chBuyBtn').disabled = $('#chSellBtn').disabled = !active;
      const qty = parseFloat($('#chQty').value) || 0;
      if (side === 'buy') {
        $('#chAvailLabel').textContent = '挑战可用';
        $('#chAvail').textContent = fmt(d.usdt, 2) + ' USDT';
        $('#chBuyBtn').textContent = `买入 ${cfg.base}`;
        $('#chSellBtn').textContent = `卖出 ${cfg.base}`;
      } else {
        const have = d.balances[cfg.base] || 0;
        $('#chAvailLabel').textContent = `持有 ${cfg.base}`;
        $('#chAvail').textContent = fmt(have, cfg.qprec);
      }
      const price = Challenge.st && Challenge.st.cfg.s === cfg.s ? Challenge.st.price : 0;
      const est = side === 'buy' ? qty : qty * (price || 0);
      $('#chHoldLine').textContent = active
        ? `按当前挑战市价,${side === 'buy' ? '买入金额' : '卖出数量'}约折合 ${fmt(est, 2)} USDT · 手续费 0.1%`
        : '开始挑战后即可交易(市价单,手续费 0.1%)';
    }

    const page = {
      name: 'challenge', html,
      bind() {
        Challenge.ensureMarket();
        chart = new CandleChart($('#chChart'), { getSym: () => Challenge.st, tf: '5s' });
        Challenge.load();
        renderCoins(); updSide();

        $('#chTf').addEventListener('click', (e) => {
          const b = e.target.closest('button'); if (!b) return;
          $$('#chTf button').forEach(x => x.classList.toggle('on', x === b));
          chart.setTf(b.dataset.tf);
          Sfx.click();
        });
        $('#chReset').onclick = () => chart.resetView();
        $('#chCoins').addEventListener('click', (e) => {
          const b = e.target.closest('button'); if (!b) return;
          const sym = b.dataset.sym;
          if (sym === coin()) return;
          const d = Store.data.challenge;
          const held = d.active && Challenge.st && (d.balances[Challenge.st.cfg.base] || 0) > 0;
          if (held) {
            UI.confirm({
              title: '切换币种?',
              body: '挑战中切换币种会按当前挑战市价<b>自动清仓</b>现有持仓,继续吗?',
              okText: '继续切换',
              onOk() { Challenge.switchCoin(sym); renderCoins(); updForm(); }
            });
          } else {
            Challenge.switchCoin(sym);
            renderCoins(); updForm();
          }
        });
        $('#chStartBtn').onclick = async () => {
          const r = await Challenge.start();
          if (r && !r.ok) { UI.toast(r.msg, 'err'); Sfx.error(); }
        };
        $('#chRankBtn').onclick = () => Challenge.showRank();
        $('#chFinishBtn').onclick = () => UI.confirm({
          title: '现在金盆洗手?',
          body: '将按当前挑战市价结算全部持仓,挑战随即结束,<br>收益率自动提交今日排行榜。',
          okText: '确认结算', danger: true,
          onOk() { Challenge.finish(); }
        });
        $$('.ch-form [data-side]').forEach(b => b.onclick = () => { side = b.dataset.side; updSide(); updForm(); Sfx.click(); });
        $('#chQty').addEventListener('input', updForm);
        $$('.ch-form [data-pct]').forEach(b => b.onclick = () => {
          const d = Store.data.challenge, pct = +b.dataset.pct / 100, cfg = cfgOf();
          if (side === 'buy') $('#chQty').value = floorQty(d.usdt * pct, 2);
          else $('#chQty').value = floorQty(d.balances[cfg.base] || 0, pct >= 1 ? 8 : cfg.qprec);
          updForm(); Sfx.click();
        });
        $('#chBuyBtn').onclick = () => {
          const r = Challenge.buy(coin(), parseFloat($('#chQty').value));
          if (r.ok) { UI.toast(r.msg, 'ok'); $('#chQty').value = ''; }
          else { UI.toast(r.msg, 'err'); Sfx.error(); }
          updForm();
        };
        $('#chSellBtn').onclick = () => {
          const r = Challenge.sell(coin(), parseFloat($('#chQty').value));
          if (r.ok) { UI.toast(r.msg, 'ok'); $('#chQty').value = ''; }
          else { UI.toast(r.msg, 'err'); Sfx.error(); }
          updForm();
        };
        updForm();
      },
      update() {
        tickN++;
        const d = Store.data.challenge;
        $('#chRemaining').textContent = Challenge.loaded ? `${d.remaining} / 3` : '读取中…';
        const best = $('#chBest');
        const hasRun = d.runs > 0 || (d.history && d.history.length > 0);
        best.textContent = hasRun ? Challenge.rankText(d.best) : '--';
        best.className = hasRun ? (d.best >= 0 ? 'up' : 'down') : '';
        const st = $('#chStatus');
        st.textContent = !Challenge.loaded ? '读取中…' : d.active ? '⚡ 进行中' : (d.remaining <= 0 ? '今日已用完' : '未开始');
        st.className = d.active ? 'up' : '';
        const startBtn = $('#chStartBtn');
        if (!Challenge.loaded) { startBtn.disabled = true; startBtn.textContent = '读取中…'; }
        else if (d.active) { startBtn.disabled = false; startBtn.textContent = '继续当前挑战'; }
        else if (d.remaining <= 0) { startBtn.disabled = true; startBtn.textContent = '今日机会已用完'; }
        else { startBtn.disabled = false; startBtn.textContent = `开始挑战(剩 ${d.remaining} 次)`; }
        $('#chFinishBtn').hidden = !d.active;

        const eq = Challenge.equity();
        flash($('#chEquity'), eq, v => fmt(v, 2));
        const pnl = eq - CHALLENGE_START;
        const p = $('#chPnl');
        p.textContent = (pnl >= 0 ? '+' : '') + fmt(pnl, 2) + ` (${Challenge.rankText(Math.round(pnl))})`;
        p.className = pnl >= 0 ? 'up' : 'down';
        $('#chTime').textContent = d.active ? Challenge.elapsedText() : '--';

        updForm();
        if (tickN % 8 === 0) renderCoins();
      },
      onThemeChange() { chart && (chart.dirty = true); },
      invalidateChart() { chart && (chart.dirty = true); },
      destroy() { chart && chart.destroy(); }
    };
    return page;
  };

  function trimNum(v, prec) {
  if (!isFinite(v)) return '';
  return String(parseFloat(v.toFixed(Math.min(prec, 8))));
}
/* 向下取整到精度位:用于按百分比卖出/买入,避免舍入后超出可用余额 */
function floorQty(v, prec) {
  if (!isFinite(v) || v <= 0) return '';
  const p = Math.min(prec, 8);
  const f = Math.floor(v * Math.pow(10, p) + 1e-9) / Math.pow(10, p);
  return String(f);
}
