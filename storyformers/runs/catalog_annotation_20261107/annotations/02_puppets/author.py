"""Manual whole-story puppet pilot. Every POS, lemma and anchor is authored."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation

a = Annotation('02_puppets', prompt_version='v0')

# One explicitly chosen POS=lemma pair per occurrence, in paragraph order.
LEXICAL = {
0: 'det=the n=puppet n=theatre adp=at n=Cedar n=School v=be adv=no adj=wide adp=than det=a n=closet conj=but conj=when det=its adj=red n=curtain v=close det=the n=cardboard n=moon v=look adj=enormous',
1: 'adp=at num=three adv=o’clock n=Nia v=be v=check det=every n=cue adp=on det=her n=list n=Ben v=be v=try part=to v=make det=the n=paper n=cloud v=sway conj=and n=Lila v=be v=crouch adp=behind det=the adj=little n=stage adp=with n=Mouse adp=on det=her n=hand n=Nia v=want part=to v=finish det=the n=rehearsal conj=before det=the n=caretaker v=lock det=the n=hall n=Ben v=want det=the n=moon n=scene part=to v=look adv=as adj=beautiful conj=as det=the n=scenery pron=he v=have v=paint n=Lila v=want det=the adj=final n=scene part=to v=go adv=perfectly adp=without pron=anyone v=notice pron=she',
2: 'n=Mouse v=bring det=the n=star n=Nia v=read adv=then det=the n=Moon v=say',
3: 'n=Lila v=reach adp=into n=Mouse adj=tiny n=pocket det=her n=finger v=find adv=only det=the n=lining',
4: 'det=the n=star adj=gone pron=she v=whisper',
5: 'pron=it v=be det=a adj=silver n=felt n=star adv=no adj=big adp=than det=a n=biscuit adp=with det=a n=loop adp=of adj=blue n=thread adp=at det=its n=tip n=Mouse v=be v=suppose part=to v=give pron=it adp=to det=the n=Moon pron=who v=have v=be adj=lonely adp=in det=the n=dark n=Lila v=have v=make det=the n=star pron=herself conj=and v=have v=carry pron=it adp=to n=school adp=in det=the n=prop n=tin',
6: 'adv=where v=do pron=you adv=last v=see pron=it n=Ben v=ask',
7: 'adp=on det=the n=windowsill adp=at n=lunch pron=I v=take pron=it adv=out part=to v=fix det=the n=loop n=Lila v=swallow adv=then det=the n=bell v=ring',
8: 'pron=they v=search det=the n=windowsill det=the n=radiator det=the n=prop n=tin conj=and det=the n=floor adp=beneath det=the n=stage n=Ben adv=even v=lift det=the n=cardboard n=cloud conj=though pron=he v=have v=glue pron=they adv=together det=that n=morning det=no n=star',
9: 'n=Nia v=glance adp=at det=her n=list det=the n=class v=be v=come adp=in num=five n=minute',
10: 'pron=we v=can v=skip det=the n=scene n=Lila v=say pron=she v=keep n=Mouse n=face v=turn adp=toward det=the n=floor pron=it v=will v=matter',
11: 'v=be det=the n=ending n=Ben v=say det=the n=Moon v=can v=be adj=lonely adv=forever',
12: 'n=Nia v=shut det=her n=list v=be det=a n=sewing n=kit adp=in n=Ms n=Rowan n=costume n=cupboard v=come adv=on',
13: 'n=Ms n=Rowan v=be v=sort det=a n=box adp=of adj=old n=scarf conj=when n=Nia v=explain pron=she v=hand adv=over det=a adj=green n=sewing n=tin conj=and det=a n=square adp=of adj=gray n=felt',
14: 'v=bring pron=it adv=back adp=with det=the n=needle pron=she v=say conj=and v=do v=cut det=the n=curtain part=to v=make det=a n=star',
15: 'pron=we v=promise n=Ben v=say',
16: 'adp=behind det=the n=stage n=Nia v=hold det=the n=felt conj=while n=Ben v=rummage adp=through det=the n=tin n=Lila v=find det=a n=brass n=button adp=with det=a adj=small n=flower v=stamp adp=on pron=it',
17: 'pron=we v=could v=sew pron=this adp=in det=the n=middle pron=she v=say',
18: 'v=be part=not adj=silver n=Ben v=point adv=out',
19: 'det=the n=Moon v=can v=have det=a adj=golden n=star n=Nia v=say pron=it v=might adv=even v=show adv=well',
20: 'n=Lila v=turn det=the n=button adv=over adp=in det=her n=palm pron=I v=do v=want pron=it part=to v=look conj=like pron=we v=forget det=the adj=real pron=one',
21: 'pron=we v=do v=forget v=say n=Nia pron=we v=lose pron=it',
22: 'pron=that v=make n=Lila v=smile adv=just det=a pron=little',
23: 'pron=they v=fold det=the n=felt conj=and v=cut det=a adj=lopsided n=star n=Nia v=thread det=the n=needle conj=but det=the n=thread v=fray adv=twice n=Ben v=hold det=the n=felt adj=tight conj=while n=Lila v=push det=the n=needle adv=through det=the n=button v=be adj=heavy conj=than pron=it v=look conj=when pron=they v=lift det=their adj=new n=star det=its n=point v=sag adv=down',
24: 'v=will v=flop adv=over n=Ben v=say',
25: 'n=Lila v=study n=Mouse n=pocket adv=then pron=it v=should v=go adp=in det=the n=pocket n=Mouse v=can v=hold pron=it adv=up adp=for det=the n=Moon part=to v=see',
26: 'conj=but det=the n=Moon v=be v=mean part=to v=keep pron=it n=Nia v=say',
27: 'n=Mouse v=can v=tuck pron=it adp=into det=the n=Moon n=lap n=Lila v=reply det=the n=button v=will v=face det=the n=audience',
28: 'pron=she v=stitch det=a n=loop adp=of n=thread adp=onto det=the n=star n=top conj=so n=Mouse v=could v=lift pron=it adp=without v=drop pron=it det=her adj=first n=knot v=come adj=loose pron=she v=try adv=again v=pull det=the n=thread adj=tight det=this n=time',
29: 'pron=they v=test det=the n=scene n=Mouse v=raise det=the n=star pron=it v=swing adv=sideways conj=and det=the n=button v=flash adp=toward det=the n=wall',
30: 'v=wait n=Lila v=say pron=she v=turn det=the n=star adv=around conj=and v=tie det=the n=loop adj=short adv=now',
31: 'n=Mouse v=lift pron=it adv=again det=the adj=gold n=button v=face det=the n=theatre',
32: 'n=Nia v=nod pron=that v=work',
33: 'det=the n=class v=file adp=into det=the adj=little n=theatre v=whisper conj=and v=bump n=knee n=Ben v=slip adp=behind det=the n=cardboard n=scenery n=Nia v=take det=her n=place adp=beside det=the n=curtain adp=with det=her n=cue n=list n=Lila v=hold n=Mouse adp=beneath det=the n=stage det=her n=hand v=tremble adv=enough part=to v=make det=his n=ear v=quiver',
34: 'det=the n=rehearsal v=begin n=Mouse v=cross det=the n=cardboard n=forest det=the n=Moon v=rise adp=above det=the v=paint n=hill',
35: 'adv=then v=come det=the adj=final n=scene',
36: 'n=Mouse v=bring det=the n=star n=Nia v=read',
37: 'n=Lila v=lift n=Mouse adp=for det=a n=moment det=her n=voice v=stay adj=trapped adp=in det=her n=throat pron=she v=could v=hear det=the n=room v=wait det=the adj=old adj=silver n=star v=be adj=gone det=this pron=one v=be adj=crooked adj=gray conj=and adj=bright adp=with det=a n=brass n=button',
38: 'pron=she v=could v=let n=Nia v=read det=the n=line adv=instead conj=or pron=she v=could v=make det=the n=scene det=her adj=own',
39: 'n=Lila v=draw det=a n=breath pron=I v=bring pron=you det=a adj=little n=light pron=she v=say part=not adp=in det=a n=whisper conj=but adp=in n=Mouse adj=clear adj=small n=voice',
40: 'det=the n=class v=lean adv=forward n=Mouse v=offer det=the n=star det=the n=Moon v=hold adv=out det=both n=felt n=hand conj=and n=Lila v=settle det=the n=star adp=in det=its n=lap',
41: 'pron=I v=can v=see det=my n=way adv=now n=Nia v=read adp=as det=the n=Moon',
42: 'n=Ben v=move det=the n=paper n=cloud det=the n=curtain v=begin part=to v=close',
43: 'adv=afterward n=Nia v=return det=the n=sewing n=tin adp=to n=Ms n=Rowan adp=with det=the n=needle v=tuck adv=safely adv=inside n=Lila v=keep n=Mouse adp=on det=her n=hand conj=as det=the num=three n=friend v=stand adp=in det=the adj=empty n=theatre adp=behind pron=they det=the adj=red n=curtain v=meet adp=in det=the n=middle adp=in det=the n=dimness det=the n=brass n=button adp=on det=the adj=new n=star v=catch num=one adj=last n=dot adp=of n=light',
}
for p, encoded in LEXICAL.items():
    pairs = [part.split('=', 1) for part in encoded.split()]
    words = a.paragraphs[p]['words']
    assert len(pairs) == len(words), (p, len(pairs), len(words))
    a.tag(p, [pos for pos, lemma in pairs], {word['w']: lemma for word, (_, lemma) in zip(words, pairs)})

# Entity IDs distinguish story-world characters from physical puppets and makers.
ENTITIES = [
('e1','Nia','person',[26,32,56,99,232,235,273,275,298,337,381,408,412,413,432,503,595,616,618,624,666,707,771,787]),
('e2','Ben','person',[34,68,80,180,216,223,265,332,342,371,441,472,610,776]),
('e3','Lila','person',[44,54,83,94,105,111,120,158,163,176,187,195,249,251,300,319,347,366,388,394,396,418,447,474,513,521,539,544,572,574,627,633,668,674,679,681,704,713,718,720,730,758,801,805]),
('e4','Ms. Rowan','person',[282,283,288,289,793,794]),
('e5','caretaker','person',[64]),
('e6','class audience','group',[238,520,600,685,743]),
('e7','three friends','group',[201,244,330,359,403,423,460,462,553,810,817]),
('e8','Cedar School','school',[4,5,169]),
('e9','puppet theatre','performance_space',[2,14,594,605,815]),
('e10','stage','stage',[50,215,336,632]),
('e11','red curtain','curtain',[16,325,622,782,820]),
('e12','Moon puppet','puppet_prop',[20,511,651,751,763]),
('e13','Moon character','fictional_character',[71,103,150,151,268,375,492,497,726,765,768,775]),
('e14','Mouse puppet','hand_puppet',[52,108,253,476,485,505,532,557,585,629,639,645,670,746,803]),
('e15','Mouse character','fictional_character',[95,142,662,724,738]),
('e16','original silver felt star','star_prop',[118,122,127,140,147,162,167,179,189,231,407,415,690]),
('e17','replacement gray star','star_prop',[380,383,399,431,464,465,469,479,488,502,508,529,535,538,560,561,577,587,694,749,761,834]),
('e18','gift star in the play','fictional_object',[98,665,729]),
('e19','cue list','document',[30,33,236,276,625,626]),
('e20','paper cloud scenery','scenery_props',[41,221,226,780]),
('e21','painted scenery','scenery_props',[79,615]),
('e22','rehearsal','performance_event',[61,643]),
('e23','final scene','script_scene',[72,87,248,262,264,556,661,717]),
('e24','hall','room',[67]),
('e25','Mouse pocket','puppet_part',[110,477,484]),
('e26','Lila hands','body_part_group',[55,634,806]),
('e27','Lila fingers','body_part_group',[112]),
('e28','Lila palm','body_part',[395]),
('e29','Mouse face','puppet_part',[254]),
('e30','Mouse ears','puppet_part_group',[640]),
('e31','pocket lining','fabric_part',[116]),
('e32','original blue loop','thread_loop',[135,194]),
('e33','original blue thread','thread',[138]),
('e34','original star tip','prop_part',[141]),
('e35','windowsill','surface',[184,204]),
('e36','radiator','radiator',[206]),
('e37','prop tin','container',[173,209]),
('e38','floor','surface',[212,258]),
('e39','school bell','bell',[199]),
('e40','sewing kit tin','sewing_kit_container',[280,306,314,346,791]),
('e41','costume cupboard','cupboard',[285]),
('e42','scarf box','container',[293]),
('e43','old scarves','garment_group',[296]),
('e44','gray felt material','fabric',[309,312,340,426,444]),
('e45','needle','sewing_needle',[318,435,450,797]),
('e46','brass flower button','button',[351,358,362,368,391,453,457,516,566,591,703,830]),
('e47','stamped flower image','depicted_flower',[355]),
('e48','new sewing thread','thread',[438,526,549]),
('e49','new lifting loop','thread_loop',[524,582]),
('e50','replacement star upper point','prop_part',[466,530]),
('e51','first knot','knot',[541]),
('e52','wall','surface',[570]),
('e53','Moon lap','puppet_part',[512,764]),
('e54','Moon felt hands','puppet_part_group',[756]),
('e55','cardboard forest','scenery_prop',[649]),
('e56','painted hills','scenery_props',[656]),
('e57','Lila voice','voice',[675]),
('e58','Lila throat','body_part',[680]),
('e59','scripted line','utterance_text',[710]),
('e60','Mouse performance voice','character_voice',[741]),
('e61','reflected light','light',[838,840]),
('e62','cue instructions on Nia’s list','instruction_set',[30]),
('e63','Lila hands together','body_part_group',[634]),
]
# Pronouns after Ms Rowan's handover: she refers to Rowan, not Lila.
ENTITIES[2][3].remove(300); ENTITIES[2][3].remove(319)
ENTITIES[3][3].extend([300,319])
ENTITIES[18][3].remove(30)
ENTITIES[18][3].remove(625)
ENTITIES[25][3].remove(634)
for word in [408,413]:
    ENTITIES[0][3].remove(word)
    ENTITIES[6][3].append(word)
for eid,name,kind,mentions in ENTITIES:
    if eid=='e26': name,kind='Lila’s puppet-bearing hand','body_part'
    a.entity(eid,name,kind,mentions)
a.entities['e63']['known_member_ids']=['e26']
a.entities['e7']['member_ids']=['e1','e2','e3']
a.entities['e12'].update(represents='e13', physical_manipulator='unknown', voice_performer='e1')
a.entities['e14'].update(represents='e15', performer='e3')
a.entities['e17'].update(replaces='e16', material_source='e44', incorporates=['e46','e49'])
a.entities['e18'].update(realizations=['e16','e17'], semantic_world='w_play')

# New representational relation: neither physical control nor ordinary identity
# equates a performer, their puppet and the character enacted by that puppet.
a.extension('enactment','object','Correlated performer, physical prop and represented character/object identities within a named performance world. Unknown performer may be omitted.','staged mention or event','Existing identity, event_control and semantic_world_id do not express the representation relation among three distinct participants.',{'performer_id':'e3','prop_id':'e14','character_id':'e15','world_id':'w_play'})
a.extension('appearance_color','object','Entity-bound perceived surface color, explicitly distinguished from material composition; assertion_status records evidence attribution, while factuality preserves negated or proposed color.','color-bearing mention','The catalog has material_composition but no typed color dimension; legacy attributes can store color only as an unbound string.',{'entity_id':'e46','scope_id':'s0','value':'gold','assertion_status':'asserted','factuality':'asserted'})
a.extension('part_whole_relation','object','Bound part entity, whole entity and physical or represented-world scope.','part mention','Lexical part types do not establish token-level actual part ownership; bridging_relation is reference licensing rather than the actual relation.',{'part_id':'e25','whole_id':'e14','scope_id':'s0'})

# Scope inventory is retrospective and deliberately not a causal training set.
QUOTES = [
('q1',95,99,'e1','Read stage direction about Mouse; scripted content.'),
('q2',101,105,'e1','Read unfinished Moon cue; interrupted before content.'),
('q3',117,120,'e3','Lila reports the missing original star.'),
('q4',174,180,'e2','Ben asks Lila for its last known location.'),
('q5',182,195,'e3','Lila recalls the windowsill and intended loop repair.'),
('q6',197,201,'e3','Lila recalls the school bell ringing.'),
('q7',237,244,'e1','Nia warns of the class arrival deadline.'),
('q8',244,249,'e3','Lila proposes omitting the scene.'),
('q9',259,262,'e3','Lila claims omission would not matter.'),
('q10',262,265,'e2','Ben identifies the scene as the ending.'),
('q11',267,273,'e2','Ben insists on resolving the fictional Moon loneliness.'),
('q12',277,288,'e1','Nia identifies sewing resources and urges movement.'),
('q13',313,319,'e4','Rowan requests return of tin and needle.'),
('q14',321,330,'e4','Rowan prohibits cutting the curtain for the replacement.'),
('q15',330,332,'e2','Ben promises on behalf of the group.'),
('q16',359,366,'e3','Lila suggests sewing the found button onto the replacement.'),
('q17',368,371,'e2','Ben contrasts the brass button with the old silver star.'),
('q18',374,381,'e1','Nia suggests changing the fictional gift to golden.'),
('q19',383,388,'e1','Nia suggests greater visibility as a possibility.'),
('q20',396,408,'e3','Lila does not want the replacement to suggest forgetting.'),
('q21',408,411,'e1','Nia denies forgetting.'),
('q22',413,416,'e1','Nia reframes the problem as loss.'),
('q23',469,472,'e2','Ben predicts the new star will flop.'),
('q24',478,495,'e3','Lila proposes a revised handling plan.'),
('q25',495,503,'e1','Nia recalls the intended gift-retention requirement.'),
('q26',505,513,'e3','Lila proposes tucking the star into the Moon lap.'),
('q27',515,521,'e3','Lila predicts the button will face the audience.'),
('q28',571,572,'e3','Lila pauses the test.'),
('q29',584,585,'e3','Lila cues the repeated test.'),
('q30',597,599,'e1','Nia accepts the working arrangement.'),
('q31',662,666,'e1','Repeated stage-direction reading during final rehearsal.'),
('q32',724,730,'e15','Mouse character speaks, voiced by Lila.'),
('q33',765,771,'e13','Moon character speaks, voiced by Nia.'),
]
for sid,start,end,holder,desc in QUOTES:
    a.scope(sid,range(start,end),kind='quotation',holder_id=holder,description=desc)
    a.feature(range(start,end),quote_mode='direct')
# Embedded goal/anticipated-event/fiction scopes override their parent span.
for sid,lo,hi,kind,holder,parent,desc in [
('g1',58,68,'desired','e1','s0','Finishing before an anticipated hall closure, not an observed locking.'),
('g2',70,80,'desired','e2','s0','Ben wants an aesthetically successful scene.'),
('g3',85,95,'desired','e3','s0','Perfect final scene while Lila avoids being noticed.'),
('playback',142,158,'fictional_backstory','e13','s0','Scripted gift and lonely Moon; not a real astronomical moon feeling lonely.'),
('m1',704,712,'considered_alternative','e3','s0','Let Nia read: considered, not chosen.'),
('m2',713,720,'considered_alternative','e3','s0','Take ownership of performing: subsequently enacted, but still an option here.'),
('attempt1',37,43,'attempted_complement','e2','s0','Desired cloud movement under trying; successful sway is not yet asserted.'),
('repair_goal',191,195,'purpose','e3','q5','Fixing the old loop was the reason for taking the star out; completion is unknown.'),
('appearance',400,408,'hypothetical_appearance','e3','q20','Possible appearance of forgetting that Lila wants to avoid.'),
('lift_goal',531,539,'purpose','e3','s0','Intended loop-enabled lifting without dropping, not a report of a completed lift.'),
]: a.scope(sid,range(lo,hi),kind=kind,holder_id=holder,parent=parent,description=desc)
a.scope('play_action',[],kind='fictional_performance',parent='s0',description='Represented events enacted during the physical rehearsal, distinct from prop manipulation.')
for ids in [range(95,99),range(101,105),range(142,158),range(662,666),range(724,730),range(765,771)]:
    a.feature(ids,semantic_world_id='w_play',evidence_world_status='fictional_substory')
a.feature(range(724,730),enactment={'performer_id':'e3','character_id':'e15','prop_id':'e14','world_id':'w_play'},evidence=[720,724,730,738,741],note='The actual speaker is Lila; first-person I is the Mouse character. Speaker_id retains enacted speaker; enactment retains physical speaker.')
a.feature(range(765,771),enactment={'performer_id':'e1','character_id':'e13','prop_id':'e12','world_id':'w_play'},evidence=[771,772,774,775],note='Nia voices the Moon. Physical manipulation of the Moon is not assigned to Nia merely from this line.')

# Small direct-authoring conveniences; these do not infer semantics from words.
def F(w, **fields): a.feature(w, **fields)
def B(entity,value,scope='s0',status='asserted'):
    bundle={'entity_id':entity,'scope_id':scope,'assertion_status':status,'value':value}
    if status not in {'asserted','attributed_claim','candidate'}:
        bundle.update(assertion_status='attributed_claim' if scope.startswith('q') else 'asserted',interpretation_status=status)
    return bundle
def E(n,w,label,actor=None,patients=(),type='other',factuality='asserted',scope=None,roles=None,**fields):
    a.event(f'ev{n}',w,label,type=type,actor=actor,patients=patients,factuality=factuality,scope=scope,roles=roles,**fields)
def P(n,text,words,scope='s0',**kw): a.proposition(f'p{n}',text,words,scope_id=scope,**kw)

# Propositions anchor mental, dialogue, plan and narrative labels.
PROPS = [
(1,'The original star is missing; its current location remains unknown.',[118,119,231,690,692]),
(2,'The rehearsal finishes before the caretaker locks the hall.',[56,57,59,61,62,65,67]),
(3,'The moon scene looks as beautiful as the painted scenery.',[68,69,72,74,76,79,82]),
(4,'The final scene goes perfectly without anyone noticing Lila.',[83,84,87,90,91,92,93,94]),
(5,'Mouse gives the star to the Moon in the play.',[142,146,147,150]),
(6,'The fictional Moon was lonely before receiving a gift.',[150,151,154,157]),
(7,'The original star was last seen on the windowsill at lunch, according to Lila.',[174,178,184,186,187,188,189]),
(8,'The original star’s loop is repaired.',[187,188,189,192,194]),
(9,'The class is expected in five minutes.',[237,238,240,242,243]),
(10,'The group could skip the final scene.',[244,245,246,248]),
(11,'Lila claims skipping the scene will not matter.',[259,260,261]),
(12,'Ben insists the ending should resolve the Moon loneliness.',[262,264,268,269,271,272]),
(13,'The sewing kit is in Rowan’s costume cupboard.',[277,280,281,283,285]),
(14,'Return the sewing tin with the needle to Rowan.',[313,314,318,319]),
(15,'Do not cut the curtain to make a replacement star.',[322,323,325,327,329]),
(16,'The group returns the tin and needle and does not cut the curtain to make a star.',[330,331,313,318,322,325]),
(17,'Sew the brass button in the replacement star’s middle.',[359,361,362,365]),
(18,'The brass button is not silver-colored.',[368,369,370]),
(19,'The Moon could receive a golden-looking replacement star.',[375,376,377,379,380]),
(20,'The replacement may show better on stage.',[383,384,386,387]),
(21,'The replacement looks as though the friends forgot the original star.',[396,398,399,401,403,404,407]),
(22,'Nia denies they forgot the original.',[408,409,410]),
(23,'Nia says they lost the original.',[413,414,415]),
(24,'The new star’s top sags under the heavy button.',[453,455,464,466,467]),
(25,'Ben predicts the new star will flop.',[469,470,471]),
(26,'Use visible holding rather than Mouse’s pocket.',[479,480,481,484,485,487,488,492,494]),
(27,'The Moon is meant to keep the gift.',[497,499,501,502]),
(28,'Tuck the star into the Moon lap with the button facing the audience.',[505,507,508,511,512,516,518,520]),
(29,'The loop should permit lifting without dropping.',[522,524,529,532,534,535,536,537,538]),
(30,'The first test turns the button toward the wall.',[560,562,566,567,570]),
(31,'The corrected loop presents the gold button to the theatre.',[575,577,580,582,583,586,590,591,592,594]),
(32,'Nia endorses the corrected arrangement as working.',[595,596,597,598]),
(33,'Lila’s hands tremble and make Mouse’s ears quiver.',[627,634,635,638,640,641]),
(34,'Lila could let Nia read the line instead.',[704,705,706,707,708,710]),
(35,'Lila could make the scene her own.',[713,714,715,717,718,719]),
(36,'Mouse says he brought the Moon a little light.',[724,725,726,729]),
(37,'The Moon says it can see its way now.',[765,766,767,768,769,770]),
(38,'Nia returns the tin with the needle inside.',[787,788,791,794,797,798,800]),
(39,'The replacement star is used successfully in the final scene.',[746,747,749,751,752,756,758,759,761,764]),
(40,'The original is still missing, but the replacement preserves the ending.',[690,692,694,696,697,703,747,761]),
(41,'Lila speaks clearly as Mouse rather than retreating into a whisper.',[720,724,730,731,732,735,738,739,741]),
(42,'The final reflected light on the new star supplies a concrete ending image.',[819,820,821,827,830,834,835,838,840]),
]
for n,text,words in PROPS:
    scope = {2:'g1',3:'g2',4:'g3',5:'playback',6:'playback',7:'q5',8:'repair_goal',9:'q7',10:'q8',11:'q9',12:'q11',13:'q12',14:'q13',15:'q14',16:'q15',17:'q16',18:'q17',19:'q18',20:'q19',21:'appearance',22:'q21',23:'q22',25:'q23',26:'q24',27:'q25',28:'q26',32:'q30',34:'m1',35:'m2',36:'q32',37:'q33'}.get(n,'s0')
    P(n,text,words,scope)

# Predicate occurrences, including narrated states and explicitly scoped options.
# The actor is semantic doer/experiencer, not necessarily the grammatical subject.
EVENT_ROWS = [
(1,6,'theatre is closet-sized',None,['e9'],'state','asserted'),
(2,17,'curtain closes',None,['e11'],'move','asserted'),
(3,21,'cardboard moon appears enormous',None,['e12'],'state','asserted'),
(4,28,'Nia checks cues','e1',['e62'],'other','asserted'),
(5,36,'Ben attempts cloud movement','e2',['e20'],'other','asserted'),
(6,38,'Ben tries to cause cloud sway','e2',['e20'],'move','desired'),
(7,42,'paper clouds sway',None,['e20'],'move','desired'),
(8,46,'Lila crouches behind stage','e3',[],'state','asserted'),
(9,57,'Nia wants timely rehearsal','e1',[],'feel','asserted'),
(10,59,'finish rehearsal before hall closure','e1',['e22'],'other','desired'),
(11,65,'anticipated caretaker locks hall','e5',['e24'],'other','hypothetical'),
(12,69,'Ben wants beautiful scene','e2',[],'feel','asserted'),
(13,74,'scene looks beautiful',None,['e23'],'state','desired'),
(14,82,'Ben painted scenery','e2',['e21'],'other','asserted'),
(15,84,'Lila wants unobtrusive perfect scene','e3',[],'feel','asserted'),
(16,89,'final scene goes perfectly',None,['e23'],'other','desired'),
(17,93,'someone notices Lila',None,['e3'],'perceive','negated'),
(18,96,'scripted Mouse brings star','e15',['e18'],'transfer','reported'),
(19,100,'Nia reads first stage directions','e1',[],'speak','asserted'),
(20,104,'scripted Moon speech cue','e13',[],'speak','reported'),
(21,106,'Lila reaches into Mouse pocket','e3',['e25'],'move','asserted'),
(22,113,'Lila feels only lining','e3',['e31'],'perceive','asserted'),
(23,119,'original star is missing',None,['e16'],'state','reported'),
(24,121,'Lila whispers discovery','e3',[],'speak','asserted'),
(25,123,'original star is described',None,['e16'],'state','asserted'),
(26,144,'script expects gift transfer',None,['e18'],'state','reported'),
(27,146,'Mouse intended to give star to Moon','e15',['e18'],'transfer','desired'),
(28,154,'Moon was lonely','e13',[],'feel','reported'),
(29,160,'Lila made original star','e3',['e16'],'other','asserted'),
(30,166,'Lila carried original star to school','e3',['e16'],'move','asserted'),
(31,178,'Lila last saw original star','e3',['e16'],'perceive','hypothetical'),
(32,181,'Ben asks last known star location','e2',[],'speak','asserted'),
(33,188,'Lila reports taking original star out','e3',['e16'],'move','reported'),
(34,192,'Lila intended to fix old loop','e3',['e32'],'repair','desired'),
(35,196,'Lila swallows','e3',[],'other','asserted'),
(36,200,'school bell rang',None,['e39'],'other','reported'),
(37,202,'friends search for missing star','e7',['e16'],'perceive','asserted'),
(38,218,'Ben lifts cloud scenery','e2',['e20'],'move','asserted'),
(39,225,'Ben had glued clouds together','e2',['e20'],'other','asserted'),
(40,231,'search does not find original star',None,['e16'],'state','negated'),
(41,233,'Nia glances at cue list','e1',['e19'],'perceive','asserted'),
(42,240,'class arrival is imminent','e6',[],'move','reported'),
(43,246,'friends could skip final scene','e7',['e23'],'other','hypothetical'),
(44,250,'Lila proposes omission','e3',[],'speak','asserted'),
(45,252,'Lila keeps Mouse face down','e3',['e29'],'state','asserted'),
(46,255,'Mouse face remains turned toward floor',None,['e29'],'state','asserted'),
(47,261,'omission would not matter',None,[],'state','negated'),
(48,262,'scene is the ending',None,['e23'],'state','reported'),
(49,266,'Ben objects to omission','e2',[],'speak','asserted'),
(50,271,'Moon must not remain lonely','e13',[],'feel','negated'),
(51,274,'Nia shuts cue list','e1',['e19'],'move','asserted'),
(52,277,'kit exists in costume cupboard',None,['e40'],'state','reported'),
(53,286,'Nia urges friends to come','e7',[],'move','desired'),
(54,291,'Rowan sorts old scarves','e4',['e43'],'other','asserted'),
(55,299,'Nia explains situation to Rowan','e1',[],'speak','asserted'),
(56,301,'Rowan hands over sewing kit and felt','e4',['e40','e44'],'transfer','asserted'),
(57,313,'return tin and needle to Rowan','e7',['e40','e45'],'transfer','desired'),
(58,320,'Rowan gives return and cutting instructions','e4',[],'speak','asserted'),
(59,323,'cutting curtain is prohibited','e7',['e11'],'other','negated'),
(60,327,'make star from curtain','e7',[],'other','hypothetical'),
(61,331,'group undertakes return and care commitment','e7',[],'other','asserted'),
(62,333,'Ben voices group promise','e2',[],'speak','asserted'),
(63,338,'Nia holds gray felt','e1',['e44'],'state','asserted'),
(64,343,'Ben rummages in sewing tin','e2',['e40'],'other','asserted'),
(65,348,'Lila finds brass flower button','e3',['e46'],'obtain','asserted'),
(66,356,'flower was stamped on button',None,['e46'],'other','asserted'),
(67,361,'friends could sew button onto star','e7',['e46','e17'],'other','hypothetical'),
(68,367,'Lila proposes button decoration','e3',[],'speak','asserted'),
(69,368,'button is not silver-colored',None,['e46'],'state','negated'),
(70,372,'Ben points out color difference','e2',[],'speak','asserted'),
(71,377,'Moon could have golden star','e13',['e18'],'state','hypothetical'),
(72,382,'Nia proposes golden gift','e1',[],'speak','asserted'),
(73,386,'replacement might be more visible',None,['e17'],'state','hypothetical'),
(74,389,'Lila turns button in palm','e3',['e46'],'move','asserted'),
(75,398,'Lila rejects appearance of forgetting','e3',[],'feel','negated'),
(76,401,'replacement could suggest forgetting',None,['e17'],'state','hypothetical'),
(77,404,'friends forgetting is imagined appearance','e7',['e16'],'other','hypothetical'),
(78,410,'friends did not forget original','e7',['e16'],'other','negated'),
(79,411,'Nia corrects forgetting frame','e1',[],'speak','asserted'),
(80,414,'friends lost original','e7',['e16'],'other','reported'),
(81,417,'Nia correction causes Lila to smile',None,['e3'],'other','asserted'),
(82,419,'Lila smiles','e3',[],'other','asserted'),
(83,424,'friends fold gray felt','e7',['e44'],'other','asserted'),
(84,428,'friends cut replacement star','e7',['e44','e17'],'other','asserted'),
(85,433,'Nia threads needle','e1',['e45','e48'],'other','asserted'),
(86,439,'thread frays twice',None,['e48'],'other','asserted'),
(87,442,'Ben holds felt taut','e2',['e44'],'state','asserted'),
(88,448,'Lila pushes needle through felt','e3',['e45','e44'],'other','asserted'),
(89,454,'button is heavier than appearance',None,['e46'],'state','asserted'),
(90,458,'button appears lighter than actual weight',None,['e46'],'state','asserted'),
(91,461,'friends lift new star','e7',['e17'],'move','asserted'),
(92,467,'new star upper point sags',None,['e50'],'move','asserted'),
(93,470,'star predicted to flop',None,['e17'],'move','hypothetical'),
(94,473,'Ben predicts flopping','e2',[],'speak','asserted'),
(95,475,'Lila studies Mouse pocket','e3',['e25'],'perceive','asserted'),
(96,481,'star should not go in pocket',None,['e17'],'move','negated'),
(97,487,'Mouse could hold star up','e14',['e17'],'state','hypothetical'),
(98,494,'Moon can see displayed gift','e13',['e18'],'perceive','hypothetical'),
(99,499,'Moon is intended to keep gift',None,['e13'],'state','reported'),
(100,501,'Moon keeps gift in play','e13',['e18'],'state','desired'),
(101,504,'Nia reminds of ending requirement','e1',[],'speak','asserted'),
(102,507,'Mouse could tuck star into Moon lap','e14',['e17'],'move','hypothetical'),
(103,514,'Lila proposes lap placement','e3',[],'speak','asserted'),
(104,518,'button will face audience',None,['e46'],'state','hypothetical'),
(105,522,'Lila stitches lifting loop to new star','e3',['e17','e49'],'other','asserted'),
(106,534,'Mouse can lift new star using loop','e14',['e17'],'move','hypothetical'),
(107,537,'dropping star is to be avoided','e14',['e17'],'move','negated'),
(108,542,'first knot loosens',None,['e51'],'other','asserted'),
(109,545,'Lila retries tying knot','e3',['e48'],'other','asserted'),
(110,547,'Lila pulls thread tight','e3',['e48'],'other','asserted'),
(111,554,'friends test revised final scene','e7',['e23'],'other','asserted'),
(112,558,'Mouse puppet raises new star','e14',['e17'],'move','asserted'),
(113,562,'new star swings sideways',None,['e17'],'move','asserted'),
(114,567,'button reflects light toward wall',None,['e46'],'other','asserted'),
(115,571,'Lila asks friends to pause','e7',[],'other','desired'),
(116,573,'Lila says wait','e3',[],'speak','asserted'),
(117,575,'Lila turns star around','e3',['e17'],'move','asserted'),
(118,580,'Lila reties lifting loop shorter','e3',['e49'],'repair','asserted'),
(119,584,'Lila cues second test','e3',[],'speak','asserted'),
(120,586,'Mouse puppet lifts star again','e14',['e17'],'move','asserted'),
(121,592,'gold-looking button faces theatre',None,['e46'],'state','asserted'),
(122,596,'Nia nods acceptance','e1',[],'other','asserted'),
(123,598,'corrected arrangement works',None,['e17'],'state','reported'),
(124,601,'class enters theatre','e6',[],'move','asserted'),
(125,606,'class whispers','e6',[],'speak','asserted'),
(126,608,'class members bump knees','e6',[],'other','asserted'),
(127,611,'Ben moves behind scenery','e2',[],'move','asserted'),
(128,617,'Nia takes position beside curtain','e1',[],'move','asserted'),
(129,628,'Lila holds Mouse below stage','e3',['e14'],'state','asserted'),
(130,635,'Lila hands tremble',None,['e63'],'move','asserted'),
(131,638,'trembling hands cause puppet ears to quiver',None,['e30'],'other','asserted'),
(132,641,'Mouse ears quiver',None,['e30'],'move','asserted'),
(133,644,'rehearsal begins',None,['e22'],'other','asserted'),
(134,646,'Mouse crosses cardboard forest','e14',[],'move','asserted'),
(135,652,'Moon puppet rises above hills',None,['e12'],'move','asserted'),
(136,655,'hills are painted scenery',None,['e56'],'state','asserted'),
(137,658,'final scene arrives in sequence',None,['e23'],'other','asserted'),
(138,663,'Mouse brings star in repeated stage direction','e15',['e18'],'transfer','reported'),
(139,667,'Nia reads final-scene direction','e1',[],'speak','asserted'),
(140,669,'Lila lifts Mouse','e3',['e14'],'move','asserted'),
(141,676,'Lila voice remains trapped metaphorically','e3',['e57'],'state','asserted'),
(142,683,'Lila hears waiting audience','e3',['e6'],'perceive','asserted'),
(143,686,'audience waits','e6',[],'state','asserted'),
(144,692,'original silver star is still missing',None,['e16'],'state','asserted'),
(145,695,'replacement is crooked gray and bright',None,['e17'],'state','asserted'),
(146,706,'Lila could let Nia read','e3',[],'other','hypothetical'),
(147,708,'Nia could read Lila line','e1',['e59'],'speak','hypothetical'),
(148,715,'Lila could own her performance','e3',['e23'],'other','hypothetical'),
(149,721,'Lila draws breath','e3',[],'other','asserted'),
(150,725,'Mouse tells Moon he brought light','e15',['e18'],'transfer','reported'),
(151,731,'Lila speaks as Mouse','e3',[],'speak','asserted'),
(152,744,'class leans forward','e6',[],'move','asserted'),
(153,747,'Mouse offers new star','e14',['e17'],'transfer','asserted'),
(154,752,'Moon puppet holds felt hands out',None,['e54'],'move','asserted'),
(155,759,'Lila settles star in Moon lap','e3',['e17'],'move','asserted'),
(156,767,'Moon says it can see its way','e13',[],'perceive','reported'),
(157,772,'Nia reads as Moon','e1',[],'speak','asserted'),
(158,777,'Ben moves paper clouds','e2',['e20'],'move','asserted'),
(159,783,'curtain starts closing',None,['e11'],'move','asserted'),
(160,785,'curtain closes',None,['e11'],'move','asserted'),
(161,788,'Nia returns sewing tin and needle','e1',['e40','e45'],'transfer','asserted'),
(162,798,'needle is tucked inside tin',None,['e45'],'state','asserted'),
(163,802,'Lila keeps Mouse on hand','e3',['e14'],'state','asserted'),
(164,811,'three friends stand in empty theatre','e7',[],'state','asserted'),
(165,821,'red curtain meets at middle',None,['e11'],'move','asserted'),
(166,835,'brass button catches final reflected light',None,['e46'],'other','asserted'),
]
for n,w,label,actor,patients,typ,fact in EVENT_ROWS:
    if n not in {26,99,138}:  # modal operators and repeated reference, not new events
        E(n,w,label,actor,patients,typ,fact)
a.mention_event('ev27',144,role='modifier',note='Supposed to scopes the intended gift event.')
a.mention_event('ev100',499,role='modifier',note='Meant to scopes keeping the gift; not another physical state event.')
a.mention_event('ev18',663,role='action',note='A second utterance of the same scripted gift direction; actual reading ev139 is new.')

# Explicit participant mention associations. Several mentions participate in two
# events; event_bindings retains both without blanketing a whole clause.
ROLE_BINDINGS = {
1:{'patient':[2]},2:{'patient':[16]},3:{'patient':[20],'modifier':[22]},
4:{'actor':[26],'patient':[30],'location':[33]},5:{'actor':[34],'patient':[41]},6:{'actor':[34],'patient':[41]},7:{'patient':[41]},8:{'actor':[44],'location':[50]},
9:{'actor':[56]},10:{'actor':[56],'patient':[61]},11:{'actor':[64],'patient':[67]},12:{'actor':[68]},13:{'patient':[72],'modifier':[76]},14:{'actor':[80],'patient':[79]},15:{'actor':[83]},16:{'patient':[87],'modifier':[90]},17:{'patient':[94]},
18:{'actor':[95],'patient':[98]},19:{'actor':[99]},20:{'actor':[103]},21:{'actor':[105],'location':[110]},22:{'actor':[111],'instrument':[112],'patient':[116]},23:{'patient':[118]},24:{'actor':[120]},25:{'patient':[122,127]},27:{'actor':[142],'patient':[147],'recipient':[150]},28:{'actor':[151]},29:{'actor':[158,163],'patient':[162]},30:{'actor':[158],'patient':[167],'location':[169,173]},
31:{'actor':[176],'patient':[179]},32:{'actor':[180]},33:{'actor':[187],'patient':[189],'location':[184]},34:{'actor':[187],'patient':[194]},35:{'actor':[195]},36:{'patient':[199]},37:{'actor':[201],'location':[204,206,209,212,215]},38:{'actor':[216],'patient':[221]},39:{'actor':[223],'patient':[226]},40:{'patient':[231]},41:{'actor':[232],'patient':[236]},42:{'actor':[238],'modifier':[242,243]},
43:{'actor':[244],'patient':[248]},44:{'actor':[249]},45:{'actor':[251],'patient':[254]},46:{'patient':[254],'location':[258]},47:{'other':[259]},48:{'patient':[262,264]},49:{'actor':[265]},50:{'actor':[268],'modifier':[272]},51:{'actor':[273],'patient':[276]},52:{'patient':[280],'location':[285]},53:{'other':[287]},54:{'actor':[288,289],'patient':[296],'location':[293]},55:{'actor':[298]},56:{'actor':[300],'patient':[306,312]},57:{'patient':[314,318]},58:{'actor':[319]},59:{'patient':[325]},61:{'actor':[330]},62:{'actor':[332]},
63:{'actor':[337],'patient':[340],'location':[336]},64:{'actor':[342],'location':[346]},65:{'actor':[347],'patient':[351]},66:{'patient':[355],'location':[358]},67:{'actor':[359],'patient':[362],'location':[365]},68:{'actor':[366]},69:{'patient':[368],'modifier':[370]},70:{'actor':[371]},71:{'actor':[375],'patient':[380]},72:{'actor':[381]},73:{'patient':[383],'modifier':[387]},74:{'actor':[388],'patient':[391],'location':[395]},75:{'actor':[396]},76:{'patient':[399]},77:{'actor':[403],'patient':[407]},78:{'actor':[408]},79:{'actor':[412]},80:{'actor':[413],'patient':[415]},81:{'other':[416],'patient':[418]},82:{'actor':[418],'modifier':[420,422]},
83:{'actor':[423],'patient':[426]},84:{'actor':[423],'patient':[431]},85:{'actor':[432],'patient':[435],'instrument':[438]},86:{'patient':[438],'modifier':[440]},87:{'actor':[441],'patient':[444],'modifier':[445]},88:{'actor':[447],'patient':[444],'instrument':[450]},89:{'patient':[453],'modifier':[455]},90:{'patient':[457]},91:{'actor':[460],'patient':[464]},92:{'patient':[466],'modifier':[468]},93:{'patient':[469]},94:{'actor':[472]},95:{'actor':[474],'patient':[477]},96:{'patient':[479],'location':[484]},97:{'actor':[485],'patient':[488]},98:{'actor':[492]},99:{'patient':[497]},100:{'actor':[497],'patient':[502]},101:{'actor':[503]},102:{'actor':[505],'patient':[508],'location':[512]},103:{'actor':[513]},104:{'patient':[516],'location':[520]},
105:{'actor':[521],'patient':[524,529],'instrument':[526]},106:{'actor':[532],'patient':[535]},107:{'actor':[532],'patient':[538]},108:{'patient':[541],'modifier':[543]},109:{'actor':[544],'modifier':[546]},110:{'actor':[544],'patient':[549],'modifier':[550]},111:{'actor':[553],'patient':[556]},112:{'actor':[557],'patient':[560]},113:{'patient':[561],'modifier':[563]},114:{'patient':[566],'location':[570]},116:{'actor':[572]},117:{'actor':[574],'patient':[577]},118:{'actor':[574],'patient':[582],'modifier':[583]},120:{'actor':[585],'patient':[587]},121:{'patient':[591],'location':[594]},122:{'actor':[595]},123:{'other':[597]},
124:{'actor':[600],'location':[605]},125:{'actor':[600]},126:{'actor':[600],'patient':[609]},127:{'actor':[610],'location':[615]},128:{'actor':[616],'location':[619,622]},129:{'actor':[627],'patient':[629],'location':[632]},130:{'patient':[634]},131:{'patient':[640]},132:{'patient':[640]},133:{'patient':[643]},134:{'actor':[645],'location':[649]},135:{'patient':[651],'location':[656]},136:{'patient':[656]},137:{'patient':[661]},138:{'actor':[662],'patient':[665]},139:{'actor':[666]},140:{'actor':[668],'patient':[670]},141:{'actor':[674],'patient':[675],'location':[680]},142:{'actor':[681],'patient':[685]},143:{'actor':[685]},144:{'patient':[690]},145:{'patient':[694],'modifier':[696,697,699]},146:{'actor':[704]},147:{'actor':[707],'patient':[710]},148:{'actor':[713],'patient':[717]},149:{'actor':[720],'patient':[723]},150:{'actor':[724],'recipient':[726],'patient':[729]},151:{'actor':[730],'modifier':[735,739,740,741]},152:{'actor':[743]},153:{'actor':[746],'patient':[749]},154:{'patient':[756]},155:{'actor':[758],'patient':[761],'location':[764]},156:{'actor':[765],'patient':[769]},157:{'actor':[771]},158:{'actor':[776],'patient':[780]},159:{'patient':[782]},160:{'patient':[782]},161:{'actor':[787],'patient':[791,797],'recipient':[793,794]},162:{'patient':[797],'location':[791]},163:{'actor':[801],'patient':[803],'location':[806]},164:{'actor':[810],'location':[815]},165:{'patient':[820],'location':[824]},166:{'patient':[830],'other':[838,840]},
}
for n, roles in ROLE_BINDINGS.items():
    if n == 99: continue
    if n == 138: n = 18
    ev=a.events[f'ev{n}']
    for role, words in roles.items():
        for w in words:
            a._binding(w,ev['event_id'],role,a.words[w]['scope_id'])
            if 'event_id' not in a.words[w]: F(w,event_id=ev['event_id'],event=ev['event'],role=role)
# Receiver and tool participants are specified explicitly, including fictional gifts.
for n,recipient in [(27,'e13'),(56,'e7'),(57,'e4'),(150,'e13'),(153,'e12'),(161,'e4')]:
    a.events[f'ev{n}']['recipient_id']=recipient
    F(a.events[f'ev{n}']['trigger'],recipient_id=recipient)
for n,tools in [(22,['e27']),(30,['e37']),(88,['e45']),(105,['e45','e48']),(106,['e49']),(118,['e48'])]:
    a.events[f'ev{n}']['instruments']=tools
    F(a.events[f'ev{n}']['trigger'],instruments=tools)

# Explicit lexical corrections and morphology, including fused pronoun/auxiliary
# forms. No entity or event interpretation is guessed from an ending.
for w,lemma in [(262,'it'),(368,'it'),(469,'it'),(277,'there')]:
    F(w,pos='pron',lemma=lemma)
for w,parts in {118:['star','is'],260:['will','not'],262:['it','is'],269:['can','not'],277:['there','is'],322:['do','not'],368:['it','is'],397:['do','not'],409:['did','not'],469:['it','will'],480:['should','not']}.items():
    F(w,contraction_expansion=parts)
a.feature(118,evidence=[118,119],note='Chosen adjectival gone (star is gone); star has gone is a possible perfect reading. This is not possessive morphology.',evidence_resolution_status='ambiguous')
for w in [108,253,283,476,511,529,738]: F(w,grammatical_case='genitive')
for w in [14,32,54,111,140,235,275,394,462,465,539,618,624,633,639,674,679,718,768,763,805]:
    F(w,determiner_kind='possessive',definiteness='definite',grammatical_case='genitive')
for w,value in [(24,3),(242,5),(809,3),(836,1)]: F(w,cardinal_value=value)
F([41,112,221,243,296,609,634,640,656,756,780,810],grammatical_number='plural')
F([126,138,312,340,426,438,444,526,549,648,755,840],noun_countability='mass_or_material_modifier')
F([8,129,455,583],adjective_degree='comparative')
F(387,adverb_degree='comparative')
# These are already manually disambiguated pronouns and determiners. The loops
# only expand those explicit decisions into redundant morphological features.
for w,row in enumerate(a.words):
    if row['pos']=='det' and row['lemma']=='the': F(w,determiner_kind='definite_article',definiteness='definite')
    if row['pos']=='det' and row['lemma']=='a': F(w,determiner_kind='indefinite_article',definiteness='indefinite')
    if row['pos']=='pron' and row['lemma'] in {'I','we','she','he','it','they','you','herself'}:
        F(w,mention_form='personal_pronoun',grammatical_person=1 if row['lemma'] in {'I','we'} else 2 if row['lemma']=='you' else 3)
    if row['pos']=='n' and row['lemma'] in {'Nia','Ben','Lila','Mouse','Moon','Rowan','Ms','Cedar','School'}: F(w,mention_form='proper_name')
F([201,244,330,359,403,408,413,423,460],grammatical_number='plural')
F([94,147,167,179,189,226,314,358,399,415,488,502,508,535,538,587,726,817],grammatical_case='objective')
F([187,396,724,765],grammatical_case='nominative',grammatical_number='singular')
F(163,mention_form='reflexive_intensifier',grammatical_case='reflexive')
F(151,mention_form='relative_pronoun')
F(277,expletive_license=True,mention_form='existential_expletive')
F([407,694],mention_form='nominal_substitute',phrase_has_elision=True)
F([259,416,597],referent_kind='proposition')
F(259,propositional_antecedent_id='p10')
F(416,propositional_antecedent_id='p22',evidence_explicit=False)
F(597,propositional_antecedent_id='p31')
F(29,determiner_kind='distributive_universal')
F(230,determiner_kind='negative',proposition_polarity='negative',negation_scope_id='p1',sentence_fragment_type='negative_nominal_search_result')
F([228,551,693],determiner_kind='demonstrative')
F(754,determiner_kind='dual',grammatical_number='plural')
F(540,ordinal_rank=1)

# Tense, auxiliaries and explicit predicate arguments. Bare infinitives remain
# nonfinite even when their governing clause is narrated in the past.
PAST = [6,17,21,27,35,45,57,65,69,81,84,100,106,113,121,123,143,152,159,165,175,188,196,200,202,218,224,233,250,252,266,274,290,299,301,320,333,338,343,348,367,372,382,389,404,409,411,414,417,424,428,433,439,442,448,454,458,461,467,473,475,503,514,522,542,545,554,558,562,567,573,575,580,586,592,596,601,611,617,628,644,646,652,658,667,669,676,691,695,721,725,731,744,747,752,759,772,777,783,788,802,811,821,835]
F(PAST,tense='past',verb_form='finite')
F([96,104,239,262,277,331,368,498,598],tense='present',verb_form='finite')
for auxiliary,predicate in [(27,28),(35,36),(239,240),(290,291)]:
    F(auxiliary,auxiliary_selection='gerund_participle')
    F(predicate,verb_form='gerund_participle',aspect='progressive',progressive_auxiliary_id=a.anchor(auxiliary))
for auxiliary,predicate in [(81,82),(159,160),(165,166),(224,225)]:
    F(auxiliary,auxiliary_selection='past_participle')
    F(predicate,verb_form='past_participle',aspect='perfect',perfect_auxiliary_id=a.anchor(auxiliary))
F(153,verb_form='past_participle',aspect='perfect',perfect_auxiliary_id=a.anchor(152))
F([93,356,537,547,606,608,635,655,686,798],verb_form='participle')
F([356,655,798],participial_function='passive_reduced_relative',voice='passive')
F(46,verb_form='past_participle',participial_function='posture_predicate')
F([38,42,59,74,89,146,178,192,246,261,270,323,327,361,377,386,398,401,410,419,470,481,487,494,501,507,518,534,638,641,683,706,708,715,767,785],verb_form='base')
for marker,predicate in [(37,38),(58,59),(73,74),(88,89),(145,146),(191,192),(326,327),(400,401),(493,494),(500,501),(637,638),(784,785)]:
    F(predicate,infinitive_marker_id=a.anchor(marker),clause_finiteness='nonfinite')
F([38,417,638],causative_syntax='make_np_bare_infinitive')
F(683,perception_complement_syntax='np_gerund_participle',evidence_observation_channel='hearing')
F(175,do_support_status='question_support',subject_auxiliary_inversion=True)
F([322,397,409],do_support_status='negative_support')
F([286,313,323,571],mood='imperative',imperative_subject_status='understood_addressee')
F(104,constituent_status='interrupted',omitted_complement_reason='interrupted_cue')
F(184,sentence_fragment_type='prepositional_answer')
F(584,sentence_fragment_type='adverbial_cue')
for w,particle,label in [(188,190,'take_out'),(301,302,'hand_over'),(313,315,'bring_back'),(372,373,'point_out'),(389,392,'turn_over'),(487,489,'hold_up'),(575,578,'turn_around')]:
    F(w,verb_particle_construction=label)
    F(particle,phrase_modifier_kind='verb_particle',phrase_complement_head_id=a.anchor(w))

# Overt grammatical subjects, deliberately independent from actor IDs. Body
# parts and passive patients can be subjects without becoming intentional agents.
SUBJECTS = {
6:'e9',17:'e11',21:'e12',28:'e1',36:'e2',42:'e20',46:'e3',57:'e1',65:'e5',69:'e2',74:'e23',82:'e2',84:'e3',89:'e23',96:'e15',100:'e1',104:'e13',106:'e3',113:'e27',119:'e16',121:'e3',123:'e16',144:'e15',146:'e15',154:'e13',160:'e3',166:'e3',178:'e3',181:'e2',188:'e3',196:'e3',200:'e39',202:'e7',218:'e2',225:'e2',233:'e1',240:'e6',246:'e7',250:'e3',252:'e3',262:'e23',266:'e2',271:'e13',274:'e1',291:'e4',299:'e1',301:'e4',320:'e4',331:'e7',333:'e2',338:'e1',343:'e2',348:'e3',367:'e3',368:'e46',372:'e2',377:'e13',382:'e1',386:'e17',389:'e3',398:'e3',401:'e17',404:'e7',410:'e7',411:'e1',414:'e7',419:'e3',424:'e7',428:'e7',433:'e1',439:'e48',442:'e2',448:'e3',454:'e46',458:'e46',461:'e7',467:'e50',470:'e17',473:'e2',475:'e3',481:'e17',487:'e14',494:'e13',499:'e13',501:'e13',504:'e1',507:'e14',514:'e3',518:'e46',522:'e3',534:'e14',542:'e51',545:'e3',547:'e3',554:'e7',558:'e14',562:'e17',567:'e46',573:'e3',575:'e3',580:'e3',586:'e14',592:'e46',596:'e1',601:'e6',606:'e6',608:'e6',611:'e2',617:'e1',628:'e3',635:'e26',641:'e30',644:'e22',646:'e14',652:'e12',658:'e23',663:'e15',667:'e1',669:'e3',676:'e57',683:'e3',686:'e6',692:'e16',695:'e17',706:'e3',708:'e1',715:'e3',721:'e3',725:'e15',731:'e3',744:'e6',747:'e14',752:'e12',759:'e3',767:'e13',772:'e1',777:'e2',783:'e11',785:'e11',788:'e1',798:'e45',802:'e3',811:'e7',821:'e11',835:'e46'}
for w,subject in SUBJECTS.items(): F(w,grammatical_subject_id=subject)
for w,obj in {28:'e19',38:'e20',59:'e22',65:'e24',82:'e21',93:'e3',96:'e18',113:'e31',146:'e18',160:'e16',166:'e16',178:'e16',188:'e16',192:'e32',218:'e20',225:'e20',246:'e23',252:'e29',274:'e19',291:'e42',313:'e40',323:'e11',338:'e44',348:'e46',361:'e46',377:'e18',389:'e46',404:'e16',414:'e16',424:'e44',428:'e17',433:'e45',442:'e44',448:'e45',461:'e17',475:'e25',487:'e17',501:'e18',507:'e17',522:'e49',534:'e17',537:'e17',547:'e48',554:'e23',558:'e17',575:'e17',580:'e49',586:'e17',628:'e14',646:'e55',663:'e18',669:'e14',683:'e6',706:'e1',708:'e59',715:'e23',725:'e18',747:'e17',752:'e54',759:'e17',777:'e20',788:'e40',802:'e14',835:'e61'}.items(): F(w,grammatical_object_id=obj)
for w,kind in [(13,'time'),(62,'before'),(77,'comparison'),(222,'concession'),(297,'time'),(341,'simultaneous'),(402,'appearance_comparison'),(446,'simultaneous'),(456,'comparison'),(459,'time'),(531,'purpose'),(807,'simultaneous')]: F(w,subordinator_type=kind)
for w,target in [(107,'e25'),(148,'e13'),(168,'e8'),(170,'e37'),(182,'e35'),(213,'e10'),(234,'e19'),(256,'e38'),(281,'e41'),(334,'e10'),(344,'e40'),(357,'e46'),(393,'e28'),(509,'e53'),(527,'e50'),(568,'e52'),(602,'e9'),(612,'e21'),(620,'e11'),(630,'e10'),(653,'e56'),(762,'e53'),(792,'e4'),(804,'e26')]: F(w,prepositional_object_id=target)

# Negation and modality target local propositions, including the scope of
# desire, prohibition and uncertainty. A grammatical negative is not global falsity.
for w,pid in [(260,'p11'),(269,'p12'),(322,'p15'),(369,'p18'),(397,'p21'),(409,'p22'),(480,'p26'),(536,'p29')]:
    F(w,polarity='negative',negation_marker_form=a.words[w]['token'],negation_scope_id=pid)
for w,kind,holder,pid in [(245,'practical_option','e3','p10'),(269,'deontic_story_requirement','e2','p12'),(360,'suggestion','e3','p17'),(376,'permitted_story_revision','e1','p19'),(384,'epistemic_possibility','e1','p20'),(480,'recommendation','e3','p26'),(486,'practical_ability','e3','p26'),(506,'practical_option','e3','p28'),(533,'intended_ability','e3','p29'),(682,'perceptual_ability','e3','p33'),(705,'available_alternative','e3','p34'),(714,'available_alternative','e3','p35'),(766,'ability_in_play','e13','p37')]:
    F(w,modal_base={'kind':kind,'holder':holder,'content_id':pid},modal_auxiliary_class='possibility_family')
F(682,modal_base={'kind':'perceptual_ability','holder':'e3','event_id':'ev142'})
F(480,modal_auxiliary_class='necessity_family')
F([260,469,517],modal_auxiliary_class='prediction_family')
F(144,modal_base={'kind':'scripted_expectation','content_id':'p5'})
F(499,modal_base={'kind':'scripted_intention','content_id':'p27'})
F(178,assertion_status='attributed_claim',truth_commitment='suspended')
F(269,semantic_world_id='w_play',evidence_world_status='fictional_requirement')
F(537,assertion_status='asserted',proposition_polarity='negative')

# Each mental predicate carries a bound owner/content, rather than projecting
# emotions onto every token or interpreting visible trembling as certain fear.
for w,owner,pid in [(57,'e1','p2'),(69,'e2','p3'),(84,'e3','p4'),(192,'e3','p8'),(398,'e3','p21')]:
    F(w,goal_owner_id=owner,goal_content_id=pid,goal_status='active',goal_polarity='achieve',goal_scope_bundle={'owner_id':owner,'intention_event_id':a.words[w]['event_id'],'scope_id':a.words[w]['scope_id'],'assertion_status':'asserted'})
F(57,goal_deadline={'relation':'before','event_id':'ev11'},goal_success_condition='p2')
F(84,goal_success_condition='p4')
F(398,goal_polarity='avoid',intention_publicity='communicated',assertion_status='attributed_claim')
F(398,goal_status='explicitly_not_desired')
a.words[398].pop('goal_polarity',None)
a.words[398]['goal_scope_bundle']['assertion_status']='attributed_claim'
a.feature(398,evidence=[396,397,398,401,404,407],note='The expressed desire is to avoid an appearance, not a confession of forgetting or an explicit fear label.')
F(154,affect_experiencer_id='e13',affect_kind='loneliness',affect_expression_channel='explicit_predicate',affect_scope_bundle={'experiencer_id':'e13','affect_event_id':'ev28','scope_id':'playback','assertion_status':'asserted'},semantic_world_id='w_play')
F(271,affect_experiencer_id='e13',affect_kind='loneliness',affect_target_id='p6',assertion_status='attributed_claim',semantic_world_id='w_play')
F(188,mental_memory_holder_id='e3',mental_memory_content_id='p7',mental_memory_event_id='ev33',epistemic_source_kind='memory',evidence_assertor_id='e3')
F(200,mental_memory_holder_id='e3',mental_memory_event_id='ev36',epistemic_source_kind='memory',evidence_assertor_id='e3')
F(386,belief_holder_id='e1',belief_content_id='p20',belief_certainty='tentative',epistemic_attitude_kind='possibility_judgment',assertion_status='attributed_claim')
F(470,belief_holder_id='e2',belief_content_id='p25',epistemic_attitude_kind='prediction',assertion_status='attributed_claim')
F(475,reasoner_id='e3',reasoning_mode='practical_plan_revision',reasoning_content_id='p24',reasoning_conclusion_id='p26')
F(487,goal_owner_id='e3',goal_content_id='p26',plan_commitment_status='proposed',plan_revision={'replace':'p10','with':'p26'})
F(507,goal_owner_id='e3',goal_content_id='p28',plan_commitment_status='proposed',goal_resource_ids=['e17','e49','e53'])
F(598,goal_owner_id='e1',goal_content_id='p28',goal_progress_judgment='working_after_test',goal_satisfaction_judgment='endorsed',assertion_status='attributed_claim')
F([706,715],reasoner_id='e3',reasoning_mode='consideration',reasoning_alternative_hypotheses=['p34','p35'])
F(683,focalizer_id='e3',viewpoint_access='hearing_and_subjective_interpretation',viewpoint_perceptual_anchor='ev142')
a.feature([635,676],evidence=[84,90,93,635,676,704,715,731],note='Trembling and blocked voice support a tentative performance-anxiety interpretation. Bodily actions themselves are asserted; no categorical fear or later emotional cure is asserted.',affect_experiencer_id='e3',affect_observer_attribution={'kind':'performance_anxiety','source':'annotator','status':'candidate'},evidence_explicit=False)

# Communication acts and their content links are on each reporting verb or
# quoted speech-act head. Enacted characters and actual voice performers differ.
SPEECH = [
(100,'e1','read_stage_direction','p5',['e2','e3']), (121,'e3','report','p1',['e1','e2']), (181,'e2','question','p7',['e3']), (188,'e3','answer','p7',['e2','e1']), (240,'e1','deadline_warning','p9',['e2','e3']), (250,'e3','suggest','p10',['e1','e2']), (266,'e2','object','p12',['e3']), (277,'e1','inform','p13',['e2','e3']), (299,'e1','explain','p1',['e4']), (320,'e4','instruct','p14',['e7']), (323,'e4','prohibit','p15',['e7']), (331,'e2','promise','p16',['e4']), (333,'e2','report_promise','p16',['e4']), (367,'e3','suggest','p17',['e1','e2']), (372,'e2','point_out','p18',['e1','e3']), (382,'e1','suggest','p19',['e2','e3']), (398,'e3','express_concern','p21',['e1','e2']), (411,'e1','correct','p22',['e3']), (414,'e1','reframe','p23',['e3']), (473,'e2','predict','p25',['e1','e3']), (487,'e3','suggest','p26',['e1','e2']), (504,'e1','remind','p27',['e3']), (514,'e3','propose_solution','p28',['e1','e2']), (573,'e3','request_pause','p30',['e1','e2']), (584,'e3','cue','p31',['e1','e2']), (596,'e1','acknowledge','p32',['e2','e3']), (667,'e1','read_stage_direction','p5',['e2','e3']), (731,'e3','perform_character_dialogue','p36',['e6']), (772,'e1','perform_character_dialogue','p37',['e6'])]
for w,speaker,act,pid,addressees in SPEECH:
    F(w,speaker_id=speaker,speech_act_kind=act,communication_channel='speech' if w!=596 else 'gesture',utterance_content_id=pid,addressee_ids=addressees)
    if a.words[w].get('event_type')=='speak':
        F(w,utterance_id=a.words[w]['event_id'],communication_scope_bundle={'speaker_id':speaker,'utterance_event_id':a.words[w]['event_id'],'scope_id':a.words[w]['scope_id'],'assertion_status':'asserted'})
F(333,speech_act_kind='promise')
F(174,question_requested_slot='original_star_last_seen_location',question_answer_status='answered_with_memory_report')
F(188,dialogue_response_to_id='ev32',dialogue_turn_function='answer',discourse_answer_relation={'question':'ev32','answer':'p7','kind':'explicit'})
F(313,request_action_id='ev57',request_acceptance_status='accepted_by_promise',obligation_debtor_id='e7',obligation_creditor_id='e4',obligation_content_id='p14',obligation_status='requested')
F(331,promise_content_id='p16',promise_beneficiary_id='e4',obligation_debtor_id='e7',obligation_creditor_id='e4',obligation_content_id='p14',obligation_status='accepted_commitment',plan_commitment_status='promised')
F(331,utterance_id='ev62',obligation_source={'kind':'promise_utterance','utterance_id':'ev62','commitment_event_id':'ev61'})
a.feature([331,333],evidence=[330,331,332,333],note='ev61 is the group commitment; ev62 is the one actual Ben utterance realizing it. These are linked analyses, not two speeches.')
F(323,obligation_debtor_id='e7',obligation_creditor_id='e4',obligation_content_id='p15',obligation_status='prohibition')
F(788,obligation_debtor_id='e7',obligation_creditor_id='e4',obligation_content_id='p14',obligation_status='fulfilled',intention_vs_action_alignment={'intention':'p14','outcome':'p38','alignment':'fulfilled'})
F(411,dialogue_repair_kind='reframing_correction',dialogue_repair_target_id='p21',discourse_correction_target='p21')
F(414,discourse_relation_kind='corrective_contrast',discourse_relation_source_id='p22',discourse_relation_target_id='p23',discourse_contrast_dimension='forgetting_versus_losing')
a.feature([411,414,416],evidence=[396,404,408,410,413,414,416,419],note='Nia corrects the feared appearance of forgetting, not an earlier assertion by Lila that they actually forgot.')
F(712,discourse_relation_kind='alternative',discourse_alternative_set=['p34','p35'])
F(736,discourse_relation_kind='contrast',discourse_contrast_dimension='whisper_versus_clear_character_voice',discourse_relation_target_id='p41')

# Physical and represented worlds: properties remain bound to their carriers.
for w,entity,color in [(15,'e11','red'),(125,'e16','silver'),(137,'e33','blue'),(304,'e40','green'),(311,'e44','gray'),(379,'e17','golden'),(590,'e46','gold'),(689,'e16','silver'),(697,'e17','gray'),(819,'e11','red')]:
    F(w,appearance_color={'entity_id':entity,'scope_id':a.words[w]['scope_id'],'value':color,'assertion_status':'attributed_claim' if w==379 else 'asserted','factuality':'hypothetical' if w==379 else 'asserted'})
F(370,appearance_color={'entity_id':'e46','scope_id':'q17','value':'silver','assertion_status':'attributed_claim','factuality':'negated'})
for w,entity,material in [(19,'e12','cardboard'),(40,'e20','paper'),(126,'e16','felt'),(220,'e20','cardboard'),(312,'e44','felt'),(350,'e46','brass'),(614,'e21','cardboard'),(648,'e55','cardboard'),(702,'e46','brass'),(755,'e54','felt'),(779,'e20','paper'),(829,'e46','brass')]:
    F(w,material_composition=B(entity,material,a.words[w]['scope_id']))
# Paper/cardboard cloud descriptions are recorded as the story's two material
# descriptions; no metal composition is inferred from silver/gold color.
a.feature([40,220,779],evidence=[40,41,220,221,779,780],note='The same scenery clouds are called paper and cardboard. Treat cardboard as a paper-based subtype rather than inventing different clouds.')
for w,part,whole in [(110,'e25','e14'),(112,'e27','e3'),(116,'e31','e25'),(135,'e32','e16'),(138,'e33','e32'),(141,'e34','e16'),(254,'e29','e14'),(395,'e28','e3'),(466,'e50','e17'),(524,'e49','e17'),(530,'e50','e17'),(541,'e51','e49'),(634,'e26','e3'),(640,'e30','e14'),(680,'e58','e3'),(756,'e54','e12'),(764,'e53','e12')]:
    F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
for w,prop,char,performer in [(52,'e14','e15','e3'),(95,'e14','e15','e3'),(108,'e14','e15','e3'),(142,'e14','e15','e3'),(485,'e14','e15','e3'),(505,'e14','e15','e3'),(532,'e14','e15','e3'),(557,'e14','e15','e3'),(585,'e14','e15','e3'),(645,'e14','e15','e3'),(662,'e14','e15','e3'),(670,'e14','e15','e3'),(746,'e14','e15','e3'),(803,'e14','e15','e3')]:
    F(w,enactment={'performer_id':performer,'prop_id':prop,'character_id':char,'world_id':'w_play'})
for w in [20,103,150,268,375,492,497,511,651,751,775]:
    F(w,enactment={'prop_id':'e12','character_id':'e13','voice_performer_id':'e1','world_id':'w_play'})
for w,prop in [(147,'e16'),(380,'e17'),(502,'e17'),(729,'e17'),(749,'e17'),(761,'e17')]:
    a.feature(w,enactment={'prop_id':prop,'character_id':'e18','world_id':'w_play'},evidence=[142,146,147,150,380,497,501,502,747,759,761],note='Physical star mention realizes the fictional gift role; the event table uses the represented object for scripted transfer/retention and the physical object for handling. These are a representation relation, not entity identity.')
# A represented offer and completed reception occur alongside prop movement.
a.event('ev167',747,'Mouse offers gift inside the play',type='transfer',actor='e15',patients=['e18'],recipient='e13',scope='play_action',primary=False,support=[746,747,749,751])
a.event('ev168',759,'Moon receives gift inside the play',type='transfer',actor='e15',patients=['e18'],recipient='e13',scope='play_action',primary=False,support=[747,751,752,756,758,759,761,764])
F(747,enactment={'performer_id':'e3','prop_id':'e14','character_id':'e15','world_id':'w_play','represented_event_id':'ev167','physical_event_id':'ev153'})
F(759,enactment={'performer_id':'e3','physical_theme_id':'e17','represented_theme_id':'e18','world_id':'w_play','represented_event_id':'ev168','physical_event_id':'ev155'})
for w in [558,586,646,747]:
    a.feature(w,event_control=B('e14',{'controller':'e3','mode':'direct','event_id':a.words[w]['event_id']}),evidence=[44,52,55,627,628,629,668,669,670,758,759],note='Retrospective controller binding from explicit Mouse-on-Lila-hand and later direct handling; Mouse remains the visible moving prop, not an autonomous animal.')
for w in [652,752]:
    a.feature(w,evidence=[651,652,751,752,771,772,775],note='Physical Moon motion is explicit, but the story does not identify its manipulator; Nia is only explicitly its voice performer.',evidence_resolution_status='controller_unresolved')

for w,entity,landmark,relation in [(3,'e9','e8','at'),(47,'e3','e10','behind'),(53,'e14','e26','on'),(139,'e32','e34','at'),(170,'e16','e37','inside'),(182,'e16','e35','on'),(213,'e38','e10','beneath'),(281,'e40','e41','inside'),(334,'e1','e10','behind'),(393,'e46','e28','in'),(527,'e49','e50','attached_to'),(612,'e2','e21','behind'),(620,'e1','e11','beside'),(630,'e14','e10','beneath'),(653,'e12','e56','above'),(762,'e17','e53','in'),(800,'e45','e40','inside'),(804,'e14','e26','on'),(812,'e7','e9','inside'),(831,'e46','e17','on')]:
    F(w,spatial_configuration=B(entity,{'landmark':landmark,'relation':relation},a.words[w]['scope_id'],status='attributed_claim' if w in [182,281] else 'asserted'))
for w,entity,container in [(170,'e16','e37'),(281,'e40','e41'),(293,'e43','e42'),(800,'e45','e40')]:
    F(w,containment_direct=B(entity,{'container':container},a.words[w]['scope_id']))
F(116,spatial_contact=B('e27',{'touches':'e31','event_id':'ev22'}))
F(116,evidence_observation_channel='touch',evidence_access_holder='e3')
F(254,spatial_facing_target=B('e29',{'faces':'e38'}))
F(518,spatial_facing_target=B('e46',{'faces':'e6'},'q27','predicted'))
F(567,spatial_facing_target=B('e46',{'faces':'e52'}))
F(592,spatial_facing_target=B('e46',{'faces':'e9'}))
F(562,spatial_orientation=B('e17',{'orientation':'sideways','event_id':'ev113'}))
F(481,containment_direct=B('e17',{'container':'e25','recommended':False},'q24','prohibited_in_plan'))
F(507,motion_destination=B('e17',{'landmark_id':'e53','event_id':'ev102','role':'destination'},'q26','planned'))
F(601,motion_destination=B('e6',{'landmark_id':'e9','event_id':'ev124','role':'destination'}))
F(646,motion_waypoint=B('e14',{'landmark_id':'e55','event_id':'ev134','role':'crossed_region'}))
F(759,motion_stopping_location=B('e17',{'location':'e53','event_id':'ev155'}),spatial_support=B('e17',{'supported_by':'e53'}))
F(467,motion_direction=B('e50',{'interpretation':'downward','event_id':'ev92'}))
F(652,motion_direction=B('e12',{'interpretation':'upward','event_id':'ev135'}))
F(835,lexical_sense_id='catch_reflected_light',evidence_explicit=True)
F(28,grammatical_object_id='e62')
F(635,grammatical_subject_id='e63')
F(625,ontological_type='instruction',phrase_modifier_kind='nominal_compound_modifier')
F(634,part_whole_relation={'part_id':'e63','whole_id':'e3','scope_id':'s0'})
F(827,attributes=[{'name':'illumination','value':'dim'}],evidence_explicit=True)

# Custody and construction. Borrowed tools are not inferred to belong to the
# borrower, and making a replacement does not recover the missing original.
for w,entity,holder in [(52,'e14','e3'),(166,'e16','e3'),(338,'e44','e1'),(389,'e46','e3'),(442,'e44','e2'),(448,'e45','e3'),(628,'e14','e3'),(788,'e40','e4'),(802,'e14','e3')]: F(w,possession_holder=B(entity,{'holder':holder}))
F(301,transfer_kind=B('e40','loan'),possession_borrower=B('e40',{'borrower':'e7'}),possession_lender=B('e40',{'lender':'e4'}),possession_return_target=B('e40',{'return_to':'e4'}))
F(313,possession_return_target=B('e40',{'return_to':'e4'},'q13','requested'))
F(788,transfer_kind=B('e40','return'),transfer_recipient=B('e40',{'recipient':'e4'}),transfer_completion=B('e40',{'completed':True,'recipient':'e4','event_id':'ev161'}))
F(797,possession_holder=B('e45',{'holder':'e4','via_container':'e40','event_id':'ev161'}))
F(160,event_creation=B('e16',{'created':True,'creator':'e3','event_id':'ev29'}))
F(428,event_creation=B('e17',{'created':True,'material_id':'e44','event_id':'ev84'}),event_result_entity=B('e17',{'created_from':'e44','event_id':'ev84'}),causal_compensation=B('e16',{'compensation':'e17','original_restored':False}))
F(522,event_creation=B('e49',{'created':True,'material_id':'e48','event_id':'ev105'}))
F(356,event_result_entity=B('e47',{'depicted_content':'flower','carrier':'e46','event_id':'ev66'}))
# Correct stamped flower's role to depicted result; button is the stamped carrier.
for binding in a.words[355]['event_bindings']:
    if binding['event_id']=='ev66': binding['role']='other'
if a.words[355].get('event_id')=='ev66': F(355,role='other')
for binding in a.words[358]['event_bindings']:
    if binding['event_id']=='ev66': binding['role']='patient'
if a.words[358].get('event_id')=='ev66': F(358,role='patient')
F(355,ontological_type='depiction',referent_kind='depicted_object')
F(430,object_shape=B('e17','lopsided'))
F(696,object_shape=B('e17','crooked'))
F(445,object_tension_state=B('e44','taut'))
F(543,object_tension_state=B('e51','loose'))
F(550,object_tension_state=B('e48','taut'))
F(439,object_integrity=B('e48','frayed'))
F(455,quantity_comparison_cue='greater',attributes=[{'name':'weight_relative_to_appearance','value':'heavier_than_it_looked'}])
F(129,quantity_comparison_cue='not_greater',attributes=[{'name':'size_comparison','value':'no_bigger_than_a_biscuit'}])
F(8,quantity_comparison_cue='not_greater',attributes=[{'name':'width_comparison','value':'no_wider_than_a_closet'}])
F(583,quantity_comparison_cue='less',attributes=[{'name':'loop_length_change','value':'shorter_than_first_test'}])
F(22,attributes=[{'name':'apparent_size','value':'enormous'}])
F(76,attributes=[{'name':'desired_aesthetic_quality','value':'as_beautiful_as_painted_scenery'}])
F([49,109,354,604,728,740],attributes=[{'name':'relative_size','value':'small'}])
F(86,ordinal_rank=1,attributes=[{'name':'sequence_position','value':'final_scene'}])
a.words[86].pop('ordinal_rank')  # final supplies ordering, never a numeric first rank
F([660,837],attributes=[{'name':'sequence_position','value':'last'}])
F(295,attributes=[{'name':'age_relative','value':'old'}])
F(463,attributes=[{'name':'discourse_object_status','value':'newly_made'}])
F(688,attributes=[{'name':'discourse_object_status','value':'original'}])
F(833,attributes=[{'name':'discourse_object_status','value':'newly_made'}])
F(739,attributes=[{'name':'voice_audibility','value':'clear'}])
F(699,attributes=[{'name':'visual_appearance','value':'bright_with_brass_button'}])
F(814,attributes=[{'name':'occupancy_description','value':'empty_of_audience'}])
a.feature(814,evidence=[600,601,786,810,811,814,815],note='Empty theatre is ordinary audience-relative emptiness; the three friends remain, so this is not zero human occupancy.')

# Grounded causes, test-driven revisions and event-relative time.
F(417,causal_parent=B('e3',{'cause':'p22','effect':'ev82'}))
F(467,causal_parent=B('e50',{'cause':'heavy_button','effect':'ev92','evidence_status':'contextual_inference'}))
a.feature(467,evidence=[453,455,461,464,466,467],note='Load-induced sag is strongly suggested by the adjacent weight comparison and lifting; causal mechanism remains inferred.',evidence_explicit=False)
F(638,causal_mediation_chain=B('e30',{'chain':['ev130','ev132'],'mechanism':'hand_puppet_contact'}),causal_direction=B('e30',{'from':'ev130','to':'ev132'}))
F(580,plan_revision={'replace':'p30','with':'p31'},causal_state_delta=B('e49',{'event_id':'ev118','changed':['loop_length_shorter']}))
F(534,causal_enabling_condition=B('e17',{'condition':'e49','enables':'ev106','occurred':None},'lift_goal','intended'))
F(537,causal_blocked_effect=B('e17',{'preventer':'e49','would_be_effect':'dropping','prevention_verified':False},'lift_goal','intended'))
F(546,event_iteration=B('e3',{'trigger_event_id':'ev109','affected_event_id':'ev105','cue':'retry_after_loose_knot'}))
F(588,event_iteration=B('e14',{'trigger_event_id':'ev120','affected_event_id':'ev112','cue':'second_test'}))
F(440,cardinal_value=2,counted_domain={'kind':'thread_fraying_occurrence','event_id':'ev86'})
F(24,time_expression_id='time_three_oclock',event_time_interval={'event_ids':['ev4','ev5','ev8'],'clock':'local_12_hour','hour':3,'meridiem':'unspecified','day':'story_day'})
F(186,time_expression_id='time_lunch',narrative_time_frame='earlier_lunch',narrative_order_mode='retrospective_return')
F(229,time_expression_id='time_morning',narrative_time_frame='earlier_same_morning',event_time_relation={'left':'ev39','relation':'before','right':'ev38'})
F(243,measure_dimension='duration',measure_unit='min',normalized_measure={'dimension':'duration','value':5,'unit':'min','original':{'value':5,'unit':'minutes'},'meaning':'expected_delay_until_class_arrival'},temporal_anchor_unresolved=True)
F(62,event_time_relation={'left':'ev10','relation':'before','right':'ev11'})
F(297,event_time_relation={'left':'ev55','relation':'during','right':'ev54'})
F(341,event_time_relation={'left':'ev64','relation':'during','right':'ev63'})
F(446,event_time_relation={'left':'ev88','relation':'during','right':'ev87'})
F(786,event_time_relation={'left':'ev161','relation':'after','right':'ev159'})
F(644,event_phase=B('e22',{'trigger_event_id':'ev133','affected_event_id':'ev133','cue':'initiated'}))
F(783,event_phase=B('e11',{'trigger_event_id':'ev159','affected_event_id':'ev160','cue':'initiated'}))
F(673,attributes=[{'name':'duration_qualitative','value':'brief_moment'}])
F(272,attributes=[{'name':'duration_scope','value':'indefinitely_in_disallowed_story_outcome'}])
F(799,attributes=[{'name':'placement_manner','value':'safely_inside'}])

# Retrospective narrative labels are evidence-supported interpretations, kept
# apart from what characters explicitly knew, wanted or claimed at that point.
F(119,narrative_thread_id='thread_missing_prop',narrative_thread_status='open',narrative_problem_id='p1',narrative_goal_link={'thread':'thread_missing_prop','goal':'p2'})
F(240,narrative_tension_source='limited_time_before_audience_arrival',narrative_thread_id='thread_prepare_ending')
F(428,narrative_thread_id='thread_prepare_ending',narrative_change_dimension='replacement_exists',narrative_change_evidence={'before':'p1','after':'p24'})
F(598,narrative_resolution_evidence={'problem':'p30','outcome':'p31','status':'test_problem_resolved'},narrative_tension_status='mechanical_problem_resolved')
F(715,narrative_thread_id='thread_lila_performance',narrative_tension_source='perform_own_scene_or_delegate_voice')
a.feature(731,evidence=[84,90,93,676,706,715,724,731,735,739,741],note='The demonstrated change is Lila speaking the character clearly. It supports growing participation but does not prove a permanent personality change or total absence of anxiety.',narrative_change_dimension='participation_and_voice',narrative_change_evidence={'before':'p4','after':'p41'},narrative_thread_id='thread_lila_performance',narrative_tension_status='speaking_choice_resolved')
a.feature(759,evidence=[118,119,261,264,271,380,747,759,761,764],note='A new prop preserves the intended gift ending; the original star remains missing. This resolves the performance need, not the search.',narrative_resolution_evidence={'problem':'p1','outcome':'p39','status':'compensated_without_original_recovery'},narrative_thread_id='thread_prepare_ending')
F(692,narrative_thread_id='thread_missing_prop',narrative_thread_status='original_still_missing')
a.feature(835,evidence=[125,127,350,351,430,689,690,697,703,729,759,830,834,835,840],note='The final reflected dot of light echoes Mouse’s little-light line and the changed prop. This is an annotator interpretation, not an explicit character moral.',narrative_motif_link={'earlier':'p36','current':'p42','relation':'literal_reflected_light_echoes_staged_gift'},narrative_closure_candidate={'cue':'curtain_closed_and_final_object_image','status':'candidate','thread':'thread_prepare_ending'},narrative_theme_candidate={'content':'imperfect_replacement_and_own_voice_preserve_the_shared_ending','source':'annotator','status':'candidate'})

# Canonical lemma convention from the shared pilot revision; modal meaning is
# retained in modal_base, so this normalization does not collapse modal force.
for row in a.words:
    if row['pos']=='v' and row['lemma'] in {'could','would','should','might'}:
        row['lemma']={'could':'can','would':'will','should':'shall','might':'may'}[row['lemma']]

# Event support includes only manually associated predicate/participant words.
# Quoted propositions carry source attribution rather than narrator endorsement.
for eid,event in a.events.items():
    supports={event['trigger'], *event['support_words']}
    supports.update(w for w,row in enumerate(a.words) if any(b['event_id']==eid for b in row.get('event_bindings',[])))
    event['support_words']=sorted(supports)
    row=a.words[event['trigger']]
    if row.get('event_id') != eid: continue
    if 'assertion_status' not in row:
        F(event['trigger'],assertion_status='attributed_claim' if event['scope_id'].startswith('q') else 'asserted')
    if event['scope_id'].startswith('q'):
        holder=a.scopes[event['scope_id']]['holder_id']
        F(event['trigger'],evidence_assertor_id=holder,evidence_report_depth=1)

# Important referential/semantic uncertainties are retained with local evidence.
a.feature([368,399],evidence=[351,359,362,368,380,383,388,391,396,399,401],note='It’s at 368 is taken as the button under immediate discussion; it at 399 as the replacement appearance. The whole revised staging is also a plausible broader reading at 399.',evidence_resolution_status='chosen_reading_with_recorded_alternative')
a.feature([466,530],evidence=[465,466,467,522,524,529,530],note='The sagging upper point and later top attachment are linked as one prop region; the exact geometric point is underspecified.',evidence_resolution_status='region_identity_coarse')
a.feature([2,605],evidence=[2,8,11,599,600,601,605],note='Theatre shifts between a small puppet booth and its performance/audience space. A single coarse performance-space identity is retained; precise spatial extent is not inferred.',evidence_resolution_status='referent_extent_underspecified')
a.feature(685,evidence=[600,601,685,686,743,744],note='Room waiting is metonymic for the assembled class, not an animate room.',lexical_sense_id='room_as_audience',entity_id='e6',entity_name='class audience',entity='group')
a.feature(677,evidence=[675,676,677,680,721,731],note='Voice trapped in throat is difficulty initiating speech, not literal physical imprisonment.',lexical_sense_id='voice_trapped_metaphor')
a.feature(757,evidence=[752,756,758,759,761,764],note='Moon puppet hands extending and Lila settling the star are separate physical events; only the fictional reception is a unified gift event.')

FEEDBACK = {
 'summary':'Complete manual retrospective annotation of the puppet-rehearsal story, with separate people, puppets, fictional characters, old/new props, staged-world events, quoted plans and actual handling.',
 'ambiguities':[
  {'words':[118,119],'issue':'star’s gone can expand to star is gone (chosen adjectival missing-state reading) or star has gone; neither implies ownership morphology.'},
  {'words':[2,605],'issue':'theatre denotes the narrow puppet booth initially and broader performance/audience space later; a coarse shared identity is retained without a precise physical extent.'},
  {'words':[147,380,502],'issue':'Physical prop mentions fill represented gift roles through explicit enactment bridges; e16/e17 remain distinct from fictional gift e18.'},
  {'words':[368,399],'issue':'Button is the selected antecedent of It’s not silver; replacement appearance is selected for I don’t want it to look. Whole staging is a plausible latter alternative.'},
  {'words':[466,530],'issue':'Sagging point and top are one coarse region; exact point identity is not guaranteed.'},
  {'words':[635,676],'issue':'Performance anxiety is an annotated candidate from bodily cues and context, not explicit fear. No permanent confidence trait is asserted.'},
  {'words':[651,652,751,752,771,772],'issue':'Nia voices Moon; its physical manipulator is unknown.'},
  {'words':[329],'issue':'Star from prohibited curtain-cutting has no actual entity witness; it is a hypothetical alternative, not the completed replacement.'},
  {'words':[609,723,769],'issue':'Individual knees, inhaled breath and the Moon’s metaphorical way remain lexical/event participants without invented stable entity identities.'},
  {'words':[380,383],'issue':'Proposed replacement/golden star is linked retrospectively to later physical replacement; its suggested gold appearance is scoped, not a material assertion.'},
 ],
 'feature_gaps':[
  {'key':'enactment','why':'Need correlated physical performer, puppet/prop and represented fictional identity; semantic_world_id alone cannot express the bridge or distinguish voicing from manipulation.'},
  {'key':'appearance_color','why':'Surface color needs an entity-bound typed value independent of material. Silver/gold here are appearance labels; brass is material.'},
  {'key':'part_whole_relation','why':'Actual token-level part→whole links are separate from reference-licensing bridging_relation or lexical part types.'},
  {'key':'event_bindings','why':'One occurrence participates in multiple predicates; especially staged/physical readings and shared subjects. Preserve correlated memberships.'},
  {'meaning':'weight and qualitative length comparison','why':'Stored as legacy attributes/quantity comparison cue; exact quantitative dimension+comparison operands need richer typed bundles.'},
 ],
 'prompt_feedback':[
  'Explicitly define a two-world performance example: puppet, performer, character, prop realization, and voice performer are different links; an identified voice performer does not establish physical manipulation.',
  'Require source-relative scope for negative plans and requirements: cannot remain lonely, do not cut, and without dropping are not reports of observed absence.',
  'State whether a repeated script direction points to the same scripted event. This pilot reuses ev18 at its second reading and keeps actual reading acts ev19/ev139 distinct.',
  'Clarify contraction POS and lemma with It’s, There’s and star’s examples. Retain contraction alternatives when is versus has cannot be resolved.',
  'Give an example of explicit light reflection versus light emission; catches light does not make a brass button a lamp.',
  'Avoid treating empty theatre as zero people when the same sentence explicitly leaves friends inside; define the restricted occupancy domain.',
  'Allow local evidence notes for grounded inference without upgrading a likely emotion, cause or broad theme to a certain psychological fact.',
  'Document event-count granularity for state observations and causative phase predicates; IDs identify this annotation’s event analyses, not a universal segmentation.',
 ],
 'coverage_notes':'Every one of 841 words has manual POS+lemma. All 44 paragraphs were read in full. Content predicates, entity mentions, quotation scopes, modality, grammar, plans, roles, materials, physical relations, creation/return, causal links, and narrative changes are covered sparsely; unavailable facts are omitted. No causal-prefix filtering or API calls. Nonword tokens are deterministic synthetic records.',
 'reviewed_all_words':True,
 'reviewed_paragraphs':list(range(44)),
 'not_claimed':['ownership of borrowed tools','identity of Moon puppeteer','recovery of original star','literal emotional state of an astronomical moon','numeric dimensions or weights','complete disappearance of Lila’s anxiety'],
}
a.save(FEEDBACK)
