"""Export intact annotated stories and exercise retrieval into a bare setup."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from .storytelling.runtime import generate, SCENARIOS, setup
from .story_memory import annotate, retrieve, generate_retrieved, query
from .event_mapping import load_bank
from .event_line_replay import paper_world, world_from_dict
from .world import Entity


def demonstration_world():
    """Explicit test affordances, not source facts silently added by retrieval."""
    world = paper_world()
    world.entities['ada'].properties.update({'can_shape_clay','can_drum','can_prepare_support',
                                            'can_sketch_moon','can_repair_fixture'})
    world.entities['ada'].state.add('practiced')
    world.entities.update(
        clay=Entity('clay','cup','object','bench',properties={'clay'},state={'wet'}),
        rib=Entity('rib','shaping rib','tool','ada',properties={'shape'}),
        drum=Entity('drum','drum','instrument','ada',properties={'portable','physics:drum'}),
        ladder=Entity('ladder','ladder','tool','bench',properties={'portable','reach'}),
        tap=Entity('tap','tap','object','garden',properties={'repairable_fixture'},state={'broken'}),
        sheet=Entity('sheet','paper','object','ada',properties={'drawable'},state={'blank'}),
        pencil=Entity('pencil','pencil','tool','ada',properties={'draw'}),
        atlas=Entity('atlas','atlas','object','ada',properties={'moon_reference'},state={'moon_picture'}))
    return world


def run(out, seed=3000, count=20):
    if count < 1: raise ValueError('positive story count required')
    out = Path(out); out.mkdir(parents=True,exist_ok=False)
    summaries, examples = {}, []
    with gzip.open(out/'stories.memory.jsonl.gz','wt') as stream:
        for scenario in SCENARIOS:
            seen, portable, hits, totals = set(), set(), Counter(), Counter()
            for current in range(seed,seed+count):
                row = generate(scenario,current,continuations='expanded',symbolic_heads=True)
                doc = annotate(row)
                stream.write(json.dumps(doc,separators=(',',':'))+'\n')
                seen.update(e['kind'] for e in doc['events'])
                supported = [e for e in doc['events'] if e['mapping_rules']]
                portable.update(e['kind'] for e in supported)
                hits.update(rule for e in supported for rule in e['mapping_rules'])
                totals.update(stories=1,tokens=len(doc['tokens']),events=len(doc['events']),
                    supported_events=len(supported),visible_supported_events=sum(bool(e['token_ids']) for e in supported))
                if current == seed:
                    examples.append(doc)
                    (out/f'{scenario}.memory.json').write_text(json.dumps(doc,indent=2)+'\n')
            pack,_ = setup(scenario,seed)
            summaries[scenario] = dict(totals,observed_kinds=sorted(seen),portable_kinds=sorted(portable),
                mapping_rule_hits=dict(hits),registered_kinds=len(pack.KERNELS),missing_kinds=sorted(set(pack.KERNELS)-seen))
            print(scenario,json.dumps(dict(totals)),flush=True)
    # Re-query the receiving state each time; no source event IDs are supplied.
    current = paper_world()
    repair_before = retrieve(examples,current,operations=['patch_paper'])
    assert not repair_before['candidates']
    continuation = []
    for op, hints in [('fetch',{'worker':'ada'}),('patch_paper',{'worker':'ada'}),
                      ('put_item',{'worker':'ada','item':'book'})]:
        row = generate_retrieved(examples,current,operations=[op],bindings=hints,seed=7)
        assert row['status']=='complete'
        continuation.append(row)
        current = world_from_dict(row['final_world'],allow_history=True)
    assert 'repaired' in current.entities['book'].state
    assert current.entities['book'].location=='bench'
    additional = []
    world = demonstration_world()
    before = world.to_dict()
    for op in ('shape_clay','perform_solo','prepare_support','repair_fixture','sketch_moon'):
        row = generate_retrieved(examples,world,operations=[op],bindings={'worker':'ada'},seed=7)
        assert row['status']=='complete' and world.to_dict()==before
        additional.append(row)
    with gzip.open(out/'retrieval.traces.jsonl.gz','wt') as stream:
        for row in continuation+additional:stream.write(json.dumps(row)+'\n')
    summary = dict(worlds=summaries,mapping_rules=len(load_bank()['rules']),
        total_stories=sum(s['stories'] for s in summaries.values()),
        total_events=sum(s['events'] for s in summaries.values()),
        observed_kinds=sum(len(s['observed_kinds']) for s in summaries.values()),
        portable_kinds=sum(len(s['portable_kinds']) for s in summaries.values()),
        supported_events=sum(s['supported_events'] for s in summaries.values()),
        visible_supported_events=sum(s['visible_supported_events'] for s in summaries.values()),
        demonstrated_target_events=sum(len(r['trace']) for r in continuation+additional),
        continuation=' '.join(r['story'] for r in continuation),
        limitations=['Operation filters and worker/item hints are supplied in the demonstration.',
            'No open-ended planner or new quality judge is part of this export.'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines = ['# Intact stories as reusable annotated memory', '',
        f"{summary['total_stories']} source stories from {len(summaries)} existing worlds. Original text and sampled token order are preserved and each source history replays.",
        f"Observed {summary['observed_kinds']} pack-qualified event kinds; {summary['portable_kinds']} have reviewed mapping support. The bank has {summary['mapping_rules']} rules.",
        f"{summary['supported_events']} supported event occurrences, of which {summary['visible_supported_events']} have their own visible tokens; the remainder are explicit silent source-history annotations.", '',
        '| World | Stories | Tokens | Event kinds | Mappable kinds |', '|---|---:|---:|---:|---:|']
    for name,s in summaries.items():
        lines.append(f"| {name} | {s['stories']} | {s['tokens']} | {len(s['observed_kinds'])}/{s['registered_kinds']} | {len(s['portable_kinds'])} |")
    lines += ['', '## Receiving-world demonstration', '',summary['continuation'], '',
        'The target starts with Ada holding a torn paper book, tape on a reachable bench, and explicit paper-repair capabilities. No source event IDs are chosen. The demonstration supplies the operation filters fetch → repair → put and binds the worker to Ada; the final put also binds the item to the book.',
        'Memory is queried again after each commit. Repair is infeasible before fetching and feasible afterward. The final book is repaired and on the bench. This is an annotated-memory retrieval demonstration, not automatic plot invention.', '',
        '## Additional target operations', '',
        'These use a separate underdefined craft setup with explicitly declared wet clay, shaping tool, practiced drummer, support-preparation capability, broken repairable tap and drawing materials/ability.', '']
    for row in additional:
        refs=row['source']['memory_retrieval']['references']
        lines += [row['story'], '', 'Source references: '+', '.join(f"{r['scenario']} event {r['event_id']} ({'silent' if r['anchor']['silent'] else 'visible'})" for r in refs)+'.', '']
    lines += ['## Intact source examples', '',
        f'First seed ({seed}) from each world, chosen before generation. Linked JSON includes token candidates, separate historical observations, and mapping references. The prose is not split into replacement snippets.', '']
    for doc in examples:
        lines += ['### '+doc['scenario'], '', doc['text'], '',
                  f"[Annotated full token stream]({doc['scenario']}.memory.json)", '']
        supported=query([doc],portable_only=True)
        lines += ['Reusable references: '+', '.join(f"{h['event_id']} {h['name']} ({'silent boundary' if h['anchor']['silent'] else str(len(h['token_ids']))+' tokens'})" for h in supported)+'.', '']
    lines += ['## Limits and inspection findings', '',
        'Unsupported events remain fully annotated and searchable. Matching an operation pattern is not permission to replay source state changes: target kinds, capabilities, live guards and replay must all pass.',
        'The source texts are unchanged, so their existing narrative strengths and defects are unchanged. The target demonstration is a short action sequence without a developed premise/turn. No Luna quality improvement is claimed.',
        'Token-local syntax labels and mention resolution retain the known embedded-object/nominal-place limitations. Historical after-state is explicitly source memory, never a target prefix observation.',
        'Compound resource changes (watering), consent, reservations and many endings remain unsupported for portable execution; they are not reduced to simpler transfers merely to raise coverage.', '']
    (out/'report.md').write_text('\n'.join(lines))
    paths=[Path(__file__),Path(__file__).with_name('story_memory.py'),Path(__file__).with_name('reusable_operations.py'),
        Path(__file__).with_name('event_mapping.py'),Path(__file__).with_name('mapping_bank')/'core.json',
        Path(__file__).with_name('mapping_bank')/'story_tokens.json']
    paths.append(Path(__file__).with_name('mapping_bank')/'seed_stories.json')
    root=Path(__file__).resolve().parents[1]
    (out/'manifest.json').write_text(json.dumps({str(p.resolve().relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=3000)
    parser.add_argument('--count',type=int,default=20)
    args=parser.parse_args(); run(args.out,args.seed,args.count)
