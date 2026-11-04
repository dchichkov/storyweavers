from copy import deepcopy
from microdrama.engine import StoryError, compose, digest, Memeplex, World
from . import pack


def run():
    w=pack.build_world(dict(access=False,cooperate=True,distraction=False))
    before=deepcopy(w.state)
    try:
        pack.practice(w,'ida','sluice','blocked')
    except StoryError:
        pass
    else:
        raise AssertionError('Unlearned action admitted')
    assert w.state==before and not w.history
    # Knowledge cannot authorize an unborrowed physical tool.
    w=pack.build_world(dict(access=True,cooperate=True,distraction=False))
    w.act('lesson','read',['ida'],lambda t:t.absorb('diagram','ida'))
    before=deepcopy(w.state)
    history=deepcopy(w.history)
    try:
        pack.practice(w,'ida','sluice','unborrowed')
    except StoryError as exc:
        assert 'temporary use' in str(exc)
    else:
        raise AssertionError('Unborrowed lever admitted')
    assert w.state==before and w.history==history
    for actor in ('ida','ren'):
        w=pack.build_world(dict(access=True,cooperate=True,distraction=False))
        w.act('lesson','read',[actor],lambda t:t.absorb('diagram',actor))
        w.act('loan','borrow',['osk',actor],lambda t:t.set('lever.user',actor))
        pack.practice(w,actor,'sluice','test')
        assert w.state['sluice.open'] and w.state['sluice.tested']
    # Same mechanism implementation binds another object and learner.
    w=pack.build_world(dict(access=True,cooperate=True,distraction=False))
    w.act('lesson','read',['ida'],lambda t:t.absorb('diagram','ida'))
    w.act('loan','borrow',['osk','ida'],lambda t:t.set('lever.user','ida'))
    pack.practice(w,'ida','gate','test')
    assert w.state['ida.applied'] and w.state['gate.open']
    # Binding Ren to the heavy mechanism must never attribute his action to Ida.
    w=pack.build_world(dict(access=True,cooperate=True,distraction=False))
    w.act('lesson','read',['ren'],lambda t:t.absorb('diagram','ren'))
    w.act('loan','borrow',['osk','ren'],lambda t:t.set('lever.user','ren'))
    pack.practice(w,'ren','gate','test')
    assert w.state['ren.applied'] and not w.state['ida.applied']
    assert w.state['gate.operator']=='ren' and w.state['gate.open']
    assert w.state['gate.effort']==8 and w.state['ren.observed_success']
    # Hold all three input settings fixed; change only physical initial load.
    config=dict(access=True,cooperate=True,distraction=False)
    base=pack.build_world(config)
    compose(base,pack.dramas(),None,0)
    for target in ('gate','sluice'):
        original=pack.build_world(config)
        initial=deepcopy(original.initial)
        initial[target+'.load']=20
        heavy=World(original.entities,original.locations,initial,original.validator)
        episodes,_=compose(heavy,pack.dramas(),None,0)
        assert not heavy.state[target+'.open'] and heavy.state[target+'.tested']
        assert heavy.state[target+'.effort'] < heavy.state[target+'.load']
        assert heavy.state['ida.meme.lift']==1 and heavy.state['osk.willing']
        if target=='gate':
            assert heavy.state['valley.outcome']!='grain_saved'
            assert base.state['valley.outcome']=='grain_saved'
        text=' '.join(p['text'] for ep in episodes for p in pack.render(ep))
        assert 'could not overcome' in text or 'resistance exceeded' in text
        qa=pack.questions(heavy,episodes)
        if target=='sluice':
            assert 'failed physical trial' in qa[4]['answer']
        from pathlib import Path
        Path(__file__).with_name('output').joinpath('heavy_'+target+'.txt').write_text(text+'\n')
    before=digest(w.state)
    unused=Memeplex.atom('lift')+Memeplex.atom('brace')
    assert unused.terms and digest(w.state)==before
    for access in (True,False):
        for cooperate in (True,False):
            for distraction in (True,False):
                w=pack.build_world(dict(access=access,cooperate=cooperate,distraction=distraction))
                eps,_=compose(w,pack.dramas(),None,0)
                assert len(eps)==7
                assert w.state['gate.open']==(access and cooperate and not distraction)
                assert not w.state['valley.blamed_ren'] and w.state['gate.pin_bent']
                assert w.state['lever.owner']=='osk' and w.state['lever.user']=='osk'
    print('Floodgate selftest passed: blocked action, two learner bindings, two objects, eight outcomes.')

if __name__=='__main__': run()
