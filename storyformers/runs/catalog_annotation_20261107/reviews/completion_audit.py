"""Final completion gate; pending stories or a missing prompt revision fail it."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN))
from review_run import review
from source_catalog_audit import main as audit_source


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    progress = review()
    audit_source()
    source = read(RUN / 'reviews/source_catalog_audit.json')
    manifest = read(RUN / 'manifest.json')
    checks = {
        'twenty_complete_and_valid': progress['completed_stories'] == progress['valid_stories'] == 20,
        'all_source_words': progress['total_words'] == 15326,
        'no_structural_errors': not progress['errors'],
        'no_extension_conflicts': not progress['extension_definition_conflicts'],
        'exact_source_and_full_catalog': source['result'] == 'pass',
        'twenty_reviewed': len(manifest['stories']) == 20 and all(
            s['status'] == 'reviewed' and (RUN / s.get('review', '__missing__')).is_file()
            and all((RUN / extra).is_file() for extra in s.get('additional_reviews', []))
            for s in manifest['stories']),
        'all_phase_reviews': all(manifest['phases'][phase]['status'] == 'reviewed'
            and (RUN / manifest['phases'][phase]['review']).is_file()
            for phase in ('pilot', 'batch_1', 'batch_2', 'batch_3')),
        'final_revision_present': manifest.get('current_prompt_version') == 'v4'
            and all((RUN / 'prompts' / name).is_file() for name in
                    ('annotate_v4.md', 'batch3_examples_v4.json', 'extension_registry_v4.json')),
    }
    example_errors = []
    example_count = 0
    snapshot_file = RUN / 'reviews/annotation_snapshots.json'
    snapshots = read(snapshot_file) if snapshot_file.exists() else []
    archived_example_count = 0
    for path in sorted((RUN / 'prompts').glob('*examples_v*.json')):
        for example in read(path)['examples']:
            folder = RUN / 'annotations' / example['story_id']
            expected = example.get('annotation_sha256', example.get('annotations_sha256'))
            if expected != sha(folder / 'annotations.jsonl'):
                snapshot = next((s for s in snapshots if s['story_id'] == example['story_id']
                                 and s['annotation_sha256'] == expected), None)
                if snapshot:
                    folder = RUN / snapshot['snapshot']
                    archived_example_count += 1
            if expected != sha(folder / 'annotations.jsonl'):
                example_errors.append(f'{path.name}: {example["title"]}: annotation hash')
            words = {r['word_index']: r for r in map(json.loads,
                     (folder / 'annotations.jsonl').read_text().splitlines()) if r['kind'] == 'word'}
            for record in example['records']:
                if any(words[record['word_index']].get(k) != v for k, v in record.items()):
                    example_errors.append(f'{path.name}: {example["title"]}: record {record["word_index"]}')
            for table, records in example.get('references', example.get('referenced_tables', {})).items():
                full = read(folder / f'{table}.json')
                # Pilot excerpts omit long mention/word lists; verify every
                # included field without requiring those deliberate omissions.
                if any(key not in full or any(full[key].get(k) != v for k, v in value.items())
                       for key, value in records.items()):
                    example_errors.append(f'{path.name}: {example["title"]}: {table}')
            example_count += 1
    checks['examples_match_reviewed_annotations'] = not example_errors and example_count == 25
    registry = read(RUN / 'prompts/extension_registry_v4.json')
    checks['seven_unique_reviewed_extensions'] = len(registry) == len({d['key'] for d in registry}) == 7
    bundle_errors = []
    for entry in map(json.loads, (RUN / 'reviews/phase_log.jsonl').read_text().splitlines()):
        for name, expected in entry.get('bundle_sha256', {}).items():
            if sha(RUN / 'prompts' / name) != expected:
                bundle_errors.append(name)
    checks['logged_bundles_unchanged'] = not bundle_errors
    report = dict(result='pass' if all(checks.values()) else 'incomplete_or_mismatch',
                  audited_at_utc=datetime.now(timezone.utc).isoformat(), checks=checks,
                  stories=progress['valid_stories'], words=progress['total_words'],
                  examples=example_count, archived_examples=archived_example_count,
                  example_errors=example_errors, bundle_errors=bundle_errors,
                  limitation='Completion, provenance and structural checks; semantic acceptance is documented separately in story and batch reviews.')
    (RUN / 'reviews/completion_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['result'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
