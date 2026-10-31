# herdr-agents-group 设计与实现边界

- 状态：已有插件实现及单元测试；不代表全部场景已验收
- 设计起点：2026-10-30；本文已按当前仓库实现核对
- 目标：Herdr 0.9.5 起（清单的 `min_herdr_version`）；原设计调查环境为 protocol 22，不据此承诺其它协议兼容性
- 实现依据：[插件清单](../herdr-plugin.toml)、[`agents_group/`](../agents_group/)

## 1. 目标与范围

侧栏上方是 workspace 列表，下方是 agents 列表。本插件以 **workspace** 为颜色归属，在本地 workspace 组之间添加带组名的分割线，优先显示任务名。

插件通过 Herdr CLI 读 snapshot、写展示 token，并通过 action 安装侧栏配置；不修改 Herdr 核心、agent 运行、状态判定、焦点或控制语义。不提供 pane 分组、独立分组折叠、session 重命名编辑器或远程 machine 的专门适配。

## 2. 显示效果

```text
 ▾ Local
   ◐ [1] wardrobe            ← workspace 名用其颜色（rose）
   × [2] marking             ← foam
   ○ [3] trade-review        ← iris

 agents             grouped
 ○ task1 impl · pi           ← 任务名用 workspace 颜色，agent 类型变暗
 ○ L0 orchestrator · claude
 ◐ orch编排 · claude
   ── marking ──────────     ← 上一组末行的第二行，使用下一组颜色并变暗
 ○ pi                        ← 没有任务名时显示类型，仍用 workspace 颜色
 × pi
   ── trade-review ─────
 ○ pi
```

- 颜色加在名字上，而非另加色块；Herdr 会在相邻非空 token 间插入 ` · `。
- workspace 名和其 agent 名共用颜色，形成上下两个列表的对应关系。
- 分割线显示下一组的 workspace 名；第一组上方没有分割线。
- 归属色不替代状态图标；色板避开状态常用的 love、gold、pine。

## 3. 颜色与 token

实现见 [`colors.py`](../agents_group/colors.py)、[`plan.py`](../agents_group/plan.py)、[`config_block.py`](../agents_group/config_block.py)。

| 槽 | 名称 | 色值 |
| --- | --- | --- |
| 1 | rose | `#ebbcba` |
| 2 | foam | `#9ccfd8` |
| 3 | iris | `#c4a7e7` |
| 4 | green | `#a6da95` |
| 5 | blue | `#8aadf4` |
| 6 | sand | `#e2c08d` |

颜色按 workspace ID 分配并保存：仍存在的 workspace 保留有效槽位，新 workspace 取使用次数最少的槽（并列取最小槽号），关闭的 workspace 从映射中移除。从空映射开始，前 6 个 workspace 可用不同色；超过 6 个会复用。保留的重复槽不会主动重新均衡，因此数量回落到 6 个以内也不保证立即恢复无重复。映射丢失、损坏、workspace ID 或 socket 路径变化均可能导致重新分配。

配置预设三组各 6 个 token：`$ag_n1`–`$ag_n6` 为 agent 名、`$ag_d1`–`$ag_d6` 为分割线、`$ag_w1`–`$ag_w6` 为 workspace 名，另有变暗的 `$ag_kind`。只填当前使用的槽，空 token 不显示；第二行为空时折叠。

原隔离 session 调查记录：每个 pane 最多 16 个 token；不同 `--source` 共用 pane token 命名空间，不是按 source 隔离。插件仅设置/清理 `ag_` 前缀 token，保留其它名称；若其它插件也使用 `ag_`，仍可能互相覆盖，前缀不是权限隔离。安装生成的 agents 布局保留 `state_icon`，spaces 布局保留 `state_icon`、`branch`、`git_status`。

## 4. 一次 reconcile

实现见 [`reconcile.py`](../agents_group/reconcile.py) 和 [`plan.py`](../agents_group/plan.py)。

1. 读取 `herdr api snapshot`，使用 `workspaces`、`agents` 和 `panes`。
2. 加载颜色映射，按当前 workspace ID 分配槽位并保存。
3. workspace 的对应 `ag_w<槽>` 写入 label（缺失时回退到 `workspace <number>`）。
4. agent pane 的 `ag_n<槽>` 写入显示名；显示名与 agent 类型不同时额外写 `ag_kind`。
5. grouped 模式下，按 snapshot 的 workspace 顺序分组，**保留 snapshot agents 在每个 workspace 内的相对顺序**。在每个非末组的最后一个 pane 上写下一组的分割线；跳过没有 agent 的 workspace。
6. 对比 snapshot 当前 token，只写变化，清除不再需要的 `ag_` token；snapshot 中不再有 agent 的现存 pane 也参与清理。

**插件没有读取 layout 的 y 坐标自行排序。** 原调查观察到 snapshot 组内顺序与侧栏的 tab 顺序 / pane 位置一致，但这不是本文能保证的 API 契约；Herdr 改变顺序时，分割线可能落到错误位置。原调查还发现 agent 第 2 行起缩进 2 列，因此分割线放在上一组最后一项的第二行，而非下一组第一项上方。

单个目标 token 写入失败会记录 `tokens.write_failed`，继续处理其它目标；失败不构成事务回滚，也没有专门的定时重试。后续事件触发的 reconcile 可再次尝试。`reconcile.done` 提供 `written`、`failed`、`ms` 等日志，但日志本身不表示视觉验收通过。

### 4.1 显示名

实现见 [`naming.py`](../agents_group/naming.py)。

1. 优先非空 `tokens.topic`，清除末尾的 ` - <目录名>`；若整个值只是目录名，则继续回退。
2. 否则使用 `terminal_title_stripped`，清除开头的 `π - `（仅 `π` 视为空），再清除目录后缀或纯目录名。
3. 目录名来自 `cwd` 和 `foreground_cwd` 的末级名称。
4. 都不可用时回退到 agent 类型；类型也为空时使用小写 `agent`。
5. 不读 `task` 这类整段 prompt token。名字写入前截取前 80 个字符，不等于 80 个终端显示列。

分割线去掉 workspace label 的 `[n]` 前缀，按当前实现的宽度算法截断/补线至目标 20 列；不随侧栏宽度自适应，也不是完整的 Unicode 字形簇宽度处理。

## 5. 事件、并发与运行时

### 5.1 清单中的实际触发项

所有触发均执行 `/usr/bin/python3 main.py reconcile`：

- `startup`
- `workspace.created`、`workspace.closed`、`workspace.renamed`、`workspace.moved`、`workspace.reordered`
- `tab.created`、`tab.closed`、`tab.moved`、`tab.renamed`
- `pane.created`、`pane.closed`、`pane.exited`、`pane.moved`、`pane.agent_detected`、`pane.agent_status_changed`
- `worktree.created`、`worktree.removed`

不是 `worktree.*` 通配订阅。`pane.updated` 是 socket subscription 事件，不是此处注册的插件事件；其它插件写 `topic` 不会直接触发本插件。`pane.agent_status_changed` 是捕捉 automatic-rename 的 `topic` 和新终端标题的刷新机会，其它后续触发也会重新读取。因此 **topic/title 更新不保证立即可见**，尤其是状态事件早于名称写入且之后没有新事件时。

### 5.2 锁与 pending 的边界

`run_coalesced` 使用 `fcntl.flock` 非阻塞文件锁和 `pending` 标记合并突发事件。持锁者在有 pending 时补跑；每次调用总共 **最多 5 pass**。达到上限仍有 pending 会记录 `reconcile.pass_limit`，没有后台 worker 保证继续排空。末次检查与新事件之间也存在并发边界，所以不能声称“事件绝不丢”或必定即时收敛；异常、持续突发或停机可能需要后续事件/手动 reconcile。

这是幂等、只写差异的全量刷新，不是有持久队列与确认机制的事件处理器。原设计中的本机毫秒数仅是局部调查，不作为启动、突发吞吐或端到端延迟承诺；当前文档不设未经基准验证的性能保证。

### 5.3 解释器与状态目录

清单固定 `/usr/bin/python3`，避免依赖 PATH 中的 Python shim；代码只使用标准库，兼容 Python 3.9。清单声明 macOS / Linux，但仍须确认目标机器存在这个路径且版本至少为 3.9；不能假定所有系统自带相同 Python。Herdr CLI 从 `HERDR_BIN_PATH` 或 PATH 查找，每次 CLI 调用的超时为 5 秒，不等于整个 reconcile 的总超时。

运行时状态目录由 [`main.py`](../agents_group/main.py) 决定：

- 有 `HERDR_PLUGIN_STATE_DIR` 时使用该目录。
- 否则使用 `tempfile.gettempdir()/herdr-agents-group`，**不是**仓库目录或固定的用户持久化目录。临时目录清理后颜色映射可能丢失。
- 槽位文件为 `slots-<socket路径SHA-256前12位>.json`，socket 字符串来自 `HERDR_SOCKET_PATH`，未设置时用 `default`。这是路径散列，不是 session 身份或跨重启稳定性保证。
- `pending` 和 `reconcile.lock` 位于同一状态目录，**不按 socket 分开**。多个 session 共用目录（尤其临时 fallback）时可能互相合并事件，不能保证各自及时刷新；不同 session 应使用彼此隔离且可写的状态目录。

## 6. Actions、配置与生命周期

三个 action 的 ID 与命令参数一致，均为 global context：

| ID | 行为 |
| --- | --- |
| `install-layout` | 备份配置，安装/替换托管块，reload-config，再 reconcile |
| `uninstall-layout` | 有托管块时备份配置、删除块、reload-config，并清除当前 snapshot 的插件 token；无托管块时直接返回 |
| `clear` | 只清除当前 snapshot 的 `ag_` token，不删除布局或颜色映射 |

配置文件使用 `HERDR_CONFIG_PATH`，未设置时为 `~/.config/herdr/config.toml`。备份在原文件旁，名为 `config.toml.bak-agents-group-<时间戳>`（实际前缀随配置文件名），以同目录临时文件替换配置；父目录需要已存在且可写。

托管块标记为 `# >>> herdr-agents-group >>>` 和 `# <<< herdr-agents-group <<<`。检测到块外已有 `[ui.sidebar.agents]` 或 `[ui.sidebar.spaces]` 时安装会拒绝，不自动合并；缺少结束标记也会报冲突。检测使用文本/正则而非完整 TOML 语义解析，不应据此认为所有等价 TOML 写法均能安全识别。用户应先备份、处理冲突再安装。

配置写入、reload 与 token 写入不是一个事务：reload 或后续刷新失败不会自动恢复旧配置。若布局已完全相同，安装直接返回，不额外 reconcile；若没有托管块，卸载直接返回，不清 token。

没有 shutdown/禁用插件的自动清理钩子。`clear` 后只要插件仍启用，后续事件即可重新写入 token；`uninstall-layout` 也不禁用插件或删除状态文件。完全移除应先停止/禁用事件触发，再移除布局并清理 token，避免运行中的 reconcile 重新写回；需要恢复旧布局时参考备份手工处理。

## 7. 已知限制与待验证项

- **排序**：`agent_panel_sort = "priority"` 被当前文本检测识别时不画分割线，仍保留颜色；该检测不是完整 TOML 解析。默认 grouped 的顺序依赖 snapshot，见第 4 节。
- **远程**：不主动枚举或适配远程 machine，仅处理当前 CLI snapshot，不能宣称远程归属展示已支持。
- **主题**：固定色板面向深色主题；rose-pine-dawn 等浅色主题的对比度未充分验证，不自动换色。
- **可识别性**：颜色可能复用；第一组没有标题分割线，且滚动后可能看不到上方 workspace 图例。不宣称仅靠当前结构即可无障碍识别所有归属。
- **视觉验收**：组末 agent 的 hover/选中高亮是否包住分割线、窄侧栏截断、长中文/复杂 Unicode 宽度、不同主题均需真实 UI 验证。
- **生命周期与可靠性**：workspace 移动、关闭、server 重启/恢复、跨 session 隔离、突发达到 5 pass、token/配置写入失败后的恢复仍需运行时验证。已有单元测试不等于这些集成场景均通过。
- **兼容与性能**：目标 Herdr 版本的事件行为、snapshot 顺序、token 限额以及多 agent 规模下的延迟需要在实际环境复核；原隔离 session 观察不是所有版本的契约。

## 8. 历史文档

以下文件误将本需求的分组单位定为 pane，并以改动 Herdr 核心为前提，已归档且不作为当前验收标准：

- [旧 PRD](archive/agents-sidebar-prd.md)
- [旧产品设计](archive/product-design/agents-sidebar.md)
- [旧实施规划](archive/implementation-plan.md)

返回[文档索引](README.md)或[项目 README](../README.md)。
