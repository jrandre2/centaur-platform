#!/usr/bin/env python3
"""
Migration Planner

Generates a detailed migration plan for moving a project to the
standardized template format. Creates actionable steps that can
be executed by humans or AI agents.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
import json

from .project_analyzer import ProjectAnalysis
from .structure_mapper import StructureMapping, MappingRule


@dataclass
class MigrationStep:
    """A single step in the migration plan."""
    order: int
    category: str  # 'setup', 'copy', 'transform', 'generate', 'verify'
    action: str
    source: Optional[str] = None
    target: Optional[str] = None
    details: str = ""
    completed: bool = False

    def to_dict(self) -> dict:
        return {
            'order': self.order,
            'category': self.category,
            'action': self.action,
            'source': self.source,
            'target': self.target,
            'details': self.details,
            'completed': self.completed,
        }

    def to_markdown(self) -> str:
        """Format step as markdown checklist item."""
        checkbox = "[x]" if self.completed else "[ ]"
        line = f"- {checkbox} **{self.category.upper()}**: {self.action}"
        if self.source and self.target:
            line += f"\n  - From: `{self.source}`"
            line += f"\n  - To: `{self.target}`"
        if self.details:
            line += f"\n  - Details: {self.details}"
        return line


@dataclass
class MigrationPlan:
    """Complete migration plan."""
    source_project: str
    target_location: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    steps: list[MigrationStep] = field(default_factory=list)
    estimated_complexity: str = "medium"  # 'low', 'medium', 'high'
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'source_project': self.source_project,
            'target_location': self.target_location,
            'created_at': self.created_at,
            'steps': [s.to_dict() for s in self.steps],
            'estimated_complexity': self.estimated_complexity,
            'notes': self.notes,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_markdown(self) -> str:
        """Generate markdown migration plan document."""
        lines = [
            f"# Migration Plan",
            f"",
            f"**Source:** `{self.source_project}`",
            f"**Target:** `{self.target_location}`",
            f"**Created:** {self.created_at}",
            f"**Complexity:** {self.estimated_complexity}",
            f"",
            "---",
            "",
            "## Steps",
            "",
        ]

        # Group steps by category
        categories = {}
        for step in self.steps:
            if step.category not in categories:
                categories[step.category] = []
            categories[step.category].append(step)

        category_order = ['setup', 'copy', 'transform', 'generate', 'verify']
        for cat in category_order:
            if cat in categories:
                lines.append(f"### {cat.title()}")
                lines.append("")
                for step in categories[cat]:
                    lines.append(step.to_markdown())
                    lines.append("")

        if self.notes:
            lines.extend([
                "---",
                "",
                "## Notes",
                "",
            ])
            for note in self.notes:
                lines.append(f"- {note}")

        return "\n".join(lines)

    @property
    def completion_percentage(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.completed)
        return (completed / len(self.steps)) * 100


class MigrationPlanner:
    """
    Generates migration plans from project analysis and structure mapping.

    Usage:
        from project_analyzer import analyze_project
        from structure_mapper import map_project

        analysis = analyze_project("/path/to/project")
        mapping = map_project(analysis)

        planner = MigrationPlanner(analysis, mapping)
        plan = planner.generate_plan("/path/to/target")
        print(plan.to_markdown())
    """

    def __init__(
        self,
        analysis: ProjectAnalysis,
        mapping: StructureMapping
    ):
        self.analysis = analysis
        self.mapping = mapping

    def generate_plan(self, target_location: str) -> MigrationPlan:
        """Generate complete migration plan."""
        plan = MigrationPlan(
            source_project=str(self.analysis.root_path),
            target_location=target_location,
        )

        step_order = 0

        # Phase 1: Setup
        step_order = self._add_setup_steps(plan, step_order)

        # Phase 2: Copy operations
        step_order = self._add_copy_steps(plan, step_order)

        # Phase 3: Transform operations
        step_order = self._add_transform_steps(plan, step_order)

        # Phase 4: Generate new files
        step_order = self._add_generate_steps(plan, step_order)

        # Phase 5: Verification
        step_order = self._add_verify_steps(plan, step_order)

        # Add notes from mapping warnings
        plan.notes.extend(self.mapping.warnings)

        # Estimate complexity
        plan.estimated_complexity = self._estimate_complexity()

        return plan

    def _add_setup_steps(self, plan: MigrationPlan, order: int) -> int:
        """Add initial setup steps."""
        steps = [
            ("Create target directory structure", "mkdir -p src/stages src/utils tests doc figures data_raw data_work"),
            ("Initialize git repository", "git init"),
            ("Create virtual environment", "python -m venv .venv"),
            ("Copy template CLAUDE.md", "Copy AI agent instructions"),
            ("Copy template requirements.txt", "Base dependencies"),
        ]

        for action, details in steps:
            order += 1
            plan.steps.append(MigrationStep(
                order=order,
                category='setup',
                action=action,
                target=plan.target_location,
                details=details,
            ))

        return order

    def _add_copy_steps(self, plan: MigrationPlan, order: int) -> int:
        """Add file copy steps from mapping rules."""
        for rule in self.mapping.rules:
            if rule.action == 'copy':
                order += 1
                plan.steps.append(MigrationStep(
                    order=order,
                    category='copy',
                    action=f"Copy {rule.source_pattern}",
                    source=rule.source_pattern,
                    target=rule.target_location,
                    details=rule.notes,
                ))

        return order

    def _add_transform_steps(self, plan: MigrationPlan, order: int) -> int:
        """Add transformation steps for code that needs refactoring."""
        # Group merge rules by target
        merge_targets = {}
        for rule in self.mapping.rules:
            if rule.action == 'merge':
                if rule.target_location not in merge_targets:
                    merge_targets[rule.target_location] = []
                merge_targets[rule.target_location].append(rule)

        for target, rules in merge_targets.items():
            order += 1
            sources = [r.source_pattern for r in rules]
            plan.steps.append(MigrationStep(
                order=order,
                category='transform',
                action=f"Merge modules into {target}",
                source=", ".join(sources[:3]) + ("..." if len(sources) > 3 else ""),
                target=target,
                details=f"Combine {len(rules)} source modules",
            ))

        return order

    def _add_generate_steps(self, plan: MigrationPlan, order: int) -> int:
        """Add steps for generating new documentation."""
        generate_items = [
            ("Generate DATA_DICTIONARY.md", "doc/DATA_DICTIONARY.md",
             "Extract variable definitions from code"),
            ("Generate METHODOLOGY.md", "doc/METHODOLOGY.md",
             "Document statistical methods from model code"),
            ("Generate PIPELINE.md", "doc/PIPELINE.md",
             "Document pipeline stages and data flow"),
            ("Create pipeline.py CLI", "src/pipeline.py",
             "Main entry point with subcommands"),
        ]

        for action, target, details in generate_items:
            order += 1
            plan.steps.append(MigrationStep(
                order=order,
                category='generate',
                action=action,
                target=target,
                details=details,
            ))

        return order

    def _add_verify_steps(self, plan: MigrationPlan, order: int) -> int:
        """Add verification steps."""
        verify_items = [
            ("Verify imports resolve", "Run: python -c 'import src.stages'"),
            ("Run existing tests", "pytest tests/"),
            ("Verify data loading", "python src/pipeline.py ingest_data --demo"),
            ("Check documentation links", "Verify all doc references"),
        ]

        for action, details in verify_items:
            order += 1
            plan.steps.append(MigrationStep(
                order=order,
                category='verify',
                action=action,
                details=details,
            ))

        return order

    def _estimate_complexity(self) -> str:
        """Estimate migration complexity."""
        n_modules = len(self.analysis.modules)
        n_warnings = len(self.mapping.warnings)
        has_notebooks = self.analysis.has_notebooks

        score = 0
        if n_modules > 20:
            score += 2
        elif n_modules > 10:
            score += 1

        if n_warnings > 5:
            score += 2
        elif n_warnings > 2:
            score += 1

        if has_notebooks:
            score += 1

        if score >= 4:
            return 'high'
        elif score >= 2:
            return 'medium'
        else:
            return 'low'


def generate_migration_plan(
    analysis: ProjectAnalysis,
    mapping: StructureMapping,
    target_location: str
) -> MigrationPlan:
    """Convenience function to generate a migration plan."""
    planner = MigrationPlanner(analysis, mapping)
    return planner.generate_plan(target_location)
