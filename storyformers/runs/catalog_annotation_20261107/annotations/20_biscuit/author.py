"""Manually authored retrospective biscuit annotations; frozen prompt v3."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a=Annotation('20_biscuit',prompt_version='v3');F=a.feature
TAGS=[
'adp num adv det n n v adj adv part v det n adp det n n v n n n v n conj n v adp det n v n adp det n adp det n adp det n n conj det adj n n v n adp det n conj n n adp det n',
'adj adp det n n v v adv det n v pron v v pron',
'adv v det n det n det n conj det n adp num adj n n v det n n v det n',
'pron v pron adp n n n v pron pron v adj n',
'pron v n v n det n pron adp n',
'n n v v det n n num n adv pron v adv adp det n adp det n conj n conj n v det n adp det n n n v v adj n det det n adp det n v det adj n adv adp det n pron v n adv v adp det n',
'n v v part v det n pron n conj n conj n v part v pron pron pron v n n conj n v v pron det adj adj n adp det adj n',
'n v det n adj n v n v adv adv conj n n v adp det n pron v det n adp n conj det n adp n adv v det n conj v pron adv',
'det n n v n v adp det n det n v adv adv pron v num n adv pron v det n adp n',
'n v adp det n v adp det n num n adv adv adj adv n n pron v adj adp num adj n',
'pron v num adj n pron v adv det n v v adj',
'n v det n adp det n pron v det n n n v n',
'pron adv v num n',
'conj part pron adp n',
'pron v v pron conj pron v v adp det n n v',
'n v det n adp det n n n v det adj n det n v adv v adp det adj n',
'pron v adp det num adj n',
'adv pron part adv adj adv adp det pron n v',
'n n v adj pron v v part v det adj n',
'adp det n n v',
'n v v n v v conj det n v adp det n n v adv det n n det pron v adp det n',
'det n v adv',
'n v adv det adj n pron v det adj n adv adp n adj n adv v det n adp n pron v adv v pron',
'det n n v',
'det n n v conj pron v v',
'n n v pron v det n n conj n v pron adv adv pron v det n n adp det n n',
'v v det det n adv n v',
'pron v',
'pron v adv v det n v n adp det n n v n adp det adj n adv pron v det adj v n adp det n pron v adv n adp pron adp det n conj det n',
'det n v adp det n adp num n part v conj det n v n v n n conj n v det pron adv adp det n n conj det n v n v det n n adp det n det n v adp det adj n adp n conj n',
'pron v det adj n adp det adj n v det n adp det n adp adv adv pron v pron adv adv',
'n n v det n adp det adj n v adp det n n v adp det n conj v adv adv det adj n n v',
'adp pron pron v v det n',
'conj adp n n v',
'n v adp det adj n pron det n conj det n v adp det n',
'n n v adv pron v det n pron v adv v det n conj pron v det n adv',
'pron v det n adp det n n conj v det adj n det n n v det adj n n v adp det n adj adp det adj n',
]
LEM={'Mom':'Mom','Dad':'Dad','Grandma':'Grandma','Grandma’s':'Grandma','Mara':'Mara','Toby':'Toby','Toby’s':'Toby','Mr':'Mr','Alvarez':'Alvarez','Pepper':'Pepper','I':'I',
'was':'be','spoons':'spoon','stirred':'stir','peeled':'peel','potatoes':'potato','sat':'sit','shelling':'shell','peas':'pea','had':'have','sleeves':'sleeve','fingernails':'fingernail','cutters':'cutter','said':'say','sliding':'slide','them':'they','don’t':'do','were':'be','chose':'choose','grabbed':'grab','We’re':'we','making':'make','tugged':'tug','reached':'reach','things':'thing','reminded':'remind','him':'he','likes':'like','one’s':'one','found':'find','nights':'night','She’d':'she','wriggled':'wriggle','searched':'search','parents':'parent','followed':'follow','pawprints':'pawprint','holding':'hold','He’d':'he','brought':'bring','wrapped':'wrap','offered':'offer','wanted':'want','They’d':'they','borrowed':'borrow','given':'give','biscuits':'biscuit','rolled':'roll','sprinkled':'sprinkle','sneezing':'sneeze','jumped':'jump','cut':'cut','stars':'star','dogs':'dog','gathered':'gather','scraps':'scrap','chimed':'chime','glanced':'glance','goes':'go','needs':'need','minutes':'minute','looked':'look','left':'leave','Toby’s':'Toby','will':'will','caught':'catch','stretched':'stretch','pieces':'piece','stared':'stare','it’s':'it','ears':'ear','went':'go','trying':'try','stopped':'stop','peeling':'peel','kept':'keep','stirring':'stir','eyes':'eye','moved':'move','children':'child','ticked':'tick','picked':'pick','pressed':'press','edges':'edge','torn':'tear','dusted':'dust','asked':'ask','face':'face','brightened':'brighten','guided':'guide','held':'hold','dog’s':'dog','Don’t':'do','leaving':'leave','shaped':'shape','grooves':'groove','lifted':'lift','baked':'bake','washed':'wash','dried':'dry','rang':'ring','slid':'slide','filled':'fill','tucked':'tuck','laying':'lay','carried':'carry','opened':'open','clipped':'clip','squeezed':'squeeze','legs':'leg','wagged':'wag','wobbled':'wobble','me':'I','taking':'take','pointed':'point','That’s':'that','is':'be','laughed':'laugh','could':'can','didn’t':'do','has':'have','larger':'large','smaller':'small','best':'good'}
for p,t in enumerate(TAGS):a.tag(p,t,LEM)
for key in ['appearance_color','part_whole_relation','figurative_mapping']:a.use_extension(key)
ENTITIES=[
('e1','Mara','person',[40,42,87,101,138,185,210,272,296,301,345,355,385,402,433,439,466,481,501,516,560,659]),
('e2','Toby','person',[44,45,91,103,112,140,187,215,287,309,311,347,387,391,400,446,462,469,472,475,486,503,505,565,657]),
('e3','Mom','person',[16,175,198,251,266,407,411,578]),('e4','Dad','person',[20,404]),('e5','Grandma','person',[24,59,61,65,195,222,417,420,562]),
('e6','Mr. Alvarez','person',[99,100,104,108,118,119,147,148,160,167,173,320,321,324,334,620,621,626,631,636,648,649,673,675,676,679,683,690,695]),
('e7','Pepper the terrier','dog',[110,117,123,124,128,132,169,323,333,337,339,633,642,656]),
('e8','Mara and Toby','person_group',[49,55,95,122,145,192,193,201,228,256,316,369,416,455,524,597,615]),
('e9','Mom and Dad','person_group',[146]),('e10','family kitchen','kitchen',[5,248,587]),('e11','spoons','spoon_group',[12,14]),('e12','spoon jar','jar',[15]),
('e13','tomato sauce','food',[19]),('e14','potatoes','potato_group',[22]),('e15','kitchen table','table',[28]),('e16','Grandma peas','pea_group',[30,223,226]),('e17','pea bowl','bowl',[33,227]),('e18','counter','counter',[39]),('e19','baking flour','flour',[217,454]),('e20','children sleeves','clothing_part_group',[50]),('e21','biscuit dough batch','dough',[213]),('e22','children fingernails','body_part_group',[56]),
('e23','Grandma cookie cutters','cutter_group',[60,68,71,196,563]),('e24','Grandma cutter tin','tin',[66]),('e25','star cutter','cutter',[75,90,490]),('e26','rabbit cutter','cutter',[77]),('e27','flower cutter','cutter',[79]),('e28','dog cutter','cutter',[82,94,354,479,483]),('e29','floppy ear on dog cutter shape','represented_part',[86]),
('e30','thank-you biscuits batch','biscuit_group',[97,209,558,601]),('e31','dog-shaped biscuits before final one','biscuit_group',[114,115,238,328]),('e32','Pepper collar','collar',[133]),('e33','earlier thunderstorm','storm',[136]),('e34','neighborhood block','place',[143]),('e35','muddy pawprints','trace_group',[152,688]),('e36','laundromat','place',[158]),('e37','Alvarez yellow flashlight','flashlight',[162,628,674,693]),('e38','ground on rescue route','ground_region',[166]),('e39','children home','home',[170]),('e40','Alvarez raincoat','raincoat',[174]),
('e41','offered thank-you cake','prospective_cake',[183]),('e42','blue biscuit tin','tin',[205,305,605,617,653,698]),('e43','row of star biscuits','biscuit_group',[233]),('e44','dough scraps','dough_portions',[242,245]),('e45','kitchen timer','timer',[249,430,576]),('e46','oven','oven',[255,269,550,585]),('e47','biscuit tray','baking_tray',[257,261,532,546]),('e48','family supper','meal',[271]),('e49','dough board','board',[280,452]),
('e50','last dough lump, later torn and recombined','dough_portion',[276,282,289,315,350,361,377,428,515,724]),('e51','Toby fist','body_part',[288]),('e52','proposed last star biscuit','prospective_biscuit',[295,300,461]),('e53','proposed additional dog biscuit','prospective_biscuit',[319,465]),('e54','Toby hand over dough','body_part',[312]),('e55','other side of dough lump','dough_region',[359]),('e56','two uneven dough pieces','dough_portions',[375]),('e57','Toby ears','body_part_group',[388]),('e58','best piece in Toby explanation','dough_portion_reference',[398]),('e59','Toby proposed dog idea','plan_reference',[401]),('e60','Mom eyes','body_part_group',[412]),('e61','Grandma pea pod','pea_pod',[422]),
('e62','larger torn dough piece','dough_portion',[438]),('e63','smaller torn dough piece held by Toby','dough_portion',[448]),('e64','torn dough edges','dough_region',[443]),('e65','Toby face','body_part',[473]),('e66','final combined dog biscuit with star impression','biscuit',[459,493,529,538,608,664,665,667,707,718]),('e67','back region of final dog biscuit','biscuit_region',[494,719]),('e68','star impression with sugar','biscuit_decoration',[512,611,670,715]),('e69','decoration sugar','sugar',[518,714]),('e70','grooves of star impression','biscuit_region',[522]),('e71','star biscuit beside final biscuit on tray','biscuit',[541]),('e72','rabbit biscuit beside final biscuit','biscuit',[544]),('e73','dish towel','towel',[573]),('e74','supper dish','dish',[582]),('e75','warm baking smell','smell',[592]),('e76','butter','food_material',[594]),('e77','Alvarez home next door','home',[619]),('e78','Alvarez door','door',[624]),('e79','Alvarez belt','clothing_part',[632]),('e80','Alvarez legs','body_part_group',[637]),('e81','Pepper back end','body_part',[645]),('e82','hallway table','table',[702]),('e83','porch illumination','light',[710]),
('e86','dough residue under children fingernails','dough_portion',[53]),('e87','flour residue on children sleeves','flour_portion',[47]),('e88','each cutter being dried','cutter_variable',[568]),('e89','sugar associated with baking smell','food_material',[596]),
]
for args in ENTITIES:a.entity(*args)
a.entities['e8']['member_ids']=['e1','e2'];a.entities['e9']['member_ids']=['e3','e4'];a.entities['e23']['member_ids']=['e25','e26','e27','e28'];a.entities['e56']['member_ids']=['e62','e63']
a.entities['e66']['material_continuity_from']='e50';a.entities['e66']['realizes_proposal_id']='e53';a.entities['e52']['status']='desired_not_selected';a.entities['e41']['status']='offered_not_made'
a.entities['e58'].update(identity_candidates=['e62','e63'],identity_candidates_exhaustive=False,counts_as_new_object=False)
a.entities['e86']['subset_of']='e21';a.entities['e87']['subset_of']='e19';a.entities['e88'].update(domain_id='e23',counts_as_new_object=False)
a.entities['e71']['subset_of']='e43'
for eid in ['e31','e43','e66','e72']:a.entities[eid]['subset_of']='e30'
a.entities['e50']['subset_of']='e21'
QUOTES=[
('q1',range(57,61),'e5','e8',62),('q2',range(67,72),'e5','e8',67),('q3',range(95,101),'e1','e2',102),('q4',range(104,108),'e1','e2',102),('q5',range(108,111),'e2','e1',111),('q6',range(113,118),'e2','e1',113),
('q7',range(256,272),'e3','e8',256),('q8',range(296,301),'e1','e2',302),('q9',range(303,309),'e1','e2',303),('q10',range(316,324),'e2','e1',316),('q11',range(324,329),'e1','e2',324),('q12',range(329,334),'e2','e1',329),('q13',range(334,345),'e1','e2',346),('q14',range(376,385),'e1','e2',386),('q15',range(391,399),'e2','e1',391),('q16',range(399,402),'e1','e2',403),
('q17',range(455,460),'e1','e2',455),('q18',range(460,462),'e2','e1',463),('q19',range(464,466),'e1','e2',467),('q20',range(468,472),'e1','e2',467),('q21',range(495,501),'e1','e2',502),('q22',range(503,505),'e2','e1',503),('q23',range(647,649),'e6','e8',650),('q24',range(654,657),'e2','e6',658),('q25',range(665,675),'e1','e6',665),('q26',range(679,695),'e6','e8',679),
]
for sid,ws,h,rec,tr in QUOTES:
 ws=list(ws);a.scope(sid,ws,kind='quotation',holder_id=h,description='Direct speech, local truth and operators retained.');uid=f'ev{1000+tr}' if tr in ws else f'ev{tr+1}';a.scopes[sid].update(utterance_event_id=uid,addressee_ids=[rec]);F(ws[0],utterance_id=uid,addressee_ids=[rec],communication_channel='speech',quote_mode='direct')
for sid,ws,kind,parent,h,desc in [
('s1',range(69,72),'prohibited_bending','q2','e5','Bending cutters is forbidden, not reported actual.'),('s2',range(118,175),'earlier_rescue','s0',None,'Two nights earlier, including an earlier escape nested in the rescue sequence.'),('s3',range(178,184),'offered_cake','s0','e3','Mom offers a cake, without an actual cake-making event.'),('s4',range(189,193),'desired_child_thanks','s0','e8','Children want to make the thank-you gift themselves, not necessarily Mom’s cake.'),
('s5',range(256,261),'scheduled_tray_entry','q7','e3','Mom instructs immediate oven entry; actual entry occurs later.'),('s6',range(298,301),'desired_star','q8','e1','Desired additional star biscuit.'),('s7',range(303,309),'expected_tin_appearance','q9','e1','Mara prediction under selecting star.'),('s8',range(318,320),'desired_dog','q10','e2','Toby desired extra dog biscuit.'),('s9',range(394,399),'intended_piece_saving','q15','e2','Toby reports attempted saving, not successful saving.'),('s10',range(455,460),'remaining_ability','q17','e1','Claim of ability to make a biscuit, distinct from later actual work.'),('s11',range(468,472),'permitted_help','q20','e1','Mara permits Toby to help.'),('s12',range(495,501),'prohibited_cut_through','q21','e1','Prohibition of a complete cut-through; later gentle impression is distinct.'),
]:a.scope(sid,ws,kind=kind,parent=parent,holder_id=h,description=desc)
def status(s):
 while s:
  if a.scopes[s]['kind']=='quotation':return 'attributed_claim'
  s=a.scopes[s].get('parent')
 return 'asserted'
def B(w,e,v,**kw):return dict(entity_id=e,scope_id=a.words[w]['scope_id'],assertion_status=status(a.words[w]['scope_id']),value=v,**kw)
def E(w,label,actor=None,patients=(),typ='other',fact='asserted',recipient=None,instruments=()):
 a.event(f'ev{w+1}',w,label,type=typ,actor=actor,patients=patients,factuality=fact,recipient=recipient,instruments=instruments);F(w,assertion_status=status(a.words[w]['scope_id']))
EVENTS=[
(7,'kitchen is loud',None,('e10',),'state'),(10,'kitchen noise rattles spoons',None,('e11',),'move','hypothetical'),(17,'Mom stirs tomato sauce','e3',('e13',)),(21,'Dad peels potatoes','e4',('e14',)),(25,'Grandma sits at table','e5',(),'state'),(29,'Grandma shells peas into bowl','e5',('e16',)),(46,'children have flour on sleeves and dough under fingernails','e8',('e87','e86'),'state'),
(62,'Grandma cautions children about cutters','e5',(),'speak'),(63,'Grandma slides cutter tin to children','e5',('e24',),'transfer','asserted','e8'),(67,'children borrow cutters','e8',('e23',),'obtain','desired'),(70,'children bend cutters','e8',('e23',),'other','negated'),(73,'four shaped cutters are in Grandma tin',None,('e23',),'state'),(88,'Mara chooses star cutter','e1',('e25',)),(92,'Toby takes dog cutter','e2',('e28',),'obtain'),
(96,'children make biscuits for Alvarez','e8',('e30',),'other','reported'),(102,'Mara reminds Toby of gift recipient','e1',(),'speak'),(105,'Alvarez likes neat things','e6',(),'state','reported'),(109,'Alvarez likes Pepper','e6',('e7',),'feel','reported'),(111,'Toby replies about Pepper','e2',(),'speak'),(115,'dog-shaped biscuit is intended for Pepper',None,('e31',),'state','reported'),
(121,'Alvarez finds Pepper','e6',('e7',),'perceive'),(129,'Pepper wriggles out of collar','e7',(),'move'),(141,'children and parents search block','e8',('e34',)),(150,'Alvarez follows muddy pawprints to laundromat','e6',('e35',),'move'),(159,'Alvarez holds flashlight low','e6',('e37',)),(168,'Alvarez brings Pepper home','e6',('e7',),'move'),(171,'Pepper is wrapped in Alvarez raincoat',None,('e7',),'state'),
(177,'Mom offers to make thank-you cake','e3',(),'speak'),(179,'Mom makes a thank-you cake','e3',('e41',),'other','desired'),(188,'children want to make thanks gift themselves','e8',(),'state'),(190,'children make thank-you gift themselves','e8',('e30',),'other','desired'),(194,'children borrow Grandma cutters','e8',('e23',),'obtain'),(200,'Mom gives children empty blue biscuit tin','e3',('e42',),'transfer','asserted','e8'),
(211,'Mara rolls dough smooth','e1',('e21',)),(216,'Toby sprinkles flour','e2',('e19',)),(218,'Toby sneezes strongly','e2',()),(224,'peas jump in bowl',None,('e16',),'move'),(229,'children cut rows of star and dog biscuits','e8',('e43','e31')), (240,'children gather dough scraps','e8',('e44',)),(244,'children roll scraps again','e8',('e44',)),
(250,'kitchen timer chimes',None,('e45',)),(252,'Mom glances at oven','e3',('e46',),'perceive'),(258,'biscuit tray enters oven',None,('e47',),'move','desired'),(262,'tray of biscuits needs eight minutes baking',None,('e30',),'state','reported'),(267,'Mom needs oven for supper','e3',('e46',),'state','reported'),(273,'Mara looks at remaining dough','e1',('e50',),'perceive'),(277,'dough remains on board',None,('e50',),'state'),(291,'remaining lump is enough for one biscuit',None,('e50',),'state'),
(297,'Mara wants one final star','e1',(),'state','reported'),(302,'Mara requests final star','e1',(),'speak'),(307,'biscuit tin looks finished',None,('e42',),'state','hypothetical'),(310,'Toby puts hand over lump','e2',('e54',),'move'),(317,'children need another dog biscuit according to Toby','e8',(),'state','reported'),(326,'four dog biscuits already allocated to Alvarez',None,('e31',),'state','reported'),(341,'Pepper has dog shape',None,('e7',),'state','reported'),(346,'Mara rejects shape as rescue reason','e1',(),'speak'),
(348,'Toby tugs dough toward dog cutter','e2',('e50',),'move'),(356,'Mara catches other side of lump','e1',('e55',)),(362,'lump stretches',None,('e50',),'state'),(364,'lump splits into uneven pieces',None,('e50',)),(370,'children stare at torn pieces','e8',('e56',),'perceive'),(380,'torn portions are large enough for a cutter',None,('e56',),'state','negated'),(386,'Mara says portions are too small','e1',(),'speak'),(390,'Toby ears turn pink',None,('e57',),'state'),(393,'Toby tried to save best piece','e2',(),'other','reported'),(395,'Toby saves best piece','e2',('e58',),'other','desired'),(403,'Mara attributes saving to Toby idea','e1',(),'speak'),
(405,'Dad stops peeling potatoes','e4',('e14',)),(408,'Mom continues stirring sauce','e3',('e13',)),(413,'Mom looks toward children','e3',('e8',),'perceive'),(418,'Grandma puts pea pod down','e5',('e61',),'move'),(425,'someone reaches for dough',None,('e50',),'other','negated'),(431,'timer continues ticking',None,('e45',)),
(434,'Mara picks up larger dough piece','e1',('e62',),'obtain'),(440,'Mara presses torn pieces together','e1',('e62','e63')), (450,'Mara dusts board with flour','e1',('e49',),'other','asserted',None,('e19',)),(458,'children make one remaining biscuit','e8',('e66',),'other','hypothetical'),(463,'Toby asks whether biscuit is star','e2',(),'speak'),(467,'Mara chooses dog and invites help','e1',(),'speak'),(471,'Toby helps make biscuit','e2',('e66',),'other','desired'),
(474,'Toby face brightens',None,('e65',),'state'),(476,'Toby guides dog cutter','e2',('e28',)),(482,'Mara presses dog cutter down','e1',('e28',)),(487,'Toby holds star cutter above dog biscuit back','e2',('e25',)),(496,'Toby cuts all way through biscuit','e2',('e66',),'other','negated'),(502,'Mara warns against cutting through','e1',(),'speak'),(504,'Toby knows not to cut through','e2',(),'state','reported'),
(506,'Toby presses star cutter gently','e2',('e25',)),(508,'Toby leaves a star-shaped impression with star cutter','e2',('e68',),'other','asserted',None,('e25',)),(517,'Mara sprinkles sugar into grooves','e1',('e69',)),(525,'children lift final biscuit onto tray','e8',('e66',),'move'),(534,'tray has just enough room between biscuits',None,('e47',),'state'),
(547,'tray enters oven',None,('e47',),'move'),(559,'biscuits bake',None,('e30',)),(561,'Mara washes Grandma cutters','e1',('e23',)),(566,'Toby dries each cutter','e2',('e23',),'other','asserted',None,('e73',)),(577,'timer rings after baking',None,('e45',)),(579,'Mom slides supper dish into oven','e3',('e74',),'move'),(588,'kitchen fills with warm butter-sugar smell',None,('e10',),'state'),
(598,'children pack cooled biscuits in blue tin','e8',('e30',)),(606,'children lay decorated dog biscuit on top','e8',('e66',),'move'),(616,'children carry biscuit tin next door','e8',('e42',),'move'),(622,'Alvarez opens door','e6',('e78',)),(629,'flashlight is clipped to Alvarez belt',None,('e37',),'state'),(634,'Pepper squeezes past Alvarez legs','e7',(),'move'),(639,'Pepper wags','e7',()),(646,'Pepper back end wobbles',None,('e81',),'move'),
(650,'Alvarez asks if gift is for him','e6',(),'speak'),(651,'Alvarez accepts tin','e6',('e42',),'obtain'),(658,'Toby includes Pepper as beneficiary','e2',(),'speak'),(660,'Mara points to top biscuit','e1',('e66',)),(667,'top biscuit depicts dog',None,('e66',),'state','reported'),(671,'star decoration symbolizes Alvarez flashlight',None,('e68',),'state','reported'),(677,'Alvarez laughs softly','e6',()),(680,'Alvarez remembers rescue night','e6',(),'state','reported'),(686,'Alvarez sees pawprints when light is held close','e6',('e35',),'perceive','reported'),(696,'Alvarez sets tin on hallway table','e6',('e42',),'move'),(704,'Alvarez lifts special biscuit','e6',('e66',),'move'),(711,'porch light illuminates sugar star',None,('e68',),'other'),
]
for args in EVENTS:E(*args)
# Retrospective mentions preserve actual event identities and local reported scope.
for w,origin in [(322,121),(336,121),(691,159),(716,508)]:
 a.mention_event(f'ev{origin+1}',w,role='action',note='Same earlier event or resulting impression, recalled locally rather than repeated.');F(w,assertion_status=status(a.words[w]['scope_id']))
a.mention_event('ev22',406,role='action',note='Peeling whose continuation Dad stops.');a.mention_event('ev18',409,role='action',note='Same ongoing sauce-stirring activity.')
seen=set()
for sid,ws,h,rec,tr in QUOTES:
 uid=a.scopes[sid]['utterance_event_id']
 if uid in seen:continue
 seen.add(uid)
 if uid not in a.events:a.event(uid,tr,'spoken turn',type='speak',actor=h,recipient=rec,scope='s0',primary=False,support=list(ws))
 else:a.events[uid]['recipient_id']=rec;F(tr,recipient_id=rec)
# One explicit collaborative episode for the final shape and decoration.
a.event('ev900',476,'make final dog biscuit with star impression',type='other',actor='e8',patients=['e66'],scope='s0',primary=False,support=[440,476,482,506,508,517,525]);a.events['ev900']['component_event_ids']=['ev441','ev477','ev483','ev507','ev509','ev518','ev526']
PROPS=[
(1,'The children are careful with Grandma’s cutters.',[57,59,60],'q1'),(2,'The children bend the cutters.',[69,70,71],'s1'),(3,'The children may borrow the cutters, but must not bend them.',[67,68,69,70,71],'q2'),(4,'The children are making these biscuits for Mr. Alvarez.',[95,96,97,99,100],'q3'),(5,'Mr. Alvarez likes neat things.',[104,105,106,107],'q4'),(6,'Mr. Alvarez likes Pepper.',[108,109,110],'q5'),(7,'The dog-shaped biscuit is intended for Pepper.',[113,114,115,116,117],'q6'),
(8,'Mom makes a thank-you cake.',[175,177,179,183],'s3'),(9,'Mara and Toby make the thank-you gift themselves.',[185,187,188,190,191,192],'s4'),(10,'The biscuit tray goes into the oven now, needs eight minutes, and then Mom needs the oven for supper.',list(range(256,272)),'q7'),(11,'The tray enters the oven now.',[256,257,258,259,260],'s5'),(12,'Mara makes one last star biscuit.',[296,297,298,299,300],'s6'),(13,'The tin will look finished after adding a final star.',[296,300,303,305,306,307,308],'s7'),(14,'Mara wants one last star biscuit.',[296,297,298,299,300],'q8'),
(15,'The children make another dog biscuit.',[316,317,318,319],'s8'),(16,'The children need another dog biscuit; Mr. Alvarez found Pepper.',list(range(316,324)),'q10'),(17,'Four dog-shaped biscuits are already allocated to Mr. Alvarez.',[324,325,326,327,328],'q11'),(18,'None of the existing dog biscuits is like Pepper in the way Toby means.',[329,330,331,332,333],'q12'),(19,'An existing dog biscuit is like Pepper in the way Toby means.',[330,331,332,333],'q12'),
(20,'Pepper’s being dog-shaped caused Mr. Alvarez to find her.',[334,335,336,337,338,339,340,341,342,343,344],'q13'),(21,'Mr. Alvarez did not find Pepper because of her dog shape.',list(range(334,345)),'q13'),(22,'Either individual torn portion is big enough for a star or dog cutter.',[373,375,377,378,380,381,383,384],'q14'),(23,'The torn dough is no longer individually big enough for either cutter.',list(range(376,385)),'q14'),(24,'Toby saves the best piece.',[391,393,395,397,398],'s9'),(25,'Toby was trying to save the best piece.',list(range(391,399)),'q15'),(26,'The saving was for Toby’s own idea.',[395,398,399,400,401],'q16'),
(27,'The children can still make one biscuit.',list(range(455,460)),'q17'),(28,'The children make one remaining biscuit.',[455,458,459],'s10'),(29,'Will the remaining biscuit be a star?',[460,461],'q18'),(30,'The remaining biscuit will be a dog.',[464,465],'q19'),(31,'Toby may help make the biscuit.',[468,469,470,471],'q20'),(32,'Toby helps make the biscuit.',[469,470,471],'s11'),(33,'Toby cuts all the way through the biscuit.',list(range(495,501)),'s12'),(34,'Toby does not cut all the way through the biscuit.',list(range(495,501)),'s12'),(35,'Toby knows not to cut all the way through.',[495,496,500,503,504],'q22'),
(36,'Is the tin of biscuits for Mr. Alvarez?',[647,648,651,653],'q23'),(37,'The biscuits are also for Pepper.',[654,655,656],'q24'),(38,'That biscuit is a dog, and the star represents Mr. Alvarez’s flashlight.',list(range(665,675)),'q25'),(39,'Mr. Alvarez remembers that night; he could see the pawprints only when he held the light close.',list(range(679,695)),'q26'),(40,'Mr. Alvarez sees the pawprints.',[683,684,686,688],'q26'),(41,'Mr. Alvarez holds the light close to the ground and pawprints.',[159,162,163,166,690,691,693,694],'q26'),(42,'Mr. Alvarez found Pepper on the earlier storm night.',[118,119,121,124,125,126,136,168,169],'s2'),
(43,'Someone reaches for the dough during the family pause.',[423,424,425,428],'s0'),(44,'The children borrow Grandma’s cutters.',[67,68,193,194,195,196],'s0'),
(45,'Toby must not cut all the way through the biscuit.',list(range(495,501)),'s12'),(46,'The children should be careful with Grandma’s cutters.',[57,59,60],'q1'),
]
for n,txt,ws,sid in PROPS:a.proposition(f'p{n}',txt,ws,scope_id=sid)
for w,p in [(57,46),(67,3),(95,4),(104,5),(108,6),(113,7),(256,10),(296,14),(303,13),(316,16),(324,17),(329,18),(334,21),(376,23),(391,25),(399,26),(455,27),(460,29),(464,30),(468,31),(495,45),(503,35),(647,36),(654,37),(665,38),(679,39)]:F(w,utterance_content_id=f'p{p}')
# Argument bindings selected for each local predicate, retaining shared mentions.
ROLES=[
(7,[],[5],{}),(10,[],[12],{}),(17,[16],[19],{}),(21,[20],[22],{}),(25,[24],[],{'location':[28]}),(29,[24],[30],{'destination':[33]}),(46,[40,45],[47,53],{'surface':[50,56]}),
(62,[61],[],{}),(63,[61],[66],{}),(67,[],[68],{}),(70,[],[71],{}),(73,[],[75,77,79,82],{}),(88,[87],[90],{}),(92,[91],[94],{}),(96,[95],[97],{'beneficiary':[99,100]}),(102,[101],[],{'recipient':[103]}),(105,[104],[],{'stimulus':[107]}),(109,[108],[110],{}),(111,[112],[],{}),(115,[],[114],{'beneficiary':[117]}),
(121,[118,119],[123,124],{}),(129,[128],[],{'source':[133]}),(141,[138,140],[143],{'co_searchers':[146]}),(150,[147,148],[152],{'destination':[158]}),(159,[148],[162],{'landmark':[166]}),(168,[167],[169],{'destination':[170]}),(171,[],[169],{'covering':[174]}),(177,[175],[],{}),(179,[175],[183],{}),(188,[185,187],[],{}),(190,[185,187],[],{}),(194,[193],[196],{'lender':[195]}),(200,[198],[205],{'recipient':[201]}),
(211,[210],[213],{}),(216,[215],[217],{}),(218,[215],[],{}),(224,[],[223],{'container':[227]}),(229,[228],[233,238],{}),(240,[228],[242],{}),(244,[228],[245],{}),(250,[],[249],{}),(252,[251],[255],{}),(258,[],[257],{}),(262,[],[261],{'duration':[263,264]}),(267,[266],[269],{'purpose':[271]}),(273,[272],[276],{}),(277,[],[276],{'surface':[280]}),(291,[],[289],{}),
(297,[296],[],{}),(302,[301],[],{}),(307,[],[305],{}),(310,[309],[312],{'landmark':[315]}),(317,[316],[],{}),(326,[],[328],{'beneficiary':[324]}),(341,[],[339],{'comparison':[344]}),(346,[345],[],{}),(348,[347],[350],{'direction_target':[354]}),(356,[355],[359],{}),(362,[],[361],{}),(364,[],[361],{}),(370,[369],[375],{}),(380,[],[377],{}),(386,[385],[],{}),(390,[],[388],{}),(393,[391],[],{}),(395,[391],[398],{}),(403,[402],[],{}),
(405,[404],[],{}),(408,[407],[],{}),(413,[411],[416],{'effector':[412]}),(418,[417],[422],{}),(425,[],[428],{}),(431,[],[430],{}),(434,[433],[438],{}),(440,[439],[438,448],{'contact_regions':[443]}),(450,[439],[452],{'instrument':[454]}),(458,[455],[459],{}),(463,[462],[],{}),(467,[466],[],{}),(471,[469],[],{}),(474,[],[473],{}),(476,[475],[479],{}),(482,[481],[483],{}),(487,[486],[490],{'landmark':[494]}),(496,[],[],{}),(502,[501],[],{}),(504,[503],[],{}),(506,[505],[],{}),(508,[505],[512],{'substrate':[515]}),(517,[516],[518],{'destination':[522]}),(525,[524],[529],{'destination':[532]}),(534,[],[538],{'landmarks':[541,544]}),
(547,[],[546],{'destination':[550]}),(559,[],[558],{}),(561,[560],[563],{'owner':[562]}),(566,[565],[568],{'instrument':[573]}),(577,[],[576],{}),(579,[578],[582],{'destination':[585]}),(588,[],[587],{'content':[592]}),(598,[597],[601],{'container':[605]}),(606,[597],[608],{}),(616,[615],[617],{'destination':[619]}),(622,[620,621],[624],{}),(629,[],[628],{'attachment_site':[632]}),(634,[633],[],{'landmark':[637]}),(639,[633],[],{}),(646,[],[645],{}),(650,[649],[],{}),(651,[649],[653],{}),(658,[657],[],{'beneficiary':[656]}),(660,[659],[664],{}),(667,[],[665],{}),(671,[],[670],{'represented_referent':[674]}),(677,[675,676],[],{}),(680,[679],[],{'remembered_time':[682]}),(686,[683],[688],{}),(696,[695],[698],{'support':[702]}),(704,[695],[707],{}),(711,[],[715],{'illumination_source':[710]}),
]
for w,actors,patients,others in ROLES:
 for role,ws in [('actor',actors),('patient',patients),*others.items()]:
  if ws:a.mention_event(f'ev{w+1}',ws,role=role)
for w,origin,actor,patient in [(322,121,[320,321],[323]),(336,121,[334],[337]),(691,159,[690],[693])]:
 a.mention_event(f'ev{origin+1}',actor,role='actor');a.mention_event(f'ev{origin+1}',patient,role='patient')
# Bound generic/proposed mentions are not additional actual baked objects.
a.entity('e84','dog-shaped biscuit Toby designates for Pepper','prospective_biscuit',[])
for w in [114,115]:
 a.entities['e31']['mentions'].remove(w);a.entities['e84']['mentions'].append(w);F(w,entity_id='e84',entity_name=a.entities['e84']['name'],entity='prospective_biscuit')
a.events['ev116']['patients']=['e84'];F(115,patients=['e84'])
a.entity('e85','neat things liked by Alvarez','generic_things',[107]);a.events['ev106']['patients']=['e85'];F(105,patients=['e85']);F(107,generic_reference=True)
a.entities['e52']['mentions'].remove(295);a.entities['e66']['mentions'].append(295);F(295,entity_id='e66',entity_name=a.entities['e66']['name'],entity='biscuit',referent_kind='prospective_realized_later',note='One more biscuit is a quantity/capacity referent, not yet a selected star shape. Later final biscuit realizes this remaining unit.')
# Surface morphology is explicit and separate from semantic roles.
for w,r in enumerate(a.words):
 t=r['token'].casefold()
 if r['pos']=='det':
  kind='possessive' if t in {'my','your','her','his','its','their'} else 'definite_article' if t=='the' else 'indefinite_article' if t in {'a','an'} else 'distributive' if t in {'each','either'} else 'quantificational';F(w,determiner_kind=kind)
  if t in {'a','an','the'}:F(w,definiteness='definite' if t=='the' else 'indefinite')
  if kind=='possessive':F(w,possessive_construction='possessive_determiner')
 if r['pos']=='pron' and r.get('entity_id'):F(w,mention_form='pronoun',antecedent_id=r['entity_id'])
 if r['pos']=='adp':F(w,dependency_relation='prepositional_marker')
 if r['pos']=='part' and t=='to':F(w,dependency_relation='infinitival_marker')
 if r['pos']=='conj' and t in {'and','but'}:F(w,coordinator_type='conjunctive' if t=='and' else 'adversative')
for w in [16,20,24,40,45,61,87,91,99,100,101,110,112,117,118,119,124,138,140,147,148,169,175,185,187,195,198,210,215,222,251,272,287,309,320,321,323,333,345,347,355,385,387,402,404,407,417,433,446,462,466,472,481,501,516,560,562,565,578,620,621,633,656,657,659,675,676]:F(w,mention_form='proper_name')
for w in [99,118,147,320,620,675]:F(w,proper_name_structure='title_plus_name')
for w in [195,222,287,387,446,472,493,562]:F(w,possessive_construction='genitive_np',genitive_realization='apostrophe_s')
for w,exp in [(69,['do','not']),(95,['we','are']),(115,['one','is']),(128,['she','had']),(167,['he','had']),(193,['they','had']),(335,['did','not']),(377,['it','is']),(495,['do','not']),(665,['that','is'])]:F(w,contraction_expansion=exp,clitic_type='contracted_auxiliary')
for w in [103]:F(w,lemma='he',grammatical_case='accusative')
F(337,lemma='she',grammatical_case='accusative');F(648,lemma='I',grammatical_case='accusative')
for w in [68,71,201,245]:F(w,lemma='they',grammatical_case='accusative')
for w in [95,266,296,316,391,455,503,648,679,683,690]:F(w,grammatical_person=1)
for w in [469]:F(w,grammatical_person=2)
for w in [95,193,201,228,316,369,455,524,597,615]:F(w,group_members=['e1','e2'],split_antecedent_ids=['e1','e2'])
for w in [12,22,30,50,56,60,68,71,107,126,146,152,196,201,209,223,233,238,242,245,264,328,375,388,412,416,443,522,558,563,601,637,688]:F(w,grammatical_number='plural')
for w in [6,17,21,25,46,62,73,88,92,102,111,120,141,149,168,176,188,199,211,216,224,229,240,244,250,252,273,290,302,310,322,346,348,356,362,364,370,386,389,392,403,405,408,413,418,425,431,434,440,450,463,467,474,476,482,487,502,506,517,525,534,547,559,561,566,577,579,588,598,616,622,634,639,646,650,658,660,671,677,696,704,711]:
 if a.words[w]['pos']=='v':F(w,verb_form='finite',tense='past')
for w in [105,109,258,262,267,297,317,326,456,470,504,680,671]:F(w,verb_form='finite',tense='present')
for w in [10,67,70,179,190,307,336,395,458,471,496,686]:F(w,verb_form='base')
for w in [29,63,96,159,218,393,406,409,508,606,651]:F(w,verb_form='gerund_participle')
for w,aux in [(121,120),(129,128),(150,149),(168,167),(177,176),(194,193),(200,199)]:F(w,verb_form='past_participle',aspect='perfect',perfect_auxiliary_id=a.anchor(aux));a.words[w].pop('tense',None)
for w in [171,277,341,629,716]:F(w,verb_form='past_participle')
for w in [511,528]:F(w,pos='adj',lemma='shaped')
for w in [69,335,495]:F(w,verb_form='finite')
F(335,tense='past');F(69,tense='present');F(495,tense='present')
F(306,verb_form='finite',tense='present');F(684,verb_form='finite',tense='past')
F(96,aspect='progressive',progressive_auxiliary_id=a.anchor(95));F(393,aspect='progressive',progressive_auxiliary_id=a.anchor(392))
for w in [67,70,496]:F(w,mood='imperative',imperative_subject_status='understood_addressee')
for w,e in [(67,'e8'),(70,'e8'),(179,'e3'),(190,'e8'),(395,'e2'),(496,'e2')]:F(w,subject_controller_id=e)
SUB={7:'e10',10:'e10',17:'e3',21:'e4',25:'e5',29:'e5',46:'e8',62:'e5',63:'e5',73:'e23',88:'e1',92:'e2',96:'e8',102:'e1',105:'e6',109:'e6',111:'e2',115:'e84',121:'e6',129:'e7',141:'e8',150:'e6',159:'e6',168:'e6',171:'e7',177:'e3',179:'e3',188:'e8',190:'e8',194:'e8',200:'e3',211:'e1',216:'e2',218:'e2',224:'e16',229:'e8',240:'e8',244:'e8',250:'e45',252:'e3',258:'e47',262:'e47',267:'e3',273:'e1',277:'e50',291:'e50',297:'e1',302:'e1',307:'e42',310:'e2',317:'e8',322:'e6',326:'e6',336:'e6',341:'e7',346:'e1',348:'e2',356:'e1',362:'e50',364:'e50',370:'e8',380:'e50',386:'e1',390:'e57',393:'e2',395:'e2',403:'e1',405:'e4',406:'e4',408:'e3',409:'e3',413:'e60',418:'e5',431:'e45',434:'e1',440:'e1',450:'e1',458:'e8',463:'e2',467:'e1',471:'e2',474:'e65',476:'e2',482:'e1',487:'e2',496:'e2',502:'e1',504:'e2',506:'e2',508:'e2',517:'e1',525:'e8',547:'e47',559:'e30',561:'e1',566:'e2',577:'e45',579:'e3',588:'e10',598:'e8',606:'e8',616:'e8',622:'e6',629:'e37',634:'e7',639:'e7',646:'e81',650:'e6',651:'e6',658:'e2',660:'e1',667:'e66',671:'e68',677:'e6',680:'e6',686:'e6',691:'e6',696:'e6',704:'e6',711:'e83',716:'e68'}
for w,e in SUB.items():F(w,grammatical_subject_id=e)
for w,e in {10:'e11',17:'e13',21:'e14',29:'e16',63:'e24',67:'e23',70:'e23',88:'e25',92:'e28',96:'e30',102:'e2',105:'e85',109:'e7',121:'e7',141:'e34',150:'e35',159:'e37',168:'e7',179:'e41',194:'e23',200:'e42',211:'e21',216:'e19',240:'e44',244:'e44',267:'e46',297:'e52',310:'e54',317:'e53',322:'e7',326:'e31',336:'e7',348:'e50',356:'e55',395:'e58',418:'e61',434:'e62',440:'e64',450:'e49',458:'e66',476:'e28',482:'e28',487:'e25',506:'e25',508:'e68',517:'e69',525:'e66',561:'e23',566:'e23',579:'e74',598:'e30',606:'e66',616:'e42',622:'e78',651:'e42',686:'e35',691:'e37',696:'e42',704:'e66',711:'e68'}.items():F(w,grammatical_object_id=e)
F(200,indirect_object_id='e8');F(534,expletive_subject_id=a.anchor(533));F(533,expletive_reference=True)
F(413,reference_metonymic_link={'literal_id':'e60','related_id':'e3','relation':'eyes_realize_person_looking'},event_effector=B(413,'e3',{'effector_id':'e60','event_id':'ev414'}))
F(10,lexical_gloss='enough to rattle describes a threshold; actual spoon rattling is not independently narrated')
F(115,lexical_gloss='dog one is an intended dog-shaped biscuit, distinct from the dog cutter and living Pepper')
F(326,lexical_gloss='has four dogs means four dog biscuits allocated to the intended recipient, before actual delivery')
F(341,voice='passive',passive_auxiliary_id=a.anchor(340))
F(711,lexical_gloss='porch illumination highlights the decoration; no grasping action')
F(340,verb_form='finite',tense='past');F(691,verb_form='finite',tense='past');F(555,verb_form='base')
F(286,pos='adp');F(613,pos='n');F(618,pos='adj',lexical_idiom_reading={'phrase':'next door','sense':'neighbor_location','referent_id':'e77'});F(619,pos='n')
F(331,referent_kind='bound_variable',quantifier_binding={'quantifier':'existential_under_negation','domain':'e31','variable_id':'x_existing_dog_biscuit','scope_id':'q12'})
F(568,referent_kind='bound_variable',quantifier_binding={'quantifier':'each','domain':'e23','variable_id':'e88'})
F(374,quantity_comparison={'left':'e62','right':'e63','dimension':'size','operator':'not_equal'})
# Spatial, material and identity state is attached to the correct physical carrier.
for w,e,col in [(161,'e37','yellow'),(204,'e42','blue'),(390,'e57','pink'),(604,'e42','blue'),(627,'e37','yellow'),(723,'e66','brown')]:F(w,appearance_color=B(w,e,col,factuality='asserted'))
for w,part,whole in [(56,'e22','e8'),(86,'e29','e28'),(288,'e51','e2'),(312,'e54','e2'),(359,'e55','e50'),(388,'e57','e2'),(412,'e60','e3'),(443,'e64','e56'),(473,'e65','e2'),(494,'e67','e66'),(522,'e70','e68'),(637,'e80','e6'),(645,'e81','e7'),(719,'e67','e66')]:F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
for w,e,shape in [(75,'e25','star'),(77,'e26','rabbit'),(79,'e27','flower'),(82,'e28','dog_with_floppy_ear'),(90,'e25','star'),(94,'e28','dog_with_floppy_ear'),(233,'e43','star'),(238,'e31','dog'),(295,'e66','unspecified_before_choice'),(300,'e52','star'),(319,'e53','dog'),(461,'e52','star'),(465,'e53','dog'),(512,'e68','star_impression'),(529,'e66','dog_with_star_impression'),(541,'e71','star'),(544,'e72','rabbit'),(667,'e66','dog'),(715,'e68','star')]:
 F(w,object_shape=B(w,e,shape,factuality='hypothetical' if w==461 else 'desired' if w in [300,319,465] else 'asserted'))
# Shape at the generic capacity mention is intentionally left unknown rather than encoded as an actual shape value.
a.words[295].pop('object_shape',None)
F(203,object_fill_state=B(203,'e42','empty'));F(214,attributes=[{'name':'surface_texture','value':'rolled smooth dough'}])
F(364,object_integrity=B(364,'e50','split'),event_result_entity=B(364,'e50',{'result_id':'e56','parts':['e62','e63'],'state':'two_uneven_pieces'}))
F(440,object_integrity=B(440,'e50','recombined'),event_result_entity=B(440,'e50',{'result_id':'e50','joined_parts':['e62','e63'],'state':'edges_pressed_together'}))
F(442,object_integrity=B(442,'e64','torn_before_pressing'))
F(629,object_attachment=B(629,'e37',{'attached_to':'e79','mode':'clipped'}))
F(600,object_temperature=B(600,'e30','cooled'));F(723,object_cooking_state=B(723,'e66','baked_browned'))
F(561,object_cleanliness=B(561,'e23','washed'));F(566,object_moisture=B(566,'e23','dried'))
F(85,object_shape=B(85,'e29','floppy'))
F(474,figurative_mapping={'target_id':'e65','source_image':'increased_brightness','kind':'metaphor','literal_event':False},note='A brighter facial expression is explicit; no precise emotion such as pride or relief is assigned.')
for w,e,l,rel in [(13,'e11','e12','inside'),(25,'e5','e15','at'),(29,'e16','e17','into'),(48,'e87','e20','on'),(54,'e86','e22','under'),(73,'e23','e24','inside'),(129,'e7','e32','out_of'),(159,'e37','e38','close_above'),(171,'e7','e40','wrapped_in'),(224,'e16','e17','inside'),(277,'e50','e49','on'),(310,'e54','e50','over'),(348,'e50','e28','toward'),(487,'e25','e67','above'),(508,'e68','e50','impressed_in'),(517,'e69','e70','into'),(525,'e66','e47','onto'),(547,'e47','e46','inside'),(579,'e74','e46','inside'),(598,'e30','e42','inside'),(606,'e66','e30','on_top_of'),(629,'e37','e79','attached_to'),(634,'e7','e80','past'),(696,'e42','e82','on'),(716,'e68','e67','impressed_in')]:F(w,spatial_configuration=B(w,e,{'landmark':l,'relation':rel},factuality=a.words[w].get('factuality','asserted')))
F(534,spatial_configuration=B(534,'e66',{'landmarks':['e71','e72'],'relation':'between'}),containment_capacity_fit=B(534,'e47',{'object_id':'e66','fits':True,'available_space':'just_enough'}))
F(598,containment_contents=B(598,'e42',{'contents':['e30'],'event_id':'ev599'}))
F(63,transfer_source=B(63,'e24',{'source':'e5'}),transfer_recipient=B(63,'e24',{'recipient':'e8'}))
for w,e,source,dest,kind in [(194,'e23','e5','e8','loan'),(200,'e42','e3','e8','provision'),(651,'e42','e8','e6','gift')]:
 F(w,transfer_kind=B(w,e,kind),transfer_source=B(w,e,{'source':source}),transfer_recipient=B(w,e,{'recipient':dest}),transfer_completion=B(w,e,{'completed':True,'event_id':a.words[w]['event_id']}))
F(60,possession_owner=B(60,'e23',{'owner':'e5'}));F(194,possession_borrower=B(194,'e23',{'borrower':'e8'}),possession_lender=B(194,'e23',{'lender':'e5'}),transfer_retained_ownership=B(194,'e23',{'holder':'e8','owner':'e5'}))
F(92,possession_holder=B(92,'e28',{'holder':'e2'}));F(162,possession_owner=B(162,'e37',{'owner':'e6'}));F(174,possession_owner=B(174,'e40',{'owner':'e6'}))
F(115,possession_reservation=B(115,'e84',{'reserved_for':'e7','reserved_recipient_holds_now':False,'holder_claim':'Toby_intention'}))
F(326,possession_reservation=B(326,'e31',{'reserved_for':'e6','reserved_recipient_holds_now':False,'allocation_is_Mara_claim':True}))
F(476,possession_user=B(476,'e28',{'user':'e2','co_user':'e1','episode':'ev900'}));F(506,possession_user=B(506,'e25',{'user':'e2','use':'make_surface_impression'}))
F(651,possession_holder=B(651,'e42',{'holder':'e6'}),transfer_recipient_acceptance=B(651,'e42',{'accepted':True,'recipient':'e6'}))
for w,e,dest in [(150,'e6','e36'),(168,'e7','e39'),(525,'e66','e47'),(547,'e47','e46'),(579,'e74','e46'),(616,'e42','e77')]:F(w,motion_destination=B(w,e,{'landmark_id':dest,'event_id':a.words[w]['event_id'],'role':'destination'}))
F(129,motion_source=B(129,'e7',{'landmark_id':'e32','event_id':'ev130','role':'source'}))
F(348,motion_trajectory_phase=B(348,'e50',{'phase':'approaching','landmark_id':'e28','arrival_not_stated':True}))
F(168,motion_carrier=B(168,'e7',{'carrier':'e6'}));F(616,motion_carrier=B(616,'e42',{'carrier':'e8'}))
F(711,event_causer=B(711,'e68',{'causer':'e83','event_id':'ev712'}))
F(224,causal_parent=B(224,'e16',{'cause_event_id':'ev219','effect_event_id':'ev225'}),evidence=[218,219,220,221,223,224])
F(646,causal_parent=B(646,'e81',{'cause_event_id':'ev640','effect_event_id':'ev647'}),evidence=[639,640,641,643,645,646])
F(141,event_collective_participants=B(141,'e8',{'participant_groups':['e8','e9'],'expanded_members':['e1','e2','e3','e4'],'event_id':'ev142'}))
F(482,event_divided_labor=B(482,'e8',{'shared_event_id':'ev900','subtasks':[{'actor_id':'e2','event_id':'ev477','action':'guide_cutter'},{'actor_id':'e1','event_id':'ev483','action':'press_cutter'}]}))
F(517,event_divided_labor=B(517,'e8',{'shared_event_id':'ev900','subtasks':[{'actor_id':'e2','event_id':'ev509','action':'make_impression'},{'actor_id':'e1','event_id':'ev518','action':'fill_impression_with_sugar'}]}))
F(525,event_collective_participants=B(525,'e8',{'members':['e1','e2'],'event_id':'ev526'}))
# Quantities preserve units, approximation and distributive domains.
F(1,cardinal_value=4,time_expression_id='time_kitchen_opening',temporal_granularity='hour',event_time_interval={'hour':4,'meridiem':'unspecified','date':'unspecified'})
F(2,time_expression_id='time_kitchen_opening')
F(84,cardinal_value=1,counted_domain={'kind':'floppy_ear','whole':'e28'})
F(125,cardinal_value=2);F(126,measure_unit='night',measure_dimension='time',quantity_exact_value=2)
F(127,temporal_deixis='earlier',event_time_interval={'event_id':'ev122','offset':-2,'unit':'night','relative_to':'time_kitchen_opening'},narrative_order_mode='flashback')
F(263,cardinal_value=8);F(264,quantity_exact_value=8,measure_unit='minute',measure_dimension='time',temporal_duration={'event_kind':'baking','value':8,'unit':'minute','status':'required_by_Mom','scope_id':'q7','assertion_status':'attributed_claim'})
F(281,cardinal_value=1,counted_domain={'kind':'remaining_dough_lump','referent':'e50'})
F(283,quantity_approximation_cue='about');F(285,quantity_comparison={'left':'e50','right':'e51','dimension':'size','operator':'approximately_equal'})
for w in [293,298]:F(w,cardinal_value=1,counted_domain={'kind':'additional_biscuit','domain':'remaining_dough'})
F(291,affordance_containing=B(291,'e50',{'note':'not_container'}));a.words[291].pop('affordance_containing',None)
F(291,attributes=[{'name':'resource_capacity','value':'remaining dough is enough for one more biscuit; shape not yet selected'}])
F(327,cardinal_value=4,counted_domain={'kind':'dog_shaped_biscuit','allocation_recipient':'e6','scope_id':'q11','assertion_status':'attributed_claim'})
F(373,cardinal_value=2,counted_domain={'kind':'dough_piece','referent':'e56'})
F(437,quantity_comparison={'left':'e62','right':'e63','dimension':'size','operator':'greater'})
F(447,quantity_comparison={'left':'e63','right':'e62','dimension':'size','operator':'less'})
F(552,cardinal_value=1);F(553,quantity_exact_value=1,measure_unit='minute',measure_dimension='time',temporal_duration={'kind':'remaining_margin_at_oven_entry','event_id':'ev548','value':1,'unit':'minute','deadline_identity_not_stated':True})
F(567,quantifier_binding={'quantifier':'each','domain':'e23','variable_id':'e88','scope':'dried_by_Toby'},quantity_distribution_cue='per_individual')
for w in [239,265,303,363,449,485,614]:F(w,temporal_order_cue='then')
F(129,event_time_relation={'left':'ev130','relation':'before','right':'ev122'})
F(168,event_time_relation={'left':'ev122','relation':'before','right':'ev169'})
for w in [177,194,200]:F(w,narrative_order_mode='earlier_gift_preparations')
F(194,event_time_relation={'left':'ev195','relation':'before','right':'ev89'})
F(137,temporal_signal_relation='while',temporal_overlap={'events':['ev142','ev151'],'scope_id':'s2'})
F(480,temporal_signal_relation='while',temporal_overlap={'events':['ev477','ev483'],'scope_id':'s0'})
F(556,temporal_signal_relation='while',temporal_overlap={'events':['ev560','ev562','ev567'],'scope_id':'s0'})
F(574,temporal_signal_relation='when',time_anchor_id='ev578')
# Scope-sensitive goals, prohibitions, beliefs, memory and explanation.
F(57,request_action_id='p1',speech_act_kind='caution')
F(67,permission_grantor_id='e5',permission_recipient_id='e8',permission_content_id='p44',permission_status='granted',request_action_id='p44')
F(69,negation_scope_id='p2',negation_marker_form='not',proposition_polarity='negative',obligation_debtor_id='e8',obligation_creditor_id='e5',obligation_content_id='p2',obligation_status='prohibited')
F(96,goal_owner_id='e8',goal_content_id='p9',goal_beneficiary_ids=['e6'],goal_status='in_progress',goal_polarity='achieve')
F(105,belief_holder_id='e1',belief_content_id='p5',epistemic_attitude_kind='attributed_preference',epistemic_source_entity_id='e1')
F(109,belief_holder_id='e2',belief_content_id='p6',epistemic_attitude_kind='attributed_preference')
F(177,offer_content_id='p8');F(188,goal_owner_id='e8',goal_content_id='p9',goal_status='desired',goal_polarity='achieve',goal_beneficiary_ids=['e6'],goal_motivation={'owner_id':'e8','reason':'thank_Alvarez_for_finding_Pepper','supporting_event_id':'ev122'})
F(258,request_action_id='p11',speech_act_kind='instruction');F(262,modal_base={'holder':'e3','kind':'required_baking_duration','value':8,'unit':'minute'})
F(297,goal_owner_id='e1',goal_content_id='p12',goal_status='desired',goal_polarity='achieve',intention_publicity='communicated')
F(307,belief_holder_id='e1',belief_content_id='p13',epistemic_attitude_kind='predicted_visual_completion',goal_motivation={'owner_id':'e1','reason':'make_tin_look_finished','desired_action_id':'p12'})
F(317,goal_owner_id='e2',goal_content_id='p15',goal_status='expressed_need',goal_polarity='achieve',goal_motivation={'owner_id':'e2','reason':'Alvarez_found_Pepper','supporting_event_id':'ev122'})
F(330,negation_scope_id='p19',proposition_polarity='negative')
F(335,negation_scope_id='p20',proposition_polarity='negative',negation_attachment_kind='causal_explanation',note='Negation rejects dog shape as the reason for rescue, not the already established finding of Pepper.')
F(338,causal_scope=B(338,'e7',{'holder_id':'e1','content_id':'p20','factuality':'negated'}),reasoner_id='e1',reasoning_conclusion_id='p21',reasoning_rule_kind='reject_causal_explanation')
F(378,negation_scope_id='p22',proposition_polarity='negative');F(380,goal_feasibility_judgment='individual_torn_portions_insufficient_for_either_cutter',belief_holder_id='e1',belief_content_id='p23')
F(395,goal_owner_id='e2',goal_content_id='p24',goal_status='reported_attempt',goal_polarity='achieve')
F(399,viewpoint_evaluative_stance={'holder_id':'e1','target_content_id':'p25','interpretation':'for_Toby_own_idea','assertion_status':'attributed_claim'})
F(423,negation_scope_id='p43',explicit_zero_count={'domain':'people_reaching_for_dough_during_pause','count':0,'scope_id':'s0'},quantifier_domain_restriction={'domain':'people_present_in_kitchen','interval':'pause_before_Mara_recombines'})
F(405,event_phase=B(405,'e4',{'activity_event_id':'ev22','phase':'stopped'}),clausal_object_id=a.anchor(406));F(408,event_phase=B(408,'e3',{'activity_event_id':'ev18','phase':'continued'}),clausal_object_id=a.anchor(409))
F(456,modal_base={'holder':'e1','kind':'remaining_ability','content_id':'p28'},modal_scope_id='p28')
F(460,question_requested_slot='shape_of_final_biscuit',question_answer_status='answered',dialogue_response_to_id='ev1455')
F(464,dialogue_response_to_id='ev464',plan_revision={'holder_id':'e1','replace':'p12','with':'p15','aspect':'final_biscuit_shape'},plan_commitment_status='adopted',intention_holder_id='e1',intention_content_id='p15',intention_publicity='communicated')
F(470,modal_base={'holder':'e1','kind':'permission','content_id':'p32'},permission_grantor_id='e1',permission_recipient_id='e2',permission_content_id='p32',permission_status='granted')
F(495,negation_scope_id='p33',proposition_polarity='negative',request_action_id='p34',obligation_debtor_id='e2',obligation_creditor_id='e1',obligation_content_id='p33',obligation_status='prohibited')
F(504,knowledge_claim_holder_id='e2',knowledge_claim_content_id='p45',epistemic_attitude_kind='explicit_knowing_claim')
F(508,event_result_entity=B(508,'e66',{'result_id':'e68','surface_impression':'e68','cut_through':False}),evidence=[495,496,500,503,504,506,507,508,512,515],note='Gentle pressing creates the star mark; no second full biscuit is cut from the dog.')
F(647,question_requested_slot='gift_beneficiary',question_answer_status='answered',speech_act_kind='confirmation_question')
F(654,dialogue_response_to_id='ev651',speech_act_kind='add_beneficiary',goal_beneficiary_ids=['e7'])
F(680,mental_memory_holder_id='e6',mental_memory_content_id='p42',mental_memory_event_id='ev122',epistemic_time_scope={'relative_nights_before':2,'reference':'time_kitchen_opening'})
F(684,modal_base={'holder':'e6','kind':'past_visual_ability','content_id':'p40'},modal_scope_id='p40')
F(685,necessary_condition={'condition':'p41','for':'p40','holder_id':'e6','scope_id':'q26','assertion_status':'attributed_claim'})
F(686,access_visibility=B(686,'e35',{'observer':'e6','condition_id':'p41','visible_under_condition':True}),epistemic_access_mode='visual_perception')
a.extension('symbolic_reference','object','An explicitly stated symbolic link from an artifact or decoration to the person, object or event it represents, without literal identity or performance enactment. carrier_id is the artifact or decoration eN; referent_id is the represented eN entity or evN event; holder_id is the person attributing the link.','Local attributed representation statement.','Object shape names a physical outline; figurative_mapping covers metaphors, and enactment binds performance roles. None separately encodes an explicitly explained gift-decoration symbol.',{'carrier_id':'e68','referent_id':'e37','relation':'represents','holder_id':'e1','scope_id':'q25','assertion_status':'attributed_claim'})
F(671,symbolic_reference={'carrier_id':'e68','referent_id':'e37','relation':'represents','holder_id':'e1','scope_id':'q25','assertion_status':'attributed_claim'})
F(667,reference_metonymic_link={'literal_id':'e66','description':'dog','relation':'object_depicts_shape','not_identity_with':'e7'})
F(440,narrative_change_dimension='split_dough_recombined')
F(525,narrative_resolution_evidence={'problem_event_id':'ev365','resolution_event_id':'ev900','outcome':'single_combined_design_made'})
F(716,narrative_motif_link={'earlier_event_id':'ev160','later_event_id':'ev712','relation':'rescue_flashlight_recalled_by_illuminated_symbol','assertion_status':'candidate'})
F(720,narrative_closure_candidate={'evidence':['gift_accepted','combined_design','star_flashlight_meaning_explained','sugar_star_illuminated'],'assertion_status':'candidate'})
feedback={'summary':'Retrospective annotation of shared baking, a recalled Pepper rescue, disagreement over the last dough portion, recombination and collaborative design, and gift delivery.',
'reviewed_all_words':True,'reviewed_paragraphs':list(range(37)),
'ambiguities':[
{'words':[121,322,336,680,691],'issue':'Rescue recollections reuse the same past finding and flashlight-holding events. Negation at didn’t find ... because rejects a reason, not the actual rescue.'},
{'words':[75,82,94,114,115,238,319,328,493,608,667],'issue':'Living Pepper, shaped cutters, planned biscuit referents, existing biscuit groups and final decorated biscuit are separate. Four dogs is an allocation claim before delivery, not four actual pets.'},
{'words':[183,190,191,209],'issue':'Mom offered a cake; children wanted to do the thanks themselves and made biscuits. No actual cake is added.'},
{'words':[194,561,566],'issue':'Borrowing and cleaning/drying cutters are explicit, but their return is not narrated. Loan completion is not inferred from a familiar story pattern.'},
{'words':[263,264,547,552,553],'issue':'Eight minutes is the stated baking requirement. One minute to spare is the oven-entry margin; exact deadline identity and a clock-stamped actual eight-minute duration are not independently given.'},
{'words':[365,375,398,438,448],'issue':'Torn pieces are unequal and recombined. Toby’s claimed best piece cannot confidently be identified with the larger or smaller piece.'},
{'words':[390,474],'issue':'Pink ears and a brightened face are observed; specific emotions such as shame, pride or relief are not forced.'},
{'words':[493,506,508,512,541,544],'issue':'Star impression is a shallow mark on the dog biscuit, not a second cut-out. A rabbit biscuit is present on the tray, although its cutting is omitted in the earlier row summary.'},
{'words':[600,616,651,656],'issue':'Cooling precedes packing, but cooling duration and tray removal action are not narrated. Alvarez receives the tin; no actual feeding of Pepper or consumption of biscuits is asserted.'},
],
'feature_gaps':[{'meaning':'Explicitly explained artifact symbolism','resolution':'Proposed symbolic_reference binds carrier, represented referent, speaker, scope and attribution. This is distinct from shape, living identity, metaphor, and performance enactment.'}],
'prompt_feedback':['Keep negated causal reasons separate from the factual event being explained.','Gift plans and allocation language need not imply current recipient custody.','A symbol can refer to a physical object without depicting its outline: the star stands for a flashlight.','A recipe duration and scheduling slack use the same units but attach to different event roles.'],
'coverage_notes':'All 725 words have explicit contextual POS/lemmas. All 37 assembled paragraphs and entity/event/scope/proposition registries were read against the full source, then material corrections were regenerated and checked. All 1,024 definitions and frozen v3 reference inputs were read for sparse use. Shape validation is separate from manual semantic review.'}
a.save(feedback)
