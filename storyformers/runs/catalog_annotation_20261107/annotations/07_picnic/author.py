"""Explicit manual whole-story interpretation, with unresolved source transitions."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a=Annotation('07_picnic',prompt_version='v1')
for key in ('appearance_color','part_whole_relation','figurative_mapping'):
    a.use_extension(key)

TAGS=[
 'adp num adv n conj n v n n adj n n adv adp det adj n pron v v part v pron conj n n v v pron part adp det n',
 'v pron adv adp n n pron v conj det n adp det n',
 'pron v adj n v',
 'pron v v n n n conj det n adp n adp det n n pron v v adp n adj n pron v v part v pron adp n n v v det n n adp adj n n v v det adj n conj pron v det n v det n',
 'pron v det adj n adv adp det n n v det n conj v det n n v det n adp det n adv pron v part v adv v num n',
 'det n v adv adv pron v',
 'pron v part',
 'det n v v det n',
 'n v pron adv conj v pron adp det n adp det n adv adv n v v pron adj pron v',
 'n v det n n adp det n n v det adj n adp n n',
 'pron v v n adv n v',
 'pron v n n pron v n',
 'pron v n',
 'pron n n',
 'n v pron v pron adj adv',
 'pron v det n n adp det n conj pron v adp det n adp det n adp num num pron v det n adv adv det n det n v adp det n conj det n n v adj',
 'adv pron v adj n v',
 'conj adv pron part v n v conj pron v v det n',
 'adv adv det n v adp det n det n n v adj det n v conj num n adp det n v adp det n det n v part v adp det n',
 'v pron n v',
 'n v det n n n v det n adp det n n det n v adp det n adp det n adp n conj v adp det n adp det n',
 'n v pron v pron v v adp det n conj det n v v adv adp det n det n v adp det n',
 'v pron v n v',
 'n v det n adp det n n v det n adv adp det n det n v adp det n det adj n v num n v adp det n conj det n n v adp det n',
 'adp det n det n v',
 'pron v v part n v det n adv adj adv',
 'n v adp det adj n n n v adv v',
 'pron v part det adj n conj v pron adp det n v v det pron adp pron',
 'n v adp det n adp det n adv adp det n det n v det adj adj n',
 'intj pron v conj pron v det n adp pron',
 'pron v det n n adp adj n conj v det n pron v n v det n adj adp det n n v n adp det n pron v adv conj v v adp det n v adp det n',
 'adp adv det n v adp det n v det n adp det adj n det n v part adp num n conj num n n v adj',
 'pron adj pron v det n n v adj conj adv det n v adj',
 'n n v part adv adv pron adv v part det n',
 'n v adp det adj n v det n v det pron',
 'pron adv v det n n v pron adp det n',
 'n v adp det n adv v adv pron adj pron v v adp pron pron v v pron',
 'n v part det adj n pron v pron adp pron',
 'n v pron adv adp num adv pron v pron v pron n v part det n pron n v adv',
 'pron v det adj adj n v n n conj n adp det adj n conj det n v adj n v pron v det n adp n n n det adj n v adv adp det n adv v adp det n pron v pron adv adp det adj n n adv adj conj adj v adv adp det n n',
]
LEMMA={
 'Bea':'Bea','Sam':'Sam','Theo':'Theo','Theo’s':'Theo','Aunt':'Aunt','June':'June','June’s':'June',
 'carried':'carry','had':'have','asked':'ask','handed':'hand','stains':'stain','said':'say','We’ll':'we',
 'promised':'promise','packed':'pack','sandwiches':'sandwich','pears':'pear','moved':'move',
 'was':'be','supposed':'suppose','them':'they','made':'make','needs':'need','chose':'choose',
 'smoothed':'smooth','set':'set','could':'can','arranged':'arrange','plates':'plate','is':'be',
 'words':'word','are':'be','facing':'face','turned':'turn','pinned':'pin','we’re':'we','came':'come',
 'slices':'slice','biggest':'big','might':'may','better':'well','told':'tell','likes':'like','I':'I',
 'It’s':'it','sighed':'sigh','I’m':'I','heard':'hear','belonged':'belong','crept':'creep','grew':'grow',
 'got':'get','lost':'lose','he’s':'he','coming':'come','kept':'keep','watching':'watch','rushed':'rush',
 'tore':'tear','napkins':'napkin','flew':'fly','lifted':'lift','began':'begin','shouted':'shout',
 'caught':'catch','planted':'plant','hands':'hand','blanket’s':'blanket','skittered':'skitter',
 'buttercups':'buttercup','snagged':'snag','reeds':'reed','saw':'see','pulling':'pull','fingers':'finger',
 'wobbled':'wobble','called':'call','leaned':'lean','dragged':'drag','stayed':'stay','letters':'letter',
 'flapping':'flap','tumbled':'tumble','scattered':'scatter','spoke':'speak','food’s':'food',
 'looked':'look','picked':'pick','cleanest':'clean','wrapped':'wrap','Let’s':'let','him':'he',
 'glanced':'glance','gave':'give','saving':'save','me':'I','weighted':'weight','corners':'corner',
 'stones':'stone','gathered':'gather','wiped':'wipe','brushed':'brush','sat':'sit','waited':'wait',
 'listening':'listen','appeared':'appear','pushing':'push','stuck':'stick','closed':'close','went':'go',
 'stood':'stand','kicked':'kick','Did':'do','stole':'steal','peered':'peer','didn’t':'do','I’d':'I',
 'missed':'miss','held':'hold','saved':'save','broke':'break','ate':'eat','trading':'trade','stories':'story',
 'were':'be','helped':'help','crumbs':'crumb','checks':'check','billowed':'billow','settled':'settle',
 'arms':'arm','folded':'fold','bent':'bend','tucked':'tuck',
}
for p,tags in enumerate(TAGS): a.tag(p,tags,LEMMA)

ENTITIES=[
 ('Bea','person',[3,50,82,114,138,154,184,263,314,321,348,352,365,378,380,434,445,514,577,582,630]),
 ('Sam','person',[5,91,98,122,143,176,197,206,212,214,216,270,273,316,376,385,427,463,469,475,483,486,491,506,605,653]),
 ('Theo','person',[65,66,67,74,169,174,190,192,199,203,210,246,260,267,441,462,536,548,561,563,572,576,588,611,619,626,640,641,659,682]),
 ('Aunt June','person',[7,8,24,25,39,201,202,689,690]),
 ('Bea and Sam','person_group',[17,47,52,64,79,105,172,219,239,421,423,492,504,520,603,621,629,636,684]),
 ('Bea, Sam and Theo','person_group',[648,650,662,664,703,705]),
 ('Aunt June’s blue picnic blanket','blanket',[10,11,22,28,34,117,153,299,327,360,384,416,495,691,707,722]),
 ('riverside meadow','meadow',[15,16,285]),
 ('river','river',[311,528,531,615]),
 ('packed sandwiches','sandwich_group',[55]),
 ('packed pears','pear_group',[56]),
 ('picnic cheese','cheese',[57,519]),
 ('lemonade jug','jug',[60,125,130,256,368,509,587]),
 ('lemonade','lemonade',[43,62,255]),
 ('town Theo moved to','town',[71]),
 ('green-crayon welcome sign','sign',[87,139,145,156,160,288,330,350,357,374,394,399,604,607,625,713]),
 ('green crayon medium used on sign','crayon_medium',[90,712]),
 ('Sam’s extra cookie','cookie',[96,467,489,657,658]),
 ('flat picnic spot','ground_region',[109]),
 ('riverbank','riverbank',[113]),
 ('blanket wrinkles','wrinkle_group',[121]),
 ('middle of blanket','region',[128]),
 ('three picnic plates','plate_group',[137,679]),
 ('sign inscription','inscription',[149,401]),
 ('picnic basket','basket',[163,305,313,319,372,388]),
 ('sign clothespin','clothespin',[166]),
 ('pear slices','food_piece_group',[179,180,411,670]),
 ('pear sunburst arrangement','food_arrangement',[183,412]),
 ('biggest sandwich initially put on Theo’s plate','sandwich',[188]),
 ('Theo’s plate','plate',[191]),
 ('picnic lunch','meal',[209,211,430,503,593,667]),
 ('first heard bicycle bell','bicycle_bell',[222,223,228]),
 ('path beside meadow','path',[226,277,540]),
 ('man with dog','person',[232]),
 ('man’s dog','dog',[235]),
 ('second distant bell','bell',[242]),
 ('sun','star',[248]),
 ('meadow grass','grass',[252,334,408,516]),
 ('gust of wind','wind',[281,596,600]),
 ('picnic napkins','napkin_group',[292]),
 ('lifted blanket corner','blanket_corner',[296]),
 ('basket handle','handle',[320]),
 ('Bea’s hands','body_part_group',[324]),
 ('blanket edge','edge',[328]),
 ('patch of buttercups','flower_patch',[337]),
 ('buttercups','flower_group',[339]),
 ('reeds by river','reed_group',[344,398,610]),
 ('river water','water',[347]),
 ('Bea’s fingers','body_part_group',[366]),
 ('sandwich that falls on grass','sandwich',[404]),
 ('Theo’s unoccupied place setting','place_setting',[439,440]),
 ('cleanest sandwich reserved and shared','sandwich',[450,453,460,474,635,638,643]),
 ('napkin wrapping saved sandwich','napkin',[456]),
 ('Sam’s pocket','pocket',[470]),
 ('Sam’s stomach','body_part',[476]),
 ('blanket corners','blanket_corner_group',[496]),
 ('stones used as blanket weights','stone_group',[499]),
 ('napkin used to wipe jug','napkin',[513]),
 ('river stones','stone_group',[532]),
 ('Theo’s bicycle','bicycle',[543]),
 ('flat bicycle tire','tire',[547,573]),
 ('Theo’s hair','hair',[549]),
 ('Theo’s trouser cuff','clothing_part',[558]),
 ('closed bridge path','path',[566,567]),
 ('crumbs on blanket','food_fragment_group',[687]),
 ('blue checks on blanket','pattern',[694]),
 ('later breeze','wind',[699]),
 ('three cousins’ arms','body_part_group',[704]),
 ('blanket fringe','fringe',[46,723]),
 ('stories about neighborhood','story_group',[672]),
 ('Theo’s new neighborhood','neighborhood',[676]),
 ('cheese as a food kind','food_kind',[195,205,208]),
]
for i,(name,kind,mentions) in enumerate(ENTITIES,1): a.entity(f'e{i}',name,kind,mentions)
a.entities['e50']['possible_same_as']=['e29']
a.entities['e52']['possible_same_as']=['e29','e50']
a.feature([195,205,208],generic_reference=True,referent_kind='kind')
a.feature(104,generic_reference=True,referent_kind='kind')
for eid,members in [('e5',['e1','e2']),('e6',['e1','e2','e3'])]:
    a.entities[eid]['members']=members
    for w in a.entities[eid]['mentions']: a.feature(w,group_members=members)

QUOTES=[
 ('q1',33,39,'e4',['e1','e2'],'return instruction'),('q2',41,47,'e4',['e1','e2'],'blanket care warning'),
 ('q3',47,50,'e1',['e4'],'promise of care'),('q4',100,105,'e2',['e1'],'cookie justification'),
 ('q5',138,143,'e2',['e1'],'sign orientation claim'),('q6',145,148,'e1',['e2'],'denial'),
 ('q7',148,154,'e2',['e1'],'orientation evidence'),('q8',167,176,'e1',['e2'],'welcome prediction'),
 ('q9',192,197,'e2',['e1'],'uncertain cheese preference'),('q10',199,206,'e1',['e2'],'report of Theo’s preference'),
 ('q11',206,209,'e2',['e1'],'Sam’s preference'),('q12',209,212,'e1',['e2'],'intended beneficiary reminder'),
 ('q13',214,219,'e2',['e1'],'acknowledgment and hunger'),('q14',259,263,'e1',['e2'],'lost-route conjecture'),
 ('q15',265,270,'e2',['e1'],'nonarrival conjecture'),('q16',312,314,'e1',['e2'],'urgent request'),
 ('q17',373,376,'e2',['e1'],'request to leave sign'),('q18',423,427,'e2',['e1'],'packing proposal'),
 ('q19',429,434,'e2',['e1'],'food state report'),('q20',441,445,'e1',['e2'],'continued arrival possibility'),
 ('q21',457,463,'e1',['e2'],'reserve sandwich proposal'),('q22',482,483,'e2',['e1'],'assent'),
 ('q23',485,492,'e2',['e1'],'cookie reservation'),('q24',561,563,'e3',['e1','e2'],'apology'),
 ('q25',565,576,'e3',['e1','e2'],'delay explanation'),('q26',576,577,'e1',['e3'],'recognition greeting'),
 ('q27',594,600,'e3',['e1','e2'],'wind-cause question'),('q28',600,605,'e2',['e3'],'lost-sign report'),
 ('q29',607,611,'e2',['e3'],'sign location report'),('q30',619,630,'e3',['e1','e2'],'gladness and unrealized missed meeting'),
 ('q31',636,641,'e1',['e3'],'saved-food report'),('q32',647,653,'e3',['e1','e2'],'sharing offer')]
for sid,start,stop,holder,audience,description in QUOTES:
    a.scope(sid,range(start,stop),kind='quotation',holder_id=holder,description=description)
    a.scopes[sid]['addressee_ids']=audience
    a.feature(range(start,stop),quote_mode='direct')
SUBSCOPES=[
 ('s1',20,23,'requested_loan','s0','e5','Borrowing as earlier request content; actual loan is separate.'),
 ('s2',77,82,'expected_meeting','s0','e3','Noon meeting expectation, not actual noon arrival.'),
 ('s3',129,134,'prospective_stability','s0',None,'Could not tip is situated stability assessment, not timeless impossibility.'),
 ('s4',172,176,'predicted_knowledge_content','q8','e3','Predicted content of Theo’s knowledge; not present omniscience.'),
 ('s5',203,206,'nested_report','q10','e3','Theo’s reported cheese preference, via Bea’s report of telling June.'),
 ('s6',352,358,'possible_pursuit','s0','e1','Unchosen possible run after sign.'),
 ('s7',583,588,'near_miss','s0','e1','Jug was nearly kicked over; no completed kick or spill.'),
 ('s8',626,630,'counterfactual','q30','e3','Missed meeting only under the unrealized departure alternative.'),
]
for sid,start,stop,kind,parent,holder,desc in SUBSCOPES:
    a.scope(sid,range(start,stop),kind=kind,parent=parent,holder_id=holder,description=desc)

E={}
def ev(w,label,type='other',actor=None,patients=(),instruments=(),recipient=None,factuality='asserted',roles=None,**kw):
    eid=f'ev{len(a.events)+1}'
    a.event(eid,w,label,type=type,actor=actor,patients=patients,instruments=instruments,recipient=recipient,factuality=factuality,roles=roles,**kw)
    E[w]=eid
    return eid
def mention(w,earlier,role='action',note='Same underlying event or continuing state, mentioned again.'):
    a.mention_event(E[earlier],w,role=role,note=note);E[w]=E[earlier]
def b(w,eid,value,status=None):
    scope=a.words[w]['scope_id']
    return dict(entity_id=eid,scope_id=scope,assertion_status=status or ('attributed_claim' if scope.startswith('q') or scope in ('s4','s5','s8') else 'asserted'),value=value)

ev(6,'carry borrowed blanket to riverside meadow','move','e5',['e7'],roles={'actor':[3,5],'patient':[11],'location':[16]})
ev(19,'ask June to borrow blanket','speak','e5',recipient='e4',roles={'actor':[17]})
ev(21,'borrow blanket as requested','obtain','e5',['e7'],factuality='desired',roles={'patient':[22]})
ev(27,'June lends blanket to Bea and Sam','transfer','e4',['e7'],recipient='e5',roles={'actor':[24,25],'patient':[28]})
ev(33,'return blanket without stains as instructed','transfer','e5',['e7'],recipient='e4',factuality='desired',roles={'patient':[34]})
ev(40,'June gives blanket-care warning','speak','e4',recipient='e5',roles={'actor':[39]})
ev(49,'Bea and Sam will be careful as promised','state','e5',factuality='desired',roles={'actor':[47]})
ev(51,'Bea promises care of blanket','speak','e1',recipient='e4',roles={'actor':[50]})
ev(54,'pack picnic food and lemonade','other','e5',['e10','e11','e12','e13'],roles={'actor':[52],'patient':[55,56,57,60],'recipient':[66]})
ev(69,'Theo moves to town last month','move','e3',roles={'actor':[67],'location':[71]})
ev(78,'Theo meets cousins at noon as arranged','other','e3',['e5'],factuality='desired',roles={'patient':[79]})
ev(84,'Bea makes welcome sign','other','e1',['e16'],['e17'],roles={'actor':[82],'patient':[87],'instrument':[90]})
ev(93,'Sam packs extra cookie','other','e2',['e18'],roles={'actor':[91],'patient':[96]})
ev(99,'Sam justifies packing cookie','speak','e2',recipient='e1',roles={'actor':[98]})
ev(102,'a welcome needs a cookie in Sam’s view','state',factuality='reported')
ev(106,'choose flat picnic spot','other','e5',['e19'],roles={'actor':[105],'patient':[109]})
ev(115,'Bea spreads blanket','other','e1',['e7'],roles={'actor':[114],'patient':[117]})
ev(119,'Bea smooths blanket wrinkles','other','e1',['e21'],roles={'patient':[121]})
ev(123,'Sam sets jug in blanket middle','move','e2',['e13'],roles={'actor':[122],'patient':[125],'location':[128]})
ev(133,'jug tips in chosen position','state',patients=['e13'],factuality='negated',roles={'patient':[130]})
ev(135,'Sam arranges three plates','other','e2',['e23'],roles={'patient':[137]})
ev(140,'sign is upside down according to Sam','state',patients=['e16'],factuality='reported',roles={'patient':[139],'modifier':[141,142]})
ev(144,'Sam points out sign orientation','speak','e2',recipient='e1',roles={'actor':[143]})
ev(146,'sign is upside down','state',patients=['e16'],factuality='negated',roles={'patient':[145]})
ev(151,'sign words face blanket','state',patients=['e24'],factuality='reported',roles={'patient':[149],'location':[153]})
ev(155,'Bea turns sign around','other','e1',['e16'],roles={'actor':[154],'patient':[156]})
ev(159,'Bea pins sign to basket','other','e1',['e16'],['e26'],roles={'patient':[160],'location':[163],'instrument':[166]})
ev(171,'Theo will know cousins are glad about his move','state','e3',factuality='hypothetical',roles={'actor':[169]})
ev(173,'cousins are happy Theo came to town','feel','e5',factuality='reported',roles={'actor':[172]})
mention(175,69,note='Came most plausibly refers to Theo’s recent move to town: he has not yet reached the picnic.')
a.mention_event(E[69],174,role='actor')
ev(177,'Sam arranges pear slices in sunburst','other','e2',['e27'],roles={'actor':[176],'patient':[180]})
ev(185,'Bea puts biggest sandwich on Theo’s plate','move','e1',['e29'],roles={'actor':[184],'patient':[188],'location':[191]})
ev(194,'Theo might prefer cheese','state','e3',['e72'],factuality='hypothetical',roles={'actor':[192],'patient':[195]})
ev(198,'Sam speculates about Theo’s preference','speak','e2',recipient='e1',roles={'actor':[197]})
ev(200,'Theo previously tells June he likes cheese','speak','e3',recipient='e4',factuality='reported',roles={'actor':[199],'recipient':[201,202]})
ev(204,'Theo likes cheese in reported claim','state','e3',['e72'],factuality='reported',roles={'actor':[203],'patient':[205]})
ev(207,'Sam likes cheese','state','e2',['e72'],factuality='reported',roles={'actor':[206],'patient':[208]})
ev(209,'lunch is intended for Theo','state',patients=['e31'],recipient='e3',factuality='reported',roles={'recipient':[210]})
ev(213,'Sam sighs','other','e2',roles={'actor':[212]})
ev(215,'Sam acknowledges lunch is for Theo','state','e2',factuality='reported',roles={'actor':[214]})
ev(217,'Sam reports hunger','state',patients=['e2'],factuality='reported',roles={'patient':[216]})
ev(220,'cousins hear first bicycle bell','perceive','e5',['e32'],roles={'actor':[219],'patient':[223],'location':[226]})
ev(229,'first bell belongs to man with dog','state',patients=['e32'],recipient='e34',roles={'patient':[228],'recipient':[232]})
ev(240,'cousins hear another distant bell','perceive','e5',['e36'],roles={'actor':[239],'patient':[242]})
ev(246,'Theo has arrived by twelve thirty','state',patients=['e3'],factuality='negated')
ev(249,'sun’s illumination advances across grass as time passes','other','e37',roles={'actor':[248],'location':[252]})
ev(257,'lemonade jug grows warm','state',patients=['e13'],roles={'patient':[256],'modifier':[258]})
ev(262,'Theo may be lost in Bea’s conjecture','state',patients=['e3'],factuality='hypothetical',roles={'patient':[260]})
ev(264,'Bea suggests Theo got lost','speak','e1',recipient='e2',roles={'actor':[263]})
ev(269,'Theo comes to the picnic','move','e3',factuality='hypothetical',roles={'actor':[267]})
ev(271,'Sam suggests Theo is not coming','speak','e2',recipient='e1',roles={'actor':[270]})
ev(275,'Sam keeps watching path','perceive','e2',['e33'],roles={'actor':[273],'patient':[277]})
ev(282,'gust rushes across meadow','move','e39',roles={'actor':[281],'location':[285]})
ev(289,'wind frees and carries away welcome sign','move','e39',['e16'],roles={'patient':[288],'modifier':[290]})
ev(293,'napkins fly in gust','move','e40',roles={'actor':[292]})
ev(300,'blanket corner lifts like sail','move','e41',roles={'actor':[296]})
ev(308,'basket begins sliding toward river','move','e25',roles={'actor':[305],'location':[311]})
ev(312,'Sam should grab basket','other','e2',['e25'],factuality='desired',roles={'patient':[313]})
ev(315,'Bea shouts to Sam to grab basket','speak','e1',recipient='e2',roles={'actor':[314]})
ev(317,'Sam catches basket handle','other','e2',['e42'],roles={'actor':[316],'patient':[320]})
ev(322,'Bea plants hands on blanket edge','other','e1',['e43'],roles={'actor':[321],'patient':[324],'location':[328]})
ev(331,'sign skitters toward river through grass','move','e16',roles={'actor':[330],'location':[334,337]})
ev(341,'sign snags in reeds near water','other',patients=['e16'],roles={'location':[344,347]})
ev(349,'Bea sees sign go','perceive','e1',['e16'],roles={'actor':[348],'patient':[350]})
mention(351,331)
ev(354,'Bea could run after sign','move','e1',['e16'],factuality='hypothetical',roles={'actor':[352],'patient':[357]})
ev(362,'blanket pulls against Bea’s fingers','other','e7',['e49'],roles={'actor':[360],'patient':[366]})
ev(369,'jug wobbles inside basket','move','e13',roles={'actor':[368],'location':[372]})
ev(375,'leave sign instead of pursuing it','other','e1',['e16'],factuality='desired',roles={'patient':[374]})
ev(377,'Sam urges Bea to let sign go','speak','e2',recipient='e1',roles={'actor':[376]})
ev(379,'Bea leans weight onto blanket','other','e1',['e7'],roles={'actor':[378],'patient':[384]})
ev(386,'Sam drags basket back','move','e2',['e25'],roles={'actor':[385],'patient':[388]})
ev(395,'sign stays in reeds','state',patients=['e16'],roles={'patient':[394],'location':[398]})
ev(402,'sign inscription flaps with its carrier','move','e16',roles={'actor':[401]})
ev(405,'one sandwich tumbles onto grass','move','e50',roles={'actor':[404],'location':[408]})
ev(413,'pear arrangement scatters across blanket','move','e27',roles={'actor':[412],'location':[416]})
ev(422,'cousins speak during the pause','speak','e5',factuality='negated',roles={'actor':[421]})
ev(425,'pack up as Sam proposes','other','e5',['e31'],factuality='desired',roles={'actor':[423]})
ev(428,'Sam suggests packing up','speak','e2',recipient='e1',roles={'actor':[427]})
ev(432,'food is mixed up according to Sam','state',patients=['e31'],factuality='reported',roles={'patient':[430]})
ev(435,'Bea looks at Theo’s unoccupied place setting','perceive','e1',['e51'],roles={'actor':[434],'patient':[440]})
ev(444,'Theo might still arrive','move','e3',factuality='hypothetical',roles={'actor':[441]})
ev(446,'Bea picks up cleanest sandwich','obtain','e1',['e52'],roles={'actor':[445],'patient':[450]})
ev(452,'Bea wraps sandwich to reserve it for Theo','other','e1',['e52'],['e53'],roles={'patient':[453],'instrument':[456]})
ev(458,'keep sandwich for Theo as proposed','other','e5',['e52'],recipient='e3',factuality='desired',roles={'patient':[460],'recipient':[462]})
ev(464,'Sam glances at cookie then sandwich','perceive','e2',['e18','e52'],roles={'actor':[463],'patient':[467,474]})
ev(477,'Sam’s stomach growls loudly','other','e55',roles={'actor':[476],'modifier':[479,480]})
ev(484,'Sam agrees to save sandwich','speak','e2',recipient='e1',roles={'actor':[483]})
ev(487,'Sam reserves cookie for himself','state','e2',['e18'],recipient='e2',factuality='reported',roles={'actor':[486],'patient':[489],'recipient':[491]})
ev(493,'cousins weight blanket corners with stones','other','e5',['e56'],['e57'],roles={'actor':[492],'patient':[496],'instrument':[499]})
ev(501,'cousins gather recoverable food','obtain','e5',['e31'],roles={'patient':[503],'actor':[504]})
ev(507,'Sam wipes jug dry with napkin','other','e2',['e13'],['e58'],roles={'actor':[506],'patient':[509],'modifier':[510],'instrument':[513]})
ev(515,'Bea brushes grass off cheese','other','e1',['e12'],roles={'actor':[514],'patient':[519]})
ev(521,'cousins sit together','state','e5',roles={'actor':[520]})
ev(524,'cousins wait for Theo','state','e5')
ev(525,'cousins listen to river','perceive','e5',['e9'],roles={'patient':[528]})
ev(529,'river flows over stones','move','e48',roles={'location':[532]})
ev(537,'Theo appears on path','move','e3',roles={'actor':[536],'location':[540]})
ev(541,'Theo pushes bicycle with flat tire','move','e3',['e60'],roles={'patient':[543]})
ev(550,'Theo’s hair sticks up on one side','state',patients=['e62'],roles={'patient':[549]})
ev(560,'Theo’s trouser cuff is muddy','state',patients=['e63'],roles={'patient':[558]})
ev(564,'Theo calls apology','speak','e3',recipient='e5',roles={'actor':[563]})
ev(569,'bridge path was closed in Theo’s report','state',patients=['e64'],factuality='reported',roles={'patient':[567]})
ev(574,'Theo’s tire goes flat','other',patients=['e61'],factuality='reported',roles={'patient':[573],'modifier':[575]})
ev(578,'Bea stands quickly on recognizing Theo','move','e1',roles={'actor':[577]})
ev(584,'Bea nearly kicks jug over','other','e1',['e13'],factuality='hypothetical',roles={'patient':[587]})
ev(589,'Theo looks at scattered lunch','perceive','e3',['e31'],roles={'actor':[588],'patient':[593]})
ev(597,'wind caused scattered lunch as questioned','other','e39',['e31'],factuality='hypothetical',roles={'actor':[596]})
mention(602,289,note='Wind stole our sign refers to the physical wind-driven sign loss, without attributing theft intention.')
a.mention_event(E[289],600,role='actor');a.mention_event(E[289],604,role='patient')
ev(606,'Sam reports lost sign','speak','e2',recipient='e3',roles={'actor':[605]})
mention(607,395,note='Current location in reeds is repeated; no recovery is supplied.')
a.mention_event(E[395],610,role='location')
ev(612,'Theo peers toward river','perceive','e3',['e9'],roles={'actor':[611],'patient':[615]})
ev(617,'Theo turns back to cousins','move','e3')
ev(620,'Theo is glad cousins did not pursue sign','feel','e3',factuality='reported',roles={'actor':[619]})
ev(623,'cousins pursue sign in Theo’s claim','move','e5',['e16'],factuality='negated',roles={'actor':[621],'patient':[625]})
ev(628,'Theo would have missed cousins if they left','other','e3',['e5'],factuality='hypothetical',roles={'actor':[626],'patient':[629]})
ev(631,'Bea offers wrapped sandwich','transfer','e1',['e52'],recipient='e3',roles={'actor':[630],'patient':[635]})
ev(637,'cousins kept sandwich for Theo','other','e5',['e52'],recipient='e3',factuality='reported',roles={'actor':[636],'patient':[638],'recipient':[640]},support=[452,458,484,524,636,637,638,640])
ev(642,'Theo breaks sandwich into three pieces','other','e3',['e52'],roles={'actor':[641],'patient':[643]})
ev(651,'all three can have some sandwich','obtain','e6',['e52'],factuality='desired',roles={'actor':[648,650]})
ev(654,'Sam gives cookie to Theo','transfer','e2',['e18'],recipient='e3',roles={'actor':[653],'patient':[657]})
ev(660,'Theo splits cookie for sharing','other','e3',['e18'],roles={'actor':[659],'patient':[658]})
ev(663,'three cousins eat picnic lunch','other','e6',['e31'],roles={'actor':[662],'patient':[667]})
ev(668,'cousins exchange pear slices','transfer','e6',['e27'],roles={'patient':[670]})
ev(672,'cousins exchange neighborhood stories','speak','e6',['e70'],primary=False)
ev(681,'plates are empty after lunch','state',patients=['e23'],roles={'patient':[679]})
ev(683,'Theo helps cousins clean blanket','other','e3',['e5'],roles={'actor':[682],'patient':[684]})
ev(685,'three cousins shake crumbs from blanket','other','e6',['e65'],roles={'patient':[687],'location':[691]})
ev(695,'blanket billows once in breeze','move','e7',roles={'actor':[694]})
ev(701,'blanket settles across cousins’ arms','move','e7',roles={'location':[704]})
ev(706,'cousins fold blanket together','other','e6',['e7'],roles={'actor':[705],'patient':[707]})
ev(715,'sign remains readable','state',patients=['e16'])
ev(717,'sign is bent at ending','state',patients=['e16'])
ev(718,'sign is tucked inside folded blanket fringe','state',patients=['e16'],roles={'location':[723]},support=[706,707,713,718,720,723])

# Actual communication instances are distinct from their content predicates.
UTTERANCES=[
 ('q1',40,'e4',['e1','e2'],'instruction'),('q2',40,'e4',['e1','e2'],'warning'),
 ('q3',51,'e1',['e4'],'promise'),('q4',99,'e2',['e1'],'justification'),
 ('q5',144,'e2',['e1'],'orientation_claim'),('q6',145,'e1',['e2'],'denial'),
 ('q7',148,'e2',['e1'],'counterevidence'),('q8',167,'e1',['e2'],'prediction'),
 ('q9',198,'e2',['e1'],'conjecture'),('q10',199,'e1',['e2'],'preference_report'),
 ('q11',206,'e2',['e1'],'preference_statement'),('q12',211,'e1',['e2'],'reminder'),
 ('q13',214,'e2',['e1'],'acknowledgment_and_hunger'),('q14',264,'e1',['e2'],'conjecture'),
 ('q15',271,'e2',['e1'],'alternative_conjecture'),('q16',315,'e1',['e2'],'urgent_request'),
 ('q17',377,'e2',['e1'],'urgent_request'),('q18',428,'e2',['e1'],'proposal'),
 ('q19',428,'e2',['e1'],'food_state_report'),('q20',441,'e1',['e2'],'continued_possibility'),
 ('q21',457,'e1',['e2'],'proposal'),('q22',484,'e2',['e1'],'assent'),
 ('q23',484,'e2',['e1'],'reservation_claim'),('q24',564,'e3',['e1','e2'],'apology'),
 ('q25',564,'e3',['e1','e2'],'explanation'),('q26',576,'e1',['e3'],'greeting'),
 ('q27',594,'e3',['e1','e2'],'question'),('q28',606,'e2',['e3'],'report'),
 ('q29',606,'e2',['e3'],'location_report'),('q30',619,'e3',['e1','e2'],'gladness_statement'),
 ('q31',636,'e1',['e3'],'offer_explanation'),('q32',647,'e3',['e1','e2'],'sharing_offer')]
for sid,w,speaker,audience,act in UTTERANCES:
    existing=E.get(w)
    if existing and a.events[existing]['event_type']=='speak': eid=existing
    else:
        eid=f'ev{len(a.events)+1}'
        a.event(eid,w,act,type='speak',actor=speaker,recipient=audience[0] if len(audience)==1 else 'e5',scope='s0',primary=False,support=a.scopes[sid]['words'])
    a.scopes[sid]['utterance_event_id']=eid
    a.feature(w,communication_scope_bundle=dict(speaker_id=speaker,utterance_event_id=eid,scope_id='s0',assertion_status='asserted'),speech_act_kind=act,utterance_id=eid,addressee_ids=audience,communication_channel='speech')

PROPS=[
 ('The borrowed blanket is returned to June without grass stains or lemonade on its fringe.',[33,34,36,38,42,43,46],'q1'),
 ('Bea and Sam handle the blanket carefully.',[47,48,49],'q3'),
 ('Theo meets Bea and Sam at noon.',[74,76,78,79,81],'s2'),
 ('The sign is upside down.',[139,140,141,142],'q5'),
 ('The sign’s words face the blanket.',[149,151,153],'q7'),
 ('Bea and Sam are happy that Theo moved to town.',[69,71,172,173,174,175],'s4'),
 ('Theo likes cheese.',[203,204,205],'s5'),
 ('The picnic lunch is intended for Theo.',[209,210,211],'q12'),
 ('Theo is lost.',[259,260,261,262],'q14'),
 ('Theo is not coming to the picnic.',[266,267,268,269],'q15'),
 ('Bea pursues the sign.',[352,353,354,357],'s6'),
 ('Bea and Sam pack up before Theo arrives.',[423,424,425,426],'q18'),
 ('Theo still arrives at the picnic.',[441,442,443,444],'q20'),
 ('The wrapped sandwich is kept for Theo.',[458,460,462],'q21'),
 ('The cookie is reserved for Sam.',[486,487,489,491],'q23'),
 ('Wind scatters the picnic food.',[282,405,413,596,597,599],'q27'),
 ('Bea and Sam did not pursue the sign.',[621,622,623,625],'q30'),
 ('Theo misses meeting his cousins.',[626,627,628,629],'s8'),
 ('All three cousins have some of the sandwich.',[648,650,651,652],'q32'),
 ('Bea and Sam leave to pursue the sign.',[621,623,625],'q30'),
 ('The picnic food is scattered.',[405,413,592,593,599],'s0'),
 ('The jug tips in its chosen position.',[129,130,131,132,133],'s3'),
 ('Theo comes to the picnic.',[265,266,267,268,269],'q15'),
]
for i,(text,support,scope) in enumerate(PROPS,1): a.proposition(f'p{i}',text,support,scope_id=scope)

# Contextual grammar and lexical inflection; no POS is inferred from spelling.
for w,r in enumerate(a.words):
    t,p=r['token'].casefold(),r['pos']
    if p=='det':
        if t in ('the','a','an'):
            a.feature(w,determiner_kind='definite_article' if t=='the' else 'indefinite_article',definiteness='definite' if t=='the' else 'indefinite')
        elif t in ('their','her','his','your','my','our','its'):
            a.feature(w,determiner_kind='possessive',possessive_construction='possessive_determiner')
        else:
            a.feature(w,determiner_kind={'no':'negative','neither':'negative_distributive','every':'universal','both':'dual','this':'demonstrative','all':'universal','another':'additive'}.get(t,'quantificational'))
    if p=='adp': a.feature(w,preposition_valency_frame='NP_complement')
    if p=='conj' and t in ('and','but','or'):
        a.feature(w,coordinator_type={'and':'conjunctive','but':'adversative','or':'disjunctive'}[t])
    if p=='part' and t=='to': a.feature(w,dependency_relation='infinitival_marker')
    if p=='pron' and t in ('they','we','we’ll','we’re','i','i’m','i’d','he','he’s','she','it','it’s','you','them','him','me'):
        a.feature(w,mention_form='personal_pronoun',grammatical_person=1 if t in ('we','we’ll','we’re','i','i’m','i’d','me') else 2 if t=='you' else 3)
        if t!='you': a.feature(w,grammatical_number='plural' if t in ('they','them','we','we’ll','we’re') else 'singular')
        if t in ('them','him','me'): a.feature(w,grammatical_case='objective')
    if p=='n' and 'entity_id' in r:
        a.feature(w,mention_form='proper_name' if r['lemma'] in ('Bea','Sam','Theo','Aunt','June') else 'nominal')
for w,exp in {47:['we','will'],172:['we','are'],209:['it','is'],216:['I','am'],267:['he','is'],430:['food','is'],457:['let','us'],486:['I','am'],561:['I','am'],607:['it','is'],619:['I','am'],622:['did','not'],626:['I','would']}.items():
    a.feature(w,contraction_expansion=exp)
for w in [8,190,210,327,495,690,722]: a.feature(w,genitive_realization='singular_s_clitic',possessive_construction='prenominal_s_genitive')
for w,value in [(1,11),(136,3),(237,12),(238,30),(295,1),(403,1),(553,1),(556,1),(646,3)]:
    a.feature(w,cardinal_value=value,numeral_syntactic_role='nominal_determiner')
for w in [187,449]: a.feature(w,adjective_degree='superlative')
a.feature(196,adverb_degree='comparative')
for w in [38,55,56,137,149,180,292,324,339,344,366,398,401,496,499,532,610,670,672,679,687,694,704]: a.feature(w,grammatical_number='plural')
for w in [43,57,62,90,195,205,208,252,255,334,347,408,516,519,549,712]: a.feature(w,noun_countability='mass')
for w in [33,312,373,375,457,458]: a.feature(w,verb_form='base',mood='imperative',imperative_subject_status='understood_addressee')
for w in [21,78,133,171,194,308,354,425,444,623,651,685]: a.feature(w,verb_form='base')
for w in [151,269,275,362,402,487,525,541,668]: a.feature(w,verb_form='gerund_participle')
for w in [76,432,634,718]: a.feature(w,verb_form='past_participle')
for w,aux in [(19,18),(27,26),(54,53),(69,68),(84,83),(93,92),(628,627)]:
    a.feature(w,verb_form='past_participle',aspect='perfect',perfect_auxiliary_id=a.anchor(aux))
for w,aux in [(151,150),(269,267),(362,361),(487,486)]:
    a.feature(w,aspect='progressive',progressive_auxiliary_id=a.anchor(aux))
PAST=[6,18,26,40,51,53,68,75,83,92,99,106,115,119,123,135,144,155,159,175,177,185,198,200,213,220,229,240,249,257,261,264,271,274,282,289,293,300,306,315,317,322,331,341,349,361,369,377,379,386,395,405,413,422,428,435,446,452,464,477,484,493,501,507,515,521,524,537,550,559,564,568,574,578,589,606,612,617,631,637,642,654,660,663,680,683,695,701,706]
for w in PAST:a.feature(w,verb_form='finite',tense='past')
for w in [102,140,146,150,204,207,215]:a.feature(w,verb_form='finite',tense='present')
for w in [131,193,353,424,442,649]: a.feature(w,modal_auxiliary_class='possibility_family')
a.feature(170,modal_auxiliary_class='volition_family')
a.feature(626,modal_auxiliary_class='volition_family')
for w in [132,147,268,622]: a.feature(w,negation_marker_form='not',polarity='negative')
a.feature(594,subject_auxiliary_inversion=True,clause_type='interrogative',verb_form='finite',tense='past')
a.feature(623,polarity='negative',negation_scope_id='p20')
a.feature(147,negation_scope_id='p4')
a.feature(132,negation_scope_id='p22')
a.feature(268,negation_scope_id='p23')
a.feature(146,verb_phrase_ellipsis=True)
a.feature(505,verb_phrase_ellipsis=True,coordination_ellipsis_source_id=a.anchor(501))
a.feature(129,relative_marker_form='locative_relative',relative_gap_role='location')
a.feature(67,relative_marker_form='human_pronoun',relative_gap_role='subject')
a.feature(658,relative_marker_form='nonhuman_pronoun',relative_gap_role='object')
for w in [134,279,471,571,616,647,700]:a.feature(w,temporal_order_cue='next')
a.feature(72,temporal_deixis='previous_month')
a.feature(73,temporal_granularity='month')
a.feature(81,time_expression_id='time_noon',temporal_granularity='hour')
for w in [443,714]:a.feature(w,temporal_phase_cue='persistence')
a.feature(306,temporal_phase_cue='onset')
a.feature(696,temporal_iteration_count=1)
for w in [97]:a.feature(w,subordinator_type='reason')
for w in [272,716]:a.feature(w,subordinator_type='concessive')
a.feature(677,subordinator_type='temporal')

# Explicit grammatical subjects, distinct from physical causers and semantic agents.
SUBJECT={6:'e5',19:'e5',27:'e4',40:'e4',51:'e1',54:'e5',69:'e3',75:'e3',84:'e1',93:'e2',99:'e2',106:'e5',115:'e1',119:'e1',123:'e2',133:'e13',135:'e2',140:'e16',144:'e2',146:'e16',150:'e24',155:'e1',159:'e1',171:'e3',173:'e5',175:'e3',177:'e2',185:'e1',194:'e3',198:'e2',200:'e3',204:'e3',207:'e2',209:'e31',213:'e2',215:'e2',217:'e2',220:'e5',229:'e32',240:'e5',249:'e37',257:'e13',261:'e3',264:'e1',269:'e3',271:'e2',274:'e2',282:'e39',289:'e16',293:'e40',300:'e41',306:'e25',315:'e1',317:'e2',322:'e1',331:'e16',341:'e16',349:'e1',354:'e1',361:'e7',369:'e13',377:'e2',379:'e1',386:'e2',395:'e16',405:'e50',413:'e28',422:'e5',425:'e5',428:'e2',432:'e31',435:'e1',444:'e3',446:'e1',452:'e1',464:'e2',477:'e55',484:'e2',487:'e2',493:'e5',501:'e5',507:'e2',515:'e1',521:'e5',524:'e5',537:'e3',550:'e62',559:'e63',564:'e3',568:'e64',574:'e61',578:'e1',584:'e1',589:'e3',597:'e39',602:'e39',606:'e2',607:'e16',612:'e3',617:'e3',620:'e3',623:'e5',628:'e3',631:'e1',637:'e5',642:'e3',651:'e6',654:'e2',660:'e3',663:'e6',680:'e23',683:'e3',695:'e66',701:'e66',706:'e6'}
for w,e in SUBJECT.items():a.feature(w,grammatical_subject_id=e)

# Physical identity, state and relation facts are sparse and time-specific.
for w,e,color in [(9,'e7','blue'),(89,'e17','green'),(400,'e24','green'),(693,'e66','blue'),(711,'e17','green')]:
    value=b(w,e,color);value['factuality']='asserted';a.feature(w,appearance_color=value)
for w,e,whole in [(46,'e69','e7'),(121,'e21','e7'),(128,'e22','e7'),(149,'e24','e16'),(296,'e41','e7'),(320,'e42','e25'),(324,'e43','e1'),(328,'e44','e7'),(366,'e49','e43'),(476,'e55','e2'),(496,'e56','e7'),(547,'e61','e60'),(549,'e62','e3'),(694,'e66','e7'),(723,'e69','e7')]:
    a.feature(w,part_whole_relation=dict(part_id=e,whole_id=whole,scope_id=a.words[w]['scope_id']))
for w,figure,landmark,relation in [(109,'e19','e20','well_above'),(123,'e13','e22','in'),(151,'e24','e7','facing'),(159,'e16','e25','attached_to'),(185,'e29','e30','on'),(341,'e16','e47','in'),(369,'e13','e25','inside'),(395,'e16','e47','in'),(405,'e50','e38','on'),(413,'e27','e7','across'),(467,'e18','e54','inside'),(537,'e3','e33','on'),(701,'e7','e68','across'),(718,'e16','e69','inside')]:
    a.feature(w,spatial_configuration=b(w,figure,dict(landmark=landmark,relation=relation)))
for w,e,key,value in [(108,'e19','object_shape','flat'),(258,'e13','object_temperature','warm'),(290,'e16','object_attachment','detached'),(510,'e13','object_moisture','dry'),(546,'e61','object_pressure_state','deflated'),(560,'e63','object_cleanliness','muddy'),(575,'e61','object_pressure_state','deflated'),(681,'e23','object_fill_state','empty_of_food'),(717,'e16','object_shape','bent')]:
    a.feature(w,**{key:b(w,e,value)})
a.feature(141,spatial_orientation=b(141,'e16',{'landmark':'e7','orientation':'upside_down'}))
a.feature(159,object_attachment=b(159,'e16',{'attached_to':'e25','via':'e26'}))
a.feature(27,transfer_kind=b(27,'e7','loan'),possession_owner=b(27,'e7',{'owner':'e4'}),possession_borrower=b(27,'e7',{'borrower':'e5'}),possession_holder=b(27,'e7',{'holder':'e5'}))
a.feature(33,possession_return_target=b(33,'e7',{'return_to':'e4'}))
a.feature(62,containment_direct=b(62,'e14',{'container':'e13'}))
a.feature(369,containment_direct=b(369,'e13',{'container':'e25'}),evidence_missing={'needed':'unreported_move_from_blanket_middle_to_basket'},evidence=[123,125,128,368,369,372],note='Keep the explicit new location; source never narrates who moved the jug into the basket.')
a.feature(438,attributes=[{'name':'occupancy','value':'Theo_absent'}],evidence=[246,438,440,441],note='Empty place setting is treated as unoccupied by Theo; no blanket assertion that its plate contains no food.')
a.feature(449,attributes=[{'name':'relative_cleanliness','value':'cleanest_of_available_sandwiches'}],evidence=[405,408,449,450],note='Superlative cleanliness does not guarantee fully clean or identify it with the fallen/biggest sandwich.')
a.feature(450,antecedent_candidates=['e29','e50'],evidence_resolution_status='ambiguous',evidence=[188,404,449,450],note='This description gets a provisional ID; either earlier sandwich may be the same object, but neither identity is established.')
a.feature(452,possession_reservation=b(452,'e52',{'current_holder':'e1','reserved_for':'e3','reserved_recipient_holds_now':False}))
a.feature(487,possession_reservation=b(487,'e18',{'current_holder':'e2','reserved_for':'e2'}))
a.feature(654,transfer_kind=b(654,'e18','sharing_handoff'),transfer_completion=b(654,'e18',{'completed':True,'recipient':'e3'}))
a.feature(718,containment_direct=b(718,'e16',{'container':'e7'}),evidence_missing={'needed':'retrieval_transition_from_reeds_to_blanket'},evidence=[395,398,607,610,706,713,718,723],note='Ending explicitly locates sign inside folded blanket. No retrieval, retriever, or transfer event is invented to fill the source continuity gap.')
a.feature(715,attributes=[{'name':'legibility','value':'readable'}])
a.feature(303,figurative_mapping={'target_id':'e41','source_image':'sail','kind':'simile','literal_event':False})
a.feature(249,figurative_mapping={'target_id':'e37','source_image':'creeping over the grass','kind':'personification','literal_event':False},evidence=[248,249,252],note='Apparent changing illumination, not the physical star traveling at ground level.')
a.feature(602,figurative_mapping={'target_id':'e39','source_image':'stealing','kind':'personification','literal_event':False},evidence=[282,289,331,602],note='Physical wind-driven loss; no thief, intention or ownership claim attributed to wind.')
a.feature(401,reference_metonymic_link={'literal':'e24','intended':'e16','relation':'inscription_for_flapping_sign'},evidence=[394,399,401,402],note='Letters move with their sign carrier rather than detaching as independent objects.')
a.feature(694,reference_metonymic_link={'literal':'e66','intended':'e7','relation':'pattern_for_blanket'},evidence=[691,694,695,701],note='The checks billow as a pattern carried by the blanket.')
a.feature(412,reference_metonymic_link={'literal':'e28','intended':'e27','relation':'arrangement_for_food_pieces'})

# Attitudes and their contents remain separate; later events do not rewrite them.
a.feature(51,promise_content_id='p2',promise_beneficiary_id='e4',plan_commitment_status='promised')
a.feature(33,goal_owner_id='e4',goal_content_id='p1',goal_polarity='achieve')
a.feature(76,plan_commitment_status='expected',proposition_id='p3')
a.feature(140,belief_holder_id='e2',belief_content_id='p4',belief_polarity='accepts')
a.feature(146,belief_holder_id='e1',belief_content_id='p4',belief_polarity='rejects',epistemic_disagreement_parties=['e1','e2'])
a.feature(151,utterance_content_id='p5',utterance_evidence_type='visual_orientation')
a.feature(171,knowledge_claim_holder_id='e3',knowledge_claim_content_id='p6',evidence=[167,169,170,171,172,175],note='Bea predicts Theo’s future knowledge; this does not assert that he currently knows or has reached the picnic.')
a.feature(173,affect_experiencer_id='e5',affect_kind='happy',affect_expression_channel='explicit_quoted_predicate',affect_target_id=E[69])
a.feature(175,evidence_resolution_status='candidate',evidence=[69,71,169,174,175,246,537],note='Retrospective interpretation: came most likely refers to the move to town. Literal current picnic arrival would conflict with later absence; retain interpretation uncertainty.')
a.feature(204,belief_holder_id='e3',belief_content_id='p7',evidence_quote_source_id='e3',evidence_report_depth=2)
a.feature(215,knowledge_claim_holder_id='e2',knowledge_claim_content_id='p8')
a.feature(217,attributes=[{'name':'bodily_need','value':'hungry'}])
a.feature(262,belief_holder_id='e1',belief_content_id='p9',belief_certainty='tentative')
a.feature(269,belief_holder_id='e2',belief_content_id='p10',belief_certainty='tentative',proposition_polarity='negative')
a.feature(354,modal_base={'holder':'e1','kind':'situational_ability'},proposition_id='p11')
a.feature(425,goal_owner_id='e2',goal_content_id='p12',plan_commitment_status='proposed')
a.feature(444,belief_holder_id='e1',belief_content_id='p13',belief_certainty='possible')
a.feature(458,goal_owner_id='e5',goal_content_id='p14',goal_beneficiary_ids=['e3'],plan_commitment_status='proposed')
a.feature(487,goal_owner_id='e2',goal_content_id='p15',goal_polarity='achieve',intention_publicity='communicated')
a.feature(583,scope_operator='near_miss',evidence=[578,581,583,584,587],note='Near kick, not actual jug overturn or spill.')
a.feature(597,utterance_content_id='p16',question_requested_slot='cause_of_scattered_lunch')
a.feature(599,propositional_antecedent_id='p21')
a.feature(620,affect_experiencer_id='e3',affect_kind='glad',affect_expression_channel='explicit_self_report',affect_target_id='p17')
a.feature(628,counterfactual_consequence={'content':'p18','world':'cousins_depart_for_sign'},active_assumptions=['p20'])
a.feature(651,goal_owner_id='e6',goal_content_id='p19',goal_polarity='achieve')
a.feature(642,quantity_total={'domain':'pieces_of_sandwich_e52','unit':'piece','value':3},evidence=[642,643,646],note='Three portions are explicit; equal sizes and individual amounts are not.')
a.feature(637,supporting_event_ids=[E[452],E[484],E[524]],evidence=[452,458,484,524,636,637],note='Joint preservation is distinct from Bea’s physical wrapping; this report does not attribute the wrapping action to Sam.')
a.feature(660,evidence=[654,657,659,660,661],note='Cookie is split too; no exact number or equality of cookie portions is supplied.')
a.feature(1,time_expression_id='time_eleven',temporal_uncertainty={'clock':'11:00','date':'unspecified','meridiem':'before_noon_context'})
a.feature(237,time_expression_id='time_twelve_thirty',temporal_uncertainty={'clock':'12:30','date':'same_story_day'})
a.feature(246,event_time_interval={'event':E[246],'scope_id':'s0','at':'12:30','day_anchor':'picnic_day','factuality':'negated'})
a.feature(69,event_time_interval={'event':E[69],'scope_id':'s0','relative_month':'previous','anchor':'picnic_day','factuality':'asserted'})
for w,r in enumerate(a.words):
    if r.get('event_id') or any(k in r for k in ('belief_content_id','goal_content_id','promise_content_id')):
        a.feature(w,assertion_status='attributed_claim' if r['scope_id'].startswith('q') or r['scope_id'] in ('s4','s5','s8') else 'asserted')
# This reference choice is an interpretation rather than a new physical event.
a.feature(175,assertion_status='candidate')

FEEDBACK={
 'summary':'Complete manual picnic annotation preserving loans, requests, conjectures, contested claims, counterfactuals, actual wind damage and cooperative food sharing.',
 'ambiguities':[
  {'words':[395,607,718],'issue':'Source continuity gap: sign remains in reeds, then is tucked inside folded blanket. Both explicit endpoint states are retained. Retrieval actor/action/time are unknown.'},
  {'words':[123,369],'issue':'Jug is placed in blanket middle but later wobbles inside basket. No move or handoff into basket is narrated.'},
  {'words':[175],'issue':'Happy he came most plausibly means Theo’s recent move to town, not picnic arrival; linked retrospectively as a candidate interpretation.'},
  {'words':[188,404,450],'issue':'Biggest, fallen and cleanest sandwiches may overlap, but source does not establish which are identical. Separate descriptions retained; wrapped/saved/shared sandwich keeps one ID.'},
  {'words':[438,440],'issue':'Empty place setting likely marks absent Theo; it does not prove no food on Theo’s plate, which earlier received a sandwich.'},
  {'words':[242,543],'issue':'Second distant bell is not established as Theo’s bicycle bell.'},
 ],
 'feature_gaps':[
  {'meaning':'explicit endpoint states with missing transition','resolution':'Use existing evidence_missing plus evidence note, not a new event or invented transition attribute.'},
  {'meaning':'legibility, relative cleanliness and hunger','resolution':'Sparse legacy attributes carry these supported descriptive values; no new names beyond the agreed extension registry.'},
 ],
 'prompt_feedback':[
  'Keep source-continuity gaps visible even when a plausible retrieval or jug move would make the story coherent.',
  'Distinguish relational superlative cleanest from an absolute hygiene claim and anaphorically identical sandwiches.',
  'Counterfactual missed meeting is separate from actual arrival; uncertain future nonarrival does not become a past fact.',
  'No completed blanket return or stain-free condition is narrated. The original promise remains a promise after folding.',
 ],
 'coverage_notes':'Every word has contextual POS/lemma; important referents, events, scopes, roles, states, attitude contents and grammar are manually assigned. Three sandwich portions do not license equal thirds, and cookie sharing does not specify a piece count. No narrative repairs, automatic POS guessing, paid API, or causal-prefix filtering.',
 'reviewed_all_words':True,
}
a.save(FEEDBACK)
