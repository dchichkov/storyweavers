"""Freeze each improvement round, its unfiltered samples, tests and Luna results."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from .. import judge
from .runtime import SCENARIOS, generate, replay
from .qa import questions
from .evaluate import prepare, report

ROOT = judge.ROOT
CAMPAIGN = ROOT / 'grammarworlds/runs/ten_rounds_20261103'


def freeze(number, change, scenarios, count=10, start=0, label='development'):
    directory = CAMPAIGN / f'round{number:02d}'
    directory.mkdir(parents=True, exist_ok=False)
    judge.save(directory / 'change.json', dict(round=number, change=change, scenarios=scenarios,
        judge_count=count, seed_start=start, label=label,
        architecture='weighted typed grammar + guarded symbolic kernels + carrier-grounded attention'))
    samples, qa_count, multisent = [], 0, 0
    source = directory / 'stories_qa.jsonl'
    with source.open('w') as sink:
        for scenario in scenarios:
            for tense in ('past', 'present'):
                for seed in range(start, start + 60):
                    row = generate(scenario, seed, tense=tense)
                    replay(row)
                    qa = questions(row)
                    assert len(qa) >= 5 and len({q['question'] for q in qa}) == len(qa)
                    assert len({q['kind'] for q in qa}) >= 3
                    assert len({p for s in row['scenes'] for p in s['speakers']}) >= 2
                    assert all(q['answer'].endswith('.') for q in qa)
                    assert all(row['story'][e['start']:e['end']] == e['text'] for q in qa for e in q['evidence'])
                    qa_count += len(qa)
                    multisent += sum(q['answer'].count('.') >= 2 for q in qa)
                    compact = {k: row[k] for k in ('scenario','seed','tense','story','text_sha256','scenes')}
                    compact.update(qa=qa, final_state=row['final_world'],
                                   frames=[e['frame'] for e in row['final_world']['history']])
                    sink.write(json.dumps(compact)+'\n')
                    if seed in (start, start+7) and tense == 'past': samples.append(compact)
            print(scenario, '120 samples replayed', flush=True)
    check = subprocess.run([sys.executable, '-m', 'grammarworlds', '--verify'], cwd=ROOT,
                           capture_output=True, text=True)
    (directory/'tests.txt').write_text(check.stdout+check.stderr)
    judge.save(directory/'checks.json',dict(stories=len(scenarios)*120, qa_pairs=qa_count,
        multis_sentence_answers=multisent, tests_returncode=check.returncode))
    if check.returncode:
        raise RuntimeError('Tests failed; inspect before requesting evaluation')
    lines=['# Inspected development samples','']
    for row in samples:
        lines += [f"## {row['scenario']} / seed {row['seed']}", '', row['story'], '']
        for q in row['qa']:
            lines += [f"Q: {q['question']}", f"A: {q['answer']}", '']
    (directory/'samples.md').write_text('\n'.join(lines))
    prepare(directory/'eval',source=source,count=count,scenarios=scenarios)
    print(directory/'eval', flush=True)


def record(number):
    directory=CAMPAIGN/f'round{number:02d}'
    q=report(directory/'eval')
    p=judge.read(directory/'eval/summary.json')
    checks=judge.read(directory/'checks.json')
    if not q['complete'] or checks['tests_returncode']:
        raise ValueError('Cannot mark an incomplete round measured')
    judge.save(directory/'measured.json', dict(round=number,
        quality=p['mean_quality'],diversity=p['mean_within_scenario_diversity'],
        qa=q['means'],defects=q['defects'],checks=checks))
    rows=[]
    for d in sorted(CAMPAIGN.glob('round[0-9][0-9]')):
        if (d/'measured.json').exists():
            m=judge.read(d/'measured.json'); c=judge.read(d/'change.json')
            rows.append((d,m,c))
    lines=['# Ten-round improvement ledger','',
        'Development subsets differ by round. Do not interpret these means as a single matched trend. '
        'Final all-world matched and held-out comparisons are required. Each linked run keeps frozen source, prose, QA, requests and responses.', '',
        '| Round | Worlds | Change | Quality /9 | Diversity /9 | QA /9 |',
        '| --- | --- | --- | ---: | ---: | ---: |']
    for d,m,c in rows:
        lines.append(f"| [{m['round']}]({d.name}/eval/REPORT.md) | {', '.join(c['scenarios'])} | {c['change']} | "
                     f"{m['quality']['overall']:.2f} | {m['diversity']['overall']:.2f} | {m['qa']['overall']:.2f} |")
    lines += ['',f'{len(rows)}/10 rounds measured. A measured round is not a claim that its score increased.','']
    (CAMPAIGN/'REPORT.md').write_text('\n'.join(lines))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=['freeze','record']);p.add_argument('round',type=int)
    p.add_argument('--change');p.add_argument('--scenarios',nargs='+',choices=SCENARIOS,default=list(SCENARIOS))
    p.add_argument('--count',type=int,default=10);p.add_argument('--start',type=int,default=0)
    args=p.parse_args()
    if not 1 <= args.round <= 10: p.error('round must be 1–10')
    if args.phase=='freeze':
        if not args.change:p.error('--change is required')
        freeze(args.round,args.change,args.scenarios,args.count,args.start)
    else: record(args.round)

if __name__=='__main__':main()
