"""Reproducible continuation comparison using intact annotated examples."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from .event_line_replay import paper_world
from .memory_continuation import continue_story
from .story_memory_export import demonstration_world
from .storytelling.runtime import SCENARIOS
from .story_memory import load_documents, memory_files


def run(memory, out, count=20):
    if count < 1:
        raise ValueError('positive sample count required')
    memory_paths = memory_files(memory)
    docs = load_documents(memory)
    out.mkdir(parents=True, exist_ok=False)
    intent = dict(op='intent', actor='ada', item='book')
    goal = dict(entity='book', field='state', value='repaired')
    cases = [
        ('plain', paper_world, [intent], None, 'plain', count),
        ('contextual', paper_world, [intent], None, 'contextual', count),
        ('dialogue_prefix', paper_world, [intent, dict(op='offer', actor='omar', listener='ada')], None, 'contextual', 5),
        ('ending_predicate', paper_world, [intent], [goal, dict(entity='book', field='location', value='bench')], 'contextual', 5),
        ('no_prefix', paper_world, [], [], 'contextual', 5),
        ('craft_no_plan', demonstration_world, [], [], 'contextual', 5)]
    summaries, samples = {}, []
    with gzip.open(out / 'traces.jsonl.gz', 'wt') as stream:
        for name, factory, prefix, goals, policy, n in cases:
            rows = []
            for seed in range(n):
                row = continue_story(docs, factory(), prefix=prefix, goals=goals, policy=policy, seed=seed)
                row['experiment'] = name
                stream.write(json.dumps(row, separators=(',', ':')) + '\n')
                rows.append(row)
            selected = [[d['candidates'][d['selected']]['event'] for d in r['decisions']
                         if d['candidates'][d['selected']]['event']['op'] != 'STOP'] for r in rows]
            summaries[name] = dict(samples=n,
                repaired=sum('repaired' in r['final_world']['entities']['book']['state'] for r in rows),
                all_goals_met=sum(bool(r['goals']) and all(r['goals_satisfied']) for r in rows),
                status=dict(Counter(r['status'] for r in rows)),
                mean_sampled_events=sum(map(len, selected))/n,
                repeated_actions=sum(len(es)-len({json.dumps(e,sort_keys=True) for e in es}) for es in selected),
                unique_event_chains=len({json.dumps(es,sort_keys=True) for es in selected}),
                source_worlds=sorted({ref['scenario'] for r in rows for d in r['decisions']
                    for ref in d['candidates'][d['selected']].get('references', [])}))
            for row, events in zip(rows, selected):
                samples.append(dict(experiment=name, seed=row['seed'], story=row['story'],
                    status=row['status'], goals_satisfied=row['goals_satisfied'], events=events))
            print(name, json.dumps(summaries[name]), flush=True)
    (out / 'summary.json').write_text(json.dumps(summaries, indent=2)+'\n')
    (out / 'samples.json').write_text(json.dumps(samples, indent=2)+'\n')
    lines = ['# Sampled continuation from intact story memory', '',
        f'Memory: {len(docs)} intact annotated source samples from {len({d["scenario"] for d in docs})} worlds. '
        'This uses the current mapping bank; many compound source event kinds remain unsupported for portable execution. '
        'Sources are references into whole stories, not detached prose snippets.', '',
        'The receiver is the explicit paper-repair fixture: Ada holds a torn paper book, '
        'tape is on the bench, and Ada/Omar have paper-repair ability. No missing entities or capabilities are imported.', '',
        'The main comparison supplies one repair-intent event. Its repaired-state goal is inferred by a small explicit intent rule. '
        'Every later action, binding and STOP is sampled; no fetch/repair/return sequence is supplied. '
        'Plain sampling uses mapping weights. Contextual sampling adds manual state-progress, goal-progress, '
        'one-step goal-enabling, actor-continuity and repetition factors. Words and attributes are then sampled conditionally.', '',
        '| Experiment | N | Book repaired | Sampled stop | Event limit | Mean events after prefix | Repeated actions | Distinct chains |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name, s in summaries.items():
        lines.append(f"| {name} | {s['samples']} | {s['repaired']} | {s['status'].get('sampled_stop',0)} | {s['status'].get('limit',0)} | {s['mean_sampled_events']:.2f} | {s['repeated_actions']} | {s['unique_event_chains']} |")
    lines += ['', 'Repeated actions count exact target operation/argument repeats within each continuation. '
        'Distinct chains omit STOP and wording. These are mechanical measures, not Luna ratings.', '',
        'The ending-predicate variant additionally asks for the repaired book to be on the bench. '
        'This is a supplied final-state condition, not an inferred literary ending. The dialogue-prefix variant adds Omar offering help. '
        'No-prefix variants have no goals. Craft has explicitly declared clay, drum, ladder, broken tap and drawing materials/abilities.', '',
        '## Samples and latent event streams', '']
    for s in samples:
        lines += [f"### {s['experiment']}, seed {s['seed']}", '', s['story'] or '(no prose)', '',
            '`'+' → '.join(e['op']+'('+', '.join(f'{k}={v}' for k,v in e.items() if k!='op')+')' for e in s['events'])+'`', '',
            f"Stop: {s['status']}; goal predicates: {s['goals_satisfied']}.", '']
    lines += ['## Interpretation and limitations', '',
        'The loop can make physical progress without an authored suffix. A source-compatible event is still only a candidate: '
        'all target guards are checked on the current world after every commit. All selected segments are independently replay-verified.', '',
        'The policy can still stop early, wander, or hit the cap. A sampled stop is not a solved-world flag. '
        'Short successful repairs remain miniature action sequences: thin premise, little emotional development, '
        'and usually no concluding image unless a final-state condition is supplied. '
        'Unconstrained craft samples may jump between unrelated activities. No prose-quality improvement is claimed from success rates alone.', '',
        'Attention factors are hand-authored state/history features, not learned heads or corpus trigram statistics. '
        'There is no automatic missing-entity import, broad intention understanding, multi-step planning or source-order continuation prior. '
        'The one-step lookahead asks only whether a proposed move enables a directly goal-satisfying next event. '
        'All event probabilities, factors, source references, word distributions and token attributes are in traces.jsonl.gz.', '']
    (out / 'report.md').write_text('\n'.join(lines))
    root = Path(__file__).resolve().parents[1]
    paths = [Path(__file__), Path(__file__).with_name('memory_continuation.py'),
             Path(__file__).with_name('story_memory.py'), Path(__file__).with_name('event_mapping.py'),
             Path(__file__).with_name('reusable_operations.py'), Path(__file__).with_name('event_line_replay.py')]
    paths += list(Path(__file__).with_name('mapping_bank').glob('*.json'))
    paths += memory_paths
    (out / 'manifest.json').write_text(json.dumps({str(p.resolve().relative_to(root)):
        hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, indent=2)+'\n')
    return summaries


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--memory', type=Path, default=Path('grammarworlds/runs/seed_worlds_20261107_v4'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--count', type=int, default=20)
    args = parser.parse_args()
    run(args.memory, args.out, args.count)
