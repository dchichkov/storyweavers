"""Manually interpreted retrospective teacher labels; no model or automatic tagger."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation

a = Annotation('03_greenhouse', prompt_version='v1')
for key in ('appearance_color', 'part_whole_relation', 'figurative_mapping'):
    a.use_extension(key)

# One contextual tag per source word. Inflections below are explicitly normalized.
TAGS = [
 'adp num adv det n n v adp det n n n v adp det n conj v det n adj conj adj',
 'n v adv v det adj n conj det n adp num n n pron v part v det n adv adp det n n conj adv pron v part v pron adp det num adj n v adj',
 'adv pron v det n n adp det adj n',
 'det n v adp det n adp det n det n v n n n adv v v',
 'pron v adj n v',
 'n n det n n v v adp det n n pron v pron v adp det adj n conj v adv',
 'pron v part det n conj pron v det n pron v det n n v pron adp num n n adp pron pron v',
 'v pron v det adj n n v pron v part v n n n',
 'n n v adp det n n adv adj v pron adp det n conj v adv adp det n v v det n n n v pron v adp n',
 'n v det n pron v adj conj pron v conj n v adp det n conj pron v pron adp det n pron v conj v det n adp det adj n',
 'det adj n v det n adp det adj n n v adv n adp n conj det n v adj pron v adv pron adp det n',
 'adv det n adp n n adp det n v adp det adj n pron adp det n v v det n v adj v det adj n adp det adj n adp n',
 'n v adp n n pron v adp det n adv v adp det n det n adv v v',
 'pron v adp det n det n v adp det n conj det n v adj adv pron v v v det adj n adp pron adv pron v v det n adp det n',
 'det adj n v adp det n',
 'n v pron conj v pron adp det adj n det n v det n conj det n v adj adp det n conj pron v v v pron conj pron v n n pron v det n det adj n n v adv adj adp n',
 'n v det n n adp det n conj v det adj n adp det n det n adp n v pron adv',
 'v pron v pron',
 'pron v det n adp adj n n adp det n conj v pron adp det n n conj det n n det n v conj pron v adp det adj n det n v adp det n n conj v det n adp n n n',
 'n n v part adp adp det n pron v v pron det n pron v pron v det n det adj n adj n',
 'n v det adj n v pron v pron conj det n v v',
 'conj pron v v det n v',
 'det det n adv det n n v adj n n v adv v det n n adp n pron v conj pron v det n',
 'det n n v pron v v adv pron v part v n',
 'pron v n v det n v det adj n',
 'n n v det adj n adp num n adv v det adj n conj pron v adp det n adv adj pron v adp n v pron v pron v det n adv',
 'adv pron v det n n adp det n n n v num n adp det n conj n v det pron adj n n v adv adp det adj n n adp det n conj v det adj n',
 'det n v v det n n v det n adj conj v pron det n n v v v adp det n adp n det n v adv adj conj n n v adv v det n',
 'det n adj pron v',
 'n v pron adv conj v det n adj part part v det n adv pron v det adj n adp n n',
 'adp v n n v det n adp det n n adp det adj n det adj n v det adj adj n det n adp n v adp det n adj adp det adj n n',
]
LEMMAS = {
 'Nia':'Nia', 'Nia’s':'Nia', 'Mr':'Mr', 'Mrs':'Mrs', 'MRS':'Mrs',
 'Bell':'Bell', 'Okafor':'Okafor', 'Okafor’s':'Okafor', 'OKAFOR’S':'Okafor',
 'grandmother’s':'grandmother', 'sunflower’s':'sunflower',
 'felt':'feel','poured':'pour','turned':'turn','came':'come','carrying':'carry',
 'wanted':'want','needed':'need','leaves':'leaf','looked':'look','strongest':'strong',
 'saw':'see','seedlings':'seedling','drooped':'droop','edges':'edge','trays':'tray',
 'TOMATOES':'tomato','DON’T':'do','said':'say','was':'be','crouched':'crouch',
 'He':'he','twisted':'twist','frowned':'frown','tried':'try','I’ve':'I',
 'I':'I','has':'have','Could':'can','asked':'ask','glanced':'glance',
 'Don’t':'do','them':'they','sorted':'sort','filled':'fill','heavier':'heavy',
 'expected':'expect','sloshed':'slosh','carried':'carry','tipped':'tip','darkened':'darken',
 'moved':'move','grew':'grow','had':'have','tomatoes':'tomato','lifted':'lift',
 'clips':'clip','broken':'break','hung':'hang','leaving':'leave','nearest':'near',
 'reaching':'reach','wouldn’t':'will','sat':'sit','could':'can','saved':'save',
 'emptied':'empty','leaned':'lean','opened':'open','held':'hold','covered':'cover',
 'couldn’t':'can','holding':'hold','helped':'help','scanned':'scan','stood':'stand',
 'pebbles':'pebble','tilted':'tilt','nudged':'nudge','told':'tell','found':'find',
 'looped':'loop','stretched':'stretch','reached':'reach','slid':'slide','should':'shall',
 'us':'we','gave':'give','thinking':'think','is':'be','fixed':'fix','stopped':'stop',
 'minutes':'minute','creaked':'creak','clothespins':'clothespin','slipped':'slip',
 'hurrying':'hurry','went':'go','snapped':'snap','explained':'explain','covers':'cover',
 'checked':'check','examined':'examine','watered':'water','roots':'root','smiled':'smile',
 'Would':'will','me':'I','fastened':'fasten','secured':'secure','done':'do','shook':'shake',
 'closed':'close','drooping':'droop','can’s':'can','returned':'return','sides':'side',
 'straightened':'straighten','repaired':'repair','smallest':'small','trembled':'tremble',
}
for paragraph,tags in enumerate(TAGS):
    a.tag(paragraph,tags,LEMMAS)

ENTITIES = [
 ('Nia','person',[23,37,45,50,63,93,143,148,150,188,196,205,211,231,242,283,303,306,312,320,330,343,345,366,369,375,379,392,416,419,463,491,497,553,576,586,588,613,641,649,673,678,684,693]),
 ('Mr. Bell','person',[95,96,99,106,117,123,127,145,157,158,286,287,288,377,378,466,467,480,482,506,618,619,628,666,667,676,699,700]),
 ('Mrs. Okafor','person',[84,85,154,155,181,182,521,522,531,534,538,542,546,561,562,583,590,604,605,703,704,709]),
 ('community greenhouse','greenhouse',[4,5,98,517]),
 ('sunlight','light',[11,282]),
 ('greenhouse roof','roof',[15]),
 ('greenhouse air','air',[19,411]),
 ('yellow umbrella','umbrella',[29,340,347,350,355,373,395,413,418,435,442,445,451,485,537,556,636,639,648]),
 ('sunflower pot','plant_pot',[32,309,465]),
 ('Nia’s sunflower seedling','sunflower_seedling',[35,36,42,56,307,308,315,328,464,650,660,685,690]),
 ('Nia’s grandmother','person',[46]),
 ('grandmother’s porch','porch',[47]),
 ('sunflower leaves','leaf_group',[59,651,691]),
 ('Mrs. Okafor’s tomato seedlings','tomato_seedling_group',[66,67,72,79,86,90,156,248,337]),
 ('far bench','bench',[71,210,257,382,439]),
 ('tomato seedling leaves','leaf_group',[73]),
 ('tomato trays','tray_group',[80,162,163,180,184]),
 ('tray edges','edge_group',[77]),
 ('tomato label','label',[82,707]),
 ('hose tap','tap',[105,108,672]),
 ('hose','hose',[104,299,502]),
 ('tap spout','spout',[113]),
 ('mains water supply','water_supply',[121]),
 ('leak in water system','leak',[126,510]),
 ('rain barrel','rain_barrel',[130,131,170]),
 ('blue watering can','watering_can',[147,167,191,192,207,239,334,495,499,674,680,697]),
 ('first canful of rainwater','water_portion',[199,326]),
 ('tomato soil','soil',[176,226,566]),
 ('watering can sides','side_group',[203]),
 ('watering can rose','sprinkler_head',[216]),
 ('first tomato tray','tray',[220]),
 ('tomato seedling stems','stem_group',[230]),
 ('tomato rows','row_group',[234,236]),
 ('shade cloth','shade_cloth',[253,254,265,270,539,540,574,593,599,600,602,715]),
 ('shade clip that breaks','clip',[263]),
 ('shade clips','clip_group',[266]),
 ('exposed nearest tomato tray','tray',[276,354,457,560]),
 ('bright square of sunlight','illuminated_region',[280]),
 ('greenhouse sink','sink',[292,473]),
 ('wrench','wrench',[297]),
 ('Nia’s knee','body_part',[313]),
 ('sunflower soil','soil',[316,661]),
 ('Nia’s backpack','backpack',[344]),
 ('umbrella shadow','shadow',[356,452,657,659]),
 ('tomato seedlings in exposed tray','tomato_seedling_group',[359]),
 ('umbrella handle','handle',[362,396]),
 ('Nia’s hand','body_part',[367]),
 ('clay pot used as umbrella stand','plant_pot',[386,399]),
 ('pebbles in support pot','pebble_group',[391]),
 ('umbrella canopy','canopy',[404]),
 ('length of garden tie','garden_tie',[422,426,432,644]),
 ('drawer','drawer',[429]),
 ('umbrella shaft','shaft',[436]),
 ('bench leg','leg',[440]),
 ('edge of sunflower pot','edge',[461]),
 ('Nia and Mr. Bell','person_group',[140,477]),
 ('greenhouse door','door',[518]),
 ('paper bag','bag',[528]),
 ('Mrs. Okafor’s clothespins','clothespin_group',[530]),
 ('tomato roots','root_group',[580]),
 ('Mrs. Okafor’s finger','body_part',[569]),
 ('Nia and Mrs. Okafor','person_group',[596]),
 ('shade rail','rail',[603]),
 ('one end of shade cloth','cloth_end',[608]),
 ('one clothespin used for repair','clothespin',[611]),
 ('other end of shade cloth','cloth_end',[616]),
 ('new replacement metal clip','clip',[626]),
 ('Mr. Bell’s toolbox','toolbox',[629]),
 ('corner with broken fastener','cloth_corner',[634]),
 ('Mrs. Okafor’s final tomato tray','tray',[710,711]),
 ('smallest tomato seedling','tomato_seedling',[718,720]),
 ('smallest seedling’s first true leaf','leaf',[723,730]),
 ('bead of water on leaf','water_droplet',[725,727]),
 ('tip of true leaf','leaf_tip',[731]),
 ('sun','star',[407]),
 ('lifting flap of shade cloth','cloth_flap',[251]),
]
for i,(name,kind,mentions) in enumerate(ENTITIES,1):
    a.entity(f'e{i}',name,kind,mentions)
a.entities['e56']['members']=['e1','e2']
a.entities['e62']['members']=['e1','e3']
a.feature([140,477], group_members=['e1','e2'], split_antecedent_ids=['e1','e2'])
a.feature(596, group_members=['e1','e3'], split_antecedent_ids=['e1','e3'])

# Speech scopes include only quoted words, not the narrator's reporting clause.
QUOTES=[('q1',84,90,'e3','Written label names an owner; the author is unknown.'),
 ('q2',90,93,'e1','Nia describes thirsty-looking tomatoes.'),
 ('q3',117,127,'e2','Bell reports shutting water off during repair.'),
 ('q4',129,142,'e2','Bell states limited rainwater and need to wait.'),
 ('q5',142,148,'e1','Nia requests a temporary loan.'),
 ('q6',150,157,'e1','Nia states her watering goal.'),
 ('q7',164,188,'e2','Permission, watering instructions and warning.'),
 ('q8',415,416,'e1','Playful imperative addressed to umbrella.'),
 ('q9',474,480,'e2','Bell predicts extra time from temporary shade.'),
 ('q10',489,491,'e2','Bell praises Nia’s thinking.'),
 ('q11',496,505,'e1','Nia asks about refilling after repair.'),
 ('q12',505,512,'e2','Bell gives conditional answer, not a guarantee.'),
 ('q13',538,542,'e3','Okafor describes earlier shade displacement.'),
 ('q14',546,551,'e3','Okafor reports earlier trip to find fasteners.'),
 ('q15',551,553,'e1','Nia reports a snap; its physical antecedent remains ambiguous.'),
 ('q16',555,561,'e1','Nia reports the current umbrella cover.'),
 ('q17',575,583,'e3','Okafor confirms watering placement and approves.'),
 ('q18',587,595,'e3','Okafor requests help restoring shade.'),
 ('q19',673,676,'e2','Bell announces the can is ready to refill.')]
for sid,start,stop,holder,desc in QUOTES:
    a.scope(sid,range(start,stop),kind='quotation',holder_id=holder,description=desc)
    a.feature(range(start,stop), quote_mode='direct')
    a.scopes[sid]['addressee_ids'] = (['e8'] if sid=='q8' else ['e2'] if sid in ('q2','q5','q6','q11') else ['e3'] if sid in ('q15','q16') else ['e1'])
# Label attribution is not itself a witnessed act of writing by the named owner.
a.scopes['q1']['holder_id']=None
for w in range(84,90):
    a.words[w].pop('speaker_id',None)
a.scopes['q1']['addressee_ids']=[]

SUBSCOPES=[
 ('s1',39,48,'desired','s0','e1','Intended journey home; not completed in text.'),
 ('s2',52,62,'planned_selection','s0','e1','Pending choice of strongest leaf; no choice outcome narrated.'),
 ('s3',153,157,'desired','q6','e1','Desired watering, distinct from the later realized action.'),
 ('s4',320,329,'counterfactual','s0','e1','Possible past saving of water, explicitly contrasted with actual use on tomatoes.'),
 ('s5',369,379,'hypothetical_constraint','s0','e1','Cannot simultaneously hand-hold umbrella and help Bell; no completed help yet.'),
 ('s6',500,505,'future_condition','q11','e1','Refill is contingent on repair.'),
 ('s7',505,512,'conditional','q12','e2','Stopping the leak is a condition, not an accomplished action here.'),
 ('s8',548,551,'reported_purpose','q14','e3','Finding clips is purpose of trip; exact success not asserted.'),
 ('s9',589,595,'requested_action','q18','e3','Nia helps Okafor restore the cloth; this request itself is not completion.'),
 ('s10',687,692,'avoided_action','s0','e1','Care is directed at preventing leaf splashing; absence is not independently observed.'),
 ('s11',701,703,'prospective_departure','s0','e3','Temporal before-clause projects departure without narrating completion.'),
]
for sid,start,stop,kind,parent,holder,desc in SUBSCOPES:
    a.scope(sid,range(start,stop),kind=kind,parent=parent,holder_id=holder,description=desc)
a.scope('s12',[],kind='expectation_content',holder_id='e1',description='Expected weight is content of Nia’s earlier expectation, not narrator truth.')

EVENT_AT={}
def ev(w,label,type='other',actor=None,patients=(),instruments=(),recipient=None,factuality='asserted',roles=None,**fields):
    eid=f'ev{len(a.events)+1}'
    a.event(eid,w,label,type=type,actor=actor,patients=patients,instruments=instruments,
            recipient=recipient,factuality=factuality,roles=roles,**fields)
    EVENT_AT[w]=eid
    return eid

def mention(w,original,role='action',note='Later mention of the same underlying event.'):
    eid=EVENT_AT[original]
    a.mention_event(eid,w,role=role,note=note)
    EVENT_AT[w]=eid

def bundle(w,eid,value,status=None):
    scope=a.words[w]['scope_id']
    if status is None:
        status='attributed_claim' if scope.startswith('q') or scope in ('s3','s6','s7','s8','s9') else 'asserted'
    return dict(entity_id=eid,scope_id=scope,assertion_status=status,value=value)

# Predicates are individually interpreted, including nonrealized content events.
ev(6,'greenhouse feels oven-hot','state',patients=['e4'],roles={'patient':[5]})
ev(12,'sunlight streams through roof','move',actor='e5',roles={'actor':[11],'location':[15]})
ev(17,'sunlight makes air warm and green','other',actor='e5',patients=['e7'],roles={'patient':[19],'modifier':[20,22]})
ev(24,'Nia enters greenhouse','move','e1',roles={'actor':[23]})
ev(26,'carry umbrella and potted sunflower','move','e1',['e8','e9'],roles={'patient':[29,32]})
ev(38,'want to take sunflower home','state','e1',roles={'actor':[37]})
ev(40,'take sunflower to grandmother’s porch','move','e1',['e10'],factuality='desired',roles={'patient':[42],'location':[47]})
ev(51,'need to choose strongest leaf','state','e1',roles={'actor':[50]})
ev(53,'choose strongest sunflower leaf','other','e1',['e13'],factuality='desired')
ev(60,'assess which leaf looks strongest','state',patients=['e13'],factuality='hypothetical',roles={'patient':[59],'modifier':[61]})
ev(64,'see tomato seedlings','perceive','e1',['e14'],roles={'actor':[63],'patient':[67],'location':[71]})
ev(74,'tomato leaves droop over tray edges','state',patients=['e16'],roles={'patient':[73],'location':[77]})
ev(83,'label displays ownership and no-move instruction','state',patients=['e19'],roles={'patient':[82]})
ev(89,'move labeled tomato plants','move',patients=['e14'],factuality='negated')
ev(91,'tomatoes look thirsty to Nia','state',patients=['e14'],factuality='reported',roles={'patient':[90],'modifier':[92]})
ev(94,'Nia comments on tomatoes','speak','e1',recipient='e2',roles={'actor':[93]})
ev(101,'Bell crouches beside tap','state','e2',roles={'actor':[95,96],'location':[105]})
ev(107,'twist tap','other','e2',['e20'],roles={'actor':[106],'patient':[108]})
ev(109,'Bell frowns at dry spout','other','e2',['e22'],roles={'patient':[113]})
ev(115,'try tap again','other','e2',['e20'])
ev(118,'Bell shuts off water supply','other','e2',['e23'],factuality='reported',roles={'actor':[117],'patient':[121]})
ev(124,'Bell works on repairing leak','repair','e2',['e24'],factuality='reported',roles={'actor':[123],'patient':[126]})
ev(128,'Bell explains water shutdown','speak','e2',recipient='e1',roles={'actor':[127]})
ev(132,'barrel contains enough for one canful','state',patients=['e25'],factuality='reported',roles={'patient':[131]})
ev(141,'wait after using limited rainwater','state','e56',factuality='desired',roles={'actor':[140]})
ev(144,'Nia requests borrowing blue can','obtain','e1',['e26'],factuality='desired',roles={'actor':[143],'patient':[147]})
ev(149,'Nia asks permission to borrow','speak','e1',recipient='e2',roles={'actor':[148]})
ev(151,'Nia wants to water tomatoes','state','e1',factuality='reported',roles={'actor':[150]})
ev(153,'water Okafor’s seedlings','other','e1',['e14'],instruments=['e26'],factuality='desired',roles={'patient':[156]})
ev(159,'Bell glances at tomato trays','perceive','e2',['e17'],roles={'actor':[157,158],'patient':[163]})
ev(166,'fill can from barrel as instructed','other','e1',['e26'],factuality='desired',roles={'patient':[167],'location':[170]})
ev(172,'pour gently onto tomato soil as instructed','other','e1',['e28'],instruments=['e26'],factuality='desired',roles={'patient':[176]})
ev(178,'move tomato trays as prohibited','move','e1',['e17'],factuality='negated',roles={'patient':[180]})
ev(185,'Okafor has sorted trays by variety','other','e3',['e17'],factuality='reported',roles={'actor':[181,182],'patient':[184]})
ev(189,'fill blue can with rainwater','other','e1',['e26'],roles={'actor':[188],'patient':[191]})
ev(194,'filled can is heavier than expected','state',patients=['e26'],roles={'patient':[192]})
ev(197,'Nia previously expected a lighter can','state','e1',['e26'],roles={'actor':[196]})
ev(200,'rainwater sloshes against can sides','move','e27',roles={'actor':[199],'location':[203]})
ev(206,'carry filled can to bench','move','e1',['e26'],roles={'actor':[205],'patient':[207],'location':[210]})
ev(212,'Nia crouches at bench','move','e1',roles={'actor':[211]})
ev(214,'tip can rose over first tray','other','e1',['e30'],instruments=['e26'],roles={'patient':[216],'location':[220]})
ev(224,'sprinkled water darkens tomato soil','other','e27',['e28'],instruments=['e26'],roles={'patient':[226]})
ev(232,'Nia waters tomatoes row by row','other','e1',['e14'],instruments=['e26'],roles={'actor':[231]})
ev(240,'watering can becomes light','state',patients=['e26'],roles={'patient':[239],'modifier':[241]})
ev(243,'Nia has just enough water for tomatoes','state','e1',['e27'],roles={'actor':[242],'recipient':[248]})
ev(258,'shade flap lifts with snap','move','e76',roles={'actor':[251]})
ev(268,'one shade clip breaks','other',patients=['e35'],roles={'patient':[263]})
ev(271,'shade cloth hangs crooked','state',patients=['e34'],roles={'patient':[270],'modifier':[272]})
ev(273,'displaced shade leaves nearest tray exposed','other','e34',['e37'],roles={'patient':[276],'location':[280]})
ev(284,'Nia looks at Bell','perceive','e1',['e2'],roles={'actor':[283],'patient':[286,287]})
ev(289,'Bell is under sink','state',patients=['e2'],roles={'patient':[288],'location':[292]})
ev(294,'Bell reaches for wrench','move','e2',['e40'],roles={'patient':[297]})
ev(302,'hose does not work','state',patients=['e21'],factuality='negated',roles={'patient':[299]})
ev(304,'Nia looks at sunflower','perceive','e1',['e10'],roles={'actor':[303],'patient':[307]})
ev(310,'sunflower pot sits beside Nia’s knee','state',patients=['e9'],roles={'patient':[309],'location':[313]})
ev(318,'sunflower soil is dusty','state',patients=['e42'],roles={'patient':[316]})
ev(323,'Nia could have saved water for sunflower','other','e1',['e27'],factuality='hypothetical',roles={'actor':[320],'patient':[326],'recipient':[328]})
mention(332,232,note='Summary of the completed tomato watering, not a second emptying of the can.')
a.mention_event(EVENT_AT[232],334,role='instrument')
a.mention_event(EVENT_AT[232],337,role='patient')
ev(341,'umbrella leans against backpack','state',patients=['e8'],roles={'patient':[340],'location':[344]})
ev(346,'Nia opens umbrella','other','e1',['e8'],roles={'actor':[345],'patient':[347]})
ev(349,'Nia holds umbrella over exposed tray','other','e1',['e8'],roles={'patient':[350],'location':[354]})
ev(357,'umbrella shadow covers exposed seedlings','state',patients=['e45'],instruments=['e8'],roles={'actor':[356],'patient':[359]})
ev(364,'umbrella handle is awkward to hold','state',patients=['e46'],roles={'patient':[362],'location':[367]})
ev(372,'continue holding umbrella while helping Bell','other','e1',['e8'],factuality='negated',roles={'actor':[369],'patient':[373]})
ev(376,'Nia helps Bell while holding umbrella','other','e1',['e2'],factuality='hypothetical',roles={'actor':[375],'patient':[377,378]})
ev(380,'Nia scans bench','perceive','e1',['e15'],roles={'actor':[379],'patient':[382]})
ev(387,'pebble-filled unplanted pot stands nearby','state',patients=['e48'],roles={'patient':[386]})
ev(393,'set umbrella handle in support pot','other','e1',['e46'],roles={'actor':[392],'patient':[396],'location':[399]})
ev(401,'tilt umbrella canopy toward sun','other','e1',['e50'],roles={'patient':[404],'location':[407]})
ev(412,'air nudges umbrella sideways','move','e7',['e8'],roles={'actor':[411],'patient':[413]})
ev(415,'umbrella should stay in place','state',patients=['e8'],factuality='desired')
ev(417,'Nia tells umbrella to stay','speak','e1',recipient='e8',roles={'actor':[416],'recipient':[418]})
ev(420,'find garden tie in drawer','obtain','e1',['e51'],roles={'actor':[419],'patient':[426],'location':[429]})
ev(431,'loop tie around umbrella shaft and bench leg','other','e1',['e51'],roles={'patient':[432],'location':[436,440]})
ev(443,'secured umbrella holds in place','state',patients=['e8'],roles={'patient':[442]})
ev(446,'umbrella leans at jaunty angle','state',patients=['e8'],roles={'patient':[445],'modifier':[449,450]})
ev(453,'umbrella shadow stretches across tomato tray','state',patients=['e37'],instruments=['e8'],roles={'actor':[452],'patient':[457]})
ev(459,'umbrella shadow reaches sunflower pot edge','state',patients=['e55'],instruments=['e8'],roles={'patient':[461]})
ev(468,'Bell slides out from under sink','move','e2',roles={'actor':[466,467],'location':[473]})
ev(476,'temporary shade should buy extra time','state',patients=['e56'],factuality='hypothetical',roles={'patient':[477]})
ev(481,'Bell assesses temporary shade','speak','e2',recipient='e1',roles={'actor':[480]})
ev(483,'Bell taps umbrella carefully','other','e2',['e8'],roles={'actor':[482],'patient':[485]})
ev(492,'Nia lifts can','move','e1',['e26'],roles={'actor':[491],'patient':[495]})
ev(498,'Nia asks to refill can after repair','other','e1',['e26'],factuality='desired',roles={'actor':[497],'patient':[499]})
ev(504,'hose will be fixed as refill condition','repair',patients=['e21'],factuality='hypothetical',roles={'patient':[502]})
ev(511,'Bell stops leak as condition','repair','e2',['e24'],factuality='hypothetical',roles={'actor':[506],'patient':[510]})
ev(519,'greenhouse door creaks open','move','e57',roles={'actor':[518],'modifier':[520]})
ev(523,'Okafor enters greenhouse','move','e3',roles={'actor':[521,522]})
ev(525,'Okafor carries bag of clothespins','move','e3',['e58'],roles={'patient':[528]})
ev(532,'Okafor stops on seeing umbrella','move','e3',roles={'actor':[531]})
ev(535,'Okafor sees umbrella','perceive','e3',['e8'],roles={'actor':[534],'patient':[537]})
# The report might denote an earlier displacement; do not force event identity.
ev(541,'Okafor reports shade cloth slipping','move','e34',factuality='reported',roles={'actor':[540]})
ev(543,'Okafor reports shade slipping','speak','e3',recipient='e1',roles={'actor':[542]})
ev(544,'Okafor hurries toward bench','move','e3')
ev(547,'Okafor previously went to find clips','move','e3',factuality='reported',roles={'actor':[546]})
ev(549,'find clips as purpose of earlier trip','obtain','e3',factuality='desired')
ev(552,'Nia reports a snapping incident','other',factuality='reported',support=[258,262,268,551,552])
ev(554,'Nia explains snap','speak','e1',recipient='e3',roles={'actor':[553]})
mention(557,453,note='Nia reports the currently maintained umbrella shade, not another covering action.')
a.mention_event(EVENT_AT[453],556,role='instrument')
a.mention_event(EVENT_AT[453],560,role='patient')
ev(563,'Okafor checks soil with finger','perceive','e3',['e28'],['e61'],roles={'actor':[561,562],'patient':[566],'instrument':[569]})
ev(571,'Okafor examines crooked shade','perceive','e3',['e34'],roles={'patient':[574]})
mention(577,232,note='Okafor recognizes the already completed tomato watering.')
a.mention_event(EVENT_AT[232],576,role='actor')
a.mention_event(EVENT_AT[232],580,role='location')
ev(584,'Okafor smiles at Nia','other','e3',recipient='e1',roles={'actor':[583],'recipient':[586]})
ev(589,'Nia helps Okafor restore cloth as requested','other','e1',['e3'],factuality='desired',roles={'actor':[588],'patient':[590]})
ev(591,'put shade cloth back as requested','repair','e62',['e34'],factuality='desired',roles={'patient':[593]})
ev(597,'Nia and Okafor stretch shade across rail','repair','e62',['e34'],roles={'actor':[596],'patient':[600],'location':[603]})
ev(606,'Okafor fastens cloth end with clothespin','repair','e3',['e64'],['e65'],roles={'actor':[604,605],'patient':[608],'instrument':[611]})
ev(614,'Nia holds other cloth end steady','other','e1',['e66'],roles={'actor':[613],'patient':[616],'modifier':[617]})
ev(620,'Bell comes over with replacement clip','move','e2',['e67'],roles={'actor':[618,619],'patient':[626],'location':[629]})
ev(631,'Bell secures broken corner with new clip','repair','e2',['e69'],['e67'],roles={'patient':[634]})
ev(638,'umbrella has served temporary shading purpose','state',patients=['e8'],roles={'patient':[636]})
ev(642,'Nia shakes tie loose','other','e1',['e51'],roles={'actor':[641],'patient':[644],'modifier':[645]})
ev(647,'Nia closes umbrella','other','e1',['e8'],roles={'patient':[648]})
ev(653,'sunflower leaves stop drooping in shade','state',patients=['e13'],roles={'patient':[651],'location':[657,659]})
ev(664,'sunflower soil remains dry','state',patients=['e42'],roles={'patient':[661]})
ev(670,'Bell completes tap repair','repair','e2',['e20'],roles={'actor':[666,667],'patient':[672]})
ev(675,'can is ready to refill after repair','state',patients=['e26'],factuality='reported',roles={'patient':[674]})
ev(677,'Bell announces refill readiness','speak','e2',recipient='e1',roles={'actor':[676]})
ev(679,'Nia fills can again','other','e1',['e26'],roles={'actor':[678],'patient':[680]})
ev(683,'Nia waters sunflower','other','e1',['e10'],['e26'],roles={'patient':[685]})
ev(689,'splash sunflower leaves as avoided action','other','e1',['e13'],factuality='negated',roles={'patient':[691]})
ev(694,'Nia returns can to Bell','transfer','e1',['e26'],recipient='e2',roles={'actor':[693],'patient':[697],'recipient':[699,700]})
ev(702,'Okafor leaves after straightening label','move','e3',factuality='hypothetical')
ev(705,'Okafor straightens tomato label','other','e3',['e19'],roles={'actor':[703,704],'patient':[707],'location':[711]})
ev(719,'smallest seedling lifts first true leaf','move','e71',['e72'],roles={'actor':[718],'patient':[723]})
ev(728,'water bead trembles on leaf tip','move','e73',roles={'actor':[725,727],'location':[731]})

# Distinct actual utterances where no narrator reporting verb is supplied.
UTTERANCES=[('q1',83,None,None,'written_label'),('q2',94,'e1','e2','observation'),
 ('q3',128,'e2','e1','explanation'),('q4',128,'e2','e1','explanation'),
 ('q5',149,'e1','e2','request'),('q6',149,'e1','e2','goal_statement'),
 ('q7',164,'e2','e1','permission_and_instruction'),('q8',417,'e1','e8','playful_command'),
 ('q9',481,'e2','e1','assessment'),('q10',489,'e2','e1','praise'),
 ('q11',496,'e1','e2','permission_question'),('q12',505,'e2','e1','conditional_answer'),
 ('q13',543,'e3','e1','report'),('q14',543,'e3','e1','report'),
 ('q15',554,'e1','e3','explanation'),('q16',554,'e1','e3','explanation'),
 ('q17',575,'e3','e1','confirmation_and_praise'),('q18',587,'e3','e1','request'),
 ('q19',677,'e2','e1','announcement')]
for sid,w,speaker,audience,act in UTTERANCES:
    if w not in EVENT_AT:
        eid=ev(w,act,'speak',speaker,recipient=audience,scope='s0',primary=False)
    else:
        eid=EVENT_AT[w]
    a.scopes[sid]['utterance_event_id']=eid
    if speaker:
        a.feature(w,speaker_id=speaker,addressee_ids=[audience],speech_act_kind=act,utterance_id=eid)
    a.feature(w,communication_channel='writing' if sid=='q1' else 'speech')

# Propositions carry content, never repeat the attitude around that content.
PROPOSITIONS=[
 ('Nia takes the sunflower to her grandmother’s porch.',[38,40,42,47],'s1'),
 ('Nia selects the strongest-looking sunflower leaf.',[51,53,59,61],'s2'),
 ('The tomato seedlings need water.',[73,74,90,92],'q2'),
 ('Nia waters Mrs. Okafor’s seedlings.',[151,153,156],'s3'),
 ('The tomato trays are moved.',[177,178,180,185,187],'q7'),
 ('The filled can weighs less than its subsequently observed actual weight.',[192,194,196,197],'s12'),
 ('Nia reserves some water for her sunflower.',[320,321,323,326,328],'s4'),
 ('Nia keeps holding the umbrella and helps Bell at the same time.',[370,372,376,378],'s5'),
 ('The umbrella stays in place.',[415,418],'q8'),
 ('Temporary umbrella shade allows additional time.',[474,475,476,479],'q9'),
 ('Nia refills the can.',[496,498,499],'q11'),
 ('The hose is repaired and the leak is stopped.',[502,504,510,511],'s7'),
 ('Nia helps Okafor restore the shade cloth.',[588,589,590,591,593],'s9'),
 ('Water splashes on the sunflower leaves.',[687,689,691],'s10'),
 ('The secured umbrella provides shade over the exposed tomato tray.',[431,443,453,457],'s0'),
]
for i,(text,support,scope) in enumerate(PROPOSITIONS,1):
    a.proposition(f'p{i}',text,support,scope_id=scope)

# Lexical and grammatical features are based on the explicit contextual POS above.
for w,row in enumerate(a.words):
    token,pos=row['token'].casefold(),row['pos']
    if pos=='det':
        if token in ('a','an','the'):
            a.feature(w,determiner_kind='definite_article' if token=='the' else 'indefinite_article',
                      definiteness='definite' if token=='the' else 'indefinite')
        elif token in ('my','your','her','his','its','their'):
            a.feature(w,determiner_kind='possessive',possessive_construction='possessive_determiner')
        else:
            a.feature(w,determiner_kind={'each':'distributive','few':'quantificational','some':'quantificational','this':'demonstrative'}.get(token,'quantificational'))
    if pos=='pron' and token in ('she','he','it','they','i','i’ve','you','we','us','me','them'):
        a.feature(w,mention_form='personal_pronoun',grammatical_person=1 if token in ('i','i’ve','we','us','me') else 2 if token=='you' else 3)
        if token not in ('you',):
            a.feature(w,grammatical_number='plural' if token in ('they','them','we','us') else 'singular')
        if token in ('us','me','them'):
            a.feature(w,grammatical_case='objective')
    if pos=='conj' and token in ('and','but'):
        a.feature(w,coordinator_type='conjunctive' if token=='and' else 'adversative')
    if pos=='adp':
        a.feature(w,preposition_valency_frame='NP_complement')
    if pos=='part' and token=='to':
        a.feature(w,dependency_relation='infinitival_marker')
    if 'entity_id' in row and pos=='n':
        a.feature(w,mention_form='proper_name' if row['lemma'] in ('Nia','Bell','Okafor','Mr','Mrs') else 'nominal')

for w,expansion in {88:['do','not'],117:['I','have'],177:['do','not'],301:['would','not'],370:['could','not'],674:['can','is']}.items():
    a.feature(w,contraction_expansion=expansion)
for w in [46,85,155,463,650]:
    a.feature(w,genitive_realization='singular_s_clitic',possessive_construction='prenominal_s_genitive')
for w in [1,34,57,135,568,607]:
    a.feature(w,cardinal_value={1:3,34:1,57:2,135:1,568:1,607:1}[w],numeral_syntactic_role='nominal_determiner')
a.feature(263,cardinal_value=1,partitive_construction=True)
for w in [219,721]: a.feature(w,ordinal_rank=1,adjective_position='attributive_prenominal')
for w in [61,275,717]: a.feature(w,adjective_degree='superlative')
a.feature(194,adjective_degree='comparative')
for w in [59,67,73,77,80,86,156,163,180,203,248,266,337,359,391,530,550,580,651,691]:
    a.feature(w,grammatical_number='plural')
for w in [121,176,199,226,316,326,566,661,727]: a.feature(w,noun_countability='mass')
for w in [142,301,321,370,475,496,507,587]:
    a.feature(w,modal_auxiliary_class='necessity_family' if w==475 else 'volition_family' if w in (301,587) else 'possibility_family')
for w in [142,496,587]: a.feature(w,subject_auxiliary_inversion=True,clause_type='interrogative')
for w in [88,177,301,370]: a.feature(w,polarity='negative',negation_marker_form='not')
a.feature(687,negation_marker_form='not',negation_attachment_kind='VP',negation_scope_id='p14')
for w in [89,166,172,178,415]:
    a.feature(w,verb_form='base',mood='imperative',imperative_subject_status='understood_addressee')
for w in [40,53,153,323,372,376,498,549,589,591,689,702]:
    a.feature(w,clause_finiteness='nonfinite' if w not in (376,) else 'finite')
for w in [26,273,294,372,525,544,654,702]: a.feature(w,verb_form='gerund_participle')
for w in [40,53,144,153,302,476,498,549,589,591,689]: a.feature(w,verb_form='base')
for w,aux in [(118,117),(268,267),(323,322),(332,331),(638,637),(653,652),(670,668)]:
    a.feature(w,aspect='perfect',verb_form='past_participle',perfect_auxiliary_id=a.anchor(aux))
a.feature(185,verb_form='past_participle',participial_function='object_predicative_result_state')
a.feature(504,verb_form='past_participle',voice='passive',passive_auxiliary_id=a.anchor(503))
a.feature(511,verb_form='past_participle',voice='passive',causative_syntax='get_np_past_participle')
PAST=[6,12,17,24,38,51,60,64,74,83,94,100,107,109,115,128,149,159,189,193,197,200,206,212,214,224,232,240,243,258,267,271,284,289,304,310,317,331,341,346,349,357,363,380,387,393,401,412,417,420,431,443,446,453,459,468,481,483,492,519,523,532,535,541,543,547,552,554,563,571,577,584,597,606,614,620,631,637,642,647,652,662,668,677,679,683,694,705,719,728]
for w in PAST: a.feature(w,tense='past',verb_form='finite')
for w in [91,124,132,141,151,183,503,557]: a.feature(w,tense='present',verb_form='finite')
# Recalled past-participle mentions retain their own surface morphology.
a.feature(332,verb_form='past_participle')
a.words[332].pop('tense',None)
a.feature(101,verb_form='past_participle',participial_function='posture_predicative')
a.feature(54,interrogative_form='embedded_subject_wh',question_gap_role='subject')
a.feature(195,subordinator_type='comparative')
for w,kind in {122:'temporal_overlap',204:'temporal_overlap',237:'temporal_boundary',374:'temporal_overlap',444:'concessive',500:'temporal_condition',505:'conditional',533:'temporal',612:'temporal_overlap'}.items():
    a.feature(w,subordinator_type=kind)
for w in [62,249,570,692]: a.feature(w,temporal_order_cue='next')
for w in [49]: a.feature(w,temporal_order_cue='first')
for w in [116,681]: a.feature(w,temporal_frequency_class='repetition')
for w in [300,663]: a.feature(w,temporal_phase_cue='persistence')
a.feature(653,temporal_phase_cue='cessation')
a.feature(701,temporal_signal_relation='before')
a.feature(138,temporal_signal_relation='after')
a.feature(515,temporal_order_cue='later')
a.feature(514,temporal_granularity='minute',measure_unit='min')

# Finite syntactic subjects selected explicitly, not copied from semantic actors.
SUBJECTS={6:'e4',12:'e5',17:'e5',24:'e1',38:'e1',51:'e1',60:'e13',64:'e1',74:'e16',83:'e19',91:'e14',94:'e1',100:'e2',107:'e2',109:'e2',115:'e2',118:'e2',124:'e2',128:'e2',132:'e25',141:'e56',144:'e1',149:'e1',151:'e1',159:'e2',183:'e3',189:'e1',193:'e26',197:'e1',200:'e27',206:'e1',212:'e1',214:'e1',224:'e27',232:'e1',240:'e26',243:'e1',258:'e76',268:'e35',271:'e34',284:'e1',289:'e2',302:'e21',304:'e1',310:'e9',317:'e42',323:'e1',332:'e1',341:'e8',346:'e1',349:'e1',357:'e44',363:'e46',372:'e1',376:'e1',380:'e1',387:'e48',393:'e1',401:'e1',412:'e7',417:'e1',420:'e1',431:'e1',443:'e8',446:'e8',453:'e44',459:'e44',468:'e2',481:'e2',483:'e2',492:'e1',498:'e1',503:'e21',508:'e2',519:'e57',523:'e3',532:'e3',535:'e3',541:'e34',543:'e3',547:'e3',554:'e1',557:'e8',563:'e3',571:'e3',577:'e1',584:'e3',597:'e62',606:'e3',614:'e1',620:'e2',631:'e2',638:'e8',642:'e1',647:'e1',653:'e13',662:'e42',670:'e2',675:'e26',677:'e2',679:'e1',683:'e1',694:'e1',705:'e3',719:'e71',728:'e73'}
for w,eid in SUBJECTS.items(): a.feature(w,grammatical_subject_id=eid)

# Supported physical bindings; values preserve the observed time and scope.
for w,eid,color in [(22,'e7','green'),(28,'e8','yellow'),(146,'e26','blue'),(339,'e8','yellow'),(494,'e26','blue'),(696,'e26','blue')]:
    v=bundle(w,eid,color);v['factuality']='asserted'
    a.feature(w,appearance_color=v)
for w,eid,material in [(385,'e48','clay'),(527,'e58','paper'),(625,'e67','metal')]:
    a.feature(w,material_composition=bundle(w,eid,material))
for w,eid,whole in [(15,'e6','e4'),(59,'e13','e10'),(73,'e16','e14'),(77,'e18','e17'),(113,'e22','e20'),(203,'e29','e26'),(216,'e30','e26'),(230,'e32','e14'),(313,'e41','e1'),(362,'e46','e8'),(367,'e47','e1'),(404,'e50','e8'),(436,'e53','e8'),(440,'e54','e15'),(461,'e55','e9'),(518,'e57','e4'),(569,'e61','e3'),(580,'e60','e14'),(608,'e64','e34'),(616,'e66','e34'),(634,'e69','e34'),(723,'e72','e71'),(731,'e74','e72')]:
    a.feature(w,part_whole_relation=dict(part_id=eid,whole_id=whole,scope_id=a.words[w]['scope_id']))
for w,figure,landmark,relation in [(67,'e14','e15','on'),(74,'e16','e18','over'),(101,'e2','e20','beside'),(254,'e34','e15','above'),(289,'e2','e39','under'),(310,'e9','e41','beside'),(341,'e8','e43','against'),(349,'e8','e37','above'),(393,'e46','e48','inside'),(420,'e51','e52','inside'),(453,'e44','e37','across'),(459,'e44','e55','reaches'),(597,'e34','e63','across'),(728,'e73','e74','at')]:
    a.feature(w,spatial_configuration=bundle(w,figure,dict(landmark=landmark,relation=relation)))
for w,eid,key,value in [(20,'e7','object_temperature','warm'),(112,'e22','object_moisture','dry'),(268,'e35','object_integrity','broken'),(272,'e34','spatial_orientation',{'orientation':'crooked'}),(302,'e21','object_operability','not_operational'),(318,'e42','object_moisture','dry_dusty'),(346,'e8','object_openness','open'),(353,'e37','object_concealment','exposed'),(389,'e48','attributes','heavy'),(403,'e50','object_openness','open'),(443,'e8','object_stability','held_in_place'),(520,'e57','object_openness','open'),(565,'e28','object_moisture','damp'),(573,'e34','spatial_orientation',{'orientation':'crooked'}),(645,'e51','object_attachment','loose'),(647,'e8','object_openness','closed'),(664,'e42','object_moisture','dry'),(670,'e20','object_operability','operational'),(714,'e34','object_attachment','secured')]:
    if key=='attributes': a.feature(w,attributes=[{'name':'weight_description','value':value}])
    else: a.feature(w,**{key:bundle(w,eid,value)})
a.feature(384,containment_contents=bundle(384,'e48',{'contents':['e49'],'excluded_kind':'plant'}),evidence=[384,386,389,391],note='Empty means unplanted here; the pot explicitly contains pebbles.')
a.feature(391,containment_direct=bundle(391,'e49',{'container':'e48'}))
a.feature(36,containment_direct=bundle(36,'e10',{'container':'e9'}))
a.feature(530,containment_direct=bundle(530,'e59',{'container':'e58'}))
a.feature(189,possession_borrower=bundle(189,'e26',{'borrower':'e1'}),possession_lender=bundle(189,'e26',{'lender':'e2'}),evidence=[144,147,164,166,189],note='Loan is established by request, permission and subsequent use; no unmentioned handoff event is invented.')
a.feature(694,transfer_kind=bundle(694,'e26','return'),transfer_completion=bundle(694,'e26',{'completed':True,'recipient':'e2'}),possession_holder=bundle(694,'e26',{'holder':'e2'}))
a.feature(431,object_attachment=bundle(431,'e8',{'attached_to':'e54','via':'e51'}))
a.feature(606,object_attachment=bundle(606,'e64',{'fastened_with':'e65'}))
a.feature(631,object_attachment=bundle(631,'e69',{'secured_with':'e67'}))
a.feature(653,causal_state_delta=bundle(653,'e13',{'before':'drooping','after':'no_longer_drooping'}),evidence=[649,651,653,654,659],note='Later text retrospectively establishes earlier drooping; no exact start or complete health recovery is inferred.')
a.feature(332,causal_resource_consumption=bundle(332,'e26',{'resource':'e27','after':'empty_of_water','used_for':'e14'}))
a.feature(224,causal_effect=bundle(224,'e28',{'cause':EVENT_AT[224],'effect':'darker_soil'}))
a.feature(273,causal_parent=bundle(273,'e37',{'cause':EVENT_AT[258],'effect':'exposed_to_sun'}))
a.feature(443,causal_parent=bundle(443,'e8',{'cause':EVENT_AT[431],'effect':'held_in_place'}),evidence=[431,436,440,443],note='The described securing sequence supports this local physical cause.')

# Mental contents, modality and discourse carry provenance without diagnosing traits.
a.feature(38,goal_owner_id='e1',goal_content_id='p1',goal_polarity='achieve',goal_status='desired')
a.feature(51,goal_owner_id='e1',goal_content_id='p2',goal_status='pending_selection')
a.feature(151,goal_owner_id='e1',goal_content_id='p4',goal_polarity='achieve',intention_publicity='communicated')
a.feature(197,belief_holder_id='e1',epistemic_attitude_kind='expectation',belief_content_id='p6',evidence=[192,194,196,197],note='Actual weight exceeds anticipated weight; expected numeric weight is unknown.')
a.feature(91,belief_holder_id='e1',epistemic_attitude_kind='perceptual_assessment',belief_content_id='p3',epistemic_source_kind='perception',evidence=[73,74,90,91,92],note='Thirsty is Nia’s plant-care assessment, not proof of a human-like conscious sensation.')
a.feature(323,counterfactual_premise={'content':'p7','world':'counterfactual_water_reservation'},evidence=[320,321,323,329,332],note='An unrealized alternative to the completed tomato watering; not an actual saved portion.')
a.feature(370,modal_base={'holder':'e1','kind':'situational_ability'},negation_scope_id='p8')
a.feature(376,causal_preventing_condition=bundle(376,'e1',{'condition':'holding_umbrella_by_hand','blocked':'simultaneously_helping_Bell'}))
a.feature(415,goal_owner_id='e1',goal_content_id='p9',goal_polarity='achieve')
a.feature(475,modal_base={'holder':'e2','kind':'expectation'},modal_scope_id='p10')
a.feature(474,propositional_antecedent_id='p15',evidence=[431,443,453,474],note='That refers to the temporary secured shading arrangement, not the predicted extra time itself.')
a.feature(498,goal_owner_id='e1',goal_content_id='p11',goal_status='permission_requested')
a.feature(505,conditional_antecedent_id='p12')
a.feature(589,goal_owner_id='e3',goal_content_id='p13',intention_publicity='communicated')
a.feature(686,goal_owner_id='e1',goal_content_id='p14',goal_polarity='avoid',evidence=[686,687,689,691],note='Explicit careful-not-to construction supports active avoidance; no completed splashing or guaranteed absence is asserted.')
a.feature(178,negation_scope_id='p5',proposition_polarity='negative',evidence=[177,178,180],note='Negation is within a prohibition; it does not itself describe whether trays moved.')
a.feature(216,lexical_sense_id='rose:watering_can_sprinkler_head',evidence=[191,214,216,220,223],note='Rose denotes the sprinkler attachment, not a flower.')
a.feature(551,reference_unresolved=True,antecedent_candidates=['e35','e76','e34'],evidence=[254,258,262,266,268,538,540,541,551,552],note='It snapped may refer to the clip failure or the shade/flap snap. Do not merge the reporting content with one specific event without this ambiguity.')
a.feature(552,evidence_resolution_status='ambiguous',supporting_event_ids=[EVENT_AT[258],EVENT_AT[268]])
a.feature(711,antecedent_candidates=['e31','e37'],evidence=[80,220,276,710,711],note='Final labeled tomato tray is not unambiguously the first tray or the exposed nearest tray; distinct description retained.')
a.feature(541,evidence_resolution_status='ambiguous',supporting_event_ids=[EVENT_AT[258]],evidence=[258,268,538,540,541,547],note='The reported slip may be the narrated displacement or an earlier related one. Separate report-content event retains uncertain identity and chronology.')
a.feature(10,figurative_mapping={'target_id':'e4','source_image':'glass oven','kind':'simile','literal_event':False})
a.feature(476,lexical_idiom_reading={'meaning':'gain_additional_time','reading':'idiomatic'})
a.feature(409,figurative_mapping={'target_id':'e7','source_image':'breath','kind':'metaphor','literal_event':False})
a.feature(737,figurative_mapping={'target_id':'e73','source_image':'little glass bell','kind':'simile','literal_event':False})
a.feature(732,attributes=[{'name':'appearance','value':'bright'}],evidence=[725,727,731,732,736,737],note='Reflected brightness; not an emitting light source or literal bell.')
a.feature(1,time_expression_id='time_three_oclock',temporal_uncertainty={'clock':'3:00','meridiem':'unspecified','date':'unspecified'})
a.feature(513,quantity_approximation_cue='small_unspecified_number')
a.feature(515,temporal_elapsed={'unit':'minute','value_description':'a_few','anchor':'preceding_repair_discussion'},evidence=[505,511,512,513,514,515],note='No exact minute count is supplied.')

# Current teacher assertion status follows evidence attribution, not event actuality.
for w,row in enumerate(a.words):
    if row.get('event_id') or any(key in row for key in ('goal_content_id','belief_content_id')):
        scope=row['scope_id']
        a.feature(w,assertion_status='attributed_claim' if scope.startswith('q') or scope in ('s3','s6','s7','s8','s9') else 'asserted')

FEEDBACK={
 'summary':'Complete manual retrospective annotation of the greenhouse story, with distinct plants/pots/clips, scoped instructions and counterfactuals, and temporary shade preceding repair.',
 'ambiguities':[
  {'words':[551,552], 'issue':'It snapped could denote the clip or shade/flap incident; the report has an unresolved participant and candidate support events.'},
  {'words':[258,541,547], 'issue':'Okafor reports earlier slipping and a trip for clips, while the narrated snap occurs after Nia waters. Separate report-content event retains uncertain identity and phase chronology; it may describe this same displacement or an earlier related slip.'},
  {'words':[220,276,711], 'issue':'First watered tray, nearest exposed tray and final labeled tray are not explicitly identical; separate IDs preserve that uncertainty.'},
  {'words':[137], 'issue':'One watering can is a capacity unit rather than an independently introduced can object; no numeric volume is invented.'},
  {'words':[702], 'issue':'Before leaving establishes ordering but does not explicitly narrate departure completion; departure remains a projected event.'},
 ],
 'feature_gaps':[
  {'meaning':'qualitative size, weight, visual strength, texture and manner','resolution':'Use contextual events and legacy attributes where no precise existing typed dimension applies; no new attribute names needed in this story.'},
  {'meaning':'same underlying dynamic process at goal/in-progress/completed stages','resolution':'Actual repeated mentions reuse event IDs; hypothetical instructions/conditions remain separately scoped. Leak-repair work and completed tap repair retain distinct phase events because exact physical component equivalence is not explicit.'},
 ],
 'prompt_feedback':[
  'Keep the v1 empty-domain example: the empty clay pot explicitly contains pebbles, so universal zero containment would be wrong.',
  'Add examples of event reference with unresolved physical participant (It snapped) and historical reports with unresolved phase chronology.',
  'Contraction can’s in Your can’s ready has noun-leading POS and lemma can; it is not possessive or the modal auxiliary.',
  'Label imperatives must not attribute authorship simply because an owner is named on the label.',
 ],
 'coverage_notes':'Every word has explicit contextual POS and normalized lemma. Important content has entities/events/grammar/state features. Sparse annotation, no quota. The source leaves no completed home journey or leaf-selection outcome. No psychic emotion, unsupported ownership transfer, exact duration or complete plant recovery was invented.',
 'reviewed_all_words':True,
}
a.save(FEEDBACK)
