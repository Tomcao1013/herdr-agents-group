# Agents 侧栏实施规划（已归档）

> **已归档：本 pane 分组 / 修改 Herdr 核心的历史规划已被 [workspace 插件设计](../design.md)取代。**
> 下文保留当时的前提、阶段计划与阻塞项，不是当前插件的实施清单或验收结果。当前文档入口见 [文档索引](../README.md)。

- 历史状态：提案，依赖 Herdr 源码定位
- 关联文档：[Agents 侧栏 PRD](agents-sidebar-prd.md)、[产品设计](product-design/agents-sidebar.md)

## 1. 当前前提

编写本历史规划时，项目工作目录只有本地任务元数据，没有 Herdr 源码、测试或 Git 历史。因此本规划先定义实施顺序和验证边界，不虚构具体组件名、模块名或提交位置。此处描述仅反映当时情况，不代表当前仓库状态。

本机运行时快照已确认 Herdr 实例中存在以下信息形态：

- `workspace.custom_name`
- `workspace.identity_cwd`
- `tab.custom_name`
- pane `cwd`
- pane `label`
- pane `agent_name`
- pane `managed_agent_kind`
- pane `agent_session`

这些只能作为运行时证据，不能替代源码/API 契约。正式实现前要从目标版本源码确认字段来源、稳定性和写入权限。

## 2. 核心决策

1. Agents 的 Grouped 视图以 `pane` 为视觉分组单位。
2. pane 分组标题显示 `pane label`；没有 label 时显示 `workspace / tab / Pane <number>`。
3. agent session 主标题优先显示用户设置的 session/task display name。
4. session 没有用户设置名称时，主标题回退到 agent kind，例如 `Pi` 或 `Claude`。
5. 颜色绑定当前 local 下的稳定 pane identity，不绑定显示名称、排序位置或 agent kind。
6. workspace/tab 是 pane 的项目上下文，不再作为 agent session 名称的替代品。
7. 颜色只是归属提示，状态必须由独立的图标/文案表达。
8. display-only 名称和颜色不得改变 agent 生命周期、控制权限、消息投递或焦点策略。

## 3. 实施阶段

### Phase 0：源码与字段对齐

**目标：** 找到真实 Agent panel、Grouped 视图、列表数据源、名称来源和持久化边界。

**工作项：**

- 定位 Agents sidebar/panel 渲染入口与 Grouped 排序逻辑。
- 找到 agent list item 的现有数据模型和刷新订阅。
- 确认现有 `local`、`workspace`、`tab`、`pane`、`agent session` 的内部类型。
- 确认用户设置的 session/task 名称是否已经存在；区分它与 pane label、agent_name、agent_session ID/path。
- 确认 pane identity 在刷新、移动、server 重启和恢复后的稳定性。
- 确认现有 UI 状态存储能否保存颜色 token 或 pane 颜色映射。
- 记录目标仓库、分支、构建命令、测试命令和视觉回归入口。

**退出条件：**

- 有一份字段映射表，明确每个 PRD 字段对应源码符号/API。
- 已确认颜色键能否使用稳定 pane identity；不能时给出持久化替代方案。
- 已确认用户命名入口是否已存在。
- 现有行为有至少一个 fixture 或可重复的本地运行样本。

### Phase 1：只读展示改造

**目标：** 在不增加新的编辑能力的情况下，改善列表识别。

**工作项：**

- 将 list item 归一化为 `pane group + agent session item` 的展示模型。
- 增加 pane 分组标题和 workspace/tab 上下文。
- 实现 session display name → agent kind → `Agent` 的主标题回退。
- 将 agent kind、status、pane path 分配到独立的视觉层级。
- 加入稳定 pane 颜色 token；先使用内存派生或已有 UI 偏好存储，避免在不清楚数据契约时改变核心 session 数据。
- 处理缺少名称、缺少 label、未知 agent、断连、stale 和 unknown 状态。
- 保持既有行选择、聚焦 pane、键盘导航和控制操作不变。

**测试：**

- 单 local、多 workspace、多 pane、多 agent fixture。
- 有名/无名/空白名称回退。
- 同名 pane label 与同名 session。
- agent 增删、状态刷新、列表排序后的颜色稳定性。
- pane 移动后的分组更新和旧行清理。
- 窄侧栏长名称截断和状态不重叠。
- 浅色/深色主题视觉回归。

**退出条件：**

- PRD A1-A4、A6、A8-A10、A12 通过。
- 现有 agent 控制回归测试全部通过。
- 颜色移除后，用户仍可仅凭文字和分组结构识别 pane。

### Phase 2：名称编辑与持久化

**目标：** 在确认底层字段和 API 后提供用户可控的 session/task 命名。

**工作项：**

- 复用现有重命名 API；若不存在，增加独立的 display-only name 字段和最小写入接口。
- 提供行级重命名入口：进入、保存、取消、清空恢复回退名称。
- 处理保存失败、连接断开、并发刷新和实体已关闭。
- 名称只保存到 UI/运行时展示数据，不写入用户项目工作树。
- 兼容旧记录，缺少名称时继续走回退规则。

**测试：**

- 保存成功后刷新/重启仍显示名称。
- 空名称、空白名称、重复名称和超长名称。
- 保存失败时保留旧值并允许重试。
- session 关闭、pane 移动、server 重启期间的竞态。
- 旧客户端/旧记录读取新数据时不阻断主界面。

**退出条件：**

- PRD FR-5 和 A2、A3、A5、A7、A11 通过。
- 新写入字段不会被控制面误认成 session identity 或 agent authority。

### Phase 3：发布与观察

**目标：** 低风险发布视觉改造并验证真实使用效果。

**工作项：**

- 若架构允许，提供展示层 feature flag 或配置开关。
- 默认开启 pane 分组、命名优先级和颜色标识；保留文字-only 降级路径。
- 记录错误而不记录 session 内容、路径或敏感提示词。
- 用固定 fixture 做截图回归，再用真实多项目 local 做人工验收。
- 收集归属识别成功率、重命名成功率、错误分组数和颜色漂移问题。

**回滚策略：**

- 关闭颜色装饰时保留 pane 分组和文字上下文。
- 名称读取异常时回退到 agent kind。
- display-only 写入异常时禁用编辑入口，不影响 agent 操作。
- 回滚不删除已保存的名称或颜色偏好。

## 4. 实现边界

### 必须保持不变

- agent lifecycle/status authority。
- prompt/send/control 操作的目标解析。
- pane focus、tab focus 和用户当前焦点行为。
- workspace/tab/pane 的创建、移动、关闭和恢复语义。
- session ID/path 等内部身份的控制用途。

### 可以改变

- Agents 侧栏的分组键和显示顺序，但必须由稳定 pane 关系决定。
- agent session 主显示名称及其回退。
- pane 分组标题、项目上下文和颜色装饰。
- display-only tooltip、无障碍标签和重命名交互。

## 5. 交付物

实施完成后应包含：

- 产品设计文档和 PRD 的字段映射更新。
- 归一化展示模型及名称/颜色纯函数测试。
- Agents panel 的渲染与交互改动。
- 旧数据/未知状态兼容测试。
- 浅色、深色、窄侧栏和多 workspace 的视觉回归证据。
- 变更说明：新增字段、持久化位置、迁移策略、回滚方式。

## 6. 当前阻塞项

需要目标 Herdr 源码仓库路径或把源码放入当前工作目录。没有源码时可以继续评审产品决策，但不能可靠完成组件级实现、API 设计、单元测试或视觉截图验证。
