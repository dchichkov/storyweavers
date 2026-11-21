"""The door can open without pretending a missing original key has been found."""
from .surface import scene,claim
from ..portable.nouns import pronoun


def key(w,f,g):
    n,r,v,s,pp=g.n,g.ref,g.v,g.s,g.pp
    h=w.entities['hero'].noun;p=w.entities['helper'].noun
    if f.kind=='notice':
        return scene(g.join(s('hero',v('want',g.adv(v('read',r('storybook',first=True)),'inside'))),s(r('door'),g.be('locked')),'but'),
                     s(r('target'),g.be('missing')),qa=[
            claim('goal','who','Who wanted to read inside?',f'{h} wanted to read a storybook inside. The door was locked.','hero','storybook','door'),
            claim('problem','what','Why could they not open the door?', 'The door was locked, and the key was missing.','door','target')])
    if f.kind=='offer_help':
        return scene(g.line('helper',g.me(g.can(v('help',pronoun('you')))),listener='hero'),qa=[
            claim('help','who','Who offered help?',f'{p} offered to help {h}.','hero','helper')])
    if f.kind=='choose_search':
        return scene(g.line('hero',g.me(v('want',v('find',r('target')))),listener='helper'))
    if f.kind=='admit_loss':
        return scene(g.line('hero',s(pronoun('I'),v('lose',r('target')),tense='past'),listener='helper'),qa=[
            claim('honesty','what',f'What did {h} admit?',f'{h} admitted losing the key. {p} had offered help.','hero','helper','target',supports=('help',))])
    if f.kind=='fetch_light':
        return scene(s('hero',g.adv(v('fetch',r('tool')),pp('from',n('porch')))),qa=[
            claim('tool','where','Where did the lantern come from?',f'{h} fetched the lantern from the porch.','hero','tool')])
    if f.kind=='find_key':
        return scene(g.using('hero',g.adv(v('find',r('target')),pp('under',n('bench'))),r('tool')),qa=[
            claim('solution','how','How was the missing key found?',f'{h} found it under the bench with the lantern. The lantern came from the porch.','hero','target','tool',supports=('tool',))])
    if f.kind=='lend_spare':
        return scene(s('helper',v('give',r('hero'),r('spare',first=True))),qa=[
            claim('solution','how',f'How did {p} help after {h} admitted the loss?',f'{p} gave {h} a spare key. {h} had admitted losing the original key.','hero','helper','spare','target',supports=('honesty',))])
    if f.kind.startswith('unlock_'):
        return scene(g.sequence('hero',g.adv(v('unlock',r('door')),pp('with',r(f.instrument))),
                                g.adv(v('step'),pp('inside',n('cottage')))),qa=[
            claim('entry','what','What opened the door?',f'{h} unlocked the door with '+('the original key.' if f.instrument=='target' else 'the spare key.'),'hero','door',f.instrument)])
    if f.kind=='hang_key':
        return scene(s('hero',g.adv(v('hang',r('target')),pp('on',n('hook')))),qa=[
            claim('storage','where','Where did the original key go?',f'{h} hung the key on the hook. The key had been found under the bench.','hero','target',supports=('solution',))])
    if f.kind=='return_spare':
        return scene(s('hero',g.adv(v('return',r('spare')),pp('to',r('helper')))),qa=[
            claim('return','who','Who got the spare key back?',f'{h} returned the spare key to {p}.','hero','helper','spare')])
    if f.kind=='write_reminder':
        return scene(g.line('hero',g.me(v('promise',g.adv(v('look'),pp('for',r('target')),'tomorrow'))),listener='helper'),
                     g.sequence('hero',v('write',r('note',first=True)),g.adv(v('hang',r('note')),pp('on',n('hook')))),qa=[
            claim('reminder','what',f'What did {h} promise?',f'{h} promised to look tomorrow and hung a note on the hook. The original key was still missing.','hero','target','note')])
    if f.kind=='ending':
        reading=s('hero',g.adv(v('open',r('storybook')),pp('beside',r('helper'))))
        if 'found' in w.flags:
            return scene(reading,qa=[claim('outcome','what_next','What changed by the end?',f'{h} opened the storybook beside {p}. The found key was on the hook.','hero','helper','target','storybook',supports=('storage',))])
        return scene(g.join(s(r('target'),g.be('missing')),reading,'but'),qa=[
            claim('outcome','what_next','What was solved, and what still needed doing?',f'{h} got inside and opened the storybook beside {p}. The original key was still missing; {h} promised to look tomorrow.','hero','helper','target','storybook',supports=('entry','reminder')),
            claim('storage','where','Where was the reminder?',f'The note was on the hook. {h} had promised to look for the missing key tomorrow.','hero','target','note',supports=('reminder',))])
    raise ValueError(f.kind)
