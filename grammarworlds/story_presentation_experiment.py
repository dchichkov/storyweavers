"""Sample framing over saved joined plots or raw beat-experiment source rows."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from .story_presentation import present


def experiment(source,out):
    out.mkdir(parents=True,exist_ok=False)
    lines=['# Sampled titles, openings and closings','',
        'Saved native narratives, presented with the weighted framing grammar. '
        'Body prose, native events and world state are preserved. Titles, openings '
        'and closings have their own annotated-word distributions.','']
    summary=[]
    with gzip.open(source,'rt') as src,gzip.open(out/'presentations.jsonl.gz','wt') as dst:
        for line in src:
            record=json.loads(line)
            original=record.get('row',record)
            if not ('rows' in original or 'scenes' in original):continue
            r=present(original)
            assert r['final_world']==original['final_world']
            native_key='rows' if 'rows' in original else 'scenes'
            assert r[native_key]==original[native_key]
            assert r['raw_story']==original.get('raw_story',original['story'])
            styles={role:r['presentation'][role]['styles'] for role in ('title','opening','closing')
                    if role in r['presentation']}
            label=r.get('plan',r.get('scenario','story'))
            summary.append(dict(source=label,seed=r['seed'],styles=styles))
            dst.write(json.dumps(dict(source=label,seed=r['seed'],raw_story=r['raw_story'],
                story=r['story'],presentation=r['presentation']),separators=(',',':'))+'\n')
            lines += [f"## {label}, seed {r['seed']}",'',r['story'],'',
                      'Styles: '+', '.join(role+' = '+','.join(v) for role,v in styles.items())+'.','']
    lines += ['## Behavior and limits','',
        '- The title appears once, followed by an optional opening, the intact story, and an optional closing.',
        '- Immediate openings and final-image closings reuse the existing first/last scene; they do not duplicate it.',
        '- Incomplete plots offer “To be continued” forms. Empty generations get no invented wrapper story.',
        '- Standalone source completion uses its native ending flag, separately from executable plot achievement; final-image reuse needs an authored image role.',
        '- Openings use initial identity/location; titles can name the final object, including a cup reshaped into a bowl.',
        '- No new weather, habits, dialogue, future happiness or physical outcomes are invented.',
        '- This improves presentation; it does not establish a stronger plot or a higher literary-quality score.','']
    (out/'report.md').write_text('\n'.join(lines))
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    root=Path(__file__).parent
    files=['story_presentation.py','plot_continuation.py','story_presentation_experiment.py']
    manifest=dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  code_sha256={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('grammarworlds/runs/plot_execution_20261109_v2/traces.jsonl.gz'))
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();experiment(args.source,args.out)
