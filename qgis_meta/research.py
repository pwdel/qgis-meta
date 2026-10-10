"""Unpublished evidence queues: activity traces never establish access permission."""
import json
from pathlib import Path

def validate_research(record):
    from jsonschema import Draft202012Validator,FormatChecker
    schema=json.loads((Path(__file__).parent/'contracts/research-review.schema.json').read_text())
    errors=[f'{list(e.path)}: {e.message}' for e in Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(record)]
    if errors:return errors
    seen=set()
    for c in record['candidates']:
        prefix=c['id']
        if prefix in seen:errors.append(f'{prefix}: duplicate candidate ID')
        seen.add(prefix)
        evidence={e['id']:e for e in c['evidence']}
        if len(evidence)!=len(c['evidence']):errors.append(f'{prefix}: duplicate evidence ID')
        for claim in c['claims']:
            refs=[evidence.get(i) for i in claim['evidence_ids']]
            if any(e is None for e in refs):errors.append(f'{prefix}: missing evidence reference')
            if claim['status']!='unknown' and not any(e and e['kind']=='authority' and claim['activity'] in e['supports'] for e in refs):
                errors.append(f'{prefix}: {claim["activity"]} permission needs activity-specific authority evidence; traces/observations are insufficient')
        if c['stage']=='promoted' and (not c['review'] or c['jurisdiction']=='unknown' or not c['location']):
            errors.append(f'{prefix}: promotion needs reviewed decision, jurisdiction and location')
        if c['stage']=='promoted' and any(x['status']=='unknown' for x in c['claims']):
            errors.append(f'{prefix}: split unresolved claims before promotion')
    return errors

def check_research_publication(layout, layers, errors):
    if layout.customProperty('qgis_meta/layout_purpose','publication')!='research':
        for layer in layers:
            if layer.customProperty('qgis_meta/research_only',False):
                errors.append(f'{layout.name()}: research-only layer {layer.id()} cannot appear in a publication layout')
