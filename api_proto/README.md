# API 直调线路（实验性，独立于主线）

> ⚠️ 这条是**另一条实现线路**，与主线（DOM 模拟点击）完全隔离。
> 主线 `bot.py` / `fx_lib.py` 保持不变，本目录是独立原型。

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

## 文件

| 文件 | 说明 |
|------|------|
| `bot_inject.py` | FXBot + route 注入版 bot（主线 bot.py 加注入逻辑的副本）|
| `poc_inject.py` | PoC：篡改 + 直调开仓/平仓验证 |
| `netprobe2.py` | 网络探针：抓所有请求，证明没有行情/交易后端 |
| `netprobe3.py` | 源码分析：app.js 只有 frankfurter 一个外部 API |

## 待办（如果想接主线）

- [ ] 在 fx_lib 加 `open_position_fast()` / `close_position_fast()`（优先 `__game`，回退 DOM）
- [ ] 处理单仓/多仓平仓（游戏 `closePosition(id)` 是按 id 平，不是 index）
- [ ] 跑一轮完整策略对比两组性能