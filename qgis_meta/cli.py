"""Command-line entry point; no shell interpolation of paths or test arguments."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from .engine import validate


def main(argv=None):
    parser = argparse.ArgumentParser(prog='qgis-meta')
    commands = parser.add_subparsers(dest='command', required=True)
    research = commands.add_parser('research-check', help='Validate an unpublished research review JSON')
    research.add_argument('target',type=Path)
    command = commands.add_parser('validate', help='Validate a repository, project, or registry')
    command.add_argument('target', type=Path)
    command.add_argument('--mode', choices=['static', 'full'], default='full')
    command.add_argument('--output', type=Path)
    command.add_argument('--governance-root', type=Path, help='Pinned qgis-meta checkout (required for a non-editable installation)')
    runtime = command.add_mutually_exclusive_group()
    runtime.add_argument('--qgis-python', help='Interpreter from a configured QGIS environment')
    runtime.add_argument('--qgis-app', help='macOS QGIS .app bundle')
    command.add_argument('--timeout', type=int, default=120)
    command.add_argument('--run-project-tests', action='store_true', help='Execute trusted project Python tests')
    args = parser.parse_args(argv)
    if not args.target.exists():
        parser.error('Target does not exist')
    if args.command=='research-check':
        import json
        from .research import validate_research
        errors=validate_research(json.loads(args.target.read_text()))
        print('\n'.join(errors) if errors else 'PASS: research evidence and promotion rules')
        return 1 if errors else 0
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    base = args.target.parent if args.target.is_file() else args.target
    output = args.output or base / 'reports' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    report = validate(args.target, mode=args.mode, output=output, qgis_python=args.qgis_python,
                      qgis_app=args.qgis_app, timeout=args.timeout, run_project_tests=args.run_project_tests, governance_root=args.governance_root)
    print(f'{report["status"].upper()}: {len(report["projects"])} registered project(s)')
    for project in report['projects']:
        print(project['project_id'] or project['registry'])
        for check in project['checks']:
            print(f'  {check["status"].upper():7} {check["id"]}: {check["message"]}')
    for check in report['checks']:
        print(f'{check["status"].upper():7} {check["id"]}: {check["message"]}')
    print(f'Report: {output / "report.json"}')
    return report['exit_code']
