"""Manual whole-story music annotations; frozen v1 conventions."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a = Annotation('08_music', prompt_version='v1')
for key in ['appearance_color', 'part_whole_relation', 'figurative_mapping']:
    a.use_extension(key)

# Explicit occurrence-by-occurrence contextual decisions, including all lemmas.
LEX = {
0:'det=every n=Thursday det=the n=community n=music n=room v=fill adp=with n=sound pron=that v=do adv=quite v=agree det=a n=piano v=practice n=scale det=a n=flute v=make adj=long adj=sleepy n=note conj=and pron=someone adp=in det=the n=corner v=try part=to v=teach det=a n=tambourine part=to v=behave',
1:'n=Nia v=like det=the adj=little n=drum adv=well pron=it v=be adv=just det=the adj=right n=size part=to v=tuck adp=beneath det=her n=arm adp=with det=a adj=red n=ribbon v=knot adp=around det=its n=handle n=Ms n=Dalia v=let pron=she v=borrow pron=it adp=for det=the n=week',
2:'pron=I v=want part=to v=play det=a n=duet adp=at n=Saturday n=music n=room n=picnic n=Nia v=tell pron=she pron=something adp=with det=a n=drumbeat conj=and det=an n=answer',
3:'adv=then pron=you v=need pron=someone part=to v=answer v=say n=Ms n=Dalia',
4:'det=that n=afternoon det=a adj=new n=boy v=come adv=in v=hold det=a n=music n=folder adp=against det=his n=chest det=his n=name v=be n=Mateo pron=he v=sit adp=near det=the n=door conj=and v=watch det=the adj=other n=child v=play',
5:'n=Nia v=test det=a n=beat adp=on det=her n=drum intj=bum intj=bum n=pause intj=bum',
6:'n=Mateo n=finger v=tap det=the adj=same n=rhythm adp=on det=his n=knee',
7:'n=Nia v=notice conj=but pron=she v=do v=point pron=she v=play det=the n=beat adv=again adv=soft det=this n=time n=Mateo n=finger v=answer',
8:'conj=when det=the n=song v=end pron=she v=ask v=will pron=you v=like part=to v=make det=a n=duet adp=with pron=I adp=for n=Saturday',
9:'n=Mateo v=look adp=toward det=the n=roomful adp=of n=child pron=I v=like v=play pron=I adv=just v=do v=want pron=everybody v=look adp=at pron=I adv=yet',
10:'intj=okay n=Nia v=say',
11:'pron=she v=do v=ask adv=again pron=she v=carry det=her n=drum adp=to det=the n=rug conj=and v=practice adv=there v=leave adj=little n=pause adp=in det=her n=beat det=the adj=red n=ribbon v=bob conj=whenever pron=she v=play',
12:'n=Mateo v=stay adp=by det=the n=door adv=sometimes det=his n=finger v=tap adv=sometimes pron=they v=do',
13:'adp=on n=Friday n=Ms n=Dalia v=set det=a n=signup n=sheet adp=beside det=the n=piano pron=I v=need det=the n=name adp=for n=Saturday n=program conj=before pron=we v=lock adv=up pron=she v=say pron=there n=room adp=for num=one adv=more n=act',
14:'n=Nia v=have v=imagine n=Mateo adp=beside pron=she v=answer det=her n=drum adp=with det=a adj=second n=drum adp=from det=the n=shelf pron=she v=look adp=at pron=he pron=he v=be v=study det=the n=signup n=sheet det=his n=mouth v=press adp=into det=a adj=thin n=line',
15:'pron=she v=can v=write det=both det=their n=name n=Mateo v=may v=say intj=yes conj=once pron=he v=see pron=they adv=there conj=but pron=that v=will v=make det=the n=choice adp=for pron=he',
16:'n=Nia v=take det=the n=pencil conj=and v=write n=Nia n=drum n=solo',
17:'pron=it v=feel adp=like v=put adv=away det=a adj=favorite n=toy conj=before pron=she v=be adj=finished v=play',
18:'n=Mateo v=glance adp=at det=the n=page pron=you v=can adv=still v=do det=a n=duet pron=he v=say adv=quietly',
19:'pron=I v=can n=Nia v=reply conj=but pron=I v=do v=know conj=if pron=you v=want pron=one',
20:'pron=he v=look adv=down adp=at det=his n=folder part=not adp=on det=the n=program',
21:'adv=then pron=it det=a n=solo',
22:'n=Nia v=practice det=her n=song det=that n=evening adp=in det=the n=kitchen adp=without det=another n=player det=the n=pause v=seem adj=enormous det=her n=father v=offer part=to v=clap adv=along conj=but pron=she v=shake det=her n=head pron=she v=try v=make det=the n=beat adj=soft conj=and adj=loud adp=like n=footstep v=come adp=down det=a n=hall det=the n=song v=begin part=to v=sound adv=little adj=empty',
23:'adp=on n=Saturday det=the n=community n=music n=room v=be adj=crowded adp=with adj=folding n=chair conj=and n=paper n=cup adp=of n=lemonade n=Nia n=drum v=wait adp=beside det=her n=stool det=the n=ribbon v=lie adp=against det=its adj=wooden n=rim',
24:'pron=she v=can v=see n=Mateo adp=in det=the adj=back n=row adv=still v=hold det=his n=folder',
25:'n=Ms n=Dalia v=introduce det=the adj=next n=act n=Nia adp=with det=a n=drum n=solo',
26:'n=Nia v=sit adv=down det=her n=palm v=feel adj=warm pron=she v=play intj=bum intj=bum n=pause intj=bum det=the n=pause v=open adv=wide pron=she v=fill pron=it adp=with det=a adj=quiet n=beat adv=then pron=another v=make det=a n=path adp=through det=the n=song',
27:'adp=from det=the adj=back n=row v=come det=a adj=faint n=tap',
28:'n=Nia v=keep det=her n=eye adp=on det=the n=drum',
29:'n=tap n=tap',
30:'pron=she v=play det=her adj=next n=pattern det=the v=answer n=tap v=grow adj=clear conj=though n=Mateo v=have v=leave det=his n=chair n=Nia n=shoulder v=loosen pron=she v=finish det=the n=song adp=with num=three adj=soft n=beat conj=and v=let det=the adj=last pron=one v=ring',
31:'det=the n=room v=clap',
32:'n=Mateo v=stand adv=then v=stop pron=he v=look adp=at det=the adj=second adj=small n=drum adp=on det=the n=instrument n=shelf pron=it v=be det=the adj=same n=size conj=as n=Nia',
33:'n=Nia v=do v=wave pron=he adv=over pron=she adv=simply v=set det=her n=drum adp=beside det=her n=stool conj=and v=wait conj=while n=Ms n=Dalia v=thank det=the n=audience',
34:'n=Mateo v=cross adp=to det=the n=shelf conj=and v=lift det=the adj=second n=drum v=can pron=I v=try det=the n=answer n=part pron=he v=ask',
35:'intj=sure v=say n=Nia',
36:'pron=they v=sit adp=on det=the n=rug part=not det=the adj=little n=performance n=space n=Mateo v=tap adv=once v=test det=the n=sound n=Nia v=answer pron=he v=try num=two n=beat pron=she v=leave pron=he n=room adp=for num=three',
37:'adp=by det=the n=time det=the n=lemonade v=be adj=gone det=their n=duet v=have det=no n=name det=no n=program n=listing conj=and det=no n=ending pron=they v=have v=agree adp=on pron=they v=keep v=play adv=anyway',
38:'conj=when pron=it v=be n=time part=to v=put det=the n=instrument adv=away n=Nia v=return det=her v=borrow n=drum adp=to det=the n=shelf n=Mateo v=place det=the pron=other adp=beside pron=it det=the adj=red n=ribbon v=hang adp=between det=the num=two n=handle v=quiver adv=faintly conj=as det=the adj=last n=sound v=fade',
}
for p, text in LEX.items():
    pairs = [pair.split('=', 1) for pair in text.split()]
    words = a.paragraphs[p]['words']
    assert len(words) == len(pairs), (p, len(words), len(pairs))
    a.tag(p, [pair[0] for pair in pairs], {word['w']: pair[1] for word, pair in zip(words, pairs)})

ENTS = [
('e1','Nia','person',[35,50,63,69,80,91,128,133,148,151,154,169,179,202,204,208,210,222,229,273,278,280,289,306,329,335,347,356,365,367,370,391,393,407,414,416,418,455,459,468,486,491,494,498,508,531,533,540,542,556,559,597,598,603,606,609,639,656,662,703,705]),
('e2','Mateo','person',[103,111,113,116,117,139,146,162,172,182,189,192,199,231,237,276,292,293,299,312,317,328,351,362,374,377,381,471,478,551,554,576,580,601,619,630,635,650,658,664,711]),
('e3','Ms. Dalia','person',[60,61,82,97,98,245,246,254,265,480,481,614,615]),
('e4','Nia father','person',[408]),
('e5','community music room','room',[5,78,444,574]),
('e6','Nia borrowed drum','drum',[39,41,58,65,134,211,281,336,456,465,489,537,607,707,716]),
('e7','second small drum','drum',[285,586,591,628,714]),
('e8','red ribbon tied to first drum','ribbon',[55,226,462,719]),
('e9','first drum handle','handle',[59]),
('e10','first drum wooden rim','rim',[467]),
('e11','music room rug','rug',[214,217,644]),
('e12','performance space','performance_space',[649]),
('e13','Nia performance stool','stool',[460,610]),
('e14','instrument shelf','shelf',[288,590,623,710]),
('e15','signup sheet','sheet',[250,298,355]),
('e16','Saturday program','program',[260,386,681]),
('e17','Mateo music folder','folder',[109,382,479]),
('e18','piano','piano',[14,253]),
('e19','flute','flute',[18]),
('e20','tambourine','tambourine',[32]),
('e21','unnamed tambourine learner','person',[24]),
('e22','music room corner','room_region',[27]),
('e23','music room door','door',[121,235]),
('e24','other children in Thursday room','child_group',[126,188]),
('e25','Saturday audience','person_group',[618]),
('e26','Nia and Mateo','person_group',[310,640,675,686,690]),
('e27','Mateo fingers','body_part_group',[140,163,238,241]),
('e28','Mateo knees','body_part_group',[147]),
('e29','Mateo chest','body_part',[112]),
('e30','Mateo mouth','body_part',[300]),
('e31','Nia arm','body_part',[51]),
('e32','Nia head','body_part',[417]),
('e33','Nia palms','body_part_group',[495]),
('e34','Nia eyes','body_part_group',[534]),
('e35','Nia shoulders','body_part_group',[557]),
('e36','Saturday back row','seating_row',[475,526]),
('e37','Mateo Saturday chair','chair',[555]),
('e38','Saturday folding chairs','chair_group',[449]),
('e39','paper cups','cup_group',[452]),
('e40','picnic lemonade','lemonade',[454,672]),
('e41','kitchen','room',[399]),
('e42','signup pencil','pencil',[332]),
('e43','Saturday picnic','gathering',[79]),
('e44','desired Saturday duet','proposed_musical_act',[74,83,177,361,376]),
('e45','Nia listed drum solo','musical_act',[388,390,485,490]),
('e46','actual informal rug duet','musical_act',[676]),
('e47','Nia musical composition','musical_composition',[167,394,433,522,562]),
('e48','tested rhythmic pattern','rhythmic_pattern',[131,144,157,223]),
('e49','pauses in Nia arrangement','musical_rest_group',[220,404]),
('e50','two drum handles','handle_group',[724]),
('e52','hypothetical public watchers','person_group',[196]),
('e53','duet answer part','musical_part',[89,634]),
('e54','Saturday names on signup','written_name_group',[257]),
('e55','hypothetical written pair of names','hypothetical_written_name_group',[311,319]),
('e56','Nia written signup entry','written_entry',[337]),
('e57','hypothetical duet partner','person_role',[93]),
('e58','Nia imagined toy','imagined_toy',[345]),
('e59','simile footsteps','imagined_sound_group',[427]),
('e60','simile hall','imagined_hall',[431]),
('e61','room sounds','sound_group',[8]),
('e62','flute notes','sound_group',[22]),
('e63','piano scale exercises','musical_scale_group',[16]),
('e64','three final solo beats','sound_group',[566]),
('e65','last final solo beat','sound',[571]),
('e66','Mateo voluntary seat taps','sound_group',[530,538,539,547]),
('e67','last informal duet sound','sound',[730]),
('e68','both drums as instruments to put away','instrument_group',[701]),
('e69','next pattern during solo','rhythmic_pattern',[544]),
('e70','rest in tested rhythmic pattern','musical_rest',[137]),
('e71','particular formal solo pause','musical_rest',[502,505,510]),
]
for args in ENTS: a.entity(*args)
a.feature(640, group_members=['e1','e2'])
a.feature(701, group_members=['e6','e7'])

SCOPES = [
('s1',list(range(69,80))+list(range(83,90)),'quotation','e1','Nia states a desired Saturday duet and its musical content.'),
('s2',range(90,96),'quotation','e3','Dalia comments on the duet needing another player.'),
('s3',range(171,182),'quotation','e1','Invitation to a Saturday duet, not an agreement.'),
('s4',range(189,201),'quotation','e2','Mateo likes playing but explicitly does not want public attention yet.'),
('s5',[201],'quotation','e1','Nia acknowledges Mateo boundary.'),
('s6',list(range(254,265))+list(range(267,273)),'quotation','e3','Names needed before lockup; room for one program act.'),
('s7',range(276,289),'imagined','e1','Nia imagined Mateo answering with the second drum; no actual acquisition or formal duet.'),
('s8',range(306,329),'considered_alternative','e1','Unchosen signup of both names and possible later acceptance; free indirect perspective.'),
('s9',range(335,338),'written_content','e1','Actual written solo entry content.'),
('s10',range(341,351),'figurative','e1','Toy-putting-away comparison for Nia feeling, not an actual toy episode.'),
('s11',range(356,362),'quotation','e2','Mateo suggests Nia could still do a duet; not consent to program participation.'),
('s12',list(range(365,367))+list(range(369,377)),'quotation','e1','Nia acknowledges possibility and lack of knowledge of Mateo wishes.'),
('s13',range(383,387),'quotation','e2','Mateo excludes program participation.'),
('s14',range(387,391),'quotation','e1','Nia retains formal solo designation.'),
('s15',range(427,432),'figurative','e1','Dynamics compared to footsteps in a hall; no literal walkers.'),
('s16',range(486,491),'quotation','e3','Dalia publicly introduces the listed drum solo.'),
('s17',range(629,635),'quotation','e2','Mateo asks to try answer part after solo; separate from formal enrollment.'),
('s18',[637],'quotation','e1','Nia accepts Mateo request.'),
]
for sid, words, kind, holder, description in SCOPES:
    a.scope(sid,words,kind=kind,holder_id=holder,description=description)
    if kind == 'quotation': a.feature(words,quote_mode='direct',assertion_status='attributed_claim')

PROPS = [
('p1','Nia borrows the first drum for the week.',[62,64,65,68],'s0'),
('p2','Nia plays a Saturday duet with a drumbeat and answer.',[72,74,76,86,89],'s1'),
('p3','The duet requires a partner to answer.',[92,93,95],'s2'),
('p4','Nia and Mateo make a duet for Saturday.',[175,177,179,181],'s3'),
('p5','Everybody watches Mateo play yet.',[196,197,199,200],'s4'),
('p6','Mateo likes playing but does not want everybody watching him yet.',[190,191,195,197,200],'s4'),
('p7','The Saturday program needs names before lockup and has room for one more act.',[255,257,260,263,270,272],'s6'),
('p8','Mateo answers Nia drum with the second drum beside her.',[276,277,279,281,285],'s7'),
('p9','Nia writes both names on the signup sheet.',[306,308,309,311],'s8'),
('p10','Mateo says yes after seeing both names written there.',[312,313,314,315,318,319],'s8'),
('p11','Writing both names would make the choice for Mateo.',[322,324,326,328],'s8'),
('p12','Nia is listed for a drum solo.',[335,336,337],'s9'),
('p13','Nia could still do a duet.',[356,357,359,361],'s11'),
('p14','Mateo wants a duet.',[374,375,376],'s12'),
('p15','Mateo participates in a duet on the Saturday program.',[383,384,386],'s13'),
('p16','The formal listed act remains a solo.',[387,388,390],'s14'),
('p17','Nia father claps along with her practice.',[408,411,412],'s0'),
('p18','Nia plays the formal drum solo.',[486,489,490],'s16'),
('p19','Mateo tries the answer part after the solo.',[630,631,633,634],'s17'),
('p20','Nia and Mateo play together informally on the rug.',[640,641,644,676,692],'s0'),
('p21','The informal duet has no name, program listing or agreed ending.',[676,678,679,680,682,684,685,688],'s0'),
('p22','Both drums are put back on the shelf.',[703,704,707,710,711,712,714,716],'s0'),
('p23','Nia plays without her father clapping along.',[409,411,415,417],'s0'),
('p28','Nia does not know whether Mateo wants a duet.',[370,371,372,373,374,375,376],'s12'),
]
for pid,text,support,scope in PROPS: a.proposition(pid,text,support,scope_id=scope)

F=a.feature
def B(entity,value,scope='s0',status='asserted',**extra):
    return dict(entity_id=entity,scope_id=scope,assertion_status=status,value=value,**extra)
EV={}
def E(key,w,label,**kwargs):
    eid=f'ev{len(EV)+1}'; EV[key]=eid
    a.event(eid,w,label,**kwargs)
    if kwargs.get('primary',True) is not False:
        F(w,assertion_status='attributed_claim' if a.words[w]['scope_id'] in {'s1','s2','s3','s4','s5','s6','s11','s12','s13','s14','s16','s17','s18'} else 'asserted')
    return eid
def M(key,words,role='reference',note=''):
    a.mention_event(EV[key],words,role=role,note=note)
def U(key,w,speaker,content,addressees=(),kind='assertion',**kwargs):
    eid=E(key,w,'communicate: '+content,type='speak',actor=speaker,**kwargs)
    F(w,speaker_id=speaker,speech_act_kind=kind,utterance_id=eid,
      utterance_content_id=content,addressee_ids=list(addressees),communication_channel='speech',
      communication_scope_bundle=dict(speaker_id=speaker,utterance_event_id=eid,scope_id='s0',assertion_status='asserted'))
    return eid

# Explicit predicates and participant bindings. Repetition creates new events;
# later references to an ongoing act keep its event identity.
E('fill',6,'Thursday room fills with mixed sounds',type='state',patients=['e5','e61'],roles={'patient':[5,8]})
E('disagree',12,'room sounds fully harmonize',type='state',patients=['e61'],factuality='negated',roles={'patient':[8,9]})
E('piano',15,'unnamed player practices scales on piano',patients=['e63'],instruments=['e18'],roles={'instrument':[14],'patient':[16]})
E('flute',19,'unnamed player makes long flute notes',patients=['e62'],instruments=['e19'],roles={'instrument':[18],'result':[22]})
E('learner',28,'someone attempts to play tambourine controllably',actor='e21',instruments=['e20'],roles={'actor':[24],'instrument':[32]})
M('learner',[30,34],note='Personifying description of attempting controlled playing; no literal tambourine instruction.')
E('like_drum',36,'Nia prefers small drum',type='feel',actor='e1',patients=['e6'],roles={'experiencer':[35],'patient':[39]})
E('size',42,'drum is suitable size for underarm carrying',type='state',patients=['e6'],roles={'patient':[41]})
E('tuck',48,'Nia can tuck drum under arm',type='move',actor='e1',patients=['e6'],factuality='hypothetical',roles={'landmark':[51]})
E('knot',56,'ribbon is knotted around first drum handle',type='state',patients=['e8'],roles={'patient':[55],'landmark':[59]})
E('loan_permission',62,'Dalia permits Nia drum loan for week',actor='e3',patients=['e6'],recipient='e1',roles={'actor':[60,61],'recipient':[63],'patient':[65]})
E('borrow',64,'Nia borrows first drum',type='obtain',actor='e1',patients=['e6'],roles={'actor':[63],'patient':[65]},support=[62,64,68,706])
E('want_duet',70,'Nia wants Saturday duet',type='feel',actor='e1',patients=['e44'],roles={'experiencer':[69],'patient':[74]})
E('desired_duet',72,'Nia plays desired Saturday duet',actor='e1',patients=['e44'],instruments=['e6'],factuality='desired',roles={'actor':[69],'patient':[74]})
U('tell_desire',81,'e1','p2',['e3'],'report_desire',roles={'actor':[80],'addressee':[82]})
E('need_partner',92,'duet needs an answering partner',type='state',patients=['e44','e57'],factuality='hypothetical',roles={'patient':[93]})
E('partner_answer',95,'unspecified partner supplies answering part',actor='e57',patients=['e53'],factuality='hypothetical',roles={'actor':[93]})
U('dalia_advice',96,'e3','p3',['e1'],'advice',roles={'actor':[97,98]})
E('arrive',104,'Mateo enters music room',type='move',actor='e2',roles={'actor':[103]})
E('hold_folder_thu',106,'Mateo holds folder against chest',type='state',actor='e2',patients=['e17'],roles={'actor':[103],'patient':[109],'landmark':[112]})
E('named',115,'new boy is named Mateo',type='state',patients=['e2'],roles={'patient':[116]})
E('sit_door',118,'Mateo sits near door',type='move',actor='e2',roles={'actor':[117],'landmark':[121]})
E('watch_children',123,'Mateo watches children play',type='perceive',actor='e2',patients=['e24'],roles={'actor':[117],'patient':[126]})
E('children_play',127,'other children play music',actor='e24',roles={'actor':[126]})
E('test_pattern',129,'Nia tests drum pattern',actor='e1',patients=['e48'],instruments=['e6'],roles={'actor':[128],'patient':[131],'instrument':[134]})
E('tap_first',141,'Mateo taps same rhythm on knees',actor='e2',patients=['e48'],instruments=['e27'],roles={'effector':[140],'patient':[144],'surface':[147]})
E('notice',149,'Nia notices Mateo rhythmic response',type='perceive',actor='e1',roles={'actor':[148]})
E('not_point',153,'Nia points out Mateo response',actor='e1',factuality='negated',roles={'actor':[151]})
E('repeat_pattern',155,'Nia repeats beat more softly',actor='e1',patients=['e48'],instruments=['e6'],roles={'actor':[154],'patient':[157]})
E('tap_answer',164,'Mateo fingers answer repeated beat',actor='e2',instruments=['e27'],roles={'effector':[163]})
E('song_end_thu',168,'Thursday trial song ends',type='state',patients=['e47'],roles={'patient':[167]})
U('invite',170,'e1','p4',['e2'],'invitation',roles={'actor':[169]})
E('invitation_like',173,'Mateo liking proposed duet is queried',type='feel',actor='e2',patients=['e44'],factuality='hypothetical',roles={'experiencer':[172],'patient':[177]})
E('proposed_duet',175,'Nia and Mateo make proposed Saturday duet',actor='e26',patients=['e44'],factuality='hypothetical',roles={'actor':[172,179],'patient':[177]})
E('look_children',183,'Mateo looks toward children',type='perceive',actor='e2',patients=['e24'],roles={'actor':[182],'patient':[188]})
E('like_play',190,'Mateo likes playing',type='feel',actor='e2',roles={'experiencer':[189]})
E('enjoyed_play',191,'Mateo playing as preferred activity',actor='e2',factuality='hypothetical',roles={'actor':[189]})
E('not_want_watching',195,'Mateo wants everyone watching at this time',type='feel',actor='e2',factuality='negated',roles={'experiencer':[192]})
E('watching_unwanted',197,'everyone watching Mateo as undesired content',type='perceive',actor='e52',patients=['e2'],factuality='hypothetical',roles={'actor':[196],'patient':[199]})
U('boundary',190,'e2','p6',['e1'],'state_boundary',primary=False,scope='s0')
U('okay',203,'e1','p6',['e2'],'acknowledgment',roles={'actor':[202]})
E('not_ask',206,'Nia repeats the invitation',type='speak',actor='e1',factuality='negated',roles={'actor':[204]})
E('carry_rug',209,'Nia carries drum to rug',type='move',actor='e1',patients=['e6'],roles={'actor':[208],'patient':[211],'destination':[214]})
E('practice_thu',216,'Nia practices on rug',actor='e1',instruments=['e6'],roles={'actor':[208],'location':[217]})
E('leave_pauses',218,'Nia leaves little musical pauses',actor='e1',patients=['e49'],roles={'patient':[220]})
E('ribbon_bob',227,'ribbon bobs during Nia playing',type='move',patients=['e8'],roles={'patient':[226]})
M('practice_thu',230,'action','When-clause elaborates the same ongoing rehearsal.')
E('stay_door',232,'Mateo stays by door',type='state',actor='e2',roles={'actor':[231],'location':[235]})
E('tap_sometimes',239,'Mateo sometimes taps during practice',actor='e2',instruments=['e27'],roles={'effector':[238]})
E('not_tap_sometimes',242,'Mateo taps during the specified occasional interval',actor='e2',instruments=['e27'],factuality='negated',roles={'effector':[241]})
E('set_sheet',247,'Dalia sets signup sheet beside piano',type='move',actor='e3',patients=['e15'],roles={'actor':[245,246],'patient':[250],'landmark':[253]})
E('need_names',255,'Dalia needs Saturday program names',type='state',actor='e3',patients=['e54'],roles={'actor':[254],'patient':[257]})
E('lockup',263,'anticipated music room lockup',patients=['e5'],factuality='hypothetical')
U('signup_announcement',266,'e3','p7',kind='request',roles={'actor':[265]})
E('one_slot',268,'program has space for one more act',type='state',patients=['e16'])
E('imagine',275,'Nia imagines Mateo formal second-drum response',actor='e1',roles={'actor':[273]})
E('imagined_answer',279,'Mateo answers on second drum in Nia imagination',actor='e2',instruments=['e7'],factuality='hypothetical',roles={'actor':[276],'instrument':[285]})
E('look_mateo',290,'Nia looks at Mateo',type='perceive',actor='e1',patients=['e2'],roles={'actor':[289],'patient':[292]})
E('study_sheet',295,'Mateo studies signup sheet',type='perceive',actor='e2',patients=['e15'],roles={'actor':[293],'patient':[298]})
E('mouth_thin',301,'Mateo mouth is pressed into a thin line',type='state',patients=['e30'],roles={'patient':[300]})
E('possible_signup',308,'Nia writes both names',actor='e1',patients=['e55'],instruments=['e42'],factuality='hypothetical',roles={'actor':[306],'patient':[311]})
E('possible_accept',314,'Mateo might consent after seeing signup',type='speak',actor='e2',factuality='hypothetical',roles={'actor':[312]})
E('possible_see',318,'Mateo sees unchosen two-name signup',type='perceive',actor='e2',patients=['e55'],factuality='hypothetical',roles={'actor':[317],'patient':[319]})
E('choose_for_him',324,'two-name signup would substitute Nia choice for Mateo',actor='e1',patients=['e2'],factuality='hypothetical',roles={'affected_person':[328]})
E('take_pencil',330,'Nia takes pencil',type='obtain',actor='e1',patients=['e42'],roles={'actor':[329],'patient':[332]})
E('write_solo',334,'Nia writes her solo signup entry',actor='e1',patients=['e56'],instruments=['e42'],roles={'actor':[329],'content':[335,336,337]})
E('felt_loss',339,'Nia experiences solo choice as unfinished-play loss',type='feel',actor='e1')
E('simile_puttoy',341,'imagined comparison putting favorite toy away',type='move',actor='e1',patients=['e58'],factuality='hypothetical',roles={'patient':[345]})
E('simile_finish',349,'Nia finishes playing in the toy comparison',type='state',actor='e1',factuality='negated',roles={'actor':[347]})
E('simile_play',350,'unfinished toy play in comparison',actor='e1',patients=['e58'],factuality='hypothetical')
E('glance_entry',352,'Mateo glances at signup page',type='perceive',actor='e2',patients=['e15'],roles={'actor':[351],'patient':[355]})
E('still_duet',359,'Nia could still do a duet',actor='e1',patients=['e44'],factuality='hypothetical',roles={'actor':[356],'patient':[361]})
U('suggest',363,'e2','p13',['e1'],'suggestion',roles={'actor':[362]})
M('still_duet',366,'action','Nia acknowledges the same available possibility, not a completed act.')
U('not_know_reply',368,'e1','p28',['e2'],'clarify_uncertainty',roles={'actor':[367]})
E('not_know',372,'Nia knows whether Mateo wants a duet',type='state',actor='e1',factuality='negated',roles={'experiencer':[370]})
E('queried_desire',375,'Mateo desire for duet remains queried',type='feel',actor='e2',patients=['e44'],factuality='hypothetical',roles={'experiencer':[374],'patient':[376]})
E('look_folder',378,'Mateo looks down at folder',type='perceive',actor='e2',patients=['e17'],roles={'actor':[377],'patient':[382]})
E('not_program',383,'Mateo participates in a program duet',type='state',actor='e2',patients=['e44'],factuality='negated')
U('decline_program',383,'e2','p15',['e1'],'decline_limited',primary=False,scope='s0')
E('retain_solo',390,'formal act is retained as solo',type='state',patients=['e45'],roles={'patient':[388]})
U('confirm_solo',390,'e1','p16',['e2'],'decision',primary=False,scope='s0')
E('practice_home',392,'Nia practices song in kitchen Friday evening',actor='e1',patients=['e47'],instruments=['e6'],roles={'actor':[391],'patient':[394],'location':[399]})
E('pauses_enormous',405,'pauses seem enormous without another player',type='perceive',actor='e1',patients=['e49'],roles={'patient':[404]})
E('father_offer',409,'father offers to clap along',type='speak',actor='e4',recipient='e1',roles={'actor':[408]})
E('offered_clap',411,'father proposed accompaniment',actor='e4',factuality='hypothetical',roles={'actor':[408]})
E('headshake',415,'Nia declines father offer by shaking head',actor='e1',patients=['e32'],roles={'actor':[414],'effector':[417]})
E('try_dynamics',419,'Nia tries varied drum dynamics',actor='e1',patients=['e47'],instruments=['e6'],roles={'actor':[418]})
M('try_dynamics',420,'action','Making the beats softer/louder specifies the actual experiment.')
E('simile_steps',428,'imagined footsteps approach down hall',type='move',patients=['e59'],factuality='hypothetical',roles={'patient':[427],'path':[431]})
E('less_empty',436,'song sounds less empty after dynamics change',type='perceive',actor='e1',patients=['e47'],roles={'patient':[433]})
E('crowded',446,'Saturday music room crowded with chairs and cups',type='state',patients=['e5'],roles={'patient':[444],'contents':[449,452]})
E('drum_stool',457,'drum rests beside Nia stool before act',type='state',patients=['e6'],roles={'patient':[456],'landmark':[460]})
E('ribbon_rim',463,'ribbon lies against first drum rim',type='state',patients=['e8'],roles={'patient':[462],'landmark':[467]})
E('see_back',470,'Nia sees Mateo in back row',type='perceive',actor='e1',patients=['e2'],roles={'actor':[468],'patient':[471],'location':[475]})
E('hold_folder_sat',477,'Mateo still holds folder on Saturday',type='state',actor='e2',patients=['e17'],roles={'actor':[471],'patient':[479]})
U('introduce',482,'e3','p18',['e25'],'introduction',roles={'actor':[480,481],'topic':[485]})
E('sit_solo',492,'Nia sits down for solo',type='move',actor='e1',roles={'actor':[491]})
E('warm_palms',496,'Nia palms feel warm',type='feel',actor='e1',patients=['e33'],roles={'patient':[495]})
E('formal_solo',499,'Nia plays formal listed solo',actor='e1',patients=['e45'],instruments=['e6'],roles={'actor':[498]})
E('wide_pause',506,'solo musical pause is experienced as wide',type='perceive',actor='e1',patients=['e71'],roles={'patient':[505]})
E('fill_pause',509,'Nia fills pause with quieter beats',actor='e1',patients=['e71'],instruments=['e6'],roles={'actor':[508],'patient':[510],'result':[514,516]})
M('fill_pause',517,'action','Metaphorical path describes continuation through song, not physical construction.')
E('seat_response',527,'Mateo taps response from back row seat',actor='e2',patients=['e66'],roles={'result':[530],'location':[526]},support=[527,530,547,551,553,555])
E('look_drum',532,'Nia maintains gaze on drum',type='perceive',actor='e1',patients=['e6'],roles={'actor':[531],'effector':[534],'patient':[537]})
M('seat_response',[538,539],note='Written sound continuation of the same seat-response sequence, not extra speakers.')
M('formal_solo',541,'action','Next pattern within the ongoing formal solo.')
E('taps_clear',548,'Mateo answering taps become clearer',type='state',patients=['e66'],roles={'patient':[547]})
M('seat_response',546,'action','Answering describes ongoing offstage response to solo.')
E('not_leave_chair',553,'Mateo leaves the chair during the tapping interval',type='move',actor='e2',factuality='negated',roles={'actor':[551],'source':[555]})
E('shoulders_relax',558,'Nia shoulders loosen',type='state',patients=['e35'],roles={'patient':[557]})
E('finish_solo',560,'Nia finishes solo with three soft beats',actor='e1',patients=['e47','e64'],instruments=['e6'],roles={'actor':[559],'patient':[562],'result':[566]})
E('let_ring',568,'Nia lets last beat ring',actor='e1',patients=['e65'],roles={'patient':[571]})
E('last_ring',572,'last solo beat rings',type='state',patients=['e65'],roles={'patient':[571]})
E('applause',575,'Saturday audience applauds',actor='e25',roles={'metonymic_actor':[574]})
E('stand',577,'Mateo stands after solo',type='move',actor='e2',roles={'actor':[576]})
E('stop',579,'Mateo stops after standing',type='state',actor='e2')
E('look_second',581,'Mateo looks at second drum on shelf',type='perceive',actor='e2',patients=['e7'],roles={'actor':[580],'patient':[586],'location':[590]})
E('equal_size',592,'second drum matches first drum size',type='state',patients=['e7','e6'],roles={'patient':[591]})
E('not_wave',600,'Nia beckons Mateo to the performance area',actor='e1',patients=['e2'],factuality='negated',roles={'actor':[598],'patient':[601]})
E('set_drum_after',605,'Nia sets first drum beside stool after solo',type='move',actor='e1',patients=['e6'],roles={'actor':[603],'patient':[607],'landmark':[610]})
E('wait',612,'Nia waits while Dalia thanks audience',actor='e1')
E('thanks',616,'Dalia thanks audience',type='speak',actor='e3',recipient='e25',roles={'actor':[614,615],'addressee':[618]})
E('cross_shelf',620,'Mateo crosses to instrument shelf',type='move',actor='e2',roles={'actor':[619],'destination':[623]})
E('lift_second',625,'Mateo lifts second drum from shelf',type='obtain',actor='e2',patients=['e7'],roles={'actor':[619],'patient':[628]})
E('requested_answer',631,'Mateo tries the answer part',actor='e2',patients=['e53'],instruments=['e7'],factuality='desired',roles={'actor':[630],'patient':[634]})
U('ask_answer',636,'e2','p19',['e1'],'request_permission',roles={'actor':[635]})
U('accept_answer',638,'e1','p19',['e2'],'acceptance',roles={'actor':[639]})
E('sit_rug_together',641,'Nia and Mateo sit on rug',type='move',actor='e26',roles={'actor':[640],'destination':[644]})
E('informal_first',651,'Mateo taps once to test second drum',actor='e2',instruments=['e7'],roles={'actor':[650],'result':[655]})
M('informal_first',653,'action','Testing describes the purpose of the same single tap.')
E('nia_answers',657,'Nia answers Mateo informal tap',actor='e1',instruments=['e6'],roles={'actor':[656]})
E('mateo_two',659,'Mateo tries two beats',actor='e2',instruments=['e7'],roles={'actor':[658],'result':[661]})
E('space_three',663,'Nia leaves rhythmic room for three beats',actor='e1',recipient='e2',roles={'actor':[662],'recipient':[664]})
E('lemonade_gone',674,'picnic lemonade gone by late duet',type='state',patients=['e40'],roles={'patient':[672]})
E('duet_unlisted',677,'informal duet has no name or program listing or agreed ending',type='state',patients=['e46'],roles={'patient':[676]})
E('no_agreed_end',688,'Nia and Mateo agree an ending for the informal duet',actor='e26',factuality='negated',roles={'actor':[686],'content':[685]})
E('informal_duet',692,'Nia and Mateo keep playing informal rug duet',actor='e26',patients=['e46'],instruments=['e6','e7'],roles={'actor':[690],'patient':[676]})
E('cleanup_time',697,'time to put instruments away arrives',type='state',patients=['e68'])
E('putaway',699,'both drums are put away',type='move',actor='e26',patients=['e68'],roles={'patient':[701]})
E('return_first',704,'Nia returns borrowed first drum to shelf',type='move',actor='e1',patients=['e6'],roles={'actor':[703],'patient':[707],'destination':[710]})
M('borrow',706,'reference','Borrowed reuses original loan, not another borrowing.')
E('return_second',712,'Mateo places second drum beside first on shelf',type='move',actor='e2',patients=['e7'],roles={'actor':[711],'patient':[714],'landmark':[716]})
E('ribbon_hang',720,'first-drum ribbon hangs between two handles',type='state',patients=['e8'],roles={'patient':[719],'landmark':[724]})
E('ribbon_quiver',725,'ribbon quivers faintly at ending',type='move',patients=['e8'])
E('sound_fade',731,'last informal duet sound fades',type='state',patients=['e67'],roles={'patient':[730]})

# Grammatical operators and local relations, explicitly chosen in this story.
F([2,13,17,26,31,37,44,53,67,73,85,88,101,107,120,124,130,142,156,166,176,185,213,224,234,248,252,256,267,270,283,287,296,303,325,331,343,354,360,385,389,398,403,421,430,432,441,461,473,483,488,504,512,518,521,524,528,536,545,561,569,573,583,588,593,617,622,626,632,643,646,654,669,671,700,709,713,717,722,728],
  constituent_category='DP')
# Existential there and numeral one are not articles despite their shared DP frame.
for w in [267,270]: a.words[w].pop('constituent_category',None)
F([2,26,37,44,67,120,124,142,156,166,185,213,224,234,252,256,287,296,325,331,354,385,398,403,421,432,441,461,473,483,504,521,524,536,545,561,569,573,583,588,593,617,622,626,632,643,646,654,669,671,700,709,713,717,722,728],determiner_kind='definite_article',definiteness='definite')
F([13,17,31,53,73,85,88,101,107,130,176,248,283,303,343,360,389,430,488,512,518,528],determiner_kind='indefinite_article',definiteness='indefinite')
F([50,58,82,111,113,133,146,210,222,237,280,299,310,381,393,407,416,455,459,465,478,494,533,542,554,556,606,609,675,705],possessive_construction='prenominal_possessive')
# w82 is an object pronoun and w455/w556 are genitives, so remove the coarse label there.
for w in [82,455,556]: a.words[w].pop('possessive_construction',None)
F([50,58,111,113,133,146,210,222,237,280,299,310,381,393,407,416,459,465,478,494,533,542,554,606,609,675,705],determiner_kind='possessive',grammatical_case='genitive')
F([76,139,162,259,455,556,597],genitive_realization='singular_s_clitic',grammatical_case='genitive',possessive_construction='prenominal_s_genitive')
F(597,possessive_construction='independent_s_genitive',phrase_has_elision=True,
  reference_metonymic_link={'literal':'e1','referent':'e6','relation':'elided_possessed_drum'},evidence=[586,591,595,597],note='Nia’s retains Nia as possessor; the omitted drum is the comparison target e6, not an identity equation between Nia and a drum.')
F([0],determiner_kind='universal')
F([99,160,395],determiner_kind='demonstrative',definiteness='definite')
F(309,determiner_kind='total_dual',cardinal_value=2)
F(401,determiner_kind='additional_indefinite')
F([678,680,684],determiner_kind='negative')
F([69,189,192,254,365,370,630],grammatical_person=1,grammatical_case='subjective',mention_form='personal_pronoun')
F([91,172,356,374],grammatical_person=2,mention_form='personal_pronoun')
F([63,82,179,199,278,292,319,328,601,664],grammatical_case='objective',mention_form='personal_pronoun')
F([41,117,151,154,169,204,208,229,241,289,293,306,317,338,362,377,388,414,418,468,498,508,510,540,559,580,591,603,635,640,658,662,686,690,716],mention_form='personal_pronoun')
F([640,675,686,690],split_antecedent_ids=['e1','e2'],grammatical_number='plural')
F([8,16,22,126,140,147,163,188,220,238,257,311,404,422,427,449,452,495,534,547,557,566,661,701,724],grammatical_number='plural')
F([10,152,194,205,242,371,599],contraction_expansion=['did','not'])
F([194,371],contraction_expansion=['do','not'])
F(91,contraction_expansion=['you','will'])
F(267,contraction_expansion=['there','is'],expletive_reference=True,expletive_subject_id=a.anchor(267))
F(388,contraction_expansion=['it','is'])
F(552,contraction_expansion=['had','not'])
F(695,expletive_reference=True,expletive_subject_id=a.anchor(695))
F([10,152,194,205,242,371,552,599],proposition_polarity='negative')
F([383,645],proposition_polarity='negative')
for w,target in [(10,'disagree'),(152,'not_point'),(194,'not_want_watching'),(205,'not_ask'),(242,'not_tap_sometimes'),(371,'not_know'),(552,'not_leave_chair'),(599,'not_wave')]:
    F(w,negation_scope_id=EV[target],do_support_status='negative_auxiliary' if w!=552 else 'perfect_negative_auxiliary')
F(383,negation_scope_id='p15')
F(645,negation_scope_id='p_location_performance_space')
a.proposition('p24','Nia and Mateo sit in the performance space for the later duet.',[641,645,649])
F(645,negation_scope_id='p24')
F(678,negation_scope_id='p25'); a.proposition('p25','The informal duet has a name.',[676,678,679])
F(680,negation_scope_id='p26'); a.proposition('p26','The informal duet has a program listing.',[676,680,681,682])
F(684,negation_scope_id='p27'); a.proposition('p27','Nia and Mateo have agreed an ending for their informal duet.',[684,685,686,688])
F([171,307,313,323,357,366,469,629],verb_form='finite',modal_auxiliary_class='modal')
F(171,modal_base={'kind':'polite_invitation','content_id':'p4'},subject_auxiliary_inversion=True)
F(307,modal_base={'kind':'circumstantial_possibility','content_id':'p9'})
F(313,modal_base={'kind':'epistemic_possibility','content_id':'p10'})
F(323,modal_base={'kind':'hypothetical_consequence','content_id':'p11'})
F([357,366],modal_base={'kind':'circumstantial_possibility','content_id':'p13'})
F(469,modal_base={'kind':'perceptual_access','event_id':EV['see_back']})
F(629,modal_base={'kind':'polite_permission_request','content_id':'p19'},subject_auxiliary_inversion=True)
F(366,verb_phrase_ellipsis=True)
F(242,verb_phrase_ellipsis=True)
F([383,637,201],sentence_fragment_type='contextual_dialogue_response')
F([83,335,486],sentence_fragment_type='nominal_elaboration')
F([135,136,138,500,501,503,538,539],sentence_fragment_type='sound_representation')
F([6,36,42,62,81,96,104,115,118,123,129,141,149,155,164,168,170,183,203,209,216,227,232,239,247,266,290,330,334,339,352,363,368,378,392,405,409,415,419,434,445,457,463,482,492,496,499,506,509,527,532,541,548,558,560,568,575,577,579,581,592,605,612,616,620,625,636,638,641,651,657,659,663,673,677,691,696,704,712,720,731],verb_form='finite',tense='past')
F([70,190,195,255,372,375],verb_form='finite',tense='present')
F([12,64,72,92,95,127,153,173,175,197,206,263,308,314,318,324,359,411,436,553,572,600,631],verb_form='bare')
F([48,72,95,175,411,436,699],verb_form='infinitive')
for marker,head,controller in [(29,30,'e21'),(33,34,'e20'),(47,48,'e1'),(71,72,'e1'),(94,95,'e57'),(174,175,'e2'),(410,411,'e4'),(435,436,'e47'),(698,699,'e26')]:
    F(marker,constituent_category='infinitive_marker',syntactic_governor_id=a.anchor(head))
    F(head,infinitive_marker_id=a.anchor(marker))
F([15,19,28,106,191,218,279,295,341,350,420,428,477,517,546,653,692,725],verb_form='present_participle')
F([56,275,301,553,688,706],verb_form='past_participle')
F(295,aspect='progressive',progressive_auxiliary_id=a.anchor(294),auxiliary_chain=['be'])
F(275,aspect='perfect',perfect_auxiliary_id=a.anchor(274),auxiliary_chain=['have'])
F(553,aspect='perfect',perfect_auxiliary_id=a.anchor(552),auxiliary_chain=['have'])
F(688,aspect='perfect',perfect_auxiliary_id=a.anchor(687),auxiliary_chain=['have'])
F([56,301,706],participial_function='nominal_modifier')
F(191,gerund_function='verb_complement')
F(349,adjective_degree='positive',predicative_complement_id=a.anchor(349))
F(40,adverb_degree='superlative')
F(159,adverb_degree='comparative')
F([423,425,513,549],adjective_degree='comparative')
F(437,adverb_degree='comparative')
F([20,21,38,45,54,102,125,143,219,225,284,304,344,406,446,448,466,474,484,497,525,529,543,565,570,584,585,594,627,647,718,729],adjective_degree='positive')
for w in [284,584,627]: F(w,ordinal_rank=2)
for w,n in [(270,1),(564,3),(652,1),(660,2),(667,3),(723,2)]: F(w,cardinal_value=n)
F(667,phrase_has_elision=True,lexical_sense_id='three_beats_potential_space',factuality='hypothetical')
F(652,temporal_iteration_count=1)
F(594,quantity_comparison={'left':'e7','right':'e6','domain':'drum_size','relation':'equal'},quantity_comparison_cue='equal')
F([38,585,647],lexical_scale_dimension='size',lexical_scale_direction='small')
F(304,lexical_scale_dimension='width',lexical_scale_direction='thin')
F(497,lexical_scale_dimension='temperature',lexical_scale_direction='warm')
F([159,423,513,565],lexical_scale_dimension='sound_level',lexical_scale_direction='lower')
F(425,lexical_scale_dimension='sound_level',lexical_scale_direction='higher')

# Overt grammatical subjects: body-part/instrument syntax stays separate from actor.
SUBJECTS = {
'e1':[36,81,129,149,153,155,170,203,206,209,216,230,275,290,308,330,334,339,368,372,392,415,419,470,492,499,509,532,541,560,568,600,605,612,638,657,663,704],
'e2':[104,106,115,118,123,183,190,191,195,232,279,295,314,318,352,363,375,378,477,553,577,579,581,620,625,631,636,651,659,712],
'e3':[62,96,247,255,266,482,616], 'e4':[409,411],
'e5':[6,445,575], 'e6':[42,457], 'e7':[592], 'e8':[227,463,720,725],
'e18':[15], 'e19':[19], 'e21':[28], 'e24':[127], 'e27':[141,164,239,242],
'e30':[301], 'e33':[496], 'e35':[558], 'e40':[673], 'e47':[168,434,436],
'e49':[405], 'e71':[506], 'e66':[527,548], 'e65':[572], 'e26':[641,688,692], 'e46':[677], 'e67':[731], 'e61':[12],
}
for entity,words in SUBJECTS.items(): F(words,grammatical_subject_id=entity)
# Nonfinite controlled subjects need controller fields, not fabricated overt subjects.
for w,entity in [(48,'e1'),(64,'e1'),(72,'e1'),(95,'e57'),(175,'e2'),(218,'e1'),(341,'e1'),(350,'e1'),(420,'e1'),(517,'e1'),(653,'e2'),(699,'e26')]:
    F(w,subject_controller_id=entity)
for w,entity in [(36,'e6'),(64,'e6'),(106,'e17'),(123,'e24'),(129,'e48'),(155,'e48'),(209,'e6'),(247,'e15'),(255,'e54'),(295,'e15'),(308,'e55'),(318,'e55'),(330,'e42'),(334,'e56'),(392,'e47'),(415,'e32'),(470,'e2'),(477,'e17'),(482,'e45'),(509,'e71'),(532,'e34'),(541,'e48'),(560,'e47'),(605,'e6'),(616,'e25'),(625,'e7'),(704,'e6'),(712,'e7')]:
    F(w,grammatical_object_id=entity)
for w,entity in [(25,'e22'),(49,'e31'),(57,'e9'),(110,'e29'),(119,'e23'),(132,'e6'),(145,'e28'),(184,'e24'),(198,'e2'),(212,'e11'),(233,'e23'),(251,'e18'),(277,'e1'),(282,'e7'),(286,'e14'),(291,'e2'),(327,'e2'),(354,'e15'),(381,'e17'),(397,'e41'),(458,'e13'),(464,'e10'),(472,'e36'),(535,'e6'),(587,'e14'),(608,'e13'),(621,'e14'),(642,'e11'),(708,'e14'),(715,'e6'),(721,'e50')]:
    # The entry is only a preposition anchor; possessive/nominal offsets are fixed below.
    F(w,prepositional_object_id=entity)
for wrong,correct in [(354,353),(381,380)]:
    entity=a.words[wrong].pop('prepositional_object_id'); F(correct,prepositional_object_id=entity)
F(663,indirect_object_id='e2')
for w,kind in [(165,'temporal_when'),(228,'temporal_whenever'),(261,'temporal_before'),(316,'conditional_once'),(346,'temporal_before'),(373,'interrogative_if'),(550,'concessive'),(613,'temporal_while'),(694,'temporal_when'),(727,'temporal_as')]: F(w,subordinator_type=kind)
for w,kind in [(23,'addition'),(87,'addition'),(122,'addition'),(150,'contrast'),(215,'addition'),(321,'contrast'),(333,'addition'),(369,'contrast'),(413,'contrast'),(424,'addition'),(450,'addition'),(567,'addition'),(611,'addition'),(624,'addition'),(683,'addition')]: F(w,discourse_relation_kind=kind)
F(90,discourse_relation_kind='prerequisite_consequence')
F(387,discourse_relation_kind='decision_from_boundary')
F(693,discourse_relation_kind='concessive_continuation')
F(9,relative_marker_form='inanimate_relative',relative_gap_governor_id=a.anchor(12))

# Time: recurring Thursdays, particular Friday, then Saturday; no invented dates.
for w,day in [(1,'Thursday'),(76,'Saturday'),(181,'Saturday'),(244,'Friday'),(259,'Saturday'),(440,'Saturday')]: F(w,calendar_day_name=day)
F(0,temporal_frequency_class='weekly',temporal_recurrence={'weekday':'Thursday','interval':1,'unit':'week'})
F(68,temporal_duration={'value':1,'unit':'week','event_id':EV['borrow']},measure_unit='week')
F(100,temporal_deixis='same_day_afternoon',time_expression_id='time_thursday_afternoon')
F([158,207],temporal_phase_cue='repetition')
F([236,240],temporal_frequency_class='sometimes')
F(200,temporal_phase_cue='not_yet',temporal_anchor_unresolved=True)
F(261,temporal_signal_relation='before',temporal_deadline={'event_id':EV['need_names'],'before_event_id':EV['lockup']})
F(316,temporal_signal_relation='after_condition')
F(346,temporal_signal_relation='before',scope_id='s10')
F(396,time_expression_id='time_friday_evening',temporal_deixis='same_day_evening')
F([476],temporal_phase_cue='continuation')
F([515,578],temporal_signal_relation='then')
F([613,727],temporal_signal_relation='overlap')
F(668,temporal_bound_cue='by_the_time')
F(691,temporal_phase_cue='continuation')
F(694,temporal_signal_relation='when')

# Identity, part links, grounded spatial states and explicit custody.
for w,part,whole in [(51,'e31','e1'),(59,'e9','e6'),(112,'e29','e2'),(140,'e27','e2'),(147,'e28','e2'),(300,'e30','e2'),(417,'e32','e1'),(467,'e10','e6'),(495,'e33','e1'),(534,'e34','e1'),(557,'e35','e1')]:
    F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':'s0'})
F(724,part_whole_relation={'parts':[{'part_id':'e9','whole_id':'e6'},{'part_description':'second drum handle','whole_id':'e7'}],'scope_id':'s0'})
F([54,225,718],appearance_color=B('e8','red'))
F(466,material_composition=B('e10',{'material':'wood'}))
F(451,material_composition=B('e39',{'material':'paper'}))
F(56,object_connection_state=B('e8','knotted_to_handle'),spatial_configuration=B('e8',{'landmark':'e9','relation':'around'}))
F(48,spatial_configuration=B('e6',{'landmark':'e31','relation':'beneath'},factuality='hypothetical'))
F(106,possession_holder=B('e17',{'holder':'e2'}),spatial_contact=B('e17',{'touches':'e29'}))
F(118,spatial_configuration=B('e2',{'landmark':'e23','relation':'near'}))
F(141,event_effector=B('e2',{'event_id':EV['tap_first'],'effector':'e27'}),spatial_contact=B('e27',{'touches':'e28'}))
F([164,239],event_effector=B('e2',{'effector':'e27'}))
F(209,motion_destination=B('e6',{'event_id':EV['carry_rug'],'landmark_id':'e11','role':'destination'}))
F(216,event_setting=B('e1',{'event_id':EV['practice_thu'],'setting':'e11'}))
F(232,spatial_configuration=B('e2',{'landmark':'e23','relation':'by'}))
F(247,spatial_configuration=B('e15',{'landmark':'e18','relation':'beside'}))
F(277,spatial_configuration=B('e2',{'landmark':'e1','relation':'beside'},'s7',factuality='hypothetical'))
F(285,possession_user=B('e7',{'user':'e2'},'s7',factuality='hypothetical'))
F(330,possession_holder=B('e42',{'holder':'e1'}))
F(334,event_instrument_binding=B('e42',{'event_id':EV['write_solo'],'used_on':'e15'}),event_result_entity=B('e56',{'event_id':EV['write_solo'],'carrier':'e15'}),communication_channel='writing')
F(392,event_setting=B('e1',{'event_id':EV['practice_home'],'setting':'e41'}))
F(446,containment_contents=B('e5',{'contents':['e38','e39'],'exhaustive':False}))
F(452,containment_contents=B('e39',{'contents':['e40'],'exhaustive':False}))
F(457,spatial_configuration=B('e6',{'landmark':'e13','relation':'beside'}))
F(463,spatial_contact=B('e8',{'touches':'e10'}))
F(471,spatial_configuration=B('e2',{'landmark':'e36','relation':'in'}))
F(477,possession_holder=B('e17',{'holder':'e2'}))
F(553,spatial_configuration=B('e2',{'landmark':'e37','relation':'still_seated_in','time':'during_solo_response'}))
F(586,spatial_support=B('e7',{'supported_by':'e14'}))
F(605,spatial_configuration=B('e6',{'landmark':'e13','relation':'beside'}))
F(620,motion_destination=B('e2',{'event_id':EV['cross_shelf'],'landmark_id':'e14','role':'destination'}))
F(625,possession_holder=B('e7',{'holder':'e2'}),motion_source=B('e7',{'event_id':EV['lift_second'],'landmark_id':'e14','role':'source'}))
F(641,spatial_configuration=B('e26',{'landmark':'e11','relation':'on','excluded_landmark':'e12'}))
F(651,possession_user=B('e7',{'user':'e2'}))
F(657,possession_user=B('e6',{'user':'e1'}))
F(704,motion_destination=B('e6',{'event_id':EV['return_first'],'landmark_id':'e14','role':'destination'}),spatial_support=B('e6',{'supported_by':'e14'}))
F(712,motion_destination=B('e7',{'event_id':EV['return_second'],'landmark_id':'e14','role':'destination'}),spatial_configuration=B('e7',{'landmark':'e6','relation':'beside'}),spatial_support=B('e7',{'supported_by':'e14'}))
F(720,spatial_configuration=B('e8',{'landmark':'e50','relation':'between_members'}))
F(64,possession_borrower=B('e6',{'borrower':'e1'}),possession_lender=B('e6',{'lender':'e3'}),transfer_kind=B('e6','temporary_loan'),transfer_completion=B('e6',{'completed':True}),evidence=[62,64,65,68,706],note='The initial permission plus later explicitly borrowed drum establishes actual loan. Neither lender nor user is thereby asserted owner.')
F(62,permission_grantor_id='e3',permission_recipient_id='e1',permission_content_id='p1',permission_status='granted_limited')
F(704,transfer_completion=B('e6',{'completed':True,'kind':'return_to_storage','destination':'e14'}))
F(712,transfer_completion=B('e7',{'completed':True,'kind':'return_to_storage','destination':'e14'}))

# Musical readings and comparisons; sound descriptors are not literal people/paths.
F(12,lexical_sense_id='harmonize_musically')
F(15,reference_metonymic_link={'literal':'e18','relation':'instrument_for_unnamed_player'},evidence=[14,15,16],note='Piano is the surface subject, but player is unstated. No invented named performer.')
F(19,reference_metonymic_link={'literal':'e19','relation':'instrument_for_unnamed_player'})
F(21,figurative_mapping={'target_id':'e62','source_image':'sleepiness','kind':'personification','literal_event':False})
F([30,34],figurative_mapping={'target_id':'e20','source_image':'teaching_an_unruly_pupil','kind':'personification','literal_event':False},evidence=[24,28,30,32,34],note='The narrator humorously describes attempting to control a tambourine; no mental life or literal learning is assigned to the instrument.')
F([135,136,138,500,501,503],lexical_sense_id='onomatopoeic_drum_strike')
F([137,220,404,502,505,510],lexical_sense_id='musical_rest')
F([89,95,164,279,546,633,657],lexical_sense_id='musical_call_and_response')
F(144,reference_identity_conflict={'left':'e48','relation':'same_rhythm_different_sound_occurrence','right_event_id':EV['tap_first']})
# This is compatible pattern identity, not a diagnostic conflict.
a.words[144].pop('reference_identity_conflict')
F(144,lexical_sense_id='same_abstract_rhythmic_pattern')
F(155,event_iteration=B('e1',{'event_id':EV['repeat_pattern'],'prior_event_id':EV['test_pattern'],'cue':'again'}))
F(159,object_sound_level=B('e6',{'event_id':EV['repeat_pattern'],'comparison':'softer_than_previous'}))
F(338,propositional_antecedent_id='p12',evidence=[334,337,338,339,345],note='It refers to choosing/registering the solo, not to the drum or an actual toy.')
F(322,propositional_antecedent_id='p9')
F(340,figurative_mapping={'target_id':'p12','source_image':'putting_away_favorite_toy_before_finished_playing','kind':'simile','literal_event':False})
F(406,figurative_mapping={'target_id':'e49','source_image':'enormous_physical_extent','kind':'metaphor','literal_event':False})
F([423,425],event_manner=B('e1',{'event_id':EV['try_dynamics'],'manner':'vary_sound_dynamics'}))
F(426,figurative_mapping={'target_id':'e47','source_image':'footsteps_coming_down_hall','kind':'simile','literal_event':False})
F(438,figurative_mapping={'target_id':'e47','source_image':'less_empty_container','kind':'metaphor','literal_event':False})
F(457,lexical_sense_id='remain_in_readiness',figurative_mapping={'target_id':'e6','source_image':'waiting_person','kind':'personification','literal_event':False})
F(506,figurative_mapping={'target_id':'e71','source_image':'opening_wide_space','kind':'metaphor','literal_event':False})
F(519,figurative_mapping={'target_id':'e47','source_image':'path_through_space','kind':'metaphor','literal_event':False})
F(529,object_sound_level=B('e66','faint'))
F(549,object_sound_level=B('e66','clearer'))
F(565,object_sound_level=B('e64','soft'))
F(574,reference_metonymic_link={'literal':'e5','referent':'e25','relation':'room_for_its_audience'},evidence=[574,575,616,618],note='Applause is by the audience; room remains the grammatical surface subject.')
F(665,lexical_sense_id='rhythmic_time_for_response',figurative_mapping={'target_id':'e46','source_image':'making_room','kind':'metaphor','literal_event':False})
F(674,explicit_zero_count={'entity_id':'e40','domain':'remaining_picnic_lemonade','value':0},evidence=[672,673,674],note='Gone establishes none remaining at this time. Consumption or removal is not separately invented.')
F(731,object_sound_level=B('e67','fading'))

# Consent and desires are anchored to their particular action, not global traits.
F(70,goal_owner_id='e1',goal_content_id='p2',goal_status='active',goal_polarity='achieve',
  goal_scope_bundle={'owner_id':'e1','intention_event_id':EV['want_duet'],'scope_id':'s1','assertion_status':'attributed_claim'},
  goal_deadline={'anchor':'Saturday_picnic','relation':'at'},goal_resource_ids=['e6'],intention_publicity='communicated')
F(170,request_action_id='p4',request_acceptance_status='public_attention_boundary_then_explicit_program_decline')
F(190,affect_experiencer_id='e2',affect_kind='enjoyment_of_playing',affect_scope_bundle={'experiencer_id':'e2','content_event_id':EV['enjoyed_play'],'scope_id':'s4','assertion_status':'attributed_claim'})
F(195,goal_owner_id='e2',goal_content_id='p5',goal_status='explicitly_not_desired',
  goal_scope_bundle={'owner_id':'e2','intention_event_id':EV['not_want_watching'],'scope_id':'s4','assertion_status':'attributed_claim'},
  boundary_preference={'owner_id':'e2','excluded':'p5','time':'yet','scope_id':'s4','assertion_status':'attributed_claim'},
  evidence=[189,190,191,194,195,196,197,199,200],note='Negated desire for public watching is not an asserted active avoidance goal or a refusal of all music or friendship.')
F(203,dialogue_response_to_id=EV['boundary'],dialogue_turn_function='accept_boundary')
F(266,request_action_id='p7')
F(275,imaginer_id='e1',imagined_content_id='p8',imagined_world_id='s7',imagination_function='desired_duet_envisaging')
F(301,affect_observer_attribution={'observer':'narrator_or_Nia','experiencer_id':'e2','cue':'mouth_pressed_thin','interpretation':'possible_tension','scope_id':'s0','assertion_status':'candidate'},
  evidence=[290,293,295,300,301,304,305],note='Thin mouth is explicit. Tension is only a candidate; no exact fear or permanent shyness is asserted.')
F([308,314,318,324],assertion_status='attributed_claim')
F(308,plan_commitment_status='considered_not_chosen',intention_publicity='private_consideration')
F(314,belief_holder_id='e1',belief_content_id='p10',belief_certainty='possible',epistemic_attitude_kind='speculation')
F(324,belief_holder_id='e1',belief_content_id='p11',epistemic_attitude_kind='recognition_of_agency_cost',evidence=[306,308,312,314,322,324,326,328,334,337],note='Free indirect alternative is attributed to Nia; possible later yes is not actual consent, and actual signup is solo.')
F(334,plan_revision={'old':'p2','new':'p12','dimension':'formal_program_entry','duet_desire_not_globally_cancelled':True},plan_commitment_status='adopted_solo_entry',goal_owner_id='e1')
F(339,affect_experiencer_id='e1',assertion_status='asserted',
  affect_observer_attribution={'experiencer_id':'e1','interpretation':'disappointment','scope_id':'s0','assertion_status':'candidate'},
  evidence=[334,337,339,340,344,345,346,349,350],note='The narrator explicitly supplies an unfinished-toy comparison. Disappointment is an interpretation of that comparison, not a literal lost toy or a promise of abandoning all duets.')
F(363,dialogue_response_to_id=EV['write_solo'],dialogue_turn_function='suggest_alternative',communication_channel='quiet_speech')
F(368,dialogue_response_to_id=EV['suggest'])
F(372,knowledge_gap_holder_id='e1',knowledge_gap_content_id='p14',belief_holder_id='e1',belief_content_id='p14',belief_certainty='unresolved')
F(383,trust_holder_id='e2',consent_status='explicit_limited_no',
  consent_scope={'giver_id':'e2','other_id':'e1','action':'p15','time':'Saturday_program','scope_id':'s13','assertion_status':'attributed_claim'},
  boundary_preference={'owner_id':'e2','excluded':'p15'},dialogue_response_to_id=EV['not_know_reply'],
  evidence=[383,384,385,386,629,631,634],note='Not on the program narrows the refusal to formal participation. Later voluntary participation does not retrospectively remove that boundary.')
F(390,dialogue_response_to_id=EV['decline_program'],plan_commitment_status='solo_designation_retained')
F(409,speaker_id='e4',speech_act_kind='offer',utterance_id=EV['father_offer'],utterance_content_id='p17',addressee_ids=['e1'])
F(415,speaker_id='e1',speech_act_kind='decline',communication_channel='head_gesture',utterance_id=EV['headshake'],utterance_content_id='p23',dialogue_response_to_id=EV['father_offer'],request_acceptance_status='declined',
  evidence=[409,411,414,415,417],note='The explicit contrast and headshake support declining this accompaniment offer, not an aversion to all joint music.')
F(496,affect_experiencer_id='e1',affect_observer_attribution={'experiencer_id':'e1','cue':'warm_palms','interpretation':'possible_performance_arousal','scope_id':'s0','assertion_status':'candidate'},evidence=[482,490,491,495,496,497],note='Warm palms are explicit; excitement versus anxiety is unresolved. No diagnosis or fixed emotional intensity.')
F(558,affect_experiencer_id='e1',affect_observer_attribution={'experiencer_id':'e1','cue':'shoulders_loosen','interpretation':'possible_easing_of_tension','scope_id':'s0','assertion_status':'candidate'},
  evidence=[547,548,549,556,557,558],note='Physical loosening is explicit; emotional relief is a supported candidate, without asserting its cause or full recovery.')
F(616,speaker_id='e3',speech_act_kind='thanks',utterance_id=EV['thanks'],addressee_ids=['e25'])
F(636,request_action_id='p19',request_acceptance_status='accepted_next_turn',dialogue_turn_function='initiate_voluntary_participation')
F(638,permission_grantor_id='e1',permission_recipient_id='e2',permission_content_id='p19',permission_status='granted',dialogue_response_to_id=EV['ask_answer'],
  consent_status='explicit_limited_yes',consent_scope={'giver_id':'e1','other_id':'e2','action':'p19','scope_id':'s18','assertion_status':'attributed_claim'})
F(651,event_volition=B('e2',{'event_id':EV['informal_first'],'intentional':True}),event_goal_role=B('e2',{'event_id':EV['informal_first'],'goal_state':'test_second_drum_sound'}))
F(692,event_collective_participants=B('e26',{'event_id':EV['informal_duet'],'actors':['e1','e2']}),cooperation_goal_id='p20',cooperation_commitment='joint_activity_observed')
F(677,explicit_zero_count={'entity_id':'e46','domains':['name','program_listing','agreed_ending'],'value':0,'time':'during_informal_duet'},evidence=[676,678,679,680,682,684,685,688],note='The three absences are restricted to informal duet metadata; they do not imply absence of music, eventual stopping, or the separate solo program entry.')
F(527,evidence=[523,526,527,530,546,547,551,553,555],note='Later explicit Mateo/chair clause resolves the source of seat taps retrospectively. The surface subject is tap; the semantic actor is Mateo. No drum is assigned to those taps because he acquires the second drum only later.')
F(699,event_collective_participants=B('e26',{'actors':['e1','e2'],'subevents':[EV['return_first'],EV['return_second']]}))
F(720,evidence=[55,59,707,712,714,716,719,720,724],note='The ribbon remains attached to the original drum; it hangs between the handles of two now-adjacent drums. No shared ribbon attachment or merged drum identity is inferred.')

# Interpretation stays explicitly candidate and is tied to local evidence.
F(692,narrative_thread_id='thread_duet_and_choice',narrative_change_dimension='mode_of_shared_music',
  narrative_change_evidence={'before':'p4','after':'p20','relation':'formal_invitation_replaced_by_voluntary_informal_play','assertion_status':'candidate'},
  narrative_resolution_evidence={'criterion':'p2','outcome':'p20','status':'shared_music_realized_outside_formal_program','assertion_status':'candidate'},
  narrative_theme_candidate={'content':'leaving_other_people_a_choice_can_allow_voluntary_cooperation','assertion_status':'candidate'},
  evidence=[170,195,206,308,324,334,383,390,600,612,625,636,638,641,692],note='Narrative reading contrasts a wanted formal duet with later freely initiated informal music. It does not claim Mateo agreed to the original program invitation or overcame all discomfort.')
F(731,narrative_motif_link={'earlier_words':[55,226,462],'current_word':719,'relation':'ribbon_now_between_two_drums','assertion_status':'candidate'},
  narrative_closure_candidate={'thread':'thread_duet_and_choice','cue':'two_returned_drums_and_fading_last_sound','assertion_status':'candidate'},
  evidence=[55,227,462,704,712,719,724,731],note='Closing image links the earlier single borrowed drum to two returned drums; interpreted closure is distinct from factual instrument positions.')

# Corrections from reading every assembled paragraph and its exact lexical heads.
for w in [115,339]: a.words[w].pop('grammatical_subject_id',None)
F(197,verb_form='present_participle')
F(318,verb_form='finite',tense='past')
F(470,verb_form='bare')
F(301,participial_function='absolute_clause_predicate')
a.words[552].pop('do_support_status',None)
F(541,grammatical_object_id='e69')
M('formal_solo',544,'subpart','Next pattern is a part of the ongoing solo; it is not assumed identical to the initial tested pattern.')
F(337,reference_metonymic_link={'literal':'e56','referent':'e45','relation':'written_entry_names_musical_act'})
F(262,grammatical_person=1,grammatical_number='plural',mention_form='personal_pronoun',
  evidence=[254,261,262,263,265],note='Inclusive/exclusive we includes Dalia but its complete membership is unspecified; no exact group entity is invented.')
F(315,speech_act_kind='hypothetical_acceptance',consent_status='hypothetical_not_actual',assertion_status='attributed_claim',factuality='hypothetical')
for head,mods in [(5,[3,4]),(78,[77]),(109,[108]),(250,[249]),(298,[297]),(444,[442,443]),(590,[589]),(634,[633]),(649,[648]),(682,[681])]:
    F(mods,dependency_relation='nominal_modifier',syntactic_governor_id=a.anchor(head))
F([46,595],lexical_sense_id='physical_size')
F(86,lexical_sense_id='proposed_musical_beat',factuality='desired')
F(114,lexical_sense_id='personal_name',syntactic_governor_id=a.anchor(115))
F(186,lexical_sense_id='occupants_of_room')
F(268,lexical_sense_id='available_program_capacity')
F(271,quantity_comparison_cue='additional')
F(305,lexical_sense_id='mouth_configuration_line',syntactic_governor_id=a.anchor(301))
F(326,lexical_sense_id='decision_about_program_participation',propositional_antecedent_id='p9')
F(400,explicit_zero_count={'domain':'additional_player_during_home_rehearsal','value':0,'scope_id':'s0'})
F(402,lexical_sense_id='additional_musical_performer')
F(422,lexical_sense_id='drum_beat_sound',event_bindings=[{'event_id':EV['try_dynamics'],'role':'patient','scope_id':'s0'}])
F(679,lexical_sense_id='formal_name_of_duet',factuality='negated')
F(682,lexical_sense_id='entry_in_formal_music_program',factuality='negated')
F(685,lexical_sense_id='agreed_musical_ending',factuality='negated')
F(434,temporal_phase_cue='onset',event_bindings=[{'event_id':EV['less_empty'],'role':'phase_operator','scope_id':'s0'}])
F(691,event_bindings=[{'event_id':EV['informal_duet'],'role':'phase_operator','scope_id':'s0'}])

feedback={
 'summary':'Manual whole-story annotation preserves explicit formal-program refusal, offstage response, later voluntary informal duet, and separate drum custody/returns.',
 'ambiguities':[
   {'words':[15,19],'issue':'Piano/flute subjects stand for playing; individual players are unspecified and remain unregistered.'},
   {'words':[262,263],'issue':'Dalia’s we at lockup has no exact membership. Lockup remains prospective, not an invented actual closing event.'},
   {'words':[301,496,558],'issue':'Bodily cues remain explicit; tension/arousal/relief readings are candidate only.'},
   {'words':[527,530,547,551],'issue':'Seat tap source resolves retrospectively to Mateo; surface or instrument used on Saturday is unspecified.'},
   {'words':[625,628],'issue':'Second drum is lifted and later returned; no separate loan permission or ownership is stated.'},
 ],
 'feature_gaps':[
   {'meaning':'musical call-and-response, pattern identity versus sound occurrence, and dynamic variation','handling':'Existing lexical senses, event IDs, sound-level bundles, and explicit composition/part entities suffice for this story; no new alias proposed.'},
 ],
 'prompt_feedback':[
   'Keep consent scope narrow: declining program participation is compatible with later seat tapping and informal joint playing.',
   'Add an example separating instrument/body-part grammatical subjects from performer actors, without inventing unnamed player identities.',
   'Possessive ellipsis such as Nia’s in a size comparison needs an explicit possessor-to-omitted-object bridge.',
 ],
 'coverage_notes':'All 39 paragraphs and 732 words manually interpreted. Explicit lexical decisions, semantic event/role links, physical and imagined scopes, dialogue/consent, custody, rhythm, figurative comparisons, grammatical and temporal operators. Only applicable sparse fields emitted.',
 'reviewed_all_words':True,
}
a.save(feedback)
# Keep the optional human-readable review view synchronized with final JSONL.
review=[]
for p,para in enumerate(a.paragraphs):
    review.append(f'P{p}')
    for word in para['words']:
        w=word['w']; row=a.words[w]
        review.append(f"{w}:{row['token']} {row['pos']}/{row['lemma']} "
                      + ' '.join(str(row.get(k,'')) for k in ['entity_id','role','event','factuality','scope_id']))
(a.output/'review_words.txt').write_text('\n'.join(review)+'\n')

