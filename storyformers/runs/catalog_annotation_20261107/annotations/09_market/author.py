"""Manual retrospective market annotation, frozen v2 conventions."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a = Annotation('09_market', prompt_version='v2')
for key in ['appearance_color', 'part_whole_relation', 'figurative_mapping']:
    a.use_extension(key)

# Each occurrence has an explicit contextual POS and lemma.
LEX = [
'adp=by num=nine adv=o’clock det=the n=fruit n=market v=smell adp=of n=orange n=peel adj=damp n=crate conj=and det=the n=cinnamon n=bun adp=from det=the n=bakery n=stall n=Mina v=stand adp=behind det=her n=aunt n=Farah n=apple v=polish det=a adj=red pron=one adp=with det=her n=sleeve',
'pron=I v=can v=do n=Mrs n=Dutta n=order pron=she v=say adv=all adp=by pron=myself',
'n=Aunt n=Farah v=glance adp=at det=the adj=handwritten n=list num=two n=kilo adp=of adj=tart n=apple adp=for det=her n=grandson n=birthday n=pie det=our n=scale v=be adp=at det=the n=repair n=shop conj=so pron=you v=need part=to v=borrow n=Mr n=Boulos',
'n=Mina n=grin v=widen n=Aunt n=Farah v=have v=let pron=she v=stack n=fruit conj=and v=make n=change conj=but adv=never v=fill det=an n=order adv=alone pron=I v=bring pron=it adv=back adj=clean',
'adp=at det=the adj=next n=stall n=Mr n=Boulos v=be v=arrange n=jar adp=of n=olive det=his n=brass n=scale v=sit adp=beside pron=they det=its adj=round n=dial v=shine',
'v=may pron=I v=borrow det=your n=scale intj=please n=Mina v=ask',
'adv=certainly v=mind det=the n=pan pron=it v=wobble conj=if pron=you v=bump det=the n=counter pron=he v=lift pron=it adv=over conj=and v=set pron=it adp=in det=her n=hand conj=and v=bring pron=it adv=back adp=before pron=I v=sell det=my adj=last n=olive',
'n=Mina v=carry pron=it adv=carefully adp=to det=the n=apple n=stall n=Mrs n=Dutta det=their adj=next n=door n=neighbor adp=at n=home v=be v=wait adp=with det=a n=cloth n=shopping n=bag v=fold adp=over det=her n=arm',
'pron=I v=have part=to v=catch det=the num=eleven num=twenty n=bus pron=she v=say det=my n=grandson v=arrive adv=tonight conj=and pron=he adv=already v=tell pron=everyone pron=he v=expect n=pie',
'pron=I v=be adj=quick n=Mina v=promise',
'pron=she v=choose adj=firm adj=speckled n=apple conj=and v=set pron=they num=one adp=by num=one adp=on det=the n=brass n=pan det=the n=needle v=climb num=one n=kilo num=one conj=and det=a n=half adv=then num=two n=Mina v=slide det=the n=apple adp=into det=a n=paper n=bag',
'adv=exactly num=two n=kilo pron=she v=say',
'n=Mrs n=Dutta v=reach adp=for det=the n=bag conj=but n=Mina v=turn part=to v=return det=the n=scale adv=first det=its n=pan v=be adj=empty det=the n=needle adv=still v=point adp=at det=a n=quarter n=kilo',
'n=Mina v=frown pron=she v=lift det=the n=pan det=a adj=curled adj=green n=leaf v=be v=pinch adp=beneath det=its n=rim v=press det=the n=scale adv=down pron=she v=pluck pron=it adj=free det=the n=needle v=spring adv=back adp=to num=zero',
'v=wait pron=she v=say',
'n=Mrs n=Dutta v=pause det=her n=finger adp=on det=the n=bag n=handle pron=what v=be pron=it',
'n=Mina v=put det=the n=bag adv=back adp=on det=the n=pan det=the n=needle v=stop adp=at num=one conj=and num=three n=quarter n=kilo',
'adp=for det=a n=moment det=the n=market n=bustle v=seem part=to v=hush adp=around pron=she n=Mina v=can v=hand adv=over det=the n=bag conj=and det=no pron=one v=will v=know n=Mrs n=Dutta v=will v=be adp=on det=her n=bus conj=and n=Aunt n=Farah v=will v=think pron=she v=do det=the n=job adv=perfectly',
'adv=instead n=Mina v=push det=the n=bag adv=gently adv=away adp=from n=Mrs n=Dutta pron=I adj=sorry det=the n=leaf v=make det=the n=scale v=say pron=there v=be pron=more conj=than pron=there v=be pron=you adj=short det=a n=quarter n=kilo',
'n=Mrs n=Dutta v=look adp=at det=the n=dial adv=then adp=at n=Mina v=can pron=you v=fix pron=it adp=before det=my n=bus',
'pron=I v=can v=try n=Mina n=cheek v=feel adj=hot pron=I v=weigh det=the n=apple adv=again conj=and pron=I v=tell n=Aunt n=Farah pron=what v=happen',
'pron=she v=empty det=the n=bag adp=into det=a n=crate conj=and v=start adv=over v=check det=the n=dial adp=between det=each n=handful det=this n=time pron=it v=take num=three adj=small n=apple part=to v=bring det=the n=needle adp=to adv=exactly num=two n=kilo pron=she v=fold det=the n=top adp=of det=the n=bag conj=and v=tie pron=it adp=with n=twine',
'n=Aunt n=Farah v=come adv=back v=carry det=an adj=empty n=crate adv=just conj=as n=Mrs n=Dutta v=check det=the n=time',
'pron=what v=happen pron=she v=ask',
'n=Mina v=show pron=she det=the adj=curled n=leaf pron=I v=think det=the n=order v=be adj=right conj=but pron=it v=be pron=I v=stop adp=before pron=she v=take pron=it',
'n=Aunt n=Farah v=examine det=the n=scale conj=and v=nod adj=good n=catch n=Mr n=Boulos v=shall v=know adv=too',
'pron=I v=tell pron=he n=Mina v=say conj=and pron=I v=return det=the n=scale',
'n=Mrs n=Dutta v=tuck det=the n=bag adp=into det=her n=cloth n=shopping n=bag pron=I adv=still v=catch det=my n=bus conj=and pron=you v=save det=my n=pie adp=from v=be det=a adj=little adj=short adp=on n=apple',
'pron=she v=leave det=a n=coin adp=on det=the n=counter adp=for det=the n=order conj=and v=hurry adp=toward det=the n=market n=gate n=Mina v=watch conj=until pron=she v=turn det=the n=corner adv=then v=carry det=the n=scale adv=back adp=to n=Mr n=Boulos',
'pron=I v=find det=a n=leaf adp=under det=the n=pan pron=she v=tell pron=he pron=it v=be v=make det=the n=dial v=read adv=too adj=high pron=I v=clean pron=it conj=and v=check pron=it adv=again',
'n=Mr n=Boulos v=turn det=the n=scale adv=over adv=then v=give n=Mina det=a adj=serious n=nod v=thank pron=you adp=for v=tell pron=I pron=you v=may v=borrow pron=it adv=again conj=whenever pron=you v=need pron=it',
'adp=by n=closing n=time n=Aunt n=Farah v=have v=put n=Mina n=name adp=at det=the n=top adp=of n=tomorrow n=order n=list conj=when n=Mrs n=Dutta v=return adp=with det=a adj=warm n=slice adp=of n=birthday n=pie v=wrap adp=in det=a n=napkin n=Mina v=set pron=it adp=beside det=the n=scale det=the n=dial v=rest adv=neatly adp=on num=zero conj=and det=the n=pie adj=golden n=crust v=glow adp=in det=the adj=last n=square adp=of n=sunlight',
]
for p,encoded in enumerate(LEX):
    pairs=[pair.split('=',1) for pair in encoded.split()]
    words=a.paragraphs[p]['words']
    assert len(words)==len(pairs),(p,len(words),len(pairs))
    a.tag(p,[x[0] for x in pairs],{w['w']:x[1] for w,x in zip(words,pairs)})

ENTS=[
('Mina','person',[20,23,32,34,40,44,70,76,83,95,122,127,136,148,160,209,212,214,240,251,260,279,281,298,309,323,350,351,374,380,389,416,418,424,427,431,437,443,474,505,511,520,540,543,546,566,593,608,615,626,641,646,650,656,666,690]),
('Aunt Farah','person',[24,25,45,46,79,80,370,371,439,440,486,487,503,507,526,527,662,663]),
('Mrs. Dutta','person',[37,38,58,168,169,173,185,187,195,197,253,254,311,312,314,362,363,367,387,388,403,408,409,422,496,497,523,550,551,556,560,563,568,577,596,676,677]),
('Mr. Boulos','person',[74,75,104,105,111,124,140,155,157,535,536,542,606,607,617,633,634,649]),
('Mrs. Dutta grandson','person',[59,198,202,206]),
('fruit market','market',[5,344,591]),
('orange peel','peel',[9]),('damp crates','crate_group',[11]),('cinnamon buns','bun_group',[15]),('bakery stall','stall',[19]),
('Farah apple stock','apple_group',[26,56]),('red apple being polished','apple',[30]),('Mina sleeve','clothing_part',[33]),
('Mrs. Dutta apple order','order',[39,93,377,420,514,518,586]),('current handwritten order list','list',[51]),('grandson birthday pie','pie',[61,208,569,685]),
('Farah scale at repair shop','scale',[63]),('repair shop','shop',[68]),
('Boulos brass scale','scale',[97,113,117,125,142,146,152,162,265,267,296,395,549,603,628,631,637,653,658,695]),
('Mina grin','facial_expression',[77]),('fruit from earlier permitted work','fruit_group',[85]),('change money','money',[88]),('Boulos stall','stall',[103]),
('olive jars','jar_group',[108,116]),('olives for sale','olive_group',[110]),('scale dial','dial',[119,413,455,622,697]),
('brass weighing pan','pan',[132,133,228,268,284,292,330,614]),('Boulos counter','counter',[139]),('Mina hands','body_part_group',[149]),('Farah apple stall','stall',[167]),
('family home','home',[175]),('Dutta cloth shopping bag','bag',[182,559]),('Dutta arm','body_part',[186]),('eleven twenty bus','bus',[194,368,423,564]),
('grandson reported audience','person_group',[205]),('apple batch for this order','apple_group',[218,221,243,434,576]),
('scale needle','indicator',[230,272,303,332,469]),('paper apple bag','bag',[247,258,318,326,356,383,446,480,483,525,554]),
('curled green leaf','leaf',[288,300,392,510,611,618]),('pan rim','rim',[293]),('Dutta fingers','body_part_group',[315]),('paper bag handles','handle_group',[319]),
('market bustle','ambient_activity',[345]),('hypothetical people who could know','person_group',[359]),('Mina cheeks','body_part_group',[428]),
('crate used when restarting weighing','crate',[449]),('three small apples used in correction','apple_group',[465]),('paper bag top','bag_part',[477]),('twine','twine',[485]),
('empty crate Farah brings','crate',[493]),('payment coin','coin',[580]),('Farah stall counter','counter',[583]),('market gate','gate',[592]),('corner Dutta turns','place',[599]),
('Mina written name','name_text',[667]),('tomorrow order list','list',[674]),('warm slice of birthday pie','pie_slice',[682,692]),('napkin around pie slice','napkin',[689]),
('pie slice crust','crust',[706]),('sunlight','light',[713]),('last square of sunlight','light_patch',[711]),('Boulos last olive','olive',[159]),
]
for i,(name,kind,mentions) in enumerate(ENTS,1): a.entity(f'e{i}',name,kind,mentions)
a.entities['e47']['identity_note']='A three-apple contribution during the restarted weighing; not asserted to be the whole two-kilo order.'
a.entities['e50']['identity_note']='The crate Farah carries is distinct from Mina’s earlier crate unless further evidence establishes identity.'
# Prior generic order permission is not the current Dutta order.
a.entities['e14']['mentions'].remove(93)
a.entity('e63','nonspecific order in past permission contrast','order',[93],identity_note='Nonspecific action object under negated permission; not a completed prior order.')
a.entities['e11']['mentions'].remove(56)
a.entities['e36']['mentions'].insert(0,56)
FUTURE_BATCH=a.entities['e36']
a.feature(56,entity_id='e36',entity_name=FUTURE_BATCH['name'],entity=FUTURE_BATCH['type'])

QUOTES=[
('q1',list(range(34,40))+list(range(42,45)),'e1','e2',41),('q2',range(52,76),'e2','e1',52),('q3',range(95,100),'e1','e2',95),
('q4',range(121,127),'e1','e4',128),('q5',list(range(129,140))+list(range(150,160)),'e4','e1',129),
('q6',list(range(187,195))+list(range(197,209)),'e3','e1',196),('q7',range(209,212),'e1','e3',213),('q8',range(248,251),'e1','e3',252),
('q9',[308],'e1','e3',310),('q10',range(320,323),'e3','e1',320),('q11',range(389,408),'e1','e3',389),('q12',range(417,424),'e3','e1',417),
('q13',list(range(424,427))+list(range(431,443)),'e1','e3',424),('q14',range(501,503),'e2','e1',504),('q15',range(511,526),'e1','e2',511),
('q16',range(533,540),'e2','e1',533),('q17',list(range(540,543))+list(range(545,550)),'e1','e2',544),('q18',range(560,577),'e3','e1',560),
('q19',list(range(608,615))+list(range(618,633)),'e1','e4',616),('q20',range(645,659),'e4','e1',645),
]
for sid,words,speaker,audience,trigger in QUOTES:
    a.scope(sid,words,kind='quotation',holder_id=speaker,description='Direct speech; content truth and physical utterance remain distinct.')
    a.scopes[sid]['addressee_ids']=[audience]
    a.feature(words,quote_mode='direct')
SUB=[
('s1',range(81,95),'retrospective_permission','s0','e2','Past permitted tasks; permitted action content is distinct from execution.'),
('s2',range(135,140),'condition','q5','e4','Bumping counter is a condition, not a narrated bump.'),
('s3',range(155,160),'prospective_deadline','q5','e4','Last olive sale is a future deadline, not a completed sale.'),
('s4',[199,200],'expected_future','q6','e3','Grandson arrival tonight is anticipated, not narrated as completed.'),
('s5',range(206,209),'reported_expectation','q6','e5','Grandson’s expectation as reported by Dutta; no completed pie meal.'),
('s6',range(262,267),'purpose','s0','e1','First intention to return scale is interrupted before completion.'),
('s7',range(351,379),'considered_alternative','s0','e1','Unchosen delivery of short order and imagined consequences.'),
('s8',range(374,379),'nested_belief_content','s7','e2','Imagined Farah belief about a perfect job; not narrator truth.'),
('s9',range(513,517),'recalled_belief_content','q15','e1','Content of Mina earlier mistaken belief.'),
('s10',range(523,526),'prevented_early_handoff','q15','e1','Initial short-order handoff was prevented; later corrected-order receipt is separate.'),
('s11',range(571,577),'prevented_shortfall','q18','e3','Pie apple shortfall is a prevented outcome, not a completed deficient pie.'),
('s12',range(655,659),'permission_condition','q20','e4','Future need limits standing permission; no second actual loan.'),
]
for sid,words,kind,parent,holder,desc in SUB:a.scope(sid,words,kind=kind,parent=parent,holder_id=holder,description=desc)

def F(w,**fields): a.feature(w,**fields)
def status(w):
    sid=a.words[w]['scope_id']
    while sid:
        if a.scopes[sid]['kind']=='quotation': return 'attributed_claim'
        sid=a.scopes[sid].get('parent')
    return 'asserted'
def B(w,entity,value,**fields):return dict(entity_id=entity,scope_id=a.words[w]['scope_id'],assertion_status=status(w),value=value,**fields)
EV={}
def E(key,w,label,typ='other',actor=None,patients=(),instruments=(),recipient=None,fact='asserted',roles=None,**kw):
    eid=f'ev{len(a.events)+1}'; EV[key]=eid
    a.event(eid,w,label,type=typ,actor=actor,patients=patients,instruments=instruments,recipient=recipient,factuality=fact,roles=roles,**kw)
    return eid
def M(key,words,role='action',note='Same underlying occurrence, with mention-local scope and attribution.'):
    a.mention_event(EV[key],words,role=role,note=note)

E('smell',6,'market smells of peel crates and buns','state',patients=['e6'],roles={'location':[5],'source':[9,11,15]})
E('stand',21,'Mina stands behind apple stock','state','e1',roles={'actor':[20],'landmark':[26]})
E('polish',27,'Mina polishes red apple','other','e1',['e12'],['e13'],roles={'patient':[30],'instrument':[33]})
E('do_order',36,'Mina fills Dutta order alone','other','e1',['e14'],fact='hypothetical',roles={'actor':[34],'patient':[39]})
E('read_list',47,'Farah looks at order list','perceive','e2',['e15'],roles={'actor':[45,46],'patient':[51]})
E('old_scale',64,'Farah scale is at repair shop','state',patients=['e17'],fact='reported',roles={'patient':[63],'location':[68]})
E('need_loan',71,'Mina needs borrowed scale','state','e1',['e19'],fact='reported',roles={'actor':[70]})
E('proposed_borrow',73,'Mina borrows Boulos scale','obtain','e1',['e19'],fact='desired')
E('grin',78,'Mina grin widens','state',patients=['e20'],roles={'patient':[77]})
E('past_permission',82,'Farah permits Mina stacking and change tasks','other','e2',recipient='e1',roles={'actor':[79,80],'recipient':[83]})
E('stack',84,'Mina stacks fruit','other','e1',['e21'],fact='desired',roles={'patient':[85]})
E('change',87,'Mina makes change','transfer','e1',['e22'],fact='desired',roles={'patient':[88]})
E('prior_order',91,'Mina fills an order alone','other','e1',['e63'],fact='hypothetical',roles={'patient':[93]})
E('prior_permission',91,'Farah permits Mina to fill an order alone','other','e2',recipient='e1',fact='negated',primary=False)
E('promise_return',96,'Mina returns scale clean','transfer','e1',['e19'],recipient='e4',fact='desired',roles={'actor':[95],'patient':[97],'result':[99]})
E('arrange',107,'Boulos arranges olive jars','other','e4',['e24'],roles={'actor':[104,105],'patient':[108]})
E('scale_position',114,'Boulos scale rests beside jars','state',patients=['e19'],roles={'patient':[113],'landmark':[116]})
E('shine_dial',120,'dial shines','state',patients=['e26'],roles={'patient':[119]})
M('proposed_borrow',123)
E('mind_pan',130,'Mina handles pan carefully','other','e1',['e27'],fact='desired',roles={'patient':[132]})
E('wobble',134,'pan wobbles after counter bump','move',patients=['e27'],fact='hypothetical',roles={'patient':[133]})
E('bump',137,'Mina bumps counter','other','e1',['e28'],fact='hypothetical',roles={'actor':[136],'patient':[139]})
E('lift_scale',141,'Boulos lifts scale over','move','e4',['e19'],roles={'actor':[140],'patient':[142]})
E('loan',145,'Boulos hands scale to Mina','transfer','e4',['e19'],recipient='e1',roles={'patient':[146],'destination':[149]})
M('promise_return',151,note='Return requirement refers to the same intended return; the clean-state promise remains separately attributed to Mina.')
E('last_sale',156,'Boulos sells last olive','transfer','e4',['e62'],fact='hypothetical',roles={'actor':[155],'patient':[159]})
E('carry_scale',161,'Mina carries borrowed scale to apple stall','move','e1',['e19'],roles={'actor':[160],'patient':[162],'destination':[167]})
E('wait_customer',177,'Dutta waits at apple stall','state','e3',roles={'actor':[168,169]})
E('folded_shoppingbag',183,'cloth shopping bag is folded over Dutta arm','state',patients=['e32'],roles={'patient':[182],'landmark':[186]})
E('catch_bus',190,'Dutta catches eleven twenty bus','move','e3',['e34'],fact='desired',roles={'actor':[187],'patient':[194]})
E('arrive_grandson',199,'grandson arrives tonight','move','e5',fact='hypothetical',roles={'actor':[198]})
E('grandson_report',204,'grandson tells others he expects pie','speak','e5',recipient='e35',fact='reported',roles={'actor':[202],'recipient':[205]})
E('expect_pie',207,'grandson expects pie','state','e5',['e16'],fact='reported',roles={'actor':[206],'patient':[208]})
E('be_quick',211,'Mina completes order quickly','state','e1',['e14'],fact='desired',roles={'actor':[209]})
E('choose',215,'Mina chooses apples','other','e1',['e36'],roles={'actor':[214],'patient':[218]})
E('weigh_initial',220,'Mina loads apples onto faulty scale pan','move','e1',['e36'],instruments=['e19'],roles={'patient':[221],'destination':[228]})
E('initial_reading',231,'needle rises through readings to two kilos','state',patients=['e37'],roles={'patient':[230],'reading':[232,233,234,237,239]})
E('bag_initial',241,'Mina moves apples into paper bag','move','e1',['e36'],roles={'actor':[240],'patient':[243],'destination':[247]})
E('claim_two',249,'initial order contains exactly two kilos','state',patients=['e36'],fact='reported')
E('reach_bag',255,'Dutta reaches for apple bag','move','e3',roles={'actor':[253,254],'goal':[258]})
E('turn_return',261,'Mina turns intending to return scale','move','e1',roles={'actor':[260]})
E('early_return',263,'Mina returns scale before handoff','transfer','e1',['e19'],recipient='e4',fact='desired',roles={'patient':[265]})
E('empty_pan',270,'pan is empty of weighing load','state',patients=['e27'],roles={'patient':[268]})
E('offset',274,'unloaded needle indicates a quarter kilo','state',patients=['e37'],roles={'patient':[272],'reading':[277,278]})
E('frown',280,'Mina frowns','other','e1',roles={'actor':[279]})
E('lift_pan',282,'Mina lifts scale pan','move','e1',['e27'],roles={'actor':[281],'patient':[284]})
E('discover_leaf',288,'Mina discovers trapped leaf beneath pan','perceive','e1',['e39'])
E('pinched_leaf',290,'leaf is pinched beneath pan rim','state',patients=['e39'],roles={'patient':[288],'landmark':[293]})
E('press_leaf',294,'leaf presses scale downward','other','e39',['e19'],roles={'patient':[296]})
E('remove_leaf',299,'Mina removes trapped leaf from scale','repair','e1',['e39','e19'],roles={'actor':[298],'patient':[300]})
E('zero',304,'needle returns to zero after leaf removal','state',patients=['e37'],roles={'patient':[303],'reading':[307]})
E('wait_request',308,'Dutta waits before taking order','state','e3',fact='desired')
E('pause_customer',313,'Dutta pauses with fingers on bag handles','state','e3',roles={'actor':[311,312],'effector':[315],'contact':[319]})
E('reweigh_bag',324,'Mina places apple bag on corrected pan','move','e1',['e38'],roles={'actor':[323],'patient':[326],'destination':[330]})
E('actual_short_weight',333,'needle indicates one and three quarter kilos','state',patients=['e37'],roles={'patient':[332],'reading':[335,337,338,339]})
E('seems_hush',346,'market bustle seems to hush to Mina','perceive','e1',['e43'],roles={'patient':[345],'experiencer':[350]})
M('seems_hush',348)
E('unchosen_handoff',353,'Mina hands over short bag','transfer','e1',['e38'],recipient='e3',fact='hypothetical',roles={'actor':[351],'patient':[356]})
E('hyp_know',361,'someone knows order is short','state','e44',fact='negated',roles={'actor':[359]})
E('hyp_bus',365,'Dutta is on bus after short order handoff','state',patients=['e3'],fact='hypothetical',roles={'patient':[362,363],'location':[368]})
E('hyp_belief',373,'Farah believes Mina completed order perfectly','state','e2',fact='hypothetical',roles={'actor':[370,371]})
E('hyp_perfect',375,'Mina completes order perfectly','other','e1',['e14'],fact='hypothetical',roles={'actor':[374],'patient':[377]})
E('stop_handoff',381,'Mina pushes bag away to stop short delivery','move','e1',['e38'],roles={'actor':[380],'patient':[383],'away_from':[387,388]})
E('sorry',390,'Mina is sorry for weighing error','feel','e1',fact='reported',roles={'experiencer':[389]})
E('bias',393,'leaf causes scale to overstate load','other','e39',['e19'],fact='reported',roles={'actor':[392],'patient':[395]})
E('overread',396,'scale reading exceeds actual load','state',patients=['e19'],fact='reported')
E('short_order',404,'order is a quarter kilo below required weight','state',patients=['e36'],fact='reported',roles={'affected_customer':[403],'shortfall':[406,407]})
E('look_dial',410,'Dutta looks at dial then Mina','perceive','e3',['e26','e1'],roles={'actor':[408,409],'patient':[413,416]})
E('fix_request',419,'Mina corrects order before Dutta bus','repair','e1',['e14'],fact='desired',roles={'actor':[418],'patient':[420]})
E('try_fix',426,'Mina attempts correction','other','e1',['e14'],fact='desired',roles={'actor':[424]})
E('hot_cheeks',429,'Mina cheeks feel hot','feel','e1',['e45'],roles={'patient':[428],'state':[430]})
E('weigh_promise',432,'Mina weighs apples again','other','e1',['e36'],instruments=['e19'],fact='desired',roles={'actor':[431],'patient':[434]})
E('tell_farah_plan',438,'Mina tells Farah what happened','speak','e1',recipient='e2',fact='desired',roles={'actor':[437],'recipient':[439,440]})
E('empty_bag',444,'Mina empties apples from bag into crate','move','e1',['e36'],roles={'actor':[443],'source':[446],'destination':[449]})
E('restart',451,'Mina restarts weighing order','other','e1',['e36'],instruments=['e19'])
E('check_final',453,'Mina checks dial between handfuls during corrected weighing','perceive','e1',['e26'],roles={'patient':[455]})
E('add_three',467,'three small apples bring needle to two kilos','other','e1',['e47'],instruments=['e19'],roles={'added_items':[465],'indicator':[469],'reading':[472,473]})
E('fold_top',475,'Mina folds top of apple bag','other','e1',['e48'],roles={'actor':[474],'patient':[477]})
E('tie_bag',482,'Mina ties apple bag with twine','other','e1',['e38'],['e49'],roles={'patient':[483],'instrument':[485]})
E('farah_return',488,'Farah returns carrying empty crate','move','e2',['e50'],roles={'actor':[486,487],'patient':[493]})
M('farah_return',490)
E('check_time',498,'Dutta checks time','perceive','e3',roles={'actor':[496,497]})
E('show_leaf',506,'Mina shows leaf to Farah','other','e1',['e39'],recipient='e2',roles={'actor':[505],'recipient':[507],'patient':[510]})
E('old_belief',512,'Mina believed initial order was right','state','e1',fact='reported',roles={'actor':[511]})
E('believed_right',516,'initial order is correct','state',patients=['e14'],fact='hypothetical',roles={'patient':[514]})
E('not_right',519,'initial order is correct','state',patients=['e14'],fact='negated',roles={'patient':[518]})
M('stop_handoff',521)
E('early_take',524,'Dutta takes short order before correction','obtain','e3',['e38'],fact='hypothetical',roles={'actor':[523],'patient':[525]})
E('farah_examine',528,'Farah examines scale','perceive','e2',['e19'],roles={'actor':[526,527],'patient':[530]})
E('farah_nod',532,'Farah nods after inspection','other','e2')
E('boulos_should_know',538,'Boulos knows about scale fault and correction','state','e4',fact='desired',roles={'actor':[535,536]})
E('tell_boulos_plan',541,'Mina tells Boulos about fault and correction','speak','e1',recipient='e4',fact='desired',roles={'actor':[540],'recipient':[542]})
M('promise_return',547)
E('take_order',552,'Dutta puts corrected order bag into shopping bag','obtain','e3',['e38'],roles={'actor':[550,551],'patient':[554],'destination':[559]})
M('catch_bus',562,note='Same intended bus catch, now predicted still feasible; no completed boarding is narrated.')
E('save_pie',567,'Mina prevents pie apple shortfall','other','e1',['e16'],fact='reported',roles={'actor':[566],'beneficiary':[568],'patient':[569]})
E('pie_shortfall',574,'pie is short on apples','state',patients=['e16'],fact='hypothetical')
E('pay',578,'Dutta leaves coin to pay for order','transfer','e3',['e51'],roles={'actor':[577],'patient':[580],'destination':[583],'purpose':[586]})
E('leave_market',588,'Dutta hurries toward market gate','move','e3',roles={'destination':[592]})
E('watch_depart',594,'Mina watches Dutta leave','perceive','e1',['e3'],roles={'actor':[593]})
E('turn_corner',597,'Dutta turns corner','move','e3',roles={'actor':[596],'path':[599]})
E('actual_return',601,'Mina returns scale to Boulos','transfer','e1',['e19'],recipient='e4',roles={'patient':[603],'recipient':[606,607]})
M('discover_leaf',609)
M('bias',620)
M('overread',623)
M('remove_leaf',627,note='Cleaning summarizes the narrated removal of the trapped leaf; no additional washing or repair method is invented.')
M('check_final',630,note='Reported rechecking refers to narrated corrected-weight checks, not a new test after the return.')
E('inspect_boulos',635,'Boulos turns scale over to inspect','move','e4',['e19'],roles={'actor':[633,634],'patient':[637]})
E('boulos_nod',640,'Boulos gives Mina serious nod','other','e4',recipient='e1',roles={'recipient':[641],'result':[644]})
E('borrow_future',652,'Mina borrows scale again','obtain','e1',['e19'],fact='hypothetical',roles={'actor':[650],'patient':[653]})
E('need_future',657,'Mina needs scale on future occasion','state','e1',['e19'],fact='hypothetical',roles={'actor':[656],'patient':[658]})
E('next_list',665,'Farah puts Mina name at top of tomorrow order list','other','e2',['e55'],roles={'actor':[662,663],'patient':[667],'destination':[674]})
E('dutta_return',678,'Dutta returns with pie slice','move','e3',['e57'],roles={'actor':[676,677],'patient':[682]})
E('wrapped_pie',686,'pie slice is wrapped in napkin','state',patients=['e57'],instruments=['e58'],roles={'patient':[682],'covering':[689]})
E('set_pie',691,'Mina sets pie slice beside scale','move','e1',['e57'],roles={'actor':[690],'patient':[692],'landmark':[695]})
E('final_zero',698,'scale dial rests on zero at ending','state',patients=['e26'],roles={'patient':[697],'reading':[701]})
E('crust_glow',707,'golden pie crust catches sunlight','state',patients=['e59'],roles={'patient':[706],'illumination':[711,713]})

PROPS=[
('Mina fills Dutta apple order alone.',[34,36,39,44],'q1'),
('Dutta order requires two kilos of tart apples for birthday pie.',[52,53,55,56,59,61],'q2'),
('Mina borrows Boulos scale.',[73,75,123,125],'q4'),
('Mina returns Boulos scale clean.',[95,96,97,99],'q3'),
('Mina bumps Boulos counter.',[136,137,139],'s2'),
('Scale pan wobbles following a counter bump.',[132,133,134,135,137],'q5'),
('Mina returns scale before Boulos sells last olive.',[151,152,154,155,156,159],'q5'),
('Dutta catches eleven twenty bus.',[187,190,192,193,194],'q6'),
('Grandson arrives tonight and expects birthday pie.',[198,199,200,202,204,206,207,208],'q6'),
('Mina completes order quickly.',[209,210,211],'q7'),
('Initial apple load is exactly two kilos.',[248,249,250],'q8'),
('Unloaded scale needle indicates a quarter kilo.',[268,270,272,274,277,278],'s0'),
('Leaf removal restores zero at no load.',[299,300,303,304,307],'s0'),
('Initial order is only one and three quarter kilos.',[324,326,333,335,337,338,339],'s0'),
('Mina hands the short bag to Dutta without disclosure.',[351,353,356,358,361],'s7'),
('Someone knows the order is short.',[358,359,361],'s7'),
('Mina completed the order perfectly.',[374,375,377,378],'s8'),
('The leaf caused the scale to overstate the amount and the order is a quarter kilo short.',[392,393,395,396,399,404,406,407],'q11'),
('Mina corrects order before Dutta bus.',[417,418,419,420,421,423],'q12'),
('Mina reweighs apples and tells Farah what happened.',[431,432,434,437,438,439,440,442],'q13'),
('Corrected order reaches exactly two kilos.',[451,453,463,465,467,469,471,472,473],'s0'),
('Initial order is correct.',[514,515,516],'s9'),
('Mina earlier believed the order correct but it was not; she stopped the short handoff.',[511,512,514,516,518,519,520,521,523,524,525],'q15'),
('Boulos knows about the fault and its correction.',[535,536,537,538],'q16'),
('Mina tells Boulos and returns scale.',[540,541,542,546,547,549],'q17'),
('Dutta still expects to catch her bus and credits Mina with preventing pie apple shortfall.',[560,562,564,566,567,569,574,576],'q18'),
('Pie is short on apples.',[569,571,574,576],'s11'),
('Mina found trapped leaf, removed it and rechecked the scale.',[608,609,611,614,618,620,622,623,627,628,630,631],'q19'),
('Mina may borrow scale again whenever she needs it.',[650,651,652,653,655,656,657,658],'q20'),
('Farah previously permitted Mina to fill an order alone.',[79,80,82,83,90,91,93,94],'s1'),
('Dutta waits before taking the order.',[308,311,313],'q9'),
('What interrupted the apple transaction?', [320,321,322],'q10'),
('What happened with the order?', [501,502],'q14'),
('Initial order is not correct.',[518,519],'q15'),
('Birthday pie is available for grandson tonight.',[198,200,206,207,208],'s5'),
('Grandson expects birthday pie.',[202,204,206,207,208],'q6'),
('Dutta must catch the eleven twenty bus; her grandson arrives tonight and has told others he expects pie.',[187,190,192,193,194,198,199,200,202,204,205,207,208],'q6'),
('Mina has permission to borrow the scale, should mind its pan because it wobbles if the counter is bumped, and must return it before Boulos sells his last olive.',[129,130,132,134,135,137,139,151,156,159],'q5'),
('Dutta order needs two kilos of tart apples for her grandson birthday pie; Farah scale is at repair shop so Mina needs to borrow Boulos scale.',[52,53,55,56,59,61,63,64,68,70,71,73,75],'q2'),
('Boulos thanks Mina for telling him about the scale and permits future borrowing when she needs it.',[645,646,648,649,650,651,652,653,655,657,658],'q20'),
('Mina stacks fruit and makes change.',[83,84,85,87,88],'s1'),
]
for i,(content,words,scope) in enumerate(PROPS,1):a.proposition(f'p{i}',content,words,scope_id=scope)

UTT={
'q1':('offer','p1'),'q2':('instruction','p39'),'q3':('promise','p4'),'q4':('request_permission','p3'),'q5':('grant_and_warn','p38'),
'q6':('explain_deadline','p37'),'q7':('promise','p10'),'q8':('weight_claim','p11'),'q9':('request_pause','p31'),'q10':('question','p32'),
'q11':('apology_and_correction','p18'),'q12':('request_correction','p19'),'q13':('promise','p20'),'q14':('question','p33'),
'q15':('admit_error','p23'),'q16':('praise_and_advice','p24'),'q17':('promise','p25'),'q18':('reassure_and_thank','p26'),'q19':('report_fault_correction','p28'),'q20':('thanks_and_permission','p40')}
for sid,words,speaker,audience,w in QUOTES:
    act,pid=UTT[sid]
    eid=E('utter_'+sid,w,act,'speak',speaker,recipient=audience,scope='s0',primary=a.words[w]['scope_id']=='s0')
    a.scopes[sid]['utterance_event_id']=eid
    F(w,utterance_id=eid,speaker_id=speaker,addressee_ids=[audience],utterance_content_id=pid,speech_act_kind=act,communication_channel='speech',communication_scope_bundle={'speaker_id':speaker,'utterance_event_id':eid,'scope_id':'s0','assertion_status':'asserted'})
M('utter_q19',648,note='Boulos thanks Mina for the disclosure just made, not a new telling.')


# Stable mention chains and selected grammar; no actor-to-subject default.
for eid,ent in a.entities.items():
    for w in ent['mentions']:
        F(w,reference_chain_id=eid,referent_kind='group' if ent['type'].endswith('_group') else 'individual')
    F(ent['mentions'][0],reference_introduction=True)
for eid,ws in {'e19':[530],'e57':[704]}.items():
    for w in ws:
        a.entities[eid]['mentions'].append(w)
        F(w,entity_id=eid,entity_name=a.entities[eid]['name'],entity=a.entities[eid]['type'],reference_chain_id=eid,referent_kind='individual')
# Possessives and contextually expanded contractions are explicit, including auxiliary components.
for w,parts in {70:['you','will'],95:['I','will'],202:['he','has'],209:['I','will'],374:['she','had'],389:['I','am'],403:['you','are'],431:['I','will'],437:['I','will'],519:['was','not'],540:['I','will'],546:['I','will'],560:['I','will'],566:['you','have']}.items():
    F(w,contraction_expansion=parts)
for ws,person in [([34,44,95,122,155,187,209,389,424,431,437,511,520,540,546,560,608,626,649],1),([70,124,136,403,418,566,646,650,656],2),([40,83,97,117,133,140,142,146,152,162,195,202,206,214,221,251,267,281,298,300,309,350,374,397,401,420,443,461,474,483,503,507,518,523,525,542,577,596,615,617,618,628,631,653,658,692],3)]:
    F(ws,grammatical_person=person)
for w in [44]:F(w,personal_pronoun_series='reflexive')
for w in [397,401,461]:F(w,expletive_reference=True,referential_use='expletive')
for w in [8,14,18,60,67,166,180,181,227,246,344,557,558,673,684]:F(w,referential_use='attributive')
for w in [20,25,38,45,46,74,75,76,79,80,104,105,127,160,168,169,198,212,240,253,254,279,311,312,323,350,362,363,370,371,380,387,388,408,409,416,427,439,440,486,487,496,497,505,526,527,535,536,543,550,551,593,606,607,633,634,641,662,663,666,676,677,690]:
    # Grandson is relational, not a proper name.
    if w!=198:F(w,proper_name_structure='named_person_or_title_component')
for w in [11,15,26,56,108,110,149,218,243,315,319,428,434,465,576]:F(w,grammatical_number='plural')
for w in [5,9,19,30,33,39,51,85,59,61,63,68,77,88,93,103,113,119,125,132,139,159,167,173,175,182,186,194,198,208,228,230,247,258,265,268,272,284,288,293,296,303,318,326,330,332,345,356,368,377,383,392,395,413,423,446,449,455,469,477,480,485,493,500,510,514,530,549,554,559,564,569,580,583,586,591,592,599,603,611,614,622,637,644,667,674,682,685,689,695,697,706,711]:F(w,grammatical_number='singular')
for w in [3,13,17,49,66,101,131,138,165,191,226,229,242,257,264,271,283,295,302,317,325,329,331,343,355,376,382,391,394,412,433,445,454,468,476,479,499,508,513,529,548,553,582,585,590,598,602,613,621,636,669,694,696,703,709]:F(w,definiteness='definite')
for w in [28,92,179,236,245,276,285,341,405,448,491,572,579,610,642,680,688]:F(w,definiteness='indefinite')
SUBJECTS={6:'e6',21:'e1',47:'e2',64:'e17',71:'e1',78:'e20',82:'e2',96:'e1',107:'e4',114:'e19',120:'e26',123:'e1',134:'e27',137:'e1',141:'e4',145:'e4',156:'e4',161:'e1',177:'e3',183:'e32',190:'e3',199:'e5',204:'e5',207:'e5',211:'e1',215:'e1',220:'e1',231:'e37',241:'e1',255:'e3',261:'e1',270:'e27',274:'e37',280:'e1',282:'e1',290:'e39',294:'e39',299:'e1',304:'e37',313:'e3',324:'e1',333:'e37',346:'e43',353:'e1',361:'e44',365:'e3',373:'e2',375:'e1',381:'e1',390:'e1',393:'e39',396:'e19',404:'e3',410:'e3',419:'e1',426:'e1',429:'e45',432:'e1',438:'e1',444:'e1',451:'e1',467:'e47',475:'e1',482:'e1',488:'e2',498:'e3',506:'e1',512:'e1',516:'e14',519:'e14',521:'e1',524:'e3',528:'e2',532:'e2',538:'e4',541:'e1',547:'e1',552:'e3',562:'e3',567:'e1',574:'e16',578:'e3',588:'e3',594:'e1',597:'e3',601:'e1',609:'e1',620:'e39',623:'e26',627:'e1',630:'e1',635:'e4',640:'e4',652:'e1',657:'e1',665:'e2',678:'e3',686:'e57',691:'e1',698:'e26',707:'e59'}
for w,eid in SUBJECTS.items():F(w,grammatical_subject_id=eid)
# The three apples control bring, but the matrix took has expletive it.
F(467,clause_finiteness='nonfinite',verb_form='infinitive')
OBJECTS={27:'e12',36:'e14',73:'e19',84:'e21',87:'e22',91:'e63',96:'e19',107:'e24',123:'e19',130:'e27',137:'e28',141:'e19',145:'e19',151:'e19',156:'e62',161:'e19',190:'e34',207:'e16',215:'e36',220:'e36',241:'e36',263:'e19',282:'e27',294:'e19',299:'e39',324:'e38',353:'e38',375:'e14',381:'e38',393:'e19',419:'e14',432:'e36',438:'e2',444:'e38',453:'e26',467:'e37',475:'e48',482:'e38',490:'e50',498:'e50',506:'e39',524:'e38',528:'e19',547:'e19',552:'e38',562:'e34',567:'e16',578:'e51',601:'e19',609:'e39',620:'e26',627:'e19',630:'e19',635:'e19',640:'e60',652:'e19',657:'e19',665:'e55',691:'e57'}
# Time and the nod are abstract discourse referents, not the nearby crate/light.
OBJECTS.pop(498);OBJECTS.pop(640)
for w,eid in OBJECTS.items():F(w,grammatical_object_id=eid)
for w,eid in {204:'e35',506:'e2',541:'e4',616:'e4',640:'e1',648:'e4'}.items():
    # tell-recipient is direct object with clause; show/give recipient is indirect object.
    F(w,**({'indirect_object_id':eid} if w in [506,640] else {'grammatical_object_id':eid}))
for w,eid in {22:'e11',31:'e13',48:'e15',65:'e18',115:'e24',147:'e29',164:'e30',174:'e31',178:'e32',184:'e33',225:'e27',244:'e38',256:'e38',291:'e40',316:'e42',328:'e27',349:'e1',366:'e34',386:'e3',411:'e26',415:'e1',447:'e46',484:'e49',555:'e32',581:'e52',589:'e53',605:'e4',612:'e27',679:'e57',683:'e16',687:'e58',693:'e19',708:'e61',712:'e60'}.items():F(w,prepositional_object_id=eid)
for w in [35,121,352,360,364,372,417,425,537,651]:
    F(w,modal_auxiliary_class=a.words[w]['lemma'])
for w in [130,151,308]:F(w,mood='imperative',clause_finiteness='finite')
for w in [27,120,183,294,453,490,648,686]:F(w,clause_finiteness='nonfinite',verb_form='participle')
for w in [73,84,87,91,263,348,467]:F(w,clause_finiteness='nonfinite',verb_form='infinitive')
for w in [107,177]:F(w,aspect='progressive',tense='past')
F(82,aspect='perfect',tense='past');F(204,aspect='perfect',tense='present');F(375,aspect='perfect',tense='past');F(567,aspect='perfect',tense='present');F(665,aspect='perfect',tense='past')
F(290,voice='passive',tense='past');F(686,voice='passive')
F(90,negation_marker_form='never',negation_scope_id='p30',scope_operator='negation',proposition_id='p30',proposition_polarity='negative')
F(358,negation_marker_form='no',negation_scope_id='p16',scope_operator='negative_quantifier',proposition_id='p16',proposition_polarity='negative')
F(519,polarity='negative',negation_marker_form='not',negation_scope_id='p22',proposition_id='p22',proposition_polarity='negative',verb_phrase_ellipsis=True)
F(516,proposition_id='p22',proposition_polarity='positive')
F(320,question_requested_slot='cause_of_pause',clause_type='interrogative')
F(501,question_requested_slot='cause_of_order_delay',clause_type='interrogative')
F(121,clause_type='interrogative',modal_base={'kind':'deontic_permission','grantor_id':'e4','recipient_id':'e1','content_id':'p3'})
F(417,clause_type='interrogative',modal_base={'kind':'ability_request','holder_id':'e1','content_id':'p19'})
F(35,modal_base={'kind':'claimed_ability','holder_id':'e1','content_id':'p1'})
F(352,modal_base={'kind':'considered_option','holder_id':'e1','content_id':'p15'})
F(425,modal_base={'kind':'tentative_ability','holder_id':'e1','content_id':'p19'})
F(537,modal_base={'kind':'advice','holder_id':'e2','content_id':'p24'})
F(651,modal_base={'kind':'permission','grantor_id':'e4','recipient_id':'e1','content_id':'p29'})

# Observable carriers, parts, materials and states.
def attr(w,name,value):
    a.words[w].setdefault('attributes',[]).append({'name':name,'value':value})
for w,eid,col in [(29,'e12','red'),(287,'e39','green'),(705,'e59','golden')]:F(w,appearance_color=B(w,eid,col))
for w,eid,mat in [(112,'e19','brass'),(180,'e32','cloth'),(227,'e27','brass'),(246,'e38','paper'),(557,'e32','cloth')]:F(w,material_composition=B(w,eid,mat))
F(10,object_moisture=B(10,'e8','damp'))
F(118,object_shape=B(118,'e26','round'))
for w in [286,509]:F(w,object_shape=B(w,'e39','curled'))
F(430,object_temperature=B(430,'e45','hot'))
F(681,object_temperature=B(681,'e57','warm'))
F(270,object_fill_state=B(270,'e27','empty',qualification='no weighing load; trapped leaf beneath rim is still present'))
F(492,object_fill_state=B(492,'e50','empty'))
F(99,object_cleanliness=B(99,'e19','clean',factuality='desired',event_id=EV['promise_return']))
F(627,object_cleanliness=B(627,'e19','cleaned_by_leaf_removal',event_id=EV['remove_leaf']))
F(134,object_stability=B(134,'e27','wobbles',factuality='conditional',condition_id='p5'))
F(290,object_attachment=B(290,'e39','trapped_under_rim',landmark_id='e40'))
F(299,object_attachment=B(299,'e39','freed_from_rim',landmark_id='e40',event_id=EV['remove_leaf']))
for w,pid,whole in [(33,'e13','e1'),(77,'e20','e1'),(119,'e26','e19'),(132,'e27','e19'),(149,'e29','e1'),(186,'e33','e3'),(230,'e37','e19'),(293,'e40','e27'),(315,'e41','e3'),(319,'e42','e38'),(428,'e45','e1'),(477,'e48','e38'),(682,'e57','e16'),(706,'e59','e57')]:
    F(w,part_whole_relation={'part_id':pid,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
for w,name,val in [(9,'odor_source','orange peel'),(15,'flavoring','cinnamon'),(50,'inscription_method','handwritten'),(55,'taste','tart'),(163,'manner','carefully'),(216,'texture','firm'),(217,'appearance_pattern','speckled'),(384,'manner','gently'),(464,'relative_size','small'),(643,'display_manner','serious'),(699,'reading_alignment','neatly on zero')]:attr(w,name,val)
F(120,evidence=[117,118,119,120],note='Shining brass dial reflects light; no active illumination is asserted.')
F(707,evidence=[704,705,706,707,708,711,713],note='Golden crust in sunlight is reflected light, not an emitting lamp or a material-gold crust.')
for w,fig,rel,land in [(21,'e1','behind','e11'),(114,'e19','beside','e24'),(183,'e32','folded_over','e33'),(290,'e39','beneath','e40'),(313,'e41','on','e42'),(365,'e3','on','e34'),(552,'e38','inside','e32'),(578,'e51','on','e52'),(686,'e57','wrapped_in','e58'),(691,'e57','beside','e19')]:
    F(w,spatial_configuration=B(w,fig,{'relation':rel,'landmark_id':land},factuality=a.words[w].get('factuality','asserted')))
for w,obj,holder in [(145,'e19','e1'),(161,'e19','e1'),(552,'e38','e3'),(601,'e19','e4'),(635,'e19','e4')]:
    F(w,possession_holder=B(w,obj,holder,event_id=a.words[w]['event_id']))
F(111,possession_owner=B(111,'e19','e4'))
F(25,possession_owner=B(25,'e11','e2'))
F(145,possession_borrower=B(145,'e19','e1'),possession_lender=B(145,'e19','e4'),transfer_kind=B(145,'e19','loan',event_id=EV['loan']),transfer_completion=B(145,'e19',True,event_id=EV['loan']),transfer_retained_ownership=B(145,'e19','e4'))
F(151,possession_return_target=B(151,'e19','e4'),transfer_return_due=B(151,'e19',{'before_event_id':EV['last_sale'],'factuality':'desired'}))
F(220,possession_user=B(220,'e19','e1',event_id=EV['weigh_initial']))
F(601,transfer_kind=B(601,'e19','return',event_id=EV['actual_return']),transfer_completion=B(601,'e19',True,event_id=EV['actual_return']),possession_owner=B(601,'e19','e4'))
F(578,transfer_kind=B(578,'e51','payment',event_id=EV['pay']),transfer_exchange_counterpart=B(578,'e51','e14'))
F(695,evidence_missing={'inference':'second scale loan to Mina','missing_premise':'No new loan or custody transfer after actual return is narrated. Final location beside pie alone is insufficient.','object_id':'e19','known_return_event_id':EV['actual_return']},evidence=[601,603,606,607,635,637,652,691,695],note='Final co-location is retained without inventing a new loan, owner, stall or retrieval transition.')

# Measures distinguish observations, mistaken claims and corrected object quantities.
for w in [53,233,250,278,339,407,473]:F(w,measure_unit='kg',measure_dimension='mass',measure_noun_role='mass_unit')
for w,val in [(237,.5),(277,.25),(338,.25),(406,.25)]:F(w,quantity_fraction_lexeme=val)
for w,val,eid,kind,phase in [(52,2,'e14','required_mass','order_specification'),(232,1,'e36','dial_reading','faulty_loading_intermediate'),(234,1.5,'e36','dial_reading','faulty_loading_intermediate'),(239,2,'e36','dial_reading','faulty_initial_load'),(249,2,'e36','claimed_mass','initial_order'),(277,.25,'e27','dial_reading','empty_pan_fault'),(307,0,'e27','dial_reading','empty_pan_after_removal'),(335,1.75,'e36','measured_mass','initial_order_after_fault_removal'),(406,.25,'e36','mass_shortfall','initial_order'),(463,3,'e47','count','correction_contribution'),(472,2,'e36','measured_mass','corrected_order'),(701,0,'e19','dial_reading','ending')]:
    F(w,measure_entity_id=eid,quantity_total={'domain':eid,'unit':'apple' if w==463 else 'kg','value':val,'measure_kind':kind,'phase':phase,'scope_id':a.words[w]['scope_id'],'assertion_status':status(w)})
for w in [249,472]:F(w,quantity_exact_value=2)
F(333,proposition_id='p14',quantity_comparison={'domain':'e36','unit':'kg','observed':1.75,'required':2,'relation':'less_than','required_source':'p2','observed_source':'p14'})
F(404,quantity_comparison={'domain':'e36','unit':'kg','required':2,'observed':1.75,'difference':.25,'relation':'shortfall','scope_id':'q11','assertion_status':'attributed_claim'})
F(467,quantity_change={'domain':'e36','unit':'apple','value':3,'event_id':EV['add_three'],'source_words':[463,464,465],'assertion_status':'asserted'})
F(472,quantity_comparison={'domain':'e36','unit':'kg','before_value':1.75,'after_value':2,'relation':'increased_to_required_weight','earlier_content_id':'p14','later_content_id':'p21','event_id':EV['add_three']})
F(333,evidence_conflict={'claim_id':'p11','corrected_measurement_id':'p14','entity_id':'e36','property':'initial_order_mass','same_order_before_addition':True,'earlier_observation':'faulty dial did genuinely indicate 2 kg'},evidence=[231,239,249,274,277,299,304,324,333,335,337,338,339],note='The earlier mass claim is false; the earlier dial observation remains true.')
F(399,figurative_mapping={'target_id':'e19','source_image':'speaking an amount','kind':'personification','literal_event':False},evidence=[392,393,395,396,399],note='Scale saying more means a false reading, not a communicative agent.')
F(294,causal_mechanism=B(294,'e19',{'cause_entity_id':'e39','process':'leaf trapped beneath rim presses scale downward','effect_event_id':EV['offset']}))
F(304,causal_parent=B(304,'e37',{'cause_event_id':EV['remove_leaf'],'effect_event_id':EV['zero']}))
F(393,causal_effect=B(393,'e39',{'effect_event_id':EV['overread'],'mechanism':'mechanical bias of scale'}))
F(567,causal_parent=B(567,'e16',{'cause_event_ids':[EV['stop_handoff'],EV['restart'],EV['add_three']],'prevented_content_id':'p27'}))

# Plans, permission and epistemic correction are scoped rather than world facts.
for w,pid in [(36,'p1'),(73,'p3'),(96,'p4'),(190,'p8'),(211,'p10'),(432,'p20'),(541,'p25')]:
    owner='e3' if w==190 else 'e1'
    F(w,goal_owner_id=owner,goal_content_id=pid,goal_polarity='achieve',intention_publicity='communicated')
for w,pid,beneficiary in [(95,'p4','e2'),(213,'p10','e3'),(431,'p20','e3'),(540,'p25','e2')]:
    F(w,promise_content_id=pid,promise_beneficiary_id=beneficiary,plan_commitment_status='promised')
F(129,permission_grantor_id='e4',permission_recipient_id='e1',permission_content_id='p3',permission_status='granted')
F(121,permission_grantor_id='e4',permission_recipient_id='e1',permission_content_id='p3',permission_status='requested')
F(82,permission_grantor_id='e2',permission_recipient_id='e1',permission_content_id='p41',permission_status='granted',evidence=[81,82,83,84,87,89,90,91],note='Prior permission covers stacking and making change; it does not entail independent order-filling permission or execution of every permitted task.')
F(651,permission_grantor_id='e4',permission_recipient_id='e1',permission_content_id=EV['borrow_future'],permission_status='granted',active_assumptions=[EV['need_future']])
F(154,temporal_deadline={'event_id':EV['promise_return'],'before_event_id':EV['last_sale'],'scope_id':'q5','factuality':'desired'})
F(154,pos='conj',subordinator_type='temporal',temporal_signal_relation='before')
F(188,goal_deadline={'event_id':EV['catch_bus'],'clock':'11:20','day':'story_day','meridiem':'unspecified'})
F(421,temporal_deadline={'event_id':EV['try_fix'],'before_event_id':EV['catch_bus'],'scope_id':'q12','factuality':'desired'})
F(207,belief_holder_id='e5',belief_content_id='p35',belief_certainty='expected',evidence=[197,198,199,200,202,204,206,207,208],note='Dutta reports grandson’s pie expectation; arrival and meal are not narrated completions.')
F(353,plan_commitment_status='considered_not_adopted',goal_owner_id='e1',goal_content_id='p15',intention_publicity='privately_attributed')
F(361,knowledge_claim_holder_id='e44',knowledge_claim_content_id='p14',proposition_polarity='negative',active_assumptions=['p15'])
F(373,belief_holder_id='e2',belief_content_id='p17',belief_polarity='accepts',belief_nested_holders=['e1','e2'],active_assumptions=['p15'])
F(512,belief_holder_id='e1',belief_content_id='p22',belief_polarity='accepts',belief_error_status='contradicted_by_corrected_measurement')
F(519,belief_revision={'holder_id':'e1','old_content_id':'p22','new_content_id':'p34','evidence_event_id':EV['actual_short_weight'],'scope_id':'q15','assertion_status':'attributed_claim'})
F(249,belief_holder_id='e1',belief_content_id='p11',belief_polarity='accepts',belief_error_status='contradicted_by_later_fault_discovery')
F(390,affect_experiencer_id='e1',affect_kind='sorry',affect_expression_channel='explicit_self_report',affect_target_id='p18')
F(430,affect_embodied_sensation={'experiencer_id':'e1','body_part_id':'e45','sensation':'hot_cheeks','scope_id':'s0','assertion_status':'asserted'},evidence=[427,428,429,430],note='Bodily heat is explicit; shame or embarrassment is plausible but no stable trait or certain named emotion is asserted.')
F(78,affect_expression_channel='widening_grin',affect_experiencer_id='e1',evidence=[76,77,78],note='Observable expression without committing to pride, joy or permanent confidence.')
F(280,affect_expression_channel='frown',affect_experiencer_id='e1',evidence=[279,280],note='Frown alone does not determine anger, worry or doubt.')
F(346,evidence=[340,342,344,345,346,348,350],note='Narrated subjective seeming; the actual market is not asserted to become silent.')
F(538,knowledge_claim_holder_id='e4',knowledge_claim_content_id='p18',factuality='desired')
F(533,attributes=[{'name':'evaluation','value':'positive assessment of fault detection'}])
F(645,speech_act_kind='thanks_and_permission',discourse_answer_relation={'source_event_id':EV['utter_q19'],'response_event_id':EV['utter_q20'],'relation':'thanks_for_disclosure'})
F(665,evidence=[662,663,665,666,667,670,672,674],note='Farah places Mina’s name first on tomorrow’s list. Increased trust is a supported interpretation, but no explicit permanent trait or completed tomorrow order is asserted.')

# Calendar and event ordering preserve future uncertainty and completion status.
F(1,time_expression_id='time_nine',temporal_end_bound={'event_id':EV['smell'],'clock':'9:00','day':'story_day','meridiem':'unspecified','relation':'state_holds_by_boundary','factuality':'asserted'})
F(192,time_expression_id='time_bus',event_time_interval={'event_id':EV['catch_bus'],'clock':'11:20','day':'story_day','factuality':'desired'})
F(200,temporal_deixis='tonight',event_time_interval={'event_id':EV['arrive_grandson'],'relative_interval':'tonight','anchor':'story_day','factuality':'hypothetical'})
F(203,temporal_order_cue='already',event_time_relation={'earlier_event_id':EV['grandson_report'],'later_event_id':EV['utter_q6'],'relation':'before'})
F(238,temporal_order_cue='then');F(266,temporal_order_cue='first')
F(600,event_time_relation={'earlier_event_id':EV['turn_corner'],'later_event_id':EV['actual_return'],'relation':'before'})
F(672,temporal_deixis='tomorrow',event_time_interval={'entity_id':'e56','relative_interval':'next_day','anchor':'story_day','factuality':'planned_orders'})
F(659,temporal_end_bound={'event_id':EV['next_list'],'boundary':'market_closing_time','absolute_time':'unknown','inclusive':True})
F(675,temporal_simultaneity={'event_ids':[EV['dutta_return'],EV['set_pie']],'relation':'return provides occasion for placing pie'})
for w in [308,320,501]:F(w,discourse_relation_kind='transaction_interruption_or_query')
F(379,discourse_relation_kind='contrast_chosen_with_considered',discourse_relation_source_id='p15',discourse_relation_target_id=EV['stop_handoff'])
F(517,discourse_relation_kind='correction',discourse_relation_source_id='p22',discourse_relation_target_id='p34')
# Correlate mention-local participants without creating repeat events.
for key,roles in {
    'proposed_borrow':{'actor':[122],'patient':[125]},
    'promise_return':{'actor':[546],'patient':[152,549]},
    'stop_handoff':{'actor':[520]},
    'catch_bus':{'actor':[560],'patient':[564]},
    'discover_leaf':{'actor':[608],'patient':[611]},
    'bias':{'actor':[618],'affected_part':[622]},
    'remove_leaf':{'actor':[626],'cleaned_item':[628]},
    'check_final':{'inspected_instrument':[631]},
    'utter_q19':{'recipient':[617,649],'speaker':[615]},
}.items():
    for role,ws in roles.items():M(key,ws,role=role)
F(204,utterance_id=EV['grandson_report'],speaker_id='e5',addressee_ids=['e35'],utterance_content_id='p36',communication_channel='speech',evidence_report_depth=2)
F(625,pos='adv')
F(442,proposition_id='p18',referent_kind='proposition')
F(173,social_relation_kind='neighbors',social_relation_participants={'neighbor_id':'e3','household_member_ids':['e1','e2'],'location_id':'e31'},evidence=[168,169,170,171,172,173,174,175],note='Next-door neighbor relation, not proof of legal ownership of either home.')
# Rich scopes survive later mentions; attribution follows ancestry, not ID spelling.
for w,row in enumerate(a.words):
    if row.get('event_id') or any(k in row for k in ('belief_content_id','goal_content_id','promise_content_id','permission_content_id')):
        F(w,assertion_status=status(w))
    if row.get('entity_id') and row['pos']=='pron' and status(w)=='attributed_claim' and row.get('grammatical_person') in [1,2]:
        F(w,reference_quotation_shift={'entity_id':row['entity_id'],'scope_id':row['scope_id'],'person':row['grammatical_person']})
for w in [288,609]:F(w,evidence=[282,288,290,299,608,609,611,614],note='Discovery is recoverable retrospectively from lifting the pan and Mina’s later found report; both mentions reuse one event.')
F(467,evidence=[451,453,462,463,464,465,467,472,473],note='Three small apples participate in correction; their individual masses are unknown. The text implies a quarter-kilo shortfall corrected, without supplying tare or separate fruit mass measurements.')
F(562,evidence=[560,561,562,564,588,592,597],note='Dutta predicts she will still catch the bus; walking toward market gate does not prove actual boarding.')
F(678,evidence=[59,61,198,208,569,676,677,678,682,685],note='Birthday-pie slice is retrospectively linked to the pie discussed earlier; no grandson arrival, complete pie-eating event, or physical handoff details are invented.')
for eid,event in a.events.items():
    event['support_words']=sorted({event['trigger']}|{w for w,row in enumerate(a.words) for binding in row.get('event_bindings',[]) if binding['event_id']==eid})

FEEDBACK={
 'summary':'Complete manual retrospective annotation preserving false initial weight claim, actual faulty dial observation, corrected measurements, considered dishonest alternative, disclosed fault, fulfilled physical scale return and uncompleted future plans.',
 'ambiguities':[
  {'words':[52,239,249,277,335,472],'issue':'The narrative treats the corrected 1.75-kilo measurement as order mass despite weighing the paper bag too. Bag mass/tare is unspecified; no engineering correction is invented.'},
  {'words':[463,465,467],'issue':'Three small apples correct the order. Their individual masses and whether any earlier apples were swapped are not specified.'},
  {'words':[601,635,652,691,695],'issue':'Scale is explicitly returned to Boulos. Final pie beside scale establishes co-location, not a second loan, transfer back to Mina, or exact final stall location.'},
  {'words':[187,190,199,207,562,588,597,678],'issue':'Bus boarding and grandson arrival/meal remain expected, not observed, even though Dutta later returns with pie.'},
  {'words':[627],'issue':'Cleaned is linked to the narrated leaf removal; no additional washing or unreported mechanical repair is asserted.'},
  {'words':[78,280,430,665],'issue':'Grin, frown, hot cheeks and first position on tomorrow’s list are concrete evidence; named emotions and a permanent trust or competence trait are not certain.'},
 ],
 'feature_gaps':[
  {'meaning':'instrument indication versus object measurement versus false quantity claim','resolution':'Existing quantity_total/comparison objects retain measure_kind, phase, source scope and evidence. Do not conflate a true reading observation with a false mass assertion.'},
  {'meaning':'load tare uncertainty','resolution':'Document missing mass premise; no new field or inferred numeric bag tare is needed.'},
 ],
 'prompt_feedback':[
  'Retain observation truth separately from the property inferred from a faulty instrument; later correction does not erase earlier dial motion.',
  'In quantity-change stories distinguish the initial measured state from a later physical correction; neither should overwrite earlier evidence.',
  'A scale that says more is a figurative instrument reading, not a speaking agent.',
  'Nested private alternatives and attributed reports need their own scoped content; no-one-would-know is not an actual knowledge claim about all characters.',
  'Final co-location does not establish a new loan or unmentioned transfer after an explicit return.',
 ],
 'coverage_notes':'Every one of 714 words has manually specified contextual POS and lemma. All 1,024 catalog definitions were available and previously reviewed, with used meanings consulted during annotation. Supported sparse entity, event, grammar, measurement, spatial, possession, mental, speech, scope and evidence fields are applied without a coverage quota. Agreed trial extensions only. Whole-story retrospective, no causal filtering or API.',
 'reviewed_all_words':True,
}
a.save(FEEDBACK)
# Compact paragraph view for a manual source-versus-assembled annotation review.
import json
out=[]
for p in a.paragraphs:
    out.append(f"P{p['paragraph']}" if 'paragraph' in p else 'PARAGRAPH')
    for item in p['words']:
        r=a.words[item['w']]
        fields={k:v for k,v in r.items() if k not in {'token','index','start','end','kind','position','word_index','entity_name','event','event_bindings','reference_chain_id'}}
        out.append(f"{item['w']} {r['token']} "+json.dumps(fields,ensure_ascii=False,separators=(',',':')))
(a.output/'review_words.txt').write_text('\n'.join(out)+'\n')
