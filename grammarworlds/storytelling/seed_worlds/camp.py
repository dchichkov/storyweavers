from .schema import *
SPEC=story(10,'camp',dict(
 hero=person('Nora','she'),helper=person('Theo','he',memes={'Fear':.8}),father=person('Dad','he'),
 work=place('campground'),bench=place('picnic table'),branch=place('pine branch'),
 lantern=tool('lantern',location='bench',state=('lit',)),rabbit=obj('toy rabbit',location='branch',state=('caught','missing')),
 tent=obj('tent'),collar=obj('blue collar',location='rabbit'),bell=obj('brass bell',location='rabbit')),
 chain(
  event('missing_rabbit',S(R('rabbit'),B('missing')),Say('helper',V('need',R('rabbit')),listener='hero'),Say('hero',Can(V('help',P('you')))),actor='helper',
   qa=[Q('goal','who','Who needed the lost toy rabbit?','Theo needed his toy rabbit. Nora offered to help him.','hero','helper','rabbit')]),
  event('borrow_lantern',S('hero',V('borrow',R('lantern'))),patient='lantern',destination='hero',guards=[at('lantern','bench')],effects=[change('lantern',location='hero')],portable='fetch'),
  event('dark_fork',Say('helper',B('afraid'),listener='hero'),S('hero',A(V('stay'),PP('beside',R('helper')))),actor='helper',
   effects=[change('hero',add=('stays_together',)),change('helper',memes={'Trust':.8})],
   qa=[Q('choice','why','Why did Nora stay beside Theo?','Theo said he was afraid. Nora stayed beside him.','hero','helper')]),
  fork('find_clue',
   event('bell_clue',S('helper',V('hear',R('bell'))),actor='helper',patient='bell',guards=[has('hero','stays_together')],effects=[change('helper',add=('rabbit_located','heard_bell'))]),
   event('collar_clue',S('helper',V('spot',R('collar'))),actor='helper',patient='collar',guards=[has('hero','stays_together')],effects=[change('helper',add=('rabbit_located','saw_collar'))])),
  event('share_light',S('hero',V('give',R('helper'),R('lantern'))),patient='lantern',destination='helper',guards=[at('lantern','hero'),together('hero','helper')],effects=[change('lantern',location='helper')],portable='transfer',
   qa=[Q('light','who','Who held the lantern for the rescue?','Nora gave the lantern to Theo. They stayed together.','hero','helper','lantern',supports=('choice',))]),
  event('reach_from_path',S('hero',A(V('free',R('rabbit')),PP('from',R('branch')))),patient='rabbit',instrument='lantern',destination='hero',
   guards=[at('lantern','helper'),has('lantern','lit'),has('helper','rabbit_located'),has('rabbit','caught')],
   effects=[change('rabbit',location='hero',add=('free',),remove=('caught','missing'))],
   qa=[Q('rescue','how','How did they recover the rabbit?','Nora freed the toy rabbit from the pine branch. Theo held the lantern for her.','hero','helper','rabbit','lantern','branch',supports=('light',))]),
  event('return_rabbit',S('hero',V('give',R('helper'),R('rabbit'))),patient='rabbit',destination='helper',guards=[at('rabbit','hero')],effects=[change('rabbit',location='helper')],portable='transfer'),
  event('return_light',S('helper',A(V('return',R('lantern')),PP('to',R('father')))),actor='helper',patient='lantern',destination='father',guards=[at('lantern','helper')],effects=[change('lantern',location='father')],portable='transfer'),
  event('friendly_shadows',S('helper',A(V('hold',R('rabbit')),PP('beside',R('tent')))),S('helper',V('smile')),actor='helper',patient='rabbit',
   guards=[at('rabbit','helper'),at('lantern','father')],effects=[change('helper',memes={'Fear':.2,'Trust':.9})],
   qa=[Q('outcome','what_next','How did Theo finish the search?','Theo held the toy rabbit beside the tent and smiled. Nora had freed it from the pine branch.','hero','helper','rabbit','tent',supports=('rescue',))])
 ),target='rabbit',tool_id='lantern',premise='Nora and a frightened Theo search together for a toy rabbit at dusk.',
 fidelity='Stay together, use light and the collar/bell clue, free the toy from the path and return the lantern.',variants=['A bell or a blue collar supplies the discovery clue.'])
