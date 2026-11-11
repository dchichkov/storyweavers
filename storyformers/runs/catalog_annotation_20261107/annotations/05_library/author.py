"""Manual v1 whole-story library annotation; no external model or tagger."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation

a = Annotation('05_library', prompt_version='v1')
for key in ['appearance_color','part_whole_relation','figurative_mapping']:
    a.use_extension(key)

# Explicit contextual POS/lemma choice for every occurrence, in paragraph order.
LEX = [
'adp=at num=five adv=o’clock n=Mina v=find det=the n=moon n=atlas pron=she v=want adp=on det=the n=library n=display n=table pron=she v=tuck pron=it adp=under det=her n=arm conj=if pron=she v=borrow pron=it adp=before n=closing pron=she v=can v=sketch det=the n=crater adv=tonight conj=and v=show det=her n=class adv=tomorrow',
'adv=then n=Jun v=hurry adv=over det=his n=cheek adj=pink adp=from v=run pron=he v=be num=six conj=and n=Mina v=be num=nine pron=which v=mean pron=he adv=often v=ask pron=she part=to v=reach adj=high n=shelf conj=and v=read det=the adj=tricky n=word',
'det=my n=whale n=book adj=gone pron=he v=say det=the pron=one pron=I v=pick adp=for n=Grandma part=to v=read adv=tonight pron=I v=have pron=it adp=by det=the n=window conj=and adv=now pron=it part=not adv=there',
'n=Jun n=grandmother v=be v=wait adp=at det=the adj=front n=desk det=the n=library v=close adp=at num=six',
'pron=I v=help pron=you v=find pron=it n=Mina v=say pron=I v=promise adp=before n=closing',
'det=the n=book v=be v=call det=the n=Whale pron=who v=sing adp=to det=the n=Moon n=Jun v=have v=be v=carry pron=it adp=around det=the n=child n=room v=show pron=everyone det=the n=picture adp=of det=a adj=blue n=whale v=swim adp=beneath det=a n=sky adj=full adp=of n=star',
'n=Mina v=hurry adp=to n=Ms n=Alvarez det=the n=librarian v=can pron=we v=borrow det=the adj=little n=book n=trolley part=to v=search',
'pron=you v=may v=borrow pron=it n=Ms n=Alvarez v=say v=hand pron=she det=the n=handle v=put det=any adj=stray n=book pron=you v=find adp=on pron=it conj=and v=keep det=all num=four n=wheel adp=on det=the n=floor',
'pron=I v=know n=Mina v=say pron=she v=set det=her n=moon n=atlas adv=carefully adp=on det=the adj=front n=desk adv=where pron=she v=can v=collect pron=it adv=later adv=then v=push det=the adj=empty n=trolley adp=into det=the n=child n=room',
'pron=they v=search det=the n=window n=nook adv=first n=Jun v=check adp=behind det=the n=cushion conj=while n=Mina v=look adp=beneath det=the n=bench pron=they v=find det=a n=mitten num=two n=board n=book conj=and det=a n=crayon v=shape adp=like det=a n=dinosaur pron=all v=go adp=onto det=the n=trolley',
'part=not det=my n=whale n=Jun v=say',
'pron=they v=check det=the n=puppet n=theater det=the n=rug conj=and det=the n=shelf adp=beside det=the n=fish n=tank n=Mina v=run det=her n=finger adp=along det=the n=picture n=book n=spine n=Jun v=crouch part=to v=inspect det=the adj=low n=shelf v=whisper det=the n=title adp=to pron=himself conj=as conj=if det=the n=book v=may v=answer',
'adp=at num=five num=twenty det=the n=trolley v=be adv=already v=carry det=a adj=crooked n=tower adp=of n=book n=Mina v=stop pron=it conj=whenever det=a n=wheel v=squeak conj=and v=steady det=the n=stack adp=with num=one n=hand pron=they v=look adp=through det=every n=book pron=they v=collect conj=but pron=none v=have det=a adj=blue n=whale adp=on det=the n=cover',
'n=Jun n=mouth v=turn adv=down n=Grandma v=say pron=we v=have part=to v=go conj=when det=the n=library v=close',
'pron=we adv=still v=have n=time n=Mina v=say',
'pron=they v=search det=the n=reading n=table adp=near det=the n=astronomy n=shelf n=Jun v=spot det=a adj=silver n=paper n=star adp=on det=the n=floor pron=he v=pick pron=it adv=up conj=and v=rub det=a n=crease adj=flat adp=with det=his n=thumb',
'det=my n=bookmark pron=he v=say pron=it v=be adp=inside det=the n=whale n=book',
'n=Mina v=look adp=at det=the adj=high n=shelf adp=above det=the n=astronomy n=book det=a adj=silver n=point v=glimmer adp=between num=two adj=thick n=volume',
'v=be pron=that pron=it n=Jun v=ask',
'pron=I v=think adv=so conj=but pron=we v=can v=climb',
'n=Mina v=glance adp=at det=the n=moon n=atlas adp=on det=the n=desk pron=she v=have v=imagine v=open pron=it adp=at n=home adv=then v=draw det=the n=moon adp=in det=the adj=round n=corner adp=of det=her n=notebook det=the n=clock adp=above det=the n=desk v=say num=5 num=48',
'pron=she v=can v=ask n=Ms n=Alvarez part=to v=put det=the n=atlas adv=aside conj=while pron=they v=search conj=but det=the n=librarian v=be v=check adv=out det=a n=family adp=at det=the n=desk conj=and det=the adj=silver n=point v=may v=be det=the n=bookmark conj=or v=may v=be pron=something adj=else',
'n=Mina v=take det=the n=moon n=atlas adp=from det=the n=desk conj=and v=carry pron=it adp=to n=Ms n=Alvarez',
'v=can pron=you v=put pron=this adv=back adp=on det=the n=shelf pron=she v=ask pron=I v=need part=to v=keep v=look adp=with n=Jun',
'n=Ms n=Alvarez v=study det=her n=face adv=then v=nod adv=all adj=right conj=but pron=I v=get det=the n=ladder',
'conj=while pron=they v=wait n=Jun v=grip det=the n=trolley n=handle pron=I v=think pron=I v=put det=the n=book adv=back pron=he v=say pron=I v=can v=reach det=the n=picture n=book n=shelf conj=so pron=I v=put pron=it adp=on det=the n=astronomy n=shelf det=the n=whale v=have n=star adp=around pron=it',
'n=Mina v=look adv=up adp=at det=the adj=silver n=point adv=then pron=it adv=probably adv=there',
'n=Ms n=Alvarez v=return adp=with det=the n=library n=ladder conj=and v=climb adv=carefully adp=from adv=below n=Mina conj=and n=Jun v=watch det=the n=star n=bookmark v=tremble conj=as det=the n=librarian v=ease det=the adj=thick n=book adv=apart det=a adj=blue n=cover v=slide adv=forward',
'det=the n=Whale pron=who v=sing adp=to det=the n=Moon n=Ms n=Alvarez v=read',
'n=Jun v=make det=a n=sound adp=like det=a adj=tiny n=cheer n=Ms n=Alvarez v=bring det=the n=book adv=down conj=and v=hand pron=it adp=to pron=he det=his n=bookmark v=be adv=still v=tuck adv=inside adv=just adv=where pron=he v=have v=leave pron=it',
'adp=at num=five num=fifty num=eight n=Ms n=Alvarez v=check det=the n=book adv=out adp=to n=Jun n=Mina v=push det=the n=trolley adv=back adp=to det=its n=place det=its n=wheel v=click adv=softly adp=over det=the n=tile det=her n=moon n=atlas v=be adv=back adp=on det=the n=display n=shelf',
'adv=outside n=Jun n=grandmother v=open det=the n=whale n=book adp=beneath det=the n=streetlamp n=Jun v=lean adp=against det=her n=side conj=and n=Mina v=lean adv=in adv=too adp=on det=the adj=first n=page det=the v=paint n=whale v=sail adp=through det=a n=sky adp=of adj=silver n=star conj=while n=Jun n=paper n=bookmark v=rest adp=against det=its n=tail',
]
for p, encoded in enumerate(LEX):
    pairs = [x.split('=',1) for x in encoded.split()]
    words = a.paragraphs[p]['words']
    assert len(pairs)==len(words),(p,len(pairs),len(words))
    a.tag(p,[x[0] for x in pairs],{w['w']:pair[1] for w,pair in zip(words,pairs)})

ENTITIES = [
('e1','Mina','person',[3,8,15,19,22,27,35,51,59,108,113,115,154,178,197,199,201,203,212,238,281,283,321,369,411,434,441,450,466,476,513,535,537,547,596,619,693,708,733]),
('e2','Jun','person',[39,42,47,56,69,73,77,84,95,110,130,232,263,265,290,301,351,380,389,399,401,403,432,543,561,566,568,573,575,583,621,650,668,669,677,692,718,727,752]),
('e3','Jun’s grandmother','person',[80,96,355,719,730]),
('e4','Ms. Alvarez','person',[157,158,160,174,175,479,480,491,525,526,528,544,545,554,607,608,629,647,648,658,659,685,686]),
('e5','Mina and Jun','person_group',[162,170,185,226,243,267,335,340,365,371,438,487,559]),
('e6','library','library',[12,104,363,612]),
('e7','moon atlas','atlas',[7,17,24,205,215,446,454,484,517,523,530,710]),
('e8','initial display table','table',[14]),
('e9','Mina’s arm','body_part',[20]),
('e10','moon studied by Mina','celestial_body',[460]),
('e11','moon craters to sketch','surface_features',[31]),
('e12','Mina’s class','group',[36]),
('e13','Jun’s cheeks','body_part_group',[43]),
('e14','habitually hard-to-reach shelves','shelf_group',[63]),
('e15','trickier words Jun asks about','word_set',[68]),
('e16','The Whale Who Sang to the Moon','book',[71,76,86,92,112,120,134,264,305,410,431,571,585,604,662,666,689,723]),
('e17','library window','window',[89,229]),
('e18','front desk','desk',[102,210,449,472,499,520]),
('e19','whale-book title','title_text',[299]),
('e20','children’s room','room',[138,225]),
('e21','whale depicted in the book','depicted_character',[124,146,591,595,641,743,757]),
('e22','sky depicted in whale book','depicted_setting',[150,747]),
('e23','stars depicted around whale','depicted_star_group',[153,593,750]),
('e24','library book trolley','trolley',[167,173,188,221,261,312,323,564,696,699,701]),
('e25','trolley handle','handle',[180,565]),
('e26','four trolley wheels','wheel_group',[193,702]),
('e27','library floor','floor',[196,388]),
('e28','window nook','room_region',[230]),
('e29','nook cushions','cushion_group',[236]),
('e30','window-nook bench','bench',[242]),
('e31','found mitten','mitten',[246]),
('e32','two found board books','book_group',[249]),
('e33','dinosaur-shaped crayon','crayon',[252]),
('e34','mitten board books and crayon','object_group',[257]),
('e35','library puppet theater','puppet_theater',[271]),
('e36','library rug','rug',[273]),
('e37','shelves beside fish tank','shelf_group',[276]),
('e38','fish tank','aquarium',[280]),
('e39','Mina’s finger','body_part',[284]),
('e40','picture-book spines','book_part_group',[289]),
('e41','lowest shelf examined','shelf',[296]),
('e42','stack of collected books','book_group',[318,320,331,339,343]),
('e43','Mina’s steadying hand','body_part',[334]),
('e44','Jun’s mouth','body_part',[352]),
('e45','reading tables','table_group',[375]),
('e46','astronomy shelving','shelf_region',[379,589]),
('e47','Jun’s paper star bookmark','bookmark',[385,391,402,405,507,625,670,680,754]),
('e48','bookmark crease','fold',[396]),
('e49','Jun’s thumb','body_part',[400]),
('e50','high shelves above astronomy books','shelf_group',[416,606]),
('e51','visible silver bookmark point','bookmark_part',[423,503,602]),
('e52','two thick flanking volumes','book_group',[428,633]),
('e53','Mina’s home','home',[456]),
('e54','Mina’s notebook','notebook',[467]),
('e55','notebook corner','page_region',[464]),
('e56','library clock','clock',[469]),
('e57','family checking out','person_group',[496]),
('e58','atlas display shelf','shelf',[534,716]),
('e59','Mina’s face','body_part',[548]),
('e60','library ladder','ladder',[557,613]),
('e61','picture-book shelf Jun could not reach','shelf',[581]),
('e62','whale-book blue cover','book_cover',[637]),
('e63','Jun’s cheer-like sound','sound',[653]),
('e64','trolley storage place','place',[700]),
('e65','floor tiles','tile_group',[707]),
('e66','streetlamp','lamp',[726]),
('e67','grandmother’s side','body_region',[731]),
('e68','first whale-book page','page',[740]),
('e69','depicted whale’s tail','depicted_body_part',[758]),
('e70','moon named in book title','depicted_celestial_body',[129,646]),
('e71','astronomy books','book_group',[420]),
('e72','Jun and grandmother','person_group',[357]),
('e73','squeaking trolley wheel','wheel',[326]),
]
for eid,name,kind,mentions in ENTITIES:
    a.entity(eid,name,kind,mentions)
a.entities['e5']['member_ids']=['e1','e2']
a.entities['e34']['member_ids']=['e31','e32','e33']
a.entities['e72']['member_ids']=['e2','e3']
a.entities['e47']['continuity_note']='The text identifies the floor star as Jun’s bookmark, then describes his bookmark as still inside the recovered book. One intended identity is retained; the intervening location history is unresolved. No reinsertion, duplication or additional bookmark is asserted.'
a.entities['e8']['identity_note']='The initial display table and final display shelf have separate discourse referents; their physical relationship is unspecified.'

# Dialogue scopes are exact half-open word ranges; reports and plans are nested.
QUOTES=[
('s1',69,73,'e2'),('s2',75,95,'e2'),('s3',108,113,'e1'),('s4',115,119,'e1'),
('s5',161,170,'e1'),('s6',170,174,'e4'),('s7',181,197,'e4'),('s8',197,199,'e1'),
('s9',262,265,'e2'),('s10',355,365,'e2'),('s11',365,369,'e1'),('s12',401,403,'e2'),
('s13',405,411,'e2'),('s14',429,432,'e2'),('s15',434,441,'e1'),('s16',527,535,'e1'),
('s17',537,544,'e1'),('s18',551,558,'e4'),('s19',566,573,'e2'),('s20',575,596,'e2'),
('s21',603,607,'e1'),('s22',640,647,'e4')]
for sid,lo,hi,holder in QUOTES:
    a.scope(sid,range(lo,hi),kind='quotation',holder_id=holder,description='Direct speech, distinct from its actual utterance event.')
    a.feature(range(lo,hi),quote_mode='direct')
SCOPES=[
('s23',21,38,'conditional_plan','e1','s0','Borrowing atlas is a condition of an imagined sketch/show plan, not a completed loan.'),
('s24',54,69,'habitual','e2','s0','Repeated help requests, not one new present request.'),
('s25',81,84,'intended','e2','s2','Grandmother’s intended reading tonight is not narrated as complete.'),
('s26',123,130,'title_content',None,'s0','The book title is language about a fictional whale and moon.'),
('s27',145,154,'depicted_scene',None,'s0','Pictured whale, sky and stars; not animals swimming in the library.'),
('s28',168,170,'purpose','e1','s5','Search is the proposed purpose of the trolley loan.'),
('s29',181,190,'conditional_instruction','e4','s7','Any stray book found is to be put on the trolley; no universal future finding is asserted.'),
('s30',211,217,'possible_plan','e1','s0','Potential later atlas collection, not executed here.'),
('s31',302,308,'figurative_hypothetical','e2','s0','As-if book response personifies the book without actual speech.'),
('s32',357,365,'reported_obligation','e3','s10','Jun reports grandmother’s departure rule.'),
('s33',453,468,'imagined','e1','s0','Home atlas opening and moon drawing are imagined, not actual scenes.'),
('s34',476,489,'considered_plan','e1','s0','Asking to reserve atlas is considered, not the later actual request to reshelve it.'),
('s35',501,513,'epistemic_alternatives','e1','s0','Silver point may be the bookmark or something else, unresolved for Mina at this moment.'),
('s36',568,573,'belief_content','e2','s19','Content of Jun’s earlier belief that he had put the book back.'),
('s37',590,596,'reported_depiction','e2','s20','Jun’s description of the book image, not physical stars around a library animal.'),
('s38',741,751,'depicted_scene',None,'s0','Painted whale and silver stars on the first page.'),
('s39',292,297,'purpose','e2','s0','Inspecting the lowest shelf is the stated purpose of crouching; the purpose alone does not guarantee completed inspection.'),
]
for sid,lo,hi,kind,holder,parent,desc in SCOPES:
    a.scope(sid,range(lo,hi),kind=kind,holder_id=holder,parent=parent,description=desc)
for words in [range(123,130),range(145,154),range(590,596),range(640,647),range(741,751)]:
    a.feature(words,semantic_world_id='w_whale_book',evidence_world_status='depicted_or_titled_content')

def F(w,**fields): a.feature(w,**fields)
def B(w,entity,value,status=None,fact=None):
    scope=a.words[w]['scope_id']
    result={'entity_id':entity,'scope_id':scope,'assertion_status':status or ('attributed_claim' if a.words[w].get('quotation_scope_id') else 'asserted'),'value':value}
    if fact: result['factuality']=fact
    return result
def E(w,label,actor=None,patients=(),typ='other',fact='asserted',roles=None,**kwargs):
    eid=f'ev{w+1}'
    a.event(eid,w,label,actor=actor,patients=patients,type=typ,factuality=fact,roles=roles,**kwargs)
    return eid
def P(n,text,words,scope='s0'): a.proposition(f'p{n}',text,words,scope_id=scope)

# Event analyses are explicit. evN numbering derives from the chosen trigger,
# without asserting that every verb is a separate event.
EVENTS=[
(4,'Mina finds moon atlas','e1',['e7'],'perceive','asserted'),
(9,'Mina wants moon atlas','e1',['e7'],'state','asserted'),
(16,'Mina tucks atlas under arm','e1',['e7'],'move','asserted'),
(23,'Mina borrows atlas','e1',['e7'],'obtain','hypothetical'),
(26,'library closing boundary',None,['e6'],'state','hypothetical'),
(29,'Mina sketches moon craters','e1',['e11'],'other','hypothetical'),
(34,'Mina shows planned sketches to class','e1',[],'other','hypothetical'),
(40,'Jun hurries over','e2',[],'move','asserted'),
(44,'Jun cheeks are pink',None,['e13'],'state','asserted'),
(46,'Jun runs','e2',[],'move','asserted'),
(49,'Jun is six years old',None,['e2'],'state','asserted'),
(53,'Mina is nine years old',None,['e1'],'state','asserted'),
(58,'Jun habitually requests Mina’s help','e2',[],'speak','asserted'),
(61,'Mina reaches high shelves for Jun','e1',['e14'],'other','desired'),
(65,'Mina reads difficult words for Jun','e1',['e15'],'other','desired'),
(72,'whale book is missing from Jun’s access',None,['e16'],'state','reported'),
(74,'Jun reports missing whale book','e2',[],'speak','asserted'),
(78,'Jun selected whale book','e2',['e16'],'other','reported'),
(82,'grandmother reads chosen book','e3',['e16'],'other','desired'),
(85,'Jun had whale book by window','e2',['e16'],'state','reported'),
(94,'whale book is by window',None,['e16'],'state','negated'),
(98,'grandmother waits at front desk','e3',[],'state','asserted'),
(105,'library scheduled to close at six',None,['e6'],'state','asserted'),
(109,'Mina helps Jun search','e1',['e2'],'other','desired'),
(111,'Jun finds whale book with Mina','e2',['e16'],'perceive','desired'),
(114,'Mina offers help','e1',[],'speak','asserted'),
(116,'Mina promises help before closing','e1',[],'speak','asserted'),
(122,'whale book bears its title',None,['e16'],'state','asserted'),
(126,'title whale sang to moon','e21',[],'speak','reported'),
(133,'Jun had carried whale book around room','e2',['e16'],'move','asserted'),
(139,'Jun showed book picture','e2',[],'other','asserted'),
(147,'pictured whale swims below starry sky','e21',[],'move','asserted'),
(151,'pictured sky is full of stars',None,['e22'],'state','asserted'),
(155,'Mina hurries to librarian','e1',[],'move','asserted'),
(163,'Mina and Jun borrow trolley','e5',['e24'],'obtain','desired'),
(169,'Mina and Jun search using trolley','e5',['e16'],'perceive','desired'),
(172,'Mina and Jun borrow trolley with permission','e5',['e24'],'obtain','desired'),
(176,'Alvarez grants permission and instructions','e4',[],'speak','asserted'),
(177,'Alvarez hands trolley handle to Mina','e4',['e25'],'transfer','asserted'),
(181,'children put found stray books on trolley','e5',[],'move','desired'),
(186,'children find stray books','e5',[],'perceive','hypothetical'),
(190,'children keep trolley wheels on floor','e5',['e26'],'state','desired'),
(198,'Mina claims knowledge of instructions','e1',[],'state','reported'),
(200,'Mina acknowledges instructions','e1',[],'speak','asserted'),
(202,'Mina sets atlas on desk','e1',['e7'],'move','asserted'),
(214,'Mina collects atlas later','e1',['e7'],'obtain','hypothetical'),
(218,'Mina pushes trolley into children’s room','e1',['e24'],'move','asserted'),
(220,'trolley has no collected load yet',None,['e24'],'state','asserted'),
(227,'children search window nook','e5',['e16'],'perceive','asserted'),
(233,'Jun checks behind cushions','e2',['e16'],'perceive','asserted'),
(239,'Mina looks beneath bench','e1',['e16'],'perceive','asserted'),
(244,'children find mitten board books crayon','e5',['e31','e32','e33'],'perceive','asserted'),
(253,'crayon has dinosaur shape',None,['e33'],'state','asserted'),
(258,'found objects go on trolley',None,['e34'],'move','asserted'),
(264,'found objects include Jun’s whale book',None,['e16'],'state','negated'),
(266,'Jun rejects found objects as desired book','e2',[],'speak','asserted'),
(268,'children search more library areas','e5',['e16'],'perceive','asserted'),
(282,'Mina runs finger along book spines','e1',['e39'],'move','asserted'),
(291,'Jun crouches','e2',[],'state','asserted'),
(293,'Jun inspects lowest shelf','e2',['e41'],'perceive','desired'),
(297,'Jun whispers book title to himself','e2',['e19'],'speak','asserted'),
(307,'book answers Jun in as-if comparison','e16',[],'speak','hypothetical'),
(315,'trolley carries collected book stack',None,['e42'],'state','asserted'),
(322,'Mina intermittently stops trolley','e1',['e24'],'move','asserted'),
(327,'a trolley wheel squeaks',None,['e73'],'other','asserted'),
(329,'Mina steadies book stack','e1',['e42'],'other','asserted'),
(336,'children examine collected books','e5',['e42'],'perceive','asserted'),
(341,'children collected the examined books','e5',['e42'],'obtain','asserted'),
(344,'a collected book has a blue whale on its cover',None,['e42'],'state','negated'),
(353,'Jun mouth turns down',None,['e44'],'move','asserted'),
(356,'grandmother gives closing-time departure rule','e3',[],'speak','reported'),
(360,'Jun and grandmother leave at closing','e72',[],'move','desired'),
(364,'library reaches scheduled closure',None,['e6'],'state','hypothetical'),
(367,'Mina and Jun have remaining search time','e5',[],'state','reported'),
(370,'Mina reassures Jun about time','e1',[],'speak','asserted'),
(372,'children search reading tables','e5',['e16'],'perceive','asserted'),
(381,'Jun spots paper star on floor','e2',['e47'],'perceive','asserted'),
(390,'Jun picks up paper star','e2',['e47'],'obtain','asserted'),
(394,'Jun rubs bookmark crease flat','e2',['e48'],'other','asserted'),
(404,'Jun identifies bookmark','e2',[],'speak','asserted'),
(406,'bookmark was inside whale book',None,['e47'],'state','reported'),
(412,'Mina looks at high shelves','e1',['e50'],'perceive','asserted'),
(424,'silver point glimmers between books',None,['e51'],'other','asserted'),
(429,'silver point is sought clue',None,['e51'],'state','hypothetical'),
(433,'Jun asks whether point indicates book','e2',[],'speak','asserted'),
(435,'Mina tentatively accepts clue identity','e1',[],'state','reported'),
(440,'children climb','e5',[],'move','negated'),
(442,'Mina glances at atlas','e1',['e7'],'perceive','asserted'),
(452,'Mina previously imagined atlas activity','e1',[],'state','asserted'),
(453,'Mina opens atlas at home','e1',['e7'],'other','hypothetical'),
(458,'Mina draws moon in notebook','e1',['e10'],'other','hypothetical'),
(473,'clock displays 5:48',None,['e56'],'state','asserted'),
(478,'Mina asks librarian to reserve atlas','e1',[],'speak','hypothetical'),
(482,'librarian sets atlas aside','e4',['e7'],'move','hypothetical'),
(488,'children continue searching','e5',['e16'],'perceive','hypothetical'),
(493,'librarian checks out family','e4',[],'other','asserted'),
(505,'silver point belongs to bookmark',None,['e51'],'state','hypothetical'),
(510,'silver point is something else',None,['e51'],'state','hypothetical'),
(514,'Mina takes atlas from desk','e1',['e7'],'obtain','asserted'),
(522,'Mina carries atlas to librarian','e1',['e7'],'move','asserted'),
(529,'librarian returns atlas to shelf','e4',['e7'],'move','desired'),
(536,'Mina requests atlas reshelving','e1',[],'speak','asserted'),
(538,'Mina needs to continue search with Jun','e1',[],'state','reported'),
(541,'Mina continues searching with Jun','e1',['e16'],'perceive','desired'),
(546,'Alvarez studies Mina’s face','e4',['e59'],'perceive','asserted'),
(550,'Alvarez nods','e4',[],'other','asserted'),
(555,'Alvarez gets library ladder','e4',['e60'],'obtain','desired'),
(560,'children wait','e5',[],'state','asserted'),
(562,'Jun grips trolley handle','e2',['e25'],'state','asserted'),
(567,'Jun previously believed he had shelved book','e2',[],'state','reported'),
(569,'Jun put whale book back','e2',['e16'],'move','reported'),
(574,'Jun explains prior book placement','e2',[],'speak','asserted'),
(577,'Jun reaches picture-book shelf','e2',['e61'],'other','negated'),
(584,'Jun put whale book on astronomy shelf','e2',['e16'],'move','reported'),
(592,'pictured whale has stars around it',None,['e21'],'state','reported'),
(597,'Mina looks up at silver point','e1',['e51'],'perceive','asserted'),
(606,'whale book probably lies on high shelves',None,['e16'],'state','hypothetical'),
(609,'Alvarez returns with ladder','e4',['e60'],'move','asserted'),
(615,'Alvarez climbs ladder','e4',[],'move','asserted'),
(622,'children watch bookmark tremble','e5',['e47'],'perceive','asserted'),
(626,'bookmark trembles',None,['e47'],'move','asserted'),
(630,'Alvarez eases thick books apart','e4',['e52'],'move','asserted'),
(638,'blue book cover slides forward',None,['e62'],'move','asserted'),
(649,'Alvarez reads recovered book title','e4',['e19'],'speak','asserted'),
(651,'Jun makes cheer-like sound','e2',['e63'],'other','asserted'),
(660,'Alvarez brings whale book down','e4',['e16'],'move','asserted'),
(665,'Alvarez hands whale book to Jun','e4',['e16'],'transfer','asserted'),
(673,'bookmark is still tucked inside book',None,['e47'],'state','asserted'),
(679,'Jun had left bookmark inside book','e2',['e47'],'move','asserted'),
(687,'Alvarez checks whale book out to Jun','e4',['e16'],'transfer','asserted'),
(694,'Mina returns trolley to storage place','e1',['e24'],'move','asserted'),
(703,'trolley wheels click over tiles',None,['e26'],'other','asserted'),
(712,'atlas is back on display shelf',None,['e7'],'state','asserted'),
(720,'grandmother opens whale book','e3',['e16'],'other','asserted'),
(728,'Jun leans against grandmother','e2',[],'move','asserted'),
(734,'Mina leans in','e1',[],'move','asserted'),
(744,'painted whale sails through sky','e21',[],'move','asserted'),
(755,'paper bookmark rests against depicted tail',None,['e47'],'state','asserted'),
]
for w,label,actor,patients,typ,fact in EVENTS:
    if w not in {26,172,364,569}: E(w,label,actor,patients,typ,fact)
for word,source,role in [(26,105,'reference'),(118,105,'reference'),(172,163,'action'),(364,105,'reference'),(569,584,'action'),(643,126,'action')]:
    a.mention_event(f'ev{source+1}',word,role=role,note='Same identified schedule, proposed loan, prior placement or title content; not an additional occurrence.')

# Further hand-authored roles/features follow; no lexical tagging is inferred.
ROLES={
4:{'actor':[3],'patient':[7],'location':[14]},9:{'actor':[8],'patient':[7]},16:{'actor':[15],'patient':[17],'location':[20]},23:{'actor':[22],'patient':[24]},29:{'actor':[27],'patient':[31]},34:{'actor':[27],'recipient':[36]},
40:{'actor':[39]},44:{'patient':[43]},46:{'actor':[39]},49:{'patient':[47]},53:{'patient':[51]},58:{'actor':[56],'recipient':[59]},61:{'actor':[59],'patient':[63]},65:{'actor':[59],'patient':[68]},72:{'patient':[71]},74:{'actor':[73]},78:{'actor':[77],'patient':[76]},82:{'actor':[80],'patient':[76]},85:{'actor':[84],'patient':[86],'location':[89]},94:{'patient':[92],'location':[94]},98:{'actor':[96],'location':[102]},105:{'patient':[104]},
109:{'actor':[108],'beneficiary':[110]},111:{'actor':[110],'patient':[112]},114:{'actor':[113]},116:{'actor':[115]},122:{'patient':[120],'content':[123,124,125,126,127,128,129]},126:{'actor':[124],'recipient':[129]},133:{'actor':[130],'patient':[134],'location':[138]},139:{'actor':[130],'recipient':[140],'content':[142]},147:{'actor':[146],'location':[150]},151:{'patient':[150],'content':[153]},155:{'actor':[154],'destination':[157,158]},163:{'actor':[162],'patient':[167,173]},169:{'actor':[162],'instrument':[167]},176:{'actor':[174,175]},177:{'recipient':[178],'patient':[180]},181:{'actor':[185],'patient':[184],'location':[188]},186:{'actor':[185],'patient':[184]},190:{'patient':[193],'location':[196]},198:{'actor':[197]},200:{'actor':[199]},202:{'actor':[201],'patient':[205],'destination':[210]},214:{'actor':[212],'patient':[215]},218:{'patient':[221],'destination':[225]},220:{'patient':[221]},
227:{'actor':[226],'location':[230]},233:{'actor':[232],'location':[236]},239:{'actor':[238],'location':[242]},244:{'actor':[243],'patient':[246,249,252]},253:{'patient':[252]},258:{'patient':[257],'destination':[261]},264:{'patient':[264]},266:{'actor':[265]},268:{'actor':[267],'location':[271,273,276]},282:{'actor':[281],'patient':[284],'path':[289]},291:{'actor':[290]},293:{'actor':[290],'patient':[296]},297:{'actor':[290],'content':[299],'recipient':[301]},307:{'actor':[305]},315:{'patient':[318,320],'carrier':[312]},322:{'actor':[321],'patient':[323]},327:{'patient':[326]},329:{'actor':[321],'patient':[331],'instrument':[334]},336:{'actor':[335],'patient':[339]},341:{'actor':[340],'patient':[339]},344:{'patient':[343],'excluded_content':[347]},353:{'patient':[352]},356:{'actor':[355]},360:{'actor':[357]},367:{'actor':[365],'content':[368]},370:{'actor':[369]},
372:{'actor':[371],'location':[375]},381:{'actor':[380],'patient':[385],'location':[388]},390:{'actor':[389],'patient':[391]},394:{'actor':[389],'patient':[396],'instrument':[400]},404:{'actor':[403],'content':[402]},406:{'patient':[405],'container':[410]},412:{'actor':[411],'patient':[416]},424:{'patient':[423],'location':[428]},429:{'subject':[430],'comparison':[431]},433:{'actor':[432]},435:{'actor':[434],'content':[436]},440:{'actor':[438]},442:{'actor':[441],'patient':[446],'location':[449]},452:{'actor':[450]},453:{'patient':[454],'location':[456]},458:{'patient':[460],'location':[464,467]},473:{'patient':[469]},478:{'actor':[476],'recipient':[479,480]},482:{'actor':[479,480],'patient':[484]},488:{'actor':[487]},493:{'actor':[491],'recipient':[496],'location':[499]},505:{'subject':[503],'comparison':[507]},510:{'subject':[503],'comparison':[511]},
514:{'actor':[513],'patient':[517],'source':[520]},522:{'actor':[513],'patient':[523],'destination':[525,526]},529:{'actor':[528],'patient':[530],'destination':[534]},536:{'actor':[535]},538:{'actor':[537]},541:{'actor':[537],'companion':[543]},546:{'actor':[544,545],'patient':[548]},550:{'actor':[544,545]},555:{'actor':[554],'patient':[557]},560:{'actor':[559]},562:{'actor':[561],'patient':[565]},567:{'actor':[566]},584:{'actor':[583,568],'patient':[585,571],'destination':[589]},574:{'actor':[573]},577:{'actor':[575],'patient':[581]},592:{'patient':[591],'surrounding':[593]},597:{'actor':[596],'patient':[602]},606:{'patient':[604],'location':[606]},609:{'actor':[607,608],'patient':[613]},615:{'actor':[607,608],'instrument':[613]},622:{'actor':[619,621],'patient':[625]},626:{'patient':[625]},630:{'actor':[629],'patient':[633]},638:{'patient':[637]},649:{'actor':[647,648],'content':[640,641,642,643,644,645,646]},651:{'actor':[650],'patient':[653]},660:{'actor':[658,659],'patient':[662]},665:{'patient':[666],'recipient':[668]},673:{'patient':[670],'container':[674]},679:{'actor':[677],'patient':[680]},687:{'actor':[685,686],'patient':[689],'recipient':[692]},694:{'actor':[693],'patient':[696],'destination':[700]},703:{'patient':[702],'location':[707]},712:{'patient':[710],'location':[716]},720:{'actor':[719],'patient':[723],'location':[726]},728:{'actor':[727],'landmark':[731]},734:{'actor':[733]},744:{'actor':[743],'location':[747]},755:{'patient':[754],'landmark':[758]},
}
for w,roles in ROLES.items():
    event=a.events[f'ev{w+1}']
    for role,mentions in roles.items():
        for mention in mentions:
            a._binding(mention,event['event_id'],role,a.words[mention]['scope_id'])
            if 'event_id' not in a.words[mention]:
                F(mention,event_id=event['event_id'],event=event['event'],role=role)
for w,recipient in [(34,'e12'),(58,'e1'),(74,'e1'),(114,'e2'),(116,'e2'),(126,'e70'),(176,'e5'),(177,'e1'),(200,'e4'),(266,'e1'),(297,'e2'),(356,'e2'),(370,'e2'),(404,'e1'),(433,'e1'),(478,'e4'),(493,'e57'),(536,'e4'),(574,'e1'),(665,'e2'),(687,'e2')]:
    event=a.events[f'ev{w+1}'];event['recipient_id']=recipient
    F(w,recipient_id=recipient)
for w,tools in [(169,['e24']),(282,['e39']),(329,['e43']),(394,['e49']),(615,['e60'])]:
    a.events[f'ev{w+1}']['instruments']=tools; F(w,instruments=tools)
# Relative who denotes the title's character. Quantified book/none are variables,
# not the entire book group squeezed into an individual entity slot.
for w in [125,642]:
    a.entities['e21']['mentions'].append(w);F(w,entity_id='e21',entity_name=a.entities['e21']['name'],entity=a.entities['e21']['type'])
for w in [339,343]:
    a.entities['e42']['mentions'].remove(w)
    for key in ['entity_id','entity_name','entity']: a.words[w].pop(key,None)
F(430,antecedent_id='e51',mention_form='demonstrative_pronoun')

PROPS=[
(1,'Mina has the moon atlas available for study.',[7,9,23,29],'s23'),
(2,'Mina sketches the moon craters tonight.',[27,29,31,32],'s23'),
(3,'Mina shows her sketches to her class tomorrow.',[34,36,37],'s23'),
(4,'Jun cannot locate his selected whale book.',[69,71,72,84,89,92,93,94],'s1'),
(5,'Grandmother reads Jun’s selected whale book tonight.',[76,78,80,82,83],'s25'),
(6,'Mina helps Jun find the whale book before closing.',[108,109,110,111,112,115,116,117,118],'s3'),
(7,'Mina and Jun use the borrowed trolley for their search.',[162,163,167,169,170,172,173],'s5'),
(8,'Any stray books the children find go on the trolley.',[181,182,184,185,186,188],'s29'),
(9,'All four trolley wheels stay on the floor.',[190,191,192,193,196],'s7'),
(10,'Mina later collects the atlas from the desk.',[212,214,215,216],'s30'),
(11,'None of the collected books has a blue whale on its cover.',[335,336,339,341,343,344,346,347,350]),
(12,'Jun and grandmother leave when the library closes.',[355,356,357,358,360,364],'s32'),
(13,'Time remains before closing.',[365,366,367,368],'s11'),
(14,'Jun spots and picks up the paper star on the floor.',[380,381,385,388,389,390,391]),
(15,'Jun’s bookmark was inside the whale book.',[401,402,405,406,407,410],'s13'),
(16,'The silver point is part of Jun’s bookmark.',[422,423,429,430,431,435,436,505,507],'s35'),
(17,'The whale book is at the high shelves indicated by the silver point.',[423,435,503,584,589,602,604,605,606],'s21'),
(18,'Mina and Jun climb the shelves.',[438,439,440],'s15'),
(19,'Mina opens the atlas at home and draws the moon in her notebook.',[453,454,456,458,460,464,467],'s33'),
(20,'Alvarez sets aside the atlas while the children search.',[476,478,479,480,482,484,487,488],'s34'),
(21,'The silver point is something other than the bookmark.',[503,509,510,511,512],'s35'),
(22,'Alvarez puts the moon atlas back on a shelf.',[527,528,529,530,534],'s16'),
(23,'Mina continues looking for the whale book with Jun.',[537,538,540,541,543],'s17'),
(24,'Alvarez obtains the ladder.',[554,555,557],'s18'),
(25,'Jun has put the whale book back.',[566,567,568,569,571,572],'s36'),
(26,'Jun reaches the picture-book shelf.',[575,576,577,581],'s20'),
(27,'Jun put the whale book on the astronomy shelf.',[583,584,585,589],'s20'),
(28,'The depicted whale has stars around it.',[591,592,593,594,595],'s37'),
(29,'The retrieved blue book is The Whale Who Sang to the Moon.',[637,638,640,641,642,643,644,645,646,649]),
(30,'The whale book is checked out to Jun before closing.',[681,682,683,684,685,686,687,689,692]),
(31,'Jun’s bookmark is still inside the recovered book where he left it.',[669,670,672,673,674,675,676,677,678,679,680]),
(32,'Mina’s atlas is back on the display shelf.',[708,710,711,712,716]),
(33,'Grandmother opens the whale book and both children lean in.',[719,720,723,727,728,731,733,734]),
(34,'Jun and Mina are six and nine respectively.',[47,49,51,53]),
(35,'Jun habitually asks Mina for help reaching and reading.',[54,55,56,57,58,59,61,63,65,68],'s24'),
(36,'Mina borrows the atlas before closing.',[22,23,24,25,26],'s23'),
(37,'The title is The Whale Who Sang to the Moon.',[123,124,125,126,127,128,129,297,299,640,641,642,643,644,645,646]),
(38,'Jun cannot reach the picture-book shelf.',[575,576,577,581],'s20'),
(39,'The whale book answers Jun.',[302,303,305,306,307],'s31'),
(40,'The whale book is by the window.',[89,92,93,94],'s2'),
(41,'The just-found objects include Jun’s selected whale book.',[243,244,246,249,252,262,263,264],'s9'),
(42,'At least one collected book has a blue whale on its cover.',[338,339,343,344,346,347,350]),
(43,'The just-found objects do not include Jun’s selected whale book.',[243,244,246,249,252,262,263,264],'s9'),
]
for row in PROPS: P(*row)

# Explicitly located states, changes and claims. B keeps figure/scope/status
# together; no final property is copied back onto earlier mentions.
for w,entity,landmark,relation in [
(10,'e7','e8','on'),(18,'e7','e9','under'),(87,'e16','e17','by'),(99,'e3','e18','at'),
(135,'e16','e20','around'),(148,'e21','e22','beneath'),(194,'e26','e27','on'),
(207,'e7','e18','on'),(222,'e24','e20','inside'),(234,'e2','e29','behind'),(240,'e1','e30','beneath_search_region'),
(259,'e34','e24','on'),(277,'e37','e38','beside'),(285,'e39','e40','along'),
(376,'e47','e46','near'),(386,'e47','e27','on'),(417,'e50','e71','above'),(425,'e51','e52','between'),
(447,'e7','e18','on'),(461,'e10','e55','planned_depiction_in'),(470,'e56','e18','above'),
(497,'e4','e18','at'),(586,'e16','e46','on'),(724,'e16','e66','beneath'),(729,'e2','e67','against'),
(737,'e21','e68','depicted_on'),(745,'e21','e22','through'),(756,'e47','e69','against_depicted_tail')]:
    F(w,spatial_configuration=B(w,entity,{'landmark':landmark,'relation':relation}))
# Below the bench is the examined region, not a claim Mina's entire body was there.
F(234,spatial_configuration=B(234,'e16',{'landmark':'e29','relation':'behind','query_only':True},fact='hypothetical'))
F(240,spatial_configuration=B(240,'e16',{'landmark':'e30','relation':'beneath','query_only':True},fact='hypothetical'))
F(194,spatial_configuration=B(194,'e26',{'landmark':'e27','relation':'on'},fact='desired'))
for w,entity,holder in [(16,'e7','e1'),(85,'e16','e2'),(133,'e16','e2'),(390,'e47','e2'),(514,'e7','e1'),(665,'e16','e2')]:
    F(w,possession_holder=B(w,entity,{'holder':holder}))
F(218,possession_borrower=B(218,'e24',{'borrower':'e5'}),possession_lender=B(218,'e24',{'lender':'e4'}),transfer_kind=B(218,'e24','loan'))
F(177,reference_metonymic_link={'literal':'e25','intended':'e24','relation':'handle_handoff_enables_trolley_use'})
F(220,object_fill_state=B(220,'e24',{'state':'empty','domain':'collected_load'}))
F(258,spatial_support=B(258,'e34',{'supported_by':'e24'}))
F(315,spatial_support=B(315,'e42',{'supported_by':'e24'}))
F(329,object_stability=B(329,'e42',{'action':'steadied','event_id':'ev330'}))
F(394,event_state_change=B(394,'e48',{'before':'creased','after':'rubbed_flat','event_id':'ev395'}),event_effector=B(394,'e2',{'effector':'e49'}))
F(407,containment_direct=B(407,'e47',{'container':'e16'}))
F(673,containment_direct=B(673,'e47',{'container':'e16','continuity_claim':'still_where_left'}))
F(712,spatial_configuration=B(712,'e7',{'landmark':'e58','relation':'on','transition_not_narrated':True}))
F(687,transfer_kind=B(687,'e16','library_loan'),possession_borrower=B(687,'e16',{'borrower':'e2'}),transfer_recipient=B(687,'e16',{'recipient':'e2'}))
F(665,transfer_completion=B(665,'e16',{'completed':True,'recipient':'e2','event_id':'ev666'}))
F(720,object_openness=B(720,'e16','open'))
F(694,motion_return_destination=B(694,'e24',{'destination':'e64'}))
F(615,motion_direction=B(615,'e4',{'interpretation':'upward','event_id':'ev616'}),event_instrument_binding=B(615,'e60',{'used_by':'e4','event_id':'ev616'}))
F(660,motion_direction=B(660,'e16',{'interpretation':'downward','event_id':'ev661'}))
F(638,motion_direction=B(638,'e62',{'interpretation':'forward','event_id':'ev639'}))
F(577,access_reachability=B(577,'e61',{'actor':'e2','reachable':False},fact='reported'))
for w,part,whole in [(20,'e9','e1'),(43,'e13','e2'),(180,'e25','e24'),(193,'e26','e24'),(284,'e39','e1'),(326,'e73','e24'),(334,'e43','e1'),(352,'e44','e2'),(396,'e48','e47'),(400,'e49','e2'),(423,'e51','e47'),(464,'e55','e54'),(548,'e59','e1'),(637,'e62','e16'),(731,'e67','e3'),(740,'e68','e16'),(758,'e69','e21')]:
    F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
for w,entity,color in [(44,'e13','pink'),(145,'e21','blue'),(383,'e47','silver'),(422,'e51','silver'),(502,'e51','silver'),(601,'e51','silver'),(636,'e62','blue'),(749,'e23','silver')]:
    F(w,appearance_color=B(w,entity,color))
for w in [384,753]: F(w,material_composition=B(w,'e47','paper'))
F(253,object_shape=B(253,'e33',{'resembles_kind':'dinosaur','actual_dinosaur':False}))
F(317,spatial_configuration=B(317,'e42',{'arrangement':'crooked_stack'}))
F(327,object_sound_level=B(327,'e73','squeaking'))
F(703,object_sound_level=B(703,'e26','soft_clicking'))
F(424,lexical_gloss='A visible point reflects or catches light; no light-emitting bookmark is asserted.')
F(307,figurative_mapping={'target_id':'e16','source_image':'answering_speaker','kind':'personification_in_as_if_comparison','literal_event':False})
F(654,figurative_mapping={'target_id':'e63','source_image':'tiny_cheer','kind':'simile','literal_identity':False})
# The final physical bookmark lies on the printed whale-tail region, not on an
# actual animal. The picture's first-page image is not asserted to be the cover.
F(756,reference_metonymic_link={'literal':'e69','intended_surface':'e68','relation':'depicted_part_for_printed_page_region'})
F(142,lexical_gloss='An image in or on the whale book; the text does not fix this occurrence to the cover rather than an interior page.')

# Source continuity is a recorded uncertainty rather than a generated repair.
a.feature([385,402,423,507,625,670,754],evidence=[381,385,388,390,391,401,402,405,406,423,625,670,672,673,677,679,680,754],note='One text-intended bookmark identity is retained. Picking it up from the floor and later saying it was still inside the book leave unexplained continuity. No second bookmark, reinsertion or unseen transfer is added.',evidence_resolution_status='identity_intended_location_history_unresolved',evidence_missing={'needed':'transition_or_source_correction_between_floor_pickup_and_still_inside_book'})
a.feature(712,evidence=[14,202,205,210,514,517,520,529,534,710,712,716],note='Actual final atlas-on-display-shelf state is explicit. Its reshelving transition and performer are not narrated; initial display table and final display shelf remain distinct. No atlas checkout or completed reservation is inferred.',evidence_resolution_status='endpoint_known_transition_unreported')

# Claims and attitudes retain their owners, target propositions and local scope.
F(9,goal_owner_id='e1',goal_content_id='p1',goal_status='active',goal_polarity='achieve',goal_scope_bundle={'owner_id':'e1','intention_event_id':'ev10','scope_id':'s0','assertion_status':'asserted'})
F(21,scope_operator='conditional',conditional_antecedent_id='p36',conditional_consequent_id='p2',plan_contingency={'condition':'p36','then':['p2','p3']})
F(78,goal_owner_id='e2',goal_content_id='p5',goal_beneficiary_ids=['e2'],goal_status='active',intention_publicity='communicated')
F(116,promise_content_id='p6',promise_beneficiary_id='e2',plan_commitment_status='promised',goal_owner_id='e1',goal_content_id='p6',goal_deadline={'anchor':'time_closing','relation':'before'},obligation_debtor_id='e1',obligation_creditor_id='e2',obligation_content_id='p6',obligation_status='accepted_commitment')
# The commitment and reporting speech describe one utterance, with distinct roles.
a.events['ev117'].update(event_type='other',event='Mina undertakes help-before-closing commitment')
for row in a.words:
    if row.get('event_id')=='ev117': row['event']=a.events['ev117']['event']
F(116,event_type='other',event=a.events['ev117']['event'],utterance_id='ev115',obligation_source={'kind':'promise_utterance','utterance_id':'ev115','commitment_event_id':'ev117'})
F(171,permission_grantor_id='e4',permission_recipient_id='e5',permission_content_id='p7',permission_status='granted_for_search',modal_base={'kind':'permission','holder':'e5'})
F(181,obligation_debtor_id='e5',obligation_creditor_id='e4',obligation_content_id='p8',obligation_status='instructed')
F(190,obligation_debtor_id='e5',obligation_creditor_id='e4',obligation_content_id='p9',obligation_status='instructed')
F(198,knowledge_claim_holder_id='e1',knowledge_claim_content_id='p9',epistemic_source_kind='stated_familiarity',evidence_resolution_status='scope_may_include_both_trolley_instructions')
F(214,goal_owner_id='e1',goal_content_id='p10',plan_commitment_status='possible_not_committed')
F(227,cooperation_goal_id='p6',social_relation_participants={'members':['e1','e2']},cooperation_commitment='joint_search_observed')
F(233,event_divided_labor=B(233,'e5',{'jun_task':'ev234','mina_task':'ev240'}))
F(344,quantifier_binding={'quantifier':'no','variable':'collected_book','restriction':'e42','predicate':'blue_whale_on_cover'},proposition_polarity='negative',negation_scope_id='p42',evidence_coverage_domain={'domain':'e42','exhaustive':True})
F(356,evidence_report_depth=2,evidence_assertor_id='e3',utterance_content_id='p12')
F(358,obligation_debtor_id='e72',obligation_creditor_id='e3',obligation_content_id='p12',obligation_status='reported_requirement',modal_base={'kind':'necessity','source_id':'e3','content_id':'p12'})
F(367,belief_holder_id='e1',belief_content_id='p13',belief_polarity='accepts',epistemic_attitude_kind='asserted_assessment')
F(406,mental_memory_holder_id='e2',mental_memory_content_id='p15',epistemic_source_kind='memory',assertion_status='attributed_claim')
F(429,question_requested_slot='identity_or_location_of_sought_book_clue',question_answer_status='tentative_answer_then_visual_confirmation',truth_commitment='suspended')
F(430,reference_metonymic_link={'literal':'e51','intended':'e16','relation':'visible_bookmark_point_for_sought_book_location'})
F(435,belief_holder_id='e1',belief_content_id='p17',belief_certainty='tentative',belief_polarity='accepts',epistemic_source_kind='visual_clue',epistemic_scope_bundle={'holder_id':'e1','attitude_event_id':'ev436','scope_id':'s15','assertion_status':'attributed_claim'})
F(436,propositional_antecedent_id='p17')
F(439,modal_base={'kind':'practical_or_normative_constraint','holder':'e5','content_id':'p18'},polarity='negative',negation_scope_id='p18')
a.feature(439,evidence=[415,416,429,435,438,439,440,555,557,609,613,615],note='Cannot climb is explicitly a constraint, but the text does not settle physical inability versus a safety/permission rule. The ladder solution is actual; no exact height or unsupported universal prohibition is added.',evidence_resolution_status='modal_source_ambiguous')
F(452,imaginer_id='e1',imagined_content_id='p19',imagined_world_id='w_mina_study',imagination_function='anticipated_personal_activity')
F(range(453,468),semantic_world_id='w_mina_study',evidence_world_status='imagined')
F(478,reasoner_id='e1',reasoning_mode='considered_plan',reasoning_content_id='p20',plan_commitment_status='considered_not_executed')
F(504,belief_holder_id='e1',epistemic_attitude_kind='uncertainty',epistemic_alternatives=['p16','p21'],belief_certainty='uncertain')
F(508,disjunction_alternatives=['p16','p21'],discourse_relation_kind='alternative')
F(538,goal_owner_id='e1',goal_content_id='p23',goal_status='active',goal_polarity='achieve',intention_publicity='communicated',goal_beneficiary_ids=['e2'])
a.feature(536,evidence=[9,29,452,453,458,473,478,482,493,514,529,538,541,543],note='Requesting reshelving while explicitly continuing the search supports a current tradeoff favoring the help commitment. It does not prove Mina never studies the atlas later.',goal_tradeoff={'prefer':'p23','defer_current_visit':'p1','assertion_status':'candidate'})
F(555,offer_content_id='p24',plan_commitment_status='announced',intention_publicity='communicated')
F(567,belief_holder_id='e2',belief_content_id='p25',epistemic_attitude_kind='remembered_belief',epistemic_time_scope={'phase':'before_current_search'},epistemic_scope_bundle={'holder_id':'e2','attitude_event_id':'ev568','scope_id':'s19','assertion_status':'attributed_claim'})
F(584,mental_memory_holder_id='e2',mental_memory_event_id='ev585',mental_memory_content_id='p27',epistemic_source_kind='memory',evidence_assertor_id='e2')
F(582,discourse_relation_kind='reason_result',discourse_explanation_target='p27',reasoner_id='e2',reasoning_premise_ids=['p38'],reasoning_conclusion_id='p27',reasoning_rule_kind='practical_alternative_after_unreachability')
F(592,discourse_explanation_target='p27',discourse_implicit_relation={'interpreter_id':'e2','kind':'topic_based_placement_explanation','status':'text_supported'},semantic_world_id='w_whale_book')
F(605,belief_holder_id='e1',belief_content_id='p17',belief_certainty='probable',epistemic_source_kind='testimony_plus_visual_clue',epistemic_source_entity_id='e2',reasoner_id='e1',reasoning_premise_ids=['p27','p16'],reasoning_conclusion_id='p17',assertion_status='attributed_claim')
F(649,evidence_observation_channel='reading_visible_title',evidence_access_holder='e4',evidence_resolution_status='book_identity_confirmed',supporting_proposition_ids=['p29'])
F(687,intention_vs_action_alignment={'intention':'p6','outcome':'p30','alignment':'help_and_recovery_before_closing_observed'},goal_owner_id='e1',goal_content_id='p6',goal_status='achieved',goal_termination_event_id='ev688')
a.feature(353,evidence=[72,336,343,344,351,352,353,354,355,360],note='Downturned mouth during unsuccessful search supports possible discouragement, not a stated internal emotion or intensity.',affect_experiencer_id='e2',affect_observer_attribution={'kind':'discouragement','source':'annotator','assertion_status':'candidate'})
a.feature(651,evidence=[637,649,650,651,653,654,657],note='Cheer-like vocal behavior after recognition is explicit. Possible pleasure/relief is an interpretation, not an exact affect measure.',affect_experiencer_id='e2',affect_expression_channel='cheer_like_vocalization',affect_observer_attribution={'kind':'pleasure_or_relief','source':'annotator','assertion_status':'candidate'})

# Actual outer communication acts without an overt reporting verb have their
# own narrated scope; they do not replace the quoted-content event participants.
for w,speaker,audience,label in [(161,'e1','e4','request trolley loan'),(355,'e2','e1','report grandmother departure rule'),(434,'e1','e2','give tentative answer and climbing constraint'),(551,'e4','e1','accept request and offer ladder'),(603,'e1','e2','infer likely book location')]:
    a.event(f'ev{w+1}',w,label,type='speak',actor=speaker,recipient=audience,scope='s0',primary=False,factuality='asserted')
SPEECH=[
(74,'e2','e1','report','p4'),(114,'e1','e2','promise','p6'),(161,'e1','e4','request','p7'),
(176,'e4','e5','permission_and_instruction','p7'),(200,'e1','e4','acknowledge','p9'),
(266,'e2','e1','reject_candidate','p43'),(297,'e2','e2','self_directed_title_recital','p37'),
(355,'e2','e1','report_requirement','p12'),(370,'e1','e2','reassure','p13'),
(404,'e2','e1','identify_and_recall','p15'),(433,'e2','e1','question','p17'),
(434,'e1','e2','tentative_answer','p17'),(536,'e1','e4','request','p22'),
(551,'e4','e1','accept_and_offer','p24'),(574,'e2','e1','explain_placement','p27'),
(603,'e1','e2','inference','p17'),(649,'e4','e5','read_identifying_title','p29')]
for w,speaker,audience,act,pid in SPEECH:
    eid=f'ev{w+1}'
    F(w,utterance_id=eid,speaker_id=speaker,addressee_ids=[audience],speech_act_kind=act,communication_channel='speech',utterance_content_id=pid,communication_scope_bundle={'speaker_id':speaker,'utterance_event_id':eid,'scope_id':'s0','assertion_status':'asserted'})
for sid,lo,hi,holder in QUOTES:
    utterance={ 's1':74,'s2':74,'s3':114,'s4':114,'s5':161,'s6':176,'s7':176,'s8':200,'s9':266,'s10':355,'s11':370,'s12':404,'s13':404,'s14':433,'s15':434,'s16':536,'s17':536,'s18':551,'s19':574,'s20':574,'s21':603,'s22':649}[sid]
    a.scopes[sid]['utterance_event_id']=f'ev{utterance+1}'
F(434,dialogue_response_to_id='ev434',dialogue_turn_function='tentative_answer',discourse_answer_relation={'question':'ev434','answer':'p17','kind':'tentative'})
F(551,dialogue_response_to_id='ev537',request_acceptance_status='accepted_with_ladder_offer')
F(536,request_action_id='ev530')
F(161,request_action_id='ev164')
F(176,dialogue_response_to_id='ev162',request_acceptance_status='granted')

# Explicit clock readings and relation to closing; no absolute date/time zone
# or completed closure is fabricated.
for w,label,hour,minute in [(1,'time_start',5,0),(309,'time_twenty',5,20),(474,'time_fortyeight',5,48),(682,'time_checkout',5,58),(107,'time_closing',6,0)]:
    F(w,time_expression_id=label,temporal_granularity='minute' if minute else 'hour',event_time_interval={'clock':'local_12_hour','hour':hour,'minute':minute,'meridiem':'unspecified','day_anchor':'story_day','role':'scheduled_closing' if w==107 else 'narrated_clock_reference'})
for w in [32,83]: F(w,temporal_deixis='tonight',time_anchor_id='story_day')
F(37,temporal_deixis='next_day',time_anchor_id='story_day')
F([25,117],temporal_bound_cue='upper_bound_exclusive',time_anchor_id='time_closing')
F(474,temporal_remaining={'value':12,'unit':'min','from':'time_fortyeight','until':'time_closing','derivation':'6:00 minus 5:48 within same stated closing period'})
F(682,temporal_remaining={'value':2,'unit':'min','from':'time_checkout','until':'time_closing','derivation':'6:00 minus 5:58 within same closing period'})
F(49,cardinal_value=6,measure_entity_id='e2',attributes=[{'name':'age','value':'six_years'}])
F(53,cardinal_value=9,measure_entity_id='e1',attributes=[{'name':'age','value':'nine_years'}])
F(192,cardinal_value=4,counted_domain={'kind':'wheel','whole_id':'e24'})
F(247,cardinal_value=2,measure_entity_id='e32',counted_domain={'kind':'board_book'})
F(333,cardinal_value=1,counted_domain={'kind':'hand','owner_id':'e1'})
F(426,cardinal_value=2,measure_entity_id='e52',counted_domain={'kind':'thick_volume'})
F(739,ordinal_rank=1,numeral_syntactic_role='page_order')
F(57,temporal_frequency_class='often',narrative_frequency_mode='recurring_help_requests')
F(324,temporal_frequency_class='whenever_condition_occurs',temporal_signal_relation='each_squeak_triggers_stop')
F(133,narrative_order_mode='retrospective_background',narrative_time_frame='before_missing_book_report')
F(452,narrative_order_mode='retrospective_imagination',narrative_time_frame='earlier_anticipated_home_activity')
F(584,narrative_order_mode='reported_earlier_placement',narrative_time_frame='before_current_search')
for w,left,right,rel in [(237,233,239,'overlap'),(558,560,562,'overlap'),(627,626,630,'overlap'),(751,744,755,'simultaneous_depiction_and_physical_reading_view')]:
    F(w,event_time_relation={'left':f'ev{left+1}','right':f'ev{right+1}','relation':rel})
F(45,causal_parent=B(45,'e13',{'cause':'ev47','effect':'ev45'}))
F(55,discourse_relation_kind='explanation',discourse_explanation_target='p35',supporting_proposition_ids=['p34'])

# Morphology and syntax: source forms and explicit local constructions, never
# semantic roles inferred from a blanket nearest-noun rule.
for r in a.words:
    w,t,pos=r['word_index'],r['token'].casefold(),r['pos']
    if pos=='det':
        if t in {'the','a','an'}: F(w,determiner_kind='definite_article' if t=='the' else 'indefinite_article',definiteness='definite' if t=='the' else 'indefinite')
        elif t in {'my','her','his','its','their'}: F(w,determiner_kind='possessive',possessive_construction='possessive_determiner')
        elif t in {'any','every','all'}: F(w,determiner_kind='quantifier',quantifier_scope_id=f'word_{w}')
    if pos=='adp': F(w,dependency_relation='prepositional_marker')
    if pos=='part' and t=='to': F(w,dependency_relation='infinitival_marker',clause_finiteness='nonfinite')
    if pos=='conj' and t in {'and','but','or'}: F(w,coordinator_type={'and':'conjunctive','but':'adversative','or':'disjunctive'}[t])
    if pos=='pron':
        if t in {'i','i’ll','she','he','we','they','they’d','you','her','him','it','it’s','himself'}:
            F(w,mention_form='personal_pronoun',grammatical_person=1 if t in {'i','i’ll','we'} else 2 if t=='you' else 3)
            if t in {'her','him'}: F(w,grammatical_case='objective')
    if pos=='n' and r.get('entity_id'):
        F(w,referent_kind='group' if a.entities[r['entity_id']]['type'].endswith(('group','set')) else 'individual')
for w,parts in [(71,['book','is']),(92,['it','is']),(108,['I','will']),(340,['they','had']),(439,['can','not']),(554,['I','will']),(576,['could','not']),(604,['it','is'])]: F(w,contraction_expansion=parts)
for w in [12,95,137,224,351,718,752]: F(w,genitive_realization='possessive_s',possessive_construction='prenominal_s_genitive')
F(71,evidence_resolution_status='is_gone_state_reading_has_gone_alternative',lexical_gloss='Contracted book is, not a genitive. A book has gone reading is possible; no motion path is inferred.')
for w in [93,262,439,576]: F(w,polarity='negative',negation_marker_form='not' if w in [93,262] else a.words[w]['token'])
for w,p in [(93,'p40'),(262,'p41'),(343,'p42'),(439,'p18'),(576,'p26')]: F(w,negation_scope_id=p)
for w,kind,p in [(28,'conditional_practical_ability','p2'),(161,'permission_request','p7'),(213,'future_practical_option','p10'),(306,'as_if_possibility','p39'),(439,'unresolved_constraint','p18'),(477,'considered_option','p20'),(504,'epistemic_possibility','p16'),(509,'epistemic_possibility','p21'),(527,'polite_request','p22'),(576,'past_physical_inability','p26')]: F(w,modal_auxiliary_class='possibility_family',modal_base={'kind':kind,'content_id':p})
F(171,modal_auxiliary_class='permission_family')
F(358,modal_auxiliary_class='necessity_construction')
for w in [108,554]: F(w,modal_auxiliary_class='volitional_future')
PAST=[4,9,16,23,40,48,52,55,58,74,78,85,97,105,114,121,131,132,155,176,200,202,218,227,233,239,244,258,266,268,282,291,313,322,327,329,336,344,353,370,372,381,390,394,404,406,412,424,433,442,451,452,473,488,492,493,514,522,536,546,550,560,562,567,569,574,577,584,592,597,609,615,622,630,638,649,651,660,665,671,678,679,687,694,711,720,728,734,744,755]
for w in PAST: F(w,tense='past',verb_form='finite')
for w in [116,172,186,198,356,358,364,367,429,435,505,510,538]: F(w,tense='present',verb_form='finite')
for w in [29,34,61,65,82,109,111,163,169,181,190,214,293,307,440,478,482,529,555]: F(w,verb_form='base')
for w in [46,98,133,139,147,177,253,297,315,453,458,493,541,703,742]: F(w,verb_form='gerund_participle' if w not in [253,742] else 'past_participle')
F(626,verb_form='base')
for w in [122,341,452,673,679]: F(w,verb_form='past_participle')
for w in [172,360,505,510,540,577]: F(w,verb_form='base')
F(132,verb_form='past_participle')
F([126,643],verb_form='finite',tense='past')
for row in a.words:
    if row.get('verb_form') in {'base','past_participle','gerund_participle'}: row.pop('tense',None)
for pred,aux in [(98,97),(133,132),(315,313),(493,492)]: F(pred,aspect='progressive',progressive_auxiliary_id=a.anchor(aux));F(aux,auxiliary_selection='gerund_participle')
for pred,aux in [(133,131),(341,340),(452,451),(679,678)]: F(pred,aspect='perfect_progressive' if pred==133 else 'perfect',perfect_auxiliary_id=a.anchor(aux))
F(122,voice='passive',passive_auxiliary_id=a.anchor(121))
F(673,voice='passive_or_resultative_state',passive_auxiliary_id=a.anchor(671))
for w in [181,190]: F(w,mood='imperative',imperative_subject_status='understood_addressees')
for w in [161,429,527]: F(w,subject_auxiliary_inversion=True)
for w in [262,401]: F(w,sentence_fragment_type='nominal_identification')
F(301,reflexive_antecedent_id='e2',reflexive_form='third_singular_masculine')
F(67,adjective_degree='comparative');F(295,adjective_degree='superlative')
for w in [125,642]: F(w,relative_marker_form='personified_nonhuman_who',relative_gap_role='subject',relative_head_id=a.anchor(w-1))
for w,source in [(8,7),(77,76),(185,184),(340,339),(676,674)]: F(w,relative_head_id=a.anchor(source),relative_gap_role='object' if w in [8,77,185,340] else 'location')
F(76,nominal_ellipsis_license='one_substitute_for_book',antecedent_id='e16')
F(264,reference_metonymic_link={'literal':'whale_depiction','intended':'e16','relation':'content_for_book'})
F(473,lexical_sense_id='clock_display',lexical_gloss='A clock displays a time; no speaking clock or audible utterance is asserted.')
F(318,lexical_sense_id='tower_like_stack',lexical_gloss='A tall stack of books, not a separate building.')
for modifier,head,relation in [(6,7,'topic'),(13,14,'function'),(70,71,'content'),(137,138,'intended_users'),(166,167,'function'),(204,205,'topic'),(224,225,'intended_users'),(229,230,'location'),(248,249,'format'),(270,271,'performance_type'),(279,280,'contents_kind'),(287,288,'format'),(288,289,'whole'),(374,375,'function'),(378,379,'topic'),(384,385,'material'),(409,410,'content'),(419,420,'topic'),(445,446,'topic'),(516,517,'topic'),(564,565,'whole'),(579,580,'format'),(580,581,'book_category'),(588,589,'topic'),(612,613,'association'),(624,625,'shape'),(709,710,'topic'),(715,716,'function'),(722,723,'content'),(753,754,'material')]: F(modifier,noun_compound_relation=relation,noun_compound_head_id=a.anchor(head))
for mod,head in [(62,63),(67,68),(101,102),(145,146),(165,167),(183,184),(209,210),(220,221),(295,296),(317,318),(346,347),(383,385),(415,416),(422,423),(427,428),(463,464),(502,503),(632,633),(636,637),(656,657),(742,743),(749,750)]: F(mod,adjective_position='attributive_prenominal',syntactic_governor_id=a.anchor(head),dependency_relation='adjectival_modifier')
for w,entity,attrs in [(62,'e14',{'height':'high'}),(67,'e15',{'reading_difficulty':'trickier'}),(165,'e24',{'size':'little'}),(183,None,{'book_state':'stray'}),(295,'e41',{'relative_height':'lowest'}),(415,'e50',{'height':'high'}),(427,'e52',{'thickness':'thick'}),(463,'e55',{'shape':'round'}),(632,'e52',{'thickness':'thick'}),(656,'e63',{'cheer_scale':'tiny'})]:
    F(w,attributes=[{'name':key,'value':value} for key,value in attrs.items()])
for v,particle,construction in [(390,392,'pick_up'),(493,494,'check_out_patron'),(514,518,'take_from'),(529,531,'put_back'),(569,572,'put_back'),(584,586,'put_on'),(597,598,'look_up'),(630,634,'ease_apart'),(660,663,'bring_down'),(687,690,'check_out_book'),(694,697,'push_back'),(734,735,'lean_in')]: F(v,verb_particle_construction=construction);F(particle,syntactic_governor_id=a.anchor(v),dependency_relation='verbal_particle' if particle not in [518,586] else 'prepositional_marker')

SUBJECTS={4:'e1',9:'e1',16:'e1',23:'e1',29:'e1',34:'e1',40:'e2',44:'e13',49:'e2',53:'e1',58:'e2',72:'e16',74:'e2',78:'e2',85:'e2',94:'e16',98:'e3',105:'e6',109:'e1',111:'e2',114:'e1',116:'e1',122:'e16',126:'e21',133:'e2',139:'e2',147:'e21',151:'e22',155:'e1',163:'e5',172:'e5',176:'e4',177:'e4',186:'e5',198:'e1',200:'e1',202:'e1',214:'e1',218:'e1',227:'e5',233:'e2',239:'e1',244:'e5',258:'e34',266:'e2',268:'e5',282:'e1',291:'e2',297:'e2',307:'e16',315:'e24',322:'e1',327:'e73',329:'e1',336:'e5',341:'e5',353:'e44',356:'e3',360:'e72',364:'e6',367:'e5',370:'e1',372:'e5',381:'e2',390:'e2',394:'e2',404:'e2',406:'e47',412:'e1',424:'e51',429:'e51',435:'e1',440:'e5',442:'e1',452:'e1',473:'e56',478:'e1',488:'e5',493:'e4',505:'e51',510:'e51',514:'e1',522:'e1',529:'e4',536:'e1',538:'e1',546:'e4',550:'e4',555:'e4',560:'e5',562:'e2',567:'e2',569:'e2',574:'e2',577:'e2',584:'e2',592:'e21',597:'e1',606:'e16',609:'e4',615:'e4',622:'e5',626:'e47',630:'e4',638:'e62',643:'e21',649:'e4',651:'e2',660:'e4',665:'e4',673:'e47',679:'e2',687:'e4',694:'e1',703:'e26',712:'e7',720:'e3',728:'e2',734:'e1',744:'e21',755:'e47'}
for w,entity in SUBJECTS.items(): F(w,grammatical_subject_id=entity)
for w,entity in {4:'e7',9:'e7',16:'e7',23:'e7',29:'e11',58:'e1',61:'e14',65:'e15',78:'e16',82:'e16',85:'e16',109:'e2',111:'e16',133:'e16',163:'e24',172:'e24',177:'e25',190:'e26',202:'e7',214:'e7',218:'e24',227:'e28',244:'e34',268:'e37',282:'e39',293:'e41',297:'e19',322:'e24',329:'e42',336:'e42',341:'e42',372:'e45',381:'e47',390:'e47',394:'e48',412:'e50',442:'e7',453:'e7',458:'e10',478:'e4',482:'e7',493:'e57',514:'e7',522:'e7',529:'e7',546:'e59',555:'e60',562:'e25',569:'e16',577:'e61',584:'e16',592:'e23',597:'e51',622:'e47',630:'e52',651:'e63',660:'e16',665:'e16',679:'e47',687:'e16',694:'e24',720:'e16'}.items(): F(w,grammatical_object_id=entity)
for w,kind in [(21,'conditional'),(237,'temporal_overlap'),(302,'comparison'),(303,'as_if_comparison'),(324,'recurrent_temporal_condition'),(361,'time_boundary'),(486,'temporal_overlap'),(558,'temporal_overlap'),(627,'temporal_overlap'),(751,'simultaneity')]: F(w,subordinator_type=kind)
for w in [268,336,412,442,597]:
    a.words[w].pop('grammatical_object_id',None)  # Coordinated places or PP complements, not a single direct object.
F(643,recipient_id='e70')  # Same title-content event as the earlier title occurrence.

# Explicit entity mentions supply reference links; this only serializes the
# manual identity decisions above and never identifies entities by a name rule.
for eid,entity in a.entities.items():
    for i,w in enumerate(sorted(entity['mentions'])):
        row=a.words[w]
        if row['pos']=='pron' and i:
            earlier=sorted(entity['mentions'])[i-1]
            F(w,antecedent_id=eid,reference_chain_id=f'chain_{eid}',antecedent_mention_index=a.words[earlier]['index'])
        if row['pos']=='n' and entity['type']=='person': F(w,mention_form='proper_name' if row['lemma'] in {'Mina','Jun','Grandma','Ms','Alvarez'} else 'definite_description')
for w in [226,243,267,335,371,487,559]: F(w,split_antecedent_ids=['e1','e2'],group_members=['e1','e2'])
F(357,split_antecedent_ids=['e2','e3'],group_members=['e2','e3'])
for w in [157,174,479,525,544,607,647,658,685]: F(w,proper_name_structure='title_plus_name')

# Narrative interpretation is sparse and explicitly anchored to physical or
# cognitive evidence; no permanent virtue, hidden emotion or atlas loan added.
F(72,narrative_thread_id='thread_find_whale_book',narrative_problem_id='p4',narrative_thread_status='open',narrative_goal_link={'thread':'thread_find_whale_book','goal':'p6'})
F(473,narrative_tension_source='closing_deadline_and_personal_atlas_plan',narrative_thread_id='thread_find_whale_book')
a.feature(536,evidence=[9,29,34,108,116,452,478,529,538,541],note='Local action favors continuing promised help over taking the atlas home now; this is a narrative interpretation, not an immutable generous trait.',narrative_change_dimension='priority_of_current_action',narrative_theme_candidate={'content':'keeping_a_help_commitment_despite_a_personal_plan','source':'annotator','assertion_status':'candidate'})
F(687,narrative_thread_id='thread_find_whale_book',narrative_thread_status='resolved',narrative_resolution_evidence={'problem':'p4','outcome':'p30','status':'book_recovered_and_loan_completed_before_deadline'})
a.feature(755,evidence=[7,29,31,123,124,129,145,146,153,640,641,646,719,720,727,733,743,747,750,754,758],note='The closing shared reading and celestial picture connect Mina’s initial moon interest with the recovered whale book. This does not fulfill her specific atlas-sketch plan or repair the bookmark continuity gap.',narrative_motif_link={'earlier':'moon_atlas_plan','current':'shared_whale_book_celestial_image','relation':'changed_shared_context'},narrative_closure_candidate={'cue':'shared_reading_and_bookmark_final_image','thread':'thread_find_whale_book','assertion_status':'candidate'})

# Support sets include actual role witnesses, and assertion labels describe the
# evidence source while factuality/scope preserve hypothetical content.
for event in a.events.values():
    eid=event['event_id'];support=set(event['support_words'])
    support.update(w for w,row in enumerate(a.words) if any(b['event_id']==eid for b in row.get('event_bindings',[])))
    event['support_words']=sorted(support)
    row=a.words[event['trigger']]
    if row.get('event_id')==eid:
        F(event['trigger'],assertion_status='attributed_claim' if row.get('quotation_scope_id') else 'asserted',supporting_mention_indices=event['support_words'])
for w in [429,505,510]: F(w,truth_commitment='suspended')

FEEDBACK={
'summary':'Complete manual retrospective library annotation, preserving the unborrowed atlas plan, actual whale-book checkout, depicted characters, scoped reports and the unresolved bookmark continuity.',
'ambiguities':[
 {'words':[385,390,402,423,625,670,672,673,679,754],'issue':'Bookmark picked up from floor is later described as still inside the book.','decision':'Retain one text-intended identity with evidence_resolution_status and evidence_missing; no duplicate bookmark or reinsertion event is invented.'},
 {'words':[14,534,710,712,716],'issue':'Atlas starts on a display table and ends on a display shelf; transition is unreported.','decision':'Separate table/shelf referents; record request and final state without an invented completed reshelving action or atlas checkout.'},
 {'words':[429,430,431,435,503,505,507,510,604,605,606],'issue':'Is that it can ask whether the visible point is the bookmark or whether it indicates the book.','decision':'Represent a tentative clue-to-book-location interpretation and explicit metonymic bridge; Mina’s uncertainty remains at its local time despite later confirmation.'},
 {'words':[438,439,440],'issue':'Cannot climb may express physical constraint or a safety/permission rule.','decision':'Keep modal source unresolved; later librarian use of ladder does not prove a precise height or universal rule.'},
 {'words':[71,72],'issue':'book’s gone permits book is gone or book has gone.','decision':'Choose missing-state is reading with recorded alternative, without an invented departure event.'},
 {'words':[137,142,146,153,347,350,637,740,743],'issue':'Image first shown is not explicitly located on cover versus an interior page.','decision':'Depicted whale identity is shared, but illustration location is left open until explicit first-page final image.'},
 {'words':[355,357,360],'issue':'we in grandmother departure report is contextually Jun and grandmother.','decision':'Use that pair, distinct from search-team we. Mina’s accompanying departure is not stated by this rule.'},
 {'words':[569,584],'issue':'Put back and put on astronomy shelf describe the same prior placement.','decision':'Reuse one underlying placement event while preserving the earlier-belief scope.'},
],
'feature_gaps':[
 {'meaning':'source continuity gap','decision':'Existing evidence_missing/evidence_resolution_status and feedback suffice for this trial; a typed transition-gap relation could be useful later but no extra attribute is required here.'},
 {'meaning':'represented image versus physical page contact','decision':'Existing semantic_world_id plus reference_metonymic_link and part_whole_relation preserve the final bookmark/depicted-tail distinction; no runtime enactment claim is used.'},
],
'prompt_feedback':[
 'Keep source continuity defects separate from character false belief and from a proven logical contradiction; missing transition evidence alone does not license a repair event.',
 'Distinguish actual loans/checkouts, permission, considered reservations and endpoint shelf states. Holding an atlas does not establish borrowing it.',
 'Quantified book/none denote variables or sets under restricted quantification, not a single book identity or the whole collection in an individual slot.',
 'Negation and modality should point to the precise positive action/state content; an explicitly negative premise needs its own proposition when used in reasoning.',
 'Separate grammatical direct objects from objects of prepositions, and finite tense from tense inferred for a participial clause.',
 'A display table and display shelf can both be explicit without a narrated transfer between them. Avoid silently merging furniture to repair continuity.',
],
'coverage_notes':'All 759 words received explicit contextual POS and lemmas. All 32 paragraphs and all 1,024 supplied feature definitions were read. Sparse annotation covers identities, predicates, roles, scope, grammar, time, quantities, physical relations, mental and communicative content, and evidence-marked narrative interpretation. No causal-prefix filter, API call or automatic semantic tagger. Gaps/punctuation remain deterministic.',
'reviewed_all_words':True,'reviewed_paragraphs':list(range(32)),
'not_claimed':['atlas checkout','completed atlas reservation','unseen atlas reshelving actor','bookmark reinsertion','second bookmark','permanent character traits','literal swimming animal or speaking book in library','absolute date or timezone'],
}
a.save(FEEDBACK)
