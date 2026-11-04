#!/usr/bin/env python3
"""Reproducible content inventory, causal witnesses, and policy traversal."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import unittest

from content import BEATS, ENDINGS, EXCHANGES, MIXINS
from engine import Session, replay
from interactions import PRIVATE
from play import DEMOS, run_demo
from test_drama import all_performances, assert_world

ROOT = Path(__file__).resolve().parent


def inventory():
    performances = list(all_performances())
    lines = [line for p in performances for line in p.lines]
    source_files = ('content.py', 'content_ext.py', 'interactions.py')
    return {
        'sequenced_beats': len(BEATS), 'within_beat_goals': sum(len(b.goals) for b in BEATS),
        'terminal_outcomes': len(ENDINGS), 'terminal_performances': sum(len(v) for _, v, _ in ENDINGS),
        'global_mixin_topics': len(MIXINS), 'global_mixin_tiers': sum(len(t) for t in MIXINS.values()),
        'private_content_units': sum(len(v) for topics in PRIVATE.values() for v in topics.values()),
        'social_exchange_bindings': len(EXCHANGES), 'performance_slots': len(performances),
        'authored_line_slots': len(lines), 'unique_authored_lines': len(set(lines)),
        'authored_word_slots': sum(len(line.split()) for line in lines),
        'unique_line_words': sum(len(line.split()) for line in set(lines)),
        'content_source_lines': sum(len((ROOT/p).read_text().splitlines()) for p in source_files),
        'engine_source_lines': len((ROOT/'engine.py').read_text().splitlines()),
        'note': 'Counts are loaded performance slots, including alternates and reused lines; engine and dynamic interaction scaffolding is excluded. Units are not comparable to production Façade beats. Source lines include superseded base definitions, so they are not a content measure.',
    }


def policy_actions(session, policy):
    actions = list(session.actions())
    if policy == 'curious':
        actions = [a for a in actions if a not in ('leave', 'provoke')]
        return actions + ['listen'] * 4
    return actions + ['listen'] * 8


def sample(seed, policy):
    rng = random.Random(seed)
    session = Session(seed)
    session.start()
    while not session.outcome and session.state['turn'] < session.max_turns:
        session.step(rng.choice(policy_actions(session, policy)))
    return session


def audit(count, start=0, policy='broad'):
    check = unittest.TestCase()
    demos = {name: run_demo(name) for name in DEMOS}
    outcomes, paths, seen_beats = Counter(), set(), set()
    goal_variants, failures, transcripts = set(), [], []
    disclosure_patterns, endings_with_knowledge = Counter(), Counter()
    private_count = betrayal_count = 0
    for seed in range(start, start + count):
        try:
            session = sample(seed, policy)
            check.assertIsNotNone(session.outcome)
            assert_world(check, session)
            check.assertEqual(replay(session.export()).export(), session.export())
            for event in session.events:
                if event['kind'] == 'private':
                    before, after = event['before']['people'], event['after']['people']
                    for person in ('mara', 'eli'):
                        if before[person]['location'] != before['player']['location']:
                            check.assertEqual(before[person]['knows'], after[person]['knows'])
        except (AssertionError, ValueError, RuntimeError, KeyError) as error:
            failures.append({'seed': seed, 'error': str(error)})
            continue
        outcomes[session.outcome] += 1
        path = tuple(d['chosen'] for d in session.selections if 'chosen' in d)
        paths.add(path); seen_beats.update(path)
        goal_variants.update((e['source'], e['variant']) for e in session.events if e['kind'] == 'goal')
        people = session.state['people']
        pattern = ''.join('1' if people[p]['disclosed'] else '0' for p in ('mara', 'eli'))
        disclosure_patterns[pattern] += 1
        endings_with_knowledge[session.outcome + ':' + pattern] += 1
        private_count += any(e['kind'] == 'private' for e in session.events)
        betrayal_count += people['player']['betrayal']
        transcripts.append(hashlib.sha256('\n'.join(session.transcript).encode()).hexdigest())
    report = {
        'inventory': inventory(),
        'traversal': {'sessions': count, 'seed_start': start, 'seed_end': start+count-1, 'policy': policy,
                      'policy_definition': 'supported actions plus 8 listens' if policy == 'broad' else 'supported actions excluding leave/provoke, plus 4 listens',
                      'outcomes': dict(outcomes), 'unique_selected_beat_paths': len(paths),
                      'beats_reached': sorted(seen_beats), 'unreached_beats': sorted(set(b.id for b in BEATS)-seen_beats),
                      'goal_variants_reached': len(goal_variants), 'private_sessions': private_count,
                      'betrayal_sessions': betrayal_count, 'public_disclosure_patterns_mara_eli': dict(disclosure_patterns),
                      'unique_exact_transcripts': len(set(transcripts)), 'failures': failures},
        'scripted_witnesses': {name: {'outcome': s.outcome, 'turns': s.state['turn'],
                                     'words': len(' '.join(s.transcript).split()),
                                     'completed_beats': s.completed, 'aborted_beats': s.aborted} for name, s in demos.items()},
        'counterfactual': {'changed_inputs': 'Only the two early empathize actions become blame actions.',
                           'warm_outcome': demos['repair'].outcome, 'cold_outcome': demos['distrust'].outcome,
                           'same_later_script': DEMOS['repair'][4:] == DEMOS['distrust'][4:],
                           'different_completed_paths': demos['repair'].completed != demos['distrust'].completed},
        'limits': 'Mechanical invariants, audience knowledge, and replay are checked. Text counts and beat paths are not independent stories or literary ratings. No labor baseline or cost multiplier is measured.',
        'source_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')},
    }
    return report, demos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=500)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--policy', choices=('broad', 'curious'), default='broad')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--write', action='store_true', help='Regenerate examples, audit.json, and replay records')
    args = parser.parse_args()
    if args.samples < 1:
        parser.error('--samples must be positive')
    report, demos = audit(args.samples, args.seed_start, args.policy)
    text = json.dumps(report, indent=2) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    if args.write:
        (ROOT/'audit.json').write_text(text)
        (ROOT/'examples').mkdir(exist_ok=True)
        for name, session in demos.items():
            (ROOT/'examples'/(name+'.txt')).write_text('\n\n'.join(session.transcript) + '\n\n[Ending: ' + session.outcome + ']\n')
            if name in ('repair', 'private', 'practical', 'betrayal'):
                session.save(ROOT/'examples'/(name+'.trace.json'))
    print(json.dumps({k: v for k, v in report.items() if k != 'source_hashes'}, indent=2))
    if report['traversal']['failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
