"""Manual contextual annotation, museum story, frozen v3."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a=Annotation('16_museum',prompt_version='v3')
for key in ['appearance_color','part_whole_relation','figurative_mapping','enactment']:a.use_extension(key)
LEX={
0:'adp=at num=three adv=o’clock det=the adj=local n=museum n=activity n=room v=smell adp=of n=paste adj=old n=book conj=and det=the n=orange n=peel adp=in n=Kit n=pocket n=Miri v=have v=arrange num=six n=chair adp=in det=a adj=neat n=row adp=for det=the n=shadow n=exhibit pron=she v=want n=Mr n=Bell part=to v=choose pron=she adp=as det=a adj=junior n=guide adp=for n=Saturday n=Kit v=want det=his adj=little n=sister n=Dot part=to v=stop v=call n=museum n=room adv=where pron=you v=can v=touch pron=anything',
1:'adv=today n=Miri v=say v=hold adv=up det=the n=label pron=we v=prove conj=that v=move det=the n=moth adp=toward det=the n=screen v=make det=its n=shadow adj=small',
2:'conj=and adv=then n=Kit v=say v=lift det=his n=cardboard n=dragon pron=we v=make pron=one adj=big adv=enough part=to v=eat det=the n=moon',
3:'det=the n=dragon v=be part=not adp=on det=the n=label',
4:'pron=it det=an adj=improved n=moth',
5:'pron=they v=borrow det=a n=torch adp=from n=Mr n=Bell adp=at det=the n=front n=desk pron=he v=hand pron=it adp=to n=Miri pron=who v=promise part=to v=bring pron=it adv=back adp=before n=closing adp=in det=the n=activity n=room pron=they v=stretch det=a adj=white n=sheet adp=between num=two n=chair conj=and v=set det=the n=moth adp=on det=the adj=wooden n=track adp=in n=front adp=of pron=it det=the n=label v=show det=a n=torch adp=at num=one n=end det=a n=screen adp=at det=the adj=other conj=and det=a adj=little n=arrow v=point det=the n=moth adp=toward det=the n=screen',
6:'n=Miri v=hold det=the n=torch n=Kit v=slide det=the n=moth adp=along det=the n=track',
7:'det=the n=shadow v=spread adv=wide adp=across det=the n=sheet',
8:'n=Miri v=stop pron=he pron=that det=the n=opposite',
9:'adv=maybe det=the n=label adj=wrong v=say n=Kit pron=he v=sound adj=pleased det=a adj=wrong n=label v=may v=be adv=more adj=exciting conj=than det=a adj=correct pron=one',
10:'pron=they v=try adv=again n=Miri v=lean adv=forward part=to v=keep det=the n=beam adp=on det=the n=moth conj=as n=Kit v=move pron=it det=this n=time det=the n=shadow v=grow conj=until det=its n=wing adv=nearly v=touch det=both n=chair',
11:'v=see n=Kit v=say n=dragon adj=sized',
12:'pron=that v=do v=prove pron=anything n=Miri v=say conj=though pron=she v=be v=look adp=at det=the n=label conj=as conj=if pron=it v=have v=insult pron=she',
13:'n=Kit v=move det=the n=moth adv=back n=Miri v=move det=the n=torch adv=too v=keep det=the adj=bright n=circle adj=centered det=the n=shadow v=jump conj=and v=wobble',
14:'v=hold adj=still n=Miri v=tell pron=herself pron=she v=plant det=her n=foot det=her n=arm v=begin part=to v=ache conj=when n=Kit v=slide det=the n=moth adv=forward det=the n=beam v=slip adp=off det=its n=paper n=wing',
15:'adp=from det=the n=corridor v=come det=the n=rumble adp=of v=arrive n=voice n=Dot n=laugh v=float adp=above pron=they',
16:'n=Miri v=glance adp=at det=the n=chair pron=they adj=early',
17:'n=Kit v=peek adp=through det=the n=doorway n=Dot adp=with pron=they pron=I v=tell pron=she pron=there v=be det=a n=dragon',
18:'n=Miri n=stomach v=tighten n=Mr n=Bell v=may v=be adp=among det=the n=visitor conj=if pron=she v=start adp=with det=a n=shadow pron=that v=contradict det=the n=label pron=he v=may adv=never v=ask pron=she part=to v=guide pron=anyone',
19:'n=Kit v=point adp=at det=the adj=small n=print adp=beneath det=the n=diagram adv=there v=keep det=the n=torch adp=on det=the n=star',
20:'det=a adj=yellow n=star v=be v=print adp=at det=the adj=left n=end adp=of det=the n=track n=Miri v=have v=be adv=so adj=busy v=make det=the n=beam v=follow det=the n=moth conj=that pron=she v=have adv=never v=notice pron=it',
21:'pron=we v=can v=say det=the n=torch v=be adj=faulty n=Kit v=whisper adv=then adv=just v=do det=the n=dragon',
22:'n=Miri v=look adp=at det=the n=visitor v=gather adv=outside pron=she v=can v=start det=her n=speech adv=now conj=and v=hope pron=nobody v=ask adv=instead pron=she v=put det=the n=torch adv=down adp=on num=two n=book v=wedge det=its n=handle adp=with det=a n=lump adp=of n=modeling n=clay conj=and v=turn det=the n=beam adp=toward det=the n=sheet',
23:'v=wait pron=she v=call det=our adj=first n=try v=do v=match det=the n=label pron=we v=move det=the n=torch adv=too v=can pron=you v=give pron=we num=one n=minute',
24:'det=a n=boy adp=in det=a adj=red n=scarf v=step adp=into det=the n=room n=Dot v=peer adp=around det=his n=elbow',
25:'n=Miri v=slide det=the n=moth adv=back adp=to det=the n=start n=Kit v=watch det=the n=torch adj=ready part=to v=catch pron=it conj=if pron=it v=shift n=Miri v=push det=the n=moth adp=toward det=the n=screen det=its n=shadow v=shrink adp=from det=the n=size adp=of det=a n=dinner n=plate adp=to det=the n=size adp=of det=a n=saucer',
26:'intj=oh v=say n=Dot',
27:'det=the n=torch v=stay adj=put n=Miri v=say conj=when det=the n=moth v=be adj=near det=the n=torch det=its n=shadow v=spread adv=out adp=near det=the n=screen pron=there det=less n=room adp=for pron=it part=to v=spread conj=before pron=it v=land',
28:'n=Kit v=lift det=his n=dragon conj=and pron=this v=be pron=what v=happen conj=when pron=you v=put pron=something adj=close adp=to det=the n=torch',
29:'pron=he v=hold det=the n=dragon adp=near det=the n=beam det=its adj=jagged n=shadow v=fill det=the n=sheet n=tail v=curl adp=over num=one n=chair conj=and n=wing v=climb adv=almost adp=to det=the n=top',
30:'n=Dot v=squeal pron=it v=eat det=the n=moon',
31:'pron=it det=an adj=improved n=moth n=Kit v=say v=grin',
32:'n=Miri v=hand det=the n=dragon adp=to n=Dot pron=you v=can v=try adv=just v=leave det=the n=torch adp=on det=the n=star',
33:'n=Dot v=hold det=the n=cutout adp=near det=the n=screen det=its n=shadow v=become det=a adj=small adj=tidy n=shape adv=then pron=she v=raise num=two n=finger adp=beside pron=it conj=and det=their n=shadow v=flutter adv=together adp=on det=the adj=white n=sheet num=one n=paper n=moth num=one adj=little n=pair adp=of adj=living n=wing',
}
for p,s in LEX.items():
 pairs=[x.split('=',1) for x in s.split()];words=a.paragraphs[p]['words']
 assert len(words)==len(pairs),(p,len(words),len(pairs))
 a.tag(p,[x[0] for x in pairs],{w['w']:x[1] for w,x in zip(words,pairs)})
F=a.feature
def B(e,value,scope='s0',status='asserted',**more):return dict(entity_id=e,value=value,scope_id=scope,assertion_status=status,**more)
ENTS=[
('e1','Miri','person',[20,33,39,63,125,126,181,199,228,263,266,277,283,300,302,303,305,307,339,361,372,385,417,429,448,455,458,466,491,526,545,575,656]),
('e2','Kit','person',[18,46,48,84,87,185,201,210,211,239,255,278,313,346,354,389,441,534,601,603,618,653]),
('e3','Dot','person',[50,51,334,351,356,521,570,643,661,662,672,687]),
('e4','Mr. Bell','person',[35,36,115,116,121,364,365,381]),
('e5','Miri and Kit','person_group',[69,90,110,138,225,434,493,500,508]),
('e6','arriving visitors','person_group',[344,353,370,452,506]),
('e7','boy in red scarf','person',[512,524]),
('e8','local museum','museum',[5]),
('e9','museum activity room','room',[7,137,520]),
('e10','paste in room','paste',[10]),
('e11','old books in room','book_group',[12]),
('e12','orange peels','peel_group',[16]),
('e13','Kit pocket','pocket',[19]),
('e14','six arranged chairs','chair_group',[24,343]),
('e15','shadow exhibit label','label',[68,105,159,207,271,274,380,499]),
('e16','paper moth cutout','paper_cutout',[74,79,149,188,237,241,281,316,322,427,529,548,552,579,584]),
('e17','Kit cardboard dragon cutout','cardboard_cutout',[89,100,106,109,360,447,604,621,625,649,652,659,675,679,692]),
('e18','moth projected shadow','shadow',[80,193,245,248,294,553,585,595,599]),
('e19','dragon projected shadow','shadow',[627,680,685]),
('e20','white sheet serving as screen','sheet_screen',[77,142,157,198,489,551,590,630,678,701]),
('e21','wooden moth track','track',[153,191,416]),
('e22','borrowed torch','torch',[113,123,130,184,286,401,438,469,475,503,537,541,543,572,583,617,668]),
('e23','torch beam','light_beam',[234,319,424,486,624]),
('e24','bright circle of torch light','light_patch',[291]),
('e25','two screen-supporting chairs','chair_pair',[145,253]),
('e26','moth shadow wings','shadow_part_group',[249]),
('e27','Miri feet','body_part_group',[306]),
('e28','Miri arms','body_part_group',[308]),
('e29','corridor outside activity room','corridor',[327]),
('e30','arriving visitors voices','sound_group',[333,338]),
('e31','Dot laugh','sound',[335]),
('e32','activity room doorway','doorway',[350]),
('e33','Miri stomach','body_part',[362]),
('e34','instruction small print','written_text',[394]),
('e35','diagram on label','diagram',[397]),
('e36','yellow star printed on track','printed_mark',[404,407,433,671]),
('e37','left end of track','track_region',[413]),
('e38','two torch-support books','book_pair',[473]),
('e39','torch handle','handle',[476]),
('e40','lump of modeling clay','clay_lump',[479,482]),
('e41','boy red scarf','scarf',[516]),
('e42','boy elbow','body_part',[525]),
('e43','start of track','track_region',[533]),
('e44','dinner plate size comparator','comparison_object',[561]),
('e45','saucer size comparator','comparison_object',[567]),
('e46','dragon shadow tail','shadow_part',[631]),
('e47','dragon shadow wings','shadow_part_group',[637]),
('e48','one chair crossed by shadow','chair',[635]),
('e49','top of screen','screen_region',[642]),
('e50','Dot raised two fingers','body_part_pair',[690,707,710]),
('e51','fingers projected shadow','shadow',[]),
('e52','cutout and finger shadows','shadow_group',[695]),
('e53','pretend moon-eating dragon','fictional_character',[92,645]),
('e54','moon in playful dragon scenario','fictional_object',[98,648]),
('e55','closing paper moth description','unresolved_cutout_reference',[704]),
('e56','torch drawn in diagram','depicted_torch',[162]),
('e57','screen drawn in diagram','depicted_screen',[167,180]),
('e58','direction arrow in diagram','depicted_arrow',[174]),
('e59','moth drawn in diagram','depicted_moth',[177]),
('e60','torch end shown in diagram','depicted_track_region',[165]),
('e61','other end shown in diagram','depicted_track_region',[170]),
('e62','considered early speech','planned_speech',[459]),
('e63','hypothetical wrong label','label_kind',[216]),
('e64','hypothetical correct label','label_kind',[224]),
('e65','moth paper wings','cutout_part_group',[324]),
('e66','front desk','desk',[120]),
('e67','cutout and Dot fingers forming shadows','mixed_group',[694]),
]
# The second ending shadow is only part of plural shadows, so register its
# entity at the final metonymic wings rather than duplicate the group mention.
for i,x in enumerate(ENTS):
 if x[0]=='e50':ENTS[i]=(*x[:3],[690])
 if x[0]=='e51':ENTS[i]=(*x[:3],[707,710])
for args in ENTS:a.entity(*args)
a.entities['e5']['member_ids']=['e1','e2']
a.entities['e6']['known_member_ids']=['e3','e7']
a.entities['e25']['subset_of']='e14';a.entities['e48']['member_of']='e14'
a.entities['e52']['member_ids']=['e19','e51']
a.entities['e67']['member_ids']=['e17','e50']
a.entities['e55']['candidate_ids']=['e17','e16'];a.entities['e55']['not_an_additional_physical_object']=True
a.entities['e38']['identity_note']='May be drawn from old room books e11; no explicit identity is forced.'
a.entities['e43']['identity_note']='Track start; no forced identity with printed-star end e37.'
QUOTES=[
('q1',62,63,'e1','Proposed demonstration opening',['e2']),('q2',69,82,'e1','Claim to prove',['e2']),
('q3',82,84,'e2','Playful addition',['e1']),('q4',90,99,'e2','Proposed giant dragon shadow',['e1']),
('q5',99,106,'e1','Dragon absent from label',['e2']),('q6',106,110,'e2','Improved moth joke',['e1']),
('q7',202,205,'e1','Opposite trial result',['e2']),('q8',205,209,'e2','Possible wrong label',['e1']),
('q9',254,255,'e2','Look at result',['e1']),('q10',257,259,'e2','Dragon-sized comparison',['e1']),
('q11',259,263,'e1','Reject proof',['e2']),('q12',298,300,'e1','Self instruction',['e1']),
('q13',344,346,'e1','Visitors early',['e2']),('q14',351,361,'e2','Dot present and prior dragon statement',['e1']),
('q15',398,405,'e2','Read label instruction',['e1']),('q16',434,441,'e2','Proposed false excuse',['e1']),
('q17',443,448,'e2','Proposed dragon only demonstration',['e1']),
('q18',490,491,'e1','Wait request',['e6']),('q19',493,511,'e1','Disclose failed trial and ask minute',['e6']),
('q20',568,569,'e3','Reaction to shrinking shadow',['e5']),
('q21',571,575,'e1','Torch stationary',['e6']),('q22',577,601,'e1','Size-distance explanation',['e6']),
('q23',605,618,'e2','Introduce near-torch demonstration',['e6']),
('q24',645,649,'e3','Pretend moon eating',['e5']),('q25',649,653,'e2','Repeat improved moth joke',['e6']),
('q26',662,672,'e1','Dot permission and torch condition',['e3']),
]
for sid,lo,hi,h,desc,audience in QUOTES:
 a.scope(sid,range(lo,hi),kind='quotation',holder_id=h,description=desc)
 a.scopes[sid]['addressee_ids']=audience
 F(range(lo,hi),quote_mode='direct',assertion_status='attributed_claim')
for sid,lo,hi,kind,holder,parent,desc in [
('s1',35,46,'desired_appointment','e1','s0','Bell selecting Miri is desired, not awarded.'),
('s2',48,62,'desired_reappraisal','e2','s0','Kit wants Dot to cease her museum description.'),
('s3',56,62,'remembered_quotation','e3','s2','Dot museum complaint, generic and attributed.'),
('s4',95,99,'playful_imagined_outcome','e2','q4','Eating moon belongs to pretend giant dragon scenario.'),
('s5',128,134,'promised_return','e1','s0','Torch return before closing is promised, not observed.'),
('s6',161,181,'diagram_content',None,'s0','Represented layout on physical label, distinct from actual apparatus.'),
('s7',214,225,'possible_evaluation','e2','s0','Hypothetical wrong-label excitement, compatible with Kit focalization.'),
('s8',231,238,'purpose','e1','s0','Keep moving beam on moth is purpose of leaning.'),
('s9',272,278,'figurative_comparison',None,'s0','Label insulting Miri is an as-if comparison, not an actual act.'),
('s10',357,361,'reported_prediction_content','e2','q14','Earlier predicted dragon presence, not a live dragon.'),
('s11',364,371,'possible_attendance','e1','s0','Bell may be among visitors; not confirmed.'),
('s12',371,381,'conditional_bad_opening','e1','s0','Unchosen demonstration opening with contradictory shadow.'),
('s13',381,389,'conditional_feared_consequence','e1','s12','Possible nonappointment, not a completed Bell decision.'),
('s14',399,405,'quoted_written_instruction','e2','q15','Kit reads label wording; original author is unknown.'),
('s15',436,441,'proposed_excuse','e2','q16','Saying torch faulty considered; no actual fault or false excuse uttered.'),
('s16',437,441,'excuse_content','e2','s15','Faultiness exists only as content of the proposed excuse.'),
('s17',455,465,'unchosen_early_speech','e1','s0','Start now and hope nobody asks, not the eventual honest speech.'),
('s18',463,465,'desired_absence_of_question','e1','s17','Nobody asks is a hoped-for state within unchosen alternative.'),
('s19',539,545,'conditional_catch','e2','s0','Prepared to catch torch only if it shifts; no shift/catch occurs.'),
('s20',645,649,'pretend_shadow_scene','e3','q24','Dot playfully interprets dragon shadow as eating moon.'),
('s21',611,618,'generic_demonstration_rule','e2','q23','Generic placement condition, not unnamed person doing another actual placement.'),
]:a.scope(sid,range(lo,hi),kind=kind,parent=parent,holder_id=holder,description=desc)
F(range(56,62),quotation_scope_id='s3',speaker_id='e3',quote_mode='remembered_direct',assertion_status='attributed_claim')
F(range(399,405),quote_mode='read_aloud',assertion_status='attributed_claim')
F(range(161,181),semantic_world_id='world_diagram')
F(range(645,649),semantic_world_id='world_playful_dragon')
F(range(95,99),semantic_world_id='world_playful_dragon')
PROPS=[
(1,'Mr. Bell chooses Miri as a junior guide for Saturday.',[35,36,38,39,42,43,45],'s1'),
(2,'Dot stops calling museums rooms where people cannot touch anything.',[50,51,53,54,55,56,59,60,61],'s2'),
(3,'People can touch things in museums.',[55,56,58,59,60,61],'s3'),
(4,'Moving the moth toward the screen with the torch fixed makes its shadow smaller.',[70,72,74,77,78,80,81,399,401,404],'q2'),
(5,'Miri and Kit will prove the moth-shadow shrinking relation today.',[62,69,70,72,78,81],'q2'),
(6,'Miri and Kit will make a giant dragon shadow in pretend moon-eating play.',[90,91,92,93,96,98],'q4'),
(7,'The dragon is represented on the label.',[100,101,103,105],'q5'),
(8,'The dragon is not represented on the label.',[100,101,102,103,105],'q5'),
(9,'The dragon is an improved moth.',[106,108,109],'q6'),
(10,'Miri returns the torch to Bell before closing.',[127,129,130,132,133],'s5'),
(11,'The initial shadow spreads wider instead of smaller.',[193,194,195,202,204],'q7'),
(12,'The label is wrong.',[205,207,208],'q8'),
(13,'A wrong label might be more exciting than a correct label.',[215,216,217,220,223,224],'s7'),
(14,'The second result is dragon-sized.',[245,246,249,251,253,257,258],'q10'),
(15,'The second result proves a conclusion about the label.',[259,260,261,262],'q11'),
(16,'The second result does not prove a conclusion about the label.',[259,260,261,262],'q11'),
(17,'Miri holds still.',[298,299],'q12'),
(18,'The visitors are early.',[344,345],'q13'),
(19,'Dot is with the arriving visitors, and Kit previously told her there would be a dragon.',[351,352,353,354,355,356,357,358,360],'q14'),
(20,'There will be a dragon cutout at the demonstration.',[357,358,360],'s10'),
(21,'Mr. Bell is among the visitors.',[364,365,366,367,370],'s11'),
(22,'Miri starts with a shadow result that contradicts the label.',[371,372,373,376,378,380],'s12'),
(23,'Mr. Bell asks Miri to guide someone.',[381,382,384,385,387,388],'s13'),
(24,'Mr. Bell might never ask Miri to guide if she opens with a contradictory result.',[371,373,378,381,382,383,384,387],'s13'),
(25,'Keep the torch on the printed star.',[399,401,402,404],'s14'),
(26,'Miri notices the printed star.',[429,431,432,433],'s0'),
(27,'The printed star is at the left end of the track.',[407,409,412,413,416],'s0'),
(28,'The torch is faulty.',[438,439,440],'s16'),
(29,'Miri and Kit could say that the torch is faulty.',[434,435,436,438,439,440],'q16'),
(30,'Miri and Kit just perform the dragon demonstration.',[443,445,447],'q17'),
(31,'Miri starts her speech now.',[455,456,457,459,460],'s17'),
(32,'Any visitor asks a question about the trial.',[463,464],'s18'),
(33,'No visitor asks a question about the trial.',[462,463,464],'s18'),
(34,'The first try matches the label.',[493,494,495,496,497,499],'q19'),
(35,'The first try did not match the label; Miri and Kit also moved the torch.',[493,495,496,497,499,500,501,503,504],'q19'),
(36,'Visitors give Miri and Kit one minute.',[505,506,507,508,509,510],'q19'),
(37,'The torch shifts during the controlled trial.',[542,543,544],'s19'),
(38,'Kit catches the torch if it shifts.',[538,540,541,542,544],'s19'),
(39,'The torch stays put during the successful trial.',[571,572,573,574],'q21'),
(40,'With fixed torch, nearer moth gives larger shadow; nearer screen allows less spreading before projection.',[577,579,581,583,585,586,588,590,592,593,597,600],'q22'),
(41,'Putting a cutout close to the torch produces the demonstrated larger shadow.',[605,606,607,609,610,612,614,617],'q23'),
(42,'The pretend dragon eats the moon.',[645,646,648],'s20'),
(43,'Dot may try the shadow demonstration while leaving the torch on the star.',[662,663,664,666,668,671],'q26'),
(44,'Dot tries the shadow demonstration.',[662,663,664],'q26'),
(45,'Visitors wait for the presenters.',[490],'q18'),
]
for n,text,support,scope in PROPS:a.proposition(f'p{n}',text,support,scope_id=scope)
EV={}
def attributed(scope):
 while scope:
  s=a.scopes[scope]
  if s['kind'] in ['quotation','remembered_quotation','quoted_written_instruction','reported_prediction_content','excuse_content']:return True
  scope=s['parent']
 return False
def E(key,w,label,**kw):
 eid=f'ev{len(EV)+1}';EV[key]=eid;a.event(eid,w,label,**kw)
 if kw.get('primary',True):F(w,assertion_status='attributed_claim' if attributed(a.words[w]['scope_id']) else 'asserted')
 return eid
def M(key,ws,role='reference',note=''):
 a.mention_event(EV[key],ws,role=role,note=note)
 if role=='action':
  for w in [ws] if isinstance(ws,int) else ws:F(w,assertion_status='attributed_claim' if attributed(a.words[w]['scope_id']) else 'asserted')
def U(key,w,speaker,content,audience,kind='assertion',**kw):
 ids=[audience] if isinstance(audience,str) else audience
 eid=E(key,w,'communicate '+content,type='speak',actor=speaker,recipient=ids[0] if len(ids)==1 else None,**kw)
 F(w,speaker_id=speaker,speech_act_kind=kind,utterance_id=eid,utterance_content_id=content,addressee_ids=ids,communication_channel='speech',communication_scope_bundle={'speaker_id':speaker,'utterance_event_id':eid,'scope_id':kw.get('scope','s0'),'assertion_status':'asserted'})
 return eid
E('smell',8,'room smells of paste books and orange peels',type='state',patients=['e9'],roles={'patient':[7],'odor_source':[10,12,16]})
E('arrange',22,'Miri arranges six chairs in a row',actor='e1',patients=['e14'],roles={'actor':[20],'patient':[24]})
E('want_guide',34,'Miri wants Bell to choose her as junior guide',type='feel',actor='e1',roles={'experiencer':[33]})
E('choose_guide',38,'Bell chooses Miri as junior guide',actor='e4',patients=['e1'],factuality='desired',roles={'actor':[35,36],'patient':[39]})
E('want_reappraisal',47,'Kit wants Dot to stop her museum complaint',type='feel',actor='e2',roles={'experiencer':[46]})
E('stop_complaint',53,'Dot stops calling museums untouchable rooms',actor='e3',factuality='desired',roles={'actor':[50,51]})
E('museum_complaint',54,'Dot describes museums as rooms with no touching',type='speak',actor='e3',factuality='reported',roles={'actor':[50,51]})
E('touch_permission',60,'museum visitors touch objects',factuality='hypothetical')
U('announce_proof',64,'e1','p5','e2','announce_intention',roles={'actor':[63]})
E('hold_label',65,'Miri holds label up',type='move',actor='e1',patients=['e15'],roles={'patient':[68]})
E('prove_plan',70,'Miri and Kit prove shrinking relation',actor='e5',factuality='desired',roles={'actor':[69]})
E('move_rule',72,'moth moves toward screen in demonstration rule',type='move',patients=['e16'],factuality='hypothetical',roles={'patient':[74],'target':[77]})
E('shrink_rule',78,'moth approach makes shadow smaller under rule',type='state',patients=['e18'],factuality='reported',roles={'patient':[80]})
U('play_plan',85,'e2','p6','e1','playful_proposal',roles={'actor':[84]})
E('lift_dragon1',86,'Kit lifts cardboard dragon',type='move',actor='e2',patients=['e17'],roles={'patient':[89]})
E('giant_plan',91,'Miri and Kit make giant dragon shadow',actor='e5',patients=['e19'],factuality='desired',roles={'actor':[90]})
E('eat_plan',96,'pretend dragon eats moon',actor='e53',patients=['e54'],factuality='hypothetical',roles={'actor':[92],'patient':[98]})
E('dragon_on_label',101,'dragon appears on label',type='state',patients=['e17'],factuality='negated',roles={'patient':[100],'representation_carrier':[105]})
U('label_objection',101,'e1','p8','e2','objection',primary=False,scope='s0')
E('moth_joke1',108,'dragon is called an improved moth',type='state',patients=['e17'],factuality='reported',roles={'patient':[106,109]})
U('moth_joke_speech1',108,'e2','p9','e1','playful_relabeling',primary=False,scope='s0')
E('loan',111,'Bell lends torch to Miri for Miri and Kit',type='transfer',actor='e4',patients=['e22'],recipient='e1',roles={'borrower_group':[110],'patient':[113],'actor':[115,116],'location':[120]},support=[110,111,113,115,116,121,122,123,125])
M('loan',122,'action','Handed describes the same loan from giver perspective, not a second loan.')
M('loan',121,'giver');M('loan',123,'patient');M('loan',125,'recipient')
U('promise_return',127,'e1','p10','e4','promise',roles={'actor':[126]})
E('return_planned',129,'Miri brings torch back to Bell before closing',type='transfer',actor='e1',patients=['e22'],recipient='e4',factuality='desired',roles={'patient':[130]})
E('stretch_sheet',139,'Miri and Kit stretch sheet between two chairs',actor='e5',patients=['e20'],roles={'actor':[138],'patient':[142],'supports':[145]})
E('set_moth',147,'Miri and Kit set moth on track',type='move',actor='e5',patients=['e16'],roles={'patient':[149],'destination':[153]})
E('label_layout',160,'label depicts torch screen and direction arrow',type='state',patients=['e15'],roles={'patient':[159],'depicted_content':[162,167,174]})
E('arrow_direction',175,'diagram arrow points moth toward screen',type='state',patients=['e59'],roles={'indicator':[174],'patient':[177],'target':[180]})
E('hold_torch1',182,'Miri holds torch during first trial',type='state',actor='e1',patients=['e22'],roles={'actor':[181],'patient':[184]})
E('slide1',186,'Kit slides moth along track first trial',type='move',actor='e2',patients=['e16'],roles={'actor':[185],'patient':[188],'route':[191]})
E('grow1',194,'first trial shadow spreads wider',type='state',patients=['e18'],roles={'patient':[193],'projection_surface':[198]})
E('stop_kit',200,'Miri stops Kit',actor='e1',patients=['e2'],roles={'actor':[199],'patient':[201]})
E('opposite_content',204,'first result is opposite of predicted shrinking',type='state',factuality='reported')
U('opposite',204,'e1','p11','e2','contrast_result',primary=False,scope='s0')
E('label_wrong',208,'label is wrong',type='state',patients=['e15'],factuality='hypothetical',roles={'patient':[207]})
U('wrong_speech',209,'e2','p49','e1','tentative_hypothesis',roles={'actor':[210]})
E('pleased',212,'Kit sounds pleased',type='feel',actor='e2',roles={'experiencer':[211]})
E('exciting',218,'wrong label is more exciting than correct label',type='state',patients=['e63'],factuality='hypothetical',roles={'patient':[216],'comparison':[224]})
E('trial2',226,'Miri and Kit try shadow experiment again',actor='e5',roles={'actor':[225]})
E('lean',229,'Miri leans forward during second trial',type='move',actor='e1',roles={'actor':[228]})
E('beam_on',232,'Miri keeps beam on moth',type='state',actor='e1',patients=['e23'],factuality='desired',roles={'patient':[234],'target':[237]})
E('slide2',240,'Kit moves moth during second trial',type='move',actor='e2',patients=['e16'],roles={'actor':[239],'patient':[241]})
E('grow2',246,'second trial shadow grows',type='state',patients=['e18'],roles={'patient':[245]})
E('nearly_touch',251,'shadow wings touch both chairs',patients=['e26'],factuality='hypothetical',roles={'patient':[249],'target':[253]})
U('dragon_sized',256,'e2','p14','e1','point_out_result',roles={'actor':[255]})
E('prove_rejected',261,'second trial result proves a conclusion',factuality='negated')
U('reject_proof',264,'e1','p16','e2','reject_inference',roles={'actor':[263]})
E('look_label',268,'Miri looks at label',type='perceive',actor='e1',patients=['e15'],roles={'actor':[266],'patient':[271]})
E('insult_comparison',276,'label insults Miri in comparison',actor='e15',patients=['e1'],factuality='hypothetical',roles={'actor':[274],'patient':[277]})
E('moth_back',279,'Kit moves moth back',type='move',actor='e2',patients=['e16'],roles={'actor':[278],'patient':[281]})
E('torch_move3',284,'Miri moves torch with moth',type='move',actor='e1',patients=['e22'],roles={'actor':[283],'patient':[286]})
E('center_circle',288,'Miri keeps beam circle centered',type='state',actor='e1',patients=['e24'],roles={'patient':[291]})
E('jump_shadow',295,'shadow jumps',type='move',patients=['e18'],roles={'patient':[294]})
E('wobble_shadow',297,'shadow wobbles',type='move',patients=['e18'])
E('hold_still',298,'Miri holds still',type='state',actor='e1',factuality='desired')
U('self_instruction',301,'e1','p17','e1','self_instruction',roles={'actor':[300],'addressee':[302]})
E('plant_feet',304,'Miri plants her feet',actor='e1',patients=['e27'],roles={'actor':[303],'patient':[306]})
E('ache',311,'Miri arms begin aching',type='state',patients=['e28'],roles={'patient':[308]})
M('ache',309,'onset_operator')
E('slide3',314,'Kit slides moth forward after Miri plants feet',type='move',actor='e2',patients=['e16'],roles={'actor':[313],'patient':[316]})
E('beam_slip',320,'beam slips off paper moth wings',type='move',patients=['e23'],roles={'patient':[319],'source_surface':[324]})
E('voices_arrive',328,'sound of arriving voices comes from corridor',type='state',patients=['e30'],roles={'patient':[333],'source':[327]})
E('laugh_above',336,'Dot laugh is audible above other voices',type='state',patients=['e31'],roles={'patient':[335],'background':[338]})
E('look_chairs',340,'Miri glances at arranged chairs',type='perceive',actor='e1',patients=['e14'],roles={'actor':[339],'patient':[343]})
E('early',345,'visitors are early',type='state',patients=['e6'],factuality='reported',roles={'patient':[344]})
U('early_speech',345,'e1','p18','e2','concern',primary=False,scope='s0')
E('peek',347,'Kit peeks through doorway',type='perceive',actor='e2',roles={'actor':[346],'view_path':[350]})
E('dot_with',352,'Dot is with visitors',type='state',patients=['e3'],factuality='reported',roles={'patient':[351],'group':[353]})
U('dot_report',352,'e2','p19','e1','report',primary=False,scope='s0')
U('earlier_dragon_telling',355,'e2','p20','e3','earlier_prediction',factuality='reported',roles={'actor':[354],'addressee':[356]})
E('dragon_present_expected',358,'dragon cutout is present at demonstration',type='state',patients=['e17'],factuality='hypothetical',roles={'patient':[360]})
E('stomach_tight',363,'Miri stomach tightens',type='state',patients=['e33'],roles={'patient':[362]})
E('bell_possible',367,'Bell is among visitors',type='state',patients=['e4'],factuality='hypothetical',roles={'patient':[364,365],'group':[370]})
E('bad_opening',373,'Miri opens with contradictory shadow result',actor='e1',factuality='hypothetical',roles={'actor':[372]})
E('contradiction',378,'opening shadow contradicts label',type='state',factuality='hypothetical',roles={'representation_carrier':[380]})
E('ask_guide',384,'Bell asks Miri to guide',type='speak',actor='e4',recipient='e1',factuality='hypothetical',roles={'actor':[381],'recipient':[385]})
E('guide_possible',387,'Miri guides visitors',actor='e1',factuality='hypothetical')
E('point_print',390,'Kit points at print beneath diagram',actor='e2',patients=['e34'],roles={'actor':[389],'patient':[394],'landmark':[397]})
E('torch_star_instruction',399,'operator keeps torch on printed star',type='state',patients=['e22'],factuality='desired',roles={'patient':[401],'location':[404]})
U('read_instruction',399,'e2','p25','e1','read_instruction',primary=False,scope='s0')
E('printed_star',409,'yellow star is printed at track left end',type='state',patients=['e36'],roles={'patient':[407],'location':[413],'whole':[416]})
E('busy',421,'Miri had been busy tracking moth with beam',type='state',actor='e1',roles={'experiencer':[417]})
E('beam_tracking_summary',422,'Miri makes beam follow moth during earlier trials',actor='e1',patients=['e23'],roles={'patient':[424],'target':[427]})
M('beam_tracking_summary',425,'action','Follow describes the controlled beam tracking, not independent agency of light.')
E('notice_star',432,'Miri notices printed star before discovery',type='perceive',actor='e1',patients=['e36'],factuality='negated',roles={'actor':[429],'patient':[433]})
E('say_excuse',436,'Miri and Kit say torch is faulty',type='speak',actor='e5',factuality='hypothetical',roles={'actor':[434]})
E('faulty_content',439,'torch is faulty',type='state',patients=['e22'],factuality='hypothetical',roles={'patient':[438]})
U('propose_excuse',442,'e2','p29','e1','propose_excuse',roles={'actor':[441]})
E('dragon_only_plan',445,'Miri and Kit perform only dragon demonstration',actor='e5',patients=['e17'],factuality='desired',roles={'patient':[447]})
U('propose_dragon_only',445,'e2','p30','e1','proposal',primary=False,scope='s0')
E('watch_visitors',449,'Miri looks at gathering visitors',type='perceive',actor='e1',patients=['e6'],roles={'actor':[448],'patient':[452]})
E('gather_visitors',453,'visitors gather outside',type='move',actor='e6',roles={'actor':[452]})
E('early_speech_option',457,'Miri starts speech immediately',type='speak',actor='e1',factuality='hypothetical',roles={'actor':[455],'speech':[459]})
E('hope_no_questions',462,'Miri hopes nobody asks about trial',type='feel',actor='e1',factuality='hypothetical')
E('visitor_question',464,'visitors ask about trial',type='speak',actor='e6',factuality='negated')
E('put_torch',467,'Miri puts torch on two books',type='move',actor='e1',patients=['e22'],roles={'actor':[466],'patient':[469],'support':[473]})
E('wedge_handle',474,'Miri wedges torch handle with clay',actor='e1',patients=['e39'],instruments=['e40'],roles={'patient':[476],'instrument':[479,482]})
E('aim_beam',484,'Miri turns beam toward sheet',actor='e1',patients=['e23'],roles={'patient':[486],'target':[489]})
E('wait_request',490,'visitors wait for presenters',actor='e6',factuality='desired')
U('disclose',492,'e1','p35','e6','disclose_trial_problem',roles={'actor':[491]})
E('match_first',497,'first try matches label',factuality='negated',roles={'comparison':[499]})
E('first_torch_move_report',501,'presenters moved torch during first try',type='move',actor='e5',patients=['e22'],factuality='reported',roles={'actor':[500],'patient':[503]})
E('give_minute',507,'visitors give presenters one minute',actor='e6',recipient='e5',factuality='desired',roles={'actor':[506],'recipient':[508]})
U('ask_minute',507,'e1','p36','e6','request_time',primary=False,scope='s0')
E('boy_enter',517,'boy enters activity room',type='move',actor='e7',roles={'actor':[512],'destination':[520]})
E('dot_peer',522,'Dot peers around boy elbow',type='perceive',actor='e3',roles={'actor':[521],'landmark':[525]})
E('reset_moth',527,'Miri slides moth back to start',type='move',actor='e1',patients=['e16'],roles={'actor':[526],'patient':[529],'destination':[533]})
E('watch_torch',535,'Kit watches stabilized torch',type='perceive',actor='e2',patients=['e22'],roles={'actor':[534],'patient':[537]})
E('ready_catch',538,'Kit is ready to catch torch if it shifts',type='state',actor='e2')
E('catch_conditional',540,'Kit catches shifting torch',actor='e2',patients=['e22'],factuality='hypothetical',roles={'patient':[541]})
E('shift_conditional',544,'torch shifts during trial',type='move',patients=['e22'],factuality='hypothetical',roles={'patient':[543]})
E('slide_fixed',546,'Miri pushes moth toward screen with fixed torch',type='move',actor='e1',patients=['e16'],roles={'actor':[545],'patient':[548],'target':[551]})
E('shrink_fixed',554,'moth shadow shrinks from plate size to saucer size',type='state',patients=['e18'],roles={'patient':[553],'size_from':[561],'size_to':[567]})
U('oh',569,'e3','p46','e5','reaction',roles={'actor':[570]})
E('torch_still',573,'torch stays put during controlled trial',type='state',patients=['e22'],factuality='reported',roles={'patient':[572]})
U('explain_fixed',576,'e1','p47','e6','explain_control',roles={'actor':[575]})
E('moth_near',580,'moth was nearer torch in explained comparison',type='state',patients=['e16'],factuality='reported',roles={'patient':[579],'landmark':[583]})
E('shadow_spread_explain',586,'nearer-torch moth gives spread-out shadow',type='state',patients=['e18'],factuality='reported',roles={'patient':[585]})
E('less_spread_room',591,'near screen there is less room for shadow to spread',type='state',factuality='reported',roles={'landmark':[590]})
E('spread_rule',597,'shadow spreads while projected toward screen',type='move',patients=['e18'],factuality='reported',roles={'patient':[595]})
E('land_rule',600,'shadow lands on screen in explanation',type='state',patients=['e18'],factuality='reported',roles={'patient':[599]})
M('explain_fixed',597,'quoted_content','Continuation of the same explanation utterance after narrator said.')
E('lift_dragon2',602,'Kit lifts dragon for near-torch demonstration',type='move',actor='e2',patients=['e17'],roles={'actor':[601],'patient':[604]})
E('demonstration_content',607,'this demonstrates near-torch placement result',type='state',factuality='reported')
U('introduce_dragon',607,'e2','p41','e6','demonstration_introduction',primary=False,scope='s0')
E('place_generic',612,'operator puts an object close to torch',type='move',factuality='hypothetical',roles={'landmark':[617]})
E('hold_dragon',619,'Kit holds dragon near beam',type='state',actor='e2',patients=['e17'],roles={'actor':[618],'patient':[621],'landmark':[624]})
E('fill_screen',628,'dragon shadow fills sheet',type='state',patients=['e19'],roles={'patient':[627],'surface':[630]})
E('curl_tail',632,'dragon shadow tail curls over chair',type='state',patients=['e46'],roles={'patient':[631],'landmark':[635]})
E('climb_wings',638,'dragon shadow wings extend nearly to screen top',type='state',patients=['e47'],roles={'patient':[637],'limit':[642]})
U('dot_play',644,'e3','p42','e5','playful_exclamation',roles={'actor':[643]})
E('eat_pretend',646,'pretend dragon eats moon',actor='e53',patients=['e54'],factuality='asserted',roles={'actor':[645],'patient':[648]})
E('moth_joke2',651,'dragon is called an improved moth again',type='state',patients=['e17'],factuality='reported',roles={'patient':[649,652]})
U('moth_joke_speech2',654,'e2','p9','e6','playful_relabeling',roles={'actor':[653]})
E('grin',655,'Kit grins',type='state',actor='e2')
E('handoff_dragon',657,'Miri hands dragon to Dot',type='transfer',actor='e1',patients=['e17'],recipient='e3',roles={'actor':[656],'patient':[659],'recipient':[661]})
E('dot_try_plan',664,'Dot tries shadow demonstration',actor='e3',factuality='desired',roles={'actor':[662]})
U('invite_dot',664,'e1','p43','e3','permission_with_condition',primary=False,scope='s0')
E('leave_torch_instruction',666,'Dot leaves torch on star',type='state',actor='e3',patients=['e22'],factuality='desired',roles={'patient':[668],'location':[671]})
E('dot_holds_cutout',673,'Dot holds received cutout near screen',type='state',actor='e3',patients=['e17'],roles={'actor':[672],'patient':[675],'landmark':[678]})
E('small_shadow',681,'received cutout shadow becomes small tidy shape',type='state',patients=['e19'],roles={'patient':[680,685]})
E('raise_fingers',688,'Dot raises two fingers beside cutout',type='move',actor='e3',patients=['e50'],roles={'actor':[687],'patient':[690],'landmark':[692]})
E('flutter_shadows',696,'cutout and finger shadows flutter on white sheet',type='move',patients=['e52'],roles={'patient':[695],'surface':[701]})
a.proposition('p46','Oh.',[568],scope_id='q20')
a.proposition('p47','The torch stayed put; nearer the torch the moth shadow spread out, and near the screen it has less room to spread.',[572,573,574,579,581,583,585,586,590,592,593,597,600],scope_id='q22')

# Grammar selected from explicit contextual tags, never an automatic POS pass.
for w,r in enumerate(a.words):
 if r['pos']=='det' and r['lemma'] in ['the','a','an']:
  F(w,determiner_kind='definite_article' if r['lemma']=='the' else 'indefinite_article',definiteness='definite' if r['lemma']=='the' else 'indefinite')
 if r['pos']=='det' and r['lemma'] in ['his','her','its','our','their']:
  F(w,determiner_kind='possessive',possessive_construction='possessive_determiner',mention_form='possessive_determiner',definiteness='definite')
 if r['pos']=='conj' and r['lemma']=='and':F(w,coordinator_type='additive',discourse_relation_kind='addition')
 if r['pos']=='pron' and r['lemma'] in ['he','she','it','I','we','they','you']:F(w,mention_form='personal_pronoun')
F([5,18,334,361],possessive_construction='s_genitive',grammatical_case='genitive')
F([106,649],contraction_expansion=['it','is'])
F([69,90],contraction_expansion=['we','will'])
F(59,contraction_expansion=['can','not'])
F(202,contraction_expansion=['that','is'])
F(207,contraction_expansion=['label','is'])
F(260,contraction_expansion=['does','not'],do_support_status='negative_auxiliary')
F(344,contraction_expansion=['they','are'])
F(351,contraction_expansion=['Dot','is'])
F(357,contraction_expansion=['there','would'],expletive_reference=True)
F(496,contraction_expansion=['did','not'],do_support_status='negative_auxiliary')
F(591,contraction_expansion=['there','is'],expletive_reference=True)
F(645,contraction_expansion=['it','is'])
F([39,125,130,201,241,277,385,433,508,541,543,595,599,692],grammatical_case='objective')
# She/it forms are syncretic; only actual object occurrences receive objective.
a.words[125].pop('grammatical_case',None);a.words[543].pop('grammatical_case',None);a.words[599].pop('grammatical_case',None)
F([69,90,434,500],grammatical_person=1,grammatical_number='plural',split_antecedent_ids=['e1','e2'])
F(354,grammatical_person=1,grammatical_number='singular')
F([506,662],grammatical_person=2)
F([110,138,225,493,508],split_antecedent_ids=['e1','e2'],grammatical_number='plural')
F(302,reflexive_antecedent_id='e1',reflexive_form='herself')
F([12,16,24,55,56,145,249,253,306,308,324,333,338,343,353,370,452,473,637,690,695,710],grammatical_number='plural')
for w,n in [(1,3),(23,6),(144,2),(164,1),(252,2),(472,2),(509,1),(634,1),(689,2),(702,1),(705,1)]:F(w,cardinal_value=n)
F(252,determiner_kind='dual_quantifier')
F(242,determiner_kind='demonstrative',definiteness='definite')
F(494,ordinal_rank=1,adjective_degree='positive')
F(592,determiner_kind='comparative_quantity',quantity_comparison_cue='less')
F([4,11,27,42,49,88,93,108,141,152,173,208,213,215,220,223,258,290,292,299,393,406,412,421,440,515,538,574,614,626,651,683,684,700,706,709],adjective_degree='positive')
# Cardboard is an attributive noun, not an adjective form.
a.words[88].pop('adjective_degree',None)
F(81,adjective_degree='comparative',lexical_scale_dimension='size',lexical_scale_direction='smaller')
F(195,adverb_degree='comparative',lexical_scale_dimension='width',lexical_scale_direction='wider')
F(581,adjective_degree='comparative',lexical_scale_dimension='distance',lexical_scale_direction='nearer')
F(219,adverb_degree='comparative')
for w,head in [(6,7),(15,16),(31,32),(88,89),(119,120),(136,137),(257,258),(323,324),(560,561),(703,704)]:F(w,dependency_relation='nominal_modifier',syntactic_governor_id=a.anchor(head))
F(481,dependency_relation='compound',syntactic_governor_id=a.anchor(482))
F([8,21,34,47,64,85,111,122,127,139,147,160,182,186,194,200,209,212,226,229,240,246,256,264,267,279,284,295,297,301,304,309,314,320,328,336,340,347,355,363,373,378,390,408,418,430,442,449,467,474,484,492,496,501,517,522,527,535,544,546,554,569,573,576,580,586,602,619,628,644,654,657,673,681,688,696],verb_form='finite',tense='past')
F([59,78,101,260,366,382,435,439,456,505,607,609,663],verb_form='finite',tense='present')
# Modal morphology does not imply time; these are morphologically preterite modals.
F([217,366,382,435,456],verb_form='finite',tense='past')
F([22,276,419,409,432],verb_form='past_participle')
for w in [22,276,419,409,432]:a.words[w].pop('tense',None)
F([54,65,72,86,175,268,288,332,422,453,632,638,646,655],verb_form='present_participle')
F([38,53,60,70,91,96,129,232,254,261,298,311,358,367,384,387,399,425,436,445,457,462,464,490,497,507,540,597,600,612,664,666],verb_form='bare')
# Lands is finite within explanation, not controlled by the earlier infinitive.
F(600,verb_form='finite',tense='present')
for marker,head,controller in [(37,38,'e4'),(52,53,'e3'),(95,96,'e53'),(128,129,'e1'),(231,232,'e1'),(310,311,'e28'),(386,387,'e1'),(539,540,'e2'),(596,597,'e18')]:
 F(marker,constituent_category='infinitive_marker',syntactic_governor_id=a.anchor(head))
 F(head,verb_form='infinitive',infinitive_marker_id=a.anchor(marker),subject_controller_id=controller)
for head,aux in [(22,21),(276,275),(419,418),(432,430)]:F(head,aspect='perfect',perfect_auxiliary_id=a.anchor(aux),auxiliary_chain=['have'])
for head,aux in [(268,267),(646,645)]:F(head,aspect='progressive',progressive_auxiliary_id=a.anchor(aux),auxiliary_chain=['be'])
F(409,voice='passive',passive_auxiliary_id=a.anchor(408),auxiliary_chain=['be'])
F([217,366,382,435,456,505,663],modal_auxiliary_class='modal')
F([254,298,399,445,490,666],imperative_subject_status='understood_second_person')
F(505,subject_auxiliary_inversion=True)
F([202,204,257,258,398,568],sentence_fragment_type='contextual_utterance_fragment')
F(170,phrase_has_elision=True,nominal_ellipsis_license='parallel_other_end')
F(224,kind_antecedent_id='kind_label',referent_kind='kind')
F([216,224],generic_reference=True)
F([55,56],generic_reference=True,referent_kind='kind')
F(58,referent_kind='generic_person',generic_reference=True)
F(611,referent_kind='generic_operator',generic_reference=True)
F(613,reference_specificity='nonspecific',referent_kind='bound_variable')
F(61,quantifier_domain_restriction={'kind':'museum_objects','scope_id':'s3'})
F(463,quantifier_domain_restriction={'group':'e6'},proposition_polarity='negative',negation_scope_id='p32')
for w,p in [(59,'p3'),(102,'p7'),(260,'p15'),(383,'p23'),(431,'p26'),(496,'p34')]:F(w,proposition_polarity='negative',negation_scope_id=p)
F(464,proposition_polarity='negative',factuality='negated',evidence=[455,456,457,461,462,463,464,465],note='The hoped-for absence of questions is embedded in an unchosen alternative; it is not an actual no-question fact.')
F(59,modal_base={'kind':'permission_or_access_complaint','holder':'e3','content_id':'p3'})
F(217,modal_base={'kind':'possible_evaluation','holder':'e2','content_id':'p13'})
F(366,modal_base={'kind':'epistemic_possibility','holder':'e1','content_id':'p21'})
F(382,modal_base={'kind':'feared_conditional_possibility','holder':'e1','condition_id':'p22','content_id':'p24'})
F(435,modal_base={'kind':'proposed_option','holder':'e2','content_id':'p29'})
F(456,modal_base={'kind':'considered_option','holder':'e1','content_id':'p31'})
F(505,modal_base={'kind':'request','content_id':'p36'})
F(663,modal_base={'kind':'permission','grantor':'e1','recipient':'e3','content_id':'p44'})
for w,typ in [(57,'relative_locative'),(71,'declarative_content'),(126,'supplementary_relative'),(132,'temporal_before'),(175,'reduced_relative'),(221,'comparison'),(238,'temporal_as'),(247,'temporal_until'),(265,'concessive'),(272,'as_if_comparison'),(312,'temporal_when'),(371,'conditional'),(377,'relative_subject'),(428,'result'),(542,'conditional'),(577,'temporal_when'),(598,'temporal_before'),(610,'generic_condition')]:F(w,subordinator_type=typ)
for w,rel in [(83,'then'),(132,'before'),(227,'again'),(238,'overlap'),(247,'until'),(265,'concession'),(287,'addition'),(312,'when'),(443,'then'),(465,'alternative_replacement'),(504,'addition'),(542,'conditional'),(577,'when'),(598,'before'),(610,'when'),(686,'then')]:F(w,discourse_relation_kind=rel)
for w,rel in [(83,'then'),(132,'before'),(238,'overlap'),(247,'until'),(312,'when'),(443,'then'),(577,'when'),(598,'before'),(686,'then')]:F(w,temporal_signal_relation=rel)
F(2,time_expression_id='time_three_oclock',temporal_anchor_unresolved=True,event_time_interval={'clock_text':'three_oclock','am_pm':'unspecified','day':'story_day'})
F(45,calendar_day_name='Saturday',time_expression_id='time_saturday',temporal_anchor_unresolved=True)
F(62,temporal_deixis='today',time_anchor_id='time_story_day')
F(133,time_expression_id='time_museum_closing',temporal_anchor_unresolved=True)
F(510,measure_unit='minute',temporal_granularity='minute',temporal_duration={'value':1,'unit':'minute','kind':'requested_wait','scope_id':'q19','factuality':'desired'})

SUBJECTS={
'e1':[22,34,64,65,127,129,182,200,229,232,264,268,284,288,298,301,304,340,421,422,432,449,457,462,467,474,484,492,527,546,576,657],
'e2':[47,85,86,186,209,212,240,256,279,314,347,355,390,442,535,538,540,602,619,654,655],
'e3':[53,54,352,522,569,644,664,666,673,688], 'e4':[38,122,367,384], 'e5':[70,91,111,139,147,226,436,445,501],
'e6':[345,453,464,490,507], 'e7':[517], 'e9':[8], 'e15':[160,208,276],
'e16':[580], 'e17':[101,108,358,651], 'e18':[194,246,295,297,554,586,597,600],
'e19':[628,681], 'e22':[439,544,573], 'e23':[320,425], 'e26':[251], 'e28':[309,311],
'e30':[328], 'e31':[336], 'e33':[363], 'e36':[409], 'e46':[632], 'e47':[638], 'e52':[696], 'e53':[96,646], 'e63':[218],
}
for eid,ws in SUBJECTS.items():F(ws,grammatical_subject_id=eid)
F(399,imperative_subject_status='generic_operator_or_current_operator')
# We do not copy Kit's reporting subject onto the instruction's operator.
for w,eid in [(22,'e14'),(38,'e1'),(65,'e15'),(86,'e17'),(111,'e22'),(122,'e22'),(129,'e22'),(139,'e20'),(147,'e16'),(182,'e22'),(186,'e16'),(200,'e2'),(232,'e23'),(240,'e16'),(276,'e1'),(279,'e16'),(284,'e22'),(288,'e24'),(304,'e27'),(314,'e16'),(399,'e22'),(422,'e23'),(425,'e16'),(432,'e36'),(445,'e17'),(467,'e22'),(474,'e39'),(484,'e23'),(501,'e22'),(527,'e16'),(535,'e22'),(540,'e22'),(546,'e16'),(602,'e17'),(619,'e17'),(628,'e20'),(646,'e54'),(657,'e17'),(666,'e22'),(673,'e17'),(688,'e50')]:F(w,grammatical_object_id=eid)
F(355,indirect_object_id='e3');F(507,indirect_object_id='e5')
for w,eid in [(9,'e10'),(17,'e13'),(75,'e20'),(103,'e15'),(114,'e4'),(117,'e66'),(124,'e1'),(134,'e9'),(143,'e25'),(150,'e21'),(156,'e20'),(163,'e60'),(168,'e61'),(178,'e57'),(189,'e21'),(196,'e20'),(235,'e16'),(269,'e15'),(321,'e65'),(325,'e29'),(337,'e30'),(341,'e14'),(348,'e32'),(352,'e6'),(368,'e6'),(391,'e34'),(395,'e35'),(402,'e36'),(410,'e37'),(414,'e21'),(450,'e6'),(471,'e38'),(477,'e40'),(480,'e40'),(487,'e20'),(513,'e41'),(518,'e9'),(523,'e42'),(531,'e43'),(549,'e20'),(558,'e44'),(566,'e45'),(588,'e20'),(615,'e22'),(622,'e23'),(633,'e48'),(640,'e49'),(660,'e3'),(669,'e36'),(676,'e20'),(691,'e17'),(698,'e20')]:F(w,prepositional_object_id=eid)
F(9,coordination_category='NP',conjunct_head_ids=[a.anchor(10),a.anchor(12),a.anchor(16)])

# Physical carriers, depicted apparatus and projection states remain distinct.
F(7,part_whole_relation={'part_id':'e9','whole_id':'e8','scope_id':'s0'})
F(16,containment_direct=B('e12',{'container':'e13'}))
F(18,possession_owner=B('e13',{'owner':'e2'}))
F(23,quantity_total={'domain':'e14','value':6,'unit':'chairs','scope_id':'s0','assertion_status':'asserted'})
F(22,spatial_configuration=B('e14',{'configuration':'neat_row','event_id':EV['arrange']}))
F(32,attributes=[{'name':'exhibit_topic','value':'shadow_projection'}])
F(88,material_composition=B('e17','cardboard'))
F(87,possession_owner=B('e17',{'owner':'e2'}))
F(96,enactment={'performer_id':'e2','prop_id':'e17','character_id':'e53','world_id':'world_playful_dragon','represented_event_id':EV['eat_plan']},evidence=[89,90,91,93,96,98,645,646,648],note='Moon eating is proposed imaginative play around a dragon shadow, not literal consumption or a physical moon prop established in the room.')
F(108,speaker_local_name={'entity_id':'e17','name':'improved moth','speaker_id':'e2'},figurative_mapping={'target_id':'e17','source_image':'improved_moth','kind':'playful_relabeling','literal_event':False})
F(111,possession_borrower=B('e22',{'borrower_group':'e5','receiving_holder':'e1'}),possession_lender=B('e22',{'lender':'e4'}),transfer_kind=B('e22','temporary_loan'),transfer_completion=B('e22',{'completed':True}),event_collective_participants=B('e5',{'event_id':EV['loan'],'borrowers':['e1','e2']}),retrieval_inverse_relation={'borrower_group':'e5','event_id':EV['loan'],'canonical_relation':'lend_to','source_id':'e4','recipient_id':'e1','theme_id':'e22','surface_perspective':'borrow_from','scope_id':'s0','assertion_status':'asserted'},evidence=[110,111,113,115,116,121,122,123,125],note='Borrowed and handed describe one loan. Canonical transfer roles retain giver Bell, direct recipient Miri and borrower group Miri/Kit rather than inventing another loan.')
F(122,possession_holder=B('e22',{'holder':'e1'}),transfer_source=B('e22',{'source':'e4'}),transfer_recipient=B('e22',{'recipient':'e1'}),transfer_handoff_location=B('e22',{'location':'e66'}))
F(129,possession_return_target=B('e22',{'return_to':'e4'},'s5',factuality='desired'),transfer_return_due=B('e22',{'condition':'before_museum_closing'},'s5',factuality='desired'))
F(141,appearance_color=B('e20','white'))
F(139,spatial_configuration=B('e20',{'landmarks':['e25'],'relation':'between'}),spatial_support=B('e20',{'supported_by':'e25'}))
F(145,quantity_part={'whole':'e14','part':'e25','part_count':2,'whole_count':6})
F(147,spatial_configuration=B('e16',{'landmark':'e21','relation':'on'}),spatial_support=B('e16',{'supported_by':'e21'}))
F(152,material_composition=B('e21','wood'))
F(155,spatial_configuration=B('e21',{'landmark':'e20','relation':'in_front_of'}))
for w,eid,role in [(162,'e56','torch'),(167,'e57','screen'),(174,'e58','arrow'),(177,'e59','moth'),(180,'e57','screen')]:
 F(w,evidence_world_status='depicted',reference_metonymic_link={'depicted_entity':eid,'representation_carrier':'e15','apparatus_role':role,'relation':'diagram_symbol_for_role'},evidence=[159,160,162,167,174,175,177,180],note='Diagram symbols are represented apparatus roles, not additional physical torches/screens placed in the activity room.')
F(175,spatial_configuration=B('e58',{'direction_target':'e57','directed_item':'e59'},'s6'),semantic_world_id='world_diagram')
F(182,possession_holder=B('e22',{'holder':'e1'}),object_luminosity=B('e22','lit'))
F(186,motion_route=B('e16',{'event_id':EV['slide1'],'landmark_id':'e21','role':'route'}))
F(194,event_state_change=B('e18',{'dimension':'projected_width','change':'wider','event_id':EV['grow1']}),spatial_configuration=B('e18',{'landmark':'e20','relation':'projected_across'}))
F(229,motion_posture=B('e1','leaning_forward'),event_goal_role=B('e1',{'event_id':EV['lean'],'goal_event_id':EV['beam_on'],'goal_state':'beam_on_moth'}))
F(246,event_state_change=B('e18',{'dimension':'projected_size','change':'larger','event_id':EV['grow2']}))
F(250,lexical_sense_id='near_achievement_without_attainment',evidence=[249,250,251,252,253],note='Nearly touching is an approached boundary, not asserted contact between shadow wings and chairs.')
F(251,spatial_contact=B('e26',{'target':'e25','touching':False,'near_contact':True}))
F(258,quantity_comparison={'entity_id':'e18','dimension':'projected_size','comparison_kind':'figurative_dragon_sized','scope_id':'q10','assertion_status':'attributed_claim'})
F(276,figurative_mapping={'target_id':'e15','source_image':'person_insulting_Miri','kind':'as_if_personification','literal_event':False},evidence=[263,266,268,271,272,273,274,276,277],note='The label has no actual hostile intention. The look is narrated; its insult comparison remains nonliteral.')
F(284,possession_holder=B('e22',{'holder':'e1'}),event_control=B('e22',{'controller':'e1','mode':'direct','event_id':EV['torch_move3']}))
F(290,attributes=[{'name':'light_quality','value':'bright'}])
F(292,spatial_alignment=B('e24',{'aligned_with':'e16','relation':'centered_on'}))
F(295,causal_parent=B('e18',{'cause_events':[EV['moth_back'],EV['torch_move3']],'effect':EV['jump_shadow']},status='candidate'),evidence=[279,281,284,286,288,291,295,297],note='The changes coincide with moving moth and torch; candidate combined-motion explanation is retained without claiming either change alone is experimentally isolated.')
for w,part,whole in [(249,'e26','e18'),(306,'e27','e1'),(308,'e28','e1'),(324,'e65','e16'),(362,'e33','e1'),(394,'e34','e15'),(397,'e35','e15'),(413,'e37','e21'),(476,'e39','e22'),(525,'e42','e7'),(631,'e46','e19'),(637,'e47','e19'),(642,'e49','e20'),(690,'e50','e3')]:F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
F(311,attributes=[{'name':'bodily_state','value':'aching_arms'}])
F(309,event_phase=B('e28',{'affected_event_id':EV['ache'],'cue':'onset'}))
F(320,event_state_change=B('e23',{'before':'aimed_on_moth','after':'off_moth_wings','event_id':EV['beam_slip']}))
F(323,material_composition=B('e16','paper'))
F(328,event_source_role=B('e30',{'source':'e29','event_kind':'audible_arrival'}))
F(332,reference_metonymic_link={'literal':'e30','relation':'voices_of_arriving_people','person_group':'e6'},evidence=[327,328,332,333,334,335,344,353,370],note='Voices are sound carriers of the arriving group. Dot is later identified among them; Bell membership remains only possible.')
F(336,figurative_mapping={'target_id':'e31','source_image':'floating_above','kind':'auditory_prominence_metaphor','literal_event':False},object_sound_level=B('e31',{'relative_to':'e30','quality':'audibly_prominent'}))
F(390,spatial_configuration=B('e34',{'landmark':'e35','relation':'beneath'}))
F(406,appearance_color=B('e36','yellow'))
F(409,spatial_configuration=B('e36',{'landmark':'e37','relation':'printed_at'}))
F(413,spatial_region=B('e37',{'landmark':'e21','region':'left_end'}))
F(422,supporting_event_ids=[EV['lean'],EV['beam_on'],EV['torch_move3'],EV['center_circle']],evidence=[229,232,234,237,284,286,288,291,417,421,422,424,425,427],note='Busy beam-following summarizes earlier actions; it is not an additional trial or an independent action of light.')
F(439,object_operability=B('e22','faulty','s16','attributed_claim',factuality='hypothetical'),evidence=[434,435,436,438,439,440,465,467,474,546,554,572,573],note='Faulty torch is proposed excuse content. No narrator observation establishes an actual device fault, and no repair is performed.')
F(473,quantity_total={'domain':'e38','value':2,'unit':'books','scope_id':'s0','assertion_status':'asserted'})
F(467,spatial_support=B('e22',{'supported_by':'e38'}),motion_destination=B('e22',{'landmark_id':'e38','role':'placed_on'}),possession_user=B('e22',{'user_group':'e5'}))
F(474,event_instrument_binding=B('e39',{'event_id':EV['wedge_handle'],'instrument_id':'e40'}),object_stability=B('e22',{'stabilized_by':'e40','supported_by':'e38'}))
F(482,material_composition=B('e40','modeling_clay'))
F(484,spatial_facing_target=B('e23',{'target':'e20'}))
F(515,appearance_color=B('e41','red'))
F(516,possession_holder=B('e41',{'wearer':'e7'}))
F(517,motion_destination=B('e7',{'landmark_id':'e9','role':'destination'}),motion_arrival_completion=B('e7',{'arrived_at':'e9'}))
F(522,spatial_viewpoint=B('e3',{'view_path':'around_boy_elbow','landmark':'e42'}))
F(527,motion_destination=B('e16',{'landmark_id':'e43','role':'destination'}))
F(554,event_state_change=B('e18',{'dimension':'projected_size','change':'smaller','from_comparator':'e44','to_comparator':'e45','event_id':EV['shrink_fixed']}),evidence=[527,533,537,544,546,548,551,553,554,561,567,572,573,574],note='Later controlled trial actually yields smaller shadow while torch stays put. Plate/saucer supply familiar size comparisons, not measured diameters or actual plates present in room.')
F([561,567],referent_kind='comparison_kind')
F(573,spatial_anchor_stability=B('e22',{'stationary_during':EV['slide_fixed']},'q21','attributed_claim'))
F(581,spatial_distance_band=B('e16',{'landmark':'e22','distance_change':'nearer'},'q22','attributed_claim'))
F(586,event_state_change=B('e18',{'dimension':'projected_extent','change':'spread_out','condition':'moth_nearer_torch'},'q22','attributed_claim'))
F(591,causal_mechanism=B('e18',{'source':'e1','condition':'cutout_near_screen','mechanism':'less_space_for_shadow_to_spread_before_projection'},'q22','attributed_claim'),evidence=[577,581,583,586,588,590,592,593,595,597,599,600],note='Miri offers this explanation. It is not an independent geometric derivation or a separate new experimental result.')
F(600,figurative_mapping={'target_id':'e18','source_image':'landing_on_surface','kind':'projection_metaphor','literal_event':False})
F(619,possession_holder=B('e17',{'holder':'e2'}),spatial_distance_band=B('e17',{'landmark':'e23','distance':'near'}))
F(626,object_shape=B('e19','jagged'))
F(628,spatial_extent=B('e19',{'occupied_region':'e20','extent':'fills_sheet'}))
F(632,spatial_configuration=B('e46',{'landmark':'e48','relation':'projected_over'}))
F(638,spatial_extent=B('e47',{'limit':'e49','extent':'almost_to_top'}),figurative_mapping={'target_id':'e47','source_image':'climbing','kind':'spatial_extent_metaphor','literal_event':False})
F(646,enactment={'performer_id':'e2','prop_id':'e17','character_id':'e53','world_id':'world_playful_dragon','represented_event_id':EV['eat_pretend'],'physical_support_event_id':EV['hold_dragon']},evidence=[619,621,627,628,643,644,645,646,648],note='Dot supplies playful interpretation of Kit-controlled shadow. No literal animal eating or physical moon object is inferred.')
F(651,speaker_local_name={'entity_id':'e17','name':'improved moth','speaker_id':'e2'},figurative_mapping={'target_id':'e17','source_image':'improved_moth','kind':'playful_relabeling','literal_event':False})
F(657,transfer_source=B('e17',{'source':'e1'}),transfer_recipient=B('e17',{'recipient':'e3'}),transfer_kind=B('e17','temporary_demo_handoff'),transfer_completion=B('e17',{'completed':True}),possession_holder=B('e17',{'holder':'e3'}),evidence_missing={'needed':'unreported_transfer_from_Kit_to_Miri_before_handoff'},evidence=[601,602,604,618,619,621,656,657,659,661],note='Kit holds dragon, then Miri explicitly hands it to Dot. No Kit-to-Miri transfer event is invented to bridge the source gap.')
F(673,spatial_distance_band=B('e17',{'landmark':'e20','distance':'near'}),possession_holder=B('e17',{'holder':'e3'}))
F(681,event_state_change=B('e19',{'dimension':'projected_size','after':'small_tidy_shape','event_id':EV['small_shadow']}))
F(689,quantity_total={'domain':'e50','value':2,'unit':'fingers','scope_id':'s0','assertion_status':'asserted'})
F(690,spatial_configuration=B('e50',{'landmark':'e17','relation':'beside'}))
F(695,group_members=['e19','e51'],spatial_configuration=B('e52',{'landmark':'e20','relation':'projected_on'}))
F(700,appearance_color=B('e20','white'))
F(704,reference_unresolved=True,antecedent_candidates=['e17','e16'],identity_hypothesis={'entity_id':'e55','candidate_ids':['e17','e16'],'scope_id':'s0','assertion_status':'candidate','basis':'closing_moth_name_after_dragon_handoff'},evidence=[649,651,652,657,659,661,675,680,692,695,703,704],note='Last physical cutout is the handed-over dragon, twice called improved moth. Closing paper moth could continue that nickname or reflect a source naming inconsistency. e55 is a role/reference placeholder, not an additional physical cutout or invented swap.')
F([707,710],reference_metonymic_link={'literal_shadow':'e51','source_body_part':'e50','relation':'finger_shadows_as_living_wings'},figurative_mapping={'target_id':'e51','source_image':'living_wings','kind':'visual_metaphor','literal_event':False})

# Mental and spoken contents are checked independently of outer attitudes.
F(34,goal_owner_id='e1',goal_content_id='p1',goal_polarity='achieve',goal_status='active',goal_scope_bundle={'owner_id':'e1','intention_event_id':EV['want_guide'],'scope_id':'s0','assertion_status':'asserted'},evidence=[34,35,36,38,39,42,43,45,364,366,382,384],note='Junior-guide appointment is desired and later worried about, never awarded. Bell arrival also remains uncertain.')
F(47,goal_owner_id='e2',goal_content_id='p2',goal_polarity='achieve',goal_status='active',goal_beneficiary_ids=['e3'],evidence=[46,47,50,51,53,54,55,59,60,61,672,673,688],note='Kit wants Dot to stop her no-touch museum description. Ending participation supports progress by interpretation, not an explicit statement that she permanently changed her view.')
F(54,utterance_content_id='p3',proposition_polarity='negative',speech_act_kind='reported_recurring_complaint',evidence=[47,50,53,54,55,56,59,60,61],note='Negative permission/access content is Dot’s prior complaint, not an objective no-touch rule imposed on this activity room.')
# Full negative complaint content is distinct from the positive negation target.
a.proposition('p48','Museums are rooms where people cannot touch anything.',[55,56,58,59,60,61],scope_id='s3')
F(54,utterance_content_id='p48')
F(70,intention_holder_id='e1',intention_content_id='p5',plan_commitment_status='announced',cooperation_goal_id='p5')
F(78,causal_scope=B('e18',{'claim':'p4','source_id':'e1','condition':'fixed_torch'},'q2','attributed_claim'))
F(91,intention_holder_id='e2',intention_content_id='p6',plan_commitment_status='playfully_proposed')
F(108,dialogue_response_to_id=EV['label_objection'],dialogue_turn_function='playful_reframing')
F(127,promise_content_id='p10',promise_beneficiary_id='e4',plan_commitment_status='promised',temporal_deadline={'action_event_id':EV['return_planned'],'before':'time_museum_closing'},evidence=[111,122,125,126,127,129,130,132,133,668],note='Return is promised. Story ends while torch remains in use; no completed return or broken-promise verdict is implied.')
F(204,propositional_antecedent_id='p4',discourse_contrast_dimension='shadow_size_change_direction',discourse_result_target=EV['grow1'])
F(208,belief_holder_id='e2',belief_content_id='p12',belief_certainty='possible',epistemic_attitude_kind='hypothesis')
F(209,utterance_content_id='p49')
a.proposition('p49','The label may be wrong.',[205,207,208],scope_id='q8')
F(212,affect_experiencer_id='e2',affect_kind='pleased',affect_expression_channel='audible_tone',affect_scope_bundle={'experiencer_id':'e2','affect_event_id':EV['pleased'],'scope_id':'s0','assertion_status':'asserted'})
F(218,viewpoint_evaluative_stance={'holder_id':'e2','content_id':'p13','assertion_status':'candidate'},evidence=[209,210,211,212,213,215,217,220,223],note='Adjacent pleased tone licenses Kit-centered evaluation as a candidate; the modal comparative itself remains hypothetical.')
F(226,event_iteration=B('e5',{'earlier_trial_event_ids':[EV['slide1'],EV['grow1']],'new_trial_event_id':EV['trial2']}))
F(261,reasoner_id='e1',reasoning_mode='reject_inference',reasoning_content_id='p15',reasoning_validity_claim='insufficient_proof')
F(264,dialogue_response_to_id=EV['dragon_sized'])
F(301,speaker_id='e1',addressee_ids=['e1'],communication_channel='self_directed_speech')
F(345,belief_holder_id='e1',belief_content_id='p18',epistemic_attitude_kind='arrival_timing_assessment')
F(355,communication_scope_bundle={'speaker_id':'e2','utterance_event_id':EV['earlier_dragon_telling'],'scope_id':'q14','assertion_status':'attributed_claim'},source_scope_id='q14')
F(363,affect_observer_attribution={'experiencer_id':'e1','cue':'stomach_tightening','interpretation':'concern_about_possible_evaluation','scope_id':'s0','assertion_status':'candidate'},evidence=[361,362,363,364,366,371,373,378,381,382,383,384,387],note='Bodily tightening is explicit. Anxiety about evaluation is a contextual reading, not a diagnosis or permanent disposition.')
F(367,belief_holder_id='e1',belief_content_id='p21',belief_certainty='possible')
F(371,conditional_antecedent_id='p22',conditional_consequent_id='p24',scope_operator='conditional')
F(384,proposition_polarity='negative',negation_scope_id='p23',belief_holder_id='e1',belief_content_id='p24',belief_certainty='feared_possibility')
F(399,request_action_id='p25',evidence_source_id='e34',communication_channel='reading_aloud',evidence=[390,394,397,398,399,401,404],note='Kit reads existing instruction. The source does not name the original label writer; Kit is the current reader, not author of the rule.')
F(432,belief_holder_id='e1',belief_content_id='p27',epistemic_attitude_kind='unawareness',causal_parent=B('e1',{'cause':EV['busy'],'effect':EV['notice_star'],'effect_polarity':'negative'}),evidence=[417,418,419,420,421,422,425,427,428,429,430,431,432,433],note='Narrator links distraction to not noticing the star; content is the star’s presence/location, separate from the negated noticing predicate p26.')
F(436,plan_commitment_status='considered_not_executed',utterance_content_id='p28',speech_act_kind='proposed_excuse',evidence=[434,435,436,438,440,442,465,492,497,501],note='Actual Kit proposal is p29. The hypothetical inner saying would communicate p28; no actual false claim to visitors is fabricated.')
F(445,plan_commitment_status='proposed_not_adopted',intention_holder_id='e2',intention_content_id='p30')
F(457,plan_commitment_status='considered_not_executed',intention_holder_id='e1',intention_content_id='p31')
F(462,goal_owner_id='e1',goal_content_id='p33',goal_status='hypothetical_within_unchosen_option',goal_polarity='achieve')
F(465,plan_revision={'considered':'p31','chosen_action_events':[EV['put_torch'],EV['wedge_handle'],EV['aim_beam'],EV['disclose']]})
F(490,request_action_id='p45')
F(492,disclosure_content_id='p35',communication_intended_effect='acknowledge_confounded_trial_and_request_time')
F(501,reference_metonymic_link={'grammatical_actor':'e5','relation':'joint_responsibility_for_trial','known_torch_operator':'e1'},evidence=[182,184,229,284,286,493,495,500,501,503,504],note='Miri uses we to acknowledge the shared experimental procedure. This does not require inventing Kit physically taking the torch during the first try.')
F(507,request_action_id='p36',request_acceptance_status='no_explicit_verbal_acceptance',evidence=[505,506,507,508,509,510,517,522,527,554],note='Demonstration continues after request, but no exact measured one-minute wait or verbal assent is supplied.')
F(538,plan_contingency={'if':'p37','then':'p38'},plan_commitment_status='ready_if_needed')
F(542,conditional_antecedent_id='p37',conditional_consequent_id='p38',scope_operator='conditional')
F(569,speech_act_kind='reaction',communication_intended_effect='brief_reaction_to_observed_shrinking',evidence=[554,561,567,568,569,570],note='Oh has no fully asserted geometrical proposition; no automatic comprehension or endorsement of the later explanation is inferred.')
F(576,reasoner_id='e1',reasoning_mode='causal_explanation',reasoning_content_id='p4',reasoning_conclusion_id='p40',reasoning_premise_ids=['p39'],supporting_event_ids=[EV['slide_fixed'],EV['shrink_fixed']],utterance_evidence_type='observed_controlled_demonstration')
F(607,discourse_example_target='p41')
F(646,imaginer_id='e3',imagined_content_id='p42',imagined_world_id='world_playful_dragon',imagination_function='playful_shadow_interpretation')
F(654,dialogue_response_to_id=EV['dot_play'],dialogue_turn_function='repeat_playful_improved_moth_name')
F(664,permission_grantor_id='e1',permission_recipient_id='e3',permission_content_id='p44',permission_status='granted_with_torch_position_condition',request_action_id='p25')
F(666,obligation_debtor_id='e3',obligation_creditor_id='e1',obligation_content_id='p25',obligation_status='instructed_for_demo')
F(696,narrative_thread_id='thread_shadow_trial_and_participation',narrative_change_dimension='confounded_rehearsal_to_stable_demonstration_and_Dot_participation',narrative_resolution_evidence={'problem':'p4','outcome_event_ids':[EV['shrink_fixed'],EV['small_shadow'],EV['raise_fingers']],'status':'controlled_result_and_participation_observed','assertion_status':'candidate'},narrative_theme_candidate={'content':'honest_revision_and_shared_play_make_demonstration_work','assertion_status':'candidate'},narrative_motif_link={'earlier_words':[53,54,55,59,60,61,96,98,108,109],'ending_words':[673,675,688,690,696,704,710],'relation':'untouchable_room_complaint_and_improved_moth_joke_resolve_in_hands_on_play','assertion_status':'candidate'},narrative_closure_candidate={'cue':'paired_cutout_and_finger_shadows','assertion_status':'candidate'},evidence=[53,54,59,60,111,127,194,246,284,399,467,474,492,546,554,657,673,688,696],note='Closing participation and successful projection are observed. Guide selection, completed return, permanent change in Dot’s museum opinion and a cutout swap are not inferred.')

# Infinitival clauses with their own overt subjects do not inherit subject control.
for w in [38,53]:a.words[w].pop('subject_controller_id',None)
F([275,464],verb_form='finite',tense='past')
F(694,split_antecedent_ids=['e17','e50'],group_members=['e17','e50'],evidence=[675,688,690,692,694,695],note='Their denotes the cutout and fingers that cast shadows; it does not denote the shadows themselves.')
M('disclose',490,'quoted_directive')

feedback={
 'summary':'Museum demonstration separates physical apparatus and diagram symbols, confounded early trials and the stable successful trial, imaginative dragon play, quoted claims, promises and unchosen excuses.',
 'ambiguities':[
 {'words':[619,621,656,657,659,661],'issue':'Kit holds dragon, then Miri hands it to Dot. The intervening Kit-to-Miri transfer is not narrated and is not invented.'},
 {'words':[659,675,704],'issue':'Ending calls the received dragon cutout a paper moth. It may continue the improved-moth nickname or reflect source inconsistency. Closing reference remains unresolved rather than inventing a cutout swap.'},
 {'words':[366,367,370,382,384],'issue':'Bell is only possibly among visitors and no junior-guide appointment is awarded.'},
 {'words':[127,129,133,668],'issue':'Torch return before closing is promised, not observed or judged broken.'},
 {'words':[436,438,440],'issue':'Faulty torch is a proposed excuse, not an observed failure or an actual false assertion to visitors.'},
 {'words':[12,473],'issue':'Two support books are not explicitly identical to the old books whose smell opens the story.'},
 {'words':[561,567],'issue':'Plate and saucer are comparison kinds, not objects introduced in the activity room or precise measured dimensions.'},
 {'words':[182,229,284,501],'issue':'Early trials confound moth and torch movement; first-trial torch movement is later acknowledged, without adding an exact path or assigning physical torch custody to Kit.'},
 ],
 'feature_gaps':[],
 'prompt_feedback':[
 'Keep depicted apparatus roles separate from physical objects while linking the representation to its carrier.',
 'A proposed false excuse is neither an actual fault nor a completed deception.',
 'When a source changes an object name or holder without a transition, retain the stated endpoints and mark the reference or transfer gap.',
 'Do not upgrade a short reaction such as Oh into explicit comprehension or endorsement of a later explanation.',
 'Comparisons using plates, wings and moons do not by themselves introduce physical comparison objects or literal animals.',
 ],
 'coverage_notes':'All 711 words in 34 paragraphs have explicit contextual POS and lemma, with sparse grammar, physical, mental, communication and narrative features from the full frozen v3 catalog. Whole-story retrospective interpretation has no causal filter.',
 'reviewed_all_words':True,
}
a.save(feedback)
review=[]
for p,para in enumerate(a.paragraphs):
 review.append(f'P{p}')
 for word in para['words']:
  w=word['w'];r=a.words[w]
  review.append(f"{w}:{r['token']} {r['pos']}/{r['lemma']} "+' '.join(str(r.get(k,'')) for k in ['entity_id','role','event','factuality','scope_id']))
(a.output/'review_words.txt').write_text('\n'.join(review)+'\n')
