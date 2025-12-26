#!/usr/bin/env python3
"""
Project Analyzer Agent

Analyzes an existing research project structure and generates a comprehensive
report of its components, data flows, and organization.

This is designed to be used by AI agents to understand project structure
before migration or transformation.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Literal
import json
import re


@dataclass
class FileInfo:
    """Information about a single file."""
    path: Path
    relative_path: str
    size_bytes: int
    extension: str
    category: str  # 'code', 'data', 'config', 'doc', 'output'

    def to_dict(self) -> dict:
        return {
            'path': str(self.path),
            'relative_path': self.relative_path,
            'size_bytes': self.size_bytes,
            'extension': self.extension,
            'category': self.category,
        }


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: Path
    name: str
    docstring: Optional[str]
    imports: list[str]
    functions: list[str]
    classes: list[str]

    def to_dict(self) -> dict:
        return {
            'path': str(self.path),
            'name': self.name,
            'docstring': self.docstring,
            'imports': self.imports,
            'functions': self.functions,
            'classes': self.classes,
        }


@dataclass
class DirectoryInfo:
    """Information about a directory."""
    path: Path
    name: str
    purpose: str  # inferred purpose
    file_count: int
    subdirs: list[str]

    def to_dict(self) -> dict:
        return {
            'path': str(self.path),
            'name': self.name,
            'purpose': self.purpose,
            'file_count': self.file_count,
            'subdirs': self.subdirs,
        }


@dataclass
class ProjectAnalysis:
    """Complete analysis of a research project."""
    root_path: Path
    project_name: str

    # Structure
    directories: list[DirectoryInfo] = field(default_factory=list)
    files: list[FileInfo] = field(default_factory=list)
    modules: list[ModuleInfo] = field(default_factory=list)

    # Detected patterns
    has_pipeline: bool = False
    pipeline_stages: list[str] = field(default_factory=list)
    has_tests: bool = False
    has_docs: bool = False
    has_notebooks: bool = False
    has_manuscript: bool = False

    # Data files
    data_files: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)

    # Dependencies
    requirements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'root_path': str(self.root_path),
            'project_name': self.project_name,
            'directories': [d.to_dict() for d in self.directories],
            'files': [f.to_dict() for f in self.files],
            'modules': [m.to_dict() for m in self.modules],
            'has_pipeline': self.has_pipeline,
            'pipeline_stages': self.pipeline_stages,
            'has_tests': self.has_tests,
            'has_docs': self.has_docs,
            'has_notebooks': self.has_notebooks,
            'has_manuscript': self.has_manuscript,
            'data_files': self.data_files,
            'output_files': self.output_files,
            'requirements': self.requirements,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"# Project Analysis: {self.project_name}",
            f"",
            f"**Root:** `{self.root_path}`",
            f"",
            "## Structure",
            f"- Directories: {len(self.directories)}",
            f"- Files: {len(self.files)}",
            f"- Python modules: {len(self.modules)}",
            f"",
            "## Detected Patterns",
            f"- Pipeline: {'Yes' if self.has_pipeline else 'No'}",
        ]

        if self.pipeline_stages:
            lines.append(f"  - Stages: {', '.join(self.pipeline_stages)}")

        lines.extend([
            f"- Tests: {'Yes' if self.has_tests else 'No'}",
            f"- Documentation: {'Yes' if self.has_docs else 'No'}",
            f"- Notebooks: {'Yes' if self.has_notebooks else 'No'}",
            f"- Manuscript: {'Yes' if self.has_manuscript else 'No'}",
            "",
            "## Data",
            f"- Data files: {len(self.data_files)}",
            f"- Output files: {len(self.output_files)}",
        ])

        if self.requirements:
            lines.extend([
                "",
                "## Dependencies",
                f"- {len(self.requirements)} packages",
            ])

        return "\n".join(lines)


class ProjectAnalyzer:
    """
    Analyzes research project structure.

    Usage:
        analyzer = ProjectAnalyzer(Path("/path/to/project"))
        analysis = analyzer.analyze()
        print(analysis.summary())
    """

    # File extension categories
    CODE_EXTENSIONS = {'.py', '.r', '.R', '.jl', '.do', '.ado', '.m'}
    DATA_EXTENSIONS = {'.csv', '.parquet', '.xlsx', '.xls', '.dta', '.sav',
                       '.json', '.geojson', '.gpkg', '.shp', '.feather'}
    DOC_EXTENSIONS = {'.md', '.rst', '.txt', '.pdf', '.docx', '.tex', '.qmd'}
    CONFIG_EXTENSIONS = {'.yml', '.yaml', '.toml', '.ini', '.cfg', '.json'}
    OUTPUT_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.svg', '.eps', '.html'}

    # Directory purpose patterns
    DIR_PURPOSES = {
        'src': 'source code',
        'lib': 'library code',
        'scripts': 'executable scripts',
        'data': 'data files',
        'data_raw': 'raw data',
        'data_work': 'working data',
        'tests': 'test suite',
        'test': 'test suite',
        'docs': 'documentation',
        'doc': 'documentation',
        'notebooks': 'jupyter notebooks',
        'outputs': 'generated outputs',
        'output': 'generated outputs',
        'figures': 'figure outputs',
        'results': 'analysis results',
        'models': 'statistical models',
        'features': 'feature engineering',
        'utils': 'utility functions',
        'visualization': 'visualization code',
        'manuscript': 'manuscript files',
        'manuscript_quarto': 'quarto manuscript',
    }

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project not found: {self.project_path}")

    def analyze(self) -> ProjectAnalysis:
        """Perform full project analysis."""
        analysis = ProjectAnalysis(
            root_path=self.project_path,
            project_name=self.project_path.name,
        )

        # Scan directories
        analysis.directories = self._scan_directories()

        # Scan files
        analysis.files = self._scan_files()

        # Analyze Python modules
        analysis.modules = self._analyze_modules()

        # Detect patterns
        self._detect_patterns(analysis)

        # Categorize data/output files
        analysis.data_files = [
            f.relative_path for f in analysis.files
            if f.category == 'data'
        ]
        analysis.output_files = [
            f.relative_path for f in analysis.files
            if f.category == 'output'
        ]

        # Load requirements
        analysis.requirements = self._load_requirements()

        return analysis

    def _scan_directories(self) -> list[DirectoryInfo]:
        """Scan all directories in project."""
        dirs = []

        for path in self.project_path.rglob('*'):
            if not path.is_dir():
                continue

            # Skip hidden and cache directories
            if any(part.startswith('.') or part == '__pycache__'
                   for part in path.parts):
                continue

            name = path.name
            purpose = self.DIR_PURPOSES.get(name.lower(), 'unknown')

            # Count files directly in this directory
            file_count = len([f for f in path.iterdir() if f.is_file()])

            # List immediate subdirectories
            subdirs = [d.name for d in path.iterdir()
                      if d.is_dir() and not d.name.startswith('.')]

            dirs.append(DirectoryInfo(
                path=path,
                name=name,
                purpose=purpose,
                file_count=file_count,
                subdirs=subdirs,
            ))

        return dirs

    def _scan_files(self) -> list[FileInfo]:
        """Scan all files in project."""
        files = []

        for path in self.project_path.rglob('*'):
            if not path.is_file():
                continue

            # Skip hidden files and cache
            if any(part.startswith('.') or part == '__pycache__'
                   for part in path.parts):
                continue

            ext = path.suffix.lower()

            # Categorize file
            if ext in self.CODE_EXTENSIONS:
                category = 'code'
            elif ext in self.DATA_EXTENSIONS:
                category = 'data'
            elif ext in self.DOC_EXTENSIONS:
                category = 'doc'
            elif ext in self.CONFIG_EXTENSIONS:
                category = 'config'
            elif ext in self.OUTPUT_EXTENSIONS:
                category = 'output'
            else:
                category = 'other'

            try:
                size = path.stat().st_size
            except OSError:
                size = 0

            files.append(FileInfo(
                path=path,
                relative_path=str(path.relative_to(self.project_path)),
                size_bytes=size,
                extension=ext,
                category=category,
            ))

        return files

    def _analyze_modules(self) -> list[ModuleInfo]:
        """Analyze Python modules."""
        modules = []

        for path in self.project_path.rglob('*.py'):
            # Skip hidden and cache
            if any(part.startswith('.') or part == '__pycache__'
                   for part in path.parts):
                continue

            try:
                content = path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue

            # Extract docstring
            docstring = self._extract_docstring(content)

            # Extract imports
            imports = self._extract_imports(content)

            # Extract function names
            functions = self._extract_functions(content)

            # Extract class names
            classes = self._extract_classes(content)

            modules.append(ModuleInfo(
                path=path,
                name=path.stem,
                docstring=docstring,
                imports=imports,
                functions=functions,
                classes=classes,
            ))

        return modules

    def _extract_docstring(self, content: str) -> Optional[str]:
        """Extract module docstring."""
        # Match triple-quoted string at start of file
        match = re.match(r'^[\s]*["\'][\'"]{2}(.*?)["\'][\'"]{2}',
                        content, re.DOTALL)
        if match:
            return match.group(1).strip()[:500]  # Limit length
        return None

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements."""
        imports = []

        # Match 'import X' and 'from X import Y'
        for match in re.finditer(r'^(?:from\s+(\S+)|import\s+(\S+))',
                                 content, re.MULTILINE):
            module = match.group(1) or match.group(2)
            if module:
                # Get root module
                root = module.split('.')[0]
                if root not in imports:
                    imports.append(root)

        return imports

    def _extract_functions(self, content: str) -> list[str]:
        """Extract function definitions."""
        functions = []
        for match in re.finditer(r'^def\s+(\w+)\s*\(', content, re.MULTILINE):
            functions.append(match.group(1))
        return functions

    def _extract_classes(self, content: str) -> list[str]:
        """Extract class definitions."""
        classes = []
        for match in re.finditer(r'^class\s+(\w+)\s*[:\(]', content, re.MULTILINE):
            classes.append(match.group(1))
        return classes

    def _detect_patterns(self, analysis: ProjectAnalysis) -> None:
        """Detect project patterns."""
        dir_names = {d.name.lower() for d in analysis.directories}

        # Check for pipeline structure
        # Look for numbered directories like 00_xxx, 01_xxx
        numbered_dirs = [d.name for d in analysis.directories
                        if re.match(r'^\d+_', d.name)]
        if numbered_dirs:
            analysis.has_pipeline = True
            analysis.pipeline_stages = sorted(numbered_dirs)

        # Check for stages/ directory
        if 'stages' in dir_names:
            analysis.has_pipeline = True

        # Check for tests
        analysis.has_tests = 'tests' in dir_names or 'test' in dir_names

        # Check for docs
        analysis.has_docs = 'docs' in dir_names or 'doc' in dir_names

        # Check for notebooks
        analysis.has_notebooks = 'notebooks' in dir_names or any(
            f.extension == '.ipynb' for f in analysis.files
        )

        # Check for manuscript
        analysis.has_manuscript = (
            'manuscript' in dir_names or
            'manuscript_quarto' in dir_names or
            any(f.relative_path.endswith('.qmd') for f in analysis.files)
        )

    def _load_requirements(self) -> list[str]:
        """Load requirements from requirements.txt or setup.py."""
        requirements = []

        req_path = self.project_path / 'requirements.txt'
        if req_path.exists():
            try:
                content = req_path.read_text()
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (before ==, >=, etc.)
                        pkg = re.split(r'[<>=!]', line)[0].strip()
                        if pkg:
                            requirements.append(pkg)
            except OSError:
                pass

        return requirements


def analyze_project(project_path: str | Path) -> ProjectAnalysis:
    """Convenience function to analyze a project."""
    analyzer = ProjectAnalyzer(Path(project_path))
    return analyzer.analyze()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python project_analyzer.py <project_path>")
        sys.exit(1)

    project_path = Path(sys.argv[1])
    analyzer = ProjectAnalyzer(project_path)
    analysis = analyzer.analyze()

    print(analysis.summary())
    print("\n" + "=" * 60)
    print("\nFull JSON analysis saved to: project_analysis.json")

    Path('project_analysis.json').write_text(analysis.to_json())
