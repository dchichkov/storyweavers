"""Typed rescue scenes: personal goal, negotiated strategy, material consequence."""
from .surface import scene, claim
from ..portable.nouns import pronoun


def rescue(w,f,g):
    n,r,v,s,pp=g.n,g.ref,g.v,g.s,g.pp
    hero=w.entities['hero'].noun; helper=w.entities['helper'].noun; animal=w.entities['target'].noun
    if f.kind=='notice':
        return scene(g.join(s('hero',v('want',v('eat',r('bread')))),
                            s(r('target',first=True),g.adv(v('shiver'),pp('on',n('ledge','high',det='a')))),'but'),
                     g.line('hero',s(r('target'),v('need',n('help',det='bare')),tense='present'),listener='helper'),qa=[
            claim('problem','what','What interrupted the meal?',f'A {animal} was shivering on a high ledge. {hero} wanted to eat the bread.','hero','target','bread'),
            claim('goal','who','Who noticed that the animal needed help?',f'{hero} said the {animal} needed help.','hero','target')])
    if f.kind=='choose_ladder':
        return scene(g.line('helper',g.me(g.can(v('climb',r('tool')))),listener='hero'),
                     g.line('hero',g.me(g.can(v('steady',r('tool')))),listener='helper'),qa=[
            claim('strategy','how','How did they divide the rescue work?',f'{helper} would climb the ladder. {hero} would steady it.','hero','helper','tool')])
    if f.kind=='choose_basket':
        return scene(g.line('helper',g.me(g.can(v('lower',r('basket')))),listener='hero'),
                     g.line('hero',g.me(g.can(v('share',r('bread')))),listener='helper'),qa=[
            claim('strategy','how','What did they offer to do?',f'{helper} offered to lower a basket. {hero} offered to share the bread.','hero','helper','basket','bread')])
    if f.kind=='prepare_ladder':
        return scene(g.sequence('hero',g.adv(v('fetch',r('tool')),pp('from',n('shed'))),v('steady',r('tool'))),qa=[
            claim('tool','where','Where did the ladder come from?',f'{hero} fetched the ladder from the shed.','hero','tool')])
    if f.kind=='prepare_basket':
        return None  # The helper fetches the basket before the child can fill it.
    if f.kind=='load_basket':
        return scene(s('hero',g.adv(v('put',r('bread')),pp('in',r('basket')))),qa=[
            claim('tool','where','Where did the bread go?',f'{hero} put the bread in the basket.','hero','bread','basket')])
    if f.kind=='place_basket':
        return scene(g.sequence('helper',g.adv(v('carry',r('basket')),pp('to',n('window'))),
                     g.adv(v('lower',r('basket')),pp('to',n('ledge')),pp('with',r('rope')))))
    if f.kind=='rescue_lift':
        return scene(g.sequence('helper',v('climb',r('tool')),g.adv(v('lift',r('target')),'down')),qa=[
            claim('solution','how','How did the animal get down?',f'{helper} climbed the ladder and lifted the {animal} down. {hero} steadied the ladder.','hero','helper','target','tool',supports=('tool',))])
    if f.kind=='basket_wait':
        return scene(g.join(s('hero',v('wait')),s(r('target'),g.be('frightened')),'because'),qa=[
            claim('patience','why',f'Why did {hero} wait?',f'The {animal} was frightened. {hero} waited.','hero','target')])
    if f.kind=='basket_enter':
        return scene(g.sequence('target',v('enter',r('basket')),v('eat',r('bread'))),qa=[
            claim('choice','what',f'What did the {animal} do in the basket?',f'The {animal} ate the bread. {hero} had put the bread there.','hero','target','bread','basket',supports=('tool',))])
    if f.kind=='basket_lower':
        return scene(s('helper',g.adv(v('lower',r('basket')),pp('to',n('garden')),pp('with',r('rope')))),qa=[
            claim('solution','how','How did the animal get down?',f'{helper} lowered the basket to the garden with a rope. The {animal} had entered the basket and eaten the bread.','helper','target','basket','rope',supports=('choice',))])
    if f.kind=='shelter':
        return scene(g.sequence('hero',g.adv(v('carry',r('target')),pp('into',n('cottage'))),
                              g.adv(v('wrap',r('target')),pp('in',r('blanket',adjectives=('warm',))))),qa=[
            claim('care','what',f'What did {hero} do after the rescue?',f'{hero} carried the {animal} inside the cottage and wrapped it in a warm blanket.','hero','target','blanket')])
    if f.kind=='ending':
        rest=s(r('target'),g.adv(v('rest'),pp('in',r('blanket',adjectives=('warm',)))))
        if 'basket_plan' in w.flags:
            return scene(g.join(s('hero',g.be('hungry')),rest,'but'),qa=[
                claim('outcome','why',f'Why was {hero} hungry at the end?',f'The {animal} ate the bread that {hero} had meant to eat. It rested in the warm blanket after the rescue.','hero','target','bread','blanket',supports=('problem','choice'))])
        return scene(rest,qa=[claim('outcome','what_next','Where did the rescued animal rest?',f'The {animal} rested in the warm blanket. {helper} had lifted it down while {hero} steadied the ladder.','hero','helper','target','blanket',supports=('solution',))])
    raise ValueError(f.kind)
