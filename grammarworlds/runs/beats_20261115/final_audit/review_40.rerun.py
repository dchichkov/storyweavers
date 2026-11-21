"""Reproduce the final 20-world / two-seed review, preserving its earlier rows."""
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT))
from grammarworlds.storytelling.runtime import generate,replay
from grammarworlds.storytelling.qa import questions
from grammarworlds.story_memory import annotate
from grammarworlds.beat_qa import presentation_evidence,questions as beat_questions

FILES=['beat_grammar.py','beat_generation.py','beat_qa.py','beat_annotations.py',
       'story_presentation.py','storytelling/subject_coherence.py',
       'storytelling/attribute_grammar.py','storytelling/runtime.py']


def manifest():
    return {f:hashlib.sha256((ROOT/'grammarworlds'/f).read_bytes()).hexdigest() for f in FILES}


def main():
    prior=OUT/'review_40.before.jsonl.gz'
    if prior.exists():
        with gzip.open(prior,'rt') as f:before=[json.loads(line) for line in f]
    else:
        before=json.loads(Path('/tmp/beat_audit_701_907.json').read_text())
        with gzip.open(prior,'wt') as f:
            for row in before:f.write(json.dumps(row,separators=(',',':'))+'\n')
    assert len(before)==40 and {r['seed'] for r in before}=={701,907}
    assert len({r['scenario'] for r in before})==20
    started=datetime.now(timezone.utc).isoformat();code=manifest();summaries=[]
    samples=['# Held-out review: all 20 source worlds, seeds 701 and 907','',
             'Beat budget 6; expanded continuations. Raw-body and framed QA offsets checked.','']
    with gzip.open(OUT/'review_40.after.jsonl.gz','wt') as f:
        for old in before:
            row=generate(old['scenario'],old['seed'],beat_budget=6,continuations='expanded')
            replay(row);annotation=annotate(row);qa=questions(row,4);beat_qa=beat_questions(row)
            start=row['presentation']['body_offset']
            assert row['presented_story'][start:start+len(row['story'])]==row['story']
            for q in qa+beat_qa:
                for e in q['evidence']:assert row['story'][e['start']:e['end']]==e['text']
                for e in presentation_evidence(row,q):assert row['presented_story'][e['start']:e['end']]==e['text']
            for trace in row['trace']:
                for step in trace['word_trace']:
                    assert abs(sum(c['probability'] for c in step['annotated_choices'])-1)<1e-9
            memory=row['final_world']['narrative']['beats']
            selected=[b['id'] for b in memory['history']]
            info=dict(scenario=row['scenario'],seed=row['seed'],
                before_words=len(old['story'].split()),after_words=len(row['story'].split()),
                before_title=old['title'],after_title=row['title'],
                body_changed=old['story']!=row['story'],
                event_sequence_changed=[e['frame']['kind'] for e in old['final_world']['history']]!=
                    [e['frame']['kind'] for e in row['final_world']['history']],
                completed='ended' in row['final_world']['flags'],
                beats=selected,qa_count=len(qa),beat_qa_count=len(beat_qa),replay=True,annotation=True,
                qa_offsets=True,joint_probabilities=True)
            summaries.append(info)
            f.write(json.dumps(dict(row=row,qa=qa,beat_qa=beat_qa,annotations=annotation,summary=info),separators=(',',':'))+'\n')
            samples.extend([f"## {row['scenario']}, seed {row['seed']}",'',row['presented_story'],'',
                'Optional choices: '+', '.join(selected)+'.',''])
            for q in qa:samples.extend(['Q: '+q['question'],'A: '+q['answer'],''])
    assert code==manifest(),'source changed during held-out run; rerun before interpreting comparison'
    summary=dict(started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),
        manifest=code,before_source='Earlier read-only audit snapshot; prior code was not separately frozen.',
        comparison_scope='Final integrated fixes versus earlier held-out snapshot; not an isolated ablation.',
        samples=40,worlds=20,seeds=[701,907],beat_budget=6,continuations='expanded',
        changed_bodies=sum(x['body_changed'] for x in summaries),
        changed_titles=sum(x['before_title']!=x['after_title'] for x in summaries),
        changed_event_sequences=sum(x['event_sequence_changed'] for x in summaries),
        completed=sum(x['completed'] for x in summaries),
        total_qa=sum(x['qa_count'] for x in summaries),
        total_beat_qa=sum(x['beat_qa_count'] for x in summaries),
        selected_beats=dict(Counter(b for x in summaries for b in x['beats'])),rows=summaries)
    (OUT/'review_40.summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'review_40.samples.md').write_text('\n'.join(samples)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in {'manifest','rows'}}))


if __name__=='__main__':main()
