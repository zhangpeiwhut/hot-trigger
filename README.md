# hot-trigger

`hot-trigger` 是一个 **protocol-first（协议优先）** 的事件驱动热点触发系统。
它把「平台抓取」「热点触发」「AI 分析」「是否参与」拆成统一协议，任何平台都只是 Adapter。

## 核心设计

### 1) 统一 TrendSource 协议
平台仅需实现：
- `platform_id: str`
- `fetch_snapshot() -> TrendSnapshot`

MVP 已内置 `xhs`（小红书）实现，其他平台（抖音/微博/Twitter/Reddit）只需新增 adapter。

### 2) 统一 ContentUnit 抽象
`ContentUnit` 是跨平台通用的热点内容单元，字段包括：
- `unit_id`（跨快照稳定 hash）
- `title`、`url`、`rank`、`heat_score`
- `content_type`（text/image/video/mixed）
- `text_payload`、`media_payload`
- `author`、`tags`
- `raw`（平台原始数据）

### 3) 统一 Trigger → Analyze → Decide 流水线
- **Trigger（确定性）**：使用 YAML 配置驱动，输出 `TriggerEvent`
- **Analyze（概率性）**：LLM 生成 `AnalysisArtifact`，纯数据输出
- **Decide（确定性）**：可解释打分（0-100）+ `GO/WAIT/NO`

所有产物都是结构化数据，Action 只负责消费 Decision 结果并输出（控制台 + 文件）。

---

## 项目结构

```text
hot_trigger/
  adapters/xhs.py            # XHS 平台适配器（TrendSource 实现）
  triggers/engine.py         # YAML 驱动 trigger 引擎（new/rank/spike/keyword/cooldown）
  analysis/llm_client.py     # 平台无关 LLM client 抽象（OpenAI compatible）
  analysis/analyzer.py       # TriggerEvent -> AnalysisArtifact
  decision/engine.py         # 确定性评分与 GO/WAIT/NO 结论
  actions/output.py          # 控制台 + json/markdown 输出
  pipeline.py                # snapshot -> trigger -> analysis -> decision
  cli.py                     # hot-trigger init/run/test
  config.py                  # YAML 配置模型
```

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## CLI 使用

### 1) 初始化配置

```bash
hot-trigger init
```

将生成 `config.yaml`。

### 2) 运行完整流水线

> 必须提供 LLM Key（默认读 `OPENAI_API_KEY`）

```bash
export OPENAI_API_KEY=xxx
hot-trigger run --config config.yaml
```

执行流程：
`snapshot -> trigger -> analysis -> decision -> output`

输出目录（默认 `output/<timestamp>/`）包含：
- `result.json`
- `result.md`

并自动维护：
- `output/last_snapshot_<platform>.json`（上次快照）
- `output/.cooldown.json`（跨运行 cooldown）

### 3) 用指定快照测试

```bash
export OPENAI_API_KEY=xxx
hot-trigger test --config config.yaml --snapshot examples/xhs_snapshot.json
```

## Trigger 配置（YAML 驱动）

`config.yaml` 中 `triggers` 字段控制以下内置触发器：
- `new_entry`
- `rank_jump`
- `heat_spike`
- `keyword_match`
- `cooldown`

示例：

```yaml
triggers:
  enabled: true
  min_jump: 5
  min_spike: 25
  keywords: ["AI", "效率"]
  cooldown_minutes: 60
```

## Decision 评分维度（可解释）

- 领域相关性
- 差异化空间
- 参与成本
- 风险与合规
- 热度时效性

输出字段：
- `ride_score`
- `verdict`（GO / WAIT / NO）
- `rationale`
- `suggested_comment`
- `suggested_post_outline`

## 如何新增平台（实现 TrendSource）

1. 在 `hot_trigger/adapters/` 新建如 `douyin.py`。
2. 实现 `TrendSource` 协议：
   - `platform_id`
   - `fetch_snapshot()`
3. 将平台原始数据映射成统一 `ContentUnit`。
4. 在 `hot_trigger/bootstrap.py` 的 `build_source` 注册新平台。

这样无需修改 Trigger/Analysis/Decision 核心逻辑。

## 注意

- 当前版本不会自动发帖，仅输出结构化决策建议。
- LLM 接口为 OpenAI 兼容协议，默认走 `/chat/completions`。
