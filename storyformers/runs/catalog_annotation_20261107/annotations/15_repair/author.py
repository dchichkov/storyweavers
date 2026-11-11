"""Manually interpreted, retrospective v3 annotation of the repair story."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation

a = Annotation('15_repair', prompt_version='v3')
for key in ('appearance_color', 'part_whole_relation', 'figurative_mapping'):
    a.use_extension(key)

# Each line is one explicitly tagged paragraph, in the original word order.
TAGS = [
 'det n n n v adp det n n adp n adp n v adv adp det n adp pron v det adj n n adj adp det n n conj v adp n adp v n n conj n det adj adj n v det adj adj n conj pron v pron',
 'n v part v det n conj det n v adv adp pron pron v n n part v pron adp det n adp det n n v num adj n n v adp det n conj det n n v n adv adv pron v',
 'v pron v det adj n n v n n det n adj n v adj',
 'n n v pron det n v pron adj conj v pron v',
 'n v adp det n pron v',
 'pron det n pron v v v det n adv adv conj v det n',
 'conj n v adv v det n adp n adp det n n det n adp det n v adj conj adj n v det n adp det n conj v adp det adj n pron v adv adp det pron pron v det n det n adp det n adv pron det n v v',
 'adv pron v',
 'pron v pron part v pron adv v n v conj v det n adv adv v det n v v v adj',
 'n v det n adp det n adj',
 'n v det n v adv adv v adp det n det adj n v v',
 'pron v v pron n v det n v part v adv adp det n',
 'n v adp det adj n adv adp det n conj pron v pron det n v v conj det n v v pron v v det n v pron adv pron v det n n',
 'v pron v pron adj pron v v v det n adp det n conj pron v pron adv',
 'n n v conj pron v pron v det n adv det adj n v det n n',
 'n v det n adv adp n n det n v adj pron v pron v pron conj adv det n v v',
 'adv adj pron v pron v pron v conj v pron adv',
 'n v adv pron v det n adv adp det n pron v det n adj conj v det n det n pron v det n det adj n v adv adp det n',
 'pron adv pron v',
 'n n v det n conj n v det n pron v adv det n conj v det adj adj n adp n n v adp det n conj det n num adj n v det n adp det n det n pron v det n v v adj adv adv det n v v det n v conj v',
 'n v adp det n pron adp det n pron v det n v v adj',
 'v pron v det n n v',
 'pron v pron conj pron v det n pron v adv adp det adj adj n n v det n adp det n adv v det n conj n adv adp n pron v det n conj pron v adj v det n n part v',
 'det n det n v adv n v det adj n adp det n n det n det n adv det adj n adp det n adp det n',
 'n v num n adp det n n n v det pron conj adv pron v pron adp det n pron v adp det adj n v adv part v det n pron v adp det n det n v part v adp det n n conj pron v det adj n',
 'n v det n adp n n conj v det adj n adp det adj n adv adj n adp n v v adv pron v det n adv adp det n',
 'det n adp n v adp det n adj n conj v adp det adj n adp det n num n n v adp det n',
]
LEMMAS = {
 'Ada':'Ada','Niko':'Niko','Mr':'Mr','Rafi':'Rafi','I':'I','Its':'its',
 'stood':'stand','jars':'jar','nails':'nail','lined':'line','sat':'sit','scratched':'scratch',
 'years':'year','hauling':'haul','dolls':'doll','books':'book','flowerpots':'flowerpot',
 'gave':'give','pushed':'push','wanted':'want','came':'come','tools':'tool','had':'have',
 'plants':'plant','waiting':'wait','roof’s':'roof','spilled':'spill','asked':'ask','cart’s':'cart',
 'is':'be','Is':'be','handed':'hand','glanced':'glance','rattles':'rattle','That’s':'that',
 'said':'say','smiling':'smile','was':'be','carrying':'carry','clouds':'cloud','rooftops':'rooftop',
 'were':'be','wheeled':'wheel','crouched':'crouch','looked':'look','others':'other',
 'stopped':'stop','rattling':'rattle','spun':'spin','moved':'move','frowned':'frown',
 'tightened':'tighten','thinking':'think','been':'be','set':'set','lurched':'lurch','locked':'lock',
 'We':'we','dragged':'drag','might':'may','could':'can','gripped':'grip','made':'make','worse':'bad',
 'Let’s':'let','Niko’s':'Niko','helped':'help','raindrops':'raindrop','spotted':'spot','stones':'stone',
 'carried':'carry','wasn’t':'be','won’t':'will','thought':'think','turning':'turn','tipped':'tip','held':'hold',
 'rocked':'rock','Something’s':'something','steadied':'steady','loosened':'loosen','slid':'slide',
 'found':'find','pinched':'pinch','tapped':'tap','turned':'turn','peered':'peer','unwound':'unwind',
 'checked':'check','strands':'strand','leaving':'leave','wheels':'wheel','cracks':'crack',
 'lifted':'lift','took':'take','stopping':'stop','leaned':'lean','began':'begin','leaves':'leaf',
 'reached':'reach','returned':'return','tucked':'tuck','bits':'bit','things':'thing','kept':'keep',
 'rolled':'roll','gathered':'gather','trembled':'tremble','does':'do',
 72:'she',118:'she',332:'she',65:'that',
}
for paragraph, tags in enumerate(TAGS):
    a.tag(paragraph, tags, LEMMAS)

ENTITIES = [
 ('Ada','person',[53,66,72,100,105,118,128,172,191,207,209,217,240,271,294,302,308,312,322,332,344,356,358,373,379,382,390,401,415,423,427,480,498,504,516,532,552,583,627,651]),
 ('Niko','person',[79,151,232,260,326,330,477,484,486,494,500,575]),
 ('Mr. Rafi','person',[68,69,102,107,108,115,116,138,350,351,369,417,418,632,633]),
 ('Ada and Niko','person_group',[256,282,589,595,622]),
 ('courtyard repair bench','bench',[3,19,78,178,320,658]),
 ('fig tree','tree',[8]), ('jars of nails','jar_group',[10]), ('nails','nail_group',[12]),
 ('back of repair bench','bench_part',[17]),
 ('shared blue toy cart','cart',[24,40,52,58,110,143,175,238,243,259,284,286,305,310,385,388,398,421,556,570,594,654,666,677]),
 ('cart left front wheel','wheel',[43,112,122,126,132,133,184,185,193,203,211,214,227,253,280,291,364,393,404,431,456,459,473,497,502,528,542,549,674]),
 ('other cart wheels','wheel_group',[190]),
 ('left-wheel nut','nut',[194,222,353,360,426,462,535,537]),
 ('Rafi small spanner','spanner',[104,120,199,347,630]),
 ('repair bench tools','tool_group',[75]),
 ('six young tomato plants','plant_group',[84,97,158,263,317]),
 ('tomato plant tray','tray',[88,156,235,276,335,582,591]),
 ('roof above plants','roof',[91]), ('roof downspout and drain','downspout',[92,270]),
 ('water spilled by downspout','water',[94]), ('courtyard gate','gate',[162]),
 ('dark clouds','cloud_group',[164]), ('courtyard rooftops','roof_group',[167]),
 ('courtyard','courtyard',[1,161]), ('rain in repair episode','rain',[61,613,662]),
 ('cart handle','handle',[306]), ('Niko mouth','body_part',[327]),
 ('courtyard paving stones','paving',[343,560]), ('cart side used during inspection','cart_part',[389]),
 ('green loop of kite string','string',[413,437,440,469,482,507,508,515,638]),
 ('left wheel hub','hub',[444]), ('left wheel washer','washer',[447,526]),
 ('frayed string end','string_end',[450]), ('inside surface of left wheel','wheel_surface',[453]),
 ('Niko kite','kite',[485]), ('Niko kite tail','kite_tail',[489]),
 ('cart axle','axle',[519]), ('possible additional string strands','string_group',[522]),
 ('tray end lifted by Niko','tray_end',[578]), ('other tray end taken by Ada','tray_end',[586]),
 ('sunny courtyard wall','wall',[600]), ('leaning plant pot','pot',[606]),
 ('neighboring plant pot','pot',[611]), ('fig tree leaves','leaf_group',[620]),
 ('sheltered courtyard corner','place',[626]), ('lost bits tin','tin',[642]),
 ('lost bits of things kept in tin','object_group',[645,647]),
 ('bead of rain on cart','raindrop',[660]), ('six trembling tomato leaves','leaf_group',[680]),
 ('courtyard breeze','air_motion',[684]), ('cart wheels collectively','wheel_group',[571]),
 ('rattle noise kind','sound_kind',[48,135,137,400,562]),
 ('scrape noise kind','sound_kind',[250,298,564]), ('dry click sound','sound_kind',[407]),
 ('Ada shoulder','body_part',[481]), ('historically carried dolls','doll_group',[36]),
 ('historically carried books','book_group',[37]), ('historically carried flowerpots','flowerpot_group',[39]),
 ('first rain drops on paving','raindrop_group',[339]), ('paving cracks','crack_group',[574]),
 ('blue cart side in final image','cart_part',[668]),
]
for i,(name,kind,mentions) in enumerate(ENTITIES,1):
    a.entity(f'e{i}',name,kind,mentions)
a.entities['e4']['member_ids']=['e1','e2']
a.entities['e51']['member_ids']=['e11','e12']
a.entities['e38']['existence_status']='searched_for_not_confirmed'
a.entities['e30']['identity_note']='Something inside is retrospectively resolved to the discovered string; origin in Niko kite is separately attributed.'
for eid in ('e52','e53','e54'):
    a.feature(a.entities[eid]['mentions'],referent_kind='kind')

def scope(sid,lo,hi,kind,holder=None,parent='s0',description=''):
    a.scope(sid,range(lo,hi+1),kind=kind,holder_id=holder,parent=parent,description=description)

quotes=[
 (99,104,'e1','e3'),(109,114,'e1','e3'),(121,127,'e3','e1'),(133,134,'e1','e3'),
 (135,137,'e3','e1'),(141,149,'e3','e1'),(206,206,'e1','e3'),(239,239,'e2','e1'),
 (256,259,'e2','e1'),(262,270,'e2','e1'),(307,311,'e1','e2'),(314,325,'e1','e2'),
 (352,355,'e1','e3'),(358,366,'e1','e3'),(367,368,'e3','e1'),(371,378,'e3','e1'),
 (413,414,'e1','e3'),(482,492,'e2','e1'),(493,497,'e1','e2'),
]
for i,(lo,hi,holder,audience) in enumerate(quotes,1):
    scope(f'q{i}',lo,hi,'quotation',holder,description='Direct speech; claims remain locally attributed.')
    a.scopes[f'q{i}']['addressee_ids']=[audience]
    a.feature(range(lo,hi+1),quote_mode='direct',assertion_status='attributed_claim')
scope('s1',56,62,'desired_repair','e1',description='Repair desired before rain, not yet achieved.')
scope('s2',68,78,'desired_trust','e1',description='Rafi trusting Ada is desired by Ada, not asserted attained.')
scope('s3',226,231,'belief_content','e1',description='Ada inferred prior crookedness; no narrator endorsement.')
scope('s4',281,293,'conditional_risk','e1',description='Dragging, tipping and breakage are considered alternatives, not actual.')
scope('s5',294,300,'contemplated_pretence','e1',description='Pretending scrape is unimportant is considered and not enacted.')
scope('s6',375,378,'proposed_future_turn','e3',parent='q16',description='Question anticipates a possible further turn; does not narrate one.')
scope('s7',488,492,'remembered_belief_content','e2',parent='q18',description='Niko reports earlier tail-loose belief; actual tail detachment is not established.')
scope('s8',521,522,'search_target','e1',description='Additional strands sought; no positive finding stated.')

PROPS=[
 ('Ada repairs the cart before the rain arrives.',[54,56,58,59,61,62],'s1'),
 ('Mr. Rafi trusts Ada with the bench tools.',[68,69,71,72,75,78],'s2'),
 ('Ada borrows Rafi small spanner.',[99,100,101,102,104],'q1'),
 ('The cart left wheel is loose.',[110,112,113,114],'q2'),
 ('Is the wheel loose, or does it rattle?',[121,122,123,124,125,126,127],'q3'),
 ('The wheel rattles when the cart is pushed.',[43,44,48,49,51,52,133,134],'s0'),
 ('The described rattle is a sound.',[135,136,137,121,123,127],'q5'),
 ('Ada brings the cart to the bench and inspects it.',[141,143,145,147,149],'q6'),
 ('The wheel had been crooked.',[226,227,228,229,230,231],'s3'),
 ('Is the cart ready to move the plants?',[239,233,235,238],'q8'),
 ('Ada and Niko drag the cart.',[256,258,259,282,283,284],'q9'),
 ('The plants get away from the downspout.',[263,264,266,267,270],'q10'),
 ('The cart tips if dragged.',[281,283,286,287,288],'s4'),
 ('The left wheel breaks if the cart is dragged.',[281,283,291,292,293],'s4'),
 ('The scrape is of no significance.',[297,298,299,300],'s5'),
 ('Ada has worsened the cart wheel problem.',[308,309,310,311],'q11'),
 ('Niko waits before moving the loaded cart.',[307,258,303],'q11'),
 ('Ada and Niko place the plants under the bench while Ada identifies the wheel problem.',[314,315,317,320,321,322,323,324,325],'q12'),
 ('Ada identifies what is wrong with the cart wheel.',[322,323,324,325],'q12'),
 ('The nut was loose before Ada tightened it.',[353,354,355],'q13'),
 ('The nut was not loose before Ada tightened it.',[353,354,355],'q13'),
 ('The wheel turns after Ada tightened the nut.',[364,365,366],'q14'),
 ('Ada tightened the nut and the wheel now cannot turn.',[358,359,360,361,362,364,365,366],'q14'),
 ('What can Ada check before turning it again, with nut or wheel reference unresolved?',[371,372,373,374,375,376,377,378],'q16'),
 ('The held wheel rattles while Ada rocks the cart.',[391,393,396,398,399,400],'s0'),
 ('Something is inside the wheel.',[413,414],'q17'),
 ('The trapped string is from Niko kite.',[482,483,484,485],'q18'),
 ('The kite tail had come loose.',[488,489,490,491,492],'s7'),
 ('Niko previously thought the kite tail had come loose.',[486,487,488,489,490,491,492],'q18'),
 ('Niko holds the wheel for Ada.',[493,494,495,497],'q19'),
 ('The wheel rattles during the repaired empty-cart trial.',[553,556,561,562],'s0'),
 ('The cart scrapes during the repaired empty-cart trial.',[553,556,563,564],'s0'),
 ('The repaired wheel turns smoothly and the empty cart moves without rattle or scrape.',[550,551,553,561,562,563,564],'s0'),
 ('The string caused the earlier wheel clatter and drag.',[469,471,473,474,476],'s0'),
 ('The nut was snug before Ada initial intervention.',[462,463,464,465,466,467],'s0'),
 ('The plants need to get away from the downspout.',[263,264,265,266,267,270],'q10'),
 ('Ada and Niko can drag the cart.',[256,257,258,259],'q9'),
 ('The wheel has stopped rattling after initial tightening.',[203,204,205,206],'s0'),
 ('Can Ada borrow the small spanner from Mr. Rafi?' ,[99,100,101,102,104],'q1'),
 ('Can Niko hold the wheel for Ada?',[493,494,495,497],'q19'),
]
for i,(text,support,sid) in enumerate(PROPS,1): a.proposition(f'p{i}',text,support,scope_id=sid)

def attribution(sid):
    while sid:
        data=a.scopes[sid]
        if data['kind'] in ('quotation','belief_content','remembered_belief_content','contemplated_pretence'):
            return 'attributed_claim'
        sid=data.get('parent')
    return 'asserted'

def ev(w,label,actor=None,patients=(),*,type='other',fact='asserted',roles=None,instruments=(),recipient=None,support=None):
    eid=f'ev{w+1}'
    a.event(eid,w,label,actor=actor,patients=patients,type=type,factuality=fact,
            roles=roles,instruments=instruments,recipient=recipient,support=support)
    a.feature(w,assertion_status=attribution(a.words[w]['scope_id']))
    return eid

def say(w,speaker,audience,pid,kind,*,roles=None):
    eid=f'ev{w+1001}'
    primary=a.words[w].get('role')!='action' and a.words[w]['scope_id']=='s0'
    a.event(eid,w,f'{kind}: {pid}',type='speak',actor=speaker,recipient=audience,
            scope='s0',primary=primary,roles=roles)
    a.feature(w,speech_act_kind=kind,utterance_id=eid,utterance_content_id=pid,
              addressee_ids=[audience] if audience else [],communication_channel='speech',
              communication_scope_bundle={'speaker_id':speaker,'utterance_event_id':eid,
                                          'scope_id':'s0','assertion_status':'asserted'})
    # Never replace the grammatical subject/actor of a primary quoted predicate.
    if primary: a.feature(w,speaker_id=speaker,assertion_status='asserted')
    return eid

# P0–P5: physical setting, goals and observation-versus-diagnosis dialogue.
ev(4,'repair bench stands beneath fig tree',patients=['e5'],type='state',roles={'patient':[3],'landmark':[8]})
ev(13,'nail jars are lined along bench back',patients=['e7'],type='state',roles={'patient':[10],'landmark':[17]})
ev(20,'shared toy cart stands beside bench',patients=['e10'],type='state',roles={'patient':[24],'landmark':[19]})
ev(31,'cart surface is scratched by earlier hauling',patients=['e10'],type='state')
ev(35,'cart historically hauls dolls books and flowerpots',patients=['e56','e57','e58'],instruments=['e10'],roles={'patient':[36,37,39]})
ev(44,'left wheel makes rattle during cart pushes',patients=['e11'],type='state',roles={'patient':[43],'sound':[48]})
ev(51,'people push the cart in recurring use',patients=['e10'],type='move',roles={'actor_variable':[50],'patient':[52]})
ev(54,'Ada wants timely cart repair','e1',type='feel',roles={'experiencer':[53]})
ev(56,'Ada repairs cart','e1',['e10'],type='repair',fact='desired',roles={'patient':[58]})
ev(62,'rain arrives',patients=['e25'],type='other',fact='hypothetical',roles={'patient':[61]})
ev(67,'Ada wants Rafi trust','e1',type='feel',roles={'experiencer':[66]})
ev(71,'Rafi trusts Ada with bench tools','e3',type='state',fact='desired',roles={'holder':[68,69],'target':[72],'domain':[75]})
ev(80,'Niko has six tomato plants','e2',['e16'],type='state',roles={'actor':[79],'patient':[84]})
ev(85,'tomato plants stand waiting in tray',patients=['e16'],type='state',roles={'patient':[84],'container':[88]})
ev(93,'downspout spills water at plants location',patients=['e20'],type='move',roles={'source':[92],'patient':[94]})
ev(98,'plants stand at downspout outlet',patients=['e16'],type='state',roles={'patient':[97]})
ev(101,'Ada borrows small spanner','e1',['e14'],type='obtain',fact='desired',roles={'actor':[100],'patient':[104]})
say(106,'e1','e3','p39','request_permission',roles={'actor':[105],'addressee':[107,108]})
ev(114,'left wheel is loose',patients=['e11'],type='state',fact='reported',roles={'patient':[112]})
say(114,'e1','e3','p4','diagnosis_claim')
ev(117,'Rafi lends spanner to Ada','e3',['e14'],type='transfer',recipient='e1',roles={'actor':[115,116],'recipient':[118],'patient':[120]})
ev(123,'wheel is loose',patients=['e11'],type='state',fact='hypothetical',roles={'patient':[122]})
ev(127,'wheel rattles',patients=['e11'],type='state',fact='hypothetical',roles={'patient':[126]})
say(123,'e3','e1','p5','diagnostic_question')
ev(129,'Ada glances at left wheel','e1',['e11'],type='perceive',roles={'actor':[128],'patient':[132]})
a.mention_event('ev45',134,role='action',note='Ada reports the already established recurring rattle, without validating looseness.')
say(134,'e1','e3','p6','observation_report')
ev(137,'described rattle is a sound',patients=['e52'],type='state',fact='reported',roles={'patient':[135]})
say(139,'e3','e1','p7','distinguish_observation_from_diagnosis',roles={'actor':[138]})
ev(140,'Rafi smiles','e3',type='other')
ev(141,'Ada brings cart to bench','e1',['e10'],type='move',fact='desired',roles={'patient':[143]})
ev(147,'Ada inspects cart','e1',['e10'],type='perceive',fact='desired')
say(141,'e3','e1','p8','instruction')

# P6–P12: three tightening movements, separate trial and mechanical failure.
ev(154,'Niko carries plant tray toward gate','e2',['e17'],type='move',roles={'actor':[151],'patient':[156],'contents':[158],'direction':[162]})
ev(168,'clouds are dark and swollen',patients=['e22'],type='state',roles={'patient':[164],'landmark':[167]})
ev(173,'Ada wheels cart to repair bench','e1',['e10'],type='move',roles={'actor':[172],'patient':[175],'destination':[178]})
ev(180,'Ada crouches beside left wheel','e1',type='state',roles={'landmark':[184]})
ev(186,'left wheel looks similar to other wheels',patients=['e11'],type='state',roles={'patient':[185],'comparison':[190]})
ev(192,'Ada gives nut first turn with spanner','e1',['e13'],instruments=['e14'],roles={'actor':[191],'patient':[194],'instrument':[199]})
ev(201,'Ada gives nut another turn','e1',['e13'],instruments=['e14'])
ev(204,'left wheel stops rattling',patients=['e11'],type='state',roles={'patient':[203]})
a.mention_event('ev205',205,role='predicate_complement',note='Rattling is the terminated activity, not a fresh asserted rattle.')
say(208,'e1','e3','p38','result_demonstration',roles={'actor':[207]})
ev(210,'Ada spins left wheel for first check','e1',['e11'],roles={'actor':[209],'patient':[211]})
ev(213,'Ada checks left wheel motion','e1',['e11'],type='perceive')
ev(216,'left wheel moves barely',patients=['e11'],type='move',roles={'patient':[214]})
ev(218,'Ada frowns','e1',roles={'actor':[217]})
ev(220,'Ada tightens nut a third time','e1',['e13'],roles={'patient':[222]})
ev(225,'Ada thinks left wheel was crooked','e1',type='state')
ev(231,'left wheel was crooked',patients=['e11'],type='state',fact='reported',roles={'patient':[227]})
ev(233,'Niko loads tray in cart','e2',['e17'],type='move',roles={'actor':[232],'patient':[235],'destination':[238]})
say(239,'e2','e1','p10','readiness_question')
ev(241,'Ada pushes loaded cart','e1',['e10'],type='move',roles={'actor':[240]})
ev(244,'loaded cart lurches forward',patients=['e10'],type='move',roles={'patient':[243]})
ev(247,'cart stops with scrape',patients=['e10'],type='move',roles={'sound':[250]})
ev(255,'left wheel has jammed',patients=['e11'],type='state',roles={'patient':[253]})
ev(258,'Ada and Niko drag cart','e4',['e10'],type='move',fact='hypothetical',roles={'actor':[256],'patient':[259]})
say(261,'e2','e1','p37','alternative_proposal',roles={'actor':[260]})
ev(264,'plants need relocation away from drain',patients=['e16'],type='state',fact='reported',roles={'patient':[263]})
ev(266,'plants move away from drain',patients=['e16'],type='move',fact='desired',roles={'source':[270]})
say(264,'e2','e1','p36','express_urgent_need')
ev(272,'Ada looks at tray and wheel','e1',['e17','e11'],type='perceive',roles={'actor':[271],'patient':[276,280]})
ev(283,'Ada and Niko drag cart','e4',['e10'],type='move',fact='hypothetical',roles={'actor':[282],'patient':[284]})
ev(288,'cart tips during dragging',patients=['e10'],type='move',fact='hypothetical',roles={'patient':[286]})
ev(293,'left wheel breaks during dragging',patients=['e11'],type='other',fact='hypothetical',roles={'patient':[291]})
ev(296,'Ada pretends scrape is unimportant','e1',type='other',fact='hypothetical',roles={'actor':[294]})
ev(299,'scrape is insignificant',patients=['e53'],type='state',fact='hypothetical',roles={'patient':[298]})
ev(303,'Ada grips cart handle','e1',['e26'],roles={'actor':[302],'patient':[306]})

# P13–P18: admission, requested delay and diagnosis without inventing a tool return.
ev(307,'Niko waits before moving cart','e2',type='state',fact='desired')
ev(309,'Ada worsened cart wheel problem','e1',['e10'],type='other',fact='reported',roles={'actor':[308],'patient':[310]})
say(313,'e1','e2','p16','admit_error',roles={'actor':[312]})
say(307,'e1','e2','p17','request_wait')
ev(315,'Ada and Niko place plants under bench','e4',['e16'],type='move',fact='desired',roles={'patient':[317],'destination':[320]})
ev(323,'Ada identifies wheel problem','e1',type='other',fact='desired',roles={'actor':[322]})
say(315,'e1','e2','p18','joint_plan')
ev(328,'Niko mouth tightens',patients=['e27'],type='state',roles={'patient':[327]})
ev(331,'Niko helps Ada lower tray','e2',['e17'],recipient='e1',roles={'actor':[330],'recipient':[332],'patient':[335]})
ev(333,'Ada and Niko lower plant tray out of cart','e4',['e17'],type='move',roles={'patient':[335]})
ev(340,'first raindrops mark paving stones',patients=['e28'],type='other',roles={'causer':[339],'patient':[343]})
ev(345,'Ada carries spanner back to Rafi','e1',['e14'],type='move',roles={'actor':[344],'patient':[347],'destination_person':[350,351]})
ev(355,'nut was loose before initial tightening',patients=['e13'],type='state',fact='negated',roles={'patient':[353]})
say(357,'e1','e3','p21','correct_initial_diagnosis',roles={'actor':[356]})
a.mention_event('ev221',359,role='action',note='Report of Ada already narrated tightening; encompasses earlier turns rather than inventing another turn.')
a.mention_event('ev221',[358],role='actor')
a.mention_event('ev221',[360],role='patient')
ev(366,'wheel turns after initial tightening',patients=['e11'],type='move',fact='negated',roles={'patient':[364]})
say(359,'e1','e3','p23','report_action_and_failure')
say(370,'e3','e1','p23','acknowledge_report',roles={'actor':[369]})
ev(374,'Ada checks diagnostic evidence','e1',type='perceive',fact='hypothetical',roles={'actor':[373]})
ev(376,'Ada turns the unresolved nut or wheel again','e1',type='other',fact='hypothetical')
say(374,'e3','e1','p24','diagnostic_question')
ev(380,'Ada considers diagnostic question','e1',type='state',roles={'actor':[379]})
ev(383,'Ada tips cart onto its side','e1',['e10'],type='move',roles={'actor':[382],'patient':[385],'supporting_part':[389]})
ev(391,'Ada holds wheel still','e1',['e11'],roles={'actor':[390],'patient':[393]})
ev(396,'Ada rocks cart with wheel held','e1',['e10'],type='move',roles={'patient':[398]})
ev(400,'held wheel produces rattle during rocking',patients=['e11'],type='state',fact='negated')
ev(402,'Ada spins wheel for second diagnostic check','e1',['e11'],roles={'actor':[401],'patient':[404]})
ev(408,'wheel makes dry click once per revolution',patients=['e11'],type='state',roles={'sound':[407]})
ev(414,'something is inside wheel',patients=['e30'],type='state',fact='reported',roles={'patient':[413]})
say(416,'e1','e3','p26','diagnostic_observation',roles={'actor':[415]})

# P19–P26: source-backed explanation, cooperative repair, distinct trial and relocation.
ev(419,'Rafi steadies cart','e3',['e10'],roles={'actor':[417,418],'patient':[421]})
ev(424,'Ada loosens nut','e1',['e13'],roles={'actor':[423],'patient':[426]})
ev(428,'Ada slides wheel off axle','e1',['e11'],type='move',roles={'actor':[427],'patient':[431]})
ev(433,'Ada finds trapped loop of string','e1',['e30'],type='perceive',roles={'patient':[437,440]})
ev(441,'green string is pinched between hub and washer',patients=['e30'],type='state',roles={'landmark':[444,447]})
ev(451,'frayed string end taps wheel interior on rotations',patients=['e33'],type='other',roles={'patient':[450],'contact_surface':[453]})
ev(460,'wheel turns during clicking episodes',patients=['e11'],type='move',roles={'patient':[459]})
ev(465,'nut was snug before initial intervention',patients=['e13'],type='state',roles={'patient':[462]})
ev(471,'trapped string caused wheel clatter and drag',patients=['e11'],type='other',roles={'causer':[469],'patient':[473]})
a.mention_event('ev45',474,role='action',note='Narrator explains the already described recurring wheel rattle.')
ev(476,'wheel drags while string is trapped',patients=['e11'],type='move')
ev(478,'Niko peers over Ada shoulder','e2',type='perceive',roles={'actor':[477],'landmark':[481]})
ev(483,'discovered string comes from Niko kite',patients=['e30'],type='state',fact='reported',roles={'patient':[482],'source':[485]})
say(483,'e2','e1','p27','identify_origin')
ev(487,'Niko earlier believed kite tail came loose','e2',type='state',fact='reported',roles={'holder':[486]})
ev(491,'kite tail comes loose',patients=['e36'],type='state',fact='reported',roles={'patient':[489]})
say(487,'e2','e1','p29','report_previous_belief')
ev(495,'Niko holds wheel for repair','e2',['e11'],type='state',fact='desired',roles={'actor':[494],'patient':[497]})
say(499,'e1','e2','p40','request_help',roles={'actor':[498]})
ev(501,'Niko holds removed wheel','e2',['e11'],type='state',roles={'actor':[500],'patient':[502]})
ev(505,'Ada unwinds trapped string','e1',['e30'],type='repair',roles={'actor':[504],'patient':[507]})
ev(509,'string comes away as knot',patients=['e30'],type='move',roles={'patient':[508],'configuration':[515]})
ev(517,'Ada checks axle for further string strands','e1',['e37'],type='perceive',roles={'actor':[516],'patient':[519],'search_target':[522]})
ev(524,'Ada slides washer and wheel back into place','e1',['e32','e11'],type='repair',roles={'patient':[526,528]})
ev(533,'Ada turns nut to snug fit','e1',['e13'],roles={'actor':[532],'patient':[535]})
ev(539,'reassembled nut is snug',patients=['e13'],type='state',roles={'patient':[537]})
ev(540,'reassembly leaves clearance for wheel rotation',patients=['e11'],type='state',roles={'patient':[542]})
ev(545,'wheel spins with adequate clearance',patients=['e11'],type='move',fact='hypothetical')
ev(550,'reassembled wheel turns smoothly',patients=['e11'],type='move',roles={'patient':[549]})
ev(553,'Ada pushes empty repaired cart across paving','e1',['e10'],type='move',roles={'actor':[552],'patient':[556],'surface':[560]})
ev(562,'repaired wheel produces rattle in empty-cart trial',patients=['e11'],type='state',fact='negated')
ev(564,'repaired cart scrapes in empty-cart trial',patients=['e10'],type='state',fact='negated')
ev(568,'cart wheels bump softly over cracks',patients=['e51'],type='move',roles={'patient':[571],'surface':[574]})
ev(576,'Niko lifts one end of plant tray','e2',['e39'],type='move',roles={'actor':[575],'patient':[578]})
ev(584,'Ada takes other tray end','e1',['e40'],type='other',roles={'actor':[583],'patient':[586]})
ev(590,'Ada and Niko load plant tray together','e4',['e17'],type='move',roles={'actor':[589],'patient':[591],'destination':[594]})
ev(596,'Ada and Niko push loaded cart toward sunny wall','e4',['e10'],type='move',roles={'actor':[595],'direction':[600]})
ev(601,'Ada and Niko stop once to adjust pot','e4',type='move')
ev(604,'Ada and Niko shift leaning pot','e4',['e42'],type='move',roles={'patient':[606]})
ev(608,'pot leans against neighboring pot',patients=['e42'],type='state',roles={'patient':[606],'landmark':[611]})
ev(614,'rain begins pattering on fig leaves',patients=['e44'],type='other',roles={'causer':[613],'patient':[620]})
a.mention_event('ev615',616,role='predicate_complement',note='Patter is the activity whose onset is narrated, not a separate rain episode.')
ev(623,'Ada and Niko reach sheltered corner with cart','e4',['e10'],type='move',roles={'actor':[622],'destination':[626]})
ev(628,'Ada returns spanner to Rafi','e1',['e14'],type='transfer',recipient='e3',roles={'actor':[627],'patient':[630],'recipient':[632,633]})
ev(635,'Ada tucks removed string into lost-bits tin','e1',['e30'],type='move',roles={'patient':[638],'destination':[642]})
ev(649,'lost bits are kept in tin',patients=['e47'],type='state',roles={'patient':[645,647]})
ev(652,'Ada rolls cart back beside repair bench','e1',['e10'],type='move',roles={'actor':[651],'patient':[654],'destination':[658]})
ev(663,'rain bead slides down blue cart side',patients=['e48'],type='move',roles={'patient':[660],'surface':[668]})
ev(670,'rain bead gathers beneath quiet left wheel',patients=['e48'],type='state',roles={'landmark':[674]})
ev(681,'six tomato leaves tremble in breeze inside cart',patients=['e49'],type='move',roles={'patient':[680],'surroundings':[684]})

# Morphology and constructions: these lists are contextual manual decisions.
for eid, data in a.entities.items():
    for j,w in enumerate(data['mentions']):
        a.feature(w,reference_chain_id=f'rc_{eid}',reference_introduction=(j==0))
for w in [53,68,69,79,105,107,108,115,116,128,151,172,217,232,240,260,271,344,350,351,379,417,418,423,477,498,516,552,575,583,627,632,633]:
    a.feature(w,mention_form='proper_name',grammatical_number='singular')
for w in [91,110,305,326,666]:
    a.feature(w,mention_form='genitive_nominal',possessive_construction='s_genitive',grammatical_number='singular')
for w in [16,40,102,193,388,480,484,570,610]:
    a.feature(w,mention_form='possessive_determiner',determiner_kind='possessive',possessive_construction='possessive_determiner')
for w in [19,52,65,66,72,97,100,118,122,126,133,138,185,191,207,209,211,214,256,259,282,284,294,302,308,310,312,322,324,330,332,356,358,360,369,373,377,382,390,401,415,427,459,486,494,500,502,504,508,532,537,552,589,591,595,622,651]:
    if a.words[w]['pos']=='pron': a.feature(w,mention_form='personal_pronoun')
for w in [100,308,322,358,486]:
    a.feature(w,personal_pronoun_series='first_person_singular',grammatical_person=1,grammatical_number='singular',grammatical_case='nominative')
for w in [256]: a.feature(w,personal_pronoun_series='first_person_plural',grammatical_person=1,grammatical_number='plural',grammatical_case='nominative')
for w in [373,494]: a.feature(w,personal_pronoun_series='second_person',grammatical_person=2,grammatical_number='singular',grammatical_case='common')
for w in [66,138,191,207,209,294,302,312,330,356,369,382,390,401,415,427,500,504,532,651]:
    a.feature(w,personal_pronoun_series='third_person_singular',grammatical_person=3,grammatical_number='singular',grammatical_case='nominative')
for w in [72,118,332]: a.feature(w,personal_pronoun_series='third_person_singular',grammatical_person=3,grammatical_number='singular',grammatical_case='accusative')
for w in [97,282,589,595,622]: a.feature(w,personal_pronoun_series='third_person_plural',grammatical_person=3,grammatical_number='plural',grammatical_case='nominative')
for w in [135,482]: a.feature(w,mention_form='demonstrative_pronoun',contraction_expansion=['that','is'])
a.feature(413,mention_form='indefinite_pronoun',contraction_expansion=['something','is'],reference_specificity='specific_unknown_until_discovery',evidence=[413,433,437,440],note='Retrospective identity with the found string; the original speaker has not yet identified its material or origin.')
a.feature(314,contraction_expansion=['let','us'],mood='hortative',complement_control_type='inclusive_speaker_addressee')
a.feature(354,contraction_expansion=['was','not'],negation_marker_form='contracted_not')
a.feature(365,contraction_expansion=['will','not'],negation_marker_form='contracted_not')
for w in [19,52,122,126,133,185,211,214,259,284,310,360,377,459,502,508,537,591]:
    a.feature(w,grammatical_person=3,grammatical_number='singular')
for w in [100,102,256,308,322,358,373,484,486,494]:
    sid=a.words[w].get('quotation_scope_id')
    if sid: a.feature(w,reference_quotation_shift={'scope_id':sid,'speaker_id':a.scopes[sid]['holder_id'],'addressee_ids':a.scopes[sid]['addressee_ids'],'resolved_entity_id':a.words[w].get('entity_id')})
a.feature(377,reference_unresolved=True,reference_competitor_ids=['e13','e11'],evidence=[353,359,364,366,376,377],note='Rafi may mean turn the nut again or test the wheel again; neither identity is uniquely licensed.')
a.feature(324,reference_unresolved=False,mention_form='situation_anaphor',evidence=[323,324,325],note='Figure it out refers to identifying the wheel problem, not physically manipulating the cart.')
a.feature(65,mention_form='discourse_demonstrative',clausal_object_id='p1')
a.feature(50,mention_form='indefinite_pronoun',quantifier_binding={'variable':'x_push','restriction':'people who push the cart','nuclear_scope_event_id':'ev52','scope_id':'s0'},evidence=[49,50,51],note='Conditional recurring use, not a newly introduced named pusher.')
for w in [201,586]: a.feature(w,mention_form='nominal_ellipsis',nominal_ellipsis_license='contextual_nominal_head_recovery')
a.feature(201,coordination_ellipsis_source_id=a.anchor(196),evidence=[192,196,200,201],note='Another repeats the nut-turn event, not a second nut.')
a.feature(586,coordination_ellipsis_source_id=a.anchor(578),evidence=[578,584,586],note='Other is the other tray end, separately identified from the end Niko lifts.')
a.feature(190,mention_form='nominal_ellipsis',grammatical_number='plural')

# Function-word annotations use the already manually chosen POS, never infer it.
for w,row in enumerate(a.words):
    if row['pos']=='det' and row['lemma'] in ('the','a'):
        a.feature(w,determiner_kind='definite_article' if row['lemma']=='the' else 'indefinite_article',definiteness='definite' if row['lemma']=='the' else 'indefinite')
for w in [399,561,563]: a.feature(w,determiner_kind='negative_quantifier',negation_marker_form='no',negation_attachment_kind='existential_nominal')
for w in [411,457]: a.feature(w,determiner_kind='distributive',distributive_nominal_form=a.words[w]['lemma'])
a.feature(521,determiner_kind='additive_quantity',quantity_comparison_cue='additional',factuality='hypothetical',evidence=[517,520,521,522],note='Search for additional strands does not establish that any exist.')
a.feature(546,determiner_kind='demonstrative',temporal_deixis='current_repair_trial')
a.feature(448,cardinal_value=1)
a.feature(577,cardinal_value=1,quantity_part={'entity_id':'e39','whole_id':'e17','scope_id':'s0','assertion_status':'asserted','value':{'count':1,'unit':'tray_end'}})
a.feature(81,cardinal_value=6,quantity_total={'entity_id':'e16','scope_id':'s0','assertion_status':'asserted','value':{'count':6,'unit':'plant'}})
a.feature(678,cardinal_value=6,quantity_total={'entity_id':'e49','scope_id':'s0','assertion_status':'asserted','value':{'count':6,'unit':'leaf'}},evidence=[678,680],note='Six leaves are described; this does not assert one leaf per plant or six total leaves on the plants.')
a.feature(338,ordinal_rank=1)
for w in [10,12,33,36,37,39,75,84,158,164,167,263,317,339,343,522,560,571,574,620,645,647,680]: a.feature(w,grammatical_number='plural')
for w in [3,8,17,24,43,48,58,61,78,88,92,104,112,120,132,137,143,149,156,162,175,178,184,194,196,199,203,222,227,235,238,243,250,253,270,276,280,286,291,298,306,320,327,335,347,353,364,385,389,393,398,400,404,407,412,421,426,431,437,440,444,447,450,453,456,462,469,473,481,485,489,497,507,515,519,526,528,531,535,542,543,547,549,556,562,564,568,578,582,594,600,606,611,613,626,630,638,642,654,658,660,668,674,677,684]: a.feature(w,grammatical_number='singular')
for w in [311]: a.feature(w,adjective_degree='comparative')
for w in [63,224]: a.feature(w,adverb_degree='comparative')
# Finite tense and nonfinite forms are selected by clause, including reduced clauses.
PAST=[4,20,44,51,54,62,67,80,93,98,106,117,129,139,152,168,173,180,186,192,204,208,210,216,218,220,229,230,233,241,244,247,254,261,272,283,299,303,309,313,328,331,340,345,354,357,359,370,380,383,391,396,402,408,416,419,424,428,433,451,460,463,464,470,478,487,490,501,505,509,517,524,533,538,550,553,576,584,590,596,608,614,623,628,635,648,652,663,670,681]
for w in PAST: a.feature(w,tense='past',clause_finiteness='finite',verb_form='finite')
for w in [113,121,125,127,134,257,264,372,493]: a.feature(w,tense='present',clause_finiteness='finite')
# Auxiliary-governed past participles are not themselves finite or past-tense carriers.
for w in [13,31,230,255,441,464,471,491,649]:
    a.words[w].pop('tense',None)
    a.feature(w,verb_form='past_participle',clause_finiteness='nonfinite')
for w in [35,85,140,154,205,225,376,540,601]: a.feature(w,verb_form='gerund_participle',clause_finiteness='nonfinite')
for w in [56,71,101,127,141,147,213,258,266,288,293,296,307,315,323,333,366,374,474,476,495,545,604,616]:
    a.feature(w,verb_form='base')
for w in [56,71,101,213,258,266,288,293,296,333,366,374,474,476,495,545,604,616]: a.feature(w,clause_finiteness='nonfinite')
for w in [141,147,307,315]: a.feature(w,mood='imperative',clause_finiteness='finite')
for w in [152,154]: a.feature(w,aspect='progressive')
for w in [228,229,230,231,254,255,463,464,465,470,471,490,491,492]: a.feature(w,aspect='perfect')
for w in [13,31,441,648,649]: a.feature(w,voice='passive')
for w in [55,70,212,265,544,603,615]: a.feature(w,infinitive_marker_id=a.anchor(w))
for w in [99,257,372,493]: a.feature(w,modal_auxiliary_class='can',modal_scope_id=f'clause_t{w}')
for w in [287,292]: a.feature(w,modal_auxiliary_class='may',modal_base={'kind':'risk_possibility','scope_id':'s4','assertion_status':'asserted'})
a.feature(295,modal_auxiliary_class='can',modal_base={'kind':'available_alternative','scope_id':'s5','assertion_status':'attributed_claim'})
a.feature(228,modal_auxiliary_class='must',modal_base={'kind':'epistemic_inference','holder_id':'e1','content_id':'p9','scope_id':'s3','assertion_status':'attributed_claim'})
a.feature(99,polar_question_marker='can',modal_base={'kind':'permission_request','holder_id':'e1','content_id':'p3','scope_id':'q1','assertion_status':'attributed_claim'})
a.feature(257,modal_base={'kind':'physical_ability_proposal','holder_id':'e2','content_id':'p11','scope_id':'q9','assertion_status':'attributed_claim'})
a.feature(372,modal_base={'kind':'available_diagnostic_action','holder_id':'e3','content_id':'p24','scope_id':'q16','assertion_status':'attributed_claim'})
a.feature(493,polar_question_marker='can',modal_base={'kind':'request_for_help','holder_id':'e1','content_id':'p30','scope_id':'q19','assertion_status':'attributed_claim'})
a.feature(365,modal_auxiliary_class='will',modal_base={'kind':'current_mechanical_inability','entity_id':'e11','content_id':'p22','scope_id':'q14','assertion_status':'attributed_claim'},evidence=[362,364,365,366],note='Will not turn expresses the wheel present failure to rotate, not refusal by an agent or a future-only prediction.')
a.feature(371,interrogative_form='object_wh_question',question_gap_role='direct_object',question_requested_slot='diagnostic_check')
a.feature(121,polar_question_marker='be',alternative_question_set=['p4','p6'])
a.feature(124,disjunction_alternatives=['p4','p6'],coordination_category='clause')
a.feature(239,interrogative_form='elliptical_polar_question',question_requested_slot='cart_ready_for_transport')
for w in [59,375]: a.feature(w,complementizer_type='temporal_subordinator',temporal_signal_relation='before')
for w in [321,422,503]: a.feature(w,complementizer_type='temporal_subordinator',temporal_signal_relation='overlap')
a.feature(536,complementizer_type='temporal_subordinator',temporal_signal_relation='until')
a.feature(621,complementizer_type='temporal_subordinator',temporal_signal_relation='overlap')
a.feature(49,complementizer_type='temporal_subordinator',temporal_frequency_class='conditional_recurrence')
a.feature(607,relative_marker_form='relative_that',relative_pronoun_id=a.anchor(607),grammatical_subject_id='e42')
a.feature(643,relative_marker_form='relative_where',relative_pronoun_id=a.anchor(643))
for w in [38,527]: a.feature(w,coordination_category='NP')
for w in [30,170]: a.feature(w,coordination_category='predicative_phrase')
for w in [146,179,219,361,395,432,475,587,634,669]: a.feature(w,coordination_category='VP')
for w in [89,329]: a.feature(w,coordination_category='clause')
a.feature(289,disjunction_alternatives=['p13','p14'],coordination_category='clause')

# Grammatical subjects are authored independently of actors and affected entities.
SUBJECTS={4:'e5',13:'e7',20:'e10',31:'e10',44:'e11',54:'e1',62:'e25',67:'e1',71:'e3',80:'e2',85:'e16',93:'e19',98:'e16',101:'e1',106:'e1',113:'e11',114:'e11',117:'e3',121:'e11',123:'e11',127:'e11',129:'e1',134:'e11',137:'e52',139:'e3',140:'e3',154:'e2',168:'e22',169:'e22',171:'e22',173:'e1',180:'e1',186:'e11',192:'e1',204:'e11',208:'e1',210:'e1',216:'e11',218:'e1',220:'e1',225:'e1',230:'e11',231:'e11',233:'e2',241:'e1',244:'e10',247:'e10',255:'e11',258:'e4',261:'e2',264:'e16',272:'e1',283:'e4',288:'e10',293:'e11',296:'e1',299:'e53',303:'e1',309:'e1',313:'e1',323:'e1',328:'e27',331:'e2',340:'e59',345:'e1',354:'e13',355:'e13',357:'e1',359:'e1',366:'e11',370:'e3',374:'e1',380:'e1',383:'e1',391:'e1',396:'e1',402:'e1',408:'e54',414:'e30',416:'e1',419:'e3',424:'e1',428:'e1',433:'e1',441:'e30',451:'e33',460:'e11',465:'e13',471:'e30',474:'e11',476:'e11',478:'e2',483:'e30',487:'e2',491:'e36',495:'e2',499:'e1',501:'e2',505:'e1',509:'e30',517:'e1',524:'e1',533:'e1',538:'e13',539:'e13',550:'e11',553:'e1',576:'e2',584:'e1',590:'e4',596:'e4',601:'e4',608:'e42',614:'e25',616:'e25',623:'e4',628:'e1',635:'e1',649:'e47',652:'e1',663:'e48',670:'e48',681:'e49'}
for w,eid in SUBJECTS.items(): a.feature(w,grammatical_subject_id=eid)
OBJECTS={51:'e10',56:'e10',71:'e1',80:'e16',93:'e20',101:'e14',117:'e14',141:'e10',154:'e17',173:'e10',192:'e13',210:'e11',220:'e13',233:'e17',258:'e10',272:'e17',283:'e10',303:'e26',309:'e10',315:'e16',331:'e1',333:'e17',340:'e28',345:'e14',359:'e13',383:'e10',391:'e11',396:'e10',402:'e11',419:'e10',424:'e13',428:'e11',433:'e30',451:'e34',471:'e11',495:'e11',501:'e11',505:'e30',517:'e37',533:'e13',540:'e11',553:'e10',576:'e39',584:'e40',590:'e17',604:'e42',623:'e45',628:'e14',635:'e30',652:'e10'}
# Gave its nut a turn is a double-object light-verb frame: nut is indirect object.
OBJECTS.pop(192)
# Look at an object has a prepositional rather than direct object.
OBJECTS.pop(272)
for w,eid in OBJECTS.items(): a.feature(w,grammatical_object_id=eid)
a.feature(192,indirect_object_id='e13',dative_alternation_form='double_object_light_verb')
a.feature(117,indirect_object_id='e1',dative_alternation_form='double_object')
for w,eid in {56:'e1',147:'e1',213:'e1',266:'e16',307:'e2',315:'e4',333:'e1',376:'e1',545:'e11',604:'e4'}.items(): a.feature(w,subject_controller_id=eid)
a.feature(331,object_controller_id='e1',complement_control_type='object_control_help')
for w,eid in {5:'e6',9:'e7',11:'e8',15:'e9',18:'e5',73:'e15',76:'e5',86:'e17',130:'e11',157:'e16',159:'e21',165:'e23',176:'e5',181:'e11',188:'e12',197:'e14',236:'e10',268:'e19',273:'e17',278:'e11',318:'e5',349:'e3',387:'e29',438:'e30',454:'e11',479:'e55',483:'e35',511:'e30',520:'e38',557:'e28',569:'e51',572:'e60',579:'e17',592:'e10',597:'e41',609:'e43',617:'e44',631:'e3',639:'e46',646:'e47',656:'e5',661:'e25',664:'e61',671:'e11',675:'e10',682:'e50'}.items(): a.feature(w,prepositional_object_id=eid,preposition_valency_frame='NP')
a.feature(442,preposition_valency_frame='coordinated_NP',evidence=[444,447],note='Between takes the hub and washer together; neither alone is the full complement.')

# Auxiliary construction corrections: bare lexical rattle/have are nonfinite.
a.words[127].pop('tense',None)
a.feature(127,clause_finiteness='nonfinite')
a.words[229].pop('tense',None)
a.feature(229,verb_form='base',clause_finiteness='nonfinite')
a.feature(99,tense='present',clause_finiteness='finite')

# Correlated physical and semantic values retain the carrier, local scope and status.
def bound(w,key,entity,value,*,status=None,fact=None,scope_id=None,evidence=None,note=None):
    sid=scope_id or a.words[w]['scope_id']
    bundle={'entity_id':entity,'scope_id':sid,'assertion_status':status or attribution(sid),'value':value}
    if fact: bundle['factuality']=fact
    a.feature(w,**{key:bundle},evidence=evidence,note=note)

def spatial(w,figure,landmark,relation,*,fact=None,note=None):
    bound(w,'spatial_configuration',figure,{'landmark_id':landmark,'relation':relation},fact=fact,note=note)

def part(w,part_id,whole_id):
    a.feature(w,part_whole_relation={'part_id':part_id,'whole_id':whole_id,'scope_id':a.words[w]['scope_id'],'assertion_status':attribution(a.words[w]['scope_id'])})

for w,p,h in [(17,'e9','e5'),(43,'e11','e10'),(91,'e18','e23'),(92,'e19','e18'),(194,'e13','e11'),(306,'e26','e10'),(327,'e27','e2'),(389,'e29','e10'),(444,'e31','e11'),(447,'e32','e11'),(450,'e33','e30'),(453,'e34','e11'),(481,'e55','e1'),(489,'e36','e35'),(519,'e37','e10'),(578,'e39','e17'),(586,'e40','e17'),(620,'e44','e6'),(668,'e61','e10'),(680,'e49','e16')]: part(w,p,h)
# The individual roof is not asserted to be a member of the background rooftops set.
a.words[91].pop('part_whole_relation',None)
for args in [(5,'e5','e6','beneath'),(11,'e8','e7','contained_in'),(15,'e7','e9','lined_along'),(18,'e10','e5','beside'),(86,'e16','e17','inside'),(95,'e20','e16','at_location_of'),(165,'e22','e23','above'),(181,'e1','e11','beside'),(236,'e17','e10','inside'),(387,'e10','e29','resting_on_own_side'),(414,'e30','e11','inside'),(479,'e2','e55','viewing_over'),(592,'e17','e10','inside'),(609,'e42','e43','leaning_against'),(617,'e25','e44','falling_on'),(639,'e30','e46','inside'),(643,'e47','e46','inside'),(656,'e10','e5','beside'),(664,'e48','e61','down_surface_of'),(671,'e48','e11','beneath'),(675,'e49','e10','inside')]: spatial(*args)
spatial(318,'e16','e5','under',fact='desired',note='Proposed placement under the bench; lowering the tray is narrated but no later sentence explicitly locates it under the bench.')
bound(41,'spatial_frame_kind','e11',{'frame':'cart_intrinsic','axis':'left','whole_id':'e10'})
bound(42,'spatial_axis','e11',{'axis':'front_back','position':'front','whole_id':'e10'})
bound(145,'spatial_deictic_center','e5',{'speaker_id':'e3','value':'at_repair_bench'},evidence=[141,143,145,173,178],note='Here resolves retrospectively to the bench where Rafi proposes inspection.')
bound(442,'spatial_configuration','e30',{'relation':'pinched_between','landmark_ids':['e31','e32']})
bound(441,'spatial_contact','e30',{'contact_with_ids':['e31','e32'],'state':'pinched'})
bound(451,'spatial_contact','e33',{'contact_with_id':'e34','state':'repeated_tapping_on_rotation'})
bound(31,'object_surface_condition','e10','scratched_from_prior_hauling')
bound(22,'possession_shared','e10',{'shared':True,'owners_unspecified':True},evidence=[22],note='Shared is explicit, but the text does not list owners or establish Ada and Niko as owners.')
for w,eid,color in [(25,'e10','blue'),(436,'e30','green'),(637,'e30','green'),(667,'e61','blue')]: bound(w,'appearance_color',eid,color)
a.feature(26,figurative_mapping={'target_id':'e10','source_image':'a summer sky','dimension':'blue_color','kind':'simile','literal_event':False,'scope_id':'s0','assertion_status':'asserted'})
bound(46,'object_sound_level','e11',{'quality':'sharp_little_rattle','event_id':'ev45'})
bound(183,'object_sound_level','e11','noisy_rattling')
bound(169,'appearance_color','e22','dark')
bound(171,'object_shape','e22','swollen')
bound(435,'object_tension_state','e30','tight_loop')
bound(449,'object_integrity','e33','frayed')
bound(513,'object_surface_condition','e30','fuzzy')
bound(515,'object_shape','e30','knot')
a.feature(514,lexical_sense_id='stubborn_resistant_to_unwinding',evidence=[505,513,514,515],note='Physical resistance of the knot, not a mental disposition of string.')
bound(114,'object_attachment','e11','loose',fact='reported',evidence=[109,112,113,114],note='Ada diagnosis is a quoted claim; rattle alone does not establish looseness.')
bound(123,'object_attachment','e11','loose',fact='hypothetical',evidence=[121,122,123,124,127],note='One alternative in Rafi question, not a looseness assertion.')
bound(216,'object_operability','e11','barely_rotates_after_initial_tightening')
bound(255,'object_operability','e11','jammed_cannot_rotate')
a.feature(255,lexical_sense_id='lock_up_become_mechanically_jammed',evidence=[244,247,250,253,255],note='Wheel jam, not engagement of a lock or latch.')
bound(355,'object_attachment','e13','loose',fact='negated',evidence=[352,353,354,355],note='Ada correction denies previous nut looseness; preserve earlier diagnosis as an earlier attributed claim.')
bound(366,'object_operability','e11','turns',fact='negated')
bound(394,'motion_control','e11',{'state':'held_stationary','controller_id':'e1','cause_event_id':'ev392'},evidence=[391,393,394],note='Still during the controlled rocking test means deliberately held stationary, not independently jammed.')
bound(406,'object_sound_level','e11',{'quality':'dry_click','event_id':'ev409'})
bound(428,'object_attachment','e11',{'state':'removed','from_id':'e37'})
bound(465,'object_attachment','e13',{'fit':'snug','time':'before_initial_nut_turn'},evidence=[192,194,462,463,465,466,467],note='All along corrects the original looseness diagnosis; it does not override the later explicit loosening at w424.')
bound(492,'object_attachment','e36','loose',fact='reported',evidence=[486,487,488,489,491,492],note='Content of Niko prior belief within his current report; no narrator-confirmed tail detachment.')
bound(509,'object_attachment','e30',{'state':'removed_from_wheel','from_id':'e11'})
bound(524,'object_assembly_state','e10',{'state':'wheel_and_washer_refitted','part_ids':['e11','e32']})
bound(539,'object_attachment','e13',{'fit':'snug','time':'final_reassembly'})
bound(540,'causal_enabling_condition','e11',{'condition':'reassembly_leaves_clearance','enabled_event_id':'ev546'})
bound(550,'object_operability','e11','turns_smoothly')
bound(555,'object_fill_state','e10','empty',evidence=[553,555,556],note='Empty-cart test after the tray was removed; the story does not identify its exact interim resting location.')
bound(568,'object_sound_level','e10',{'quality':'soft_bumping_over_cracks','event_id':'ev569'})
bound(673,'object_sound_level','e11','quiet',evidence=[550,561,562,563,564,673],note='The repaired wheel no longer has the problematic rattle/scrape; preceding soft bumps over cracks remain compatible.')

# Tool custody and transport: handoff, carrying back, and final return are distinct.
bound(102,'possession_owner','e14',{'owner_id':'e3'},fact='reported',evidence=[99,101,102,104],note='Your small spanner addresses Rafi; recorded as the speaker attribution, distinct from subsequent custody.')
bound(117,'possession_holder','e14',{'holder_id':'e1','source_id':'e3','event_id':'ev118'})
bound(117,'possession_borrower','e14',{'borrower_id':'e1','lender_id':'e3','event_id':'ev118'},evidence=[99,101,104,117,120],note='Rafi hands over the requested spanner; contextual completed temporary loan.')
bound(117,'possession_lender','e14',{'lender_id':'e3','borrower_id':'e1','event_id':'ev118'})
bound(197,'possession_user','e14',{'user_id':'e1','event_id':'ev193'})
bound(345,'possession_holder','e14',{'holder_id':'e1','event_id':'ev346'},evidence=[345,347,348,350,351],note='Carried back for consultation does not say Rafi takes it or establish an additional completed return.')
bound(628,'possession_holder','e14',{'holder_id':'e3','source_id':'e1','event_id':'ev629'})
bound(628,'possession_return_target','e14',{'person_id':'e3','event_id':'ev629','status':'completed'})
bound(484,'possession_owner','e35',{'owner_id':'e2'},fact='reported')
# Material origin is a provenance relation, not an asserted departure movement.
a.words[483].pop('motion_source',None)
a.feature(483,evidence_source_kind='reported_origin',evidence_quote_source_id='e2',evidence=[482,483,484,485],note='Attributed material origin does not establish a departure movement or entry mechanism into the wheel.')
for w,entity,carrier,eid in [(154,'e17','e2','ev155'),(173,'e10','e1','ev174'),(233,'e17','e10','ev234'),(345,'e14','e1','ev346'),(590,'e17','e10','ev591')]:
    bound(w,'motion_carrier',entity,{'carrier_id':carrier,'event_id':eid})
for w,entity,dest,eid in [(173,'e10','e5','ev174'),(233,'e17','e10','ev234'),(623,'e10','e45','ev624'),(635,'e30','e46','ev636'),(652,'e10','e5','ev653')]:
    bound(w,'motion_destination',entity,{'landmark_id':dest,'event_id':eid,'reached':True})
for w,entity,direction,landmark in [(159,'e17','toward','e21'),(176,'e10','to','e5'),(245,'e10','forward',None),(267,'e16','away_from','e19'),(336,'e17','down',None),(387,'e10','onto','e29'),(429,'e11','off','e37'),(597,'e10','toward','e41'),(655,'e10','back_to','e5'),(664,'e48','down','e61')]:
    bound(w,'motion_trajectory_phase',entity,{'direction':direction,'landmark_id':landmark},fact='desired' if w==267 else None)
bound(623,'motion_arrival_completion','e4',{'destination_id':'e45','event_id':'ev624','completed':True})
bound(601,'motion_pace_variability','e4',{'event_id':'ev597','pattern':'one_pause_to_adjust_pot'})
bound(588,'event_collective_participants','e4',{'event_id':'ev591','participant_ids':['e1','e2']})
bound(331,'event_collective_participants','e4',{'event_id':'ev334','participant_ids':['e1','e2'],'contributions':{'e2':'help','e1':'lift'}})

# Time, alternatives and negation preserve their local proposition identities.
for w in [200,246,277,381,523,650]: a.feature(w,temporal_order_cue='then')
a.feature(153,temporal_deixis='already_at_current_reference_time')
a.feature(362,temporal_deixis='now_at_report_time')
for w in [378]: a.feature(w,temporal_frequency_class='repetition')
a.feature(192,temporal_iteration_index=1)
a.feature(201,temporal_iteration_index=2)
a.feature(220,temporal_iteration_index=3,evidence=[192,196,200,201,220,223,224],note='A turn, another turn, and once more specify three separate tightening actions.')
a.feature(409,temporal_iteration_count=1,temporal_recurrence={'event_id':'ev409','scope_id':'s0','assertion_status':'asserted','value':{'count':1,'per':'wheel_revolution'}})
a.feature(457,temporal_frequency_class='each_rotation',temporal_recurrence={'event_id':'ev452','scope_id':'s0','assertion_status':'asserted','value':{'condition_event_id':'ev461','frequency':'each_rotation'}})
a.feature(59,temporal_deadline={'event_id':'ev57','goal_content_id':'p1','boundary':'rain_arrival','scope_id':'s1','assertion_status':'asserted','factuality':'desired'},evidence=[54,56,59,61,62],note='Desired completion before rain, not actual completion before the later first raindrops.')
a.feature(422,temporal_overlap={'event_ids':['ev420','ev425'],'scope_id':'s0','assertion_status':'asserted'})
a.feature(503,temporal_overlap={'event_ids':['ev502','ev506'],'scope_id':'s0','assertion_status':'asserted'})
a.feature(621,temporal_overlap={'event_ids':['ev615','ev624'],'scope_id':'s0','assertion_status':'asserted'})
a.feature(466,temporal_persistence_window={'entity_id':'e13','value':'snug','interval':'before_Ada_initial_intervention','scope_id':'s0','assertion_status':'asserted'})
a.feature(33,temporal_granularity='year',temporal_duration={'event_id':'ev36','scope_id':'s0','assertion_status':'asserted','value':{'magnitude':'unspecified_plural','unit':'year'}})
for w,pid in [(354,'p20'),(365,'p22'),(399,'p25'),(561,'p31'),(563,'p32')]: a.feature(w,polarity='negative',negation_scope_id=pid)
a.feature(354,negation_attachment_kind='clausal_auxiliary')
a.feature(365,negation_attachment_kind='modal_predicate')
a.feature(300,lexical_sense_id='nothing_of_consequence',evidence=[296,298,299,300],note='The contemplated pretence minimizes the scrape; it does not deny that a sound occurred.')
a.proposition('p41','Ada and Niko drag the cart in the contemplated conditional branch.',[281,282,283,284],scope_id='s4')
a.proposition('p42','If Ada and Niko drag the cart, the cart may tip or the wheel may break.',[281,283,287,288,289,292,293],scope_id='s4')
a.feature(281,complementizer_type='conditional',conditional_antecedent_id='p41',conditional_consequent_id='p42',evidence=[281,283,288,289,293],note='Consequent alternatives are bound separately in p43; p42 preserves the full conditional and neither consequence is asserted to occur.')
# The conditional consequent is the disjunctive risk content, not the entire conditional.
a.proposition('p43','The cart may tip or the left wheel may break.',[285,286,287,288,289,290,291,292,293],scope_id='s4')
a.feature(281,conditional_consequent_id='p43')
a.feature(301,discourse_relation_kind='alternative_rejection',discourse_alternative_set=['p11','p15'],evidence=[283,288,293,295,296,300,301,303,307,309],note='Dragging and minimizing the scrape are entertained; Ada instead holds the cart, admits the mistake and asks to pause. Neither rejected action is narrated as completed.')

# Attitudes bind target content, not recursive reports of the same attitude.
for w,goal,owner,pid in [(54,'g_repair','e1','p1'),(67,'g_trust','e1','p2'),(315,'g_stage_plants','e4','p18'),(323,'g_diagnose','e1','p19')]:
    a.feature(w,goal_owner_id=owner,goal_content_id=pid,goal_polarity='achieve',goal_status='active',goal_scope_bundle={'owner_id':owner,'intention_event_id':a.words[w]['event_id'],'scope_id':a.words[w]['scope_id'],'assertion_status':attribution(a.words[w]['scope_id'])})
a.feature(67,goal_priority='more_important_than_timely_repair',evidence=[63,64,65,66,67,71],note='More than that explicitly prioritizes desired trust; no claim that Rafi actually comes to trust Ada.')
a.feature(71,trust_holder_id='e3',trust_target_id='e1',trust_domain='using_repair_bench_tools',factuality='desired',evidence=[67,68,69,71,72,75])
a.feature(315,plan_commitment_status='proposed',plan_step_ids=['ev316','ev324'],cooperation_goal_id='p18')
a.feature(495,goal_owner_id='e1',goal_content_id='p30',goal_polarity='achieve',goal_status='requested_help',plan_commitment_status='proposed')
a.feature(225,belief_holder_id='e1',belief_content_id='p9',belief_polarity='accept',belief_certainty='inferred_necessity',reasoner_id='e1',reasoning_mode='diagnostic_guess',reasoning_conclusion_id='p9',evidence=[216,220,225,227,228,231],note='The explicit thought attributes crookedness to Ada; the actual finding explains the rattle/drag with trapped string, without proving the wheel had no geometric irregularity.')
a.feature(231,assertion_status='attributed_claim',evidence_report_depth=1)
a.feature(114,belief_holder_id='e1',belief_content_id='p4',belief_polarity='accept',evidence_source_kind='speaker_diagnosis',evidence_quote_source_id='e1')
a.feature(129,evidence_observation_channel='vision')
a.feature(134,evidence_observation_channel='hearing',evidence_source_kind='quoted_observation',assertion_status='attributed_claim')
a.feature(139,dialogue_repair_kind='distinguish_observation_from_diagnosis',dialogue_repair_target_id='ev1115',evidence=[114,123,127,134,135,137],note='Rafi calls rattling a sound and invites inspection rather than accepting it as proof of looseness.')
a.feature(357,dialogue_repair_kind='correction',dialogue_repair_target_id='ev1115',evidence=[114,353,354,355],note='Ada revises her looseness diagnosis with the narrower nut correction. Do not treat wheel-loose and nut-loose as identical propositions.')
a.feature(357,belief_revision={'holder_id':'e1','earlier_content_id':'p4','revised_content_id':'p21','revision_event_id':'ev1358','scope_id':'s0','assertion_status':'asserted','relationship':'narrows_and_corrects_mechanical_diagnosis'})
a.feature(380,reasoner_id='e1',reasoning_mode='deliberate_diagnostic_check',reasoning_content_id='p24',reasoning_scope_bundle={'reasoner_id':'e1','event_id':'ev381','scope_id':'s0','assertion_status':'asserted'})
a.feature(402,evidence_observation_channel='hearing',evidence_source_kind='controlled_rotation_check',evidence=[391,396,399,400,402,407,408],note='Rocking with held wheel followed by wheel rotation distinguishes noise conditions; the unexplained rotation after the earlier jam remains a source continuity gap.')
a.feature(433,evidence_source_kind='inspection_discovery',evidence_observation_channel='vision',evidence=[428,431,433,437,440,441],note='Ada finding establishes the trapped object, not narrator endorsement of Niko later origin claim.')
a.feature(487,belief_holder_id='e2',belief_content_id='p28',belief_polarity='accept',belief_certainty='unspecified',belief_nested_holders=['e2'],evidence_report_depth=1,evidence=[486,487,489,491,492],note='Current quote reports a prior belief; whether the kite tail actually detached is left unknown.')
a.feature(491,assertion_status='attributed_claim',evidence_report_depth=2)
a.feature(517,reasoner_id='e1',reasoning_mode='inspect_for_remaining_obstruction',reasoning_evidence_gap='No result of the search for additional strands is explicitly given.',evidence=[517,519,521,522])

# Supported mechanics and narrative interpretations are distinct from mental claims.
bound(471,'causal_mechanism','e11',{'cause_entity_id':'e30','mechanism':'trapped_string_and_frayed_end_contact','effect_event_ids':['ev45','ev477'],'evidence_event_ids':['ev434','ev442','ev452']},evidence=[441,444,447,451,453,460,469,471,474,476])
bound(220,'causal_side_effect','e11',{'intended_goal':'repair_cart','observed_effect':'jammed_after_further_tightening','effect_event_ids':['ev256'],'causal_status':'retrospective_supported_interpretation'},status='candidate',evidence=[192,201,216,220,255,309,311,359,365,366],note='Tightening worsens operation according to Ada admission and observed sequence; the exact contribution of each individual turn is not stated.')
bound(509,'causal_termination_condition','e11',{'condition_event_id':'ev506','removed_obstruction_id':'e30','later_test_content_id':'p33'},status='candidate',evidence=[471,505,509,524,533,550,562,564],note='Removal plus reassembly precedes successful trial; do not claim string removal alone, absent reassembly, was sufficient.')
a.feature(550,narrative_resolution_evidence={'problem_content_id':'p34','outcome_content_id':'p33','event_ids':['ev506','ev525','ev534','ev551','ev554'],'scope_id':'s0','assertion_status':'asserted'},evidence=[471,474,476,505,524,533,550,553,562,564])
a.feature(673,narrative_motif_link={'earlier_word':48,'current_word':673,'entity_id':'e11','contrast':'rattle_to_quiet','scope_id':'s0','assertion_status':'candidate'},narrative_closure_candidate={'scope_id':'s0','assertion_status':'candidate','evidence_words':[628,652,673,678,680,681],'interpretation':'tools_returned_and_cart_operable_in_final_rain_image'},evidence=[48,628,652,673,678,680,681],note='The ending proves repaired operation and restored tool custody; it does not prove Rafi trust or invent a plant unloading.')
a.feature(433,narrative_theme_candidate={'scope_id':'s0','assertion_status':'candidate','interpretation':'admitting_a_mistake_and_inspecting_evidence_supports_effective_repair','evidence_words':[114,137,220,309,355,374,433,471,505,550]},evidence=[114,137,220,309,355,374,433,471,505,550],note='Interpretive theme, not a new permanent character trait or a quoted moral.')

# Explicit descriptors without a dedicated typed catalog dimension retain the
# documented legacy name/string-value format, bound to their actual referent.
def descriptor(w,eid,name,value):
    ent=a.entities[eid]
    if w not in ent['mentions']: ent['mentions'].append(w)
    a.feature(w,entity_id=eid,entity_name=ent['name'],entity=ent['type'],attributes=[{'name':name,'value':value}],assertion_status=attribution(a.words[w]['scope_id']))
for args in [(47,'e52','sound_scale','little'),(82,'e16','life_stage','young'),(103,'e14','relative_size','small'),(275,'e17','weight_description','heavy'),(599,'e41','sunlight_exposure','sunny'),(641,'e46','relative_size','little')]: descriptor(*args)
bound(625,'affordance_sheltering','e45',{'shelter_condition':'rain','sheltered':True},evidence=[613,614,623,625,626])
a.feature(7,lexical_sense_id='fig_tree_species_modifier')
a.feature(2,lexical_sense_id='repair_bench_purpose_modifier')
a.feature(23,lexical_sense_id='toy_cart_use_class')
for w in [83,679]: a.feature(w,lexical_sense_id='tomato_plant_species_modifier')
a.feature(439,lexical_sense_id='kite_string_use_class')
a.feature(581,lexical_sense_id='plant_tray_contents_modifier')
a.feature(28,lexical_sense_id='summer_sky_simile_source_modifier',evidence=[25,26,28,29])
a.feature(29,figurative_mapping={'target_id':'e10','source_image':'summer_sky','kind':'simile','literal_event':False,'scope_id':'s0','assertion_status':'asserted'})
for w in [342,559]: a.feature(w,lexical_sense_id='paving_stone_use_modifier')
a.feature(619,lexical_sense_id='fig_tree_leaf_species_modifier')
a.feature(95,lexical_sense_id='exact_location_intensifier')
a.feature(96,relative_marker_form='locative_relative_where')
a.feature(187,lexical_sense_id='similarity_degree_intensifier')
a.feature(215,lexical_sense_id='minimal_positive_degree',evidence=[214,215,216],note='Barely moved still asserts small movement, unlike the later jam/negated turn.')
a.feature(223,temporal_iteration_count=1)
a.feature(602,temporal_iteration_count=1)
a.feature(551,lexical_sense_id='smooth_rotation_manner')
a.feature(386,lexical_sense_id='careful_handling_manner')
a.feature(644,lexical_sense_id='lost_bits_storage_category',evidence=[642,643,644,645,647,649],note='Lost bits names the tin contents category; it does not make the located string presently missing.')
a.feature(565,lexical_sense_id='restrictive_only_sound',evidence=[561,562,563,564,565,567,568],note='Only the ordinary soft wheel bump remains, not absolute silence.')
a.feature(311,appraisal_goal_congruence='worsened_cart_problem',appraisal_responsibility={'holder_id':'e1','responsible_id':'e1','content_id':'p16','scope_id':'q11','assertion_status':'attributed_claim'})
# The source shows expressions; it does not name a permanent emotional trait.
a.feature(140,affect_experiencer_id='e3',affect_expression_channel='smiling',evidence=[138,139,140],note='Smile is explicit; its exact emotion or pedagogical motive is not imposed.')
a.feature(218,affect_experiencer_id='e1',affect_expression_channel='frown',evidence=[216,217,218],note='Frown follows failed wheel check; no unique emotion is claimed.')
a.feature(328,affect_experiencer_id='e2',affect_expression_channel='mouth_tightening',evidence=[326,327,328,329,331],note='Mouth tension and subsequent help are explicit; frustration remains an interpretation, not a categorical feeling label.')
a.words[540].pop('grammatical_object_id',None)
a.feature(540,indirect_object_id='e11',dative_alternation_form='double_object_leave_room',subject_controller_id='e1')
# Modal 'can' and auxiliary 'does' license nonfinite lexical predicates.
for w in [99,121,125,257,372,493]: a.feature(w,verb_form='finite')
# Mark referent-bound uncertain candidates without replacing narrator event truth.
a.feature(231,evidence_world_status='belief_content')
a.feature(492,evidence_world_status='reported_prior_belief_content')


# Final assembled-output review corrections.
for w,eid in [(16,'e5'),(610,'e42')]:
    ent=a.entities[eid]
    ent['mentions'].append(w)
    a.feature(w,entity_id=eid,entity_name=ent['name'],entity=ent['type'],reference_chain_id=f'rc_{eid}',reference_introduction=False)
a.feature(206,pos='intj',lexical_sense_id='result_demonstration_interjection',evidence=[204,205,206,208],note='There demonstrates the apparent result rather than locating a referent.')
a.feature(323,tense='present',clause_finiteness='finite',verb_form='finite')
a.feature(314,clause_finiteness='finite')
a.words[315].pop('mood',None)
a.feature(315,clause_finiteness='nonfinite',goal_status='proposed')
for w in [361,587]: a.feature(w,coordination_category='clause')
a.feature(445,coordination_category='NP')
a.feature(499,tense='past',clause_finiteness='finite',verb_form='finite')
a.words[65].pop('clausal_object_id',None)
a.feature(65,proposition_id='p1')
a.words[324].pop('clausal_object_id',None)
a.feature(324,lexical_sense_id='anaphoric_wheel_problem',evidence=[323,324,325],note='It is the problem/situation to figure out, not a syntactically clausal direct object.')
for w in [233,590]: a.words[w].pop('motion_carrier',None)
for eid in ['ev193','ev202']:
    a.mention_event(eid,359,role='action',note='The later tightening report collectively recalls the earlier tightening turns, including this turn.')
# Bits are parts of source objects, not identical to those whole objects.
a.entities['e47']['mentions'].remove(647)
for key in ['event_bindings','event_id','event','role','reference_chain_id','reference_introduction']:
    a.words[647].pop(key,None)
a.entity('e62','unspecified things from which stored bits came','object_group',[647],existence_status='source_objects_not_located_by_story')
a.feature(647,reference_chain_id='rc_e62',reference_introduction=True)
a.feature(646,prepositional_object_id='e62')
part(645,'e47','e62')
a.feature(645,evidence=[642,643,645,646,647,649],note='Only the bits are stored in the tin; their whole source objects are not asserted present.')
# These are left unspecified rather than silently making two side mentions identical.
a.feature(668,identity_hypothesis={'source_mention':a.anchor(668),'antecedent_entity_id':'e29','scope_id':'s0','assertion_status':'candidate','relationship':'may_be_same_cart_side'},evidence=[389,668],note='The cart has multiple sides. The final blue side may be the inspection side, but exact side identity is not stated.')
for ent in a.entities.values(): ent['mentions'].sort()

FEEDBACK={
 'summary':'Complete manual retrospective v3 annotation of the repair story, preserving diagnosis versus observation, scoped alternatives, tool custody, cooperative repair and the final image.',
 'ambiguities':[
  {'words':[374,376,377,378],'issue':'Rafi asks what to check before turning it again; it can refer to the nut or the wheel.','decision':'Leave the object unresolved, retain e13/e11 alternatives, and do not fabricate an actual turn.'},
  {'words':[253,255,365,366,402,404,424],'issue':'The wheel is jammed and reported unable to turn, but Ada next spins it for the clicking test before the source narrates loosening the nut.','decision':'Preserve both narrated states/actions; do not invent an intermediate loosening or force. The movement limit might permit a forced test, but that is not stated.'},
  {'words':[315,317,318,320,333,335,336,553,555,556],'issue':'Under-bench placement is proposed; the actual next action only lowers the tray, and the later trial cart is empty.','decision':'Record proposed under-bench location, actual lowering out of cart, and empty trial; leave the tray interim location unspecified.'},
  {'words':[483,484,485,487,489,491,492],'issue':'Niko reports that the string is from his kite and that he had thought its tail came loose.','decision':'Keep origin as attributed report and the tail detachment as a nested prior belief; do not invent entry of string into wheel or equate string with the entire kite tail.'},
  {'words':[623,626,652,654,675,677,678,680],'issue':'The cart reaches the sheltered corner and then returns to the bench; final leaves remain inside. No unloading at the corner is narrated.','decision':'Preserve explicit states, no unload/reload invention. Six final leaves do not establish one leaf per plant or a total plant leaf count.'},
  {'words':[428,431,524,526,528],'issue':'Wheel removal is explicit; washer is later refitted but no separate washer-removal action is narrated.','decision':'Keep removal of wheel and later refitting of washer+wheel; omit a fabricated washer-removal event.'},
  {'words':[206,207,208],'issue':'The addressee of Ada brief There is not explicitly named.','decision':'Rafi is the contextual audience at the bench, retained as an inference; no plot outcome depends on it.'},
  {'words':[114,355,465],'issue':'Initial claim says wheel loose; correction denies nut looseness.','decision':'Treat this as a narrowed mechanical diagnosis, not a literal contradiction between identical predicates; do not infer the wheel can never have been crooked.'}
 ],
 'feature_gaps':[
  {'words':[82,103,275,599,641],'meaning':'Qualitative life stage, relative size/weight and sunlight exposure lack dedicated typed carrier fields in this inventory.','decision':'Use existing entity-bound legacy attributes name/string-value pairs. Future reusable typed fields could cover these dimensions; no new extension is introduced in this story.'}
 ],
 'prompt_feedback':[
  'The v3 positive predicate/negative content rule cleanly distinguishes nut-was-loose p20 from the quoted nut-was-not-loose p21 and avoids double negation.',
  'Keep current source-gap guidance: a repaired final state must not license invented missing mechanical or transport transitions.',
  'Add a mechanical-jam example if revising: wheel locked is operability failure, not object_lock_state, which describes engagement of a lock.',
  'Add a controlled-test example if useful: wheel held still is a test condition, distinct from a wheel unable to move on its own.',
  'Preserve quoted actual events through mention_event; the repeated tightening report and repeated rattle explanation reuse earlier event identities.',
  'No new attribute names were required; agreed appearance_color, part_whole_relation and figurative_mapping were reused alongside event_bindings.'
 ],
 'coverage_notes':'All 27 paragraphs and 685 words manually tagged. Actions, states, utterances, conditional risks, goals, beliefs, references, counts, parts, tool custody, location changes and physical mechanisms are annotated sparsely. Whitespace/punctuation are synthetic. Narrator-supported repair does not become proof of achieved trust or a deadline met before rain.',
 'reviewed_all_words':True,
 'self_review':{'paragraphs':27,'mode':'Read every assembled word and all event/entity/scope/proposition registries against the complete source; repair material semantic discrepancies separately from shape validation.'}
}
a.save(FEEDBACK)
# A review view contains every word's full semantic payload, in paragraph order.
structural={'index','start','end','kind','position','word_index','token'}
lines=[]
for i,para in enumerate(a.paragraphs):
    lines.append(f'P{i}: '+ ' '.join(a.words[x['w']]['token'] for x in para['words']))
    for x in para['words']:
        row=a.words[x['w']]
        fields={k:v for k,v in row.items() if k not in structural}
        lines.append(f"w{x['w']} {row['token']} "+json.dumps(fields,ensure_ascii=False,separators=(',',':')))
    lines.append('')
(a.output/'review_words.txt').write_text('\n'.join(lines)+'\n')
