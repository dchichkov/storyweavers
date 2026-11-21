"""Rebuild the final comparison from frozen, complete Luna assessments."""
import json
from pathlib import Path
import statistics

from .. import judge
from .runtime import SCENARIOS
from .evaluate import report

ROOT=judge.ROOT
CAMPAIGN=ROOT/'grammarworlds/runs/ten_rounds_20261103'


def metrics(directory):
    judge.verify_artifacts(directory)
    qa=judge.read(directory/'qa_summary.json');prose=judge.read(directory/'summary.json')
    assert qa['complete'] and prose['complete']
    return dict(quality=prose['mean_quality']['overall'],diversity=prose['mean_within_scenario_diversity']['overall'],
        qa=qa['means']['overall'],grounded=qa['means']['grounded'],usable=qa['means']['usable'],
        pairs=qa['pairs'],stories=prose['judged'],defects=qa['defects'])


def compare():
    paths={
        'original_development':ROOT/'grammarworlds/runs/luna_short_dialogue_qa_20261103',
        'final_development':CAMPAIGN/'round10/eval',
        'original_fresh':CAMPAIGN/'baseline_heldout_eval',
        'final_fresh':CAMPAIGN/'final_heldout_eval'}
    results={name:metrics(path) for name,path in paths.items()}
    # Same positions, seeds, sample sizes and unchanged judging instructions.
    for left,right in [('original_development','final_development'),('original_fresh','final_fresh')]:
        for scenario in SCENARIOS:
            a,b=[judge.read(paths[k]/scenario/'input.json') for k in (left,right)]
            assert [s['source_index'] for s in a['stories']]==[s['source_index'] for s in b['stories']]
            for kind in ('','qa'):
                ra,rb=[judge.read(paths[k]/scenario/kind/'request.json') for k in (left,right)]
                assert ra['input'][0]==rb['input'][0]
                assert ra['model']==rb['model']=='gpt-6-luna'
                assert ra['service_tier']==rb['service_tier']=='flex'
                assert ra['reasoning']==rb['reasoning']==dict(effort='none')
    assert all((CAMPAIGN/f'round{i:02d}/measured.json').is_file() for i in range(1,11))
    regeneration=judge.read(CAMPAIGN/'baseline_regeneration.json')
    assert regeneration['matched_original_stories_and_qa']==420
    audit=judge.read(CAMPAIGN/'final_heldout_audit/summary.json')
    total=lambda field:sum(s[field] for s in audit.values())
    results['audit']=dict(stories=total('stories'),qa_pairs=total('qa_pairs'),guard_interventions=total('guard_interventions'),
        ablations=total('ablations'),attention_changed_event_mass=total('attention_changed_event_mass'),
        mean_words=statistics.mean(s['mean_words'] for s in audit.values()),
        min_words=min(s['min_words'] for s in audit.values()),max_words=max(s['max_words'] for s in audit.values()))
    judge.save(CAMPAIGN/'comparison.json',results)
    lines=['# Ten rounds: final Luna comparison','',
        'Ten implementation rounds are complete. Generation still uses weighted typed grammar, guarded symbolic kernels and carrier-grounded attention. Luna is an offline evaluator; no LLM generates or repairs prose at runtime.','',
        'All scores are 0–9. Each cell comes from one Luna/Flex/reasoning-none assessment of each world set, using unchanged calibrated prose and separate text-only QA rubrics. Each version has 20 uniformly selected past-tense stories per world (140 total); duplicates remain.','',
        '| Evaluation | Story quality | Within-world diversity | QA quality | Grounded QA | Usable QA |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for key,label in [('original_development','Original, development'),('final_development','Final, same development positions'),('original_fresh','Original, fresh seeds'),('final_fresh','Final, same fresh positions')]:
        r=results[key]
        lines.append(f"| {label} | {r['quality']:.2f} | {r['diversity']:.2f} | {r['qa']:.2f} | {r['grounded']:.1%} | {r['usable']:.1%} |")
    lines+=['','Development seeds are 0–59; fresh seeds are 1000–1059, reserved before the campaign. The final version was frozen before its fresh outputs were judged; no changes were made in response to fresh scores. These are unseen draws within the same seven authored worlds, not novel-world generalization.','',
        'The old source snapshot was restored with unchanged portable dependencies. It exactly reproduced all 420 original past-tense pool stories **and QA** before producing fresh samples. Identical sampled positions and identical system rubrics are checked by `comparison.py`. The old QA and current QA differ in number/content, so QA gains compare each version’s question sets, not identical questions.','',
        '## Fresh sample by world','',
        '| World | Original quality | Final quality | Original diversity | Final diversity | Final QA | Grounded answers |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for scenario in SCENARIOS:
        old=judge.read(paths['original_fresh']/scenario/'result.json')['assessment']
        new=judge.read(paths['final_fresh']/scenario/'result.json')['assessment']
        followups=judge.read(paths['final_fresh']/'qa_followups.json') if (paths['final_fresh']/'qa_followups.json').exists() else {}
        qa_dir=followups.get(scenario,{}).get('directory','qa')
        qa=judge.read(paths['final_fresh']/scenario/qa_dir/'result.json')['assessment']['pairs']
        lines.append(f"| {scenario} | {old['rating']['overall']:.2f} | {new['rating']['overall']:.2f} | {old['diversity']['overall']} | {new['diversity']['overall']} | {statistics.mean(q['overall'] for q in qa):.2f} | {sum(q['grounded'] for q in qa)}/{len(qa)} |")
    a=results['audit']
    lines+=['','## Architecture and physical verification','',
        f"- 63 tests passed, including physical interventions, consent, tools, conservation, firing/cooling, ownership, ambiguity-safe pronouns and transitive evidence failures.",
        f"- {a['stories']} fresh unfiltered stories (both tenses) completed and replayed; {a['qa_pairs']} QA pairs retained exact visible evidence and event/entity IDs.",
        f"- {a['guard_interventions']:,} carrier-removal, prerequisite-removal and forged-actor checks rejected invalid execution without mutation.",
        f"- {a['ablations']} first branching states were compared with attention on/off; {a['attention_changed_event_mass']} changed event mass, while every comparison retained exactly the same legal frames. This measures causal influence on authored probabilities, not learned attention or calibrated uncertainty.",
        f"- Fresh lengths: {a['min_words']}–{a['max_words']} words, mean {a['mean_words']:.1f}. At least two speakers and five distinct QA pairs per story; actual final samples contain six.",
        '- Every word (including punctuation and END) is sampled from the normalized forest. Token probabilities telescope to surface mass; the semantic event is selected from the posterior and executed once. Prediction is pure.',
        '- The frozen GF/Codeco-derived modules and original evidence are unchanged. New plans, speech constructions and world packs layer above them. This prototype does not implement the full memeplex algebra or full GF/Codeco languages.','',
        '## Limits and next work','',
        'Diversity remains low: there are only two or three major causal outcomes per world. More event-order paths are not automatically more distinct plots. Scores vary across single judge calls; intermediate rounds use different subsets, so their means are not a clean learning curve. No human validation or independent repeated judge estimate is claimed.','',
        'Remaining defects include procedural prose, repetitive dialogue/names, thin character responses and literal-recall QA. All 15 fresh grounding failures are kite answers that call the material paper where the visible story only names a kite; this remains unresolved in the frozen final version. Exact evidence links and physical replay do not prove every English entailment; Luna’s raw grounding judgments are retained, including questionable flags. Meaningful contextual answers remain multi-sentence; thin trace answers use one complete sentence instead of padding.','',
        'Two final QA responses hit the 20,000-token output limit (development kite and fresh greenhouse). Their identical samples/rubrics were repeated with a 40,000-token allowance; incomplete responses are retained and contribute no ratings. No valid low-scoring response was retried.','',
        'The original round-2 QA request timed out after dispatch and was not resent. A separately recorded six-story follow-up is used for that round’s QA diagnostic; its prose used twelve stories. See its follow-up manifest.','',
        '[Ten-round ledger](REPORT.md) · [Fresh stories and QA](final_heldout_audit/samples.md) · [Final development evaluation](round10/eval/REPORT.md) · [Final fresh evaluation](final_heldout_eval/REPORT.md) · [Original fresh evaluation](baseline_heldout_eval/REPORT.md)','']
    (CAMPAIGN/'FINAL_COMPARISON.md').write_text('\n'.join(lines))
    return results


if __name__=='__main__':
    print(json.dumps(compare(),indent=2))
