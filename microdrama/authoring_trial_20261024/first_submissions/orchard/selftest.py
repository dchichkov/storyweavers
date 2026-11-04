"""Focused mechanics checks in addition to the shared evaluator."""
from copy import deepcopy
from microdrama.engine import StoryError, compose, Memeplex
from .pack import build_world, dramas, shelter


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
    print('Orchard selftests passed: blocked read rollback, unembedded content, two shelter bindings, eight outcomes.')

if __name__=='__main__': main()
