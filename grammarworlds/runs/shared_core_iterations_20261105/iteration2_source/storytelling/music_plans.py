"""Typed music scenes in which listening and composing are distinct from performing."""
from .surface import scene,claim
from ..portable.nouns import pronoun


def music(w,f,g):
    n,r,v,s,pp=g.n,g.ref,g.v,g.s,g.pp
    if f.kind=='opening':return None
    if f.kind=='borrow':
        return scene(g.sequence('hero',g.adv(v('borrow',r('drum')),pp('from',r('teacher'))),
            g.adv(v('hope',v('play',n('duet',det='a'))),pp('with',r('partner')))),qa=[
            claim('goal','what','What did Nia hope to do?','Nia hoped to play a duet with Mateo. She borrowed the little drum from Dalia.','hero','partner','drum','teacher'),
            claim('instrument','who','Who lent Nia the drum?','Nia borrowed the little drum from Dalia.','hero','teacher','drum')])
    if f.kind=='invite':
        return scene(g.line('hero',g.me(v('need',n('beat','answering',det='a'))),listener='partner'))
    if f.kind=='decline':
        return scene(g.line('partner',g.me(g.adv(g.be('ready'),pp('for',n('audience'))),negative=True),listener='hero'),qa=[
            claim('boundary','what','What did Mateo say about playing for an audience?','Mateo said he was not ready for the audience. Nia had hoped to play a duet with him.','hero','partner',supports=('goal',))])
    if f.kind=='choose_solo':
        return scene(g.say_intent('hero', 'choose', v('perform', n('solo', det='a')), listener='partner'),qa=[
            claim('choice','what','What did Nia choose after Mateo declined?','Nia chose to perform a solo. Mateo was not ready for the audience.','hero','partner',supports=('boundary',))])
    if f.kind=='offer_pattern':
        return scene(g.offer('partner', v('write', n('rhythm', det='a')), listener='hero'),qa=[
            claim('choice','how','How did Mateo offer to help without performing?','Mateo offered to write a rhythm. He had said he was not ready for the audience.','hero','partner','paper',supports=('boundary',))])
    if f.kind=='offer_private':
        return scene(g.say_intent('partner', 'want', g.adv(v('play'), 'privately', pp('with', pronoun('you'))), listener='hero'),qa=[
            claim('choice','how','What kind of playing did Mateo agree to?','Mateo wanted to play privately with Nia. He was not ready for the audience.','hero','partner',supports=('boundary',))])
    if f.kind=='write_pattern':
        return scene(s('partner',g.adv(v('write',n('rhythm',det='a')),pp('on',r('paper')),pp('with',r('pencil')))),qa=[
            claim('pattern','where','Where did Mateo write the rhythm?','Mateo wrote the rhythm on paper with a pencil.','partner','paper','pencil')])
    if f.kind=='prepare_solo':
        return scene(s('hero',v('practice',g.both(n('beat','soft',det='a'),n('beat','loud',det='a')))),qa=[
            claim('preparation','how','How did Nia prepare her solo?','Nia practiced a soft beat and a loud beat. She had chosen to perform a solo.','hero','drum',supports=('choice',))])
    if f.kind=='prepare_pattern':
        return scene(s('hero',g.adv(v('practice',g.possess(r('partner'),g.cn('rhythm'))),pp('on',r('drum')))))
    if f.kind=='pickup':return None
    if f.kind=='perform':
        if 'pattern_plan' in w.flags:
            action=v('play',g.possess(r('partner'),g.cn('rhythm')))
            answer="Nia played Mateo's rhythm on the little drum before Dalia. Mateo had written the rhythm on paper."
            supports=('pattern',)
        else:
            action=v('perform',n('solo'))
            answer='Nia performed her solo on the little drum before Dalia. She had practiced a soft beat and a loud beat.'
            supports=('preparation',)
        return scene(s('hero',g.adv(action,pp('on',r('drum')),pp('before',r('teacher')))),qa=[
            claim('performance','how','What did Nia perform?',answer,'hero','teacher','drum','partner',supports=supports)])
    if f.kind=='join':
        return scene(s(g.both(r('hero'),r('partner')),g.adv(v('play',n('duet',det='a')),'privately')),
                     s('partner',v('answer',g.possess(r('hero'),g.cn('beat')))),qa=[
            claim('performance','how','How did Mateo take part in the music?','Nia and Mateo played a duet privately. Mateo answered Nia\'s beat.','hero','partner','drum','spare')])
    if f.kind=='response':
        if 'private_plan' in w.flags:
            return scene(g.line('hero',g.me(v('hear',g.possess(pronoun('you'),g.cn('answer')))),listener='partner'),
                         s(g.both(r('hero'),r('partner')),v('smile')),qa=[
                claim('outcome','what_next','How did the private duet end?','Nia said she heard Mateo\'s answer, and they smiled. Mateo had answered her beat during the duet.','hero','partner',supports=('performance',))])
        return scene(g.join(s('partner',v('clap')),s('hero',v('bow'))),qa=[
            claim('outcome','what_next','How did Mateo respond after Nia played?','Mateo clapped, and Nia bowed. Nia had performed before Dalia.','hero','partner','teacher',supports=('performance',))])
    if f.kind=='return':return None
    if f.kind=='ending':
        if 'pattern_plan' in w.flags:
            return scene(g.say_intent('hero', 'want', g.adv(v('play', g.possess(pronoun('you'), g.cn('rhythm'))), 'again'), listener='partner'),
                         s('hero',g.adv(v('put',r('paper')),pp('between',g.both(r('drum'),r('spare'))))),qa=[
                claim('keepsake','where','Where did Nia put the written rhythm?','Nia put the paper between the two drums. Mateo had written the rhythm on it.','hero','partner','paper','drum','spare',supports=('pattern',))])
        return None
    raise ValueError(f.kind)
