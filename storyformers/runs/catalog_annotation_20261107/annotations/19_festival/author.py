"""Manual contextual annotation of festival, using frozen v3."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from authoring import Annotation
a=Annotation('19_festival',prompt_version='v3')
for k in ['appearance_color','part_whole_relation','figurative_mapping']:a.use_extension(k)
LEX={
0:'n=Bea v=borrow det=a n=spool adp=of adj=green n=string adp=from n=Mrs n=Ives adp=before n=breakfast',
1:'v=bring pron=it adv=back adp=before n=supper n=Mrs n=Ives v=say pron=it det=the adj=good n=kind v=do v=snap conj=when det=the n=wind v=get adj=bossy',
2:'n=Bea v=promise pron=she v=have det=a n=plan adp=for det=the n=village n=welcome n=festival det=a adj=long n=rainbow adp=of n=bunting v=string adv=low adv=enough adp=for n=Rafi det=the adj=new n=boy adv=next n=door part=to v=help v=hang pron=it adj=last n=year det=the n=bunting v=have v=stretch adv=high adp=over det=the n=square conj=and pron=everyone pron=who v=help v=have v=need det=a n=ladder n=Rafi v=use det=a n=wheelchair n=Bea v=want pron=he part=to v=tie det=the adj=last n=knot pron=himself',
3:'pron=she v=carry det=the n=spool conj=and det=a n=stack adp=of n=paper n=flag adp=to det=his n=house n=Rafi v=be adp=on det=the adj=front n=step v=fold adj=silver n=paper adp=into det=a n=crescent n=moon',
4:'pron=I v=make det=a n=flag pron=he v=say pron=it v=need det=a n=place part=to v=fly',
5:'v=come v=help pron=I v=hang det=the n=bunting n=Bea v=say det=no n=ladder pron=I v=bring det=the n=string',
6:'n=Rafi v=turn det=the n=moon n=flag adp=in det=his n=hand v=can pron=I v=choose adv=where pron=it v=go',
7:'adp=of n=course',
8:'conj=and v=tie pron=it',
9:'pron=that det=the adj=important n=part',
10:'adp=at det=the n=square det=the n=festival n=helper v=be v=set adv=out n=jam n=jar conj=and adj=folding n=table n=Bea conj=and n=Rafi v=start adp=at det=the n=gate v=stretch det=the n=string adp=between num=two n=post adp=at det=the n=height adp=of n=Rafi n=shoulder n=Bea v=knot num=one n=end conj=while n=Rafi v=hold det=the n=spool pron=they v=begin v=thread det=the n=paper n=flag adp=onto det=the n=line',
11:'adv=then n=Mr n=Duran v=come v=roll adp=from det=the n=bakery adp=with det=a n=handcart v=stack adp=with n=bread n=basket pron=he v=stop adv=short',
12:'pron=I v=can v=get adp=through adv=there pron=he v=call det=the n=cart v=need det=the n=gate',
13:'n=Bea v=look adp=at det=the n=string adv=then adp=at n=Rafi n=wheel pron=it v=cross det=the adj=whole n=entrance adv=right adv=where pron=everyone v=will v=have part=to v=pass',
14:'pron=we v=can v=hang pron=it adv=high v=say n=Mr n=Duran pron=that adv=where pron=it adv=usually v=go',
15:'n=Bea v=glance adp=at det=the n=ladder v=lean adp=beside det=the n=bandstand pron=she v=imagine n=Rafi v=hold det=a n=flag conj=while pron=someone adj=else v=climb adv=up part=to v=tie pron=it pron=that v=be pron=what pron=she v=have v=ask pron=he part=to v=come adp=for',
16:'n=Rafi v=back det=his n=chair adv=away adp=from det=the n=gate pron=we v=need det=a n=place adv=where n=people v=can v=roll adv=through pron=he v=say conj=and adv=where det=the n=flag v=will v=get v=catch adp=in pron=anyone n=wheel',
17:'n=Mr n=Duran v=wait adp=with det=his n=cart adp=behind pron=he det=more n=festival n=helper v=be v=arrive det=the n=welcome n=arch adp=over det=the n=gate v=stand adj=bare det=its adj=old n=nail n=hole v=show',
18:'n=Bea v=untie det=the n=string pron=she v=have v=plan part=to v=make det=the adj=big n=rainbow adp=in det=the n=village adv=now det=the n=line v=be adj=coiled adp=in det=her n=hand conj=and det=the n=arch v=be adv=still adj=empty',
19:'v=let v=use det=the n=fence adp=by det=the n=welcome n=table pron=she v=say pron=it v=will v=stretch adp=across det=the n=square conj=but pron=it v=will v=block pron=anybody',
20:'n=Mr n=Duran v=push det=his n=cart adp=through det=the n=gate pron=that v=work pron=he v=say conj=and v=roll adv=on adp=toward det=the n=table',
21:'det=the n=fence v=run adp=around det=the adj=little n=garden adp=beside det=the n=welcome n=table pron=it v=be det=a adj=short n=stretch conj=than det=the n=arch conj=but pron=it v=have adj=smooth adj=wooden n=rail conj=and pron=plenty adp=of n=room part=to v=pass n=Bea v=unwind det=the n=string adp=along det=the adj=inside n=rail n=Rafi v=hold det=the n=spool adj=steady adp=in det=his n=lap conj=and v=call adv=out conj=when det=the n=line v=begin part=to v=sag',
22:'adv=too adj=loose pron=he v=say',
23:'n=Bea v=tug pron=it adj=tight',
24:'adv=now pron=it v=try part=to v=pull det=the n=fence adv=over',
25:'pron=she v=laugh conj=and v=ease pron=it adv=back n=Rafi v=tie det=a adj=neat n=knot adp=around det=the n=rail adv=then v=show n=Bea adv=how pron=he v=have v=wrap det=the n=string adv=twice adp=before v=pull pron=it adj=snug',
26:'adv=where v=shall det=my n=moon v=go pron=he v=ask',
27:'adv=somewhere pron=it v=can v=see det=the adj=whole n=festival',
28:'n=Rafi v=choose det=the n=middle adp=of det=the n=line adp=beside det=a adj=yellow n=paper n=sun n=Bea v=tie pron=it adv=there pron=they v=add n=flag adv=all adp=along det=the n=rail v=leave n=space adp=between pron=they adp=for det=the n=breeze part=to v=turn det=each pron=one',
29:'conj=when pron=they v=finish det=the n=rainbow v=curve adp=around det=the n=welcome n=table adv=instead adp=of v=span det=the n=square det=the n=gate v=remain adj=clear det=the adj=high n=arch v=be adv=still adj=bare',
30:'n=Mr n=Bell pron=who v=organize det=the n=festival v=stop part=to v=look pron=we v=be v=expect n=bunting adp=over det=the n=entrance pron=he v=say',
31:'pron=I v=know n=Bea v=reply det=her n=cheek v=feel adj=warm conj=but det=the n=cart v=need part=to v=get adv=through conj=and n=Rafi v=can v=reach pron=this',
32:'n=Rafi v=turn det=his n=moon conj=so det=its adj=silver n=side v=catch det=the n=sun pron=it v=look adj=good adp=from adv=here pron=he v=say pron=you v=can v=see det=every n=flag',
33:'n=Mr n=Bell v=study det=the adj=empty n=arch adv=then det=the adj=open n=gate pron=he v=pick adv=up det=a n=paper n=flag adp=from det=the n=stack conj=and v=hand pron=it adp=to det=a adj=little n=girl v=wait adp=by det=the n=table v=will pron=you v=like part=to v=tie pron=one adv=on',
34:'adv=soon n=people v=be v=stop part=to v=add n=flag det=a n=baker v=tie adv=on det=a adj=tiny n=loaf det=the adj=little n=girl v=choose det=a adj=blue n=star n=Mr n=Bell v=knot det=a adj=red n=square conj=while n=Rafi v=show pron=he det=the adj=double n=wrap',
35:'conj=as n=evening v=settle det=the n=festival n=lantern v=blink adv=on det=the n=string v=hold adj=firm adp=along det=the n=fence conj=and det=the n=moon n=flag v=glimmer adp=between det=the n=sun conj=and det=a n=paper n=loaf n=Rafi v=reach adv=down part=to v=smooth det=its adj=pointed n=tip adp=across det=the adj=clear n=gate n=Mr n=Duran v=roll det=the adj=last n=bread n=basket adp=into det=the n=square det=the adj=little n=girl adj=blue n=star v=spin adp=in det=the n=breeze adp=beside det=the n=moon',
}
for p,s in LEX.items():
 x=[i.split('=',1) for i in s.split()];ws=a.paragraphs[p]['words'];assert len(ws)==len(x),(p,len(ws),len(x))
 a.tag(p,[i[0] for i in x],{w['w']:i[1] for w,i in zip(ws,x)})
F=a.feature
def B(e,value,scope='s0',status='asserted',**kw):return dict(entity_id=e,value=value,scope_id=scope,assertion_status=status,**kw)
ENTS=[
('e1','Bea','person',[0,31,33,83,92,132,136,140,181,200,248,282,291,308,370,374,391,407,469,498,510,526,564,629,631,633]),
('e2','Mrs. Ives','person',[8,9,17,18]),
('e3','Rafi','person',[51,54,79,85,91,103,105,118,122,144,150,153,183,198,205,255,293,311,315,317,332,477,483,496,516,528,540,543,552,645,649,651,665,737,770]),
('e4','Mr. Duran','person',[219,220,233,236,241,275,276,344,345,348,351,420,421,423,430,782,783]),
('e5','Mr. Bell','person',[611,612,613,627,672,673,682,730,731,739]),
('e6','little girl at table','person',[697,703,725,794]),
('e7','baker adding loaf flag','person',[717]),
('e8','borrowed spool','spool',[3,13,95,208,480]),
('e9','green string wound on spool then fence','string',[6,20,143,190,217,252,257,272,373,387,472,490,500,503,514,532,536,558,752]),
('e10','Bea stack of paper flags','paper_flag_group',[98,101,214,690]),
('e11','current festival bunting rainbow','bunting',[44,46,60,135,279,381,409,416,590,623,648]),
('e12','previous year bunting','bunting',[64]),
('e13','village square','square',[70,169,414,600,791]),
('e14','Rafi wheelchair','wheelchair',[82,318]),
('e15','Rafi house next to Bea','house',[56,104]),
('e16','house front step','step',[110]),
('e17','Rafi silver paper moon flag','paper_flag',[113,117,121,124,147,148,156,162,541,546,566,652,654,707,760,761,775,803]),
('e18','Rafi hands','body_part_group',[151]),
('e19','helpers already setting up','person_group',[172]),
('e20','jam jars','jar_group',[177]),
('e21','folding tables','table_group',[180,437]),
('e22','square entrance gate','gate',[187,240,247,261,322,362,427,602,626,681,781]),
('e23','gate posts','post_pair',[193]),
('e24','Rafi shoulders','body_part_group',[199]),
('e25','initial string end','string_part',[203]),
('e26','Bea and Rafi','person_group',[209,323,568,587]),
('e27','bakery','bakery',[225]),
('e28','Duran bread handcart','handcart',[228,244,349,424]),
('e29','bread baskets','basket_group',[232]),
('e30','Rafi wheelchair wheels','wheel_group',[256]),
('e31','ladder beside bandstand','ladder',[286]),
('e32','bandstand','bandstand',[290]),
('e33','welcome arch above gate','arch',[359,365,395,456,607,677]),
('e34','old nail holes in arch','hole_group',[368]),
('e35','Bea hands','body_part_group',[392]),
('e36','garden fence','fence',[402,439,449,458,508,757]),
('e37','welcome table','table',[406,448,595,701]),
('e38','little garden','garden',[444]),
('e39','fence rails','rail_group',[462]),
('e40','inside fence rail used for string','rail',[476,523,574]),
('e41','Rafi lap','body_region',[484]),
('e42','Rafi rail knot','knot',[520]),
('e43','middle of string line','string_region',[555,567]),
('e44','yellow paper sun flag','paper_flag',[563,765]),
('e45','ambient breeze','wind',[581,800]),
('e46','festival','festival',[41,551,616]),
('e47','Bea cheeks','body_part_group',[634]),
('e48','moon flag silver side','flag_region',[656]),
('e49','actual sunlight','sunlight',[659]),
('e50','flag handed by Bell to girl','paper_flag',[687,693]),
('e51','loaf shaped paper flag','paper_flag',[722,769]),
('e52','girl blue star flag','paper_flag',[729,796]),
('e53','Bell red square flag','paper_flag',[735]),
('e54','festival lanterns','lantern_group',[748]),
('e55','moon flag pointed tip','flag_part',[777]),
('e56','last bread basket Duran brings','basket',[788]),
('e57','village','village',[39,384]),
('e58','generic strong wind in Ives claim','generic_wind',[28]),
('e59','previous year helpers','person_group',[72,73]),
('e60','generic previous year ladder','generic_ladder',[78]),
('e61','generic passers through gate','generic_people',[264,328,419]),
('e62','unspecified imagined climber','imagined_person',[298]),
('e63','general wheels to keep clear','generic_wheel_group',[343]),
('e64','Duran and potential helpers','proposal_group',[269]),
('e65','Bell and unspecified other expecters','attributed_group',[620]),
('e66','generic carts needing passage','generic_cart_group',[639]),
('e67','people joining flag activity','person_group',[710]),
('e68','prospective last knot','planned_knot',[90]),
('e69','flag in imagined excluded-participation scenario','imagined_flag',[296,304]),
('e70','it in better-from-here assessment','unresolved_reference',[660]),
('e71','additional arriving festival helpers','person_group',[354]),
('e72','flags in the developing display','paper_flag_group',[337,570,578,671,715]),
('e73','each spaced flag as bound variable','quantified_flag',[585]),
]
# The girl is offered an unspecified flag; it is not Rafi's moon.
ENTS=[(eid,n,k,([w for w in ws if w!=707] if eid=='e17' else ws)) for eid,n,k,ws in ENTS]
for args in ENTS:a.entity(*args)
a.entities['e26']['member_ids']=['e1','e3']
a.entities['e64']['known_member_ids']=['e4'];a.entities['e65']['known_member_ids']=['e5']
a.entities['e29']['known_member_ids']=['e56'];a.entities['e39']['known_member_ids']=['e40']
a.entities['e7']['identity_note']='May be Duran, but baker is not explicitly identified; do not force identity.'
a.entities['e50']['identity_note']='Handed flag may later be chosen blue star e52; source does not equate them explicitly.'
a.entities['e72']['membership_by_phase']=[
 {'phase':'initial_fence_display','from_word':565,'until_word':717,'known_member_ids':['e17','e44'],'exhaustive':False,'support_words':[563,565,569]},
 {'phase':'after_baker_addition','from_word':718,'until_word':731,'known_member_ids':['e17','e44','e51'],'exhaustive':False,'support_words':[718,722]},
 {'phase':'after_Bell_addition','from_word':732,'until_word':795,'known_member_ids':['e17','e44','e51','e53'],'exhaustive':False,'support_words':[732,735]},
 {'phase':'evening_star_observed','from_word':796,'known_member_ids':['e17','e44','e51','e52','e53'],'exhaustive':False,'support_words':[761,765,769,796,797]},
]
a.entities['e72']['identity_note']='Display is an evolving group. Membership is local to each phase; before565 its members are not enumerated. Blue star attachment time/actor are unknown, and its membership is only confirmed by the ending.'
a.entities['e72']['source_group_ids']=['e10']
a.entities['e73']['quantifier_domain']='e72'
a.entities['e73']['not_an_additional_physical_object']=True
a.entities['e70']['not_an_additional_physical_object']=True
a.entities['e68']['identity_note']='Desired last knot is not equated with Rafi actual rail knot e42; other knots follow.'
QUOTES=[
('q1',12,17,'e2',['e1'],'Return request'),('q2',20,31,'e2',['e1'],'String quality claim'),
('q3',118,122,'e3',['e1'],'Flag made'),('q4',124,130,'e3',['e1'],'Flag place needed'),
('q5',130,136,'e1',['e3'],'Invite participation'),('q6',138,144,'e1',['e3'],'No ladders and string supplied'),
('q7',152,158,'e3',['e1'],'Ask to choose flag position'),('q8',158,160,'e1',['e3'],'Permission to choose'),
('q9',160,163,'e3',['e1'],'Ask to tie flag'),('q10',163,167,'e1',['e3'],'Endorse tying participation'),
('q11',236,241,'e4',['e1','e3'],'Cannot pass'),('q12',243,248,'e4',['e1','e3'],'Cart requires gate'),
('q13',269,274,'e4',['e1','e3'],'Propose high string'),('q14',277,282,'e4',['e1','e3'],'Usual high placement'),
('q15',323,332,'e3',['e1'],'Accessible route requirement'),('q16',334,344,'e3',['e1'],'Keep flags clear of wheels'),
('q17',399,407,'e1',['e3'],'Fence proposal'),('q18',409,420,'e1',['e3'],'Smaller unobstructive layout'),
('q19',428,430,'e4',['e1','e3'],'Approve new plan'),('q20',494,496,'e3',['e1'],'Line too loose'),
('q21',502,510,'e3',['e1'],'Overtight line joke'),('q22',538,543,'e3',['e1'],'Ask moon placement'),
('q23',545,552,'e1',['e3'],'Suggest full view'),('q24',620,627,'e5',['e1','e3'],'Earlier expected arch bunting'),
('q25',629,631,'e1',['e5'],'Acknowledge expectation'),('q26',637,649,'e1',['e5'],'Access explanation'),
('q27',660,665,'e3',['e5','e1'],'Better from here'),('q28',667,672,'e3',['e5','e1'],'All flags visible'),
('q29',702,709,'e5',['e6'],'Invite girl to tie a flag'),
]
for sid,lo,hi,h,au,d in QUOTES:
 a.scope(sid,range(lo,hi),kind='quotation',holder_id=h,description=d)
 a.scopes[sid]['addressee_ids']=au
 F(range(lo,hi),assertion_status='attributed_claim',quote_mode='direct')
SCOPES=[
('s1',42,61,'planned_low_bunting','e1','s0','Low rainbow layout intended to enable Rafi participation.'),
('s2',61,79,'previous_year',None,'s0','Earlier festival and different bunting.'),
('s3',85,92,'desired_last_knot_participation','e1','s0','Rafi tying last knot is desired, not identical to final observed knot.'),
('s4',128,130,'desired_flag_location','e3','q4','Place to fly concerns paper flag hanging, not animal flight.'),
('s5',155,158,'requested_choice_content','e3','q7','Flag location is still open.'),
('s6',263,269,'required_passage',None,'s0','Generic necessary route, not every individual completed crossing.'),
('s7',293,305,'imagined_exclusion','e1','s0','Rafi holds flag while someone else ties; not enacted.'),
('s8',302,305,'imagined_purpose','e62','s7','Climber intended to tie flag in imagined alternative.'),
('s9',327,332,'desired_route_capability','e3','q15','A place allowing people to roll through.'),
('s10',335,344,'desired_wheel_clearance','e3','q16','Flags not catching in wheels is required outcome, not an actual entanglement.'),
('s11',377,385,'superseded_large_layout','e1','s0','Largest rainbow plan considered earlier, later revised.'),
('s12',467,469,'passage_affordance',None,'s0','Room to pass, not an extra actual passage event.'),
('s13',505,510,'figurative_line_agency','e3','q21','Pulling fence over is personified excessive tension, not collapse.'),
('s14',546,552,'figurative_moon_viewpoint','e1','q23','Paper moon sees metaphorically, without literal perception.'),
('s15',579,586,'spacing_purpose','e26','s0','Space allows breeze to turn flags, not all turns already observed.'),
('s16',598,601,'unchosen_square_span',None,'s0','Instead of spanning square; this alternative is not realized.'),
('s17',623,627,'earlier_expected_layout','e5','q24','Bunting over entrance is prior expectation, not current layout.'),
('s18',641,644,'needed_cart_passage','e1','q26','Cart passage is an access requirement.'),
('s19',705,709,'invited_tying','e5','q29','Girl tying a flag is invited; not explicitly completed.'),
('s20',713,716,'joining_purpose',None,'s0','Visitors stop to add flags.'),
('s21',773,778,'tip_smoothing_purpose','e3','s0','Reach down to smooth moon tip; no literal celestial moon.'),
]
for sid,lo,hi,k,h,parent,d in SCOPES:a.scope(sid,range(lo,hi),kind=k,holder_id=h,parent=parent,description=d)
a.scope('s22',[],kind='promised_return',holder_id='e1',description='Promised spool return before supper, not observed.')
PROPS=[
(1,'Bea returns the borrowed spool to Mrs. Ives before supper.',[12,13,15,16,31,32],'s22'),
(2,'The string is good quality and does not snap when strong wind acts on it.',[20,22,23,24,25,28,29,30],'q2'),
(3,'The string snaps under strong wind.',[24,25,28,30],'q2'),
(4,'Bea and Rafi hang a low rainbow of bunting for the festival.',[43,44,46,47,48,51,58,59,60],'s1'),
(5,'Rafi ties the last knot himself.',[85,87,89,90,91],'s3'),
(6,'Rafi made a paper moon flag.',[111,113,117,118,119,121],'q3'),
(7,'The paper moon flag has a place to hang and flutter.',[124,125,127,129],'s4'),
(8,'Rafi comes to help Bea hang the bunting.',[130,131,132,133,135],'q5'),
(9,'Ladders are needed for this proposed activity.',[138,139],'q6'),
(10,'No ladders are needed, and Bea brought the string.',[138,139,140,141,143],'q6'),
(11,'Rafi chooses where his moon flag goes.',[152,153,154,155,156,157],'q7'),
(12,'Rafi ties his moon flag on.',[160,161,162],'q9'),
(13,'Rafi may choose the position of his flag.',[152,154,158,159],'q8'),
(14,'Rafi tying his flag is the important part of participating.',[161,162,163,165,166],'q10'),
(15,'Duran can pass through the gate with his cart.',[236,237,238,239,240],'q11'),
(16,'Duran cannot pass through the gate with his cart; the cart needs that gate.',[236,237,238,240,244,245,247],'q12'),
(17,'The group could hang the bunting high.',[269,270,271,272,273],'q13'),
(18,'Bunting usually goes high over the gate.',[277,278,279,280,281],'q14'),
(19,'Rafi holds a flag while someone else climbs and ties it.',[293,294,296,298,300,303,304],'s7'),
(20,'Bea invited Rafi in order only to hold a flag while someone else tied it.',[305,306,307,308,310,311,313],'s0'),
(21,'People can roll through the chosen place and flags do not catch in wheels.',[323,324,327,328,329,330,331,337,338,340,343],'q16'),
(22,'Flags catch in people’s wheels.',[337,338,339,340,343],'s10'),
(23,'Bea makes the biggest bunting rainbow in the village.',[374,376,378,380,381,384],'s11'),
(24,'Bea and Rafi use the fence by the welcome table for bunting.',[399,400,402,406],'q17'),
(25,'The new layout stretches across the square.',[409,410,411,414],'q18'),
(26,'The new layout blocks somebody.',[416,417,418,419],'q18'),
(27,'The new layout does not span the square and will not block people.',[409,410,411,414,416,417,418,419],'q18'),
(28,'The fence plan will work.',[428,429],'q19'),
(29,'The string is too loose.',[490,493,494,495],'q20'),
(30,'The string is now trying to pull the fence over.',[502,503,504,506,508,509],'q21'),
(31,'The moon flag goes at a chosen location.',[538,539,540,541,542],'q22'),
(32,'The moon flag goes somewhere with a view of the whole festival.',[545,546,547,548,551],'q23'),
(33,'The breeze can turn each spaced flag.',[575,576,578,581,583,584,585],'s15'),
(34,'The bunting spans the square.',[596,598,600],'s16'),
(35,'Bunting is hung over the entrance.',[620,622,623,626],'s17'),
(36,'Bell and others were expecting bunting over the entrance.',[620,621,622,623,626],'q24'),
(37,'Carts need to pass and Rafi can reach the current bunting.',[639,640,642,643,645,646,647,648],'q26'),
(38,'Bea knows about the earlier expectation.',[629,630,620,622,626],'q25'),
(39,'It—the moon flag or the display—looks better from Rafi’s present position.',[660,661,662,663,664],'q27'),
(40,'People can see every flag from here.',[667,668,669,670,671],'q28'),
(41,'The girl ties a flag onto the line.',[702,703,704,706,707,708],'s19'),
(42,'Rafi wraps the string twice and pulls it snug to form the rail knot.',[517,520,525,528,530,532,533,535,536,537],'s0'),
]
for n,t,ws,s in PROPS:a.proposition('p'+str(n),t,ws,scope_id=s)
EV={}
def quoted(s):
 while s:
  if a.scopes[s]['kind']=='quotation':return True
  s=a.scopes[s].get('parent')
 return False
def E(k,w,label,**kw):
 eid='ev'+str(len(EV)+1);EV[k]=eid
 a.event(eid,w,label,**kw)
 if kw.get('primary',True):F(w,assertion_status='attributed_claim' if quoted(kw.get('scope',a.words[w]['scope_id'])) else 'asserted')
 return eid
def M(k,ws,role='reference',note=''):a.mention_event(EV[k],ws,role=role,note=note)
def U(k,w,speaker,content,audience,kind='assertion',**kw):
 au=[audience] if isinstance(audience,str) else audience
 eid=E(k,w,'communicate '+content,type='speak',actor=speaker,recipient=au[0] if len(au)==1 else None,**kw)
 scope=kw.get('scope',a.words[w]['scope_id'])
 F(w,utterance_id=eid,speaker_id=speaker,addressee_ids=au,utterance_content_id=content,speech_act_kind=kind,communication_channel='speech',communication_scope_bundle={'speaker_id':speaker,'utterance_event_id':eid,'scope_id':scope,'assertion_status':'attributed_claim' if quoted(scope) else 'asserted'})
 return eid

E('loan',1,'Ives lends spool of green string to Bea',type='transfer',actor='e2',patients=['e8'],recipient='e1',roles={'borrower':[0],'patient':[3],'contained_material':[6],'giver':[8,9]})
E('return',12,'Bea returns borrowed spool to Ives',type='transfer',actor='e1',patients=['e8'],recipient='e2',factuality='desired',roles={'patient':[13]})
U('return_request',19,'e2','p1','e1','request_return',roles={'actor':[17,18]})
E('quality',22,'borrowed string is good quality',type='state',patients=['e9'],factuality='reported',roles={'patient':[20]})
U('quality_claim',22,'e2','p2','e1','quality_assurance',primary=False,scope='s0')
E('snap',25,'string snaps under strong wind',type='state',patients=['e9'],factuality='negated')
E('strong_wind',29,'wind becomes strong in personified description',type='state',patients=['e58'],factuality='hypothetical',roles={'patient':[28]})
U('promise',32,'e1','p1','e2','promise',roles={'actor':[31]})
E('plan',34,'Bea has a low bunting participation plan',type='feel',actor='e1',roles={'experiencer':[33]})
E('low_layout',47,'current bunting strung low for shared hanging',type='state',patients=['e11'],factuality='desired',roles={'patient':[44,46]})
E('help_plan',58,'Rafi helps hang current bunting',actor='e3',patients=['e11'],factuality='desired',roles={'actor':[51,54],'patient':[60]})
M('help_plan',59,'action','Help hang describes Rafi participating in the same desired hanging activity.')
E('old_layout',66,'previous year bunting stretches high over square',type='state',patients=['e12'],roles={'patient':[64],'location':[70]})
E('old_help',74,'previous year helpers help hang bunting',actor='e59',patients=['e12'],roles={'actor':[72,73]})
E('old_need',76,'previous year helpers need ladder',type='state',actor='e59',patients=['e60'],roles={'patient':[78]})
E('wheelchair',80,'Rafi uses wheelchair',type='state',actor='e3',patients=['e14'],roles={'actor':[79],'patient':[82]})
E('want_knot',84,'Bea wants Rafi to tie last knot himself',type='feel',actor='e1',roles={'experiencer':[83]})
E('last_knot',87,'Rafi ties prospective last knot',actor='e3',patients=['e68'],factuality='desired',roles={'actor':[85,91],'patient':[90]})
E('carry',93,'Bea carries spool and paper flags to Rafi house',type='move',actor='e1',patients=['e8','e10'],roles={'actor':[92],'patient':[95,98,101],'destination':[104]})
E('on_step',107,'Rafi is on front step',type='state',patients=['e3'],roles={'patient':[105],'location':[110]})
E('fold_moon',111,'Rafi folds silver paper into moon flag',actor='e3',patients=['e17'],roles={'patient':[113,117]})
M('fold_moon',119,'action','Made a flag refers to the same creation by folding, not another moon.')
M('fold_moon',118,'maker');M('fold_moon',121,'result')
U('made_report',123,'e3','p6','e1','report_creation',roles={'actor':[122]})
E('place_need',125,'moon flag needs hanging place',type='state',patients=['e17'],factuality='reported',roles={'patient':[124]})
U('place_request',125,'e3','p44','e1','indirect_request',primary=False,scope='s0')
E('flag_fly',129,'paper flag hangs and flutters at a place',type='state',patients=['e17'],factuality='desired')
E('come_help',130,'Rafi comes to help Bea hang bunting',type='move',actor='e3',factuality='desired')
E('shared_hang',133,'Rafi and Bea hang bunting',actor='e26',patients=['e11'],factuality='desired',roles={'co_actor':[132],'patient':[135]})
M('shared_hang',131,'participation_predicate')
U('invitation',137,'e1','p8','e3','invitation',roles={'actor':[136]})
U('assurance',139,'e1','p10','e3','access_assurance',primary=False,scope='s0')
M('carry',141,'action','Brought string reports the same outward carrying trip with the loaded spool.')
M('carry',140,'actor');M('carry',143,'contained_material')
E('turn_moon1',145,'Rafi turns moon flag in hands',type='move',actor='e3',patients=['e17'],roles={'actor':[144],'patient':[147,148],'body_instrument':[151]})
E('choose_requested',154,'Rafi chooses flag location',actor='e3',patients=['e17'],factuality='desired',roles={'actor':[153]})
U('ask_choice',154,'e3','p11','e1','permission_request',primary=False,scope='s0')
E('flag_location',157,'moon flag goes at chosen position',type='state',patients=['e17'],factuality='hypothetical',roles={'patient':[156]})
U('grant_choice',159,'e1','p13','e3','grant_permission',scope='s0',primary=False)
E('tie_requested',161,'Rafi ties moon flag on',actor='e3',patients=['e17'],factuality='desired',roles={'patient':[162]})
U('ask_tie',161,'e3','p12','e1','permission_request',scope='s0',primary=False)
E('participation_priority',165,'Rafi tying is important part',type='state',factuality='reported')
U('endorse_tie',165,'e1','p14','e3','endorsement',scope='s0',primary=False)
E('setup',174,'helpers set out jars and folding tables',type='move',actor='e19',patients=['e20','e21'],roles={'actor':[172],'patient':[177,180]})
E('gate_string',188,'Bea and Rafi stretch string across gate at shoulder height',actor='e26',patients=['e9'],roles={'co_actor':[181,183],'patient':[190],'support':[193],'height_reference':[199]})
M('gate_string',184,'onset_operator')
E('gate_knot',201,'Bea knots one end at gate',actor='e1',patients=['e25'],roles={'actor':[200],'patient':[203]})
E('hold_spool1',206,'Rafi holds spool at gate',type='state',actor='e3',patients=['e8'],roles={'actor':[205],'patient':[208]})
E('thread_start',211,'Bea and Rafi begin threading flags onto line',actor='e26',patients=['e10'],instruments=['e9'],roles={'actor':[209],'patient':[214],'attachment_target':[217]})
M('thread_start',210,'onset_operator')
E('duran_arrive',221,'Duran arrives from bakery rolling loaded handcart',type='move',actor='e4',patients=['e28'],roles={'actor':[219,220],'source':[225],'patient':[228]})
M('duran_arrive',222,'manner')
E('cart_loaded',229,'handcart is stacked with bread baskets',type='state',patients=['e28'],roles={'contents':[232]})
E('duran_stop',234,'Duran stops short at blocked gate',type='move',actor='e4',patients=['e28'],roles={'actor':[233]})
E('cannot_pass',238,'Duran passes through gate with cart',type='move',actor='e4',patients=['e28'],factuality='negated',roles={'actor':[236],'route':[240]})
U('blocked_report',242,'e4','p16',['e1','e3'],'report_obstruction',roles={'actor':[241]})
E('gate_need',245,'cart needs gate access',type='state',patients=['e28'],factuality='reported',roles={'patient':[244],'required_route':[247]})
E('look_obstruction',249,'Bea looks from string to Rafi wheels',type='perceive',actor='e1',patients=['e9','e30'],roles={'actor':[248],'patient':[252,256]})
E('string_crosses',258,'string crosses whole entrance at required passage',type='state',patients=['e9'],roles={'patient':[257],'location':[261]})
E('required_pass',268,'people pass through required entrance',type='move',actor='e61',factuality='desired',roles={'actor':[264]})
E('high_proposal',271,'helpers hang string high',actor='e64',patients=['e9'],factuality='hypothetical',roles={'actor':[269],'patient':[272]})
U('suggest_high',274,'e4','p17',['e1','e3'],'proposal',roles={'actor':[275,276]})
E('usual_high',281,'bunting usually hangs high',type='state',patients=['e11'],factuality='reported',roles={'patient':[279]})
U('usual_report',281,'e4','p18',['e1','e3'],'explain_custom',scope='s0',primary=False)
E('look_ladder',283,'Bea glances at ladder',type='perceive',actor='e1',patients=['e31'],roles={'actor':[282],'patient':[286]})
E('ladder_leans',287,'ladder leans beside bandstand',type='state',patients=['e31'],roles={'landmark':[290]})
E('imagine_exclusion',292,'Bea imagines Rafi holding while someone else ties',type='feel',actor='e1',roles={'experiencer':[291]})
E('imagined_holding',294,'Rafi holds flag in imagined arrangement',type='state',actor='e3',patients=['e69'],factuality='hypothetical',roles={'actor':[293],'patient':[296]})
E('imagined_climb',300,'someone else climbs in imagined arrangement',type='move',actor='e62',factuality='hypothetical',roles={'actor':[298]})
E('imagined_tie',303,'imagined climber ties flag',actor='e62',patients=['e69'],factuality='hypothetical',roles={'patient':[304]})
E('reject_purpose',306,'imagined holding-only role is Bea invitation purpose',type='state',factuality='negated')
M('invitation',310,'action','Had asked him to come recalls the earlier actual invitation; the holding-only purpose is separately negated.')
M('come_help',313,'invited_content')
E('back_chair',316,'Rafi backs wheelchair away from gate',type='move',actor='e3',patients=['e14'],roles={'actor':[315],'patient':[318],'source':[322]})
E('access_need',324,'Bea and Rafi need accessible flag location',type='state',actor='e26',factuality='reported',roles={'actor':[323]})
E('roll_access',330,'people roll through chosen place',type='move',actor='e61',factuality='desired',roles={'actor':[328]})
U('access_request',333,'e3','p45','e1','requirements',roles={'actor':[332]})
E('wheel_entangle',340,'flags get caught in wheels',type='state',patients=['e72'],factuality='negated',roles={'patient':[337],'obstruction':[343]})
E('duran_wait',346,'Duran waits with cart',type='state',actor='e4',patients=['e28'],roles={'actor':[344,345],'patient':[349]})
E('helpers_arrive',356,'more helpers arrive behind Duran',type='move',actor='e71',roles={'actor':[354],'landmark':[351]})
E('arch_bare1',363,'welcome arch stands bare above gate',type='state',patients=['e33'],roles={'patient':[359],'landmark':[362]})
E('holes_visible',369,'old arch nail holes show',type='state',patients=['e34'],roles={'patient':[368]})
E('untie_gate',371,'Bea unties string from gate',actor='e1',patients=['e9'],roles={'actor':[370],'patient':[373]})
M('plan',376,'action','Earlier largest-rainbow planning elaborates the same plan, not a second new commitment.')
E('largest_rainbow',378,'Bea makes biggest bunting rainbow in village',actor='e1',patients=['e11'],factuality='desired',roles={'patient':[381],'comparison_domain':[384]})
E('coiled_line',389,'line is coiled in Bea hands',type='state',patients=['e9'],roles={'patient':[387],'holder_body':[392]})
M('arch_bare1',398,'state_continuation','Arch is still empty, retaining ongoing absence of bunting.')
E('use_fence',400,'Bea and Rafi use fence by welcome table',actor='e26',patients=['e36'],factuality='desired',roles={'patient':[402],'landmark':[406]})
U('fence_proposal',408,'e1','p24','e3','revised_plan',roles={'actor':[407]})
E('square_span',411,'new bunting spans square',type='state',patients=['e11'],factuality='negated',roles={'patient':[409],'location':[414]})
E('block_people',418,'new bunting blocks somebody',type='state',patients=['e11'],factuality='negated',roles={'patient':[416],'affected':[419]})
U('fence_explain',418,'e1','p27','e3','explain_tradeoff',scope='s0',primary=False)
E('cart_through',422,'Duran pushes cart through clear gate',type='move',actor='e4',patients=['e28'],roles={'actor':[420,421],'patient':[424],'route':[427]})
E('plan_works',429,'fence plan will work',type='state',factuality='reported')
U('approve_fence',431,'e4','p28',['e1','e3'],'approval',roles={'actor':[430]})
E('cart_toward_tables',433,'Duran rolls cart onward toward tables',type='move',actor='e4',patients=['e28'],roles={'destination_direction':[437]})
E('fence_layout',440,'fence extends around garden',type='state',patients=['e36'],roles={'patient':[439],'enclosed_region':[444]})
E('fence_shorter',450,'fence hanging stretch is shorter than arch span',type='state',patients=['e36'],roles={'patient':[449],'comparison':[456]})
E('fence_properties',459,'fence has smooth wooden rails and passing room',type='state',patients=['e36'],roles={'patient':[458],'parts':[462]})
E('pass_space',468,'people pass beside fence',type='move',factuality='hypothetical')
E('unwind_fence',470,'Bea unwinds string along inside rail',type='move',actor='e1',patients=['e9'],roles={'actor':[469],'patient':[472],'route':[476]})
E('hold_spool2',478,'Rafi holds spool steady in lap',type='state',actor='e3',patients=['e8'],roles={'actor':[477],'patient':[480],'support':[484]})
U('loose_call',486,'e3','p29','e1','tension_feedback')
E('sag',493,'string line begins to sag',type='state',patients=['e9'],roles={'patient':[490]})
M('sag',491,'onset_operator')
E('loose_state',495,'string is too loose',type='state',patients=['e9'],factuality='reported')
M('loose_call',497,'action','Said elaborates the same call about sagging, not another independent utterance.')
E('tighten',499,'Bea tugs string tighter',actor='e1',patients=['e9'],roles={'actor':[498],'patient':[500]})
E('trying_pull',504,'string tries to pull fence over in personification',actor='e9',patients=['e36'],factuality='reported',roles={'actor':[503]})
E('pull_over',506,'string pulls fence over in joking warning',actor='e9',patients=['e36'],factuality='hypothetical',roles={'patient':[508]})
U('tight_joke',504,'e3','p30','e1','playful_tension_warning',scope='s0',primary=False)
E('laugh',511,'Bea laughs',type='state',actor='e1',roles={'actor':[510]})
E('ease',513,'Bea eases string tension back',actor='e1',patients=['e9'],roles={'patient':[514]})
E('rail_knot',517,'Rafi ties neat knot around fence rail',actor='e3',patients=['e9','e42'],roles={'actor':[516],'result':[520],'attachment_target':[523]})
E('show_wrap',525,'Rafi shows Bea double wrap method',type='speak',actor='e3',recipient='e1',roles={'recipient':[526]})
E('wrap',530,'Rafi wraps string twice before pulling snug',actor='e3',patients=['e9'],roles={'actor':[528],'patient':[532]})
E('pull_snug',535,'Rafi pulls wrapped string snug',actor='e3',patients=['e9'],roles={'patient':[536]})
E('moon_where',542,'moon flag goes at a location',type='state',patients=['e17'],factuality='hypothetical',roles={'patient':[541]})
U('ask_moon_where',544,'e3','p31','e1','location_question',roles={'actor':[543]})
E('moon_see',548,'moon flag sees whole festival in personification',type='perceive',actor='e17',patients=['e46'],factuality='hypothetical',roles={'actor':[546],'patient':[551]})
U('suggest_view',545,'e1','p32','e3','placement_suggestion',primary=False,scope='s0')
E('choose_middle',553,'Rafi chooses line middle beside sun for moon',actor='e3',patients=['e43'],roles={'actor':[552],'chosen_location':[555],'landmark':[563]})
E('tie_moon',565,'Bea ties Rafi moon at chosen location',actor='e1',patients=['e17'],roles={'actor':[564],'patient':[566],'destination':[567]})
E('add_flags',569,'Bea and Rafi add flags along rail',actor='e26',patients=['e72'],roles={'actor':[568],'patient':[570],'attachment_target':[574]})
E('leave_gaps',575,'Bea and Rafi leave spaces between flags',actor='e26',patients=['e72'],roles={'patient':[578]})
E('wind_turn_possible',583,'breeze turns each spaced flag',type='move',actor='e45',patients=['e73'],factuality='desired',roles={'actor':[581],'patient':[585]})
E('finish',588,'Bea and Rafi finish initial bunting layout',actor='e26',roles={'actor':[587]})
E('rainbow_curve',591,'bunting curves around welcome table',type='state',patients=['e11'],roles={'patient':[590],'landmark':[595]})
E('span_unrealized',598,'bunting spans square',type='state',patients=['e11'],factuality='negated',roles={'location':[600]})
E('gate_clear',603,'gate remains clear after line relocation',type='state',patients=['e22'],roles={'patient':[602]})
M('arch_bare1',610,'state_continuation','High arch is still bare after relocated display is finished.')
E('organize',614,'Bell organizes festival',actor='e5',patients=['e46'],roles={'actor':[611,612,613],'patient':[616]})
E('bell_stop',617,'Bell stops to inspect layout',actor='e5')
E('bell_look',619,'Bell looks at layout',type='perceive',actor='e5')
E('expect',622,'Bell and others expected bunting over entrance',type='feel',actor='e65',factuality='reported',roles={'experiencer':[620],'content_object':[623],'expected_location':[626]})
U('expect_report',628,'e5','p36',['e1','e3'],'report_expectation',roles={'actor':[627]})
E('know',630,'Bea knows Bell expected entrance bunting',type='feel',actor='e1',factuality='reported',roles={'experiencer':[629]})
U('acknowledge',632,'e1','p38','e5','acknowledge_expectation',roles={'actor':[631]})
E('cheeks_warm',635,'Bea cheeks feel warm',type='state',patients=['e47'],roles={'patient':[634]})
E('cart_need',640,'carts need unobstructed passage',type='state',patients=['e66'],factuality='reported',roles={'patient':[639]})
E('cart_pass_needed',642,'carts pass through entrance',type='move',patients=['e66'],factuality='desired')
E('rafi_reach',647,'Rafi can reach current bunting',type='state',actor='e3',patients=['e11'],factuality='reported',roles={'actor':[645],'patient':[648]})
U('access_explain',647,'e1','p37','e5','explain_access',scope='s0',primary=False)
E('turn_moon2',650,'Rafi turns his moon flag',type='move',actor='e3',patients=['e17'],roles={'actor':[649],'patient':[652]})
E('silver_catches_light',657,'moon silver side catches sunlight',type='state',patients=['e48'],roles={'patient':[656],'light_source':[659]})
E('looks_better',661,'moon or display looks better from Rafi position',type='state',patients=['e70'],factuality='reported',roles={'patient':[660]})
U('better_report',666,'e3','p39',['e1','e5'],'positive_assessment',roles={'actor':[665]})
E('flags_visible',669,'all display flags can be seen from current position',type='perceive',patients=['e72'],factuality='reported',roles={'patient':[671]})
U('visibility_claim',669,'e3','p40',['e1','e5'],'viewpoint_claim',scope='s0',primary=False)
E('bell_study',674,'Bell studies empty arch then open gate',type='perceive',actor='e5',patients=['e33','e22'],roles={'actor':[672,673],'patient':[677,681]})
E('pick_flag',683,'Bell picks a paper flag from stack',type='obtain',actor='e5',patients=['e50'],roles={'actor':[682],'patient':[687],'source':[690]})
E('hand_flag',692,'Bell hands paper flag to little girl',type='transfer',actor='e5',patients=['e50'],recipient='e6',roles={'patient':[693],'recipient':[697]})
E('girl_wait',698,'girl waits by welcome table',type='state',actor='e6',roles={'location':[701]})
E('invited_tie',706,'girl ties a flag onto line',actor='e6',factuality='desired')
U('invite_girl',704,'e5','p41','e6','invitation',scope='s0',primary=False)
E('join_stop',712,'people stop to join flag adding',type='move',actor='e67',roles={'actor':[710]})
E('join_add',714,'people add flags to display',actor='e67',patients=['e72'],factuality='desired',roles={'patient':[715]})
E('tie_loaf',718,'baker ties tiny loaf shaped flag onto line',actor='e7',patients=['e51'],roles={'actor':[717],'patient':[722]})
E('choose_star',726,'girl chooses blue star flag',actor='e6',patients=['e52'],roles={'actor':[725],'patient':[729]})
E('knot_red',732,'Bell knots red square flag onto display',actor='e5',patients=['e53'],roles={'actor':[730,731],'patient':[735]})
E('show_bell',738,'Rafi shows Bell double wrap',type='speak',actor='e3',recipient='e5',roles={'actor':[737],'recipient':[739]})
E('evening',745,'evening settles',type='state')
E('lanterns_on',749,'festival lanterns light up',type='state',patients=['e54'],roles={'patient':[748]})
E('string_firm',753,'string holds firm along fence at evening',type='state',patients=['e9'],roles={'patient':[752],'attachment_target':[757]})
E('moon_glimmer',762,'moon flag glimmers between sun and loaf flags',type='state',patients=['e17'],roles={'patient':[760,761],'flanking_flags':[765,769]})
E('rafi_reach_down',771,'Rafi reaches down toward moon flag tip',type='move',actor='e3',roles={'actor':[770]})
E('smooth_tip',774,'Rafi smooths moon flag pointed tip',actor='e3',patients=['e55'],factuality='desired',roles={'patient':[777]})
E('last_basket',784,'Duran rolls last bread basket through gate into square',type='move',actor='e4',patients=['e56'],roles={'actor':[782,783],'patient':[788],'route':[781],'destination':[791]})
E('star_spins',797,'girl blue star spins in breeze beside moon',type='move',patients=['e52'],roles={'patient':[796],'motive_medium':[800],'landmark':[803]})

# Sparse grammatical facts derive only from the explicit contextual tags above.
for w,r in enumerate(a.words):
 if r['pos']=='det' and r['lemma'] in ['a','an','the']:
  F(w,determiner_kind='definite_article' if r['lemma']=='the' else 'indefinite_article',definiteness='definite' if r['lemma']=='the' else 'indefinite')
 if r['pos']=='det' and r['lemma'] in ['his','her','my','its']:
  F(w,determiner_kind='possessive',possessive_construction='possessive_determiner',mention_form='possessive_determiner',definiteness='definite')
 if r['pos']=='pron' and r['lemma'] in ['I','he','she','it','we','they','you']:F(w,mention_form='personal_pronoun')
 if r['pos']=='conj' and r['lemma']=='and':F(w,coordinator_type='additive',discourse_relation_kind='addition')
for w,ex in [(20,['it','is']),(24,['does','not']),(163,['that','is']),(237,['can','not']),(277,['that','is']),(306,['was','not']),(338,['will','not']),(399,['let','us']),(410,['will','not']),(417,['will','not']),(428,['that','will']),(503,['it','is'])]:F(w,contraction_expansion=ex)
F([198,255,342,794],possessive_construction='s_genitive',grammatical_case='genitive')
F([85,132,162,257,272,304,311,500,514,536,566,578,648,693,739],grammatical_case='objective')
# It at257 is the subject of crossed, not an object.
a.words[257].pop('grammatical_case',None)
F(91,reflexive_antecedent_id='e3',reflexive_form='himself',dependency_relation='emphatic_reflexive')
F([209,323,568,587],split_antecedent_ids=['e1','e3'],grammatical_number='plural')
F([118,140,153,236,629],grammatical_person=1,grammatical_number='singular')
F(620,grammatical_person=1,grammatical_number='plural',reference_unresolved=True,antecedent_candidates=['e5'],evidence=[620,621,622],note='Bell is included in we; the other expecters are unspecified, not automatically all helpers.')
F([101,139,151,172,177,180,193,199,214,232,256,337,343,354,368,392,437,462,570,578,639,710,715,748],grammatical_number='plural')
F([13,20,60,95,117,121,124,148,156,162,208,228,244,257,318,349,402,439,449,458,480,503,541,546,652,660,687,693,671,707,735,761,788,803],grammatical_number='singular')
F([139,264,328,342,343,419,639,667],generic_reference=True)
F(667,referent_kind='generic_observer',grammatical_person=2)
F(707,referent_kind='nonspecific_flag',reference_specificity='nonspecific',antecedent_candidates=['e50'],reference_unresolved=True)
F(620,referent_kind='partially_resolved_group')
F(299,adjective_degree='positive')
F(138,determiner_kind='negative_quantifier')
F(192,cardinal_value=2);F(202,cardinal_value=1);F(533,cardinal_value=2,temporal_iteration_count=2)
F(670,determiner_kind='universal_distributive',quantifier_domain_restriction={'domain_id':'e72','context':'current_display'})
F(584,determiner_kind='distributive',quantifier_domain_restriction={'domain_id':'e72','context':'spaced_display_flags'})
F(352,determiner_kind='additional_quantity',quantity_comparison_cue='more')
F(741,cardinal_value=2)
F([5,22,43,53,61,89,109,112,165,179,260,299,364,366,398,443,460,461,475,481,495,519,537,550,561,604,606,610,636,655,676,680,696,721,724,728,734,754,776,780,786,793,795],adjective_degree='positive')
F(380,adjective_degree='superlative',lexical_scale_dimension='display_size',lexical_scale_direction='largest')
F(452,adjective_degree='comparative',lexical_scale_dimension='available_hanging_length',lexical_scale_direction='shorter')
F(501,adjective_degree='comparative',lexical_scale_dimension='tension',lexical_scale_direction='tighter')
F(662,adjective_degree='comparative',lexical_scale_dimension='view_quality',lexical_scale_direction='better')
for w,h in [(39,40),(40,41),(100,101),(116,117),(147,148),(171,172),(176,177),(213,214),(231,232),(353,354),(358,359),(367,368),(405,406),(447,448),(562,563),(594,595),(686,687),(740,742),(747,748),(760,761),(768,769),(787,788)]:F(w,dependency_relation='nominal_modifier',syntactic_governor_id=a.anchor(h))
# Double modifies the wrap noun adjectivally, not as a separate nominal object.
a.words[740].pop('dependency_relation',None);a.words[740].pop('syntactic_governor_id',None)
F(741,syntactic_governor_id=a.anchor(742),dependency_relation='adjectival_modifier')
F([1,19,32,34,65,66,74,75,76,80,84,93,106,119,123,137,141,145,173,184,201,206,210,221,234,242,249,258,274,283,292,300,306,309,310,316,333,346,355,363,371,375,376,388,396,408,422,431,433,440,450,459,470,478,486,491,497,499,511,513,517,525,529,530,544,553,565,569,588,591,603,608,614,617,621,628,632,635,650,657,666,674,683,692,711,718,726,732,738,745,749,753,762,771,784,797],verb_form='finite',tense='past')
F([24,29,125,152,237,245,265,270,281,324,329,338,399,410,417,539,547,622,630,640,646,647,661,668,702,704],verb_form='finite',tense='present')
F([265,270,539,702],tense='past')
F([47,229,340],verb_form='past_participle')
F([111,174,188,211,222,287,294,356,369,535,575,598,622,698,712],verb_form='present_participle')
a.words[622].pop('tense',None)
F([12,25,58,59,87,129,130,131,133,154,157,161,238,266,268,271,303,313,330,339,378,400,411,418,429,468,493,506,542,548,583,619,642,647,669,706,714,774],verb_form='bare')
F(157,verb_form='finite',tense='present')
# Modal reach is bare although its possibility applies now.
a.words[647].pop('tense',None)
for h,aux in [(66,65),(76,75),(310,309),(376,375),(530,529)]:F(h,verb_form='past_participle',aspect='perfect',perfect_auxiliary_id=a.anchor(aux),auxiliary_chain=['have']);a.words[h].pop('tense',None)
for h,aux in [(174,173),(356,355),(504,503),(622,621),(712,711)]:F(h,verb_form='present_participle',aspect='progressive',progressive_auxiliary_id=a.anchor(aux),auxiliary_chain=['be']);a.words[h].pop('tense',None)
F(340,voice='passive',passive_auxiliary_id=a.anchor(339),auxiliary_chain=['get'])
for marker,head,control in [(57,58,None),(86,87,None),(128,129,'e17'),(267,268,'e61'),(302,303,'e62'),(312,313,'e3'),(377,378,'e1'),(467,468,None),(492,493,'e9'),(505,506,'e9'),(582,583,None),(618,619,'e5'),(641,642,'e66'),(705,706,None),(713,714,'e67'),(773,774,'e3')]:
 F(marker,constituent_category='infinitive_marker',syntactic_governor_id=a.anchor(head))
 F(head,verb_form='infinitive',infinitive_marker_id=a.anchor(marker))
 if control:F(head,subject_controller_id=control)
F([12,130,131],imperative_subject_status='understood_second_person')
F(399,mood='hortative')
F([152,539,702],subject_auxiliary_inversion=True)
F([24,237,306],proposition_polarity='negative')
F(24,do_support_status='negative_auxiliary',negation_scope_id='p3')
F(138,proposition_polarity='negative',negation_scope_id='p9')
F(237,negation_scope_id='p15')
F(306,negation_scope_id='p20')
F(338,proposition_polarity='negative',negation_scope_id='p22')
F(410,proposition_polarity='negative',negation_scope_id='p25')
F(417,proposition_polarity='negative',negation_scope_id='p26')
F(596,proposition_polarity='negative',negation_scope_id='p34',discourse_relation_kind='replacement')
F([152,237,265,270,329,338,410,417,539,547,646,668,702],modal_auxiliary_class='modal')
for w,kind,content in [(152,'request_permission','p11'),(237,'physical_inability','p15'),(265,'route_necessity','p15'),(270,'proposed_option','p17'),(329,'desired_access_capability','p21'),(338,'desired_nonentanglement','p22'),(410,'predicted_absence','p25'),(417,'predicted_absence','p26'),(539,'placement_advice_request','p31'),(547,'figurative_viewpoint_capability','p32'),(646,'reach_capability','p37'),(668,'visibility_capability','p40'),(702,'polite_invitation','p41')]:F(w,modal_base={'kind':kind,'content_id':content})
# Route necessity is generic: do not reuse Duran-specific proposition p15.
a.proposition('p43','People must use the entrance to pass into the square.',[261,263,264,265,266,268],scope_id='s6')
F(265,modal_base={'kind':'route_necessity','content_id':'p43'})
for w,rel in [(26,'generic_condition'),(73,'relative_subject'),(155,'embedded_location_question'),(204,'temporal_overlap'),(263,'relative_locative'),(278,'relative_locative'),(297,'imagined_overlap'),(307,'fused_relative'),(327,'relative_locative'),(335,'relative_locative'),(454,'comparison'),(488,'temporal_when'),(527,'embedded_manner'),(586,'temporal_when'),(613,'supplementary_relative'),(653,'result'),(736,'temporal_overlap'),(743,'temporal_as')]:F(w,subordinator_type=rel)
for w,rel in [(10,'before'),(15,'before'),(204,'overlap'),(218,'then'),(253,'then'),(297,'overlap'),(488,'when'),(524,'then'),(534,'before'),(586,'when'),(678,'then'),(736,'overlap'),(743,'overlap')]:F(w,discourse_relation_kind=rel,temporal_signal_relation=rel)
F(653,discourse_relation_kind='result')
for w in [415,457,637]:F(w,discourse_relation_kind='contrast',coordinator_type='contrastive')
F(280,temporal_frequency_class='habitual')
F(11,time_expression_id='time_breakfast',temporal_anchor_unresolved=True)
F(16,time_expression_id='time_supper',temporal_anchor_unresolved=True)
F(62,time_expression_id='time_last_year',temporal_deixis='previous_year')
F(744,time_expression_id='time_evening',temporal_granularity='part_of_day')
F([385,502],temporal_deixis='now')
F(709,temporal_signal_relation='soon_after')
F([139,158,159,161,165,494,495,545],sentence_fragment_type='contextual_dialogue_fragment')

SUBJECTS={
'e1':[1,32,34,84,93,133,137,141,201,249,283,292,310,371,376,378,408,470,499,511,513,565,630,632],
'e2':[12,19], 'e3':[58,59,80,87,106,111,119,123,145,154,161,206,294,313,316,333,478,486,497,517,525,530,535,544,553,647,650,666,738,771,774],
'e4':[221,222,234,238,242,274,346,422,431,433,784],
'e5':[614,617,619,628,674,683,692,732], 'e6':[698,706,726], 'e7':[718],
'e9':[25,258,493,504,506,753], 'e11':[271,281,411,418,591], 'e12':[66], 'e17':[125,129,157,542,548,762],
'e19':[174], 'e71':[356], 'e26':[184,188,211,324,400,569,575,588], 'e28':[229,245], 'e33':[363,396,608], 'e34':[369],
'e36':[440,450,459], 'e45':[583], 'e47':[635], 'e48':[657], 'e52':[797], 'e54':[749], 'e58':[29],
'e59':[74,76], 'e61':[268,330], 'e62':[300,303], 'e65':[622], 'e66':[640,642], 'e67':[712,714], 'e70':[661],
}
for e,ws in SUBJECTS.items():F(ws,grammatical_subject_id=e)
# Ives is requesting a return; understood addressee Bea is its grammatical subject.
F(12,grammatical_subject_id='e1')
F(271,grammatical_subject_id='e64')
for w,e in [(1,'e8'),(12,'e8'),(80,'e14'),(87,'e68'),(93,'e8'),(111,'e17'),(119,'e17'),(133,'e11'),(141,'e9'),(145,'e17'),(161,'e17'),(174,'e20'),(188,'e9'),(201,'e25'),(206,'e8'),(211,'e10'),(271,'e9'),(294,'e69'),(303,'e69'),(316,'e14'),(371,'e9'),(378,'e11'),(400,'e36'),(418,'e61'),(422,'e28'),(459,'e39'),(470,'e9'),(478,'e8'),(499,'e9'),(506,'e36'),(513,'e9'),(517,'e42'),(530,'e9'),(535,'e9'),(548,'e46'),(553,'e43'),(565,'e17'),(569,'e72'),(614,'e46'),(622,'e11'),(647,'e11'),(650,'e17'),(657,'e49'),(669,'e72'),(674,'e33'),(683,'e50'),(692,'e50'),(714,'e72'),(718,'e51'),(726,'e52'),(732,'e53'),(774,'e55'),(784,'e56')]:F(w,grammatical_object_id=e)
F(93,conjunct_head_ids=[a.anchor(95),a.anchor(101)],coordination_category='NP')
F(174,conjunct_head_ids=[a.anchor(177),a.anchor(180)],coordination_category='NP')
F(674,conjunct_head_ids=[a.anchor(677),a.anchor(681)],coordination_category='NP')
for w,e in [(4,'e9'),(7,'e2'),(37,'e46'),(45,'e11'),(68,'e13'),(99,'e10'),(102,'e15'),(107,'e16'),(114,'e17'),(149,'e18'),(167,'e13'),(185,'e22'),(191,'e23'),(197,'e24'),(215,'e9'),(223,'e27'),(226,'e28'),(230,'e29'),(239,'e22'),(250,'e9'),(254,'e30'),(284,'e31'),(288,'e32'),(320,'e22'),(341,'e63'),(347,'e28'),(350,'e4'),(360,'e22'),(382,'e57'),(390,'e35'),(403,'e37'),(412,'e13'),(425,'e22'),(435,'e21'),(441,'e38'),(445,'e37'),(473,'e40'),(482,'e41'),(521,'e40'),(556,'e9'),(559,'e44'),(572,'e40'),(577,'e72'),(592,'e37'),(624,'e22'),(688,'e10'),(694,'e6'),(699,'e37'),(755,'e36'),(763,'e44'),(778,'e22'),(789,'e13'),(798,'e45'),(801,'e17')]:F(w,prepositional_object_id=e)
F([525,738],communication_channel='physical_demonstration',utterance_content_id='p42')
for k in ['show_wrap','show_bell']:
 a.events[EV[k]]['event_type']='other';a.words[a.events[EV[k]]['trigger']]['event_type']='other'

# Physical identities, states and access are anchored to their local event.
F(1,retrieval_inverse_relation={'event_id':EV['loan'],'canonical_relation':'lend_to','source_id':'e2','recipient_id':'e1','theme_id':'e8','surface_perspective':'borrow_from','scope_id':'s0','assertion_status':'asserted'},possession_lender=B('e8',{'lender':'e2'}),possession_borrower=B('e8',{'borrower':'e1'}),transfer_kind=B('e8','temporary_loan'),transfer_completion=B('e8',{'completed':True}))
F(3,containment_contents=B('e8',{'wound_material':'e9'}),evidence=[3,4,6,95,143,208,472,480,752],note='Spool and string are distinct. Borrowed spool carries string; later string remains on fence, while the spool return is not narrated.')
F(5,appearance_color=B('e9','green'))
F(12,possession_return_target=B('e8',{'return_to':'e2'},'q1','attributed_claim',factuality='desired'),transfer_return_due=B('e8',{'before':'time_supper'},'q1','attributed_claim',factuality='desired'))
F(29,figurative_mapping={'target_id':'e58','source_image':'bossy_person','kind':'wind_force_personification','literal_event':False},evidence=[24,25,26,28,29,30],note='Bossy wind is a condition in Ives quality claim, not a social attitude of wind or actual strong weather already occurring.')
F(25,object_integrity=B('e9',{'does_not_snap_under':'strong_wind'},'q2','attributed_claim'),evidence=[20,22,24,25,28,30],note='Durability is Ives claim; evening holding firm supplies one later observed result, not proof under every wind strength.')
F(44,figurative_mapping={'target_id':'e11','source_image':'rainbow','kind':'colorful_bunting_metaphor','literal_event':False})
F(47,spatial_configuration=B('e11',{'height':'low_enough_for_Rafi_to_help'},'s1',factuality='desired'),access_reachability=B('e11',{'actor':'e3','reachable':True},'s1',factuality='desired'))
F(66,spatial_configuration=B('e12',{'landmark':'e13','relation':'high_over'},'s2'),evidence=[61,62,64,66,67,70],note='Earlier-year bunting is a different display, not the present display already high.')
F(76,access_tool_requirement=B('e12',{'actor_group':'e59','tool':'e60'},'s2'))
F(80,possession_user=B('e14',{'user':'e3'}),evidence=[79,80,82,315,316,318],note='Wheelchair use is explicit. No medical diagnosis or blanket inability to perform unrelated tasks is inferred.')
F(93,possession_holder=B('e8',{'holder':'e1'}),motion_destination=B('e8',{'landmark_id':'e15','role':'destination'}))
F(103,possession_user=B('e15',{'resident':'e3'}))
F(107,spatial_configuration=B('e3',{'landmark':'e16','relation':'on'}))
F(111,event_result_entity=B('e17',{'created_from':'silver_paper','event_id':EV['fold_moon']}))
F(112,appearance_color=B('e17','silver'))
F(113,material_composition=B('e17','paper'))
F(116,object_shape=B('e17','crescent'))
F(145,possession_holder=B('e17',{'holder':'e3'}))
F(174,spatial_configuration=B('e20',{'landmark':'e13','relation':'set_out_in'}),evidence=[172,174,177,179,180],note='Folding tables is interpreted as the table type in a coordinated set-out list; no separate actual folding action is required by this reading.')
F(188,spatial_configuration=B('e9',{'landmark':'e23','relation':'between','height_reference':'e24'}),event_collective_participants=B('e9',{'event_id':EV['gate_string'],'actors':['e1','e3']}))
F(192,quantity_total={'domain':'e23','value':2,'unit':'posts','scope_id':'s0','assertion_status':'asserted'})
F(206,possession_holder=B('e8',{'holder':'e3'}),evidence_missing={'needed':'exact_spool_handoff_from_Bea_to_Rafi'},evidence=[93,95,200,201,205,206,208],note='Spool is first carried by Bea then held by Rafi; no unreported transfer event is inserted.')
F(211,event_phase=B('e10',{'affected_event_id':EV['thread_start'],'cue':'began'}))
F(229,containment_contents=B('e28',{'supported_load':'e29'}),spatial_support=B('e29',{'supported_by':'e28'}))
F(221,motion_source=B('e28',{'landmark_id':'e27','role':'source'}),motion_carrier=B('e29',{'carrier':'e28'}))
F(238,access_clearance=B('e28',{'passage':'e22','fits':False,'obstruction':'e9'},'q11','attributed_claim'),evidence=[236,237,238,240,244,245,247,257,258,261],note='Inability to pass is Duran report, supported by narrated string crossing. This is obstruction, not an invented measured cart/gate width mismatch.')
F(258,spatial_extent=B('e9',{'covers':'whole_entrance','landmark':'e22'}),access_blocking_object=B('e22',{'obstruction':'e9'}),evidence=[257,258,260,261,264,268],note='Entrance-crossing string is actual obstruction; route necessity is separate from claiming every passer has already traversed the gate.')
F(271,spatial_configuration=B('e9',{'height':'high'},'q13','attributed_claim',factuality='hypothetical'))
F(287,spatial_configuration=B('e31',{'landmark':'e32','relation':'leaning_beside'}))
F(316,motion_source=B('e14',{'landmark_id':'e22','role':'away_from'}),motion_control=B('e14',{'controller':'e3'}))
F(356,spatial_configuration=B('e71',{'landmark':'e4','relation':'behind'}))
F(363,spatial_configuration=B('e33',{'landmark':'e22','relation':'above'}),attributes=[{'name':'decoration_state','value':'bare'}])
F(371,event_state_change=B('e9',{'before':'tied_across_gate','after':'untied','event_id':EV['untie_gate']}),causal_parent=B('e22',{'cause':EV['untie_gate'],'effect':EV['cart_through']},status='candidate'),evidence=[258,261,371,373,387,389,422,424,427],note='Unfastening and relocation explain restored passage; the text states the acts and subsequent crossing without specifying clearance measurements.')
F(389,object_shape=B('e9','coiled'),possession_holder=B('e9',{'holder':'e1'}))
F(398,attributes=[{'name':'decoration_state','value':'still_empty'}])
F(422,access_clearance=B('e28',{'passage':'e22','fits':True}),motion_route=B('e28',{'landmark_id':'e22','role':'through'}))
F(433,motion_destination=B('e28',{'landmark_id':'e21','role':'toward_not_arrival'}))
F(440,spatial_configuration=B('e36',{'landmark':'e38','relation':'around'}))
F(445,spatial_configuration=B('e38',{'landmark':'e37','relation':'beside'}))
F(452,quantity_comparison={'figure':'e36','comparison':'e33','dimension':'available_hanging_stretch','relation':'shorter','scope_id':'s0','assertion_status':'asserted'},evidence=[449,450,452,453,456],note='Shorter compares the hanging span, not precise whole-object perimeter measurements.')
F(460,object_surface_condition=B('e39','smooth'))
F(461,material_composition=B('e39','wood'))
F(466,access_clearance=B('e36',{'people_can_pass_alongside':True}))
F(470,motion_route=B('e9',{'landmark_id':'e40','role':'along'}))
F(478,possession_holder=B('e8',{'holder':'e3'}),spatial_support=B('e8',{'supported_by':'e41'}),object_stability=B('e8','held_steady'))
F(493,event_state_change=B('e9',{'after':'sagging','event_id':EV['sag']}),object_tension_state=B('e9','slack'))
F(495,object_tension_state=B('e9','too_loose','q20','attributed_claim'))
F(499,event_state_change=B('e9',{'dimension':'tension','change':'increased','event_id':EV['tighten']}))
F(504,figurative_mapping={'target_id':'e9','source_image':'trying_agent','kind':'excess_tension_personification','literal_event':False},object_tension_state=B('e9','too_tight','q21','attributed_claim'),evidence=[499,500,501,503,504,506,508,509,511,513],note='Rafi warns humorously about excess tension. No actual fence fall or intention possessed by string is inferred.')
F(513,event_state_change=B('e9',{'dimension':'tension','change':'reduced_from_too_tight','event_id':EV['ease']}))
F(517,spatial_configuration=B('e42',{'landmark':'e40','relation':'around'}),event_result_entity=B('e42',{'formed_in':'e9','event_id':EV['rail_knot']}))
F(530,event_iteration=B('e9',{'event_id':EV['wrap'],'count':2,'part_of_knot_event':EV['rail_knot']}))
F(535,object_tension_state=B('e9','snug'),supporting_event_ids=[EV['rail_knot'],EV['wrap']])
F(548,figurative_mapping={'target_id':'e17','source_image':'seeing_observer','kind':'display_viewpoint_personification','literal_event':False},evidence=[545,546,547,548,551],note='Moon flag is a paper object placed for a good view; no literal visual perception or celestial moon is introduced.')
F(561,appearance_color=B('e44','yellow'))
F(562,material_composition=B('e44','paper'))
F(565,spatial_configuration=B('e17',{'landmark':'e43','relation':'at','beside':'e44'}),evidence=[552,553,555,558,563,564,565,566,567],note='Rafi chooses the position; Bea actually ties his moon there. Permission to tie a flag is not substituted for the actual actor.')
F(575,spatial_configuration=B('e72',{'relation':'spaced_apart_along_rail','landmark':'e40'}),event_goal_role=B('e72',{'event_id':EV['leave_gaps'],'goal_content_id':'p33'}))
F(591,spatial_configuration=B('e11',{'landmark':'e37','relation':'curves_around'}),figurative_mapping={'target_id':'e11','source_image':'rainbow','kind':'colorful_bunting_metaphor','literal_event':False})
F(603,access_blocking_object=B('e22',{'obstruction_absent':True,'scope':'described_gate_route'}))
F(610,attributes=[{'name':'decoration_state','value':'still_bare'}])
F(635,object_temperature=B('e47','warm'),affect_observer_attribution={'experiencer_id':'e1','cue':'warm_cheeks_after_expectation_comment','interpretation':'self_consciousness_or_embarrassment','scope_id':'s0','assertion_status':'candidate'},evidence=[620,622,628,629,630,634,635,636,637],note='Warm cheeks are explicit; embarrassment is a context-supported possibility, not a stated diagnosis or permanent trait.')
F(647,access_reachability=B('e11',{'actor':'e3','reachable':True},'q26','attributed_claim'))
F(655,appearance_color=B('e48','silver'))
F(657,evidence=[649,650,652,654,655,656,657,659],note='Sun here is real illumination, distinct from the adjacent yellow paper sun e44.')
F(660,reference_unresolved=True,antecedent_candidates=['e17','e11'],identity_hypothesis={'candidate_ids':['e17','e11'],'scope_id':'q27','assertion_status':'candidate'},evidence=[650,652,660,661,662,664,667,669,671],note='It may refer to the moon just turned or to the overall display; the following all-flags sentence supports the broader reading without eliminating the local moon reading.')
F(664,spatial_viewpoint=B('e70',{'observer':'e3','location':'current_Rafi_position'},'q27','attributed_claim'))
F(669,access_visibility=B('e72',{'observer_kind':'generic_viewer_at_current_position','visible':True,'quantification':'every_display_flag'},'q28','attributed_claim'))
F(683,possession_holder=B('e50',{'holder':'e5'}),transfer_source=B('e50',{'source_group':'e10'}))
F(692,transfer_kind=B('e50','handoff_for_participation'),transfer_source=B('e50',{'source':'e5'}),transfer_recipient=B('e50',{'recipient':'e6'}),transfer_completion=B('e50',{'completed':True}),possession_holder=B('e50',{'holder':'e6'}))
F(722,material_composition=B('e51','paper'),object_shape=B('e51','loaf'),evidence=[717,718,722,768,769],note='Later paper loaf retrospectively clarifies loaf-shaped flag, not actual bread tied to the string. Baker identity is not explicitly Duran.')
F(728,appearance_color=B('e52','blue'))
F(729,object_shape=B('e52','star'),identity_hypothesis={'candidate_same_as':'e50','scope_id':'s0','assertion_status':'candidate'},evidence=[687,692,693,697,725,726,729],note='Girl receives an unspecified flag, then chooses blue star. They may be identical, but no forced identity or extra exchange is added.')
F(734,appearance_color=B('e53','red'));F(735,object_shape=B('e53','square'))
F(749,event_state_change=B('e54',{'after':'lit','event_id':EV['lanterns_on']}),object_luminosity=B('e54','lit'))
F(753,object_stability=B('e9','holds_firm'),spatial_configuration=B('e9',{'landmark':'e36','relation':'along'}))
F(762,spatial_configuration=B('e17',{'landmarks':['e44','e51'],'relation':'between'}))
F(771,motion_direction=B('e3',{'direction':'down','event_id':EV['rafi_reach_down']}))
F(775,antecedent_candidates=['e17'],evidence=[760,761,762,769,770,771,774,775,776,777],note='Pointed tip is resolved to the crescent moon flag despite the nearer loaf mention; source does not introduce a new moon.')
F(784,motion_route=B('e56',{'landmark_id':'e22','role':'through'}),motion_destination=B('e56',{'landmark_id':'e13','role':'into'}),evidence=[780,781,782,783,784,788,791],note='Last basket is rolled into square; cart use in this ending clause is not explicitly restated. No count of earlier baskets is inferred.')
F(795,appearance_color=B('e52','blue'))
F(797,spatial_configuration=B('e52',{'landmark':'e17','relation':'beside'}),causal_parent=B('e52',{'cause_entity':'e45','effect_event':EV['star_spins']}),evidence=[796,797,798,800],note='Spin occurs in breeze. No actor or time is supplied for attaching the chosen star, so its final display position is retained without inventing a tying event.')
for w,part,whole in [(56,'e15','e57'),(110,'e16','e15'),(151,'e18','e3'),(193,'e23','e22'),(199,'e24','e3'),(203,'e25','e9'),(256,'e30','e14'),(368,'e34','e33'),(392,'e35','e1'),(462,'e39','e36'),(476,'e40','e36'),(484,'e41','e3'),(555,'e43','e9'),(634,'e47','e1'),(656,'e48','e17'),(777,'e55','e17')]:F(w,part_whole_relation={'part_id':part,'whole_id':whole,'scope_id':a.words[w]['scope_id']})
# House is in the village rather than a component manufactured into the village.
a.words[56].pop('part_whole_relation',None)

# Contents and goals retain their holders and are distinct from completed actions.
F(19,request_action_id='p1')
F(32,promise_content_id='p1',promise_beneficiary_id='e2',plan_commitment_status='promised',temporal_deadline={'event_id':EV['return'],'before':'time_supper'},evidence=[1,3,12,13,15,16,31,32,744,752,753],note='Return before supper is promised; evening string stability neither confirms spool return nor establishes that supper/deadline passed. No broken-promise judgment is added.')
F(34,goal_owner_id='e1',goal_content_id='p4',goal_polarity='achieve',goal_status='planned',goal_beneficiary_ids=['e3'],goal_resource_ids=['e8','e9','e10'],goal_scope_bundle={'owner_id':'e1','intention_event_id':EV['plan'],'scope_id':'s0','assertion_status':'asserted'})
F(84,goal_owner_id='e1',goal_content_id='p5',goal_polarity='achieve',goal_status='desired',goal_beneficiary_ids=['e3'],evidence=[84,85,87,89,90,91,517,520,565,718,732],note='Rafi eventually ties the rail knot. The source does not establish this is the last knot overall, and Bea later ties his moon while other participants also tie flags.')
F(123,utterance_evidence_type='self_report_of_creation',supporting_event_ids=[EV['fold_moon']])
F(137,request_action_id='p8',cooperation_goal_id='p4',social_relation_participants={'members':['e1','e3']})
F(139,disclosure_content_id='p10')
F(154,request_action_id='p11',request_acceptance_status='accepted_by_Bea')
F(159,permission_grantor_id='e1',permission_recipient_id='e3',permission_content_id='p11',permission_status='granted',dialogue_response_to_id=EV['ask_choice'],evidence=[152,153,154,155,158,159],note='Of course answers permission to choose position. It does not mean the choice or attachment has already occurred.')
F(161,request_action_id='p12')
F(165,permission_grantor_id='e1',permission_recipient_id='e3',permission_content_id='p12',permission_status='affirmed_in_context',goal_priority='active_participation',dialogue_response_to_id=EV['ask_tie'],evidence=[160,161,162,163,165,166],note='Bea endorses tying as important. Actual later moon attachment is by Bea; endorsement is not rewritten as completed Rafi attachment.')
F(188,cooperation_goal_id='p4',cooperation_commitment='joint_work_observed',social_relation_participants={'members':['e1','e3']})
F(242,disclosure_content_id='p16',communication_intended_effect='report_access_obstruction')
F(274,plan_commitment_status='proposed_not_adopted',intention_holder_id='e4',intention_content_id='p17')
F(292,imaginer_id='e1',imagined_content_id='p19',imagined_world_id='world_rejected_high_layout',imagination_function='consider_participation_consequence',evidence=[283,286,291,292,293,294,298,300,303,305,306,310],note='Holding-only alternative is imagined and rejected. Rafi is not actually left holding a flag while a replacement climber hangs it.')
F(range(293,305),semantic_world_id='world_rejected_high_layout')
F(306,reasoner_id='e1',reasoning_mode='compare_with_invitation_goal',reasoning_content_id='p19',reasoning_conclusion_id='p46',evidence=[305,306,307,308,310,311,313],note='The positive purpose proposition p20 is the negation target; the reasoning conclusion p46 is its explicit negative. The earlier invitation itself is not negated.')
F(333,request_action_id='p21',goal_owner_id='e3',goal_content_id='p21',goal_polarity='achieve',goal_status='explicit_requirement')
F(340,negation_scope_id='p22',proposition_polarity='negative',evidence=[323,324,327,330,334,335,337,338,339,340,343],note='Non-entanglement is required of the proposed location; no actual wheel snag or completed inspection of every possible wheel is asserted.')
F(376,intention_holder_id='e1',intention_content_id='p23',plan_commitment_status='earlier_plan_revised')
F(408,intention_holder_id='e1',intention_content_id='p24',plan_commitment_status='proposed_then_adopted',plan_revision={'replace':'gate_spanning_layout','with':'p24','adoption_events':[EV['unwind_fence'],EV['rail_knot']]})
F(418,goal_tradeoff={'holder_id':'e1','prefer':'unblocked_access_and_reachable_participation','relax':'largest_square_spanning_rainbow','scope_id':'q18','assertion_status':'attributed_claim'},evidence=[374,376,380,381,399,400,402,409,410,411,414,415,417,418,419])
F(431,dialogue_response_to_id=EV['fence_proposal'],dialogue_turn_function='approve_revised_plan')
F(486,disclosure_content_id='p29',utterance_evidence_type='observed_line_sag',supporting_event_ids=[EV['sag']])
F(504,communication_scope_bundle={'speaker_id':'e3','utterance_event_id':EV['tight_joke'],'scope_id':'s0','assertion_status':'candidate'},evidence=[486,494,495,497,498,499,502,504,506,510,511,513],note='Unattributed tension joke is assigned to Rafi from turn continuity: he monitors tension, Bea adjusts, and she laughs and eases it. This is contextual speaker resolution.')
F(525,utterance_content_id='p42',communication_intended_effect='demonstrate_double_wrap',supporting_event_ids=[EV['wrap'],EV['pull_snug'],EV['rail_knot']])
F(544,request_action_id='p31',knowledge_gap_content_id='p31')
F(545,dialogue_response_to_id=EV['ask_moon_where'])
F(553,intention_vs_action_alignment={'intention':'p11','outcome_event_id':EV['choose_middle'],'alignment':'choice_exercised','scope_id':'s0','assertion_status':'asserted'})
F(565,intention_vs_action_alignment={'earlier_permission':'p12','actual_event_id':EV['tie_moon'],'actual_actor_id':'e1','permission_recipient_id':'e3','alignment':'Bea_attaches_Rafi_chosen_flag','scope_id':'s0','assertion_status':'asserted'},evidence=[161,162,165,552,553,555,564,565,566])
F(622,belief_holder_id='e65',belief_content_id='p35',epistemic_attitude_kind='prior_expectation',epistemic_time_scope={'belief':'p35','phase':'before_current_inspection'},epistemic_scope_bundle={'holder_id':'e65','attitude_event_id':EV['expect'],'scope_id':'q24','assertion_status':'attributed_claim'})
F(630,belief_holder_id='e1',belief_content_id='p36',epistemic_attitude_kind='acknowledged_knowledge',epistemic_scope_bundle={'holder_id':'e1','attitude_event_id':EV['know'],'scope_id':'q25','assertion_status':'attributed_claim'})
F(632,dialogue_response_to_id=EV['expect_report'],dialogue_turn_function='acknowledge_then_explain')
F(647,reasoner_id='e1',reasoning_mode='justify_accessible_layout',reasoning_content_id='p37',reasoning_conclusion_id='p24',reasoning_scope_bundle={'reasoner_id':'e1','reasoning_event_id':EV['access_explain'],'scope_id':'q26','assertion_status':'attributed_claim'})
F(661,viewpoint_evaluative_stance={'holder_id':'e3','content_id':'p39','scope_id':'q27','assertion_status':'attributed_claim'})
F(704,request_action_id='p41',request_acceptance_status='no_explicit_verbal_response',evidence=[692,697,702,703,704,706,707,725,726,729,796,797],note='Girl is invited to tie and later chooses a star; ending shows the star in the display. Source does not state who attaches it, so no completed tying by the girl is invented.')
F(738,utterance_content_id='p42',communication_intended_effect='teach_double_wrap_to_Bell',supporting_event_ids=[EV['rail_knot'],EV['wrap']],evidence=[517,520,525,530,533,735,737,738,739,741,742],note='Rafi gives Bell a new demonstration of the same method; this is a distinct act from his earlier demonstration to Bea.')
F(797,narrative_thread_id='thread_reachable_welcome_display',narrative_change_dimension='largest_gate_display_revised_for_access_and_shared_participation',narrative_resolution_evidence={'outcome_events':[EV['cart_through'],EV['rail_knot'],EV['choose_middle'],EV['tie_moon'],EV['knot_red'],EV['last_basket'],EV['star_spins']],'resolved':'clear_gate_and_shared_display_observed','assertion_status':'candidate'},narrative_theme_candidate={'content':'welcome_requires_access_and_meaningful_participation','assertion_status':'candidate'},narrative_motif_link={'earlier_words':[44,47,48,84,87,90,258,261],'ending_words':[591,603,610,738,753,762,784,797],'relation':'rainbow_changes_route_while_gate_and_participation_stay_open','assertion_status':'candidate'},narrative_closure_candidate={'image':'silver_moon_and_blue_star_beside_clear_gate','assertion_status':'candidate'},evidence=[47,48,84,87,258,261,292,306,371,400,517,553,565,603,610,647,704,738,753,762,784,797],note='Ending proves a usable gate, stable display and several contributions. It does not prove Rafi attached his moon, tied the final knot, spool return, or all possible disability-access claims.')

a.proposition('p44','The moon flag needs a place to hang and flutter.',[124,125,127,129],scope_id='q4')
a.proposition('p46','Bea did not invite Rafi merely to hold a flag while someone else tied it.',[305,306,307,308,310,311,313],scope_id='s0')
a.proposition('p45','We need a place where people can roll through and where flags will not get caught in wheels.',[323,324,326,328,329,330,337,338,340,343],scope_id='q16')
F(585,referent_kind='bound_variable',quantifier_domain_restriction={'domain_id':'e72','operator':'each'})
F(704,verb_form='bare');a.words[704].pop('tense',None)
F(569,group_members=['e17','e44'],evidence=[563,565,569,718,732,796,797],note='Initial fence display has the moon and paper sun plus unspecified flags. Later loaf, red square and blue star belong to later membership phases, not this adding event or the early every-flag visibility claim.')
F(354,evidence=[172,174,344,346,352,354,356],note='Additional arriving helpers are distinct from the earlier helpers already setting out tables; no whole-group arrival is inferred.')

feedback={
 'summary':'Festival annotations preserve changes in gate clearance, reachable hanging, author/chooser/tyer roles and the distinct spool/string identities. Figurative rainbow, bossy wind, trying string and seeing moon are separated from physical states.',
 'ambiguities':[
 {'words':[12,13,32,744,752,753],'issue':'Return before supper is promised but unobserved. Evening does not establish deadline passed; string in use does not imply spool return or breach.'},
 {'words':[161,162,517,553,565],'issue':'Rafi is allowed to tie and actually ties rail knot, but Bea ties his moon at his chosen position. No false Rafi attachment or total goal fulfillment is added.'},
 {'words':[660,661,664,671],'issue':'It looks better may refer to moon or overall bunting; reference placeholder retains both.'},
 {'words':[687,692,729,796],'issue':'Unspecified flag handed to girl may be blue star, but explicit identity and attachment actor are absent.'},
 {'words':[717,722,782,783],'issue':'Baker tying paper loaf is not explicitly Duran; no forced identity.'},
 {'words':[93,95,206,208],'issue':'Spool moves from Bea carrying to Rafi holding without narrated handoff; no transfer invented.'},
 {'words':[174,177,179,180],'issue':'Folding tables interpreted as portable table type in coordinated set-out list; source surface could also admit folding activity reading.'},
 {'words':[486,497,504,510,511],'issue':'Unattributed too-tight joke assigned to Rafi through turn continuity, recorded as candidate speaker interpretation.'},
 ],
 'feature_gaps':[],
 'prompt_feedback':[
 'Separate permission, choosing, tying, and final object position; source can distribute these actions among different participants.',
 'Treat a planned last action separately from an observed action of the same kind when more actions follow.',
 'Preserve borrowed container versus used material identity, and do not infer deadline failure solely from an evening ending.',
 'Accessibility claims should bind the stated person, task and route, without inferring diagnoses or general incapacity.',
 'Methods can recur in distinct teaching acts while the underlying earlier wrapping event remains singular.',
 ],
 'coverage_notes':'All 804 words across 36 paragraphs receive contextual POS and lemma. Full frozen v3 catalog used sparsely with whole-story retrospective interpretation and no causal filter.',
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
