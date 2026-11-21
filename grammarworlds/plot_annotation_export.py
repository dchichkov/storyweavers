"""Annotate the complete twenty-world source pool and export live examples."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from .plot_bank import BANK,ARCHETYPES
from .plot_annotations import annotate_plots,validate_bank
from .event_scales import annotate_scales
from .story_memory import load_documents,validate,annotate
from .storytelling.runtime import generate,replay


def export(memory,out):
    validate_bank();documents=[d for d in load_documents(memory) if d['scenario'] in BANK]
    out.mkdir(parents=True,exist_ok=False)
    by_world={};kinds=set();roles=Counter();links=Counter();tokens=0
    with gzip.open(out/'stories.memory.jsonl.gz','wt') as sink:
        for doc in documents:
            original=(doc['text'],doc['text_sha256'],json.dumps(doc['attributes'],sort_keys=True),
                      [[dict(c) for c in t['candidates']] for t in doc['tokens']])
            if 'event_scales' not in doc:annotate_scales(doc)
            annotate_plots(doc);validate(doc)
            assert original==(doc['text'],doc['text_sha256'],json.dumps(doc['attributes'],sort_keys=True),
                              [[dict(c) for c in t['candidates']] for t in doc['tokens']])
            sink.write(json.dumps(doc,separators=(',',':'))+'\n')
            by_world.setdefault(doc['scenario'],doc)
            kinds.update((doc['scenario'],e['kind']) for e in doc['events'])
            roles.update(e['plot']['role'] for e in doc['events']);tokens+=len(doc['tokens'])
            links.update(link['relation'] for n in doc['plots']['nodes'].values() for link in n['links'])
    live=[]
    with gzip.open(out/'live_candidates.jsonl.gz','wt') as sink:
        for scenario in BANK:
            base=generate(scenario,3007,multiscale=True)
            row=generate(scenario,3007,multiscale=True,plot_annotations=True)
            assert row['story']==base['story'];assert replay(row)
            assert row['final_world']==base['final_world']
            annotate(row)
            sink.write(json.dumps(row,separators=(',',':'))+'\n')
            live.append(scenario)
    supported=sorted({a['name'] for s in BANK.values() for a in s['archetypes']})
    summary=dict(worlds=len(by_world),source_documents=len(documents),observed_fine_event_kinds=len(kinds),
        annotated_tokens=tokens,observed_event_roles=dict(roles),narrative_links=dict(links),
        supported_partial_archetypes=supported,unrepresented_archetypes=sorted(set(ARCHETYPES)-set(supported)),
        worlds_without_archetype=[s for s in BANK if not BANK[s]['archetypes']],
        authored_event_roles=sum(e['basis']=='authored_event_reading' for s in BANK.values() for e in s['events'].values()),
        neutral_event_roles=sum(e['basis']=='neutral_default' for s in BANK.values() for e in s['events'].values()),
        live_examples=len(live),text_and_existing_posteriors_preserved=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Plot annotations on intact story memory','',
        f"Annotated {len(documents)} source documents across {len(by_world)} worlds: {len(kinds)} observed fine-event kinds and {tokens} tokens. "
        'Original prose, text hashes, candidate attribute tables and posterior probabilities were preserved. '
        'Twenty fresh live examples also carry proposed plot context before sampling; their text and final physical worlds match the metadata-free baseline.','',
        '## Scope','',
        'Archetype labels are authored partial analogies, not calibrated probabilities or claims of complete Booker structures. '
        'This collection supports quest, mystery and limited comedy analogies; other stories retain their local pattern without an archetype. '
        'No example was forced into tragedy, rebirth, rags-to-riches, voyage-and-return, overcoming-the-monster or rebellion. '
        'These categories remain available in the inventory but need suitable examples.','',
        'Narrative relationships (responds-to, uses-discovery, payoff-of, and similar) are authored interpretations. '
        'Native engine dependencies and replayed entity changes are recorded separately. Candidate context sees only prior events; '
        'observed consequences occur only in retrospective source annotations. These labels do not yet change event selection or fix story quality.','',
        '| World | Local pattern | Partial archetype | Named narrative links in example |',
        '|---|---|---|---:|']
    for scenario,doc in by_world.items():
        s=BANK[scenario];n=next(iter(doc['plots']['nodes'].values()))
        lines.append(f"| {scenario} | {s['local_pattern']} | {', '.join(a['name'] for a in s['archetypes']) or 'unassigned'} | {len(n['links'])} |")
    for scenario,doc in by_world.items():
        lines+=['',f'## {scenario}','',doc['text'],'',
            '| Event | Stage | Narrative role | Earlier narrative evidence |',
            '|---|---|---|---|']
        names={e['id']:e['kind'] for e in doc['events']}
        for e in doc['events']:
            p=e['plot'];refs='; '.join(f"{l['relation']}: {names[l['source_event']]}" for l in p['incoming_links'])
            lines.append(f"| {e['kind']} | {p['stage']} | {p['role']} | {refs or '—'} |")
    lines+=['','Artifacts: `stories.memory.jsonl.gz` retains the full annotated pool; `live_candidates.jsonl.gz` records '
            'fresh generated token distributions; `summary.json` records counts.','']
    (out/'report.md').write_text('\n'.join(lines))
    root=Path(__file__).parent
    files=['plot_bank.py','plot_annotations.py','plot_annotation_export.py','story_memory.py','storytelling/runtime.py','memory_transfer.py']
    (out/'manifest.json').write_text(json.dumps(dict(input_archive=str(memory),source_sha256={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files}),indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--memory',type=Path,default=Path('grammarworlds/runs/seed_worlds_20261107_v4'))
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();export(a.memory,a.out)
