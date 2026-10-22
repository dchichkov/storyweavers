#!/usr/bin/env python3
"""Sample conversational QA from saved pinned stories, without authoring/API calls."""
import argparse
import hashlib
import json
from pathlib import Path

from conversation import Conversation, VERSION
from qa import enrich
from qa_checks import measure


def sample(runs, out):
    out.mkdir(parents=True, exist_ok=True)
    rows = []; failures = []; coverage = []
    for run in runs:
        for source in sorted(run.glob('*/samples_with_trace.json')):
            for index, original in enumerate(json.loads(source.read_text())):
                try:
                    row = enrich(original)
                    row['qa_source'] = dict(file=str(source), index=index, seed=original['seed'])
                    rows.append(row)
                    dialog = Conversation(original['trace'], original.get('paragraphs'))
                    coverage.append(dict(source=row['qa_source'],
                        described_events=sum(dialog.event_description(e) is not None for e in dialog.events),
                        total_events=len(dialog.events), attributed_utterances=len(dialog.dialogue),
                        conversations=len(row['conversations'])))
                except Exception as exc:
                    failures.append(dict(source=str(source), index=index, error=str(exc)))
    with (out/'samples.jsonl').open('w') as stream:
        for row in rows: stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    report = measure(rows)
    report.update(protocol=VERSION, source_runs=list(map(str,runs)), failures=failures,
                  coverage=coverage, api_requests=0, api_cost_usd=0,
                  source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                 for name in ('conversation.py','dialogue.py','qa.py','qa_checks.py','qa_trial.py')})
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    with (out/'samples.md').open('w') as stream:
        for row in rows:
            stream.write(f'## {row["qa_source"]["file"]} — seed {row["seed"]}\n\n{row["story"]}\n\n')
            for conversation in row['conversations']:
                for turn in conversation['turns']:
                    stream.write(f'**Q:** {turn["question"]}\n\n**A:** {turn["answer"]}\n\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, action='append', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if any(not path.is_dir() for path in args.run): parser.error('Every run must exist')
    report = sample(args.run,args.out)
    print(json.dumps({k:v for k,v in report.items() if k not in ('coverage','source_sha256')},indent=2))
    raise SystemExit(int(bool(report['defects'] or report['failures']) or not report['conversations']))
