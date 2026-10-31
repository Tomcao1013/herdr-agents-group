# herdr-agents-group

<p align="center">
  <a href="https://herdr.dev">herdr.dev</a> · <a href="#install">install</a> · <a href="docs/README.md">docs</a> · <a href="docs/design.md">design</a>
</p>

<p align="center">
  English · <a href="README.zh-CN.md">简体中文</a>
</p>

---

**see which workspace every agent belongs to.**

A sidebar plugin for [Herdr](https://github.com/herdrdev/herdr). It colors workspace labels and their agents with the same palette, and adds named dividers between workspace groups. It changes presentation—not agent execution, focus, or workspace membership.

- **one workspace, one color** — six remembered color slots, shared by workspace labels and agent names. Closed workspaces release their slots; when all six are in use, new workspaces reuse the least-used color.
- **named group boundaries** — a dim divider names the next workspace below the previous group's last agent. Empty groups are skipped.
- **task names first** — uses the `topic` token, then a cleaned terminal title, then the agent type. Redundant directory suffixes are removed; a differing agent type is shown dimmed.
- **follows workspace changes** — startup and workspace, tab, pane, agent-status, and worktree events reconcile the sidebar. Only changed `ag_` tokens are written.
- **your layout, your choice** — installing the plugin does not install the sidebar layout. A separate action writes a marked configuration block with backup and conflict protection.
- **standard library only** — no third-party Python runtime dependencies, no Herdr source patch, no agent wrapper.

---

## install

Requirements:

- **Herdr 0.9.5 or newer**; this is the manifest's minimum, not a promise of testing every newer release.
- **Python 3.9+ at `/usr/bin/python3`**. Every event and action uses that absolute path; a `python3` elsewhere on `PATH` is not enough. Check before installing:

  ```bash
  /usr/bin/python3 --version
  herdr --version
  ```

- The manifest declares **macOS and Linux**. Local unit tests have been run on macOS; Linux runtime integration is not yet verified. Windows is not supported by this manifest.
- Herdr must be reachable through its injected `HERDR_BIN_PATH` or on `PATH`.

Install from GitHub:

```bash
herdr plugin install Tomcao1013/herdr-agents-group
```

Or link a local checkout, from its repository root:

```bash
herdr plugin link "$PWD" --enabled
```

Then explicitly install the sidebar layout in the target Herdr session:

```bash
herdr plugin action invoke install-layout --plugin herdr-agents-group
```

This action changes `config.toml`, reloads Herdr's configuration, and reconciles the sidebar; when the marked block is already up to date, it reports that and does neither. Plugin installation alone only registers the plugin and its token updates; the custom sidebar rows need this extra action. Check the action's completion in Herdr's plugin logs before assuming the layout was installed.

### configuration safety

The layout action uses `HERDR_CONFIG_PATH` when set, otherwise `~/.config/herdr/config.toml`. Its parent directory must already exist and be writable.

- Before changing an existing file, it makes a sibling backup named `config.toml.bak-agents-group-YYYYMMDD-HHMMSS` and replaces the config atomically.
- It owns only the block between `# >>> herdr-agents-group >>>` and `# <<< herdr-agents-group <<<`. Reinstalling replaces that block; edits inside it are not preserved.
- If `[ui.sidebar.agents]` or `[ui.sidebar.spaces]` already exists outside the block, installation stops rather than overwriting it. Back up and manually merge or remove the conflicting tables before retrying. A missing end marker also requires manual repair.
- Removing the layout deletes the marked block, not the rest of the config. Backups remain available for manual recovery; they are not automatically restored.

Color assignments are stored per session socket in `slots-<hash>.json` under `HERDR_PLUGIN_STATE_DIR`, falling back to the system temporary directory's `herdr-agents-group` folder. Losing that state can reassign colors. Tokens use the `ag_` prefix; reserve it for this plugin because Herdr token names are shared across metadata sources.

Multiple sessions should use separate writable `HERDR_PLUGIN_STATE_DIR` directories. Color files are socket-specific, but the lock and pending flag are shared within a directory; sharing a directory can coalesce events from different sessions.

## actions

While the plugin is enabled:

```bash
herdr plugin action invoke install-layout --plugin herdr-agents-group
herdr plugin action invoke uninstall-layout --plugin herdr-agents-group
herdr plugin action invoke clear --plugin herdr-agents-group
```

- `install-layout` — installs or replaces the marked layout, reloads config, and refreshes tokens; when the marked block is already up to date, it neither reloads nor refreshes.
- `uninstall-layout` — removes the marked layout and reloads config; when a block was removed, it also clears the plugin's tokens.
- `clear` — removes `ag_` tokens from panes and workspaces in the current snapshot, leaving other token names alone. **It does not disable the plugin.** Subsequent events can recreate those tokens, even after layout removal.

### remove cleanly

Keep an intact source copy until cleanup finishes. Run the following **from that plugin source directory**, in a terminal attached to the Herdr session you intend to clean:

```bash
herdr plugin disable herdr-agents-group
# Wait for any already-running plugin commands to finish before continuing.
/usr/bin/python3 main.py uninstall-layout
/usr/bin/python3 main.py clear
herdr plugin uninstall herdr-agents-group
```

The order matters: disable event handling first, then remove the layout and clear tokens, then remove the installation. Herdr rejects actions for disabled plugins, so these cleanup commands deliberately run the retained Python entry point directly. The explicit `clear` also handles the case where the marked layout was already absent. Do not proceed past a failed cleanup command.

For a local link, use `herdr plugin unlink herdr-agents-group` instead of the final uninstall command. If you used a custom config path, keep `HERDR_CONFIG_PATH` set for cleanup too. When targeting another session, set the appropriate `HERDR_SOCKET_PATH`; repeat token cleanup for other sessions where the plugin ran. Do not remove the source directory before these steps finish.

## limits

- **workspace groups, not pane groups** — this plugin styles Herdr's existing workspace-based agent list; it does not create groups or change sort order.
- **priority sorting has no dividers** — with `agent_panel_sort = "priority"`, workspace colors remain but group dividers are omitted.
- **local snapshot only** — remote-machine agents in a combined sidebar are not handled.
- **dark themes first** — the fixed palette targets dark themes. Light-theme contrast, including rose-pine-dawn, is not validated and may be insufficient.
- **snapshot order is assumed** — agents within each workspace keep snapshot order. Matching that order to the rendered sidebar is not an API guarantee.
- **names are event-driven** — another plugin writing `topic` does not itself trigger a plugin event. Names refresh on the next subscribed event, including agent-status changes.
- **dividers are a second row** — the first group has no leading divider. Dividers target 20 terminal columns; narrow sidebars can truncate them. Selection/hover rendering and narrow-width behavior still need visual verification.

## docs

[Documentation index →](docs/README.md) · [Current design and implementation notes →](docs/design.md) · [Herdr plugins →](https://herdr.dev/docs/plugins/)

The documentation index separates current behavior from archived proposals. The implementation is a Python plugin using Herdr metadata tokens, not a modification of Herdr's pane model.

## development

From the repository root, using Python 3.9+:

```bash
python3 -m unittest discover -s tests -v
```

The tests use only the standard library and do not need a running Herdr server. They cover color allocation and state files, naming and divider formatting, token planning and diffs, marked config-block handling, and event coalescing. They do not replace live sidebar, remote-machine, or cross-platform integration checks.

## license

Licensed under the [MIT License](LICENSE). Copyright © 2026 Tomcao1013.
