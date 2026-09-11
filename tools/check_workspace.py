#!/usr/bin/env python3
"""Check authored package assets, syntax and local Markdown references."""

import ast
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {".git", "build", "install", "log", "__pycache__", ".venv"}


def main():
    errors = []
    manifests = []
    files = [p for p in ROOT.rglob("*") if p.is_file() and not IGNORED.intersection(p.relative_to(ROOT).parts)]
    for path in files:
        if path.suffix.lower() in {".jpg", ".png", ".pdf"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
            is_chinese_doc = path.suffix == ".md" and path.stem.endswith("_cn")
            if not is_chinese_doc and re.search(r"[\u3400-\u9fff]", content):
                errors.append(f"{path.relative_to(ROOT)}: CJK text is only allowed in *_cn.md documents")
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
    if len(manifests) != 10 or len(set(manifests)) != len(manifests):
        errors.append("expected ten uniquely named first-party packages")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: {len(manifests)} packages; syntax, language pairs, text policy and local links checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
