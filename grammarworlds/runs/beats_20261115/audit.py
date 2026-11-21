"""Reproduce the final structural audit; this is not a literary judge."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import gzip
import hashlib
import json
import math
from pathlib import Path

from grammarworlds.plot_bank import BANK
from grammarworlds.storytelling.runtime import generate,replay
from grammarworlds.storytelling.qa import questions
from grammarworlds.story_memory import annotate
from grammarworlds.beat_qa import presentation_evidence
from grammarworlds.beat_annotation_export import replay_document
from grammarworlds.plot_continuation import catalogue,run

OUT=Path(__file__).parent/'final_audit'


def check(row,counts):
    assert replay(row)
    doc=annotate(row)
    replay_document(doc)
    assert doc['text']==row['story']
    for trace in row['trace']:
        for step in trace['word_trace']:
            counts['body_word_distributions']+=1
            joint=defaultdict(float)
            for c in step['annotated_choices']:
                assert c['probability']>0 and c['attributes'] in trace['attribute_table']
                joint[c['word']]+=c['probability']
            assert math.isclose(sum(joint.values()),1.,abs_tol=1e-9)
            assert math.isclose(sum(c['probability'] for c in step['selected_attributes']),1.,abs_tol=1e-9)
            assert set(joint)=={c['word'] for c in step['choices']}
            for c in step['choices']:assert math.isclose(c['probability'],joint[c['word']],abs_tol=1e-9)
    memory=row['final_world']['narrative']['beats']
    assert memory['used']<=memory['budget']
    for beat in memory['history']:
        assert row['final_world']['entities'][beat['experiencer']]['kind']=='person'
        assert beat['preceding_event']<beat['event']
        if beat.get('discovery_event'):assert beat['discovery_event']<beat['event']
    qa=questions(row,12);counts['qa_pairs']+=len(qa)
    for q in qa:
        assert set(q['entity_ids'])<=row['final_world']['entities'].keys()
        for item in q['evidence']:assert row['story'][item['start']:item['end']]==item['text']
        for item in presentation_evidence(row,q):
            assert row.get('presented_story',row['story'])[item['start']:item['end']]==item['text']
    if row.get('presentation'):
        p=row['presentation'];start=p['body_offset']
        assert row['presented_story'][start:start+p['body_length']]==row['story']
        for role in ('title','opening','closing'):
            assert math.isclose(sum(c['probability'] for c in p[role]['alternatives']),1.,abs_tol=1e-9)
            for step in p[role]['trace']:
                counts['framing_word_distributions']+=1
                for key in ('choices','annotated_choices','selected_attributes'):
                    assert math.isclose(sum(c['probability'] for c in step[key]),1.,abs_tol=1e-9)
    counts['verified_rows']+=1
    return doc,qa


def main():
    OUT.mkdir(exist_ok=True)
    counts=Counter();samples=[];lines=['# Final broad audit samples','',
        'Seeds1103/1307 were not used for the implementation review. Structural checks are not literary scores.','']
    started=datetime.now(timezone.utc).isoformat()
    with gzip.open(OUT/'source_samples.jsonl.gz','wt') as sink:
        for scenario in BANK:
            for seed,tense in ((1103,'past'),(1307,'present')):
                for budget in (2,6):
                    row=generate(scenario,seed,beat_budget=budget,tense=tense,continuations='expanded')
                    doc,qa=check(row,counts)
                    memory=row['final_world']['narrative']['beats']
                    info=dict(scenario=scenario,seed=seed,tense=tense,budget=budget,
                              used=memory['used'],choices=[b['id'] for b in memory['history']],
                              words=len(row['story'].split()))
                    samples.append(info)
                    sink.write(json.dumps(dict(row=row,annotations=doc,qa=qa,summary=info),separators=(',',':'))+'\n')
                    lines.extend([f'## {scenario}: seed{seed}, {tense}, budget{budget}','',row['presented_story'],'',
                                  'Selected beats: '+(', '.join(info['choices']) or 'none')+'.',''])
                    for q in qa:lines.extend(['Q: '+q['question'],'A: '+q['answer'],''])
            print(scenario,flush=True)
    docs=[annotate(generate(s,3006)) for s in BANK]
    pool=catalogue(docs);joined=[]
    for plan,seed,budget in [('changed_approach',1103,2),('changed_approach',1307,6),('adapt_gift',1103,6)]:
        result=run(pool,plan,seed=seed,beat_budget=budget)
        assert result['summary']['success'],result['summary']
        used=[]
        for row in result['rows']:
            check(row,counts);used.append(row['final_world']['narrative']['beats']['used'])
        assert used==sorted(used) and used[-1]<=budget
        for decision in result['decisions']:
            assert math.isclose(sum(c['probability'] for c in decision['candidates']),1.,abs_tol=1e-9)
        joined.append(dict(plan=plan,seed=seed,budget=budget,used=used,summary=result['summary']))
        with gzip.open(OUT/f'joined_{plan}_{seed}.json.gz','wt') as f:json.dump(result,f,separators=(',',':'))
        lines.extend([f'## Joined {plan}: seed{seed}','','Sources: '+', '.join(result['summary']['sources']),'',result['story'],''])
        print(plan,seed,flush=True)
    summary=dict(started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),worlds=len(BANK),
                 standalone_samples=len(samples),counts=dict(counts),samples=samples,joined=joined,
                 quality_score_claimed=False,leakage_allowed=True)
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'samples.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(counts=counts,joined=len(joined))))


if __name__=='__main__':main()
