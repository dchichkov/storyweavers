"""Focused mechanics checks in addition to the shared evaluator."""
from copy import deepcopy
from microdrama.engine import StoryError, compose, Memeplex, World
from .pack import build_world, dramas, shelter, render, questions


def main():
    w=build_world(dict(access=False,cooperate=True,distraction=False))
    before=deepcopy((w.state,w.history,w.last_writer))
    def blocked(tx):
        tx.set('fork.user','mara')
        tx.absorb('notebook','mara')
    try:
        w.act('test','inaccessible reading',['mara'],blocked)
        raise AssertionError('Blocked read succeeded')
    except StoryError:
        pass
    assert (w.state,w.history,w.last_writer)==before
    # An unembedded expression cannot change any carrier.
    ignored=Memeplex.atom('air_gap')+Memeplex.atom('anchor_edges')
    assert (w.state,w.history,w.last_writer)==before
    for target in ('trial','rows'):
        w=build_world(dict(access=True,cooperate=True,distraction=False))
        def ready(tx):
            tx.absorb('notebook','mara')
            tx.set('fork.user','mara')
            if target=='rows': shelter(tx,'mara','trial',1)
        w.act('test','prepare',['mara'],ready)
        w.act('test','apply shared shelter practice',['mara'],lambda tx:shelter(tx,'mara',target,1 if target=='trial' else 6))
        assert w.state[target+'.protected']==(1 if target=='trial' else 6)
        assert w.state['fork.owner']=='ivo'
    outcomes=set()
    for access in (False,True):
        for cooperate in (False,True):
            for distraction in (False,True):
                w=build_world(dict(access=access,cooperate=cooperate,distraction=distraction))
                compose(w,dramas(),None)
                assert w.state['fork.returned'] and w.state['fork.owner']=='ivo'
                assert w.state['trial.cause']=='frost' and w.state['mara.belief']=='frost'
                outcomes.add(w.state['valley.outcome'])
    assert len(outcomes)==3
    # Same advertised inputs; vary only an initial physical cold condition.
    base=build_world(dict(access=True,cooperate=True,distraction=False))
    for key in ('valley.trial_cold','valley.night_cold'):
        initial=deepcopy(base.initial)
        initial[key]=3
        cold=World(base.entities,base.locations,initial,base.validator)
        episodes,_=compose(cold,dramas(),None)
        assert cold.state['rows.surviving']==0
        assert cold.state['mara.meme.air_gap']==1
        if key=='valley.trial_cold':
            assert cold.state['trial.protected']==1 and not cold.state['trial.retains_warmth']
            assert cold.state['rows.protected']==0
            assert 'sound construction' in questions(cold,episodes)[3]['answer']
            deployment=render(episodes[5])[0]['text']
            assert 'stood properly' in deployment and 'too little insulation' in deployment
            assert 'did not keep it raised' not in deployment
        else:
            assert cold.state['trial.retains_warmth'] and cold.state['rows.protected']==6
            assert 'more severe overnight cold' in questions(cold,episodes)[5]['answer']
        assert 'cold' in render(episodes[3 if key=='valley.trial_cold' else 6])[0]['text']
    print('Orchard selftests passed: blocked read rollback, unembedded content, two shelter bindings, eight outcomes.')

if __name__=='__main__': main()
