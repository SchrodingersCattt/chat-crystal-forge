# 2609 CrystalForge 可执行完成计划

## 摘要

在 `learn-ai-basis-2609` 的 `feat/native-inspection-chat` 分支上，将现有只读检查扩展为共享的“检查 → 决策 → 加氢/无序 → 导出重载 → 完成判定”流程。Web、TUI 和独立 HTTP API 都读取同一份 SQLite 快照；全流程不安装、不调用 `mattervis-saas`。

## 关键实施

1. **锁定依赖宿主**
   - 审查并提交 `external/mattervis` 当前工作区中与 workbench、显示、扩展宿主及其测试相关的改动，推送现有远程并记录完整 SHA。
   - 父仓库将 MatterVis gitlink 更新到该 SHA；MolCrysKit pin 更新为 `f2188c1`。
   - 排除密钥、缓存、`.mattervis-objects/`、`.parent-objects/`、`.venv/` 等文件。
   - 重装 editable 依赖，验证导入路径和父仓库、MatterVis 测试。

2. **建立准备状态和进程边界**
   - 在现有 SQLite 中加入 `revisions`、`decisions`、`jobs`、`exports` 表，保留原始 CIF 副本和操作谱系。
   - 新增 `preparation.py`：子进程只接收工作区 CIF 路径及已校验参数，通过 stdout 返回 JSON；父进程执行修订匹配、迟到结果丢弃和状态发布。
   - 启动时把未完成的 `working/running` 状态标记为 `interrupted`；同一修订运行中拒绝重复变异提交；连续无进展转为 `blocked`。

3. **实现科学操作和严格证据**
   - 加氢覆盖无氢和部分有氢输入；moiety、质子化、电荷、位点或公式参考含糊时返回 `awaiting_decision`，不猜测。
   - 无序仅使用 `scan_cif_disorder` 与 `generate_ordered_replicas_from_disordered_sites`，支持 `optimal`、`random`、`enumerate`、数量、seed、coupled；记录请求数、返回数、不同 source-index 数和重复。
   - `optimal` 明确描述为占有率/冲突图贪心，不称为能量优化。
   - 导出到 `exports/` 后独立重载，按同一六项 MCK 检查和用户确认的 `reference_formula` 复核；缺项、跳过、异常、空报告、缺文件均不得通过。
   - 注册修订或策略变化会使旧检查和旧导出过期；MatterVis 当前结构与活动修订不一致时要求重新 `/load`。

4. **统一接口和完成门**
   - 增加 `/complete-h <id>`、`/disorder <id> <method> <count>`、`/export <id>`、`/finish`，并为模型工具提供同等严格的 JSON Schema。
   - 扩展 snapshot，使每个输入呈现未检查、等待决定、运行中、失败、中断、已导出等状态。
   - `finish` 只在批次非空、所有声明输入均有交付记录、所有应交付 CIF 已独立重载且六项检查真实通过、修订和策略均未过期时放行。阻塞记录可以保留和展示，但不能使整批标记为 passed。
   - Web、TUI、`serve` 只渲染共享快照，显示 `awaiting decision`、`blocked`、`interrupted`、`passed` 等状态。

5. **演示与文档**
   - 将本计划原样保存为 `_tmp/2609-executable-plan.md`。
   - 编写 `examples/DEMO.md`，用 `mat-chat ui`、`mat-chat tui`、`mat-chat serve` 完成 DAP-4 主路径、拒绝路径、重启恢复和同 session 对照。
   - 更新 `README.md`、`docs/forge-api.md`、验证记录；明确渲染服务属于另一私有仓库，本项目不调用 `mattervis-saas`。
   - API key 仅留在本地进程，不进入浏览器、SQLite、日志或演示文稿。

## 验证

- 父仓库：`python -B -m pytest tests`、`ruff check src tests`。
- MatterVis：在子仓库运行相关 app/extension 测试；保留 DAP-4 oracle 的独立失败记录，不修改断言放行。
- 新增覆盖：无氢/部分氢、含糊 moiety、坏导出、重载后修订失效、三种无序策略、seed/coupled、短少/重复、重启中断、防重复提交、迟到结果、空批次、跳过检查和双前端状态一致性。
- 手工验收：浏览器完成 DAP-4 主路径和一次被拒绝的 `finish`，再用 TUI 打开同一 session；可选验证 HTTP `/healthz`、建 session、上传、inspect，确认无 SaaS 路由。

## 假设与边界

- 当前 MatterVis 工作区改动按计划作为宿主提交候选，提交前只保留相关文件。
- 不实现计算输入、能量优化、计算提交、100 结构基准或多 agent。
- 原始输入字节永远保留；演示中 DAP-4 原 CIF 的 SHA-256 必须保持不变。
- 当前仍处于 Plan Mode；本轮只完成计划定稿，不写文件、不提交、不推送。
