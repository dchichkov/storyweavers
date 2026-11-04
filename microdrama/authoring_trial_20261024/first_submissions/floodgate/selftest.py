from copy import deepcopy
from microdrama.engine import StoryError, compose, digest, Memeplex
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
    for actor in ('ida','ren'):
        w=pack.build_world(dict(access=True,cooperate=True,distraction=False))
        w.act('lesson','read',[actor],lambda t:t.absorb('diagram',actor))
        pack.practice(w,actor,'sluice','test')
        assert w.state['sluice.open'] and w.state['sluice.tested']
    # Same mechanism implementation binds another object and learner.
    w=pack.build_world(dict(access=True,cooperate=True,distraction=False))
    w.act('lesson','read',['ida'],lambda t:t.absorb('diagram','ida'))
    pack.practice(w,'ida','gate','test')
    assert w.state['ida.applied'] and not w.state['gate.open']
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
