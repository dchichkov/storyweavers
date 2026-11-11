"""Manually interpreted, whole-story retrospective laundry annotations, frozen v3."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a=Annotation('17_laundry',prompt_version='v3');F=a.feature
TAGS=[
'adp num adv n v det n v adp det adj n pron v adj adv adp det adj n adp n n n',
'n n v adp det n n v part v det n adp num n det adj n v v adp det adj n',
'pron v v det n pron v conj det n v v part v',
'pron v pron v n pron v n n part v pron adp det adj n n n v adv v pron v det n adp det n conj n v v adj part part v det n',
'v pron pron v part v det n conj pron v n n v pron det adj n n v pron det adj n v adv v num adp det n adp det n',
'n v det n adp det n adp det adj n adp det n n n n n v adp det n pron v pron pron adp n',
'adv v det n n v pron n adp n conj v pron adv adv pron v n n n adp det n conj det n v v det n det n v det n n',
'det n v v adp det n adj adp det adj n n v pron adj pron v adp adv v adp det n adp det n pron v v pron adp n',
'adv pron v pron',
'pron v num n adv pron det n v adp det n det adj n det adj n pron v pron adv v adp det n',
'n v adp det adj n adp det n pron v v det n adj conj v adv conj det n v adv v conj n n n n v adj adv conj pron v det n adj pron v v pron adv',
'det adj n pron v v part v pron v v det n v n n v v adv adv conj n v det adj n v adp det adj n',
'n n pron v',
'pron v adp adp det n adp det n adp det n pron det n',
'det n v v pron v det n conj pron v det n',
'pron v adv det n conj v det adj n n v det n conj n pron v v pron v pron adv adp det adj n v pron adp det n',
'pron v v det n n n n v pron det n adp det n',
'n v v det adj n adp det adj n n conj pron v pron v v pron v pron v v adv',
'v pron pron v',
'adp n pron adp pron',
'pron v det n adp det n n n v det n conj n v pron adv adv v pron adp det adj n det adj n v adp det n',
'det n n v',
'pron v num adj n adp det n adv conj n n v v pron adv pron v adp det n v det n adv n n v pron n conj n adp det n conj pron v det n adp det n',
'det adj n v det n n n v adp n pron v adp det adj adj n conj det n v pron adp det n pron v adp det n n',
'n n v pron adp det n',
'v pron v v pron adv',
'n v det n adp det n conj det adj n adv n v adp det n n conj v det n n adv det n det n v adv adp det adj n',
'n n v adp det n v det adj n n adp det n det n v adp det adj n adv adp det n v adp det n',
'pron v pron v pron adp det adj n pron v',
'det n v n v pron v det adj n n adp det n adv pron v pron',
'n n v det n conj v n n adp det adj n adj n conj v pron adp det n',
'n v adp det adj n det adj n v adv v adp adj adj n adp det n n v adj n adp det n n adv num adj n v adp det n',
]
LEM={'Tessa':'Tessa','Tessa’s':'Tessa','Mrs':'Mrs','Bell':'Bell','Bell’s':'Bell','Mr':'Mr','Osei':'Osei','Osei’s':'Osei','I':'I','I’ll':'I',
'saw':'see','clouds':'cloud','gathering':'gather','were':'be','plums':'plum','stood':'stand','washing':'washing','trying':'try','was':'be','wrapped':'wrap','shirts':'shirt','said':'say','is':'be','going':'go','wanted':'want','had':'have','seedlings':'seedling','been':'be','Would':'will','closes':'close','handed':'hand','pegs':'peg','best':'well','hooked':'hook','towels':'towel','flapped':'flap','left':'leave','them':'they','came':'come','socks':'sock','paired':'pair','clipped':'clip','hung':'hang','hems':'hem','wouldn’t':'will','shoulders':'shoulder','rattled':'rattle','lay':'lie','folded':'fold','shook':'shake','billowed':'billow','ballooning':'balloon','couldn’t':'can','told':'tell','caught':'catch','dipped':'dip','held':'hold','skidded':'skid','looked':'look','could':'can','sagging':'sag','might':'may','pulled':'pull','thought':'think','hadn’t':'have','noticed':'notice','slipping':'slip','would':'will','pictured':'picture','tumbling':'tumble','called':'call','appeared':'appear','What’s':'what','prop’s':'prop','sliding':'slide','Could':'can','unclipped':'unclip','laid':'lay','keeping':'keep','There’s':'there','seen':'see','lines':'line','she’d':'she','hoped':'hope','Using':'use','meant':'mean','starting':'start','May':'may','asked':'ask','It’s':'it','They':'they','carried':'carry','draped':'drape','sagged':'sag','used':'use','worked':'work','edges':'edge','clipping':'clip','passed':'pass','filled':'fill','raindrops':'raindrop','struck':'strike','prickled':'prickle','reached':'reach','shoved':'shove','sailed':'sail','trousers':'trousers','Saved':'save','handing':'hand','pegged':'peg','pattered':'patter','darkened':'darken','beds':'bed','stirred':'stir','carrying':'carry','eyes':'eye','went':'go','hanging':'hang','you’d':'you','slid':'slide','replied':'reply','lifted':'lift','moved':'move','took':'take','squeezed':'squeeze','thinking':'thinking','glanced':'glance','stitched':'stitch','swung':'swing'}
for p,t in enumerate(TAGS):a.tag(p,t,LEM)
for key in ['appearance_color','part_whole_relation','figurative_mapping']:a.use_extension(key)
ENTITIES=[
('e1','Tessa','person',[3,62,66,67,73,83,91,101,114,134,139,156,166,177,210,220,225,232,235,261,268,270,294,307,312,325,337,363,377,383,386,399,414,426,428,438,439,459,479,481,495,497,509,517,530,535,548,569,634,646,648,655,668,682]),
('e2','Mrs. Bell','person',[21,22,24,25,39,48,53,69,70,78,79,102,111,112,179,180,318,319,491,492,603,604,617,632,641,661,662,671]),
('e3','Mr. Osei','person',[148,149,286,287,335,336,339,349,358,367,370,405,406,453,454,506,507,556,557,561,564]),
('e4','Tessa and Mr. Osei','person_group',[446,658]),('e5','gathering clouds','cloud_group',[6,12]),('e6','shared garden','garden',[11,590,707]),
('e7','bruised plums in Bell’s tree','plum_group',[19]),('e8','Mrs. Bell’s tree','tree',[23]),('e9','large outdoor washing line','clothesline',[30,147,242,247,255,281,640]),
('e10','washing basket','basket',[35,204,393,449,515,623]),('e11','Mrs. Bell’s usable hand','body_part',[38,673]),('e12','Mrs. Bell’s braced wrist','body_part',[41]),('e13','green wrist brace','brace',[47]),
('e14','white sheet with blue border','sheet',[57,64,133,199,212,214,230,234,274,297,299,361,457,461,465,472,504,627,687]),
('e15','Mrs. Bell’s shirts','shirt_group',[52,181,183,329,380,510]),('e16','socks in the washing','sock_group',[165,168,174,382,512]),
('e17','washing being hung for Mrs. Bell','laundry_group',[366,388,395,596,636,660]),('e18','greenhouse seedlings','seedling_group',[86]),('e19','greenhouse','greenhouse',[89,344]),('e20','pharmacy','pharmacy',[107,109,616]),
('e21','borrowed yellow peg bag','bag',[118,120,137,269,653,665]),('e22','blue clothes pegs','peg_group',[123,266,478,485,697]),('e23','Tessa’s shoulder','body_part',[140,656,669]),('e24','Mr. Osei’s tea towels','tea_towel_group',[151,158,289]),('e25','outdoor wind and breeze','wind',[155,187]),
('e26','gust rattling shed door','wind_gust',[193]),('e27','shed door','door',[197]),('e28','garden shed','shed',[196,585]),('e29','shirt hems','clothing_part_group',[184]),('e30','shirt shoulders','clothing_part_group',[191]),('e31','sheet blue border','sheet_part',[209,690]),('e32','Tessa’s head','body_part',[221]),
('e33','first sheet corner Tessa catches','sheet_corner',[238]),('e34','second sheet corner Tessa catches','sheet_corner',[240]),('e35','outdoor line midpoint','line_region',[246]),('e36','wooden forked line prop','prop_stick',[249,252,253,316,355,644]),('e37','grass beneath the outdoor line','grass_region',[260,334]),('e38','washing at risk including tea towels','laundry_group',[302]),
('e39','Mr. Osei’s trowel','trowel',[347,371]),('e40','Mr. Osei’s trowel-holding hand','body_part',[350]),('e41','sheet corner Osei holds','sheet_corner_reference',[376]),
('e42','wooden rain shelter','shelter',[404,424,443,452,554,594,700]),('e43','short clotheslines in shelter','clothesline_group',[419,431,433]),('e44','selected sheltered clothesline','clothesline',[410,469,523]),('e45','shelter roof','roof',[413,631]),('e46','sheet middle','sheet_region',[476]),('e47','sheet edges','sheet_part_group',[501]),
('e48','first falling raindrops','raindrop_group',[526]),('e49','garden path','path',[529,708]),('e50','Tessa’s hair','body_part_group',[531]),('e51','last little sock caught by Osei','sock',[541,546,550,559,567,572,574]),('e52','gust blowing the sock','wind_gust',[544]),('e53','Tessa’s sock-holding hand','body_part',[549]),('e54','shelter entrance','entrance',[555]),('e55','Mr. Osei’s trousers','trousers',[562]),('e56','mate of the caught sock','sock',[575]),('e57','striped shirt beside sock','shirt',[579]),
('e58','ongoing rain','rain',[581,701]),('e59','garden beds','garden_bed_group',[591]),('e60','warm sheltered air','air',[602]),('e61','garden gate','gate',[608]),('e62','paper bag from pharmacy','bag',[613]),('e63','Mrs. Bell’s eyes','body_part_group',[618]),('e64','mud below washing','mud_region',[681]),
('e65','one sock of closing pair, unresolved member','sock_reference',[712,715]),('e66','other sock of closing pair','sock_reference',[716]),('e67','each corner of the sheet','sheet_corner_variable',[130,488]),('e68','two pegs per sheet corner','peg_pair_variable',[127,483]),('e69','shed roof','roof',[586]),
]
for eid,name,kind,mentions in ENTITIES:a.entity(eid,name,kind,mentions)
a.entities['e4']['member_ids']=['e1','e3'];a.entities['e17']['member_ids']=['e14','e15','e16'];a.entities['e38']['member_ids']=['e14','e15','e16','e24']
for eid,whole in [('e51','e16'),('e56','e16'),('e57','e15'),('e44','e43')]:a.entities[eid]['subset_of']=whole
for eid in ['e65','e66']:a.entities[eid]['identity_candidates']=['e51','e56'];a.entities[eid]['counts_as_new_object']=False
# The pronouns them at 388/395 refer to the shirts and socks, excluding the held sheet.
a.entity('e70','shirts and socks moved in basket','laundry_subgroup',[]);a.entities['e70']['member_ids']=['e15','e16']
for w in [388,395]:
 a.entities['e17']['mentions'].remove(w);a.entities['e70']['mentions'].append(w);F(w,entity_id='e70',entity_name=a.entities['e70']['name'],entity='laundry_subgroup')
QUOTES=[
('q1',[*range(48,53),*range(55,62)],'e2','e1',54,'ability_and_difficulty'),('q2',range(62,65),'e1','e2',65,'offer_to_hang_sheet'),
('q3',range(100,111),'e2','e1',100,'accept_offer_and_explain_deadline'),('q4',range(119,134),'e2','e1',119,'loan_and_pegging_instruction'),
('q5',[231],'e1',None,233,'address_sheet'),('q6',[335,336],'e1','e3',338,'summons'),('q7',range(351,354),'e3','e1',351,'ask_problem'),('q8',range(354,367),'e1','e3',354,'explain_and_request_help'),
('q9',range(399,405),'e3','e1',407,'permit_shelter_use'),('q10',range(408,414),'e3','e1',407,'line_information'),('q11',[437,438],'e1','e3',440,'permission_question'),('q12',range(441,446),'e3','e1',441,'confirm_shared_access'),
('q13',[477,478],'e1','e3',480,'request_more_pegs'),('q14',[563],'e3','e1',565,'acknowledge_catch'),('q15',range(632,641),'e2','e1',642,'report_prior_expectation'),('q16',range(643,646),'e1','e2',647,'explain_prop_problem'),('q17',range(657,661),'e1','e2',657,'explain_relocation'),('q18',range(674,682),'e2','e1',674,'praise_and_note_outcome'),
]
for sid,words,holder,recipient,trig,act in QUOTES:
 words=list(words);a.scope(sid,words,kind='quotation',holder_id=holder,description=act.replace('_',' '));uid=f'ev{1000+trig}' if trig in words else f'ev{trig+1}'
 a.scopes[sid].update(utterance_event_id=uid,addressee_ids=[recipient] if recipient else [])
 F(words[0],utterance_id=uid,speech_act_kind=act,addressee_ids=[recipient] if recipient else [],communication_channel='speech',quote_mode='direct')
for sid,words,kind,parent,holder,desc in [
('s1',range(71,78),'desired_trust','s0','e1','Trust is Tessa’s desired outcome, not yet achieved.'),('s2',range(95,100),'avoided_spill','s0','e1','Careful not to spill expresses prevention; no spill event is asserted.'),
('s3',range(104,111),'desired_pharmacy_visit','q3','e2','Visit before closing is needed, not yet actual.'),('s4',range(185,192),'preventive_purpose','s0','e1','Stretching is a prevented purpose outcome, not observed damage.'),
('s5',range(270,279),'considered_fast_finish','s0','e1','Possible quick fastening and completion, not executed on the unsafe line.'),('s6',range(293,299),'conditional_pulling','s0','e1','Pulling the sheet tight is only contemplated.'),('s7',range(299,304),'conditional_possible_fall','s0','e1','The outcome is possible under the condition, not actual.'),
('s8',[*range(304,307),*range(309,324)],'private_thought','s0','e1','The easy evasion and expected return are considered privately.'),('s9',range(310,318),'considered_pretense','s8','e1','Pretending not to have noticed is an unchosen alternative, not performed deception.'),('s10',range(312,318),'pretense_content','s9','e1','False non-noticing content of the proposed pretense, separate from actual awareness.'),('s11',range(327,335),'imagined_muddy_clothes','s0','e1','Imagined tumbling of clean shirts into mud, not actual soiling.'),
('s12',range(357,367),'requested_cooperation','q8','e1','Request that Osei hold sheet while Tessa moves clothes.'),('s13',range(428,432),'hoped_nonneed','s0','e1','Tessa had hoped the sheltered lines would not be needed.'),('s14',range(432,437),'prospective_restarting','s0','e1','Using sheltered lines would entail redoing the hanging, not already completed at this point.'),
('s15',range(634,641),'prior_expectation_content','q15','e2','Earlier expected big-line placement, contradicted by present sheltered placement.'),
]:a.scope(sid,words,kind=kind,parent=parent,holder_id=holder,description=desc)
def status(sid):
 while sid:
  if a.scopes[sid]['kind'] in ['quotation','private_thought','pretense_content','prior_expectation_content']:return 'attributed_claim'
  sid=a.scopes[sid].get('parent')
 return 'asserted'
def B(w,e,value,**extra):return dict(entity_id=e,scope_id=a.words[w]['scope_id'],assertion_status=status(a.words[w]['scope_id']),value=value,**extra)
def E(w,label,actor=None,patients=(),typ='other',fact='asserted',recipient=None,instruments=()):
 a.event(f'ev{w+1}',w,label,type=typ,actor=actor,patients=patients,factuality=fact,recipient=recipient,instruments=instruments);F(w,assertion_status=status(a.words[w]['scope_id']))
def M(w,original,note):
 a.mention_event(f'ev{original+1}',w,role='action',note=note);F(w,assertion_status=status(a.words[w]['scope_id']))
EVENTS=[
(4,'Tessa sees gathering clouds','e1',('e5',),'perceive'),(7,'clouds gather over garden',None,('e5',),'move'),(14,'clouds are dark underneath',None,('e5',),'state'),
(26,'Bell stands beside line','e2',(),'state'),(31,'Bell tries lifting basket','e2',('e10',),'other'),(33,'Bell lifts basket','e2',('e10',),'move','desired'),(43,'Bell wrist is wrapped in brace',None,('e12',),'state'),
(50,'Bell manages hanging shirts','e2',('e15',),'other','hypothetical'),(54,'Bell describes washing difficulty','e2',(),'speak'),(61,'sheet defeats Bell handling effort',None,('e14',),'other','hypothetical'),
(63,'Tessa hangs sheet','e1',('e14',),'other','desired'),(65,'Tessa offers to hang sheet','e1',(),'speak'),(68,'Tessa wants Bell trust','e1',(),'state'),(72,'Bell trusts Tessa with important task','e2',(),'state','desired'),(82,'Bell lets Tessa water seedlings','e2',(),'other'),(84,'Tessa waters seedlings','e1',('e18',),'other'),(94,'Tessa was careful in watering','e1',(),'state'),(97,'Tessa spills water','e1',(),'other','negated'),
(103,'Bell needs pharmacy visit','e2',(),'state','reported'),(105,'Bell reaches pharmacy before closing','e2',('e20',),'move','desired'),(110,'pharmacy closes',None,('e20',),'state','hypothetical'),(113,'Bell hands peg bag to Tessa','e2',('e21',),'transfer','asserted','e1'),(119,'Tessa borrows peg bag','e1',('e21',),'obtain','desired'),(124,'blue pegs grip best',None,('e22',),'state','reported'),(126,'Tessa uses two pegs per sheet corner','e1',('e68',),'other','desired'),
(135,'Tessa hooks peg bag over shoulder','e1',('e21',),'move'),(152,'Osei towels flap in breeze',None,('e24',),'move'),(157,'Tessa leaves space for towels','e1',(),'other'),
(163,'socks come first in hanging order',None,('e16',),'other'),(167,'Tessa pairs socks toe to toe','e1',('e16',),'other'),(173,'Tessa clips socks on outdoor line','e1',('e16',),'other'),(178,'Tessa hangs Bell shirts by hems','e1',('e15',),'other'),(189,'wind stretches shirt shoulders',None,('e30',),'other','negated'),(194,'gust rattles shed door',None,('e27',),'move'),
(200,'sheet lies folded in basket',None,('e14',),'state'),(211,'Tessa shakes sheet open','e1',('e14',),'move'),(215,'sheet billows',None,('e14',),'move'),(218,'sheet balloons above Tessa head',None,('e14',),'move'),(227,'Tessa sees beyond the sheet','e1',(),'perceive','negated'),(233,'Tessa tells sheet down','e1',('e14',),'speak'),
(236,'Tessa catches first sheet corner','e1',('e33',),'other'),(240,'Tessa catches another sheet corner','e1',('e34',),'other'),(243,'outdoor line dips at middle',None,('e9',),'move'),(254,'prop holds outdoor line high',None,('e9',),'state'),(257,'wooden prop slides across grass',None,('e36',),'move'),
(262,'Tessa looks at blue pegs','e1',('e22',),'perceive'),(272,'Tessa pins sheet fast','e1',('e14',),'other','hypothetical'),(277,'Tessa finishes hanging quickly','e1',('e17',),'other','hypothetical'),(284,'outdoor line sags',None,('e9',),'state'),(291,'Osei towels are close by',None,('e24',),'state'),(295,'Tessa pulls sheet tight','e1',('e14',),'other','hypothetical'),(301,'sheet drags washing down',None,('e38',),'move','hypothetical'),
(308,'Tessa considers easy evasion','e1',(),'state'),(311,'Tessa pretends she did not notice slipping','e1',(),'other','hypothetical'),(314,'Tessa notices prop slipping','e1',('e36',),'perceive','negated'),(322,'Bell returns soon','e2',(),'move','hypothetical'),(326,'Tessa imagines shirts falling into mud','e1',(),'other'),(330,'shirts tumble into muddy grass',None,('e15',),'move','hypothetical'),(338,'Tessa calls Osei','e1',(),'speak'),
(340,'Osei appears from behind greenhouse','e3',(),'move'),(359,'Osei holds sheet','e3',('e14',),'other','desired'),(364,'Tessa moves clothes','e1',('e17',),'move','desired'),
(368,'Osei puts trowel down','e3',('e39',),'move'),(373,'Osei takes sheet corner','e3',('e41',),'other'),(378,'Tessa unclips shirts and socks','e1',('e15','e16'),'other'),(387,'Tessa lays clothes in basket','e1',('e70',),'move'),(394,'Tessa keeps clothes off ground','e1',('e70',),'state'),
(401,'Tessa uses rain shelter','e1',('e42',),'other','hypothetical'),(407,'Osei offers rain shelter and line','e3',(),'speak'),(410,'a line is under shelter roof',None,('e44',),'state','reported'),
(416,'Tessa had seen shelter lines','e1',('e43',),'perceive'),(427,'Tessa hoped not to need shelter lines','e1',(),'state'),(430,'Tessa needs sheltered lines','e1',('e43',),'state','negated'),(432,'Tessa uses sheltered lines','e1',('e43',),'other','hypothetical'),(434,'shelter use entails restarting hanging',None,(),'state'),(435,'Tessa starts hanging over','e1',('e17',),'other','hypothetical'),(440,'Tessa asks permission to use shelter','e1',(),'speak'),(445,'shelter is for everyone',None,('e42',),'state','reported'),
(447,'Tessa and Osei carry basket to shelter','e4',('e10',),'move'),(455,'Osei holds sheet during folding','e3',('e14',),'other'),(460,'Tessa folds sheet lengthwise','e1',('e14',),'other'),(464,'Tessa drapes sheet over sheltered line','e1',('e14',),'other'),(473,'sheet sags at middle',None,('e14',),'state'),(480,'Tessa requests more pegs','e1',(),'speak'),
(482,'Tessa uses two blue pegs at each corner','e1',('e68',),'other'),(498,'Tessa works along sheet edges','e1',('e47',),'other'),(502,'Tessa clips sheet securely','e1',('e14',),'other'),(508,'Osei passes shirts and socks to Tessa','e3',('e15','e16'),'transfer','asserted','e1'),(518,'Tessa fills rest of sheltered line','e1',('e70',),'other'),
(527,'first raindrops strike path',None,('e49',),'other'),(532,'Tessa hair prickles with cold',None,('e50',),'state'),(536,'Tessa reaches for last sock','e1',('e51',),'move'),(545,'gust shoves sock from Tessa hand',None,('e51',),'move'),(551,'sock sails toward shelter entrance',None,('e51',),'move'),(558,'Osei catches sock against trousers','e3',('e51',),'other'),(565,'Osei acknowledges saving sock','e3',(),'speak'),(566,'Osei hands sock back to Tessa','e3',('e51',),'transfer','asserted','e1'),
(570,'Tessa pegs sock between mate and shirt','e1',('e51',),'other'),(582,'rain patters on shed roof',None,('e58',),'other'),(588,'rain darkens garden beds',None,('e59',),'other'),(597,'sheltered washing stirs gently',None,('e17',),'move'),
(605,'Bell enters through garden gate','e2',(),'move'),(609,'Bell carries pharmacy paper bag','e2',('e62',),'other'),(619,'Bell looks from basket to sheet','e2',('e10','e14'),'perceive'),(628,'sheet hangs beneath shelter roof',None,('e14',),'state'),
(633,'Bell held big-line expectation','e2',(),'state','reported'),(635,'Tessa has all washing on outdoor line','e1',('e17',),'state','hypothetical'),(642,'Bell reports earlier expectation','e2',(),'speak'),(647,'Tessa explains prop slipping','e1',(),'speak'),(649,'Tessa lifts peg bag off shoulder','e1',('e21',),'move'),
(663,'Bell takes peg bag back','e2',('e21',),'obtain'),(667,'Bell squeezes Tessa shoulder','e2',('e23',),'other'),(677,'Tessa observes clean result','e1',('e17',),'perceive','desired'),(678,'washing is in mud',None,('e17',),'state','negated'),
(683,'Tessa glances at white sheet','e1',('e14',),'perceive'),(691,'sheet border hangs straight',None,('e31',),'state'),(693,'blue pegs hold sheet border',None,('e31',),'state'),(702,'rain makes silver streaks across path',None,('e58',),'move'),(713,'one sock swings beside its mate',None,('e65',),'move'),
]
for args in EVENTS:E(*args)
seen=set()
for sid,words,holder,recipient,trig,act in QUOTES:
 uid=a.scopes[sid]['utterance_event_id']
 if uid in seen:continue
 seen.add(uid)
 if uid not in a.events:a.event(uid,trig,act.replace('_',' '),type='speak',actor=holder,recipient=recipient,scope='s0',primary=False,support=list(words))
 else:
  a.events[uid]['recipient_id']=recipient
  if recipient:F(trig,recipient_id=recipient)
# Explicit episode referents preserve multi-action recalls without inventing repeats.
a.event('ev900',173,'initial hanging of socks and shirts',type='other',actor='e1',patients=['e16','e15'],scope='s0',primary=False,support=[167,173,178]);a.events['ev900']['component_event_ids']=['ev174','ev179']
a.event('ev901',447,'Tessa and Osei relocate and rehang washing under shelter',type='other',actor='e4',patients=['e17'],scope='s0',primary=False,support=[378,387,447,455,460,464,482,502,508,518,570]);a.events['ev901']['component_event_ids']=['ev379','ev388','ev448','ev456','ev461','ev465','ev483','ev503','ev509','ev519','ev571']
for w,origin,note in [(317,257,'The same prop sliding supplies the content of the considered non-noticing pretense.'),(356,257,'Present-progressive report of the ongoing prop slipping, not another skid.'),(645,257,'Later report of the same prop sliding.'),(563,558,'Saved summarizes the immediately narrated catch, not a second rescue.')]:M(w,origin,note)
a.mention_event('ev900',385,role='action',note='Recall of earlier socks-and-shirts hanging episode, not another actual hanging.');F(385,assertion_status='asserted')
a.mention_event('ev1119',494,role='action',note='Earlier two-pegs instruction is the same original utterance.');F(494,assertion_status='asserted')
a.mention_event('ev901',659,role='action',note='We moved it summarizes the joint relocation/rehanging episode; it is the washing, not the outdoor line.');F(659,assertion_status='attributed_claim')
PROPS=[
(1,'Mrs. Bell manages hanging the shirts.',[48,49,50,52],'q1'),(2,'Mrs. Bell can manage the shirts, but the sheet will defeat her handling effort.',[48,49,50,52,55,57,59,61],'q1'),
(3,'Tessa hangs the sheet.',[62,63,64],'q2'),(4,'Mrs. Bell trusts Tessa with an important job.',[69,70,72,73,76,77],'s1'),(5,'Tessa spills some water while watering seedlings.',[84,86,95,97,99],'s2'),
(6,'Mrs. Bell reaches the pharmacy before it closes.',[102,105,107,108,109,110],'s3'),(7,'Mrs. Bell needs to reach the pharmacy before it closes.',[102,103,105,107,108,110],'q3'),(8,'Tessa borrows the peg bag.',[113,114,118,119,120],'q4'),(9,'Tessa uses two blue pegs on each corner of the sheet.',[122,123,126,127,129,130,133],'q4'),(10,'The blue pegs grip best.',[122,123,124,125],'q4'),
(11,'The wind stretches the shirt shoulders.',[187,188,189,191],'s4'),(12,'Tessa can see things beyond the cloth.',[225,226,227,228,229,230],'s0'),(13,'The sheet comes down.',[231,233,234],'q5'),(14,'Tessa pins the sheet fast and finishes quickly.',[270,271,272,274,275,277,278],'s5'),
(15,'Tessa pulls the sheet tight.',[293,294,295,297,298],'s6'),(16,'The sheet drags the washing and nearby towels down.',[299,301,302,303],'s7'),(17,'The sheet might drag the washing and nearby towels down.',[299,300,301,302,303],'s7'),
(18,'Tessa had not noticed the prop slipping.',[312,313,314,316,317],'s10'),(19,'Tessa had noticed the prop slipping.',[312,313,314,316,317],'s10'),(20,'Pretending not to have noticed the slipping prop would be easy.',list(range(304,318)),'s8'),(21,'Mrs. Bell will be back soon.',list(range(318,324)),'s8'),(22,'The clean shirts tumble into muddy grass.',[328,329,330,333,334],'s11'),(23,'The line prop slides.',[249,257,355,356,644,645],'s0'),
(24,'What problem needs attention?',[351,352,353],'q7'),(25,'Mr. Osei holds the sheet while Tessa moves the clothes.',list(range(357,367)),'s12'),(26,'Mr. Osei holds the sheet.',[358,359,361],'s12'),(27,'Tessa moves the clothes.',[363,364,366],'s12'),(28,'Tessa uses the rain shelter.',[399,401,404,437,438],'q9'),(29,'There is a line under the shelter roof.',list(range(408,414)),'q10'),
(30,'Tessa will not need the sheltered lines.',[428,429,430,431],'s13'),(31,'Tessa needs the sheltered lines.',[428,429,430,431],'s13'),(32,'May Tessa use the rain shelter?',[437,438,399,401,404],'q11'),(33,'The shelter is available for everyone.',[441,442,443,444,445],'q12'),(34,'More pegs are needed for hanging the sheet.',[477,478,473,482],'q13'),(35,'The last little sock is saved by Mr. Osei’s catch.',[558,559,563],'q14'),
(36,'Mrs. Bell thought Tessa would have all the washing on the big outdoor line.',list(range(632,641)),'q15'),(37,'Tessa has all the washing on the big outdoor line.',list(range(634,641)),'s15'),(38,'Tessa and Mr. Osei moved the washing to the shelter.',[446,447,464,518,657,658,659,660],'q17'),(39,'The relocation was good thinking, and none of the washing is in the mud.',list(range(674,682)),'q18'),(40,'Some washing is in the mud.',[678,679,681],'q18'),(41,'None of the washing is in the mud.',[678,679,681],'q18'),
(42,'Would Tessa hang the sheet?',[100,101,62,63,64],'q3'),(43,'Would Tessa hang the sheet? Mrs. Bell needs to reach the pharmacy before it closes.',list(range(100,111)),'q3'),(44,'Tessa may borrow the peg bag; blue pegs grip best, and she should use two on each sheet corner.',list(range(119,134)),'q4'),(45,'Tessa will hang the sheet.',[62,63,64],'q2'),(46,'Tessa starts the hanging over.',[432,433,434,435,436],'s14'),(47,'Using the sheltered lines means starting the hanging over.',[432,433,434,435,436],'s14'),(48,'The prop is sliding; could Osei hold the sheet while Tessa moves the clothes?',list(range(354,367)),'q8'),(49,'Tessa may use the rain shelter.',[399,400,401,404],'q9'),
]
for n,text,ws,sid in PROPS:a.proposition(f'p{n}',text,ws,scope_id=sid)
for w,pid in [(48,'p2'),(62,'p45'),(100,'p43'),(119,'p44'),(231,'p13'),(351,'p24'),(354,'p48'),(399,'p49'),(408,'p29'),(437,'p32'),(441,'p33'),(477,'p34'),(563,'p35'),(632,'p36'),(643,'p23'),(657,'p38'),(674,'p39')]:F(w,utterance_content_id=pid)
# Semantic memberships authored against specific mentions, including shared arguments.
ROLES=[
(4,[3],[6],{}),(7,[],[6],{'location':[11]}),(14,[],[12],{'comparison':[19]}),(26,[24,25],[],{'location':[30]}),(31,[24,25],[35],{'effector':[38]}),(33,[],[35],{'effector':[38]}),(43,[],[41],{'covering':[47]}),
(50,[48],[52],{}),(54,[53],[],{}),(61,[],[57],{}),(63,[62],[64],{}),(65,[66],[],{}),(68,[67],[],{}),(72,[69,70],[],{'trust_target':[73],'domain':[77]}),(82,[78,79],[],{'permitted_actor':[83]}),(84,[83],[86],{'location':[89]}),(94,[91],[],{}),(97,[91],[],{'amount':[99]}),
(103,[102],[],{}),(105,[102],[107],{}),(110,[],[109],{}),(113,[111,112],[118],{'recipient':[114]}),(119,[],[120],{}),(124,[],[123],{}),(126,[],[127],{'attachment_site':[130],'whole':[133]}),
(135,[134],[137],{'support':[140]}),(152,[],[151],{'medium':[155]}),(157,[156],[],{'beneficiary':[158]}),(163,[],[165],{}),(167,[166],[168],{'alignment':[169,171]}),(173,[166],[174],{}),(178,[177],[181],{'attachment_part':[184]}),(189,[],[191],{'causer':[187]}),(194,[],[197],{'causer':[193]}),
(200,[],[199],{'container':[204]}),(211,[210],[212],{}),(215,[],[214],{}),(218,[],[214],{'landmark':[221]}),(227,[225],[],{'occluder':[230]}),(233,[232],[234],{}),
(236,[235],[238],{}),(240,[235],[240],{}),(243,[],[242],{'affected_region':[246]}),(254,[],[255],{'support':[252,253]}),(257,[],[249,252],{'surface':[260]}),(262,[261],[266],{'container':[269]}),(272,[270],[274],{}),(277,[270],[],{}),(284,[],[281],{}),(291,[],[289],{}),(295,[294],[297],{}),(301,[],[302],{'causer':[299]}),
(308,[307],[],{}),(311,[307],[],{}),(314,[312],[316],{}),(322,[318,319],[],{}),(326,[325],[],{}),(330,[],[329],{'destination':[334]}),(338,[337],[],{'recipient':[335,336]}),(340,[339],[],{'source':[344],'carried_tool':[347],'effector':[350]}),
(359,[358],[361],{}),(364,[363],[366],{}),(368,[367],[371],{}),(373,[367],[376],{}),(378,[377],[380,382],{}),(387,[386],[388],{'container':[393]}),(394,[386],[395],{'excluded_surface':[398]}),
(401,[399],[404],{}),(407,[405,406],[],{}),(410,[],[410],{'location':[413]}),(416,[414],[419],{'location':[424]}),(427,[426],[],{}),(430,[428],[431],{}),(432,[],[433],{}),(440,[439],[],{}),(445,[],[443],{}),
(447,[446],[449],{'destination':[452]}),(455,[453,454],[457],{}),(460,[459],[461],{}),(464,[459],[465],{'support':[469]}),(473,[],[472],{'affected_region':[476]}),(480,[479],[478],{}),
(482,[481],[483,485],{'attachment_site':[488]}),(498,[497],[501],{}),(502,[497],[504],{}),(508,[506,507],[510,512],{'recipient':[509],'source':[515]}),(518,[517],[],{'support':[523]}),
(527,[],[529],{'causer':[526]}),(532,[],[531],{'cause':[534]}),(536,[535],[541],{}),(545,[],[546],{'causer':[544],'source':[549]}),(551,[],[550],{'direction_target':[555]}),(558,[556,557],[559],{'contact_surface':[562]}),(565,[564],[],{}),(566,[564],[567],{}),
(570,[569],[572],{'landmark':[575,579]}),(582,[],[581],{'contact_surface':[586]}),(588,[],[591],{'causer':[581]}),(597,[],[596],{'medium':[602]}),
(605,[603,604],[],{'route':[608]}),(609,[603,604],[613],{'origin':[616]}),(619,[617],[623,627],{'effector':[618]}),(628,[],[627],{'location':[631]}),(633,[632],[],{}),(635,[634],[636],{'location':[640]}),(642,[641],[],{}),(647,[646],[],{}),(649,[648],[653],{'source':[656]}),
(663,[661,662],[665],{}),(667,[661,662],[669],{'effector':[673]}),(678,[],[],{'location':[681]}),(683,[682],[687],{}),(691,[],[690],{}),(693,[],[690],{'support':[697]}),(702,[],[701],{'path':[708]}),(713,[],[712],{'landmark':[716]}),
]
for w,actors,patients,others in ROLES:
 for role,words in [('actor',actors),('patient',patients),*others.items()]:
  if words:a.mention_event(f'ev{w+1}',words,role=role,note='Explicit role at the local predicate, separate from grammatical subject where needed.')
a.mention_event('ev900',383,role='actor');a.mention_event('ev900',[380,382],role='patient')
a.mention_event('ev1119',[491,492],role='actor');a.mention_event('ev1119',495,role='recipient')
a.mention_event('ev901',658,role='actor');a.mention_event('ev901',660,role='patient')
for w,origin in [(356,257),(645,257)]:a.mention_event(f'ev{origin+1}',w-1,role='patient')
# Surface forms and grammar explicitly contextualized by manually selected POS.
for w,r in enumerate(a.words):
 if r['pos']=='det':
  t=r['token'].casefold();kind='possessive' if t in {'her','his','its','their'} else 'definite_article' if t=='the' else 'indefinite_article' if t in {'a','an'} else 'demonstrative' if t in {'that','this'} else 'distributive' if t=='each' else 'quantificational';F(w,determiner_kind=kind)
  if t in {'a','an','the'}:F(w,definiteness='definite' if t=='the' else 'indefinite')
  if kind=='possessive':F(w,possessive_construction='possessive_determiner')
 if r['pos']=='pron' and r.get('entity_id'):F(w,mention_form='pronoun',antecedent_id=r['entity_id'])
 if r['pos']=='adp':F(w,dependency_relation='prepositional_marker')
 if r['pos']=='part' and r['token'].casefold()=='to':F(w,dependency_relation='infinitival_marker')
 if r['pos']=='conj' and r['token'].casefold() in {'and','but'}:F(w,coordinator_type='conjunctive' if r['token'].casefold()=='and' else 'adversative')
for w in [3,21,22,24,25,66,69,70,78,79,91,111,112,134,148,149,166,179,180,210,261,286,287,318,319,325,335,336,377,405,406,414,453,454,459,479,491,492,506,507,530,556,557,569,603,604,646,661,662,668,682]:F(w,mention_form='proper_name')
for w in [21,24,69,78,111,148,179,286,318,335,405,453,491,506,556,603,661]:F(w,proper_name_structure='title_plus_name')
for w in [22,149,180,287,530,668]:F(w,possessive_construction='genitive_np',genitive_realization='apostrophe_s')
for w in [73,83,114,495,509]:F(w,lemma='she',grammatical_case='accusative')
for w in [158,168,174,388,395,431,433]:F(w,lemma='they',grammatical_case='accusative')
for w in [48,62,102,363,438,632]:F(w,grammatical_person=1)
for w in [101,358,399,634]:F(w,grammatical_person=2)
for w in [446,658]:F(w,group_members=['e1','e3'],split_antecedent_ids=['e1','e3'])
for w in [6,12,19,52,86,123,151,158,165,168,174,181,184,191,266,289,302,329,366,380,382,388,395,419,431,433,478,485,501,510,512,526,591,596,618,636,697,704]:F(w,grammatical_number='plural')
for w,x in [(62,['I','will']),(188,['would','not']),(226,['could','not']),(313,['had','not']),(351,['what','is']),(355,['prop','is']),(408,['there','is']),(426,['she','had']),(429,['would','not']),(443,['it','is']),(634,['you','would'])]:F(w,contraction_expansion=x)
F(408,expletive_reference=True,expletive_subject_id=a.anchor(408))
for w in [4,13,26,42,54,65,68,80,92,113,135,152,157,163,167,173,178,194,200,211,215,233,236,243,254,257,262,282,284,290,295,308,309,326,338,340,368,373,378,384,387,407,415,434,440,447,455,460,464,473,480,482,493,498,508,518,527,532,536,545,551,558,565,570,582,588,597,605,619,633,642,645,647,649,659,663,667,683,691,702,713]:
 if a.words[w]['pos']=='v':F(w,verb_form='finite',tense='past')
for w in [49,58,103,110,124,400]:F(w,verb_form='finite',tense='present')
for w in [50,61,63,72,84,97,105,119,126,189,227,272,277,301,311,321,359,364,401,430,635,677]:F(w,verb_form='base')
for w in [7,31,59,218,317,330,356,394,432,435,502,566,609,628]:F(w,verb_form='gerund_participle')
for w in [43,201,563,693]:F(w,verb_form='past_participle')
for w,aux in [(82,80),(93,92),(314,313),(385,384),(416,415),(427,426),(494,493)]:F(w,verb_form='past_participle',aspect='perfect',perfect_auxiliary_id=a.anchor(aux));a.words[w].pop('tense',None)
for w,aux in [(284,282),(356,355)]:F(w,verb_form='gerund_participle',aspect='progressive',progressive_auxiliary_id=a.anchor(aux));a.words[w].pop('tense',None)
F(43,voice='passive',passive_auxiliary_id=a.anchor(42))
for w in [100,188,226,271,300,313,320,357,429]:F(w,verb_form='finite',tense='past')
F(437,verb_form='finite',tense='present')
for w in [119,126,677]:F(w,mood='imperative',imperative_subject_status='understood_addressee')
for w,ctrl in [(33,'e2'),(72,'e2'),(84,'e1'),(97,'e1'),(105,'e2'),(119,'e1'),(126,'e1'),(272,'e1'),(277,'e1'),(311,'e1'),(359,'e3'),(364,'e1'),(435,'e1'),(677,'e1')]:F(w,subject_controller_id=ctrl)
# Grammatical subjects come from the local construction, not copied from actors.
SUBJECTS={4:'e1',7:'e5',14:'e5',26:'e2',31:'e2',43:'e12',50:'e2',54:'e2',61:'e14',63:'e1',65:'e1',68:'e1',72:'e2',82:'e2',84:'e1',94:'e1',97:'e1',103:'e2',105:'e2',110:'e20',113:'e2',124:'e22',135:'e1',152:'e24',157:'e1',163:'e16',167:'e1',173:'e1',178:'e1',189:'e25',194:'e26',200:'e14',211:'e1',215:'e14',218:'e14',227:'e1',233:'e1',236:'e1',240:'e1',243:'e9',254:'e36',257:'e36',262:'e1',272:'e1',277:'e1',284:'e9',291:'e24',295:'e1',301:'e14',308:'e1',311:'e1',314:'e1',317:'e36',322:'e2',326:'e1',330:'e15',338:'e1',340:'e3',356:'e36',359:'e3',364:'e1',368:'e3',373:'e3',378:'e1',385:'e1',387:'e1',394:'e1',401:'e1',407:'e3',416:'e1',427:'e1',430:'e1',440:'e1',445:'e42',447:'e4',455:'e3',460:'e1',464:'e1',473:'e14',480:'e1',482:'e1',494:'e2',498:'e1',502:'e1',508:'e3',518:'e1',527:'e48',532:'e50',536:'e1',545:'e52',551:'e51',558:'e3',565:'e3',566:'e3',570:'e1',582:'e58',588:'e58',597:'e17',605:'e2',609:'e2',619:'e63',628:'e14',633:'e2',635:'e1',642:'e2',645:'e36',647:'e1',649:'e1',659:'e4',663:'e2',667:'e2',683:'e1',691:'e31',693:'e31',702:'e58',713:'e65'}
for w,e in SUBJECTS.items():F(w,grammatical_subject_id=e)
for w,e in {4:'e5',33:'e10',50:'e15',63:'e14',84:'e18',105:'e20',113:'e21',119:'e21',126:'e68',135:'e21',167:'e16',173:'e16',178:'e15',189:'e30',194:'e27',211:'e14',233:'e14',236:'e33',240:'e34',254:'e9',272:'e14',295:'e14',301:'e38',359:'e14',364:'e17',368:'e39',373:'e41',387:'e70',394:'e70',401:'e42',416:'e43',430:'e43',432:'e43',447:'e10',455:'e14',460:'e14',464:'e14',482:'e68',502:'e14',527:'e49',545:'e51',558:'e51',566:'e51',570:'e51',588:'e59',609:'e62',649:'e21',659:'e17',663:'e21',667:'e23'}.items():F(w,grammatical_object_id=e)
for w,es in [(378,['e15','e16']),(508,['e15','e16'])]:F(w,conjunction_members=es)
for w,e in {8:'e6',20:'e8',27:'e9',36:'e11',44:'e13',74:'e1',87:'e19',128:'e67',131:'e14',138:'e23',145:'e9',153:'e25',160:'e24',182:'e29',202:'e10',206:'e31',219:'e32',229:'e14',244:'e35',258:'e37',263:'e22',267:'e21',331:'e37',342:'e19',345:'e39',348:'e40',390:'e10',396:'e37',411:'e45',420:'e42',450:'e42',466:'e44',474:'e46',486:'e67',499:'e47',513:'e10',537:'e51',547:'e53',552:'e54',560:'e55',583:'e69',599:'e60',606:'e61',614:'e20',629:'e45',637:'e9',654:'e23',670:'e11',679:'e64',684:'e14',694:'e22',698:'e42',705:'e49',714:'e66'}.items():F(w,prepositional_object_id=e)
a.words[74].pop('prepositional_object_id',None);a.words[160].pop('prepositional_object_id',None) # job and room are not the person/towels.
F(157,indirect_object_id='e24',event_beneficiary=B(157,'e24',{'actor_id':'e1','beneficiary':'e24','event_id':'ev158'}))
F(619,reference_metonymic_link={'literal_id':'e63','related_id':'e2','relation':'eyes_realize_person_looking'},event_effector=B(619,'e2',{'effector_id':'e63','event_id':'ev620'}))
F(432,gerund_function='clausal_subject');F(434,clausal_subject_id=a.anchor(432),clausal_object_id=a.anchor(435))
F(163,lexical_gloss='came first indicates task order, not locomotion by socks')
F(105,lexical_gloss='reach the pharmacy while open; no grabbing of the building')
F(355,note='Prop’s is prop is here, a contraction rather than a genitive.')
F([355,351,408,443,634,426,62],clitic_type='contracted_auxiliary')

# Physical states and parts use correlated entity/scope bundles.
for w,e,color in [(14,'e5','dark'),(46,'e13','green'),(116,'e21','yellow'),(122,'e22','blue'),(205,'e14','white'),(208,'e31','blue'),(265,'e22','blue'),(471,'e14','white'),(484,'e68','blue'),(651,'e21','yellow'),(686,'e14','white'),(689,'e31','blue'),(696,'e22','blue')]:F(w,appearance_color=B(w,e,color,factuality='asserted'))
for w,p,whole in [(38,'e11','e2'),(41,'e12','e2'),(140,'e23','e1'),(184,'e29','e15'),(191,'e30','e15'),(197,'e27','e28'),(209,'e31','e14'),(221,'e32','e1'),(238,'e33','e14'),(240,'e34','e14'),(246,'e35','e9'),(350,'e40','e3'),(376,'e41','e14'),(413,'e45','e42'),(476,'e46','e14'),(501,'e47','e14'),(531,'e50','e1'),(549,'e53','e1'),(555,'e54','e42'),(586,'e69','e28'),(618,'e63','e2'),(673,'e11','e2')]:F(w,part_whole_relation={'part_id':p,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
for w,e,material in [(248,'e36','wood'),(422,'e42','wood'),(612,'e62','paper')]:F(w,material_composition=B(w,e,material))
F(251,object_shape=B(251,'e36','forked'))
F(18,object_integrity=B(18,'e7','bruised'),note='Bruising is explicitly on the comparison plums, not a physical cloud injury.')
F(43,object_attachment=B(43,'e13',{'attached_to':'e12','mode':'wrapped'}),evidence=[39,41,43,46,47],note='Brace and support are explicit; diagnosis, cause and duration are not supplied.')
F(328,object_cleanliness=B(328,'e15','clean',factuality='hypothetical'))
F(333,object_moisture=B(333,'e37','muddy',factuality='hypothetical'))
F(201,object_shape=B(201,'e14','folded'));F(213,object_shape=B(213,'e14','unfolded'))
F(284,object_tension_state=B(284,'e9','sagging'));F(473,object_shape=B(473,'e14','sagging_at_middle'))
F(298,object_tension_state=B(298,'e14','tight',factuality='hypothetical'))
F(392,object_fill_state=B(392,'e10',{'state':'empty','domain':'washing_before_reloading'}))
F(622,object_fill_state=B(622,'e10',{'state':'empty','domain':'washing_after_hanging'}))
F(601,object_temperature=B(601,'e60','warm'))
F(532,attributes=[{'name':'bodily_sensation','value':'hair prickles with cold; no emotion or diagnosis inferred'}])
F(578,attributes=[{'name':'surface_pattern','value':'striped shirt'}])
F(692,object_shape=B(692,'e31','straight'))
for w,e,landmark,relation in [(7,'e5','e6','over'),(26,'e2','e9','beside'),(135,'e21','e23','over'),(152,'e24','e9','at_far_end'),(200,'e14','e10','inside'),(218,'e14','e32','above'),(243,'e9','e35','dipped_at'),(257,'e36','e37','across'),(267,'e22','e21','inside'),(291,'e24','e9','close_to_sheet_work_area'),(330,'e15','e37','into'),(340,'e3','e19','from_behind'),(347,'e39','e40','in_hand'),(387,'e70','e10','inside'),(394,'e70','e37','off_ground'),(410,'e44','e45','under'),(416,'e43','e42','inside'),(447,'e10','e42','beneath'),(464,'e14','e44','over'),(545,'e51','e53','from'),(551,'e51','e54','toward'),(558,'e51','e55','against'),(570,'e51','e56','beside'),(597,'e17','e42','inside'),(628,'e14','e45','beneath'),(649,'e21','e23','off'),(713,'e65','e66','beside')]:
 F(w,spatial_configuration=B(w,e,{'landmark':landmark,'relation':relation},factuality=a.words[w].get('factuality','asserted')))
F(570,spatial_configuration=B(570,'e51',{'landmarks':['e56','e57'],'relation':'between'}))
F(254,spatial_support=B(254,'e9',{'supported_by':'e36'}))
F(693,spatial_support=B(693,'e31',{'supported_by':'e22','via':'e44'}))
F(227,spatial_occlusion=B(227,'e1',{'observer':'e1','occluder':'e14','blocked_domain':'anything_beyond_cloth'}),negation_scope_id='p12',quantifier_domain_restriction={'excluded_visible_exception':'e14','domain':'things_in_view'})
F(376,identity_hypothesis={'mention':376,'candidates':['e33','e34'],'scope_id':'s0','assertion_status':'candidate','exhaustive':False},note='Osei takes a sheet corner; which previously caught corner is not specified.')
for w,e,other in [(712,'e65','e66'),(716,'e66','e65')]:
 F(w,identity_hypothesis={'entity_id':e,'candidates':['e51','e56'],'distinct_from':other,'same_pair':True,'scope_id':'s0','assertion_status':'candidate'},note='Closing one tiny sock may be either member of the established pair; this provisional reference does not add a third sock.')
F(18,figurative_mapping={'target_id':'e5','source_image':'bruised plums in Bell tree','kind':'simile','literal_event':False})
F(61,figurative_mapping={'target_id':'e14','source_image':'winning a contest against Bell','kind':'personification','literal_event':False})
F(218,figurative_mapping={'target_id':'e14','source_image':'inflating balloon','kind':'metaphor','literal_event':False})
F(702,figurative_mapping={'target_id':'e58','source_image':'stitching silver lines','kind':'metaphor','literal_event':False})

# Bounded ownership, loans and completed handoffs.
F(23,possession_owner=B(23,'e8',{'owner':'e2'}));F(151,possession_owner=B(151,'e24',{'owner':'e3'}));F(181,possession_owner=B(181,'e15',{'owner':'e2'}))
F(113,transfer_kind=B(113,'e21',{'kind':'loan'}),transfer_source=B(113,'e21',{'source':'e2'}),transfer_recipient=B(113,'e21',{'recipient':'e1'}),transfer_completion=B(113,'e21',{'completed':True,'event_id':'ev114'}),possession_lender=B(113,'e21',{'lender':'e2'}),possession_borrower=B(113,'e21',{'borrower':'e1'}))
F(135,possession_holder=B(135,'e21',{'holder':'e1'}))
F(368,attributes=[{'name':'placement','value':'trowel put down; surface and subsequent custody unspecified'}])
F(508,transfer_source=B(508,'e70',{'source':'e3'}),transfer_recipient=B(508,'e70',{'recipient':'e1'}),transfer_completion=B(508,'e70',{'completed':True,'event_id':'ev509'}))
F(558,possession_holder=B(558,'e51',{'holder':'e3'}))
F(566,transfer_kind=B(566,'e51',{'kind':'return'}),transfer_source=B(566,'e51',{'source':'e3'}),transfer_recipient=B(566,'e51',{'recipient':'e1'}),transfer_completion=B(566,'e51',{'completed':True,'event_id':'ev567'}))
F(663,transfer_kind=B(663,'e21',{'kind':'return'}),transfer_source=B(663,'e21',{'source':'e1'}),transfer_recipient=B(663,'e21',{'recipient':'e2'}),transfer_completion=B(663,'e21',{'completed':True,'event_id':'ev664'}),possession_holder=B(663,'e21',{'holder':'e2'}),evidence=[649,653,661,662,663,665],note='This returns the bag. Blue pegs remain on the sheet; the bag is not asserted to contain all equipment.')
F(697,possession_user=B(697,'e22',{'use':'holding_sheet_border','current_support':'e44'}))

# Modal, goal and belief contents preserve polarity and holder scope.
F(49,modal_base={'holder':'e2','kind':'ability','content_id':'p1'},modal_scope_id='p1')
F(63,intention_holder_id='e1',intention_content_id='p3',intention_publicity='communicated',plan_commitment_status='adopted',offer_content_id='p3')
F(68,goal_owner_id='e1',goal_content_id='p4',goal_status='desired',goal_polarity='achieve',goal_success_condition='p4')
F(72,trust_holder_id='e2',trust_target_id='e1',trust_domain='important_job',social_relation_status='desired_by_Tessa',social_scope_bundle={'holder_id':'e2','scope_id':'s1','factuality':'desired','assertion_status':'asserted'})
F(82,permission_grantor_id='e2',permission_recipient_id='e1',permission_content_id='ev85',permission_status='granted_past',narrative_order_mode='earlier_gardening_episode')
F(95,negation_scope_id='p5',negation_marker_form='not',polarity='negative');F(97,negation_scope_id='p5',goal_owner_id='e1',goal_content_id='p5',goal_polarity='avoid',goal_status='preventive_care')
F(103,goal_owner_id='e2',goal_content_id='p6',goal_status='expressed_need',goal_polarity='achieve',goal_deadline={'before_event_id':'ev111','absolute_time_unknown':True})
F(100,verb_phrase_ellipsis=True,modal_base={'holder':'e2','kind':'polite_request_confirmation','content_id':'p3'},question_requested_slot='Tessa_accepts_hanging_sheet',request_action_id='p3',dialogue_response_to_id='ev66')
F(119,permission_grantor_id='e2',permission_recipient_id='e1',permission_content_id='p8',permission_status='granted',request_action_id='p8')
F(126,request_action_id='p9',speaker_id='e2',addressee_ids=['e1'])
F(124,affordance_fastening=B(124,'e22',{'target':'e14','comparative_grip':'best','scope':'Bell_report'}))
F(188,negation_scope_id='p11',modal_base={'holder':'e1','kind':'preventive_purpose','content_id':'p11'})
F(189,goal_owner_id='e1',goal_content_id='p11',goal_polarity='avoid',goal_status='preventive_purpose')
F(231,request_action_id='p13',figurative_mapping={'target_id':'e14','source_image':'obedient addressee','kind':'personification','literal_event':False})
F(271,modal_base={'holder':'e1','kind':'available_option','content_id':'p14'},modal_scope_id='p14')
F(293,scope_operator='conditional',conditional_antecedent_id='p15',conditional_consequent_id='p17')
F(300,modal_base={'holder':'e1','kind':'epistemic_possibility','content_id':'p16'},modal_scope_id='p16')
F(308,belief_holder_id='e1',belief_content_id='p20',epistemic_attitude_kind='considered_ease',belief_polarity='accepts')
F(311,imaginer_id='e1',imagined_content_id='p18',imagined_world_id='world_feigned_nonnotice',plan_commitment_status='considered_not_adopted')
F(313,negation_scope_id='p19',negation_marker_form='not',proposition_polarity='negative')
F(314,belief_holder_id='e1',belief_content_id='p23',epistemic_attitude_kind='feigned_unawareness',note='This is the content of contemplated pretense, not actual narrator-supported unawareness.')
F(320,modal_base={'holder':'e1','kind':'expectation','content_id':'p21'})
F(326,imaginer_id='e1',imagined_content_id='p22',imagined_world_id='world_muddy_laundry_risk')
F(357,modal_base={'holder':'e1','kind':'polite_request','requested_actor_id':'e3','content_id':'p25'},request_action_id='p25')
F(400,permission_grantor_id='e3',permission_recipient_id='e1',permission_content_id='p28',permission_status='granted',modal_base={'holder':'e3','kind':'permission','content_id':'p28'})
F(427,goal_owner_id='e1',goal_content_id='p30',goal_status='hoped_earlier',goal_polarity='achieve',narrative_order_mode='earlier_hope')
F(429,negation_scope_id='p31',modal_base={'holder':'e1','kind':'hoped_future_nonneed','content_id':'p31'},proposition_polarity='negative')
F(434,proposition_id='p47',necessary_condition={'condition':'p46','for':'p28','domain':'rehanging_washing_under_shelter'},note='Starting over means rehanging this washing, not repeating the washing process.')
F(437,modal_base={'holder':'e1','kind':'permission_question','content_id':'p28'},verb_phrase_ellipsis=True,question_requested_slot='permission_to_use_shelter',question_answer_status='answered',dialogue_response_to_id='ev408')
F(441,permission_grantor_id='e3',permission_recipient_id='e1',permission_content_id='p28',permission_status='confirmed',dialogue_response_to_id='ev441',dialogue_turn_function='permission_answer')
F(445,quantifier_domain_restriction={'domain':'garden_shelter_users'})
F(477,request_action_id='p34',dialogue_turn_function='request_more_fasteners')
F(633,belief_holder_id='e2',belief_content_id='p37',belief_polarity='accepts',epistemic_attitude_kind='prior_expectation',epistemic_time_scope={'phase':'before_return_and_inspection'},belief_error_status='current_location_contradicted_by_sheltered_washing',note='Earlier belief is preserved; this does not assert a persisting belief after seeing the sheltered sheet.')
F(657,discourse_relation_kind='explanation',discourse_explanation_target='ev901',supporting_event_ids=['ev258'])
F(674,appraisal_goal_congruence='positive_evaluation_of_relocation',viewpoint_evaluative_stance={'holder_id':'e2','target_event_id':'ev901','evaluation':'good_thinking','assertion_status':'attributed_claim'})
F(678,negation_scope_id='p40',proposition_polarity='negative',explicit_zero_count={'domain':'washing_in_mud','count':0,'scope_id':'q18','assertion_status':'attributed_claim'},quantifier_domain_restriction={'domain':'relevant_washing','does_not_mean':'no_objects_exist_in_mud'})
# Quantities, time and physical mechanisms use only stated units and participants.
F(1,cardinal_value=4,time_expression_id='time_opening',temporal_granularity='hour',event_time_interval={'hour':4,'meridiem':'unspecified','date':'unspecified'})
F(2,time_expression_id='time_opening')
F(37,cardinal_value=1,counted_domain={'kind':'hand','owner_id':'e2','action_id':'ev34'})
F(40,reference_excluded_ids=['e11'],note='Other wrist is on the other side from the usable lifting hand; no left/right side is specified.')
F(81,temporal_frequency_class='single_prior_occasion',narrative_order_mode='earlier_gardening_episode')
F(108,temporal_signal_relation='before',temporal_deadline={'event_id':'ev106','before_event':'ev111','clock_unknown':True})
for w in [127,483]:F(w,cardinal_value=2,counted_domain={'kind':'blue_peg','per_corner_variable':'e67','whole':'e14'},referent_kind='bound_variable')
for w in [129,487]:F(w,quantity_distribution_cue='per_individual',quantifier_binding={'quantifier':'each','variable_id':'e67','restriction':{'corner_of':'e14'},'scope':'two_pegs_per_corner'})
for w in [130,488]:F(w,referent_kind='bound_variable',generic_reference=False)
F(125,adverb_degree='superlative')
F(159,quantity_approximation_cue='plenty',counted_domain={'kind':'available_hanging_space','reserved_for':'e24','unit_unspecified':True})
F(162,temporal_order_cue='first');F(525,ordinal_rank=1)
for w in [176,239,496,624]:F(w,temporal_order_cue='then')
F(237,cardinal_value=1);F(240,nominal_ellipsis_license='another_sheet_corner')
F(224,temporal_duration={'event_id':'ev228','value':'brief_moment','exact_duration_unknown':True})
F(216,temporal_bound_cue='immediate_at_once')
F(323,temporal_deixis='soon',time_anchor_id='ev309',temporal_uncertainty={'duration':'unspecified_short_interval','content_id':'p21'})
for w in [362,458]:F(w,temporal_signal_relation='while')
F(458,temporal_overlap={'events':['ev456','ev461'],'scope_id':'s0'})
F(539,ordinal_rank=1,attributes=[{'name':'relative_order','value':'last remaining little sock to hang; total sock count unspecified'}]);a.words[539].pop('ordinal_rank',None)
F(710,cardinal_value=1,counted_domain={'kind':'sock','domain':'closing_pair','exact_member_unresolved':True})
for w,e,src,dst in [(447,'e10',None,'e42'),(545,'e51','e53',None),(566,'e51','e3','e1')]:
 if src:F(w,motion_source=B(w,e,{'landmark_id':src,'event_id':a.words[w]['event_id'],'role':'source'}))
 if dst:F(w,motion_destination=B(w,e,{'landmark_id':dst,'event_id':a.words[w]['event_id'],'role':'destination'}))
F(551,motion_trajectory_phase=B(551,'e51',{'landmark_id':'e54','event_id':'ev552','phase':'approaching','arrival_unestablished':True}))
F(340,motion_source=B(340,'e3',{'landmark_id':'e19','region':'behind','event_id':'ev341','role':'source'}))
F(605,motion_waypoint=B(605,'e2',{'landmark_id':'e61','event_id':'ev606','role':'through_route'}))
F(194,event_causer=B(194,'e27',{'causer':'e26','event_id':'ev195'}))
F(545,event_causer=B(545,'e51',{'causer':'e52','event_id':'ev546'}),motion_control=B(545,'e51',{'kind':'externally_driven','force_source':'e52'}))
F(527,event_causer=B(527,'e49',{'causer':'e48','event_id':'ev528'}))
F(588,event_causer=B(588,'e59',{'causer':'e58','event_id':'ev589'}))
F(667,event_effector=B(667,'e2',{'effector_id':'e11','event_id':'ev668'}))
F(558,spatial_contact=B(558,'e51',{'touches':'e55','event_id':'ev559'}))
F(545,causal_effect=B(545,'e51',{'effect_event_id':'ev552','cause_event_id':'ev546'}),evidence=[544,545,546,547,549,550,551])
F(532,causal_parent=B(532,'e50',{'cause':'explicit_cold','effect_event_id':'ev533'}),evidence=[531,532,533,534])
F(447,event_collective_participants=B(447,'e4',{'members':['e1','e3'],'event_id':'ev448'}))
F(508,event_divided_labor=B(508,'e4',{'shared_episode_id':'ev901','subtasks':[{'actor_id':'e3','event_id':'ev509','action':'pass_clothes'},{'actor_id':'e1','event_id':'ev519','action':'hang_clothes'}]}))
F(659,causal_parent=B(659,'e17',{'cause_event_id':'ev258','effect_event_id':'ev901','claimed_by':'e1'}),causal_scope=B(659,'e17',{'holder':'e1','scope_id':'q17','factuality':'reported'}),evidence=[643,644,645,657,658,659,660])
F(464,plan_revision={'holder_id':'e1','old_location':'e9','new_location':'e44','action':'hang_washing','evidence_events':['ev379','ev448','ev465']},narrative_change_dimension='washing_location_and_support_plan')
F(570,narrative_resolution_evidence={'problem_event_id':'ev546','status':'sock_caught_and_pegged','evidence_events':['ev559','ev567','ev571']})
F(663,narrative_resolution_evidence={'loan_event_id':'ev114','returned_entity_id':'e21','status':'bag_returned','excludes_claim':'all_pegs_returned_to_bag'})
F(691,narrative_motif_link={'earlier_event_id':'ev474','later_event_id':'ev692','relation':'sagging_sheet_to_straight_supported_border','assertion_status':'candidate'})
F(713,narrative_closure_candidate={'evidence':['washing_sheltered','sock_recovered_and_hung','bag_returned','paired_sock_final_image'],'assertion_status':'candidate'})
F(455,evidence_missing={'needed':'continuous_sheet_transport_trace_between_outdoor_line_and_shelter','observed':'Osei holds sheet at both stages'})
feedback={
'summary':'Retrospective annotation of Tessa’s washing task, unsafe outdoor support, considered evasion, requested cooperation, sheltered rehanging, sock recovery and peg-bag return.',
'reviewed_all_words':True,'reviewed_paragraphs':list(range(32)),
'ambiguities':[
 {'words':[38,41,47,673],'issue':'A brace and a good usable hand are explicit; injury type, diagnosis, left/right side, pain and recovery are not specified.'},
 {'words':[249,257,317,356,645],'issue':'Skidding/slipping/sliding descriptions are linked to the same prop episode. The prop’s final support state or repair is not narrated.'},
 {'words':[291,301,302,330,334],'issue':'Whole washing falling and becoming muddy is a risk or imagined outcome, not an actual event. Osei’s tea towels are nearby but their later relocation is not narrated.'},
 {'words':[304,308,311,313,314],'issue':'Pretending not to notice is contemplated but not chosen. Scoped false non-noticing must not become narrator-supported unawareness or actual deception.'},
 {'words':[373,376,447,455],'issue':'Osei holds a sheet corner and later the sheet under the shelter; precise corner identity and continuous sheet transport are not narrated. No extra transport/handoff is invented.'},
 {'words':[127,129,130,483,487,488,501,502],'issue':'Two pegs per corner does not specify the total corners clipped or every extra edge peg. No total of eight or inventory subtraction is invented.'},
 {'words':[518,539,541,570],'issue':'Filling the rest of the line is a summary/process preceding the last-sock incident; the final sock is pegged only after recovery.'},
 {'words':[541,575,712,716],'issue':'Closing one tiny sock beside its pair may denote either known member. Provisional closing references are constrained to the established pair, not counted as new socks.'},
 {'words':[663,665,693,697],'issue':'The peg bag is returned while blue pegs visibly remain holding the sheet. Bag contents and return of all pegs are not asserted.'},
 {'words':[1,2,107,110,605,616],'issue':'Four o’clock has no stated meridiem/date. The pharmacy bag and return support a pharmacy origin, but the visit transaction and a precise closing time are unreported.'},
],
'feature_gaps':[
 {'meaning':'Distributed fasteners per object corner','resolution':'Existing quantifier_binding/count fields with bound-variable corner and peg-pair referents suffice. No new field proposed.'},
 {'meaning':'Unresolved paired-object reference without increasing object count','resolution':'Existing identity_hypothesis carries candidate identity and distinct-other-member constraints; the entity registry marks provisional references as not new physical objects.'},
],
'prompt_feedback':[
 'Separate a negative belief inside an unchosen pretense from actual unawareness; scope and factuality must remain correlated.',
 'A multi-predicate recollection such as the shirts and socks she had hung can refer to an explicit episode with component event IDs instead of inventing another action.',
 'Distinguish a completed bag return from returning every tool normally stored in it, especially when the final image shows tools still in use.',
 'Task-order came first and rain stitched are not literal locomotion or sewing. Interpret the selected sense before assigning a physical event kind.',
],
'coverage_notes':'All 717 words have manually selected contextual POS and lemma choices. All 1,024 feature definitions, overrides, v3 extension registry and three frozen example bundles were read. Sparse fields preserve whole-story retrospective reference resolution with local time/scope. Shape validation is separate from semantic paragraph review.'
}
a.save(feedback)
