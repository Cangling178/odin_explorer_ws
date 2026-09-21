#!/usr/bin/env python3
"""Check authored package assets, syntax and local Markdown references."""

import ast
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {".git", "build", "install", "log", "__pycache__", ".venv"}
C_STYLE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
HASH_COMMENT_SUFFIXES = {".py", ".yaml", ".yml", ".sh", ".bash", ".cmake"}
HASH_COMMENT_NAMES = {".clang-format", ".clang-tidy", "CMakeLists.txt"}
CJK_PATTERN = re.compile(r"[\u3400-\u9fff]")


def strip_c_style_comments(content):
    """Remove C/C++ comments while preserving strings and line structure."""
    result = []
    index = 0
    state = "code"
    quote = ""
    while index < len(content):
        char = content[index]
        following = content[index + 1] if index + 1 < len(content) else ""
        if state == "code":
            if char in {'"', "'"}:
                state = "string"
                quote = char
                result.append(char)
            elif char == "/" and following == "/":
                state = "line_comment"
                result.extend("  ")
                index += 1
            elif char == "/" and following == "*":
                state = "block_comment"
                result.extend("  ")
                index += 1
            else:
                result.append(char)
        elif state == "string":
            result.append(char)
            if char == "\\" and following:
                result.append(following)
                index += 1
            elif char == quote:
                state = "code"
        elif state == "line_comment":
            result.append("\n" if char == "\n" else " ")
            if char == "\n":
                state = "code"
        else:
            result.append("\n" if char == "\n" else " ")
            if char == "*" and following == "/":
                result.append(" ")
                index += 1
                state = "code"
        index += 1
    return "".join(result)


def strip_hash_comments(content):
    """Remove # comments while preserving quoted text and line structure."""
    result = []
    for line in content.splitlines(keepends=True):
        quote = ""
        escaped = False
        comment_at = None
        for index, char in enumerate(line):
            if escaped:
                escaped = False
                continue
            if char == "\\" and quote:
                escaped = True
            elif quote:
                if char == quote:
                    quote = ""
            elif char in {'"', "'"}:
                quote = char
            elif char == "#":
                comment_at = index
                break
        if comment_at is None:
            result.append(line)
        else:
            newline = "\n" if line.endswith("\n") else ""
            result.append(line[:comment_at] + newline)
    return "".join(result)


def cjk_outside_comments(path, content):
    if path.suffix.lower() in C_STYLE_SUFFIXES:
        content = strip_c_style_comments(content)
    elif path.suffix.lower() in HASH_COMMENT_SUFFIXES or path.name in HASH_COMMENT_NAMES:
        content = strip_hash_comments(content)
    return CJK_PATTERN.search(content) is not None


def main():
    errors = []
    manifests = []
    # Honor repository exclusions, including the vendor underlay and nested builds.
    # Include new authored files so this also checks changes before staging.
    candidates = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode("utf-8").split("\0")
    files = [ROOT / name for name in sorted(set(candidates)) if name
             and (ROOT / name).is_file() and not IGNORED.intersection(Path(name).parts)]
    for path in files:
        if path.suffix.lower() in {".jpg", ".png", ".pdf", ".stl", ".sldprt", ".step", ".stp"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
            is_chinese_doc = path.suffix == ".md" and path.stem.endswith("_cn")
            if not is_chinese_doc and cjk_outside_comments(path, content):
                errors.append(
                    f"{path.relative_to(ROOT)}: CJK text is only allowed in comments and *_cn.md documents"
                )
            if path.suffix == ".py":
                ast.parse(content)
            if path.suffix in {".yaml", ".yml", ".repos"}:
                yaml.safe_load(content)
            if path.name == "package.xml":
                manifest = ET.fromstring(content)
                name = manifest.findtext("name")
                if name != path.parent.name:
                    errors.append(f"{path}: package name mismatch")
                if not (path.parent / "CMakeLists.txt").is_file():
                    errors.append(f"{path}: missing CMakeLists.txt")
                manifests.append(name)
            if path.suffix == ".md":
                counterpart = path.with_name(
                    path.stem[:-3] + ".md" if is_chinese_doc else path.stem + "_cn.md"
                )
                if not counterpart.is_file():
                    errors.append(f"{path.relative_to(ROOT)}: missing language counterpart {counterpart.name}")
                elif f"]({counterpart.name})" not in content:
                    errors.append(f"{path.relative_to(ROOT)}: missing language navigation link")
                for target in re.findall(r"\]\(([^)]+)\)", content):
                    target = target.split("#")[0]
                    if not target or re.match(r"[a-zA-Z]+:", target):
                        continue
                    if not (path.parent / unquote(target)).exists():
                        errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
        except (ValueError, SyntaxError, ET.ParseError, yaml.YAMLError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    if len(manifests) != 11 or len(set(manifests)) != len(manifests):
        errors.append("expected eleven uniquely named first-party packages")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: {len(manifests)} packages; syntax, language pairs, text policy and local links checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
