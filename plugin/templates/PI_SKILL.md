---
name: coderlm
description: "Primary tool for code navigation and reading in supported languages (Rust, Python, TypeScript, JavaScript, Go, Java, Scala, SQL). Use instead of native read/grep/glob for finding symbols, reading implementations, tracing callers, discovering tests, and understanding execution paths."
---

# CodeRLM — Structural Codebase Exploration for Pi

You have access to a tree-sitter-backed index server that knows the structure of this codebase: every function, every caller, every symbol, every test reference. Use it instead of guessing with grep.

The server monitors the directory via filesystem watcher and stays up-to-date as you make changes.

## Prerequisites

The `coderlm-server` must be running. Start it separately:

```bash
coderlm-server serve                     # indexes projects on-demand
coderlm-server serve /path/to/project    # pre-index a specific project
```

If the server is not running, all CLI commands will fail with a connection error.

## CLI Reference

Run commands from the project root. Set `CODERLM_STATE_DIR` on every invocation so session state stays in `{{STATE_DIR}}`:

```bash
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} <command> [args]
```

### Setup

```bash
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} init
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} structure --depth 2
```

### Finding Code

```bash
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} search "symbol_name" --limit 20
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} symbols --kind function --file path
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} grep "pattern" --max-matches 20
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} grep "pattern" --scope code
```

### Retrieving Exact Code

```bash
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} impl function_name --file path
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} peek path --start N --end M
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} variables function_name --file path
```

Prefer `impl` and `peek` over reading entire files. They return exactly the code you need — a single function from a 1000-line file, a specific line range — without loading irrelevant code into context.

### Tracing Connections

```bash
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} callers function_name --file path
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} tests function_name --file path
```

These search the entire indexed codebase, not just files you've already seen.

### Annotating

```bash
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} define-file src/server/mod.rs "HTTP routing and handler dispatch"
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} define-symbol handle_request --file src/server/mod.rs "Routes requests by method+path"
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} mark tests/integration.rs test
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} save-annotations
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} load-annotations
```

### Cleanup

```bash
CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} cleanup
```

## Workflow

1. **Init** — `init` to create a session and index the project.
2. **Orient** — `structure` to see the project layout. Identify likely starting points.
3. **Find the entrypoint** — `search` or `grep` to locate the starting symbol or pattern.
4. **Retrieve** — `impl` to read the exact implementation. Not the file. The function.
5. **Trace** — `callers` to see what calls it. `impl` on those callers. Follow the chain.
6. **Widen** — `tests` to find test coverage. `grep` for related patterns discovered during tracing.
7. **Annotate** — `define-symbol` and `define-file` as understanding solidifies.
8. **Synthesize** — Compile findings into a coherent answer with specific file:line references.

Steps 3-7 repeat. A typical exploration is: find a symbol -> read its implementation -> trace its callers -> read those implementations -> discover related symbols -> repeat until the causal chain is clear.

## When to Use the Server vs Native Tools

| Task | Use server | Why |
|------|-----------|-----|
| Find a function by name | `search` | Index lookup, not file globbing |
| Find code when name is unknown | `grep` + `symbols` | Searches all indexed files at once |
| Get a function's source | `impl` | Returns just that function, even from large files |
| Read specific lines | `peek` | Surgical extraction, not the whole file |
| Find what calls a function | `callers` | Cross-project search with exact call sites |
| Find tests for a function | `tests` | By symbol reference, not filename guessing |
| Get project overview | `structure` | Tree with file counts and language breakdown |
| Read an entire small file | Native read | When you genuinely need the whole file |

Default to the server. Use native file reading only when you need an entire file or the server is unavailable.

## Troubleshooting

- **"Cannot connect to coderlm-server"** — Server not running. Start with `coderlm-server serve`.
- **"No active session"** — Run `init` first.
- **"Project was evicted"** — Server hit capacity (default 5 projects). Re-run `init`.
- **Search returns nothing relevant** — Try broader grep patterns or list all symbols: `symbols --limit 200`.
