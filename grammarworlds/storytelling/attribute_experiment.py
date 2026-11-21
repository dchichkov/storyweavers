"""Reproducible seven-world attribute export and matched surface-sampler check."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path

from .runtime import SCENARIOS, generate, replay, setup
from .qa import questions


def check_joint(row):
    ambiguous = changed = 0
    for event in row['trace']:
        for p in event['word_trace']:
            joint = defaultdict(float)
            for c in p['annotated_choices']:
                assert c['attributes'] in event['attribute_table']
                joint[c['word']] += c['probability']
            assert math.isclose(sum(joint.values()), 1., abs_tol=1e-9)
            for c in p['choices']:
                assert math.isclose(c['probability'], joint[c['word']], abs_tol=1e-9)
            assert math.isclose(sum(c['probability'] for c in p['selected_attributes']), 1., abs_tol=1e-9)
            ambiguous += len(p['selected_attributes']) > 1
            changed += p.get('head_total_variation', 0) > 1e-10
    return ambiguous, changed


def readable_tokens(row):
    return dict(story=row['story'], scenario=row['scenario'], seed=row['seed'],
        tokens=[{**token, 'candidates': [dict(probability=c['probability'],
                **row['trace'][token['scene_index']]['attribute_table'][c['attributes']])
                for c in token['candidates']]} for token in row['attribute_generation']['tokens']])


def run(out, seeds=10):
    out.mkdir(parents=True, exist_ok=True)
    results = []
    samples = {}
    candidate_kinds = defaultdict(set)
    for scenario in SCENARIOS:
        stats = Counter()
        pack, _ = setup(scenario, 7)
        for mode in ('original', 'expanded'):
            for seed in range(seeds):
                row = generate(scenario, seed, continuations=mode)
                old = generate(scenario, seed, continuations=mode, predict_attributes=False)
                assert row['story'] == old['story'] and row['final_world'] == old['final_world']
                assert questions(row) == questions(old)
                for event, old_event in zip(row['trace'], old['trace']):
                    for p, old_p in zip(event['word_trace'], old_event['word_trace']):
                        mass = {c['word']: c['probability'] for c in old_p['choices']}
                        assert set(mass) == {c['word'] for c in p['choices']}
                        assert all(math.isclose(c['probability'], mass[c['word']], abs_tol=1e-10) for c in p['choices'])
                    candidate_kinds[scenario].update(e['frame']['kind'] for e in event['event_evidence'].values())
                stats['paired_unchanged'] += 1
                stats['ambiguous_selected_steps'] += check_joint(row)[0]
                head = generate(scenario, seed, continuations=mode, symbolic_heads=True)
                assert replay(head)
                assert len(questions(head)) >= 5
                stats['head_runs'] += 1
                stats['head_changed_steps'] += check_joint(head)[1]
                stats['head_vs_no_head_text_changed'] += head['story'] != row['story']
        row = generate(scenario, 7)
        samples[scenario] = row
        (out/f'{scenario}.tokens.json').write_text(json.dumps(readable_tokens(row), indent=2)+'\n')
        with gzip.GzipFile(filename=str(out/f'{scenario}.trace.json.gz'), mode='wb', mtime=0) as file:
            file.write((json.dumps(row, separators=(',', ':'))+'\n').encode())
        results.append(dict(scenario=scenario, **stats,
                            candidate_kernels_seen=len(candidate_kinds[scenario]),
                            kernel_count=len(pack.KERNELS),
                            missing_candidate_kernels=sorted(set(pack.KERNELS)-candidate_kinds[scenario])))
        print(json.dumps(results[-1]), flush=True)
    summary = dict(seeds=seeds, results=results,
        paired_unchanged=sum(r['paired_unchanged'] for r in results),
        head_runs=sum(r['head_runs'] for r in results),
        head_changed_steps=sum(r['head_changed_steps'] for r in results))
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    source_paths = [Path(__file__), *[Path(__file__).with_name(name) for name in
        ('runtime.py', 'surface.py', 'semantic_rules.py', 'attribute_grammar.py', 'attribute_sampler.py',
         'head_adapter.py', 'continuations.py')], Path(__file__).parents[1]/'grammar.py']
    (out/'sources.json').write_text(json.dumps({str(p.relative_to(Path(__file__).parents[2])):
        hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}, indent=2)+'\n')
    lines = ['# Joint annotated-token generation', '',
             f"{summary['paired_unchanged']} matched runs preserve text, physical state, QA and word probabilities with heads off.",
             f"{summary['head_runs']} runs with heads replay successfully; heads changed {summary['head_changed_steps']} word distributions.",
             'These are correctness and preservation checks, not a new independent quality evaluation.', '',
             '| World | Matched runs | Ambiguous selected steps | Head-changed steps | Candidate kernels seen |',
             '|---|---:|---:|---:|---:|']
    for r in results:
        lines.append(f"| {r['scenario']} | {r['paired_unchanged']} | {r['ambiguous_selected_steps']} | {r['head_changed_steps']} | {r['candidate_kernels_seen']}/{r['kernel_count']} |")
    for scenario, row in samples.items():
        lines.extend(['', f'## {scenario.capitalize()} — seed 7', '', row['story'], '',
            f'[Annotated tokens]({scenario}.tokens.json) · [Complete joint trace]({scenario}.trace.json.gz)', ''])
        for pair in questions(row, 2):
            lines.extend([f"**Q:** {pair['question']}  ", f"**A:** {pair['answer']}", ''])
        # Prefer a step with same-word semantic ambiguity and a short prefix.
        choices = [(e, p) for e in row['trace'] for p in e['word_trace']
                   if len(p['annotated_choices']) > len(p['choices']) and len(p['prefix']) <= 4]
        if choices:
            event, p = choices[0]
            lines.extend([f"Next candidates after `{(' '.join(p['prefix']) or '(scene start)')}`:", '',
                          '| Word | Scene meaning | Clause/action | Entity | Probability |', '|---|---|---|---|---:|'])
            for candidate in p['annotated_choices'][:12]:
                a = event['attribute_table'][candidate['attributes']]
                lines.append(f"| {candidate['word']} | {a['event']['name']} | {(a.get('action') or {}).get('lemma', '—')} | {a.get('entity') or '—'} | {candidate['probability']:.4f} |")
            if len(p['annotated_choices']) > 12:
                lines.extend(['', 'Table shows the first 12 alternatives; the complete distribution is in the trace.'])
    lines.extend(['', 'The runtime conditions on the visible word while retaining correlated attribute alternatives.',
                  'The exported per-token posterior is what was known at emission; later words can resolve it internally.',
                  'State features are from before the candidate scene commits. Scene frame roles and clause roles are distinct.',
                  'Unknown or inapplicable bindings remain explicit; no entity is invented from a matching noun.', ''])
    (out/'report.md').write_text('\n'.join(lines))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path('grammarworlds/runs/attribute_generation_20261106'))
    parser.add_argument('--seeds', type=int, default=10)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error('seeds must be positive')
    run(args.out, args.seeds)
