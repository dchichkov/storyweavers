"""Authored bindings for reusable appraisal/commitment/payoff constructions."""
from copy import deepcopy

from .engine import event
from .language import clause as c, speech as s, sequence
from .decision_policy import motif, reminder, utterance
from ..surface import claim


def enrich(source):
    spec=deepcopy(source);spec['decision_policy']=True
    events={e['name']:e for e in spec['events']};name=spec['name']
    def wrap(e,key,carrier,meaning,phase='setup',guards=None):
        events[e]['surface']=motif(key,carrier,meaning,events[e]['surface'],phase=phase,guards=guards)
    def talk(e,key,speaker,listener,act,requires=()):
        original=events[e]['surface']
        # Wrap only the actual matching utterance, not unrelated scene dialogue.
        def bind(n):
            if n['kind']=='speech' and all(n[k]==v for k,v in [('speaker',speaker),('listener',listener),('act',act)]):
                return utterance(key,speaker,listener,act,n)
            for k in ('nodes',):
                if k in n:n[k]=[bind(x) for x in n[k]]
            return n
        events[e]['surface']=bind(original)
        for later in requires:events[later].setdefault('requires_utterances',[]).append(key)
    def cost(e,carrier,states,description):
        events[e].setdefault('observed_costs',[]).append(dict(carrier=carrier,states=states,description=description))
    def remind(e,key,carrier,meaning,words):
        events[e]['surface']=sequence(reminder(key,carrier,meaning,c(carrier,'remain',words,role='reminder')),events[e]['surface'])
    def appraisals(trigger,obj,choices,rows):
        for choice_name,stakes in choices.items():
            events[choice_name]['requires'].append('chosen:appraisal')
            events[choice_name]['stakes']=stakes
        for key,words,priorities,preferences in rows:
            e=event('appraise_'+key,c('hero','consider',words,object=obj,role='appraisal'),
                    after=[trigger],group='appraisal',patient=obj,function='appraisal',preferences=preferences,
                    qa=[claim('appraisal','why','What mattered to '+spec['entities']['hero']['noun']+' when choosing?',
                              words.replace('{hero}',spec['entities']['hero']['noun']).replace('{grandpa}',spec['entities'].get('grandpa',{}).get('noun','')),
                              'hero',obj)])
            # QA is authored from the same selected alternative, not a generic
            # conclusion inferred from the later outcome.
            e['appraisal']=dict(carrier='hero',object=obj,evidence=[trigger],priorities=priorities)
            spec['events'].append(e)
    if name=='pottery':
        appraisals('preference','cup',{
            'keep_dent':dict(Usefulness=1,Design=-.6,Deadline=1),
            'remake':dict(Usefulness=.7,Design=1,Deadline=-1),
            'make_bowl':dict(Usefulness=1,Design=-1,Deadline=.8)},[
            ('usefulness','{hero} had been hiding the dent from {grandpa}. Now she wondered whether it could help him hold the cup.',
             dict(Usefulness=1,Design=.1,Deadline=.4),[('Care',1)]),
            ('design','{hero} still wanted to make the cup in her drawing. Starting again would preserve that shape, but the gift would be late.',
             dict(Usefulness=.3,Design=1,Deadline=.1),[('Pride',1)]),
            ('deadline','{hero} pictured the birthday table without her present. Even a changed cup could be ready for Saturday.',
             dict(Usefulness=.5,Design=.1,Deadline=1),[('Care',.4)])])
        wrap('plan','gift_shape','cup','perfect_pattern')
        wrap('drawing_on_birthday','birthday','hero','missed')
        for e,meaning,states in [('use','useful_dent',['thumb_hollow','safe']),('use_late','late_useful_gift',['wide_handle','safe']),('use_bowl','changed_design',['bowl_shape','safe'])]:
            wrap(e,'gift_shape','cup',meaning,'payoff',{'cup':states})
        remind('use_late','birthday','hero','missed','The birthday had already passed.')
        talk('schedule','remake_warning','helper','hero','warn',requires=['remake'])
        talk('reveal','help_request','hero','grandpa','admit',requires=['preference'])
        talk('preference','grip_need','grandpa','hero','suggest',requires=['keep_dent','remake','make_bowl'])
        events['preference']['resolves_utterances']={'help_request':'answered'}
        cost('reveal','hero',['surprise_lost'],'The gift is no longer a surprise.')
        cost('keep_dent','cup',['dented','thumb_hollow'],'The visible imperfection remains.')
        cost('drawing_on_birthday','hero',['birthday_missed'],'The birthday passes without the finished cup.')
        cost('make_bowl','hero',['abandoned_cup_design'],'The original cup design is given up.')
    elif name=='music':
        # The forthcoming appraisal supplies the reaction; retain the teacher's
        # consequential deadline rather than another generic look at the list.
        events['hear_deadline']['surface']['nodes']=events['hear_deadline']['surface']['nodes'][:1]
        appraisals('hear_deadline','drum',{
            'choose_private':dict(Together=1,PublicTurn=-1,Authorship=0),
            'choose_solo':dict(Together=-1,PublicTurn=1,Authorship=0),
            'choose_written':dict(Together=.1,PublicTurn=.6,Authorship=1)},[
            ('together','{hero} looked at the sticks Mateo had set down. Without his answer, the concert turn seemed less important.',
             dict(Together=1,PublicTurn=.1,Authorship=.2),[('Care',1)]),
            ('public_turn','{hero} had practiced for her turn, too. Mateo could refuse the audience without making her refuse it.',
             dict(Together=.1,PublicTurn=1,Authorship=.1),[('Pride',1)]),
            ('contribution','{hero} wanted the audience to hear Mateo\'s answer. Perhaps his music could go on stage without him.',
             dict(Together=.2,PublicTurn=.6,Authorship=1),[('Care',.5),('Pride',.3)])])
        wrap('hear_practice','answer','drum','shared_practice')
        wrap('withdraw_both','entry','program','withdrawn')
        # The crossed-out entry has already been narrated; the answering drums
        # are the new payoff. Keep both available, but favor the shorter ending.
        final=events['end_private']['surface']['nodes']
        events['end_private']['surface']=sequence(reminder('entry','program','withdrawn',final[0]),*final[1:])
        for e,meaning,state in [('end_private','private_partnership','played_private'),('end_solo','self_answer','played_public_solo'),('end_written','absent_author','played_written_answer')]:
            wrap(e,'answer','drum',meaning,'payoff',{'hero':[state]})
        talk('refuse_public','public_refusal','partner','hero','boundary',requires=['choose_private','choose_solo','choose_written'])
        talk('choose_private','private_invitation','hero','partner','invite',requires=['agree_private'])
        talk('agree_private','door_promise','hero','partner','promise',requires=['shut_door','play_private'])
        talk('choose_written','use_permission','partner','hero','offer',requires=['write_answer','play_written'])
        talk('choose_written','credit_promise','hero','partner','accept',requires=['give_credit'])
        events['agree_private']['resolves_utterances']={'private_invitation':'answered'}
        events['shut_door']['resolves_utterances']={'door_promise':'fulfilled'}
        events['give_credit']['resolves_utterances']={'credit_promise':'fulfilled'}
        cost('withdraw_both','hero',['public_turn_lost'],'The public concert slot is given to another child.')
        cost('perform_solo','hero',['played_public_solo'],'The public performance has no answering partner.')
        events['play_written']['effects']['hero']['add'].append('performed_without_partner')
        cost('play_written','hero',['played_written_answer','performed_without_partner'],
             'Mateo contributes his music, but Nia gives up having a public duet partner.')
    elif name=='greenhouse':
        appraisals('learn_shade','can',{
            'choose_share':dict(Care=.7,Show=-.5,Certainty=.2,Balance=1),
            'choose_flower':dict(Care=-1,Show=1,Certainty=.3,Balance=-1),
            'choose_seedlings':dict(Care=1,Show=-1,Certainty=1,Balance=-.5)},[
            ('both','{hero} looked from her sunflower to the little class\'s seedlings. Sharing might help both, but she would have to stay.',
             dict(Care=.8,Show=.2,Certainty=.1,Balance=1),[('Care',.6)]),
            ('show','{hero} had waited all year for the show. She was tempted to save the whole can for her sunflower.',
             dict(Care=.1,Show=1,Certainty=.1,Balance=.1),[('Pride',1)]),
            ('risk','{hero} looked at the curled leaf. Half a can might be enough, but she did not want to gamble on those seedlings.',
             dict(Care=.7,Show=.1,Certainty=1,Balance=.1),[('Care',1)])])
        authored={e['name']:e for e in spec['events']}
        for e,key,meaning in [('appraise_show','show_wait','waited_year'),('appraise_risk','risk','seedlings_risk')]:
            authored[e]['surface']=motif(key,'hero',meaning,authored[e]['surface'])
        flowers=events['choose_flower']['surface']['nodes']
        flowers[0]=reminder('show_wait','hero','waited_year',flowers[0])
        withdrawal=s('hero','caretaker','withdraw','My flower will have to miss the show.',lemma='withdraw',object='sunflower',hypothetical=True)
        withdrawal['content']=sequence(
            reminder('risk','hero','seedlings_risk',c('hero','want',"I don't want to risk the little ones.",object='tomatoes',role='dialogue',hypothetical=True)),
            withdrawal['content'])
        events['choose_seedlings']['surface']=sequence(
            c('hero','pour','{hero} poured the whole can over the seedlings.',object='tomatoes'),withdrawal)
        wrap('prepare_show','ribbon','ribbon','show_decoration')
        wrap('discover_scarcity','leaf','leaf','warning')
        for e in ('choose_share','choose_flower','choose_seedlings'):wrap(e,'water','can','spent')
        wrap('end_shared','ribbon','ribbon','shared_shade','payoff',{'tomatoes':['recovered'],'hero':['show_missed']})
        wrap('stay_after_mistake','leaf','leaf','lasting_damage','payoff',{'leaf':['brown'],'tomatoes':['water_units_0']})
        wrap('end_seedlings','ribbon','ribbon','water_reminder','payoff',{'ribbon':['water_first_marker'],'sunflower':['water_units_0']})
        for e in ('end_shared','end_flower','end_seedlings'):remind(e,'water','can','spent','The watering can was empty.')
        talk('ask_for_hold','hold_request','hero','caretaker','request',requires=['hold_handle'])
        events['hold_handle']['resolves_utterances']={'hold_request':'answered'}
        cost('keep_shared_shade','hero',['show_missed'],'The flower show begins while Nia stays with the plants.')
        cost('see_brown_leaf','leaf',['brown'],'A leaf is permanently damaged after the first allocation.')
        cost('choose_seedlings','sunflower',['water_units_0','dry'],'Her sunflower receives none of the remaining water.')
    else:raise ValueError('no authored decision bindings for '+name)
    return spec
