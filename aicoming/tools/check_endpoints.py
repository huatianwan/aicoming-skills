#!/usr/bin/env python3
"""Fail when the generated endpoint table diverges from its manifest."""
from __future__ import annotations
import argparse, json, re, urllib.request
from pathlib import Path

def load(source: str) -> dict:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source, timeout=20) as response: return json.load(response)
    return json.loads(Path(source).read_text("utf-8"))

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("manifest")
    parser.add_argument("--reference", type=Path, default=Path("aicoming/references/endpoints.generated.md")); args = parser.parse_args()
    manifest = load(args.manifest); content = args.reference.read_text("utf-8")
    documented = set(re.findall(r"\|\s*(?:GET|POST|PATCH|PUT|DELETE)\s*\|\s*`([^`]+)`", content))
    expected = {str(ep["path"]) for ep in manifest.get("endpoints", [])}
    missing, extra = sorted(expected - documented), sorted(documented - expected)
    if missing or extra: raise SystemExit(f"端点文档不一致 missing={missing} extra={extra}")
    print(f"端点对账通过：{len(expected)} 个"); return 0

if __name__ == "__main__": raise SystemExit(main())
