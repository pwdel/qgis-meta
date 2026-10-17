"""Command-line entry point; no shell interpolation of paths or test arguments."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from .engine import validate


def main(argv=None):
    parser = argparse.ArgumentParser(prog='qgis-meta')
    commands = parser.add_subparsers(dest='command', required=True)
    qr = commands.add_parser('qr-location', help='Generate an offline location QR image and JSON record (no QGIS required)')
    qr.add_argument('--latitude', type=float, required=True)
    qr.add_argument('--longitude', type=float, required=True)
    qr.add_argument('--output', type=Path, required=True, help='PNG or SVG output path; parent directory must exist')
    qr.add_argument('--format', choices=['geo', 'maps'], default='geo', help='RFC 5870 geo URI or HTTPS Google Maps search link')
    qr.add_argument('--force', action='store_true', help='Replace existing image and JSON record')
    research = commands.add_parser('research-check', help='Validate an unpublished research review JSON')
    research.add_argument('target',type=Path)
    command = commands.add_parser('validate', help='Validate a repository, project, native registry, or qgis-checks.json')
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
    if args.command == 'qr-location':
        from .location_qr import generate_location_qr
        try:
            result = generate_location_qr(args.latitude, args.longitude, args.output, args.format, args.force)
        except (ValueError, OSError) as exc:
            parser.error(str(exc))
        print(f'Created {args.output}: {result["payload"]}')
        return 0
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
    print(f'{report["status"].upper()}: {len(report["projects"])} project check group(s); scope={report["scope"]}')
    for project in report['projects']:
        print(project['project_id'] or project['registry'])
        for check in project['checks']:
            print(f'  {check["status"].upper():7} {check["id"]}: {check["message"]}')
    for check in report['checks']:
        print(f'{check["status"].upper():7} {check["id"]}: {check["message"]}')
    print(f'Report: {output / "report.json"}')
    return report['exit_code']
