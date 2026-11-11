"""Manual retrospective costume annotation with physical and represented roles."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from authoring import Annotation

a=Annotation('13_costume',prompt_version='v2');F=a.feature
TAGS=[
'adp num num det n n v adp n n conj det n pron v v adp adj n n n v adp det n adp n conj det n adp n adp det adj n adp det n pron v det adj n conj det n v adp det n',
'pron v pron pron v pron v det n',
'det n v det n adp det n v adv pron v det n part v det adj n det pron pron v v adp det n conj det n v pron part v v adv det n',
'adp det adj n v det adj n adp adj n n v adp pron adv v det n n v n v adp n',
'n n pron v',
'det n v adp det n v n pron v v pron n v v pron conj v pron conj v pron adv adp det n',
'n v det n adp det n pron v det n adp det n det n v conj pron v',
'adp pron n v v det adj n det n v det n det adj n v v adp det n',
'pron v n pron v',
'n v adp det n n v adp det n pron det n',
'pron v n n v pron det n n v det n adp num n conj det adj n v adj conj pron v pron pron pron v part v adv conj v pron v intj v det n',
'pron v part v conj det n v adp det n',
'n v adv pron v n v v det adj adj n n adp n pron v det n part v adp pron adv',
'v pron pron v conj v det n adp det n',
'n v det n pron pron det n n v pron',
'pron v pron n v det adj n det n v conj pron v det adj adj n v pron v v det n v det n adp det n',
'n n v adp det n adp det n adp n num n adp n pron v det n v adp n n adp n n det n n v adp det n n v pron pron v conj adv v v pron v pron adv adv',
'pron v adv',
'n v adp det n adj n adv pron v pron adp n',
'v pron adp det n det n v v',
'n v pron adv adv pron v pron v',
'det n n',
'pron v det n adv pron v det n conj v adp det n pron v num n conj det n v adp det n',
'part adp pron n v v det n adp det n adp pron v det n',
'n v adv det n det n v adj adp det n conj det n adp adj n adv v adv',
'n v det n n n adp det n n det adj n v adj adp num n n v pron adp det adj n adp det n det adj n v adp det adj n conj det n v adp pron',
'adv pron v adp det n v det adj n n v',
'n v det n pron v adp det n adp det n',
'det n n v n',
'n n v det adj n adj',
'n v det n adp det n adj',
'adp det n n v adp det adj n conj n n v pron v adp det n det n v det n conj pron v pron adv adv adp n pron v det n n conj v adp det adj adj n',
'pron v v part v det n',
'det det n adp det n v adv n v adv det adj n v adp det adj n',
'adv n n v pron v adv n v adv adp det n det n v adp adj n pron v n adv conj pron v v pron v det n adp num n conj det adj n v adp pron n n v adp det n',
'adp det n pron v adp num adj v n n v adp det n',
'conj det n v n v adv v det n n n v v adv conj pron adp det adj n v v adj pron v pron adv adp det n n',
'pron v det n adp det n adv n v pron adp det n conj n v det n conj pron v adv adp det n det n v adp det adj n conj det adj n det adj n v det adj n adp n adp det adj n',
]
LEM={'Nia':'Nia','Nia’s':'Nia','Rafi':'Rafi','Rafi’s':'Rafi','Ms':'Ms','Vale':'Vale','Wind':'Wind','Sun':'Sun','Moon':'Moon','MOON':'Moon','SCHOOL':'school','RETURN':'return','AFTER':'after','PLAY':'play','Comes':'come','Home':'home','I':'I',
'smelled':'smell','oranges':'orange','had':'have','eaten':'eat','year’s':'year','squeezed':'squeeze','hats':'hat','coats':'coat','saw':'see','sleeves':'sleeve','ribbons':'ribbon','tied':'tie','wrists':'wrist','moves':'move','told':'tell','was':'be','wanted':'want','practiced':'practice','asked':'ask','knocking':'knock','lay':'lie','reached':'reach','paused':'pause','called':'call','scripts':'script','Don’t':'do','slipped':'slip','brushed':'brush','flashed':'flash','turned':'turn','stood':'stand','holding':'hold','covered':'cover','hands':'hand','stitched':'stitch','says':'say','said':'say','looked':'look','taped':'tape','You’re':'you','promised':'promise','me':'I','pinched':'pinch','fingers':'finger','is':'be','missing':'missing','gave':'give','I’m':'I','supposed':'suppose','tried':'try','dragged':'drag','knew':'know','felt':'feel','weeks':'week','lifted':'lift','shook':'shake','That’s':'that','needs':'need','these':'these','raised':'raise','ribboned':'ribboned','fluttered':'flutter','pictured':'picture','vanishing':'vanish','imagined':'imagine','following':'follow','appeared':'appear','minutes':'minute','places':'place','eyes':'eye','went':'go','you’ve':'you','got':'get','don’t':'do','hurried':'hurry','cape’s':'cape','handed':'hand','took':'take','swallowed':'swallow','shoulders':'shoulder','puddled':'puddle','shoes':'shoe','caught':'catch','you’re':'you','showed':'show','fetched':'fetch','cracked':'cracked','glowed':'glow','shone':'shine','wearing':'wear','studied':'study','sounds':'sound','Places':'place','tightened':'tighten','wings':'wing','listened':'listen','lines':'line','came':'come','stepped':'step','gathered':'gather','spoke':'speak','rooftops':'rooftop','leaned':'lean','taller':'tall','arrived':'arrive','rushed':'rush','arms':'arm','sweeping':'sweep','flickered':'flicker','sparks':'spark','circled':'circle','they':'they','opened':'open','edges':'edge','billowed':'billow','him':'he','streamed':'stream','turning':'turn','fell':'fall','breathing':'breathe','ribbons':'ribbon','come':'come','tucked':'tuck','returned':'return','hung':'hang','straightened':'straighten','faced':'face','rested':'rest','catching':'catch'}
for p,tags in enumerate(TAGS):a.tag(p,tags,LEM)
for name in ['appearance_color','part_whole_relation','figurative_mapping','enactment']:a.use_extension(name)
ENTITIES=[
('e1','Nia','person',[20,39,41,49,51,56,58,60,70,76,81,85,88,91,109,125,135,139,153,158,171,174,199,209,262,286,288,295,302,303,308,311,313,320,322,327,362,388,396,417,419,450,484,527,536,555,573,640,643,652,658,680,712,719,725,730,748,767]),
('e2','Rafi','person',[175,184,197,212,217,220,234,236,238,251,265,267,270,277,284,297,299,359,400,410,422,429,434,436,445,456,459,463,502,506,538,562,564,580,583,594,601,609,628,660,666,679,705,741,763]),
('e3','Ms. Vale','person',[123,124,128,214,215,338,339,353,355,380,385]),
('e4','stage manager','person',[552]),('e5','Nia’s mother','person',[89]),('e6','unidentified orange eater','person',[13]),('e7','Nia and Rafi','person_group',[374,663,689,733]),
('e8','play audience','person_group',[73,245,331,625]),('e9','few audience members leaning forward','person_group',[622]),('e10','school named on cape tag','institution',[119]),
('e11','Wind role in play','fictional_character',[64,304]),('e12','Sun role in play','fictional_character',[211,219,273,280,531,613]),('e13','Moon role evoked by robe','fictional_character',[196,250]),
('e14','The Sun Comes Home','play',[66,67,68,69,122,152,549]),
('e15','costume cupboard','cupboard',[5,132,739]),('e16','hat box','box',[24]),('e17','hats in box','hat_group',[26]),('e18','coat rack','rack',[29]),('e19','coats on rack','coat_group',[31]),
('e20','cupboard door mirror','mirror',[35,166,511,758]),('e21','cupboard door','door',[38,782]),('e22','Nia’s mirror image','reflection',[59]),('e23','Rafi’s mirror image in costume','reflection',[541]),
('e24','Nia’s blue sleeves','clothing_part_group',[43]),('e25','Nia’s wind ribbons','ribbon_group',[46,310,317,421,653,681,721]),('e26','Nia’s wrists','body_part_group',[50,315]),
('e27','Nia’s bed','bed',[86]),('e28','bedside lamp','lamp',[97]),('e29','school red cape','cape',[105,112,138,142,145,148,156,160,287,293,301,307,334,363,392,398,402,412,425,427,469,514,568,589,596,651,669,674,736,743,745,760,770]),
('e30','cape gold lining','lining',[108,168,394,407,633,685,772]),('e31','cupboard top shelf','shelf',[101]),('e32','school return tag','tag',[117,751,753]),('e33','Vale’s scripts','script_group',[134,346,348]),
('e34','Nia’s shoulders','body_part_group',[159,296]),('e35','floor','floor',[163,261,474,592]),('e36','Rafi’s gray robe','robe',[180,181,194,237,257,360,405,480,519,525,638]),
('e37','robe sleeves','clothing_part_group',[182]),('e38','Rafi’s hands','body_part_group',[185]),('e39','stitched silver crescent','costume_symbol',[188,223,765]),('e40','robe chest panel','clothing_part',[193]),
('e41','cast list','cast_list',[204]),('e42','wall bearing cast list','wall',[208]),('e43','Rafi’s two pinching fingers','body_part_group',[226]),('e44','missing yellow tunic','tunic',[230]),
('e45','cupboard doorway','doorway',[343]),('e46','Rafi’s cape-gathering hand','body_part',[457]),('e47','Rafi’s free disk-holding hand','body_part',[508]),('e48','Rafi’s shoulders','body_part_group',[430]),('e49','Rafi’s shoes','shoe_group',[435]),('e50','Rafi’s heel','body_part',[446]),
('e51','cape hem','cape_part',[442]),('e52','cape front','cape_part',[454]),('e53','cardboard Sun disk prop','prop',[366,489,494,504,522,605,711]),('e54','prop box','box',[371,493]),('e55','yellow paint on Sun disk','paint',[496]),('e56','cracked disk edge','prop_part',[501]),
('e57','stage','stage',[337]),('e58','stage wings','stage_region',[572]),('e59','stage illumination','light',[587]),('e60','opening play lines','utterance_sequence',[578]),
('e61','Rafi’s stage cue','stage_cue',[581]),('e62','Nia’s stage cue','stage_cue',[641]),('e63','Rafi’s Sun voice','voice',[274,612]),('e64','Nia’s sweeping arms','body_part_group',[646]),('e65','Rafi’s cape-opening arm','body_part',[672]),('e66','cape red edges','cape_part_group',[676]),
('e67','stage curtain','curtain',[703]),('e68','Nia’s loosened ribbon','ribbon',[717,727]),('e69','Nia’s wrist knot','knot',[732]),('e70','cape hook','hook',[746]),('e71','last stripe of doorway light','light',[776,778]),
('e72','Nia’s stomach','body_part',[556]),('e73','Rafi’s head','body_part',[300]),('e74','last-year oranges','orange_group',[12]),('e75','wool smelled in cupboard','wool',[9]),('e76','dust smelled in cupboard','dust',[8]),('e77','last year’s play performance','performance',[19]),
('e78','Nia’s intended first swirl movement','choreography',[78,80]),('e79','rooftops inside the play','fictional_place_group',[619]),('e80','closing reflected blue ribbon','ribbon',[769]),
]
# w234 is Ms. Vale, the giver, not Rafi: correct before registration.
ENTITIES[1][3].remove(234);ENTITIES[2][3].append(234)
for w in [209,286,302,527]:ENTITIES[0][3].remove(w)
ENTITIES[1][3].extend([209,527]);ENTITIES[1][3].remove(284)
next(row[3] for row in ENTITIES if row[0]=='e12').append(284)
next(row[3] for row in ENTITIES if row[0]=='e29').append(302)
for eid,name,kind,mentions in ENTITIES:a.entity(eid,name,kind,mentions)
a.entities['e7']['member_ids']=['e1','e2'];a.entities['e9']['subset_of']='e8';a.entities['e68']['subset_of']='e25';a.entities['e80']['subset_of']='e25'

QUOTES=[
('q1',range(51,56),'e1',None,57,'self_directed_design_need'),
('q2',range(119,123),None,None,118,'written_return_instruction'),
('q3',range(123,125),'e1','e3',126,'summons'),
('q4',range(135,153),'e3','e1',135,'loan_permission_and_conditions'),
('q5',range(194,197),'e2','e1',198,'costume_role_complaint'),
('q6',range(209,212),'e1','e2',209,'role_reminder'),
('q7',range(212,220),'e2','e1',212,'acknowledgment_and_promise_report'),
('q8',range(227,251),'e2','e1',227,'costume_mismatch_complaint'),
('q9',range(286,288),'e1','e2',289,'try_costume_offer'),
('q10',range(301,308),'e2','e1',301,'reluctant_response'),
('q11',range(308,311),'e1','e2',308,'alternative_costume_response'),
('q12',range(349,353),'e3','e7',354,'time_warning'),
('q13',range(364,385),'e3','e7',364,'prop_information_and_instruction'),
('q14',range(401,410),'e1','e2',401,'wearing_advice'),
('q15',range(414,419),'e2','e1',414,'costume_question'),
('q16',range(419,422),'e1','e2',419,'costume_answer'),
('q17',range(447,450),'e1','e2',451,'reject_wearing_method'),
('q18',range(452,463),'e1','e2',451,'gathering_guidance'),
('q19',range(526,536),'e1','e2',537,'costume_reframing'),
('q20',range(542,550),'e2','e1',542,'accept_reframing'),
('q21',[554],'e4','e7',553,'places_call'),
('q22',[561],'e1','e2',561,'readiness_question'),
('q23',[569],'e2','e1',569,'readiness_answer'),
('q24',range(613,620),'e2','e8',607,'performed_sun_line'),
]
for sid,words,speaker,recipient,trig,act in QUOTES:
 a.scope(sid,words,kind='quotation',holder_id=speaker,description='Direct quoted content with its own local attribution.')
 uid=f'ev{1000+trig}' if trig in words else f'ev{trig+1}'
 a.scopes[sid].update(utterance_event_id=uid,addressee_ids=[recipient] if recipient else [])
 F(list(words)[0],utterance_id=uid,speech_act_kind=act,addressee_ids=[recipient] if recipient else [],communication_channel='written_tag' if sid=='q2' else 'speech',quote_mode='direct')
# The printed tag's author is unknown; a school name does not identify its writer.
a.scopes['q2']['description']='Printed school return tag, author unknown; label and instruction retain their written-source attribution.'
for sid,words,kind,parent,holder,description in [
('s1',range(66,70),'play_title','s0',None,'Title words name the work, not an actual Sun arrival.'),
('s2',range(74,79),'desired_audience_attention','s0','e1','Nia wants her first swirl noticed; audience noticing is not yet actual.'),
('s3',range(92,98),'requested_cessation','s0','e5','Mother requests ending the knocking, not proof that the request was obeyed.'),
('s4',range(140,146),'prohibited_alterations','q4','e3','Cutting and pinning are prohibited; neither is narrated as performed.'),
('s5',range(238,251),'imagined_unwanted_audience_reading','q8','e2','Rafi complains that the Moon-like costume would misidentify his assigned Sun role; this is not a teacher order to portray Moon.'),
('s6',range(247,251),'imagined_audience_thought','s5','e8','Nested imagined audience thought, not an actual audience utterance.'),
('s7',range(281,286),'desired_costume_appearance','s0','e2','Rafi wants visual appearance to fit his assigned Sun role.'),
('s8',range(322,327),'imagined_loss_of_sweep','s0','e1','Nia pictures losing the large red sweep when giving up the cape.'),
('s9',range(330,338),'imagined_audience_following','s0','e1','Nia earlier imagined audience attention following the cape.'),
('s10',range(378,385),'prohibited_sewing_request','q13','e3','Vale asks not to be made to sew now; no sewing occurs.'),
('s11',range(459,463),'guidance_simile','q18','e1','Holding a sunbeam is a simile for gathering fabric, not a physical beam grip.'),
('s12',range(530,536),'costume_metaphor','q19','e1','Sun wearing a cloudy morning describes the visual costume reading.'),
('s13',range(613,620),'performed_fiction','q24','e12','Sun character speaks within the play; performer is Rafi. Warming rooftops is a purpose, not a narrated achieved effect.'),
('s14',range(696,701),'closing_simile','s0',None,'Sunlight caught in wind is a figurative image of the two performers, not literal weather.'),
('s15',range(759,783),'mirror_view','s0',None,'The final relation is presented as a reflected arrangement in the mirror, not a measured external layout.'),
]:a.scope(sid,words,kind=kind,parent=parent,holder_id=holder,description=description)

def status(scope):
 while scope:
  if a.scopes[scope]['kind']=='performed_fiction':return 'asserted'
  if a.scopes[scope]['kind']=='quotation':return 'attributed_claim'
  scope=a.scopes[scope].get('parent')
 return 'asserted'
def B(w,e,value,**extra):return dict(entity_id=e,scope_id=a.words[w]['scope_id'],assertion_status=status(a.words[w]['scope_id']),value=value,**extra)
def E(w,label,actor=None,patients=(),typ='other',fact='asserted',recipient=None,instruments=()):
 a.event(f'ev{w+1}',w,label,type=typ,actor=actor,patients=patients,factuality=fact,recipient=recipient,instruments=instruments);F(w,assertion_status=status(a.words[w]['scope_id']))
def M(w,original,note):
 a.mention_event(f'ev{original+1}',w,role='action',note=note);F(w,assertion_status=status(a.words[w]['scope_id']))
PROPS=[
(1,'Nia has a costume element that moves.',[51,52,53,55],'q1'),(2,'The audience notices Nia’s first swirl.',[71,73,75,77,78],'s2'),
(3,'Nia portrays Wind in the play.',[60,61,62,64,66,69],'s0'),(4,'Nia knocks over the bedside lamp.',[81,83,89,90,93,94,97],'s0'),
(5,'The borrowed cape is returned after the play.',[119,120,121,122,147,149,150,152],'q2'),
(6,'Nia borrows the cape.',[135,136,137,138,139],'q4'),(7,'Nia cuts the cape.',[140,141,142],'s4'),(8,'Nia pins the cape.',[140,143,144,145],'s4'),
(9,'The robe evokes the Moon role.',[188,194,195,196],'q5'),(10,'Rafi has the Sun role.',[209,211,214,216,217,219],'q6'),
(11,'The yellow tunic is available.',[229,230,231,232],'q8'),(12,'Vale gives Rafi the gray robe.',[234,235,236,237],'q8'),
(13,'The audience interprets Rafi as Moon.',[238,244,245,246,247,248,250],'s5'),
(14,'Rafi’s costume looks appropriate to his assigned Sun part.',[277,278,280,282,284],'s7'),
(15,'Rafi tries wearing the red cape.',[286,287,291,293],'q9'),(16,'Nia’s Wind portrayal needs the cape.',[303,304,305,306,307],'q10'),
(17,'Nia uses her wind ribbons.',[308,309,310,419,420,421],'q11'),(18,'Nia’s imagined big red sweep vanishes.',[321,322,323,324,325,326],'s8'),
(19,'The audience follows the cape around the stage.',[329,331,332,334,337],'s9'),(20,'The Sun disk is in the prop box.',[365,366,367,368,371],'q13'),
(21,'Nia and Rafi make Vale sew something now.',[374,378,379,380,381,382,384],'s10'),(22,'Rafi wears the cape over the robe.',[401,402,403,405],'q14'),
(23,'The gold helps Rafi’s Sun appearance.',[407,408,409,531],'q14'),(24,'Rafi wears the cape with its hem dragging under his heel.',[423,425,432,435,442,443,446],'s0'),
(25,'Rafi gathers the cape front in his hand.',[452,454,456,457],'q18'),(26,'Rafi holds a sunbeam.',[459,460,462],'s11'),
(27,'Rafi’s costume resembles Sun wearing a cloudy morning.',[526,527,528,531,532,534,535],'q19'),
(28,'Nia is ready to enter the play.',[555,556,557,560,561],'q22'),(29,'Rafi is ready to enter the play.',[562,563,565,568,569],'q23'),
(30,'The Sun character warms the rooftops.',[613,615,617,619],'s13'),(31,'Nia and Rafi perform their complementary parts together.',[644,647,653,659,660,667,669,677,681,682],'s0'),
(32,'The cape has been returned to the cupboard.',[733,734,736,739,741,742,743,746],'s0'),
]
for n,text,support,scope in PROPS:a.proposition(f'p{n}',text,support,scope_id=scope)
EVENTS=[
(6,'cupboard smells of stored materials',None,('e15',),'state'),(15,'someone ate oranges during prior play','e6',('e74',),'other'),(21,'Nia squeezes between stored costumes','e1',(),'move'),(40,'Nia sees sleeves and ribbons in mirror','e1',('e24','e25'),'perceive'),(47,'ribbons are tied at Nia wrists',None,('e25',),'state'),
(52,'Nia needs a moving costume element','e1',(),'state','reported'),(55,'desired costume element moves',None,(),'move','desired'),(57,'Nia speaks to her reflection','e1',(),'speak'),
(62,'Nia has Wind role','e1',('e11',),'state'),(71,'Nia wants audience attention','e1',(),'state'),(75,'audience notices Nia swirl','e8',('e78',),'perceive','desired'),(83,'Nia practices swirl by bed','e1',('e78',),'other'),(90,'mother asks Nia to stop knocking lamp','e5',(),'speak'),(93,'Nia stops knocking lamp','e1',('e28',),'other','desired'),(94,'Nia knocks lamp over','e1',('e28',),'move'),
(102,'cape lies on top shelf',None,('e29',),'state'),(110,'Nia reaches toward cape','e1',('e29',),'move'),(114,'Nia pauses reaching','e1',(),'other'),(118,'tag carries school return instruction',None,('e32',),'state'),(120,'borrower returns cape after play',None,('e29',),'transfer','desired'),(126,'Nia calls Vale','e1',(),'speak'),
(129,'Vale is outside cupboard','e3',(),'state'),(133,'Vale sorts scripts','e3',('e33',),'other'),(137,'Nia borrows cape','e1',('e29',),'obtain','desired'),(141,'Nia cuts cape','e1',('e29',),'other','negated'),(144,'Nia pins cape','e1',('e29',),'other','negated'),(147,'Nia returns cape after show','e1',('e29',),'transfer','desired'),
(154,'Nia puts cape on shoulders','e1',('e29',),'move'),(161,'cape brushes floor',None,('e29',),'move'),(169,'gold lining flashes in mirror',None,('e30',),'state'),(172,'Nia turns in cape','e1',(),'move'),
(176,'Rafi stands behind Nia','e2',(),'state'),(177,'Rafi holds robe','e2',('e36',),'other'),(183,'robe sleeves cover Rafi hands',None,('e37','e38'),'state'),(190,'crescent is stitched to robe chest',None,('e39',),'state'),
(195,'robe visually evokes Moon role',None,('e36',),'state','reported'),(198,'Rafi complains about Moon appearance','e2',(),'speak'),(200,'Nia looks at cast list','e1',('e41',),'perceive'),(205,'cast list is taped to wall',None,('e41',),'state'),(211,'Rafi has Sun role','e2',('e12',),'state','reported'),
(213,'Rafi knows his Sun assignment','e2',(),'state','reported'),(216,'Vale promises Rafi Sun role','e3',('e12',),'speak','reported'),(221,'Rafi pinches crescent','e2',('e39',),'other'),(232,'yellow tunic is missing',None,('e44',),'state','reported'),(235,'Vale gave Rafi robe','e3',('e36',),'transfer','reported'),(241,'Rafi enters stage','e2',(),'move','hypothetical'),(244,'Rafi costume makes audience think Moon','e2',(),'other','hypothetical'),(246,'audience thinks Rafi is Moon','e8',(),'state','hypothetical'),(248,'imagined audience looks at Moon portrayal','e8',('e13',),'perceive','hypothetical'),
(252,'Rafi tries to smile','e2',(),'other'),(254,'Rafi smiles','e2',(),'other','desired'),(258,'robe drags across floor',None,('e36',),'move'),
(263,'Nia understands Rafi feelings','e1',(),'state'),(266,'Rafi has the felt reaction','e2',(),'feel'),(269,'Rafi practices Sun voice','e2',('e63',),'other'),(278,'Rafi wants visual fit for his role','e2',(),'state'),(282,'Rafi part appearance fits his assigned role',None,('e12',),'state','desired'),
(286,'Rafi tries cape','e2',('e29',),'other','desired'),(289,'Nia offers cape trial','e1',(),'speak'),(291,'Nia lifts cape from shoulders','e1',('e29',),'move'),(298,'Rafi shakes head','e2',('e73',),'move'),(302,'cape is Nia assigned costume',None,('e29',),'state','reported'),(306,'Nia Wind part needs cape',None,('e11',),'state','reported'),
(309,'Nia has wind ribbons','e1',('e25',),'state','reported'),(312,'Nia raises ribboned wrists','e1',('e26',),'move'),(318,'ribbons flutter',None,('e25',),'move'),(321,'Nia imagines loss of red sweep','e1',(),'other'),(326,'large red sweep vanishes',None,(),'state','hypothetical'),(329,'Nia imagined audience following cape','e1',(),'other'),(332,'audience follows cape movement','e8',('e29',),'perceive','hypothetical'),
(340,'Vale appears in doorway','e3',('e33',),'move'),(354,'Vale announces time to places','e3',(),'speak'),(357,'Vale looks from robe to cape','e3',('e36','e29'),'perceive'),(367,'Sun disk is in prop box',None,('e53',),'state','reported'),(372,'children use available props','e7',(),'other','desired'),(375,'children have available costumes and props','e7',(),'state','reported'),(379,'children make Vale sew','e7',(),'other','negated'),(381,'Vale sews a costume item','e3',(),'repair','hypothetical'),(386,'Vale hurries away','e3',(),'move'),
(389,'Nia looks at cape lining','e1',('e30',),'perceive'),(397,'Nia hands cape to Rafi','e1',('e29',),'transfer'),(401,'Rafi wears cape over robe','e2',('e29',),'other','desired'),(409,'gold helps Sun appearance',None,('e30',),'other','hypothetical'),(418,'Nia wears a costume choice','e1',(),'other','hypothetical'),
(423,'Rafi puts cape on','e2',('e29',),'move'),(428,'cape envelops Rafi shoulders',None,('e29','e48'),'state'),(432,'cape gathers around Rafi shoes',None,('e29',),'state'),(437,'Rafi takes one step','e2',(),'move'),(443,'cape hem catches under heel',None,('e51',),'state'),
(451,'Nia corrects cape wearing method','e1',(),'speak'),(452,'Rafi gathers cape front','e2',('e52',),'move','desired'),(460,'Rafi holds a sunbeam','e2',(),'other','hypothetical'),
(464,'Rafi retries cape movement','e2',('e29',),'other'),(470,'cape lifts clear of floor',None,('e29',),'move'),(482,'silver robe strip remains visible',None,('e36',),'state'),
(485,'Nia fetches Sun disk from box','e1',('e53',),'obtain'),(498,'disk paint is cracked',None,('e55',),'state'),(503,'Rafi holds Sun disk','e2',('e53',),'other'),(515,'cape glows in mirror',None,('e29',),'state'),(523,'disk shines above robe',None,('e53',),'state'),
(528,'Rafi looks like Sun in cloudy morning',None,('e2',),'state','reported'),(532,'Sun wears a cloudy morning','e12',(),'other','hypothetical'),(537,'Nia reframes costume appearance','e1',(),'speak'),(539,'Rafi studies his reflection','e2',('e23',),'perceive'),(543,'description resembles play beginning',None,('e14',),'state','reported'),(553,'stage manager calls places','e4',(),'speak'),
(557,'Nia stomach gives small jump',None,('e72',),'state'),(561,'Nia is ready','e1',(),'state','hypothetical'),(563,'Rafi tightens cape grip','e2',('e29',),'other'),(569,'Rafi is ready','e2',(),'state','reported'),
(574,'Nia listens to opening lines','e1',('e60',),'perceive'),(582,'Rafi cue occurs',None,('e61',),'other'),(584,'Rafi steps into stage light','e2',(),'move'),(590,'cape brushes stage floor',None,('e29',),'move'),(595,'Rafi gathers cape in time','e2',('e29',),'move'),(602,'Rafi raises disk','e2',('e53',),'move'),(607,'Rafi performs Sun speech','e2',(),'speak'),
(615,'Sun character has arrived','e12',(),'move'),(617,'Sun character warms rooftops','e12',('e79',),'other','desired'),
(626,'audience members lean forward','e9',(),'move'),(629,'Rafi stands taller','e2',(),'state'),(634,'gold lining shines against robe',None,('e30',),'state'),
(642,'Nia cue occurs',None,('e62',),'other'),(644,'Nia rushes onto stage','e1',(),'move'),(647,'Nia arms sweep wide',None,('e64',),'move'),(654,'ribbons flicker like blue sparks',None,('e25',),'move'),(659,'Nia circles Rafi','e1',('e2',),'move'),(665,'Nia and Rafi practiced circling','e7',(),'other'),(667,'Rafi opens cape with arm','e2',('e29',),'move'),(677,'cape edges billow',None,('e66',),'move'),(682,'Nia ribbons stream around gold lining',None,('e25',),'move'),(690,'performers appear as one turning image',None,('e7',),'state'),
(704,'curtain falls',None,('e67',),'move'),(714,'Nia breathes hard','e1',(),'other'),(723,'one ribbon comes loose',None,('e68',),'state'),(726,'Nia tucks loose ribbon into wrist knot','e1',('e68',),'repair'),
(734,'Nia and Rafi return cape to cupboard','e7',('e29',),'transfer'),(742,'Rafi hangs cape on hook','e2',('e29',),'move'),(749,'Nia straightens return tag','e1',('e32',),'move'),(754,'tag faces out',None,('e32',),'state'),(761,'cape rests in reflected arrangement',None,('e29',),'state'),(773,'cape lining catches doorway light',None,('e30',),'state'),
]
for args in EVENTS:E(*args)
seen=set()
for sid,words,holder,recipient,trig,act in QUOTES:
 uid=a.scopes[sid]['utterance_event_id']
 if uid in seen:continue
 seen.add(uid)
 if uid not in a.events:
  a.event(uid,trig,act.replace('_',' '),type='other' if sid=='q2' else 'speak',actor=holder,recipient=recipient,scope='s0',primary=False,support=list(words))
 else:
  a.events[uid]['recipient_id']=recipient
  if recipient:F(trig,recipient_id=recipient)
# Rafi still holds the same disk across the curtain; no new acquisition.
M(411,397,'Taking is the recipient perspective of the same handoff described by handed.')
a.mention_event('ev398',410,role='recipient',note='Rafi receives, while Nia remains the canonical transfer source.')
a.mention_event('ev398',412,role='patient')
M(708,503,'Continued holding of the same Sun disk, not a new acquisition or pickup.')

ROLES=[
(6,[],[5],{'odor_source':[8,9,12]}),(15,[13],[12],{'occasion':[19]}),(21,[20],[],{'landmark':[24,29]}),(40,[39],[43,46],{'medium':[35]}),(47,[],[46],{'attachment_site':[50]}),
(52,[51],[],{}),(57,[56],[],{'addressed_image':[59]}),(62,[60],[64],{}),(71,[70],[],{}),(75,[73],[78],{}),(83,[81],[80],{'location':[86]}),(90,[89],[],{'recipient':[91]}),(93,[91],[97],{}),(94,[91],[97],{}),
(102,[],[105],{'support':[101]}),(110,[109],[112],{}),(114,[109],[],{}),(118,[],[117],{}),(126,[125],[],{'recipient':[123,124]}),
(129,[128],[],{'location':[132]}),(133,[128],[134],{}),(137,[135],[138],{}),(141,[135],[142],{}),(144,[135],[145],{}),(147,[135],[148],{}),
(154,[153],[156],{'body_location':[159]}),(161,[],[160],{'contact_surface':[163]}),(169,[],[168],{'medium':[166]}),(172,[171],[],{}),
(176,[175],[],{'landmark':[174]}),(177,[175],[180],{}),(183,[],[182,185],{}),(190,[],[188],{'attachment_site':[193]}),(195,[],[194],{'evoked_role':[196]}),(198,[197],[],{}),
(200,[199],[204],{}),(205,[],[204],{'attachment_site':[208]}),(211,[209],[211],{}),(213,[212],[],{}),(216,[214,215],[219],{'recipient':[217]}),(221,[220],[223],{'effector':[226]}),(232,[],[230],{}),(235,[234],[237],{'recipient':[236]}),(241,[238],[],{}),(244,[238],[],{}),(246,[245],[],{}),
(252,[251],[],{}),(254,[251],[],{}),(258,[],[257],{'contact_surface':[261]}),(263,[262],[],{}),(266,[265],[],{}),(269,[267],[274],{}),(278,[277],[],{}),(282,[],[280],{}),
(286,[],[287],{}),(289,[288],[],{}),(291,[288],[293],{'source':[296]}),(298,[297],[300],{}),(302,[],[301],{}),(306,[],[305],{'required_object':[307]}),
(309,[308],[310],{}),(312,[311],[315],{}),(318,[],[317],{}),(321,[320],[],{}),(329,[327],[],{}),(332,[331],[334],{}),
(340,[338,339],[348],{'destination':[343]}),(354,[353],[],{}),(357,[355],[360,363],{}),(367,[],[366],{'location':[371]}),(372,[],[],{}),(375,[374],[],{}),(379,[],[],{'affected_actor':[380]}),(381,[380],[],{}),(386,[385],[],{}),
(389,[388],[394],{}),(397,[396],[398],{'recipient':[400]}),(401,[],[402],{'underlayer':[405]}),(409,[],[407],{}),(418,[417],[],{}),
(423,[422],[425],{}),(428,[],[427,430],{}),(432,[],[427],{'landmark':[435]}),(437,[436],[],{}),(443,[],[442],{'obstacle':[446]}),
(451,[450],[],{}),(452,[],[454],{'holder':[456],'grip':[457]}),(460,[459],[],{}),(464,[463],[],{}),(470,[],[469],{'separated_surface':[474]}),(482,[],[480],{}),
(485,[484],[489],{'source':[493]}),(498,[],[496],{'affected_region':[501]}),(503,[502],[504],{'effector':[508]}),(515,[],[514],{'surrounds':[519],'medium':[511]}),(523,[],[522],{'landmark':[525]}),
(528,[],[527],{}),(532,[531],[],{}),(537,[536],[],{}),(539,[538],[541],{}),(543,[],[549],{}),(553,[552],[],{}),
(557,[],[556],{}),(563,[562],[568],{}),(569,[562],[],{}),
(574,[573],[578],{'location':[572]}),(582,[],[581],{}),(584,[583],[],{'destination':[587]}),(590,[],[589],{'contact_surface':[592]}),(595,[594],[596],{}),(602,[601],[605],{}),(607,[601],[],{'voice':[612]}),
(615,[613],[],{}),(617,[613],[619],{}),(626,[622],[],{}),(629,[628],[],{}),(634,[],[633],{'background':[638]}),
(642,[],[641],{}),(644,[643],[],{}),(647,[],[646],{}),(654,[],[653],{}),(659,[658],[660],{}),(665,[663],[],{}),(667,[666],[669],{'effector':[672]}),(677,[],[676],{'landmark':[679]}),(682,[],[681],{'landmark':[685]}),(690,[],[689],{}),
(704,[],[703],{}),(714,[712],[],{}),(723,[],[717],{}),(726,[725],[727],{'destination':[732]}),(734,[733],[736],{'destination':[739]}),(742,[741],[743],{'support':[746]}),(749,[748],[751],{}),(754,[],[753],{}),(761,[],[760],{'landmark':[765,769]}),(773,[],[772],{'light_source':[776,778]}),
]
for w,actors,patients,rest in ROLES:
 for role,words in [('actor',actors),('patient',patients),*rest.items()]:
  if words:a.mention_event(f'ev{w+1}',words,role=role,note='Explicit local participant with its own role, not a nearby-name guess.')
for w,recipient,instruments in [(90,'e1',[]),(216,'e2',[]),(235,'e2',[]),(397,'e2',[]),(221,None,['e43']),(667,None,['e65'])]:
 a.events[f'ev{w+1}'].update(recipient_id=recipient,instruments=instruments);F(w,instruments=instruments)
 if recipient:F(w,recipient_id=recipient)
# Give reporter attribution to secondary actual utterance events without overwriting content actors.
for row in a.words:
 if row.get('role')=='action':row.setdefault('assertion_status',status(row['scope_id']))

for w,row in enumerate(a.words):
 if row['pos']=='det':
  tok=row['token'].casefold();kind='possessive' if tok in {'her','his','my','your','its'} else 'definite_article' if tok=='the' else 'indefinite_article' if tok in {'a','an'} else 'demonstrative' if tok in {'that','this'} else 'quantificational'
  F(w,determiner_kind=kind)
  if tok in {'the','a','an'}:F(w,definiteness='definite' if tok=='the' else 'indefinite')
  if kind=='possessive':F(w,possessive_construction='possessive_determiner')
 if row['pos']=='pron' and row.get('entity_id'):F(w,mention_form='pronoun',antecedent_id=row['entity_id'])
 if row['pos']=='adp':F(w,dependency_relation='prepositional_marker')
 if row['pos']=='part' and row['token'].casefold()=='to':F(w,dependency_relation='infinitival_marker')
 if row['pos']=='conj' and row['token'].casefold() in {'and','but','or'}:F(w,coordinator_type={'and':'conjunctive','but':'adversative','or':'alternative'}[row['token'].casefold()])
for w in [20,109,139,153,199,262,311,362,388,450,484,536,555,573,640,680,712,748,175,220,267,297,359,400,410,463,502,538,562,580,628,660,705,741,123,124,214,215,338,339]:F(w,mention_form='proper_name')
for w in [123,214,338]:F(w,proper_name_structure='title_plus_name')
for w in [18,359,362,392,555,580,640,680]:F(w,possessive_construction='genitive_np',genitive_realization='apostrophe_s')
for w in [12,26,31,43,46,50,134,159,182,185,226,276,296,315,317,348,350,356,421,430,435,572,578,619,646,653,657,676,681,721]:F(w,grammatical_number='plural')
for w in [51,212,238,308]:F(w,grammatical_person=1,grammatical_number='singular')
F(613,grammatical_person=1,grammatical_number='singular',reference_quotation_shift={'physical_speaker_id':'e2','represented_speaker_id':'e12','world_id':'world_play'})
for w in [135,209,417,459,527]:F(w,grammatical_person=2)
for w in [374,663,689,733]:F(w,group_members=['e1','e2'],split_antecedent_ids=['e1','e2'])
for w in [217,236,380]:F(w,grammatical_case='accusative',lemma='I')
F(679,grammatical_case='accusative',lemma='he')
for w in [140,378]:F(w,contraction_expansion=['do','not'],lemma='do')
F(209,contraction_expansion=['you','are']);F(238,contraction_expansion=['I','am']);F(301,contraction_expansion=['that','is']);F(374,contraction_expansion=['you','have']);F(459,contraction_expansion=['you','are'])
F(284,possessive_construction='independent_possessive',nominal_ellipsis_license='assigned_part',evidence=[273,274,278,280,282,284],note='His denotes the appropriate assigned Sun part/appearance, not the human possessor as an object of comparison.')
F(302,possessive_construction='independent_possessive',nominal_ellipsis_license='assigned_cape',evidence=[137,138,154,301,302,303,304,306,307],note='Rafi calls the assigned borrowed costume yours; this does not transfer school ownership to Nia.')
for w,n in [(1,3),(2,12),(225,2),(349,2),(438,1),(500,1),(671,1),(692,1)]:F(w,cardinal_value=n)
F(1,time_expression_id='time_opening_clock',temporal_granularity='minute',event_time_interval={'hour':3,'minute':12,'meridiem':'unspecified','date':'unspecified'},evidence=[0,1,2],note='Exact clock components, no unsupported afternoon or date normalization.')
F(2,time_expression_id='time_opening_clock')
F(18,temporal_deixis='previous_year',time_anchor_id='time_current_play_year')
F(16,temporal_signal_relation='during');F(87,temporal_signal_relation='until')
F(77,ordinal_rank=1);F(577,ordinal_rank=1)
F(276,measure_unit='week',temporal_duration={'event_id':'ev270','unit':'week','magnitude':'unspecified_plural'})
F(350,measure_unit='minute',temporal_remaining={'value':2,'unit':'minute','until':'places_call','relative_to':'ev355'},evidence=[349,350,351,352,353,354],note='Two minutes from the announcement, not necessarily 3:14; elapsed time since opening is unknown.')
F(621,quantity_approximation_cue='few',counted_domain={'subset_id':'e9','of_group':'e8','exact_count_unknown':True})
F(688,temporal_duration={'event_id':'ev691','value':'brief_moment','exact_duration_unknown':True})
for w in [113,395,639]:F(w,temporal_order_cue='then')
for w,relation in [(121,'after'),(150,'after'),(170,'when'),(579,'when'),(701,'when')]:F(w,temporal_signal_relation=relation)
F(465,temporal_order_cue='again');F(466,temporal_iteration_index=2)
F(598,temporal_bound_cue='just_in_time')

# Explicit contextual verb morphology, including nonfinite predicates and operators.
for w in [6,14,21,40,57,62,71,82,83,90,102,110,114,118,126,129,154,161,169,172,176,183,189,198,200,216,221,231,235,252,258,263,266,268,269,278,289,291,298,312,318,321,328,329,340,354,357,367,375,386,389,397,411,423,428,432,437,443,451,464,470,482,485,497,503,515,523,537,539,543,553,557,563,574,582,584,590,595,602,607,626,629,634,642,644,659,664,665,667,677,682,690,704,706,713,722,723,726,734,742,749,754,761]:
 if a.words[w]['pos']=='v':F(w,verb_form='finite',tense='past')
for w in [52,55,195,213,306,309,528,614]:F(w,verb_form='finite',tense='present')
for w in [75,93,120,137,141,144,147,241,244,246,248,254,282,286,372,379,381,401,409,418,452,617]:F(w,verb_form='base')
for w in [47,15,190,205,615]:F(w,verb_form='past_participle')
for w in [94,133,177,326,332,460,532,647,694,708,714,773]:F(w,verb_form='gerund_participle')
for w,aux in [(15,14),(83,82),(269,268),(329,328),(665,664),(723,722),(615,614)]:F(w,verb_form='past_participle',aspect='perfect',perfect_auxiliary_id=a.anchor(aux))
for w,aux in [(133,129),(708,706),(714,713)]:F(w,aspect='progressive',progressive_auxiliary_id=a.anchor(aux))
F(190,voice='passive',passive_auxiliary_id=a.anchor(189))
F(630,adverb_degree='comparative')
for w in [120,141,144,147,286,372,401,452]:F(w,mood='imperative',imperative_subject_status='understood_addressee')
for w in [55,75,93,94,137,141,144,147,241,244,246,254,282,286,372,379,381,401,418,452,460,532,617]:
 actor=a.events.get(f'ev{w+1}',{}).get('actor_id')
 if actor:F(w,subject_controller_id=actor)

SUBJ={6:'e15',15:'e6',21:'e1',40:'e1',47:'e25',52:'e1',57:'e1',71:'e1',75:'e8',83:'e1',90:'e5',102:'e29',110:'e1',114:'e1',118:'e32',126:'e1',129:'e3',133:'e3',137:'e1',154:'e1',161:'e29',169:'e30',172:'e1',176:'e2',177:'e2',183:'e37',190:'e39',195:'e36',198:'e2',200:'e1',205:'e41',211:'e2',213:'e2',216:'e3',221:'e2',232:'e44',235:'e3',241:'e2',244:'e2',246:'e8',252:'e2',258:'e36',263:'e1',266:'e2',269:'e2',278:'e2',282:'e12',289:'e1',291:'e1',298:'e2',302:'e29',306:'e11',309:'e1',312:'e1',318:'e25',321:'e1',329:'e1',332:'e8',340:'e3',354:'e3',367:'e53',375:'e7',386:'e3',389:'e1',397:'e1',409:'e30',411:'e2',418:'e1',423:'e2',428:'e29',432:'e29',437:'e2',443:'e51',451:'e1',460:'e2',464:'e2',470:'e29',482:'e36',485:'e1',498:'e55',503:'e2',515:'e29',523:'e53',528:'e2',532:'e12',537:'e1',539:'e2',553:'e4',557:'e72',561:'e1',563:'e2',569:'e2',574:'e1',582:'e61',584:'e2',590:'e29',595:'e2',602:'e2',607:'e2',615:'e12',626:'e9',629:'e2',634:'e30',642:'e62',644:'e1',647:'e64',654:'e25',659:'e1',665:'e7',667:'e2',677:'e66',682:'e25',690:'e7',704:'e67',708:'e2',714:'e1',723:'e68',726:'e1',734:'e7',742:'e2',749:'e1',754:'e32',761:'e29',773:'e30'}
for w,e in SUBJ.items():F(w,grammatical_subject_id=e)
# Eyes are a grammatical subject metonymically realizing Vale's looking.
a.entity('e81','Vale’s eyes','body_part_group',[356]);F(357,grammatical_subject_id='e81',reference_metonymic_link={'literal_id':'e81','related_id':'e3','relation':'eyes_realize_person_gaze'})
for w,e in {15:'e74',40:'e24',75:'e78',83:'e78',94:'e28',137:'e29',141:'e29',144:'e29',147:'e29',154:'e29',161:'e35',177:'e36',183:'e38',216:'e12',221:'e39',235:'e36',269:'e63',286:'e29',291:'e29',298:'e73',306:'e29',309:'e25',312:'e26',332:'e29',397:'e29',401:'e29',411:'e29',418:'e1',423:'e29',428:'e48',452:'e52',485:'e53',503:'e53',539:'e23',590:'e35',595:'e29',602:'e53',617:'e79',659:'e2',667:'e29',726:'e68',734:'e29',742:'e29',749:'e32',773:'e71'}.items():F(w,grammatical_object_id=e)
a.words[418].pop('grammatical_object_id',None) # interrogative what, not the subject Nia.
for w,e in {7:'e76',22:'e16',25:'e17',30:'e19',36:'e21',48:'e26',84:'e27',98:'e31',106:'e30',111:'e29',130:'e15',157:'e34',164:'e20',173:'e1',191:'e40',201:'e41',206:'e42',224:'e43',259:'e35',283:'e12',294:'e34',335:'e57',341:'e45',347:'e33',358:'e36',361:'e29',368:'e54',390:'e30',399:'e2',403:'e36',433:'e49',444:'e50',455:'e46',472:'e35',490:'e54',499:'e56',505:'e47',509:'e20',516:'e36',524:'e36',529:'e12',547:'e14',566:'e29',570:'e58',575:'e60',585:'e59',623:'e8',635:'e36',649:'e29',670:'e65',678:'e2',683:'e30',718:'e25',729:'e69',737:'e15',744:'e70',756:'e20',779:'e21'}.items():F(w,prepositional_object_id=e)
for w,e in [(216,'e2'),(235,'e2')]:F(w,indirect_object_id=e)
F(542,propositional_antecedent_id='p27',referent_kind='proposition',mention_form='demonstrative_pronoun')
F(543,clause_type='declarative',lexical_gloss='the quoted costume description resembles a play opening; sounds is evaluative, not a newly heard sound')

# Physical carriers, body parts and appearance. Gold/silver name appearance, not metal.
a.entity('e82','visible strip of silver robe','clothing_part',[477])
F(482,grammatical_subject_id='e82',patients=['e82']);a.events['ev483']['patients']=['e82']
a.mention_event('ev483',477,role='patient',note='A strip is the visible subject, while the robe is the whole garment.')
for w,part,whole in [(35,'e20','e21'),(46,'e25','e1'),(50,'e26','e1'),(108,'e30','e29'),(117,'e32','e29'),(159,'e34','e1'),(182,'e37','e36'),(185,'e38','e2'),(188,'e39','e36'),(193,'e40','e36'),(226,'e43','e2'),(300,'e73','e2'),(356,'e81','e3'),(430,'e48','e2'),(442,'e51','e29'),(446,'e50','e2'),(454,'e52','e29'),(457,'e46','e2'),(477,'e82','e36'),(501,'e56','e53'),(508,'e47','e2'),(556,'e72','e1'),(646,'e64','e1'),(672,'e65','e2'),(676,'e66','e29'),(717,'e68','e25'),(769,'e80','e25')]:
 F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
# Clothing/body association is wearing/attachment, not a biological part relation.
for w in [35,46]:a.words[w].pop('part_whole_relation',None)
F(35,spatial_support=B(35,'e20',{'supported_by':'e21'}))
F(47,spatial_contact=B(47,'e25',{'attached_at':'e26','means':'tied'}))
for w,e,color in [(42,'e24','blue'),(104,'e29','red'),(107,'e30','gold'),(167,'e30','gold'),(179,'e36','gray'),(187,'e39','silver'),(229,'e44','yellow'),(324,'e29','red'),(393,'e30','gold'),(407,'e30','gold'),(479,'e82','silver'),(495,'e55','yellow'),(513,'e29','gold_appearance_in_mirror'),(518,'e36','gray'),(632,'e30','gold'),(637,'e36','gray'),(656,'e25','blue'),(675,'e66','red'),(685,'e30','gold'),(720,'e68','blue'),(764,'e39','silver'),(768,'e80','blue'),(771,'e30','gold')]:
 F(w,appearance_color=B(w,e,color,factuality='imagined' if w==324 else 'asserted'))
for w,e,material in [(116,'e32','paper'),(487,'e53','cardboard'),(604,'e53','cardboard')]:F(w,material_composition=B(w,e,material))
F(188,object_shape=B(188,'e39','crescent'));F(489,object_shape=B(489,'e53','disk'))
F(498,object_integrity=B(498,'e55','cracked_at_one_edge'),evidence=[495,496,497,498,499,500,501],note='Cracking belongs to the paint, not necessarily the cardboard disk substrate.')
F(723,event_state_change=B(723,'e68',{'before':'secured_at_wrist','after':'loose','event_id':'ev724'}))
F(726,event_state_change=B(726,'e68',{'before':'loose','after':'tucked_back_into_wrist_knot','event_id':'ev727'}),event_effector=B(726,'e1',{'action':'retuck','body_part_unspecified':True}))
F(780,containment_boundary_state=B(780,'e15',{'boundary_id':'e21','state':'open'}))
F(769,identity_hypothesis={'entity_id':'e68','mention':769,'scope_id':'s15','assertion_status':'candidate','evidence':'recent single loosened ribbon; identity not fixed'},note='The closing blue ribbon is one of Nia’s ribbons; identity with the just-retucked ribbon is not forced.')

# Source-bound spatial relations and changes, with mirror layout distinguished.
for w,e,landmark,relation in [(102,'e29','e31','on'),(129,'e3','e15','outside'),(154,'e29','e34','over'),(176,'e2','e1','behind'),(183,'e37','e38','covering'),(190,'e39','e40','stitched_to'),(205,'e41','e42','taped_to'),(340,'e3','e45','in'),(367,'e53','e54','in'),(401,'e29','e36','over'),(432,'e29','e49','around'),(443,'e51','e50','under'),(470,'e29','e35','clear_of'),(482,'e82','e29','visible_underneath'),(523,'e53','e36','above'),(677,'e66','e2','behind'),(682,'e25','e30','around'),(742,'e29','e70','on')]:
 F(w,spatial_configuration=B(w,e,{'landmark':landmark,'relation':relation},factuality=a.words[w].get('factuality','asserted')))
for w,e,surface in [(161,'e29','e35'),(258,'e36','e35'),(443,'e51','e50'),(590,'e29','e35')]:F(w,spatial_contact=B(w,e,{'touches':surface,'event_id':a.words[w]['event_id']}))
F(21,motion_route=B(21,'e1',{'between':['e16','e18'],'event_id':'ev22'}),motion_manner=B(21,'e1',{'interpretation':'squeezing','event_id':'ev22'}))
F(291,motion_source=B(291,'e29',{'landmark_id':'e34','event_id':'ev292','role':'source'}))
F(485,motion_source=B(485,'e53',{'landmark_id':'e54','event_id':'ev486','role':'source'}))
F(584,motion_destination=B(584,'e2',{'landmark_id':'e59','event_id':'ev585','role':'destination'}))
F(602,motion_direction=B(602,'e53',{'interpretation':'upward','event_id':'ev603'}))
F(644,motion_manner=B(644,'e1',{'interpretation':'rushing','event_id':'ev645'}))
F(659,motion_path_shape=B(659,'e1',{'interpretation':'circle_around','landmark':'e2','event_id':'ev660'}))
F(734,motion_return_destination=B(734,'e29',{'destination':'e15'}),motion_arrival_completion=B(734,'e29',{'arrived_at':'e15'}),motion_collectivity=B(734,'e7',{'companions':['e1','e2'],'coordination':'together'}))
F(742,spatial_support=B(742,'e29',{'supported_by':'e70'}))
F(754,spatial_orientation=B(754,'e32',{'orientation':'facing_out','frame':'cupboard_front'}))
F(761,spatial_configuration=B(761,'e29',{'landmarks':['e39','e80'],'relation':'between','world':'mirror_reflection'}),spatial_frame_kind=B(761,'e29','mirror_reflection'),evidence=[756,758,760,761,762,765,769])
F(773,attributes=[{'name':'illumination','value':'gold lining catches the last stripe of light from the open door'}])

# Physical custody is distinct from assigned costume and performed role.
F(119,possession_owner=B(119,'e29',{'owner':'e10','basis':'school_label_on_return_tag'}),evidence=[117,118,119,120,121,122])
F(136,permission_grantor_id='e3',permission_recipient_id='e1',permission_content_id='p6',permission_status='granted_limited',modal_base={'kind':'deontic_permission','holder':'e3','force':'possibility','source':'Vale explicit permission','limits':['no_cutting','no_pinning','return_after_show']})
F(137,transfer_kind=B(137,'e29',{'kind':'loan','borrower':'e1','permission_given_by':'e3'},factuality='permitted'),transfer_return_due=B(137,'e29',{'condition':'after_show','content_id':'p5'}))
F(154,possession_borrower=B(154,'e29',{'borrower':'e1','permission_event_id':'ev1135'}),possession_user=B(154,'e29',{'user':'e1','use':'worn_costume'}))
F(302,attributes=[{'name':'assigned_costume_claim','value':'Rafi calls the borrowed cape Nia’s costume, not Nia’s owned property'}])
F(397,transfer_source=B(397,'e29',{'source':'e1'}),transfer_recipient=B(397,'e29',{'recipient':'e2'}),transfer_completion=B(397,'e29',{'completed':True,'event_id':'ev398'}),transfer_joint_participation=B(397,'e29',{'event_id':'ev398','source':'e1','recipient':'e2','theme':'e29'}),transfer_retained_ownership=B(397,'e29',{'owner':'e10','basis':'school_return_tag_and_temporary_loan'}))
F(411,recipient_id='e2',retrieval_inverse_relation={'event_id':'ev398','canonical_relation':'hand_to','source_id':'e1','recipient_id':'e2','theme_id':'e29','surface_perspective':'recipient_takes'},possession_holder=B(411,'e29',{'holder':'e2'}))
F(413,event_manner=B(413,'e2',{'event_id':'ev398','manner':'carefully','participant_role':'recipient'}))
F(423,possession_user=B(423,'e29',{'user':'e2','use':'worn_costume'}))
F(503,possession_holder=B(503,'e53',{'holder':'e2'}),event_effector=B(503,'e2',{'effector_id':'e47','event_id':'ev504'}))
F(708,possession_holder=B(708,'e53',{'holder':'e2'}))
F(734,transfer_kind=B(734,'e29',{'kind':'return','event_id':'ev735'}),transfer_completion=B(734,'e29',{'completed':True,'destination':'e15'}),possession_custody_chain=B(734,'e29',{'holders':['e1','e2'],'final_location':'e15','handoff_id':'ev398','return_id':'ev735'}))
F(742,possession_owner=B(742,'e29',{'owner':'e10','basis':'persistent_school_loan_no_ownership_transfer'}))

# Intentions, imagination and requests keep action content distinct from operators.
F(52,goal_owner_id='e1',goal_content_id='p1',goal_status='expressed_need',goal_polarity='achieve')
F(71,goal_owner_id='e1',goal_content_id='p2',goal_status='desired',goal_polarity='achieve',goal_success_condition='p2')
F(278,goal_owner_id='e2',goal_content_id='p14',goal_status='desired',goal_polarity='achieve',goal_success_condition='p14')
a.proposition('p33','Nia stops knocking over the lamp.',[89,90,91,93,94,97],scope_id='s3')
F(90,speaker_id='e5',addressee_ids=['e1'],speech_act_kind='request',request_action_id='p33',quote_mode='indirect_report')
F(93,goal_owner_id='e5',goal_content_id='p33',goal_polarity='achieve',goal_status='requested',subject_controller_id='e1')
# Earlier lamp knocking is presupposed by stop; it is not a newly desired knocking.
F(94,presupposition_projection={'content':'p4','status':'presupposed_prior','operator':'requested_stop','scope_id':'s3'},note='Past lamp knocking is presupposed through the cessation request, not newly requested.')
F(141,negation_scope_id='p7',obligation_debtor_id='e1',obligation_content_id='p7',obligation_status='prohibited',obligation_source={'speaker_id':'e3','utterance_event_id':'ev1135'})
F(144,negation_scope_id='p8',obligation_debtor_id='e1',obligation_content_id='p8',obligation_status='prohibited',obligation_source={'speaker_id':'e3','utterance_event_id':'ev1135'})
F(147,obligation_debtor_id='e1',obligation_content_id='p5',obligation_status='required_after_show',obligation_source={'speaker_id':'e3','utterance_event_id':'ev1135'},request_action_id='p5')
F(213,knowledge_claim_holder_id='e2',knowledge_claim_content_id='p10',epistemic_attitude_kind='knowledge_claim',epistemic_source_kind='reported_promise')
F(216,speaker_id='e3',addressee_ids=['e2'],promise_content_id='p10',promise_beneficiary_id='e2',speech_act_kind='promise',quote_mode='indirect_report',source_scope_id='q7',communication_scope_bundle={'speaker_id':'e3','utterance_event_id':'ev217','scope_id':'q7','reported_by_id':'e2','assertion_status':'attributed_claim'},evidence=[212,214,215,216,217,219],note='Vale is the reported promiser, while Rafi is the current quoting reporter.')
F(232,negation_scope_id='p11',attributes=[{'name':'availability','value':'reported missing; location and cause unspecified'}])
F(240,modal_base={'kind':'expectation_as_complaint','holder':'e2','assigned_role':'e12','unwanted_costume_reading':'e13'},irony_interpretation={'kind':'context_supported_ironic_complaint','assertion_status':'candidate','speaker_id':'e2','target_content_id':'p13','evidence_words':[196,211,219,230,232,240,250]},evidence=[196,211,219,230,232,240,250],note='Not an order from Vale to play Moon; the anticipated audience response is framed as a complaint.')
F(246,belief_holder_id='e8',belief_content_id='p49',epistemic_attitude_kind='imagined_interpretation',belief_nested_holders=['e2','e8'],assertion_status='attributed_claim')
a.proposition('p34','Rafi feels a reaction to the costume mismatch; its exact emotion is not named.',[195,211,252,263,264,265,266],scope_id='s0')
F(263,knowledge_claim_holder_id='e1',knowledge_claim_content_id='p34',epistemic_attitude_kind='understanding_others_feeling',evidence=[262,263,264,265,266],note='Explicit empathy does not require inventing a specific emotion label.')
F(286,offer_content_id='p15',request_action_id='p15',addressee_ids=['e2'],speaker_id='e1')
F(289,offer_content_id='p15',speech_act_kind='offer',addressee_ids=['e2'],speaker_id='e1')
F(321,imaginer_id='e1',imagined_content_id='p18',imagined_world_id='world_nia_without_cape')
F(329,imaginer_id='e1',imagined_content_id='p19',imagined_world_id='world_nia_cape_attention',narrative_order_mode='earlier_imagination')
F(379,negation_scope_id='p21',request_action_id='p51',obligation_debtor_id='e7',obligation_content_id='p21',obligation_status='prohibited',speaker_id='e3',addressee_ids=['e1','e2'])
F(401,request_action_id='p22',speaker_id='e1',addressee_ids=['e2'])
F(408,modal_base={'kind':'epistemic','force':'possibility','holder':'e1','content_id':'p23','evidence':'gold lining considered as visual aid'})
F(452,request_action_id='p25',speaker_id='e1',addressee_ids=['e2'])
F(617,goal_owner_id='e12',goal_content_id='p30',goal_status='announced_purpose',goal_polarity='achieve',semantic_world_id='world_play')

# Literal utterance content may include a modal, negative or interrogative operator.
for n,text,ws,scope in [
(35,'Nia may borrow the cape but must not cut or pin it and must return it after the show.',list(range(135,153)),'q4'),
(36,'What costume will Nia wear?',[414,415,416,417,418],'q15'),
(37,'Rafi should not wear the cape in the dragging, heel-catching way.',[447,448,449,442,443,446],'q17'),
(38,'Is Rafi ready to enter the play?',[561,562,569],'q22'),
(39,'The Sun character has come in order to warm the rooftops.',list(range(613,620)),'s13'),
(40,'The Sun disk is in the prop box; use available props and do not make Vale sew now.',list(range(364,385)),'q13'),
(41,'Rafi should wear the cape over the robe; the gold might help.',list(range(401,410)),'q14'),
(42,'Rafi should gather the cape front in his hand as if holding a sunbeam.',list(range(452,463)),'q18'),
(43,'Nia will wear her wind ribbons.',[414,418,419,420,421],'q16'),
(44,'The Sun-with-cloudy-morning costume description sounds like the beginning of the play.',list(range(542,550)),'q20'),
]:a.proposition(f'p{n}',text,ws,scope_id=scope)
# Ready? addresses Rafi, not an inquiry into Nia's own readiness.
a.propositions['p28']['text']='Rafi is ready to enter the play.'
a.propositions['p28']['support_words']=[561,562,569]
a.events['ev562']['actor_id']='e2';F(561,actor_id='e2',actor=a.entities['e2']['name'],grammatical_subject_id='e2')
for w,pid in [(51,'p1'),(120,'p5'),(135,'p35'),(194,'p9'),(209,'p10'),(212,'p10'),(286,'p15'),(301,'p16'),(308,'p17'),(364,'p40'),(401,'p41'),(414,'p36'),(419,'p43'),(447,'p37'),(452,'p42'),(526,'p27'),(542,'p44'),(561,'p38'),(569,'p29'),(613,'p39')]:F(w,utterance_content_id=pid)
F(414,question_requested_slot='Nia_costume_choice',question_answer_status='answered',interrogative_form='wh_question')
F(419,dialogue_response_to_id='ev1414',dialogue_turn_function='answer',intention_holder_id='e1',intention_content_id='p17',intention_publicity='communicated',plan_commitment_status='adopted')
F(561,question_requested_slot='Rafi_readiness',question_answer_status='answered',interrogative_form='polar_ellipsis')
F(569,dialogue_response_to_id='ev1561',dialogue_turn_function='answer',utterance_common_ground_delta={'participants':['e1','e2'],'add':['p29']})
F(542,dialogue_response_to_id='ev538',dialogue_turn_function='accept_reframing')
F(447,negation_scope_id='p24',speech_act_kind='correct_method',dialogue_turn_function='corrective_instruction')

# Figurative descriptions and staged representation retain physical grounding.
for w,target,image,kind in [(195,'e36','Moon role recognition','metaphor'),(428,'e29','swallowing shoulders','metaphor'),(432,'e29','puddle around shoes','metaphor'),(460,'e52','holding a sunbeam','simile'),(528,'e2','Sun wearing a cloudy morning','simile'),(654,'e25','blue sparks','simile'),(697,'e7','sunlight caught in wind','simile')]:
 F(w,figurative_mapping={'target_id':target,'source_image':image,'kind':kind,'literal_event':False,'scope_id':a.words[w]['scope_id']})
F(557,attributes=[{'name':'bodily_sensation','value':'small stomach jump before performance; exact emotion unspecified'}])
for w,performer,character,prop in [(62,'e1','e11','e25'),(211,'e2','e12','e36'),(423,'e2','e12','e29'),(607,'e2','e12','e53'),(613,'e2','e12','e53'),(644,'e1','e11','e25'),(659,'e1','e11','e25')]:
 F(w,enactment={'performer_id':performer,'character_id':character,'prop_id':prop,'world_id':'world_play'})
F(range(613,620),semantic_world_id='world_play')
F(607,communication_scope_bundle={'speaker_id':'e2','utterance_event_id':'ev608','scope_id':'s0','represented_speaker_id':'e12','represented_world_id':'world_play','assertion_status':'asserted'})
F(615,event_goal_role=B(615,'e12',{'purpose_content_id':'p30','world_id':'world_play'}))
F(695,figurative_mapping={'target_id':'e7','source_image':'one bright turning image','kind':'visual_comparison','literal_event':False})
F(665,event_collective_participants=B(665,'e7',{'members':['e1','e2'],'event_id':'ev666'}),narrative_order_mode='earlier_rehearsal')
F(734,event_collective_participants=B(734,'e7',{'members':['e1','e2'],'event_id':'ev735'}),event_divided_labor=B(734,'e7',{'event_id':'ev735','subtasks':[{'actor_id':'e2','event_id':'ev743','action':'hang_cape'},{'actor_id':'e1','event_id':'ev750','action':'straighten_tag'}]}))
F(690,narrative_resolution_evidence={'problem_content_id':'p14','status':'observed_coordinated_appearance','evidence_events':['ev529','ev645','ev668','ev683','ev691'],'does_not_establish':'all_audience_members_correctly_identified_both_roles'})
F(734,narrative_resolution_evidence={'problem_content_id':'p5','status':'completed_return','evidence_events':['ev735','ev743']})
F(761,narrative_motif_link={'earlier_entity_ids':['e20','e29','e39','e25'],'relation':'mirror_reframes_separate_costume_parts_as_shared_ending_image','assertion_status':'candidate'},narrative_closure_candidate={'evidence':['completed_cape_return','coordinated_performance','final_mirror_image'],'assertion_status':'candidate'})

# Focused lexical corrections and scoped causal evidence.
for w in [231,367,543]:F(w,tense='present')
F(375,verb_form='past_participle',aspect='perfect',perfect_auxiliary_id=a.anchor(374));a.words[375].pop('tense',None)
F(40,conjunction_members=['e24','e25']);a.words[40].pop('grammatical_object_id',None)
F(357,event_effector=B(357,'e3',{'effector_id':'e81','event_id':'ev358'}))
F(221,event_effector=B(221,'e2',{'effector_id':'e43','event_id':'ev222'}))
F(667,event_effector=B(667,'e2',{'effector_id':'e65','event_id':'ev668'}))
F(235,causal_parent=B(235,'e36',{'cause_event_id':'ev233','effect_event_id':'ev236','claim_source_id':'e2'}),causal_scope=B(235,'e36',{'scope_id':'q8','holder':'e2','factuality':'reported'}),evidence=[230,231,232,233,234,235,236,237])
F(470,event_attempt_outcome=B(470,'e2',{'attempt_event_id':'ev465','outcome':'cape_clears_floor','evidence_event_id':'ev471'}))
F(609,attributes=[{'name':'voice_volume','value':'big bright stage voice'}])
F(629,motion_posture=B(629,'e2','standing_taller'),note='Posture is explicit; confidence or pride is not forced.')
F(714,event_manner=B(714,'e1',{'event_id':'ev715','manner':'breathing_hard'}))
F(661,subordinator_type='comparison');F(475,subordinator_type='concessive');F(617,subject_controller_id='e12')
F(416,lemma='will',modal_base={'kind':'future_question','holder':'e2','question_id':'p36'})
F(408,lemma='may');F(136,lemma='can')

# Repairs after reading all 38 assembled paragraphs against the full source.
F([91,174],lemma='she',grammatical_case='accusative')
F(133,lemma='sort');F(503,lemma='hold')
F(68,verb_form='finite',tense='present')
for w in [136,408,416]:F(w,verb_form='finite',modal_auxiliary_class='possibility_family' if w in [136,408] else 'will_family')
F(136,tense='present');F(416,tense='present')
F([140,378],verb_form='base',mood='imperative')
F([239,697],verb_form='past_participle')
F(654,verb_form='finite',tense='past')
for w in [83,269,329,665,723]:a.words[w].pop('tense',None)
F(630,pos='adj',adjective_degree='comparative');a.words[630].pop('adverb_degree',None)
a.words[168]['appearance_color']=a.words[167].pop('appearance_color')
a.words[781]['containment_boundary_state']=a.words[780].pop('containment_boundary_state')
a.words[662]['subordinator_type']=a.words[661].pop('subordinator_type')
a.words[610]['attributes']=a.words[609].pop('attributes')
a.events['ev562']['event']='Rafi is ready to enter the play';F(561,event='Rafi is ready to enter the play')
# Remove the old whole-robe patient membership after introducing its visible strip.
for b in a.words[480].get('event_bindings',[]):
 if b['event_id']=='ev483' and b['role']=='patient':b['role']='whole_garment'
if a.words[480].get('event_id')=='ev483':F(480,role='whole_garment')
for m in a.events['ev483'].get('mentions',[]):
 if m['word']==480 and m['role']=='patient':m['role']='whole_garment'
# Content IDs preserve the complete stated claim, distinct from future action targets.
for n,text,ws,scope in [
 (45,'Nia has the ribbons she indicates.',[308,309,310,312,317],'q11'),
 (46,'Rafi knows his assigned role, and Vale promised him the Sun part.',list(range(212,220)),'q7'),
 (47,'The cape is Nia’s assigned costume, and her Wind part needs it.',list(range(301,308)),'q10'),
 (48,'The yellow tunic is missing, so Vale gave Rafi this robe; walking on in it would make the audience interpret him as Moon.',list(range(227,251)),'q8'),
]:a.proposition(f'p{n}',text,ws,scope_id=scope)
for w,pid in [(308,'p45'),(212,'p46'),(301,'p47'),(227,'p48')]:F(w,utterance_content_id=pid)
a.proposition('p49','The arriving performer portrays Moon.',[241,245,246,247,248,250],scope_id='s6')
a.proposition('p50','Nia needs a costume element that moves.',[51,52,53,54,55],scope_id='q1')
F(51,utterance_content_id='p50')
a.proposition('p51','Nia and Rafi do not make Vale sew anything now.',[378,379,380,381,382,383,384],scope_id='s10')
F(239,modal_scope_id='p13')
F(449,event_antecedent_id='ev444',referent_kind='event',note='That rejects the just-demonstrated heel-catching costume method, not the existence of the cape.')
F(418,interrogative_form='wh_question')
F(752,subordinator_type='result')
F(61,lexical_gloss='assigned performance role; not a physical person')
F(305,lexical_gloss='Wind performance part; its alleged need for the cape is Rafi’s claim')
F(740,event_manner=B(740,'e7',{'event_id':'ev735','manner':'together'}))

feedback={
'summary':'Per-word retrospective annotation of a shared performance, temporary school cape loan, costume-role reframing, physical stage action and completed return.',
'reviewed_all_words':True,'reviewed_paragraphs':list(range(38)),
'ambiguities':[
 {'words':[119,136,154,302,397,423,734],'issue':'School label and temporary permission support school ownership and Nia borrowing; yours denotes assigned costume in Rafi’s utterance. Rafi receives custody and wears the cape, but no ownership transfer or separate formally authorized subloan is invented.'},
 {'words':[240,244,246,250],'issue':'Rafi’s supposed-to Moon line is a context-supported ironic complaint, not an actual teacher instruction to portray Moon. The imagined audience response remains hypothetical.'},
 {'words':[485,503],'issue':'Nia fetches the disk and Rafi next holds it. The handoff is unreported; endpoints are preserved without inventing a transfer event.'},
 {'words':[479,518,637],'issue':'The robe is predominantly gray and a silver strip is visible; preserve local appearance descriptions rather than globally recoloring the robe.'},
 {'words':[717,769],'issue':'The closing blue ribbon may be the previously loosened ribbon, but this identity is not explicit; its membership in Nia’s ribbons is established.'},
 {'words':[761,765,769,773],'issue':'Final cape-between-crescent-and-ribbon layout is explicitly in the mirror. No unreported robe return or physical undressing movement is inferred.'},
 {'words':[1,2,349,350],'issue':'3:12 supplies clock components without a date or meridiem. Two minutes to places is anchored to Vale’s later announcement, not assumed to end at 3:14.'},
 {'words':[94],'issue':'Stop knocking presupposes earlier lamp knocking while the mother’s request is not proof of compliance. Prior knocking is separately marked through presupposition_projection, not newly desired.'},
 {'words':[55,266,557,629],'issue':'The moving costume element is unspecified; Rafi’s exact emotion and Nia’s stomach-jump emotion are unnamed, and standing taller does not itself assert confidence.'},
],
'feature_gaps':[
 {'meaning':'Wearing and temporary costume assignment in relation to fictional roles','resolution':'Existing possession_user, enactment, role events and explicit assigned-costume description suffice; no new field proposed.'},
 {'meaning':'Presupposed prior action embedded under requested cessation','resolution':'Use presupposition_projection, a positive content proposition and the request’s separate target. A future validator can check that operator and embedded event are not collapsed.'},
],
'prompt_feedback':[
 'Readiness questions need an understood addressee subject; the quoted speaker is not automatically the person whose readiness is asked about.',
 'A give/take pair may be one handoff from opposite perspectives. Reuse event identity and keep the grammatical subject distinct from the canonical transfer actor.',
 'Performed first-person speech needs physical speaker and represented character identities, plus its own world and desired-purpose scope.',
 'Novel metaphors such as says MOON and swallowed shoulders require representation links, not literal writing or ingestion events.',
 'Utterance content preserves spoken operators such as need and know, but omits an extra outer says/thinks wrapper supplied only by annotation. Nested belief content is the proposition believed, separate from the whole holder-plus-attitude proposition.',
],
'coverage_notes':'All 783 words received contextual POS and lemma choices after reading all 1,024 catalog definitions and frozen v2 inputs. Sparse semantic selections are grounded per occurrence; punctuation and spaces are synthetic. Complete assembled-paragraph review is performed before final delivery.'
}
a.save(feedback)
