# 更新日志（CHANGELOG）

## [v1.0.0] - 2026-11-18

### 新增功能
- 正式发布 **汇芯朋友圈文案自动化工坊（huixin-moments-writer）**。
- **6 大主流行业原生支持**：`AI与一人公司`、`财税企服`、`家装本地`、`口腔医美`、`法律咨询`、`母婴消费`，内置各行业高转化切口、受众错配避坑与合规红线。
- **6 大朋友圈高转化内容类型**：`生活洞察`、`实战案例`、`反常识破局`、`软性种草`、`观点金句`、`信任背书`。
- **真实语料蒸馏引擎**：基于 7,253 条（2012–2026）真实朋友圈数据库分析提炼，固化「短段落呼吸感、生活切口转商业洞察、纯文本零乱码」规范。
- **双脚本零依赖工具链（L0 全平台直用）**：
  - `scripts/moments_planner.py`：支持单条创作骨架生成、一周 6 天黄金配比排期生成。
  - `scripts/moments_check.py`：支持去 AI 味、首行防截断、6 行业合规红线及双文案防折叠相似度校验。

### 致谢与兼容
- 纯 Python 3 标准库实现，零外部二进制依赖，支持 Windows / macOS / Linux 全平台直用。
- 方法论致谢：借鉴 GitHub 开源社区 `mengke-wang/wechat-anti-fold`（防折叠变体思路）、`kangarooking/viral-copywriting-skill`（好友对话开头法）、`AlexLaoBai/wechat-article-writing-skill`（MIT，全自动与引导双模式）。
