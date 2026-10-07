(() => {
  'use strict';
  const PAIRS = [
    { id: 'EUR/USD', name: '欧元 / 美元', initial: 1.08742, digits: 5 },
    { id: 'GBP/USD', name: '英镑 / 美元', initial: 1.27486, digits: 5 },
    { id: 'USD/JPY', name: '美元 / 日元', initial: 149.382, digits: 3 },
    { id: 'USD/CHF', name: '美元 / 瑞郎', initial: 0.88521, digits: 5 },
    { id: 'EUR/CHF', name: '欧元 / 瑞郎', initial: 0.94170, digits: 5 },
    { id: 'AUD/USD', name: '澳元 / 美元', initial: 0.65432, digits: 5 },
    { id: 'USD/CAD', name: '美元 / 加元', initial: 1.37185, digits: 5 }
  ];
  const BATTLES = [
    { id: 'franc-2015', title: '瑞郎脱钩黑天鹅', pair: 'EUR/CHF', event: '2015-01-15', start: '2014-12-01', end: '2015-02-20', description: '瑞士央行取消欧元兑瑞郎的最低汇率。', source: 'https://www.snb.ch/en/the-snb/organisation/history/geld-und-waehrungspolitische-chronik', news: [
      { date: '2014-12-18', tag: '央行政策', title: '瑞士央行宣布负利率', body: '瑞士央行宣布对活期存款余额实施负利率，并重申将维护 1 欧元兑 1.20 瑞郎的最低汇率。' },
      { date: '2015-01-12', tag: '市场观察', title: '市场仍把 1.20 当作政策底线', body: '交易者普遍围绕最低汇率布置仓位，瑞郎波动受到政策承诺压制。' },
      { date: '2015-01-15', tag: '突发决议', title: '瑞士央行取消最低汇率', body: '瑞士央行停止维持 1.20 下限，并把活期存款利率下调至 -0.75%。市场流动性骤降。' }
    ] },
    { id: 'brexit-2016', title: '英国公投冲击', pair: 'GBP/USD', event: '2016-06-24', start: '2016-05-16', end: '2016-07-22', description: '英国脱欧公投结果公布后，英镑快速下跌。', source: 'https://www.bankofengland.co.uk/news/2016/june/statement-from-the-governor-of-the-boe-following-the-eu-referendum-result', news: [
      { date: '2016-06-14', tag: '风险提示', title: '英国央行警示公投风险', body: '英国央行把欧盟公投视为显著的短期金融稳定风险，市场开始提高英镑波动预期。' },
      { date: '2016-06-23', tag: '投票日', title: '英国举行欧盟成员资格公投', body: '投票结束后，各地结果将陆续公布；市场对最终结果仍有明显分歧。' },
      { date: '2016-06-24', tag: '结果公布', title: '英国投票决定离开欧盟', body: '脱欧阵营胜出。英国央行表示已准备提供超过 2500 亿英镑的额外资金支持市场运作。' }
    ] },
    { id: 'parity-2022', title: '欧元接近平价', pair: 'EUR/USD', event: '2022-07-12', start: '2022-06-01', end: '2022-08-12', description: '美元走强，欧元兑美元逼近平价。', source: 'https://www.ecb.europa.eu/press/pr/date/2022/html/ecb.mp220721~53e5bdd317.en.html', news: [
      { date: '2022-06-09', tag: '政策预告', title: '欧洲央行预告结束负利率', body: '欧洲央行计划在 7 月加息 25 个基点，并表示若通胀前景恶化，9 月可能采取更大幅度行动。' },
      { date: '2022-07-12', tag: '关键价位', title: '欧元兑美元触及平价附近', body: '能源风险、增长担忧与美元走强叠加，1 欧元接近兑换 1 美元。' },
      { date: '2022-07-21', tag: '利率决议', title: '欧洲央行加息 50 个基点', body: '欧洲央行以高于此前指引的幅度加息，并批准传导保护工具 TPI。' }
    ] },
    { id: 'yen-2022', title: '日元干预时刻', pair: 'USD/JPY', event: '2022-09-22', start: '2022-08-15', end: '2022-10-28', description: '日本当局买入日元，美元兑日元经历震荡。', source: 'https://www.mof.go.jp/english/policy/international_policy/reference/feio/index.html', news: [
      { date: '2022-09-07', tag: '口头干预', title: '日本当局关注日元单边波动', body: '美元兑日元快速上行，日本官员对单边、快速的汇率走势表达担忧。' },
      { date: '2022-09-22', tag: '市场干预', title: '日本实施买入日元干预', body: '在日本央行维持宽松政策后，日本当局进入外汇市场买入日元。' },
      { date: '2022-10-21', tag: '剧烈波动', title: '美元兑日元高位快速回落', body: '汇率在高位出现急速反转，市场随后确认日本再次实施了外汇干预。' }
    ] }
  ];
  const SIM_NEWS = [
    { tag: '通胀数据', title: '核心通胀高于预期', body: '利率路径预期重新定价，美元短线波动放大。', bias: { 'EUR/USD': -.00045, 'GBP/USD': -.00035, 'USD/JPY': .00038, 'USD/CHF': .0003, 'AUD/USD': -.00042, 'USD/CAD': .00025 } },
    { tag: '就业数据', title: '新增就业明显降温', body: '交易者下调紧缩预期，但不同货币对的资金流向仍有分歧。', bias: { 'EUR/USD': .00035, 'GBP/USD': .0003, 'USD/JPY': -.00035, 'USD/CHF': -.00025, 'AUD/USD': .00028, 'USD/CAD': -.0002 } },
    { tag: '风险事件', title: '避险情绪突然升温', body: '股市与大宗商品承压，避险货币获得买盘，市场流动性变薄。', bias: { 'EUR/USD': -.00025, 'GBP/USD': -.00032, 'USD/JPY': -.00022, 'USD/CHF': -.00018, 'AUD/USD': -.0005, 'USD/CAD': .0003 } },
    { tag: '央行讲话', title: '官员强调政策取决于数据', body: '市场同时解读出偏鹰与偏鸽信号，价格可能先冲高再回落。', bias: {} },
    { tag: '能源市场', title: '能源价格快速反弹', body: '通胀与贸易条件预期发生变化，欧系与商品货币波动加大。', bias: { 'EUR/USD': -.00028, 'GBP/USD': -.00016, 'AUD/USD': .0002, 'USD/CAD': -.00034 } },
    { tag: '市场传闻', title: '大型资金调整月底仓位', body: '跨市场再平衡带来短时订单流，方向并不一定延续。', bias: {} }
  ];
  const TUTORIAL = [
    { icon: '↗', title: '做多：期待价格上涨', text: '选择货币对后点击“做多 / 买入”。如果之后的价格高于开仓价，你的仓位就会盈利；如果跌了，就会亏损。', example: '例：EUR/USD 从 1.0800 涨到 1.0900，做多方向有利。' },
    { icon: '↘', title: '做空：期待价格下跌', text: '点击“做空 / 卖出”，价格下跌时盈利，价格上涨时亏损。做空和做多都可以在持仓区平仓。', example: '例：GBP/USD 从 1.2800 跌到 1.2700，做空方向有利。' },
    { icon: '$', title: '保证金：先放入押金', text: '开仓时投入的金额是保证金，会从可用余额暂时锁定。平仓后，剩余保证金与盈亏一起返回账户。', example: '例：投入 $500 保证金后，可用余额会先减少 $500。' },
    { icon: '×', title: '杠杆：放大波动', text: '杠杆会放大交易仓位，也同样放大盈利、亏损与手续费。杠杆越高，开仓手续费越高。', example: '例：$500 保证金 × 20 倍杠杆 = $10,000 名义仓位，并收取对应手续费。' },
    { icon: '♡', title: '平仓与穿仓', text: '持仓区会显示实时盈亏。点击“平仓”后按当前价格结算；亏损达到保证金的 80% 会触发爆仓，但跳空可能让亏损超过保证金。', example: '临近爆仓时可以追加保证金，也能借款补仓；穿仓后余额会显示为负数。' }
  ];
  const $ = (id) => document.getElementById(id);
  const money = (n) => `${n < 0 ? '-' : ''}$${Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const signedMoney = (n) => `${n >= 0 ? '+' : '-'}$${Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const pct = (n) => `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;
  const priceText = (pair, n) => Number.isFinite(n) ? n.toFixed(PAIRS.find(p => p.id === pair).digits) : '—';
  const LOAN_MAX = 200000;
  const loanDailyRate = amount => amount <= 10000 ? .0001 : amount <= 50000 ? .0002 : amount <= 100000 ? .0003 : .0004;
  const rateText = rate => `${(rate * 100).toFixed(2)}%`;
  const tradeFee = (margin, leverage) => margin * leverage * (.00005 + leverage * .000005);
  const accountSeed = () => ({ cash: 10000, debt: 0, loanPrincipal: 0, loanRate: 0, simLoanTicks: 0, positions: [], history: [], pair: 'EUR/USD', leverage: 20, margin: 500, feesPaid: 0, equityTrail: [], realProgress: {}, realRangeKey: null, realRange: null });
  const initialState = mode => ({ ...accountSeed(), mode: mode || 'sim' });
  let state = initialState('sim');
  let modeAccounts = { sim: null, real: null, battle: null, challenge: null };
  let savedSim = null;
  try {
    const saved = JSON.parse(localStorage.getItem('fx-heartbeat-save-v3') || localStorage.getItem('fx-heartbeat-save') || 'null');
    if (saved?.accounts) {
      modeAccounts = { ...modeAccounts, ...saved.accounts };
      // 开局固定进入模拟数据模式；其他模式的进度保留，切换时自动续播
      state = { ...initialState('sim'), ...(modeAccounts.sim || {}), mode: 'sim' };
      if (saved.market) Object.assign(state, saved.market);
      if (saved.sim && PAIRS.filter(p => p.id !== 'EUR/CHF').every(p => Array.isArray(saved.sim?.[p.id]?.candles) && Number.isFinite(saved.sim[p.id].price))) savedSim = saved.sim;
    } else if (saved && Number.isFinite(saved.cash) && Array.isArray(saved.positions)) {
      state = { ...state, ...saved, mode: 'sim' };
      if (PAIRS.filter(p => p.id !== 'EUR/CHF').every(p => Array.isArray(saved.sim?.[p.id]?.candles) && Number.isFinite(saved.sim[p.id].price))) savedSim = saved.sim;
    }
  } catch (_) {}
  if (!PAIRS.some(p => p.id === state.pair)) state.pair = 'EUR/USD';
  state.leverage = Math.max(1, Math.min(100, Number(state.leverage) || 20));
  state.margin = Math.max(10, Number(state.margin) || 500);
  state.debt = Math.max(0, Number(state.debt) || 0);
  state.loanPrincipal = state.debt > 0 ? Math.max(1, Number(state.loanPrincipal) || state.debt) : 0;
  state.loanRate = state.debt > 0 ? loanDailyRate(state.loanPrincipal) : 0;
  state.simLoanTicks = Math.max(0, Math.min(19, Math.floor(Number(state.simLoanTicks) || 0)));
  state.positions.forEach(pos => { pos.notional = Number.isFinite(pos.notional) ? pos.notional : pos.margin * pos.leverage; pos.warned = false; });
  normalizeAccount();
  if (state.mode === 'battle' && !BATTLES.some(item => item.id === state.battleId)) state.mode = 'sim';
  let sim = {};
  let challengeSim = {};
  let real = { items: [], cursor: 0, loading: false, error: '' };
  let battle = { items: [], cursor: 0, loading: false, error: '', id: null };
  let battlePickerOpen = false;
  let autoPlay = false;
  let toastTimer;
  let modalAction = null;
  let modalQueue = [];
  let modalOpen = false;
  let historyExpanded = false;
  let requestCounter = 0;
  let battleRequestCounter = 0;
  let riskPaused = false;
  let riskPositionId = null;
  let loanQuoteActive = false;
  let tutorialStep = 0;
  let simNewsTicks = 8 + Math.floor(Math.random() * 8);
  let simTickCount = 0;
  let marginHelpDone = false;
  let progressActive = false, progressActiveTimer = null;
  let activeSimNews = null;
  let activeSimNewsTicks = 0;
  const todayKey = () => new Date().toLocaleDateString('en-CA');
  let challenge = { date: todayKey(), remaining: 3, active: false, loaded: false, loading: false, saving: false };
  let challengeSaveTimer = null;
  const supportCache = new Map();
  const CHALLENGE_BOARD = 3;
  const CHALLENGE_SCORE_MIN = -16777216;
  const CHALLENGE_SCORE_MAX = 16777215;
  const CHALLENGE_SCORE_DOLLARS = 100;
  const challengeScore = profit => Math.max(CHALLENGE_SCORE_MIN, Math.min(CHALLENGE_SCORE_MAX, Math.trunc(profit / CHALLENGE_SCORE_DOLLARS)));
  const challengeRankText = score => {
    const value = Number(score) || 0;
    return `${value < 0 ? '-' : ''}${(Math.abs(value) / 100).toFixed(2)} W`;
  };

  /* ===== v3：设置 / 主题 ===== */
  const DEFAULT_SETTINGS = { sfxOn: true, sfxVol: 70, musicOn: false, musicVol: 60, newsOn: true, newsFreq: 'mid', theme: 'day' };
  let settings = (() => { try { return { ...DEFAULT_SETTINGS, ...(JSON.parse(localStorage.getItem('fx-settings-v1') || 'null') || {}) }; } catch (_) { return { ...DEFAULT_SETTINGS }; } })();
  function saveSettings() {
    try { localStorage.setItem('fx-settings-v1', JSON.stringify(settings)); } catch (_) {}
    document.documentElement.dataset.theme = settings.theme;
    const meta = $('metaTheme');
    if (meta) meta.content = settings.theme === 'night' ? '#101c1e' : '#eff8f4';
  }
  const CHART_THEMES = {
    day: { bg: '#24383c', grid: '#3c5254', vgrid: '#32494b', axis: '#91a9a8', date: '#7f9999', up: '#8fddb1', down: '#f19aa8', dash: '#d5e1b3' },
    night: { bg: '#0e2023', grid: '#24413c', vgrid: '#1c3436', axis: '#7e9a94', date: '#5f7d78', up: '#8fddb1', down: '#f19aa8', dash: '#c9d8a8' }
  };

  /* ===== v3：音频（WebAudio 音效 + 导入音乐） ===== */
  const AudioFX = {
    ctx: null, sfxGain: null, musicGain: null, musicSource: null,
    ensure() {
      if (!this.ctx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return null;
        this.ctx = new AC();
        this.sfxGain = this.ctx.createGain(); this.sfxGain.connect(this.ctx.destination);
        this.musicGain = this.ctx.createGain(); this.musicGain.connect(this.ctx.destination);
        this.applyVolumes();
      }
      if (this.ctx.state === 'suspended') this.ctx.resume();
      return this.ctx;
    },
    applyVolumes() {
      if (!this.ctx) return;
      this.sfxGain.gain.value = settings.sfxOn ? (settings.sfxVol / 100) * .9 : 0;
      this.musicGain.gain.value = settings.musicOn ? (settings.musicVol / 100) * .8 : 0;
    },
    tone(freq, dur, type = 'sine', start = 0, vol = 1, slide = 0) {
      const ctx = this.ensure();
      if (!ctx || !settings.sfxOn) return;
      const t = ctx.currentTime + start;
      const osc = ctx.createOscillator(), gain = ctx.createGain();
      osc.type = type; osc.frequency.setValueAtTime(freq, t);
      if (slide) osc.frequency.exponentialRampToValueAtTime(Math.max(40, freq + slide), t + dur);
      gain.gain.setValueAtTime(0, t);
      gain.gain.linearRampToValueAtTime(.26 * vol, t + .012);
      gain.gain.exponentialRampToValueAtTime(.0001, t + dur);
      osc.connect(gain); gain.connect(this.sfxGain);
      osc.start(t); osc.stop(t + dur + .05);
    },
    open() { this.tone(660, .09, 'triangle'); this.tone(880, .1, 'triangle', .07); },
    win() { this.tone(523, .12, 'triangle'); this.tone(659, .12, 'triangle', .09); this.tone(784, .2, 'triangle', .18); },
    lose() { this.tone(392, .16, 'triangle'); this.tone(311, .24, 'triangle', .12); },
    blow() { this.tone(440, .32, 'sawtooth', 0, .9, -330); },
    alarm() { this.tone(740, .09, 'square', 0, .5); this.tone(740, .09, 'square', .14, .5); },
    news() { this.tone(988, .07, 'sine', 0, .45); this.tone(1319, .09, 'sine', .06, .35); },
    achieve() { [523, 659, 784, 1047].forEach((f, i) => this.tone(f, .14, 'triangle', i * .09)); },
    click() { this.tone(1200, .04, 'sine', 0, .22); }
  };
  document.addEventListener('pointerdown', () => { AudioFX.ensure(); }, { passive: true });

  const MusicStore = {
    db: null,
    open() {
      return new Promise(resolve => {
        if (this.db) return resolve(this.db);
        if (!window.indexedDB) return resolve(null);
        const req = indexedDB.open('fx-audio', 1);
        req.onupgradeneeded = () => req.result.createObjectStore('music');
        req.onsuccess = () => { this.db = req.result; resolve(this.db); };
        req.onerror = () => resolve(null);
      });
    },
    async put(record) {
      const db = await this.open();
      if (!db) return false;
      return new Promise(resolve => {
        const tx = db.transaction('music', 'readwrite');
        tx.objectStore('music').put(record, 'track');
        tx.oncomplete = () => resolve(true); tx.onerror = () => resolve(false); tx.onabort = () => resolve(false);
      });
    },
    get() {
      return this.open().then(db => db ? new Promise(resolve => {
        const tx = db.transaction('music', 'readonly');
        const req = tx.objectStore('music').get('track');
        req.onsuccess = () => resolve(req.result || null); req.onerror = () => resolve(null);
      }) : null);
    },
    async clear() {
      const db = await this.open();
      if (!db) return;
      await new Promise(resolve => { const tx = db.transaction('music', 'readwrite'); tx.objectStore('music').delete('track'); tx.oncomplete = resolve; tx.onerror = resolve; });
    }
  };
  let musicBuffer = null, musicName = '';
  let previewing = false, previewTimer = null;
  function stopMusic() { if (AudioFX.musicSource) { try { AudioFX.musicSource.stop(); } catch (_) {} AudioFX.musicSource = null; } }
  function playMusicBuffer() {
    AudioFX.ensure(); stopMusic();
    if (!AudioFX.ctx || !musicBuffer) return;
    const src = AudioFX.ctx.createBufferSource();
    src.buffer = musicBuffer; src.loop = true; src.connect(AudioFX.musicGain);
    src.start(); AudioFX.musicSource = src;
  }
  async function onMusicFile(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    if (file.size > 15 * 1024 * 1024) notify('文件超过 15MB，可能无法保存，仅本次会话有效。');
    try {
      AudioFX.ensure();
      if (!AudioFX.ctx) throw new Error('no audio');
      const raw = await file.arrayBuffer();
      musicBuffer = await AudioFX.ctx.decodeAudioData(raw.slice(0));
      musicName = file.name;
      const stored = await MusicStore.put({ name: file.name, buf: raw });
      if (!stored) notify('本机存储不可用，音乐仅本次会话有效。');
      previewing = false; $('musicPreviewBtn').textContent = '试听';
      renderSettingsControls();
      if (settings.musicOn) playMusicBuffer();
      notify(`已导入音乐「${file.name}」。`);
    } catch (_) { notify('无法解码该音频文件，请换一个试试。'); }
  }
  function toggleMusicPreview() {
    if (!musicBuffer) return notify('请先导入音乐文件。');
    if (previewing) { stopMusic(); previewing = false; $('musicPreviewBtn').textContent = '试听'; return; }
    AudioFX.ensure(); stopMusic();
    if (!AudioFX.ctx) return;
    const src = AudioFX.ctx.createBufferSource();
    src.buffer = musicBuffer; src.connect(AudioFX.musicGain); src.start();
    AudioFX.musicSource = src;
    previewing = true; $('musicPreviewBtn').textContent = '停止';
    clearTimeout(previewTimer);
    previewTimer = setTimeout(() => { if (previewing) { stopMusic(); previewing = false; $('musicPreviewBtn').textContent = '试听'; } }, 12000);
  }
  async function clearMusic() {
    stopMusic(); previewing = false; $('musicPreviewBtn').textContent = '试听';
    musicBuffer = null; musicName = '';
    await MusicStore.clear();
    renderSettingsControls(); notify('已清除导入的音乐。');
  }

  /* ===== v3：新闻（跑马灯 + 滑入卡 + 新闻中心） ===== */
  const NEWS_FREQ_TICKS = { low: [80, 160], mid: [24, 44], high: [10, 20] };
  let newsFeed = [];
  let newsFloatQueue = [], newsFloatActive = false, newsFloatTimer = null;
  function updateTickerVisibility() { $('newsTicker').classList.toggle('hidden', !settings.newsOn); }
  function renderTicker() {
    updateTickerVisibility();
    if (!settings.newsOn) return;
    const track = $('tickerTrack');
    const latest = newsFeed[0];
    track.textContent = latest ? `【${latest.tag}】${latest.title} —— ${latest.body}` : '等待市场消息…';
    track.classList.toggle('flat', !latest);
    track.style.animation = 'none'; void track.offsetWidth; track.style.animation = '';
  }
  function queueNewsFloat(item) {
    if (!item.ach && !settings.newsOn) return;
    newsFloatQueue.push(item);
    if (!newsFloatActive) showNextNewsFloat();
  }
  function showNextNewsFloat() {
    const item = newsFloatQueue.shift();
    if (!item) { newsFloatActive = false; return; }
    newsFloatActive = true;
    $('nfTag').textContent = item.tag;
    $('nfTag').classList.toggle('ach', !!item.ach);
    $('nfTitle').textContent = item.title;
    $('nfBody').textContent = item.body;
    $('nfDate').textContent = item.date || '';
    $('newsFloat').classList.add('show');
    clearTimeout(newsFloatTimer);
    newsFloatTimer = setTimeout(() => { $('newsFloat').classList.remove('show'); setTimeout(showNextNewsFloat, 320); }, 6200);
  }
  function dismissNewsFloat() {
    clearTimeout(newsFloatTimer);
    $('newsFloat').classList.remove('show');
    setTimeout(showNextNewsFloat, 320);
  }
  function pushNews(item) {
    if (!settings.newsOn) return;
    newsFeed.unshift({ ...item, ts: Date.now() });
    newsFeed = newsFeed.slice(0, 40);
    renderTicker(); queueNewsFloat(item); AudioFX.news();
  }
  function renderNewsCenter() {
    const list = $('newsCenterList'); list.replaceChildren();
    if (!newsFeed.length) { list.innerHTML = '<div class="empty-state">还没有收到快讯</div>'; return; }
    newsFeed.forEach(item => {
      const row = document.createElement('div'); row.className = 'news-center-item';
      row.innerHTML = `<span class="nf-tag${item.ach ? ' ach' : ''}"></span><h4></h4><p></p><span class="nf-date"></span>`;
      row.querySelector('.nf-tag').textContent = item.tag;
      row.querySelector('h4').textContent = item.title;
      row.querySelector('p').textContent = item.body;
      row.querySelector('.nf-date').textContent = item.date || '';
      list.append(row);
    });
  }

  /* ===== v3：成就系统 ===== */
  const ACHIEVEMENTS = [
    { id: 'fx-simple', name: 'fx，简单！', desc: '账户权益比初始资金多出 $100,000（浮盈也算）。', hint: '让权益比 $10,000 高出十万' },
    { id: 'buy-top', name: '现在买入，一定爆赚', desc: '在近 40 根 K 线的最高点附近开多。', hint: '在近期最高价 0.2% 范围内做多' },
    { id: 'finger-support', name: '手指支撑线', desc: '借款补仓救过的仓位，最终还是爆仓了。', hint: '借款补仓后仍被强制平仓' },
    { id: 'never-sell', name: '不卖就不算亏', desc: '单笔仓位持续浮亏很久仍不平仓（模拟 8 分钟 / 回放 30 个交易日）。', hint: '长时间抱着亏损单不撒手' },
    { id: 'just-kill-me', name: '杀就杀吧', desc: '风险提醒弹窗选了"暂不处理"，随后爆仓。', hint: '拒绝补仓，直到爆仓' },
    { id: 'killed-by-chf', name: '被瑞士杀死了', desc: '在瑞郎脱钩战役里亲历 2015-01-15 事件日。', hint: '推进瑞郎脱钩战役到事件日' },
    { id: 'innocent-cat', name: '本喵明明没做坏事', desc: '第一次被强制平仓。', hint: '经历一次爆仓' },
    { id: 'sorry-family', name: '最对不起的就是家人', desc: '贷款本金达到 $100,000。', hint: '一次性借入十万' },
    { id: 'sure-win', name: '我有必胜法', desc: '账户权益比初始资金多出 $1,000,000。', hint: '收益达到一百万' },
    { id: 'honest-work', name: '老实赚钱，很枯燥吧', desc: '完成第一次盈利平仓。', hint: '盈利平仓一次' },
    { id: 'rooftop', name: '天台见', desc: '账户权益比初始资金少了 $100,000。', hint: '权益比 $10,000 低十万' },
    { id: 'thanks-meow', name: '感谢支持喵', desc: '关注 UP 主 -会飞的蝈蝈-。', hint: '点击"去关注"并完成关注', follow: true }
  ];
  let achievements = (() => { try { return { unlocked: (JSON.parse(localStorage.getItem('fx-achievements-v1') || 'null')?.unlocked) || {} }; } catch (_) { return { unlocked: {} }; } })();
  let achCloudTimer = null, pendingFollowCheck = false;
  function persistAchievements() {
    try { localStorage.setItem('fx-achievements-v1', JSON.stringify(achievements)); } catch (_) {}
    clearTimeout(achCloudTimer);
    achCloudTimer = setTimeout(async () => {
      if (!(await toySupports('setCloudStorage'))) return;
      try { await toyCallWithBackoff(() => window.toy.setCloudStorage({ fx_achievements: JSON.stringify({ v: 1, u: achievements.unlocked }) })); } catch (_) {}
    }, 800);
  }
  function unlockAchievement(id) {
    const def = ACHIEVEMENTS.find(a => a.id === id);
    if (!def || achievements.unlocked[id]) return;
    achievements.unlocked[id] = new Date().toISOString().slice(0, 10);
    persistAchievements();
    AudioFX.achieve();
    queueNewsFloat({ tag: '成就', title: `达成「${def.name}」`, body: def.desc, date: '成就解锁', ach: true });
    notify(`🏆 达成成就「${def.name}」`);
    if (!$('achModal').classList.contains('hidden')) renderAchBook();
  }
  function checkEquityAchievements() {
    const profit = account().equity - 10000;
    if (profit >= 100000) unlockAchievement('fx-simple');
    if (profit >= 1000000) unlockAchievement('sure-win');
    if (profit <= -100000) unlockAchievement('rooftop');
  }
  async function checkFollowRelation() {
    if (achievements.unlocked['thanks-meow']) return true;
    if (!(await toySupports('getAuthorRelation'))) return false;
    try {
      const rel = await toyCallWithBackoff(() => window.toy.getAuthorRelation());
      if (rel?.status === 'ok' && rel.data?.isFollowing) { unlockAchievement('thanks-meow'); return true; }
    } catch (_) {}
    return false;
  }
  async function loadAchievementsCloud() {
    if (!(await toySupports('getCloudStorage'))) return;
    try {
      const cloud = await toyCallWithBackoff(() => window.toy.getCloudStorage(['fx_achievements']));
      const parsed = cloud?.fx_achievements ? JSON.parse(cloud.fx_achievements) : null;
      if (parsed?.u) {
        Object.entries(parsed.u).forEach(([id, ts]) => { if (!achievements.unlocked[id] || achievements.unlocked[id] > ts) achievements.unlocked[id] = ts; });
        persistAchievements();
        if (!$('achModal').classList.contains('hidden')) renderAchBook();
      }
    } catch (_) {}
  }
  function renderAchBook() {
    const grid = $('achGrid'); grid.replaceChildren();
    const unlockedCount = ACHIEVEMENTS.filter(a => achievements.unlocked[a.id]).length;
    $('achProgressLine').textContent = `已解锁 ${unlockedCount} / ${ACHIEVEMENTS.length}`;
    ACHIEVEMENTS.forEach(def => {
      const ts = achievements.unlocked[def.id];
      const card = document.createElement('div');
      card.className = 'ach-card' + (ts ? ' unlocked' : ' locked');
      if (ts) {
        card.innerHTML = `<span class="ach-medal">🏅</span><span class="ach-name"></span><span class="ach-desc"></span><span class="ach-date"></span>`;
        card.querySelector('.ach-name').textContent = def.name;
        card.querySelector('.ach-desc').textContent = def.desc;
        card.querySelector('.ach-date').textContent = ts;
      } else {
        card.innerHTML = `<span class="ach-medal">❔</span><span class="ach-name">？？？</span><span class="ach-desc"></span>`;
        card.querySelector('.ach-desc').textContent = def.hint;
        if (def.follow) {
          const btn = document.createElement('button');
          btn.type = 'button'; btn.className = 'ach-follow-btn';
          btn.textContent = window.toy ? '去关注 UP 主' : '去 B站主页关注';
          btn.addEventListener('click', async () => {
            if (window.toy && typeof window.toy.navigate === 'function') {
              try { await Promise.resolve(window.toy.navigate({ type: 'space', id: '443211651' })); pendingFollowCheck = true; return; } catch (_) {}
            }
            window.open('https://space.bilibili.com/443211651', '_blank', 'noopener');
            if (!window.toy) unlockAchievement('thanks-meow');
            else { pendingFollowCheck = true; setTimeout(() => { checkFollowRelation().finally(() => { pendingFollowCheck = false; }); }, 3000); }
          });
          card.append(btn);
        }
      }
      grid.append(card);
    });
  }

  /* ===== v3：战绩分享卡 ===== */
  let shareDataUrl = null;
  function rr(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      if (!src.startsWith('data:')) img.crossOrigin = 'anonymous';
      img.onload = () => resolve(img); img.onerror = reject; img.src = src;
    });
  }
  function loadImageWithTimeout(src, ms = 3000) { return Promise.race([loadImage(src), new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms))]); }
  async function buildShareCard(noAvatar = false) {
    const W = 1080, H = 1440;
    const canvas = document.createElement('canvas'); canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext('2d');
    const night = settings.theme === 'night';
    const T = night ? { bg0: '#13292d', bg1: '#0a1719', ink: '#eef8f2', sub: '#93b8ab', card: '#15282c' } : { bg0: '#eaf6ef', bg1: '#cfe9dc', ink: '#173d3a', sub: '#5f827b', card: '#ffffff' };
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, T.bg0); grad.addColorStop(1, T.bg1);
    ctx.fillStyle = grad; ctx.fillRect(0, 0, W, H);
    const upColor = night ? '#57cf9b' : '#2f9c76', downColor = night ? '#ef8ba0' : '#e06e81';
    if (!noAvatar) {
      try {
        const avatar = await loadImageWithTimeout('./assets/kurumi-avatar.jpg');
        ctx.save(); rr(ctx, 72, 64, 108, 108, 30); ctx.clip(); ctx.drawImage(avatar, 72, 64, 108, 108); ctx.restore();
      } catch (_) {
        ctx.fillStyle = night ? '#1c4434' : '#dff2e8';
        rr(ctx, 72, 64, 108, 108, 30); ctx.fill();
        ctx.fillStyle = night ? '#67d3a0' : '#4f8e74'; ctx.font = '900 52px Nunito, "Microsoft YaHei", sans-serif'; ctx.textAlign = 'center';
        ctx.fillText('♡', 126, 136); ctx.textAlign = 'left';
      }
    }
    ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
    ctx.fillStyle = T.ink; ctx.font = '900 62px Nunito, "Microsoft YaHei", sans-serif';
    ctx.fillText('FX 简单!', 208, 126);
    ctx.fillStyle = T.sub; ctx.font = '800 26px Nunito, "Microsoft YaHei", sans-serif';
    ctx.fillText('-会飞的蝈蝈- 的外汇交易室', 210, 168);
    const modeName = state.mode === 'real' ? '真实历史数据' : state.mode === 'battle' ? '经典战役' : state.mode === 'challenge' ? '每日挑战' : '模拟行情';
    ctx.fillStyle = T.card; rr(ctx, 72, 224, 372, 56, 28); ctx.fill();
    ctx.fillStyle = T.sub; ctx.font = '800 24px Nunito, "Microsoft YaHei", sans-serif';
    ctx.fillText(`当前模式 · ${modeName}`, 102, 261);
    const a = account(); const profit = a.equity - 10000;
    ctx.fillStyle = T.ink; ctx.font = '900 40px Nunito, "Microsoft YaHei", sans-serif';
    ctx.fillText('账户总权益', 74, 366);
    ctx.font = '900 104px Nunito, "Microsoft YaHei", sans-serif';
    ctx.fillText(money(a.equity), 66, 474);
    ctx.fillStyle = profit >= 0 ? upColor : downColor; ctx.font = '900 46px Nunito, "Microsoft YaHei", sans-serif';
    ctx.fillText(`累计收益 ${signedMoney(profit)}`, 70, 552);
    const wins = state.history.filter(h => h.pnl > 0).length, total = state.history.length;
    const winRate = total ? Math.round(wins / total * 100) : 0;
    const achCount = ACHIEVEMENTS.filter(x => achievements.unlocked[x.id]).length;
    ctx.fillStyle = T.card; rr(ctx, 72, 606, 936, 128, 32); ctx.fill();
    ctx.font = '800 22px Nunito, "Microsoft YaHei", sans-serif'; ctx.fillStyle = T.sub;
    ctx.fillText('近 25 笔胜率', 128, 656); ctx.fillText('成就进度', 452, 656); ctx.fillText('交易笔数', 748, 656);
    ctx.font = '900 40px "DM Mono", monospace'; ctx.fillStyle = T.ink;
    ctx.fillText(`${winRate}%`, 128, 708); ctx.fillText(`${achCount} / ${ACHIEVEMENTS.length}`, 452, 708); ctx.fillText(`${total}`, 748, 708);
    ctx.fillStyle = T.card; rr(ctx, 72, 766, 936, 320, 32); ctx.fill();
    const trail = Array.isArray(state.equityTrail) ? state.equityTrail : [];
    if (trail.length >= 2) {
      const min = Math.min(...trail), max = Math.max(...trail), span = (max - min) || 1;
      ctx.strokeStyle = profit >= 0 ? upColor : downColor; ctx.lineWidth = 6; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.beginPath();
      trail.forEach((v, i) => { const x = 112 + i / (trail.length - 1) * 856; const y = 806 + (1 - (v - min) / span) * 240; if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); });
      ctx.stroke();
    } else {
      ctx.fillStyle = T.sub; ctx.font = '800 28px Nunito, "Microsoft YaHei", sans-serif';
      ctx.fillText('继续交易，这里会生成你的权益曲线', 112, 940);
    }
    let qrImg = null;
    if (await toySupports('getQrCode')) {
      try {
        const qr = await Promise.race([
          toyCallWithBackoff(() => window.toy.getQrCode({ size: 300 })),
          new Promise((_, reject) => setTimeout(() => reject(new Error('qr-timeout')), 4000))
        ]);
        if (qr?.base64) qrImg = await loadImage(qr.base64).catch(() => null);
      } catch (_) {}
    }
    if (qrImg) {
      const qs = 230;
      ctx.fillStyle = T.sub; ctx.font = '800 24px Nunito, "Microsoft YaHei", sans-serif';
      ctx.fillText('扫码打开游戏', W - 72 - qs + 30, H - 72 - qs - 16);
      ctx.drawImage(qrImg, W - 72 - qs, H - 72 - qs, qs, qs);
    }
    ctx.fillStyle = T.ink; ctx.font = '900 30px Nunito, "Microsoft YaHei", sans-serif';
    ctx.fillText('B站搜索：-会飞的蝈蝈-', 72, H - 148);
    ctx.fillStyle = T.sub; ctx.font = '700 22px Nunito, "Microsoft YaHei", sans-serif';
    ctx.fillText('模拟交易游戏 · 盈亏与数据仅供娱乐，不涉及真实资金', 72, H - 102);
    return canvas.toDataURL('image/jpeg', .87);
  }
  async function openShare() {
    try {
      $('shareModal').classList.remove('hidden');
      $('sharePlaceholder').textContent = '正在生成战绩卡…';
      $('sharePlaceholder').classList.remove('hidden');
      $('shareImg').classList.add('hidden');
      const canSave = await toySupports('saveImageToAlbum');
      const canShareLink = await toySupports('share');
      $('shareSaveBtn').classList.toggle('hidden', !canSave);
      $('shareDownloadBtn').classList.toggle('hidden', canSave);
      $('shareLinkBtn').classList.toggle('hidden', !canShareLink);
      shareDataUrl = null;
      try {
        shareDataUrl = await buildShareCard();
      } catch (avatarError) {
        // 头像把画布污染（file:// 或跨域）时，改用无头像版重画
        shareDataUrl = await buildShareCard(true);
      }
      $('shareImg').src = shareDataUrl;
      $('sharePlaceholder').classList.add('hidden'); $('shareImg').classList.remove('hidden');
    } catch (error) {
      console.error('share card failed:', error);
      $('sharePlaceholder').textContent = '生成失败，请关闭后重试';
      notify('战绩卡生成失败，请重试。');
    }
  }

  /* ===== v3：回放 K 线构造（日度参考价 → 蜡烛，影线为示意） ===== */
  function hashSeed(str) { let h = 2166136261; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return ((h >>> 0) % 1000) / 1000; }
  function isoWeekKey(dateStr) { const d = new Date(`${dateStr}T00:00:00Z`); const day = (d.getUTCDay() + 6) % 7; d.setUTCDate(d.getUTCDate() - day); return d.toISOString().slice(0, 10); }
  function candleFromRows(rows, pair, tf) {
    const out = [];
    let open = rows.length ? rows[0].prices[pair] : NaN;
    let group = null;
    const pushCandle = c => {
      if (!c || !Number.isFinite(c.open) || !Number.isFinite(c.close)) return;
      const wick = Math.abs(c.close) * (.00035 + hashSeed(c.key || c.date || '') * .00095);
      out.push({ open: c.open, close: c.close, high: Math.max(c.open, c.close) + wick, low: Math.min(c.open, c.close) - wick, date: c.date });
    };
    rows.forEach(row => {
      const price = row.prices[pair];
      if (!Number.isFinite(price)) return;
      if (tf === '1w' || tf === '1M') {
        const key = tf === '1w' ? isoWeekKey(row.date) : row.date.slice(0, 7);
        if (!group || group.key !== key) { if (group) pushCandle(group); group = { key, open, close: price, date: row.date }; }
        else group.close = price;
      } else pushCandle({ open, close: price, date: row.date });
      open = price;
    });
    if (group) pushCandle(group);
    return out;
  }

  /* ===== v3：真实数据区间（≤600 天） ===== */
  const REAL_MAX_SPAN = 600;
  function defaultRealRange() { const end = new Date(); const start = new Date(); start.setUTCDate(start.getUTCDate() - 364); return { start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10) }; }
  const realRangeKey = range => `${range.start}~${range.end}`;
  function normalizeRealRange(range) {
    let { start, end } = range || {};
    if (!/^\d{4}-\d{2}-\d{2}$/.test(start) || !/^\d{4}-\d{2}-\d{2}$/.test(end)) return null;
    if (start > end) [start, end] = [end, start];
    const days = Math.round((Date.parse(end) - Date.parse(start)) / 86400000) + 1;
    if (days > REAL_MAX_SPAN) {
      start = new Date(Date.parse(end) - (REAL_MAX_SPAN - 1) * 86400000).toISOString().slice(0, 10);
      notify(`区间超出 600 天，已调整为 ${start} → ${end}。`);
    }
    return { start, end };
  }
  async function applyRealRange(range) {
    const normalized = normalizeRealRange(range);
    if (!normalized) return notify('请选择有效的起止日期。');
    if (state.positions.length) return notify('真实数据账户仍有持仓，请先平仓再更换区间。');
    autoPlay = false;
    const ok = await loadReal(normalized);
    if (ok) { save(); render(); notify(`已载入 ${real.items.length} 个交易日（${normalized.start} → ${normalized.end}）。`); }
    else render();
  }

  function normalizeAccount() {
    state.positions = Array.isArray(state.positions) ? state.positions : [];
    state.history = Array.isArray(state.history) ? state.history : [];
    state.equityTrail = Array.isArray(state.equityTrail) ? state.equityTrail : [];
    state.realProgress = state.realProgress && typeof state.realProgress === 'object' ? state.realProgress : {};
    state.positions.forEach(pos => { pos.notional = Number.isFinite(pos.notional) ? pos.notional : pos.margin * pos.leverage; pos.warned = false; });
  }
  function accountSnapshot() {
    return { cash: state.cash, debt: state.debt, loanPrincipal: state.loanPrincipal, loanRate: state.loanRate, simLoanTicks: state.simLoanTicks, positions: state.positions, history: state.history.slice(0, 25), pair: state.pair, leverage: state.leverage, margin: state.margin, feesPaid: state.feesPaid || 0, battleId: state.battleId, lastRealDate: state.lastRealDate, lastBattleDate: state.lastBattleDate, equityTrail: state.equityTrail, realProgress: state.realProgress, realRangeKey: state.realRangeKey, realRange: state.realRange };
  }
  function activateMode(mode) {
    if (state.mode === mode) return;
    modeAccounts[state.mode] = accountSnapshot();
    const stored = modeAccounts[mode];
    state = { ...initialState(mode), ...(stored || {}), mode };
    if (!PAIRS.some(pair => pair.id === state.pair)) state.pair = 'EUR/USD';
    normalizeAccount();
  }
  function save() {
    modeAccounts[state.mode] = accountSnapshot();
    try { localStorage.setItem('fx-heartbeat-save-v3', JSON.stringify({ mode: state.mode, accounts: modeAccounts, sim })); } catch (_) {}
  }
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  async function toySupports(name) {
    if (supportCache.has(name)) return supportCache.get(name);
    if (!window.toy) { supportCache.set(name, false); return false; }
    try {
      const supported = await Promise.race([window.toy.isSupport(name), wait(1500).then(() => false)]);
      supportCache.set(name, !!supported); return !!supported;
    } catch (_) { supportCache.set(name, false); return false; }
  }
  async function toyCallWithBackoff(action, attempt = 0) {
    try { return await action(); }
    catch (error) {
      if (error?.code === 307044 && attempt < 2) { await wait(900 * 2 ** attempt); return toyCallWithBackoff(action, attempt + 1); }
      throw error;
    }
  }
  function compactChallengeState() {
    return {
      c: Math.round(state.cash * 100) / 100,
      p: state.positions.slice(0, 5).map(pos => [pos.pair, pos.side, pos.entry, pos.margin, pos.leverage, pos.notional, pos.fee || 0]),
      q: state.pair, l: state.leverage, m: state.margin,
      r: PAIRS.map(pair => Math.round((challengeSim[pair.id]?.price || pair.initial) * 100000) / 100000)
    };
  }
  function hydrateChallengeState(data) {
    if (!data || !Number.isFinite(data.c)) return;
    const restored = initialState('challenge');
    restored.cash = data.c;
    restored.pair = PAIRS.some(pair => pair.id === data.q) ? data.q : 'EUR/USD';
    restored.leverage = Math.max(1, Math.min(100, Number(data.l) || 20));
    restored.margin = Math.max(10, Number(data.m) || 500);
    restored.positions = Array.isArray(data.p) ? data.p.slice(0, 5).map((pos, index) => ({ id: `challenge-${Date.now()}-${index}`, pair: pos[0], side: pos[1], entry: pos[2], margin: pos[3], leverage: pos[4], notional: pos[5], fee: pos[6] || 0, warned: false, opened: '云存档恢复' })).filter(pos => PAIRS.some(pair => pair.id === pos.pair) && Number.isFinite(pos.entry)) : [];
    modeAccounts.challenge = { ...restored };
    if (state.mode === 'challenge') state = { ...restored };
    challengeSim = {}; seedChallengeSim();
    if (Array.isArray(data.r)) PAIRS.forEach((pair, index) => {
      const price = Number(data.r[index]);
      if (!Number.isFinite(price) || price <= 0) return;
      const series = challengeSim[pair.id]; const last = series.candles.at(-1);
      last.close = price; last.high = Math.max(last.high, price); last.low = Math.min(last.low, price); series.price = price;
    });
  }
  function saveChallengeLocal() {
    try {
      localStorage.setItem('fx-challenge-meta-v1', JSON.stringify({ date: challenge.date, remaining: challenge.remaining, active: challenge.active }));
      if (challenge.active && state.mode === 'challenge') localStorage.setItem('fx-challenge-state-v1', JSON.stringify(compactChallengeState()));
      else if (!challenge.active) localStorage.removeItem('fx-challenge-state-v1');
    } catch (_) {}
  }
  async function saveChallengeCloud(showFailure = false) {
    saveChallengeLocal();
    if (!challenge.loaded || challenge.saving || !(await toySupports('setCloudStorage'))) return;
    challenge.saving = true;
    const items = { fx_challenge_meta: JSON.stringify({ d: challenge.date, r: challenge.remaining, a: challenge.active ? 1 : 0 }) };
    if (challenge.active && state.mode === 'challenge') items.fx_challenge_state = JSON.stringify(compactChallengeState());
    else items.fx_challenge_state = '';
    try { await toyCallWithBackoff(() => window.toy.setCloudStorage(items)); }
    catch (error) { if (showFailure) notify(error?.code === 307044 ? '云存档请求较多，请稍后再试。' : '云存档失败，本机进度仍已保存。'); }
    finally { challenge.saving = false; }
  }
  function scheduleChallengeSave() {
    if (state.mode !== 'challenge' || !challenge.active) return;
    clearTimeout(challengeSaveTimer);
    challengeSaveTimer = setTimeout(() => saveChallengeCloud(false), 700);
  }
  async function loadChallengeProgress() {
    if (challenge.loaded || challenge.loading) return;
    challenge.loading = true;
    let meta = null, savedState = null;
    try { meta = JSON.parse(localStorage.getItem('fx-challenge-meta-v1') || 'null'); savedState = JSON.parse(localStorage.getItem('fx-challenge-state-v1') || 'null'); } catch (_) {}
    if (await toySupports('getCloudStorage')) {
      try {
        const cloud = await toyCallWithBackoff(() => window.toy.getCloudStorage(['fx_challenge_meta', 'fx_challenge_state']));
        if (cloud.fx_challenge_meta) { const value = JSON.parse(cloud.fx_challenge_meta); meta = { date: value.d, remaining: value.r, active: !!value.a }; }
        if (cloud.fx_challenge_state) savedState = JSON.parse(cloud.fx_challenge_state);
      } catch (error) { notify(error?.code === 307044 ? '挑战记录读取繁忙，已使用本机记录。' : '云端挑战记录暂时不可用，已使用本机记录。'); }
    }
    if (meta?.date === todayKey()) {
      challenge.date = meta.date; challenge.remaining = Math.max(0, Math.min(3, Number(meta.remaining) || 0)); challenge.active = !!meta.active;
      if (challenge.active && savedState) hydrateChallengeState(savedState);
    } else {
      challenge = { ...challenge, date: todayKey(), remaining: 3, active: false };
      modeAccounts.challenge = null;
      if (state.mode === 'challenge') state = initialState('challenge');
    }
    challenge.loaded = true; challenge.loading = false; saveChallengeLocal();
  }
  function seedMarket(target, restoreSaved = false) {
    if (restoreSaved && savedSim) { sim = savedSim; savedSim = null; }
    PAIRS.forEach((pair, index) => {
      if (target[pair.id]) return;
      let value = pair.initial;
      const candles = [];
      for (let i = 0; i < 76; i++) {
        const open = value;
        const wave = Math.sin(i * .43 + index * 1.9) * .0008 + Math.cos(i * .19 + index) * .00055;
        value = open * (1 + wave + (Math.random() - .5) * .0019);
        const spread = open * (.0005 + Math.random() * .00065);
        candles.push({ open, high: Math.max(open, value) + spread, low: Math.min(open, value) - spread, close: value });
      }
      target[pair.id] = { candles, price: value };
    });
  }
  function seedSim() { seedMarket(sim, true); }
  function seedChallengeSim() { seedMarket(challengeSim); }
  seedSim(); seedChallengeSim();
  function currentPrice(pair) {
    if (state.mode === 'real') return real.items[real.cursor]?.prices[pair] ?? NaN;
    if (state.mode === 'battle') return battle.items[battle.cursor]?.prices[pair] ?? NaN;
    return (state.mode === 'challenge' ? challengeSim : sim)[pair]?.price ?? NaN;
  }
  function previousPrice(pair) {
    if (state.mode === 'real') return real.items[Math.max(0, real.cursor - 1)]?.prices[pair] ?? currentPrice(pair);
    if (state.mode === 'battle') return battle.items[Math.max(0, battle.cursor - 1)]?.prices[pair] ?? currentPrice(pair);
    const candles = (state.mode === 'challenge' ? challengeSim : sim)[pair]?.candles || [];
    return candles.at(-2)?.close ?? currentPrice(pair);
  }
  function positionPnl(pos) {
    const price = currentPrice(pos.pair);
    if (!Number.isFinite(price)) return 0;
    return pos.notional * pos.side * (price / pos.entry - 1);
  }
  function account() {
    const used = state.positions.reduce((sum, p) => sum + p.margin, 0);
    const floating = state.positions.reduce((sum, p) => sum + positionPnl(p), 0);
    return { used, floating, equity: state.cash + used + floating - state.debt };
  }
  function accrueLoanInterest() {
    if (state.debt <= 0) return;
    state.debt = Math.round((state.debt + Math.round(state.debt * state.loanRate * 100) / 100) * 100) / 100;
  }
  function borrowLoan(amount, position = null) {
    if (!Number.isFinite(amount) || amount < 1 || amount > LOAN_MAX || state.debt > 0) return false;
    state.debt = amount;
    state.loanPrincipal = amount;
    state.loanRate = loanDailyRate(amount);
    state.simLoanTicks = 0;
    if (position) position.margin += amount;
    else state.cash += amount;
    if (state.loanPrincipal >= 100000) unlockAchievement('sorry-family');
    return true;
  }
  function updateLoanQuote() {
    if (!loanQuoteActive) return;
    const amount = Number($('modalInput').value);
    if (!Number.isFinite(amount) || amount < 1 || amount > LOAN_MAX) { $('modalDetail').textContent = `请输入 $1–${money(LOAN_MAX)}。`; return; }
    const rate = loanDailyRate(amount);
    $('modalDetail').textContent = `日利率 ${rateText(rate)} · 每交易日约 ${money(Math.round(amount * rate * 100) / 100)} 利息`;
  }
  function notify(message) {
    const toast = $('toast'); toast.textContent = message; toast.classList.add('show');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove('show'), 3300);
  }
  function openModal(options) {
    if (modalOpen) { modalQueue.push(options); return; }
    modalOpen = true;
    modalAction = options.action || null;
    riskPositionId = options.riskPositionId || null;
    loanQuoteActive = !!options.loanQuote;
    $('modalIcon').textContent = options.icon || '✦';
    $('modalIcon').classList.toggle('loss', !!options.loss);
    $('modalTitle').textContent = options.title;
    $('modalMessage').textContent = options.message || '';
    $('modalDetail').textContent = options.detail || '';
    $('modalDetail').classList.toggle('preline', !!options.preline);
    $('modalInputWrap').classList.toggle('hidden', !options.input);
    $('modalInputLabel').textContent = options.input?.label || '';
    $('modalInput').value = options.input?.value ?? '';
    $('modalInput').min = options.input?.min ?? 1;
    $('modalInput').max = options.input?.max ?? '';
    $('modalInput').step = options.input?.step ?? 1;
    $('modalConfirm').textContent = options.confirm || '知道了';
    $('modalCancel').classList.toggle('hidden', !options.action);
    $('modalRiskActions').classList.toggle('hidden', !options.riskPositionId);
    $('addMarginBtn').disabled = !options.riskPositionId || state.cash < 1;
    $('loanMarginBtn').disabled = !options.riskPositionId || state.debt > 0;
    $('modal').classList.remove('hidden');
    updateLoanQuote();
    if (options.input) setTimeout(() => $('modalInput').focus(), 30);
    else setTimeout(() => $('modalConfirm').focus(), 30);
  }
  function closeModal() {
    const finishingRiskId = riskPositionId;
    $('modal').classList.add('hidden'); modalOpen = false; modalAction = null;
    riskPositionId = null;
    loanQuoteActive = false;
    if (finishingRiskId) {
      riskPaused = false;
      const pos = state.positions.find(p => p.id === finishingRiskId);
      if (pos && !marginHelpDone) pos.refusedHelp = true;
      marginHelpDone = false;
      if (pos && riskRatio(pos) >= .8) closePosition(pos.id, true);
      else checkLiquidations();
      renderChartHeader();
    }
    if (modalQueue.length) setTimeout(() => openModal(modalQueue.shift()), 70);
  }
  function renderPairs() {
    const list = $('pairList'); list.replaceChildren();
    PAIRS.forEach(pair => {
      const rate = currentPrice(pair.id);
      const change = (rate / previousPrice(pair.id) - 1) * 100;
      const row = document.createElement('button'); row.type = 'button'; row.className = 'pair-row' + (state.pair === pair.id ? ' selected' : '');
      row.disabled = state.mode === 'battle' && pair.id !== state.pair;
      row.setAttribute('role', 'option'); row.setAttribute('aria-selected', String(state.pair === pair.id));
      row.innerHTML = `<span><strong>${pair.id}</strong><small>${pair.name}</small></span><span class="pair-numbers"><strong>${priceText(pair.id, rate)}</strong><small class="${change >= 0 ? 'positive' : 'negative'}">${pct(Number.isFinite(change) ? change : 0)}</small></span>`;
      row.addEventListener('click', () => { state.pair = pair.id; save(); render(); });
      list.append(row);
    });
    const mobile = $('mobilePairSelect');
    if (!mobile.options.length) PAIRS.forEach(pair => mobile.add(new Option(`${pair.id} · ${pair.name}`, pair.id)));
    mobile.value = state.pair;
    mobile.disabled = state.mode === 'battle';
  }
  function renderAccount() {
    const a = account();
    const modeName = state.mode === 'real' ? '真实数据账户' : state.mode === 'battle' ? '经典战役账户' : state.mode === 'challenge' ? '每日挑战账户' : '模拟数据账户';
    $('accountModeName').textContent = modeName;
    $('sessionLabel').textContent = modeName.replace('数据', '').replace('每日', '');
    $('equity').textContent = money(a.equity);
    $('cash').textContent = money(state.cash);
    $('floating').textContent = signedMoney(a.floating);
    $('floating').className = a.floating >= 0 ? 'positive' : 'negative';
    $('usedMargin').textContent = money(a.used);
    $('debt').textContent = money(state.debt);
    $('loanInfo').textContent = state.debt > 0
      ? `借款 ${money(state.loanPrincipal)} · 日利率 ${rateText(state.loanRate)} · 待还 ${money(state.debt)}。每交易日计息；模拟数据每 30 秒计一天。还清后可再次借入。`
      : '最多借 $200,000。日利率按金额分级：≤$10,000 为 0.01%，≤$50,000 为 0.02%，≤$100,000 为 0.03%，以上为 0.04%。模拟数据每 30 秒计一天。';
    $('borrowBtn').disabled = state.mode === 'challenge';
    $('repayBtn').disabled = state.mode === 'challenge' || state.debt <= 0;
    if (state.mode === 'challenge') $('loanInfo').textContent = '挑战模式不开放贷款，所有成绩只使用初始 $10,000 本金。';
  }
  function renderOrder() {
    $('orderPair').textContent = state.pair;
    $('marginInput').value = state.margin;
    $('leverageRange').value = state.leverage;
    $('leverageRange').style.setProperty('--progress', `${(state.leverage - 1) / 99 * 100}%`);
    $('leverageValue').textContent = `${state.leverage}×`;
    $('notional').textContent = money(state.margin * state.leverage);
    $('tradeFee').textContent = money(tradeFee(state.margin, state.leverage));
    $('riskPercent').textContent = `${(80 / state.leverage).toFixed(2)}%`;
  }
  function renderPositions() {
    $('positionCount').textContent = state.positions.length;
    $('riskHint').textContent = state.positions.length ? `合计 ${money(account().used)} 保证金` : '暂无持仓';
    const root = $('positions'); root.replaceChildren();
    if (!state.positions.length) { root.innerHTML = '<div class="empty-state"><div class="empty-icon">♡</div>还没有持仓，选一个货币对开始吧</div>'; return; }
    state.positions.forEach(pos => {
      const pnl = positionPnl(pos);
      const row = document.createElement('div'); row.className = 'position-row';
      row.innerHTML = `<div class="pos-name"><strong>${pos.pair}<span class="direction ${pos.side === 1 ? 'long' : 'short'}">${pos.side === 1 ? '做多' : '做空'}</span>${riskRatio(pos) >= .6 ? '<span class="risk-tag">风险偏高</span>' : ''}</strong><small>${money(pos.margin)} 保证金 · ${money(pos.notional)} 仓位</small></div><div class="pos-cell pos-entry"><strong>${priceText(pos.pair, pos.entry)}</strong><small>开仓价格</small></div><div class="pos-cell"><strong>${priceText(pos.pair, currentPrice(pos.pair))}</strong><small>当前价格</small></div><div class="pos-cell"><strong class="${pnl >= 0 ? 'positive' : 'negative'}">${signedMoney(pnl)}</strong><small>浮动盈亏</small></div><button class="close-btn" type="button">平仓</button>`;
      row.querySelector('button').addEventListener('click', () => closePosition(pos.id, false)); root.append(row);
    });
  }
  function renderHistory() {
    $('history').classList.toggle('hidden', !historyExpanded);
    $('historyToggle').textContent = historyExpanded ? '收起记录' : '展开记录';
    if (!historyExpanded) return;
    const root = $('history'); root.replaceChildren();
    if (!state.history.length) { root.innerHTML = '<div class="empty-state">交易结算后会显示在这里</div>'; return; }
    state.history.slice(0, 8).forEach(item => {
      const row = document.createElement('div'); row.className = 'history-row';
      row.innerHTML = `<span>${item.pair} · ${item.side === 1 ? '做多' : '做空'} · ${item.liquidated ? '爆仓' : '平仓'} · ${item.time}</span><strong class="${item.pnl >= 0 ? 'positive' : 'negative'}">${signedMoney(item.pnl)}</strong>`;
      root.append(row);
    });
  }
  function renderChartHeader() {
    const pair = PAIRS.find(p => p.id === state.pair);
    const rate = currentPrice(pair.id); const change = (rate / previousPrice(pair.id) - 1) * 100;
    const playback = !['sim', 'challenge'].includes(state.mode);
    const series = state.mode === 'battle' ? battle : real;
    $('pairTitle').textContent = pair.id.replace('/', ' / ');
    $('pairName').textContent = pair.name;
    $('currentPrice').textContent = priceText(pair.id, rate);
    $('priceChange').textContent = pct(Number.isFinite(change) ? change : 0);
    $('priceChange').className = change >= 0 ? 'positive' : 'negative';
    $('modeBadge').textContent = state.mode === 'real' ? '真实历史数据' : state.mode === 'battle' ? '经典战役' : state.mode === 'challenge' ? '每日挑战' : '模拟行情';
    $('modeBadge').classList.toggle('real', state.mode === 'real');
    $('modeBadge').classList.toggle('battle', state.mode === 'battle');
    $('modeBadge').classList.toggle('challenge', state.mode === 'challenge');
    $('simMode').classList.toggle('active', state.mode === 'sim');
    $('realMode').classList.toggle('active', state.mode === 'real');
    $('battleMode').classList.toggle('active', state.mode === 'battle' || battlePickerOpen);
    $('challengeMode').classList.toggle('active', state.mode === 'challenge');
    $('nextDayBtn').classList.toggle('hidden', !playback);
    $('playBtn').classList.toggle('hidden', !playback);
    $('replayBtn').classList.toggle('hidden', !playback);
    $('playBtn').textContent = autoPlay ? '暂停播放' : '自动播放';
    $('nextDayBtn').disabled = !playback || series.loading || series.cursor >= series.items.length - 1 || riskPaused;
    $('playBtn').disabled = !playback || series.loading || series.cursor >= series.items.length - 1 || riskPaused;
    $('replayBtn').disabled = !playback || series.loading || !!state.positions.length || riskPaused;
    $('dataStatus').textContent = playback ? (series.loading ? '读取中…' : series.items[series.cursor] ? `历史回放 · ${series.items[series.cursor].date}` : '尚未载入数据') : state.mode === 'challenge' ? '挑战行情 · 每 1.5 秒更新' : '每 1.5 秒更新';
    $('chartLegend').textContent = playback ? 'Frankfurter · 日度参考汇率（影线为示意）' : state.mode === 'challenge' ? '挑战模式 · 随机模拟 K 线' : '模拟数据 · 模拟 K 线';
    $('chartDate').textContent = playback ? `${series.items.length ? series.cursor + 1 : 0} / ${series.items.length} 个交易日` : state.mode === 'challenge' ? (challenge.active ? '挑战进行中' : '等待开始') : '实时模拟';
    $('chartLoading').classList.toggle('hidden', !playback || !series.loading);
    $('playbackTools').classList.toggle('hidden', !playback);
    if (playback) {
      const tf = series.tf || '1d';
      [...$('tfSeg').children].forEach(btn => btn.classList.toggle('active', btn.dataset.tf === tf));
      const progress = $('progressBar');
      progress.max = Math.max(0, series.items.length - 1);
      if (!progressActive) progress.value = series.cursor;
      $('progressDateLabel').textContent = series.items[series.cursor]?.date || '—';
      $('rangeDaysNote').textContent = state.mode === 'real' && real.items.length ? `共 ${real.items.length} 个交易日` : '';
    }
    $('realRangeBar').classList.toggle('hidden', state.mode !== 'real');
    if (state.mode === 'real' && state.realRange) { $('rangeStart').value = state.realRange.start; $('rangeEnd').value = state.realRange.end; }
    renderRangeStats();
  }
  function renderBattleShelf() {
    const visible = battlePickerOpen || state.mode === 'battle';
    $('battleShelf').classList.toggle('hidden', !visible);
    if (!visible) return;
    const selected = BATTLES.find(item => item.id === state.battleId);
    $('battleShelfTitle').textContent = battlePickerOpen ? '选择一场经典战役' : selected?.title || '选择一场经典战役';
    $('battleChooseBtn').classList.toggle('hidden', battlePickerOpen || state.mode !== 'battle');
    $('battleList').classList.toggle('hidden', !battlePickerOpen);
    if (battlePickerOpen) {
      $('battleInfo').textContent = '选择一场，使用当年的日度参考汇率逐日模拟。';
      if ($('battleList').childElementCount) return;
      BATTLES.forEach(item => {
        const card = document.createElement('button'); card.type = 'button'; card.className = 'battle-card';
        card.innerHTML = `<span class="battle-date">${item.event}</span><strong>${item.title}</strong><span class="battle-pair">${item.pair}</span><small>${item.description}</small>`;
        card.addEventListener('click', () => selectBattle(item.id)); $('battleList').append(card);
      });
    } else {
      $('battleList').replaceChildren();
      $('battleInfo').innerHTML = selected ? `${selected.description} <a class="battle-source" href="${selected.source}" target="_blank" rel="noopener noreferrer">事件来源 ↗</a><br>从重大事件前数周开始；推进日期时会出现当时的政策与市场快讯。日度参考价不展示盘中极端波动。` : '';
    }
  }
  function renderChallenge() {
    const visible = state.mode === 'challenge';
    $('challengeBar').classList.toggle('hidden', !visible);
    if (!visible) { $('longBtn').disabled = false; $('shortBtn').disabled = false; $('resetBtn').disabled = false; return; }
    const ready = challenge.loaded && !challenge.loading;
    $('challengeAttempts').textContent = ready ? `今日剩余 ${challenge.remaining} 次${challenge.active ? ' · 当前挑战进行中' : ''}` : '正在读取挑战记录…';
    $('challengeStatus').textContent = challenge.active ? `当前权益 ${money(account().equity)} · 收益 ${signedMoney(account().equity - 10000)}` : challenge.remaining > 0 ? '一万元开局，随时可以金盆洗手' : '今日机会已经用完';
    $('challengeStartBtn').textContent = challenge.active ? '继续挑战' : '开始挑战';
    $('challengeStartBtn').disabled = !ready || challenge.active || challenge.remaining <= 0;
    $('challengeRetireBtn').disabled = !ready || !challenge.active;
    $('longBtn').disabled = !challenge.active;
    $('shortBtn').disabled = !challenge.active;
    $('resetBtn').disabled = challenge.active;
  }
  function render() { renderPairs(); renderAccount(); renderOrder(); renderPositions(); renderHistory(); renderChartHeader(); renderBattleShelf(); renderChallenge(); drawChart(); }

  function openPosition(side) {
    if (state.mode === 'challenge' && !challenge.active) { notify('请先开始一次挑战。'); return null; }
    if (state.mode === 'challenge' && state.positions.length >= 5) { notify('挑战模式最多同时持有 5 笔仓位。'); return null; }
    const margin = Number($('marginInput').value);
    if (!Number.isFinite(margin) || margin < 10) { notify('保证金至少为 $10。'); return null; }
    const fee = tradeFee(margin, state.leverage);
    if (margin + fee > state.cash + .001) { notify(`可用余额不足：保证金与手续费合计 ${money(margin + fee)}。`); return null; }
    const entry = currentPrice(state.pair);
    if (!Number.isFinite(entry)) { notify('行情尚未准备好，请稍后再试。'); return null; }
    state.margin = margin;
    state.cash -= margin + fee;
    state.feesPaid = (state.feesPaid || 0) + fee;
    const position = { id: `${Date.now()}-${Math.random()}`, pair: state.pair, side, entry, margin, leverage: state.leverage, notional: margin * state.leverage, fee, warned: false, opened: new Date().toLocaleString('zh-CN') };
    state.positions.unshift(position);
    AudioFX.open();
    if (side === 1) {
      const playback = ['real', 'battle'].includes(state.mode);
      const series = playback ? (state.mode === 'battle' ? battle : real) : null;
      const windowPrices = playback
        ? series.items.slice(Math.max(0, series.cursor - 39), series.cursor + 1).map(row => row.prices[state.pair])
        : (state.mode === 'challenge' ? challengeSim : sim)[state.pair].candles.slice(-40).map(c => c.high);
      const top = Math.max(...windowPrices);
      if (Number.isFinite(top) && entry >= top * .998) unlockAchievement('buy-top');
    }
    save(); if (state.mode === 'challenge') scheduleChallengeSave(); render(); notify(`${state.pair} ${side === 1 ? '做多' : '做空'}开仓成功，已收手续费 ${money(fee)}。`);
    return position;
  }
  function closePosition(id, liquidated) {
    const index = state.positions.findIndex(p => p.id === id);
    if (index < 0) return;
    const pos = state.positions[index];
    const rawPnl = positionPnl(pos);
    const pnl = rawPnl;
    state.cash += pos.margin + pnl;
    state.positions.splice(index, 1);
    state.history.unshift({ pair: pos.pair, side: pos.side, pnl, liquidated, time: new Date().toLocaleDateString('zh-CN') });
    state.history = state.history.slice(0, 25);
    if (liquidated) {
      AudioFX.blow();
      unlockAchievement('innocent-cat');
      if (pos.borrowed) unlockAchievement('finger-support');
      if (pos.refusedHelp) unlockAchievement('just-kill-me');
    } else if (pnl >= 0) AudioFX.win();
    else AudioFX.lose();
    checkEquityAchievements();
    save(); if (state.mode === 'challenge') scheduleChallengeSave(); render();
    openModal({ icon: liquidated ? '✕' : pnl >= 0 ? '✦' : '♡', loss: liquidated || pnl < 0,
      title: liquidated ? '哎呀，仓位爆掉了' : pnl >= 0 ? '平仓成功，漂亮！' : '已经平仓，休息一下',
      message: liquidated ? `${pos.pair} 的亏损穿过保证金 80% 爆仓线，已按当前可得价格结算。跳空时亏损可能超过保证金。` : `${pos.pair} ${pos.side === 1 ? '做多' : '做空'}仓位已结算，盈亏计入可用余额。`,
      detail: `${liquidated ? '本次爆仓盈亏' : '本次交易盈亏'}  ${signedMoney(pnl)}${state.cash < 0 ? ` · 账户已穿仓 ${money(state.cash)}` : ''}` });
  }
  function checkLiquidations() {
    if (riskPaused) return;
    for (const pos of [...state.positions]) {
      const ratio = riskRatio(pos);
      if (ratio < .55) pos.warned = false;
      if (ratio >= .6 && !pos.warned) {
        pos.warned = true;
        riskPaused = true;
        autoPlay = false;
        save();
        AudioFX.alarm();
        const suggested = Math.max(1, Math.ceil(-positionPnl(pos) / .55 - pos.margin));
        openModal({ icon: '!', loss: true, riskPositionId: pos.id, title: ratio >= .8 ? '仓位已触及爆仓线' : '仓位接近爆仓线',
          message: `${pos.pair} 已亏损保证金的 ${(ratio * 100).toFixed(1)}%。${ratio >= .8 ? '行情已穿过爆仓线，关闭提醒后会按当前价格结算，亏损可能超过保证金。' : '你可以在这里补保证金，或借款直接补仓。'}借款按金额分级计息。`,
          detail: `当前浮亏 ${signedMoney(positionPnl(pos))} · 爆仓线 80%`,
          input: { label: `补仓金额（建议 ${money(suggested)}）`, value: suggested }, confirm: '暂不处理' });
        return;
      }
      if (ratio >= .8) closePosition(pos.id, true);
    }
  }
  function riskRatio(pos) { return Math.max(0, -positionPnl(pos) / pos.margin); }
  function addMarginToPosition(borrow) {
    const pos = state.positions.find(p => p.id === riskPositionId);
    const amount = Number($('modalInput').value);
    const available = borrow ? LOAN_MAX : state.cash;
    if (!pos || !Number.isFinite(amount) || amount < 1 || amount > available + .001) return notify(borrow ? '借款补仓金额应为 $1–$200,000。' : '补仓金额不能超过可用余额。');
    if (borrow && state.debt > 0) return notify('请先偿还当前贷款，才能再次借入。');
    marginHelpDone = true;
    if (borrow) { borrowLoan(amount, pos); pos.borrowed = true; }
    else state.cash = Math.max(0, state.cash - amount);
    if (!borrow) pos.margin += amount;
    save(); render();
    closeModal();
    notify(`${borrow ? '已借款' : '已追加'} ${money(amount)} 至 ${pos.pair} 保证金。`);
  }
  function triggerBattleNews() {
    if (state.mode !== 'battle' || !battle.items.length) return;
    const item = BATTLES.find(candidate => candidate.id === state.battleId);
    const date = battle.items[battle.cursor]?.date;
    if (!item || !date) return;
    battle.shownNews ||= [];
    item.news.filter(news => news.date <= date && !battle.shownNews.includes(news.date)).forEach(news => {
      battle.shownNews.push(news.date);
      pushNews({ tag: news.tag, title: news.title, body: news.body, date: news.date });
    });
  }
  function triggerSimNews() {
    const template = SIM_NEWS[Math.floor(Math.random() * SIM_NEWS.length)];
    activeSimNews = template;
    activeSimNewsTicks = 5 + Math.floor(Math.random() * 4);
    const range = NEWS_FREQ_TICKS[settings.newsFreq] || NEWS_FREQ_TICKS.mid;
    simNewsTicks = range[0] + Math.floor(Math.random() * (range[1] - range[0] + 1));
    pushNews({ tag: template.tag, title: template.title, body: template.body, date: '模拟事件' });
  }
  function tickSim() {
    if (riskPaused) return;
    [sim, challengeSim].forEach((market, marketIndex) => PAIRS.forEach((pair, index) => {
      const series = market[pair.id]; const open = series.price;
      const drift = Math.sin(Date.now() / 13000 + index * 2 + marketIndex * .7) * .00036;
      const shock = Math.random() < .018 ? (Math.random() - .5) * .019 : 0;
      let newsEffect = activeSimNews?.bias?.[pair.id] || 0;
      newsEffect *= .25 + Math.random() * 1.1;
      if (Math.random() < .24) newsEffect *= -.6;
      const close = Math.max(open * .5, open * (1 + drift + (Math.random() - .5) * .0042 + shock + newsEffect));
      const wick = open * (Math.random() * .0007 + .00015);
      series.candles.push({ open, high: Math.max(open, close) + wick, low: Math.min(open, close) - wick, close });
      if (series.candles.length > 150) series.candles.shift();
      series.price = close;
    }));
    if (state.mode === 'sim' || state.mode === 'challenge') {
      if ((state.mode === 'sim' || challenge.active) && --simNewsTicks <= 0) triggerSimNews();
      if (activeSimNewsTicks > 0 && --activeSimNewsTicks <= 0) activeSimNews = null;
      if (state.mode === 'sim' && state.debt > 0 && ++state.simLoanTicks >= 20) { state.simLoanTicks = 0; accrueLoanInterest(); }
      state.positions.forEach(pos => {
        if (positionPnl(pos) < 0) { pos.loseMs = (pos.loseMs || 0) + 1500; if (pos.loseMs >= 8 * 60 * 1000) unlockAchievement('never-sell'); }
      });
      if (++simTickCount % 20 === 0) {
        state.equityTrail.push(Math.round(account().equity * 100) / 100);
        if (state.equityTrail.length > 120) state.equityTrail = state.equityTrail.slice(-120);
        save();
      }
      checkEquityAchievements();
      checkLiquidations(); render();
    }
    save();
  }
  const FX_SYMBOLS = 'USD,GBP,JPY,CHF,AUD,CAD';
  async function fetchFrankfurter(path, attempts = 3) {
    let lastError = null;
    for (let attempt = 0; attempt < attempts; attempt++) {
      if (attempt) {
        const loading = $('chartLoading');
        if (loading && !loading.classList.contains('hidden')) loading.textContent = `正在读取历史汇率…（自动重试 ${attempt}/${attempts - 1}）`;
        await wait(800 * attempt);
      }
      try {
        const response = await fetch(`https://api.frankfurter.dev/v1${path}`, { signal: AbortSignal.timeout(20000) });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } catch (error) { lastError = error; }
    }
    const loading = $('chartLoading');
    if (loading && !loading.classList.contains('hidden')) loading.textContent = '正在读取历史汇率…';
    throw lastError || new Error('网络错误');
  }
  function parseFrankfurter(data) {
    return Object.entries(data.rates || {}).sort(([a], [b]) => a.localeCompare(b)).map(([date, r]) => {
      if (!['USD', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD'].every(key => Number.isFinite(r[key]) && r[key] > 0)) return null;
      return { date, prices: { 'EUR/USD': r.USD, 'GBP/USD': r.USD / r.GBP, 'USD/JPY': r.JPY / r.USD, 'USD/CHF': r.CHF / r.USD, 'EUR/CHF': r.CHF, 'AUD/USD': r.USD / r.AUD, 'USD/CAD': r.CAD / r.USD } };
    }).filter(Boolean);
  }
  function chunkRange(start, end, days = 120) {
    const chunks = [];
    let cursor = start;
    while (cursor <= end) {
      const chunkEnd = new Date(Math.min(Date.parse(cursor) + (days - 1) * 86400000, Date.parse(end))).toISOString().slice(0, 10);
      chunks.push([cursor, chunkEnd]);
      cursor = new Date(Date.parse(chunkEnd) + 86400000).toISOString().slice(0, 10);
    }
    return chunks;
  }
  async function fetchHistory(start, end = '') {
    const path = `/${start}..${end}?base=EUR&symbols=${FX_SYMBOLS}`;
    try {
      return parseFrankfurter(await fetchFrankfurter(path));
    } catch (_) {}
    // 服务端偶发 520/522 时兜底：把区间切成小段逐段拉取合并
    const chunks = chunkRange(start, end || new Date().toISOString().slice(0, 10));
    const merged = [];
    const loading = $('chartLoading');
    for (let i = 0; i < chunks.length; i++) {
      if (loading && !loading.classList.contains('hidden')) loading.textContent = `正在读取历史汇率… ${i + 1}/${chunks.length} 段`;
      merged.push(...parseFrankfurter(await fetchFrankfurter(`/${chunks[i][0]}..${chunks[i][1]}?base=EUR&symbols=${FX_SYMBOLS}`, 2)));
    }
    if (loading && !loading.classList.contains('hidden')) loading.textContent = '正在读取历史汇率…';
    const seen = new Set();
    return merged.filter(row => !seen.has(row.date) && seen.add(row.date)).sort((a, b) => a.date.localeCompare(b.date));
  }
  async function loadReal(range) {
    const target = range && /^\d{4}-\d{2}-\d{2}$/.test(range.start) && /^\d{4}-\d{2}-\d{2}$/.test(range.end) ? range : (state.realRange || defaultRealRange());
    const key = realRangeKey(target);
    if (real.items.length && state.realRangeKey === key) return true;
    real.loading = true; renderChartHeader();
    const request = ++requestCounter;
    try {
      const items = await fetchHistory(target.start, target.end);
      if (request !== requestCounter) return false;
      if (items.length < 15) throw new Error('历史数据不足');
      real = { items, cursor: 0, loading: false, error: '', tf: real.tf || '1d' };
      state.realRange = target; state.realRangeKey = key;
      const progressDate = state.realProgress?.[key];
      const savedCursor = progressDate ? items.findIndex(item => item.date === progressDate) : -1;
      real.cursor = savedCursor >= 0 ? savedCursor : 0;
      state.lastRealDate = items[real.cursor].date;
      return true;
    } catch (error) {
      if (request !== requestCounter) return false;
      real.loading = false; real.error = error.message || '网络错误';
      const detail = error?.name === 'TimeoutError' ? '请求超时' : error?.message || '网络错误';
      notify(`真实历史数据读取失败（${detail}），请点击“真实数据”重试。`); return false;
    }
  }
  async function selectBattle(id, resume = false) {
    const item = BATTLES.find(candidate => candidate.id === id);
    if (!item) return;
    if (state.mode === 'battle' && state.positions.length && state.battleId !== id) return notify('经典战役账户仍有持仓，请先平仓再更换战役。');
    if (state.mode === 'battle' && state.positions.length && !resume) return notify('经典战役账户仍有持仓，不能重新开始战役。');
    const previousMode = state.mode;
    const previousBattle = battle;
    autoPlay = false; battlePickerOpen = false;
    activateMode('battle'); state.battleId = id; state.pair = item.pair;
    const request = ++battleRequestCounter;
    battle = { items: [], cursor: 0, loading: true, error: '', id };
    render();
    try {
      const items = await fetchHistory(item.start, item.end);
      if (request !== battleRequestCounter) return;
      const eventIndex = items.findIndex(row => row.date >= item.event);
      if (items.length < 15 || eventIndex < 2) throw new Error('战役历史数据不足');
      const startCursor = 0;
      const savedCursor = resume && state.lastBattleDate ? items.findIndex(row => row.date === state.lastBattleDate) : -1;
      battle = { items, cursor: savedCursor >= 0 ? savedCursor : startCursor, startCursor, loading: false, error: '', id, endNotified: false, shownNews: [] };
      state.lastBattleDate = items[battle.cursor].date;
      save(); render(); checkLiquidations(); triggerBattleNews(); notify(`${item.title} 已就绪，从事件前数周开始回放。`);
    } catch (error) {
      if (request !== battleRequestCounter) return;
      battle = previousMode === 'battle' ? previousBattle : { items: [], cursor: 0, loading: false, error: error.message || '网络错误', id: null };
      activateMode(previousMode);
      battlePickerOpen = true; render(); const detail = error?.name === 'TimeoutError' ? '请求超时' : error?.message || '网络错误'; notify(`战役数据读取失败（${detail}），请稍后重试。`);
    }
  }
  async function setMode(mode) {
    if (mode === 'challenge') { await enterChallengeMode(); return; }
    if (mode === 'battle') {
      battlePickerOpen = true; renderBattleShelf(); renderChartHeader(); return;
    }
    battlePickerOpen = false;
    if (state.mode === mode) {
      if (mode === 'real' && !real.items.length && !real.loading) { await loadReal(); render(); }
      else render();
      return;
    }
    autoPlay = false; battleRequestCounter++;
    activateMode(mode);
    if (mode === 'real') { const ok = await loadReal(); if (!ok) { render(); save(); return; } }
    if (mode === 'real') state.lastRealDate = real.items[real.cursor].date;
    save(); render(); notify(mode === 'real' ? '已切换为真实历史汇率回放。' : '已切换为模拟数据行情。');
  }
  async function enterChallengeMode() {
    battlePickerOpen = false; autoPlay = false; battleRequestCounter++;
    activateMode('challenge');
    render();
    await loadChallengeProgress();
    save(); render();
    if (challenge.active) notify('已恢复今天尚未结束的挑战。');
  }
  async function startChallenge() {
    if (!challenge.loaded || challenge.loading) return notify('挑战记录仍在读取，请稍候。');
    if (challenge.active) return;
    if (challenge.date !== todayKey()) { challenge.date = todayKey(); challenge.remaining = 3; }
    if (challenge.remaining <= 0) return notify('今天的三次挑战机会已经用完。');
    state = initialState('challenge'); modeAccounts.challenge = null;
    challengeSim = {}; seedChallengeSim();
    challenge.remaining--; challenge.active = true;
    save(); render();
    openModal({ icon: '⚑', title: '挑战开始', message: '初始本金 $10,000，挑战模式不开放贷款。你可以随时点击“金盆洗手”，结算收益并提交今日排行榜。', detail: `今日剩余机会 ${challenge.remaining} 次` });
    saveChallengeCloud(true);
  }
  async function finishChallenge() {
    if (!challenge.active || state.mode !== 'challenge') return;
    let settled = 0;
    [...state.positions].forEach(pos => {
      const pnl = positionPnl(pos);
      state.cash += pos.margin + pnl;
      settled += pnl;
      state.history.unshift({ pair: pos.pair, side: pos.side, pnl, liquidated: false, time: new Date().toLocaleDateString('zh-CN') });
    });
    state.positions = []; state.history = state.history.slice(0, 25);
    const profit = state.cash - 10000;
    challenge.active = false;
    save(); render(); await saveChallengeCloud(true);
    let rankNote = '当前环境无法连接 B站排行榜，成绩已保存在本机。';
    if (await toySupports('submitScore')) {
      const score = challengeScore(profit);
      try {
        await toyCallWithBackoff(() => window.toy.submitScore({ board: CHALLENGE_BOARD, score }));
        rankNote = `本次排行榜成绩 ${challengeRankText(score)}`;
      } catch (error) { rankNote = error?.code === 307044 ? '排行榜请求较多，稍后可再次打开今日榜单。' : '排行榜提交失败，本机挑战结算仍已保存。'; }
    }
    openModal({ icon: profit >= 0 ? '✦' : '♡', loss: profit < 0, title: '金盆洗手 · 挑战结束', message: `已结算 ${settled ? `${state.history.length} 笔记录中的未平仓仓位` : '全部仓位'}，本次成绩按最终权益计算。`, detail: `最终权益 ${money(state.cash)}\n挑战收益 ${signedMoney(profit)}\n${rankNote}`, preline: true });
  }
  async function showChallengeRank() {
    if (!(await toySupports('getRankList'))) {
      openModal({ icon: '♛', title: '今日挑战榜', message: '排行榜需要在支持 Toy SDK 的 B站环境中打开。', detail: '本地预览仍可完整测试挑战流程。' }); return;
    }
    notify('正在读取今日挑战榜…');
    try {
      const list = await toyCallWithBackoff(() => window.toy.getRankList({ board: CHALLENGE_BOARD, period: 'day', limit: 10 }));
      let mine = null;
      if (await toySupports('getMyRank')) { try { mine = await toyCallWithBackoff(() => window.toy.getMyRank({ board: CHALLENGE_BOARD, period: 'day' })); } catch (_) {} }
      const rows = list.length ? list.map(item => `${item.rank}. ${item.nickname || '匿名玩家'}  ${challengeRankText(item.score)}`) : ['今天还没有挑战成绩'];
      if (mine?.ranked) rows.push('', `我的排名：${mine.rank} · ${challengeRankText(mine.score)}`);
      openModal({ icon: '♛', title: '今日挑战榜', message: '榜单按“金盆洗手”时的收益排序，只在手动打开时读取。', detail: rows.join('\n'), preline: true });
    } catch (error) { notify(error?.code === 307044 ? '榜单访问人数较多，请稍后再试。' : '今日榜单读取失败。'); }
  }
  function nextDay() {
    if (riskPaused || ['sim', 'challenge'].includes(state.mode)) return;
    const series = state.mode === 'battle' ? battle : real;
    if (series.loading || series.cursor >= series.items.length - 1) { autoPlay = false; renderChartHeader(); return; }
    series.cursor++;
    accrueLoanInterest();
    if (state.mode === 'battle') state.lastBattleDate = series.items[series.cursor].date;
    else { state.lastRealDate = series.items[series.cursor].date; if (state.realRangeKey) state.realProgress[state.realRangeKey] = state.lastRealDate; }
    state.positions.forEach(pos => {
      if (positionPnl(pos) < 0) { pos.loseDays = (pos.loseDays || 0) + 1; if (pos.loseDays >= 30) unlockAchievement('never-sell'); }
    });
    const row = series.items[series.cursor], prevRow = series.items[series.cursor - 1];
    if ((series.tf || '1d') === '1d' && row && prevRow) {
      const move = row.prices[state.pair] / prevRow.prices[state.pair] - 1;
      if (Math.abs(move) >= .015) notify(`⚡ ${row.date} ${state.pair} 单日波动 ${pct(move * 100)}`);
    }
    if (state.mode === 'battle' && state.battleId === 'franc-2015' && row && row.date >= '2015-01-15') unlockAchievement('killed-by-chf');
    state.equityTrail.push(Math.round(account().equity * 100) / 100);
    if (state.equityTrail.length > 120) state.equityTrail = state.equityTrail.slice(-120);
    checkEquityAchievements();
    checkLiquidations(); save(); render();
    if (state.mode === 'battle') triggerBattleNews();
    if (series.cursor >= series.items.length - 1) {
      autoPlay = false; renderChartHeader();
      if (state.mode === 'battle' && !series.endNotified) {
        series.endNotified = true;
        openModal({ icon: '✦', title: '这场战役回放结束', message: '你可以平掉剩余持仓，随后选择下一场经典战役。', detail: `当前账户总权益 ${money(account().equity)}` });
      } else if (state.mode === 'real') {
        const firstPrice = real.items[0]?.prices[state.pair], lastPrice = real.items.at(-1)?.prices[state.pair];
        const buyHold = firstPrice && lastPrice ? (lastPrice / firstPrice - 1) * 100 : 0;
        const mine = (account().equity - 10000) / 10000 * 100;
        openModal({ icon: '✦', title: '回放到最后一个交易日', message: `区间 ${real.items[0].date} → ${real.items.at(-1).date} 回放完毕。`, detail: `你的收益 ${pct(mine)}\n买入持有对照 ${pct(buyHold)}`, preline: true });
      }
    }
  }
  function replaySeries() {
    if (state.positions.length) return notify('请先平掉当前持仓，再回到起点。');
    if (['sim', 'challenge'].includes(state.mode)) return;
    const series = state.mode === 'battle' ? battle : real;
    if (!series.items.length) return;
    autoPlay = false; series.cursor = 0;
    if (state.mode === 'battle') { state.lastBattleDate = series.items[series.cursor].date; series.endNotified = false; series.shownNews = []; triggerBattleNews(); }
    else { state.lastRealDate = series.items[series.cursor].date; if (state.realRangeKey) state.realProgress[state.realRangeKey] = state.lastRealDate; }
    save(); render(); notify('已回到回放起点。');
  }
  function renderTutorial() {
    const step = TUTORIAL[tutorialStep];
    $('tutorialStep').textContent = `${tutorialStep + 1} / ${TUTORIAL.length}`;
    $('tutorialIcon').textContent = step.icon;
    $('tutorialTitle').textContent = step.title;
    $('tutorialText').textContent = step.text;
    $('tutorialExample').textContent = step.example;
    $('tutorialBack').disabled = tutorialStep === 0;
    $('tutorialNext').textContent = tutorialStep === TUTORIAL.length - 1 ? '开始交易' : '下一步';
  }
  function openTutorial() { tutorialStep = 0; renderTutorial(); $('welcome').classList.add('hidden'); $('tutorial').classList.remove('hidden'); $('tutorialNext').focus(); }
  function closeTutorial() { $('tutorial').classList.add('hidden'); $('tutorialBtn').focus(); }

  function drawChart() {
    const canvas = $('chart'); const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.round(rect.width * dpr); canvas.height = Math.round(rect.height * dpr);
    const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);
    const w = rect.width, h = rect.height;
    const theme = CHART_THEMES[settings.theme] || CHART_THEMES.day;
    ctx.fillStyle = theme.bg; ctx.fillRect(0, 0, w, h);
    const left = 16, right = w - 58, top = 23, bottom = h - 28;
    const playback = !['sim', 'challenge'].includes(state.mode);
    const series = state.mode === 'battle' ? battle : real;
    let candles = [], dates = [];
    if (playback) {
      if (series.items.length && !series.loading) {
        const tf = series.tf || '1d';
        const rows = series.items.slice(0, series.cursor + 1);
        const all = candleFromRows(rows, state.pair, tf);
        const visible = Math.max(30, Math.min(70, Math.floor((right - left) / 9)));
        candles = all.slice(-visible);
        dates = candles.map(c => c.date);
      }
    } else {
      candles = (state.mode === 'challenge' ? challengeSim : sim)[state.pair].candles.slice(-54);
    }
    const values = candles.flatMap(c => [c.high, c.low]);
    if (values.length < 2) return;
    let min = Math.min(...values), max = Math.max(...values);
    const pad = Math.max((max - min) * .18, min * .0006); min -= pad; max += pad;
    const yOf = value => top + (max - value) / (max - min) * (bottom - top);
    ctx.strokeStyle = theme.grid; ctx.lineWidth = 1;
    ctx.fillStyle = theme.axis; ctx.font = '10px DM Mono, monospace'; ctx.textAlign = 'left';
    for (let i = 0; i < 5; i++) {
      const y = top + i * (bottom - top) / 4;
      ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(right, y); ctx.stroke();
      ctx.fillText(priceText(state.pair, max - i * (max - min) / 4), right + 7, y + 3);
    }
    ctx.strokeStyle = theme.vgrid;
    for (let i = 0; i < 6; i++) {
      const x = left + i * (right - left) / 5;
      ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, bottom); ctx.stroke();
    }
    const step = (right - left) / candles.length;
    const showMoveMarkers = playback && (series.tf || '1d') === '1d';
    candles.forEach((c, i) => {
      const x = left + step * (i + .5); const rising = c.close >= c.open;
      ctx.strokeStyle = rising ? theme.up : theme.down; ctx.fillStyle = rising ? theme.up : theme.down;
      ctx.lineWidth = 1.3; ctx.beginPath(); ctx.moveTo(x, yOf(c.high)); ctx.lineTo(x, yOf(c.low)); ctx.stroke();
      const yTop = yOf(Math.max(c.open, c.close)), yBottom = yOf(Math.min(c.open, c.close));
      ctx.fillRect(x - Math.max(2, step * .3), yTop, Math.max(4, step * .6), Math.max(2, yBottom - yTop));
      if (showMoveMarkers && c.open > 0) {
        const move = c.close / c.open - 1;
        if (Math.abs(move) >= .01) {
          const y = move > 0 ? Math.min(bottom - 3, yOf(c.low) + 9) : Math.max(top + 3, yOf(c.high) - 9);
          ctx.beginPath(); ctx.arc(x, y, 2.2, 0, Math.PI * 2); ctx.fill();
        }
      }
    });
    ctx.fillStyle = theme.date; ctx.font = '10px DM Mono, monospace';
    if (playback && dates.length) {
      ctx.fillText(dates[0].slice(5), left, h - 9); ctx.textAlign = 'right'; ctx.fillText(dates.at(-1).slice(5), right, h - 9); ctx.textAlign = 'left';
    } else {
      ctx.fillText('← 过去', left, h - 9); ctx.textAlign = 'right'; ctx.fillText('现在 →', right, h - 9); ctx.textAlign = 'left';
    }
    const p = currentPrice(state.pair);
    if (Number.isFinite(p) && p >= min && p <= max) {
      const y = yOf(p);
      ctx.setLineDash([4, 5]); ctx.strokeStyle = theme.dash; ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(right, y); ctx.stroke(); ctx.setLineDash([]);
    }
  }
  function renderRangeStats() {
    const el = $('rangeStats');
    if (state.mode !== 'real' || !real.items.length) { el.classList.add('hidden'); return; }
    el.classList.remove('hidden');
    const prices = real.items.map(row => row.prices[state.pair]).filter(Number.isFinite);
    if (prices.length < 2) { el.classList.add('hidden'); return; }
    const hi = Math.max(...prices), lo = Math.min(...prices);
    const change = (prices.at(-1) / prices[0] - 1) * 100;
    el.innerHTML = `<span>区间最高 <b>${priceText(state.pair, hi)}</b></span><span>区间最低 <b>${priceText(state.pair, lo)}</b></span><span>振幅 <b>${pct((hi / lo - 1) * 100)}</b></span><span>区间涨跌 <b class="${change >= 0 ? 'positive' : 'negative'}">${pct(change)}</b></span>`;
  }

  $('longBtn').addEventListener('click', () => openPosition(1));
  $('shortBtn').addEventListener('click', () => openPosition(-1));
  $('simMode').addEventListener('click', () => setMode('sim'));
  $('realMode').addEventListener('click', () => setMode('real'));
  $('battleMode').addEventListener('click', () => setMode('battle'));
  $('challengeMode').addEventListener('click', () => setMode('challenge'));
  $('challengeStartBtn').addEventListener('click', startChallenge);
  $('challengeRetireBtn').addEventListener('click', () => openModal({ icon: '♡', title: '现在金盆洗手？', message: '所有未平仓仓位会按当前价格结算，本次挑战随即结束，收益将提交今日排行榜。', confirm: '确认结算', action: () => { closeModal(); finishChallenge(); } }));
  $('challengeRankBtn').addEventListener('click', showChallengeRank);
  $('mobilePairSelect').addEventListener('change', event => { state.pair = event.target.value; save(); render(); });
  $('battleChooseBtn').addEventListener('click', () => { if (state.positions.length) return notify('经典战役账户仍有持仓，请先平仓再更换战役。'); battlePickerOpen = true; renderBattleShelf(); renderChartHeader(); });
  $('nextDayBtn').addEventListener('click', nextDay);
  $('replayBtn').addEventListener('click', replaySeries);
  $('playBtn').addEventListener('click', () => { autoPlay = !autoPlay; renderChartHeader(); });
  $('leverageRange').addEventListener('input', e => { state.leverage = Number(e.target.value); save(); renderOrder(); });
  $('marginInput').addEventListener('input', e => { state.margin = Number(e.target.value) || 0; save(); renderOrder(); });
  $('maxBtn').addEventListener('click', () => { const multiplier = 1 + state.leverage * (.00005 + state.leverage * .000005); state.margin = Math.max(0, Math.floor(state.cash / multiplier * 100) / 100); save(); renderOrder(); });
  $('historyToggle').addEventListener('click', () => { historyExpanded = !historyExpanded; renderHistory(); });
  $('borrowBtn').addEventListener('click', () => {
    if (state.mode === 'challenge') return notify('挑战模式不开放贷款。');
    if (state.debt > 0) return notify('请先偿还当前贷款，再申请新贷款。');
    openModal({ icon: '$', title: '申请周转贷款', message: '最多可借 $200,000。借得越多，日利率越高；真实数据与经典战役每推进一个交易日计息，模拟数据每 30 秒计息一次。', loanQuote: true, input: { label: '借款金额（最多 $200,000）', value: 1000, max: LOAN_MAX }, confirm: '确认借入', action: amount => { if (!borrowLoan(amount)) return notify('请输入 $1–$200,000 的借款金额。'); save(); render(); closeModal(); notify(`已借入 ${money(amount)}，日利率 ${rateText(state.loanRate)}。`); } });
  });
  $('repayBtn').addEventListener('click', () => {
    if (state.debt <= 0) return notify('现在没有待还贷款。');
    if (state.cash < .01) return notify('可用余额不足，暂时无法还款。');
    const max = Math.min(state.debt, state.cash);
    openModal({ icon: '♡', title: '偿还贷款', message: `当前待还 ${money(state.debt)}，可用余额 ${money(state.cash)}。`, input: { label: '还款金额', value: Math.floor(max * 100) / 100, min: .01, step: .01, max }, confirm: '确认还款', action: amount => { if (!Number.isFinite(amount) || amount < .01 || amount > max + .001) return notify('还款金额超出可用范围。'); state.cash = Math.max(0, state.cash - amount); state.debt = Math.max(0, state.debt - amount); if (state.debt < .005) { state.debt = 0; state.loanPrincipal = 0; state.loanRate = 0; state.simLoanTicks = 0; } save(); render(); closeModal(); notify(`已偿还 ${money(amount)}。`); } });
  });
  $('resetBtn').addEventListener('click', () => { if (state.mode === 'challenge' && challenge.active) return notify('挑战进行中不能重置，请选择金盆洗手完成结算。'); openModal({ icon: '↺', title: '重置当前模式？', message: '只会重置当前模式的余额、持仓、贷款和交易记录，其他模式不受影响。', confirm: '确认重置', action: () => { const mode = state.mode; state = initialState(mode); modeAccounts[mode] = null; if (mode === 'real') real = { items: [], cursor: 0, loading: false, error: '' }; if (mode === 'battle') { battle = { items: [], cursor: 0, loading: false, error: '', id: null }; battlePickerOpen = true; } else battlePickerOpen = false; autoPlay = false; riskPaused = false; modalQueue = []; requestCounter++; battleRequestCounter++; if (mode === 'sim') { savedSim = null; sim = {}; seedSim(); } save(); closeModal(); render(); notify('当前模式已重新开始。'); } }); });
  $('addMarginBtn').addEventListener('click', () => addMarginToPosition(false));
  $('loanMarginBtn').addEventListener('click', () => addMarginToPosition(true));
  $('modalConfirm').addEventListener('click', () => { if (modalAction) modalAction(Number($('modalInput').value)); else closeModal(); });
  $('modalInput').addEventListener('input', updateLoanQuote);
  $('modalCancel').addEventListener('click', closeModal);
  $('modalClose').addEventListener('click', closeModal);
  $('modal').addEventListener('click', e => { if (e.target === $('modal')) closeModal(); });
  $('tutorialBtn').addEventListener('click', openTutorial);
  $('newPlayerBtn').addEventListener('click', () => { try { localStorage.setItem('fx-heartbeat-intro-v2', 'new'); } catch (_) {} openTutorial(); });
  $('veteranBtn').addEventListener('click', () => { try { localStorage.setItem('fx-heartbeat-intro-v2', 'veteran'); } catch (_) {} $('welcome').classList.add('hidden'); $('simMode').focus(); });
  $('tutorialBack').addEventListener('click', () => { tutorialStep = Math.max(0, tutorialStep - 1); renderTutorial(); });
  $('tutorialNext').addEventListener('click', () => { if (tutorialStep >= TUTORIAL.length - 1) closeTutorial(); else { tutorialStep++; renderTutorial(); } });
  $('tutorialClose').addEventListener('click', closeTutorial);
  $('tutorialSkip').addEventListener('click', closeTutorial);

  /* ===== v3 事件绑定 ===== */
  function renderSettingsControls() {
    $('sfxToggle').checked = settings.sfxOn;
    $('sfxVolume').value = settings.sfxVol;
    $('musicToggle').checked = settings.musicOn;
    $('musicVolume').value = settings.musicVol;
    $('musicStatus').textContent = musicName ? `已导入：${musicName}` : '尚未导入音乐（音频仅保存在本机浏览器）';
    [...$('newsFreqSeg').children].forEach(btn => btn.classList.toggle('active', btn.dataset.freq === settings.newsFreq));
    [...$('themeSeg').children].forEach(btn => btn.classList.toggle('active', btn.dataset.theme === settings.theme));
  }
  function markProgressActive() {
    progressActive = true;
    clearTimeout(progressActiveTimer);
    progressActiveTimer = setTimeout(() => { progressActive = false; renderChartHeader(); }, 500);
  }
  $('settingsBtn').addEventListener('click', () => { renderSettingsControls(); $('settingsModal').classList.remove('hidden'); AudioFX.click(); });
  $('settingsClose').addEventListener('click', () => $('settingsModal').classList.add('hidden'));
  $('settingsDone').addEventListener('click', () => { $('settingsModal').classList.add('hidden'); AudioFX.click(); });
  $('settingsReset').addEventListener('click', () => {
    settings = { ...DEFAULT_SETTINGS };
    saveSettings(); AudioFX.applyVolumes(); stopMusic(); previewing = false; $('musicPreviewBtn').textContent = '试听';
    renderSettingsControls(); renderTicker(); drawChart(); notify('已恢复默认设置。');
  });
  $('sfxToggle').addEventListener('change', e => { settings.sfxOn = e.target.checked; saveSettings(); AudioFX.applyVolumes(); AudioFX.click(); });
  $('sfxVolume').addEventListener('input', e => { settings.sfxVol = Number(e.target.value); saveSettings(); AudioFX.applyVolumes(); });
  $('sfxVolume').addEventListener('change', () => AudioFX.click());
  $('musicToggle').addEventListener('change', e => {
    settings.musicOn = e.target.checked; saveSettings(); AudioFX.applyVolumes();
    if (settings.musicOn) { if (musicBuffer) playMusicBuffer(); else notify('尚未导入音乐，请先选择本地音频文件。'); }
    else stopMusic();
  });
  $('musicVolume').addEventListener('input', e => { settings.musicVol = Number(e.target.value); saveSettings(); AudioFX.applyVolumes(); });
  $('musicFile').addEventListener('change', onMusicFile);
  $('musicPreviewBtn').addEventListener('click', toggleMusicPreview);
  $('musicClearBtn').addEventListener('click', clearMusic);
  $('newsToggle').addEventListener('change', e => {
    settings.newsOn = e.target.checked; saveSettings(); renderTicker();
    if (settings.newsOn) { const range = NEWS_FREQ_TICKS[settings.newsFreq] || NEWS_FREQ_TICKS.mid; simNewsTicks = Math.min(simNewsTicks, range[1]); }
  });
  $('newsFreqSeg').addEventListener('click', e => { const btn = e.target.closest('button[data-freq]'); if (!btn) return; settings.newsFreq = btn.dataset.freq; saveSettings(); renderSettingsControls(); notify('新闻频率已调整。'); });
  $('themeSeg').addEventListener('click', e => { const btn = e.target.closest('button[data-theme]'); if (!btn) return; settings.theme = btn.dataset.theme; saveSettings(); renderSettingsControls(); drawChart(); });
  $('newsCenterBtn').addEventListener('click', () => { renderNewsCenter(); $('newsCenter').classList.remove('hidden'); });
  $('newsCenterOk').addEventListener('click', () => $('newsCenter').classList.add('hidden'));
  $('newsCenterClose').addEventListener('click', () => $('newsCenter').classList.add('hidden'));
  $('newsFloatClose').addEventListener('click', dismissNewsFloat);
  $('tfSeg').addEventListener('click', e => { const btn = e.target.closest('button[data-tf]'); if (!btn || !['real', 'battle'].includes(state.mode)) return; (state.mode === 'battle' ? battle : real).tf = btn.dataset.tf; render(); });
  $('rangeQuickSeg').addEventListener('click', e => {
    const btn = e.target.closest('button[data-days]'); if (!btn) return;
    const startValue = $('rangeStart').value;
    let start, end;
    if (btn.dataset.days === 'ytd') {
      const today = new Date();
      start = new Date(Date.UTC(today.getUTCFullYear(), 0, 1));
      end = today;
    } else if (/^\d{4}-\d{2}-\d{2}$/.test(startValue)) {
      // 有开始日期：从开始日期往后推 N 天，开始保持不变
      start = new Date(`${startValue}T00:00:00Z`);
      end = new Date(start.getTime() + (Number(btn.dataset.days) - 1) * 86400000);
    } else {
      const today = new Date();
      start = new Date();
      start.setUTCDate(start.getUTCDate() - (Number(btn.dataset.days) - 1));
      end = today;
    }
    $('rangeStart').value = start.toISOString().slice(0, 10);
    $('rangeEnd').value = end.toISOString().slice(0, 10);
    applyRealRange({ start: $('rangeStart').value, end: $('rangeEnd').value });
  });
  $('rangeApplyBtn').addEventListener('click', () => applyRealRange({ start: $('rangeStart').value, end: $('rangeEnd').value }));
  $('progressBar').addEventListener('input', e => {
    const series = state.mode === 'battle' ? battle : real;
    if (!series.items.length) return;
    autoPlay = false;
    markProgressActive();
    const target = Math.max(0, Math.min(series.items.length - 1, Number(e.target.value)));
    if (target === series.cursor) { renderChartHeader(); return; }
    const forward = Math.max(0, target - series.cursor);
    for (let i = 0; i < forward; i++) accrueLoanInterest();
    series.cursor = target;
    if (state.mode === 'battle') state.lastBattleDate = series.items[target].date;
    else { state.lastRealDate = series.items[target].date; if (state.realRangeKey) state.realProgress[state.realRangeKey] = state.lastRealDate; }
    renderChartHeader(); renderAccount(); renderPositions(); drawChart();
  });
  $('progressBar').addEventListener('change', () => { checkLiquidations(); save(); render(); if (state.mode === 'battle') triggerBattleNews(); });
  $('achBtn').addEventListener('click', () => { renderAchBook(); $('achModal').classList.remove('hidden'); AudioFX.click(); checkFollowRelation(); });
  $('achOk').addEventListener('click', () => $('achModal').classList.add('hidden'));
  $('achClose').addEventListener('click', () => $('achModal').classList.add('hidden'));
  $('shareBtn').addEventListener('click', () => { AudioFX.click(); openShare(); });
  $('shareClose').addEventListener('click', () => $('shareModal').classList.add('hidden'));
  $('shareSaveBtn').addEventListener('click', async () => {
    if (!shareDataUrl) return;
    try { await toyCallWithBackoff(() => window.toy.saveImageToAlbum({ base64Data: shareDataUrl, hintMsg: '需要相册权限来保存战绩卡' })); notify('战绩卡已保存到相册。'); }
    catch (error) { notify(error?.type === 'invalid_param' ? '图片数据过大，保存失败。' : '保存失败，可改用下载或截图。'); }
  });
  $('shareDownloadBtn').addEventListener('click', () => {
    if (!shareDataUrl) return;
    const link = document.createElement('a'); link.download = 'fx-share-card.jpg'; link.href = shareDataUrl;
    document.body.append(link); link.click(); link.remove();
  });
  $('shareLinkBtn').addEventListener('click', async () => { try { await window.toy.share({ path: 'index.html' }); } catch (_) { notify('分享未完成，请稍后再试。'); } });
  $('authorHomeBtn').addEventListener('click', event => {
    const fallback = event.currentTarget.href;
    if (!window.toy || typeof window.toy.navigate !== 'function') return;
    event.preventDefault();
    try {
      Promise.resolve(window.toy.navigate({ type: 'space', id: '443211651' })).catch(() => window.location.assign(fallback));
    } catch (_) { window.location.assign(fallback); }
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Enter' && modalOpen && e.target === $('modalInput')) $('modalConfirm').click();
    if (e.key !== 'Escape') return;
    if (modalOpen) { closeModal(); return; }
    const openLayer = ['settingsModal', 'newsCenter', 'achModal', 'shareModal', 'tutorial'].find(id => !$(id).classList.contains('hidden'));
    if (openLayer === 'tutorial') closeTutorial();
    else if (openLayer) $(openLayer).classList.add('hidden');
  });
  window.addEventListener('resize', drawChart);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden' && state.mode === 'challenge' && challenge.active) saveChallengeCloud(false);
    else if (document.visibilityState === 'visible' && pendingFollowCheck) checkFollowRelation().finally(() => { pendingFollowCheck = false; });
  });
  window.addEventListener('pagehide', () => { if (state.mode === 'challenge' && challenge.active) saveChallengeCloud(false); });
  setInterval(() => { tickSim(); if (autoPlay && ['real', 'battle'].includes(state.mode)) nextDay(); }, 1500);
  if (document.modelContext?.registerTool) {
    const tools = [
      { name: 'read_fx_game_state', title: '读取游戏状态', description: '查看账户余额、模式、货币对价格和持仓，供后续游戏操作使用。', inputSchema: { type: 'object', properties: {}, additionalProperties: false }, annotations: { readOnlyHint: true }, execute() { return { mode: state.mode, battleId: state.mode === 'battle' ? state.battleId : null, challenge: state.mode === 'challenge' ? { active: challenge.active, remaining: challenge.remaining } : null, date: state.mode === 'real' ? real.items[real.cursor]?.date : state.mode === 'battle' ? battle.items[battle.cursor]?.date : null, cash: state.cash, debt: state.debt, equity: account().equity, prices: Object.fromEntries(PAIRS.map(p => [p.id, currentPrice(p.id)])), positions: state.positions.map(p => ({ id: p.id, pair: p.pair, side: p.side === 1 ? 'long' : 'short', margin: p.margin, leverage: p.leverage, entry: p.entry, pnl: positionPnl(p) })) }; } },
      { name: 'place_fx_trade', title: '开仓', description: '按当前游戏价格做多或做空，扣除保证金与手续费并更新可见持仓。', inputSchema: { type: 'object', properties: { pair: { type: 'string', enum: PAIRS.map(p => p.id) }, side: { type: 'string', enum: ['long', 'short'] }, margin: { type: 'number', minimum: 10 }, leverage: { type: 'integer', minimum: 1, maximum: 100 } }, required: ['pair', 'side', 'margin', 'leverage'], additionalProperties: false }, annotations: { readOnlyHint: false }, execute(input) { const fee = tradeFee(input.margin, input.leverage); if (!PAIRS.some(p => p.id === input.pair) || !['long', 'short'].includes(input.side) || !Number.isFinite(input.margin) || input.margin < 10 || input.margin + fee > state.cash || !Number.isInteger(input.leverage) || input.leverage < 1 || input.leverage > 100 || (state.mode === 'challenge' && !challenge.active)) throw new Error('开仓参数无效、挑战未开始或可用余额不足'); state.pair = input.pair; state.margin = input.margin; state.leverage = input.leverage; render(); const pos = openPosition(input.side === 'long' ? 1 : -1); if (!pos) throw new Error('行情尚未准备好'); return { id: pos.id, pair: pos.pair, side: input.side, entry: pos.entry, fee: pos.fee, remainingCash: state.cash }; } },
      { name: 'close_fx_trade', title: '平仓', description: '按当前游戏价格结算指定持仓，并显示平仓弹窗。', inputSchema: { type: 'object', properties: { id: { type: 'string' } }, required: ['id'], additionalProperties: false }, annotations: { readOnlyHint: false }, execute(input) { const pos = state.positions.find(p => p.id === input.id); if (!pos) throw new Error('找不到该持仓'); const pnl = positionPnl(pos); closePosition(pos.id, false); return { id: pos.id, pnl, cash: state.cash }; } },
      { name: 'advance_real_fx_day', title: '推进交易日', description: '在真实历史数据或经典战役模式中回放下一个交易日，并结算风险。', inputSchema: { type: 'object', properties: {}, additionalProperties: false }, annotations: { readOnlyHint: false }, execute() { const series = state.mode === 'battle' ? battle : real; if (state.mode === 'sim' || riskPaused || series.cursor >= series.items.length - 1) throw new Error('当前无法推进交易日'); nextDay(); return { date: series.items[series.cursor].date, prices: series.items[series.cursor].prices, equity: account().equity }; } }
    ];
    tools.forEach(tool => { try { Promise.resolve(document.modelContext.registerTool(tool)).catch(() => {}); } catch (_) {} });
  }
  saveSettings();
  renderTicker();
  loadAchievementsCloud();
  (async () => {
    const record = await MusicStore.get();
    if (!record?.buf) return;
    try {
      AudioFX.ensure();
      if (!AudioFX.ctx) return;
      musicBuffer = await AudioFX.ctx.decodeAudioData(record.buf.slice(0));
      musicName = record.name || '本地音乐';
      if (settings.musicOn) playMusicBuffer();
      renderSettingsControls();
    } catch (_) {}
  })();
  render();
  try { if (!localStorage.getItem('fx-heartbeat-intro-v2')) { $('welcome').classList.remove('hidden'); $('newPlayerBtn').focus(); } } catch (_) {}

window.__game = {
    openPosition: openPosition,
    closePosition: closePosition,
    getState: () => state,
    getSim: () => sim,
    save: save,
    setPair: (id) => { state.pair = id; save(); render(); },
};
})();