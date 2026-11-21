"""Resource decisions are spoken before their visible physical consequences."""
from .surface import scene,claim


def greenhouse(w,f,g):
    n,r,v,s,pp=g.n,g.ref,g.v,g.s,g.pp
    if f.kind=='notice':
        return scene(g.join(s('hero',v('want',v('water',r('sunflower')))),
                           s(r('tomatoes'),g.be('thirsty')),'but'),
                     g.line('caretaker',s(r('tap'),g.be('broken'),tense='present'),listener='hero'),qa=[
            claim('goal','who','Who wanted to water the sunflower?', 'Nia wanted to water the sunflower. The tomato seedlings were thirsty too.','hero','sunflower','tomatoes'),
            claim('problem','what','What was wrong with the water supply?', 'Mr Bell said the tap was broken.','caretaker','tap')])
    if f.kind=='borrow':return None
    if f.kind=='fill':
        return scene(s(r('barrel'),v('hold',g.counted(1,'can',pp('of',n('water',det='bare'))))),qa=[
            claim('water','where','Where was the first water, and how much was there?', 'The rain barrel held one can of water.','hero','barrel','can')])
    if f.kind=='choose_seedlings':
        return scene(g.offer('hero', g.adv(v('water', r('tomatoes')), 'first'), listener='caretaker'),qa=[
            claim('choice','what','Which plants did Nia choose first?', 'Nia chose to water the tomato seedlings first. She had wanted to water the sunflower.','hero','tomatoes','sunflower',supports=('goal',))])
    if f.kind=='choose_flower':
        return scene(g.say_intent('hero', 'want', g.adv(v('water', r('sunflower')), 'first'), listener='caretaker'),qa=[
            claim('choice','what','Which plant did Nia choose first?', 'Nia chose to water the sunflower first. The tomato seedlings were also thirsty.','hero','tomatoes','sunflower',supports=('goal',))])
    if f.kind=='choose_share':
        return scene(g.offer('hero', g.adv(v('divide', n('water', det='bare')), 'equally'), listener='caretaker'),qa=[
            claim('choice','how','How did Nia choose to use the limited water?', 'Nia chose to divide the water equally. There was only one can of water in the barrel.','hero','barrel','can',supports=('water',))])
    if f.kind=='water_first':
        if 'share_plan' in w.flags:
            return scene(s('hero',g.adv(v('divide',n('water',det='bare')),'equally',pp('between',g.both(r('tomatoes'),r('sunflower'))))),qa=[
                claim('first_water','how','How did both kinds of plant get water?', 'Nia divided the water equally between the tomato seedlings and the sunflower.','hero','tomatoes','sunflower','can')])
        return scene(g.using('hero',v('water',r(f.patient)),r('can')),qa=[
            claim('first_water','how','What did Nia use to water the plants?', 'Nia used the watering can to water '+('the sunflower.' if f.patient=='sunflower' else 'the tomato seedlings.'),'hero',f.patient,'can')])
    if f.kind=='shade_break':
        if 'flower_first' in w.flags:
            return scene(s(r('cloth'),v('fall')),s(r('tomatoes'),v('have',n('leaf','brown',det='a'))),qa=[
                claim('damage','what','What sign of damage appeared?', 'A leaf was brown after the shade cloth fell. Nia had watered the sunflower first.','tomatoes','cloth','sunflower',supports=('choice',))])
        return scene(s(r('cloth'),v('fall')),qa=[claim('damage','what','What fell after the first watering?','The shade cloth fell.','cloth')])
    if f.kind=='secure':
        return scene(s('hero',g.adv(v('secure',r('umbrella')),pp('above',r('tomatoes')),pp('with',r('tie')))),qa=[
            claim('shade','why','Why did Nia secure an umbrella above the seedlings?', 'The shade cloth had fallen. Nia secured an umbrella above the seedlings with a garden tie.','hero','tomatoes','umbrella','tie','cloth',supports=('damage',))])
    if f.kind=='move_flower':
        return scene(s('hero',g.adv(v('move',r('sunflower')),pp('under',r('umbrella')))),qa=[
            claim('move','where','Where did Nia move the sunflower?', 'Nia moved the sunflower under the umbrella beside the tomato seedlings. Both had received a share of water.','hero','sunflower','tomatoes','umbrella',supports=('shade','first_water'))])
    if f.kind=='repair_tap':
        return scene(s('caretaker',v('repair',r('tap'))),qa=[claim('repair','who','Who repaired the tap?', 'Mr Bell repaired the tap.','caretaker','tap')])
    if f.kind=='refill':return None
    if f.kind=='water_second':
        return scene(s('hero',g.adv(v('water',r(f.patient)),pp('with',n('water',det='bare')),pp('from',r('tap')))),qa=[
            claim('second_water','where','Where did the later water come from?', 'The later water came from the tap. Mr Bell had repaired it.','hero',f.patient,'tap','caretaker',supports=('repair',))])
    if f.kind=='repair_shade':
        return scene(g.using('owner',v('repair',r('cloth')),r('clip')))
    if f.kind=='promise_repair':
        return scene(g.say_intent('caretaker', 'promise', g.adv(v('repair', r('tap')), 'tomorrow'), listener='hero'),qa=[
            claim('repair','who','Who promised to repair the tap?', 'Mr Bell promised to repair the tap tomorrow.','caretaker','tap')])
    if f.kind=='return':return None
    if f.kind=='ending':
        if 'share_plan' in w.flags:
            return scene(s(g.both(r('tomatoes'),r('sunflower')),g.adv(v('stand'),'upright',pp('under',r('umbrella')))),qa=[
                claim('outcome','what_next','How were the plants protected at the end?', 'The tomato seedlings and sunflower stood under the umbrella. Nia had divided the water equally between them.','hero','tomatoes','sunflower','umbrella',supports=('first_water','move'))])
        ending=s(r('tomatoes'),g.adv(v('stand'),pp('under',r('cloth',adjectives=('repaired',)))))
        if 'flower_first' in w.flags:
            return scene(g.say_intent('hero', 'promise', g.adv(v('water', r('tomatoes')), 'first', 'tomorrow'), listener='caretaker'),
                         s(r('leaf',adjectives=('brown',)),g.adv(v('remain'),pp('under',r('cloth',adjectives=('repaired',))))),qa=[
                claim('outcome','what_next','What did Nia promise after seeing the brown leaf?', 'Nia promised to water the tomato seedlings first tomorrow. The brown leaf remained under the repaired shade cloth.','hero','tomatoes','sunflower','cloth',supports=('damage','choice'))])
        return scene(ending,s('hero',g.adv(v('move',r('sunflower')),pp('beside',r('tomatoes')))),qa=[
            claim('outcome','what_next','What happened to the sunflower after it waited?', 'The sunflower was watered after Mr Bell repaired the tap. The tomato seedlings stood under the repaired shade cloth.','hero','sunflower','tomatoes','tap','cloth',supports=('second_water',))])
    raise ValueError(f.kind)
