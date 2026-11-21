"""Unfiltered current-world audit: replay, physical guards, attention and visible QA."""
import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import statistics

from ..world import Frame
from .runtime import SCENARIOS, generate, replay, setup, build_forest
from .qa import questions

ROOT = Path(__file__).resolve().parents[2]


def physical_checks(pack, world, frame):
    """Remove carriers/prerequisite flags, and reject a forged physical actor."""
    checks = 0
    kernel = next(k for k, f in pack.candidates(world) if f == frame)
    mutations = [('carrier', x) for x in {frame.actor, frame.patient, frame.instrument} if x]
    mutations += [('flag', x) for x in kernel.requires]
    for kind, value in mutations:
        altered = world.clone()
        if kind == 'carrier':
            del altered.entities[value]
        else:
            altered.flags.remove(value)
        before = altered.to_dict()
        try:
            pack.commit(altered, frame, '')
        except ValueError:
            pass
        else:
            raise AssertionError((world.scenario, frame.kind, kind, value, 'accepted'))
        assert altered.to_dict() == before, 'Rejected event mutated state'
        checks += 1
    before = world.to_dict()
    try:
        pack.commit(world, replace(frame, actor='unembedded'), '')
    except ValueError:
        pass
    else:
        raise AssertionError('Unembedded actor accepted')
    assert before == world.to_dict()
    return checks + 1


def run(out, count=60, start=1000):
    if count < 1:
        raise ValueError('count must be positive')
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    summary, samples = {}, []
    with (out/'stories_qa.jsonl').open('w') as sink:
        for scenario in SCENARIOS:
            words, kinds, paths = [], Counter(), Counter()
            guards = qa_count = ablations = attention_changes = 0
            for tense in ('past','present'):
                for seed in range(start,start+count):
                    row = generate(scenario,seed,tense=tense); replay(row)
                    qa = questions(row)
                    assert len(qa) >= 5 and len({q['question'] for q in qa}) == len(qa)
                    assert len({q['kind'] for q in qa}) >= 3
                    assert all(q['answer'].endswith('.') and len(q['answer'].split()) >= 3 for q in qa)
                    assert any(q['answer'].count('.') >= 2 for q in qa)
                    assert len({p for scene in row['scenes'] for p in scene['speakers']}) >= 2
                    assert row['story'].count('“') == row['story'].count('”') >= 2
                    for q in qa:
                        assert q['event_ids'] and q['entity_ids']
                        assert all(row['story'][e['start']:e['end']] == e['text'] for e in q['evidence'])
                    pack,w = setup(scenario,seed)
                    compared = False
                    for event in row['final_world']['history']:
                        f = Frame(**{**event['frame'],'cause_ids':tuple(event['frame']['cause_ids'])})
                        assert set(f.cause_ids) <= {x.id for x in w.facts_for_attention()}
                        guards += physical_checks(pack,w,f)
                        if not compared and len(pack.candidates(w)) > 1:
                            on,_ = build_forest(pack,w,tense)
                            off,_ = build_forest(pack,w,tense,attention=False)
                            def masses(forest):
                                result=Counter()
                                for d in forest.derivations: result[d.frame] += d.probability
                                return result
                            a,b = masses(on), masses(off)
                            assert a.keys() == b.keys()
                            assert all(x['contribution'] == 0 for item in off.evidence.values() for x in item['attention'])
                            attention_changes += any(abs(a[k]-b[k])>1e-8 for k in a)
                            ablations += 1; compared=True
                        record=pack.commit(w,f,event['sentence'])
                        for key in ('referents','speakers','narrated'):record[key]=event[key]
                    assert w.to_dict() == row['final_world']
                    words.append(len(row['story'].split()));qa_count+=len(qa);kinds.update(q['kind'] for q in qa)
                    paths[tuple(e['frame']['kind'] for e in w.history)]+=1
                    compact={k:row[k] for k in ('scenario','seed','tense','story','text_sha256','scenes')}
                    compact.update(qa=qa,final_state=w.snapshot(),frames=[e['frame'] for e in w.history])
                    sink.write(json.dumps(compact)+'\n')
                    if seed==start+7 and tense=='past':samples.append(compact)
            summary[scenario]=dict(stories=len(words),mean_words=statistics.mean(words),min_words=min(words),max_words=max(words),
                qa_pairs=qa_count,question_kinds=dict(kinds),guard_interventions=guards,
                ablations=ablations,attention_changed_event_mass=attention_changes,event_paths=len(paths))
            print(scenario,json.dumps(summary[scenario]),flush=True)
    frozen=json.loads((ROOT/'grammarworlds/portable/sources/pre_holdout_freeze.json').read_text())
    assert all(hashlib.sha256((ROOT/'grammarworlds/portable'/p).read_bytes()).hexdigest()==h for p,h in frozen['sha256'].items())
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Fresh unfiltered stories and reading QA','',f'Seed {start+7}, selected before generation.','']
    for row in samples:
        lines += [f"## {row['scenario']}",'',row['story'],'']
        for q in row['qa']:lines += ['Q: '+q['question'],'A: '+q['answer'],'']
    (out/'samples.md').write_text('\n'.join(lines))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--count',type=int,default=60);p.add_argument('--start',type=int,default=1000)
    a=p.parse_args();run(a.out,a.count,a.start)
