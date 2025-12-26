#!/usr/bin/env python3
"""
Structure Mapper

Maps an analyzed project structure to the standardized template format.
Identifies how source components should be reorganized.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import json

from .project_analyzer import ProjectAnalysis, ModuleInfo


@dataclass
class MappingRule:
    """A rule for mapping source to target."""
    source_pattern: str  # e.g., "src/*/features/*"
    target_location: str  # e.g., "src/stages/s02_features.py"
    action: str  # 'move', 'merge', 'transform', 'copy'
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            'source_pattern': self.source_pattern,
            'target_location': self.target_location,
            'action': self.action,
            'notes': self.notes,
        }


@dataclass
class StructureMapping:
    """Complete mapping from source to target structure."""
    source_project: str
    target_template: str
    rules: list[MappingRule] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'source_project': self.source_project,
            'target_template': self.target_template,
            'rules': [r.to_dict() for r in self.rules],
            'warnings': self.warnings,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"# Structure Mapping",
            f"",
            f"**Source:** {self.source_project}",
            f"**Target:** {self.target_template}",
            f"",
            f"## Mapping Rules ({len(self.rules)})",
            "",
        ]

        for rule in self.rules:
            lines.append(f"- `{rule.source_pattern}` → `{rule.target_location}`")
            lines.append(f"  Action: {rule.action}")
            if rule.notes:
                lines.append(f"  Notes: {rule.notes}")

        if self.warnings:
            lines.extend([
                "",
                "## Warnings",
                "",
            ])
            for warning in self.warnings:
                lines.append(f"- {warning}")

        return "\n".join(lines)


class StructureMapper:
    """
    Maps source project structure to template format.

    Usage:
        from project_analyzer import analyze_project

        analysis = analyze_project("/path/to/project")
        mapper = StructureMapper(analysis)
        mapping = mapper.generate_mapping()
        print(mapping.summary())
    """

    # Template stage structure
    TEMPLATE_STAGES = [
        ('s00_ingest', ['data', 'loader', 'ingest', 'load', 'import']),
        ('s01_link', ['link', 'merge', 'join', 'match']),
        ('s02_panel', ['panel', 'construct', 'build', 'prepare']),
        ('s03_estimation', ['model', 'estim', 'regress', 'fit', 'sem']),
        ('s04_robustness', ['robust', 'sensitiv', 'check', 'valid']),
        ('s05_figures', ['visual', 'plot', 'figure', 'graph', 'chart']),
        ('s06_manuscript', ['manuscript', 'report', 'output']),
    ]

    def __init__(self, analysis: ProjectAnalysis):
        self.analysis = analysis

    def generate_mapping(self) -> StructureMapping:
        """Generate mapping from analysis to template."""
        mapping = StructureMapping(
            source_project=str(self.analysis.root_path),
            target_template='Research Project Management Platform',
        )

        # Map Python modules to stages
        for module in self.analysis.modules:
            rule = self._map_module_to_stage(module)
            if rule:
                mapping.rules.append(rule)

        # Map data directories
        for dir_info in self.analysis.directories:
            if dir_info.purpose == 'data files':
                mapping.rules.append(MappingRule(
                    source_pattern=f"{dir_info.name}/*",
                    target_location="data_raw/",
                    action="copy",
                    notes="Raw data files",
                ))

        # Map output directories
        for dir_info in self.analysis.directories:
            if dir_info.purpose in ('generated outputs', 'figure outputs'):
                mapping.rules.append(MappingRule(
                    source_pattern=f"{dir_info.name}/*",
                    target_location="manuscript_quarto/figures/",
                    action="copy",
                    notes="Output files",
                ))

        # Map documentation
        if self.analysis.has_docs:
            mapping.rules.append(MappingRule(
                source_pattern="docs/*",
                target_location="doc/",
                action="copy",
                notes="Documentation",
            ))

        # Map tests
        if self.analysis.has_tests:
            mapping.rules.append(MappingRule(
                source_pattern="tests/*",
                target_location="tests/",
                action="copy",
                notes="Test suite",
            ))

        # Generate warnings for unmapped content
        self._generate_warnings(mapping)

        return mapping

    def _map_module_to_stage(self, module: ModuleInfo) -> Optional[MappingRule]:
        """Map a Python module to a template stage."""
        module_name = module.name.lower()
        module_path = str(module.path.relative_to(self.analysis.root_path))

        # Check against each stage's keywords
        for stage_name, keywords in self.TEMPLATE_STAGES:
            if any(kw in module_name for kw in keywords):
                return MappingRule(
                    source_pattern=module_path,
                    target_location=f"src/stages/{stage_name}.py",
                    action="merge",
                    notes=f"Contains: {', '.join(module.functions[:5])}",
                )

        # Check module path for hints
        for stage_name, keywords in self.TEMPLATE_STAGES:
            if any(kw in module_path.lower() for kw in keywords):
                return MappingRule(
                    source_pattern=module_path,
                    target_location=f"src/stages/{stage_name}.py",
                    action="merge",
                    notes=f"Path match: {module_path}",
                )

        # Utility modules go to utils
        if 'util' in module_path.lower() or 'helper' in module_path.lower():
            return MappingRule(
                source_pattern=module_path,
                target_location="src/utils/",
                action="copy",
                notes="Utility module",
            )

        return None

    def _generate_warnings(self, mapping: StructureMapping) -> None:
        """Generate warnings for potential issues."""
        mapped_paths = {r.source_pattern for r in mapping.rules}

        # Check for unmapped Python files
        for module in self.analysis.modules:
            rel_path = str(module.path.relative_to(self.analysis.root_path))
            if rel_path not in mapped_paths:
                mapping.warnings.append(
                    f"Unmapped module: {rel_path}"
                )

        # Check for notebooks
        if self.analysis.has_notebooks:
            mapping.warnings.append(
                "Project contains Jupyter notebooks - manual review needed"
            )


def map_project(analysis: ProjectAnalysis) -> StructureMapping:
    """Convenience function to map a project."""
    mapper = StructureMapper(analysis)
    return mapper.generate_mapping()
