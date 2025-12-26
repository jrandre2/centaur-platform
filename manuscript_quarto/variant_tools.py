#!/usr/bin/env python3
"""
Tools for managing divergent manuscript variants.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except Exception:
    yaml = None


MAX_HASH_BYTES = 50 * 1024 * 1024


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def iso_from_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> Optional[str]:
    if path.stat().st_size > MAX_HASH_BYTES:
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path, project_root: Path, category: Optional[str] = None) -> Dict[str, Any]:
    stat = path.stat()
    record: Dict[str, Any] = {
        "path": relpath(path, project_root),
        "size_bytes": stat.st_size,
        "mtime": iso_from_ts(stat.st_mtime),
    }
    if category:
        record["category"] = category
    digest = sha256_file(path)
    if digest:
        record["sha256"] = digest
    return record


def collect_files(
    directory: Path,
    project_root: Path,
    category: Optional[str] = None,
    source_dirs: Optional[List[Path]] = None,
    include_exts: Optional[List[str]] = None,
    exclude_names: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    if not directory.exists():
        return []
    records: List[Dict[str, Any]] = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        if include_exts and path.suffix not in include_exts:
            continue
        if exclude_names and path.name in exclude_names:
            continue
        record = file_record(path, project_root, category=category)
        if source_dirs:
            hints = []
            for source_dir in source_dirs:
                candidate = source_dir / path.name
                if candidate.exists():
                    hints.append(relpath(candidate, project_root))
            if hints:
                record["source_hints"] = hints
        records.append(record)
    return records


def run_git(project_root: Path, args: List[str]) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def get_git_info(project_root: Path) -> Dict[str, Any]:
    inside = run_git(project_root, ["rev-parse", "--is-inside-work-tree"])
    if inside != "true":
        return {}
    commit = run_git(project_root, ["rev-parse", "HEAD"])
    status = run_git(project_root, ["status", "--porcelain"]) or ""
    status_lines = [line for line in status.splitlines() if line.strip()]
    return {
        "commit": commit,
        "dirty": bool(status_lines),
        "status": status_lines[:100],
    }


def load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None or not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def parse_output_dir_from_text(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    in_project = False
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "project:":
            in_project = True
            continue
        if in_project and not raw_line.startswith(" "):
            in_project = False
        if in_project and line.startswith("output-dir:"):
            return line.split(":", 1)[1].strip()
    return None


def get_output_dir(base_cfg: Dict[str, Any], profile_cfg: Dict[str, Any]) -> str:
    profile_project = profile_cfg.get("project", {}) if profile_cfg else {}
    base_project = base_cfg.get("project", {}) if base_cfg else {}
    output_dir = profile_project.get("output-dir") or base_project.get("output-dir") or "_output"
    return output_dir


def get_config_value(base_cfg: Dict[str, Any], profile_cfg: Dict[str, Any], key: str) -> Any:
    if profile_cfg and key in profile_cfg:
        return profile_cfg.get(key)
    return base_cfg.get(key)


def quarto_summary(base_cfg: Dict[str, Any], profile_cfg: Dict[str, Any]) -> Dict[str, Any]:
    output_dir = get_output_dir(base_cfg, profile_cfg)
    bibliography = get_config_value(base_cfg, profile_cfg, "bibliography")
    csl = get_config_value(base_cfg, profile_cfg, "csl")
    book_cfg = profile_cfg.get("book") if profile_cfg and "book" in profile_cfg else base_cfg.get("book", {})
    format_cfg = {}
    format_cfg.update(base_cfg.get("format", {}) if base_cfg else {})
    format_cfg.update(profile_cfg.get("format", {}) if profile_cfg else {})

    return {
        "output_dir": output_dir,
        "bibliography": bibliography,
        "csl": csl,
        "book_title": book_cfg.get("title"),
        "chapters": book_cfg.get("chapters", []),
        "appendices": book_cfg.get("appendices", []),
        "formats": sorted(format_cfg.keys()),
    }


def normalize_output_dir(output_dir: str, manuscript_root: Path, project_root: Path) -> str:
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = (manuscript_root / output_path).resolve()
    return relpath(output_path, project_root)


def load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def write_variant_markdown(path: Path, manifest: Dict[str, Any]) -> None:
    variant = manifest.get("variant", {})
    git = manifest.get("git", {})
    quarto = manifest.get("quarto", {})
    data_prov = manifest.get("data_provenance", {})
    manuscript_files = manifest.get("manuscript_files", [])
    code_files = manifest.get("code_files", [])
    support_files = manifest.get("support_files", [])

    lines = [
        f"# Manuscript Variant: {variant.get('name', '')}",
        "",
        f"- Created: {variant.get('created_at', '')}",
        f"- Snapshot: {variant.get('snapshot_at', '')}",
        f"- Profile: {variant.get('profile', '')}",
        f"- Output dir: {variant.get('output_dir', '')}",
        f"- Git commit: {git.get('commit', '')}",
        f"- Git dirty: {git.get('dirty', '')}",
        "",
        "## Manuscript Files",
        "",
    ]
    if manuscript_files:
        lines.append("| Path | Size (bytes) | SHA256 |")
        lines.append("| --- | --- | --- |")
        for item in manuscript_files:
            lines.append(
                f"| {item.get('path', '')} | {item.get('size_bytes', '')} | {item.get('sha256', '')} |"
            )
        lines.append("")
    else:
        lines.append("_None detected._\n")

    lines.extend([
        "## Data Inputs",
        "",
        f"- Data dir: {data_prov.get('data_dir', '')}",
        f"- Figures dir: {data_prov.get('figures_dir', '')}",
        f"- Diagnostics dir: {data_prov.get('diagnostics_dir', '')}",
        f"- Figures export dir: {data_prov.get('figures_export_dir', '')}",
        "",
    ])
    data_files = data_prov.get("files", [])
    if data_files:
        lines.append("| Path | Size (bytes) | SHA256 | Source hints |")
        lines.append("| --- | --- | --- | --- |")
        for item in data_files:
            hints = ", ".join(item.get("source_hints", [])) if item.get("source_hints") else ""
            lines.append(
                f"| {item.get('path', '')} | {item.get('size_bytes', '')} | {item.get('sha256', '')} | {hints} |"
            )
        lines.append("")
    else:
        lines.append("_None detected._\n")

    lines.extend([
        "## Quarto Configuration",
        "",
        f"- Base config: {quarto.get('base_config', {}).get('path', '')}",
        f"- Base config sha256: {quarto.get('base_config', {}).get('sha256', '')}",
        f"- Profile config: {quarto.get('profile_config', {}).get('path', '')}",
        f"- Profile config sha256: {quarto.get('profile_config', {}).get('sha256', '')}",
        f"- Formats: {', '.join(quarto.get('summary', {}).get('formats', []))}",
        f"- CSL: {quarto.get('summary', {}).get('csl', '')}",
        f"- Bibliography: {quarto.get('summary', {}).get('bibliography', '')}",
        "",
        "## Supporting Files",
        "",
    ])
    if code_files or support_files:
        lines.append("| Path | Size (bytes) | SHA256 |")
        lines.append("| --- | --- | --- |")
        for item in code_files + support_files:
            lines.append(
                f"| {item.get('path', '')} | {item.get('size_bytes', '')} | {item.get('sha256', '')} |"
            )
        lines.append("")
    else:
        lines.append("_None detected._\n")

    notes = manifest.get("notes", "")
    lines.extend([
        "## Notes",
        "",
        notes if notes else "_None._",
        "",
    ])

    path.write_text("\n".join(lines))


def snapshot_variant(manuscript_root: Path, name: str, created_by: Optional[str], notes: Optional[str]) -> Dict[str, Any]:
    project_root = manuscript_root.parent
    variants_root = manuscript_root / "variants"
    variant_dir = variants_root / name
    if not variant_dir.exists():
        raise FileNotFoundError(f"Variant directory not found: {variant_dir}")

    profile_name = f"variant-{name}"
    profile_file = manuscript_root / f"_quarto-{profile_name}.yml"
    base_cfg_path = manuscript_root / "_quarto.yml"

    existing_manifest = load_manifest(variant_dir / "variant.json")
    created_at = existing_manifest.get("variant", {}).get("created_at") or now_iso()
    created_by = created_by or existing_manifest.get("variant", {}).get("created_by") or os.getenv("USER", "")
    notes = notes if notes is not None else existing_manifest.get("notes", "")

    base_cfg = load_yaml(base_cfg_path)
    profile_cfg = load_yaml(profile_file)
    summary = quarto_summary(base_cfg, profile_cfg)
    if summary.get("output_dir") == "_output" and not (base_cfg or profile_cfg):
        output_override = parse_output_dir_from_text(profile_file) or parse_output_dir_from_text(base_cfg_path)
        if output_override:
            summary["output_dir"] = output_override
    output_dir = normalize_output_dir(summary.get("output_dir", "_output"), manuscript_root, project_root)

    manuscript_files = collect_files(
        variant_dir,
        project_root,
        category="manuscript",
        include_exts=[".qmd"],
        exclude_names=["variant.json", "variant.md"],
    )
    code_files = collect_files(manuscript_root / "code", project_root, category="code")

    support_files: List[Dict[str, Any]] = []
    references = manuscript_root / "references.bib"
    if references.exists():
        support_files.append(file_record(references, project_root, category="bibliography"))

    csl_value = summary.get("csl")
    if isinstance(csl_value, str):
        csl_path = manuscript_root / csl_value
        if csl_path.exists():
            support_files.append(file_record(csl_path, project_root, category="csl"))

    data_dir = manuscript_root / "data"
    figures_dir = manuscript_root / "figures"
    diagnostics_dir = project_root / "data_work" / "diagnostics"
    upstream_figures_dir = project_root / "figures"

    data_files = collect_files(
        data_dir,
        project_root,
        category="data",
        source_dirs=[diagnostics_dir] if diagnostics_dir.exists() else [],
    )
    figure_files = collect_files(
        figures_dir,
        project_root,
        category="figure",
        source_dirs=[upstream_figures_dir] if upstream_figures_dir.exists() else [],
    )

    data_provenance = {
        "data_dir": relpath(data_dir, project_root),
        "figures_dir": relpath(figures_dir, project_root),
        "diagnostics_dir": relpath(diagnostics_dir, project_root) if diagnostics_dir.exists() else "",
        "figures_export_dir": relpath(upstream_figures_dir, project_root) if upstream_figures_dir.exists() else "",
        "files": sorted(data_files + figure_files, key=lambda x: x.get("path", "")),
    }

    manifest = {
        "schema_version": 1,
        "variant": {
            "name": name,
            "path": relpath(variant_dir, project_root),
            "profile": profile_name,
            "profile_path": relpath(profile_file, project_root) if profile_file.exists() else "",
            "output_dir": output_dir,
            "created_at": created_at,
            "snapshot_at": now_iso(),
            "created_by": created_by,
        },
        "git": get_git_info(project_root),
        "quarto": {
            "base_config": file_record(base_cfg_path, project_root, category="config") if base_cfg_path.exists() else {},
            "profile_config": file_record(profile_file, project_root, category="config") if profile_file.exists() else {},
            "summary": summary,
        },
        "manuscript_files": manuscript_files,
        "code_files": code_files,
        "support_files": support_files,
        "data_provenance": data_provenance,
        "notes": notes,
    }

    manifest_path = variant_dir / "variant.json"
    write_json(manifest_path, manifest)
    write_variant_markdown(variant_dir / "variant.md", manifest)
    return manifest


def build_index(manuscript_root: Path) -> None:
    variants_root = manuscript_root / "variants"
    project_root = manuscript_root.parent
    variants: List[Dict[str, Any]] = []
    for manifest_path in sorted(variants_root.glob("*/variant.json")):
        manifest = load_manifest(manifest_path)
        if not manifest:
            continue
        variant = manifest.get("variant", {})
        git = manifest.get("git", {})
        variants.append({
            "name": variant.get("name", ""),
            "created_at": variant.get("created_at", ""),
            "snapshot_at": variant.get("snapshot_at", ""),
            "profile": variant.get("profile", ""),
            "output_dir": variant.get("output_dir", ""),
            "git_commit": git.get("commit", ""),
            "git_dirty": git.get("dirty", False),
            "manifest": relpath(manifest_path, project_root),
            "notes": manifest.get("notes", ""),
        })

    index = {
        "generated_at": now_iso(),
        "variants": variants,
    }
    write_json(variants_root / "index.json", index)

    lines = [
        "# Variants Index",
        "",
        f"Generated: {index['generated_at']}",
        "",
        "| Variant | Created | Snapshot | Profile | Output | Git | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    if variants:
        for item in variants:
            git_info = item.get("git_commit", "")
            if item.get("git_dirty"):
                git_info = f"{git_info} (dirty)"
            notes = item.get("notes", "")
            lines.append(
                f"| {item.get('name', '')} | {item.get('created_at', '')} | {item.get('snapshot_at', '')} | "
                f"{item.get('profile', '')} | {item.get('output_dir', '')} | {git_info} | {notes} |"
            )
    else:
        lines.append("| _none_ |  |  |  |  |  |  |")

    (variants_root / "INDEX.md").write_text("\n".join(lines))


def compare_records(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    if a.get("sha256") and b.get("sha256"):
        return a.get("sha256") != b.get("sha256")
    return (a.get("size_bytes"), a.get("mtime")) != (b.get("size_bytes"), b.get("mtime"))


def compare_variants(manuscript_root: Path, left: str, right: str, output: Optional[str]) -> None:
    variants_root = manuscript_root / "variants"
    left_manifest = load_manifest(variants_root / left / "variant.json")
    right_manifest = load_manifest(variants_root / right / "variant.json")

    if not left_manifest:
        raise FileNotFoundError(f"Missing manifest for variant: {left}")
    if not right_manifest:
        raise FileNotFoundError(f"Missing manifest for variant: {right}")

    def map_files(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        return {item.get("path", ""): item for item in items if item.get("path")}

    left_files = map_files(left_manifest.get("manuscript_files", []))
    right_files = map_files(right_manifest.get("manuscript_files", []))

    left_only = sorted(set(left_files) - set(right_files))
    right_only = sorted(set(right_files) - set(left_files))
    changed = sorted(
        path for path in set(left_files) & set(right_files)
        if compare_records(left_files[path], right_files[path])
    )

    left_data = map_files(left_manifest.get("data_provenance", {}).get("files", []))
    right_data = map_files(right_manifest.get("data_provenance", {}).get("files", []))

    data_left_only = sorted(set(left_data) - set(right_data))
    data_right_only = sorted(set(right_data) - set(left_data))
    data_changed = sorted(
        path for path in set(left_data) & set(right_data)
        if compare_records(left_data[path], right_data[path])
    )

    left_quarto = left_manifest.get("quarto", {})
    right_quarto = right_manifest.get("quarto", {})

    lines = [
        f"# Variant Comparison: {left} vs {right}",
        "",
        f"- Left snapshot: {left_manifest.get('variant', {}).get('snapshot_at', '')}",
        f"- Right snapshot: {right_manifest.get('variant', {}).get('snapshot_at', '')}",
        f"- Left git: {left_manifest.get('git', {}).get('commit', '')}",
        f"- Right git: {right_manifest.get('git', {}).get('commit', '')}",
        "",
        "## Manuscript Files",
        "",
        f"- Only in {left}: {', '.join(left_only) if left_only else 'none'}",
        f"- Only in {right}: {', '.join(right_only) if right_only else 'none'}",
        f"- Changed: {', '.join(changed) if changed else 'none'}",
        "",
        "## Data Inputs",
        "",
        f"- Only in {left}: {', '.join(data_left_only) if data_left_only else 'none'}",
        f"- Only in {right}: {', '.join(data_right_only) if data_right_only else 'none'}",
        f"- Changed: {', '.join(data_changed) if data_changed else 'none'}",
        "",
        "## Quarto Configuration",
        "",
        f"- Base config sha256: {left_quarto.get('base_config', {}).get('sha256', '')} vs {right_quarto.get('base_config', {}).get('sha256', '')}",
        f"- Profile config sha256: {left_quarto.get('profile_config', {}).get('sha256', '')} vs {right_quarto.get('profile_config', {}).get('sha256', '')}",
        f"- Output dir: {left_manifest.get('variant', {}).get('output_dir', '')} vs {right_manifest.get('variant', {}).get('output_dir', '')}",
        "",
    ]

    report = "\n".join(lines)
    if output:
        Path(output).write_text(report)
    else:
        print(report)


def main() -> None:
    manuscript_root = Path(__file__).resolve().parent
    variants_root = manuscript_root / "variants"
    variants_root.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(description="Manage manuscript variants.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser("snapshot", help="Capture metadata for a variant.")
    snapshot_parser.add_argument("--variant", required=True, help="Variant name (folder under variants/).")
    snapshot_parser.add_argument("--created-by", help="Creator name for metadata.")
    snapshot_parser.add_argument("--notes", help="Notes to store in manifest.")
    snapshot_parser.add_argument("--no-index", action="store_true", help="Skip rebuilding the index.")

    index_parser = subparsers.add_parser("index", help="Rebuild the variants index.")

    compare_parser = subparsers.add_parser("compare", help="Compare two variants.")
    compare_parser.add_argument("--left", required=True, help="Left variant name.")
    compare_parser.add_argument("--right", required=True, help="Right variant name.")
    compare_parser.add_argument("--output", help="Write report to a file.")

    args = parser.parse_args()

    if args.command == "snapshot":
        snapshot_variant(manuscript_root, args.variant, args.created_by, args.notes)
        if not args.no_index:
            build_index(manuscript_root)
        return

    if args.command == "index":
        build_index(manuscript_root)
        return

    if args.command == "compare":
        compare_variants(manuscript_root, args.left, args.right, args.output)
        return


if __name__ == "__main__":
    main()
