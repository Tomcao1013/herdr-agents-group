# 文档索引

herdr-agents-group 是按 **workspace** 为本地 Agents 侧栏着色、添加组间分割线的 Herdr 插件；不是按 pane 分组的 Herdr 核心改造。

## 当前文档

- 项目 README（[English](../README.md) / [简体中文](../README.zh-CN.md)）：功能、安装、操作与运行要求。
- [插件设计与实现边界](design.md)：当前实现、事件、颜色与命名规则、状态文件、已知限制和待验证项。已有实现不等于全面验收。
- 实现依据：[插件清单](../herdr-plugin.toml)、[`agents_group/`](../agents_group/)。

## 历史提案（已归档，不作为当前需求或验收标准）

以下文档曾提出按 pane 分组、修改 Herdr 核心及增加命名交互，已被当前 workspace 插件方案取代。保留原文用于追溯，不表示这些能力已实现。

| 历史文档 | 归档位置 |
| --- | --- |
| Agents 侧栏可识别性与归属视觉 PRD | [archive/agents-sidebar-prd.md](archive/agents-sidebar-prd.md) |
| Agents 侧栏产品设计 | [archive/product-design/agents-sidebar.md](archive/product-design/agents-sidebar.md) |
| Agents 侧栏实施规划 | [archive/implementation-plan.md](archive/implementation-plan.md) |

术语：`local`、`workspace`、`tab`、`pane`、`agent session`、`agent kind`、`display name`。当前颜色绑定 workspace；pane 是 token 的写入目标，不是分组或颜色分配单位。
