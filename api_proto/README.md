# API 直调线路（已放弃 ❌）

> ⚠️ **此线路已放弃（2026-10-07）**：尝试绕过 DOM 模拟点击、直接用 JS 注入调用游戏内部函数，**最终行不通**，原因见下。主线路（DOM 模拟点击）完全不受影响，照常可用。

## 想法

游戏 `app.js` 是 `(() => { ... })()` 闭包，内部函数（`openPosition` / `closePosition` / `state`）外部不可达。

通过 **Playwright route 拦截 app.js 响应**，在闭包结尾注入：

```js
window.__game = {
    openPosition: openPosition,
    closePosition: closePosition,
    getState: () => state,
    getSim: () => sim,
    setPair: (id) => { state.pair = id; },
    save: save,
};
```

之后直接 `frame.evaluate("window.__game.openPosition('long')")` 调用**游戏原生函数**，
不再模拟点击 DOM。手续费/保证金/杠杆/强平校验全部走游戏自己的逻辑。

## 验证结果（PoC 成功 ✅）

```
暴露检查:  {"exposed": true, "has_open": "function", "has_close": "function"}
直调开仓:  before=0 → after=1
           (side=long, entry=1.0932, margin=500, leverage=20, fee=$1.50)
直调平仓:  before=1 → after=0
```

游戏原生生成仓位（含手续费计算），比 DOM 模拟点击快且可靠。

## 实现要点

1. **route 拦截**：`**/fx-simple/**/app.js*`，用 urllib 同步抓取源码（sync API 里
   `route.fetch()` 的 response 会被 dispose，不能用）
2. **gzip 处理**：响应是 gzip 压缩，需解压 → 篡改 → 直接 `route.fulfill(body=明文)`
3. **依赖版本**：注入代码引用 `openPosition/closePosition/state/sim/save/render`，
   都必须是 app.js 闭包内声明的函数/变量（`v=3.0.1` 验证 OK）
4. **state 是闭包内的实时对象**：`getState()` 直接读内存里的 state，
   比解析 localStorage（100KB JSON）快得多

## 结论：行不通 ❌

**为什么放弃：**

1. **游戏没有后端**（已验证）：交易/行情/新闻全是浏览器 JS 本地算的，浏览器只是 JS 宿主，不存在"API 直连"
2. **JS 注入直调内部函数**（route 篡改 app.js 暴露 `window.__game`）PoC 单次开/平仓能成功，但：
   - 直接改闭包 `state.margin/leverage` → 游戏 UI 计算出 NaN（脏状态）
   - `reset()` 的 `page.reload()` → 重载瞬间闭包与存档不一致，UI 出 NaN
   - 多次实验导致游戏运行时频繁 NaN，不稳定，无法跑完整策略
3. 最终结论：**模拟点击虽然笨但稳定**，主线方案（DOM 模拟点击 + localStorage 读状态）是唯一可靠路线

**留下可复用的东西：**

- 游戏默认参数就是 `margin=500 / leverage=20 / 手续费$1.5`（`accountSeed()`），主线策略参数无需额外设置
- 行情确认为本地随机游走（`tickSim()`），且 `app_src.js` 源码存档可供参考

## 文件

| 文件 | 说明 |
|------|------|
| `bot_inject.py` | FXBot + route 注入版 bot（已废弃，勿用）|
| `poc_inject.py` | PoC：单次直调开/平仓验证（成功但不稳定，废弃）|
| `check_api.py` | __game API 检查（margin/leverage 默认值确认）|
| `check_default.py` | 默认参数直调开/平仓验证（废弃）|
| `strategy_inject.py` | 直调版策略（无法跑完整轮，废弃）|
| `netprobe*.py` / `app_src.js` | 网络探针 + 源码分析（有价值的证据存档）|