#!/usr/bin/env python3
"""
Tests for manuscript_quarto/variant_tools.py
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

MANUSCRIPT_DIR = Path(__file__).parent.parent.parent / "manuscript_quarto"
sys.path.insert(0, str(MANUSCRIPT_DIR))

import variant_tools


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def setup_project(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    manuscript_root = project_root / "manuscript_quarto"

    (manuscript_root / "variants").mkdir(parents=True)
    (manuscript_root / "code").mkdir()
    (manuscript_root / "data").mkdir()
    (manuscript_root / "figures").mkdir()
    (manuscript_root / "csl").mkdir()

    (project_root / "data_work" / "diagnostics").mkdir(parents=True)
    (project_root / "figures").mkdir()

    write_text(manuscript_root / "code" / "_common.py", "# stub\n")
    write_text(manuscript_root / "references.bib", "@article{test, title={Test}}\n")
    write_text(manuscript_root / "csl" / "apa.csl", "<style></style>\n")

    write_text(
        manuscript_root / "_quarto.yml",
        "\n".join([
            "project:",
            "  output-dir: _output",
            "book:",
            "  title: \"Test\"",
            "  chapters:",
            "    - index.qmd",
            "  appendices:",
            "    - appendix-a-data.qmd",
            "bibliography: references.bib",
            "csl: csl/apa.csl",
            "format:",
            "  html:",
            "    toc: true",
        ]) + "\n",
    )

    return project_root, manuscript_root


def create_variant(manuscript_root: Path, name: str, content: str) -> None:
    variant_dir = manuscript_root / "variants" / name
    variant_dir.mkdir(parents=True, exist_ok=True)
    write_text(variant_dir / "index.qmd", content)
    write_text(variant_dir / "appendix-a-data.qmd", f"{content}\nappendix")

    write_text(
        manuscript_root / f"_quarto-variant-{name}.yml",
        "\n".join([
            "project:",
            f"  output-dir: _output/variants/{name}",
            "book:",
            "  chapters:",
            f"    - variants/{name}/index.qmd",
            "  appendices:",
            f"    - variants/{name}/appendix-a-data.qmd",
        ]) + "\n",
    )


def populate_inputs(project_root: Path, manuscript_root: Path) -> None:
    write_text(manuscript_root / "data" / "main_results.csv", "x,y\n1,2\n")
    write_text(manuscript_root / "figures" / "fig_main.png", "PNGDATA")
    write_text(project_root / "data_work" / "diagnostics" / "main_results.csv", "x,y\n1,2\n")
    write_text(project_root / "figures" / "fig_main.png", "PNGDATA")


def test_snapshot_variant_creates_manifest(tmp_path: Path) -> None:
    project_root, manuscript_root = setup_project(tmp_path)
    create_variant(manuscript_root, "test", "variant test")
    populate_inputs(project_root, manuscript_root)

    manifest = variant_tools.snapshot_variant(manuscript_root, "test", "Tester", "Initial snapshot")

    manifest_path = manuscript_root / "variants" / "test" / "variant.json"
    markdown_path = manuscript_root / "variants" / "test" / "variant.md"
    assert manifest_path.exists()
    assert markdown_path.exists()

    assert manifest["variant"]["name"] == "test"
    assert manifest["variant"]["profile"] == "variant-test"
    assert manifest["quarto"]["summary"]["output_dir"] == "_output/variants/test"

    manuscript_paths = {item["path"] for item in manifest["manuscript_files"]}
    assert "manuscript_quarto/variants/test/index.qmd" in manuscript_paths

    data_paths = {item["path"] for item in manifest["data_provenance"]["files"]}
    assert "manuscript_quarto/data/main_results.csv" in data_paths
    assert "manuscript_quarto/figures/fig_main.png" in data_paths


def test_build_index_and_compare(tmp_path: Path) -> None:
    project_root, manuscript_root = setup_project(tmp_path)
    populate_inputs(project_root, manuscript_root)

    create_variant(manuscript_root, "test", "variant test")
    create_variant(manuscript_root, "alt", "variant alt")

    variant_tools.snapshot_variant(manuscript_root, "test", "Tester", "first")
    variant_tools.snapshot_variant(manuscript_root, "alt", "Tester", "second")
    variant_tools.build_index(manuscript_root)

    index_path = manuscript_root / "variants" / "index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text())
    names = {item["name"] for item in index["variants"]}
    assert {"test", "alt"} <= names

    report_path = tmp_path / "compare.md"
    variant_tools.compare_variants(manuscript_root, "test", "alt", str(report_path))
    report = report_path.read_text()
    assert "Variant Comparison" in report
    assert "Only in test:" in report
    assert "Only in alt:" in report
