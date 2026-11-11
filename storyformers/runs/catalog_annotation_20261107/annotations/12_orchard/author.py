"""Explicit contextual word annotation of the orchard story, prompt v2."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation

a = Annotation('12_orchard', prompt_version='v2')
TAGS = [
'det n v adj adv adp n part v n v adp num n conj pron v adp det pron n n v adp det n det n v adj conj det n v pron n v v num n conj det n adp n n v v det adj n adp n',
'num n n v num adp n conj num pron adp pron',
'det adj n v v part v det n n det n n v v part v det n',
'conj pron v part v pron pron n v det n adv v adv conj pron v det n part v adv',
'n n pron v det n v adp adp det n adv pron v v det n n pron v det adj n adp det n n conj det n adp adj adj n adp det n v adp det n v det n adp det n adv v adv conj pron v v v pron det n n conj n',
'pron v adp det adj adj n adp det n pron v v det n adv conj pron adj pron part det n',
'n v adp det n pron v',
'n v det n conj pron v adp det adj n det adj n v adj adj n conj det pron pron v v adj pron v det n adp pron adp det adj pron conj v det n v adj adp det adj n v adp det n n',
'pron v pron pron v',
'pron v v n adv v pron',
'pron v det n conj v part v adv adv det n v n v det n adp det n part v pron',
'adv pron v pron',
'n v adv det n det n v adv conj det adj n v adv adp det n pron v det n adp det n conj v pron adv num n pron v num adj',
'v n v det pron adj',
'det adj adj n v adp det n adp det adj n pron v part v adp det n n v det n conj det n v det n',
'adj n v',
'pron v v adj n v det n',
'det n v det n conj det n v adv det adj n v adv det n adp adj adj n v adp n n',
'pron v adv',
'v n v det n v v',
'n v adj det adj n v adv adp det n adj adv part v conj pron v adp det n pron v adp pron adv adp det n adv adp det n v adp det n',
'pron v v pron adp adv pron v',
'n n v det n v det n',
'n n v adp det n conj n n',
'pron v n v adv pron det pron',
'pron v det n adv det n v adp det n v adv conj det n v adv adp n',
'pron v det adj n adp det adj n det n v adj adp num n conj conj n v pron pron v v',
'part adj n v',
'pron v pron adv pron v adp adv n v det adj n v adp det adj n adj adv adp det n part v adp v det n pron v det n adp pron conj v adv det n v adp det n',
'num pron v',
'conj conj pron v det n adp det n det adj n v det adj adj n adp det n pron v adv adj part v conj n v',
'n v v det adj n',
'pron v n v conj pron v v adp pron',
'n v adv adp det adj adj n pron adv v adp pron adj pron v adv det adj pron conj v pron adp det n',
'n v det adj pron pron v pron v pron',
'pron v det n adp det n adp det n n v det n adv adp det adj adj n n n v det n adp adj n v num adp det n n v n adp pron det n v adp adj n conj adj n conj det n v adp det n conj v adv',
'pron v adv v det adj n adp n conj pron v det n n n v det n pron v v adp det adj adj n v adv adv conj det n v v v',
'adj n pron v v adp det n det pron v v adj adp det n v adv',
'n v pron v n n adp det n conj v pron adv',
'det n v v adp num n n v adp det adj adj n pron v pron pron v v n adp det n',
'n v det n adp pron adp det adj n adp pron det n adj n v adp det adj n v adp det adj n',
]
LEMMAS = {
'Tessa':'Tessa','Jun':'Jun','Jun’s':'Jun','Willa':'Willa','Willa’s':'Willa','Mrs':'Mrs','Bell':'Bell',
'was':'be','wasn’t':'be','were':'be','is':'be','am':'be','being':'be','been':'be','had':'have','has':'have',
'did':'do','didn’t':'do','won’t':'will','could':'can','would':'will','might':'may','It’s':'it','one’s':'one','you’re':'you','there’s':'there','We’ll':'we',
'calling':'call','stood':'stand','trees':'tree','leaned':'lean','leaves':'leaf','flashing':'flash','turned':'turn','brought':'bring',
'oatcakes':'oatcake','pears':'pear','promised':'promise','said':'say','took':'take','owned':'own','listened':'listen','picking':'picking',
'lifted':'lift','fingers':'finger','tipped':'tip','climbing':'climbing','shaking':'shaking','yanking':'yanking','pointed':'point',
'finished':'finish','glanced':'glance','walked':'walk','nearest':'near','branches':'branch','held':'hold','fitted':'fit','ones':'one',
'twisted':'twist','came':'come','settling':'settle','chose':'choose','tried':'try','wobbled':'wobble','reminded':'remind',
'rolled':'roll','carried':'carry','needed':'need','hung':'hang','seemed':'seem','raised':'raise','reached':'reach','caught':'catch',
'bent':'bend','buds':'bud','trembled':'tremble','harder':'hard','bending':'bend','climbed':'climb','looked':'look','quivering':'quiver',
'tightened':'tighten','lowered':'lower','remained':'remain','swaying':'sway','searched':'search','lower':'low','left':'leave',
'found':'find','tucked':'tuck','pulling':'pull','slid':'slide','dropped':'drop','frowned':'frown','bruised':'bruise','shone':'shine',
'picked':'pick','best':'good','gets':'get','decided':'decide','folding':'folding','broke':'break','pieces':'piece','setting':'set',
'drizzled':'drizzle','smelled':'smell','wandered':'wander','moving':'move','ate':'eat','saving':'save','neatest':'neat','returned':'return',
'checked':'check','torn':'tear','gathering':'gathering','looking':'look','smiled':'smile','wrapped':'wrap','waiting':'wait',
'dolls':'doll','seated':'seat','cried':'cry','making':'make','placed':'place','orchard’s':'orchard','balanced':'balance',
}
for paragraph,tags in enumerate(TAGS):a.tag(paragraph,tags,LEMMAS)
a.words[294]['pos']='v'  # let go: bare verb in an idiomatic release predicate
for row in a.words:
    if row['pos']=='pron':row['lemma']={'i':'I','me':'I','him':'he','her':'she','us':'we','them':'they'}.get(row['token'].casefold(),row['lemma'])
if '--lexical-check' in sys.argv:
    print(f'Explicit POS and lemma: {len(a.tagged)} words')
    raise SystemExit

def F(words,**fields):a.feature(words,**fields)
def status(scope):
    while scope:
        if a.scopes[scope]['kind'] in {'quotation','reported_claim'}:return 'attributed_claim'
        scope=a.scopes[scope]['parent']
    return 'asserted'
def B(w,entity,value,*,claim=None):
    scope=a.words[w]['scope_id']
    return {'entity_id':entity,'scope_id':scope,'assertion_status':claim or status(scope),'value':value}

ENTITIES = [
('e1','Tessa','person',[6,15,45,85,90,91,93,197,222,247,250,252,272,283,357,396,464,466,510,604,658,664,681]),
('e2','Jun','person',[9,35,55,65,77,94,190,195,255,258,259,285,286,322,346,359,363,390,392,402,418,423,439,445,455,518,528,549,565,594,612,626,636,643,669,759,761,772,786,796,807]),
('e3','Willa','person',[59,67,462,596,602,638,713,763,773,789]),
('e4','Mrs. Bell','person',[106,107,108,121,124,167,447,448,719,720,743]),
('e5','Tessa and Jun','person_group',[64,118,177,184,202,304,317,472,492,520,569,607,624,645,648,650,700,705,715,724]),
('e6','orchard','orchard',[1,111,687,809]),('e7','pear trees','tree_group',[20,21]),
('e8','orchard grass','grass',[25,654,691]),('e9','orchard leaves','leaf_group',[27,34]),('e10','breeze','wind',[32]),
('e11','two oatcakes','oatcake_pair',[39]),('e12','cheese wedge','cheese',[42,44,701]),
('e13','honey jar','jar',[50]),('e14','honey','honey',[52,683]),
('e15','three pears intended for the picnic','intended_pear_group',[54,89,83]),
('e16','Willa puppet picnic','picnic',[73,74]),('e17','generic available tool','tool_kind',[102]),
('e18','orchard shed','shed',[116]),('e19','picking basket','picking_basket',[123,181,270,281,307,313,349,412,475,542,572,718]),
('e20','picking basket handle','handle',[128,200,278,366,460]),('e21','basket cloth pouch','pouch',[132,246,303,563]),
('e22','picking ring','ring',[135,149,225,352,368,552]),('e23','soft-tipped picker fingers','prong_group',[139]),
('e24','generic pear in picking instructions','pear_variable',[152,157,161]),
('e25','orchard ground','ground',[146]),('e26','empty wooden crate','crate',[173,186,194,310,422,430,444,451,575,657]),
('e27','orchard gate','gate',[176,805]),('e28','first selected tree','tree',[207,208]),
('e29','first-tree low branches','branch_group',[210]),('e30','green pears on first tree','pear_group',[214]),
('e31','golden pears on first tree','pear_group',[218,231]),('e32','first picked pear','pear',[227,235]),
('e33','second picked pear','pear',[262,298]),('e34','Tessa steadying hand','body_part',[275]),
('e35','second pear stem','stem',[292]),('e36','collected pears','pear_group',[316,748]),
('e37','high golden pear left on tree','pear',[325,330,339,355,371,407,426,442,478,619,620,811]),
('e38','high pear branch','branch',[338,379,399,438,487,821]),('e39','high pear stem','stem',[374,482]),
('e40','green buds near high pear','bud_group',[383,387,434,731]),('e41','leaves around high pear','leaf_group',[345]),
('e42','Jun hand','body_part',[391,637]),('e43','Jun fingers','body_part_group',[456]),
('e44','next searched tree','tree',[500]),('e45','next-tree lower branches','branch_group',[496]),
('e46','partly golden pear that will not budge','pear',[502,512,513,522,524]),
('e47','third picked bruised pear','pear',[532,554,559,578,585,587,601,631,634,647,672,750]),
('e48','broad leaf hiding third pear','leaf',[537]),('e49','third pear branch','branch',[548]),
('e50','third pear bruise','bruise',[583,611,661,756]),('e51','picnic napkin','napkin',[651,767]),
('e52','Tessa folding picnic knife','knife',[668]),('e53','pieces of third pear','pear_piece_group',[675]),
('e54','passing bee','bee',[697]),('e55','pear selected for Willa','pear',[463,642,711,764,770,788,799]),
('e56','two rag dolls','doll_pair',[779,795,801]),('e57','tiny wooden picnic table','table',[785]),
('e58','Jun and Willa home','home',[771]),('e59','late light','light',[816]),
('e60','branches checked after picking','branch_group',[723]),('e61','leaves checked for damage','leaf_group',[737]),
('e62','pop of first pear detaching','sound',[241]),('e63','Jun end of orchard','place',[13]),
('e64','Tessa end of orchard','place',[19]),('e65','third pear side','part',[586]),
('e66','each oatcake in the pair','oatcake_variable',[680]),
('e67','two pear pieces per oatcake','distributed_piece_pair',[677]),
]
for args in ENTITIES:a.entity(*args)
a.entities['e5']['member_ids']=['e1','e2']
a.entities['e55']['identity_candidates']=['e32','e33']
a.entities['e67']['subset_of']='e53'
a.entities['e67']['distribution_domain']='e66'
F(463,reference_specificity='intended_unspecified',evidence=[461,462,463,638,642,711],note='Willa recipient role does not identify the high pear or determine which earlier-picked pear becomes her gift.')
F([642,711,764,770,788,799],antecedent_candidates=['e32','e33'],evidence=[315,316,532,560,578,638,642,646,659,670,706,708,711],note='Willa receives the neatest remaining collected pear; first versus second picked identity is not resolved.')

QUOTES=[
('q1',53,55,'e2','e1'),('q2',57,65,'e2','e1'),('q3',84,91,'e1','e2'),('q4',105,106,'e1','e2'),
('q5',117,124,'e4','e5'),('q6',143,167,'e4','e5'),('q7',177,190,'e4','e5'),('q8',195,197,'e2','e4'),
('q9',247,250,'e1','e2'),('q10',252,254,'e2','e1'),('q11',256,259,'e2','e1'),('q12',282,283,'e1','e2'),
('q13',321,322,'e2','e1'),('q14',324,327,'e2','e1'),('q15',356,357,'e1','e2'),('q16',359,363,'e2','e1'),
('q17',395,396,'e1','e2'),('q18',398,402,'e1','e2'),('q19',439,445,'e2','e1'),('q20',447,455,'e1','e2'),
('q21',461,464,'e2','e1'),('q22',464,466,'e1','e2'),('q23',468,472,'e1','e2'),('q24',516,518,'e2','e1'),
('q25',564,565,'e2','e1'),('q26',596,602,'e2','e1'),('q27',602,604,'e1','e2'),('q28',606,612,'e1','e2'),
('q29',638,643,'e2','e1'),('q30',645,648,'e2','e1'),('q31',741,743,'e4','e5'),('q32',749,759,'e4','e5'),
('q33',786,789,'e3','e2'),
]
for sid,start,stop,speaker,listener in QUOTES:
    a.scope(sid,range(start,stop),kind='quotation',holder_id=speaker)
    a.scopes[sid]['addressee_ids']=[listener]
    F(range(start,stop),quote_mode='direct_quotation')
for sid,start,stop,kind,parent,holder,description in [
 ('s1',93,105,'habitual','s0',None,'Tessa cousin usually takes over tools; recurring background, not a new present takeover.'),
 ('s2',156,160,'conditional','q6','e4','Generic conditional resistance; not every pear is asserted stuck.'),
 ('s3',413,423,'hypothetical','s0',None,'Touching by climbing is a possible route, not completed climbing.'),
 ('s4',450,455,'reported_claim','q20','e4','Tessa recalls Bell earlier crate-use rule; not a new Bell utterance.'),
 ('s5',538,549,'capacity','s0',None,'Third pear is reachable without pulling branch; no such branch-pulling occurrence asserted.'),
 ('s6',70,77,'promised_content','s0','e3','Willa planned puppet picnic.'),
 ('s7',80,84,'promised_content','s0','e2','Jun planned fruit delivery.'),
]:a.scope(sid,range(start,stop),kind=kind,parent=parent,holder_id=holder,description=description)
for key in ['appearance_color','part_whole_relation','figurative_mapping']:a.use_extension(key)

PROPS=[
 (1,'Three pears are gathered: one for Willa and one each for Tessa and Jun.',[53,54,57,59,61,62,64],'q1'),
 (2,'Willa holds a puppet picnic that evening.',[67,69,71,74,76],'s6'),
 (3,'Jun brings fruit for Willa picnic.',[77,79,81,83],'s7'),
 (4,'Tessa personally picks pears carefully.',[85,86,88,89,90,105],'q3'),
 (5,'Tessa and Jun borrow the picking basket.',[118,119,120,123],'q5'),
 (6,'Pickers stand on the ground, turn pears gently, and leave resistant fruit.',[143,146,147,149,154,155,156,159,160,161],'q6'),
 (7,'The crate is used as a step.',[186,187,189,451,452,454],'q7'),
 (8,'Tessa picks the first pear.',[222,223,233,235,236,247,248],'s0'),
 (9,'Jun picks another pear.',[256,257,258,259,260,262],'q11'),
 (10,'The high golden pear is perfect.',[324,325,326],'q14'),
 (11,'The high branch bends.',[379,380,399,400,401],'s0'),
 (12,'Jun climbs onto the crate.',[418,419,422],'s3'),
 (13,'Jun reaches the high pear from the crate.',[439,440,441,442,444],'q19'),
 (14,'Jun stops applying force to the high pear.',[393,395,402,403,404],'q17'),
 (15,'Another suitable pear is available.',[468,469,470,471],'q23'),
 (16,'The partly golden pear is ready for picking.',[502,504,511,515,516,517],'q24'),
 (17,'The partly golden pear budges.',[513,514,515],'s0'),
 (18,'Willa wants the bruised pear.',[596,597,598,601],'q26'),
 (19,'The bruised area is cut away.',[607,609,610,611],'q28'),
 (20,'Willa receives the best remaining pear.',[638,639,641,642,711,713],'q29'),
 (21,'Tessa and Jun share the bruised pear.',[645,646,647],'q30'),
 (22,'The third pear is suitable to eat after bruise removal.',[749,750,752,753,756,757],'q32'),
 (23,'Leaves on the checked branches were torn.',[723,736,737,738,739,740],'s0'),
 (24,'The high pear remains on its unbent branch.',[811,812,817,820,821],'s0'),
 (25,'Jun brought a pear to Willa.',[786,787,788],'q33'),
 (26,'Pickers climb, shake branches or yank fruit.',[162,163,164,166],'q6'),
 (27,'The picking basket is set on the crate after use.',[177,179,181,182,183,185],'q7'),
 (28,'The generic pear comes free.',[157,158,159],'s2'),
 (29,'Tessa and Jun do not use the crate as a step.',[186,187,189,447,449,452,454],'q20'),
 (30,'The half-golden pear is not ready for picking.',[516,517],'q24'),
]
for i,text,words,scope in PROPS:a.proposition(f'p{i}',text,words,scope_id=scope)

def E(w,label,actor=None,patients=(),kind='other',factuality=None):
    scope=a.words[w]['scope_id']
    a.event(f'ev{w+1}',w,label,actor=actor,patients=patients,type=kind,
            factuality=factuality or ('reported' if status(scope)=='attributed_claim' else 'asserted'))
    F(w,assertion_status=status(scope))

EVENTS=[
(3,'orchard is small',None,['e6'],'state'),(8,'Tessa hears Jun','e1',['e2'],'perceive','hypothetical'),
(10,'Jun calls from one end','e2',[],'speak'),(16,'Tessa stands at other end','e1',[],'state'),
(22,'pear trees lean over grass',None,['e7'],'state'),(28,'leaves flash silver',None,['e9'],'state'),
(33,'breeze turns leaves','e10',['e9'],'move'),(37,'Jun brings oatcakes and cheese','e2',['e11','e12'],'move'),
(47,'Tessa brings honey jar','e1',['e13'],'move'),(56,'Jun states pear allocation','e2',[],'speak'),
(69,'Willa promises puppet picnic','e3',[],'speak'),(71,'Willa holds puppet picnic','e3',['e16'],'other','desired'),
(79,'Jun promises fruit','e2',[],'speak'),(81,'Jun brings fruit','e2',['e15'],'move','desired'),
(86,'Tessa wants to do the picking','e1',[],'state'),(88,'Tessa picks pears','e1',['e15'],'other','desired'),
(92,'Tessa asserts wish to pick','e1',[],'speak'),(96,'Jun habitually takes over tool use','e2',[],'other'),
(104,'someone uses a tool',None,['e17'],'other','hypothetical'),(109,'Bell owns orchard','e4',['e6'],'state'),
(112,'Bell listens to children','e4',['e5'],'perceive'),(120,'children borrow picker','e5',['e19'],'obtain','desired'),
(125,'Bell lifts picker handle','e4',['e20'],'move'),(143,'pickers stand on ground','e5',[],'state','desired'),
(147,'pickers fit ring around pear','e5',['e22','e24'],'other','desired'),(154,'pickers turn gently','e5',['e24'],'other','desired'),
(159,'pear comes free',None,['e24'],'move','negated'),(160,'pickers leave resistant pear','e5',['e24'],'other','desired'),
(163,'pickers climb','e5',[],'move','hypothetical'),(164,'pickers shake branches','e5',[],'other','hypothetical'),
(166,'pickers yank fruit','e5',[],'other','hypothetical'),(168,'Bell indicates crate','e4',['e26'],'other'),
(179,'pickers set basket on crate','e5',['e19'],'move','desired'),(185,'picking is finished','e5',[],'state','hypothetical'),
(189,'crate serves as step',None,['e26'],'state','negated'),(191,'Jun glances at crate','e2',['e26'],'perceive'),
(196,'Jun acknowledges crate rule','e2',[],'state'),(198,'Tessa takes picker handle','e1',['e20'],'obtain'),
(203,'children walk to first tree','e5',[],'move'),(211,'low branches hold pears',None,['e30','e31'],'state'),
(220,'some pears have turned golden',None,['e31'],'state'),(223,'Tessa fits ring around first pear','e1',['e22','e32'],'other'),
(233,'Tessa picks first pear by twisting','e1',['e32'],'other'),(236,'first pear comes free',None,['e32'],'move'),
(242,'first pear settles in pouch',None,['e32'],'move'),(251,'Tessa announces success','e1',[],'speak'),
(254,'Jun acknowledges Tessa success','e2',[],'speak'),(257,'Tessa permits Jun a picking turn','e1',[],'other','desired'),
(260,'Jun chooses second pear','e2',['e33'],'other'),(264,'Jun attempts second-pear twist','e2',['e33'],'other'),
(266,'Jun twists second pear','e2',['e33'],'other','desired'),(271,'picker wobbles',None,['e19'],'move'),
(273,'Tessa puts hand on handle','e1',['e34'],'move'),(280,'Tessa steadies picker','e1',['e19'],'other','desired'),
(284,'Tessa reminds Jun to slow down','e1',[],'speak'),(287,'Jun retries second-pear twist','e2',['e33'],'other'),
(293,'second pear stem releases fruit',None,['e35','e33'],'other'),(299,'second pear rolls into pouch',None,['e33'],'move'),
(305,'children carry picker to crate','e5',['e19'],'move'),(312,'children set picker down','e5',['e19'],'move'),
(318,'children need one more pear','e5',[],'state'),(321,'Tessa looks at high pear','e1',['e37'],'perceive','desired'),
(323,'Jun points out high pear','e2',[],'speak'),(326,'high pear is perfect',None,['e37'],'state'),
(331,'high pear hangs near branch end',None,['e37'],'state'),(342,'high pear appears to glow',None,['e37'],'state'),
(347,'Jun raises picker','e2',['e19'],'move'),(353,'ring reaches high pear',None,['e22'],'move'),
(358,'Tessa urges gentleness','e1',[],'speak'),(362,'Jun is being gentle','e2',[],'state'),
(364,'Jun turns picker handle','e2',['e20'],'other'),(369,'ring catches high pear',None,['e22','e37'],'other'),
(375,'high pear stem holds fast',None,['e39'],'state'),(380,'high branch bends downward',None,['e38'],'move'),
(388,'high buds tremble',None,['e40'],'move'),(393,'Jun turns harder','e2',['e20'],'other'),
(395,'Jun stops forcing picker','e2',[],'other','desired'),(397,'Tessa asks Jun to stop','e1',[],'speak'),
(403,'Jun holds still','e2',[],'state'),(408,'high pear hangs above basket',None,['e37'],'state'),
(416,'Jun touches high pear','e2',['e37'],'other','hypothetical'),(419,'Jun climbs crate','e2',['e26'],'move','hypothetical'),
(424,'Jun looks at pear crate and buds','e2',['e37','e26','e40'],'perceive'),
(441,'Jun reaches high pear from crate','e2',['e37'],'other','hypothetical'),(446,'Jun describes possible reach','e2',[],'speak'),
(457,'Jun fingers tighten around handle',None,['e43'],'other'),(465,'Tessa acknowledges Willa fruit goal','e1',[],'state'),
(467,'Tessa suggests alternative pear','e1',[],'speak'),(469,'another suitable pear exists',None,[],'state','hypothetical'),
(473,'children lower picker','e5',['e19'],'move'),(479,'high pear remains attached',None,['e37'],'state'),
(483,'high pear sways lightly',None,['e37'],'move'),(488,'high branch returns to position',None,['e38'],'move'),
(493,'children search next-tree branches','e5',['e45'],'perceive'),(504,'another pear is partly golden',None,['e46'],'state'),
(511,'Tessa turns partly golden pear','e1',['e46'],'other'),(515,'partly golden pear budges',None,['e46'],'move','negated'),
(517,'partly golden pear is ready',None,['e46'],'state','negated'),(519,'Jun diagnoses pear readiness','e2',[],'speak'),
(521,'children leave partly golden pear','e5',['e46'],'other'),(529,'Jun finds third ripe pear','e2',['e47'],'perceive'),
(533,'third pear is tucked behind leaf',None,['e47'],'state'),(544,'picker reaches third pear',None,['e19'],'move','hypothetical'),
(546,'picker pulls third branch',None,['e49'],'other','hypothetical'),(550,'Jun slides ring around third pear','e2',['e22','e47'],'other'),
(556,'Jun turns third pear carefully','e2',['e47'],'other'),(560,'third pear drops into pouch',None,['e47'],'move'),
(566,'Jun announces three pears','e2',[],'speak'),(570,'children carry picker to crate again','e5',['e19'],'move'),
(579,'third pear has bruise',None,['e47','e50'],'state'),(590,'third pear is edible',None,['e47'],'state'),
(595,'Jun frowns','e2',[],'other'),(598,'Willa wants bruised pear','e3',['e47'],'state','hypothetical'),
(603,'Willa might want bruised pear','e3',['e47'],'state','hypothetical'),(605,'Tessa offers alternative assessment','e1',[],'speak'),
(609,'cousins cut around bruise','e5',['e50'],'other','hypothetical'),(613,'Jun looks toward high pear','e2',['e37'],'perceive'),
(622,'high pear shines above cousins',None,['e37'],'state'),(627,'Jun picks up bruised pear','e2',['e47'],'obtain'),
(633,'Jun turns bruised pear in palm','e2',['e47'],'other'),(639,'Willa receives best pear','e3',['e55'],'obtain','desired'),
(644,'Jun decides fruit allocation','e2',[],'state'),(646,'cousins share bruised pear','e5',['e47'],'other','desired'),
(649,'cousins spread napkin on grass','e5',['e51'],'other'),(659,'Tessa cuts bruise away','e1',['e50'],'other'),
(670,'Jun breaks third pear into pieces','e2',['e47'],'other'),(676,'Jun puts two pieces on each oatcake','e2',['e67'],'move'),
(682,'Tessa drizzles honey over prepared food','e1',['e14'],'other'),(688,'orchard smells of warm grass and sweet fruit',None,['e6'],'state'),
(698,'bee moves past cheese','e54',[],'move'),(703,'bee moves on','e54',[],'move'),
(706,'cousins eat slowly','e5',[],'other'),(708,'cousins reserve neatest pear for Willa','e5',['e55'],'other'),
(716,'cousins return picker','e5',['e19'],'transfer'),(721,'Bell checks picked-from branches','e4',['e60'],'perceive'),
(726,'cousins picked from checked branches','e5',[],'other'),(734,'green buds remain on branch',None,['e40'],'state'),
(740,'leaves on checked branches are torn',None,['e61'],'state','negated'),(742,'picking is good in Bell assessment',None,[],'state'),
(744,'Bell praises gathering','e4',[],'speak'),(745,'Bell looks at pears','e4',['e36'],'perceive'),
(752,'trimmed pear tastes fine',None,['e47'],'state','hypothetical'),(760,'Jun smiles','e2',[],'other'),
(762,'Jun wraps Willa pear','e2',['e55'],'other'),(769,'Jun carries Willa pear home','e2',['e55'],'move'),
(775,'Willa waits with dolls','e3',[],'state'),(780,'rag dolls are seated around table',None,['e56'],'state'),
(790,'Willa welcomes delivery','e3',[],'speak'),(791,'Willa makes room beside dolls','e3',[],'other'),
(797,'Jun places pear between dolls','e2',['e55'],'move'),(812,'high pear shines in late light',None,['e37'],'state'),
(817,'high pear rests on unbent branch',None,['e37'],'state'),
]
for args in EVENTS:E(*args)

def M(w,original,role='action',note='Same underlying event, later mention.'):
    a.mention_event(f'ev{original+1}',w,role=role,note=note)
    if role=='action':F(w,assertion_status=status(a.words[w]['scope_id']))
M(248,233,note='Did it recalls first picking success, not an extra twist.')
M(253,233,note='Jun acknowledges same first picking.')
M(401,380,note='Tessa describes the already bending branch.')
M(454,189,note='Same crate-step content recalled as Bell rule.')
M(757,659,note='Bell refers to the already completed bruise trimming.')
M(787,769,note='Brought one refers to completed carrying-home event.')
M(294,293,note='Go is the bare-verb component of the same let-go release predicate.')
M(435,388,note='Quivering continues the same visible trembling of the buds.')
a.events['ev727']['summarized_event_ids']=['ev234','ev288','ev557']

# Surface argument anchors, authored separately from the event participants.
ARGS=[
(3,[],[1]),(8,[6],[9]),(10,[9],[]),(16,[15],[]),(22,[],[21]),(28,[],[27]),(33,[32],[34]),
(37,[35],[39,44]),(47,[45],[50]),(56,[55],[]),(69,[67],[]),(71,[67],[74]),(79,[77],[]),(81,[77],[83]),
(86,[85],[]),(88,[85],[89]),(92,[91],[]),(96,[94],[]),(104,[],[102]),(109,[108],[111]),(112,[106,107],[]),
(120,[118],[123]),(125,[124],[128]),(147,[],[149,152]),(159,[],[157]),(160,[],[161]),(168,[167],[173]),
(179,[177],[181]),(185,[184],[]),(189,[],[186]),(191,[190],[194]),(196,[195],[]),(198,[197],[200]),
(203,[202],[]),(211,[],[214,218]),(220,[],[218]),(223,[222],[225,227]),(233,[222],[235]),(236,[],[235]),(242,[],[235]),
(251,[250],[]),(254,[255],[]),(260,[259],[262]),(264,[259],[262]),(266,[259],[262]),(271,[],[270]),
(273,[272],[275]),(280,[272],[281]),(284,[283],[]),(287,[286],[298]),(293,[],[292,298]),(299,[],[298]),
(305,[304],[307]),(312,[304],[313]),(318,[317],[]),(321,[],[325]),(323,[322],[]),(326,[],[325]),
(331,[],[330]),(342,[],[339]),(347,[346],[349]),(353,[],[352]),(358,[357],[]),(362,[359],[]),
(364,[363],[366]),(369,[],[368,371]),(375,[],[374]),(380,[],[379]),(388,[],[387]),(393,[392],[]),
(397,[396],[]),(403,[402],[]),(408,[],[407]),(416,[418],[407]),(419,[418],[422]),(424,[423],[426,430,434]),
(441,[439],[442]),(446,[445],[]),(457,[],[456]),(465,[464],[]),(467,[466],[]),(473,[472],[475]),
(479,[],[478]),(483,[],[478]),(488,[],[487]),(493,[492],[496]),(504,[],[502]),(511,[510],[512]),
(515,[],[513]),(517,[],[]),(519,[518],[]),(521,[520],[522]),(529,[528],[532]),(533,[],[532]),
(544,[],[542]),(546,[],[548]),(550,[549],[552,554]),(556,[549],[559]),(560,[],[559]),(566,[565],[]),
(570,[569],[572]),(579,[],[578,583]),(590,[],[587]),(595,[594],[]),(598,[596],[601]),(603,[602],[]),
(605,[604],[]),(609,[607],[611]),(613,[612],[619]),(622,[],[620]),(627,[626],[631]),(633,[626],[634]),
(639,[638],[642]),(644,[643],[]),(646,[645],[647]),(649,[648],[651]),(659,[658],[661]),
(670,[669],[672]),(676,[669],[677]),(682,[681],[683]),(688,[],[687]),(698,[697],[]),(703,[697],[]),
(706,[705],[]),(708,[705],[711]),(716,[715],[718]),(721,[719,720],[723]),(726,[724],[]),(734,[],[731]),
(740,[],[737]),(744,[743],[]),(745,[743],[748]),(752,[],[750]),(760,[759],[]),(762,[761],[764]),
(769,[761],[770]),(775,[773],[]),(780,[],[779]),(790,[789],[]),(791,[789],[]),(797,[796],[799]),
(812,[],[811]),(817,[],[811]),
]
for trigger,actors,patients in ARGS:
    for role,words in [('actor',actors),('patient',patients)]:
        if words:a.mention_event(f'ev{trigger+1}',words,role=role,note='Explicit local argument anchor.')
for trigger,w,role in [(10,13,'source'),(16,19,'location'),(22,25,'landmark'),(112,116,'location'),
 (143,146,'location'),(168,176,'landmark'),(179,182,'destination'),(203,207,'destination'),
 (223,225,'instrument'),(242,246,'destination'),(273,278,'landmark'),(299,303,'destination'),
 (305,310,'destination'),(312,310,'support'),(331,338,'landmark'),(342,345,'landmark'),
 (353,355,'destination'),(388,391,'landmark'),(408,412,'landmark'),(441,444,'source'),
 (457,460,'landmark'),(479,482,'attachment'),(493,500,'location'),(533,537,'landmark'),
 (560,563,'destination'),(570,575,'destination'),(579,586,'location'),(622,624,'landmark'),
 (633,637,'location'),(649,654,'location'),(659,668,'instrument'),(676,680,'destination'),
 (698,701,'waypoint'),(708,713,'beneficiary'),(762,767,'wrapping'),(769,771,'destination'),
 (775,779,'companion'),(780,785,'landmark'),(791,795,'landmark'),(797,801,'landmark'),(817,821,'support')]:
    a.mention_event(f'ev{trigger+1}',w,role=role,note='Explicit semantic relation at this mention.')
for w,fields in {37:{'patients':['e11','e12']},47:{'patients':['e13']},
 56:{'recipient_id':'e1'},79:{'recipient_id':'e3'},92:{'recipient_id':'e2'},
 120:{'recipient_id':'e5'},233:{'instruments':['e19']},251:{'recipient_id':'e2'},254:{'recipient_id':'e1'},
 257:{'recipient_id':'e2'},273:{'instruments':['e34']},284:{'recipient_id':'e2'},323:{'recipient_id':'e1'},
 358:{'recipient_id':'e2'},397:{'recipient_id':'e2'},446:{'recipient_id':'e1'},467:{'recipient_id':'e2'},
 519:{'recipient_id':'e1'},566:{'recipient_id':'e1'},605:{'recipient_id':'e2'},659:{'instruments':['e52']},
 716:{'recipient_id':'e4'},744:{'recipient_id':'e5'},769:{'recipient_id':'e3'},790:{'recipient_id':'e2'}
 }.items():
    a.events[f'ev{w+1}'].update(fields)
    for row in a.words:
        if row.get('event_id')==f'ev{w+1}' and row.get('role')=='action':F(row['word_index'],**fields)

REPORTS={'q1':56,'q2':56,'q3':92,'q4':92,'q9':251,'q10':254,'q11':254,'q12':284,
 'q13':323,'q14':323,'q15':358,'q17':397,'q18':397,'q19':446,'q22':467,'q23':467,
 'q24':519,'q25':566,'q27':605,'q28':605,'q29':644,'q30':644,'q31':744,'q32':744,'q33':790}
ACTS=['allocation','allocation','desire_statement','manner_commitment','loan_permission','picking_instructions','crate_rule',
 'acknowledgment','success_announcement','acknowledgment','request_turn','manner_reminder','attention_request','quality_judgment',
 'manner_reminder','gentleness_claim','stop_request','hazard_report','ability_claim','rule_reminder','recipient_goal_reminder',
 'acknowledgment','alternative_suggestion','readiness_judgment','count_announcement','preference_prediction','alternative_prediction',
 'repair_suggestion','allocation_decision','sharing_plan','praise','taste_prediction','delivery_acknowledgment']
for n,((sid,start,stop,speaker,listener),act) in enumerate(zip(QUOTES,ACTS),1001):
    if sid in REPORTS:uid=f'ev{REPORTS[sid]+1}'
    else:
        uid=f'ev{n}'
        a.event(uid,start,act,type='speak',actor=speaker,recipient=listener,scope='s0',primary=False,support=range(start,stop))
    a.scopes[sid]['utterance_event_id']=uid
    F(start,utterance_id=uid,speech_act_kind=act,addressee_ids=[listener],communication_channel='speech')
original_rule=a.scopes['q7']['utterance_event_id']
a.mention_event(original_rule,449,role='action',note='Tessa recalls Bell original crate rule; outer Tessa utterance is separate.')
F(449,assertion_status='attributed_claim',evidence_report_depth=2)

# Explicit morphology and simple constructional features.
for row in a.words:
    w,t,pos=row['word_index'],row['token'].casefold(),row['pos']
    if pos=='det' and t in {'the','a','an'}:F(w,determiner_kind='definite_article' if t=='the' else 'indefinite_article',definiteness='definite' if t=='the' else 'indefinite')
    if pos=='det' and t in {'his','her','my','their','its'}:F(w,determiner_kind='possessive',possessive_construction='possessive_determiner')
    if pos=='conj' and t in {'and','but','or'}:F(w,coordinator_type={'and':'conjunctive','but':'adversative','or':'disjunctive'}[t])
    if pos=='conj' and t in {'while','when','whenever','before','after','until'}:F(w,subordinator_type='temporal',temporal_signal_relation={'while':'overlap','whenever':'recurring'}.get(t,t))
    if pos=='adp':F(w,dependency_relation='prepositional_marker')
    if pos=='part' and t=='to':F(w,dependency_relation='infinitival_marker')
    if pos=='pron' and t in {'i','she','he','we','you','they','it','me','him','us','them'}:
        F(w,mention_form='personal_pronoun',grammatical_person=1 if t in {'i','we','me','us'} else 2 if t=='you' else 3)
        if t in {'me','him','us','them'}:F(w,grammatical_case='objective')
        if row.get('entity_id'):F(w,antecedent_id=row['entity_id'])
    if pos=='n' and t in {'tessa','jun','willa','mrs','bell'}:F(w,mention_form='proper_name',grammatical_number='singular')
for w in [2,16,22,33,36,46,56,68,78,92,96,100,109,112,125,168,191,198,203,211,219,220,223,233,
 236,248,251,253,254,260,264,271,273,284,287,293,299,305,312,318,323,331,340,347,353,358,364,
 369,375,380,388,393,397,403,408,419,424,446,449,452,457,467,473,479,488,493,503,511,514,519,
 521,525,529,550,556,560,566,570,579,588,595,605,613,622,627,633,644,649,659,670,682,688,698,
 706,716,721,725,732,738,744,760,762,769,774,787,790,797,812]:F(w,tense='past',verb_form='finite')
for w in [86,178,196,360,400,465,469,639]:F(w,tense='present',verb_form='finite')
for w in [8,71,81,88,104,120,143,147,154,159,160,179,257,266,280,321,342,395,416,441,515,544,592,598,609,646,752]:F(w,verb_form='base')
for w in [37,47,69,79,138,242,533,726,739,740,757,780,817]:
    if w!=242:F(w,verb_form='past_participle')
for w in [10,28,242,361,401,435,483,546,676,703,708,745,775,791]:F(w,verb_form='gerund_participle')
for w,aux in [(37,36),(47,46),(69,68),(79,78),(220,219),(726,725),(740,738)]:F(w,aspect='perfect',perfect_auxiliary_id=a.anchor(aux))
F(220,verb_form='past_participle');a.words[220].pop('tense',None)
for w,aux in [(361,360),(401,400),(775,774)]:F(w,aspect='progressive',progressive_auxiliary_id=a.anchor(aux))
for w in [69,79,726,740]:a.words[w].pop('tense',None)
F(740,voice='passive',passive_auxiliary_id=a.anchor(739))
for w,expansion in {158:['will','not'],184:['you','are'],186:['it','is'],325:['one','is'],452:['was','not'],469:['there','is'],514:['did','not'],597:['will','not'],645:['we','will']}.items():F(w,contraction_expansion=expansion)
for w in [65,93,121,208,351,481,585,636,650,664,700,772,819]:F(w,possessive_construction='possessive_determiner')
for w in [390,455,462,763,809]:F(w,genitive_realization='singular_s_clitic')
for w in [21,27,39,54,89,139,210,214,218,231,298,316,345,387,434,456,496,675,723,731,737,748,779,795]:
    if w!=298:F(w,grammatical_number='plural')
F(90,reflexive_antecedent_id='e1',mention_form='emphatic_reflexive')
for w in [64,118,177,184,202,304,317,472,492,520,569,607,624,645,648,705,715]:F(w,group_members=['e1','e2'],split_antecedent_ids=['e1','e2'])
F(685,antecedent_candidates=['e11','e53'],reference_unresolved=True,evidence=[675,676,680,682,683,685],note='Honey is drizzled over the prepared food; them can denote the topped oatcakes or their pear pieces.')
F(680,referent_kind='bound_variable',evidence=[38,39,676,677,679,680],note='Each oatcake is a distributive variable over the two actual oatcakes, not kind-level generic reference or the whole pair as one recipient.')
F(677,referent_kind='bound_variable',evidence=[670,675,676,677,679,680],note='A pair of pieces per oatcake, drawn from the produced pieces. The text does not assert that all produced pieces were placed.')
a.mention_event('ev671',675,role='result',note='Pieces result from breaking the pear; not all are asserted placed on oatcakes.')

# Syntax is authored from the clauses, independently of semantic actor roles.
F(8,modal_base={'kind':'ability','holder':'e1'},evidence=[1,3,4,6,8,9,10],note='The small orchard establishes hearing capacity. The underlying hearing event remains hypothetical; the narration does not independently assert a particular hearing episode.')
SUBJECTS={
 2:'e6',3:'e6',8:'e1',10:'e2',16:'e1',22:'e7',28:'e9',33:'e10',37:'e2',47:'e1',56:'e2',
 69:'e3',71:'e3',79:'e2',81:'e2',86:'e1',88:'e1',92:'e1',96:'e2',109:'e4',112:'e4',120:'e5',125:'e4',
 143:'e5',147:'e5',154:'e5',159:'e24',160:'e5',168:'e4',179:'e5',185:'e5',189:'e26',191:'e2',196:'e2',
 198:'e1',203:'e5',211:'e29',220:'e31',223:'e1',233:'e1',236:'e32',242:'e32',248:'e1',251:'e1',253:'e1',
 254:'e2',257:'e1',260:'e2',264:'e2',266:'e2',271:'e19',273:'e1',280:'e1',284:'e1',287:'e2',293:'e35',
 299:'e33',305:'e5',312:'e5',318:'e5',321:'e1',323:'e2',326:'e37',331:'e37',340:'e37',342:'e37',347:'e2',
 353:'e22',358:'e1',361:'e2',362:'e2',364:'e2',369:'e22',375:'e39',380:'e38',388:'e40',393:'e2',395:'e2',
 397:'e1',401:'e38',403:'e2',408:'e37',416:'e2',419:'e2',424:'e2',441:'e2',446:'e2',449:'e4',454:'e26',
 457:'e43',465:'e1',467:'e1',473:'e5',479:'e37',483:'e37',488:'e38',493:'e5',504:'e46',511:'e1',515:'e46',
 519:'e2',521:'e5',525:'e46',529:'e2',533:'e47',544:'e19',546:'e19',550:'e2',556:'e2',560:'e47',566:'e2',
 570:'e5',579:'e47',590:'e47',595:'e2',598:'e3',603:'e3',605:'e1',609:'e5',613:'e2',622:'e37',627:'e2',
 633:'e2',639:'e3',644:'e2',646:'e5',649:'e5',659:'e1',670:'e2',676:'e2',682:'e1',688:'e6',698:'e54',
 703:'e54',706:'e5',708:'e5',716:'e5',721:'e4',726:'e5',734:'e40',740:'e61',744:'e4',745:'e4',752:'e47',
 760:'e2',762:'e2',769:'e2',775:'e3',780:'e56',787:'e2',790:'e3',791:'e3',797:'e2',812:'e37',817:'e37'}
for w,eid in SUBJECTS.items():F(w,grammatical_subject_id=eid)
for w in [143,147,154,160,257,321,395]:
    F(w,mood='imperative',imperative_subject_status='understood_addressee')
F(99,expletive_reference=True,expletive_license=True)
F(469,expletive_reference=True,expletive_license=True)
for w,head in [(7,8),(70,71),(80,81),(87,88),(103,104),(265,266),(279,280),(341,342),(415,416),(543,544),(591,592)]:
    F(w,infinitive_marker_id=a.anchor(w),syntactic_governor_id=a.anchor(head))
for w,eid in {37:'e11',47:'e13',109:'e6',120:'e19',125:'e20',147:'e22',160:'e24',179:'e19',198:'e20',
 211:'e30',223:'e22',260:'e33',273:'e34',280:'e19',305:'e19',312:'e19',347:'e19',353:'e37',364:'e20',
 369:'e37',441:'e37',473:'e19',493:'e45',511:'e46',521:'e46',529:'e47',550:'e22',570:'e19',579:'e50',
 598:'e47',627:'e47',633:'e47',639:'e55',646:'e47',649:'e51',659:'e50',670:'e47',676:'e53',682:'e14',
 708:'e55',716:'e19',721:'e60',762:'e55',769:'e55',787:'e55',797:'e55'}.items():F(w,grammatical_object_id=eid)
F(676,grammatical_object_id='e67')
F(294,verb_form='base')
F([119,440,597,603,608,751],verb_form='finite')
F(435,grammatical_subject_id='e40')
F(625,lexical_gloss='left unpicked despite the earlier ring contact',evidence=[369,371,479,620,625],note='Untouched here contrasts with gathering; literal absence of all prior physical contact would contradict the ring catching the fruit.')
F(376,lexical_gloss='firmly attached, not quickly')
F(792,lexical_gloss='available space beside the dolls, not an enclosed room')
F(122,noun_compound_head_id=a.anchor(123),noun_compound_relation='purpose')
F(667,noun_compound_head_id=a.anchor(668),noun_compound_relation='purpose')
F(778,noun_compound_head_id=a.anchor(779),noun_compound_relation='material')
F(694,lexical_gloss='orchard fruit as a source of scent; not a resolved picked-pear identity')
F(693,lexical_scale_dimension='scent_quality',lexical_gloss='sweet-smelling in the orchard odor description')
for w,eid,rel in [(11,'e63','source'),(17,'e64','location'),(23,'e8','above'),(51,'e14','contents'),
 (58,'e3','beneficiary'),(63,'e5','beneficiary'),(114,'e18','beside'),(144,'e25','support'),(150,'e24','around'),
 (169,'e26','direction'),(174,'e27','near'),(192,'e26','perception_target'),(204,'e28','destination'),
 (226,'e32','around'),(243,'e21','destination'),(276,'e20','contact'),(301,'e21','destination'),
 (308,'e26','destination'),(343,'e41','between'),(389,'e42','near'),(410,'e19','above'),
 (420,'e26','hypothetical_destination'),(425,'e37','perception_target'),(428,'e26','perception_target'),
 (432,'e40','perception_target'),(436,'e38','attachment'),(443,'e26','hypothetical_source'),(458,'e20','around'),
 (480,'e39','attachment'),(497,'e44','part_whole'),(534,'e48','behind'),(553,'e47','around'),
 (561,'e21','destination'),(573,'e26','destination'),(584,'e65','location'),(615,'e37','perception_target'),
 (623,'e5','above'),(635,'e42','location'),(652,'e8','support'),(655,'e26','beside'),(663,'e52','instrument'),
 (678,'e66','distributed_destination'),(699,'e12','waypoint'),(712,'e3','beneficiary'),(727,'e60','source'),
 (746,'e36','perception_target'),(765,'e51','wrapping'),(776,'e56','accompaniment'),(781,'e57','around'),
 (793,'e56','beside'),(800,'e56','between'),(802,'e27','viewing_aperture'),(806,'e2','behind'),(818,'e38','support')]:
    F(w,prepositional_object_id=eid,preposition_valency_frame=rel)
for w,value in [(206,'superlative'),(495,'comparative'),(641,'superlative'),(710,'superlative')]:F(w,adjective_degree=value)
F(394,adverb_degree='comparative',lexical_scale_dimension='turning_force',lexical_scale_direction='increase')
for w in [49,66,127,137,171,172,209,212,213,230,240,328,329,337,378,385,386,406,495,531,536,581,582,600,618,630,641,665,674,690,693,710,729,730,783,784,804,810,815,820]:F(w,adjective_position='attributive')
for w in [3,221,326,362,404,504,517,590,753]:F(w,adjective_position='predicative')
for w in [54,123,139,173,210,214,246,298,330,338,387,438,463,500,532,537,583,631,642,651,668,675,680,711,718,723,737,764,779,785,799,811,821]:F(w,noun_countability='count')
for w in [44,52,683,701]:F(w,noun_countability='mass')
F(249,propositional_antecedent_id='p8',mention_form='event_anaphor')
F([248,253],verb_phrase_ellipsis=True,propositional_antecedent_id='p8')
F(603,verb_phrase_ellipsis=True,propositional_antecedent_id='p18',evidence=[597,598,601,602,603],note='She might means Willa might want the bruised pear; it does not repeat Jun negative prediction.')

# Quantities describe local sets or plans, not a single timeless inventory.
for w,n,domain in [(12,1,{'kind':'orchard_end'}),(38,2,{'entity_id':'e11'}),(53,3,{'entity_id':'e15','status':'planned'}),
 (57,1,{'beneficiary_id':'e3','kind':'pear'}),(61,1,{'distribution':'per_cousin','kind':'pear'}),
 (315,2,{'entity_id':'e36','members':['e32','e33']}),(319,1,{'kind':'additional_needed_pear'}),
 (501,1,{'entity_id':'e46'}),(506,1,{'kind':'side','whole_id':'e46'}),
 (564,3,{'entity_id':'e36','members':['e32','e33','e47']}),
 (677,2,{'kind':'pear_piece','per_entity':'e66'}),(777,2,{'entity_id':'e56'})]:
    F(w,cardinal_value=n,counted_domain=domain)
F(62,quantity_distribution_cue='per_individual',quantifier_binding={'quantifier':'each','restriction_ids':['e1','e2'],'scope':'one pear per cousin'})
F(679,determiner_kind='distributive',quantity_distribution_cue='per_individual',quantifier_binding={'quantifier':'each','variable_id':'e66','restriction_id':'e11','scope':'two pieces on each oatcake'},evidence=[38,39,676,677,679,680],note='Four pieces are placed in total by two times two; total pieces produced and sizes are unstated.')
F(297,ordinal_rank=2);F(577,ordinal_rank=3)
F(217,determiner_kind='vague_quantifier',quantity_approximation_cue='few')
F([261,470],determiner_kind='alternative',reference_specificity='different_member')
F([53,315,564],sentence_fragment_type='count_noun_phrase')
F(461,sentence_fragment_type='interrupted_goal_reminder')
F(516,sentence_fragment_type='elliptical_negative_predication')
F(95,temporal_frequency_class='usual',evidence=[93,94,95,96,97],note='Recurring background behavior, not an extra current takeover.')
F(76,time_expression_id='time_picnic_evening',temporal_granularity='day_part',temporal_deixis='that_evening')
F(75,determiner_kind='demonstrative',definiteness='definite')
F(288,temporal_iteration_index=2,temporal_order_cue='again',supporting_event_ids=['ev265','ev288'])
F(256,temporal_deixis='now')
F([153,427,431],temporal_order_cue='then')
F([589,621,733],temporal_phase_cue='continuation')
F(489,temporal_phase_cue='return_to_prior_state')
F(526,temporal_order_cue='at_last')
F(815,temporal_granularity='day_part',temporal_phase_cue='late')

# Bind positive content under negation, with separate propositions for reports.
a.proposition('p31','Willa will not want the bruised pear.',[596,597,598,601],scope_id='q26')
a.proposition('p32','Willa might want the bruised pear.',[602,603],scope_id='q27')
a.proposition('p33','Pickers do not climb, shake branches or yank fruit.',[162,163,164,166],scope_id='q6')
a.proposition('p34','Jun is turning gently.',[359,360,361,362],scope_id='q16')
a.proposition('p35','The generic pear does not come free.',[157,158,159],scope_id='s2')
a.proposition('p36','Jun touches the high pear.',[413,414,415,416],scope_id='s3')
for w,pid in [(158,'p28'),(162,'p26'),(187,'p7'),(452,'p7'),(514,'p17'),(516,'p16'),(597,'p18'),(736,'p23')]:
    F(w,negation_scope_id=pid,negation_marker_form=a.words[w]['token'],polarity='negative',proposition_polarity='negative')
F(545,negation_scope_id='ev547',negation_attachment_kind='excluded_accompanying_action',evidence=[538,544,545,546,548],note='Reachability without branch-pulling; does not claim a pulling event occurred.')
for w,kind,holder,target in [(119,'permission','e4','ev121'),(178,'permission','e4','ev180'),
 (440,'ability','e2','ev442'),(603,'epistemic_possibility','e1','p18'),(608,'ability','e5','ev610'),
 (597,'prediction','e2','p18'),(751,'prediction','e4','p22')]:
    F(w,modal_auxiliary_class=a.words[w]['lemma'],modal_base={'kind':kind,'holder':holder},modal_scope_id=target)
F(417,subordinator_type='conditional',conditional_antecedent_id='p12',conditional_consequent_id='p36')
F(156,subordinator_type='conditional',conditional_antecedent_id='p35',conditional_consequent_id='ev161',evidence=[156,158,159,160],note='The negative antecedent is distinct from the positive content targeted by wont: if the fruit does not come free, leave it.')
F(468,modal_base={'kind':'epistemic_possibility','holder':'e1'},modal_scope_id='p15')
F(119,permission_grantor_id='e4',permission_recipient_id='e5',permission_content_id='p5',permission_status='granted_limited')
F(178,permission_grantor_id='e4',permission_recipient_id='e5',permission_content_id='p27',permission_status='granted_limited')
F(143,obligation_creditor_id='e4',obligation_debtor_id='e5',obligation_content_id='p6',obligation_status='instructed',obligation_source={'kind':'owner_instruction','source_id':'e4'})
F(162,obligation_creditor_id='e4',obligation_debtor_id='e5',obligation_content_id='p33',obligation_status='prohibited_actions',evidence=[162,163,164,166],note='Prohibition is not a child intention or an actual climb/shake/yank.')
F(187,obligation_creditor_id='e4',obligation_debtor_id='e5',obligation_content_id='p29',obligation_status='instructed')
F(449,utterance_content_id='p29',evidence_quote_source_id='e4',evidence_assertor_id='e1')
F(196,knowledge_claim_holder_id='e2',knowledge_claim_content_id='p29',epistemic_attitude_kind='acknowledgment',assertion_status='attributed_claim')
F(465,knowledge_claim_holder_id='e1',knowledge_claim_content_id='p3',assertion_status='attributed_claim')
F(326,belief_holder_id='e2',belief_content_id='p10',belief_polarity='accepts',assertion_status='attributed_claim')
F(362,belief_holder_id='e2',belief_content_id='p34',belief_polarity='accepts',assertion_status='attributed_claim')
F(517,belief_holder_id='e2',belief_content_id='p16',belief_polarity='rejects',epistemic_source_kind='inference',assertion_status='attributed_claim')
F(598,belief_holder_id='e2',belief_content_id='p18',belief_polarity='rejects',epistemic_attitude_kind='prediction',assertion_status='attributed_claim')
F(603,belief_holder_id='e1',belief_content_id='p18',belief_certainty='possible',epistemic_attitude_kind='possibility_assessment',assertion_status='attributed_claim')
F(752,belief_holder_id='e4',belief_content_id='p22',belief_polarity='accepts',epistemic_attitude_kind='prediction',assertion_status='attributed_claim')
for sid,pid in {'q1':'p1','q2':'p1','q3':'p4','q5':'p5','q6':'p6','q7':'p29','q8':'p29','q9':'p8',
 'q10':'p8','q11':'p9','q14':'p10','q16':'p34','q17':'p14','q18':'p11','q19':'p13','q20':'p29',
 'q21':'p3','q22':'p3','q23':'p15','q24':'p30','q26':'p31','q27':'p32','q28':'p19','q29':'p20',
 'q30':'p21','q32':'p22','q33':'p25'}.items():
    F(a.scopes[sid]['words'][0],utterance_content_id=pid)
for w,owner,pid,event in [(69,'e3','p2','ev70'),(79,'e2','p3','ev80')]:
    F(w,promise_content_id=pid,goal_owner_id=owner,goal_content_id=pid,goal_polarity='achieve',plan_commitment_status='promised',
      goal_scope_bundle={'owner_id':owner,'intention_event_id':event,'scope_id':'s0','assertion_status':'asserted'})
F(79,promise_beneficiary_id='e3')
F(86,goal_owner_id='e1',goal_content_id='p4',goal_polarity='achieve',goal_status='active',intention_publicity='communicated')
F(248,goal_owner_id='e1',goal_content_id='p4',goal_status='partly_satisfied',goal_satisfaction_judgment='success_at_one_pick',evidence=[86,88,90,233,236,248],note='Tessa successfully gets her own turn. The utterance does not say she must personally pick every pear.')
F(318,goal_owner_id='e5',goal_content_id='p1',goal_status='active',goal_resource_ids=['e19'],evidence=[53,54,315,316,318,319],note='The two collected pears leave one additional pear needed for the announced allocation.')
F(564,goal_owner_id='e2',goal_content_id='p1',goal_status='gathering_complete_allocation_pending',goal_progress_judgment='three_gathered')
F(639,goal_owner_id='e2',goal_content_id='p20',goal_polarity='achieve',goal_beneficiary_ids=['e3'],plan_commitment_status='adopted')
F(646,goal_owner_id='e5',goal_content_id='p21',goal_polarity='achieve',plan_commitment_status='proposed_by_Jun',intention_publicity='communicated')
F(708,goal_owner_id='e2',goal_content_id='p20',goal_status='reserved_not_yet_delivered')
F(769,goal_owner_id='e2',goal_content_id='p3',goal_status='satisfied',intention_vs_action_alignment={'intention':'p3','outcome':'ev770','alignment':'fulfilled'},evidence=[79,81,83,762,769,787,797],note='Fruit is brought home and placed by Willa dolls; the picnic itself is not explicitly enacted.')
F(595,affect_experiencer_id='e2',affect_expression_channel='facial_expression',affect_observer_attribution={'cue':'frown','possible_reading':'displeasure','assertion_status':'candidate'},evidence=[579,583,595],note='Frown is explicit; no precise emotional intensity or permanent trait is assigned.')
F(760,affect_experiencer_id='e2',affect_expression_channel='facial_expression',affect_observer_attribution={'cue':'smile','possible_reading':'positive_affect','assertion_status':'candidate'},evidence=[744,752,760],note='Smile is explicit; pride, relief and gratitude are not distinguished by the text.')

# Physical carriers, part relations, location, possession and changing state.
for w,part,whole in [(27,'e9','e7'),(128,'e20','e19'),(132,'e21','e19'),(135,'e22','e19'),(139,'e23','e19'),
 (210,'e29','e28'),(275,'e34','e1'),(292,'e35','e33'),(374,'e39','e37'),(387,'e40','e38'),
 (391,'e42','e2'),(456,'e43','e2'),(496,'e45','e44'),(583,'e50','e47'),(586,'e65','e47')]:
    F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
F(139,figurative_mapping={'target_id':'e23','source_image':'human fingers','kind':'object_part_metaphor','literal_event':False},evidence=[128,135,137,138,139],note='The picker fingers are physical prongs, distinct from Jun body-part fingers.')
for w,eid,color in [(29,'e9','silver'),(213,'e30','green'),(221,'e31','golden'),(230,'e31','golden'),
 (329,'e37','golden'),(386,'e40','bright_green'),(504,'e46','golden_on_one_side'),(582,'e50','brown'),
 (618,'e37','golden'),(730,'e40','green')]:F(w,appearance_color=B(w,eid,color))
for w,eid,material in [(131,'e21','cloth'),(172,'e26','wood'),(245,'e21','cloth'),(778,'e56','rag_fabric'),(784,'e57','wood')]:F(w,material_composition=B(w,eid,material))
F(171,containment_contents=B(171,'e26',{'contents':[],'at':'before_basket_placement'}))
F(531,object_ripeness=B(531,'e47','ripe'))
F(517,object_ripeness=B(517,'e46','not_ready_for_picking'),evidence=[511,514,515,516,517],note='Jun diagnosis from resistance, not a narrator ripeness declaration.')
F(581,material_hardness=B(581,'e50','soft'))
F(583,object_integrity=B(583,'e47','bruised'),evidence=[560,570,579,583],note='Bruise discovered after gathering; its cause and time of formation are unstated.')
F(590,affordance_eating=B(590,'e47',{'edible':True}),evidence=[587,588,589,590,591,592],note='Explicit narrator edibility of e47, without claiming absence of a bruise. Existing A0695 covers this meaning.')
F(659,event_state_change=B(659,'e47',{'before':'bruise_present','after':'bruised_area_cut_away'}))
F(670,event_result_entity=B(670,'e53',{'created_from_id':'e47','event_id':'ev671'}))
F(674,attributes=[{'name':'piece_size_relation','value':'uneven'}])
F(690,object_temperature=B(690,'e8','warm'))
F(804,object_openness=B(804,'e27','open'))
F(236,object_attachment=B(236,'e32','detached'))
F(293,object_attachment=B(293,'e33','detached'))
F(375,object_attachment=B(375,'e37','attached'))
F(380,object_shape=B(380,'e38','bent_downward'))
F(479,object_attachment=B(479,'e37','attached'))
F(488,event_state_change=B(488,'e38',{'before':'bent_downward','after':'back_in_place'}))
F(560,object_attachment=B(560,'e47','detached'))
F(740,object_integrity=B(740,'e61','not_torn'),evidence=[721,723,736,737,738,739,740],note='Restricted to checked leaves; no assertion that every orchard leaf is undamaged.')
F(820,object_shape=B(820,'e38','unbent'))
F([342,622,812],evidence=[329,340,342,622,812,815,816],note='Golden fruit appears to glow or shine in the light; no emitted-light property or gold material is asserted.')
for w,figure,landmark,relation in [(16,'e1','e64','at'),(22,'e7','e8','over'),(112,'e4','e18','beside'),
 (174,'e26','e27','near'),(223,'e22','e32','around'),(273,'e34','e20','on'),(331,'e37','e38','near_end'),
 (343,'e37','e41','between'),(388,'e40','e42','near'),(408,'e37','e19','above'),(436,'e40','e38','on'),
 (457,'e43','e20','around'),(479,'e37','e39','on'),(533,'e47','e48','behind'),(550,'e22','e47','around'),
 (584,'e50','e65','on'),(622,'e37','e5','above'),(633,'e47','e42','in_palm'),(649,'e51','e8','on'),
 (655,'e51','e26','beside'),(676,'e67','e66','on_per_oatcake'),(762,'e55','e51','wrapped_in'),
 (780,'e56','e57','seated_around'),(791,'e3','e56','making_room_beside'),(797,'e55','e56','between'),(806,'e27','e2','behind')]:
    F(w,spatial_configuration=B(w,figure,{'landmark':landmark,'relation':relation}))
for w,figure,container in [(242,'e32','e21'),(299,'e33','e21'),(560,'e47','e21')]:
    F(w,containment_direct=B(w,figure,{'container':container,'contained':True}))
for w,figure,support in [(312,'e19','e26'),(817,'e37','e38')]:F(w,spatial_support=B(w,figure,{'supported_by':support}))
for w,eid,landmark in [(203,'e5','e28'),(242,'e32','e21'),(299,'e33','e21'),(305,'e19','e26'),
 (560,'e47','e21'),(570,'e19','e26'),(769,'e55','e58')]:
    F(w,motion_destination=B(w,eid,{'event_id':f'ev{w+1}','landmark_id':landmark,'role':'destination'}))
F(473,motion_direction=B(473,'e19',{'direction':'down'}))
F(476,event_collective_participants=B(476,'e19',{'actors':['e1','e2'],'event_id':'ev474'}))
for w,eid,field,value in [(109,'e6','possession_owner',{'owner':'e4'}),(121,'e19','possession_owner',{'owner':'e4'}),
 (198,'e19','possession_holder',{'holder':'e1'}),(198,'e19','possession_borrower',{'borrower':'e5'}),
 (198,'e19','possession_lender',{'lender':'e4'}),(233,'e19','possession_user',{'user':'e1'}),
 (347,'e19','possession_user',{'user':'e2'}),(708,'e55','possession_reservation',{'reserved_for':'e3','reserved_recipient_holds_now':False}),
 (716,'e19','possession_return_target',{'return_to':'e4'}),(762,'e55','possession_holder',{'holder':'e2'})]:F(w,**{field:B(w,eid,value)})
F(198,transfer_kind=B(198,'e19','loan'),evidence=[119,120,121,123,198,200],note='Taking the handle realizes the permitted loan of the whole picker, not ownership transfer.')
F(716,transfer_kind=B(716,'e19','return'),transfer_completion=B(716,'e19',{'completed':True,'recipient':'e4'}))
F(67,social_relation_kind='younger_sister',social_relation_participants={'sister_id':'e3','sibling_id':'e2'})
F(94,social_relation_kind='cousin',social_relation_participants={'members':['e1','e2']})
F(779,ontological_type='physical_toy',evidence=[777,778,779,780,785],note='Rag dolls are physical props. No enacted character identities or toy actions are narrated.')
for w,eid,trigger,manner in [(105,'e1',88,'carefully'),(155,'e5',154,'gently'),(268,'e2',266,'too_quickly'),
 (282,'e2',287,'slowly_requested'),(300,'e33',299,'gently'),(394,'e2',393,'with_more_force'),
 (484,'e37',483,'lightly'),(557,'e2',556,'carefully'),(707,'e5',706,'slowly')]:
    F(w,event_manner=B(w,eid,{'event_id':f'ev{trigger+1}','manner':manner}))
F(821,narrative_resolution_evidence={'criterion':'p24','outcome':'ev818','status':'explicit_end_image'},
  narrative_theme_candidate={'content':'accepting_less_perfect_fruit_while_preserving_the_tree','assertion_status':'candidate','supporting_event_ids':['ev474','ev489','ev660','ev798','ev818']},
  evidence=[380,393,395,449,473,479,488,579,659,797,817,820,821],note='Final unbent branch and delivered pear support a restrained-picking interpretation; no permanent character transformation is asserted.')

feedback={
 'summary':'Whole-story annotation preserves distinct fruit identities, scoped rules/temptation, local gathering counts, repair and allocation, and the final intact branch.',
 'ambiguities':[
  {'words':[463,642,711,764,799],'issue':'gift_pear_identity','decision':'e55 is an unresolved role identity for e32 or e33. It is neither the third bruised pear e47 nor the high pear e37.'},
  {'words':[676,680,682,685],'issue':'honey_pronoun','decision':'them can denote the topped oatcakes or their pear pieces; antecedent candidates retained.'},
  {'words':[706,745,748,750,752,757],'issue':'post_meal_bruised_pear_reference','decision':'Bell refers to the trimmed pear after the cousins ate, but the text gives neither complete consumption nor exact remaining portions. No extra pear is invented.'},
  {'words':[560,570,579,583],'issue':'bruise_origin','decision':'The bruise is noticed after carrying; dropping or carrying is not asserted to have caused it.'},
  {'words':[737,740,821],'issue':'damage_scope','decision':'No torn leaves on checked branches; unbent high branch. This is not a universal claim about the whole orchard.'},
  {'words':[595,760],'issue':'affect_specificity','decision':'Frown and smile are explicit. Fine-grained emotion is only a candidate, with no stable personality claim.'}],
 'feature_gaps':[
  {'words':[674,677,679,680],'meaning':'uneven_portions_and_distributed_count','decision':'Existing quantity distribution plus a legacy piece-size relation suffice. Two per each of two oatcakes does not fix total pieces produced or equal portions.'}],
 'prompt_feedback':[
  'Keep a role-based recipient object distinct from its unresolved first/second token identity; candidate IDs do not create an extra physical item.',
  'Modal ellipsis may keep the positive predicate while changing polarity: She might does not repeat the negative wont want.',
  'A negative conditional antecedent is distinct from the positive proposition targeted by its negation operator.',
  'Do not upgrade a post-gathering defect into a causal claim about the immediately preceding drop or carry.',
  'A count announcement can close gathering while allocation/delivery remain pending.',
  'Do not interpret metaphorical tool fingers as a person, or a puppet picnic mention as an enacted fictional world.'],
 'coverage_notes':'All 41 paragraphs have explicit contextual POS/lemmas. Physical parts, distinct fruit/group/role referents, predicate roles, tense/aspect, direct/reported/conditional/capacity scopes, utterance/content links, instructions, promises, counts, possession, state changes and selected narrative evidence are sparse over the full1024 catalog. Spaces and punctuation remain deterministic and lossless.',
 'reviewed_all_words':True,
}
if __name__=='__main__':a.save(feedback)



