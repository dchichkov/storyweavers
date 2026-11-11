"""Manual whole-story pond annotations, frozen v2 prompt."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a=Annotation('14_pond',prompt_version='v2')
for key in ['appearance_color','part_whole_relation']:a.use_extension(key)
LEX={
0:'det=the n=pond adp=in n=Briar n=Park v=be adj=shallow conj=but det=its n=water v=be det=the n=color adp=of adj=strong n=tea conj=and det=the adj=muddy n=bottom v=disappear adp=beneath det=the adj=green n=duckweed n=Theo adj=wooden n=boat det=the n=June n=Bug v=have det=a adj=yellow n=sail v=patch adp=with det=a n=square adp=of adj=blue n=cloth det=his n=grandfather v=have v=help pron=he v=sand det=the n=hull conj=and n=Theo v=want part=to v=test det=the adj=new n=patch adp=before det=his n=grandfather v=visit adp=on n=Sunday',
1:'pron=it v=sail det=all det=the n=way adp=to det=the n=fountain pron=he v=say',
2:'n=Mina v=watch det=the n=breeze v=wrinkle det=the n=pond adv=maybe v=start adp=with det=the adj=near n=side',
3:'n=Theo v=set det=the n=boat adp=on det=the n=water adp=for det=a det=few n=second pron=it v=sail adv=beautifully adv=then det=a n=gust v=spin pron=it adv=around conj=and v=send pron=it v=skim adp=toward det=the n=reed',
4:'n=Theo n=smile v=vanish pron=it v=go part=to v=get adj=stuck',
5:'n=Mina v=stay adp=on det=the n=gravel n=path pron=I v=get n=Mr n=Alvarez',
6:'det=the n=park n=gardener v=be v=rake n=leaf adv=nearby n=Mina v=ask conj=if pron=she v=can v=borrow det=his adj=long adj=handled n=net pron=he v=look adp=from pron=she adp=to n=Theo adv=then adp=to det=the n=boat v=drift adv=far adv=out',
7:'adp=of n=course pron=he v=say conj=but v=keep det=both n=foot adp=on det=the n=path det=the n=bank v=be adj=slippery adv=even adv=where det=the n=pond v=be adj=shallow',
8:'pron=I v=will n=Mina v=promise',
9:'n=Mr n=Alvarez v=hand pron=she det=the n=net det=its adj=wooden n=handle v=be adv=almost adv=as adj=tall conj=as pron=she v=be conj=and det=the n=hoop adp=at det=the n=end v=be adj=wide adv=enough part=to v=catch det=a adj=whole n=heap adp=of n=leaf n=Theo v=walk adp=beside pron=she conj=as pron=she v=carry pron=it adp=to det=a adj=level n=stretch adp=of n=gravel',
10:'v=tell pron=I adv=where det=the n=boat v=be n=Mina v=say',
11:'adv=just adv=left adp=of det=that n=clump adp=of n=reed',
12:'pron=she v=lower det=the n=hoop conj=until pron=it v=skim det=the n=surface conj=and v=push pron=it adp=toward det=the n=boat det=the n=wind v=nudge det=the n=June n=Bug adv=away n=Mina v=reach adv=far v=keep det=her n=shoe v=plant adp=on det=the adj=dry n=path',
13:'det=the n=net n=hoop v=slide adp=beneath det=the n=boat conj=and v=snag adp=with det=a adj=sharp n=jerk',
14:'n=Mina n=arm v=jolt det=the n=handle v=bow adp=over det=the n=water adv=somewhere adp=below det=the n=surface det=the n=hoop v=have v=catch adp=on det=a v=submerge n=willow n=branch',
15:'v=pull n=Theo v=cry pron=it v=get adv=away',
16:'pron=he v=take det=a adj=quick n=step adp=toward det=the n=edge n=Mina v=catch det=his n=sleeve',
17:'v=stay adp=on det=the n=path pron=she v=say pron=I v=mean pron=it',
18:'n=Theo v=stop det=the n=boat v=bob adv=far adp=from pron=they det=its adj=yellow n=sail v=flicker adp=between det=the n=reed',
19:'n=Mina v=tighten det=her n=grip adp=on det=the n=handle conj=if pron=she v=yank adv=hard pron=she v=may v=free det=the n=hoop pron=she v=may adv=also v=break n=Mr n=Alvarez n=net conj=or v=make det=the adj=slippery n=edge v=crumble adp=under det=her n=shoe',
20:'pron=I part=not v=pull pron=she v=say',
21:'conj=but det=the n=boat',
22:'pron=I v=know pron=she v=ease det=the n=handle adv=down conj=until pron=it v=rest adp=against det=the n=gravel pron=I v=go part=to v=free det=the n=net adv=first adv=then pron=we v=follow det=the n=boat adp=from det=the n=path',
23:'det=the n=wind v=push det=the n=June n=Bug adp=past det=the n=reed conj=and adp=toward det=the n=pond adj=stone n=outlet n=Theo v=watch pron=it v=go det=his n=finger v=curl adp=around det=the adj=blue n=cord pron=he v=bring part=to v=use adp=as det=a n=tether pron=he v=have v=think det=the n=pond v=be adj=calm adv=enough adp=without pron=it',
24:'n=Mina v=study det=the n=net n=handle det=the n=hoop v=have v=catch conj=while pron=she v=be v=push pron=it adv=forward pron=she v=take det=a n=step adv=sideways adp=along det=the n=path adv=then adv=gently v=push det=the n=handle adv=away adp=from n=shore det=the n=hoop v=shift adv=underwater pron=she v=turn det=the n=handle det=a adv=little adv=then v=draw pron=it adv=back',
25:'det=the n=hoop v=slide adj=free',
26:'n=Mina v=let adv=out det=a n=breath pron=she v=have v=notice pron=she v=be v=hold pron=she v=lift det=the n=net adj=clear adp=of det=the n=water conj=and v=check pron=it det=a n=willow n=twig v=lie adp=in det=its n=mesh pron=she v=pluck pron=it adv=out conj=and v=set pron=it adp=on det=the n=gravel',
27:'adv=now pron=she v=say pron=we v=walk',
28:'pron=they v=follow det=the adj=curved n=path adp=around det=the n=pond n=Theo v=keep det=his n=eye adp=on det=the n=boat v=call adv=out conj=whenever det=a n=gust v=spin pron=it conj=or det=a n=reed v=hide pron=it det=the n=path v=bring pron=they adp=to det=the adj=stone n=outlet adv=where det=the n=water v=be adj=calm det=the n=June n=Bug v=have v=drift adp=into det=the adj=sheltered n=corner conj=and v=bump adv=softly adp=against det=the n=stone',
29:'adv=there n=Theo v=whisper adj=close adp=to det=the n=edge',
30:'adj=close v=be det=the adj=same conj=as adj=reachable n=Mina v=say',
31:'pron=she v=stand adv=well adv=back adp=on det=the n=path conj=and v=lower det=the n=net det=this n=time pron=she v=move adv=slowly n=Theo v=watch adp=from adp=beside pron=she',
32:'det=a adv=little adv=left pron=he v=say adv=now adv=down',
33:'det=the n=hoop v=slip adp=around det=the n=boat adp=without v=touch det=its n=sail n=Mina v=draw pron=it adp=toward n=shore num=one adj=careful n=inch adp=at det=a n=time conj=when det=the n=net v=reach det=the n=stone n=Theo v=pick det=the n=boat adv=out adp=of det=the n=mesh v=hold pron=it adp=by det=the n=hull',
34:'det=the adj=yellow n=sail v=be adv=still adj=upright adv=only det=a det=few n=drop v=cling adp=to det=the adj=blue n=patch',
35:'n=Mr n=Alvarez v=be v=wait adv=where pron=they v=have v=leave pron=he n=Mina v=return det=his n=net adp=with det=the n=willow n=twig v=tuck adp=through det=the n=handle',
36:'v=thank pron=you pron=she v=say',
37:'v=thank pron=you adp=for v=bring pron=it adv=back adp=in num=one n=piece pron=he v=reply',
38:'n=Theo v=tie det=the adj=blue n=cord adp=around det=the n=boat n=stern det=this n=time adp=with det=a adj=firm adj=double n=knot adv=then pron=he v=set det=the n=June n=Bug adj=afloat adv=again n=Mina v=hold det=the adj=other n=end adp=of det=the n=cord conj=while n=Theo v=guide det=the n=boat adv=away adp=from det=the n=stone',
39:'det=the n=breeze v=catch det=the adj=yellow n=sail det=the n=boat v=make det=a adj=bright adj=little n=circle adp=on det=the n=tea adj=colored n=water adp=with det=the adj=blue n=cord v=draw adv=gently adp=between n=Theo n=hand conj=and n=Mina',
}
for p,text in LEX.items():
    pairs=[x.split('=',1) for x in text.split()];words=a.paragraphs[p]['words']
    assert len(words)==len(pairs),(p,len(words),len(pairs))
    a.tag(p,[x[0] for x in pairs],{w['w']:x[1] for w,x in zip(words,pairs)})

ENTS=[
('e1','Mina','person',[74,122,128,139,142,152,183,185,190,201,222,224,234,239,248,270,274,294,330,338,340,358,360,366,369,374,388,390,393,398,400,411,469,479,484,504,518,523,526,529,547,558,630,632,645,652,670,724,738,741,775,820]),
('e2','Theo','person',[25,42,46,51,59,72,87,114,154,219,317,322,332,343,441,445,452,459,570,572,618,648,656,687,751,768,784,817]),
('e3','Theo grandfather','person',[43,60]),
('e4','Mr. Alvarez','person',[130,131,134,145,149,164,187,188,378,379,715,716,723,726,737,749]),
('e5','Mina and Theo','person_group',[350,419,560,562,592,720]),
('e6','June Bug wooden boat','model_boat',[27,29,30,64,90,98,105,109,117,158,237,262,267,268,287,319,346,351,397,422,430,431,443,576,583,588,603,604,665,668,690,696,758,771,772,787,799]),
('e7','yellow boat sail','sail',[34,353,669,702,797]),
('e8','blue cloth sail patch','cloth_patch',[38,41,57,714]),
('e9','boat hull','hull',[49,699]),
('e10','boat stern','stern',[759]),
('e11','Briar Park pond','pond',[1,8,80,180,438,463,569]),
('e12','pond water','water',[9,93,302,536,599,809]),
('e13','pond bottom','pond_bottom',[19]),
('e14','duckweed','plant_group',[24]),
('e15','Briar Park','park',[3,4]),
('e16','pond fountain','fountain',[71]),
('e17','reeds around pond','reed_group',[113,247,357,434]),
('e18','submerged willow branch','branch',[315]),
('e19','willow twig in net','twig',[542,549,553,731]),
('e20','Mr. Alvarez net','net',[148,192,193,226,282,380,416,472,532,539,545,642,683,727,744]),
('e21','net wooden handle','handle',[195,298,364,403,406,473,496,507,512,735]),
('e22','net hoop','hoop',[205,251,253,259,283,308,373,475,482,501,515,661]),
('e23','net mesh','mesh',[546,694]),
('e24','hoop end of handle','handle_end',[208]),
('e25','gravel path around pond','path',[127,172,280,337,425,491,566,590,638]),
('e26','pond bank edge','bank_edge',[174,329,385,499,623,674]),
('e27','level gravel stretch','ground_region',[230,232,410,556]),
('e28','stone pond outlet','outlet',[440,596]),
('e29','sheltered outlet corner','pond_region',[610]),
('e30','outlet stones','stone_group',[616,686,791]),
('e31','breeze and wind','air_motion',[77,264,427,793]),
('e32','first gust','gust',[103]),
('e33','later gusts while following','gust_group',[581]),
('e34','occluding reeds while following','reed_group',[586]),
('e35','pond surface','surface',[256,306]),
('e36','near side of pond','pond_region',[86]),
('e37','Theo smile','expression',[115]),
('e38','Mina feet','body_part_group',[169]),
('e39','Mina shoes','shoe_pair',[275,389]),
('e40','Mina arms','body_part_group',[295]),
('e41','Theo sleeve','clothing_part',[333]),
('e42','Mina grip','physical_hold',[361]),
('e43','Theo fingers','body_part_group',[446]),
('e44','Theo blue cord','cord',[451,468,755,782,813]),
('e45','Mina-held end of cord','cord_end',[779]),
('e46','Theo hands','body_part_group',[818]),
('e47','Mina hands','body_part_group',[]),
('e48','leaves being raked','leaf_group',[137]),
('e49','hypothetical heap of leaves fitting hoop','leaf_group',[216,218]),
('e50','drops on patch','water_drop_group',[709]),
('e51','firm double cord knot','knot',[766]),
('e52','circular boat course','trajectory',[804]),
]
# Independent possessive Mina's at ending denotes her hands, not a new mention
# of Mina herself; the explicit possessor relation is retained in features.
for i,x in enumerate(ENTS):
    if x[0]=='e1':ENTS[i]=(*x[:3],[w for w in x[3] if w!=820])
    if x[0]=='e47':ENTS[i]=(*x[:3],[820])
for args in ENTS:a.entity(*args)
a.entities['e5']['member_ids']=['e1','e2']
a.entities['e19']['identity_note']='Twig recovered from mesh; source does not establish it broke off the large submerged branch.'
a.entities['e17']['known_subgroups']=['e34']
F=a.feature
def B(e,value,scope='s0',status='asserted',**extra):return dict(entity_id=e,value=value,scope_id=scope,assertion_status=status,**extra)
QUOTES=[
('q1',64,72,'e2','Prediction of sailing to fountain','e1'),('q2',81,87,'e1','Near-side suggestion','e2'),
('q3',117,122,'e2','Anticipated stuck boat','e1'),('q4',128,132,'e1','Plan to get gardener','e2'),
('q5',162,164,'e4','Loan permission','e1'),('q6',166,183,'e4','Path instruction and bank warning','e1'),
('q7',183,185,'e1','Promise to keep feet on path','e4'),('q8',233,239,'e1','Request boat location','e2'),('q9',241,248,'e2','Boat left of reeds','e1'),
('q10',316,317,'e2','Pull command','e1'),('q11',319,322,'e2','Boat getting away','e1'),
('q12',334,338,'e1','Stay on path','e2'),('q13',340,343,'e1','Seriousness of instruction','e2'),
('q14',390,393,'e1','Refuse current pulling of snagged net','e2'),('q15',395,398,'e2','Interrupted concern for boat','e1'),
('q16',398,400,'e1','Acknowledge boat concern','e2'),('q17',411,426,'e1','Net first then follow boat from path','e2'),
('q18',557,558,'e1','Now','e2'),('q19',560,562,'e1','Joint walking decision','e2'),
('q20',617,618,'e2','Deictic boat location','e1'),('q21',620,624,'e2','Boat close to edge','e1'),
('q22',624,630,'e1','Proximity does not imply reachability','e2'),('q23',653,656,'e2','Guide net left','e1'),('q24',658,660,'e2','Guide net down','e1'),
('q25',736,738,'e1','Thanks for net loan','e4'),('q26',740,749,'e4','Thanks for intact return','e1'),
]
for sid,lo,hi,holder,desc,audience in QUOTES:
    a.scope(sid,range(lo,hi),kind='quotation',holder_id=holder,description=desc)
    a.scopes[sid]['addressee_ids']=[audience]
    F(range(lo,hi),quote_mode='direct',assertion_status='attributed_claim')
for sid,lo,hi,kind,holder,parent,desc in [
('s1',54,64,'desired_test','e2','s0','Test desired before future grandfather visit.'),
('s2',59,64,'anticipated_visit','e2','s1','Visited is morphologically past but anticipated relative to test.'),
('s3',141,149,'indirect_request','e1','s0','Net loan requested before actual handoff.'),
('s4',213,219,'affordance_content',None,'s0','Capacity to catch leaves, not actual catching of this heap.'),
('s5',365,374,'conditional_outcome','e1','s0','Forceful yank might free hoop; never performed.'),
('s6',374,390,'alternative_risk','e1','s5','Net breakage or bank crumble possible under yank, not actual damage.'),
('s7',455,459,'purpose','e2','s0','Cord brought for tethering; initial use absent.'),
('s8',462,469,'belief_content','e2','s0','Earlier judgment of pond calmness without tether.'),
]:a.scope(sid,range(lo,hi),kind=kind,holder_id=holder,parent=parent,description=desc)
PROPS=[
(1,'Theo tests the new patch before his grandfather visits Sunday.',[52,54,57,58,60,61,63],'s1'),
(2,'The boat sails all the way to the fountain.',[64,65,68,71],'q1'),(3,'Theo starts the test at the near side.',[81,82,85,86],'q2'),
(4,'The boat gets stuck in reeds.',[117,118,120,121],'q3'),(5,'Mina gets Mr. Alvarez help.',[128,129,130,131],'q4'),
(6,'Mina borrows Mr. Alvarez net.',[142,144,145,148],'s3'),(7,'Mina keeps both feet on path.',[167,168,169,172],'q6'),
(8,'The bank is slippery even by shallow water.',[174,175,176,177,180,182],'q6'),
(9,'Theo tells Mina where the boat is.',[233,234,235,237,238],'q8'),(10,'The boat is just left of that reed clump.',[241,242,245,247],'q9'),
(11,'Mina pulls the snagged net.',[316],'q10'),(12,'The boat is getting away.',[319,320,321],'q11'),
(13,'Theo stays on the path.',[334,335,337],'q12'),(14,'Mina yanks the snagged net hard.',[366,367,368],'s5'),
(15,'Mina frees the hoop by forceful pulling.',[369,370,371,373],'s5'),(16,'Mina breaks Mr. Alvarez net by yanking.',[374,377,379,380],'s6'),
(17,'The bank edge crumbles under Mina shoes due to yanking.',[382,385,386,389],'s6'),
(18,'Mina is not pulling the currently snagged net.',[390,391,392],'q14'),(19,'Mina frees the net first.',[411,414,416,417],'q17'),
(20,'Mina and Theo follow boat from path after freeing net.',[418,419,420,422,425],'q17'),
(21,'The pond is calm enough for this boat without a tether.',[462,463,464,465,466,467,468],'s8'),
(22,'Mina notices she is holding her breath.',[523,524,525,526,527,528],'s0'),
(23,'Mina and Theo walk around pond following boat.',[560,561,562,563,566],'q19'),
(24,'Boat is close to the outlet edge.',[617,620,623],'q21'),(25,'Being close is equivalent to being reachable.',[624,625,627,629],'q22'),
(26,'Being close does not mean being reachable.',[624,625,627,629],'q22'),(27,'Mina moves the net a little left.',[653,654,655],'q23'),
(28,'Mina moves the net down now.',[658,659],'q24'),(29,'The hoop touches the boat sail during capture.',[661,667,668,669],'s0'),
(30,'Mina returns the net intact to Mr. Alvarez.',[725,727,743,744,747,748],'q26'),
(31,'Theo and Mina retrieve the boat while leaving its sail upright.',[671,688,690,702,705],'s0'),
(32,'Theo uses the blue cord as a tether on relaunch.',[752,755,759,766,769,776,785],'s0'),
]
for n,text,support,scope in PROPS:a.proposition(f'p{n}',text,support,scope_id=scope)
EV={}
def st(scope):
    while scope is not None:
        s=a.scopes[scope]
        if s['kind'] in ['quotation','indirect_request','belief_content']:return 'attributed_claim'
        scope=s['parent']
    return 'asserted'
def E(key,w,label,**kw):
    eid=f'ev{len(EV)+1}';EV[key]=eid;a.event(eid,w,label,**kw)
    if kw.get('primary',True):F(w,assertion_status=st(a.words[w]['scope_id']))
    return eid
def M(key,words,role='reference',note=''):
    a.mention_event(EV[key],words,role=role,note=note)
    if role=='action':
        for w in [words] if isinstance(words,int) else words:F(w,assertion_status=st(a.words[w]['scope_id']))
def U(key,w,speaker,content,audience,kind='assertion',**kw):
    eid=E(key,w,'communicate '+content,type='speak',actor=speaker,recipient=audience,**kw)
    F(w,speaker_id=speaker,speech_act_kind=kind,utterance_id=eid,utterance_content_id=content,addressee_ids=[audience],communication_channel='speech',communication_scope_bundle={'speaker_id':speaker,'utterance_event_id':eid,'scope_id':'s0','assertion_status':'asserted'})
    return eid

E('shallow',6,'pond is shallow',type='state',patients=['e11'],roles={'patient':[1]})
E('tea_color',10,'pond water is strong-tea colored',type='state',patients=['e12'],roles={'patient':[9]})
E('bottom_hidden',20,'muddy bottom is hidden beneath duckweed',type='state',patients=['e13'],roles={'patient':[19],'occluder':[24]})
E('boat_sail',31,'boat has yellow sail',type='state',patients=['e6','e7'],roles={'patient':[27,34]})
E('patched',35,'sail is patched with blue cloth square',type='state',patients=['e7'],instruments=['e8'],roles={'patient':[34],'patch':[38,41]})
E('help_sand',45,'grandfather helped Theo sand hull',actor='e3',recipient='e2',patients=['e9'],roles={'actor':[43],'recipient':[46],'patient':[49]})
E('sand',47,'Theo sands hull with grandfather help',actor='e2',patients=['e9'],roles={'actor':[46],'patient':[49]})
E('want_test',52,'Theo wants to test new patch',type='feel',actor='e2',patients=['e8'],roles={'experiencer':[51]})
E('desired_test',54,'Theo tests new patch',actor='e2',patients=['e8'],factuality='desired',roles={'patient':[57]})
E('future_visit',61,'grandfather visits on Sunday',type='move',actor='e3',factuality='hypothetical',roles={'actor':[60]})
E('predicted_sail',65,'boat sails to fountain',type='move',patients=['e6'],factuality='hypothetical',roles={'patient':[64],'destination':[71]})
U('predict',73,'e2','p2','e1','prediction',roles={'actor':[72]})
E('watch_breeze',75,'Mina watches breeze wrinkle pond',type='perceive',actor='e1',patients=['e11'],roles={'actor':[74]})
E('wrinkle',78,'breeze wrinkles pond water',patients=['e12'],roles={'causer':[77],'surface':[80]})
E('near_test',82,'Theo starts test at near side',actor='e2',factuality='desired',roles={'location':[86]})
U('near_suggest',82,'e1','p3','e2','suggestion',primary=False,scope='s0')
E('launch1',88,'Theo sets June Bug on water',type='move',actor='e2',patients=['e6'],roles={'actor':[87],'patient':[90],'destination':[93]})
E('sail1',99,'boat sails beautifully briefly',type='move',patients=['e6'],roles={'patient':[98]})
E('gust_spin',104,'gust spins boat around',type='move',patients=['e6'],roles={'causer':[103],'patient':[105]})
E('gust_send',108,'gust sends boat skimming toward reeds',type='move',patients=['e6'],roles={'patient':[109],'direction':[113]})
M('gust_send',110,'action','Skimming is manner of same gust-caused movement.')
E('smile_vanish',116,'Theo smile vanishes',type='state',patients=['e37'],roles={'patient':[115]})
E('stuck_prediction',120,'boat gets stuck in reeds',type='state',patients=['e6'],factuality='hypothetical',roles={'patient':[117]})
U('stuck_exclaim',120,'e2','p4','e1','prediction_concern',primary=False,scope='s0')
E('mina_path',123,'Mina stays on gravel path',type='state',actor='e1',roles={'actor':[122],'location':[127]})
E('get_gardener_plan',129,'Mina gets Mr Alvarez help',actor='e1',patients=['e4'],factuality='desired',roles={'actor':[128],'patient':[130,131]})
U('get_plan_speech',129,'e1','p5','e2','announce_plan',primary=False,scope='s0')
E('rake',136,'gardener rakes leaves',actor='e4',patients=['e48'],roles={'actor':[134],'patient':[137]})
U('request_net',140,'e1','p6','e4','request_permission',roles={'actor':[139]})
E('borrow_request_content',144,'Mina borrows Alvarez net',type='obtain',actor='e1',patients=['e20'],factuality='desired',roles={'actor':[142],'patient':[148]})
E('gardener_looks',150,'Alvarez looks from Mina to Theo and boat',type='perceive',actor='e4',patients=['e1','e2','e6'],roles={'actor':[149],'patient':[152,154,158]})
E('drift_far',159,'boat drifts farther out',type='move',patients=['e6'],roles={'patient':[158]})
U('permission',165,'e4','p6','e1','grant_permission',roles={'actor':[164]})
E('feet_path_instruction',167,'Mina keeps both feet on path',type='state',actor='e1',patients=['e38'],factuality='desired',roles={'patient':[169],'location':[172]})
E('bank_slippery',176,'bank is slippery',type='state',patients=['e26'],roles={'patient':[174]})
M('shallow',182,'action','Gardener refers to narrator-established shallow pond; local report remains attributed.')
U('safety_warning',176,'e4','p8','e1','warning',primary=False,scope='s0')
M('feet_path_instruction',184,'action','Mina promises the same instructed action through ellipsis.')
U('promise_path',186,'e1','p7','e4','promise',roles={'actor':[185]})
E('loan',189,'Alvarez hands net to Mina',type='transfer',actor='e4',patients=['e20'],recipient='e1',roles={'actor':[187,188],'recipient':[190],'patient':[192]})
E('handle_height',196,'handle is almost as tall as Mina',type='state',patients=['e21'],roles={'patient':[195],'comparison':[201]})
E('hoop_capacity',210,'hoop is wide enough for heap of leaves',type='state',patients=['e22'],roles={'patient':[205]})
E('catch_capacity',213,'net catches a heap of leaves',patients=['e49'],instruments=['e20'],factuality='hypothetical',roles={'patient':[216,218]})
E('theo_walk_beside',220,'Theo walks beside Mina',type='move',actor='e2',roles={'actor':[219],'landmark':[222]})
E('carry_net',225,'Mina carries net to level gravel',type='move',actor='e1',patients=['e20'],roles={'actor':[224],'patient':[226],'destination':[230,232]})
E('location_request',233,'Theo tells Mina boat location',type='speak',actor='e2',recipient='e1',factuality='desired',roles={'recipient':[234],'topic':[237]})
U('ask_location',240,'e1','p9','e2','request_information',roles={'actor':[239]})
E('left_reeds',242,'boat is just left of reed clump',type='state',patients=['e6'],roles={'landmark':[247]})
U('location_answer',242,'e2','p10','e1','location_answer',primary=False,scope='s0')
E('lower1',249,'Mina lowers hoop toward water',type='move',actor='e1',patients=['e22'],roles={'actor':[248],'patient':[251]})
E('skim_surface',254,'hoop skims water surface',type='move',patients=['e22'],roles={'patient':[253],'surface':[256]})
E('push_forward1',258,'Mina pushes hoop toward boat',type='move',actor='e1',patients=['e22'],roles={'patient':[259],'goal':[262]})
E('wind_nudge',265,'wind nudges boat away',type='move',patients=['e6'],roles={'causer':[264],'patient':[267,268]})
E('reach_far',271,'Mina reaches farther with net',type='move',actor='e1',instruments=['e20'],roles={'actor':[270]})
E('keep_shoes',273,'Mina keeps shoes planted on dry path',type='state',actor='e1',patients=['e39'],roles={'patient':[275],'location':[280]})
E('hoop_under',284,'hoop slides beneath boat',type='move',patients=['e22'],roles={'patient':[283],'landmark':[287]})
E('snag',289,'net hoop snags on submerged willow branch',type='state',patients=['e22'],roles={'patient':[283]},support=[289,308,310,315])
E('arms_jolt',296,'Mina arms jolt',type='move',patients=['e40'],roles={'patient':[295]})
E('handle_bow',299,'net handle bows over water',type='state',patients=['e21'],roles={'patient':[298],'landmark':[302]})
M('snag',310,'action','Explicit submerged-branch explanation of the same snag, not a second capture.')
E('pull_requested',316,'Mina pulls snagged net',actor='e1',patients=['e20'],factuality='desired')
U('pull_shout',318,'e2','p11','e1','command',roles={'actor':[317]})
M('drift_far',320,'action','Theo reports ongoing boat departure, not a net departing.')
U('away_exclaim',320,'e2','p12','e1','concern',primary=False,scope='s0')
E('step_edge',323,'Theo steps toward edge',type='move',actor='e2',roles={'actor':[322],'direction':[329]})
E('catch_sleeve',331,'Mina catches Theo sleeve',actor='e1',patients=['e41'],roles={'actor':[330],'patient':[333]})
E('theo_stay_request',334,'Theo stays on path',type='state',actor='e2',factuality='desired',roles={'location':[337]})
U('theo_stay_speech',339,'e1','p13','e2','instruction',roles={'actor':[338]})
E('mean_it',341,'Mina is serious about path instruction',type='state',actor='e1',roles={'actor':[340]})
E('theo_stop',344,'Theo stops approaching edge',type='move',actor='e2',roles={'actor':[343]})
E('boat_bob',347,'boat bobs farther away',type='move',patients=['e6'],roles={'patient':[346],'reference_group':[350]})
E('sail_flicker',354,'sail flickers between reeds',type='state',patients=['e7'],roles={'patient':[353],'occluder':[357]})
E('tighten_grip',359,'Mina tightens grip on handle',actor='e1',patients=['e42'],roles={'actor':[358],'patient':[361],'grasped_object':[364]})
E('yank_option',367,'Mina yanks snagged net hard',actor='e1',patients=['e20'],factuality='hypothetical',roles={'actor':[366]})
E('free_by_yank',371,'Mina frees hoop by yanking',actor='e1',patients=['e22'],factuality='hypothetical',roles={'actor':[369],'patient':[373]})
E('break_risk',377,'Mina breaks net while yanking',actor='e1',patients=['e20'],factuality='hypothetical',roles={'actor':[374],'patient':[380]})
E('cause_crumble',382,'Mina yanking causes bank edge to crumble',patients=['e26'],factuality='hypothetical',roles={'patient':[385]})
E('crumble_risk',386,'bank edge crumbles under Mina shoes',type='state',patients=['e26'],factuality='hypothetical',roles={'patient':[385],'load':[389]})
E('not_pull',392,'Mina pulls the currently snagged net',actor='e1',patients=['e20'],factuality='negated',roles={'actor':[390]})
U('refuse_pull',394,'e1','p18','e2','refusal',roles={'actor':[393]})
U('boat_objection',397,'e2','p12','e1','interrupted_objection',primary=False,scope='s0')
E('know_concern',399,'Mina knows boat is drifting away',type='state',actor='e1',roles={'actor':[398]})
U('acknowledge',399,'e1','p12','e2','acknowledgment',primary=False,scope='s0')
E('ease_handle',401,'Mina eases handle downward',type='move',actor='e1',patients=['e21'],roles={'actor':[400],'patient':[403]})
E('handle_rest',407,'handle rests against gravel',type='state',patients=['e21'],roles={'patient':[406],'landmark':[410]})
E('free_net_plan',414,'Mina frees net first',actor='e1',patients=['e20'],factuality='desired',roles={'actor':[411],'patient':[416]})
E('follow_plan',420,'Mina and Theo follow boat from path',type='move',actor='e5',patients=['e6'],factuality='desired',roles={'actor':[419],'patient':[422],'route':[425]})
U('plan_steps',414,'e1','p19','e2','announce_plan',primary=False,scope='s0')
E('wind_push_outlet',428,'wind pushes boat beyond reeds toward outlet',type='move',patients=['e6'],roles={'causer':[427],'patient':[430,431],'waypoint':[434],'direction':[440]})
E('watch_drift',442,'Theo watches boat depart',type='perceive',actor='e2',patients=['e6'],roles={'actor':[441],'patient':[443]})
M('wind_push_outlet',444,'action','Perception complement describes the same boat motion.')
E('fingers_cord',447,'Theo fingers curl around blue cord',type='state',patients=['e43'],roles={'patient':[446],'grasped_object':[451]})
E('brought_cord',453,'Theo earlier brought blue cord',type='move',actor='e2',patients=['e44'],roles={'actor':[452],'patient':[451]})
E('tether_purpose',455,'Theo uses cord as tether',actor='e2',patients=['e44'],factuality='desired',roles={'purpose':[458]})
E('thought_calm',461,'Theo earlier thought pond calm enough without tether',type='state',actor='e2',roles={'experiencer':[459]})
E('calm_belief',464,'pond is calm enough without tether',type='state',patients=['e11'],factuality='reported',roles={'patient':[463]})
E('study_handle',470,'Mina studies net handle',type='perceive',actor='e1',patients=['e21'],roles={'actor':[469],'patient':[473]})
M('snag',477,'action','Recall of same snag before choosing release movement.')
M('push_forward1',481,'action','Recall of the forward push that preceded same snag.')
E('step_side',485,'Mina steps sideways along path',type='move',actor='e1',roles={'actor':[484],'route':[491]})
E('push_release',494,'Mina gently pushes handle away from shore',type='move',actor='e1',patients=['e21'],roles={'patient':[496],'reference_landmark':[499]})
E('hoop_shift',502,'hoop shifts underwater',type='move',patients=['e22'],roles={'patient':[501]})
E('turn_handle',505,'Mina turns handle a little',type='move',actor='e1',patients=['e21'],roles={'actor':[504],'patient':[507]})
E('draw_release',511,'Mina draws handle back',type='move',actor='e1',patients=['e21'],roles={'patient':[512]})
E('hoop_free',516,'hoop slides free from branch',type='state',patients=['e22'],roles={'patient':[515]})
E('exhale',519,'Mina lets out held breath',actor='e1',roles={'actor':[518]})
E('not_notice_breath',525,'Mina notices holding her breath',type='perceive',actor='e1',factuality='negated',roles={'actor':[523]})
E('hold_breath',528,'Mina holds her breath before release',type='state',actor='e1',roles={'actor':[526]})
E('lift_net',530,'Mina lifts freed net clear of water',type='move',actor='e1',patients=['e20'],roles={'actor':[529],'patient':[532],'source':[536]})
E('inspect_net',538,'Mina checks net',type='perceive',actor='e1',patients=['e20'],roles={'patient':[539]})
E('twig_in_mesh',543,'willow twig lies in net mesh',type='state',patients=['e19'],roles={'patient':[542],'container':[546]})
E('pluck_twig',548,'Mina plucks twig from mesh',type='move',actor='e1',patients=['e19'],roles={'actor':[547],'patient':[549]})
E('set_twig',552,'Mina sets twig on gravel',type='move',actor='e1',patients=['e19'],roles={'patient':[553],'destination':[556]})
U('now_walk_speech',559,'e1','p23','e2','decision',roles={'actor':[558]})
E('walking_decision',561,'Mina and Theo walk',type='move',actor='e5',factuality='desired',roles={'actor':[560]})
E('follow_actual',563,'Mina and Theo follow curved path around pond',type='move',actor='e5',roles={'actor':[562],'route':[566],'landmark':[569]})
E('track_boat',571,'Theo keeps eyes on boat',type='perceive',actor='e2',patients=['e6'],roles={'actor':[570],'effector':[573],'patient':[576]})
E('call_updates',577,'Theo calls boat position changes',type='speak',actor='e2',recipient='e1')
E('gusts_spin',582,'gusts spin boat during following',type='move',patients=['e6'],roles={'causer':[581],'patient':[583]})
E('reeds_hide',587,'reeds hide boat from view intermittently',type='state',patients=['e6'],roles={'occluder':[586],'patient':[588]})
E('arrive_outlet',591,'path leads Mina and Theo to outlet',type='move',actor='e5',roles={'route':[590],'actor':[592],'destination':[596]})
E('water_calm',601,'outlet water is calm',type='state',patients=['e12'],roles={'patient':[599]})
E('drift_corner',606,'boat drifts into sheltered outlet corner',type='move',patients=['e6'],roles={'patient':[603,604],'destination':[610]})
E('bump_stones',612,'boat bumps softly against stones',type='move',patients=['e6'],roles={'landmark':[616]})
U('near_report',619,'e2','p24','e1','location_report',roles={'actor':[618]})
E('boat_close',620,'boat is close to edge',type='state',patients=['e6'],roles={'landmark':[623]})
E('not_equivalent',625,'proximity is equivalent to reachability',type='state',factuality='negated')
U('reachability_caution',631,'e1','p26','e2','caution',roles={'actor':[630]})
E('stand_back',633,'Mina stands well back on path',type='state',actor='e1',roles={'actor':[632],'location':[638]})
E('lower2',640,'Mina lowers net slowly at outlet',type='move',actor='e1',patients=['e20'],roles={'patient':[642]})
M('lower2',646,'action','Moved slowly specifies the same deliberate lowering, not another ungrounded action.')
E('watch_outlet',649,'Theo watches beside Mina',type='perceive',actor='e2',roles={'actor':[648],'landmark':[652]})
E('left_guidance',655,'Mina moves net left',type='move',actor='e1',patients=['e20'],factuality='desired')
U('guide_left_speech',657,'e2','p27','e1','guidance',roles={'actor':[656]})
E('down_guidance',659,'Mina moves net down',type='move',actor='e1',patients=['e20'],factuality='desired')
U('guide_down_speech',659,'e2','p28','e1','guidance',primary=False,scope='s0')
E('hoop_around',662,'hoop slips around boat',type='move',patients=['e22'],roles={'patient':[661],'enclosed_object':[665]})
E('not_touch_sail',667,'hoop touches sail during capture',patients=['e7'],instruments=['e22'],factuality='negated',roles={'patient':[669]})
E('draw_boat',671,'Mina draws net with boat toward shore',type='move',actor='e1',patients=['e20','e6'],roles={'actor':[670],'patient':[672],'direction':[674]})
E('net_stones',684,'net reaches outlet stones',type='move',patients=['e20'],roles={'patient':[683],'destination':[686]})
E('pick_boat',688,'Theo picks boat from net mesh',type='obtain',actor='e2',patients=['e6'],roles={'actor':[687],'patient':[690],'source':[694]})
E('hold_hull',695,'Theo holds boat by hull',type='state',actor='e2',patients=['e6'],roles={'patient':[696],'grasped_part':[699]})
E('sail_upright',705,'sail remains upright',type='state',patients=['e7'],roles={'patient':[702]})
E('drops_patch',710,'few drops cling to blue patch',type='state',patients=['e50'],roles={'patient':[709],'surface':[714]})
E('alvarez_wait',718,'Alvarez waits where children left him',type='state',actor='e4',roles={'actor':[715,716]})
E('earlier_leave',722,'Mina and Theo earlier leave Alvarez location',type='move',actor='e5',roles={'actor':[720],'left_person':[723]})
E('return_net',725,'Mina returns net to Alvarez',type='transfer',actor='e1',patients=['e20'],recipient='e4',roles={'actor':[724],'patient':[727]})
E('twig_handle',732,'willow twig is tucked through net handle',type='state',patients=['e19'],roles={'patient':[731],'carrier':[735]})
U('mina_thanks',739,'e1','p33','e4','thanks',roles={'actor':[738],'addressee':[737]})
M('return_net',743,'action','Alvarez thanks Mina for actual same completed net return.')
U('alvarez_thanks',750,'e4','p30','e1','thanks',roles={'actor':[749],'addressee':[741]})
E('tie_cord',752,'Theo ties cord around boat stern with double knot',actor='e2',patients=['e44'],roles={'actor':[751],'patient':[755],'attachment':[759],'result':[766]})
E('launch2',769,'Theo sets June Bug afloat again',type='move',actor='e2',patients=['e6'],roles={'actor':[768],'patient':[771,772]})
E('hold_cord',776,'Mina holds other end of cord',type='state',actor='e1',patients=['e45'],roles={'actor':[775],'patient':[779]})
E('guide_boat',785,'Theo guides tethered boat away from stones',type='move',actor='e2',patients=['e6'],instruments=['e44'],roles={'actor':[784],'patient':[787],'reference_landmark':[791]})
E('wind_sail',794,'breeze catches sail',patients=['e7'],roles={'causer':[793],'patient':[797]})
E('boat_circle',800,'boat makes bright little circle on water',type='move',patients=['e6'],roles={'patient':[799],'path':[804],'surface':[809]})
E('cord_between',814,'cord extends gently between Theo and Mina hands',type='state',patients=['e44'],roles={'patient':[813],'endpoints':[818,820]})

# Contextual grammar and reference features; lexical decisions above are explicit.
a.entity('e53','Theo eyes','body_part_group',[573])
a.entities['e20']['mentions'].append(672)
F(672,entity_id='e20',entity='net',entity_name='Mr. Alvarez net',mention_form='personal_pronoun',
  evidence=[661,665,670,671,672,683,684,690,694],note='It is resolved to the net carrying the boat; both net and boat are patients of the draw event, without merging their identities.')
a.proposition('p33','Mr. Alvarez has lent Mina the net.',[140,144,165,189,190,192],scope_id='s0')
a.proposition('p34','Where is the boat now?', [233,235,237,238],scope_id='q8')
a.proposition('p35','Mina is holding her breath.',[526,527,528],scope_id='s0')
F(739,utterance_content_id='p33')
for w in [0,11,17,22,28,48,55,67,70,76,79,84,89,92,112,125,132,157,171,173,179,191,204,207,228,236,250,255,261,263,266,278,281,286,297,301,305,307,328,336,345,356,363,372,383,396,402,409,415,421,424,426,429,433,437,449,462,471,474,490,495,500,506,514,531,535,555,564,568,575,589,594,598,602,608,615,622,626,637,641,660,664,682,685,689,693,698,700,712,729,734,753,757,770,777,781,786,790,792,795,798,806,811]:F(w,determiner_kind='definite_article',definiteness='definite')
# w228 is 'a'; repaired below from the explicitly tagged source.
for w in [32,37,95,102,214,228,291,312,324,457,486,508,521,540,580,585,653,679,707,763,801]:F(w,determiner_kind='indefinite_article',definiteness='indefinite')
for w in [8,42,59,145,193,274,332,351,360,388,445,572,668,726]:F(w,determiner_kind='possessive',definiteness='definite',possessive_construction='possessive_determiner')
for w in [25,114,294,379,438,758,817,820]:F(w,possessive_construction='s_genitive',grammatical_case='genitive')
F(820,phrase_has_elision=True,possessive_construction='independent_s_genitive',reference_metonymic_link={'referent':'e47','possessor':'e1','relation':'elided_hands_of'})
F(244,determiner_kind='demonstrative',definiteness='definite')
F([643,760],determiner_kind='demonstrative',definiteness='definite')
F(168,determiner_kind='dual_quantifier',cardinal_value=2)
F([66,215],determiner_kind='totality_quantifier')
F([96,708],determiner_kind='small_quantity_quantifier')
F([675,747],cardinal_value=1)
F(765,lexical_sense_id='double_knot_configuration')
F([97,113,137,169,218,247,275,295,357,389,434,446,573,616,686,709,791,818,820],grammatical_number='plural')
F([128,183,234,340,390,398,411],grammatical_person=1,grammatical_number='singular',mention_form='personal_pronoun')
F([419,560],grammatical_person=1,grammatical_number='plural',split_antecedent_ids=['e1','e2'])
F([350,562,592,720],grammatical_number='plural',split_antecedent_ids=['e1','e2'],mention_form='personal_pronoun')
F([737,741],grammatical_person=2,grammatical_case='objective',mention_form='personal_pronoun')
F([46,152,190,222,234,350,592,652,723],grammatical_case='objective')
for w,expansion in [(64,['it','will']),(117,['it','is']),(128,['I','will']),(319,['it','is']),(390,['I','am']),(411,['I','am']),(419,['we','will']),(452,['he','had']),(524,['had','not']),(625,['is','not'])]:F(w,contraction_expansion=expansion)
F([72,98,105,109,142,149,164,183,190,201,222,224,226,234,248,253,259,322,338,340,342,350,366,369,374,393,398,400,406,443,459,468,479,482,484,504,512,523,526,529,539,545,547,549,553,558,560,562,583,588,592,632,645,652,656,668,672,696,720,723,737,738,741,744,749,768],mention_form='personal_pronoun')
F([3,4,25,29,30,51,63,74,87,114,122,130,131,139,154,185,187,188,219,239,267,268,270,294,317,330,343,358,378,379,430,431,441,469,518,570,603,604,618,630,648,670,687,715,716,724,751,771,772,775,784,817,820],mention_form='proper_name')
for mod,head in [(133,134),(126,127),(282,283),(314,315),(439,440),(472,473),(541,542),(595,596),(730,731),(807,809)]:F(mod,dependency_relation='nominal_modifier',syntactic_governor_id=a.anchor(head))
F([26,146,147,194,292,313,565,609,808],adjective_degree='positive')
for w in [313]:a.words[w].pop('adjective_degree',None)
F([85,160,272,348],adverb_degree='comparative')
a.words[85].pop('adverb_degree',None);F(85,adjective_degree='positive')
F([6,14,18,23,33,40,56,121,176,182,199,210,229,279,325,352,384,450,465,517,533,601,620,624,627,629,701,705,713,754,764,773,796,802,803,812],adjective_degree='positive')
for w,dim,direction in [(6,'depth','shallow'),(146,'length','long'),(199,'height','tall'),(210,'width','wide'),(803,'size','small')]:F(w,lexical_scale_dimension=dim,lexical_scale_direction=direction)
F([5,10,20,31,44,45,52,61,73,75,88,99,104,108,116,123,135,140,150,165,186,189,196,202,209,220,225,240,249,254,258,265,271,284,289,296,299,309,318,323,331,339,344,347,359,367,394,401,407,428,442,447,453,460,461,464,470,476,477,480,485,494,502,505,511,516,519,524,527,530,538,543,548,552,559,563,571,582,587,591,600,605,612,619,631,633,640,646,649,657,662,671,684,688,703,710,717,721,725,739,750,752,769,776,785,794,800],verb_form='finite',tense='past')
F([175,181,238,341,399,561,625],verb_form='finite',tense='present')
F([35,276,310,313,453,461,477,525,606,722,732,814],verb_form='past_participle')
for w in [453,461,477,525,606,722]:a.words[w].pop('tense',None)
F([35,276,313],participial_function='nominal_or_result_state_modifier')
F([110,118,136,159,273,320,354,392,412,481,528,577,667,695,718,743],verb_form='present_participle')
F([65,78,82,129,144,167,213,233,316,334,371,377,382,386,414,420,444,455,736,740],verb_form='bare')
for marker,head,controller in [(53,54,'e2'),(119,120,'e6'),(212,213,None),(413,414,'e1'),(454,455,'e2')]:
    F(marker,constituent_category='infinitive_marker',syntactic_governor_id=a.anchor(head))
    fields={'verb_form':'infinitive','infinitive_marker_id':a.anchor(marker)}
    if controller:fields['subject_controller_id']=controller
    F(head,**fields)
F(47,verb_form='bare',subject_controller_id='e2')
for head,aux in [(136,135),(481,480),(528,527),(718,717)]:F(head,aspect='progressive',progressive_auxiliary_id=a.anchor(aux),auxiliary_chain=['be'])
for head,aux in [(45,44),(310,309),(453,452),(461,460),(477,476),(525,524),(606,605),(722,721)]:F(head,aspect='perfect',perfect_auxiliary_id=a.anchor(aux),auxiliary_chain=['have'])
F(45,verb_form='past_participle');a.words[45].pop('tense',None)
F([82,167,233,316,334],imperative_subject_status='understood_second_person')
F(184,verb_phrase_ellipsis=True,modal_auxiliary_class='modal',modal_base={'kind':'promissory_commitment','holder':'e1','content_id':'p7'})
F(143,modal_auxiliary_class='modal',modal_base={'kind':'permission_request','holder':'e1','content_id':'p6'})
F(370,modal_auxiliary_class='modal',modal_base={'kind':'conditional_possibility','condition_id':'p14','content_id':'p15'})
F(375,modal_auxiliary_class='modal',modal_base={'kind':'alternative_risks','condition_id':'p14','content_ids':['p16','p17']})
F(81,modal_base={'kind':'tentative_suggestion','holder':'e1','content_id':'p3'})
F([118,412],lexical_idiom_reading={'expression':'be_going_to','meaning':'prospective'})
F(391,proposition_polarity='negative',negation_scope_id='p11')
F(524,proposition_polarity='negative',negation_scope_id='p22')
F(625,proposition_polarity='negative',negation_scope_id='p25')
F(666,proposition_polarity='negative',negation_scope_id='p29',subordinator_type='without_nonfinite')
F(467,prepositional_object_id='e44',lexical_sense_id='absence_of_tether_in_believed_setup')
F([242,397,557,617,620,655,659],sentence_fragment_type='contextual_utterance_fragment')
F(397,sentence_fragment_type='interrupted_utterance')
F(342,propositional_antecedent_id='p13')
for w,typ in [(58,'temporal_before'),(141,'embedded_interrogative'),(178,'locative'),(200,'comparative'),(223,'temporal_as'),(235,'embedded_location_question'),(252,'temporal_until'),(365,'conditional'),(405,'temporal_until'),(478,'temporal_while'),(579,'temporal_whenever'),(597,'relative_locative'),(681,'temporal_when'),(719,'relative_locative'),(783,'temporal_while')]:F(w,subordinator_type=typ)
for w,rel in [(7,'contrast'),(16,'addition'),(50,'addition'),(107,'addition'),(166,'qualification'),(203,'addition'),(257,'addition'),(288,'unexpected_outcome'),(376,'addition'),(381,'alternative_consequences'),(395,'objection'),(435,'addition'),(537,'addition'),(551,'addition'),(584,'alternative_trigger'),(611,'addition'),(639,'addition'),(819,'addition')]:F(w,discourse_relation_kind=rel)
for w,rel in [(58,'before'),(101,'then'),(155,'then'),(223,'overlap'),(252,'until'),(405,'until'),(417,'first'),(418,'then'),(478,'overlap'),(492,'then'),(510,'then'),(557,'now'),(579,'whenever'),(658,'now'),(681,'when'),(767,'then'),(783,'overlap')]:F(w,temporal_signal_relation=rel)
F(63,time_expression_id='time_sunday_visit',temporal_anchor_unresolved=True)
F(61,temporal_reference_shift={'morphology':'past','reference':'anticipated_visit_after_testing'},evidence=[52,54,58,61,63],note='Grandfather visit is future relative to desired test; visited is not an asserted completed visit.')
F(97,measure_unit='second',temporal_granularity='second',quantity_approximation_cue='few_unspecified')
F(677,measure_unit='inch',quantity_distribution_cue='one_inch_per_step')
F(774,temporal_phase_cue='repeated_launch',event_iteration=B('e6',{'earlier_event_id':EV['launch1'],'new_event_id':EV['launch2']}))
F(704,temporal_phase_cue='continued_upright_state')

SUBJECTS={
'e1':[75,82,123,129,140,144,167,184,186,225,240,249,258,271,273,331,339,341,359,367,371,377,382,392,394,399,401,407,414,470,481,485,494,505,511,519,525,528,530,538,548,552,559,631,633,640,646,671,725,739,776],
'e2':[47,52,54,73,88,233,318,323,334,344,442,453,455,461,571,577,619,649,657,688,695,752,769,785],
'e3':[45,61], 'e4':[136,150,165,189,718,750], 'e5':[420,561,563,722],
'e6':[31,65,99,110,120,159,238,320,347,444,606,612,620,800],
'e7':[35,354,705], 'e11':[6,78,182,464], 'e12':[10,601], 'e13':[20],
'e21':[196,299,407], 'e22':[210,254,284,289,310,477,502,516,662,667],
'e31':[265,428,794], 'e32':[104,108], 'e33':[582], 'e34':[587], 'e37':[116],
'e40':[296], 'e26':[176,386], 'e43':[447], 'e19':[543,732], 'e20':[684], 'e25':[591], 'e50':[710], 'e44':[814],
}
for entity,words in SUBJECTS.items():F(words,grammatical_subject_id=entity)
# The breeze, rather than the pond, is the subject of wrinkle.
F(78,grammatical_subject_id='e31')
for w,eid in [(47,'e9'),(54,'e8'),(75,'e31'),(88,'e6'),(104,'e6'),(108,'e6'),(129,'e4'),(136,'e48'),(144,'e20'),(167,'e38'),(189,'e20'),(213,'e49'),(225,'e20'),(249,'e22'),(258,'e22'),(265,'e6'),(273,'e39'),(331,'e41'),(359,'e42'),(371,'e22'),(377,'e20'),(382,'e26'),(392,'e20'),(401,'e21'),(414,'e20'),(420,'e6'),(428,'e6'),(442,'e6'),(453,'e44'),(455,'e44'),(470,'e21'),(481,'e22'),(494,'e21'),(505,'e21'),(511,'e21'),(530,'e20'),(538,'e20'),(548,'e19'),(552,'e19'),(563,'e25'),(571,'e53'),(582,'e6'),(587,'e6'),(591,'e5'),(640,'e20'),(667,'e7'),(671,'e20'),(688,'e6'),(695,'e6'),(722,'e4'),(725,'e20'),(752,'e44'),(769,'e6'),(776,'e45'),(785,'e6'),(794,'e7')]:F(w,grammatical_object_id=eid)
F(189,indirect_object_id='e1')
F(233,indirect_object_id='e1')
F(273,small_clause_kind='NP_plus_participial_state')
F([75,442],perception_complement_syntax='NP_plus_bare_infinitive')
for w,eid in [(2,'e15'),(21,'e14'),(36,'e8'),(69,'e16'),(83,'e36'),(91,'e12'),(111,'e17'),(124,'e25'),(151,'e1'),(153,'e2'),(156,'e6'),(170,'e25'),(206,'e24'),(217,'e49'),(221,'e1'),(227,'e27'),(231,'e27'),(243,'e17'),(246,'e17'),(260,'e6'),(277,'e25'),(285,'e6'),(300,'e12'),(304,'e35'),(311,'e18'),(327,'e26'),(335,'e25'),(349,'e5'),(355,'e17'),(362,'e21'),(387,'e39'),(408,'e27'),(423,'e25'),(432,'e17'),(436,'e28'),(448,'e44'),(489,'e25'),(498,'e26'),(534,'e12'),(544,'e23'),(554,'e27'),(567,'e11'),(574,'e6'),(593,'e28'),(607,'e29'),(614,'e30'),(621,'e26'),(636,'e25'),(651,'e1'),(663,'e6'),(673,'e26'),(692,'e23'),(697,'e9'),(711,'e8'),(733,'e21'),(756,'e10'),(762,'e51'),(780,'e44'),(789,'e30'),(805,'e12')]:F(w,prepositional_object_id=eid)

# Grounded physical state, causal bindings and time-local possession.
F(1,spatial_configuration=B('e11',{'landmark':'e15','relation':'in'}))
F(6,attributes=[{'name':'water_depth','value':'shallow'}])
F(12,appearance_color=B('e12',{'color_comparison':'strong_tea'}),evidence=[9,10,12,14,15,807,808,809],note='Tea is the color comparison; pond water is not tea, and no potability or exact shade is inferred.')
F(18,attributes=[{'name':'surface_material','value':'muddy'}])
F(20,object_concealment=B('e13','hidden_beneath_duckweed'),spatial_configuration=B('e13',{'landmark':'e14','relation':'beneath'}),lexical_sense_id='disappear_from_view')
for w,e,value in [(23,'e14','green'),(33,'e7','yellow'),(40,'e8','blue'),(352,'e7','yellow'),(450,'e44','blue'),(701,'e7','yellow'),(713,'e8','blue'),(754,'e44','blue'),(796,'e7','yellow'),(812,'e44','blue')]:F(w,appearance_color=B(e,value))
F(26,material_composition=B('e6','wood'))
F(194,material_composition=B('e21','wood'))
F(41,material_composition=B('e8','cloth'))
F(38,object_shape=B('e8','square'))
F(35,object_attachment=B('e8',{'attached_to':'e7','function':'patch'}),evidence=[34,35,38,41,56,57],note='Existing patch state is explicit; its original tear, repair actor and repair method are not reconstructed.')
F(25,possession_owner=B('e6',{'owner':'e2'}))
for w,part,whole in [(9,'e12','e11'),(19,'e13','e11'),(34,'e7','e6'),(49,'e9','e6'),(60,'e3','e2'),(115,'e37','e2'),(169,'e38','e1'),(195,'e21','e20'),(205,'e22','e20'),(208,'e24','e21'),(256,'e35','e11'),(295,'e40','e1'),(333,'e41','e2'),(440,'e28','e11'),(446,'e43','e2'),(546,'e23','e20'),(573,'e53','e2'),(610,'e29','e28'),(759,'e10','e6'),(779,'e45','e44'),(818,'e46','e2'),(820,'e47','e1')]:F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
# Kinship is not physical part-whole.
a.words[60].pop('part_whole_relation',None)
F(60,attributes=[{'name':'kinship','value':'grandfather_of_Theo'}])
F(45,event_divided_labor=B('e2',{'helper':'e3','assisted_actor':'e2','assisted_event_id':EV['sand']}))
F(65,motion_destination=B('e6',{'landmark_id':'e16','role':'predicted_destination'},'q1','attributed_claim',factuality='hypothetical'))
F(88,motion_destination=B('e6',{'landmark_id':'e12','role':'actual_destination'}))
F(104,event_causer=B('e6',{'causer':'e32','event_id':EV['gust_spin']}))
F(108,motion_trajectory_phase=B('e6',{'landmark':'e17','phase':'approaching'}),event_causer=B('e6',{'causer':'e32','event_id':EV['gust_send']}))
F(121,object_attachment=B('e6',{'possible_attachment':'e17','state':'stuck'},'q3','attributed_claim',factuality='hypothetical'),evidence=[117,118,120,121,289,310,347],note='Theo predicts the boat will become stuck; the later actual snag affects the net hoop, not the boat.')
F(123,spatial_configuration=B('e1',{'landmark':'e25','relation':'on'}))
F(145,possession_owner=B('e20',{'owner':'e4'}))
F(189,possession_holder=B('e20',{'holder':'e1'}),possession_borrower=B('e20',{'borrower':'e1'}),possession_lender=B('e20',{'lender':'e4'}),transfer_kind=B('e20','temporary_loan'),transfer_completion=B('e20',{'completed':True}),transfer_source=B('e20',{'source':'e4'}),transfer_recipient=B('e20',{'recipient':'e1'}))
F(199,quantity_comparison={'left':'e21','right':'e1','dimension':'height','relation':'almost_equal'})
F(210,containment_capacity_fit=B('e20',{'contents':'e49','fits':True,'basis':'hoop_width'}),evidence=[205,210,211,213,215,216,218],note='Stated capacity for a heap of leaves, not actual collection or presence of these hypothetical leaves.')
F(220,spatial_configuration=B('e2',{'landmark':'e1','relation':'beside'}))
F(225,motion_destination=B('e1',{'landmark_id':'e27','role':'destination'}),possession_holder=B('e20',{'holder':'e1'}))
F(229,attributes=[{'name':'ground_grade','value':'level'}])
F(242,spatial_configuration=B('e6',{'landmark':'e17','relation':'left_of'},'q9','attributed_claim'),evidence=[241,242,245,247],note='Relative left is reported by Theo. Exact observer coordinate frame is not independently supplied.')
F(254,spatial_contact=B('e22',{'touches':'e35','mode':'skim'}))
F(265,event_causer=B('e6',{'causer':'e31','event_id':EV['wind_nudge']}))
F(273,spatial_configuration=B('e39',{'landmark':'e25','relation':'planted_on'}))
F(279,object_moisture=B('e25','dry'))
F(284,spatial_configuration=B('e22',{'landmark':'e6','relation':'beneath'}))
F(289,object_attachment=B('e22',{'attached_to':'e18','mode':'snagged'}),event_state_change=B('e22',{'before':'moving_freely','after':'snagged_on_branch','event_id':EV['snag']}),evidence=[283,284,289,308,310,313,315],note='Later explanation identifies the existing snag; no second snag, stuck boat, or recovered boat is created here.')
F(296,causal_parent=B('e40',{'cause':EV['snag'],'effect':EV['arms_jolt']},status='candidate'),evidence=[289,292,293,294,295,296],note='Immediate mechanical sequence supports a candidate snag-to-arm-jolt causal relation.')
F(299,object_shape=B('e21','bowed'),spatial_configuration=B('e21',{'landmark':'e12','relation':'over'}),evidence=[298,299,377,380,747,748],note='Handle actually bows. This does not establish a broken net, and the later intact-return claim does not assert the exact original straightness was restored.')
F(313,spatial_configuration=B('e18',{'landmark':'e12','relation':'submerged_in'}))
F(331,event_contact_mode=B('e41',{'agent':'e1','mode':'grasp'}))
F(344,causal_parent=B('e2',{'cause_events':[EV['catch_sleeve'],EV['theo_stay_speech']],'effect':EV['theo_stop']},status='candidate'),evidence=[323,331,334,341,344],note='Following stop is consistent with physical intervention and instruction; relative causal contribution is not specified.')
F(347,spatial_distance_band=B('e6',{'landmark':'e5','distance_change':'farther'}))
F(354,spatial_occlusion=B('e7',{'occluder':'e17','visibility':'intermittent_between_reeds'}))
F(359,event_contact_mode=B('e21',{'agent':'e1','mode':'tightened_grip'}))
F(377,object_integrity=B('e20','broken','s6','asserted',factuality='hypothetical'),causal_scope=B('e20',{'cause':'p14','possible_effect':'p16','scope':'conditional_risk'} ,'s6'),evidence=[365,367,370,374,375,377,380],note='Yanking and breakage are considered possibilities. No break event or damage fact is added to the actual world.')
F(386,object_stability=B('e26',{'possible_failure':'crumble_under_load'},'s6','asserted',factuality='hypothetical'),evidence=[365,367,375,381,382,385,386,389],note='Bank crumbling is an alternative risk under forceful yanking, not a completed collapse.')
F(407,spatial_contact=B('e21',{'touches':'e27','mode':'rests_against'}))
F(428,event_causer=B('e6',{'causer':'e31','event_id':EV['wind_push_outlet']}),motion_trajectory_phase=B('e6',{'landmark':'e28','phase':'approaching'}),motion_waypoint=B('e6',{'landmark_id':'e17','relation':'past'}))
F(447,possession_holder=B('e44',{'holder':'e2'}),spatial_contact=B('e43',{'touches':'e44'}))
F(453,temporal_reference_shift={'event_id':EV['brought_cord'],'phase':'before_first_launch'})
F(455,event_goal_role=B('e2',{'event_id':EV['brought_cord'],'goal_event_id':EV['tether_purpose'],'purpose':'use_cord_as_tether'},'s7',factuality='desired'))
F(485,motion_route=B('e1',{'landmark_id':'e25','role':'actual_route'}),event_manner=B('e1',{'event_id':EV['step_side'],'manner':'sideways'}))
F(494,motion_trajectory_phase=B('e21',{'landmark':'e26','phase':'away_from'}),event_manner=B('e1',{'event_id':EV['push_release'],'manner':'gently'}))
F(502,spatial_configuration=B('e22',{'landmark':'e12','relation':'underwater'}))
F(505,motion_path_shape=B('e21',{'event_id':EV['turn_handle'],'interpretation':'small_rotation'}))
F(511,event_manner=B('e21',{'event_id':EV['draw_release'],'manner':'backward'}))
F(516,object_attachment=B('e22',{'previous_attachment':'e18','attached_after':False}),event_state_change=B('e22',{'before':'snagged','after':'free','event_id':EV['hoop_free']}),causal_parent=B('e22',{'cause_events':[EV['push_release'],EV['turn_handle'],EV['draw_release']],'effect':EV['hoop_free']},status='candidate'),evidence=[494,502,505,511,516,517],note='Release follows the deliberate push-turn-draw sequence. Sequence-to-release causality is an interpretation grounded in the described mechanics, not an independently stated sufficiency law.')
F(530,motion_source=B('e20',{'landmark_id':'e12','role':'source'}))
F(543,containment_direct=B('e19',{'container':'e23'}))
F(548,motion_source=B('e19',{'landmark_id':'e23','role':'source'}),containment_contents=B('e23',{'removed':['e19'],'exhaustive':False}))
F(552,motion_destination=B('e19',{'landmark_id':'e27','role':'destination'}),spatial_support=B('e19',{'supported_by':'e27'}))
F(563,motion_route=B('e5',{'landmark_id':'e25','role':'actual_route'}),motion_collectivity=B('e5',{'companions':['e1','e2'],'coordination':'together'}))
F(565,object_shape=B('e25','curved'))
F(571,lexical_idiom_reading={'expression':'keep_eyes_on','meaning':'maintain_visual_attention'},epistemic_access_mode='visual_tracking')
F(587,spatial_occlusion=B('e6',{'observer':'e2','occluder':'e34','visibility':'intermittently_hidden'}))
F(591,motion_destination=B('e5',{'landmark_id':'e28','role':'destination'}),motion_arrival_completion=B('e5',{'arrived_at':'e28'}),lexical_sense_id='route_leads_to_location')
F(601,attributes=[{'name':'water_motion','value':'calm_at_outlet'}])
F(606,motion_destination=B('e6',{'landmark_id':'e29','role':'destination'}),spatial_region=B('e6',{'landmark':'e28','region':'e29','world':'actual'}))
F(612,motion_collision=B('e6',{'collided_with':'e30','manner':'softly'}))
F(620,spatial_distance_band=B('e6',{'landmark':'e26','distance':'close'},'q21','attributed_claim'))
F(625,lexical_sense_id='negated_equivalence_of_proximity_and_reachability',evidence=[624,625,627,629,662,671,688],note='Mina states a general distinction. No access_reachability=false is asserted for this boat; the next sequence establishes actual successful net-assisted retrieval.')
F(633,spatial_configuration=B('e1',{'landmark':'e25','relation':'well_back_on_path'}))
F(640,event_manner=B('e1',{'event_id':EV['lower2'],'manner':'slowly'}))
F(662,spatial_configuration=B('e22',{'landmark':'e6','relation':'around'}))
F(667,spatial_contact=B('e22',{'target':'e7','touching':False,'event_id':EV['not_touch_sail']}))
F(671,containment_contents=B('e20',{'contents':['e6'],'exhaustive':False}),event_manner=B('e1',{'event_id':EV['draw_boat'],'manner':'slow_careful_one_inch_steps'}))
F(684,motion_arrival_completion=B('e20',{'arrived_at':'e30'}))
F(688,motion_source=B('e6',{'landmark_id':'e23','role':'source'}),possession_holder=B('e6',{'holder':'e2'}),access_reachability=B('e6',{'actor':'e2','reachable':True,'phase':'net_at_stones'}))
F(695,event_contact_mode=B('e6',{'agent':'e2','mode':'holding','contact_part':'e9'}))
F(705,spatial_orientation=B('e7',{'orientation':'upright'}))
F(710,spatial_contact=B('e50',{'touches':'e8'}),object_moisture=B('e8','few_water_drops'))
F(725,possession_holder=B('e20',{'holder':'e4'}),transfer_kind=B('e20','loan_return'),transfer_completion=B('e20',{'completed':True}),transfer_source=B('e20',{'source':'e1'}),transfer_recipient=B('e20',{'recipient':'e4'}))
F(732,object_attachment=B('e19',{'attached_to':'e21','mode':'tucked_through'}),evidence_missing={'needed':'unreported_twig_transfer_from_gravel_to_handle'},evidence=[548,552,553,556,725,731,732,735],note='Twig was put on gravel and is later tucked through handle. Final placement is explicit; no retrieval or tucking action, actor or time is invented to fill the transition.')
F(748,object_integrity=B('e20','intact','q26','attributed_claim'),lexical_idiom_reading={'expression':'in_one_piece','meaning':'intact_return'},evidence=[740,743,744,747,748],note='Alvarez thanks Mina for intact return of his net; this refers to the net, not the boat, and does not identify the exact final handle curvature.')
F(752,object_attachment=B('e44',{'attached_to':'e10','method':'double_knot','event_id':EV['tie_cord']}))
F(764,object_connection_state=B('e51','firmly_tied'))
F(776,possession_holder=B('e45',{'holder':'e1'}))
F(785,event_instrument_binding=B('e6',{'event_id':EV['guide_boat'],'instrument_id':'e44','actor_id':'e2'}))
F(794,event_causer=B('e7',{'causer':'e31','event_id':EV['wind_sail']}))
F(800,motion_route=B('e6',{'trajectory':'circular','surface':'e12'}))
F(808,appearance_color=B('e12',{'color_comparison':'tea'}))
F(814,spatial_configuration=B('e44',{'endpoints':['e46','e47'],'relation':'drawn_between'}),evidence=[755,759,776,779,785,813,814,817,818,820],note='Closing cord joins the cooperative hand control while attached to boat stern. No second cord or extra unreported handoff is introduced.')

# Plans, information goals, belief and dialogue remain separately scoped.
F(52,goal_owner_id='e2',goal_content_id='p1',goal_status='active',goal_polarity='achieve',goal_deadline={'relation':'before','event_id':EV['future_visit']},goal_scope_bundle={'owner_id':'e2','intention_event_id':EV['want_test'],'scope_id':'s0','assertion_status':'asserted'},evidence=[52,54,57,58,61,63],note='The expressed goal is to conduct a test before the visit. This does not supply a preferred test result or establish that visiting has happened.')
F(65,belief_holder_id='e2',belief_content_id='p2',belief_certainty='confident_prediction')
F(116,affect_observer_attribution={'experiencer_id':'e2','cue':'smile_vanished','interpretation':'concern_about_boat','scope_id':'s0','assertion_status':'candidate'},evidence=[114,115,116,117,120,121],note='Loss of smile plus stuck prediction supports local concern, not a named immutable trait.')
F(129,intention_holder_id='e1',intention_content_id='p5',plan_commitment_status='announced')
F(140,request_action_id='p6',request_acceptance_status='granted_by_permission_and_handoff')
F(165,permission_grantor_id='e4',permission_recipient_id='e1',permission_content_id='p6',permission_status='granted_with_path_condition',dialogue_response_to_id=EV['request_net'])
F(167,obligation_debtor_id='e1',obligation_creditor_id='e4',obligation_content_id='p7',obligation_status='instructed')
F(186,promise_content_id='p7',promise_beneficiary_id='e4',plan_commitment_status='promised',dialogue_response_to_id=EV['permission'],evidence=[167,169,172,183,184,185,186,189],note='I will accepts the feet-on-path instruction. It is not a separate explicit promise about returning the tool or achieving the boat rescue.')
F(240,question_requested_slot='boat_location',question_answer_status='answered_by_Theo',goal_owner_id='e1',goal_content_id='p9',goal_status='active',epistemic_question_under_discussion='p34')
F(242,dialogue_response_to_id=EV['ask_location'])
F(318,request_action_id='p11',request_acceptance_status='refused_after_risk_consideration',communication_channel='shouted_speech')
F(339,request_action_id='p13',request_acceptance_status='followed_by_stop',obligation_debtor_id='e2',obligation_creditor_id='e1',obligation_content_id='p13',obligation_status='instructed')
F(341,dialogue_turn_function='reinforce_instruction',intention_strength='firm')
F(367,plan_commitment_status='considered_not_executed',plan_contingency={'if':'p14','possible_outcomes':['p15','p16','p17']},evidence=[365,367,370,371,375,377,381,386,390,391,392],note='Potential forceful yank has beneficial and harmful alternatives. Neither the yank nor any of its conditional outcomes is promoted to an actual event.')
F(394,dialogue_response_to_id=EV['pull_shout'],boundary_preference={'owner_id':'e1','excluded':'p11','scope_id':'q14','assertion_status':'attributed_claim'},evidence=[316,318,365,377,386,390,391,392,494,511,671],note='Refusal concerns current pulling while snagged. Later gentle drawing after reorientation is a different action, not evidence that refusal was false.')
F(399,belief_holder_id='e1',belief_content_id='p12',epistemic_attitude_kind='knowledge_claim',dialogue_response_to_id=EV['boat_objection'])
F(414,intention_holder_id='e1',intention_content_id='p19',plan_step_ids=['p19','p20'],plan_next_step_id='p19',plan_commitment_status='adopted',goal_priority='free_net_before_following_boat')
F(420,intention_holder_id='e1',intention_content_id='p20',plan_commitment_status='announced_joint_action',evidence=[411,414,416,417,418,419,420,422,425,562,563],note='Mina announces joint action; Theo joins in the later actual walk. Announcement alone does not establish a separate promise by Theo.')
F(461,belief_holder_id='e2',belief_content_id='p21',epistemic_attitude_kind='earlier_belief',epistemic_time_scope={'belief':'p21','phase':'before_first_launch'},epistemic_scope_bundle={'holder_id':'e2','attitude_event_id':EV['thought_calm'],'scope_id':'s0','assertion_status':'asserted'},evidence=[451,452,453,455,458,459,460,461,463,465,467,468],note='The belief episode is narrator asserted; calm-enough content remains attributed. Actual local calm water at the later outlet does not validate the earlier untethered-use judgment.')
F(464,belief_holder_id='e2',belief_content_id='p21',epistemic_attitude_kind='belief',assertion_status='attributed_claim')
F(516,intention_vs_action_alignment={'intention':'p19','action_event_id':EV['hoop_free'],'alignment':'net_freed_before_following'})
F(519,affect_observer_attribution={'experiencer_id':'e1','cue':'releasing_previously_unnoticed_held_breath','interpretation':'possible_relief_after_freeing_net','scope_id':'s0','assertion_status':'candidate'},evidence=[516,517,519,522,524,525,528],note='Breath holding and release are explicit; relief is a defeasible emotional reading.')
F(525,epistemic_attitude_kind='unawareness_of_own_breath_holding',belief_holder_id='e1',belief_content_id='p35')
F(561,intention_holder_id='e1',intention_content_id='p23',plan_commitment_status='announced')
F(563,intention_vs_action_alignment={'intention':'p20','action_event_id':EV['follow_actual'],'alignment':'joint_path_following_after_net_release'})
F(577,speaker_id='e2',addressee_ids=['e1'],communication_channel='speech',speech_act_kind='position_updates')
F(619,communication_channel='whisper')
F(631,dialogue_response_to_id=EV['near_report'],dialogue_turn_function='distinguish_proximity_from_reachability')
F(657,request_action_id='p27',cooperation_goal_id='p31')
F(659,request_action_id='p28',cooperation_goal_id='p31')
F(688,event_divided_labor=B('e5',{'outcome':'p31','contributions':{'e1':[EV['lower2'],EV['draw_boat']],'e2':[EV['guide_left_speech'],EV['guide_down_speech'],EV['pick_boat']]}}),evidence=[640,655,659,671,684,688,695],note='Net positioning, verbal guidance and lifting are separate contributions to one rescue; the earlier freed object was the net.')
F(739,dialogue_turn_function='thank_for_loan')
F(750,dialogue_response_to_id=EV['mina_thanks'],dialogue_turn_function='reciprocal_thanks_for_intact_return')
F(752,intention_vs_action_alignment={'earlier_purpose_event_id':EV['tether_purpose'],'actual_event_id':EV['tie_cord'],'alignment':'cord_now_used_as_tether'},evidence=[451,453,455,458,461,467,468,752,755,759,766],note='Earlier cord purpose is realized on relaunch. This is not a new explicit spoken promise or proof of a verbally articulated belief revision.')
F(785,motion_control=B('e6',{'controller':'e2','kind':'guided_with_tether','assisting_holder':'e1'}))
F(814,narrative_thread_id='thread_pond_boat_and_borrowed_net',narrative_resolution_evidence={'outcomes':['p31','p30','p32'],'status':'boat_recovered_net_returned_tether_used','assertion_status':'candidate'},narrative_theme_candidate={'content':'careful_cooperation_and_changed_method_over_forceful_urgency','assertion_status':'candidate'},narrative_change_dimension='untethered_drift_to_shared_guided_sailing',narrative_motif_link={'earlier_words':[64,65,71,104,108,451,468],'current_words':[752,776,785,800,814],'relation':'same_wind_and_boat_now_under_shared_tether_control','assertion_status':'candidate'},narrative_closure_candidate={'cue':'cord_between_Theo_and_Mina_hands','assertion_status':'candidate'},evidence=[104,108,316,365,377,392,414,516,671,688,725,752,776,785,800,814,818,820],note='Closing control and cooperation are supported interpretations. Fountain arrival, grandfather visit, full patch testing verdict and a permanent lesson in either child are not established.')


# Final per-paragraph review corrections and exact local grammatical bindings.
F(82,grammatical_subject_id='e2')
F([545,668],mention_form='possessive_determiner')
F(58,pos='conj')
F([439,595],pos='n')
F(447,verb_form='past_participle',participial_function='absolute_clause_predicate')
a.words[447].pop('tense',None)
F(612,verb_form='past_participle',aspect='perfect',perfect_auxiliary_id=a.anchor(605),auxiliary_chain=['have'])
a.words[612].pop('tense',None)
F(202,grammatical_subject_id='e1',verb_phrase_ellipsis=True)
a.words[215].pop('determiner_kind',None)
F(215,adjective_degree='positive')
a.words[282].pop('adjective_degree',None)
a.words[333].pop('part_whole_relation',None)
F(333,possession_owner=B('e41',{'owner':'e2'}))
F(63,calendar_day_name='Sunday')
F(100,event_manner=B('e6',{'event_id':EV['sail1'],'manner':'beautifully'}))
F(323,light_verb_construction='take_a_step')
F(485,light_verb_construction='take_a_step')
F(519,lexical_idiom_reading={'expression':'let_out_a_breath','meaning':'exhale'})
F(162,lexical_idiom_reading={'expression':'of_course','meaning':'affirmative_permission'})
F(292,lexical_sense_id='sudden_abrupt_motion')
F(508,quantity_approximation_cue='small_unspecified_amount')
F(802,lexical_sense_id='visual_brightness_of_circular_boat_path')
F(780,part_whole_relation={'part_id':'e45','whole_id':'e44','scope_id':'s0'})
M('snag',315,'attachment_landmark')
M('mina_thanks',736,'quoted_performative')
M('alvarez_thanks',740,'quoted_performative')
# Sail belongs to boat; net is the carrier during successful retrieval, not its identity.
F(671,motion_carrier=B('e6',{'carrier':'e20','event_id':EV['draw_boat']}))
F(688,containment_contents=B('e20',{'removed':['e6'],'exhaustive':False}))

feedback={
 'summary':'Pond rescue annotated with separate boat, net, hoop, handle and twig identities; conditional risks, plans, quoted reports and actual retrieval stages remain distinct.',
 'ambiguities':[
 {'words':[542,315],'issue':'Twig recovered from mesh is not explicitly a broken-off part of the submerged branch.'},
 {'words':[552,556,731,732,735],'issue':'Twig is set on gravel then appears tucked through handle. Intervening pickup/tucking, actor and timing are unreported; only endpoint states are annotated.'},
 {'words':[299,377,748],'issue':'Handle actually bows; net breakage is hypothetical and final intact-return comment does not specify exact handle curvature.'},
 {'words':[624,625,627,629],'issue':'Close is not the same as reachable expresses a general distinction, not an actual inaccessible-boat claim.'},
 {'words':[64,65,71,61,63,705,710],'issue':'No fountain arrival, completed grandfather visit or full success verdict for the patch test is stated.'},
 {'words':[671,672,683,688],'issue':'It drawn toward shore is resolved to net carrying boat; both are motion patients, kept as distinct identities.'},
 ],
 'feature_gaps':[],
 'prompt_feedback':[
 'Retain conditional mechanical risks as scoped possibilities; actual deformation and breakage are different states.',
 'A return with an object in a new place licenses the endpoint state but not an invented intervening retrieval action.',
 'Keep a general distinction between closeness and reachability separate from a target-specific negative affordance.',
 'Repeated references to one snag or one handoff reuse the event, while freeing net and retrieving boat remain different events.',
 ],
 'coverage_notes':'Every word in all 40 paragraphs receives explicit contextual POS/lemma. Sparse grammar, physical, mental, dialogue and narrative features use the frozen v2 catalog; retrospective interpretation has no causal-prefix filter.',
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
