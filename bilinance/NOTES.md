# BILINANCE 模拟盘 · 摸透笔记

> bilibili toy 游戏: **BILINANCE 模拟盘(虚拟现货/合约交易)** by -会飞的蝈蝈-
> URL: https://www.bilibili.com/toy/IjaLS8zTiK58TTNZ/index.html
> iframe: https://www.bilibilitoy.com/toy/IjaLS8zTiK58TTNZ/40574677932032-v22575/index.html
> localStorage key: `binance-sim-v1`（key `futures` 页面知道）

## ⚠️ 与 FX 简单 相同的坑

- **行情是本地随机游走**（`engine.js`）: `trend = [-1,-0.5,0,0.5,1][Math.random()*5]` 随机趋势, 每 ~90s 随机新闻冲击(`_fireNews` mag 0.05~0.14)
- **无任何外部 API / WebSocket / fetch**（已抓包确认）
- 初始资金 `$10,000 USDT`, tick 频率: `App.tick()` 每秒跑 `Engine.tick() + Store.checkOrders() + Store.checkLiquidations()`(强平实时)

## 导航（.nav-links a）

`行情 markets | 交易 trade | 合约 futures | 资产 assets | 挑战 challenge`
路由 hash: `#/trade/BTCUSDT` `#/futures/BTCUSDT`
点击: `Array.from(document.querySelectorAll('.nav-links a')).find(a=>a.textContent.trim()==='交易').click()`

## 交易页(现货)

**按钮:**
- 买入/卖出 tab（买卖方向）
- 限价/市价 模式
- 提价幅度: 25% 50% 75% 100% + step −/+ (precent 填入)
- `fSubmit` 提交按钮（text="买入 BTC" / "卖出 BTC"）
- 委托记录: 当前委托 / 历史委托 / 持有

**输入框:**
- `fPrice` 限价模式: 价格
- `fQty` 限价模式: 数量(币); **市价模式: 填入的是 USDT 金额**(不是币数量!)

**流程:**
- 市价买入: 切市价 → `fQty` 填 USDT 金额(≥1) → 点 `fSubmit` → 立即成交, 扣除金额+0.1%手续费
- 市价卖出: 切卖出 → 填币数量 → 提交
- 限价买入: 填 `fPrice` + `fQty` → 提交 → 挂单(`openOrders`), 成交时通知
- 最小下单额: **1 USDT**（`store.js` line 131/157/173）
- 手续费: 现货 `FEE=0.001`(0.1%), 合约 `FEE_FUT=0.0005`(0.05%)

## 合约页(futures)

**按钮:**
- `fLong` 开多·看涨 / `fShort` 开空·看跌（`sub-btn buy/sell`）
- 持仓 tab: 当前持仓 / 平仓记录
- **平仓**: 持仓行里 `class="mini danger"` 的"平仓"按钮, **点击即平仓, 无确认弹窗**

**输入框:**
- `levSlider` / `levInput` 杠杆(输入 le 或滑条)
- `fMargin` 保证金(≥5 USDT)

**流程:**
- 开多: 填 `levInput`=10 → `fMargin`=50 → 点 `fLong` → positions 增加, toast "开多成功 10x"
- 平仓: 点 danger 平仓 → 直接平, toast "平仓成功 亏损 X USDT"

**数据(合约):**
```json
position: {id, ts, sym:"BTCUSDT", dir:1(多)/-1(空), entry, qty, margin, lev}
```
- 维持保证金率: `MAINT_MARGIN=0.05`, `effMM(lev)=min(0.05, 0.5/lev)`(500x 时 ~0.1% 就爆)
- 强平: 每 tick `Store.checkLiquidations()` 检查, 亏损超过保证金×(1-MM率) 就强平

## 价格读取

- **盘面大字价**: `#tkPrice` 元素(`class="tk-price fl-up/fl-down"`), 显示当前 pair 价格
- **订单簿**: `[class*="book"]` 行, 每行 `价格 量 额`
- **行情表**: markets 页 `.mkt-table tbody tr`
- 每次启动 Playwright 新 context = **全新账户($10000)**(临时 profile); 正常浏览器是持久 localStorage

## localStorage binance-sim-v1

```json
{
  v:1, usdt:10000, balances:{}, openOrders:[], history:[], positions:[],
  closedPositions:[], favorites:["BTCUSDT","ETHUSDT"], achievements:[],
  stats:{trades,wins,losses,realized,fees,volume,dailyPnl,day},
  settings:{sound,vibrate,theme,swapColor},
  challenge:{date,remaining,active,usdt,balances,coin,startedAt,best},
  lastSym:{trade,futures}, lastMode, lastSignin, welcomed, events:[]
}
```

## 已验证脚本

| 文件 | 验证内容 |
|------|---------|
| explore_ui.py | frame 定位, localStorage 结构, 按钮清单 |
| explore_trade2.py | 交易页全部按钮/输入框 |
| probe_order.py | 市价下0.0002失败(最小额) |
| probe_order2.py | 市价模式切换(只剩 fQty) |
| probe_order3.py | ✅市价10U买入成交 + 限价挂单 |
| probe_futures.py | ✅10x开多50U, positions 结构 |
| probe_cycle.py | ✅完整闭环: 开→读#tkPrice→平 |
| ui_src.js / store_src.js | 源码存档 |

## 下一步(可做)

- [ ] bot 库: 读状态(localStorage) + 价格(#tkPrice/行情表) + 市价开/平
- [ ] 策略: 类似 FX 的 15s 兜底 + 动量, 但要处理 **强平**(高杠杆爆仓风险)
- [ ] 挑战模式(challenge): 有活动期限限制, 独立资金