---
description: Explore code with CodeRLM's tree-sitter index
argument-hint: "[query]"
---
Use CodeRLM to explore this codebase and answer the user's request.

User request: $ARGUMENTS

Follow this workflow:

1. Ensure a CodeRLM session exists:
   ```bash
   CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} init
   ```
2. Use targeted CodeRLM queries instead of broad file reads:
   ```bash
   CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} structure --depth 2
   CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} search "symbol_or_pattern" --limit 20
   CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} impl symbol_name --file path
   CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} callers symbol_name --file path
   CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} tests symbol_name --file path
   CODERLM_STATE_DIR={{STATE_DIR}} python3 {{SKILL_CLI_PATH}} grep "pattern" --scope code
   ```
3. Trace from entrypoint to outcome, then synthesize findings with file and line references.

If the server is unavailable, tell the user to start it with `coderlm-server serve`.
