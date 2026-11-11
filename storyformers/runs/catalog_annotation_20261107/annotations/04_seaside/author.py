"""Manually interpreted whole-story seaside annotation, frozen prompt v1."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a=Annotation('04_seaside',prompt_version='v1')
for key in ['appearance_color','part_whole_relation','figurative_mapping']: a.use_extension(key)
a.extension('affordance_supporting','object','Bound support surface and object that the text explicitly presents it as capable of supporting, without asserting actual placement.','focused carrier and proposed supported object','spatial_support describes actual support; affordance_sitting concerns a body sitting, and affordance_containing concerns containment. A wall being a suitable resting place for a basket is neither actual placement nor containment.',{'entity_id':'e44','scope_id':'s0','assertion_status':'asserted','value':{'object_id':'e14','can_support':True}})

# Each occurrence has an explicit contextual POS=lemma decision.
LEX={
0:'det=the n=wind v=have v=be v=steal n=Tessa n=sketchbook det=all n=morning pron=it v=flip det=the n=page conj=while pron=she v=try part=to v=draw det=the n=sea conj=and v=blow det=her n=pencil adp=off det=the n=garden n=wall det=her n=brother n=Milo v=want part=to v=find det=a n=tide n=pool adv=where pron=he v=can v=watch n=Captain det=a adj=green n=anemone pron=they v=see adj=last n=summer v=open conj=and v=close adp=like det=a adj=tiny n=flower',
1:'n=Fern n=Pocket v=be adj=sheltered n=Mr n=Vale v=tell pron=they v=hand adv=over det=his adj=folded n=map v=follow det=the n=seaside n=path adp=to det=the n=Twin n=Chimneys adv=then v=turn adv=inland adp=at det=the n=stile det=the adj=real n=chimney v=be num=two adj=dark n=rock adv=out adp=in det=the n=water v=do v=mix pron=they adv=up adp=with det=the adj=old n=bathhouse',
2:'pron=we v=will n=Tessa v=say',
3:'n=Milo v=tuck det=the n=picnic n=basket adp=under num=one n=arm n=Tessa v=slide det=the n=map adp=into det=her n=jacket n=Mr n=Vale v=watch pron=they v=set adv=off adp=along det=the n=seaside n=path adv=then v=call det=the n=tide v=turn adp=at num=two',
4:'pron=we v=be adv=back adp=before adv=then n=Milo v=call',
5:'det=the n=path v=wind adp=above det=a adj=stony n=beach adp=with det=the n=sea v=flash adp=between n=clump adp=of n=grass n=Tessa v=keep num=one n=hand adp=on det=the n=map conj=and det=the pron=other adp=on det=her n=sketchbook n=Milo v=walk adv=ahead v=look adp=for n=pool v=leave adp=by det=the adj=last n=tide',
6:'adp=at det=a n=fork n=Tessa v=stop adp=below pron=they v=stand det=the adj=old n=bathhouse det=its adj=pale n=roof adv=almost adj=hidden adp=behind det=a n=dune num=two n=chimney v=stick adv=up n=side adp=by n=side',
7:'adv=there pron=she v=say n=Twin n=Chimneys',
8:'n=Milo v=peer adp=at det=the n=map n=Mr n=Vale v=say det=the n=rock v=be adv=out adp=in det=the n=water',
9:'adv=maybe det=the n=rock v=be adp=behind det=the n=bathhouse n=Tessa v=reply det=the adj=lower n=path v=lead adv=straight adp=toward pron=it conj=while det=the adj=upper pron=one v=curve adv=away adp=from det=the n=sea pron=this v=must v=be det=the n=shortcut',
10:'n=Milo v=hesitate adv=then v=follow pron=she adv=down',
11:'det=the n=bathhouse v=be adj=locked conj=and adj=boarded adv=up adp=beyond pron=it det=the n=path v=end adp=on det=a adj=narrow n=shelf adp=of n=pebble n=Tessa v=take adv=out det=the n=map det=the n=drawing v=show num=two adj=dark n=stack adp=with adj=little n=wave adp=around pron=they adp=on det=the adj=far n=side adp=of det=the n=point pron=she v=can adv=just v=make adv=out det=the adj=actual n=Twin n=Chimneys v=rise adp=from det=the n=water',
12:'intj=oh pron=she v=say',
13:'pron=we v=follow det=the n=bathhouse n=Milo v=say pron=he v=do v=sound adj=cross conj=but pron=he v=be v=look adp=at det=the n=tide n=pool adp=below det=the n=pebble v=do pron=you v=think n=Captain v=may v=be adp=in adv=there',
14:'n=Tessa v=check det=the n=map adv=again det=the adj=dotted n=line adp=to n=Fern n=Pocket v=run adp=along det=the adj=upper n=path part=not adv=down adv=here pron=she v=have v=be adv=so adj=sure pron=she v=spot det=the n=landmark conj=that pron=she v=have v=look adv=closely',
15:'det=a n=wave v=slide adp=over det=the adj=flat n=rock adp=at det=the n=end adp=of det=the n=shelf pron=it v=withdraw adp=with det=a n=hiss v=leave det=the n=stone v=shine',
16:'pron=we v=can v=scramble adp=around det=the n=point n=Tessa v=say conj=though det=the n=map v=show det=no n=path adv=there n=Fern n=Pocket v=be adv=so adj=close pron=she v=picture det=her n=sketchbook v=rest adj=flat adp=in det=the n=quiet adp=with det=the n=sea adv=still adp=in n=view',
17:'n=Milo v=point adp=to det=the n=water v=creep adp=across det=the n=rock det=that n=way v=get adj=small',
18:'det=the adj=old n=stone n=step adv=back adp=to det=the n=fork v=be adj=steep conj=but adj=dry pron=they v=can v=climb pron=they conj=and v=take det=the adj=upper n=path pron=it v=will v=mean v=go adp=past det=the n=place pron=they adv=just v=leave conj=and n=Tessa v=will v=have part=to v=admit pron=she v=lead pron=they det=the adj=wrong n=way pron=she v=look adp=at det=the n=basket adv=then adp=at det=the v=move n=water',
19:'adp=up det=the n=step pron=she v=say pron=we part=not v=go adp=around det=the n=point',
20:'n=Milo v=nod pron=he v=lift det=the n=basket conj=and adv=together pron=they v=climb adp=at det=the n=top n=Tessa v=stop part=to v=catch det=her n=breath',
21:'pron=I v=shall v=check det=the n=map pron=she v=say',
22:'pron=you v=do v=check pron=it n=Milo v=reply pron=you adv=just v=check pron=it adp=after v=choose',
23:'pron=she v=give pron=he det=a n=look pron=he v=grin conj=and pron=she v=can v=help v=laugh',
24:'adp=from det=the adj=upper n=path det=the adj=real n=Twin n=Chimneys v=stand adj=plain adp=against det=the n=water n=Tessa v=follow det=their adj=dark n=shape adp=on det=the n=map adv=then v=spot det=the adj=wooden n=stile adv=just adp=beyond det=the n=bend det=this n=time pron=she v=let n=Milo v=read det=the n=direction',
25:'adp=over det=the n=stile pron=he v=say adv=then det=the n=path v=go adp=between det=the n=rock',
26:'pron=he v=be adj=right adp=beyond det=the n=stile det=the n=path v=slip adv=inland adv=where det=the n=wind v=soften adp=among det=the n=grass n=fern v=crowd det=a adj=small n=hollow adp=under det=the n=headland det=a adj=low n=stone n=wall v=make det=a adj=perfect n=place part=to v=set adv=down det=the n=basket conj=and det=the n=sea v=be adv=still adj=visible adp=through det=a n=gap adp=in det=the n=rock',
27:'n=Tessa v=open det=her n=sketchbook det=the n=page v=stay adj=still',
28:'n=Milo v=hurry adp=to det=the adj=near n=tide n=pool conj=and v=crouch n=Captain det=a adj=green n=anemone v=open adv=slowly adp=in det=the adj=clear n=water n=Milo v=keep det=his n=hand adp=on det=his n=knee conj=and v=watch pron=it v=bloom',
29:'n=Tessa v=settle adp=beside pron=he pron=I v=can v=see det=both n=chimney adp=from adv=here pron=she v=say v=hold adj=still det=a n=second',
30:'conj=while pron=she v=draw n=Milo v=unfold det=the n=map adp=across det=the n=picnic n=cloth conj=and v=use num=two n=apple part=to v=keep det=its n=corner adv=down pron=he v=trace det=their n=route adp=with num=one n=finger adp=from det=the adj=wrong n=turn adp=to det=the adj=high n=path adv=then v=point adp=to det=the adj=sheltered n=hollow adv=where pron=they v=sit',
31:'conj=when det=the n=wind v=lift det=the n=map n=edge n=Milo v=press pron=it adj=flat adp=with det=his n=palm n=Tessa n=pencil v=move adp=across det=the n=page v=draw num=two adj=dark n=rock adp=in det=the n=sea conj=and adp=below pron=they det=a adj=small adj=green n=flower v=open adp=in det=its n=pool',
}
for p,seq in LEX.items():
    parts=[x.split('=',1) for x in seq.split()]
    words=a.paragraphs[p]['words']
    assert len(words)==len(parts),(p,len(words),len(parts))
    a.tag(p,[x[0] for x in parts],{word['w']:pair[1] for word,pair in zip(words,parts)})

# Physical identities, depicted identities and mistaken labels stay separate.
ENTS=[
('e1','Tessa','person',[5,14,22,28,104,114,119,160,171,187,211,237,264,284,307,321,345,352,371,376,381,427,429,487,492,498,511,532,536,538,543,545,551,557,565,582,601,669,671,707,711,718,725,782]),
('e2','Milo','person',[29,30,38,106,143,173,215,260,327,329,334,442,519,521,549,559,562,603,610,619,677,696,698,701,710,727,744,775,780]),
('e3','Mr. Vale','person',[60,61,66,121,122,220,221]),
('e4','coastal wind','wind',[1,9,631,770]),
('e5','Tessa sketchbook','sketchbook',[6,172,430,672]),
('e6','Captain anemone','sea_anemone',[41,44,347,686,689,705]),
('e7','sea and coastal water','sea',[19,93,154,229,254,319,438,446,507,581,659]),
('e8','real Twin Chimneys rocks','rock_pair',[75,76,85,89,96,224,232,314,315,575,576,584,715]),
('e9','Fern Pocket sheltered hollow','hollow',[56,57,361,362,422,423,640,717,764]),
('e10','Mr. Vale folded map','map',[68,117,166,219,288,355,417,542,548,554,589,730,741,773]),
('e11','seaside approach path','path',[72,130,146]),
('e12','wooden stile','stile',[82,594,609,624]),
('e13','old bathhouse','building',[101,194,195,236,245,267,274,326]),
('e14','picnic basket','basket',[110,502,524,656]),
('e15','Tessa jacket','jacket',[120]),
('e16','seaside path fork','path_junction',[186,462,482,531]),
('e17','bathhouse chimney pair','chimney_pair',[204,213,214]),
('e18','bathhouse roof','roof',[197]),
('e19','sand dune','dune',[202]),
('e20','lower bathhouse path','path',[241,255,259,276,497]),
('e21','upper path','path',[249,367,475,572,758]),
('e22','Tessa and Milo','group',[45,63,102,124,138,190,323,407,467,483,494,513,527,746,766]),
('e23','sketchbook pages','page_group',[12,674]),
('e24','Tessa pencils','pencil_group',[23]),
('e25','garden wall','wall',[27]),
('e26','stony beach','beach',[151]),
('e27','flat tidal rocks at shelf end','rock_group',[391,405,450]),
('e28','pebble shelf','shore_shelf',[281,397]),
('e29','pebbles on shelf','pebble_group',[283,343]),
('e30','coastal point','headland_point',[306,412,518]),
('e31','pool below pebble shelf','tide_pool',[340,351]),
('e32','map drawing','map_image',[290]),
('e33','depicted Twin Chimneys on map','depicted_rock_pair',[294,299,586]),
('e34','wave symbols on map','depicted_wave_group',[297]),
('e35','dotted route on map','map_route_mark',[359]),
('e36','receding wave','wave',[386,398]),
('e37','exposed shore passage around point','shore_passage',[452]),
('e38','stone steps to fork','steps',[458,470,510]),
('e39','bend before stile','path_bend',[598]),
('e40','map directions','instruction_text',[606]),
('e41','inland path beyond stile','path',[614,626]),
('e42','rocks around hollow view-gap','rock_group',[668]),
('e43','headland over hollow','headland',[643]),
('e44','low stone wall at hollow','wall',[647]),
('e45','gap in hollow rocks','gap',[665]),
('e46','Captain tide pool at Fern Pocket','tide_pool',[683]),
('e47','Milo hands','body_part_group',[699]),
('e48','Milo knees','body_part_group',[702]),
('e49','picnic cloth','cloth',[734]),
('e50','two apples','apple_pair',[738]),
('e51','clear water in Captain pool','water',[695]),
('e52','map corners','paper_parts',[742]),
('e53','map edge','paper_part',[774,777]),
('e54','drawn Twin Chimneys','depicted_rock_pair',[791,797]),
('e55','drawn Captain as flower','depicted_anemone',[801,804]),
('e56','drawn sea','depicted_sea',[794]),
('e57','drawn anemone pool','depicted_tide_pool',[805]),
('e58','Milo finger tracing map','body_part',[750]),
('e59','Milo palm pressing map','body_part',[781]),
('e60','Tessa drawing pencil','pencil',[783]),
('e61','current drawing page','page',[787]),
('e62','Milo carrying arm','body_part',[113]),
('e63','Tessa map-holding hand','body_part',[163]),
('e64','Tessa sketchbook-holding hand','body_part',[169]),
('e65','coastal grass clumps','vegetation',[157,159]),
('e66','sheltering inland grasses','vegetation',[635]),
('e67','ferns in hollow','vegetation',[636]),
('e68','traced traveled route on map','depicted_route',[747]),
('e69','a sought tide pool','desired_pool',[36]),
('e70','rocks flanking inland path','rock_group',[618]),
]
for eid,name,typ,words in ENTS:a.entity(eid,name,typ,words)
a.entities['e1']['mentions'].append(413)
F_TESSA={'entity_id':'e1','entity_name':a.entities['e1']['name'],'entity':a.entities['e1']['type']}
a.feature(413,**F_TESSA)
a.entities['e22']['member_ids']=['e1','e2']
a.entities['e24']['known_member_ids']=['e60']
a.entities['e23']['known_member_ids']=['e61']
a.entities['e6']['identity_note']='Milo recognizes the later anemone as Captain; individual biological identity is attributed rather than independently proven.'
a.entities['e69'].update(scope_id='g2',specificity='nonspecific',actual_world_existence='not_asserted_by_desire')
a.entities['e42']['identity_note']='May overlap rocks flanking inland route e70, but the text does not establish exact rock identity.'

QUOTES=[
('q1',56,60,'e3','Shelter description.'),('q2',69,102,'e3','Route instructions and landmark warning.'),('q3',102,104,'e1','Elliptical promise not to confuse landmarks.'),('q4',133,138,'e3','Tide time warning.'),('q5',138,143,'e2','Promise to be back before the tide turns.'),('q6',210,211,'e1','Deictic mistaken identification.'),('q7',213,215,'e1','Bathhouse chimneys called Twin Chimneys.'),('q8',220,230,'e2','Recall of Vale’s rock-location instruction.'),('q9',230,237,'e1','Tentative rocks-behind-bathhouse explanation.'),('q10',255,260,'e1','Confident lower-path shortcut inference.'),('q11',320,321,'e1','Recognition response.'),('q12',323,327,'e2','Report of the wrong route just taken.'),('q13',344,352,'e2','Question about possible anemone location.'),('q14',407,413,'e1','Proposed unmapped scramble.'),('q15',451,455,'e2','Warning of narrowing shore route.'),('q16',508,511,'e1','Choose steps.'),('q17',513,519,'e1','Reject shore route plan.'),('q18',538,543,'e1','Retrospective criticism of checking too late.'),('q19',545,549,'e2','Correction: Tessa did check.'),('q20',551,557,'e2','Clarify wrong ordering of choosing and checking.'),('q21',607,610,'e2','Read crossing instruction.'),('q22',612,619,'e2','Read inland path description.'),('q23',686,687,'e2','Recognition call Captain.'),('q24',711,718,'e1','Both real chimneys visible from hollow.'),('q25',720,724,'e1','Ask Milo to hold still.'),
]
for sid,lo,hi,speaker,desc in QUOTES:
    a.scope(sid,range(lo,hi),kind='quotation',holder_id=speaker,description=desc)
    a.feature(range(lo,hi),quote_mode='direct')
for sid,lo,hi,kind,holder,parent,desc in [
('g1',16,20,'attempted_complement','e1','s0','Drawing attempted, success not established here.'),
('g2',32,56,'desired_scene','e2','s0','Find a pool to watch Captain; later recognition can resolve prospective referents.'),
('memory1',45,49,'remembered_background','e22','g2','Prior summer sighting is asserted background inside desired scene.'),
('report1',223,230,'reported_content','e3','q8','Vale’s original description recalled by Milo.'),
('belief1',376,380,'mistaken_belief_content','e1','s0','Tessa thought she had identified the true landmark.'),
('imagine1',429,442,'imagined_scene','e1','s0','Calm sketchbook and visible sea are imagined here, not yet actual.'),
('option1',467,498,'considered_route','e1','s0','Possible return via steps and admission, not yet chosen.'),
('past1',483,486,'actual_background','e22','option1','The place just left is an actual earlier endpoint.'),
('past2',492,498,'actual_background','e1','option1','Wrong leading is actual prior behavior embedded under prospective admission.'),
('purpose1',534,538,'purpose','e1','s0','Stopping to catch breath does not assert an additional completed recovery.'),
('drawing1',789,806,'depiction','e1','s0','Content drawn on page, distinct from actual rocks, sea and anemone.'),
]:a.scope(sid,range(lo,hi),kind=kind,holder_id=holder,parent=parent,description=desc)
a.feature(range(789,806),semantic_world_id='w_sketch',evidence_world_status='depiction')

def F(w,**kw):a.feature(w,**kw)
def B(e,value,scope='s0',status='asserted',**kw):return dict(entity_id=e,value=value,scope_id=scope,assertion_status=status,**kw)
def P(n,text,words,scope='s0'):a.proposition(f'p{n}',text,words,scope_id=scope)
PROPS=[
(1,'Tessa draws the sea.',[14,17,19],'g1'),(2,'Milo finds a tide pool and watches Captain open and close.',[30,33,36,40,41,49,51],'g2'),
(3,'Fern Pocket is sheltered.',[56,57,59],'q1'),(4,'Follow the seaside path to the real rock pair and turn inland at the stile.',[69,72,75,76,78,79,82],'q2'),
(5,'The real Twin Chimneys are two dark rocks out in the water.',[85,87,89,91,93],'q2'),(6,'The siblings confuse bathhouse chimneys with the real landmark.',[94,95,96,101,213,214],'q2'),
(7,'The tide turns at two.',[134,135,137],'q4'),(8,'The siblings return before the tide turns.',[138,139,140,141,142],'q5'),
(9,'The bathhouse chimney pair is the Twin Chimneys landmark.',[204,210,213,214],'q7'),(10,'The real rocks may be behind the bathhouse.',[230,232,233,234,236],'q9'),
(11,'The lower path is a shortcut.',[241,255,256,259],'q10'),(12,'The bathhouse is locked and boarded.',[267,269,271],'s0'),
(13,'The actual Twin Chimneys stand in the water beyond the point.',[306,310,314,315,316,319],'s0'),(14,'The siblings followed the bathhouse route.',[263,264,265,323,324,326],'q12'),
(15,'Captain is in the pool below the pebble shelf.',[340,346,347,348,349,351],'q13'),(16,'The dotted map route uses the upper path rather than the lower shelf route.',[359,361,362,363,367,368,370],'s0'),
(17,'Tessa identified the correct landmark before choosing.',[375,376,377,379],'belief1'),(18,'Tessa did not inspect the map closely before choosing.',[375,380,381,382,383,384],'s0'),
(19,'The siblings scramble around the point.',[407,408,409,412],'q14'),(20,'No path around the point is drawn on the map.',[417,418,419,420,421],'s0'),
(21,'Tessa’s sketchbook rests flat in quiet with the sea visible.',[429,430,431,432,435,438,441],'imagine1'),(22,'The usable shore way is narrowing as water advances.',[446,447,450,452,453,454],'q15'),
(23,'The siblings climb the dry steps and use the upper path.',[458,464,466,467,469,470,472,475],'option1'),(24,'Tessa admits leading the siblings the wrong way.',[487,491,492,493,494,497],'option1'),
(25,'The siblings choose the steps and reject going around the point.',[508,510,513,514,515,518],'q17'),(26,'Tessa checks the map before choosing a route.',[538,539,540,542,553,555,556],'q18'),
(27,'Tessa checked the map after choosing.',[545,547,548,551,553,554,555,556],'q20'),(28,'The route crosses the stile then goes between rocks inland.',[607,609,615,618,624,627,628],'q22'),
(29,'The hollow permits quiet drawing with sea visible.',[632,640,647,653,659,662,672,674,675,676],'s0'),(30,'Milo recognizes a green anemone as Captain.',[677,683,686,689,690],'s0'),
(31,'Both real chimneys can be seen from the hollow.',[711,713,714,715,717],'q24'),(32,'Milo holds still briefly.',[720,721,722,723],'q25'),
(33,'Milo steadies the map with apples and his palm.',[736,738,740,742,771,774,776,781],'s0'),(34,'Tessa draws the actual landmarks and anemone after the corrected route.',[726,788,791,794,801,805],'s0'),
]
for args in PROPS:P(*args)

# Compact event specification: explicit arguments and participants, not a tagger.
# Numeric labels are stable local annotation IDs. Auxiliary operators are omitted.
EVENTS=[
(1,4,'wind disrupts sketchbook','other','e4',['e5'],'asserted'),(2,10,'wind flips pages','move','e4',['e23'],'asserted'),(3,15,'Tessa tries drawing','other','e1',[],'asserted'),(4,17,'Tessa draws sea','other','e1',['e7'],'desired'),(5,21,'wind blows pencils off wall','move','e4',['e24'],'asserted'),
(6,31,'Milo wants to watch Captain','feel','e2',[],'asserted'),(7,33,'Milo finds a tide pool','perceive','e2',['e69'],'desired'),(8,40,'Milo watches Captain','perceive','e2',['e6'],'desired'),(9,46,'siblings saw Captain last summer','perceive','e22',['e6'],'asserted'),(10,49,'Captain opens','other',None,['e6'],'desired'),(11,51,'Captain closes','other',None,['e6'],'desired'),
(12,59,'Fern Pocket is sheltered','state',None,['e9'],'reported'),(13,62,'Vale describes route and warns','speak','e3',[],'asserted'),(14,64,'Vale hands over map','transfer','e3',['e10'],'asserted'),(15,69,'siblings follow seaside route','move','e22',[],'desired'),(16,78,'siblings turn inland at stile','move','e22',[],'desired'),(17,86,'real landmark is dark rock pair','state',None,['e8'],'reported'),(18,95,'confuse the two landmarks','other','e22',['e8','e17'],'negated'),(19,105,'Tessa promises not to confuse landmarks','speak','e1',[],'asserted'),
(20,107,'Milo tucks basket under arm','move','e2',['e14'],'asserted'),(21,115,'Tessa slides map into jacket','move','e1',['e10'],'asserted'),(22,123,'Vale watches departure','perceive','e3',['e22'],'asserted'),(23,125,'siblings set off on seaside path','move','e22',[],'asserted'),(24,132,'Vale calls tide warning','speak','e3',[],'asserted'),(25,135,'tide turns at two','other',None,[],'reported'),(26,139,'siblings return before tide turns','move','e22',[],'desired'),(27,144,'Milo promises timely return','speak','e2',[],'asserted'),
(28,147,'path winds above beach','state',None,['e11'],'asserted'),(29,155,'sea flashes between grasses','other',None,['e7'],'asserted'),(30,161,'Tessa holds map and sketchbook','state','e1',['e10','e5'],'asserted'),(31,174,'Milo walks ahead','move','e2',[],'asserted'),(32,176,'Milo looks for tidal pools','perceive','e2',[],'asserted'),(33,179,'last tide left pools','other',None,[],'asserted'),
(34,188,'Tessa stops at fork','move','e1',[],'asserted'),(35,191,'bathhouse stands below fork','state',None,['e13'],'asserted'),(36,199,'dune almost hides roof','state',None,['e18'],'asserted'),(37,205,'bathhouse chimneys protrude side by side','state',None,['e17'],'asserted'),(38,212,'Tessa names mistaken landmark','speak','e1',[],'asserted'),(39,216,'Milo inspects map','perceive','e2',['e10'],'asserted'),
(40,233,'real rocks might be behind bathhouse','state',None,['e8'],'hypothetical'),(41,238,'Tessa proposes landmark explanation','speak','e1',[],'asserted'),(42,242,'lower path leads toward bathhouse','state',None,['e20'],'asserted'),(43,250,'upper path curves away from sea','state',None,['e21'],'asserted'),(44,257,'lower path is inferred shortcut','state',None,['e20'],'reported'),(45,261,'Milo hesitates','other','e2',[],'asserted'),(46,263,'Milo follows Tessa down lower route','move','e2',[],'asserted'),
(47,269,'bathhouse is locked','state',None,['e13'],'asserted'),(48,271,'bathhouse is boarded up','state',None,['e13'],'asserted'),(49,277,'lower path ends at pebble shelf','state',None,['e20'],'asserted'),(50,285,'Tessa takes map out','move','e1',['e10'],'asserted'),(51,291,'map depicts stacks and waves','state',None,['e32','e33','e34'],'asserted'),(52,310,'Tessa sees real Twin Chimneys','perceive','e1',['e8'],'asserted'),(53,316,'real rocks project above water','state',None,['e8'],'asserted'),(54,322,'Tessa reacts to mistaken identification','speak','e1',[],'asserted'),(55,328,'Milo names wrong route taken','speak','e2',[],'asserted'),(56,331,'Milo does not sound cross','state',None,['e2'],'negated'),(57,336,'Milo looks at shelf pool','perceive','e2',['e31'],'asserted'),(58,346,'question Tessa about possible Captain location','other','e1',[],'hypothetical'),(59,349,'Captain might be in shelf pool','state',None,['e6'],'hypothetical'),
(60,353,'Tessa checks map again','perceive','e1',['e10'],'asserted'),(61,363,'map route follows upper path','state',None,['e35'],'asserted'),(62,375,'Tessa was certain of identification','state','e1',[],'asserted'),(63,377,'Tessa believes correct landmark spotted','perceive','e1',['e8'],'reported'),(64,383,'Tessa had not inspected map closely','perceive','e1',['e10'],'negated'),
(65,387,'wave slides across flat rocks','move',None,['e36'],'asserted'),(66,399,'wave withdraws','move',None,['e36'],'asserted'),(67,403,'receding wave leaves shining stones','other',None,['e27'],'asserted'),(68,406,'stones shine after wave','state',None,['e27'],'asserted'),(69,409,'siblings scramble around point','move','e22',[],'hypothetical'),(70,414,'Tessa proposes shore scramble','speak','e1',[],'asserted'),(71,418,'map shows no route around point','state',None,['e10'],'negated'),(72,426,'Fern Pocket is nearby','state',None,['e9'],'asserted'),(73,428,'Tessa imagines quiet sketching','other','e1',[],'asserted'),(74,431,'sketchbook rests flat in imagined quiet','state',None,['e5'],'hypothetical'),
(75,443,'Milo points out advancing water','other','e2',['e7'],'asserted'),(76,447,'water creeps across shelf rocks','move',None,['e7'],'asserted'),(77,453,'shore way narrows','state',None,['e37'],'reported'),(78,464,'steps are steep','state',None,['e38'],'asserted'),(79,466,'steps are dry','state',None,['e38'],'asserted'),(80,469,'siblings could climb steps','move','e22',[],'hypothetical'),(81,472,'siblings could take upper path','move','e22',[],'hypothetical'),(82,478,'upper route entails retracing and admitting error','state',None,[],'hypothetical'),(83,479,'siblings go past earlier place','move','e22',[],'hypothetical'),(84,485,'siblings previously left fork','move','e22',[],'asserted'),(85,491,'Tessa would admit wrong leading','speak','e1',[],'hypothetical'),(86,493,'Tessa led siblings wrong way','move','e1',[],'asserted'),(87,499,'Tessa looks at basket and moving water','perceive','e1',['e14','e7'],'asserted'),(88,506,'coastal water continues moving','move',None,['e7'],'asserted'),
(89,512,'Tessa chooses steps and rejects point route','speak','e1',[],'asserted'),(90,515,'siblings reject going around point','move','e22',[],'negated'),(91,520,'Milo nods agreement','other','e2',[],'asserted'),(92,522,'Milo lifts basket','move','e2',['e14'],'asserted'),(93,528,'siblings climb to top','move','e22',[],'asserted'),(94,533,'Tessa stops at top','move','e1',[],'asserted'),(95,535,'Tessa catches breath','other','e1',[],'desired'),(96,540,'Tessa should have checked before choosing','perceive','e1',['e10'],'hypothetical'),(97,544,'Tessa acknowledges late checking','speak','e1',[],'asserted'),(98,550,'Milo corrects checking chronology','speak','e2',[],'asserted'),(99,556,'Tessa chose lower route','other','e1',['e20'],'asserted'),
(100,558,'Tessa gives Milo a look','other','e1',['e2'],'asserted'),(101,563,'Milo grins','other','e2',[],'asserted'),(102,568,'Tessa laughs','other','e1',[],'asserted'),(103,577,'real rocks are plainly visible','state',None,['e8'],'asserted'),(104,583,'Tessa traces real rock shapes on map','perceive','e1',['e33'],'asserted'),(105,591,'Tessa spots wooden stile','perceive','e1',['e12'],'asserted'),(106,602,'Tessa lets Milo read directions','other','e1',[],'asserted'),(107,604,'Milo reads map directions','speak','e2',['e40'],'asserted'),(108,615,'path goes between rocks','state',None,['e41'],'reported'),(109,621,'Milo directions are correct','state',None,['e2'],'asserted'),(110,627,'path extends inland','state',None,['e41'],'asserted'),(111,632,'wind weakens among inland grasses','other',None,['e4'],'asserted'),(112,637,'ferns crowd sheltered hollow','state',None,['e67'],'asserted'),(113,648,'stone wall provides basket resting place','state',None,['e44'],'asserted'),(114,653,'set down basket on wall','move',None,['e14'],'hypothetical'),(115,662,'sea remains visible through rock gap','state',None,['e7'],'asserted'),
(116,670,'Tessa opens sketchbook','other','e1',['e5'],'asserted'),(117,675,'pages stay still','state',None,['e23'],'asserted'),(118,678,'Milo hurries to nearest pool','move','e2',[],'asserted'),(119,685,'Milo crouches at pool','state','e2',[],'asserted'),(120,686,'Milo calls anemone Captain','speak','e2',['e6'],'asserted'),(121,690,'anemone opens in clear water','other',None,['e6'],'asserted'),(122,697,'Milo keeps hands on knees','state','e2',['e47'],'asserted'),(123,704,'Milo watches anemone open','perceive','e2',['e6'],'asserted'),(124,708,'Tessa settles beside Milo','move','e1',[],'asserted'),(125,713,'Tessa sees both real chimneys','perceive','e1',['e8'],'reported'),(126,719,'Tessa describes view and asks stillness','speak','e1',[],'asserted'),(127,720,'Milo holds still for drawing','state','e2',[],'desired'),
(128,726,'Tessa draws view','other','e1',[],'asserted'),(129,728,'Milo unfolds map on picnic cloth','other','e2',['e10'],'asserted'),(130,736,'Milo uses apples as map weights','other','e2',['e50'],'asserted'),(131,740,'apples hold map corners down','state','e2',['e52'],'asserted'),(132,745,'Milo traces route on map','other','e2',['e35'],'asserted'),(133,760,'Milo points at hollow on map','other','e2',['e9'],'asserted'),(134,767,'siblings sit in hollow','state','e22',[],'asserted'),(135,771,'wind lifts map edge','move','e4',['e53'],'asserted'),(136,776,'Milo presses map edge flat','other','e2',['e53'],'asserted'),(137,784,'Tessa pencil moves across page','move',None,['e60'],'asserted'),(138,788,'Tessa draws rocks and anemone','other','e1',['e54','e55','e56','e57'],'asserted'),(139,802,'drawn anemone opens in pictured pool','other',None,['e55'],'asserted'),
]
for n,w,label,typ,actor,patients,fact in EVENTS:
    if n==138: continue  # continuation/elaboration of the drawing at ev128
    if n==18: patients=['e8','e13']
    if n==30: label,patients='Tessa keeps hands on map and sketchbook',['e63','e64']
    if n==56: label='Milo sounds cross'
    if n==58: label='Tessa thinks Captain may be in shelf pool'
    if n==64: label='Tessa inspected map closely before choosing'
    if n==71: label='map depicts a path around point'
    if n==90: label='siblings go around the point'
    if n==100: patients=[]
    if n==128: label,patients='Tessa draws seaside scene and anemone',['e54','e55','e56','e57']
    a.event(f'ev{n}',w,label,type=typ,actor=actor,patients=patients,factuality=fact)
a.mention_event('ev128',788,role='action',note='Continuation and elaboration of the ongoing drawing at 726, not a new drawing session.')
# Recalled statements/actions reuse their underlying IDs. Actual speech remains
# distinct from its content and the earlier speech quoted inside that content.
a.mention_event('ev13',222,role='action',note='Milo recalls Vale’s earlier directions; this is not a new Vale utterance.')
a.mention_event('ev17',225,role='action',note='Same rocks-in-water claim, nested under Milo’s report of Vale.')
a.event('ev143',324,'siblings took the wrong bathhouse route',type='move',actor='e22',factuality='reported',support=[263,264,265,323,324,326,493])
a.mention_event('ev143',323,role='actor')
a.mention_event('ev143',326,role='location')
a.mention_event('ev60',[547,553],role='action',note='Milo recalls the map check after choosing. No new checking occurs during this conversation.')
a.mention_event('ev107',611,role='action',note='Reporting verb identifies the same current reading of directions.')
a.mention_event('ev121',706,role='action',note='Bloom metaphor refers to the opening just witnessed, not plant flowering or a new opening.')

# Participant memberships are sparse, explicit and may be multiple per word.
ROLES={
1:{'actor':[1],'patient':[6]},2:{'actor':[9],'patient':[12]},3:{'actor':[14]},4:{'actor':[14],'patient':[19]},5:{'actor':[9],'patient':[23],'location':[27]},6:{'actor':[30]},7:{'actor':[30],'patient':[36]},8:{'actor':[38],'patient':[41]},9:{'actor':[45],'patient':[44]},10:{'patient':[44]},11:{'patient':[44]},12:{'patient':[56,57]},13:{'actor':[60,61],'recipient':[63]},14:{'actor':[60,61],'patient':[68],'recipient':[63]},15:{'location':[72,75,76]},16:{'location':[82]},17:{'patient':[85,89],'location':[93]},18:{'patient':[96,101]},19:{'actor':[104]},20:{'actor':[106],'patient':[110],'location':[113]},21:{'actor':[114],'patient':[117],'location':[120]},22:{'actor':[121,122],'patient':[124]},23:{'actor':[124],'location':[130]},24:{'actor':[121,122]},25:{'other':[134,137]},26:{'actor':[138],'modifier':[142]},27:{'actor':[143]},28:{'patient':[146],'location':[151]},29:{'patient':[154],'location':[157]},30:{'actor':[160],'patient':[166,172],'instrument':[163,169]},31:{'actor':[173]},32:{'actor':[173],'patient':[178]},34:{'actor':[187],'location':[186]},35:{'patient':[194],'location':[190]},36:{'patient':[197],'location':[202]},37:{'patient':[204]},38:{'actor':[211],'patient':[213,214]},39:{'actor':[215],'patient':[219]},40:{'patient':[232],'location':[236]},41:{'actor':[237]},42:{'patient':[241],'location':[245]},43:{'patient':[249],'location':[254]},44:{'patient':[255]},45:{'actor':[260]},46:{'actor':[260],'other':[264]},47:{'patient':[267]},48:{'patient':[267]},49:{'patient':[276],'location':[281]},50:{'actor':[284],'patient':[288]},51:{'patient':[290,294,297]},52:{'actor':[307],'patient':[314,315]},53:{'patient':[314,315],'location':[319]},54:{'actor':[321]},55:{'actor':[327]},56:{'patient':[329]},57:{'actor':[334],'patient':[340]},58:{'actor':[345]},59:{'patient':[347],'location':[351]},60:{'actor':[352],'patient':[355]},61:{'patient':[359],'location':[367]},62:{'actor':[371]},63:{'actor':[376],'patient':[379]},64:{'actor':[381]},65:{'patient':[386],'location':[391]},66:{'patient':[398]},67:{'patient':[405]},68:{'patient':[405]},69:{'actor':[407],'location':[412]},70:{'actor':[413]},71:{'patient':[417]},72:{'patient':[422,423]},73:{'actor':[427]},74:{'patient':[430],'modifier':[432]},75:{'actor':[442],'patient':[446]},76:{'patient':[446],'location':[450]},77:{'patient':[452]},78:{'patient':[458]},79:{'patient':[458]},80:{'actor':[467],'location':[470]},81:{'actor':[467],'location':[475]},83:{'actor':[467],'location':[482]},84:{'actor':[483],'location':[482]},85:{'actor':[487]},86:{'actor':[492],'other':[494],'location':[497]},87:{'actor':[498],'patient':[502,507]},88:{'patient':[507]},89:{'actor':[511]},90:{'actor':[513],'location':[518]},91:{'actor':[519]},92:{'actor':[521],'patient':[524]},93:{'actor':[527]},94:{'actor':[532],'location':[531]},95:{'actor':[532],'patient':[537]},96:{'actor':[538],'patient':[542]},97:{'actor':[543]},98:{'actor':[549]},99:{'actor':[551]},100:{'actor':[557],'recipient':[559]},101:{'actor':[562]},102:{'actor':[565]},103:{'patient':[575,576],'location':[581]},104:{'actor':[582],'patient':[586],'location':[589]},105:{'actor':[582],'patient':[594]},106:{'actor':[601],'patient':[603]},107:{'actor':[603,610],'patient':[606]},108:{'patient':[614],'location':[618]},109:{'patient':[619]},110:{'patient':[626]},111:{'patient':[631],'location':[635]},112:{'patient':[636],'location':[640]},113:{'patient':[647]},114:{'patient':[656],'location':[647]},115:{'patient':[659],'location':[665]},116:{'actor':[669],'patient':[672]},117:{'patient':[674]},118:{'actor':[677],'location':[683]},119:{'actor':[677]},120:{'other':[689]},121:{'patient':[689],'location':[695]},122:{'actor':[696],'patient':[699],'location':[702]},123:{'actor':[696],'patient':[705]},124:{'actor':[707],'location':[710]},125:{'actor':[711],'patient':[715],'location':[717]},126:{'actor':[718]},127:{'modifier':[721,723]},128:{'actor':[725]},129:{'actor':[727],'patient':[730],'location':[734]},130:{'actor':[727],'patient':[738]},131:{'patient':[742]},132:{'actor':[744],'patient':[747],'instrument':[750]},133:{'actor':[744],'patient':[764]},134:{'actor':[766],'location':[764]},135:{'actor':[770],'patient':[774]},136:{'actor':[775],'patient':[777],'instrument':[781]},137:{'patient':[783],'location':[787]},138:{'actor':[782],'patient':[791,801,794,805]},139:{'patient':[801],'location':[805]},
}
for n,roles in ROLES.items():
    if n==138: n=128
    if n==30: roles={'actor':[160],'patient':[163,169],'location':[166,172]}
    for role,words in roles.items():
        a.mention_event(f'ev{n}',words,role=role)
# Explicit speech acts without reporting verbs get secondary actual events;
# their content keeps its primary event and local quote scope.
for eid,w,label,actor,support in [('ev140',222,'Milo recalls Vale warning','e2',[215,220,222,224,229]),('ev141',346,'Milo asks where Captain may be','e2',[344,345,346,347,348,351]),('ev142',453,'Milo warns shore route is shrinking','e2',[442,443,451,452,453,454])]:
    a.event(eid,w,label,type='speak',actor=actor,scope='s0',primary=False,support=support)
for n,recipient in [(14,'e22'),(19,'e3'),(27,'e3'),(100,'e2')]:
    a.events[f'ev{n}']['recipient_id']=recipient;F(a.events[f'ev{n}']['trigger'],recipient_id=recipient)
for n,tools in [(30,['e63','e64']),(104,['e10']),(131,['e50']),(132,['e58']),(136,['e59']),(138,['e60'])]:
    if n==30: continue
    if n==138: n=128
    a.events[f'ev{n}']['instruments']=tools;F(a.events[f'ev{n}']['trigger'],instruments=tools)
a.events['ev132']['patients']=['e68'];F(745,patients=['e68'])
P(35,'The siblings do not confuse the bathhouse with the real rock landmark.',[102,103,94,95,101],'q3')
a.mention_event('ev18',103,role='action',note='Elliptical future commitment to the prohibited confusion content; not a completed avoidance event.')

# Morphology and function-word operators, expanding explicit lexical decisions.
for w,parts in {45:['they','had'],94:['do','not'],103:['will','not'],138:['we','will'],330:['did','not'],376:['she','had'],382:['had','not'],452:['way','is'],483:['they','had'],492:['she','had'],513:['we','are'],539:['should','have'],566:['could','not']}.items(): F(w,contraction_expansion=parts)
F([5,773,782],grammatical_case='genitive')
for w,row in enumerate(a.words):
    if row['pos']=='det' and row['lemma'] in {'the','a'}:F(w,determiner_kind='definite_article' if row['lemma']=='the' else 'indefinite_article',definiteness='definite' if row['lemma']=='the' else 'indefinite')
    if row['pos']=='det' and row['lemma'] in {'her','his','their','its'}:F(w,determiner_kind='possessive',definiteness='definite',grammatical_case='genitive')
    if row['pos']=='pron' and row['lemma'] in {'I','she','he','it','they','we','you'}: F(w,mention_form='personal_pronoun',grammatical_person=1 if row['lemma'] in {'I','we'} else 2 if row['lemma']=='you' else 3)
    if row['pos']=='n' and row['lemma'] in {'Tessa','Milo','Mr','Vale','Fern','Pocket','Twin','Chimneys','Captain'}:F(w,mention_form='proper_name')
F([63,96,124,190,264,345,470,494,545,548,551,554,559,705,710,777,797],grammatical_case='objective')
F([12,23,85,89,178,204,224,232,283,294,297,315,343,391,405,450,458,575,576,618,635,636,668,674,699,702,715,738,742,791],grammatical_number='plural')
F([19,93,154,159,229,254,319,438,446,507,581,635,659,695],noun_countability='mass')
F([249,169],phrase_has_elision=True,mention_form='nominal_substitute')
F(169,reference_excluded_ids=['e63'],kind_antecedent_id='kind_hand')
F(249,kind_antecedent_id='kind_path',reference_excluded_ids=['e20'])
F(36,reference_specificity='nonspecific',existential_witness={'variable':'wanted_pool','kind':'tide_pool','scope':'g2'})
F([203,87,292,737,789],cardinal_value=2)
F([112,162,749],cardinal_value=1)
F([714],determiner_kind='dual',grammatical_number='plural')
F(7,determiner_kind='universal',temporal_frequency_class='throughout_named_interval')
F(599,determiner_kind='demonstrative')
F([240,454],adjective_degree='comparative')
F(681,adjective_degree='superlative')
F(28,social_relation_kind='sibling',social_relation_participants={'brother':'e2','sibling':'e1'})
F(476,referent_kind='proposition',propositional_antecedent_id='p23')
F(379,referent_kind='individual',reference_specificity='specific_intended_landmark',identity_hypothesis={'intended_entity_id':'e8','mistaken_percept_id':'e17','holder_id':'e1','scope_id':'belief1'})

# Explicit finite morphology, nonfinite forms and auxiliary chains.
F([2,10,15,21,31,62,105,107,115,123,125,132,144,147,161,174,188,191,205,212,216,222,238,242,250,261,263,268,277,285,291,310,322,324,328,330,331,335,353,363,372,375,377,382,383,387,399,414,418,424,428,443,463,478,485,493,499,512,520,522,528,533,544,546,550,553,558,563,577,583,591,602,604,611,620,627,632,637,648,660,670,675,678,685,690,697,704,708,719,726,728,736,745,760,767,771,776,784],tense='past',verb_form='finite')
F([58,86,135,225,233,257,615],tense='present',verb_form='finite')
F([4,64,155,176,179,316,336,387,403,406,431,447,453,479,506,515,568,788,802],verb_form='gerund_participle')
F(387,verb_form='finite')
F([3,46,67,373,377,383,485,493,540],verb_form='past_participle')
F([17,33,40,49,51,69,78,95,139,346,349,409,469,472,489,491,535,547,567,653,713,720,740],verb_form='base')
for aux,pred in [(2,4),(45,46),(372,375),(376,377),(382,383),(483,485),(492,493),(539,540)]:F(pred,aspect='perfect',perfect_auxiliary_id=a.anchor(aux))
F(4,aspect='perfect_progressive',auxiliary_chain=['perfect','progressive'],progressive_auxiliary_id=a.anchor(3))
for aux,pred in [(335,336),(452,453),(513,515)]:F(pred,aspect='progressive',progressive_auxiliary_id=a.anchor(aux))
for marker,pred in [(16,17),(32,33),(490,491),(534,535),(652,653),(739,740)]:F(pred,infinitive_marker_id=a.anchor(marker),clause_finiteness='nonfinite')
F([69,78,95,720],mood='imperative',imperative_subject_status='understood_addressee')
F(103,verb_phrase_ellipsis=True,polarity='negative')
F(607,sentence_fragment_type='prepositional_directive')
F(508,sentence_fragment_type='prepositional_directive')
F(214,sentence_fragment_type='nominal_identification')
F(320,sentence_fragment_type='interjection')
F(344,do_support_status='question_support',subject_auxiliary_inversion=True)
F(546,do_support_status='emphatic_affirmation')
F([94,330],do_support_status='negative_support')
for w,particle,label in [(64,65,'hand_over'),(95,97,'mix_up'),(125,126,'set_off'),(285,286,'take_out'),(310,311,'make_out'),(653,654,'set_down')]:
    F(w,verb_particle_construction=label);F(particle,phrase_modifier_kind='verb_particle',phrase_complement_head_id=a.anchor(w))
for w,relation in [(13,'simultaneity'),(141,'before'),(246,'contrast_and_simultaneity'),(380,'result'),(415,'concession'),(555,'after'),(724,'simultaneity'),(768,'time')]:F(w,subordinator_type=relation)
for w,relation in [(47,'previous'),(131,'next'),(177,'purpose'),(182,'previous'),(262,'next'),(356,'again'),(439,'persistence'),(484,'recent'),(503,'next'),(590,'next'),(612,'next'),(661,'persistence'),(759,'next')]:F(w,temporal_signal_relation=relation)
# 'for pools' is not a temporal connective; retain the selected complement role.
a.words[177].pop('temporal_signal_relation',None);F(177,phrase_complement_head_id=a.anchor(178))

# Grammatical subjects are manual decisions; natural forces, paths and body
# parts are not replaced with nearby people merely because they are actors.
SUBJECTS={4:'e4',10:'e4',15:'e1',17:'e1',21:'e4',31:'e2',33:'e2',40:'e2',46:'e22',49:'e6',51:'e6',58:'e9',59:'e9',62:'e3',64:'e3',86:'e8',105:'e1',107:'e2',115:'e1',123:'e3',125:'e22',132:'e3',139:'e22',144:'e2',147:'e11',155:'e7',161:'e1',174:'e2',176:'e2',188:'e1',191:'e13',205:'e17',212:'e1',216:'e2',222:'e3',225:'e8',233:'e8',238:'e1',242:'e20',250:'e21',257:'e20',261:'e2',263:'e2',268:'e13',269:'e13',271:'e13',277:'e20',285:'e1',291:'e32',310:'e1',316:'e8',322:'e1',324:'e22',328:'e2',331:'e2',336:'e2',346:'e1',349:'e6',353:'e1',363:'e35',375:'e1',377:'e1',383:'e1',387:'e36',399:'e36',406:'e27',409:'e22',414:'e1',418:'e10',426:'e9',428:'e1',431:'e5',443:'e2',447:'e7',453:'e37',464:'e38',466:'e38',469:'e22',472:'e22',479:'e22',485:'e22',491:'e1',493:'e1',499:'e1',512:'e1',515:'e22',520:'e2',522:'e2',528:'e22',533:'e1',535:'e1',540:'e1',544:'e1',547:'e1',550:'e2',553:'e1',556:'e1',558:'e1',563:'e2',568:'e1',577:'e8',583:'e1',591:'e1',602:'e1',604:'e2',611:'e2',615:'e41',621:'e2',627:'e41',632:'e4',637:'e67',648:'e44',662:'e7',670:'e1',675:'e23',678:'e2',685:'e2',690:'e6',697:'e2',704:'e2',706:'e6',708:'e1',713:'e1',719:'e1',726:'e1',728:'e2',736:'e2',740:'e2',745:'e2',760:'e2',767:'e22',771:'e4',776:'e2',784:'e60',788:'e60',802:'e55'}
for w,eid in SUBJECTS.items():F(w,grammatical_subject_id=eid)
for w,eid in {4:'e5',10:'e23',17:'e7',21:'e24',33:'e69',40:'e6',46:'e6',64:'e10',107:'e14',115:'e10',123:'e22',161:'e10',216:'e10',263:'e1',285:'e10',310:'e8',324:'e13',353:'e10',377:'e8',403:'e27',428:'e5',469:'e38',472:'e21',485:'e16',493:'e22',522:'e14',540:'e10',547:'e10',553:'e10',558:'e2',583:'e33',591:'e12',602:'e2',604:'e40',670:'e5',697:'e47',704:'e6',713:'e8',728:'e10',736:'e50',740:'e52',745:'e68',771:'e53',776:'e53'}.items():F(w,grammatical_object_id=eid)

# Spatial path descriptions describe static routes, never actual walking.
for w,eid,source in [(147,'e11','winding_motion'),(242,'e20','leading_motion'),(250,'e21','curving_motion'),(363,'e35','running_motion'),(615,'e41','going_motion'),(627,'e41','slipping_motion')]:F(w,figurative_mapping={'target_id':eid,'source_image':source,'kind':'fictive_motion','literal_event':False})
F(4,figurative_mapping={'target_id':'e4','source_image':'thief_stealing_a_book','kind':'personification','literal_event':False})
F(52,figurative_mapping={'target_id':'e6','source_image':'tiny_flower','kind':'simile','literal_event':False})
F(706,figurative_mapping={'target_id':'e6','source_image':'flower_blooming','kind':'metaphor','literal_event':False})
F(801,figurative_mapping={'target_id':'e55','actual_referent_id':'e6','source_image':'small_green_flower','kind':'depicted_metaphor','literal_event':False})
F(55,generic_reference=True,ontological_type='comparison_image')
for w,depiction,referent in [(294,'e33','e8'),(299,'e33','e8'),(586,'e33','e8'),(359,'e35','e21'),(791,'e54','e8'),(797,'e54','e8'),(794,'e56','e7'),(801,'e55','e6'),(805,'e57','e46')]:F(w,reference_metonymic_link={'literal':depiction,'referent':referent,'relation':'depicts'})
F(747,reference_metonymic_link={'literal':'e68','referent_event_ids':['ev143','ev93'],'relation':'maps_traveled_route'})
F(764,reference_metonymic_link={'literal_carrier':'e10','referent':'e9','relation':'map_location_represents_place'})
a.feature([294,586,747,764,791,794,801,805],evidence=[288,290,291,294,359,583,586,589,730,745,747,760,764,788,791,794,801,805],note='Map marks and final sketch contents are representations. They remain distinct from physical landmarks; reference_metonymic_link records their depiction/representation bridge, not identity.')

# Misidentification, belief correction and source continuity.
for w in [213,214]:F(w,speaker_local_name={'entity_id':'e17','name':'Twin Chimneys','speaker_id':'e1'},belief_holder_id='e1',belief_content_id='p9',belief_polarity='accepts',belief_error_status='contradicted_by_narration',assertion_status='attributed_claim')
a.feature([213,214],evidence=[194,204,213,214,294,310,314,315],note='The referent being pointed at is the bathhouse chimney pair e17. Tessa applies the rock-landmark name e8 incorrectly; do not merge these two physical pairs.',reference_identity_conflict={'left':'e17','right':'e8','constraint':'distinct_physical_landmarks'})
F(233,belief_holder_id='e1',belief_content_id='p10',belief_certainty='tentative',epistemic_attitude_kind='hypothesis')
F(230,modal_base={'kind':'epistemic_possibility','holder':'e1','content_id':'p10'})
F(256,modal_base={'kind':'epistemic_inference','holder':'e1','content_id':'p11'},modal_auxiliary_class='necessity_family')
F(257,belief_holder_id='e1',belief_content_id='p11',epistemic_attitude_kind='inference',assertion_status='attributed_claim')
F(375,belief_holder_id='e1',belief_content_id='p17',belief_certainty='certain',belief_error_status='contradicted_by_narration',epistemic_time_scope={'belief':'p17','phase':'before_corrective_map_check'})
F(377,evidence_assertor_id='e1',assertion_status='attributed_claim')
F(310,evidence_observation_channel='vision',evidence_access_holder='e1',epistemic_resolution_status='mistaken_identity_recognized')
F(320,belief_revision={'old':'p9','new':'p13','basis':'ev52'},epistemic_resolution_status='error_recognized')
a.feature(320,evidence=[290,294,310,314,315,320,324,353,375,383],note='The Oh and subsequent route correction support recognition of the misidentification; no unspoken apology is invented.',evidence_explicit=False,assertion_status='candidate')
F(222,utterance_id='ev140',speaker_id='e2',speech_act_kind='remind',utterance_content_id='p5',evidence_report_depth=1)
F(225,evidence_assertor_id='e3',evidence_quote_source_id='e3',evidence_report_depth=2)
F(383,causal_parent=B('e1',{'cause':'ev62','effect':'p18','attitude_content':'p17'}))
F(428,imaginer_id='e1',imagined_content_id='p21',imagined_world_id='w_quiet_sketch',imagination_function='anticipate_desired_rest_and_drawing')
F(431,semantic_world_id='w_quiet_sketch',evidence_world_status='imagined')
F(346,knowledge_gap_holder_id='e2',knowledge_gap_content_id='p15',truth_commitment='suspended',speaker_id='e2',utterance_id='ev141',speech_act_kind='question',utterance_content_id='p15')
F(348,modal_base={'kind':'epistemic_possibility','holder':'e2','content_id':'p15'})
F(349,assertion_status='attributed_claim',truth_commitment='suspended')
F(686,speaker_id='e2',speech_act_kind='recognition_call',utterance_content_id='p30',speaker_local_name={'entity_id':'e6','name':'Captain','speaker_id':'e2'})
a.feature([686,689],evidence=[41,44,45,46,48,686,688,689],note='Milo identifies the later green anemone as Captain. The story supports his recognition, but gives no independent individual-identification test.',identity_hypothesis={'entity_id':'e6','holder_id':'e2','basis':'recognition_call','assertion_status':'attributed_claim'})

# Desire, promise, rejected options and actual choice are independent labels.
F(31,goal_owner_id='e2',goal_content_id='p2',goal_status='active',goal_polarity='achieve')
F(15,goal_owner_id='e1',goal_content_id='p1',goal_status='attempted',goal_polarity='achieve')
F(105,speaker_id='e1',speech_act_kind='promise',promise_content_id='p35',promise_beneficiary_id='e3',plan_commitment_status='promised')
F(144,speaker_id='e2',speech_act_kind='promise',promise_content_id='p8',promise_beneficiary_id='e3',plan_commitment_status='promised')
F(139,goal_owner_id='e22',goal_content_id='p8',plan_commitment_status='promised',temporal_deadline={'event':'ev26','relation':'before','bound_event':'ev25','status':'promised_not_observed'})
F(137,time_expression_id='time_tide_two',event_time_interval={'event':'ev25','scope_id':'q4','clock':'local_12_hour','hour':2,'meridiem':'unspecified','factuality':'reported'})
F(142,time_anchor_id='time_tide_two')
F(8,time_expression_id='time_morning',temporal_containment={'inner':'ev1','outer':'time_morning'})
F(48,time_expression_id='time_last_summer',temporal_deixis='previous_summer',temporal_anchor_unresolved=True)
F(409,goal_owner_id='e1',goal_content_id='p19',plan_commitment_status='proposed')
F(468,modal_base={'kind':'practical_option','holder':'e22','content_id':'p23'})
F([477,488],modal_base={'kind':'consequence_of_route_option','holder':'e1','content_id':'p23'})
F(491,modal_base={'kind':'requirement_consequence_of_considered_route','holder':'e1','content_id':'p24','condition_id':'p23'})
F(512,goal_owner_id='e1',goal_content_id='p23',plan_commitment_status='adopted',plan_revision={'replace':'p19','with':'p23'})
F(515,plan_commitment_status='rejected',goal_owner_id='e22',goal_content_id='p19')
F(528,event_collective_participants=B('e22',{'actors':['e1','e2']}),intention_vs_action_alignment={'intention':'p23','outcome_event_id':'ev93','alignment':'steps_completed_upper_route_taken_later'})
F(540,modal_base={'kind':'retrospective_ought','holder':'e1','content_id':'p26'},assertion_status='attributed_claim')
F(539,modal_auxiliary_class='necessity_family',auxiliary_chain=['modal','perfect'])
F(602,event_role_reassignment=B('e40',{'previous_reader':'e1','new_reader':'e2','event_id':'ev107'}))
F(720,request_action_id='ev127',speaker_id='e1',addressee_ids=['e2'],factuality='desired')
F(723,temporal_duration={'qualitative':'brief','expression':'a second','exact_numeric_duration_asserted':False})

for w,pid in [(94,'p6'),(103,'p6'),(330,'p36'),(368,'p37'),(382,'p38'),(419,'p39'),(514,'p19')]:F(w,polarity='negative',negation_marker_form=a.words[w]['token'],negation_scope_id=pid)
P(36,'Milo sounds cross.',[329,330,331,332])
P(37,'The dotted map route follows the lower shelf route.',[359,360,367,368,369,370])
P(38,'Tessa looked closely before choosing the route.',[375,377,382,383,384])
P(39,'The map depicts a path around the point.',[417,418,419,420,421])
P(40,'Milo watches the green anemone he recognizes as Captain opening.',[686,689,690,704,705,706])
F(331,lexical_sense_id='sound_as_seem_from_voice')
a.feature(331,evidence=[329,330,331,332,333,334,336],note='Not sounding cross is an appearance claim, not proof that Milo feels no anger.',evidence_resolution_status='affect_not_determined')
F(567,lexical_idiom_reading={'meaning':'cannot_refrain_from_laughing','reading':'idiomatic'},polarity='negative')
a.feature([566,567,568],evidence=[562,563,565,566,567,568],note='Cannot help laughing entails actual laughter in this construction. It is not a negated helping event or an absent laugh.')
F(550,dialogue_repair_kind='chronology_correction',dialogue_repair_target_id='ev97',utterance_content_id='p27')
F(553,event_time_relation={'left':'ev60','relation':'after','right':'ev99'})

# Bound physical properties, relative locations and route topology.
for w,eid,color in [(43,'e6','green'),(88,'e8','dark'),(196,'e18','pale'),(293,'e33','dark'),(585,'e33','dark'),(688,'e6','green'),(790,'e54','dark'),(800,'e55','green')]:
    F(w,appearance_color=B(eid,color,a.words[w]['scope_id'],'attributed_claim' if w==88 else 'asserted',factuality='reported' if w==88 else 'asserted'))
for w,eid,material in [(457,'e38','stone'),(593,'e12','wood'),(646,'e44','stone')]:F(w,material_composition=B(eid,material))
for w,part,whole in [(12,'e23','e5'),(197,'e18','e13'),(204,'e17','e13'),(674,'e23','e5'),(699,'e47','e2'),(702,'e48','e2'),(742,'e52','e10'),(774,'e53','e10'),(750,'e58','e2'),(781,'e59','e2'),(787,'e61','e5'),(113,'e62','e2'),(163,'e63','e1'),(169,'e64','e1')]:F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
for w,entity,landmark,relation in [(24,'e24','e25','off'),(111,'e14','e62','under'),(118,'e10','e15','inside'),(148,'e11','e26','above'),(156,'e7','e65','visible_between'),(164,'e63','e10','on'),(170,'e64','e5','on'),(184,'e1','e16','at'),(189,'e13','e22','below'),(200,'e18','e19','behind'),(234,'e8','e13','behind'),(244,'e20','e13','toward'),(252,'e21','e7','away_from'),(278,'e20','e28','ends_on'),(298,'e34','e33','around_in_map'),(300,'e8','e30','far_side_of'),(317,'e8','e7','projects_from'),(341,'e31','e29','below'),(364,'e35','e21','represents_route_along'),(388,'e36','e27','over'),(392,'e27','e28','at_end_of'),(410,'e22','e30','around'),(448,'e7','e27','across'),(460,'e38','e16','leads_to'),(480,'e22','e16','past'),(516,'e22','e30','around'),(596,'e12','e39','beyond'),(616,'e41','e70','between'),(622,'e41','e12','beyond'),(633,'e4','e66','among'),(641,'e9','e43','under'),(663,'e7','e45','visible_through'),(666,'e45','e42','gap_in'),(692,'e6','e51','in'),(700,'e47','e48','on'),(709,'e1','e2','beside'),(731,'e10','e49','across'),(785,'e60','e61','across'),(792,'e54','e56','in_depiction'),(796,'e55','e54','below_in_depiction'),(803,'e55','e57','in_depiction')]:
    scope=a.words[w]['scope_id'];F(w,spatial_configuration=B(entity,{'landmark':landmark,'relation':relation},scope,'attributed_claim' if scope.startswith('q') else 'asserted'))
F(234,spatial_configuration=B('e8',{'landmark':'e13','relation':'behind'},'q9','attributed_claim',factuality='hypothetical'))
F(410,spatial_configuration=B('e22',{'landmark':'e30','relation':'around'},'q14','attributed_claim',factuality='hypothetical'))
F(480,spatial_configuration=B('e22',{'landmark':'e16','relation':'past'},'option1','asserted',factuality='hypothetical'))
F(516,spatial_configuration=B('e22',{'landmark':'e30','relation':'around'},'q17','attributed_claim',factuality='negated'))
F(67,object_shape=B('e10','folded'))
F(269,containment_boundary_state=B('e13',{'state':'locked'}))
F(271,access_barrier=B('e13',{'barrier_kind':'boarding','access_status':'blocked'}))
F(199,spatial_occlusion=B('e18',{'occluder':'e19','extent':'almost_hidden'}))
F(432,object_shape=B('e5','flat','imagine1','asserted',factuality='hypothetical'))
F(464,attributes=[{'name':'slope','value':'steep'}])
F(466,attributes=[{'name':'surface_moisture','value':'dry'}])
F(390,object_shape=B('e27','flat'))
F(280,attributes=[{'name':'width','value':'narrow'}])
F(645,attributes=[{'name':'height','value':'low'}])
F(694,material_transparency=B('e51','clear'))
F(676,attributes=[{'name':'motion_state','value':'still'}])
F(778,object_shape=B('e53','flat'))
F(651,ontological_type='resting_location',referent_kind='predicative_type')
F(648,affordance_supporting=B('e44',{'object_id':'e14','can_support':True}))
# No path is drawn is a claim about the map, not proof of no physical passage.
F(418,explicit_zero_count={'scope_id':'s0','assertion_status':'asserted','value':0,'domain':{'carrier':'e10','kind':'drawn_path_around_point'}})
a.feature([418,420,421],evidence=[407,409,412,417,418,419,420,421,452],note='The map lacks a marked path around the point. The exposed shore passage still exists and is later described as narrowing; no universal physical absence is inferred.')
F(453,access_clearance=B('e37',{'change':'narrowing','cause_candidate':'advancing_water','usable_width':'unspecified'},'q15','attributed_claim'))
F(447,causal_parent=B('e37',{'cause':'ev76','effect':'p22'},status='candidate'))
a.feature(447,evidence=[386,387,391,442,443,446,447,450,451,453,454],note='Milo’s juxtaposed pointing and warning support advancing water as the cause of diminishing route width; the exact tide level and remaining time are not calculated.')
F(147,motion_route=B('e11',{'landmark_id':'e26','role':'static_path_above_beach'}))
# The preceding field is deliberately a topology fact, not traversed route.
a.words[147].pop('motion_route')
F(263,motion_route=B('e2',{'landmark_id':'e20','event_id':'ev46','role':'actual_route'}))
F(493,motion_route=B('e1',{'landmark_id':'e20','event_id':'ev86','role':'actual_route'},'past2'))
F(324,event_collective_participants=B('e22',{'actors':['e1','e2'],'leader_event_id':'ev86','follower_event_id':'ev46'},'q12','attributed_claim'))
F(528,motion_route=B('e22',{'landmark_id':'e38','event_id':'ev93','role':'actual_route'}),motion_destination=B('e22',{'landmark_id':'e16','event_id':'ev93','role':'destination'}))
F(678,motion_destination=B('e2',{'landmark_id':'e46','event_id':'ev118','role':'destination'}))
F(69,motion_route=B('e22',{'landmark_id':'e11','event_id':'ev15','role':'instructed_route'},'q2','attributed_claim',factuality='desired'))
F(78,motion_waypoint=B('e22',{'landmark_id':'e12','event_id':'ev16','role':'instructed_turn_landmark'},'q2','attributed_claim',factuality='desired'))
F(469,motion_route=B('e22',{'landmark_id':'e38','event_id':'ev80','role':'proposed_route'},'option1','asserted',factuality='hypothetical'))
F(472,motion_route=B('e22',{'landmark_id':'e21','event_id':'ev81','role':'proposed_route'},'option1','asserted',factuality='hypothetical'))

# Ownership, temporary holding, instrument use, material changes and actual
# endpoints. No return or journey-completion event is supplied after the story.
F(68,possession_owner=B('e10',{'owner':'e3'}))
F(6,possession_owner=B('e5',{'owner':'e1'}))
F(23,possession_owner=B('e24',{'owner':'e1'}))
F(107,possession_holder=B('e14',{'holder':'e2'}))
F(115,possession_holder=B('e10',{'holder':'e1'}),containment_direct=B('e10',{'container':'e15'}))
F(285,containment_direct=B('e10',{'previous_container':'e15','inside_after':False}))
F(728,possession_user=B('e10',{'user':'e2'}),spatial_support=B('e10',{'supported_by':'e49'}),object_shape=B('e10','unfolded'))
F(740,event_instrument_binding=B('e50',{'used_on':'e10','event_id':'ev131'}))
F(776,event_effector=B('e53',{'effector':'e59','event_id':'ev136'}),event_state_change=B('e53',{'before':'lifted','after':'flat','event_id':'ev136'}))
F(788,reference_metonymic_link={'literal':'e60','referent':'e1','relation':'instrument_for_artist'},event_effector=B('e54',{'effector':'e60','event_id':'ev128'}))
F(21,event_causer=B('e24',{'causer':'e4','event_id':'ev5'}))
F(771,event_causer=B('e53',{'causer':'e4','event_id':'ev135'}))
F(632,attributes=[{'name':'wind_intensity_change','value':'weaker'}])
a.feature([632,771],evidence=[631,632,669,674,675,676,770,771,774],note='Wind softens at the hollow but is not absent; it can still lift the map edge. Still pages do not establish no wind anywhere.')
F(788,event_creation=B('e54',{'created':True,'carrier':'e61','other_depicted_entities':['e55','e56','e57'],'event_id':'ev128'}))
F(36,goal_beneficiary_ids=['e2'])
F(29,mention_form='kinship_description')

# Attributed speech, sources and discourse: each report verb has an actual
# utterance, while quoted state/action content retains its own truth status.
SPEECH=[(62,'e3','inform_and_instruct','p4',['e22']),(105,'e1','promise','p35',['e3']),(132,'e3','warn','p7',['e22']),(144,'e2','promise','p8',['e3']),(212,'e1','identify','p9',['e2']),(238,'e1','hypothesize','p10',['e2']),(322,'e1','recognition','p13',['e2']),(328,'e2','point_out','p14',['e1']),(414,'e1','suggest','p19',['e2']),(512,'e1','choose_and_instruct','p25',['e2']),(544,'e1','acknowledge_error','p26',['e2']),(550,'e2','correct','p27',['e1']),(604,'e2','read_directions','p28',['e1']),(611,'e2','read_directions','p28',['e1']),(719,'e1','report_view','p31',['e2'])]
for w,speaker,kind,pid,addressees in SPEECH:
    F(w,speaker_id=speaker,speech_act_kind=kind,utterance_id=a.words[w]['event_id'],utterance_content_id=pid,addressee_ids=addressees,communication_channel='speech')
F(132,warning_hazard_id='p7')
F(453,speaker_id='e2',utterance_id='ev142',speech_act_kind='warn',warning_hazard_id='p22',utterance_content_id='p22',addressee_ids=['e1'])
F(520,speaker_id='e2',communication_channel='gesture',speech_act_kind='acknowledge',dialogue_response_to_id='ev89',request_acceptance_status='accepted')
F(621,belief_acceptance_status='narrator_confirmed_direction',evidence_explicit=True)
F(558,communication_channel='gaze',communication_intended_effect='unspecified',evidence_resolution_status='look_interpretation_open')
F(568,affect_expression_channel='laughter',affect_experiencer_id='e1')
F(131,event_time_relation={'left':'ev24','relation':'after','right':'ev23'})
F(141,event_time_relation={'left':'ev26','relation':'before','right':'ev25'})
F(555,event_time_relation={'left':'ev60','relation':'after','right':'ev99'})
F(724,event_time_relation={'left':'ev129','relation':'during','right':'ev128'})
F(768,event_time_relation={'left':'ev136','relation':'when','right':'ev135'})

# Ending claims are supported by demonstrated route-checking and shared work,
# not an invented moral, return home, permanent trait or proven Captain identity.
F(214,narrative_thread_id='thread_landmark_error',narrative_problem_id='p9',narrative_thread_status='mistaken_identification')
F(383,narrative_tension_source='confident_choice_before_close_check',narrative_thread_id='thread_landmark_error')
F(515,narrative_thread_id='thread_route_choice',narrative_change_dimension='chosen_route',narrative_change_evidence={'before':'p19','after':'p25'})
F(604,narrative_change_dimension='shared_direction_reading',narrative_thread_id='thread_landmark_error')
F(675,narrative_resolution_evidence={'problem':'p1','outcome':'p29','status':'conditions_for_drawing_achieved'})
F(704,narrative_resolution_evidence={'problem':'p2','outcome':'p40','status':'partially_met_opening_observed_closing_unshown','recognition':'p30'})
a.feature(604,evidence=[213,214,256,375,383,539,540,553,555,582,583,591,601,602,603,604],note='Tessa now checks actual features and lets Milo read; this is a demonstrated local behavioral change, not proof of a permanent humility trait.',narrative_change_evidence={'before':'p18','after':'p28'})
a.feature(788,evidence=[4,10,15,21,674,675,676,726,728,736,740,771,776,781,783,788,791,801],note='The ending contrasts early disrupted solitary drawing with sheltered sketching and Milo helping steady the map. Return before two and physical return of the map remain unshown.',narrative_theme_candidate={'content':'checking_landmarks_and_sharing_the_work_supports_the_trip','source':'annotator','status':'candidate'},narrative_motif_link={'earlier':'ev1','current':'ev136','relation':'wind_disruption_met_with_shared_practical_response'},narrative_closure_candidate={'cue':'completed_destination_activity_and_final_drawing','status':'candidate','thread':'thread_landmark_error'})

# Repairs from reading the assembled paragraphs.
for w in [125,310,331,604]:
    F(w,verb_form='base');a.words[w].pop('tense',None)
F(179,verb_form='past_participle',participial_function='passive_reduced_relative')
F(556,verb_form='gerund_participle')
for w in [67,375]:
    a.words[w].pop('verb_form',None);a.words[w].pop('tense',None)
F(332,lexical_sense_id='cross_irritable')
F(161,grammatical_object_id='e63',phrase_content_head_ids=[a.anchor(163),a.anchor(169)])
a.words[216].pop('grammatical_object_id',None)
F(217,prepositional_object_id='e10')
a.words[558].pop('grammatical_object_id',None)
F(558,indirect_object_id='e2',light_verb_construction='give_a_look')
F(346,belief_holder_id='e1',belief_content_id='p15',epistemic_attitude_kind='questioned_belief')
F(210,discourse_focus_id='e17')
F(788,instruments=['e60'])
for eid,event in a.events.items():
    event['support_words']=sorted(set(event['support_words'])|{w for w,row in enumerate(a.words) if any(b['event_id']==eid for b in row.get('event_bindings',[]))})
for w,row in enumerate(a.words):
    if row.get('role')=='action' and 'assertion_status' not in row:
        F(w,assertion_status='attributed_claim' if row['scope_id'].startswith(('q','report','belief')) else 'asserted')
    if row.get('role')=='action' and row['scope_id'].startswith('q'):
        F(w,evidence_assertor_id=a.scopes[row['scope_id']]['holder_id'])

FEEDBACK={
 'summary':'Manual retrospective annotation of the seaside route mistake, correction, shared drawing and anemone observation. Distinguishes physical landmarks, mistaken labels, map representations, imagined plans and the final sketch.',
 'ambiguities':[
  {'words':[36,683],'issue':'The initially desired pool is nonspecific e69; the actual destination pool is e46. Goal satisfaction does not force identity of a hypothetical witness.'},
  {'words':[41,44,686,689],'issue':'Milo recognizes Captain; later anemone uses the same discourse ID with attributed identification, not biological proof of individual identity since last summer.'},
  {'words':[213,214,379],'issue':'Twin Chimneys at the mistaken turn names the bathhouse pair e17; correct landmark is e8. The belief’s intended landmark remains separate from its perceived wrong referent.'},
  {'words':[294,586,747,764,791,794,801,805],'issue':'Map marks and final sketch entities are distinct from their referents; representation links are recorded explicitly.'},
  {'words':[324,493],'issue':'Milo’s collective wrong-route report ev143 is the shared episode containing Tessa’s leading ev86 and Milo’s following ev46, not another walk.'},
  {'words':[418,420,421,452],'issue':'No path drawn on map does not prove no physical passage. Shore passage exists but shrinks; the scramble is never performed.'},
  {'words':[618,668],'issue':'Route-flanking rocks and view-gap rocks have separate IDs because exact overlap is unknown.'},
  {'words':[651,653,656,734],'issue':'Wall offers a basket resting place, but actual basket placement and picnic-cloth deployment are not narrated. No invented placing/unpacking event.'},
  {'words':[137,138,139,142],'issue':'Two is a local clock time with no stated meridiem; timely return is promised but never shown.'},
  {'words':[331,558,563,568],'issue':'Not sounding cross does not prove absence of anger; Tessa’s look is uninterpreted. Grinning and laughing are explicit behaviors, not permanent personality labels.'},
 ],
 'feature_gaps':[
  {'key':'affordance_supporting','decision':'Proposed typed surface/object support capacity, distinct from actual spatial_support, bodily sitting and containment. The wall can support the basket, but placement is unobserved.'},
  {'meaning':'depiction relation','decision':'Reused reference_metonymic_link with relation=depicts/maps_traveled_route. Its definition supports literal-to-related-referent links, but future schema may benefit from an explicit representation subtype distinguishing carrier, image entity and world referent.'},
  {'meaning':'collective episode decomposition','decision':'Reused event_collective_participants with member leading/following event IDs. A declared event-part/subevent convention would make this relationship less ad hoc.'},
 ],
 'prompt_feedback':[
  'Include a mistaken landmark example where speaker_local_name differs from actual entity identity; later correction must not rewrite the earlier mistaken belief into fact.',
  'Distinguish fictional enactment from map/sketch depiction; provide a standard carrier/image/referent bridge rather than forcing image objects into physical identity.',
  'A static path winding or slipping inland is fictive motion; it must not create a person walking that path.',
  'Negative evidence from a map is representation-scoped. An unmarked route can still physically exist.',
  'Use clear episode/subevent conventions when a collective retrospective report summarizes distinct leader/follower actions.',
  'Qualitative a second can mean briefly rather than an exactly measured one-second duration.',
 ],
 'coverage_notes':'All 806 words have manually selected contextual POS and lemma; every one of 32 paragraphs reviewed. Sparse supported grammar, reference, event, physical, mental, discourse and narrative fields use the full catalog as available, without feature quotas. Quoted and imagined propositions preserve local truth conditions. No API calls or causal filtering.',
 'reviewed_all_words':True,'reviewed_paragraphs':list(range(32)),
 'not_claimed':['return before two','map returned to Vale','literal wind theft','a literal flowering plant instead of an anemone','completed scramble around point','basket placed on wall','total absence of wind'],
}
a.save(FEEDBACK)
