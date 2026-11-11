"""Manually interpreted camp story, frozen whole-story annotation prompt v2."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a=Annotation('10_camp',prompt_version='v2')
for key in ['appearance_color','part_whole_relation','figurative_mapping']: a.use_extension(key)

LEX={
0:'det=the adj=last n=strip adp=of n=sunlight v=lie adp=across det=the n=picnic n=table adp=at n=Cedar n=Bend n=Campground n=Nora v=be v=help det=her n=mother v=stir n=bean adp=in det=a n=pot conj=when n=Theo v=come v=run adp=from det=the n=tent num=one n=shoe adj=untied conj=and det=his n=cheek adj=wet',
1:'n=Moss v=be adj=gone pron=he v=say',
2:'n=Moss v=be det=his adj=small adj=brown n=rabbit adp=with num=one adj=floppy n=ear conj=and det=a adj=brass n=bell v=sew adp=to det=its adj=blue n=collar n=Theo v=take n=Moss adv=everywhere adv=even part=to v=brush det=his n=tooth',
3:'adv=where v=do pron=you adv=last v=see pron=he n=Nora v=ask',
4:'adp=at det=the n=water n=pump pron=I v=have pron=he conj=and adv=then pron=I v=do n=Theo v=look adp=toward det=the n=tree det=their adj=long n=shadow v=reach adp=across det=the n=campground n=loop pron=I v=can v=go v=look det=the n=wood v=be v=get adj=dark',
5:'n=Nora v=want part=to v=find n=Moss adp=before n=bedtime pron=she adv=also v=want n=Theo part=to v=stop v=look conj=as conj=if det=the n=shadow v=may v=swallow pron=he pron=we v=look adv=together pron=she v=say',
6:'det=their n=father v=be v=hang det=a n=towel adp=on det=the n=clothesline n=Nora v=ask conj=if pron=she v=can v=borrow det=his n=lantern',
7:'v=stay adp=on det=the v=mark n=path pron=he v=say v=hand pron=it adv=over conj=and v=come adv=back conj=when n=Mom v=call adp=for n=supper',
8:'n=Nora v=click det=the n=lantern adv=on det=its adj=warm n=circle adp=of n=light v=land adp=on det=the n=dirt n=Theo v=stand adv=close adv=enough conj=that det=his n=shoulder v=press adp=against pron=hers',
9:'pron=they v=check adp=beneath det=the n=table conj=and adp=around det=the n=tent n=Nora v=lift det=a adj=folding n=chair n=Theo v=peer adp=behind det=the n=cooler',
10:'part=not adv=there pron=he v=say',
11:'v=let v=retrace det=your n=step adp=to det=the n=pump',
12:'det=the n=path v=curve adp=between adj=tall n=pine n=Nora v=walk adv=slowly conj=so n=Theo v=can v=keep adv=up det=the n=lantern v=make det=the n=tree n=trunk adj=bright adp=on num=one n=side conj=and adj=black adp=on det=the pron=other det=a n=branch v=sway adv=overhead conj=and det=its n=shadow v=slide adp=across det=the n=path',
13:'n=Theo v=grab n=Nora n=sleeve pron=something v=move',
14:'adv=just det=the n=branch pron=she v=say conj=though det=her adj=own n=stomach v=have v=tighten pron=she v=aim det=the n=lantern adv=upward det=the n=branch v=wave adp=in det=the n=breeze adv=then v=hold adj=still',
15:'pron=they v=reach det=the n=water n=pump det=no n=rabbit n=Nora v=check det=the adj=wooden n=platform conj=while n=Theo v=look adp=around det=the n=spigot',
16:'pron=I v=shall v=hold pron=he adv=tight pron=he v=whisper',
17:'pron=you v=be v=carry pron=he conj=and v=wash det=your n=hand pron=that det=a n=lot adp=of n=job',
18:'n=Theo v=sniff pron=I v=hear det=his n=bell conj=when pron=we v=come adv=back pron=I v=think',
19:'pron=they v=follow det=the n=path adp=toward n=camp adv=ahead pron=it v=split num=one n=trail v=curve adp=past det=the n=bridge adp=over det=the adj=shallow n=creek det=the pron=other v=turn adp=toward det=the n=campground n=office',
20:'pron=we v=can v=check det=the n=office n=Nora v=say adv=maybe pron=someone v=find pron=he',
21:'n=Theo v=stare adp=at det=the n=bridge adp=beyond pron=it det=the n=path v=dip adp=between adj=dark n=shrub',
22:'pron=I v=do v=want part=to v=go adv=there',
23:'n=Nora v=want part=to v=hurry conj=if n=Moss v=have v=roll adp=down det=the n=trail det=every n=minute v=matter pron=she v=can v=carry det=the n=lantern conj=and v=go adv=ahead conj=but n=Theo v=will v=be adj=alone adp=at det=the n=fork adp=with det=the n=shadow conj=and det=no n=light',
24:'intj=okay pron=she v=say pron=we v=stay adv=together pron=you v=tell pron=I pron=what pron=you v=remember',
25:'n=Theo v=take det=a n=breath pron=I v=be v=run adv=back adp=from det=the n=pump pron=I v=hear det=a adj=tiny n=jingle adv=right adp=near det=the n=bridge',
26:'pron=they v=walk adp=toward pron=it n=side adp=by n=side adp=at det=the n=railing n=Nora v=sweep det=the n=lantern adp=over det=the n=board det=the n=light v=catch det=a n=jumble adp=of n=leaf adv=then det=the adj=silver n=shine adp=of n=creek n=water adv=below',
27:'n=Theo v=lean adv=close adp=to pron=she adv=there',
28:'det=a adj=blue n=patch v=show adp=beneath det=a adj=low n=pine n=branch adp=beside det=the n=path n=Moss v=have v=catch adp=by num=one adj=floppy n=ear adv=just adp=above det=the n=ground det=his n=bell v=make det=a adj=faint n=sound conj=as det=the n=branch v=shift',
29:'n=Nora v=can v=reach pron=he conj=but det=the n=branch v=stretch adp=over det=a n=tangle adp=of adj=prickly n=blackberry n=cane n=Theo v=look adp=at det=the adj=dark n=tangle conj=and v=back adv=away',
30:'v=can pron=you v=hold det=the n=lantern adj=steady n=Nora v=ask pron=I v=reach adp=from det=the n=path v=do v=move adv=close',
31:'n=Theo v=swallow adv=then pron=he v=take det=the n=lantern adp=with det=both n=hand det=the n=light v=wobble adv=once v=paint det=a adj=tall adj=crooked n=shadow adp=over det=the n=bridge',
32:'pron=it adv=only det=the n=branch n=Nora v=remind pron=he',
33:'n=Theo v=aim det=the n=lantern adv=low det=the n=shadow v=shrink pron=I v=can v=see det=his n=ear',
34:'n=Nora v=crouch conj=and v=stretch adp=beneath det=the n=pine det=a n=thorn v=snag det=her n=sleeve conj=but pron=she v=work pron=it adj=free conj=and v=catch n=Moss adp=by det=the adj=blue n=collar pron=she v=pull adv=gently det=the n=rabbit v=come adj=loose n=leaf v=stick adp=to det=his n=fur conj=and det=his n=bell v=give num=one adj=bright n=chime',
35:'n=Theo v=hug pron=he adp=to det=his n=chest pron=you v=find pron=he',
36:'pron=we v=find pron=he n=Nora v=say v=rub det=the n=thorn n=mark adp=on det=her n=sleeve',
37:'adp=from det=the n=campsite det=their n=mother v=call n=supper',
38:'pron=they v=return adp=along det=the v=mark n=path adp=with n=Theo v=carry n=Moss conj=and n=Nora v=carry det=the n=lantern conj=when pron=they v=reach det=the n=picnic n=table det=their n=father v=hold adv=out det=a n=hand adp=for pron=it n=Nora v=give pron=it adv=back',
39:'n=Theo v=sit adp=beside det=the adj=warm n=pot conj=and v=set n=Moss adp=on det=the n=bench pron=he v=smooth det=the n=rabbit adj=bent n=ear adp=behind pron=they det=the n=lantern n=glow v=make num=three n=shadow adp=on det=the n=tent n=wall n=Theo n=Nora conj=and det=a adj=small pron=one adp=with num=one adj=floppy n=ear det=this n=time n=Theo v=lean adv=back conj=and v=let pron=they det=all v=stay',
}
for p,text in LEX.items():
    pairs=[x.split('=',1) for x in text.split()]; words=a.paragraphs[p]['words']
    assert len(words)==len(pairs),(p,len(words),len(pairs))
    a.tag(p,[x[0] for x in pairs],{w['w']:x[1] for w,x in zip(words,pairs)})

ENTS=[
('e1','Nora','person',[14,17,77,112,119,136,147,150,173,206,233,269,276,279,284,305,379,404,418,441,448,482,508,543,573,575,609,625,635,638,649,674,680,687,707,725,760]),
('e2','Theo','person',[25,35,41,45,62,69,73,83,88,90,103,122,132,187,192,211,218,222,237,267,311,316,321,323,329,336,338,346,385,398,427,446,450,452,456,463,504,558,568,583,586,611,612,620,668,672,703,729,741,759,771]),
('e3','mother','person',[18,169,693]),
('e4','father','person',[139,153,160,718]),
('e5','Nora and Theo','person_group',[133,138,197,298,348,374,443,472,677,692,696,712,717,748]),
('e6','Moss','rabbit_referent_animate_status_unspecified',[38,43,48,59,64,76,85,116,304,319,326,340,384,409,522,533,546,623,644,653,659,662,670,676,679,705,737,744]),
('e7','Moss floppy ear','ear',[52,528,624,746]),
('e8','Moss brass bell','bell',[56,341,534,663]),
('e9','Moss blue collar','collar',[61,648]),
('e10','father lantern','lantern',[154,163,176,178,242,287,422,485,571,589,615,710,724,727,750]),
('e11','Cedar Bend Campground','campground',[11,12,13]),
('e12','family campsite','campsite',[353,691]),
('e13','picnic table','table',[9,201,716]),
('e14','family tent','tent',[30,205,757]),
('e15','water pump','pump',[82,226,302,462]),
('e16','marked path network','path',[159,228,266,351,355,579,701]),
('e17','bridge-side trail','trail',[358,393,403,414,521]),
('e18','office-side trail','trail',[368]),
('e19','path fork','path_junction',[433]),
('e20','bridge','bridge',[362,389,391,471,475,604]),
('e21','creek','creek',[366,501]),
('e22','campground office','building',[373,378]),
('e23','bridge railing','railing',[481]),
('e24','bridge boards','board_group',[488]),
('e25','first overhead branch','branch',[257,261,271,275,290]),
('e26','first branch shadow','shadow',[262]),
('e27','low pine recovery branch','branch',[518,541,549,608]),
('e28','low pine tree','pine',[517,631]),
('e29','blackberry cane tangle','plant_group',[553,557,563]),
('e30','thorn snagging Nora sleeve','thorn',[633,684]),
('e31','Nora sleeve','clothing_part',[270,636,640,688]),
('e32','mark on Nora sleeve','mark',[685]),
('e33','lantern light','light',[180,182,490,594,751]),
('e34','tree shadows over campground','shadow_group',[97,129,436]),
('e35','pine and tree group near path','tree_group',[94,95,232,245]),
('e36','tree trunks','trunk_group',[246]),
('e37','first-illuminated trunk side','surface_region',[250]),
('e38','other unlit trunk side','surface_region',[255]),
('e39','recovery branch shadow','shadow',[601,605,618]),
('e40','final three shadows','shadow_group',[754,776]),
('e41','Moss shadow','shadow',[764]),
('e42','ear silhouette in Moss shadow','depicted_part',[768]),
('e43','sunlight','light',[4]),
('e44','pot of beans','pot',[23,734]),
('e45','beans','food_group',[20]),
('e46','Theo untied shoe','shoe',[32]),
('e47','Theo wet cheeks','body_part_group',[36]),
('e48','Theo teeth','body_part_group',[70]),
('e49','Theo shoulder','body_part',[193]),
('e50','Nora shoulder','body_part',[196]),
('e51','Nora stomach','body_part',[281]),
('e52','Theo hands','body_part_group',[330,592]),
('e53','Theo chest','body_part',[673]),
('e54','father hand','body_part',[722]),
('e55','towel','towel',[143]),
('e56','clothesline','clothesline',[146]),
('e57','folding chair','chair',[210]),
('e58','cooler','cooler',[215]),
('e59','pump wooden platform','platform',[309]),
('e60','pump spigot','spigot',[315]),
('e61','campsite dirt','ground',[186]),
('e62','ground beneath recovery branch','ground',[532]),
('e63','breeze','air_motion',[294]),
('e64','campground loop','path_loop',[102]),
('e65','shrubs past bridge','shrub_group',[397]),
('e66','creek water','water',[502]),
('e67','leaves seen near bridge','leaf_group',[495]),
('e68','leaves stuck to Moss','leaf_group',[656]),
('e69','Moss fur','fur',[660]),
('e70','bench','bench',[740]),
('e71','tent wall','wall',[758]),
('e72','remembered bell jingle','sound',[467]),
('e73','faint bell sound during branch shift','sound',[538]),
('e74','bright bell chime on release','sound',[667]),
('e75','woods around campground','woodland',[108]),
('e76','visible blue patch of Moss','colored_patch',[512]),
]
for args in ENTS:a.entity(*args)
a.entities['e5']['member_ids']=['e1','e2']
a.entities['e6'].update(type_alternatives=['toy_rabbit','live_rabbit'],identity_note='Moss is consistently called rabbit and has fur/ear/collar; toy versus living animal is not stated. No autonomous movement, agency, health or biological state is invented.')
a.entities['e25']['identity_note']='May be a different branch from recovery branch e27; exact identity is not asserted.'
a.entities['e34']['identity_note']='Shadows at later fork may overlap earlier tree-shadow group; generic environmental reference, not individually tracked silhouettes.'

F=a.feature
def B(entity,value,scope='s0',status='asserted',**extra):return dict(entity_id=entity,value=value,scope_id=scope,assertion_status=status,**extra)
QUOTES=[
('q1',38,41,'e2','Moss missing report','e1'),('q2',71,77,'e1','Question about last sighting','e2'),
('q3',79,90,'e2','Last possession at pump then loss','e1'),('q4',103,112,'e2','Cannot search and woods darkening','e1'),
('q5',133,136,'e1','Promise of joint search','e2'),('q6',155,160,'e4','Stay on marked path','e1'),('q7',165,173,'e4','Return when mother calls for supper','e1'),
('q8',216,218,'e2','Negative result at cooler/campsite','e1'),('q9',220,227,'e1','Suggest retracing route to pump','e2'),
('q10',271,273,'e2','Something moved','e1'),('q11',273,276,'e1','Identify moving object as branch','e2'),
('q12',316,321,'e2','Retrospective should have held tighter','e1'),('q13',323,336,'e1','Recall carrying and washing; many jobs','e2'),
('q14',338,348,'e2','Tentative bell memory on earlier return','e1'),('q15',374,379,'e1','Proposed office check','e2'),('q16',381,385,'e1','Someone may have found Moss','e2'),
('q17',398,404,'e2','Does not want bridge-side route','e1'),('q18',440,441,'e1','Boundary acknowledgment','e2'),('q19',443,452,'e1','Stay together and request memory','e2'),
('q20',456,472,'e2','More specific prior return and jingle memory','e1'),('q21',509,510,'e2','Point out visible Moss location','e1'),
('q22',567,573,'e1','Request Theo hold lantern steady','e2'),('q23',575,583,'e1','Nora will reach from path; Theo must not approach','e2'),
('q24',605,609,'e1','Reassure about projected branch shadow','e2'),('q25',620,625,'e2','Theo reports seeing Moss ear','e1'),
('q26',674,677,'e2','Credit Nora for finding Moss','e1'),('q27',677,680,'e1','Credit shared recovery','e2'),('q28',695,696,'e3','Call family to supper','e5'),
]
for sid,lo,hi,holder,desc,audience in QUOTES:
    a.scope(sid,range(lo,hi),kind='quotation',holder_id=holder,description=desc)
    a.scopes[sid]['addressee_ids']=[audience]
    F(range(lo,hi),quote_mode='direct',assertion_status='attributed_claim')
for sid,lo,hi,kind,holder,parent,desc in [
('s1',115,119,'desired_content','e1','s0','Finding Moss desired before bedtime.'),
('s2',124,133,'desired_content','e1','s0','Theo stopping frightened-looking appearance desired.'),
('s3',126,133,'figurative_comparison','e1','s2','Shadows swallowing is a fear comparison, not literal attack.'),
('s4',149,155,'indirect_request','e1','s0','Lantern loan requested; actual handoff follows.'),
('s5',168,173,'future_condition','e4','q7','Mother call is prospective condition, later realized in narration.'),
('s6',407,408,'desired_content','e1','s0','Nora desires haste, not proof she hurries.'),
('s7',408,418,'conditional_conjecture','e1','s0','Moss rolling down trail is an open possibility.'),
('s8',418,440,'considered_alternative','e1','s0','Going alone with lantern and leaving Theo is considered but unchosen.'),
('s9',580,583,'prohibited_action','e1','q23','Negative imperative prohibits Theo approaching; not proof he never moves.'),
]:a.scope(sid,range(lo,hi),kind=kind,holder_id=holder,parent=parent,description=desc)

PROPS=[
(1,'Moss is missing from Theo possession.',[38,40],'q1'),(2,'Theo last saw Moss at the pump.',[75,76,79,82],'q3'),
(3,'Theo holds Moss after the earlier pump visit.',[83,84,85,88,89],'q3'),(4,'Theo can go search alone now.',[103,104,105,106],'q4'),
(5,'The woods are getting dark.',[108,109,110,111],'q4'),(6,'Nora finds Moss before bedtime.',[115,116,117,118],'s1'),
(7,'Theo stops looking frightened by the shadows.',[122,124,125,129,131,132],'s2'),(8,'Nora and Theo search together.',[133,134,135],'q5'),
(9,'Nora borrows father lantern.',[150,152,153,154],'s4'),(10,'Nora stays on the marked path.',[155,158,159],'q6'),
(11,'Nora returns when mother calls for supper.',[166,167,168,169,170,172],'q7'),
(12,'Moss is at the searched cooler/campsite location.',[216,217],'q8'),(13,'Moss is not at the searched cooler/campsite location.',[216,217],'q8'),
(14,'Nora and Theo retrace Theo steps to the pump.',[220,221,223,226],'q9'),(15,'A branch moved.',[271,272,275],'q10'),
(16,'Theo held Moss more tightly during earlier carrying.',[316,317,318,319,320],'q12'),(17,'Theo carried Moss while washing his hands.',[323,325,326,328,330],'q13'),
(18,'Theo heard Moss bell on the earlier return from pump.',[338,339,341,344,345],'q14'),(19,'Nora and Theo check the campground office.',[374,376,378],'q15'),
(20,'Someone found Moss.',[381,382,383,384],'q16'),(21,'Theo goes along bridge-side trail.',[398,402,403],'q17'),
(22,'Nora hurries.',[404,405,407],'s6'),(23,'Moss rolled down the trail.',[409,410,411,414],'s7'),
(24,'Nora carries lantern ahead without Theo.',[418,420,422,424,425],'s8'),(25,'Theo is alone at fork without lantern light.',[427,429,430,433,438,439],'s8'),
(26,'Nora and Theo stay together.',[443,444,445],'q19'),(27,'Theo tells Nora what he remembers.',[446,447,448,449,450,451],'q19'),
(28,'Theo ran back from pump and heard a jingle near bridge.',[456,458,462,463,464,467,471],'q20'),
(29,'Theo holds lantern steady while Nora reaches.',[568,569,571,572],'q22'),(30,'Nora reaches from path.',[575,576,579],'q23'),
(31,'Theo moves closer to recovery branch.',[580,581,582],'s9'),(32,'Projected shape is a branch shadow.',[605,608],'q24'),
(33,'Theo sees Moss ear.',[620,622,623,624],'q25'),(34,'Nora contributes to finding and recovering Moss.',[674,675,676],'q26'),
(35,'Nora and Theo find and recover Moss together.',[677,678,679],'q27'),(36,'It is time for supper.',[695],'q28'),
(37,'Moss is at the pump search locations.',[303,304,306,309,312,315],'s0'),(38,'Theo wants to go along the bridge-side trail.',[398,399,400,402,403],'q17'),
(39,'Theo does not want to go along the bridge-side trail.',[398,399,400,402,403],'q17'),
(40,'Theo possessed Moss at the pump and then no longer did.',[79,82,84,85,88,89],'q3'),
]
for n,text,support,scope in PROPS:a.proposition(f'p{n}',text,support,scope_id=scope)

EV={}
def status(scope):
    while scope is not None:
        s=a.scopes[scope]
        if s['kind'] in ['quotation','indirect_request']:return 'attributed_claim'
        scope=s['parent']
    return 'asserted'
def E(key,w,label,**kw):
    eid=f'ev{len(EV)+1}';EV[key]=eid;a.event(eid,w,label,**kw)
    if kw.get('primary',True):F(w,assertion_status=status(a.words[w]['scope_id']))
    return eid
def M(key,words,role='reference',note=''):
    a.mention_event(EV[key],words,role=role,note=note)
    for w in [words] if isinstance(words,int) else words:
        if role=='action':F(w,assertion_status=status(a.words[w]['scope_id']))
def U(key,w,speaker,content,audience,kind='assertion',**kw):
    eid=E(key,w,'communicate '+content,type='speak',actor=speaker,recipient=audience,**kw)
    F(w,speaker_id=speaker,speech_act_kind=kind,utterance_id=eid,utterance_content_id=content,
      addressee_ids=[audience],communication_channel='speech',communication_scope_bundle={'speaker_id':speaker,'utterance_event_id':eid,'scope_id':'s0','assertion_status':'asserted'})
    return eid

E('sunlight',5,'last sunlight lies across picnic table',type='state',patients=['e43'],roles={'patient':[4],'landmark':[9]})
E('help',16,'Nora helps mother stir beans',actor='e1',patients=['e45'],recipient='e3',roles={'actor':[14],'recipient':[18],'patient':[20]})
E('stir',19,'mother stirs beans with Nora help',actor='e3',patients=['e45'],roles={'actor':[18],'patient':[20],'container':[23]})
E('arrive',26,'Theo comes running from tent',type='move',actor='e2',roles={'actor':[25],'source':[30]})
M('arrive',27,'action','Running specifies manner of the same arrival.')
E('shoe',33,'Theo shoe is untied',type='state',patients=['e46'],roles={'patient':[32]})
E('cheeks',37,'Theo cheeks are wet',type='state',patients=['e47'],roles={'patient':[36]})
E('missing',40,'Moss is missing from Theo possession',type='state',patients=['e6'],roles={'patient':[38]})
U('report_missing',42,'e2','p1','e1',roles={'actor':[41]})
E('rabbit_desc',44,'Moss is Theo small brown rabbit referent',type='state',patients=['e6'],roles={'patient':[43,48]})
E('bell_attach',57,'bell is sewn to Moss collar',type='state',patients=['e8'],roles={'patient':[56],'landmark':[61]})
E('carry_habit',63,'Theo habitually takes Moss everywhere',type='move',actor='e2',patients=['e6'],roles={'actor':[62],'patient':[64]})
E('brush',68,'Theo brushes teeth with Moss accompanying',actor='e2',patients=['e48'],roles={'patient':[70]})
E('last_see',75,'Theo saw Moss at an unresolved last location',type='perceive',actor='e2',patients=['e6'],factuality='hypothetical',roles={'actor':[73],'patient':[76]})
U('ask_last',78,'e1','p43','e2','question',roles={'actor':[77]})
E('held_atpump',84,'Theo holds Moss at pump',type='state',actor='e2',patients=['e6'],roles={'actor':[83],'patient':[85]})
E('not_held',89,'Theo holds Moss after pump visit',type='state',actor='e2',patients=['e6'],factuality='negated',roles={'actor':[88]})
U('last_report',84,'e2','p40','e1',primary=False,scope='s0')
E('look_trees',91,'Theo looks toward trees',type='perceive',actor='e2',patients=['e35'],roles={'actor':[90],'patient':[94]})
E('shadows_loop',98,'long tree shadows extend across campground loop',type='state',patients=['e34'],roles={'patient':[97],'landmark':[102]})
E('cannot_search',105,'Theo is able to go search now',type='state',actor='e2',factuality='negated',roles={'actor':[103]})
M('cannot_search',106,'action','Go look forms the quoted search action, under inability.')
E('dark_woods',110,'woods become dark',type='state',patients=['e75'],roles={'patient':[108]})
U('fear_report',105,'e2','p44','e1','state_inability',primary=False,scope='s0')
E('want_find',113,'Nora wants to find Moss before bedtime',type='feel',actor='e1',patients=['e6'],roles={'experiencer':[112]})
E('desired_find',115,'Nora finds Moss before bedtime',type='obtain',actor='e1',patients=['e6'],factuality='desired',roles={'patient':[116]})
E('want_comfort',121,'Nora wants Theo frightened appearance to cease',type='feel',actor='e1',patients=['e2'],roles={'experiencer':[119],'patient':[122]})
E('stop_fearlook',124,'Theo stops looking frightened',type='state',actor='e2',factuality='desired',roles={'actor':[122]})
E('fear_appearance',125,'Theo looks frightened by shadows',type='state',actor='e2',factuality='reported')
E('swallow_image',131,'shadows swallow Theo in comparison',patients=['e2'],factuality='hypothetical',roles={'figurative_causer':[129],'patient':[132]})
E('promised_search',134,'Nora and Theo search together',actor='e5',factuality='desired',roles={'actor':[133]})
U('promise_search',137,'e1','p8','e2','promise',roles={'actor':[136]})
E('hang_towel',141,'father hangs towel on clothesline',type='move',actor='e4',patients=['e55'],roles={'actor':[139],'patient':[143],'destination':[146]})
U('ask_loan',148,'e1','p9','e4','request_permission',roles={'actor':[147]})
E('requested_loan',152,'Nora borrows father lantern',type='obtain',actor='e1',patients=['e10'],factuality='desired',roles={'actor':[150],'patient':[154]})
E('stay_path_instruction',155,'Nora stays on marked path',actor='e1',factuality='desired',roles={'location':[159]})
U('instructions',161,'e4','p10','e1','instruction',roles={'actor':[160]})
E('loan_handoff',162,'father hands lantern to Nora',type='transfer',actor='e4',patients=['e10'],recipient='e1',roles={'patient':[163]})
E('return_instruction',166,'Nora returns for supper call',type='move',actor='e1',factuality='desired')
E('anticipated_call',170,'mother calls for supper',type='speak',actor='e3',factuality='hypothetical',roles={'actor':[169]})
U('return_instruction_speech',166,'e4','p11','e1','instruction',primary=False,scope='s0')
E('switch_on',174,'Nora switches lantern on',actor='e1',patients=['e10'],roles={'actor':[173],'patient':[176]})
E('light_dirt',183,'lantern light falls on dirt',type='state',patients=['e33'],roles={'patient':[182],'landmark':[186]})
E('stand_close',188,'Theo stands close to Nora',type='state',actor='e2',roles={'actor':[187]})
E('shoulder_touch',194,'Theo shoulder presses against Nora shoulder',type='state',patients=['e49'],roles={'patient':[193],'landmark':[196]})
E('check_camp',198,'Nora and Theo search table and tent areas',type='perceive',actor='e5',patients=['e6'],roles={'actor':[197],'search_location':[201,205]})
E('lift_chair',207,'Nora lifts folding chair',type='move',actor='e1',patients=['e57'],roles={'actor':[206],'patient':[210]})
E('peer_cooler',212,'Theo peers behind cooler',type='perceive',actor='e2',roles={'actor':[211],'search_landmark':[215]})
E('not_there',217,'Moss is at cooler search location',type='state',patients=['e6'],factuality='negated')
U('negative_result',219,'e2','p13','e1','negative_search_report',roles={'actor':[218]})
E('retrace_proposal',221,'Nora and Theo retrace route to pump',type='move',actor='e5',factuality='desired',roles={'destination':[226]})
U('suggest_retrace',220,'e1','p14','e2','suggestion',primary=False,scope='s0')
E('path_curves',229,'path curves between pines',type='state',patients=['e16'],roles={'patient':[228],'landmark':[232]})
E('walk_out',234,'Nora walks slowly toward pump',type='move',actor='e1',roles={'actor':[233]})
E('keepup',239,'Theo keeps up with Nora',type='move',actor='e2',factuality='desired',roles={'actor':[237]})
E('illuminate_trunks',243,'lantern illuminates one side of trunks',type='state',patients=['e36'],instruments=['e10'],roles={'causer':[242],'patient':[246]})
E('branch_sway',258,'overhead branch sways',type='move',patients=['e25'],roles={'patient':[257]})
E('shadow_slide',263,'branch shadow slides across path',type='move',patients=['e26'],roles={'patient':[262],'surface':[266]})
E('grab_sleeve',268,'Theo grabs Nora sleeve',actor='e2',patients=['e31'],roles={'actor':[267],'patient':[270]})
M('branch_sway',272,'action','Theo reports the actual branch movement; referent resolved by Nora next turn.')
U('moved_report',272,'e2','p15','e1',primary=False,scope='s0')
U('branch_explain',277,'e1','p15','e2','explanation',roles={'actor':[276]})
E('stomach_tight',283,'Nora stomach tightens',type='state',patients=['e51'],roles={'patient':[281]})
E('aim_up',285,'Nora aims lantern upward',type='move',actor='e1',patients=['e10'],roles={'actor':[284],'patient':[287]})
M('branch_sway',291,'action','Continued movement of same first branch, seen when Nora aims lantern upward.')
E('branch_still',296,'first branch holds still',type='state',patients=['e25'])
E('reach_pump',299,'Nora and Theo reach water pump',type='move',actor='e5',roles={'actor':[298],'destination':[302]})
E('not_pump',304,'Moss is at pump search locations',type='state',patients=['e6'],factuality='negated')
E('check_platform',306,'Nora checks pump platform',type='perceive',actor='e1',patients=['e59'],roles={'actor':[305],'patient':[309]})
E('look_spigot',312,'Theo searches around spigot',type='perceive',actor='e2',roles={'actor':[311],'landmark':[315]})
E('ought_hold',318,'Theo holds Moss more tightly during earlier carrying',actor='e2',patients=['e6'],factuality='hypothetical',roles={'actor':[316],'patient':[319]})
U('self_reproach',322,'e2','p16','e1','retrospective_ought',roles={'actor':[321]})
E('earlier_carry',325,'Theo carries Moss during pump visit',type='move',actor='e2',patients=['e6'],factuality='reported',roles={'actor':[323],'patient':[326]})
E('earlier_wash',328,'Theo washes hands during pump visit',actor='e2',patients=['e52'],factuality='reported',roles={'patient':[330]})
U('reframe_jobs',335,'e1','p17','e2','reassuring_reframe',primary=False,scope='s0')
E('sniff',337,'Theo sniffs',actor='e2',roles={'actor':[336]})
E('heard_before',339,'Theo hears Moss bell during earlier return',type='perceive',actor='e2',patients=['e8'],factuality='reported',roles={'actor':[338],'patient':[341]})
E('earlier_return',344,'Theo and unspecified companion return from pump',type='move',factuality='reported')
E('uncertain_memory',347,'Theo tentatively believes bell memory',type='state',actor='e2',roles={'experiencer':[346]})
U('memory_report',339,'e2','p18','e1','tentative_recollection',primary=False,scope='s0')
E('follow_back',349,'Nora and Theo follow path toward camp',type='move',actor='e5',roles={'actor':[348],'route':[351],'direction':[353]})
E('path_split',356,'path splits into two trails',type='state',patients=['e16'],roles={'patient':[355]})
E('bridge_route',359,'one trail curves past bridge',type='state',patients=['e17'],roles={'patient':[358],'landmark':[362]})
E('office_route',369,'other trail turns toward office',type='state',patients=['e18'],roles={'patient':[368],'landmark':[373]})
E('office_proposal',376,'Nora and Theo check office',type='perceive',actor='e5',patients=['e22'],factuality='hypothetical',roles={'actor':[374],'patient':[378]})
U('office_suggestion',380,'e1','p19','e2','suggestion',roles={'actor':[379]})
E('possible_finder',383,'unspecified person finds Moss',type='obtain',patients=['e6'],factuality='hypothetical',roles={'unresolved_actor':[382],'patient':[384]})
E('stare_bridge',386,'Theo stares at bridge',type='perceive',actor='e2',patients=['e20'],roles={'actor':[385],'patient':[389]})
E('path_dip',394,'bridge-side path dips among shrubs',type='state',patients=['e17'],roles={'patient':[393],'landmark':[397]})
E('not_want_route',400,'Theo wants to go along bridge-side trail',type='feel',actor='e2',factuality='negated',roles={'experiencer':[398]})
E('unwanted_route',402,'Theo goes along bridge-side trail',type='move',actor='e2',factuality='hypothetical',roles={'destination':[403]})
U('route_boundary',400,'e2','p39','e1','state_boundary',primary=False,scope='s0')
E('want_hurry',405,'Nora wants to hurry',type='feel',actor='e1',roles={'experiencer':[404]})
E('hurry_goal',407,'Nora hurries',type='move',actor='e1',factuality='desired')
E('possible_roll',411,'Moss rolls down trail',type='move',patients=['e6'],factuality='hypothetical',roles={'patient':[409],'path':[414]})
E('time_matters',417,'every minute matters under possible rolling',type='state',factuality='hypothetical')
E('alone_carry',420,'Nora carries lantern ahead without Theo',type='move',actor='e1',patients=['e10'],factuality='hypothetical',roles={'actor':[418],'patient':[422]})
E('alone_go',424,'Nora goes ahead without Theo',type='move',actor='e1',factuality='hypothetical')
E('theo_alone',429,'Theo is alone at fork without lantern light',type='state',actor='e2',factuality='hypothetical',roles={'actor':[427],'location':[433]})
U('okay',442,'e1','p39','e2','acknowledge_boundary',roles={'actor':[441]})
E('stay_promised',444,'Nora and Theo stay together',type='state',actor='e5',factuality='desired',roles={'actor':[443]})
E('tell_memory_requested',447,'Theo tells Nora his memory',type='speak',actor='e2',recipient='e1',factuality='desired',roles={'actor':[446],'recipient':[448]})
E('remember',451,'Theo remembers earlier journey details',type='state',actor='e2',factuality='hypothetical',roles={'experiencer':[450]})
U('joint_plan',444,'e1','p26','e2','promise',primary=False,scope='s0')
U('ask_memory',447,'e1','p27','e2','request',primary=False,scope='s0')
E('breath',453,'Theo takes a breath',actor='e2',roles={'actor':[452]})
M('earlier_return',458,'action','Theo adds his own running manner to the same earlier return; unknown we membership stays unresolved.')
M('heard_before',464,'action','More specific recollection of the same prior jingle, not a second hearing episode.')
U('detail_memory',464,'e2','p28','e1','recollection',primary=False,scope='s0')
E('approach_bridge',473,'Nora and Theo walk side by side to bridge',type='move',actor='e5',roles={'actor':[472],'destination':[475]})
E('sweep_light',483,'Nora sweeps lantern over bridge boards',type='move',actor='e1',patients=['e10'],roles={'actor':[482],'patient':[485],'surface':[488]})
E('light_reveals',491,'lantern light reveals leaves and creek reflection',type='state',patients=['e67','e66'],instruments=['e33'],roles={'causer':[490],'patient':[495,502]})
E('lean_near',505,'Theo leans close to Nora',type='move',actor='e2',roles={'actor':[504],'landmark':[508]})
U('point_found',509,'e2','p42','e1','deictic_discovery',primary=False,scope='s0')
E('locate_moss',513,'Nora and Theo locate Moss beside path',type='perceive',actor='e5',patients=['e6'],roles={'visible_patch':[512],'landmark':[518,521]})
E('caught_ear',524,'Moss is caught by ear on low branch',type='state',patients=['e6'],roles={'patient':[522],'caught_part':[528]})
E('faint_ring',535,'Moss bell makes faint sound',patients=['e73'],instruments=['e8'],roles={'source':[534],'result':[538]})
E('recovery_branch_shift',542,'recovery branch shifts',type='move',patients=['e27'],roles={'patient':[541]})
E('reachable',545,'Nora can reach Moss',type='state',actor='e1',patients=['e6'],roles={'actor':[543],'patient':[546]})
E('branch_extends',550,'low branch extends over blackberry canes',type='state',patients=['e27'],roles={'patient':[549],'landmark':[557]})
E('look_canes',559,'Theo looks at dark cane tangle',type='perceive',actor='e2',patients=['e29'],roles={'actor':[558],'patient':[563]})
E('back_away',565,'Theo backs away from cane tangle',type='move',actor='e2')
E('hold_requested',569,'Theo holds lantern steady',type='state',actor='e2',patients=['e10'],factuality='desired',roles={'actor':[568],'patient':[571]})
U('request_lantern_help',574,'e1','p29','e2','request',roles={'actor':[573]})
E('reach_plan',576,'Nora reaches from path',type='move',actor='e1',factuality='desired',roles={'actor':[575],'location':[579]})
E('prohibit_approach',581,'Theo moves closer to recovery branch',type='move',actor='e2',factuality='desired')
U('prohibition',581,'e1','p45','e2','prohibit',primary=False,scope='s0')
E('swallow',584,'Theo swallows',actor='e2',roles={'actor':[583]})
E('take_lantern',587,'Theo takes lantern with both hands',type='transfer',actor='e2',patients=['e10'],recipient='e2',roles={'actor':[586],'patient':[589],'effector':[592]})
E('light_wobble',595,'lantern light wobbles once',type='move',patients=['e33'],roles={'patient':[594]})
E('shadow_cast',597,'light casts crooked branch shadow over bridge',type='state',patients=['e39'],instruments=['e33'],roles={'result':[601],'surface':[604]})
U('reassure_shadow',610,'e1','p32','e2','remind',roles={'actor':[609],'addressee':[611]})
E('aim_lower',613,'Theo aims lantern lower',type='move',actor='e2',patients=['e10'],roles={'actor':[612],'patient':[615]})
E('shadow_shrink',619,'branch shadow shrinks',type='state',patients=['e39'],roles={'patient':[618]})
E('see_ear',622,'Theo sees Moss ear',type='perceive',actor='e2',patients=['e7'],roles={'actor':[620],'patient':[624]})
U('ear_report',622,'e2','p33','e1',primary=False,scope='s0')
E('crouch',626,'Nora crouches',type='move',actor='e1',roles={'actor':[625]})
E('stretch_reach',628,'Nora stretches beneath pine toward Moss',type='move',actor='e1',roles={'landmark':[631]})
E('thorn_snag',634,'thorn snags Nora sleeve',type='state',patients=['e31'],roles={'causer':[633],'patient':[636]})
E('free_sleeve',639,'Nora works sleeve free from thorn',actor='e1',patients=['e31'],roles={'actor':[638],'patient':[640]})
E('grasp_collar',643,'Nora grasps Moss by collar',actor='e1',patients=['e6'],roles={'patient':[644],'grasped_part':[648]})
E('pull_moss',650,'Nora pulls Moss gently',type='move',actor='e1',patients=['e6'],roles={'actor':[649]})
E('moss_free',654,'Moss comes loose from branch',type='state',patients=['e6'],roles={'patient':[653]})
E('leaves_fur',657,'leaves stick to Moss fur',type='state',patients=['e68'],roles={'patient':[656],'surface':[660]})
E('release_chime',664,'Moss bell gives one bright chime',patients=['e74'],instruments=['e8'],roles={'source':[663],'result':[667]})
E('hug',669,'Theo hugs Moss to chest',actor='e2',patients=['e6'],roles={'actor':[668],'patient':[670],'landmark':[673]})
M('locate_moss',675,'action','Theo credits Nora for contribution to the already established shared locating/recovery episode.')
U('credit_nora',675,'e2','p34','e1','credit_contribution',primary=False,scope='s0')
M('locate_moss',678,'action','Nora explicitly credits the shared episode, not a new discovery.')
U('credit_joint',681,'e1','p35','e2','reframe_joint_credit',roles={'actor':[680]})
E('rub_mark',682,'Nora rubs thorn mark on sleeve',actor='e1',patients=['e32'],roles={'patient':[685],'surface':[688]})
U('supper_call',694,'e3','p36','e5','call_to_meal',roles={'actor':[693]})
E('return_camp',697,'Nora and Theo return along marked path',type='move',actor='e5',roles={'actor':[696],'route':[701]})
E('carry_moss_back',704,'Theo carries Moss back',type='move',actor='e2',patients=['e6'],roles={'actor':[703],'patient':[705]})
E('carry_lantern_back',708,'Nora carries lantern back',type='move',actor='e1',patients=['e10'],roles={'actor':[707],'patient':[710]})
E('reach_table',713,'Nora and Theo reach picnic table',type='move',actor='e5',roles={'actor':[712],'destination':[716]})
E('hand_out',719,'father holds out hand for lantern',actor='e4',patients=['e54'],roles={'actor':[718],'effector':[722],'requested_object':[724]})
E('return_lantern',726,'Nora gives lantern back to father',type='transfer',actor='e1',patients=['e10'],recipient='e4',roles={'actor':[725],'patient':[727]})
E('sit_supper',730,'Theo sits beside warm pot',type='move',actor='e2',roles={'actor':[729],'landmark':[734]})
E('set_moss',736,'Theo sets Moss on bench',type='move',actor='e2',patients=['e6'],roles={'patient':[737],'destination':[740]})
E('smooth_ear',742,'Theo smooths Moss bent ear',actor='e2',patients=['e7'],roles={'actor':[741],'patient':[746]})
E('three_shadows',752,'lantern light casts three shadows on tent wall',type='state',patients=['e40'],instruments=['e10'],roles={'causer':[751],'result':[754],'surface':[758]})
E('lean_back',772,'Theo leans back',type='move',actor='e2',roles={'actor':[771]})
E('allow_shadows',775,'Theo allows all three shadows to remain',type='state',actor='e2',patients=['e40'],roles={'patient':[776]})
E('shadows_stay',778,'three shadows remain',type='state',patients=['e40'])

# Grammatical features are attached to the actual word/form, not inferred from
# event factuality or from a globally repeated spelling.
F([0,7,29,80,93,100,107,128,145,157,175,185,200,204,214,225,227,241,244,254,265,274,286,289,293,300,307,314,350,361,364,367,371,377,388,392,413,421,432,435,461,470,480,484,487,489,497,500,520,531,540,548,561,570,578,588,593,603,607,614,617,630,632,643,652,661,683,690,699,709,714,732,739,743,749,756,757],determiner_kind='definite_article',definiteness='definite')
# Remove nonarticle offsets from this authored article list; some nouns themselves
# carry definiteness through their own explicit mention instead.
for w in [500,632,643,661,757]:
    a.words[w].pop('determiner_kind',None);a.words[w].pop('definiteness',None)
F([22,54,142,208,256,332,454,465,492,510,515,536,552,598,632,721,762],determiner_kind='indefinite_article',definiteness='indefinite')
F([17,35,45,59,69,95,138,153,178,192,222,261,279,329,340,533,623,635,659,662,672,687,692,717],determiner_kind='possessive',grammatical_case='genitive',possessive_construction='prenominal_possessive')
F([269,744,750,759,760],grammatical_case='genitive',genitive_realization='singular_s_clitic',possessive_construction='prenominal_s_genitive')
F(196,personal_pronoun_series='independent_possessive',grammatical_case='genitive',phrase_has_elision=True,
  reference_metonymic_link={'literal':'e50','possessor':'e1','relation':'omitted_shoulder_in_possessive_phrase'})
F([303,438],determiner_kind='negative')
F(415,determiner_kind='universal_distributive')
F(591,determiner_kind='total_dual',cardinal_value=2)
F(769,determiner_kind='demonstrative',definiteness='definite')
F(777,determiner_kind='universal_group')
for w,n in [(31,1),(50,1),(249,1),(357,1),(526,1),(596,1),(665,1),(753,3),(766,1)]:F(w,cardinal_value=n)
F([2,8,81,101,143,301,372,501,556,684,715],dependency_relation='nominal_modifier')
for head,mods in [(9,[8]),(82,[81]),(102,[101]),(246,[245]),(302,[301]),(373,[372]),(518,[517]),(557,[556]),(685,[684]),(716,[715]),(758,[757])]:F(mods,syntactic_governor_id=a.anchor(head),dependency_relation='nominal_modifier')
F([20,36,70,94,97,108,129,223,232,246,330,335,397,436,488,495,557,592,656,754],grammatical_number='plural')
F([83,88,103,316,338,346,398,456,463,620],grammatical_person=1,grammatical_case='subjective',mention_form='personal_pronoun')
F([73,323,446,450,568,674],grammatical_person=2,mention_form='personal_pronoun')
F([76,85,132,196,319,326,384,448,508,546,611,640,670,676,679,724,727,748,776],mention_form='personal_pronoun')
F([76,85,132,319,326,384,448,508,546,611,640,670,676,679],grammatical_case='objective')
F([41,119,136,150,160,197,218,276,284,298,321,348,355,374,418,441,472,586,638,649,677,696,712,741],mention_form='personal_pronoun')
F([133,197,298,348,374,443,472,677,696,712,748],grammatical_number='plural',split_antecedent_ids=['e1','e2'])
F(343,grammatical_person=1,grammatical_number='plural',mention_form='personal_pronoun',
  evidence=[338,339,343,344,345,456,458],note='Earlier we includes Theo but no other member is securely identified; it is not equated with Nora-and-Theo search group.')
F(89,contraction_expansion=['did','not'],verb_phrase_ellipsis=True,do_support_status='negative_auxiliary')
F(104,contraction_expansion=['can','not'])
F([133,443],contraction_expansion=['we','will'])
F(220,contraction_expansion=['let','us'],imperative_subject_status='inclusive_first_plural')
F(317,contraction_expansion=['should','have'])
F(331,contraction_expansion=['that','is'])
F(399,contraction_expansion=['do','not'],do_support_status='negative_auxiliary')
F(575,contraction_expansion=['I','will'])
F(580,contraction_expansion=['do','not'],do_support_status='negative_imperative')
F(605,contraction_expansion=['it','is'])
F([5,26,42,44,63,78,91,98,113,121,137,148,161,174,183,188,194,198,207,212,219,229,234,243,258,263,268,277,285,291,296,299,306,312,322,337,349,356,359,369,380,386,394,405,442,453,473,483,491,505,513,535,542,550,559,565,574,584,587,595,610,613,619,626,628,634,639,643,650,654,669,675,678,681,694,697,713,719,726,730,736,742,752,772,775],verb_form='finite',tense='past')
F([39,109,110,170,347,400,417,429],verb_form='finite',tense='present')
# Hypothetical past morphological forms remain past morphology, not actual facts.
F([84,383,417],verb_form='finite',tense='past')
F([16,27,141,162,325,328,458,597,657,664,682,704,708],verb_form='present_participle')
F(657,verb_form='past_participle',participial_function='absolute_clause_predicate')
F([57,158,283,318,411,524,700],verb_form='past_participle')
F([57,158,700],participial_function='nominal_modifier')
F([19,75,105,106,115,124,125,131,134,152,155,166,221,239,376,402,407,420,424,444,447,451,545,569,576,581,622,778],verb_form='bare')
F(125,verb_form='present_participle')
for marker,head,controller in [(67,68,'e2'),(114,115,'e1'),(123,124,'e2'),(401,402,'e2'),(406,407,'e1')]:
    F(marker,constituent_category='infinitive_marker',syntactic_governor_id=a.anchor(head))
    F(head,verb_form='infinitive',infinitive_marker_id=a.anchor(marker),subject_controller_id=controller)
for head,aux in [(16,15),(141,140),(325,324),(328,324),(458,457)]:F(head,aspect='progressive',progressive_auxiliary_id=a.anchor(aux),auxiliary_chain=['be'])
for head,aux in [(283,282),(318,317),(411,410),(524,523)]:F(head,aspect='perfect',perfect_auxiliary_id=a.anchor(aux),auxiliary_chain=['have'])
F(318,auxiliary_chain=['should','have'])
F([155,166,447,581],imperative_subject_status='understood_second_person')
F([72,567],subject_auxiliary_inversion=True)
F([104,130,151,238,317,375,419,428,544,567,621],modal_auxiliary_class='modal')
F(104,modal_base={'kind':'self_reported_inability','holder':'e2','content_id':'p4'},proposition_polarity='negative',negation_scope_id='p4')
F(130,modal_base={'kind':'figurative_fear_possibility','holder':'e1'})
F(151,modal_base={'kind':'permission_request','holder':'e1','content_id':'p9'})
F(238,modal_base={'kind':'enabled_ability_purpose','holder':'e2','action_event_id':EV['keepup']})
F(317,modal_base={'kind':'retrospective_ought','holder':'e2','content_id':'p16'})
F(375,modal_base={'kind':'proposed_option','holder':'e1','content_id':'p19'})
F(419,modal_base={'kind':'considered_option','holder':'e1','content_id':'p24'})
F(428,modal_base={'kind':'conditional_consequence','holder':'e1','condition_id':'p24','content_id':'p25'})
F(544,modal_base={'kind':'physical_reachability','holder':'e1','target':'e6'})
F(567,modal_base={'kind':'request','holder':'e1','content_id':'p29'})
F(621,modal_base={'kind':'perceptual_access','holder':'e2','content_id':'p33'})
for w,pid in [(89,'p3'),(216,'p12'),(303,'p37'),(399,'p38'),(580,'p31')]:F(w,proposition_polarity='negative',negation_scope_id=pid)
F(581,proposition_polarity='negative',negation_scope_id='p31',factuality='desired',
  evidence=[575,576,579,580,581,582],note='The desired content is NOT moving closer; this is a prohibition, not evidence of completed approach or a global claim Theo never moves.')
F(438,proposition_polarity='negative',negation_scope_id='p41')
a.proposition('p41','Theo has lantern light at the fork if Nora goes ahead.',[427,429,433,438,439],scope_id='s8')
F([216,273,303,509,695],sentence_fragment_type='contextual_utterance_fragment')
F([320,582,616],adverb_degree='comparative')
F([1,33,37,46,47,51,55,60,96,111,158,179,209,231,247,252,280,297,308,365,396,430,466,498,511,516,527,537,555,562,572,599,600,641,647,655,666,700,733,745,763,767],adjective_degree='positive')
for w in [158,700]:a.words[w].pop('adjective_degree',None)
for w,dimension,direction in [(46,'size','small'),(96,'length','long'),(231,'height','tall'),(365,'depth','shallow'),(466,'sound_level','low'),(516,'height','low'),(599,'height','tall'),(733,'temperature','warm'),(763,'size','small')]:F(w,lexical_scale_dimension=dimension,lexical_scale_direction=direction)
F(665,temporal_iteration_count=1)
F(596,temporal_iteration_count=1)

SUBJECTS={
'e1':[16,78,113,121,137,148,174,207,234,277,285,306,380,405,407,420,424,442,483,545,574,576,610,626,628,639,643,650,681,682,708,726],
'e2':[26,42,63,68,75,84,89,91,105,124,125,188,212,219,239,268,312,318,322,325,328,337,339,347,386,400,402,429,447,451,453,458,464,505,559,565,569,584,587,613,622,669,704,730,736,742,772,775],
'e3':[19,170,694], 'e4':[141,161,162,719], 'e5':[134,198,299,349,376,444,473,678,697,713],
'e6':[39,44,411,524,654], 'e7':[745], 'e10':[243], 'e25':[258,272,291,296], 'e26':[263],
'e27':[542,550], 'e33':[183,491,595,752], 'e34':[98], 'e39':[619], 'e43':[5], 'e51':[283],
'e16':[229,356], 'e17':[359,394], 'e18':[369], 'e49':[194], 'e76':[513], 'e8':[535,664], 'e68':[657], 'e40':[778],
}
for entity,words in SUBJECTS.items():F(words,grammatical_subject_id=entity)
# Bent ear is a nominal modifier, not a finite predication.
a.words[745].pop('grammatical_subject_id',None)
F(675,grammatical_subject_id='e1')
F(634,grammatical_subject_id='e30')
F(110,grammatical_subject_id='e75')
for w,eid in [(19,'e45'),(63,'e6'),(68,'e48'),(75,'e6'),(84,'e6'),(115,'e6'),(121,'e2'),(152,'e10'),(162,'e10'),(174,'e10'),(207,'e57'),(243,'e36'),(268,'e31'),(285,'e10'),(299,'e15'),(306,'e59'),(318,'e6'),(325,'e6'),(328,'e52'),(339,'e8'),(349,'e16'),(376,'e22'),(383,'e6'),(420,'e10'),(464,'e72'),(483,'e10'),(491,'e67'),(545,'e6'),(569,'e10'),(587,'e10'),(613,'e10'),(622,'e7'),(634,'e31'),(639,'e31'),(643,'e6'),(650,'e6'),(669,'e6'),(675,'e6'),(678,'e6'),(682,'e32'),(704,'e6'),(708,'e10'),(713,'e13'),(719,'e54'),(726,'e10'),(736,'e6'),(742,'e7'),(752,'e40'),(775,'e40')]:F(w,grammatical_object_id=eid)
# Direct objects absent in look/stare/peer + PP; their semantic patients remain.
for w,eid in [(6,'e13'),(10,'e11'),(21,'e44'),(28,'e14'),(58,'e9'),(79,'e15'),(92,'e35'),(99,'e64'),(144,'e56'),(156,'e16'),(184,'e61'),(195,'e50'),(199,'e13'),(203,'e14'),(213,'e58'),(224,'e15'),(230,'e35'),(264,'e16'),(292,'e63'),(313,'e60'),(352,'e12'),(360,'e20'),(363,'e21'),(370,'e22'),(387,'e20'),(390,'e20'),(395,'e65'),(412,'e17'),(431,'e19'),(460,'e15'),(469,'e20'),(474,'e20'),(479,'e23'),(486,'e24'),(507,'e1'),(514,'e27'),(519,'e17'),(525,'e7'),(530,'e62'),(551,'e29'),(560,'e29'),(577,'e16'),(590,'e52'),(602,'e20'),(629,'e28'),(645,'e9'),(658,'e69'),(671,'e53'),(686,'e31'),(689,'e12'),(698,'e16'),(723,'e10'),(731,'e44'),(738,'e70'),(747,'e5'),(755,'e71')]:F(w,prepositional_object_id=eid)
F(447,indirect_object_id='e1')
for w,typ in [(24,'temporal_when'),(126,'comparative_as_if'),(149,'embedded_interrogative'),(168,'future_temporal_condition'),(191,'result'),(236,'purpose'),(278,'concessive'),(310,'temporal_while'),(342,'temporal_when'),(408,'conditional'),(539,'temporal_as'),(711,'temporal_when')]:F(w,subordinator_type=typ)
for w,relation in [(34,'addition'),(53,'addition'),(86,'addition'),(120,'addition'),(165,'addition'),(202,'addition'),(251,'contrast_sides'),(260,'addition'),(278,'concession'),(327,'addition'),(426,'adverse_consequence'),(437,'addition'),(547,'obstacle_contrast'),(564,'addition'),(627,'addition'),(637,'obstacle_contrast'),(642,'addition'),(661,'addition'),(706,'addition'),(735,'addition'),(761,'addition'),(774,'addition')]:F(w,discourse_relation_kind=relation)
for w,relation in [(24,'when'),(87,'then'),(117,'before'),(168,'when'),(295,'then'),(310,'overlap'),(342,'when'),(496,'then'),(539,'overlap'),(585,'then'),(711,'when')]:F(w,temporal_signal_relation=relation)
F(1,temporal_phase_cue='end_of_daylight')
F(118,time_expression_id='time_bedtime',temporal_anchor_unresolved=True)
F(63,temporal_frequency_class='habitual')
F(74,temporal_phase_cue='most_recent_prior_sighting')
F(416,measure_unit='minute',temporal_granularity='minute')
F(770,temporal_reference_shift={'from':'earlier_shadow_alarm','to':'current_shadows_at_supper'})

# Physical state, movement and holders are time-local bundles.
F(5,spatial_configuration=B('e43',{'landmark':'e13','relation':'across'}))
F(23,containment_contents=B('e44',{'contents':['e45'],'exhaustive':False}))
F(33,object_connection_state=B('e46','untied'))
F(37,object_moisture=B('e47','wet'))
F(47,appearance_color=B('e6','brown'))
F([60,647],appearance_color=B('e9','blue'))
F(511,appearance_color=B('e76','blue'))
F(55,material_composition=B('e8',{'material':'brass'}))
F(308,material_composition=B('e59',{'material':'wood'}))
F(57,object_attachment=B('e8',{'attached_to':'e9','method':'sewn'}))
F(733,object_temperature=B('e44','warm'))
F(179,lexical_sense_id='warm_visual_quality_of_light',evidence=[178,179,180,182],note='Warm describes the light appearance; it does not establish a measured or literal heat state of its illuminated target.')
for w,part,whole in [(52,'e7','e6'),(61,'e9','e6'),(36,'e47','e2'),(70,'e48','e2'),(193,'e49','e2'),(196,'e50','e1'),(281,'e51','e1'),(330,'e52','e2'),(315,'e60','e15'),(481,'e23','e20'),(488,'e24','e20'),(528,'e7','e6'),(592,'e52','e2'),(660,'e69','e6'),(673,'e53','e2'),(722,'e54','e4'),(746,'e7','e6'),(758,'e71','e14'),(768,'e42','e41')]:F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
F(48,identity_hypothesis={'entity_id':'e6','type_alternatives':['toy_rabbit','live_rabbit'],'assertion_status':'candidate','scope_id':'s0'},
  evidence=[43,48,52,56,57,61,64,68,524,742,745,746],note='Story never says toy, stuffed, alive or pet. Ear, fur, carrying, snagging and smoothing remain literal physical descriptions compatible with either type; no autonomous animal behavior or injury is inferred.')
F(44,possession_owner=B('e6',{'owner':'e2'}))
F(84,possession_holder=B('e6',{'holder':'e2','location':'e15'},'q3','attributed_claim'))
F(89,possession_holder=B('e6',{'previous_holder':'e2','still_held':False},'q3','attributed_claim'))
F(154,possession_owner=B('e10',{'owner':'e4'}))
F(162,possession_holder=B('e10',{'holder':'e1'}),possession_borrower=B('e10',{'borrower':'e1'}),possession_lender=B('e10',{'lender':'e4'}),transfer_kind=B('e10','temporary_loan'),transfer_completion=B('e10',{'completed':True}),transfer_source=B('e10',{'source':'e4'}),transfer_recipient=B('e10',{'recipient':'e1'}))
F(141,spatial_configuration=B('e55',{'landmark':'e56','relation':'on'}))
F(174,object_luminosity=B('e10','lit'),event_state_change=B('e10',{'before':'off','after':'on','event_id':EV['switch_on']}))
F(183,spatial_configuration=B('e33',{'landmark':'e61','relation':'on'}))
F(194,spatial_contact=B('e49',{'touches':'e50'}))
F(188,spatial_distance_band=B('e2',{'landmark':'e1','distance':'shoulder_touching'}))
F(198,event_collective_participants=B('e5',{'event_id':EV['check_camp'],'actors':['e1','e2']}))
F(229,spatial_configuration=B('e16',{'landmark':'e35','relation':'between'}),lexical_sense_id='static_path_curvature')
F(239,event_goal_role=B('e1',{'event_id':EV['walk_out'],'goal_event_id':EV['keepup'],'goal_state':'Theo_can_keep_pace'}))
F(247,object_luminosity=B('e37',{'illumination':'externally_lit','source':'e10'}))
# Externally lit side is not a self-luminous object.
a.words[247].pop('object_luminosity')
F(247,attributes=[{'name':'illumination','value':'bright_on_lantern_facing_side'}])
F(252,appearance_color=B('e38',{'perceived_color':'black','cause':'unlit_side'}))
F(263,spatial_configuration=B('e26',{'landmark':'e16','relation':'across'}))
F(285,spatial_orientation=B('e10',{'direction':'upward'}))
F(291,event_causer=B('e25',{'causer':'e63','event_id':EV['branch_sway']}))
F(296,attributes=[{'name':'motion_state','value':'still'}])
F(299,motion_destination=B('e5',{'event_id':EV['reach_pump'],'landmark_id':'e15','role':'destination'}))
F(349,motion_route=B('e5',{'event_id':EV['follow_back'],'landmark_id':'e16','role':'actual_route'}))
F(359,spatial_configuration=B('e17',{'landmark':'e20','relation':'past'}),lexical_sense_id='static_path_curvature')
F(362,spatial_configuration=B('e20',{'landmark':'e21','relation':'over'}))
F(369,spatial_configuration=B('e18',{'landmark':'e22','relation':'toward'}),lexical_sense_id='static_path_direction')
F(394,spatial_configuration=B('e17',{'landmark':'e65','relation':'dips_between'}),lexical_sense_id='static_path_gradient')
F(473,motion_destination=B('e5',{'event_id':EV['approach_bridge'],'landmark_id':'e20','role':'destination'}),event_collective_participants=B('e5',{'actors':['e1','e2']}))
F(476,lexical_idiom_reading={'meaning':'walking_adjacent','expression':'side_by_side'})
F(483,event_setting=B('e1',{'setting':'e23','event_id':EV['sweep_light']}))
F(498,appearance_color=B('e66',{'perceived_color':'silver','mode':'reflected_shine'}),evidence=[490,491,498,499,501,502],note='Silver is perceived reflected water shine, not silver material and not autonomous emitted light.')
F(505,spatial_distance_band=B('e2',{'landmark':'e1','distance':'close'}))
F(512,identity_hypothesis={'entity_id':'e76','possible_source':'e9','relation':'visible_blue_patch_may_be_collar','assertion_status':'candidate'},evidence=[511,512,522,647,648],note='Blue patch is linked to found Moss; its identity with the collar is plausible but not explicit, so it is not merged with collar entity.')
F(524,object_attachment=B('e6',{'attached_to':'e27','caught_part':'e7','mode':'snagged'}),spatial_configuration=B('e6',{'landmark':'e62','relation':'just_above'}))
F(518,spatial_configuration=B('e27',{'landmark':'e17','relation':'beside'}))
F(535,object_sound_level=B('e8','faint'),causal_parent=B('e8',{'cause':EV['recovery_branch_shift'],'effect':EV['faint_ring']},status='candidate'),evidence=[534,535,538,539,541,542],note='Timing supports branch movement as a candidate cause of bell sound; exact force chain is not asserted.')
F(545,access_reachability=B('e6',{'actor':'e1','reachable':True,'hazard':'e29'}))
F(550,spatial_configuration=B('e27',{'landmark':'e29','relation':'over'}))
F(555,object_surface_condition=B('e29','prickly'))
F(565,motion_source=B('e2',{'event_id':EV['back_away'],'landmark_id':'e29','role':'away_from'}))
F(587,possession_holder=B('e10',{'holder':'e2'}),transfer_recipient=B('e10',{'recipient':'e2'}),transfer_source=B('e10',{'source':'e1'}),event_effector=B('e2',{'effector':'e52'}))
F(597,spatial_configuration=B('e39',{'landmark':'e20','relation':'projected_over'}),figurative_mapping={'target_id':'e39','source_image':'painting','kind':'metaphor','literal_event':False})
F(605,reference_metonymic_link={'literal':'e39','referent':'e27','relation':'shadow_of_branch'})
F(613,spatial_orientation=B('e10',{'direction_change':'lower'}))
F(619,event_state_change=B('e39',{'dimension':'projected_size','change':'smaller','event_id':EV['shadow_shrink']}))
F(634,object_attachment=B('e31',{'attached_to':'e30','mode':'snagged'}))
F(639,object_attachment=B('e31',{'previous_attachment':'e30','attached_after':False}))
F(643,event_contact_mode=B('e6',{'contact_part':'e9','agent':'e1','mode':'grasp'}))
F(650,event_manner=B('e1',{'event_id':EV['pull_moss'],'manner':'gently'}))
F(654,object_attachment=B('e6',{'previous_attachment':'e27','attached_after':False}),event_state_change=B('e6',{'before':'caught_by_ear','after':'loose','event_id':EV['moss_free']}))
F(657,object_attachment=B('e68',{'attached_to':'e69','mode':'stuck'}))
F(669,possession_holder=B('e6',{'holder':'e2'}),spatial_contact=B('e6',{'touches':'e53'}))
F(704,possession_holder=B('e6',{'holder':'e2'}))
F(708,possession_holder=B('e10',{'holder':'e1'}),evidence_missing={'needed':'unreported_lantern_handoff_from_Theo_back_to_Nora'},
  evidence=[587,589,613,615,707,708,710],note='Nora is explicitly carrying the lantern on return. No event for Theo giving it back is invented; intervening transfer is unreported.')
F(713,motion_destination=B('e5',{'event_id':EV['reach_table'],'landmark_id':'e13','role':'destination'}))
F(726,possession_holder=B('e10',{'holder':'e4'}),transfer_kind=B('e10','loan_return'),transfer_completion=B('e10',{'completed':True}),transfer_recipient=B('e10',{'recipient':'e4'}))
F(736,spatial_support=B('e6',{'supported_by':'e70'}),motion_destination=B('e6',{'event_id':EV['set_moss'],'landmark_id':'e70','role':'destination'}))
F(745,object_shape=B('e7','bent'))
F(742,event_state_change=B('e7',{'action':'smoothing','prior_shape':'bent','final_shape_unspecified':True}))
F(752,spatial_configuration=B('e40',{'landmark':'e71','relation':'on'}))
F(754,attributes=[{'name':'shadow_casters','value':'Theo, Nora, Moss'}])
F(764,reference_metonymic_link={'literal':'e41','referent':'e6','relation':'shadow_of'})
F(768,reference_metonymic_link={'literal':'e42','referent':'e7','relation':'silhouette_of_ear'})

# Mental content, communication and inference retain holder/scope attribution.
F(113,goal_owner_id='e1',goal_content_id='p6',goal_polarity='achieve',goal_status='active',goal_deadline={'relation':'before','anchor':'time_bedtime'})
F(121,goal_owner_id='e1',goal_content_id='p7',goal_polarity='achieve',goal_status='active',goal_beneficiary_ids=['e2'])
F(131,figurative_mapping={'target_id':'e34','source_image':'swallowing_Theo','kind':'personification','literal_event':False},
  evidence=[121,122,124,125,126,127,129,131,132],note='Nora wants Theo to stop appearing frightened. Shadows are not literal predators or agents.')
F(137,promise_content_id='p8',promise_beneficiary_id='e2',plan_commitment_status='promised')
F(148,request_action_id='p9',request_acceptance_status='granted_by_handoff')
F(162,permission_grantor_id='e4',permission_recipient_id='e1',permission_content_id='p9',permission_status='granted_with_route_and_return_conditions',
  evidence=[148,152,155,159,161,162,166,170,172],note='The actual handoff licenses this requested loan; path and supper instructions remain bounded conditions, not blanket authority over all actions.')
F(155,obligation_debtor_id='e1',obligation_creditor_id='e4',obligation_content_id='p10',obligation_status='instructed')
F(166,obligation_debtor_id='e1',obligation_creditor_id='e4',obligation_content_id='p11',obligation_status='instructed')
F(170,temporal_deadline={'event_id':EV['return_instruction'],'condition_event_id':EV['anticipated_call'],'relation':'when'})
# Theo reports inability here; emotion is not an explicit self-report.
F(37,affect_observer_attribution={'experiencer_id':'e2','cue':'wet_cheeks','interpretation':'possible_recent_crying','assertion_status':'candidate','scope_id':'s0'},evidence=[25,36,37,38,40],note='Wet cheeks and missing Moss suggest distress; tears/crying are not explicitly narrated as a separate completed event.')
F(283,affect_observer_attribution={'experiencer_id':'e1','cue':'stomach_tightening_after_movement','interpretation':'possible_fear','assertion_status':'candidate','scope_id':'s0'},evidence=[272,275,278,281,283],note='Nora bodily tightening is explicit; the emotion reading is candidate and not a permanent trait.')
F(318,appraisal_responsibility={'responsible_id':'e2','for':'p1','source_id':'e2','scope_id':'q12','assertion_status':'candidate'},evidence=[316,317,318,319,320],note='Retrospective should-have-held-tighter is self-reproach, not proof that a specific grip failure caused the loss.')
F(322,communication_channel='whisper')
F(331,propositional_antecedent_id='p17')
F(335,lexical_sense_id='multiple_simultaneous_tasks')
F(325,temporal_overlap={'left':EV['earlier_carry'],'right':EV['earlier_wash'],'scope_id':'q13','assertion_status':'attributed_claim'})
F(347,belief_holder_id='e2',belief_content_id='p18',belief_certainty='tentative',epistemic_attitude_kind='uncertain_memory')
F(339,epistemic_access_mode='auditory_memory',belief_holder_id='e2',belief_content_id='p18',belief_certainty='tentative')
F(464,epistemic_access_mode='auditory_memory',belief_holder_id='e2',belief_content_id='p28',evidence=[339,341,344,347,458,464,467,471],note='Second report supplies bridge location for the same earlier jingle memory. Narrator does not independently establish the exact loss time or full membership of earlier we.')
F(381,modal_base={'kind':'epistemic_possibility','holder':'e1','content_id':'p20'})
F(383,belief_holder_id='e1',belief_content_id='p20',belief_certainty='possible',epistemic_attitude_kind='hypothesis')
F(400,goal_owner_id='e2',goal_content_id='p21',goal_status='explicitly_not_desired',
  goal_scope_bundle={'owner_id':'e2','intention_event_id':EV['not_want_route'],'scope_id':'q17','assertion_status':'attributed_claim'},
  boundary_preference={'owner_id':'e2','excluded':'p21','scope_id':'q17','assertion_status':'attributed_claim'},
  evidence=[386,389,396,397,398,399,400,402,403],note='Negated desire for that route is not an active avoidance goal. Later walking together toward the bridge is a new choice under support, not an erasure of the earlier preference.')
F(405,goal_owner_id='e1',goal_content_id='p22',goal_status='active',goal_polarity='achieve')
F(411,belief_holder_id='e1',belief_content_id='p23',belief_certainty='conditional_possibility',assertion_status='attributed_claim')
F([420,424],plan_commitment_status='considered_not_executed',assertion_status='attributed_claim')
F(429,assertion_status='attributed_claim',plan_contingency={'if':'p24','then':'p25'},evidence=[418,419,420,424,427,429,430,433,438,443,444,473],note='Going alone and leaving Theo without light are counterfactual considered consequences. Actual next movement remains together.')
F(442,dialogue_response_to_id=EV['route_boundary'])
F(444,promise_content_id='p26',promise_beneficiary_id='e2',plan_commitment_status='promised',plan_revision={'considered':'p24','adopted':'p26'})
F(447,request_action_id='p27',request_acceptance_status='answered_with_memory')
F(464,dialogue_response_to_id=EV['ask_memory'])
F(574,request_action_id='p29',request_acceptance_status='accepted_by_taking_lantern')
F(576,intention_holder_id='e1',intention_content_id='p30',plan_commitment_status='communicated')
F(581,obligation_debtor_id='e2',obligation_creditor_id='e1',obligation_content_id='p31',obligation_status='prohibited',speaker_id='e1')
F(587,intention_vs_action_alignment={'requested':'p29','action_event_id':EV['take_lantern'],'alignment':'takes_lantern_then_adjusts_aim'},cooperation_goal_id='p6')
F(610,dialogue_response_to_id=EV['moved_report'],dialogue_turn_function='reapply_branch_shadow_explanation',evidence=[263,272,275,597,601,605,608],note='Nora repeats the explanation pattern for a later shadow. Distinct branch/shadow IDs preserve uncertainty about physical branch identity.')
F(675,event_divided_labor=B('e5',{'shared_event_id':EV['locate_moss'],'credited_contributor':'e1','contributions':{'e1':[EV['sweep_light'],EV['stretch_reach'],EV['pull_moss']]},'claim_source':'e2'},'q26','attributed_claim'))
F(678,event_collective_participants=B('e5',{'shared_event_id':EV['locate_moss'],'actors':['e1','e2']},'q27','attributed_claim'),
  event_divided_labor=B('e5',{'shared_event_id':EV['locate_moss'],'contributions':{'e1':[EV['sweep_light'],EV['pull_moss']],'theo_contribution_events':[EV['detail_memory'],EV['point_found'],EV['take_lantern'],EV['aim_lower']]}},'q27','attributed_claim'),
  evidence=[464,509,587,613,650,675,677,678,679],note='You found him credits Nora within the shared episode; We found him explicitly distributes credit. Neither pronoun becomes identical to a different actor/group, and there is no second discovery.')
F(681,dialogue_response_to_id=EV['credit_nora'],dialogue_repair_kind='inclusive_credit_reframe')
F(697,intention_vs_action_alignment={'instruction':'p11','action_event_id':EV['return_camp'],'trigger_event_id':EV['supper_call'],'alignment':'returns_after_call'},obligation_status='return_instruction_fulfilled')
F(775,affect_observer_attribution={'experiencer_id':'e2','interpretation':'increased_tolerance_of_these_familiar_shadows','scope_id':'s0','assertion_status':'candidate'},
  evidence=[104,268,400,595,601,605,613,619,754,771,772,775,778],note='Ending supports local acceptance of these shadows, not disappearance of all fear or a permanent fearless personality.')
F(778,narrative_thread_id='thread_moss_search_and_shadow_fear',narrative_resolution_evidence={'problem':'p1','outcome':'p35','status':'Moss_recovered_and_returned_to_Theo','assertion_status':'candidate'},
  narrative_change_dimension='shared_search_and_local_shadow_response',narrative_theme_candidate={'content':'shared_attention_and_practical_support_allow_a_frightening_search_to_continue','assertion_status':'candidate'},
  narrative_motif_link={'earlier_words':[97,131,262,601],'current_word':754,'relation':'threatening_shapes_reframed_as_familiar_three_shadows','assertion_status':'candidate'},
  narrative_closure_candidate={'cue':'Moss_on_bench_and_three_allowed_shadows','assertion_status':'candidate'},
  evidence=[104,134,268,444,473,587,613,654,669,697,736,754,775,778],note='Interpretive closure rests on recovery, togetherness and changed response to familiar shadows; it does not establish Moss biological type or global emotional recovery.')

# Final repairs after reading all forty assembled paragraphs.
a.proposition('p42','Moss is at the visible location beside the path beneath the low pine branch.',[509,511,512,518,521,522],scope_id='q21')
a.proposition('p43','Where did Theo last see Moss?', [71,73,75,76],scope_id='q2')
a.proposition('p44','Theo cannot go search in the darkening woods.',[103,104,105,106,108,111],scope_id='q4')
F(78,question_requested_slot='last_sighting_location',question_answer_status='answered_by_pump_report')
F(84,dialogue_response_to_id=EV['ask_last'])
F(110,verb_form='present_participle',aspect='progressive',progressive_auxiliary_id=a.anchor(109))
a.words[110].pop('tense',None)
F([339,344,464],verb_form='finite',tense='past')
F(451,verb_form='finite',tense='present')
F(429,verb_form='bare');a.words[429].pop('tense',None)
for w in [2,143]:a.words[w].pop('dependency_relation',None)
F(646,determiner_kind='definite_article',definiteness='definite')
F(258,event_causer=B('e25',{'causer':'e63','event_id':EV['branch_sway']}))
F(509,discourse_focus_id='e6',question_answer_status='Moss_location_resolved')
F(166,evidence=[147,148,152,155,160,161,162,166,169,170],note='Father responds to Nora’s loan request. Nora is the grounded addressee and instruction debtor; Theo may hear, but is not added as an independent confirmed audience from a shared later journey alone.')
F(675,reference_metonymic_link={'literal':'e1','relation':'individual_contributor_to_group_event','collective_actor':'e5','event_id':EV['locate_moss']})
F(458,event_collective_participants=B('e2',{'event_id':EV['earlier_return'],'known_participant':'e2','other_participants':'unspecified'},'q20','attributed_claim'))
F(754,group_members=['e41'])
# Membership is partial: Theo/Nora shadows are textually established but unnamed IDs.
a.words[754].pop('group_members')
F([759,760],phrase_has_elision=True,possessive_construction='independent_s_genitive')
F(759,reference_metonymic_link={'possessor':'e2','relation':'elided_shadow_cast_by','member_of':'e40'})
F(760,reference_metonymic_link={'possessor':'e1','relation':'elided_shadow_cast_by','member_of':'e40'})
a.entities['e40']['known_member_ids']=['e41']
F(51,object_shape=B('e7','floppy'))
F(600,object_shape=B('e39','crooked'))
F(537,object_sound_level=B('e73','faint'))
F(666,lexical_sense_id='clear_resonant_sound_quality')
F(651,event_manner=B('e1',{'event_id':EV['pull_moss'],'manner':'gently'}))
F(235,event_manner=B('e1',{'event_id':EV['walk_out'],'manner':'slowly'}))
F(223,lexical_sense_id='prior_traveled_route')
F(455,lexical_sense_id='inhalation',light_verb_construction='take_a_breath')
F(493,lexical_sense_id='disordered_collection')
F(499,lexical_sense_id='reflected_light')
F(439,lexical_sense_id='lantern_illumination_in_unchosen_option',factuality='hypothetical')
F([172,695],lexical_sense_id='evening_meal')
F(110,object_luminosity=B('e75',{'environment':'darkening'},'q4','attributed_claim'))
# Environmental darkness does not mean active luminosity of the woods.
a.words[110].pop('object_luminosity')

a.proposition('p45','Nora instructs Theo not to move closer to the recovery branch.',[580,581,582],scope_id='s9')

feedback={
 'summary':'Camp search annotated with separate actual, remembered, desired and unchosen events; Moss type uncertainty and the lantern custody gap are preserved.',
 'ambiguities':[
  {'words':[43,48,52,57,61,524,742],'issue':'Moss may be a toy rabbit or a living rabbit; source never states which. Physical features and snagging are retained without an animate/artifact commitment.'},
  {'words':[343,344,458],'issue':'Earlier return we includes Theo; companion identity is not established. It is distinct from present Nora/Theo search group.'},
  {'words':[257,518,608],'issue':'First overhead branch and later low recovery branch are separate referents unless future evidence establishes identity.'},
  {'words':[511,512,647,648],'issue':'Visible blue patch likely belongs to collar but exact surface identity is unconfirmed; patch stays separate.'},
  {'words':[587,613,708],'issue':'Lantern passes from father to Nora, then to Theo; Nora later carries it back, but that intervening handoff is unreported and no event is invented.'},
  {'words':[524,657,745],'issue':'How Moss was lost and caught, where attached leaves came from, and final ear shape after smoothing are not specified.'},
 ],
 'feature_gaps':[],
 'prompt_feedback':[
  'A rabbit-like named referent with fur and an ear need not be forced into animal versus toy without an explicit source cue.',
  'When a remembered we has unknown membership, do not default to the current narrative pair.',
  'Prohibition is desired negative content, not an asserted past non-event; preserve operator and scope alongside the positive action label.',
  'Joint credit can reuse a shared discovery while explicitly representing individual contributions and the separate recovery steps.',
 ],
 'coverage_notes':'All 40 paragraphs receive explicit per-word contextual POS/lemma and supported sparse features. Full story retrospective; no causal-prefix filter. No new attribute aliases proposed.',
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

