"""
AI Agents for Research Project Management

This package provides AI-powered tools for:
- Analyzing existing research project structures
- Mapping projects to standardized templates
- Generating migration plans
- Executing project transformations
"""

from .project_analyzer import ProjectAnalyzer
from .structure_mapper import StructureMapper
from .migration_planner import MigrationPlanner
from .migration_executor import MigrationExecutor

__all__ = [
    'ProjectAnalyzer',
    'StructureMapper',
    'MigrationPlanner',
    'MigrationExecutor',
]
