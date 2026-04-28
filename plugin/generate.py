#!/usr/bin/env python3
"""Generate CodeRLM instruction files for AI coding platforms.

Renders a universal instruction template with platform-specific paths and copies
the CLI script to the expected location. No external dependencies required.

Usage:
    python3 plugin/generate.py --platform cursor       # Single platform
    python3 plugin/generate.py --platform all           # All platforms
    python3 plugin/generate.py --list                   # List platforms
    python3 plugin/generate.py --platform cursor --dry-run
    python3 plugin/generate.py --platform cursor --clean
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR / "templates" / "INSTRUCTIONS.md"
PI_SKILL_TEMPLATE_PATH = SCRIPT_DIR / "templates" / "PI_SKILL.md"
PI_PROMPT_TEMPLATE_PATH = SCRIPT_DIR / "templates" / "PI_PROMPT.md"
CLI_SOURCE = SCRIPT_DIR / "skills" / "coderlm" / "scripts" / "coderlm_cli.py"


@dataclass
class Platform:
    name: str
    instruction_path: str  # relative to project root
    cli_path: str  # relative to project root (where CLI gets copied)
    state_dir: str  # state directory for this platform
    format: str  # "markdown", "mdc", "append"
    mdc_frontmatter: Optional[str] = None  # for Cursor's .mdc format
    skill_path: Optional[str] = None  # optional Pi/Agent Skills SKILL.md path
    skill_cli_path: Optional[str] = None  # optional skill-local CLI copy path
    prompt_path: Optional[str] = None  # optional prompt template path
    append_marker: str = "coderlm"  # marker basename for append format


PLATFORMS: dict[str, Platform] = {
    "cursor": Platform(
        name="Cursor",
        instruction_path=".cursor/rules/coderlm.mdc",
        cli_path=".cursor/coderlm/coderlm_cli.py",
        state_dir=".cursor/coderlm/state",
        format="mdc",
        mdc_frontmatter=(
            "---\n"
            "description: CodeRLM - tree-sitter-backed codebase exploration via index server\n"
            "globs:\n"
            "alwaysApply: true\n"
            "---\n"
        ),
    ),
    "windsurf": Platform(
        name="Windsurf",
        instruction_path=".windsurf/rules/coderlm.md",
        cli_path=".windsurf/coderlm/coderlm_cli.py",
        state_dir=".windsurf/coderlm/state",
        format="markdown",
    ),
    "copilot": Platform(
        name="GitHub Copilot",
        instruction_path=".github/instructions/coderlm.instructions.md",
        cli_path=".github/coderlm/coderlm_cli.py",
        state_dir=".github/coderlm/state",
        format="markdown",
    ),
    "roo": Platform(
        name="Roo Code",
        instruction_path=".roo/rules/coderlm.md",
        cli_path=".roo/coderlm/coderlm_cli.py",
        state_dir=".roo/coderlm/state",
        format="markdown",
    ),
    "kilo": Platform(
        name="Kilo Code",
        instruction_path=".kilo/rules/coderlm.md",
        cli_path=".kilo/coderlm/coderlm_cli.py",
        state_dir=".kilo/coderlm/state",
        format="markdown",
    ),
    "gemini": Platform(
        name="Gemini CLI",
        instruction_path=".gemini/instructions/coderlm.md",
        cli_path=".gemini/coderlm/coderlm_cli.py",
        state_dir=".gemini/coderlm/state",
        format="markdown",
    ),
    "codex": Platform(
        name="Codex CLI",
        instruction_path="AGENTS.md",
        cli_path=".codex/coderlm/coderlm_cli.py",
        state_dir=".codex/coderlm/state",
        format="append",
    ),
    "pi": Platform(
        name="Pi",
        instruction_path="AGENTS.md",
        cli_path=".pi/coderlm/coderlm_cli.py",
        state_dir=".pi/coderlm/state",
        format="append",
        skill_path=".pi/skills/coderlm/SKILL.md",
        skill_cli_path=".pi/skills/coderlm/scripts/coderlm_cli.py",
        prompt_path=".pi/prompts/coderlm.md",
        append_marker="coderlm-pi",
    ),
    "opencode": Platform(
        name="OpenCode",
        instruction_path=".opencode/instructions/coderlm.md",
        cli_path=".opencode/coderlm/coderlm_cli.py",
        state_dir=".opencode/coderlm/state",
        format="markdown",
    ),
    "augment": Platform(
        name="Augment Code",
        instruction_path=".augment/instructions/coderlm.md",
        cli_path=".augment/coderlm/coderlm_cli.py",
        state_dir=".augment/coderlm/state",
        format="markdown",
    ),
    "amazonq": Platform(
        name="Amazon Q",
        instruction_path=".amazonq/rules/coderlm.md",
        cli_path=".amazonq/coderlm/coderlm_cli.py",
        state_dir=".amazonq/coderlm/state",
        format="markdown",
    ),
    "amp": Platform(
        name="Amp",
        instruction_path=".amp/rules/coderlm.md",
        cli_path=".amp/coderlm/coderlm_cli.py",
        state_dir=".amp/coderlm/state",
        format="markdown",
    ),
    "qwen": Platform(
        name="Qwen Code",
        instruction_path=".qwen/rules/coderlm.md",
        cli_path=".qwen/coderlm/coderlm_cli.py",
        state_dir=".qwen/coderlm/state",
        format="markdown",
    ),
}


def load_template(template_path: Path = TEMPLATE_PATH) -> str:
    if not template_path.exists():
        print(f"ERROR: Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)
    return template_path.read_text()


def render_template(template: str, platform: Platform) -> str:
    skill_cli_path = platform.skill_cli_path or platform.cli_path
    content = template.replace("{{CLI_PATH}}", platform.cli_path)
    content = content.replace("{{SKILL_CLI_PATH}}", skill_cli_path)
    content = content.replace("{{STATE_DIR}}", platform.state_dir)
    content = content.replace("{{PLATFORM_NAME}}", platform.name)
    return content


def generate_platform(platform: Platform, project_root: Path, dry_run: bool) -> None:
    template = load_template()
    rendered = render_template(template, platform)

    instruction_file = project_root / platform.instruction_path
    cli_dest = project_root / platform.cli_path

    # Instruction file
    if platform.format == "mdc":
        content = (platform.mdc_frontmatter or "") + "\n" + rendered
        _write_file(instruction_file, content, dry_run)

    elif platform.format == "append":
        _append_with_markers(instruction_file, rendered, dry_run, platform.append_marker)

    else:  # markdown
        _write_file(instruction_file, rendered, dry_run)

    # Copy CLI script
    _copy_file(CLI_SOURCE, cli_dest, dry_run)
    _generate_optional_resources(platform, project_root, dry_run)

    # Write env hint
    env_hint = (
        f"  Set CODERLM_STATE_DIR={platform.state_dir} when running the CLI\n"
        f"  (or the CLI defaults to .claude/coderlm_state)"
    )
    print(f"  Note: {env_hint}")


def _generate_optional_resources(
    platform: Platform,
    project_root: Path,
    dry_run: bool,
) -> None:
    if platform.skill_path:
        skill_template = load_template(PI_SKILL_TEMPLATE_PATH)
        skill_content = render_template(skill_template, platform)
        _write_file(project_root / platform.skill_path, skill_content, dry_run)

    if platform.skill_cli_path:
        _copy_file(CLI_SOURCE, project_root / platform.skill_cli_path, dry_run)

    if platform.prompt_path:
        prompt_template = load_template(PI_PROMPT_TEMPLATE_PATH)
        prompt_content = render_template(prompt_template, platform)
        _write_file(project_root / platform.prompt_path, prompt_content, dry_run)


def clean_platform(platform: Platform, project_root: Path, dry_run: bool) -> None:
    instruction_file = project_root / platform.instruction_path
    cli_dest = project_root / platform.cli_path
    cli_dir = cli_dest.parent
    state_dir = project_root / platform.state_dir

    if platform.format == "append":
        _remove_markers(instruction_file, dry_run, platform.append_marker)
    else:
        _remove_file(instruction_file, dry_run)

    _remove_file(cli_dest, dry_run)
    _clean_optional_resources(platform, project_root, dry_run)

    # Remove state dir if empty
    _remove_dir_if_empty(state_dir, dry_run)
    # Remove CLI parent dir if empty
    _remove_dir_if_empty(cli_dir, dry_run)


def _clean_optional_resources(
    platform: Platform,
    project_root: Path,
    dry_run: bool,
) -> None:
    extra_paths = [
        platform.skill_cli_path,
        platform.skill_path,
        platform.prompt_path,
    ]
    for path_str in extra_paths:
        if path_str:
            _remove_file(project_root / path_str, dry_run)

    for path_str in extra_paths:
        if path_str:
            _remove_empty_parents((project_root / path_str).parent, project_root, dry_run)


# -- File operations --


def _write_file(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"  Created {path}")


def _copy_file(src: Path, dest: Path, dry_run: bool) -> None:
    if not src.exists():
        print(f"  WARNING: source not found: {src}", file=sys.stderr)
        return
    if dry_run:
        print(f"  [dry-run] copy {src} -> {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"  Copied {dest}")


def _append_marker_start(marker: str) -> str:
    return f"<!-- {marker}-start -->"


def _append_marker_end(marker: str) -> str:
    return f"<!-- {marker}-end -->"


def _append_with_markers(
    path: Path,
    content: str,
    dry_run: bool,
    marker: str,
) -> None:
    marker_start = _append_marker_start(marker)
    marker_end = _append_marker_end(marker)
    block = f"\n{marker_start}\n{content}\n{marker_end}\n"

    if path.exists():
        existing = path.read_text()
        if marker_start in existing:
            if dry_run:
                print(f"  [dry-run] replace marked section in {path}")
                return
            start = existing.index(marker_start)
            end = existing.index(marker_end) + len(marker_end)
            before = existing[:start].rstrip("\n")
            after = existing[end:].lstrip("\n")
            parts = [before, block.strip(), after]
            updated = "\n\n".join(p for p in parts if p) + "\n"
            path.write_text(updated)
            print(f"  Updated marked section in {path}")
            return

    if dry_run:
        print(f"  [dry-run] append to {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(block)
    print(f"  Appended CodeRLM section to {path}")


def _remove_markers(path: Path, dry_run: bool, marker: str) -> None:
    marker_start = _append_marker_start(marker)
    marker_end = _append_marker_end(marker)

    if not path.exists():
        print(f"  Already absent: {path}")
        return

    content = path.read_text()
    if marker_start not in content:
        print(f"  No CodeRLM section in {path}")
        return

    if dry_run:
        print(f"  [dry-run] remove marked section from {path}")
        return

    start = content.index(marker_start)
    end = content.index(marker_end) + len(marker_end)
    before = content[:start].rstrip("\n")
    after = content[end:].lstrip("\n")
    updated = before + ("\n\n" + after if after else "") + "\n" if before else after
    path.write_text(updated)
    print(f"  Removed CodeRLM section from {path}")


def _remove_file(path: Path, dry_run: bool) -> None:
    if not path.exists():
        print(f"  Already absent: {path}")
        return
    if dry_run:
        print(f"  [dry-run] remove {path}")
        return
    path.unlink()
    print(f"  Removed {path}")


def _remove_dir_if_empty(path: Path, dry_run: bool) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    try:
        if any(path.iterdir()):
            return False
    except PermissionError:
        return False
    if dry_run:
        print(f"  [dry-run] rmdir {path}")
        return True
    path.rmdir()
    print(f"  Removed empty directory {path}")
    return True


def _remove_empty_parents(path: Path, stop: Path, dry_run: bool) -> None:
    current = path
    while current != stop and stop in current.parents:
        removed = _remove_dir_if_empty(current, dry_run)
        if not removed:
            return
        current = current.parent


# -- CLI --


def list_platforms() -> None:
    print("Available platforms:\n")
    print(f"  {'Name':<16} {'Instruction File':<48} {'Format'}")
    print(f"  {'-'*15} {'-'*47} {'-'*10}")
    for key, p in PLATFORMS.items():
        print(f"  {key:<16} {p.instruction_path:<48} {p.format}")
    print(f"\nUse --platform <name> to generate, or --platform all for everything.")
    print(f"Claude Code users: use the plugin marketplace instead (no generation needed).")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="coderlm",
        description="Generate CodeRLM instruction files for AI coding platforms",
    )
    parser.add_argument(
        "--platform",
        help="Platform to generate for (or 'all')",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available platforms",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove generated files for the specified platform",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )

    args = parser.parse_args()

    if args.list:
        list_platforms()
        return

    if not args.platform:
        parser.print_help()
        sys.exit(1)

    # Resolve platforms
    if args.platform == "all":
        targets = list(PLATFORMS.values())
    elif args.platform in PLATFORMS:
        targets = [PLATFORMS[args.platform]]
    else:
        print(f"ERROR: Unknown platform '{args.platform}'", file=sys.stderr)
        print(f"Available: {', '.join(PLATFORMS.keys())}, all", file=sys.stderr)
        sys.exit(1)

    project_root = args.project_root.resolve()
    action = "clean" if args.clean else "generate"

    if args.dry_run:
        print(f"[DRY RUN] {action} for: {', '.join(t.name for t in targets)}")
    else:
        print(f"{action.title()} for: {', '.join(t.name for t in targets)}")
    print(f"Project root: {project_root}\n")

    for platform in targets:
        print(f"[{platform.name}]")
        if args.clean:
            clean_platform(platform, project_root, args.dry_run)
        else:
            generate_platform(platform, project_root, args.dry_run)
        print()

    if not args.dry_run and not args.clean:
        print("Done. Remember to start the coderlm-server before using the CLI.")


if __name__ == "__main__":
    main()
