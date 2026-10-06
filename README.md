# FX 简单! 自动交易机器人 (fx-simple-trading-bot)

针对 **B 站玩具小游戏「FX 简单!」**（[bilibili.com/toy/fx-simple](https://www.bilibili.com/toy/fx-simple/index.html)，模拟账户模式）编写的自动化交易机器人。

> ⚠️ 这是游戏，不提供真实交易。仅供学习 Playwright 自动化与量化交易思路，请勿用于真实外汇市场。

## 玩法

- 只交易 **EUR/USD** 一个货币对
- 疯狂高频持仓：最多同时 5 个仓位
- 每笔保证金 $500，杠杆 20x（名义 $10,000）
- 止盈 +1%（快速落袋）
- 时间兜底：持仓 **15 秒**未盈利即平仓（实测比 10s/30s 均衡）
- 无止损（游戏允许死扛，靠时间兜底控制）

## 快速上手

```bash
pip install playwright
playwright install chromium
python3 strategy_v4.py
```

会打开浏览器窗口（headless=False），可实时观看交易过程。

## 文件结构

```
bot.py          # FXBot 类：浏览器控制 + localStorage 事件钩子
fx_lib.py       # 核心交易函数（开仓/平仓/动量/蜡烛）
strategy_v4.py  # 主策略（15s 时间兜底，默认参数）
EXPERIMENTS.md  # 全部测试记录（策略迭代历史）
verify_base.py  # 基函数验证测试
```

## 测试结果（模拟账户，3 分钟/次）

| 策略 | 盈亏 | 备注 |
|------|------|------|
| 纯 15s 时间兜底 | +3.72% / +5.59% | 两次平均 +4.66% ✅ |
| 纯 30s 时间兜底 | +5.42% | 胜率 86%，均笔最大 |
| 总浮亏熔断 3% | +0.99% | 防拖死但连坐赚钱仓 |
| 动量反转平仓 | +1.09% | 3 根 K 线动量太噪音 |

详见 `EXPERIMENTS.md`。

## 免责声明

本项目仅用于 B 站「FX 简单!」模拟数据的自动化玩法研究。市场有风险，任何策略都不能保证盈利。