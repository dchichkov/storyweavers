#!/usr/bin/env python3
"""One-time behavioral equivalence experiment for the existing pond concert.

This ports data, not prose. The original module/catalog and run remain untouched.
It deliberately preserves the old world's semantics, including known limitations.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import random

import algebra as a
import factory as f
import worker
from runtime import solve, realize
from prose import render_book


def guard(cs):
    return [[c.key,c.op,c.value] for c in cs]


def export_scenes(spec):
    result={}
    for s in spec.scenes:
        guards=list(s.requires)
        if s.kernel=='Observe':
            node=dict(op='Observe',args=[s.actors[0],s.effects[0].value])
        elif s.kernel=='Tell':
            key=s.effects[0].value
            node=dict(op='Tell',args=[*s.actors,key.split('.knows.',1)[1]])
            guards=guards[1:]
        elif s.kernel=='Transfer':
            node=dict(op='Transfer',args=[*s.actors,s.effects[0].key.removesuffix('.owner')])
            guards=guards[1:]
        else:
            node=dict(op='Act',label=s.kernel,actors=list(s.actors))
            for op,label in [('set','set'),('inc','inc'),('copy','copy')]:
                values={e.key:e.value for e in s.effects if e.op==op}
                if values:node[label]=values
        if guards:node['when']=guard(guards)
        if s.summary:node['summary']=s.summary
        if s.pivotal:node['pivotal']=True
        if s.weight!=1:node['weight']=s.weight
        if s.max_uses!=1:node['max_uses']=s.max_uses
        result[s.id]=node
    return result


def port(source, destination, count=300):
    module=worker.load(source/'simulation.py','ported_source')
    seeds=[next(s for s in range(100) if random.Random(s).randrange(3)==i) for i in range(3)]
    specs=[module.build(s) for s in seeds]
    base=specs[0]
    changing=[k for k in base.initial if any(spec.initial[k]!=base.initial[k] for spec in specs)]
    entities={k:dict(v,state={}) for k,v in base.entities.items()}
    for key,value in base.initial.items():
        if '.knows.' in key and value is None:continue  # compiler-supplied slots
        entity,field=key.split('.',1);entities[entity]['state'][field]=value
    doc=dict(title=base.title,entities=entities,
             vary={'situation':[{k:spec.initial[k] for k in changing} for spec in specs]},
             compose=export_scenes(base),goal=guard(base.goal),
             rules={r.name:dict(when=guard(r.when),must=guard(r.must)) for r in base.rules},
             labels=base.labels,prune=base.prune,premises=list(base.premise_keys),outcomes=list(base.outcome_keys))
    book=json.loads((source/'catalog.json').read_text())
    for seed in range(count):
        old,new=solve(module.build(seed),seed),solve(a.build(doc,seed),seed)
        if old!=new:raise ValueError(f'Trace differs at seed {seed}')
        render=lambda trace,rng:render_book(trace,rng,book)
        for ps in (seed,42):
            if realize(old,render,ps)!=realize(new,render,ps):
                raise ValueError(f'Prose/QA differs at seed {seed}, prose seed {ps}')
    destination.mkdir(parents=True,exist_ok=True)
    f.save(destination/'world.json',doc)
    (destination/'simulation.py').write_text(a.compile_source(doc))
    report=dict(source=str(source.resolve()),source_sha256=f.digest(source/'simulation.py'),
                catalog_sha256=f.digest(source/'catalog.json'),seeds=count,prose_replays=count*2,
                exact_traces=True,exact_prose_and_qa=True,
                old_source_characters=len((source/'simulation.py').read_text()),
                compact_json_characters=len(json.dumps(doc,separators=(',',':'),ensure_ascii=False)),
                note='Characters, not billed tokens. Algebra changes no narrative or trace semantics in this port.')
    f.save(destination/'equivalence.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path('storyscenes/runs/improvement_luna_v6/pond_concert'))
    p.add_argument('--out',type=Path,default=Path('storyscenes/examples/pond_concert_compact'))
    p.add_argument('--count',type=int,default=300)
    args=p.parse_args();print(json.dumps(port(args.source,args.out,args.count),indent=2))
