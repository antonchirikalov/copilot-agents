#!/usr/bin/env python3
"""
Codebase Scanner — Scans a Python project and produces project_map.json
for use by the Project Documenter agent.

Usage:
    python3 codebase-scanner.py /path/to/project [--output project_map.json]

Extracts: structure, modules (classes, functions, decorators), imports,
routes, models, dependencies, configs, infrastructure.
"""

import ast
import json
import os
import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict


IGNORE_DIRS = {
    '__pycache__', '.git', '.svn', 'node_modules', '.tox', '.mypy_cache',
    '.pytest_cache', 'venv', '.venv', 'env', '.env', 'dist', 'build',
    '.eggs', '*.egg-info', '.idea', '.vscode', 'migrations',
}

IGNORE_FILES = {'.DS_Store', 'Thumbs.db'}

ROUTE_DECORATORS = {
    'route', 'get', 'post', 'put', 'delete', 'patch', 'head', 'options',
    'api_view', 'action',
}

MODEL_BASES = {
    'Model', 'Base', 'BaseModel', 'DeclarativeBase',
    'db.Model', 'SQLModel',
}

FRAMEWORK_INDICATORS = {
    'flask': ['Flask', 'Blueprint', 'flask'],
    'fastapi': ['FastAPI', 'APIRouter', 'fastapi'],
    'django': ['django', 'INSTALLED_APPS', 'urlpatterns'],
    'celery': ['Celery', 'celery_app', 'shared_task'],
    'sqlalchemy': ['SQLAlchemy', 'create_engine', 'Session', 'declarative_base'],
    'pydantic': ['BaseModel', 'Field', 'validator', 'pydantic'],
    'pytest': ['pytest', 'fixture', 'parametrize'],
}


def should_ignore_dir(dirname):
    if dirname.startswith('.'):
        return True
    for pattern in IGNORE_DIRS:
        if pattern.endswith('*'):
            if dirname.startswith(pattern[:-1]):
                return True
        elif dirname == pattern:
            return True
    return False


def scan_structure(root_path):
    structure = {}
    total_files = defaultdict(int)
    total_lines = defaultdict(int)

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]

        rel_dir = os.path.relpath(dirpath, root_path)
        if rel_dir == '.':
            rel_dir = ''

        files_info = []
        for f in sorted(filenames):
            if f in IGNORE_FILES:
                continue
            ext = Path(f).suffix
            total_files[ext] += 1
            filepath = os.path.join(dirpath, f)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
                    line_count = sum(1 for _ in fh)
                total_lines[ext] += line_count
                files_info.append({'name': f, 'lines': line_count})
            except (OSError, PermissionError):
                files_info.append({'name': f, 'lines': 0})

        if files_info or dirnames:
            structure[rel_dir if rel_dir else '.'] = {
                'files': files_info,
                'subdirs': sorted([d for d in dirnames if not should_ignore_dir(d)])
            }

    return structure, dict(total_files), dict(total_lines)


def parse_python_file(filepath, root_path):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
    except (OSError, PermissionError):
        return None

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return None

    rel_path = os.path.relpath(filepath, root_path)
    module_info = {
        'file': rel_path,
        'docstring': ast.get_docstring(tree) or '',
        'classes': [],
        'functions': [],
        'imports_internal': [],
        'imports_external': [],
    }

    project_name = os.path.basename(root_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_info = {
                'name': node.name,
                'bases': [],
                'methods': [],
                'decorators': [],
                'line': node.lineno,
            }
            for base in node.bases:
                if isinstance(base, ast.Name):
                    class_info['bases'].append(base.id)
                elif isinstance(base, ast.Attribute):
                    class_info['bases'].append(f"{_get_attr_name(base)}")

            for dec in node.decorator_list:
                class_info['decorators'].append(_get_decorator_name(dec))

            for item in node.body:
                if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                    method_info = {
                        'name': item.name,
                        'decorators': [_get_decorator_name(d) for d in item.decorator_list],
                        'args': [a.arg for a in item.args.args if a.arg != 'self'],
                    }
                    class_info['methods'].append(method_info)

            module_info['classes'].append(class_info)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_top_level(node, tree):
                func_info = {
                    'name': node.name,
                    'decorators': [_get_decorator_name(d) for d in node.decorator_list],
                    'args': [a.arg for a in node.args.args if a.arg != 'self'],
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'line': node.lineno,
                }
                if node.returns:
                    func_info['return_type'] = _get_annotation(node.returns)
                module_info['functions'].append(func_info)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                module_info['imports_external'].append(alias.name.split('.')[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_module = node.module.split('.')[0]
                src_parts = _get_project_packages(root_path)
                if root_module in src_parts or node.level > 0:
                    module_info['imports_internal'].append(node.module)
                else:
                    module_info['imports_external'].append(root_module)

    module_info['imports_external'] = sorted(set(module_info['imports_external']))
    module_info['imports_internal'] = sorted(set(module_info['imports_internal']))

    return module_info


def _is_top_level(node, tree):
    for top_node in ast.iter_child_nodes(tree):
        if top_node is node:
            return True
    return False


def _get_decorator_name(dec):
    if isinstance(dec, ast.Name):
        return dec.id
    elif isinstance(dec, ast.Attribute):
        return _get_attr_name(dec)
    elif isinstance(dec, ast.Call):
        return _get_decorator_name(dec.func)
    return 'unknown'


def _get_attr_name(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return '.'.join(reversed(parts))


def _get_annotation(node):
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return _get_attr_name(node)
    elif isinstance(node, ast.Constant):
        return str(node.value)
    elif isinstance(node, ast.Subscript):
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}[...]"
    return 'Any'


_project_packages_cache = {}

def _get_project_packages(root_path):
    if root_path in _project_packages_cache:
        return _project_packages_cache[root_path]
    packages = set()
    packages.add(os.path.basename(root_path))
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            init_file = os.path.join(item_path, '__init__.py')
            if os.path.exists(init_file):
                packages.add(item)
        if item == 'src' and os.path.isdir(item_path):
            for sub in os.listdir(item_path):
                if os.path.isdir(os.path.join(item_path, sub)):
                    packages.add(sub)
    _project_packages_cache[root_path] = packages
    return packages


def extract_routes(modules):
    routes = []
    for mod in modules:
        for func in mod.get('functions', []):
            for dec in func.get('decorators', []):
                dec_lower = dec.lower().split('.')[-1]
                if dec_lower in ROUTE_DECORATORS:
                    routes.append({
                        'method': dec_lower.upper() if dec_lower != 'route' else 'ANY',
                        'decorator': dec,
                        'function': func['name'],
                        'file': mod['file'],
                        'line': func.get('line', 0),
                    })
        for cls in mod.get('classes', []):
            for method in cls.get('methods', []):
                for dec in method.get('decorators', []):
                    dec_lower = dec.lower().split('.')[-1]
                    if dec_lower in ROUTE_DECORATORS:
                        routes.append({
                            'method': dec_lower.upper() if dec_lower != 'route' else 'ANY',
                            'decorator': dec,
                            'function': f"{cls['name']}.{method['name']}",
                            'file': mod['file'],
                        })
    return routes


def extract_models(modules):
    models = []
    for mod in modules:
        for cls in mod.get('classes', []):
            is_model = False
            for base in cls.get('bases', []):
                base_simple = base.split('.')[-1]
                if base_simple in MODEL_BASES:
                    is_model = True
                    break
                if 'Model' in base_simple or 'Schema' in base_simple:
                    is_model = True
                    break

            if is_model:
                fields = []
                for method in cls.get('methods', []):
                    if method['name'] == '__init__':
                        fields = method.get('args', [])
                        break

                models.append({
                    'name': cls['name'],
                    'bases': cls['bases'],
                    'fields': fields,
                    'methods': [m['name'] for m in cls.get('methods', []) if not m['name'].startswith('_')],
                    'file': mod['file'],
                })
    return models


def parse_requirements(root_path):
    deps = []

    req_file = os.path.join(root_path, 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                    if match:
                        deps.append({'name': match.group(1), 'spec': line, 'source': 'requirements.txt'})

    pyproject = os.path.join(root_path, 'pyproject.toml')
    if os.path.exists(pyproject):
        try:
            with open(pyproject, 'r', encoding='utf-8') as f:
                content = f.read()
            in_deps = False
            for line in content.split('\n'):
                if 'dependencies' in line and '=' in line:
                    in_deps = True
                    continue
                if in_deps:
                    if line.strip().startswith(']'):
                        in_deps = False
                        continue
                    match = re.match(r'^\s*"([a-zA-Z0-9_-]+)', line)
                    if match:
                        deps.append({'name': match.group(1), 'spec': line.strip().strip('",'), 'source': 'pyproject.toml'})
        except Exception:
            pass

    setup_py = os.path.join(root_path, 'setup.py')
    if os.path.exists(setup_py):
        try:
            with open(setup_py, 'r', encoding='utf-8') as f:
                content = f.read()
            matches = re.findall(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if matches:
                for m in re.findall(r"['\"]([a-zA-Z0-9_-]+)", matches[0]):
                    deps.append({'name': m, 'source': 'setup.py'})
        except Exception:
            pass

    return deps


def scan_configs(root_path):
    configs = {}

    env_file = os.path.join(root_path, '.env.example')
    if not os.path.exists(env_file):
        env_file = os.path.join(root_path, '.env.sample')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            vars_list = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key = line.split('=')[0].strip()
                    vars_list.append(key)
            configs['env_variables'] = vars_list

    dc_file = os.path.join(root_path, 'docker-compose.yml')
    if not os.path.exists(dc_file):
        dc_file = os.path.join(root_path, 'docker-compose.yaml')
    if os.path.exists(dc_file):
        try:
            with open(dc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            services = re.findall(r'^\s{2}(\w[\w-]*):', content, re.MULTILINE)
            configs['docker_compose_services'] = services
        except Exception:
            pass

    dockerfile = os.path.join(root_path, 'Dockerfile')
    if os.path.exists(dockerfile):
        with open(dockerfile, 'r', encoding='utf-8') as f:
            content = f.read()
        base_images = re.findall(r'^FROM\s+(\S+)', content, re.MULTILINE)
        expose_ports = re.findall(r'^EXPOSE\s+(\d+)', content, re.MULTILINE)
        configs['dockerfile'] = {
            'base_images': base_images,
            'exposed_ports': expose_ports,
        }

    return configs


def scan_infrastructure(root_path):
    infra = {}

    tf_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]
        for f in filenames:
            if f.endswith('.tf'):
                filepath = os.path.join(dirpath, f)
                rel = os.path.relpath(filepath, root_path)
                try:
                    with open(filepath, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    resources = re.findall(r'resource\s+"([^"]+)"\s+"([^"]+)"', content)
                    tf_files.append({
                        'file': rel,
                        'resources': [{'type': r[0], 'name': r[1]} for r in resources],
                    })
                except Exception:
                    pass
    if tf_files:
        infra['terraform'] = tf_files

    ci_paths = [
        ('.github/workflows', 'github_actions'),
        ('.gitlab-ci.yml', 'gitlab_ci'),
        ('Jenkinsfile', 'jenkins'),
    ]
    for path, key in ci_paths:
        full_path = os.path.join(root_path, path)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                files = [f for f in os.listdir(full_path) if f.endswith(('.yml', '.yaml'))]
                infra[key] = files
            else:
                infra[key] = True

    return infra


def detect_frameworks(modules, deps):
    detected = set()
    all_imports = set()
    for mod in modules:
        all_imports.update(mod.get('imports_external', []))

    dep_names = {d['name'].lower().replace('-', '_') for d in deps}

    for framework, indicators in FRAMEWORK_INDICATORS.items():
        for indicator in indicators:
            if indicator.lower().replace('-', '_') in dep_names:
                detected.add(framework)
                break
            if indicator in all_imports:
                detected.add(framework)
                break

    return sorted(detected)


def main():
    parser = argparse.ArgumentParser(description='Scan Python codebase and generate project_map.json')
    parser.add_argument('project_path', help='Path to the project root directory')
    parser.add_argument('--output', '-o', default=None, help='Output file path (default: project_map.json in project dir)')
    args = parser.parse_args()

    root_path = os.path.abspath(args.project_path)
    if not os.path.isdir(root_path):
        print(f"Error: {root_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning: {root_path}")

    structure, total_files, total_lines = scan_structure(root_path)
    print(f"  Structure: {sum(total_files.values())} files")

    modules = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]
        for f in filenames:
            if f.endswith('.py'):
                filepath = os.path.join(dirpath, f)
                mod = parse_python_file(filepath, root_path)
                if mod:
                    modules.append(mod)
    print(f"  Modules: {len(modules)} Python files parsed")

    routes = extract_routes(modules)
    print(f"  Routes: {len(routes)} endpoints found")

    models = extract_models(modules)
    print(f"  Models: {len(models)} data models found")

    deps = parse_requirements(root_path)
    print(f"  Dependencies: {len(deps)} packages")

    configs = scan_configs(root_path)
    infra = scan_infrastructure(root_path)
    frameworks = detect_frameworks(modules, deps)
    print(f"  Frameworks: {', '.join(frameworks) if frameworks else 'none detected'}")

    project_map = {
        'project_info': {
            'name': os.path.basename(root_path),
            'root_path': root_path,
            'total_files': total_files,
            'total_lines': total_lines,
            'detected_frameworks': frameworks,
        },
        'structure': structure,
        'modules': modules,
        'routes': routes,
        'models': models,
        'dependencies': deps,
        'configs': configs,
        'infrastructure': infra,
    }

    output_path = args.output or os.path.join(root_path, 'project_map.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(project_map, f, indent=2, ensure_ascii=False)

    print(f"\nOutput: {output_path}")
    print(f"Summary: {len(modules)} modules, {len(routes)} routes, {len(models)} models, {len(deps)} deps")


if __name__ == '__main__':
    main()
