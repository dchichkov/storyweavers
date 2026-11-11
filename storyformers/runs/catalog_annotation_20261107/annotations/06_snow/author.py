"""Manually interpreted snow story; all word tags and semantic anchors authored."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation

a = Annotation('06_snow', prompt_version='v1')

# One contextual POS for each lossless word, in the indexed paragraph order.
TAGS = [
'n v v det n adp det n n pron v det n v det n conj v adj n adp det n n v adp n n n adp det n adp n adp det adj n det n v det n n n conj det n adp n',
'n n v adp pron conj det n v adj n n v v det n adv conj pron v adp pron',
'n v det n adj pron v pron v',
'adp det n n v v det n adp det adj n adp det n pron v v det n v conj pron v det adj n adp det n adv pron v num n adp det n conj v adp n',
'v pron adp det adj n n conj adv pron v pron v part v conj det adj n v v adv',
'n v adp det n adv pron v adp det n pron v v n pron v v pron adv adp num det n conj pron v v num n v det n v v pron adv',
'conj pron v pron pron v n n n v adv adv',
'n v adp det n det n v v adv adp adv',
'pron v',
'pron v det n num adj n adv adj conj pron v adv',
'det n n v conj n v adv adp det n n v adp det n conj v adp det adj n det adj n v adp pron n v pron v adp det n adv v adp det adj n n',
'n n v adp det adj adj n n v v adp det n conj n v part v adv adp det n det adj n n v adp det n adp n det n v adv det n v conj det n v adv adv',
'n v pron adp det n det adj n v adp det adj n n pron v det n adv v det n conj v part v det n adj pron v v',
'adp adv adp det n v det n adp n adp n n v adp det n adj adp det n adp det n det n v adv adp pron conj pron v adp det n',
'n n v v pron v pron',
'pron v adp det adj n adp det n det adj n v adv adv adp det n pron v det n adp det n',
'adv pron v det n det adj n v adp pron conj v adv adp det n',
'v det n pron v v adv pron v det n',
'adv pron v det adj n adj n v det n adp pron conj n v det n v adj conj det n v adv num n v adv adp det n n v pron conj pron v adp det n',
'pron v det n n v',
'n v det n adv adp det n pron v',
'adp n n n pron v det n v adv adp det n n v adp det n conj n v det n adp det adj n pron v det adj n adv v det n adv v n part part v det n adv',
'n n v det n conj pron v det adj n v v adp det n conj det n v adj adp det n adp pron',
'pron v v part v det n v v pron pron v',
'det n v adj n v n v',
'n n n v adp det adj n v adp det n conj det n',
'n v n adp det n pron v adv adp pron',
'n n v v pron adv pron v det n adp det n conj n v det n adp det n adv det adj n v det n v part v conj det adj n adp n conj n v adp det n',
'n n v n adp num n n v pron v adv v adp det n conj det n v pron',
'conj pron v adj part v pron v det adj n adp n adp det n conj v pron adp n adp det n adv pron num v v det v adv',
'pron v adp det n conj det n n v adj n n v v n adp det n det n pron v v v v n adp det n conj n adj n v adv adv v adv',
'v pron v n v',
'pron v v pron v pron v adp det adj n conj pron adv v part v pron',
'n v det adj n adp n n v pron v pron adp num n adp det n',
'n n v adp det adj adj n adv v num n v pron adv adp n',
'n conj n v adv adp det n adp det n adj n pron v adv adv det n v adp det adj n n v num adj n adp det n adp det n n n n v adp det adj adj n',
]

LEMMAS = {
'Nia':'Nia','Tomas':'Tomas','Tomas’s':'Tomas','Mr':'Mr','Mrs':'Mrs','Vale':'Vale','Vale’s':'Vale','Wren':'Wren','Wren’s':'Wren',
'had':'have','was':'be','were':'be','is':'be','has':'have','gets':'get','got':'get','did':'do','Did':'do','done':'do',
'could':'can','Could':'can','would':'will','wouldn’t':'will','didn’t':'do',
'I’d':'I','I’m':'I','I’ll':'I','You’ve':'you',
'softened':'soften','edges':'edge','rounded':'round','buried':'bury','benches':'bench','laid':'lay',
'caps':'cap','stood':'stand','held':'hold','groceries':'grocery','carrots':'carrot','asked':'ask','deeper':'deep',
'said':'say','tying':'tie','tugged':'tug','mittens':'mitten','promised':'promise','polishing':'polish','runners':'runner',
'spent':'spend','boasting':'boast','fastest':'fast','planted':'plant','grinned':'grin','called':'call','looked':'look',
'loved':'love','racing':'race','beaten':'beat','days':'day','insisting':'insist','slowed':'slow','glanced':'glance',
'gave':'give','going':'go','rang':'ring','children':'child','pushed':'push','sprang':'spring','shot':'shoot',
'streaming':'stream','watched':'watch','leaned':'lean','sled’s':'sled','lived':'live','drifted':'drift',
'fences':'fence','caught':'catch','jolted':'jolt','tipped':'tip','slid':'slide','hands':'hand','fingers':'finger',
'slipped':'slip','tightened':'tighten','tried':'try','came':'come','swept':'sweep','farther':'far',
'racers':'racer','kept':'keep','boots':'boot','bumped':'bump','hurrying':'hurry','rocked':'rock','pressed':'press',
'pulled':'pull','popped':'pop','lurched':'lurch','rolled':'roll','disappeared':'disappear','lost':'lose',
'tucked':'tuck','found':'find','piled':'pile','dug':'dig','used':'use','cleared':'clear','dragged':'drag',
'taking':'take','opened':'open','knocked':'knock','wrapped':'wrap','shoulders':'shoulder','sat':'sit',
'beginning':'begin','swallowed':'swallow','replied':'reply','helped':'help','eyes':'eye','moved':'move',
'resting':'rest','brushed':'brush','sleeves':'sleeve','went':'go','carried':'carry','began':'begin',
'onions':'onion','rose':'rise','poured':'pour','cups':'cup','drank':'drink','standing':'stand','glancing':'glance',
'rattled':'rattle','handed':'hand','pulling':'pull','returned':'return','turned':'turn','stacking':'stack',
'sleds':'sled','raced':'race','stamping':'stamp','longer':'long','nodded':'nod','lined':'line',
'bell’s':'bell','skimmed':'skim','drawing':'draw','lines':'line','glowed':'glow',
'lay':'lie','stuck':'stick','jammed':'jam',
}
for paragraph,tags in enumerate(TAGS):
    a.tag(paragraph,tags,LEMMAS)
for row in a.words:
    if row['pos']=='pron':
        pronouns={'i':'I','me':'I','him':'he','her':'she','us':'we','them':'they'}
        row['lemma']=pronouns.get(row['token'].casefold(),row['lemma'])

if __name__ == '__main__' and '--lexical-check' in sys.argv:
    print(f'Explicit lexical records: {len(a.tagged)}')
    raise SystemExit

ENTITIES = [
('e1','Nia','person',[23,71,72,74,77,79,122,139,145,151,156,160,183,186,206,249,278,309,315,324,379,384,388,452,483,508,511,582,626,696,750,769,770,807]),
('e2','Tomas','person',[84,90,96,112,124,132,134,159,163,170,180,194,208,210,218,232,235,243,248,251,354,364,371,373,378,382,385,403,405,408,411,413,415,420,430,434,445,447,470,479,481,485,493,514,519,584,601,605,611,662,739,748,752,755,757,764,805]),
('e3','Mr. Vale','person',[26,27,60,61,719,720,725,776,777,788,789]),
('e4','Mrs. Wren','person',[50,51,68,188,189,263,264,496,497,540,541,543,554,565,566,576,586,587,612,613,618,623,655,656,682,840,841]),
('e5','Nia and Tomas','person_group',[439,499,522,546,575,677,701,702,708,779,818,822]),
('e6','children in the first race','person_group',[226,728,729,736]),
('e7','other racers','person_group',[396]),
('e8','current snow','snow',[0,9,57,271,353,478,603,734,828]),
('e9','village square','square',[8,83,231,367,393,399,712,787,836]),
('e10','village fountain','fountain',[12,812]),
('e11','square benches','bench_group',[15]),
('e12','village roofs','roof_group',[22]),
('e13',"Mr. Vale's shop",'shop',[28,726]),
('e14','delivery basket','basket',[31,39,65,149,301,322,429,469,538,795]),
('e15',"Mrs. Wren's groceries",'grocery_group',[33,54,185,629]),
('e16','delivery loaf','loaf',[42,305,311,327,492]),
('e17','delivery carrots','carrot_group',[43,648]),
('e18','fallen carrot','carrot',[464,472,474,488]),
('e19','tea supplies','tea',[44]),
('e20','served tea','tea',[658,664]),
('e21','kindling bundle','kindling',[47,49,621]),
('e22','red delivery sled','sled',[37,141,261,288,297,337,339,390,443,450,460,530,579,762,774,781,801]),
('e23',"Tomas's blue sled",'sled',[92,103,107,117,236,417,593]),
('e24','blue sled runners','runner_group',[88,211,351]),
('e25','jammed red sled runner','runner',[289,455]),
('e26','both sleds runners','runner_group',[829]),
('e27','red and blue sleds','sled_group',[823]),
('e28',"Nia's mittens",'mitten_pair',[75]),
('e29',"Tomas's polishing rag",'rag',[95]),
('e30',"Tomas's boots",'boot_pair',[414]),
('e31',"Tomas's planted boot",'boot',[115]),
('e32',"Nia's boots",'boot_pair',[512]),
('e33',"Tomas's blue scarf",'scarf',[245,741]),
('e34','red sled rope','rope',[262,331]),
('e35','blue sled rope','rope',[409]),
('e36',"Nia's hands",'hand_pair',[314]),
('e37',"Nia's fingers",'finger_group',[317]),
('e38',"Tomas's hands",'hand_pair',[406,521]),
('e39',"Tomas's shoulder",'body_part',[448]),
('e40',"Mrs. Wren's gate",'gate',[498,597]),
('e41',"Mrs. Wren's door",'door',[544]),
('e42',"Mrs. Wren's table",'table',[563,632]),
('e43',"Mrs. Wren's stove",'stove',[624]),
('e44',"Mrs. Wren's kettle",'kettle',[558,639]),
('e45','cooking pot','pot',[654]),
('e46','three tea cups','cup_group',[661]),
('e47',"Mrs. Wren's window",'window',[670,675,842]),
('e48',"Mrs. Wren's gray shawl",'shawl',[550]),
('e49',"Mrs. Wren's shoulders",'body_part_group',[555]),
('e50','snow in the earlier race','snow',[177]),
('e51',"Mrs. Wren's fire",'fire',[190,636]),
('e52','village hill','hill',[155,839]),
('e53','old mill post','post',[129]),
('e54','main lane','lane',[242]),
('e55',"Mrs. Wren's side lane",'lane',[270,346]),
('e56','bend on racing route','bend',[255,358]),
('e57','side-lane turn','turn',[285]),
('e58','side-lane fences','fence_group',[276]),
('e59','ice ridge','ice_ridge',[293]),
('e60','snowbank','snowbank',[426]),
('e61','drift against gate latch','snowdrift',[502]),
('e62','gate latch','latch',[507]),
('e63','cleared gate gap','gap',[526]),
('e64','last piece of bread','bread_piece',[686,688,694]),
('e65','bread wrapping cloth','cloth',[691]),
('e66',"Tomas's sleeves",'clothing_part_group',[606]),
('e67','gust outside window','wind_gust',[673]),
('e68','basket rim','rim',[323]),
('e69','village bell','bell',[223,815]),
('e70',"sleds at Vale's shop",'sled_group',[723]),
('e71','cooking onions','onion_group',[650]),
('e72','afternoon light','light',[716]),
('e73','light from Wren window','light',[848]),
('e74','first village race','race',[200,365,482,600,607]),
('e75','proposed one-lap race','race',[784,799]),
('e76','two tracks in snow','track_pair',[833]),
('e77','warm smell of cooking food','smell',[646]),
('e78','figuratively personified road','road',[572]),
('e79','sky','sky',[198]),
('e80','back of blue sled','sled_part',[118]),
('e81','back of red sled','sled_part',[437]),
('e82',"Mrs. Wren's eyes",'body_part_pair',[588]),
('e83',"children's boots",'boot_group',[737]),
('e84','hiss of sled runners','sound',[349]),
]
for eid,name,kind,mentions in ENTITIES:
    a.entity(eid,name,kind,mentions)

QUOTES = [
('q1',50,60,'e3','e1'),('q2',67,72,'e3','e1'),('q3',77,81,'e1','e3'),
('q4',123,132,'e2','e1'),('q5',134,145,'e2','e1'),('q6',182,186,'e1','e2'),
('q7',188,194,'e1','e2'),('q8',199,206,'e2','e1'),('q9',206,208,'e1','e2'),
('q10',215,221,'e2','e1'),('q11',378,379,'e1','e2'),('q12',381,385,'e1','e2'),
('q13',427,430,'e2','e1'),('q14',434,438,'e2','e1'),('q15',479,483,'e1','e2'),
('q16',493,495,'e2','e1'),('q17',566,576,'e4','e5'),('q18',578,582,'e1','e4'),
('q19',584,586,'e1','e4'),('q20',598,601,'e4','e2'),('q21',607,612,'e2','e4'),
('q22',697,708,'e4','e5'),('q23',747,750,'e1','e2'),('q24',752,755,'e2','e1'),
('q25',763,770,'e2','e1'),('q26',778,788,'e1','e3'),('q27',798,805,'e3','e5'),
]
for sid,start,stop,speaker,listener in QUOTES:
    a.scope(sid,range(start,stop),kind='quotation',holder_id=speaker)
    a.scopes[sid]['addressee_ids']=[listener]
a.scope('s1',range(55,60),kind='anticipated_condition',parent='q1',holder_id='e4',description='Deeper snow is the requested delivery deadline condition, not a measured later depth.')
a.scope('s2',range(102,111),kind='reported_boast',holder_id='e2',description='Fastest-sled claim attributed to Tomas; no objective speed ranking.')
a.scope('s3',range(138,145),kind='open_question',parent='q5',holder_id='e2',description='Keeping up is the test proposed by Tomas, not an established outcome.')
a.scope('s4',range(176,182),kind='reported_excuse',holder_id='e2',description='Tomas attributed his earlier loss to snow; narrator does not independently establish that cause.')
a.scope('s5',range(474,479),kind='prevented_outcome',description='Catching the carrot prevents its disappearance under snow; no disappearance asserted.')
a.scope('s6',range(532,540),kind='prevented_outcome',holder_id='e5',description='Taking care not to tip the basket describes an avoided repeat, not a second tip.')
a.scope('s7',range(546,548),kind='anticipated_action',description='Opening before they knocked does not independently establish that a knock later occurred.')
a.scope('s8',range(571,576),kind='figurative_thought',parent='q17',holder_id='e4',description='Road swallowing visitors is a figurative worried thought, not literal ingestion.')

for key in ['appearance_color','figurative_mapping','part_whole_relation']:
    a.use_extension(key)

def F(w,**fields):
    a.feature(w,**fields)

def status_for_scope(scope):
    while scope:
        if scope.startswith('q') or scope in {'s2','s4'}:
            return 'attributed_claim'
        scope=a.scopes[scope]['parent']
    return 'asserted'

def B(w,entity,value,*,status=None,**extra):
    scope=a.words[w]['scope_id']
    return dict(entity_id=entity,scope_id=scope,assertion_status=status or status_for_scope(scope),value=value,**extra)

def E(w,label,actor=None,patients=(),kind='other',roles=None,factuality=None,**kwargs):
    scope=a.words[w]['scope_id']
    factuality=factuality or ('reported' if scope!='s0' else 'asserted')
    eid=f'ev{w+1}'
    a.event(eid,w,label,type=kind,actor=actor,patients=patients,roles=roles,factuality=factuality,**kwargs)
    F(w,assertion_status=status_for_scope(scope))
    return eid

def M(w,original,role='action',note='Later reference to the same underlying event.'):
    a.mention_event(f'ev{original+1}',w,role=role,note=note)

def P(i,text,support,scope='s0'):
    a.proposition(f'p{i}',text,support,scope_id=scope)

PROPS = [
(1,'The groceries reach Mrs. Wren before deeper snow.',[50,51,52,54,55,57,59],'q1'),
(2,'Nia goes to deliver the groceries.',[77,78,79,80,183,184,185],'q3'),
(3,'Tomas has the fastest sled in the village.',[96,101,103,106,107,110],'s2'),
(4,'Nia races Tomas to the old mill post and back.',[123,124,129,131],'q4'),
(5,'Nia red sled keeps up with Tomas blue sled.',[139,141,142,143,144],'s3'),
(6,'Snow slowed Tomas during the earlier race.',[175,177,179,180],'s4'),
(7,'Mrs. Wren fire is nearly out.',[188,189,190,191,192,193],'q7'),
(8,'The village race is over by the completion of Nia delivery.',[199,200,201,203,205],'q8'),
(9,'The red sled is jammed under ice.',[288,289,290,293,295,339,341],'s0'),
(10,'Tomas helps Nia free the red sled.',[378,381,382,383,384],'q12'),
(11,'Nia holds the basket while Tomas lifts the sled back.',[427,429,434,435,437],'q13'),
(12,'The red sled is free.',[440,443,444,455,456,457],'s0'),
(13,'Tomas does not finish the village race.',[479,480,482,607,608,610,611,752,753,754],'q24'),
(14,'The basket tips again at the gate.',[532,534,536,538,539],'s6'),
(15,'The road swallowed Nia and Tomas.',[566,570,572,574,575],'s8'),
(16,'The groceries are delivered and the stove has a flame.',[619,621,624,626,627,629,632,636,637],'s0'),
(17,'Nia and Tomas borrow the red sled for one lap.',[778,779,780,781,783,784],'q26'),
(18,'The red sled is returned before dark.',[800,801,802,803,804],'q27'),
(19,'Nia and Tomas begin racing together around the square.',[805,807,808,818,819,821,824,836],'s0'),
(20,'The earlier delivery obligation competes with an immediate race.',[78,123,135,157,182,184,199,203],'s0'),
(21,'Nia and Tomas jointly free the sled and deliver the groceries.',[438,439,440,499,523,528,619,627],'s0'),
(22,'Nia and Tomas knock at Wren door.',[540,542,544,545,546,547],'s7'),
(23,'The carrot disappears under the snow.',[474,475,478],'s5'),
(24,'The red sled budges.',[339,340,341],'s0'),
(25,'Tomas finishes the first race.',[752,753,754],'q24'),
(26,'Mrs. Wren asks further questions.',[612,613,614,615,616,617],'s0'),
(27,'Tomas scarf streams.',[739,741,742,743,744,745],'s0'),
(28,'Tomas and Nia race together.',[764,766,768,769],'q25'),
(29,'Tomas learns whether the red sled can keep up with the blue sled.',[134,135,137,138,141,142,143],'q5'),
(30,'Tomas lifts the back of the red sled.',[434,435,437],'q14'),
(31,'Nia holds the basket.',[427,429],'q13'),
(32,'Tomas helped Nia free the red sled.',[445,446,452,453,584,585],'q19'),
]
for args in PROPS:
    P(*args)

# Explicit event analysis; auxiliaries/operators are not extra physical actions.
EVENTS = [
(2,'snow softens visible edges','e8',('e9',),'state'),
(10,'snow rounds fountain','e8',('e10',),'state'),(13,'snow buries benches','e8',('e11',),'state'),
(17,'snow covers roofs','e8',('e12',),'state'),(24,'Nia stands beside shop','e1',(),'state'),
(40,'basket contains groceries',None,('e14','e15'),'state'),
(52,'Wren requests groceries','e4',('e15',),'speak'),(58,'snow grows deeper',None,('e8',),'state','hypothetical'),
(62,'Vale reports Wren request','e3',(),'speak'),(63,'Vale ties basket down','e3',('e14',),'other'),
(73,'Nia adjusts mittens','e1',('e28',),'other'),(78,'Nia promised delivery','e1',(),'speak'),
(80,'Nia goes to deliver groceries','e1',('e15',),'move','desired'),
(86,'Tomas polishes runners','e2',('e24',),'other'),(101,'Tomas boasts about sled','e2',('e23',),'speak'),
(106,'blue sled is fastest',None,('e23',),'state'),(113,'Tomas plants boot on sled','e2',('e31',),'move'),
(120,'Tomas grins at Nia','e2',(),'other'),(123,'Nia races Tomas','e1',('e2',),'move','desired'),
(133,'Tomas calls racing challenge','e2',(),'speak'),(135,'Tomas wants a speed test','e2',(),'state'),
(137,'Tomas tests red sled pace','e2',('e22',),'perceive','desired'),(143,'red sled keeps up',None,('e22',),'move','hypothetical'),
(146,'Nia looks at basket','e1',('e14',),'perceive'),(152,'Nia looks at hill','e1',('e52',),'perceive'),
(157,'Nia loves racing Tomas','e1',(),'feel'),(162,'Nia beat Tomas in an earlier race','e1',('e2',),'other'),
(175,'Tomas insists snow caused loss','e2',(),'speak'),(179,'snow slows Tomas','e50',('e2',),'move'),
(184,'Nia delivers groceries','e1',('e15',),'transfer','desired'),(187,'Nia defers race for delivery','e1',(),'speak'),
(193,'Wren fire is nearly out',None,('e51',),'state'),(195,'Tomas glances at sky','e2',(),'perceive'),
(203,'first race is over',None,('e74',),'state','hypothetical'),(207,'Nia acknowledges missed race','e1',(),'state'),
(209,'Tomas wipes runners','e2',('e24',),'other'),(219,'Tomas declares immediate departure','e2',(),'move','desired'),
(224,'village bell rings',None,('e69',),'other'),(227,'children start racing','e6',(),'move'),
(233,'Tomas jumps onto sled','e2',('e23',),'move'),(238,'Tomas races down main lane','e2',('e23',),'move'),
(246,'scarf streams behind Tomas',None,('e33',),'move'),(250,'Nia watches Tomas','e1',('e2',),'perceive'),
(252,'Tomas vanishes around bend','e2',(),'move'),(257,'Nia pulls red sled rope','e1',('e34',),'move'),
(265,'Wren lives up side lane','e4',(),'state'),(273,'snow drifts against fences','e8',(),'move'),
(281,'Nia pulls sled hard','e1',('e22',),'move'),(290,'red runner catches beneath ice',None,('e25',),'state'),
(298,'red sled jolts sideways',None,('e22',),'move'),(302,'basket tips',None,('e14',),'move'),
(306,'loaf slides halfway out',None,('e16',),'move'),(310,'Nia catches loaf','e1',('e16',),'obtain'),
(318,'Nia fingers slip on basket rim',None,('e37',),'move'),(325,'Nia restores loaf to basket','e1',('e16',),'move'),
(329,'Nia tightens sled rope','e1',('e34',),'other'),(333,'Nia tries to free sled','e1',('e22',),'other'),
(335,'Nia hauls sled free','e1',('e22',),'move','desired'),(341,'sled budges',None,('e22',),'move','negated'),
(347,'runner hiss approaches',None,('e84',),'other'),(355,'Tomas sweeps around bend','e2',('e23',),'move'),
(368,'square lies beyond Tomas',None,('e9',),'state'),(377,'Tomas leads first race','e2',('e74',),'state'),
(380,'Nia calls Tomas','e1',(),'speak'),(383,'Tomas helps Nia','e2',('e1',),'other','desired'),
(386,'Tomas looks from jammed sled to square','e2',('e22','e9'),'perceive'),
(399,'other racers near square',None,('e7',),'state'),(404,'Tomas keeps hands on rope','e2',('e38',),'state'),
(412,'Tomas plants boots','e2',('e30',),'move'),(418,'blue sled slides past Tomas',None,('e23',),'move'),
(422,'blue sled bumps snowbank',None,('e23',),'move'),(427,'Nia holds basket','e1',('e14',),'state','desired'),
(431,'Tomas gives holding instruction','e2',(),'speak'),(432,'Tomas hurries to Nia','e2',(),'move'),
(435,'Tomas lifts sled back','e2',('e22',),'move','desired'),(440,'Nia and Tomas rock red sled loose','e5',('e22',),'move'),
(446,'Tomas presses shoulder against sled','e2',('e22',),'other'),(453,'Nia pulls sled','e1',('e22',),'move'),
(456,'runner pops free',None,('e25',),'move'),(461,'sled lurches forward',None,('e22',),'move'),
(465,'carrot rolls out',None,('e18',),'move'),(471,'Tomas catches carrot','e2',('e18',),'obtain'),
(475,'carrot disappears under snow',None,('e18',),'move','hypothetical'),
(480,'Tomas loses his racing opportunity','e2',('e74',),'other'),(484,'Nia observes racing cost','e1',(),'speak'),
(486,'Tomas returns carrot to basket','e2',('e18',),'move'),(494,'Tomas acknowledges racing cost','e2',(),'state'),
(500,'Nia and Tomas find gate drift','e5',('e61',),'perceive'),(503,'drift is piled against latch',None,('e61',),'state'),
(509,'Nia digs snow with boots','e1',('e61',),'other'),(515,'Tomas uses hands to clear snow','e2',('e61',),'other'),
(523,'Nia and Tomas clear gap','e5',('e63',),'other'),(528,'Nia and Tomas drag sled through','e5',('e22',),'move'),
(536,'basket tips again',None,('e14',),'move','hypothetical'),(542,'Wren opens door','e4',('e41',),'other'),
(547,'Nia and Tomas knock','e5',('e41',),'other','hypothetical'),(552,'shawl is wrapped around shoulders',None,('e48',),'state'),
(560,'kettle is cold',None,('e44',),'state'),(570,'Wren begins thought about delayed visitors','e4',(),'state'),
(574,'road swallows visitors',None,('e5',),'other','hypothetical'),(577,'Wren greets delayed visitors','e4',(),'speak'),
(583,'Nia explains sled delay','e1',(),'speak'),(589,'Wren looks toward blue sled','e4',('e23',),'perceive'),
(594,'blue sled rests beside gate',None,('e23',),'state'),(602,'Tomas brushes snow from sleeves','e2',('e66',),'other'),
(608,'race continues without Tomas',None,('e74',),'other'),(615,'Wren asks further questions','e4',(),'speak','negated'),
(619,'Wren carries kindling to stove','e4',('e21',),'move'),(627,'Nia puts groceries on table','e1',('e15',),'transfer'),
(637,'stove flame catches',None,('e51',),'state'),(642,'kettle begins murmuring',None,('e44',),'other'),
(651,'warm food smell rises from pot',None,('e77',),'other'),(657,'Wren pours tea into cups','e4',('e20',),'transfer'),
(663,'Tomas drinks tea','e2',('e20',),'other'),(665,'Tomas stands while drinking','e2',(),'state'),
(667,'Tomas glances toward window','e2',('e47',),'perceive'),(674,'gust rattles window','e67',('e47',),'other'),
(679,'Nia and Tomas are ready to leave','e5',(),'state'),(681,'Nia and Tomas leave','e5',(),'move','desired'),
(683,'Wren wraps bread in cloth','e4',('e64',),'other'),(693,'Wren gives bread to Nia','e4',('e64',),'transfer'),
(704,'visitors have done enough pulling','e5',(),'other'),(709,'Nia and Tomas return to square','e5',(),'move'),
(717,'afternoon light turns pale',None,('e72',),'state'),(722,'Vale stacks sleds','e3',('e70',),'other'),
(733,'children stamp snow from boots','e6',(),'other'),(745,'Tomas scarf streams',None,('e33',),'move','negated'),
(749,'Tomas wins first race','e2',('e74',),'other','hypothetical'),(751,'Nia asks race outcome','e1',(),'speak'),
(754,'Tomas finishes first race','e2',('e74',),'other','negated'),(756,'Tomas states he did not finish','e2',(),'speak'),
(758,'Tomas looks at red sled','e2',('e22',),'perceive'),(766,'Tomas still wants to race Nia','e2',(),'state'),
(768,'Tomas races Nia','e2',('e1',),'move','desired'),(771,'Nia hands red sled to Vale','e1',('e22',),'transfer'),
(780,'Nia and Tomas borrow red sled','e5',('e22',),'obtain','desired'),(790,'Vale inspects empty basket','e3',('e14',),'perceive'),
(794,'basket is empty',None,('e14',),'state'),(797,'Vale permits one lap','e3',(),'other'),
(800,'borrowers return sled before dark','e5',('e22',),'transfer','desired'),
(808,'Tomas and Nia line up','e5',(),'move'),(817,'bell rings again',None,('e69',),'other'),
(819,'Tomas and Nia start new race','e5',('e27',),'move'),(824,'both sleds skim over snow',None,('e27',),'move'),
(830,'runners draw tracks in snow',None,('e26','e76'),'other'),(843,'Wren window glows',None,('e47',),'state'),
]
for item in EVENTS:
    w,label,actor,patients,kind,*factuality=item
    E(w,label,actor,patients,kind,factuality=factuality[0] if factuality else None)

# Different descriptions of these episodes are mentions, not extra events.
for w,original,note in [(69,52,'Same earlier Wren request, now specifying Nia.'),
 (581,290,'Nia reports the already narrated jam.'),(585,440,'Nia reports Tomas participation in the already narrated freeing.'),
 (731,227,'Relative clause recalls the first race rather than starting another.')]:
    M(w,original,note=note)
M(706,704,role='reference',note='Nominal pulling is the work summarized in Wren assessment, not a single new pull.')
a.events['ev705']['summarized_event_ids']=['ev282','ev454','ev529']
F([581,585],assertion_status='attributed_claim')

# Explicit local argument anchors. A shared mention may belong to several events.
ARGS = [
(2,[0],[8]),(10,[9],[12]),(13,[],[15]),(17,[],[22]),(24,[23],[]),(40,[],[39,33]),
(52,[50,51],[54]),(62,[60,61],[]),(63,[60,61],[65]),(73,[72],[75]),(78,[77],[]),(80,[79],[]),
(86,[84],[88]),(101,[96],[]),(106,[],[103,107]),(113,[112],[115]),(120,[112],[]),
(123,[],[124]),(133,[132],[]),(135,[134],[]),(137,[134],[141]),(143,[],[141]),
(146,[145],[149]),(152,[151],[155]),(157,[156],[]),(162,[160],[163]),(175,[170],[]),(179,[177],[180]),
(184,[183],[185]),(187,[186],[]),(193,[],[190]),(195,[194],[]),(203,[],[200]),(207,[206],[]),
(209,[208],[211]),(219,[218],[]),(224,[],[223]),(227,[226],[]),(233,[232],[236]),(238,[232],[236]),
(246,[],[245]),(250,[249],[251]),(252,[251],[]),(257,[249],[262]),(265,[263,264],[]),
(273,[271],[]),(281,[278],[]),(290,[],[289]),(298,[],[297]),(302,[],[301]),(306,[],[305]),
(310,[309],[311]),(318,[],[317]),(325,[324],[327]),(329,[324],[331]),(333,[324],[337]),
(335,[324],[337]),(341,[],[339]),(347,[],[349]),(355,[354],[]),(368,[],[367]),(377,[373],[365]),
(380,[379],[]),(383,[382],[384]),(386,[385],[390,393]),(399,[],[396]),(404,[403],[406]),
(412,[411],[414]),(418,[],[417]),(422,[],[417]),(427,[],[429]),(431,[430],[]),(432,[430],[]),
(435,[434],[]),(440,[439],[443]),(446,[445],[450]),(453,[452],[]),(456,[],[455]),(461,[],[460]),
(465,[],[464]),(471,[470],[472]),(475,[],[474]),(480,[479],[482]),(484,[483],[]),(486,[485],[488]),
(494,[493],[]),(500,[499],[502]),(503,[],[502]),(509,[508],[]),(515,[514],[]),(523,[522],[526]),
(528,[522],[530]),(536,[],[538]),(542,[540,541],[544]),(547,[546],[]),(552,[],[550]),(560,[],[558]),
(570,[566],[]),(574,[],[575]),(577,[576],[]),(583,[582],[]),(589,[586,587],[593]),(594,[],[593]),
(602,[601],[606]),(608,[],[607]),(615,[612,613],[]),(619,[618],[621]),(627,[626],[629]),
(637,[],[636]),(642,[],[639]),(651,[],[646]),(657,[655,656],[658]),(663,[662],[664]),(665,[662],[]),
(667,[662],[670]),(674,[673],[675]),(679,[677],[]),(681,[677],[]),(683,[682],[686]),(693,[682],[694]),
(704,[701,702],[]),(709,[708],[]),(717,[],[716]),(722,[719,720],[723]),(733,[728],[]),(745,[],[741]),
(749,[748],[]),(751,[750],[]),(754,[752],[]),(756,[755],[]),(758,[757],[762]),(766,[764],[]),
(768,[764],[769]),(771,[770],[774]),(780,[779],[781]),(790,[788,789],[795]),(794,[],[795]),
(797,[788,789],[]),(800,[],[801]),(808,[805,807],[]),(817,[],[815]),(819,[818],[823]),
(824,[],[823]),(830,[],[829,833]),(843,[],[842]),
]
for trigger,actors,patients in ARGS:
    for role,words in [('actor',actors),('patient',patients)]:
        if words:a.mention_event(f'ev{trigger+1}',words,role=role,note='Explicit local argument mention.')
# Joint actor groups have member mentions, not identity with each individual.
for trigger,word,role in [(86,95,'instrument'),(113,118,'support'),(123,129,'destination'),
 (238,242,'route'),(252,255,'waypoint'),(273,276,'landmark'),(281,270,'route'),
 (290,293,'obstacle'),(310,314,'instrument'),(318,323,'surface'),(355,358,'waypoint'),
 (404,409,'contact'),(422,426,'landmark'),(446,448,'instrument'),(465,469,'source'),
 (486,492,'landmark'),(503,507,'landmark'),(509,512,'instrument'),(515,521,'instrument'),
 (528,526,'path'),(552,555,'landmark'),(560,563,'location'),(594,597,'location'),
 (619,624,'destination'),(627,632,'destination'),(651,654,'source'),(657,661,'destination'),
 (683,691,'wrapping'),(693,696,'recipient'),(709,712,'destination'),(722,726,'location'),
 (771,776,'recipient'),(771,777,'recipient'),(780,787,'route'),(808,812,'landmark'),
 (824,828,'surface'),(830,836,'route')]:
    a.mention_event(f'ev{trigger+1}',word,role=role,note='Explicit local argument, preserving its relation.')

# Register recipients/instruments in the event record and mirror only its trigger.
for trigger,fields in {
62:{'recipient_id':'e1'},86:{'instruments':['e29']},
133:{'recipient_id':'e1'},187:{'recipient_id':'e2'},310:{'instruments':['e36']},
380:{'recipient_id':'e2'},431:{'recipient_id':'e1'},484:{'recipient_id':'e2'},
509:{'instruments':['e32']},515:{'instruments':['e38']},577:{'recipient_id':'e5'},
583:{'recipient_id':'e4'},627:{'recipient_id':'e4'},693:{'recipient_id':'e1'},
751:{'recipient_id':'e2'},756:{'recipient_id':'e1'},771:{'recipient_id':'e3'},800:{'recipient_id':'e3'},
}.items():
    a.events[f'ev{trigger+1}'].update(fields)
    F(trigger,**fields)

REPORTS={'q1':62,'q2':62,'q4':133,'q5':133,'q6':187,'q7':187,'q11':380,'q12':380,
         'q13':431,'q14':431,'q15':484,'q17':577,'q18':583,'q19':583,'q23':751,'q24':756,'q25':756}
ACTS=['report_request','report_request','report_promise','challenge','desire_statement','defer_challenge',
      'explanation','prediction','acknowledgment','departure_announcement','summons','help_request',
      'instruction','offer_help','cost_observation','acknowledgment','figurative_concern','explanation',
      'credit_help','followup_question','explanation','gift_and_appreciation','outcome_question',
      'outcome_answer','renewed_challenge','permission_request','permission_and_condition']
for n,((sid,start,stop,speaker,listener),act) in enumerate(zip(QUOTES,ACTS),1001):
    if sid in REPORTS:
        utterance=f'ev{REPORTS[sid]+1}'
    else:
        utterance=f'ev{n}'
        a.event(utterance,start,act,type='speak',actor=speaker,recipient=listener,scope='s0',primary=False,support=range(start,stop))
    a.scopes[sid]['utterance_event_id']=utterance
    F(start,utterance_id=utterance,speech_act_kind=act,addressee_ids=[listener],communication_channel='speech',quote_mode='direct_quotation')

# Basic grammatical features only follow the manually selected contextual POS.
for r in a.words:
    w,t,pos=r['word_index'],r['token'].casefold(),r['pos']
    if pos=='det' and t in {'a','an','the'}:
        F(w,determiner_kind='definite_article' if t=='the' else 'indefinite_article',definiteness='definite' if t=='the' else 'indefinite')
    if pos=='det' and t in {'her','his','its','your','their'}:
        F(w,determiner_kind='possessive',possessive_construction='possessive_determiner',definiteness='definite')
    if pos=='conj' and t in {'and','but'}:
        F(w,coordinator_type='conjunctive' if t=='and' else 'adversative')
    if pos=='conj' and t in {'before','after','while','when','whenever','then','as'}:
        F(w,subordinator_type='temporal',temporal_signal_relation={'while':'overlap','whenever':'recurring_condition'}.get(t,t))
    if pos=='adp':F(w,dependency_relation='prepositional_marker')
    if pos=='part' and t=='to':F(w,dependency_relation='infinitival_marker')
    if pos=='pron' and t in {'i','she','he','you','we','they','me','him','her','it'}:
        F(w,mention_form='personal_pronoun',grammatical_person=1 if t in {'i','me','we'} else 2 if t=='you' else 3)
        if t in {'me','him','her'}:F(w,grammatical_case='objective')
        if r.get('entity_id'):F(w,antecedent_id=r['entity_id'])
    if pos=='n' and r.get('entity_id'):
        F(w,referent_kind='group' if a.entities[r['entity_id']]['type'].endswith(('group','pair')) else 'individual')
for w in [1,10,13,17,24,40,52,58,62,69,73,78,85,97,98,104,113,120,133,135,146,152,157,161,170+1,172,178,
 187,191,195,207,209,224,227,233,238,250,257,265,272,279,290,298,302,306,310,318,325,329,333,
 347,355,368,374,380,386,397,404,412,418,422,431,440,446,453,456,461,465,471,484,486,494,500,
 509,515,523,528,542,551,559,567,573,577,580,583,585,589,602,608,615,619,627,637,640,651,657,
 663,674,678,683,693,703,704,709,717,721,730,732,742,747,751,754,756,758,766,771,790,797,808,819,824,843]:
    if a.words[w]['pos']=='v':F(w,tense='past',verb_form='finite')
for w in [58,135,184,191,207,494,766]:
    if a.words[w]['pos']=='v':F(w,tense='present',verb_form='finite')
for w in [80,123,137,143,202,252,281,335,341,383,427,435,536,570,615,642,681,749,754,768,780,800]:
    a.words[w].pop('tense',None)
    F(w,verb_form='base')
for w in [2,98,162,172,179,273,480,503,552,574,704,731]:
    a.words[w].pop('tense',None)
    F(w,verb_form='past_participle')
for w in [63,86,101,158,175,219,246,432,532,568,594,665,667,706,722,733,745,830]:
    F(w,verb_form='gerund_participle')
F(706,pos='n',lemma='pulling',nominalization_kind='gerund_nominal')
a.words[706].pop('verb_form',None)
for w,aux in [(2,1),(98,97),(162,161),(172,171),(179,178),(273,272),(480,479),(574,573),(704,703),(731,730)]:
    F(w,aspect='perfect',perfect_auxiliary_id=a.anchor(aux))
for w,aux in [(86,85),(219,218),(568,567),(722,721),(733,732),(745,742)]:
    F(w,aspect='progressive',progressive_auxiliary_id=a.anchor(aux))
for w,expansion in {79:['I','would'],218:['I','am'],340:['would','not'],434:['I','will'],479:['you','have'],614:['did','not'],753:['did','not']}.items():
    F(w,contraction_expansion=expansion)
F(547,tense='past',verb_form='finite')
for w,pid in [(340,'p24'),(534,'p14'),(614,'p26'),(743,'p27'),(753,'p25')]:
    F(w,proposition_polarity='negative',negation_marker_form='not' if w in {340,614,753} else a.words[w]['token'].casefold())
    if pid:F(w,negation_scope_id=pid)
F(340,lexical_gloss='Negated ability to budge; not negation of the jam itself.')
for w in [123,427,800]:F(w,mood='imperative',imperative_subject_status='understood_addressee')
for w,holder,kind in [(142,'e2','ability'),(340,None,'physical_inability'),(381,'e1','polite_request'),(778,'e3','permission')]:
    F(w,modal_base={'holder':holder,'kind':kind},modal_auxiliary_class='possibility_family')
a.words[142]['modal_base']['ability_bearer_id']='e22'
a.words[381]['modal_base']['requested_actor_id']='e2'
for w in [59]:F(w,adjective_degree='comparative')
F(106,adjective_degree='superlative')
F(343,adverb_degree='comparative')
for w in [4,15,19,33,43,75,88,174,211,226,276,314,317,351,396,406,414,512,521,555,588,606,648,650,661,723,728,737,823,829,833]:
    F(w,grammatical_number='plural')
for w in [23,26,27,50,51,60,61,72,84,122,145,159,188,189,194,232,249,263,264,278,309,354,378,379,445,452,470,483,485,496,497,508,514,540,541,582,584,586,587,601,612,613,626,655,656,662,696,719,720,739,750,770,776,777,788,789,805,807,840,841]:
    F(w,mention_form='proper_name',grammatical_number='singular')
for w in [27,189,261,288,497,587,739,815,841]:F(w,genitive_realization='singular_s_clitic')
for w in [439,499,522,546,575,677,701,708,779,818]:F(w,group_members=['e1','e2'],split_antecedent_ids=['e1','e2'])
for w,number in [(114,1),(173,3),(212,1),(313,2),(463,1),(660,3),(702,2),(783,1),(798,1),(831,2)]:F(w,cardinal_value=number)
F(166,quantity_fraction_lexeme=.5,measure_unit='sled_length')
F(168,quantity_comparison={'domain':'race_finish_margin','winner_id':'e1','other_id':'e2','value':.5,'unit':'sled_length'},evidence=[160,162,163,164,166,168],note='Earlier race margin only; no current distance or speed inferred.')
F(100,temporal_duration={'value':1,'unit':'week','quantification':'all_week'},time_expression_id='time_prior_week')
F(174,temporal_duration={'value':3,'unit':'day','event_id':'ev176'})
F(164,temporal_iteration_count=1)
F(402,temporal_duration={'value':None,'unit':'moment','quantification':'short_unspecified'})
F(707,temporal_deixis='current_day',time_anchor_id='time_story_day')
F(715,temporal_granularity='part_of_day',time_expression_id='time_afternoon')
F(804,temporal_deadline={'event':'ev801','by':'time_dark','status':'required'},temporal_anchor_unresolved=True)
F(816,temporal_order_cue='next_occurrence')

# Explicit syntax is independent of semantic actor selection.
SUBJECTS = {
2:'e8',10:'e8',13:'e8',17:'e8',24:'e1',40:'e14',52:'e4',58:'e8',62:'e3',69:'e4',
73:'e1',78:'e1',80:'e1',86:'e2',101:'e2',106:'e23',113:'e2',120:'e2',133:'e2',135:'e2',
143:'e22',146:'e1',152:'e1',157:'e1',162:'e1',175:'e2',179:'e50',184:'e1',187:'e1',193:'e51',
195:'e2',203:'e74',207:'e1',209:'e2',219:'e2',224:'e69',227:'e6',233:'e2',238:'e2',246:'e33',
250:'e1',252:'e2',257:'e1',265:'e4',273:'e8',281:'e1',290:'e25',298:'e22',302:'e14',306:'e16',
310:'e1',318:'e37',325:'e1',329:'e1',333:'e1',341:'e22',347:'e84',355:'e2',368:'e9',377:'e2',380:'e1',
383:'e2',386:'e2',399:'e7',404:'e2',412:'e2',418:'e23',422:'e23',431:'e2',435:'e2',440:'e5',
446:'e2',453:'e1',456:'e25',461:'e22',465:'e18',471:'e2',475:'e18',480:'e2',484:'e1',486:'e2',
494:'e2',500:'e5',509:'e1',515:'e2',523:'e5',528:'e5',542:'e4',547:'e5',552:'e48',560:'e44',
570:'e4',574:'e78',577:'e4',581:'e22',583:'e1',585:'e2',589:'e82',594:'e23',602:'e2',608:'e74',
615:'e4',619:'e4',627:'e1',637:'e51',642:'e44',651:'e77',657:'e4',663:'e2',674:'e67',679:'e5',
683:'e4',693:'e4',704:'e5',709:'e5',717:'e72',722:'e3',731:'e6',733:'e6',745:'e33',749:'e2',
751:'e1',754:'e2',756:'e2',758:'e2',766:'e2',771:'e1',780:'e5',790:'e3',794:'e14',797:'e3',
808:'e5',819:'e5',824:'e27',830:'e26',843:'e47',
}
for w,subject in SUBJECTS.items():F(w,grammatical_subject_id=subject)
F(589,reference_metonymic_link={'literal_id':'e82','related_id':'e4','relation':'eyes_realize_person_gaze'},
  evidence=[586,587,588,589,593],note='Eyes are the overt subject; Wren is the perceiver.')
F(585,event_divided_labor=B(585,'e5',{'reported_helper':'e2','shared_event_id':'ev441','helper_event_id':'ev447','other_actor':'e1'}),
  evidence=[439,440,445,446,452,453,584,585],note='Help recalls Tomas contribution to the joint freeing; its grammatical subject is Tomas, not the whole pair.')
for w in [0,13,17,295]:F(w,lexical_sense_id={0:'snow_precipitation',13:'cover_with_snow',17:'lay_covering',295:'frozen_water'}[w])
for w,gloss in {2:'visually smooth outlines by snow cover',19:'snow coverings on roofs',238:'move quickly on sled',
 252:'pass out of view',257:'apply body weight to pulling rope',290:'become physically trapped',
 377:'ahead of other racers at this point',480:'lose opportunity to complete the first race',
 552:'shawl positioned around shoulders; no wrapping agent stated',642:'kettle makes a low sound',
 704:'perform sufficient physical work',794:'delivery contents have been removed'}.items():F(w,lexical_gloss=gloss)
for w in [0,9,271,353,478,603,734,828]:F(w,ontological_type='physical_substance')
for w in [43,648,650]:F(w,ontological_type='food')
for w in [50,60,188,263,496,540,586,612,655,719,776,788,840]:F(w,proper_name_structure='title_plus_name')

# State, topology and ownership are local to the mention's time and scope.
for w,e,color in [(18,'e8','white'),(36,'e22','red'),(91,'e23','blue'),(140,'e22','red'),
 (244,'e33','blue'),(260,'e22','red'),(287,'e22','red'),(416,'e23','blue'),(442,'e22','red'),
 (549,'e48','gray'),(592,'e23','blue'),(740,'e33','blue'),(761,'e22','red'),(773,'e22','red'),(847,'e73','golden')]:
    F(w,appearance_color={**B(w,e,color),'factuality':'asserted' if a.words[w]['scope_id']=='s0' else 'reported'})
for w,part,whole in [(88,'e24','e23'),(118,'e80','e23'),(211,'e24','e23'),(262,'e34','e22'),
 (289,'e25','e22'),(314,'e36','e1'),(317,'e37','e1'),(323,'e68','e14'),(331,'e34','e22'),
 (351,'e24','e23'),(406,'e38','e2'),(409,'e35','e23'),(437,'e81','e22'),(448,'e39','e2'),
 (455,'e25','e22'),(507,'e62','e40'),(521,'e38','e2'),(555,'e49','e4'),(588,'e82','e4')]:
    F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
for w,entity,landmark,relation in [(25,'e1','e13','beside'),(34,'e14','e22','on'),(83,'e2','e9','across'),
 (116,'e31','e80','on'),(247,'e33','e2','behind'),(274,'e8','e58','against'),(291,'e25','e59','beneath'),
 (319,'e37','e68','on'),(369,'e9','e2','just_beyond'),(407,'e38','e35','on'),(449,'e39','e22','against'),
 (490,'e18','e16','beside'),(505,'e61','e62','against'),(553,'e48','e49','around'),
 (561,'e44','e42','on'),(595,'e23','e40','beside'),(630,'e15','e42','on'),(810,'e5','e10','beside')]:
    F(w,spatial_configuration=B(w,entity,{'landmark':landmark,'relation':relation}))
F(37,spatial_support=B(37,'e14',{'supported_by':'e22'}))
F(40,containment_contents=B(40,'e14',{'contents':['e16','e17','e19','e21']}))
for w,entity in [(42,'e16'),(43,'e17'),(44,'e19'),(49,'e21')]:F(w,containment_direct=B(w,entity,{'container':'e14'}))
F(63,event_state_change=B(63,'e14',{'after':'tied_down','carrier':'e22','before':None}))
F(63,verb_particle_construction='tie_down',particle_head_id=a.anchor(66))
F(66,lexical_gloss='particle in tie down: secure the basket to its carrier')
F(76,attributes=[{'name':'fit','value':'snug'}])
F(106,quantity_comparison={'entity_id':'e23','relation':'highest','dimension':'speed','domain':'village_sleds','holder_id':'e2','scope_id':'s2','assertion_status':'attributed_claim'},
  evidence=[96,101,103,106,107,110],note='Boasted ranking; no independent speed measurement.')
F(268,attributes=[{'name':'width','value':'narrow'}])
F(281,motion_effort=B(281,'e1','high'),evidence=[278,279,281,282],note='Physical effort is stated by had to pull hard.')
F(290,event_state_change=B(290,'e25',{'before':'moving','after':'jammed','obstacle':'e59'}))
F(299,motion_direction=B(299,'e22',{'interpretation':'sideways','event_id':'ev299'}))
F(306,containment_partial=B(306,'e16',{'container':'e14','inside_fraction':'halfway_out'}))
F(310,possession_holder=B(310,'e16',{'holder':'e1'}),event_attempt_outcome=B(310,'e1',{'action':'catch_loaf','outcome':'caught'}))
F(321,attributes=[{'name':'texture','value':'rough'}])
F(325,containment_direct=B(325,'e16',{'container':'e14'}))
F(333,event_attempt_outcome=B(333,'e1',{'attempt_event_id':'ev336','outcome':'failed','evidence_event_id':'ev342'}),
  evidence=[333,335,337,339,340,341],note='Only this unaided attempt fails; later joint freeing succeeds.')
F(341,motion_relative_displacement=B(341,'e22',{'displacement':'none','relative_to':'e59'}))
F(377,ordinal_rank=1,quantity_comparison={'entity_id':'e2','comparison_set':'first_race_racers','dimension':'progress','status':'currently_in_lead'},
  evidence=[354,359,362,365,373,374,377],note='Position while racing, not a final winner claim.')
F(389,attributes=[{'name':'mobility_state','value':'jammed'}],causal_preventing_condition=B(389,'e22',{'blocked':'forward_motion','condition':'runner_caught_under_ice'}))
F(395,reference_excluded_ids=['e2'])
F(412,motion_trajectory_phase=B(412,'e2','stopping'),
  evidence=[411,412,415,418,420,432],note='Tomas stops before hurrying over; his exact stopping point is unstated.')
F(422,motion_collision=B(422,'e23',{'collided_with':'e60'}))
F(423,event_manner=B(423,'e23',{'event_id':'ev423','manner':'softly'}))
for w in [440,523,528,808,819]:F(w,event_collective_participants=B(w,'e5',{'actors':['e1','e2']}))
F(440,event_divided_labor=B(440,'e5',{'press_shoulder':'e2','pull_sled':'e1'}))
F(456,event_state_change=B(456,'e25',{'before':'jammed','after':'free'}),event_success=B(456,'e5',{'affected_event_id':'ev441','cue':'sled_freed','trigger_event_id':'ev457'}))
F(465,motion_source=B(465,'e18',{'event_id':'ev466','landmark_id':'e14','role':'source'}))
F(471,possession_holder=B(471,'e18',{'holder':'e2'}),causal_blocked_effect=B(471,'e18',{'preventer':'ev472','would_be_effect':'ev476'}),
  evidence=[470,471,472,473,474,475,478],note='The actual catch prevents the proposed disappearance.')
F(486,containment_direct=B(486,'e18',{'container':'e14'}))
F(502,access_blocking_object=B(502,'e40',{'obstruction':'e61'}))
F(523,access_clearance=B(523,'e22',{'fits':True,'passage':'e63'}),evidence=[523,525,526,528,530,531],note='Subsequent passage establishes sufficient clearance for this sled, not a generic width.')
F(528,motion_boundary_crossing=B(528,'e22',{'boundary':'e40','crossed':True}),event_manner=B(528,'e5',{'event_id':'ev529','manner':'careful_to_avoid_tipping'}))
F(542,event_state_change=B(542,'e41',{'before':'closed','after':'open'}))
F(552,containment_relation_kind=B(552,'e48','wearing'),attributes=[{'name':'configuration','value':'wrapped_around_shoulders'}])
F(560,object_temperature=B(560,'e44','cold'))
F(574,figurative_mapping={'target_id':'e5','source_image':'road swallowing travelers','kind':'metaphor','literal_event':False},
  belief_holder_id='e4',belief_content_id='p15',epistemic_attitude_kind='incipient_thought',
  evidence=[566,568,570,572,574,575],note='Wren voices concern about delay through a figurative image; literal ingestion is not asserted.')
F(594,motion_stopping_location=B(594,'e23',{'stopped_at':'e40'}),evidence=[593,594,595,597],note='Endpoint beside gate is explicit; intermediate handling need not be invented.')
F(619,motion_destination=B(619,'e21',{'event_id':'ev620','landmark_id':'e43','role':'destination'}))
F(627,spatial_support=B(627,'e15',{'supported_by':'e42'}),event_completion_evidence=B(627,'e1',{'affected_event_id':'ev185','cue':'groceries_delivered','trigger_event_id':'ev628'}))
F(637,event_phase=B(637,'e51',{'affected_event_id':None,'cue':'flame_ignited','trigger_event_id':'ev638'}))
F(642,lexical_gloss='low kettle sound; nonhuman sound metaphor, not speech',
  figurative_mapping={'target_id':'e44','source_image':'quiet murmuring voice','kind':'metaphor','literal_event':False})
F(651,motion_source=B(651,'e77',{'event_id':'ev652','landmark_id':'e45','role':'source'}))
F(657,containment_direct=B(657,'e20',{'container':'e46'}))
F(665,motion_posture=B(665,'e2','standing'))
F(683,containment_relation_kind=B(683,'e64','wrapped'),containment_direct=B(683,'e64',{'container':'e65'}))
F(693,possession_holder=B(693,'e64',{'holder':'e1'}))
F(709,motion_return_destination=B(709,'e5',{'destination':'e9'}),motion_arrival_completion=B(709,'e5',{'arrived_at':'e9'}))
F(717,attributes=[{'name':'visual_change','value':'light_becoming_pale'}])
F(743,temporal_phase_cue='cessation')
F(771,possession_holder=B(771,'e22',{'holder':'e3'}))
F(793,attributes=[{'name':'arrangement','value':'tidy'}])
F(794,containment_contents=B(794,'e14',{'contents':[],'domain':'delivery_groceries','restricted_empty':True}),
  evidence=[627,629,632,793,794,795],note='Empty refers to delivery contents; no inventory of every possible object is asserted.')
F(800,possession_return_target=B(800,'e22',{'return_to':'e3','completion':'not_shown'}))
F(819,motion_collectivity=B(819,'e5',{'companions':['e1','e2'],'coordination':'together'}),
  event_phase=B(819,'e5',{'affected_event_id':None,'cue':'new_race_begins','trigger_event_id':'ev820'}))
F(824,motion_contact=B(824,'e27',{'contact':'sliding','surface':'e8'}))
F(830,event_result_entity=B(830,'e76',{'created_by':'ev831','surface':'e8'}))
F(843,attributes=[{'name':'illumination','value':'glowing'}],evidence=[842,843,846,847,848],note='Visible window glow; the exact light source inside is unstated.')

# Goals, commitments and dialogue retain content propositions and local status.
for w,holder,content,kind in [(52,'e4','p1','request'),(78,'e1','p2','promise'),(135,'e2','p29','desire'),
 (184,'e1','p1','intention'),(383,'e1','p10','request'),(435,'e2','p30','offer'),
 (766,'e2','p28','desire'),(780,'e5','p17','permission_request')]:
    F(w,goal_owner_id=holder,goal_content_id=content,goal_status='active',goal_polarity='achieve')
    if kind in {'intention','promise','offer'}:F(w,intention_holder_id=holder,intention_content_id=content)
F(78,promise_content_id='p2',promise_beneficiary_id='e4',plan_commitment_status='promised',
  obligation_debtor_id='e1',obligation_creditor_id='e4',obligation_content_id='p2',obligation_status='undertaken')
F(101,utterance_content_id='p3',epistemic_source_kind='self_boast',belief_holder_id='e2',epistemic_attitude_kind='asserted_claim')
F(175,belief_holder_id='e2',belief_content_id='p6',epistemic_attitude_kind='insistence',
  evidence=[170,172,175,177,179,180],note='Snow-caused loss is his reported explanation; cause not independently verified.')
F(179,causal_parent=B(179,'e2',{'cause':'snow','effect':'slowing','holder':'e2'}))
F(187,goal_tradeoff={'holder_id':'e1','chosen_content_id':'p1','deferred_content_id':'p4','scope_id':'s0','assertion_status':'candidate'},
  evidence=[149,155,157,182,184,187,190,193,200,203,207],note='Delivery is chosen despite an attractive race; this interprets her explicit deferral and acknowledged deadline.')
F(192,quantity_approximation_cue='nearly',lexical_gloss='fire close to going out, not already extinguished')
F(207,knowledge_claim_holder_id='e1',knowledge_claim_content_id='p8',epistemic_attitude_kind='acknowledgment')
F(383,request_action_id='ev384',communication_intended_effect='Tomas helps free sled')
F(427,request_action_id='ev428',request_acceptance_status='not_explicitly_shown')
F(435,offer_content_id='p30',plan_commitment_status='offered')
F(440,cooperation_goal_id='p12',cooperation_commitment='enacted')
F(494,knowledge_claim_holder_id='e2',knowledge_claim_content_id='p13',epistemic_attitude_kind='acknowledgment',
  evidence=[479,480,482,493,494,752,753,754],note='Acknowledges foregoing this race; later nonfinish disambiguates lost from final placement.')
F(627,goal_owner_id='e1',goal_content_id='p2',goal_status='achieved',obligation_content_id='p2',obligation_status='fulfilled',
  evidence=[78,80,619,621,627,629,632],note='Delivery promise fulfilled; no measured evidence establishes the separate deeper-snow deadline.')
F(749,question_requested_slot='whether_Tomas_won_first_race',question_answer_status='answered_by_nonfinish')
F(754,utterance_content_id='p13',proposition_polarity='negative',
  event_failure=B(754,'e2',{'affected_event_id':'ev755','cue':'noncompletion','trigger_event_id':'ev755'}))
F(765,temporal_persistence_window={'holder_id':'e2','content_id':'p28','state':'desire_continues'})
F(780,permission_recipient_id='e5',permission_grantor_id='e3',permission_content_id='p17',permission_status='requested')
F(797,permission_grantor_id='e3',permission_recipient_id='e5',permission_content_id='p17',permission_status='granted',
  evidence=[778,779,780,783,784,797,798,799,800,804],note='Nod and one-lap instruction grant the scoped loan; this does not establish Vale ownership.')
F(800,obligation_debtor_id='e5',obligation_creditor_id='e3',obligation_content_id='p18',obligation_status='requested',plan_commitment_status='instructed')
for start,pid in [(50,'p1'),(77,'p2'),(123,'p4'),(134,'p5'),(182,'p2'),(188,'p7'),(199,'p8'),
 (381,'p10'),(427,'p31'),(434,'p30'),(479,'p13'),(566,'p15'),(578,'p9'),(584,'p32'),
 (752,'p13'),(763,'p28'),(778,'p17'),(798,'p18')]:F(start,utterance_content_id=pid)
for w,response,prior in [(207,'acknowledgment','q8'),(494,'acknowledgment','q15'),(608,'answer','q20'),(754,'answer','q23')]:
    F(w,dialogue_turn_function=response,dialogue_response_to_id=a.scopes[prior]['utterance_event_id'])
F(157,affect_experiencer_id='e1',affect_kind='enjoyment',affect_target_id='racing_Tomas',affect_valence='positive',
  evidence=[156,157,158,159],note='Explicit enjoyment of racing, not a permanent personality diagnosis.')

# Interpretive causal/narrative links are candidates with transparent evidence.
F(637,causal_parent=B(637,'e51',{'cause':'kindling_brought_to_stove','effect':'flame_catches'},status='candidate'),
  evidence=[619,621,624,633,636,637],note='Context supports the kindling/fire link but does not narrate lighting mechanics.')
F(456,causal_parent=B(456,'e25',{'cause':'joint_rocking_pressing_and_pulling','effect':'runner_freed'},status='candidate'),
  evidence=[440,446,453,455,456,457],note='Resultative rocked loose plus the adjacent physical actions support the causal reading without asserting either action alone sufficient.')
F(480,goal_tradeoff={'holder_id':'e2','chosen_content_id':'p10','foregone':'first_race_completion','scope_id':'q15','assertion_status':'candidate'},
  evidence=[377,383,386,390,393,404,412,440,479,480,482,494,754],note='Helping instead of continuing costs Tomas the first race; no final rank or regret is inferred.')
F(843,narrative_closure_candidate={'content':'Warm lit window after successful delivery and the children racing together','evidence_event_ids':['ev628','ev638','ev820','ev844'],'assertion_status':'candidate'},
  narrative_theme_candidate={'content':'Helping and keeping a promise can take priority over winning while leaving room for shared play','assertion_status':'candidate'},
  evidence=[78,187,412,440,627,637,754,797,819,843,848],note='Interpretation of the closing contrast, not a narrated moral or completed second-race outcome.')

a.save({
 'summary':'Whole-story retrospective annotation of the snow delivery, interrupted race, joint freeing and new shared race. Explicit local states, quoted claims, prevented outcomes and promises remain distinct.',
 'reviewed_all_words':True,'reviewed_paragraphs':list(range(36)),
 'ambiguities':[
  {'words':[37,771,780,797],'issue':'Red sled ownership is not established; Vale receives it and grants the later loan. Initial custody does not establish a prior loan.'},
  {'words':[52,62,69],'issue':'Recipient of Wren original request is unstated; Vale reporting it does not prove he was the original addressee.'},
  {'words':[175,179],'issue':'Tomas attributes his earlier loss to snow. This remains his excuse, not narrator-established causation.'},
  {'words':[440,585],'issue':'Helped summarizes Tomas contribution to joint freeing; divided-labor binding preserves his individual subject within the shared episode.'},
  {'words':[547],'issue':'Before they knocked does not prove a knock eventually happened; the knocking remains anticipated.'},
  {'words':[44,658],'issue':'Tea supplies and served tea use separate IDs; brewing and material identity are not narrated.'},
  {'words':[42,686,688],'issue':'Gift bread may come from the earlier loaf, but no source-part identity is asserted.'},
  {'words':[475,536],'issue':'Disappearance and repeated tipping are prevented/avoided possibilities, not extra actual mishaps.'},
  {'words':[800,804,819],'issue':'Return before dark is instructed; the story ends during the new race, with no return or winner shown.'},
 ],
 'feature_gaps':[
  {'meaning':'qualitative texture, tightness and visual state','resolution':'Use lexical glosses/legacy attributes where no precise catalog dimension exists; do not misuse material hardness for roughness.'},
  {'meaning':'individual contribution summarized as joint help','resolution':'Reuse event_divided_labor plus a shared episode ID; a standard event-part convention would reduce ad hoc internal keys.'},
 ],
 'prompt_feedback':[
  'Negation operators should target positive content propositions; negating a proposition already stating nonfinish creates double negation.',
  'Same-event reference can retain a different local grammatical subject for one member contribution; distinguish shared actor group from the member being credited.',
  'Before X happened can introduce a prevented or unobserved action; inspect context rather than assign all past morphology actual factuality.',
  'Collective event actors and body-part grammatical subjects need explicit bridges; do not copy actor into grammatical subject.',
 ],
 'coverage_notes':'All849 words explicitly tagged and all36 paragraphs reread; rich sparse semantics use the full catalog as available. No causal masking, paid API, exact emotion scores, invented ownership, winner or unseen return. Spaces and punctuation are lossless synthetic records.',
})
