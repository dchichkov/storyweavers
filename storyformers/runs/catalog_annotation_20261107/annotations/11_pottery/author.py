"""Manually interpreted whole-story pottery annotation, frozen prompt v2."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation

a = Annotation('11_pottery', prompt_version='v2')
# Explicit contextual tags, one per source word; no surface POS lookup.
TAGS = [
'det n n v adp det n conj det n n adp n n n n adp num n pron v v v det n adp n n det n v adj adp det n conj det adj n adp det adj n v adj adp pron part v',
'pron v det n adj adv adp num n n v n n conj det n v part v adj n v det n adv adp det n',
'adj n part v adp v n n pron v det n adp n adp det n pron adv',
'n v n n adp det n pron adp det n adv',
'pron v det n conj v pron adv adp det adj n adv pron v n n adj n n det adj adj n conj v pron adv adp det adj n',
'det n v',
'det adj n v adp det n det n n v adp pron conj det n v det adj adj',
'n v v det n intj intj',
'pron v det n adp det adj n v part v pron adv adv det n v adv adv',
'n n v adv part v pron adv adj adv pron v conj conj pron v v pron v v det n',
'v pron v det n adp det n',
'pron v v pron v conj det n v part v adv pron v adv v det adj n adv conj v adv',
'n v adp det n det n adj n n v det adj pron adp n n conj pron v adv pron v v n adp det adj n part v conj v v pron v v pron det n v n adv conj pron v v det adj pron adv conj pron v v pron part v adv adj',
'pron v det n adv adp det n pron v v det n v det adj conj part adv part v adp',
'n v num n adp det adj n conj v det n adp det n',
'det n v adv',
'pron conj pron v det n pron v pron v v det n adp det n',
'n n v pron v v det n adv v det n conj pron v adj conj v conj det adj n v adj det det n adv',
'n v det n adp det n adv adp det adj n adp det n pron v det adj n adp det n pron v det n conj pron v det n adp det n n det n adv v adj conj adv det n v part v adp det n',
'conj pron v n n v adv det n adp det n n',
'v pron adp v pron n v v det n adp det n conj v pron',
'det n v adp det n adv v adp det n adp det adj n conj n v adv det n v adj conj adj pron v pron adp det adj n v pron adv conj det n v v det n v adp det n n adp det adj n',
'adp det adj n det n v adp det n n adp det n v adv adp num n n v pron adv adp det n v adp n',
'adp n n pron v det n adp det n n',
'pron det n n v adv det n v v conj adv pron v pron adp det n n det n v adj adp det n',
'n v det n adp det n pron v num n adp det n conj v det n adp det n det n v adp det adj n',
'intj pron v pron adv adv det n v part v',
'pron v adv n adv conj v det n adp det n pron v adj adv pron v pron adv v adp n conj v pron adp det n n',
'det adj n n v det n adp det n adp n n det n adp adj n v det n adp pron n v v adp det n n det n v adp det adj n conj pron v adp det n det n v det adj n adp n adp det n adj n',
]
LEMMAS = {
'Bea':'Bea','Grandpa':'Grandpa','Grandpa’s':'Grandpa','Len':'Len','Mr':'Mr','Ivo':'Ivo','Ivo’s':'Ivo','Thursday':'Thursday',
'I':'I','Ivo’s':'Ivo','walked':'walk','weeks':'week','had':'have','been':'be','making':'make','fingers':'finger','grew':'grow','mornings':'morning','was':'be','him':'he',
'told':'tell','needs':'need','carries':'carry','things':'thing','said':'say','pictured':'picture','hands':'hand','centered':'center','pulled':'pull','borrowed':'borrow','curved':'curve','pressed':'press','slipped':'slip','appeared':'appear','cup’s':'cup','bulged':'bulge','went':'go','stopped':'stop','turning':'turn','dabbed':'dab','hoping':'hope','shifted':'shift','farther':'far','leaned':'lean','It’s':'it','might':'may','could':'can','couldn’t':'can','glanced':'glance','workshop’s':'workshop','firing':'firing','started':'start','wouldn’t':'will','fired':'fire','bought':'buy','wanted':'want','didn’t':'do','rested':'rest','settled':'settle','asked':'ask','nodded':'nod','feels':'feel','edges':'edge','is':'be','ran':'run','eased':'ease','turned':'turn','faced':'face','looked':'look','seemed':'seem','finished':'finish','held':'hold','lending':'lend','wiping':'wipe','returning':'return','dried':'dry','pots':'pot','came':'come','dipped':'dip','coated':'coat','gathered':'gather','stood':'stand','tilted':'tilt','carried':'carry','padded':'pad','opened':'open','got':'get','dented':'dent','made':'make','knuckles':'knuckle','that’s':'that','poured':'pour','stayed':'stay','took':'take','filled':'fill','found':'find','marked':'mark','kneeling':'kneel','plants':'plant','resting':'rest','drank':'drink','caught':'catch',
}
for i,tags in enumerate(TAGS): a.tag(i,tags,LEMMAS)
F = a.feature
for name in ['appearance_color','part_whole_relation','figurative_mapping','affordance_supporting']:a.use_extension(name)

ENTITIES = [
('e1','Bea','person',[2,19,49,58,92,96,108,121,163,170,203,206,212,231,242,260,276,286,294,302,324,334,339,345,349,362,387,402,410,439,456,483,486,492,537,561,570,656]),
('e2','Mr. Ivo','person',[12,13,60,61,83,84,85,123,124,189,190,199,222,359,360,441,442,445,452]),
('e3','Grandpa Len','person',[26,27,28,40,46,69,71,98,101,105,257,279,357,548,550,582,584,589,591,600,605,613,618,623,639,650,664,676,683,691,694]),
('e4','Bea’s cup for Grandpa','cup',[24,64,119,151,237,291,297,305,310,372,424,468,487,494,500,523,530,539,558,560,587,631,635,641,648,659,675,706]),
('e5','new cup handle','handle',[52,331,413,415,531,578,597]),
('e6','Grandpa’s old mug','mug',[42,102]),('e7','old mug thin handle','handle',[38]),
('e8','Grandpa’s fingers','body_part_group',[29,57,583]),('e9','Grandpa’s two inserted fingers','body_part_group',[594]),
('e10','Grandpa’s hands','body_part_group',[99,590]),('e11','Grandpa’s thumb','body_part',[106,358,601,619,684]),
('e12','Grandpa’s knuckles','body_part_group',[606]),('e13','Grandpa’s knee','body_part',[695]),
('e14','Bea’s two inserted fingers','body_part_group',[327]),('e15','Bea’s checking finger','body_part',[390]),
('e16','Bea’s thumb','body_part',[335]),('e17','Bea’s hand','body_part',[340]),('e18','Ivo’s extended hand','body_part',[446]),
('e19','Ivo’s pottery workshop','workshop',[15,248]),('e20','bakery on Bea’s route','bakery',[6]),('e21','bus stop on Bea’s route','bus_stop',[10]),
('e22','Bea’s pottery wheel','pottery_wheel',[93,167]),('e23','clay formed into the cup','clay',[88,90,111,114,149,611]),
('e24','clay residue on rib','clay',[460]),('e25','Ivo’s wooden shaping rib','pottery_tool',[127,131,134,141,450,455,466]),
('e26','shaping rib handle','handle',[463]),('e27','cup wall','cup_part',[139,185,195,380,393]),('e28','cup side','cup_part',[152,565]),
('e29','cup rim','cup_part',[158,314,708]),('e30','dent used as thumb rest','cup_feature',[145,155,173,181,215,338,348,351,409,418,422,513,572,576,604,615,689]),
('e31','dent edges','cup_part',[370,406]),('e32','damp shaping sponge','sponge',[177,401]),('e33','soft side of sponge','sponge_part',[398]),
('e34','possible hole through cup wall','hypothetical_hole',[210]),('e35','proposed added clay','hypothetical_material',[218]),
('e36','proposed clay patch','hypothetical_patch',[226]),('e37','Bea and Ivo','person_group',[219]),('e38','workshop clock','clock',[246]),
('e39','possible replacement cup','hypothetical_cup',[270]),('e40','possible store-bought mug','hypothetical_mug',[283]),
('e41','workshop testing table','table',[309]),('e42','drying shelf','shelf',[472]),('e43','workshop kiln','kiln',[250,477]),
('e44','other pots in kiln','pot_group',[481]),('e45','blue glaze on new cup','glaze',[498,508]),
('e46','pickup table','table',[528]),('e47','padded carrying box','box',[543,553]),('e48','newspaper padding','newspaper',[546]),
('e49','Bea’s home','home',[540]),('e50','kitchen table','table',[557,634]),('e51','Grandpa’s garden','garden',[76,651]),
('e52','garden bench','bench',[652,662]),('e53','garden table mentioned under cup','table',[673]),('e54','Grandpa’s trowel','trowel',[665]),
('e55','ring of damp earth','earth_mark',[667]),('e56','damp garden earth','earth',[670]),('e57','bean plants','plant_group',[682]),
('e58','sun','sun',[697]),('e59','tiny water bead on rim','water_drop',[701,703]),('e60','water poured for initial cup test','water',[626]),
('e61','tea in the birthday cup','tea',[645]),('e62','Grandpa’s habitually carried tea','tea_kind',[72]),
]
for eid,name,kind,words in ENTITIES:a.entity(eid,name,kind,words)
a.entities['e37']['member_ids']=['e1','e2']
a.entities['e9']['subset_of']='e8'

# Direct quotations and their actual speech instances are separate.
QUOTES=[
('q1',range(49,58),'e1','e2',59,'design_goal'),('q2',range(62,77),'e1','e2',59,'design_requirements'),
('q3',range(77,82),'e2','e1',82,'encouragement'),('q4',range(94,96),'e2','e1',94,'further_question'),
('q5',range(103,108),'e1','e2',103,'design_addition'),('q6',range(168,170),'e1',None,168,'dismay_exclamation'),
('q7',range(195,199),'e2','e1',200,'reassurance'),('q8',range(201,211),'e2','e1',200,'conditional_warning'),
('q9',range(211,219),'e1','e2',211,'repair_question'),('q10',range(219,222),'e2','e1',223,'tentative_response'),
('q11',range(224,242),'e2','e1',223,'warning_and_alternative'),
('q12',range(343,349),'e1','e2',350,'proposal_question'),('q13',range(351,359),'e1','e2',350,'possible_use'),
('q14',range(362,387),'e2','e1',362,'permission_and_guidance'),
('q15',range(451,456),'e1','e2',457,'thanks'),('q16',range(558,561),'e1','e3',562,'gift_introduction'),
('q17',range(564,584),'e1','e3',562,'explanation'),('q18',[612,*range(615,623)],'e3','e1',614,'fit_appreciation')]
for sid,words,holder,recipient,trigger,act in QUOTES:
 a.scope(sid,words,kind='quotation',holder_id=holder,description='Direct speech; local attribution remains distinct from narrator evidence.')
 a.scopes[sid].update(addressee_ids=[recipient] if recipient else [],utterance_event_id=f'ev{1000+trigger}' if trigger in words else f'ev{trigger+1}')
 F(list(words)[0],speech_act_kind=act,utterance_id=a.scopes[sid]['utterance_event_id'],addressee_ids=[recipient] if recipient else [],communication_channel='speech',quote_mode='direct')
for sid,words,kind,parent,holder,description in [
('s1',range(98,103),'imagined_scene','s0','e1','Bea pictures Grandpa holding his old mug; no new physical holding occurrence is asserted.'),
('s2',range(203,206),'conditional_antecedent','q8','e2','Continued pushing is only the warning antecedent.'),
('s3',range(206,211),'possible_consequence','q8','e2','A hole is possible, not created.'),
('s4',range(225,231),'possible_patch_outcome','q11','e2','Patch adhesion failure is a possibility, not an attempted repair.'),
('s5',range(231,242),'offered_alternative','q11','e2','Cutting apart and restarting are alternatives, not performed actions.'),
('s6',range(259,263),'conditional_antecedent','s0','e1','Starting again is contemplated, not actual.'),
('s7',range(263,276),'conditional_consequence','s0','e1','Insufficient time applies to the replacement-cup branch.'),
('s8',range(276,285),'considered_alternative','s0','e1','Giving a store-bought mug is an unchosen alternative.'),
('s9',range(285,292),'considered_alternative','s0','e1','Keeping the crooked cup is considered here, enacted later.'),
('s10',range(297,302),'desired_content','s0','e1','Earlier wished-for perfection is not a fact about the cup.'),
('s11',range(321,324),'unrealized_spill','s0',None,'Insufficient rim lean to spill is a capability assessment; no actual spilling.'),
('s12',range(373,375),'instruction_purpose','q14','e2','Desired comfortable feel after smoothing.'),
('s13',range(378,387),'inspection_content','q14','e2','Thickness all around is the requested check content, not an asserted check result.'),
]:a.scope(sid,words,kind=kind,parent=parent,holder_id=holder,description=description)

def status(scope):
 while scope:
  if a.scopes[scope]['kind']=='quotation':return 'attributed_claim'
  scope=a.scopes[scope].get('parent')
 return 'asserted'
def B(w,entity,value,**extra):
 scope=a.words[w]['scope_id'];return dict(entity_id=entity,scope_id=scope,assertion_status=status(scope),value=value,**extra)
def E(w,label,actor=None,patients=(),typ='other',fact='asserted',recipient=None,instruments=(),roles=None,**fields):
 a.event(f'ev{w+1}',w,label,type=typ,actor=actor,patients=patients,instruments=instruments,recipient=recipient,factuality=fact,roles=roles,**fields)
 F(w,assertion_status=status(a.words[w]['scope_id']))
def M(w,original,role='action',note='Same underlying event, mentioned again.'):
 a.mention_event(f'ev{original+1}',w,role=role,note=note)
 if role=='action':F(w,assertion_status=status(a.words[w]['scope_id']))

PROPS=[
(1,'Bea makes a cup for Grandpa Len.',[22,24,26,27],'s0'),
(2,'The new handle accommodates two of Grandpa’s fingers.',[52,53,56,57],'q1'),
(3,'The new cup stands steady.',[64,65,67,68],'q2'),
(4,'Grandpa carries his tea to the garden.',[69,70,72,76],'q2'),
(5,'Grandpa’s hands are around his old mug.',[98,99,100,102],'s1'),
(6,'The cup provides a place for Grandpa’s thumb.',[103,106,351,355,358],'q5'),
(7,'The dent is smoothed away.',[178,180,181,182],'s0'),
(8,'Bea continues pushing the clay wall.',[202,203,204,205],'s2'),
(9,'Bea makes a hole through the clay wall.',[206,208,210],'s3'),
(10,'Bea fills the dent with additional clay.',[212,213,215,218],'q9'),
(11,'The proposed patch sticks well.',[226,228,229,230],'s4'),
(12,'Bea cuts the whole current cup apart and starts again.',[231,234,237,238,240,241],'s5'),
(13,'Bea starts the cup again.',[259,260,261,262],'s6'),
(14,'There is time for the replacement cup to dry and be fired before the birthday.',[264,266,270,272,275,258],'s7'),
(15,'Bea gives Grandpa a store-bought mug.',[276,278,279,283],'s8'),
(16,'Bea keeps the crooked cup.',[286,288,291],'s9'),
(17,'The cup is just right.',[294,296,297,299,301],'s10'),
(18,'The cup wobbles on the workshop table.',[305,309,310,311,312],'s0'),
(19,'The rim leans enough to spill from.',[314,315,319,320,322],'s11'),
(20,'Bea leaves the dent as part of the cup.',[343,345,346,348],'q12'),
(21,'Bea makes the choice to retain the thumb hollow.',[362,364,365,366],'q14'),
(22,'Bea smooths the dent edges.',[368,370],'q14'),
(23,'The cup feels comfortable.',[371,372,373,374],'s12'),
(24,'The inside cup wall is thick all the way around.',[378,380,381,382,383,385,386],'s13'),
(25,'Bea checks the inside wall thickness all around.',[376,378,380,382,386],'q14'),
(26,'Ivo lends Bea his shaping rib.',[122,123,124,127,452,454,455],'q15'),
(27,'The cup side becomes dented.',[145,146,152,153,565,567],'s0'),
(28,'Bea turns the dent into a thumb place.',[403,406,409,570,571,572,576],'q17'),
(29,'The new handle is wide for Grandpa’s fingers.',[578,580,582,583],'q17'),
(30,'The hollow matches where Grandpa wants his thumb to rest.',[599,601,604,615,617,619,620,622],'q18'),
(31,'The finished cup stays steady on the kitchen table.',[629,631,634,635,636,637],'s0'),
(32,'Grandpa uses the cup with his thumb resting in the hollow.',[684,685,689,691,692],'s0'),
(33,'There is not enough time for a replacement cup to dry and be fired before the birthday.',[264,266,270,272,275,258],'s7'),
(34,'If Bea keeps pushing the clay wall, she might make a hole.',[202,203,204,205,206,207,208,210],'q8'),
]
for n,text,support,scope in PROPS:a.proposition(f'p{n}',text,support,scope_id=scope)

# Predicate identities; nonagentive changes retain no invented actor.
EVENTS=[
(3,'Bea walks to pottery workshop','e1',(),'move'),(22,'Bea makes cup for Grandpa','e1',('e4',),'other'),
(30,'Grandpa fingers grow stiff',None,('e8',),'state'),(44,'old handle is difficult for Grandpa to hold',None,('e7',),'state'),(48,'Grandpa holds old handle','e3',('e7',),'other','hypothetical'),
(50,'Bea wants a wide handle','e1',(),'state','reported'),(53,'new handle is wide enough',None,('e5',),'state','desired'),
(59,'Bea explains cup requirements','e1',(),'speak'),(65,'cup needs stable standing',None,('e4',),'state','reported'),(67,'cup stands steady',None,('e4',),'state','desired'),
(70,'Grandpa carries tea to garden','e3',('e62',),'move','reported'),(80,'Bea thinks about design criteria','e1',(),'other','hypothetical'),
(82,'Ivo encourages design thinking','e2',(),'speak'),(86,'Ivo places clay on wheel','e2',('e23',),'move'),
(97,'Bea imagines Grandpa holding mug','e1',(),'other'),
(109,'Bea centers clay','e1',('e23',),'move'),(113,'Bea pulls clay upward into cup','e1',('e23',),'other'),
(122,'Bea borrows shaping rib','e1',('e25',),'obtain'),(133,'Bea presses rib against cup wall','e1',('e27',),'other'),
(142,'shaping rib slips',None,('e25',),'move'),(146,'dent appears in clay',None,('e30',),'state'),(153,'cup side bulges',None,('e28',),'state'),(159,'cup rim becomes crooked',None,('e29',),'state'),
(164,'Bea stops wheel turning','e1',('e22',),'other'),(165,'Bea turns pottery wheel','e1',('e22',),'move'),
(171,'Bea dabs dent with sponge','e1',('e30',),'other'),(178,'Bea hopes to remove dent','e1',(),'state'),(180,'Bea smooths dent away','e1',('e30',),'repair','desired'),
(186,'cup wall shifts farther inward',None,('e27',),'move'),(191,'Ivo leans over','e2',(),'move'),(194,'Ivo looks at clay cup','e2',('e4',),'perceive'),
(197,'cup wall is still thick enough',None,('e27',),'state','reported'),(200,'Ivo reassures and warns Bea','e2',(),'speak'),
(205,'Bea continues pushing wall','e1',('e27',),'other','hypothetical'),(208,'Bea makes hole in wall','e1',('e27',),'other','hypothetical'),
(213,'Bea fills dent with more clay','e1',('e30','e35'),'repair','hypothetical'),(221,'Bea and Ivo try patching cup','e37',('e4',),'repair','hypothetical'),
(223,'Ivo discusses possible repairs','e2',(),'speak'),(229,'patch sticks well',None,('e36',),'state','negated'),
(234,'Bea slices whole cup apart','e1',('e4',),'other','hypothetical'),(240,'Bea starts cup again','e1',(),'other','hypothetical'),
(243,'Bea glances at clock','e1',('e38',),'perceive'),(251,'scheduled next kiln firing',None,(),'other','hypothetical'),
(252,'next kiln firing is last scheduled before birthday',None,(),'state'),(261,'Bea starts over with new cup','e1',('e39',),'other','hypothetical'),
(265,'time is available for replacement cup',None,(),'state','negated'),(272,'replacement cup dries',None,('e39',),'state','hypothetical'),(275,'replacement cup is fired',None,('e39',),'other','hypothetical'),
(278,'Bea gives Grandpa store-bought mug','e1',('e40',),'transfer','hypothetical'),(288,'Bea keeps crooked cup','e1',('e4',),'other','hypothetical'),
(296,'Bea wanted cup to be just right','e1',(),'state'),(301,'cup is just right',None,('e4',),'state','desired'),
(303,'Bea sets cup on workshop table','e1',('e4',),'move'),(312,'cup wobbles',None,('e4',),'move','negated'),(315,'cup rim leans slightly',None,('e29',),'state'),(322,'contents spill from cup rim',None,(),'move','hypothetical'),
(325,'Bea slips two fingers through handle','e1',('e14',),'move'),(333,'Bea rests thumb against dent','e1',('e16',),'move'),(341,'Bea hand settles comfortably',None,('e17',),'state'),
(346,'Bea leaves dent intact','e1',('e30',),'other','hypothetical'),(350,'Bea proposes keeping dent','e1',(),'speak'),(353,'dent provides place for Grandpa thumb',None,('e30',),'state','hypothetical'),
(361,'Ivo nods to Bea proposal','e2',(),'other'),(364,'Bea chooses to keep thumb hollow','e1',(),'other','hypothetical'),
(368,'Bea smooths dent edges','e1',('e31',),'repair','desired'),(373,'cup feels comfortable',None,('e4',),'state','desired'),(376,'Bea checks inside wall thickness','e1',('e27',),'perceive','desired'),(382,'inside wall is thick all around',None,('e27',),'state','hypothetical'),
(388,'Bea runs finger along inside wall','e1',('e15',),'move'),(403,'Bea eases sharp dent edges','e1',('e31',),'repair'),
(411,'Bea turns cup handle','e1',('e5',),'move'),(416,'handle faces hollow',None,('e5',),'state'),(426,'cup still looks crooked',None,('e4',),'state'),(432,'crookedness seems directed toward hand',None,('e4',),'state'),
(440,'Bea finishes cup shaping','e1',('e4',),'other'),(443,'Ivo holds hand out for rib','e2',('e18',),'move'),
(457,'Bea thanks Ivo for rib loan','e1',(),'speak'),(458,'Bea wipes clay from rib handle','e1',('e24',),'other'),(465,'Bea returns shaping rib','e1',('e25',),'transfer'),
(469,'cup dries on shelf',None,('e4',),'state'),(474,'cup goes into kiln',None,('e4',),'move'),(484,'Bea returns to workshop','e1',(),'move'),
(489,'cup is pale after first firing',None,('e4',),'state'),(491,'cup is hard after first firing',None,('e4',),'state'),
(493,'Bea dips cup in blue glaze','e1',('e4',),'other'),(499,'Bea turns cup during glazing','e1',('e4',),'move'),(506,'every cup side is coated in glaze',None,('e4',),'state'),(509,'blue glaze gathers in thumb hollow',None,('e45',),'move'),
(521,'cup undergoes second firing',None,('e4',),'other'),(524,'cup stands on pickup table',None,('e4',),'state'),(532,'cup handle tilts slightly',None,('e5',),'state'),
(538,'Bea carries cup home','e1',('e4',),'move'),(544,'box is padded with newspaper',None,('e47',),'state'),
(551,'Grandpa opens gift box','e3',('e47',),'other'),(560,'gift is a cup',None,('e4',),'state','reported'),(562,'Bea explains cup features','e1',(),'speak'),
(571,'Bea makes dent into thumb place','e1',('e30',),'repair','reported'),(580,'cup handle is wide for Grandpa fingers',None,('e5',),'state','reported'),
(585,'Grandpa turns cup in hands','e3',('e4',),'move'),(592,'Grandpa slips two fingers through handle','e3',('e9',),'move'),
(599,'Grandpa sets thumb in hollow','e3',('e11',),'move'),(607,'Grandpa knuckles rest against clay',None,('e12',),'state'),
(614,'Grandpa appreciates thumb fit','e3',(),'speak'),(620,'Grandpa wants thumb at that position','e3',(),'state','reported'),(622,'Grandpa thumb goes to hollow',None,('e11',),'move','desired'),
(624,'Grandpa pours water into cup','e3',('e60',),'transfer'),(629,'Grandpa sets cup on kitchen table','e3',('e4',),'move'),(636,'cup stays steady',None,('e4',),'state'),
(640,'Grandpa takes cup outside','e3',('e4',),'move'),(643,'cup is filled with tea',None,('e4',),'state'),(647,'Grandpa carries cup to garden bench','e3',('e4',),'move'),
(657,'Bea finds cup on garden bench','e1',('e4',),'perceive'),(671,'damp earth ring marks table',None,('e53',),'state'),(678,'Grandpa kneels among bean plants','e3',(),'state'),
(685,'Grandpa thumb rests in hollow',None,('e11',),'state'),(692,'Grandpa drinks from cup','e3',(),'other'),(698,'sunlight catches water bead',None,('e59',),'state'),
]
for args in EVENTS:E(*args)
# Explicit actual utterances without a reporting verb get a separate event.
seen=set()
for sid,words,holder,recipient,trigger,act in QUOTES:
 eid=a.scopes[sid]['utterance_event_id']
 if eid in seen:continue
 seen.add(eid)
 if eid not in a.events:
  a.event(eid,trigger,act.replace('_',' '),type='speak',actor=holder,recipient=recipient,scope='s0',primary=False,support=list(words))
 else:a.events[eid]['recipient_id']=recipient;F(trigger,recipient_id=recipient) if recipient else None
# First firing is entailed by second firing + intervening fired state, not an invented operator.
a.event('ev1001',474,'cup undergoes first firing',type='other',patients=['e4'],scope='s0',primary=False,support=[474,477,489,491,520,521])
M(454,122,note='Lending recalls the same loan narrated as Bea borrowing; source/giver perspective does not create a second transfer.')
M(567,146,note='Bea recalls the same dent that appeared when the rib slipped, not a new damage event.')

# Explicit participant anchors, selected in each local clause.
ROLES=[
(3,[2],[],{}),(22,[19],[24],{'beneficiary':[26,27]}),(30,[],[29],{}),(44,[],[38],{'experiencer':[46]}),(48,[46],[38],{}),
(50,[49],[],{}),(53,[],[52],{}),(59,[58],[],{'recipient':[60,61]}),(65,[],[64],{}),(67,[],[64],{}),(70,[69],[72],{'destination':[76]}),
(82,[83,84],[],{}),(86,[85],[88,90],{'destination':[93]}),(97,[96],[],{}),
(109,[108],[111],{}),(113,[108],[114],{'result':[119]}),(122,[121],[127],{'source':[123,124]}),(133,[121],[139],{'instrument':[134]}),
(142,[],[141],{}),(146,[],[145],{'material':[149]}),(153,[],[152],{'landmark':[155]}),(159,[],[158],{}),
(164,[163],[167],{}),(165,[163],[167],{}),(171,[170],[173],{'instrument':[177]}),(178,[170],[],{}),(180,[170],[181],{}),(186,[],[185],{}),
(191,[189,190],[],{}),(194,[189,190],[],{}),(197,[],[195],{}),(200,[199],[],{}),(205,[203],[],{}),(208,[206],[],{'result':[210]}),
(213,[212],[215,218],{}),(221,[219],[],{}),(223,[222],[],{}),(229,[],[226],{}),(234,[231],[237],{}),(240,[231],[],{}),
(243,[242],[246],{}),(261,[260],[270],{}),(272,[],[270],{}),(275,[],[270],{}),(278,[276],[283],{'recipient':[279]}),
(288,[286],[291],{}),(296,[294],[],{}),(301,[],[297],{}),(303,[302],[305],{'destination':[309]}),(312,[],[310],{}),(315,[],[314],{}),
(325,[324],[327],{'passage':[331]}),(333,[324],[335],{'landmark':[338]}),(341,[],[340],{}),
(346,[345],[348],{}),(350,[349],[],{}),(353,[],[351],{'beneficiary':[357]}),(361,[359,360],[],{}),(364,[362],[],{}),(368,[],[370],{}),(373,[],[372],{}),(376,[],[380],{}),(382,[],[380],{}),
(388,[387],[390],{'contact_surface':[393]}),(403,[402],[406],{'instrument':[398,401]}),(411,[410],[413],{}),(416,[],[415],{'target':[418]}),(426,[],[424],{}),
(440,[439],[],{}),(443,[441,442],[446],{'requested_object':[450]}),(457,[456],[],{'recipient':[452]}),(458,[456],[460],{'source':[463]}),(465,[456],[466],{}),
(469,[],[468],{'location':[472]}),(474,[],[468],{'destination':[477],'companions':[481]}),(484,[483],[],{}),(489,[],[487],{}),(491,[],[487],{}),
(493,[492],[494],{'medium':[498]}),(499,[492],[500],{}),(506,[],[504],{}),(509,[],[508],{'destination':[513]}),
(521,[],[523],{}),(524,[],[523],{'location':[528]}),(532,[],[531],{}),(538,[537],[539],{'container':[543],'destination':[540]}),(544,[],[543],{'padding':[546]}),
(551,[550],[553],{'location':[557]}),(560,[],[558],{}),(562,[561],[],{}),(571,[570],[572],{}),(580,[],[578],{'beneficiary':[582]}),
(585,[584],[587],{'instrument':[590]}),(592,[591],[594],{'passage':[597]}),(599,[591],[601],{'destination':[604]}),(607,[],[606],{'surface':[611]}),
(614,[613],[],{}),(620,[],[],{}),(622,[],[619],{}),(624,[623],[626],{}),(629,[623],[631],{'destination':[634]}),(636,[],[635],{}),
(640,[639],[641],{}),(643,[],[641],{'contents':[645]}),(647,[639],[648],{'destination':[652]}),
(657,[656],[659],{'location':[662]}),(671,[],[673],{'mark':[667]}),(678,[676],[],{'surroundings':[682]}),(685,[],[684],{'location':[689]}),(692,[691],[],{}),(698,[],[701],{'light_source':[697]}),
]
for trigger,actors,patients,other in ROLES:
 for role,words in [('actor',actors),('patient',patients),*other.items()]:
  if words:a.mention_event(f'ev{trigger+1}',words,role=role,note='Explicit local argument, preserving the stated relation.')
# Add complete participants to the authoritative event table and scalar trigger.
for w,instruments,recipient in [(133,['e25'],None),(171,['e32'],None),(388,['e15'],None),(403,['e32'],None),(585,['e10'],None),(278,[],'e3'),(465,[],'e2')]:
 a.events[f'ev{w+1}'].update(instruments=instruments,recipient_id=recipient)
 F(w,instruments=instruments)
 if recipient:F(w,recipient_id=recipient)
# The late loan mention was constructed before these enrichments; it retains the same actor and loan object.

# Form features derive from the explicitly authored contextual POS, never POS guesses.
for w,row in enumerate(a.words):
 if row['pos']=='det':
  token=row['token'].casefold()
  kind='possessive' if token in {'his','her','its','your','my'} else 'definite_article' if token=='the' else 'indefinite_article' if token in {'a','an'} else 'demonstrative' if token in {'this','that'} else 'quantificational'
  F(w,determiner_kind=kind)
  if token in {'the','a','an'}:F(w,definiteness='definite' if token=='the' else 'indefinite')
  if kind=='possessive':F(w,possessive_construction='possessive_determiner')
 if row['pos']=='pron' and row.get('entity_id'):
  F(w,mention_form='pronoun',antecedent_id=row['entity_id'])
 if row['pos']=='adp':F(w,dependency_relation='prepositional_marker')
 if row['pos']=='part' and row['token'].casefold()=='to':F(w,dependency_relation='infinitival_marker')
 if row['pos']=='conj':
  token=row['token'].casefold()
  if token in {'and','but','or'}:F(w,coordinator_type={'and':'conjunctive','but':'adversative','or':'alternative'}[token])
for w in [2,58,96,163,242,324,387,456,483,537,561,656,12,13,60,61,83,84,123,124,189,190,359,360,441,442,26,27,69,98,257,548,584,664,676]:F(w,mention_form='proper_name')
for w in [12,60,83,123,189,359,441]:F(w,proper_name_structure='title_plus_name')
for w in [13,98,124,151,248,257,548,664,706]:F(w,possessive_construction='genitive_np',genitive_realization='apostrophe_s')
for w in [18,29,34,57,78,99,327,370,406,481,583,590,594,606,682]:F(w,grammatical_number='plural')
for w in [49,212,345,570]:F(w,grammatical_person=1,grammatical_number='singular',grammatical_case='nominative')
F(219,grammatical_person=1,grammatical_number='plural',group_members=['e1','e2'],split_antecedent_ids=['e1','e2'])
for w in [203,206,231,362,452]:F(w,grammatical_person=2)
for w in [19,85,108,121,170,199,222,260,276,286,294,302,349,402,410,439,492,550,591,613,623,639,691]:F(w,grammatical_person=3,grammatical_number='singular',grammatical_case='nominative')
for w in [46,279]:F(w,grammatical_case='accusative',grammatical_person=3)
for w in [195,558]:F(w,contraction_expansion=['it','is'])
F(615,contraction_expansion=['that','is'])
F(264,contraction_expansion=['would','not'],lemma='will')
F(311,contraction_expansion=['did','not'],lemma='do')
F(263,expletive_reference=True)
for w in [17,56,326,593]:F(w,cardinal_value=3 if w==17 else 2)
F(520,ordinal_rank=2,temporal_iteration_index=2)
F(535,cardinal_value=1)
F(0,quantifier_domain_restriction={'schedule':'Thursday','event_id':'ev4'})
F(1,calendar_day_name='Thursday',temporal_recurrence={'event_id':'ev4','period':'week','weekday':'Thursday','exact_count_unknown':True})
F(18,measure_unit='week',temporal_duration={'event_id':'ev23','value':3,'unit':'week'},evidence=[16,17,18,20,21,22],note='Three weeks of cup-making activity, not three uninterrupted weeks manipulating one clay lump.')
F(34,temporal_recurrence={'event_id':'ev31','period':'morning','pattern':'recurring'},temporal_granularity='part_of_day')
for w,relation in [(256,'before'),(438,'when'),(464,'before'),(482,'when'),(502,'until'),(518,'after'),(690,'overlap')]:F(w,temporal_signal_relation=relation)
for w in [120,473,569,638]:F(w,temporal_order_cue='then')
F(183,discourse_relation_kind='unexpected_result',discourse_relation_source_id='p7',discourse_relation_target_id='ev187')
F(249,temporal_order_cue='next_scheduled_occurrence')
F(254,temporal_order_cue='last_before_birthday')
F(258,time_expression_id='time_birthday',temporal_granularity='day')
F(549,time_expression_id='time_birthday',time_anchor_id='time_birthday',temporal_granularity='day')
F(655,temporal_deixis='next_morning',time_anchor_id='time_birthday',temporal_granularity='part_of_day')

# Explicit tense/form sets selected from the actual constructions.
FINITE_PAST=[3,20,21,30,43,59,82,86,97,109,113,122,133,142,146,153,159,164,171,186,191,200,223,243,252,261,264,265,277,287,295,296,303,311,315,325,333,341,350,361,388,403,411,416,426,432,440,443,457,469,474,484,488,493,505,509,524,538,551,562,566,571,585,592,599,607,614,620,624,629,636,640,647,657,671,677,692,698]
for w in FINITE_PAST:
 if a.words[w]['pos']=='v':F(w,tense='past',verb_form='finite')
for w in [50,65,70,204,363,373,381,579]:F(w,tense='present',verb_form='finite')
for w in [48,67,80,194,205,208,213,221,229,234,240,272,278,288,299,312,322,346,353,364,368,376,434,622]:F(w,verb_form='base')
for w in [22,165,178,454,458,465,499,678,685]:F(w,verb_form='gerund_participle')
for w in [275,506,532,544,567,643]:F(w,verb_form='past_participle')
F(22,aspect='perfect_progressive',perfect_auxiliary_id=a.anchor(20),progressive_auxiliary_id=a.anchor(21))
F(296,aspect='perfect',verb_form='past_participle',perfect_auxiliary_id=a.anchor(295))
F(275,voice='passive',passive_auxiliary_id=a.anchor(274))
F(506,voice='passive',passive_auxiliary_id=a.anchor(505))
F(567,voice='passive',passive_auxiliary_id=a.anchor(566))
F(678,aspect='progressive',progressive_auxiliary_id=a.anchor(677))
for w in [368,376]:F(w,mood='imperative',imperative_subject_status='understood_addressee',subject_controller_id='e1')
F(165,temporal_end_bound={'event_id':'ev166','at_event_id':'ev165'})
F(164,event_interruption=B(164,'e1',{'affected_event_id':'ev166','cue':'stopped_turning','trigger_event_id':'ev165'}))
# Actual subjects are not mechanically copied from semantic actors.
SUBJECTS={3:'e1',22:'e1',30:'e8',44:'e7',48:'e3',50:'e1',53:'e5',59:'e1',65:'e4',67:'e4',70:'e3',82:'e2',86:'e2',97:'e1',109:'e1',113:'e1',122:'e1',133:'e1',142:'e25',146:'e30',153:'e28',159:'e29',164:'e1',171:'e1',178:'e1',186:'e27',191:'e2',197:'e27',200:'e2',205:'e1',208:'e1',213:'e1',221:'e37',223:'e2',229:'e36',234:'e1',240:'e1',243:'e1',261:'e1',272:'e39',275:'e39',278:'e1',288:'e1',296:'e1',301:'e4',303:'e1',312:'e4',315:'e29',325:'e1',333:'e1',341:'e17',346:'e1',350:'e1',353:'e30',361:'e2',364:'e1',373:'e4',382:'e27',388:'e1',403:'e1',411:'e1',416:'e5',426:'e4',440:'e1',443:'e2',457:'e1',469:'e4',474:'e4',484:'e1',489:'e4',491:'e4',493:'e1',506:'e4',509:'e45',524:'e4',532:'e5',538:'e1',544:'e47',551:'e3',560:'e4',562:'e1',567:'e28',571:'e1',580:'e5',585:'e3',592:'e3',599:'e3',607:'e12',614:'e3',620:'e11',622:'e11',624:'e3',629:'e3',636:'e4',640:'e3',643:'e4',647:'e3',657:'e1',671:'e55',678:'e3',685:'e11',692:'e3',698:'e58'}
for w,eid in SUBJECTS.items():F(w,grammatical_subject_id=eid)
for w,eid in {22:'e4',86:'e23',109:'e23',113:'e23',122:'e25',133:'e25',165:'e22',171:'e30',180:'e30',208:'e34',213:'e30',234:'e4',278:'e40',288:'e4',303:'e4',325:'e14',333:'e16',346:'e30',368:'e31',388:'e15',403:'e31',411:'e5',443:'e18',454:'e25',458:'e24',465:'e25',493:'e4',499:'e4',538:'e4',551:'e47',571:'e30',585:'e4',592:'e9',599:'e11',624:'e60',629:'e4',640:'e4',647:'e4',657:'e4',671:'e53',698:'e59'}.items():F(w,grammatical_object_id=eid)
F(278,indirect_object_id='e3')
for w,eid in {4:'e20',11:'e19',39:'e6',55:'e8',74:'e51',91:'e22',100:'e6',125:'e25',136:'e27',147:'e23',154:'e30',174:'e32',216:'e35',244:'e38',307:'e41',328:'e5',336:'e30',356:'e11',391:'e27',400:'e32',408:'e30',417:'e30',447:'e25',461:'e26',470:'e42',475:'e43',478:'e44',495:'e45',510:'e30',525:'e46',541:'e47',545:'e48',554:'e50',581:'e8',588:'e10',595:'e5',602:'e30',608:'e23',632:'e50',644:'e61',649:'e52',660:'e52',663:'e54',674:'e4',679:'e57',686:'e30',693:'e13',704:'e29'}.items():
 if a.words[w]['pos']=='adp':F(w,prepositional_object_id=eid)
# Qualitative lexical distinctions with narrow meanings.
for w,gloss in {127:'wooden pottery shaping tool, not an anatomical rib',38:'grip on old mug',97:'imagine a scene, not make a physical picture',197:'wall has sufficient remaining thickness according to Ivo',251:'scheduled heating of pottery in a kiln',262:'restart rather than a location above',282:'bought from a shop; part of store-bought modifier',288:'retain and use the crooked cup, not merely postpone discarding',341:'hand reaches a comfortable resting fit',432:'figurative appearance of accommodating a hand',454:'the same temporary loan viewed from Ivo as lender',521:'second kiln-heating stage, following glazing',620:'personified thumb preference expresses Grandpa’s comfortable fit',698:'sunlight illuminates/reflexively highlights the water bead, not physical capture'}.items():F(w,lexical_gloss=gloss)
F(437,generic_reference=True,referent_kind='kind',lexical_gloss='a schematic hand accommodated by the cup shape, not a newly introduced physical hand')
F(517,generic_reference=True,figurative_mapping={'target_id':'e45','source_image':'a little pool','kind':'simile','literal_event':False})
F(432,figurative_mapping={'target_id':'e4','source_image':'crookedness pointing toward a hand','kind':'metaphor','literal_event':False},evidence=[424,427,431,432,434,437],note='Describes the shape appearing suited to a hand, not an intentional gesture.')
F(620,reference_metonymic_link={'literal_id':'e11','related_id':'e3','relation':'body_part_personified_preference'},figurative_mapping={'target_id':'e11','source_image':'thumb wanting a destination','kind':'personification','literal_event':False},evidence=[615,617,619,620,622],note='Grandpa evaluates the thumb position; no autonomous mind is assigned to the thumb.')

# Body parts, tool parts and cup parts retain their physical referent bindings.
for w,part,whole in [
(29,'e8','e3'),(38,'e7','e6'),(52,'e5','e4'),(99,'e10','e3'),(106,'e11','e3'),(139,'e27','e4'),(152,'e28','e4'),(158,'e29','e4'),
(327,'e14','e1'),(335,'e16','e1'),(340,'e17','e1'),(358,'e11','e3'),(370,'e31','e30'),(380,'e27','e4'),(390,'e15','e1'),(398,'e33','e32'),
(413,'e5','e4'),(446,'e18','e2'),(463,'e26','e25'),(531,'e5','e4'),(590,'e10','e3'),(594,'e9','e3'),(601,'e11','e3'),(606,'e12','e3'),(684,'e11','e3'),(695,'e13','e3'),(708,'e29','e4')]:F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
F(145,spatial_region=B(145,'e30',{'region_of':'e4','kind':'dent_in_wall'}))
F(338,alias_names=['dent','hollow','thumb rest'],evidence=[145,173,338,348,418,422,513,576,604],note='One physical indentation is retained and repurposed; the later function does not erase earlier damage.')
F(331,evidence_missing={'needed':'handle_formation_or_attachment_transition','known_endpoint':'wide_handle_present'},evidence=[113,119,331],note='Handle construction is not narrated. No creation or attachment event is invented.')

# Scoped physical states and relations: properties attach to their stated carrier.
F(31,attributes=[{'name':'bodily_flexibility','value':'fingers_stiff_in_mornings'}],evidence=[28,29,30,31,34],note='Explicit stiffness, without a diagnosis or invented permanence.')
F(37,object_shape=B(37,'e7',{'dimension':'handle_thickness','value':'thin'}))
F(44,affordance_grasping=B(44,'e7',{'actor_id':'e3','difficulty':'hard_to_hold'}))
F(53,object_shape=B(53,'e5',{'dimension':'handle_opening','value':'wide_enough_for_two_fingers'},factuality='desired'))
F(68,object_stability=B(68,'e4','steady',factuality='desired'))
F(86,spatial_support=B(86,'e23',{'supported_by':'e22'}))
F(118,object_shape=B(118,'e4','round'))
F(113,event_result_entity=B(113,'e4',{'created_from':'e23','event_id':'ev114'}),event_state_change=B(113,'e23',{'result_form':'cup','result_entity_id':'e4'}))
F(125,material_composition=B(125,'e25','wood'))
F(129,object_surface_condition=B(129,'e25','smooth'))
F(130,object_shape=B(130,'e25','curved'))
F(135,event_manner=B(135,'e1',{'event_id':'ev134','manner':'gently'}))
F(133,spatial_contact=B(133,'e25',{'touching':'e27','event_id':'ev134'}),event_instrument_binding=B(133,'e25',{'event_id':'ev134','used_on':'e27'}))
F(144,object_shape=B(144,'e30',{'depth':'deep','measurement_unspecified':True}))
F(146,causal_parent={**B(146,'e30',{'cause':'ev143','effect':'ev147'}),'assertion_status':'candidate'},evidence=[133,141,142,145,146],note='Adjacent slip and dent strongly suggest causation; the mechanism is not separately stated.')
F(153,object_shape=B(153,'e28','bulged'),spatial_configuration=B(153,'e28',{'relation':'beside','landmark':'e30'}))
F(162,object_shape=B(162,'e29','slightly_crooked'))
F(176,object_moisture=B(176,'e32','damp'))
F(186,motion_direction=B(186,'e27',{'direction':'inward','frame':'cup'}),motion_relative_displacement=B(186,'e27',{'direction':'farther_inward_than_before','trigger_event_id':'ev187'}))
F(197,object_shape=B(197,'e27',{'thickness':'sufficient','criterion':'avoid_hole_at_current_state'}))
F(229,material_adhesion=B(229,'e36',{'sticks_well':False},factuality='hypothetical'),evidence=[226,227,228,229,230],note='Possible failure of a proposed patch, not actual adhesion test evidence.')
F(303,spatial_support=B(303,'e4',{'supported_by':'e41'}),event_manner=B(303,'e1',{'event_id':'ev304','manner':'carefully'}))
F(312,object_stability=B(312,'e4','does_not_wobble'))
F(315,spatial_orientation=B(315,'e29',{'tilt':'slight','frame':'cup'}))
F(319,containment_spill_risk=B(319,'e4',{'orientation_insufficient_to_spill':True,'measurement_unspecified':True}),evidence=[314,315,319,320,322],note='Text describes a limited rim lean. No actual water-filled test has occurred yet.')
F(325,containment_partial=B(325,'e14',{'through_opening_of':'e5'}))
F(333,spatial_contact=B(333,'e16',{'touching':'e30'}))
F(341,attributes=[{'name':'fit','value':'Bea_hand_settles_comfortably'}])
F(355,affordance_supporting=B(355,'e30',{'object_id':'e11','can_support':True},factuality='hypothetical'))
F(397,material_hardness=B(397,'e33','soft'))
F(405,object_edge_condition=B(405,'e31','sharp_before_easing'))
F(403,event_state_change=B(403,'e31',{'before':'sharp','after':'eased_smooth','event_id':'ev404'}),object_edge_condition=B(403,'e31','eased'),event_instrument_binding=B(403,'e32',{'event_id':'ev404','used_on':'e31','part_id':'e33'}))
F(416,spatial_facing_target=B(416,'e5',{'target':'e30','description':'faces_hollow_opposite_thumb_rest'}),evidence=[413,415,416,418,419,422],note='Retains the source wording; exact handle rotation geometry is not supplied.')
F(427,object_shape=B(427,'e4','crooked'))
F(458,object_cleanliness=B(458,'e26',{'clay_wiped_off':True}),event_state_change=B(458,'e24',{'removed_from':'e26','event_id':'ev459'}))
F(469,object_moisture=B(469,'e4','dry'),spatial_support=B(469,'e4',{'supported_by':'e42'}))
F(474,containment_direct=B(474,'e4',{'container':'e43'}),event_time_relation={'earlier':'ev470','later':'ev475','relation':'before'},evidence=[469,472,473,474,477],note='Drying and kiln entry are separate from actual first firing.')
F(489,appearance_color=B(489,'e4','pale',factuality='asserted'))
F(491,material_hardness=B(491,'e4','hard'))
F(497,appearance_color=B(497,'e45','blue',factuality='asserted'))
F(506,object_surface_condition=B(506,'e4',{'coating':'e45','coverage':'every_side'}),quantifier_domain_restriction={'domain':'cup_sides','entity_id':'e4','coverage':'all'})
F(509,containment_partial=B(509,'e45',{'collected_in':'e30'}))
F(521,event_time_relation={'earlier':'ev494','later':'ev522','relation':'before'},temporal_iteration_index=2,evidence=[493,498,506,518,520,521],note='Second firing follows glaze application; no duration or temperature is invented.')
F(524,spatial_support=B(524,'e4',{'supported_by':'e46'}))
F(532,spatial_orientation=B(532,'e5',{'tilt':'slightly_to_one_side','side_unspecified':True}))
F(538,containment_direct=B(538,'e4',{'container':'e47'}),motion_destination=B(538,'e4',{'destination':'e49','carrier':'e1'}))
F(544,containment_contents=B(544,'e47',{'padding':'e48','carried_object':'e4'}))
F(551,object_openness=B(551,'e47','open'))
F(580,affordance_grasping=B(580,'e5',{'actor_id':'e3','accommodates':'e8','opening':'wide'}))
F(585,possession_holder=B(585,'e4',{'holder':'e3'}))
F(592,containment_partial=B(592,'e9',{'through_opening_of':'e5'}))
F(599,spatial_contact=B(599,'e11',{'touching':'e30'}),affordance_supporting=B(599,'e30',{'object_id':'e11','can_support':True}))
F(607,spatial_contact=B(607,'e12',{'touching':'e23'}))
F(610,object_surface_condition=B(610,'e23','smooth'))
F(624,containment_direct=B(624,'e60',{'container':'e4'}))
F(629,spatial_support=B(629,'e4',{'supported_by':'e50'}))
F(637,object_stability=B(637,'e4','steady'))
F(643,containment_contents=B(643,'e4',{'contents':['e61']}),evidence=[640,641,643,645],note='Tea-filled endpoint is stated. Emptying the test water and pouring tea are not narrated as separate acts.')
F(647,motion_destination=B(647,'e4',{'destination':'e52','carrier':'e3'}))
F(657,spatial_support=B(657,'e4',{'supported_by':'e52'}),spatial_configuration=B(657,'e4',{'relation':'beside','landmark':'e54'}))
F(669,object_moisture=B(669,'e56','damp'))
F(671,spatial_configuration=B(671,'e53',{'relation':'under','landmark':'e4'}),evidence_missing={'needed':'bench_table_layout_or_intervening_cup_movement'},evidence=[659,660,662,671,673,674,675],note='Bench placement and table-under-cup descriptions are both retained; the source supplies no movement or identity bridge.')
F(678,motion_posture=B(678,'e3','kneeling'),spatial_surroundings=B(678,'e3',{'landmarks':['e57']}))
F(685,spatial_contact=B(685,'e11',{'touching':'e30'}),evidence_missing={'needed':'pickup_transition_after_Bea_finds_cup_on_bench'},evidence=[657,659,662,684,685,689,692],note='Later drinking is explicit, but no pickup transition is narrated.')
F(688,appearance_color=B(688,'e30','blue',factuality='asserted'))
F(698,lexical_gloss='sunlight highlights the water bead; no claim that cup or bead emits light',spatial_configuration=B(698,'e59',{'relation':'on','landmark':'e29'}))
F(707,object_shape=B(707,'e29','crooked'))

# Goals, modalities, alternatives and communications retain positive contents.
F(22,goal_owner_id='e1',goal_content_id='p1',goal_beneficiary_ids=['e3'],goal_status='in_progress',goal_polarity='achieve',event_beneficiary=B(22,'e4',{'beneficiary_id':'e3','event_id':'ev23'}))
F(50,goal_owner_id='e1',goal_content_id='p2',goal_status='active',goal_polarity='achieve',goal_beneficiary_ids=['e3'],intention_publicity='communicated')
F(65,goal_owner_id='e1',goal_content_id='p3',goal_status='active',goal_polarity='achieve',goal_beneficiary_ids=['e3'],goal_motivation={'holder_id':'e1','content_id':'p3','reason':'p4','scope_id':'q2','assertion_status':'attributed_claim'},evidence=[64,65,67,68,69,70,72,76],note='Bea presents stability in connection with Grandpa carrying tea; no universal carrying guarantee.')
F(97,imaginer_id='e1',imagined_content_id='p5',imagined_world_id='imagined_old_mug_grip',evidence=[96,97,98,99,102],note='Imagination has an actual mental event and a separately scoped pictured scene.')
F(103,goal_owner_id='e1',goal_content_id='p6',goal_status='proposed',goal_polarity='achieve',goal_beneficiary_ids=['e3'],sentence_fragment_type='nominal_design_addition')
F(168,affect_experiencer_id='e1',affect_kind='dismay',affect_expression_channel='exclamation',affect_valence='unpleasant',assertion_status='candidate',affect_target_id='p27',evidence=[145,146,159,162,164,168,169],note='Oh no after the dent licenses a tentative local dismay reading, not an enduring trait or intensity.')
F(178,goal_owner_id='e1',goal_content_id='p7',goal_status='active',goal_polarity='achieve')
F(186,event_attempt_outcome=B(186,'e1',{'attempt_event_id':'ev172','intended_content_id':'p7','outcome_event_id':'ev187','outcome':'wall_moves_further_inward'}),evidence=[171,178,180,181,183,185,186,187,188],note='The intended smoothing-away and actual deeper displacement are distinct.')
F(202,conditional_antecedent_id='p8',conditional_consequent_id='p9',scope_operator='conditional')
F(207,modal_auxiliary_class='possibility_family',modal_base={'holder_id':'e2','kind':'possible_consequence','content_id':'p9','condition_id':'p8'})
F(201,warning_hazard_id='p9')
F(211,modal_auxiliary_class='possibility_family',modal_base={'holder_id':'e1','kind':'repair_feasibility_question','content_id':'p10'},question_requested_slot='whether_filling_dent_is_feasible',question_answer_status='answered_with_caution')
F(220,modal_auxiliary_class='possibility_family',modal_base={'holder_id':'e2','kind':'tentative_joint_option','content_id':'p10'})
F(221,plan_commitment_status='tentative',offer_content_id='p10',dialogue_response_to_id='ev1211')
F(227,modal_auxiliary_class='possibility_family',modal_base={'holder_id':'e2','kind':'possible_failure','content_id':'p11'})
F(228,negation_marker_form='not',proposition_polarity='negative',negation_scope_id='p11')
F(232,modal_auxiliary_class='possibility_family',modal_base={'holder_id':'e2','kind':'offered_alternative','content_id':'p12'})
F(259,conditional_antecedent_id='p13',conditional_consequent_id='p33',scope_operator='conditional',evidence=[259,260,261,264,266,270,272,275],note='The conditional consequent is negative time availability; the local negation operator separately targets positive p14.')
F(264,modal_auxiliary_class='prediction_family',negation_marker_form='not',proposition_polarity='negative',negation_scope_id='p14')
F(265,causal_preventing_condition=B(265,'e39',{'blocked':'replacement_cup_ready_by_birthday','condition':'insufficient_drying_and_firing_time','branch':'p13'}))
F(277,modal_auxiliary_class='possibility_family',modal_base={'holder_id':'e1','kind':'considered_option','content_id':'p15'})
F(287,modal_auxiliary_class='possibility_family',modal_base={'holder_id':'e1','kind':'considered_option','content_id':'p16'})
F(285,disjunction_alternatives=['p15','p16'],discourse_alternative_set=['p13','p15','p16'])
F(296,goal_owner_id='e1',goal_content_id='p17',goal_polarity='achieve',goal_status='earlier_desired_standard')
F(311,proposition_polarity='negative',negation_marker_form='not',negation_scope_id='p18')
F(319,proposition_polarity='negative',negation_marker_form='not',negation_scope_id='p19')
F(343,question_requested_slot='acceptability_of_retaining_dent',question_answer_status='answered_by_permission',utterance_content_id='p20')
F(352,modal_auxiliary_class='possibility_family',modal_base={'holder_id':'e1','kind':'possible_use','content_id':'p6'})
F(361,dialogue_response_to_id='ev351',request_acceptance_status='acknowledged_with_permission')
F(363,modal_auxiliary_class='possibility_family',modal_base={'holder_id':'e2','kind':'permission','content_id':'p21'})
F(364,permission_grantor_id='e2',permission_recipient_id='e1',permission_content_id='p21',permission_status='granted')
F(368,request_action_id='ev369',utterance_content_id='p22',goal_owner_id='e1',goal_content_id='p23',goal_status='instructed',goal_polarity='achieve')
F(376,request_action_id='ev377',utterance_content_id='p25',question_requested_slot='whether_inside_wall_is_thick_all_around')
F(382,object_shape=B(382,'e27',{'thickness':'thick_all_around'},factuality='hypothetical'))
F(388,event_completion_evidence={**B(388,'e1',{'affected_event_id':'ev377','trigger_event_id':'ev389','cue':'runs_finger_along_inside'}),'assertion_status':'candidate'},evidence=[376,380,382,387,388,390,393],note='Running a finger along the inside plausibly carries out the requested check; no explicit uniform-thickness verdict is supplied.')
F(403,goal_owner_id='e1',goal_content_id='p22',goal_status='achieved',plan_revision={'holder_id':'e1','earlier_goal':'p7','new_goal':'p20','support_events':['ev351','ev404'],'scope_id':'s0','assertion_status':'candidate'},evidence=[178,180,346,348,368,403,406,409],note='Bea keeps and eases the dent instead of removing it. Plan revision is a supported interpretation, not a separately narrated mental declaration.')
F(440,event_completion_evidence=B(440,'e1',{'affected_event_id':'ev404','trigger_event_id':'ev441','cue':'finished_shaping'}))
F(122,possession_borrower=B(122,'e25',{'borrower':'e1'}),possession_lender=B(122,'e25',{'lender':'e2'}),possession_holder=B(122,'e25',{'holder':'e1'}),transfer_kind=B(122,'e25','loan'))
F(454,retrieval_inverse_relation={'source_event_id':'ev123','source_relation':'borrow_from','inverse_relation':'lend_to','borrower_id':'e1','lender_id':'e2','object_id':'e25','scope_id':'q15','assertion_status':'attributed_claim'},subject_controller_id='e2',evidence=[121,122,123,124,127,452,454,455],note='The local lender is Ivo; the canonical loan event remains anchored by Bea borrowing.')
F(465,possession_holder=B(465,'e25',{'holder':'e2'}),possession_return_target=B(465,'e25',{'return_to':'e2'}),transfer_kind=B(465,'e25','return'),transfer_completion=B(465,'e25',{'complete':True,'recipient_id':'e2'}))
F(251,temporal_deadline={'event_id':'ev252','before':'time_birthday','status':'scheduled_last_before_birthday'},evidence=[249,250,251,252,254,255,256,257,258],note='Scheduled firing is distinct from the actual drying, first firing and second firing; the source’s last-before-birthday wording is not silently repaired.')
F(474,supporting_mention_indices=[474,477,489,491,520,521],evidence=[474,477,489,491,520,521],note='First firing occurrence is supported retrospectively by fired-state description and the explicit second firing, but no operator or thermal parameters are supplied.')
F(571,supporting_event_ids=['ev404','ev412'],supporting_mention_indices=[403,406,409,411,413,418,422,570,571,576],evidence=[403,406,409,411,418,422,570,571,576],note='This reported adaptation summarizes the earlier edge-easing and handle-orientation episode; it is not a second physical repair at the birthday.')
F(620,goal_owner_id='e3',goal_content_id='p30',goal_status='satisfied_as_reported',goal_satisfaction_judgment='exactly_matches_thumb_position',evidence=[599,601,604,615,617,619,620,622],note='The idiomatic personified preference evaluates the current comfortable fit; no historical thumb plan is inferred.')
# p30 is an evaluative fit content, not a recursive desire proposition.
a.propositions['p30']['text']='The hollow is a comfortable resting position for Grandpa’s thumb.'
F(637,narrative_resolution_evidence={'problem':'p3','outcome':'p31','status':'observed_stable_water_test'},evidence=[64,65,67,68,624,626,629,634,636,637],note='The explicit stability requirement is met in this test, without a universal spill-proof guarantee.')
F(692,narrative_resolution_evidence={'problem':'p6','outcome':'p32','status':'thumb_rest_used_while_drinking'},evidence=[103,106,355,358,599,601,604,684,685,689,692],note='The desired thumb place has an actual use, while the original indentation remains visible.')
F(708,narrative_closure_candidate={'content':'Grandpa uses the handmade cup; water catches light on its still-crooked rim','evidence_event_ids':['ev600','ev637','ev686','ev693','ev699'],'assertion_status':'candidate'},narrative_theme_candidate={'content':'An imperfect handmade shape can become useful when adapted to its intended user','assertion_status':'candidate'},narrative_motif_link={'earlier_content_id':'p27','later_content_id':'p32','image':'dent_becomes_used_thumb_rest','assertion_status':'candidate'},evidence=[145,162,338,355,403,576,604,685,689,692,707,708],note='Interpretive closing pattern, not a literal stated moral or proof of permanent comfort.')

for start,pid in [(49,'p2'),(62,'p3'),(103,'p6'),(201,'p34'),(211,'p10'),(219,'p10'),(343,'p20'),(351,'p6'),(451,'p26'),(564,'p27'),(578,'p29'),(615,'p30')]:F(start,utterance_content_id=pid)
# Keep all primary predicate attribution explicit, including same-event quote mentions.
for row in a.words:
 if row.get('role')=='action':row.setdefault('assertion_status',status(row['scope_id']))
# Exclamation interpretation is candidate, while the actual spoken utterance is asserted in its registry.
F(168,assertion_status='candidate')
# Purpose of leaning is not independently proof that the intended looking occurred.
a.events['ev195']['factuality']='desired';F(194,factuality='desired')
# The quantified exterior sides are parts of the cup, not identical to the whole cup.
a.entity('e63','all coated cup sides','cup_part_group',[504])
F(504,part_whole_relation={'part_id':'e63','whole_id':'e4','scope_id':'s0'},grammatical_number='singular',quantifier_domain_restriction={'domain':'cup_sides','whole_entity_id':'e4'})
F(506,grammatical_subject_id='e63',patients=['e63']);a.events['ev507']['patients']=['e63']
# Exact lexical corrections independent of semantic role.
F(275,lemma='fire');F(282,lemma='buy',verb_form='past_participle',participial_function='compound_modifier')
F(398,lexical_gloss='soft physical face of the sponge, not a spatial side of the cup')
F(595,prepositional_object_id='e5')
F(421,noun_compound_relation='purpose_of_rest');F(527,noun_compound_relation='purpose_of_table')

# Corrections from the complete assembled paragraph review.
F(205,lemma='push',verb_form='gerund_participle')
F(21,verb_form='past_participle');a.words[21].pop('tense',None)
F(265,verb_form='base');a.words[265].pop('tense',None)
F(274,verb_form='base')
for w in [194,180,165,458,465,499]:F(w,subject_controller_id='e2' if w==194 else 'e1')
F(330,object_shape=B(330,'e5',{'dimension':'handle_opening','value':'wide'}))
F(255,event_antecedent_id='ev252',referent_kind='event',mention_form='nominal_substitute')
F(462,entity_id='e25',entity_name=a.entities['e25']['name'],entity=a.entities['e25']['type']);a.entities['e25']['mentions'].append(462)
a.mention_event('ev123',452,role='lender',note='Ivo is the lender in the inverse view of the original loan.')
a.mention_event('ev123',455,role='patient',note='The same shaping rib is the loan object.')
F(567,event_affected_entity=B(567,'e28',{'affected_feature':'e30','original_event_id':'ev147'}))
F(3,motion_waypoint=B(3,'e1',{'landmark_ids':['e20','e21']}),motion_destination=B(3,'e1',{'destination':'e19'}))
F(115,motion_direction=B(115,'e23',{'direction':'upward','event_id':'ev114'}))
F(383,quantifier_domain_restriction={'domain':'inside_wall_circumference','entity_id':'e27','desired_inspection':'all_around'})
F(501,event_manner=B(501,'e1',{'event_id':'ev500','manner':'slowly'}))
F(563,event_manner=B(563,'e1',{'event_id':'ev563','manner':'quickly'}))
F(627,temporal_order_cue='water_test_before_tea_use')
F(394,temporal_order_cue='then')
F(377,complementizer_type='declarative')
F(371,subordinator_type='purpose');F(414,subordinator_type='result');F(293,subordinator_type='concessive')
F(344,interrogative_form='what_if_proposal')
F(9,noun_compound_relation='vehicle_served_by_stop');F(14,noun_compound_relation='activity_of_workshop')
F([126,449],noun_compound_relation='tool_purpose',nominalization_kind='gerund_nominal')
F(512,noun_compound_relation='body_part_accommodated_by_hollow');F(575,noun_compound_relation='body_part_accommodated_by_place')
F(556,noun_compound_relation='location_of_table');F(681,noun_compound_relation='plant_kind')
F(567,source_scope_id='s0',source_claim_id='p27')

feedback={
'summary':'Retrospective per-word annotation of Bea’s functional cup design, accidental dent, considered alternatives, adaptation, drying and two distinct firings, birthday gift and observed use.',
'reviewed_all_words':True,'reviewed_paragraphs':list(range(29)),
'ambiguities':[
 {'words':[22,86,90,113,119],'issue':'Three-week making activity is a summary; the current clay lump’s exact earlier history is not narrated.'},
 {'words':[52,119,331,411],'issue':'A wide handle is present later, but its creation or attachment is not narrated. No construction event is invented.'},
 {'words':[249,251,254,258,474,520,521,549],'issue':'The source calls the next kiln firing the last before the birthday, yet narrates a second firing before the gift. Scheduled-event identity and workshop schedule are unresolved; two actual firings remain separate and no extra dates are invented.'},
 {'words':[413,416,418,419,422],'issue':'Handle faces the hollow, opposite the thumb rest is geometrically underspecified. Preserve the wording without inventing a measured orientation or separating the same indentation into an extra object.'},
 {'words':[309,528],'issue':'Workshop testing table and pickup table have separate provisional identities; the story does not establish that they are the same table.'},
 {'words':[388,393,382],'issue':'Finger inspection is shown, but a conclusive all-around wall-thickness finding is not stated.'},
 {'words':[624,626,643,645],'issue':'Water test precedes a tea-filled cup; emptying water and filling tea are unreported transitions, not separate invented events.'},
 {'words':[659,662,671,673,675,684,685,692],'issue':'Final cup is found on the bench; a table is described beneath it; Grandpa is then drinking while kneeling. Bench/table layout, pickup and intermediate movements are unspecified. Preserve endpoints and do not fabricate transitions.'},
 {'words':[454,122],'issue':'Borrowing and later thanks for lending refer to one loan from opposite participant perspectives.'},
 {'words':[620,622],'issue':'Thumb wanted to go is a personified evaluation of fit by Grandpa, not an autonomous thumb mental state.'},
],
'feature_gaps':[
 {'meaning':'ergonomic fit and comfort for a specific body part and grip','resolution':'Use existing grasping/supporting/contact fields plus a narrow legacy fit description. A future typed ergonomic_fit bundle could bind person, body part, object feature and condition without diagnosing pain or general usability.'},
 {'meaning':'operation stages of material manufacture','resolution':'Event identities, state changes and temporal relations suffice here; no new manufacture-stage field is proposed solely for pottery.'},
],
'prompt_feedback':[
 'Quote summaries of a prior multi-action adaptation need a stable episode or explicit supporting-event links, without creating a second actual repair.',
 'Before selecting causality, distinguish a strongly implied accident mechanism from explicit causal wording; candidate status can retain a useful uncertain link.',
 'Scope a possible negated outcome under its modal: might not stick is not observed failure.',
 'Keep source schedule inconsistencies and layout gaps visible rather than silently repairing them with domain knowledge.',
],
'coverage_notes':'All 709 words have explicit contextual POS and lemma choices. All 1,024 catalog definitions and v2 examples were read. Every one of the 29 assembled paragraphs was read against the source and repaired. Full-story retrospective annotations retain no causal-prefix filter; gaps remain synthetic and lossless. Shape validation is supplemented by manual semantic review.'
}
a.save(feedback)
