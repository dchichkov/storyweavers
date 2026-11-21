"""A small material failure can change the child's goal, not only the wording."""
from .surface import scene,claim


def kite(w,f,g):
    n,r,v,s,pp=g.n,g.ref,g.v,g.s,g.pp
    h=w.entities['hero'].noun;p=w.entities['helper'].noun
    if f.kind=='notice':
        return scene(g.join(s('hero',v('want',v('fly',r('target',first=True)))),s(r('target'),g.be('torn')),'but'),
            g.say_intent('hero', 'want', v('repair', r('target')), listener='helper'),qa=[
                claim('goal','who','Who wanted to fly the kite?',f'{h} wanted to fly the kite. The kite was torn.','hero','target'),
                claim('problem','what','What stopped the kite from flying?', 'The kite was torn.','target')])
    if f.kind=='inspect':
        if 'fragile' in w.entities['target'].state:
            return scene(g.line('helper',s(n('paper'),g.be('thin'),tense='present'),listener='hero'),qa=[
                claim('material','what',f'What did {p} notice about the paper?',f'{p} said the paper was thin.','helper','target')])
        return scene(g.line('helper',s(r('boat'),v('need',n('sail',det='a')),tense='present'),listener='hero'),qa=[
            claim('material','what',f'What did {p} say the boat needed?',f'{p} said the boat needed a sail.','helper','boat')])
    if f.kind=='choose_patch':
        return scene(g.offer('hero', v('cover', n('tear')), listener='helper'))
    if f.kind=='choose_sail':
        return scene(g.say_intent('hero', 'want', v('make', n('sail', det='a')), listener='helper'),qa=[
            claim('decision','what',f'What new plan did {h} choose for the torn kite?',f'{h} wanted to make a sail. The kite had been torn.','hero','target',supports=('problem',))])
    if f.kind=='fetch_tape':return None
    if f.kind=='mend':
        return scene(g.using('hero',v('cover',n('tear')),r('tool')),qa=[
            claim('patch','how',f'How did {h} mend the kite?',f'{h} covered the tear with tape.','hero','target','tool')])
    if f.kind=='test_flight':
        if 'fragile' in w.entities['target'].state:
            return scene(g.join(s('hero',g.adv(v('launch',r('target')),pp('in',n('wind')))),
                                s(n('paper'),g.adv(v('tear'),'again')),'but'),qa=[
                claim('test','what', 'What happened when the patched kite was launched?',f'The paper tore again in the wind. {p} had said the paper was thin.','hero','target',supports=('material',))])
        return scene(s('hero',g.adv(v('launch',r('target')),pp('in',n('wind')))),qa=[
            claim('test','what', 'What happened after the kite was patched?',f'{h} launched it in the wind. The tear had been covered with tape.','hero','target','tool',supports=('patch',))])
    if f.kind=='reconsider':
        return scene(g.say_intent('hero', 'want', v('make', n('sail', det='a')), listener='helper'),qa=[
            claim('decision','why',f'Why did {h} change plans?',f'{h} decided to make a sail because the patched kite tore again.','hero','target',supports=('test',))])
    if f.kind=='fetch_scissors':return None
    if f.kind=='cut_sail':
        return scene(s('helper',g.adv(v('cut',n('sail','small',det='a')),pp('from',r('target')),pp('with',r('scissors')))),qa=[
            claim('conversion','how','How did the kite become something useful?',f'{p} cut a small sail from the kite with scissors. The kite had been torn.','helper','target','scissors',supports=('problem',))])
    if f.kind=='attach_sail':
        return scene(s('hero',g.adv(v('tie',r('target')),pp('to',r('boat')),pp('with',r('string')))),qa=[
            claim('attach','how',f'How did {h} attach the sail?',f'{h} tied the sail to the boat with string.','hero','target','boat','string')])
    if f.kind=='launch_boat':
        return scene(s('hero',g.adv(v('set',r('boat')),pp('on',n('pond')))),qa=[
            claim('launch','where',f'Where did {h} put the boat?',f'{h} set the boat on the pond.','hero','boat')])
    if f.kind=='ending':
        if 'flying' in w.entities['target'].state:
            return scene(s(g.both(r('hero'),r('helper')),v('watch',r('target',adjectives=('patched',)))),
                         s(r('target'),g.adv(v('dance'),pp('above',n('meadow')))),qa=[
                claim('outcome','what_next','What did they watch at the end?',f'{h} and {p} watched the patched kite dancing above the meadow. The tape had covered its tear.','hero','helper','target','tool',supports=('patch',)),
                claim('place','where','Where did the repaired kite fly?','The kite danced above the meadow.','target')])
        return scene(s(g.both(r('hero'),r('helper')),v('watch',r('boat'))),
                     s(r('boat'),g.adv(v('sail'),pp('across',n('pond')))),qa=[
            claim('outcome','what_next','What happened to the torn kite at the end?',f'Its paper became the sail on a boat. {h} and {p} watched the boat sail across the pond.','hero','helper','target','boat',supports=('conversion','attach')),
            claim('place','where','Where did the boat sail?',f'The boat sailed on the pond. Its sail was cut from the kite.','boat','target',supports=('conversion','launch'))])
    raise ValueError(f.kind)
