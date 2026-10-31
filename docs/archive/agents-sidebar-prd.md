# Agents 侧栏可识别性与归属视觉 PRD（已归档）

> **已归档：本 pane 分组 / 修改 Herdr 核心的历史提案已被 [workspace 插件设计](../design.md)取代。**
> 下文保留当时的假设、需求与验收目标，不代表现有插件的功能、实现状态或已验证结论。当前文档入口见 [文档索引](../README.md)。

- 历史状态：提案，待评审
- 版本：0.1
- 产品范围：Herdr local 中 Agents 侧栏的 session 命名、pane 归属展示和颜色标识
- 配套设计：[Agents 侧栏产品设计](product-design/agents-sidebar.md)

## 1. 产品摘要

为 Agents 侧栏增加稳定、可扫描的工作上下文：当一个 local 同时运行多个 workspace、tab、pane 和 agent session 时，用户可以直接看到 session/task 名称，并能快速判断它属于哪个具体 pane 和项目。Grouped 模式按 pane 形成视觉分组；归属色绑定 pane，agent 状态和 agent kind 保持独立表达。

本 PRD 解决信息识别和视觉层级问题，不改变 agent 的运行、消息发送、pane 布局、session 生命周期或工作区控制语义。

## 2. 背景与问题

用户的实际工作方式是：在一个 local 中打开多个不同项目，每个项目下运行多个 agent session，并在不同 pane 中同时推进任务。当前 Agents 区域虽然可以分组，但存在以下问题：

- `Local` 被反复显示，实际项目上下文不够突出。
- session 行常显示 `Pi`、`Claude` 等 agent kind，而不是用户正在处理的任务名称。
- workspace/tab/pane 序号和 agent session 信息分散在行内，用户需要人工对照。
- 不同 pane 的 agent 行缺少稳定、明确的视觉归属信号。
- 用户无法在不聚焦 pane 的情况下确认“这个 agent 到底属于哪个项目”。

截图 OCR 可读到的现有模式包括 `Local`、`[1] wardrobe`、`[2] marking`、`[3] trade-review`、`agents`、`grouped`，以及重复出现的 `pi`/`claude`。这些文字说明当前已经有 local、workspace/tab 名称和 agent 类型信息，但信息层级尚未围绕用户的识别任务组织。

## 3. 目标

### 3.1 产品目标

1. 识别目标：用户在 Agents 侧栏中看到任意 agent 行时，能在 2 秒内回答“它属于哪个 pane/项目、正在做什么”。
2. 命名目标：有用户设置的 session/task 名称时，主显示名称必须是该名称；未设置时直接回退到 Pi/Claude 等 agent kind。
3. 归属目标：Grouped 模式按 pane 分组，pane 标题中包含 workspace/tab 上下文。
4. 视觉目标：不同 pane 使用稳定的颜色标识，同时保留文字和图形辅助信息。
5. 兼容目标：旧 session、无名称数据、无颜色数据或 local 断连时继续可见，不因新增展示字段导致启动或控制失败。

### 3.2 非目标

- 不重构 Herdr 的 workspace、tab、pane 或 agent 生命周期模型。
- 不改变 agent 的运行状态判定、消息投递、控制命令或焦点策略。
- 不强制 session 名称全局唯一。
- 不把颜色用于权限、状态、健康度或控制语义。
- 不在本期实现跨设备同步、session 历史搜索、任务管理或新的调度系统。
- 不把底层 session ID/path 直接暴露给普通用户作为名称。

## 4. 用户与使用场景

### 场景 A：同一 local 多项目并行

用户在 wardrobe、marking、trade-review 等 workspace 中同时运行 agent。用户打开 Agents 侧栏，希望通过 pane 标题、项目上下文和颜色快速定位某个 agent。

### 场景 B：同一项目多个任务

一个 workspace 中有多个 agent session，分别执行“实时行情后端实现”“前端实现”“图表实时增量实现”等任务。用户希望看见任务名，而不是多个难以区分的 `Pi`。

### 场景 C：未命名 session

用户没有设置 session/task 名称，或历史 session 没有新字段。系统应显示 agent kind 或可解释的默认名称，而不显示空白、不显示 UUID/path。

### 场景 D：恢复和连接异常

Herdr server 重启、pane 移动、workspace 断连或 agent 状态未知。Agents 侧栏仍需遵守现有状态语义，不将缓存名称误认为可操作的 live agent。

## 5. 术语与概念模型

| 概念 | 本 PRD 中的定义 |
| --- | --- |
| `local` | 当前本地 Herdr server/session 的运行边界。若存在多个 local，需要作为跨来源消歧信息。 |
| `workspace` | 一组 tabs 的工作区，通常对应项目/工作主题；作为 pane 的项目上下文。 |
| `tab` | workspace 内的终端标签页；作为 pane 的位置上下文。 |
| `pane` | tab 内的终端区域，agent 运行在其中；是 Agents Grouped 视图的主要分组单位。 |
| `agent session` | agent 的会话身份、显示名称和运行状态。底层 ID/path 仅用于内部关联。 |
| `agent kind` | Pi、Claude 等运行时类型；是辅助信息和未命名回退，不是默认主标题。 |
| `display name` | 面向用户的可读名称，可由用户设置；未设置时主标题回退到 agent kind。 |
| `grouped` | Agents 侧栏当前的分组显示模式；本期将其分组锚点明确为 pane。 |

推荐关系：`local → workspace → tab → pane → agent session`。UI 以 pane 为分组锚点，pane 标题中呈现 workspace/tab 上下文。

## 6. 功能需求

### FR-1：Pane 分组

**优先级：P0**

- Grouped 模式按 pane 分组，不把多个 pane 的 agent 混在一个只写 `Local` 的列表层级下。
- 分组标题优先显示 pane label；没有 label 时显示 `workspace / tab / Pane <number>` 的短路径。
- 分组标题可以显示当前 agent session 数量。
- pane 分组顺序沿用当前产品排序，或按稳定规则排序；实现不能因颜色分配改变排序。
- 用户折叠/展开状态沿用现有侧栏行为并持久化到现有 UI 状态存储（如已有）。

**验收：**

- Given 同一个 local 下存在多个 workspace 和 pane，When 打开 Grouped Agents，Then 每个 pane 都有独立可识别的分组标题，且每个 agent session 只出现在其真实 pane 分组中。
- Given 两个 pane label 相同，When 渲染列表，Then 不得把其 agent 合并成一个实体；必须保留 local + workspace/tab 上下文 + stable pane identity 以区分。

### FR-2：Session/task 主名称

**优先级：P0**

- 每个 agent 行主标题优先显示已设置的 session/task display name。
- display name 不存在、为空白或无效时，直接回退到 agent kind，例如 `Pi` 或 `Claude`；agent kind 也未知时显示 `Agent`。
- pane label 只用于 pane 分组标题，不代替 session 主标题。
- 没有任何可用信息时显示 `Agent`，不得显示空标题。
- 主标题不得直接显示 session ID、UUID、session 文件路径或内部 JSON 值。
- 名称截断不改变存储值；完整值可通过 tooltip、focus hint 或无障碍标签获得。

**验收：**

- Given session display name 为“实时行情后端实现”，When 渲染 agent 行，Then 行主标题为“实时行情后端实现”，且 `Pi` 只出现在辅助信息。
- Given display name 为空且 agent kind 为 Pi，When 渲染 agent 行，Then 行主标题至少为 `Pi`，不出现空白行或 UUID/path。
- Given display name 只有空格，When 重新渲染，Then 按未设置处理。

### FR-3：Pane 归属展示

**优先级：P0**

- pane 分组标题负责表达具体 pane 归属，并包含 workspace/tab 项目上下文。
- pane 有用户可见 label 时优先显示；否则显示短位置回退，例如 `marking / engineering-gap-plan / Pane 1`。
- agent 行只需显示 session/task 名称、agent kind 和状态，避免每行重复完整 pane 路径。
- pane 移动后，归属按实时结构更新；不能永久依赖旧 pane ID 或显示名称。
- agent session 脱离 pane 或状态未知时，遵循现有 stale/unknown 状态，不制造可聚焦的假行。

**验收：**

- Given 一个 Pi session 位于 workspace `marking` 的 tab `scoring-input-wiring` 的 pane 1，When 渲染，Then 用户能看到 pane 分组标题、`marking` 项目上下文、session 主名称和 agent kind。
- Given pane 被移动到另一个 workspace，When 数据更新，Then agent session 移动到新的 pane 分组并按当前 pane 归属色显示，且不保留旧分组中的重复 live 行。

### FR-4：Pane 归属颜色

**优先级：P0**

- 颜色表达 pane 归属，不表达 agent kind 或运行状态。
- 同一 local + stable pane identity 的分组标题和组内 agent 行使用同一颜色 token。
- pane 重命名、agent 排序变化、agent 加入/退出不得导致其它 pane 颜色重新洗牌。
- 颜色耗尽时允许复用颜色，但仍必须显示 workspace 文本、分组边界和非颜色辅助标识。
- 颜色在浅色/深色主题中分别映射到可辨识色值；不使用随机色。
- 颜色必须配合分组标题、文字或形状，不能作为唯一语义。

**验收：**

- Given 3 个 pane 各有一个或多个 agent session，When 列表刷新或 agent 数量变化，Then 同 pane 的色标一致，不同 pane 在色板容量内可区分。
- Given 颜色 token 已被分配，When pane label、workspace 名或列表排序变化，Then 颜色 token 不因显示文本变化而漂移。
- Given 用户无法区分某两种颜色，When 查看 pane 路径文字和分组结构，Then 仍能独立识别 pane 归属。

### FR-5：名称编辑

**优先级：P1，除非现有实现已有命名入口，则提升为 P0 接入项**

- 若当前系统已有 session/task 命名能力，Agents 侧栏直接使用该能力的 display name。
- 若没有，提供行级“重命名”入口，支持 Enter 保存、Escape 取消，清空恢复自动名称。
- 名称允许重复；重复名称需依靠 pane 分组和 workspace/tab 辅助信息区分。
- 保存失败、连接断开或并发冲突时，不得静默丢失用户输入；显示可重试反馈并保持当前已知值。
- 最大长度、允许字符和跨 local 持久化范围需与底层存储限制一致；在源码确认前不写死任意字符集。

**验收：**

- Given 用户将 session 改名为“后端 API 重构”，When 保存成功并刷新列表，Then 主标题仍为该名称。
- Given 用户清空名称，When 保存成功，Then 主标题恢复到规定回退名称。
- Given 保存请求失败，When UI 收到错误，Then 旧名称不会被错误覆盖，用户可以重新提交。

### FR-6：兼容旧数据和未知状态

**优先级：P0**

- 缺少 display name、归属色或新字段的旧记录必须正常显示。
- 读取缺失字段时使用本 PRD 的回退规则，不要求一次性迁移所有历史 session。
- 新字段写入失败不应阻断 agent 启动、pane 控制或已有导航；按已有数据一致性策略降级。
- local/workspace/session 断开、加载中、stale、unknown 和 empty 状态必须保持可理解的状态文案/图标。
- 缓存显示名称不得赋予 pane 聚焦、发送、关闭等控制权限。

## 7. 显示规格

### 7.1 推荐行模型

```text
<归属色标> <workspace> / <tab> / <pane label or Pane number>
             <session/task display name>                     <status>
             <agent kind>
```

推荐优先级：

1. pane 分组标题及其 workspace/tab 上下文
2. session/task display name
3. 未命名时的 agent kind
4. 状态图标/状态文案

`Local` 仅在跨 local 或其它上下文不足以消歧时显示；当前 local 内的 pane 标题不重复渲染它。

### 7.2 长文本

- 主标题单行显示，按可用宽度截断。
- 辅助信息可折叠、截断或仅在 hover/focus 时显示。
- 行高、色标宽度和状态区域保持稳定，避免名称更新造成列表跳动。
- 完整名称、workspace、tab、pane、agent kind 和状态应进入可访问性标签或详情提示。

## 8. 数据模型与持久化要求

实现阶段至少需要把以下展示模型映射到真实代码结构：

```text
AgentListItem {
  localId: StableId
  workspaceId: StableId
  workspaceDisplayName: string | null
  tabId: StableId | null
  tabDisplayName: string | null
  paneId: StableId
  paneDisplayName: string | null
  paneColorToken: ColorToken | null
  sessionId: StableId | null
  sessionDisplayName: string | null
  agentKind: string | null
  agentStatus: AgentStatus
}
```

要求：

- `workspaceId`、`paneId`、`sessionId` 使用底层稳定身份；display name 与 ID 分离。
- `paneColorToken` 绑定 local + 当前可保证稳定的 pane identity；不绑定 pane label、workspace 名或当前索引。
- 缺少 session display name 时读取时计算回退，不把回退文本写回用户名称字段。
- pane 移动、workspace 重建、server 重启后的稳定性以当前 Herdr API/持久化保证为准；若某 ID 不跨重启稳定，必须使用已有恢复关联机制而非仅靠 label。
- 任何 display-only metadata 写入都不能改变 pane agent 状态权威、控制权限或生命周期记录。

## 9. 可访问性与非功能要求

- pane 归属色与状态色不能复用同一语义通道。
- 至少提供一种不依赖颜色的归属信号：pane 分组标题、色标形状/位置或 workspace/tab/pane 文字上下文。
- 文本与背景满足主题下的对比度要求。
- 键盘可以遍历分组和 agent 行，并看到清晰焦点态。
- tooltip/详情提示对鼠标和键盘 focus 可用。
- 大量 agent 时列表滚动、分组折叠和状态刷新不应造成明显卡顿；具体性能预算待源码与基线确认。
- 名称更新和实时状态刷新不应改变当前选中实体，除非实体确实已被删除或失去控制能力。

## 10. 迁移、发布与回滚

### 10.1 迁移

- 首版读取旧数据时允许 display name、color token 缺失。
- 首版可在内存中计算颜色和回退名称；持久化策略需结合现有 UI 状态存储确认。
- 若需新增持久化字段，采用向后兼容的可选字段，不要求旧客户端理解新字段。
- session/workspace 的可见名称不应写入项目代码仓库或用户工作树。

### 10.2 发布

建议分两阶段：

- Phase 1：先接入 pane 分组、主名称优先级、workspace/tab/pane 归属标题和只读稳定颜色。
- Phase 2：接入重命名入口、颜色自定义或更细粒度的 pane 管理（仅在 Phase 1 验证必要后）。

如当前代码的 Agent panel 没有独立 feature flag，则至少保留旧显示逻辑的可回退分支，确保未知字段和旧数据不会阻断主界面。

### 10.3 回滚

- 回滚只影响 Agents 侧栏的展示层，不删除已有 session 名称或 pane metadata。
- 如果颜色映射异常，可关闭颜色装饰，继续显示 pane 分组和文字归属。
- 如果命名字段读取异常，回退到 agent kind，不影响 agent 控制操作。

## 11. 指标与验证

本期最小验证以可观察任务成功率为主：

1. 归属识别成功率：给用户展示混合 workspace/pane 的 Agents 列表，用户能正确指出任意 agent 所属 pane 和项目的比例目标 ≥ 95%。
2. 任务识别成功率：用户能正确指出 session 当前任务名或明确回答“未命名”的比例目标 ≥ 95%。
3. 误聚类率：一个 agent 出现在错误 pane 分组中的比例为 0。
4. 稳定性：列表刷新、排序变化、重命名和状态变化不导致颜色在非目标 pane 间漂移。
5. 可访问性：无颜色辅助时仍可通过文字/分组完成归属判断；键盘可访问所有 agent 行和命名操作。

若暂时没有用户研究基础，先用固定 fixture 和视觉回归测试验证上述行为，再补充真实用户测试。

## 12. 验收场景总表

| 编号 | 场景 | 期望结果 |
| --- | --- | --- |
| A1 | 一个 local、多个 workspace 和 pane | Grouped 模式按 pane 分组，所有 agent session 归属正确。 |
| A2 | 有 session 名称 | 主标题显示 session/task 名称，agent kind 降为辅助信息。 |
| A3 | 无 session 名称 | 主标题回退为 Pi/Claude 等 agent kind，不显示空白/UUID/path。 |
| A4 | 两个 pane label 相同 | 仍为两个分组，使用 workspace/tab/path 和 stable pane identity 消歧。 |
| A5 | session 名称重复 | 允许重复，通过 pane 分组和位置上下文区分。 |
| A6 | pane 移动 workspace | agent session 移动到当前 pane 分组并按当前归属色显示，无旧分组重复。 |
| A7 | pane/workspace 改名 | 分组文字变化，颜色 token 不因显示名变化而漂移。 |
| A8 | 列表排序/agent 增删 | 非目标 pane 颜色不漂移；选中状态按实体保持。 |
| A9 | 颜色耗尽/色觉差异 | 颜色可复用，文字分组和结构仍可识别。 |
| A10 | server 重启/旧记录 | 缺失新字段时正常回退；未知/断连状态不被伪装成 live。 |
| A11 | 名称保存失败 | 旧值保留，错误可见，用户可以重试。 |
| A12 | 窄侧栏和长名称 | pane 标题、session 主名称和状态不重叠；长辅助信息可通过 tooltip/辅助标签查看。 |

## 13. 依赖与风险

### 依赖

- Herdr 当前 Agent panel 的真实源码或可定位的发布仓库。
- 当前 agent list/grouped view 的数据接口和排序策略。
- workspace/tab/pane/session 的稳定 ID 与 display-only metadata 能力。
- 当前主题、状态图标和侧栏布局约束。

### 风险

- “session 名称”可能同时指 agent session ID、pane label、tab label 或用户任务名；不先完成字段语义映射，容易把内部寻址名暴露给用户。
- workspace、tab、pane 的 label 可能可变且不唯一，不能作为唯一关联键。
- pane identity 是否跨移动和重启稳定，决定颜色映射是直接持久化还是按实时 identity 重新解析；不能依靠可变 pane label 猜测。
- 当前 local 的侧栏可能只呈现当前 local；多 local 的消歧规则需要结合真实 UI 决定。
- 直接读取运行时缓存可以验证实例结构，但不能替代源码/API 的持久化与恢复契约。

## 14. 开放问题

1. 当前代码中的“group”实际按 local、workspace、tab 还是其它键聚合？
2. 用户所说的“session 名称”对应哪个现有字段或交互入口？
3. pane identity 在 Herdr 当前版本中是否能作为稳定颜色键；若不能，需要哪一种 display-only metadata 持久化方案？
4. pane 分组标题中显示完整 workspace/tab 路径的长度和截断策略是什么？
5. 重命名是否属于本期，还是只消费已有 session 名称？
6. 颜色是否需要用户自定义，还是自动稳定色即可？本期默认自动稳定色。
7. 现有主题是否已有语义色板和对比度约束？
8. 是否需要跨 local 的统一 Agents 视图？
9. 真实源码位于何处，以及本需求最终应提交到哪个 Git repository？

## 15. 变更记录

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| 0.1 | 2026-10-30 | 基于用户截图、当前 Herdr 运行时快照和只读调查形成初稿。 |
