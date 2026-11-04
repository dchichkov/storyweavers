"""Independent post-submission checks; separate from the frozen evaluator."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from microdrama.engine import World, StoryError
from .evaluate import ROOT, produce, validate


def main():
    manifest = json.loads((ROOT/'trial.json').read_text())
    for path, expected in manifest['fixed_inputs_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
    config = dict(access=True, cooperate=True, distraction=False)
    cases = [('floodgate','gate.load',20,'grain_lost'),
             ('floodgate','sluice.load',20,'grain_saved'),
             ('orchard','valley.trial_cold',3,'lost blossoms'),
             ('orchard','valley.night_cold',3,'lost blossoms')]
    checked = []
    output = ROOT/'parent_evidence'
    output.mkdir(exist_ok=True)
    for name, key, value, expected in cases:
        pack = importlib.import_module(f'{__package__}.{name}.pack')
        baseline = produce(pack,config,0)
        def build(cfg, pack=pack, key=key, value=value):
            w = pack.build_world(cfg)
            initial = deepcopy(w.initial)
            initial[key] = value
            return World(w.entities, w.locations, initial, w.validator)
        proxy = SimpleNamespace(TITLE=pack.TITLE, build_world=build, dramas=pack.dramas,
                                render=pack.render, questions=pack.questions)
        row = produce(proxy,config,0)
        validate(proxy,row)
        assert row['config'] == baseline['config']
        assert row['final']['valley.outcome'] == expected
        assert row['final'] != baseline['final']
        if name == 'floodgate':
            target = key.split('.')[0]
            assert row['final'][target+'.tested'] and not row['final'][target+'.open']
            assert row['final'][target+'.effort'] < row['final'][key]
        elif key == 'valley.trial_cold':
            assert row['final']['trial.air_gap'] and row['final']['trial.anchored']
            assert not row['final']['trial.retains_warmth']
        else:
            assert row['final']['rows.protected'] == 6 and row['final']['rows.surviving'] == 0
        slug=name+'_'+key.replace('.','_')
        (output/(slug+'.json')).write_text(json.dumps(row,indent=2,ensure_ascii=False)+'\n')
        (output/(slug+'.txt')).write_text(row['title']+'\n\n'+'\n\n'.join(p['text'] for p in row['paragraphs'])+'\n')
        checked.append({'candidate':name,'intervention':{key:value},'inputs':config,
                        'baseline_outcome':baseline['final']['valley.outcome'],'outcome':expected})
    flood = importlib.import_module(f'{__package__}.floodgate.pack')
    no_loan = flood.build_world(config)
    no_loan.act('parent','read',['ida'],lambda t:t.absorb('diagram','ida'))
    before = deepcopy((no_loan.state,no_loan.history,no_loan.last_writer))
    try:
        flood.practice(no_loan,'ida','sluice','parent_trial')
    except StoryError:
        pass
    else:
        raise AssertionError('Unborrowed lever was used')
    assert (no_loan.state,no_loan.history,no_loan.last_writer) == before
    w = flood.build_world(config)
    def prepare(t):
        t.set('lever.user','ren')
        t.absorb('diagram','ren')
    w.act('parent','lend and read',['osk','ren'],prepare)
    flood.practice(w,'ren','gate','parent_trial')
    assert w.state['ren.applied'] and not w.state['ida.applied']
    assert w.state['gate.operator'] == 'ren'
    # Check that the diagnosis genuinely catches the original role defect.
    initial_flood = importlib.import_module(f'{__package__}.first_submissions.floodgate.pack')
    old = initial_flood.build_world(config)
    old.act('parent','lend and read',['osk','ren'],prepare)
    initial_flood.practice(old,'ren','gate','parent_trial')
    assert old.state['ida.applied'], 'Original defect was not reproduced'
    report = {'fixed_inputs_unchanged':True,'physical_counterfactuals':checked,
              'bound_actor_preserved':True,'original_role_defect_reproduced':True,
              'unborrowed_tool_rejected_atomically':True,
              'parent_edited_candidate_code':False,
              'limits':'Finite-world review; not proof of arbitrary module composition or English entailment.'}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
