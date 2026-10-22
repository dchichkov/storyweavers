"""Reproduce dialogue indexing on the same 36 stories, using current prose libs."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from conversation import Conversation, VERSION
from prose import render_book
from qa import enrich
from qa_checks import measure
from runtime import realize


def main():
    out=Path(__file__).resolve().parent;rows=[];coverage=[];targeted=[]
    for run in ['compact_algebra_v2','improvement_luna_v6']:
        for source in sorted((ROOT/'runs'/run).glob('*/samples_with_trace.json')):
            module=ast.parse((source.parent/'generator.py').read_text())
            book=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign)
                      and any(isinstance(t,ast.Name) and t.id=='BOOK' for t in n.targets))
            for original in json.loads(source.read_text()):
                rendered=realize(original['trace'],lambda trace,rng:render_book(trace,rng,book),original['prose_seed'])
                assert rendered['story']==original['story'],(source,original['seed'])
                assert rendered['trace']==original['trace']
                row=enrich(rendered);rows.append(row)
                prototype=Conversation(row['trace'],row['paragraphs'])
                coverage.append(dict(source=str(source.relative_to(ROOT)),seed=row['seed'],
                    utterances=len(prototype.dialogue),precise_events=sum(u['event_id'] is not None for u in prototype.dialogue)))
                conversations=[]
                for starter in prototype.starters():
                    if starter['kind']!='dialogue':continue
                    dialog=Conversation(row['trace'],row['paragraphs'])
                    for question in [starter['question'],'Why did they say that?','Who were they talking to?','What was said next?']:
                        dialog.ask(question)
                    conversations.append(dict(id=f'd{len(conversations)}',protocol=VERSION,
                        trace_sha256=dialog.trace_sha256,turns=dialog.turns))
                targeted.append(dict(row,conversations=conversations))
    report=measure(rows)
    report.update(identical_stories=len(rows),coverage=coverage,targeted=measure(targeted),api_requests=0,api_cost_usd=0,
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                       for name in ('conversation.py','dialogue.py','qa.py','qa_checks.py','prose.py','runtime.py')})
    (out/'renderer_replay.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows))
    (out/'renderer_replay_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    with (out/'targeted_dialogue.md').open('w') as stream:
        for row in targeted:
            if not row['conversations']:continue
            stream.write(f'## {row["title"]} — {row["seed"]}\n\n{row["story"]}\n\n')
            for conversation in row['conversations']:
                for turn in conversation['turns']:
                    stream.write(f'**Q:** {turn["question"]}\n\n**A:** {turn["answer"]}\n\n')
    (out/'targeted_dialogue.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in targeted if row['conversations']))
    print(json.dumps({k:v for k,v in report.items() if k not in ('coverage','source_sha256')},indent=2))
    return int(bool(report['defects'] or report['targeted']['defects']))


if __name__=='__main__':raise SystemExit(main())
