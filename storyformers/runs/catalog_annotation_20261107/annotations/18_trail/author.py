"""Manual retrospective trail annotation; deterministic assembly only."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a=Annotation('18_trail',prompt_version='v3')
TAGS=[
'adp det n adp n n n n n v det adj n adp n n',
'v pron v v pron pron v det adj n v adv v det n v det adj n conj det n conj pron v v det n adp det adj n',
'n v v v adp det n adj n pron v part v pron v v det n adp v adp n n v det adj n n n adp det n n adv pron v det n det n n v det adj n pron v part v det adj n adp det n',
'pron v adv adp n det n adv v pron v pron pron v v det n adv n conj n v part v adp pron',
'det num v part adp adj n n adp det n n v det n n v det n conj n v n pron v adv v v det n adj n det n v adp det n det adj n adv det n v v adp n',
'adp det n pron v det n det n v v det n det n adp n det n v adp det n n n num n conj det n n num num adp det n det n v adj adj n det n v adv adp det n',
'n v det n det n n v adp num pron v num n',
'conj pron v det n pron v pron n v adv pron v adp det adj adj n n n n v adp det n adp det n',
'n v adp det n adp det n pron v v det n n pron v pron adv v v pron adp det n',
'n v pron v v v det n n det n pron v v det n',
'adv pron v v pron n v pron part v pron adp det n',
'n v conj pron v adp det n det n v adj pron adv det n adp det n n',
'pron v adp det n n',
'n v v adp det n det n v conj det n v adp pron v det adj n adp det adj n n v det n adp det n conj n v det n adp det n',
'adp det adj n det adj n v det n det adj n v adp det n det n v adp det n',
'pron v v adv n v v adp det n',
'n v det adj n adp num n pron v det adj part adv',
'n v det n det adj n v det adj n conj det n pron v v adp pron v adj adp adj n pron v det n n conj v adv conj det adj n v adv adv pron v det n part v',
'det n v v adp det n pron v conj pron v adv adp det adj adj n pron v v adp det n',
'pron v det n adv adv adp n part v det n n v det n conj n v det n adp det adj n n v det n',
'adv pron v det adj n v v v adp det n n adv v adp adj n adp pron det adj conj adj n v adp det adj n',
'n v adj n',
'adj n n v conj v n det n part v conj pron v det n adv',
'det n v pron adp det n n v adp det n conj adp det adj adj n det adj n v adp det adj adj n v adp det adj n',
'n v n v n v adv',
'v v adv adj n v pron v det n conj v adv conj det n v adp det n det n v det n adp adj n',
'conj pron v det n n n n v v det n adv adp n pron v',
'n v part det n n det n n n v adp det adj adj n n v det n det adj n adv adj adp n n n v n n det n conj pron v adv part v det adj n',
'adp det n det n v v det n adp det n n v num adj n n adp det n n adp det adj n conj n v adp det n n adj adp det adj n v adp det adj adj n',
]
LEMMA={'Brackenwood':'Brackenwood','Discovery':'Discovery','Trail':'Trail','Ranger':'Ranger','Ivo':'Ivo','Nia':'Nia','Nia’s':'Nia','Felix':'Felix','Felix’s':'Felix','Leni':'Leni','Leni’s':'Leni','Pine':'Pine','Knob':'Knob','Shortcut':'Shortcut','Fern':'Fern','Loop':'Loop',
'asking':'ask','bushes':'bush','placed':'place','don’t':'do','Don’t':'do','said':'say','points':'point','turned':'turn','won’t':'will','had':'have','been':'be','practicing':'practice','grandfather’s':'grandfather','maps':'map','wanted':'want','could':'can','he’d':'he','hoped':'hope','moved':'move','crutches':'crutch','healing':'heal','She’d':'she','told':'tell','them':'they','promised':'promise','leaves':'leaf','read':'read','checked':'check','noticed':'notice','things':'thing','might':'may','passed':'pass','snail’s':'snail','caught':'catch','searched':'search','reached':'reach','clouds':'cloud','pointed':'point','minutes':'minute','climbed':'climb','steps':'step','curved':'curve','closes':'close','We’ve':'we','got':'get','we’ll':'we','looked':'look','tips':'tip','rested':'rest','can’t':'can','sighed':'sigh','polishing':'polish','We’re':'we','leaving':'leave','smiled':'smile','is':'be','easier':'easy','It’s':'it','began':'begin','pattering':'patter','darkened':'darken','reflecting':'reflect','held':'hold','guarded':'guard','blocked':'block','lay':'lie','branches':'branch','tangled':'tangle','looking':'look','tested':'test','slid':'slide','studied':'study','marked':'mark','should':'shall','was':'be','opened':'open','settled':'settle','rotated':'rotate','retraced':'retrace','lifted':'lift','painted':'paint','covered':'cover','grinned':'grin','eyes':'eye','gave':'give','pushed':'push','brought':'bring','trickled':'trickle','stones':'stone','paused':'pause','dots':'dot','shining':'shine','stopped':'stop','whispered':'whisper','drew':'draw','slipped':'slip','tapped':'tap','fingers':'finger','stacking':'stack','cards':'card','landed':'land','returned':'return','showed':'show','leaned':'lean','closer':'close','spots':'spot','reflections':'reflection','balancing':'balance','curled':'curl'}
for p,tags in enumerate(TAGS):a.tag(p,tags,LEMMA)
for row in a.words:
 if row['pos']=='pron':row['lemma']={'i':'I','her':'she','them':'they'}.get(row['token'].lower(),row['lemma'])
if '--lexical-check' in sys.argv:print(len(a.tagged));raise SystemExit
F=a.feature
def B(w,e,value,**extra):return dict(entity_id=e,value=value,scope_id=a.words[w]['scope_id'],assertion_status=status(a.words[w]['scope_id']),**extra)
def status(s):
 while s:
  if a.scopes[s]['kind'] in {'quotation','reported_claim'}:return 'attributed_claim'
  s=a.scopes[s]['parent']
 return 'asserted'
ENTITIES=[
('e1','Nia','person',[14,39,48,53,57,61,121,144,248,251,313,371,376,433,457,459,472,485,519,567,577,618,682,726]),
('e2','Felix','person',[70,78,82,123,140,226,228,292,294,298,379,413,514,561,616,666,669,692,730,732]),
('e3','Leni','person',[88,93,103,108,112,115,128,149,258,268,276,282,284,318,322,325,419,509,512,527,529,532,571,614,625,627,629,694,698,736,739]),
('e4','Ranger Ivo','person',[7,8,21,655,656,664,696,697,701]),
('e5','three friends','person_group',[130,152,180,236,241,245,303,309,342,409,483,488,496,502,504,585,650]),
('e6','Nia and Felix','person_pair',[86,114,315]),('e7','brass compass','compass',[12,17,20,37,382,461,517,573,685,686]),
('e8','Nia palm','body_part',[15]),('e9','compass red needle end','compass_needle',[25,468]),
('e10','trail map','map',[30,147,212,329,374,436,475,522,566,729]),
('e11','Brackenwood Discovery Trail','trail',[4,5,6,119]),('e12','trail entrance','entrance',[2]),
('e13','generic bend in instruction','bend_variable',[43]),('e14','new-trail interpretation of a bend','trail_variable',[47]),
('e15','Nia grandfather','person',[54]),('e16','grandfather old maps','map_group',[56]),
('e17','prospective hike','hike',[65]),('e18','last copper-acorn stamp impression','stamp_impression',[74,75,76,307,312,673,674,675]),
('e19','Felix discovery card','card',[80,300,671,678,734]),('e20','station collection','station_group',[85]),
('e21','prospective salamander sketch subject','salamander_role',[99]),('e22','stream','stream',[102,225,479,588]),
('e23','Leni crutches','crutch_pair',[107,740]),('e24','Leni ankle','body_part',[109]),
('e25','beech leaves','leaf_group',[136]),('e26','visited stations','station_group',[139]),('e27','station clues','clue_group',[143]),
('e28','noticed trail details','detail_group',[151]),('e29','snail','snail',[158]),('e30','snail trail','mucus_trail',[160]),
('e31','feather','feather',[162]),('e32','fern','fern',[166]),('e33','woodpecker hole','hole',[169]),('e34','woodpecker','bird',[172]),('e35','sought breakfast','food_role',[176]),
('e36','trail fork','fork',[183,321]),('e37','clouds','cloud_group',[185]),('e38','sky','sky',[189]),('e39','fork route sign','sign',[195]),
('e40','Pine Knob Shortcut','trail_route',[199,200,201,214,244,272]),('e41','Fern Loop','trail_route',[206,207,220,275,280,281,288,331,334,346,347]),
('e42','shortcut steps','step_group',[218,257]),('e43','Felix watch','watch',[229]),('e44','stamp table','table',[232,654]),
('e45','crutch tips','crutch_tip_group',[260]),('e46','fork path edge','path_edge',[264]),('e47','fork path','path',[267]),('e48','salamander pool','pool',[341]),
('e49','rain','rain',[348,385,642,713]),('e50','canopy','tree_canopy',[353]),('e51','loop path','path',[355,362,395,402]),
('e52','rain puddle on loop','puddle',[359]),('e53','branch reflected in puddle','branch',[366]),('e54','Nia jacket','jacket',[377]),
('e55','next bend','bend',[389]),('e56','fallen birch','tree',[392,396,403,560]),('e57','birch trunk','trunk',[398,418]),('e58','birch branches','branch_group',[404]),('e59','bushes','bush_group',[408]),
('e60','muddy ground','ground',[423]),('e61','tested crutch','crutch',[426,427]),('e62','map dotted line','map_symbol',[439]),
('e63','detour','trail_route',[443,451,501,555,583]),('e64','hidden detour sign','sign',[446]),('e65','dripping leaves concealing sign','leaf_group',[456]),
('e66','last blue route marker','marker',[495,526]),('e67','Leni chin','body_part',[530]),('e68','marker tree trunk','trunk',[543]),('e69','wet ivy','ivy',[548,580]),
('e70','Leni eyes','body_part_group',[564]),('e71','rainwater','water',[589]),('e72','stream stones','stone_group',[593]),('e73','mossy log','log',[599,645]),
('e74','observed spotted salamander','salamander',[602,605,611,636]),('e75','salamander orange dots','mark_group',[608]),('e76','salamander back','body_part',[613]),
('e77','Leni sketchbook','sketchbook',[630,741]),('e78','leaves entered by salamander','leaf_group',[640]),('e79','cards Ivo stacks','card_group',[660]),
('e80','final card square','card_square',[681]),('e81','compass cover','cover',[688]),('e82','Felix jacket','jacket',[693]),('e83','Leni salamander drawing','drawing',[699]),
('e84','drawn orange spots','depicted_mark_group',[708]),('e85','exit gate','gate',[711]),('e86','ending puddle','puddle',[717]),('e87','trail sign at exit','sign',[721]),
('e88','three reflections','reflection_group',[725]),('e89','drawn salamander','depicted_salamander',[746]),('e90','drawn blue triangle','depicted_marker',[752]),
('e91','blue triangle indicating detour','marker',[536,550]),
]
for args in ENTITIES:a.entity(*args)
a.entities['e5']['members']=['e1','e2','e3'];a.entities['e6']['members']=['e1','e2']
a.entities['e61']['member_of']='e23';a.entities['e21']['eventual_fulfilling_entity']='e74'
a.entities['e64']['possible_identity']='e91';a.entities['e64']['identity_uncertain']=True
for key in ['appearance_color','part_whole_relation','figurative_mapping']:a.use_extension(key)
QUOTES=[('q1',[*range(16,21),*range(23,48)],'e4'),('q2',range(230,240),'e2'),('q3',range(240,248),'e1'),('q4',[*range(276,282),*range(284,292)],'e3'),('q5',range(303,308),'e2'),('q6',[*range(308,313),*range(315,322)],'e1'),('q7',range(330,342),'e3'),('q8',range(409,413),'e2'),('q9',range(431,433),'e3'),('q10',[*range(478,485),*range(487,502)],'e1'),('q11',[531],'e3'),('q12',[563,564],'e2'),('q13',[565,566],'e1'),('q14',range(621,625),'e3'),('q15',range(661,664),'e4')]
for sid,words,speaker in QUOTES:a.scope(sid,words,kind='quotation',holder_id=speaker);F(words,quote_mode='direct')
SCOPES=[('s1',range(39,48),'conditional_consequence','q1','e4','Map-orientation instruction prevents a possible error.'),('s2',range(59,70),'desired','s0','e1','Nia goal: demonstrate independent leadership.'),('s3',range(72,86),'desired','s0','e2','Felix wants the final stamp and complete collection.'),('s4',range(95,103),'desired','s0','e3','Leni hopes to sketch a salamander.'),('s5',range(115,120),'reported_claim','s0','e3','Earlier ability claim; not a completed trail traversal.'),('s6',range(125,129),'promised','s0','e6','Promise to remain beside Leni.'),('s7',range(152,157),'counterfactual','s0',None,'Potentially overlooked details.'),('s8',range(240,245),'conditional_antecedent','q3','e1','Take shortcut, unchosen.'),('s9',range(245,248),'conditional_consequence','q3','e1','Reach table on time if shortcut chosen.'),('s10',range(447,452),'expected','s0',None,'Expected sign function.'),('s11',range(487,496),'conditional_antecedent','q10','e1','Retrace to marker.'),('s12',range(496,502),'conditional_consequence','q10','e1','Ability to look for detour.'),('s13',range(745,753),'depiction','s0','e3','Drawing content, distinct from actual final salamander location.')]
for sid,words,kind,parent,holder,desc in SCOPES:a.scope(sid,words,kind=kind,parent=parent,holder_id=holder,description=desc)
PROPS=[
(1,'Nia loses the borrowed compass.',[18,19,20],'q1'),(2,'Nia keeps the map aligned with the compass.',[28,30,31,37],'q1'),(3,'Nia mistakes a bend for a new trail.',[40,41,43,47],'s1'),
(4,'Nia demonstrates that she can lead a hike without asking for help.',list(range(60,70)),'s2'),(5,'Felix obtains the final copper-acorn stamp and completes his station collection.',[76,83,84,85],'s3'),(6,'Leni sketches a spotted salamander near the stream.',[96,99,102],'s4'),
(7,'Leni can manage the trail.',[115,116,117,119],'s5'),(8,'Nia and Felix keep beside Leni.',[121,123,126,128],'s6'),
(9,'The stamp table closes at five.',[232,233,235],'q2'),(10,'The friends have forty minutes remaining.',[236,237,238,239],'q2'),
(11,'The friends take the shortcut.',[241,242,244],'s8'),(12,'The friends reach the stamp table before it closes.',[245,246,247],'s9'),(13,'Leni can traverse the Fern Loop.',[276,277,278,281],'q4'),(14,'Leni traverses the Fern Loop at a sprint.',[284,287,288,291],'q4'),
(15,'The friends miss the final stamp.',[303,305,307],'q5'),(16,'Nia and Felix leave Leni at the fork.',[315,317,318,321],'q6'),(17,'Nia and Felix do not leave Leni at the fork.',[315,316,317,318,321],'q6'),
(18,'The Fern Loop is easier and leads to the salamander pool.',[331,333,334,337,341],'q7'),(19,'The friends climb safely over the fallen birch.',[409,411,418,431,432],'q9'),
(20,'The stream is on the friends’ left.',[479,481,483,484],'q10'),(21,'The friends go back to the last blue marker.',[488,489,495],'s11'),(22,'The friends can look for the detour.',[496,497,498,501],'s12'),
(23,'The friends get too close to the salamander.',[621,622,624,636],'q14'),(24,'The friends do not get too close to the salamander.',[621,622,624,636],'q14'),(25,'The friends reach the stamp table just in time.',[650,651,654,661,663],'q15'),
(26,'The friends take the shortcut and consequently reach the stamp table in time.',[240,242,246],'q3'),(27,'If the friends go back to the last blue marker, they can look for the detour.',[487,489,498,501],'q10'),(28,'Leni cannot traverse the Fern Loop at a sprint.',[284,286,287,291],'q4'),
(29,'The friends cannot safely climb over the fallen birch.',[431,432],'q9'),(30,'The friends might miss the final stamp.',[303,304,305,307],'q5'),
]
for i,text,support,scope in PROPS:a.proposition(f'p{i}',text,support,scope_id=scope)

def E(w,label,actor=None,patients=(),kind='other',factuality=None):
 scope=a.words[w]['scope_id']
 if w==564:
  a.event('ev565',w,label,actor=actor,patients=patients,type=kind,factuality='asserted',scope='s0',primary=False)
  F(w,assertion_status='attributed_claim')
  return
 a.event(f'ev{w+1}',w,label,actor=actor,patients=patients,type=kind,factuality=factuality or ('reported' if status(scope)=='attributed_claim' else 'asserted'))
 F(w,assertion_status=status(scope))
EVENTS=[
(9,'Ivo places compass in Nia palm','e4',['e7'],'transfer'),(16,'Nia borrows compass','e1',['e7'],'obtain','desired'),(19,'Nia loses compass','e1',['e7'],'other','negated'),(22,'Ivo gives borrowing and navigation instructions','e4',[],'speak'),
(26,'red needle end points north',None,['e9'],'state'),(28,'Nia keeps map aligned with compass','e1',['e10'],'state','desired'),(41,'Nia mistakes bend for new trail','e1',['e13','e14'],'other','negated'),
(51,'Nia practices using grandfather maps','e1',['e16'],'other'),(58,'Nia wants to demonstrate independent leadership','e1',[],'state'),(60,'Nia demonstrates independent leadership','e1',[],'other','desired'),(63,'Nia leads hike','e1',['e17'],'other','desired'),(67,'Nia asks for help','e1',[],'speak','negated'),
(71,'Felix wants final stamp','e2',[],'state'),(83,'Felix completes station collection','e2',['e20'],'state','desired'),(89,'Leni has a different mission','e3',[],'state'),(94,'Leni hopes to sketch salamander','e3',[],'state'),(96,'Leni sketches salamander','e3',['e21'],'other','desired'),
(104,'Leni moves carefully on crutches','e3',[],'move'),(111,'Leni ankle is healing',None,['e24'],'state'),(113,'Leni earlier states trail capacity','e3',[],'speak'),(117,'Leni manages trail','e3',['e11'],'other','hypothetical'),(124,'Nia and Felix promise to stay beside Leni','e6',[],'speak'),(126,'Nia and Felix keep beside Leni','e6',[],'state','desired'),
(131,'three friends set off','e5',[],'move'),(134,'beech leaves drip',None,['e25'],'other'),(141,'Felix reads clues at successive stations','e2',['e27'],'perceive'),(145,'Nia checks map at successive stations','e1',['e10'],'perceive'),(150,'Leni notices trail details','e3',['e28'],'perceive'),(156,'friends pass details unnoticed','e5',['e28'],'other','hypothetical'),(163,'feather is caught in fern',None,['e31'],'state'),(174,'woodpecker searches for breakfast','e34',['e35'],'other'),
(181,'friends reach fork','e5',[],'move'),(187,'clouds change sky color','e37',['e38'],'other'),(196,'sign indicates route choices',None,['e39','e40','e41'],'state'),(215,'shortcut climbs steep uneven steps',None,['e40'],'state'),(221,'loop curves gently along stream',None,['e41'],'state'),
(227,'Felix checks watch','e2',['e43'],'perceive'),(233,'stamp table closes',None,['e44'],'other','hypothetical'),(237,'friends have forty minutes remaining','e5',[],'state'),(242,'friends take shortcut','e5',['e40'],'move','hypothetical'),(246,'friends reach table in time','e5',['e44'],'move','hypothetical'),(249,'Nia predicts shortcut success','e1',[],'speak'),(252,'Nia looks at shortcut steps','e1',['e42'],'perceive'),(261,'crutch tips rest at path edge',None,['e45'],'state'),
(269,'Leni looks between routes','e3',['e40','e41'],'perceive'),(278,'Leni traverses Fern Loop','e3',['e41'],'move','hypothetical'),(283,'Leni states ability and pace limitation','e3',[],'speak'),(287,'Leni traverses loop at sprint','e3',['e41'],'move','hypothetical'),(293,'Felix sighs','e2',[],'other'),(297,'Felix polishes discovery card','e2',['e19'],'other'),(305,'friends miss stamp','e5',['e18'],'other','hypothetical'),(311,'friends possibly miss stamp','e5',['e18'],'other','hypothetical'),(314,'Nia accepts possible delay and refuses leaving Leni','e1',[],'speak'),(317,'Nia and Felix leave Leni at fork','e6',['e3'],'other','negated'),
(323,'Leni smiles','e3',[],'other'),(326,'Leni points to map','e3',['e10'],'other'),(333,'loop is easier than shortcut',None,['e41'],'state'),(337,'loop leads to salamander pool',None,['e41'],'state'),(343,'friends turn onto loop','e5',[],'move'),
(350,'rain patters through canopy',None,['e49'],'other'),(356,'path darkens',None,['e51'],'state'),(360,'puddle spreads across path',None,['e52'],'move'),(363,'puddle reflects bent branch',None,['e52','e53'],'state'),(372,'Nia shelters map beneath jacket','e1',['e10'],'state'),(380,'Felix protects compass from rain','e2',['e7'],'other'),
(393,'fallen birch blocks trail',None,['e56','e51'],'state'),(399,'birch trunk lies across path',None,['e57'],'state'),(405,'birch branches are tangled in bushes',None,['e58'],'state'),(411,'friends climb over fallen birch','e5',['e56'],'move','hypothetical'),(414,'Felix proposes climbing over','e2',[],'speak'),(415,'Felix looks at trunk','e2',['e57'],'perceive'),(420,'Leni tests muddy ground with crutch','e3',['e60'],'other'),(428,'tested crutch slides slightly',None,['e61'],'move'),(432,'friends climb over birch safely','e5',['e56'],'move','hypothetical'),
(434,'Nia studies map','e1',['e10'],'perceive'),(440,'dotted map line marks detour',None,['e62','e63'],'state'),(449,'sign points to detour',None,['e64','e63'],'state','hypothetical'),(453,'sign is hidden behind leaves',None,['e64'],'state'),(455,'concealing leaves drip',None,['e65'],'other'),(458,'Nia opens compass','e1',['e7'],'other'),(463,'Nia turns slowly','e1',[],'move'),(469,'red needle settles north',None,['e9'],'other'),(473,'Nia rotates map to match compass','e1',['e10'],'other'),
(481,'stream lies on friends left',None,['e22'],'state','hypothetical'),(486,'Nia describes location and proposes retracing','e1',[],'speak'),(489,'friends return to blue marker','e5',[],'move','hypothetical'),(498,'friends look for detour','e5',['e63'],'perceive','hypothetical'),
(503,'friends retrace to blue marker','e5',[],'move'),(511,'Leni keeps balance','e3',[],'state'),(515,'Felix holds compass','e2',['e7'],'state'),(520,'Nia checks map again','e1',['e10'],'perceive'),(528,'Leni raises chin','e3',['e67'],'move'),(533,'Leni indicates blue triangle','e3',['e91'],'speak'),(539,'someone previously painted blue triangle',None,['e91'],'other'),(545,'ivy almost covers triangle',None,['e91'],'state'),(556,'detour path curves around birch',None,['e63'],'state'),
(562,'Felix grins','e2',[],'other'),(564,'Felix praises Leni observation','e2',['e3'],'speak'),(568,'Nia credits map','e1',['e10'],'speak'),(570,'Nia gives compass to Leni','e1',['e7'],'transfer'),(575,'Leni holds compass','e3',['e7'],'state','desired'),(578,'Nia pushes ivy aside','e1',['e69'],'move'),
(584,'friends follow detour to stream','e5',[],'move'),(590,'rainwater trickles over stones',None,['e71'],'move'),(603,'salamander pauses under log','e74',[],'state'),(609,'orange dots shine against dark back',None,['e75'],'state'),(615,'Leni stops','e3',[],'move'),(617,'Felix stops','e2',[],'move'),(619,'Nia stops','e1',[],'move'),
(622,'friends get too close to salamander','e5',['e74'],'move','negated'),(626,'Leni warns against approaching too closely','e3',[],'speak'),(628,'Leni opens sketchbook','e3',['e77'],'other'),(632,'Leni draws salamander','e3',['e83'],'other'),(637,'salamander slips into leaves','e74',[],'move'),(643,'rain taps log',None,['e49','e73'],'other'),
(651,'friends reach stamp table','e5',[],'move'),(658,'Ivo stacks cards','e4',['e79'],'other'),(665,'Ivo acknowledges timely arrival','e4',[],'speak'),(667,'Felix holds out discovery card','e2',['e19'],'other'),(676,'final stamp impression appears in last square',None,['e18'],'other'),(683,'Nia returns compass to Ivo','e1',['e7'],'transfer'),(690,'compass cover remains dry',None,['e81'],'state'),(695,'Leni shows drawing to Ivo','e3',['e83'],'other'),(702,'Ivo leans closer','e4',[],'move'),(705,'Ivo admires drawn orange spots','e4',['e84'],'perceive','desired'),(715,'rain stops',None,['e49'],'other'),(722,'ending puddle holds three reflections',None,['e86','e88'],'state'),(737,'Leni balances on crutches','e3',[],'state'),(742,'sketchbook is open at drawing',None,['e77'],'state'),(747,'drawn salamander curls beneath drawn triangle',None,['e89'],'state'),
]
for args in EVENTS:E(*args)
# Auxiliary or aspect words refer to their existing lexical predicate.
for w,target in [(31,28),(349,350),(477,473)]:a.mention_event(f'ev{target+1}',w,role='reference')
a.events['ev677']['agent_unknown']=True
a.events['ev748']['semantic_world_id']='world_drawing'
for w,recipient in [(9,'e1'),(570,'e3'),(683,'e4')]:
 a.events[f'ev{w+1}']['recipient_id']=recipient;F(w,recipient_id=recipient)
for w,instruments in [(420,['e61']),(632,['e77'])]:
 a.events[f'ev{w+1}']['instruments']=instruments;F(w,instruments=instruments)
for w,e in [(9,'e4'),(26,'e9'),(51,'e1'),(58,'e1'),(71,'e2'),(94,'e3'),(104,'e3'),(111,'e24'),(113,'e3'),(124,'e6'),(131,'e5'),(141,'e2'),(145,'e1'),(150,'e3'),(163,'e31'),(174,'e34'),(181,'e5'),(187,'e37'),(196,'e39'),(215,'e40'),(221,'e41'),(227,'e2'),(233,'e44'),(237,'e5'),(242,'e5'),(246,'e5'),(249,'e1'),(252,'e1'),(261,'e45'),(269,'e3'),(278,'e3'),(283,'e3'),(287,'e3'),(293,'e2'),(297,'e2'),(305,'e5'),(311,'e5'),(314,'e1'),(317,'e6'),(323,'e3'),(326,'e3'),(333,'e41'),(337,'e41'),(343,'e5'),(350,'e49'),(356,'e51'),(360,'e52'),(363,'e52'),(372,'e1'),(380,'e2'),(393,'e56'),(399,'e57'),(405,'e58'),(411,'e5'),(414,'e2'),(415,'e2'),(420,'e3'),(428,'e61'),(434,'e1'),(440,'e62'),(449,'e64'),(453,'e64'),(455,'e65'),(458,'e1'),(463,'e1'),(469,'e9'),(473,'e1'),(481,'e22'),(486,'e1'),(489,'e5'),(498,'e5'),(503,'e5'),(511,'e3'),(515,'e2'),(520,'e1'),(528,'e3'),(539,'e91'),(545,'e91'),(556,'e63'),(562,'e2'),(568,'e1'),(570,'e1'),(575,'e3'),(578,'e1'),(584,'e63'),(590,'e71'),(603,'e74'),(609,'e75'),(615,'e3'),(617,'e2'),(619,'e1'),(622,'e5'),(626,'e3'),(628,'e3'),(632,'e3'),(637,'e74'),(643,'e49'),(651,'e5'),(658,'e4'),(665,'e4'),(667,'e2'),(676,'e18'),(683,'e1'),(690,'e81'),(695,'e3'),(702,'e4'),(705,'e4'),(715,'e49'),(722,'e86'),(737,'e3'),(742,'e77'),(747,'e89')]:F(w,grammatical_subject_id=e)
ARGS=[(9,[7,8],[12]),(22,[21],[]),(26,[],[25]),(28,[],[30]),(41,[39],[43]),(51,[48],[56]),(58,[57],[]),(60,[61],[]),(63,[61],[65]),(71,[70],[76]),(83,[82],[85]),(89,[88],[92]),(94,[93],[]),(96,[93],[99]),(104,[103],[]),(111,[],[109]),(113,[112],[114]),(117,[115],[119]),(124,[121,123],[]),(126,[121,123],[128]),(131,[130],[]),(141,[140],[143]),(145,[144],[147]),(150,[149],[151]),(163,[],[162]),(174,[172],[176]),(181,[180],[183]),(187,[185],[189]),(196,[],[195,201,207]),(215,[],[214,218]),(221,[],[220]),(227,[226],[229]),(233,[],[232]),(237,[236],[]),(242,[241],[244]),(246,[245],[]),(249,[248],[]),(252,[251],[257]),(261,[],[260]),(269,[268],[272,275]),(278,[276],[281]),(283,[282],[]),(287,[284],[288]),(293,[292],[]),(297,[294],[300]),(305,[303],[307]),(311,[309],[312]),(314,[313],[]),(317,[315],[318]),(323,[322],[]),(326,[325],[329]),(333,[],[331]),(337,[],[334]),(343,[342],[347]),(350,[],[348]),(356,[],[355]),(360,[],[359]),(363,[],[359,366]),(372,[371],[374]),(380,[379],[382]),(393,[],[392,395]),(399,[],[398]),(405,[],[404]),(411,[409],[418]),(414,[413],[]),(415,[413],[418]),(420,[419],[423]),(428,[],[427]),(434,[433],[436]),(440,[],[439,443]),(449,[],[446,451]),(453,[],[446]),(458,[457],[461]),(463,[457],[]),(469,[],[468]),(473,[472],[475]),(481,[],[479]),(486,[485],[]),(489,[488],[]),(498,[496],[501]),(503,[502],[]),(511,[509],[]),(515,[514],[517]),(520,[519],[522]),(528,[527],[530]),(533,[532],[]),(539,[],[536]),(545,[],[536]),(556,[],[555]),(562,[561],[]),(568,[567],[566]),(570,[567],[573]),(575,[571],[573]),(578,[577],[580]),(584,[585],[583]),(590,[],[589]),(603,[602],[]),(609,[],[608]),(615,[614],[]),(617,[616],[]),(619,[618],[]),(626,[625],[]),(628,[627],[630]),(632,[627],[]),(637,[636],[]),(643,[],[642,645]),(651,[650],[654]),(658,[655,656],[660]),(665,[664],[]),(667,[666],[671]),(676,[],[675]),(683,[682],[685]),(690,[],[688]),(695,[694],[699]),(702,[701],[]),(705,[701],[708]),(715,[],[713]),(722,[],[717,725]),(737,[736],[]),(742,[],[741]),(747,[],[746])]
for w,actors,patients in ARGS:
 for role,words in [('actor',actors),('patient',patients)]:
  if words:a.mention_event(f'ev{w+1}',words,role=role,note='Explicit local participant words; syntax stored separately.')

# Grammatical labels follow the explicit contextual POS choices above.
for row in a.words:
 w=row['word_index']; word=row['token'].lower(); pos=row['pos']
 if pos=='det':
  if word in {'a','an','the'}:F(w,determiner_kind='definite_article' if word=='the' else 'indefinite_article',definiteness='definite' if word=='the' else 'indefinite')
  elif word in {'her','his','their','our','its','your'}:F(w,determiner_kind='possessive',possessive_construction='possessive_determiner')
  elif word in {'each','every'}:F(w,determiner_kind='distributive')
  elif word=='all':F(w,determiner_kind='universal')
 if pos=='conj':F(w,coordinator_type='additive' if word=='and' else 'alternative' if word=='or' else 'contrastive' if word=='but' else 'subordinator')
 if row.get('entity_id') and pos=='pron':F(w,mention_form='personal_pronoun',antecedent_id=row['entity_id'])
 if row.get('entity_id') and pos=='det':F(w,mention_form='possessive_determiner')
 if pos=='adp':F(w,dependency_relation='case_or_adposition')
 if pos=='n' and row['token'].endswith('’s'):F(w,possessive_construction='genitive',genitive_realization='apostrophe_s')
for w in [16,19,28,621,622]:F(w,mood='imperative',imperative_subject_status='understood_addressee')
for w in [16,19,28]:F(w,grammatical_subject_id='e1')
for w in [9,22,51,58,71,83,89,94,104,111,113,124,131,141,145,150,163,174,181,187,196,215,221,227,237,249,252,261,269,283,293,297,314,323,326,343,349,350,356,360,363,372,380,393,399,405,414,415,420,428,434,440,452,453,458,463,469,473,486,503,511,515,520,528,533,539,545,556,562,568,570,578,584,590,603,609,615,617,619,626,628,632,637,643,651,658,665,667,676,683,695,702,705,715,722,737,747]:F(w,tense='past')
for w in [51,111,297,350,363,405,415,455,545,609,658,737,747]:F(w,verb_form='participle')
for w in [60,63,67,96,117,126,156,242,246,278,287,305,311,317,411,449,477,481,489,498,511,575,622,705]:F(w,verb_form='base')
for w in [26,233,332,333,337]:F(w,tense='present')
for aux,verb in [(49,51),(112,113),(173,174),(186,187),(295,297),(537,539),(714,715)]:F(verb,aspect='perfect',perfect_auxiliary_id=a.anchor(aux))
for aux,verb in [(50,51),(296,297),(315,317),(538,539),(657,658)]:F(verb,progressive_auxiliary_id=a.anchor(aux))
F(539,voice='passive',passive_auxiliary_id=a.anchor(538));a.words[539].pop('progressive_auxiliary_id',None)
for w in [18,621]:F(w,contraction_expansion=['do','not'])
for w,exp in [(40,['will','not']),(82,['he','would']),(112,['she','had']),(236,['we','have']),(245,['we','will']),(286,['can','not']),(315,['we','are']),(334,['it','is'])]:F(w,contraction_expansion=exp)
for w in [56,85,107,136,139,143,151,160,185,203,218,239,257,260,300,404,408,456,505,564,593,608,640,648,660,708,725,740]:
 if a.words[w]['token'].lower() not in {'trail','card','station','clue'}:F(w,grammatical_number='plural')
for w in [63,67,96,126,477,575,705]:F(w,subject_controller_id={'63':'e1','67':'e1','96':'e3','126':'e6','477':'e1','575':'e3','705':'e4'}[str(w)])
for w,governor in [(59,60),(95,96),(125,126),(476,477),(510,511),(574,575),(704,705)]:F(w,infinitive_marker_id=a.anchor(w),syntactic_governor_id=a.anchor(governor))
for w in [105,222,464,506,633]:F(w,dependency_relation='manner_adverb')
F(333,adjective_degree='comparative',lexical_scale_dimension='traversal_difficulty')
F(703,adverb_degree='comparative',lexical_scale_dimension='distance')
F(247,mention_form='propositional_anaphor',propositional_antecedent_id='p12')
F(505,lexical_gloss='previous route traversed, not the shortcut stair treads',reference_unresolved=False)
F(564,reference_metonymic_link={'source_id':'e70','target_id':'e3','relation':'eyes_for_observational_skill'})
F(410,modal_auxiliary_class='can',modal_base={'kind':'practical_ability','holder':'e2'},modal_scope_id='ev412')
for w,kind,holder,target in [(62,'ability','e1','ev64'),(116,'ability','e3','ev118'),(153,'counterfactual_possibility',None,'ev157'),(277,'ability','e3','ev279'),(286,'ability','e3','p14'),(304,'epistemic_possibility','e2','p15'),(310,'epistemic_possibility','e1','p15'),(448,'expectation',None,'ev450'),(480,'epistemic_expectation','e1','p20'),(497,'ability','e1','p22')]:F(w,modal_auxiliary_class=a.words[w]['lemma'],modal_base={'kind':kind,'holder':holder},modal_scope_id=target)
for w,pid in [(18,'p1'),(40,'p3'),(286,'p14'),(316,'p16'),(431,'p19'),(621,'p23')]:F(w,negation_scope_id=pid,negation_marker_form=a.words[w]['token'],polarity='negative',proposition_polarity='negative')
F(66,negation_scope_id='ev68',negation_attachment_kind='excluded_assistance',evidence=[58,60,63,66,67,69],note='Independence is Nia goal, not a proved final accomplishment.')
F(240,subordinator_type='conditional',conditional_antecedent_id='p11',conditional_consequent_id='p12')
a.propositions['p26']['text']='If the friends take the shortcut, they will reach the stamp table in time.'
F(487,subordinator_type='conditional',conditional_antecedent_id='p21',conditional_consequent_id='p22')
F(38,conditional_antecedent_id='p2',conditional_consequent_id='p3')
# The negative consequence needs its own complete proposition.
a.proposition('p31','Nia does not mistake a bend for a new trail.',[39,40,41,43,47],scope_id='s1')
F(38,conditional_consequent_id='p31')
for w,pid,owner in [(58,'p4','e1'),(71,'p5','e2'),(94,'p6','e3')]:F(w,goal_owner_id=owner,goal_content_id=pid,goal_polarity='achieve',goal_status='active')
F(124,promise_content_id='p8',promise_beneficiary_id='e3',plan_commitment_status='promised')
F(113,utterance_content_id='p7',speaker_id='e3',addressee_ids=['e1','e2'],quote_mode='indirect',speech_act_kind='ability_claim')
F(16,permission_grantor_id='e4',permission_recipient_id='e1',permission_content_id='ev17',permission_status='granted',possession_borrower=B(16,'e7','e1'))
F(18,obligation_debtor_id='e1',obligation_creditor_id='e4',obligation_content_id='p1',obligation_status='prohibited')
F(28,obligation_debtor_id='e1',obligation_content_id='p2',obligation_status='instructed')
F(317,intention_holder_id='e6',intention_content_id='p17',plan_commitment_status='declared')
F(621,obligation_debtor_id='e6',obligation_content_id='p23',obligation_status='prohibited',request_action_id='p24')
F(624,lexical_scale_direction='excess',spatial_distance_band=B(624,'e5','too_close',landmark_id='e74'))
SPEECH=[('q1',16,'e1','instruction',None),('q2',233,'e5','time_report','p9'),('q3',242,'e5','conditional_prediction','p26'),('q4',278,'e6','ability_report','p13'),('q5',305,'e5','concern','p30'),('q6',311,'e5','acceptance',None),('q7',333,'e6','route_assessment','p18'),('q8',411,'e5','proposal',None),('q9',432,'e6','safety_objection','p29'),('q10',481,'e5','navigation_assessment','p20'),('q11',531,'e6','indication',None),('q12',564,'e3','praise',None),('q13',566,'e5','credit',None),('q14',622,'e6','warning','p24'),('q15',661,'e5','acknowledgment','p25')]
for sid,w,addressee,act,pid in SPEECH:
 speaker=a.scopes[sid]['holder_id']
 listeners=[e for e in a.entities['e5']['members'] if e!=speaker] if addressee=='e5' else [addressee]
 F(w,utterance_id=sid,speaker_id=speaker,addressee_ids=listeners,speech_act_kind=act,communication_channel='spoken')
 if pid:F(w,utterance_content_id=pid)
F(237,utterance_content_id='p10');F(287,utterance_content_id='p28');F(317,utterance_content_id='p17');F(489,utterance_content_id='p27')
F(432,verb_phrase_ellipsis=True,evidence=[409,411,418,431,432],note='Leni denies safe group climbing under current mud conditions, not all movement or her ability to use the loop.')
F(278,affordance_traversal={'actor_id':'e3','route_id':'e41','scope_id':'q4','can_traverse':True,'pace':'not_sprint','assertion_status':'attributed_claim'})
F(432,affordance_traversal={'actor_id':'e5','route_id':'e51','obstacle_id':'e56','method':'climb_over','safely_traversable':False,'scope_id':'q9','assertion_status':'attributed_claim'})
F(111,event_state_change={'entity_id':'e24','dimension':'healing','phase':'ongoing','scope_id':'s0','assertion_status':'asserted'})
F(104,motion_manner=B(104,'e3','carefully'),motion_support=B(104,'e3','e23'))
F(503,motion_manner=B(503,'e5','slow_enough_for_Leni_balance'),motion_path_reversal=B(503,'e5','retrace_to_marker'),motion_waypoint=B(503,'e5','e66'))
F(511,motion_balance=B(511,'e3','maintained'))
F(556,affordance_traversal={'actor_id':'e5','route_id':'e63','surface':'level','scope_id':'s0','assertion_status':'asserted','evidence':'actual group traversal later; no claim of universal access'})
F(584,motion_detour={'actor_id':'e5','route_id':'e63','blocked_route_id':'e51','obstacle_id':'e56','scope_id':'s0','assertion_status':'asserted'},motion_destination=B(584,'e5','e22'))
for w,actor,dest in [(181,'e5','e36'),(343,'e5','e41'),(651,'e5','e44')]:F(w,motion_destination=B(w,actor,dest),motion_arrival_completion=B(w,actor,True))
for w,e,landmark,relation in [(9,'e7','e8','in'),(126,'e6','e3','beside'),(163,'e31','e32','caught_in'),(221,'e41','e22','along'),(261,'e45','e46','at'),(337,'e41','e48','leads_to'),(360,'e52','e51','across'),(372,'e10','e54','beneath'),(399,'e57','e51','across'),(405,'e58','e59','tangled_in'),(453,'e64','e65','hidden_behind'),(481,'e22','e5','left_of'),(539,'e91','e68','painted_on'),(545,'e91','e69','almost_covered_by'),(556,'e63','e56','around'),(603,'e74','e73','beneath'),(637,'e74','e78','into'),(676,'e18','e80','in'),(690,'e81','e82','beneath'),(722,'e86','e87','beside'),(747,'e89','e90','beneath')]:F(w,spatial_configuration={'entity_id':e,'landmark_id':landmark,'relation':relation,'scope_id':a.words[w]['scope_id'],'assertion_status':status(a.words[w]['scope_id'])})
for w,e,color in [(24,'e9','red'),(159,'e30','silver'),(191,'e38','pewter_color'),(397,'e57','pale'),(467,'e9','red'),(494,'e66','blue'),(525,'e66','blue'),(535,'e91','blue'),(607,'e75','orange'),(612,'e76','dark'),(707,'e84','orange'),(751,'e90','blue')]:F(w,appearance_color=B(w,e,color))
for w,e,material in [(11,'e7','brass'),(256,'e42','wood'),(687,'e81','brass')]:F(w,material_composition=B(w,e,material))
for w,e,whole in [(15,'e8','e1'),(25,'e9','e7'),(109,'e24','e3'),(260,'e45','e23'),(398,'e57','e56'),(404,'e58','e56'),(426,'e61','e23'),(468,'e9','e7'),(530,'e67','e3'),(564,'e70','e3'),(608,'e75','e74'),(613,'e76','e74'),(681,'e80','e19'),(688,'e81','e7')]:F(w,part_whole_relation={'part_id':e,'whole_id':whole,'relation':'member_of' if w==426 else 'part_of'})
F(193,figurative_mapping={'target_id':'e38','source_image':'pewter','kind':'color_comparison','literal_material':False})
F(370,figurative_mapping={'target_id':'e53','source_image':'black antler','kind':'simile','literal_identity':False})
F(648,figurative_mapping={'target_id':'e49','source_image':'tiny fingers tapping','kind':'simile','literal_identity':False})
F(363,lexical_gloss='puddle optically reflects the branch; no actual antler',evidence=[359,363,366,370],note='Optical reflection is not an intrinsic, observer-relative or geographical direction frame. The antler is a simile.')
F(722,lexical_gloss='puddle displays optical reflections of the three friends; the friends are not inside it')
F(747,semantic_world_id='world_drawing',evidence=[699,708,741,746,752],note='Drawn salamander and blue triangle are picture content, not actual salamander relocation beneath the marker.')
F(746,bridging_relation={'depiction_id':'e89','depicted_entity_id':'e74'});F(752,bridging_relation={'depiction_id':'e90','depicted_entity_id':'e91'})
F(202,cardinal_value=15,measure_unit='minute',temporal_duration={'route_id':'e40','value':15,'unit':'minute','source_id':'e39','kind':'sign_nominal_route_time','scope_id':'s0','assertion_status':'asserted'})
F(208,cardinal_value=35,measure_unit='minute',temporal_duration={'route_id':'e41','value':35,'unit':'minute','source_id':'e39','kind':'sign_nominal_route_time','scope_id':'s0','assertion_status':'asserted'});F(209,lexical_gloss='ones component of the compound number thirty-five')
F(235,cardinal_value=5,time_expression_id='time_table_close',temporal_deadline={'event_id':'ev234','clock_hour':5,'scope_id':'q2','assertion_status':'attributed_claim'})
F(238,cardinal_value=40,measure_unit='minute',temporal_remaining={'value':40,'unit':'minute','boundary_id':'time_table_close','scope_id':'q2','assertion_status':'attributed_claim'})
F(302,temporal_duration={'event_id':'ev298','value':'all_morning','scope_id':'s0','assertion_status':'asserted'})
F(661,temporal_deadline={'event_id':'ev652','boundary_id':'time_table_close','relation':'just_before','scope_id':'q15','assertion_status':'attributed_claim'})
F(130,cardinal_value=3,counted_domain={'entity_id':'e5','members':['e1','e2','e3']});F(723,cardinal_value=3,counted_domain={'entity_id':'e88'})
F(425,cardinal_value=1,counted_domain={'entity_id':'e61','subset_of':'e23'})
F(138,quantifier_binding={'quantifier':'each','restriction_id':'e26','scope':'visited stations before fork'},quantity_distribution_cue='per_station')
F(84,quantifier_binding={'quantifier':'every','restriction_id':'e20','scope':'desired complete station collection'})
F(680,explicit_zero_count={'container_id':'e80','counted_kind':'stamp_impression','value':0,'phase':'before_final_stamp','scope_id':'s0','assertion_status':'asserted'})
F(676,event_state_change={'entity_id':'e80','dimension':'stamp_occupancy','before':'empty','after':'stamped','scope_id':'s0','assertion_status':'asserted'},goal_owner_id='e2',goal_content_id='p5',goal_status='achieved')
F(632,goal_owner_id='e3',goal_content_id='p6',goal_status='achieved',evidence=[94,96,102,588,602,632,699],note='Actual drawing beside the stream fulfills the stated sketch goal.')
F(570,transfer_source=B(570,'e7','e1'),transfer_recipient=B(570,'e7','e3'),transfer_kind=B(570,'e7','temporary_custody'))
F(683,transfer_source=B(683,'e7','e1'),transfer_recipient=B(683,'e7','e4'),transfer_kind=B(683,'e7','return'),transfer_completion=B(683,'e7',True))
F(690,evidence=[515,570,573,683,688,690,692,693],note='Final dry cover under Felix jacket is explicit. Transfers among Felix, Nia and Leni between narrated custody endpoints are unreported; no invented handoff.')
F(453,identity_hypothesis={'entity_id':'e64','candidate_ids':['e91'],'assertion_status':'candidate','scope_id':'s0'},evidence=[443,446,453,495,526,536,548],note='Hidden detour sign and blue triangle may coincide; text does not fix their identity.')
F(632,narrative_resolution_evidence={'goal_id':'p6','event_id':'ev633','scope_id':'s0','assertion_status':'asserted'})
F(676,narrative_resolution_evidence={'goal_id':'p5','event_id':'ev677','scope_id':'s0','assertion_status':'asserted'})
F(725,narrative_closure_candidate={'evidence_words':[723,725,729,734,740,741],'meaning':'three companions together with map, completed card and sketch','assertion_status':'candidate','scope_id':'s0'})

# Final contextual refinements from reading all 29 assembled paragraphs.
F(67,lemma='ask',verb_form='gerund');F(317,verb_form='participle',tense='present')
F(83,verb_form='base');a.words[83].pop('tense',None)
F(237,tense='present',lexical_gloss='have got: current possession of time remaining')
F(87,entity_id='e3',entity_name='Leni',entity='person');a.entities['e3']['mentions'].append(87)
F(114,antecedent_id='e6');F(86,mention_form='possessive_determiner')
F(447,entity_id='e64',entity_name='hidden detour sign',entity='sign',antecedent_id='e64',mention_form='relative_pronoun');a.entities['e64']['mentions'].append(447)
for w in [134,455]:F(w,lemma='drip',verb_form='participle')
for w in [55,91,98,168,216,217,255,365,388,391,422,438,442,552,554,559,597,598,601,606,679,724,733,745,750]:F(w,adjective_position='attributive')
for w in [33,46,73,388,442,493,552,554,563,565,620,679,689,724]:
 if 'event_id' not in a.words[w]:F(w,lexical_gloss={33:'same orientation',46:'newly distinct route',73:'final missing station stamp',388:'following bend',442:'short detour length, not quantified duration',493:'most recent earlier marker',552:'narrow path width',554:'level path',563:'praise for observation',565:'credit to the map',620:'also',679:'last previously empty square',689:'continued dryness',724:'wavering reflection appearance'}[w])
for w,eid in [(0,'e12'),(3,'e11'),(13,'e8'),(52,'e16'),(68,'e69'),(100,'e22'),(106,'e23'),(127,'e3'),(133,'e25'),(164,'e32'),(175,'e35'),(197,'e40'),(210,'e10'),(223,'e22'),(253,'e42'),(262,'e46'),(270,'e40'),(273,'e41'),(319,'e36'),(327,'e10'),(338,'e48'),(344,'e41'),(351,'e50'),(361,'e51'),(375,'e54'),(383,'e49'),(386,'e55'),(400,'e51'),(406,'e59'),(416,'e57'),(424,'e61'),(450,'e63'),(454,'e65'),(491,'e66'),(499,'e63'),(523,'e66'),(540,'e68'),(546,'e69'),(549,'e91'),(557,'e56'),(586,'e22'),(591,'e72'),(595,'e73'),(610,'e76'),(638,'e78'),(677,'e80'),(691,'e82'),(709,'e85'),(718,'e87'),(727,'e10'),(731,'e19'),(738,'e23'),(748,'e90')]:
 if w!=68:F(w,prepositional_object_id=eid)
F(68,lexical_gloss='complement of asking for assistance; no named helper')
F(27,spatial_absolute_direction=B(27,'e9','north'))
F(470,spatial_absolute_direction=B(470,'e9','north'))
F(473,spatial_alignment={'entity_id':'e10','reference_id':'e7','alignment':'matched_orientation','scope_id':'s0','assertion_status':'asserted'})
F(428,motion_manner=B(428,'e61','sliding'),evidence=[420,422,423,426,428],note='A slight slide is explicit; speed is not specified.')
F(676,lexical_gloss='stamp imprint made in the card square; no copper material or named stamping agent is inferred')
F(215,lexical_gloss='route ascends steps, shown on the map; no actual shortcut hike')
F(584,lexical_gloss='detour route conveys the group; grammatical subject route differs from moving participants')
a.proposition('p32','Nia may borrow the compass, must not lose it, and should align the map with its north-pointing red end to avoid mistaking bends for new trails.',list(range(16,48)),scope_id='q1')
F(16,utterance_content_id='p32')
a.proposition('p33','The friends can climb over the fallen birch.',[409,410,411,418],scope_id='q8')
F(411,utterance_content_id='p33')
a.proposition('p34','The friends might miss the stamp, and Nia and Felix will not leave Leni at the fork.',[308,310,311,315,316,317,318,321],scope_id='q6')
F(311,utterance_content_id='p34')
# Actual implicit utterances coexist with the scoped action content.
for eid,w,speaker,label in [('ev901',233,'e2','Felix reports table closing and remaining time'),('ev902',305,'e2','Felix raises possible missed stamp'),('ev903',333,'e3','Leni describes loop difficulty and destination'),('ev904',432,'e3','Leni objects that climbing is unsafe')]:
 a.event(eid,w,label,actor=speaker,type='speak',factuality='asserted',scope='s0',primary=False)
F(564,utterance_id='ev565',communication_scope_bundle={'speaker_id':'e2','utterance_event_id':'ev565','scope_id':'s0','assertion_status':'asserted'})
a.proposition('p35','The stream should be on the friends’ left.',[479,480,481,483,484],scope_id='q10')
F(481,utterance_content_id='p35')
for pid in ['p23','p24']:a.propositions[pid]['text']=a.propositions[pid]['text'].replace('The friends','Nia and Felix')
a.events['ev623']['actor_id']='e6';F(622,actor_id='e6',actor='Nia and Felix',grammatical_subject_id='e6')
F(624,spatial_distance_band=B(624,'e6','too_close',landmark_id='e74',factuality='hypothetical',operator='prohibited',content_id='p23',prohibition_content_id='p24'))
a.words[481]['spatial_configuration'].update(factuality='hypothetical',operator='expectation',content_id='p20',utterance_content_id='p35')
F(156,verb_form='past_participle',aspect='perfect',perfect_auxiliary_id=a.anchor(155))
F(85,lexical_gloss='completing station activities and collecting their stamps, not possessing physical stations')
for w,verb in [(49,51),(50,51),(155,156),(173,174),(186,187),(295,297),(296,297),(537,539),(538,539),(657,658),(714,715)]:F(w,dependency_relation='auxiliary',syntactic_governor_id=a.anchor(verb),verb_form='finite' if w not in [50,155,296,538] else 'participle' if w in [50,296,538] else 'base')
for w,head,relation in [(79,80,'purpose'),(135,136,'tree_kind'),(259,260,'part_whole'),(299,300,'purpose'),(460,461,'size_use'),(542,543,'part_whole'),(653,654,'purpose'),(670,671,'purpose'),(720,721,'associated_route')]:F(w,noun_compound_head_id=a.anchor(head),noun_compound_relation=relation)
for w,value in [(81,'consequence'),(250,'subsequent'),(471,'subsequent')]:F(w,temporal_order_cue=value)
F(110,temporal_phase_cue='continuing');F(120,lexical_gloss='concessive still: despite Leni stated capacity')
F(154,lexical_gloss='in the alternative without Leni noticing')
F(179,lexical_gloss='temporal boundary at reaching the fork')
F(170,lexical_gloss='location of earlier breakfast search')
for w,head in [(132,131),(581,578),(668,667)]:F(w,dependency_relation='verb_particle',syntactic_governor_id=a.anchor(head))
for w,meaning in [(69,'assistance Nia wants to lead without requesting'),(369,'black within the antler simile'),(430,'small displacement of the tested crutch'),(507,'sufficiently slow for Leni balance'),(513,'Leni maintained physical equilibrium'),(544,'near-complete visual covering, not total invisibility'),(547,'wet ivy'),(647,'small size within the rain-as-fingers simile')]:F(w,lexical_gloss=meaning)

FEEDBACK={'summary':'Whole-story trail annotation separates accessible group route choice, navigation, nominal route times, scoped ability claims, actual goals and drawing/reflection content.',
'reviewed_all_words':True,'reviewed_paragraphs':list(range(29)),'ambiguities':[
 {'words':[107,109,117,278,286,431,432],'issue':'Ankle healing and crutches are explicit. No diagnosis or universal inability is inferred. Leni reports she can use the loop, but not sprint; the muddy trunk objection concerns safe current traversal.'},
 {'words':[202,208,235,238,651,661],'issue':'15/35 minutes are nominal sign durations; forty minutes is reported remaining time. Actual traversal duration and clock reading are unstated.'},
 {'words':[380,458,515,570,683,693],'issue':'Several compass custody transitions are unreported. Preserve holder endpoints and final dry cover under Felix jacket without inventing transfers.'},
 {'words':[446,495,526,536],'issue':'Keep the last blue route marker distinct from the nearby triangle. The hidden detour sign may denote that triangle, but identity is not certain.'},
 {'words':[676],'issue':'Stamp impression lands in final square, but the person stamping is not explicitly named.'},
 {'words':[58,60,67,564,568],'issue':'Nia leads navigation with group contributions; the ending does not prove her initial no-help goal was fully achieved.'},
 {'words':[602,636,746,752],'issue':'Observed salamander, its drawing and the final drawn marker are distinct; drawn layout does not assert actual animal location.'}],
'feature_gaps':[],
'prompt_feedback':['Nominal route times, reported time remaining and timely arrival are separate; do not invent actual duration by arithmetic.','A mobility aid and temporary healing condition do not license a broader diagnosis or blanket traversal incapacity.','A source can narrate actual custody endpoints while omitting intermediate transfers; record the gap.','A final drawing can combine pictured elements without relocating their real-world referents.'],
'coverage_notes':'All 753 assembled lexical records and 29 paragraphs reviewed, including full proposition and scope links, contextual entities/events, mobility claims, time distinctions and endpoints. Full catalog available sparsely; nonwords/positions assembled locally; no causal filter. Independent review follows.'}
a.save(FEEDBACK)


