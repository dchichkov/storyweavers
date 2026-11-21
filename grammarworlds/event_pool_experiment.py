"""Reproduce the bounded fragment-pool comparison and physical ablations."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from .event_pool import attach, demo_brief, generate, run
from .pool_fragments import ROOTS, FRAGMENTS
from .pool_mechanics import PoolLines
from .event_line_replay import replay, verify
from .catalog_attachment import Unresolved, bare_world
from .world import Entity


def local_fixture(magic=True):
    w=bare_world();w.setting='garden';w.hero='ada';w.helper='teo'
    w.entities={
        'ada':Entity('ada','Ada','person','garden',pronoun='she',properties={'can_hold'}|({'can_portal'} if magic else set())),
        'teo':Entity('teo','Teo','person','garden',pronoun='he',properties={'can_hold'}),
        'pet':Entity('pet','brown rabbit','animal','pen',properties={'rabbit','calm'},state={'hungry'}),
        'prop':Entity('prop','velvet hat','object','desk',properties={'hat','rabbit_capacity'}|({'portal_hat'} if magic else set()),state={'bound'} if magic else {'open'}),
        'pen':Entity('pen','pen','place','garden',properties={'reachable'}),
        'desk':Entity('desk','desk','place','garden',properties={'reachable'}),
        'bell':Entity('bell','bell','object','garden',properties={'rings'},state={'silent'}),
    }
    return w


def experiment(out,count=20):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    local=dict(schema='event-pool-v1',intent='reveal',setting='garden',roles={'rabbit':'pet','hat':'prop'})
    renamed=demo_brief();renamed['roles']['actor']={'name':'Merlinus'}
    profiles={
        'magic_from_bare':(demo_brief(),None),
        'magic_local_cast':(local,local_fixture()),
        'stage_local_cast':(local,local_fixture(False)),
        'source_flavor':(renamed,None),
        'ambiguous_open_hat':(demo_brief('ambiguous'),None),
        'kite_from_brief':(dict(schema='event-pool-v1',intent='fly',setting='meadow',environment=['windy'],roles={'item':{}}),None),
        'drawing_from_brief':(dict(schema='event-pool-v1',intent='draw',setting='garden',roles={'item':{}}),None),
    }
    summaries={name:run(out/name,brief,count,w) for name,(brief,w) in profiles.items()}
    # Direct replay of the authored program is a control for retrieval plumbing,
    # not an independent quality judge or a test of extracting arbitrary code.
    a=attach(demo_brief());control=[];identical=0
    for seed in range(count):
        for heads in (False,True):
            row=replay(a['world'],a['template'],a['bindings'],seed,heads=heads,driver_class=PoolLines)
            verify(row,a['template'],driver_class=PoolLines);control.append(row)
            retrieved,_=generate(demo_brief(),seed=seed,heads=heads)
            identical+=row['story']==retrieved['story'] and row['final_world']==retrieved['final_world']
    with gzip.open(out/'direct_authored_control.jsonl.gz','wt') as f:
        for row in control:f.write(json.dumps(row)+'\n')
    ablations={};blocked_rows=[]
    for name in ['no_hat_physics','wand_elsewhere','missing_ribbon','rabbit_not_calm','food_elsewhere']:
        a=attach(demo_brief());w,t,b=a['world'],a['template'],a['bindings']
        if name=='no_hat_physics':w.entities[b['hat']].properties.remove('portal_hat')
        elif name=='wand_elsewhere':w.entities[b['wand']].location='elsewhere'
        elif name=='missing_ribbon':del w.entities[b['ribbon']]
        elif name=='rabbit_not_calm':w.entities[b['rabbit']].properties.remove('calm')
        else:w.entities[b['food']].location='elsewhere'
        # Removal before construction of a driver fails the binding contract.
        if name=='missing_ribbon':
            try:replay(w,t,b,driver_class=PoolLines)
            except ValueError as exc:ablations[name]=dict(status='invalid_binding',reason=str(exc))
            else:raise AssertionError(name)
            continue
        rows=[replay(w,t,b,seed,heads=True,driver_class=PoolLines) for seed in range(count)]
        for row in rows:verify(row,t,driver_class=PoolLines);assert row['status']=='blocked'
        ablations[name]=dict(runs=count,blocked=len(rows),example=rows[0]['blocked'])
        blocked_rows.extend(dict(ablation=name,**row) for row in rows)
    shortened=deepcopy(ROOTS);shortened['hat.portal_bound']['steps'].pop(1)
    for name,options in [('no_pool',{'roots':{}}),('missing_recovery_fragment',{'roots':shortened})]:
        try:attach(demo_brief(),**options)
        except Unresolved as exc:ablations[name]=dict(status='unresolved',reason=str(exc))
        else:raise AssertionError(name)
    with gzip.open(out/'blocked_traces.jsonl.gz','wt') as f:
        for row in blocked_rows:f.write(json.dumps(row)+'\n')
    summary=dict(profiles=summaries,direct_authored_equal=identical,direct_authored_runs=len(control),ablations=ablations)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'pool.json').write_text(json.dumps(dict(recipes=ROOTS,fragments=FRAGMENTS),indent=2)+'\n')
    files=['event_pool.py','pool_fragments.py','pool_mechanics.py','pool_qa.py','event_pool_experiment.py','test_event_pool.py']
    hashes={}
    for name in files:
        source=Path(__file__).parent/name;target=out/'source'/name;target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source,target);hashes[name]=hashlib.sha256(source.read_bytes()).hexdigest()
    (out/'manifest.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print(json.dumps({'direct_authored_equal':identical,'profiles':len(profiles),'blocked_runs':len(blocked_rows)},indent=2))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--count',type=int,default=20)
    args=p.parse_args();experiment(args.out,args.count)
