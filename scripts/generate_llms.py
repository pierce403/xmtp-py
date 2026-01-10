#!/usr/bin/env python3
"""Generate LLM reference files from docs and public Python APIs."""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import difflib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
LLMS_DIR = REPO_ROOT / 'llms'


@dataclass(frozen=True)
class DocSection:
    title: str
    files: list[Path]


@dataclass(frozen=True)
class ApiGroup:
    title: str
    roots: list[Path]


@dataclass(frozen=True)
class LlmsConfig:
    filename: str
    title: str
    description: str
    doc_sections: list[DocSection]
    api_groups: list[ApiGroup]


@dataclass(frozen=True)
class FunctionInfo:
    name: str
    signature: str
    summary: str
    is_async: bool


@dataclass(frozen=True)
class ClassInfo:
    name: str
    signature: str
    summary: str
    methods: list[FunctionInfo]


@dataclass(frozen=True)
class ModuleInfo:
    name: str
    summary: str
    exports: list[str]
    constants: list[str]
    classes: list[ClassInfo]
    functions: list[FunctionInfo]


def _read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def _format_generated_at(now: dt.datetime) -> str:
    stamp = now.strftime('%I:%M %p UTC / %B %d, %Y')
    return stamp[1:] if stamp.startswith('0') else stamp


def _normalize_for_check(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if 'Generated at:' in line:
            prefix, _ = line.split('Generated at:', 1)
            lines.append(f'{prefix}Generated at: <generated>')
        else:
            lines.append(line.rstrip())
    return '\n'.join(lines).strip() + '\n'


def _to_ascii(text: str) -> str:
    return text.encode('ascii', errors='ignore').decode('ascii')


def _iter_py_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob('*.py')):
        if '__pycache__' in path.parts:
            continue
        if any(part.endswith('.egg-info') for part in path.parts):
            continue
        yield path


def _module_name_from_path(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix('')
    parts = list(rel.parts)
    if parts and parts[-1] == '__init__':
        parts = parts[:-1]
    return '.'.join(parts)


def _parse_dunder_all(tree: ast.AST) -> list[str]:
    for node in getattr(tree, 'body', []):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    return _parse_all_value(node.value)
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == '__all__':
                return _parse_all_value(node.value)
    return []


def _parse_all_value(value: ast.AST | None) -> list[str]:
    if not isinstance(value, (ast.List, ast.Tuple)):
        return []
    items: list[str] = []
    for elt in value.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
            items.append(elt.value)
    return items


def _summarize_docstring(docstring: str | None) -> str:
    if not docstring:
        return ''
    return _to_ascii(docstring.strip().splitlines()[0].strip())


def _format_annotation(node: ast.AST | None) -> str:
    if node is None:
        return ''
    return ast.unparse(node)


def _format_default(node: ast.AST | None) -> str:
    if node is None:
        return ''
    return ast.unparse(node)


def _format_arg(arg: ast.arg, default: ast.AST | None) -> str:
    rendered = arg.arg
    annotation = _format_annotation(arg.annotation)
    if annotation:
        rendered = f'{rendered}: {annotation}'
    if default is not None:
        rendered = f'{rendered} = {_format_default(default)}'
    return rendered


def _build_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = node.args
    parts: list[str] = []

    posonly = list(args.posonlyargs)
    normal = list(args.args)
    combined = posonly + normal
    defaults = list(args.defaults)
    default_offset = len(combined) - len(defaults)

    for index, arg in enumerate(combined):
        default = defaults[index - default_offset] if index >= default_offset else None
        parts.append(_format_arg(arg, default))
    if posonly:
        parts.insert(len(posonly), '/')

    if args.vararg:
        parts.append(f'*{_format_arg(args.vararg, None)}')

    if args.kwonlyargs:
        if not args.vararg:
            parts.append('*')
        for kw_arg, kw_default in zip(args.kwonlyargs, args.kw_defaults):
            parts.append(_format_arg(kw_arg, kw_default))

    if args.kwarg:
        parts.append(f'**{_format_arg(args.kwarg, None)}')

    signature = f"({', '.join(parts)})"
    returns = _format_annotation(node.returns)
    if returns:
        signature = f'{signature} -> {returns}'
    return signature


def _format_constant(name: str, value: ast.AST | None) -> str:
    if value is None:
        return name
    rendered = ast.unparse(value)
    if len(rendered) > 120:
        rendered = rendered[:117] + '...'
    return _to_ascii(f'{name} = {rendered}')


def _collect_module_info(module_path: Path, module_name: str) -> ModuleInfo:
    source = _read_text(module_path)
    tree = ast.parse(source, filename=str(module_path))
    module_doc = _summarize_docstring(ast.get_docstring(tree))
    exports = _parse_dunder_all(tree)
    export_set = set(exports) if exports else None

    def is_public(name: str) -> bool:
        if export_set is not None:
            return name in export_set
        return not name.startswith('_')

    constants: list[str] = []
    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and is_public(node.name):
            class_summary = _summarize_docstring(ast.get_docstring(node))
            bases = [ast.unparse(base) for base in node.bases] if node.bases else []
            signature = f"class {node.name}({', '.join(bases)})" if bases else f'class {node.name}'
            methods: list[FunctionInfo] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith('_'):
                    method_summary = _summarize_docstring(ast.get_docstring(item))
                    method_signature = _build_signature(item)
                    methods.append(
                        FunctionInfo(
                            name=item.name,
                            signature=f'{item.name}{method_signature}',
                            summary=method_summary,
                            is_async=isinstance(item, ast.AsyncFunctionDef),
                        )
                    )
            classes.append(
                ClassInfo(
                    name=node.name,
                    signature=signature,
                    summary=class_summary,
                    methods=methods,
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(node.name):
            func_summary = _summarize_docstring(ast.get_docstring(node))
            func_signature = _build_signature(node)
            functions.append(
                FunctionInfo(
                    name=node.name,
                    signature=f'{node.name}{func_signature}',
                    summary=func_summary,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                )
            )
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id != '__all__' and is_public(target.id):
                    constants.append(_format_constant(target.id, node.value))
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id != '__all__' and is_public(node.target.id):
                constants.append(_format_constant(node.target.id, node.value))

    return ModuleInfo(
        name=module_name,
        summary=module_doc,
        exports=exports,
        constants=constants,
        classes=classes,
        functions=functions,
    )


def _render_docs_section(section: DocSection) -> list[str]:
    lines: list[str] = [f'## {section.title}', '']
    for path in section.files:
        rel = path.relative_to(REPO_ROOT)
        lines.append(f'### {rel.as_posix()}')
        lines.append('')
        content = _to_ascii(_read_text(path).strip())
        lines.append(content)
        lines.append('')
    return lines


def _render_api_group(group: ApiGroup) -> list[str]:
    lines: list[str] = [f'## {group.title} API Reference', '']
    modules: list[ModuleInfo] = []
    for root in group.roots:
        for path in _iter_py_files(root):
            module_name = _module_name_from_path(root, path)
            if not module_name:
                continue
            modules.append(_collect_module_info(path, module_name))

    for module in sorted(modules, key=lambda m: m.name):
        if not (module.exports or module.constants or module.classes or module.functions or module.summary):
            continue
        lines.append(f'### Module: {module.name}')
        lines.append('')
        if module.summary:
            lines.append(f'Doc: {module.summary}')
            lines.append('')
        if module.exports:
            lines.append(f"Exports: {', '.join(module.exports)}")
            lines.append('')
        if module.constants:
            lines.append('Constants:')
            for const in module.constants:
                lines.append(f'- {const}')
            lines.append('')
        if module.classes:
            lines.append('Classes:')
            for cls in module.classes:
                summary = f': {cls.summary}' if cls.summary else ''
                lines.append(f'- {cls.signature}{summary}')
                for method in cls.methods:
                    method_summary = f': {method.summary}' if method.summary else ''
                    async_prefix = 'async ' if method.is_async else ''
                    lines.append(f'  - {async_prefix}{method.signature}{method_summary}')
            lines.append('')
        if module.functions:
            lines.append('Functions:')
            for func in module.functions:
                summary = f': {func.summary}' if func.summary else ''
                async_prefix = 'async ' if func.is_async else ''
                lines.append(f'- {async_prefix}{func.signature}{summary}')
            lines.append('')
    return lines


def _build_llms_content(config: LlmsConfig) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    generated_at = _format_generated_at(now)

    included_items: list[str] = []
    for section in config.doc_sections:
        for path in section.files:
            included_items.append(path.relative_to(REPO_ROOT).as_posix())
    for group in config.api_groups:
        included_items.append(f'api:{group.title}')

    lines: list[str] = [
        '---',
        'description: >',
        f'  {config.description}',
        '---',
        '',
        f'# {config.title}',
        '',
        '> NOTE',
        '> This file is generated automatically from the xmtp-py repository.',
        f'> Generated at: {generated_at}',
        '> Included Sections:',
    ]
    for item in included_items:
        lines.append(f'> - {item}')
    lines.append('')

    for section in config.doc_sections:
        lines.extend(_render_docs_section(section))
    for group in config.api_groups:
        lines.extend(_render_api_group(group))

    return _to_ascii('\n'.join(lines).strip() + '\n')


def _write_or_check(path: Path, content: str, check: bool) -> bool:
    if check:
        if not path.exists():
            print(f'Missing file: {path}', file=sys.stderr)
            return False
        existing = _read_text(path)
        if _normalize_for_check(existing) != _normalize_for_check(content):
            diff = difflib.unified_diff(
                _normalize_for_check(existing).splitlines(),
                _normalize_for_check(content).splitlines(),
                fromfile=str(path),
                tofile='generated',
                lineterm='',
            )
            print('\n'.join(diff), file=sys.stderr)
            return False
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return True


def _content_type_readmes() -> list[Path]:
    return sorted((REPO_ROOT / 'content-types').glob('*/README.md'))


def _content_type_src_roots() -> list[Path]:
    return sorted((REPO_ROOT / 'content-types').glob('*/src'))


def _build_configs() -> list[LlmsConfig]:
    readme = REPO_ROOT / 'README.md'
    python_sdk_readme = REPO_ROOT / 'sdks/python-sdk/README.md'
    agent_sdk_readme = REPO_ROOT / 'sdks/agent-sdk/README.md'
    bindings_readme = REPO_ROOT / 'bindings/python/README.md'

    docs_index = REPO_ROOT / 'docs/index.rst'
    docs_python = REPO_ROOT / 'docs/python_sdk.rst'
    docs_agent = REPO_ROOT / 'docs/agent_sdk.rst'
    docs_examples = REPO_ROOT / 'docs/examples.rst'
    docs_migration = REPO_ROOT / 'docs/migration_guide.rst'
    docs_contributing = REPO_ROOT / 'docs/contributing.rst'

    content_type_readmes = _content_type_readmes()

    python_api_roots = [REPO_ROOT / 'sdks/python-sdk/src']
    agent_api_roots = [REPO_ROOT / 'sdks/agent-sdk/src']
    content_api_roots = _content_type_src_roots()
    bindings_api_roots = [REPO_ROOT / 'bindings/python/src']

    chat_docs = [
        readme,
        python_sdk_readme,
        docs_python,
        docs_examples,
        *content_type_readmes,
    ]
    agent_docs = [
        readme,
        agent_sdk_readme,
        docs_agent,
        docs_examples,
        *content_type_readmes,
    ]
    full_docs = [
        readme,
        python_sdk_readme,
        agent_sdk_readme,
        docs_index,
        docs_python,
        docs_agent,
        docs_examples,
        docs_migration,
        docs_contributing,
        bindings_readme,
        *content_type_readmes,
    ]

    return [
        LlmsConfig(
            filename='llms-chat-apps.txt',
            title='xmtp-py LLM Reference (Chat Apps)',
            description='LLM reference for building chat apps with the xmtp-py Python SDK.',
            doc_sections=[DocSection('Chat App Documentation', chat_docs)],
            api_groups=[
                ApiGroup('Python SDK', python_api_roots),
                ApiGroup('Content Types', content_api_roots),
            ],
        ),
        LlmsConfig(
            filename='llms-agents.txt',
            title='xmtp-py LLM Reference (Agents)',
            description='LLM reference for building agents with the xmtp-py agent SDK.',
            doc_sections=[DocSection('Agent Documentation', agent_docs)],
            api_groups=[
                ApiGroup('Agent SDK', agent_api_roots),
                ApiGroup('Content Types', content_api_roots),
            ],
        ),
        LlmsConfig(
            filename='llms-full.txt',
            title='xmtp-py LLM Reference (Full)',
            description='Full LLM reference for the xmtp-py monorepo.',
            doc_sections=[DocSection('Repository Documentation', full_docs)],
            api_groups=[
                ApiGroup('Python SDK', python_api_roots),
                ApiGroup('Agent SDK', agent_api_roots),
                ApiGroup('Content Types', content_api_roots),
                ApiGroup('Bindings', bindings_api_roots),
            ],
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate llms/*.txt reference files.')
    parser.add_argument('--check', action='store_true', help='Fail if files are out of date.')
    args = parser.parse_args()

    ok = True
    for config in _build_configs():
        content = _build_llms_content(config)
        target = LLMS_DIR / config.filename
        if not _write_or_check(target, content, args.check):
            ok = False

    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
