# Agents 侧栏产品设计（已归档）

> **已归档：本 pane 分组 / 修改 Herdr 核心的历史设计已被 [workspace 插件设计](../../design.md)取代。**
> 下文保留当时的设计假设与待确认项，不代表现有插件支持 pane 分组、名称编辑或全面主题适配。当前文档入口见 [文档索引](../../README.md)。

- 历史状态：提案，待产品与实现评审
- 版本：0.1
- 语言：中文；领域实体保留英文 canonical term
- 关联 PRD：[Agents 侧栏可识别性与归属视觉 PRD](../agents-sidebar-prd.md)

## 1. 背景

当用户在同一个 Herdr local 中同时运行多个项目和多个 agent 时，Agents 侧栏需要同时回答两个问题：

1. 这个 agent 正在做什么，或者对应哪个 session？
2. 这个 agent 属于哪个 workspace、tab 和 pane？

当前截图显示 Agents 区域提供 Grouped 视图，并以 Local、workspace/tab 序号和 agent 类型等信息组织内容。但在窄侧栏中，归属上下文被分散到多个短列，agent 行本身常只显示 `Pi` 或 `Claude`。用户需要来回对照才能判断某个 agent 属于哪个项目或 pane。

## 2. 设计目标

- 用户无需打开目标 pane，就能从 Agents 侧栏识别 session 的任务名称。
- 用户能清楚判断每个 agent 属于哪个 workspace 项目，以及需要时定位到具体 tab/pane。
- Agents 按具体 pane 形成稳定分组；不同 pane 使用可辨别的颜色标识。
- 颜色之外仍保留文字和状态图标，确保含义不依赖颜色。
- 窄侧栏中名称不重叠、不挤压状态，也不要求用户阅读内部 ID。
- 不改变 pane 布局、agent 执行或 session 生命周期语义。

## 3. 领域模型与术语

产品文档采用以下概念区分：

| 术语 | 定义 | 可见性建议 |
| --- | --- | --- |
| `local` | 当前本地 Herdr server/session 的运行上下文。它是运行边界，不是项目名称。 | 在跨 local 汇总或无法从所在面板推断时显示。 |
| `workspace` | Herdr 中组织 tabs 的工作区；通常对应一个项目或工作主题。 | 作为 pane 所在项目的上下文，不作为 agent session 的主分组。 |
| `tab` | workspace 内的终端标签页。 | 作为 pane 位置的次级上下文；有自定义名称时显示名称。 |
| `pane` | tab 内的终端区域，也是 agent 当前运行位置。 | Agents 的主要分组单位；显示用户可见 pane label 或位置描述。 |
| `agent session` | agent 的会话身份与运行状态。其底层 ID/path 不是面向用户的名称。 | pane 分组下的条目；有用户设置的名称时显示名称。 |
| `agent kind` | Pi、Claude 等 agent 类型。 | 未命名时作为主行回退；已命名时作为辅助信息。 |

推荐结构：`local → workspace → tab → pane → agent session`。Agents 的 Grouped 视图按 pane 分组，pane 组内列出当前归属的 agent sessions；具体一个 pane 可以承载多少 agent 以 Herdr 当前模型为准。没有 agent 的 pane 不出现在 Agents 列表中。

本结构基于 Herdr 运行时快照中可见的 workspace、tab、pane、agent 记录字段推导。目标目录当前没有 Herdr 源码，因此实现前必须核对这些字段在当前版本中的真实类型、生命周期和命名语义。

## 4. 信息架构

### 4.1 分组

- Grouped 模式以 pane 为分组单位；同一 pane 归属的 agent sessions 出现在同一个 pane 组中。
- 分组标题优先使用用户设置的 pane label；缺失时使用 `workspace / tab / Pane <number>` 的短路径。
- `Local` 仅作为运行来源上下文，不代替具体 pane 名称。
- workspace 与 tab 名称作为 pane 标题的项目路径，避免相同 pane 序号在不同项目中产生歧义。
- 分组默认展开；用户折叠状态保留现有行为。
- 每个分组标题可呈现 session 数量，便于在多个 pane 间快速扫描。

### 4.2 Agent 行

建议分组和行结构：

```text
[color-1] <workspace> / <tab> / <pane label or Pane number>
          Session / task name                     [working]
          Pi
```

视觉优先级：

1. pane 分组标题：用户可见 pane label 或包含 workspace/tab 上下文的位置名称。
2. 主名称：用户明确设置的 session/task display name。
3. 未命名回退：Pi、Claude 等 agent kind，符合用户未设置 session 名时仍显示 agent 类型的预期。
4. 状态：使用独立状态图标或现有 status indicator，不用 pane 颜色表示运行状态。

如果用户可见宽度不足以完整显示辅助上下文，先截断辅助上下文；主名称应在合理长度内优先保留。截断的完整名称和归属信息通过 tooltip 或可访问性标签提供。

### 4.3 名称优先级

显示名称与内部身份必须分开。agent session 主标题建议严格采用：

1. 用户明确设置的 session/task display name。
2. 未设置时回退到 agent kind，例如 `Pi` 或 `Claude`。
3. agent kind 也未知时显示 `Agent`。

pane label 不进入 session 主标题，而用于 pane 分组标题。这样既满足“命名了就显示 session 名，没命名就显示 Pi/Claude”，也保留具体 pane 归属。不要显示底层 session ID、UUID、session 文件路径作为名称。实现前需确认当前可用的用户设置名称字段；不能仅因 `agent_name` 是可寻址字段，就自动将它当成 session 标题。

### 4.4 归属信息

- pane label 作为 pane 分组标题；没有 label 时组合 `workspace / tab / Pane <number>`。
- workspace 与 tab 有用户自定义名称时优先显示；缺失时分别使用项目目录名、tab 序号。
- agent 行只显示 session/task 名称、agent kind 和状态，避免每个 agent 重复展示完整项目路径。
- 多 local 汇总视图中，在 pane 路径前加 local 名称或来源标记，消除同名 workspace/tab/pane 的歧义。
- 内部归属由 local + 当前 pane identity 判定，不能靠可变 label 关联。

## 5. 颜色与状态

### 5.1 颜色绑定

- 颜色表达 pane 归属，不表达 agent 类型、运行状态或健康程度。
- 同一 pane 下的 agent sessions 共用 pane 色标；不同 pane 在可用色板范围内使用不同颜色。
- 稳定键使用当前 Herdr 可保证稳定的 `(local identity, pane identity)`；不使用 pane label、workspace 显示名、当前排序位置或 agent 行序号。
- pane 重命名、agent 创建/退出或排序变化不得重新分配该 pane 的颜色。
- pane 被移动或重建后的颜色行为依赖 Herdr 对 pane identity 的保证；若移动会产生新 pane identity，则按新 identity 重新解析颜色，不依赖旧可变 label 猜测归属。
- pane 删除并重建后可获得新颜色。颜色只用于视觉识别，不作身份、权限或控制依据。

### 5.2 视觉应用

- 用 pane 分组标题的窄色条或色点作为主要归属信号；组内 agent 行可复用小色点形成连续视觉轨道。
- 不给整行铺大面积高饱和底色；选中态、焦点态和状态图标使用各自的视觉通道。
- 选择能在浅色、深色主题下辨识的有限语义色板，并通过文字标签/分组边界辅助颜色。
- 超出色板容量时允许重复颜色，但仍保留 pane 路径文本、分组边界和稳定排序。不可通过每次渲染随机挑色。
- 主题切换可改变色值，但不能改变 workspace 与颜色 token 的映射。

## 6. 交互

### 6.1 导航

- 选择 agent 行聚焦其当前 pane，并保持既有 Herdr 导航行为。
- 行上的状态、类型和归属仅为展示，不改变 agent 的控制目标。
- 键盘焦点、鼠标 hover 和当前选中态应与 pane 归属色可区分。

### 6.2 命名

- 若 Herdr 已有 session/task display name 设置能力，Agents 侧栏立即消费该值，不再要求用户重复配置。
- 若没有对应能力，本期需提供明确的重命名入口，并持久化到 agent session 的可展示名称字段；不能把寻址用的 agent 名称或底层 session ID 当成替代品。
- 建议通过行菜单的“重命名”命令进入行内编辑，Enter 保存、Escape 取消；清空名称恢复自动回退名称。
- 重复显示名称允许存在，因为 workspace、agent kind 和 tab/pane 辅助信息可消歧；不强制跨项目唯一。

重命名入口是否属于本期 P0 取决于代码中是否已有用户可设置的 session 名称。此项为 PRD 的实现前确认点。

## 7. 视觉草图

```text
AGENTS                                      Grouped

[color-1] [1] wardrobe / [3] wardrobe-app / Pane 1
          图像裁切修复                    [working]
          Pi

[color-2] [2] marking / [4] engineering-gap-plan / Pane 1
          scoring input wiring           [working]
          Pi

[color-3] [3] trade-review / [2] 实时复盘前端实现 / Pane 1
          Pi                              [idle]
```

草图重点：pane 是视觉分组锚点，标题直接暴露 pane label 或 workspace/tab/pane 路径；session/task 名称是 agent 行主标题；未命名时显示 agent kind。实际序号与状态字样沿用 Herdr 当前语义，不在此固定。

## 8. 边界状态

- 无 session 名称：显示 agent kind；不显示空占位或内部 ID。
- 名称为空白：按未设置处理。
- 超长名称：主标题视觉截断，完整名称可通过 tooltip/辅助标签读取。
- 同名 session：允许；通过 pane 分组和 workspace/tab 辅助信息区分。
- session 恢复但 pane 未恢复：不应根据缓存名称制造可聚焦的伪 agent 行；使用现有 stale/unknown 状态约定。
- agent kind 未知：显示 `Agent`，保留状态与归属。
- session 名称缺失：显示 agent kind，不使用 pane label 代替 session 名称。
- workspace/tab 名称缺失：按前述稳定位置回退显示。
- pane 被移动：按 Herdr 真实 pane 归属更新分组与归属色；旧 ID 不作为永久归属依据。
- local 断连：保留现有断连/重连状态表现，不把 offline 误作 idle/done。

## 9. 可访问性

- 颜色不得是唯一归属或状态信号。
- 每行的可访问性名称应包含主名称、agent kind、workspace/tab/pane 归属和状态。
- 所有交互支持键盘焦点与明确的焦点指示。
- Tooltip 可通过鼠标和键盘 focus 触发。
- 颜色需在当前主题背景上满足对比度要求；与文本/图标组合后仍能在常见色觉差异下判断分组。

## 10. 待实现确认

1. Herdr 当前代码中 Agent panel 的渲染组件和 Grouped 模式排序规则。
2. session/task display name、pane label、agent name 三者的真实来源与含义。
3. workspace/tab/pane identity 在重启、移动和跨 local 场景中的保证。
4. pane 分组色是否作为 UI 偏好持久化，或由当前 pane identity 派生。
5. 重命名是否需复用现有 API，或需增加独立的用户可见 display name 字段。
6. 多 local 的 Agents 面板是否存在；若只展示当前 local，避免重复显示 Local。
