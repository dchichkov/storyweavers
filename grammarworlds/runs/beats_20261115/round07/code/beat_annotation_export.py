"""Add beat readings to the existing 400-story archive without replacing text."""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

from .story_memory import load_documents,validate
from .storytelling.runtime import setup
from .storytelling.surface import detokenize
from .world import Frame
from .beat_annotations import annotate_beats


def replay_document(doc):
    """Replay the archived frame tape, not a fresh stochastic surface sample."""
    pack,w=setup(doc['scenario'],doc['seed'],**doc['source_options'])
    initial=w.to_dict()
    for entity,record in doc['entities'].items():
        if record['initial'] is not None:
            assert initial['entities'][entity]==record['initial'],'source initial state changed'
    for event in doc['events']:
        f=Frame(**{**event['frame'],'cause_ids':tuple(event['frame']['cause_ids'])})
        before=w.to_dict()['entities']
        prose=detokenize([doc['tokens'][tid]['token'] for tid in event['token_ids']])
        record=pack.commit(w,f,prose);after=w.to_dict()['entities']
        effects={}
        for entity in before.keys()|after.keys():
            old=before.get(entity,{});new=after.get(entity,{})
            delta={k:dict(before=old.get(k),after=new.get(k)) for k in old.keys()|new.keys() if old.get(k)!=new.get(k)}
            if delta:effects[entity]=delta
        assert effects==event['effects'],'archived source physics changed'
        record['speakers']=[e for e,tags in event['entity_tags'].items() if 'speaker' in tags]
        record['referents']=[e for e,tags in event['entity_tags'].items() if 'mentioned' in tags]
        record['narrated']=event['narrated']
    return dict(initial_world=initial,final_world=w.to_dict(),options=doc['source_options'])


def export(source,out):
    out.mkdir(parents=True,exist_ok=False);counts=Counter();worlds=set();tokens=0;events=0;documents=0
    with gzip.open(out/'stories.memory.jsonl.gz','wt') as sink:
        for doc in load_documents(source):
            before=deepcopy(doc)
            row=replay_document(doc)
            annotate_beats(doc,row=row);validate(doc)
            assert doc['text']==before['text'] and doc['attributes']==before['attributes']
            assert [(t['token'],t['candidates'],t['position']) for t in doc['tokens']]==[(t['token'],t['candidates'],t['position']) for t in before['tokens']]
            counts.update(b['kind'] for e in doc['events'] for b in e['beats'])
            worlds.add(doc['scenario']);tokens+=len(doc['tokens']);events+=len(doc['events']);documents+=1
            sink.write(json.dumps(doc,separators=(',',':'))+'\n')
            if documents%50==0:print(documents,flush=True)
    summary=dict(documents=documents,worlds=len(worlds),tokens=tokens,events=events,beat_counts=counts,
                 text_positions_original_attributes_and_probabilities_preserved=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    root=Path(__file__).parent
    (out/'manifest.json').write_text(json.dumps({f:hashlib.sha256((root/f).read_bytes()).hexdigest()
          for f in ('beat_annotations.py','beat_annotation_export.py')},indent=2)+'\n')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path('grammarworlds/runs/plot_annotations_20261108'))
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();export(a.source,a.out)
