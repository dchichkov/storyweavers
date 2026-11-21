from .schema import *
SPEC=story(13,'costume',dict(
 hero=person('Nia','she'),helper=person('Rafi','he'),teacher=person('Ms Vale','she'),
 work=place('theatre'),bench=place('costume cupboard'),box=place('prop box'),
 cape=obj('golden cape',location='bench',state=('intact',)),robe=obj('Moon robe',location='helper'),
 disk=obj('Sun disk',location='box'),ribbons=obj('blue ribbons',location='hero',number='plural',pronoun='they')),
 chain(
  event('wind_wish',Say('hero',V('want',R('cape'))),S('helper',V('hold',R('robe'))),
   qa=[Q('goal','what','What did Nia want to wear?','Nia wanted the golden cape. Rafi held a Moon robe.','hero','helper','cape','robe')]),
  event('borrow_cape',S('hero',V('borrow',R('cape'))),patient='cape',destination='hero',guards=[at('cape','bench')],effects=[change('cape',location='hero')],portable='fetch'),
  event('wrong_costume',Say('helper',V('need',N('Sun costume',det='a')),listener='hero'),actor='helper',
   qa=[Q('problem','why','Why was Rafi unhappy with his costume?','Rafi needed a Sun costume. He was holding a Moon robe.','helper','robe',supports=('goal',))]),
  event('share_cape',S('hero',V('give',R('helper'),R('cape'))),patient='cape',destination='helper',guards=[at('cape','hero'),together('hero','helper')],effects=[change('cape',location='helper')],portable='transfer',
   qa=[Q('choice','who','Who gave up the golden cape?','Nia gave the cape to Rafi. He needed a Sun costume.','hero','helper','cape',supports=('problem',))]),
  event('dragging_hem',S(Poss('cape','hem'),B('long')),Say('hero',Can(V('help',P('you')))),patient='cape',guards=[at('cape','helper')],effects=[change('cape',add=('tripping_risk',))]),
  fork('clear_hem',
   event('gather_front',S('helper',V('gather',Poss('cape','front'))),actor='helper',patient='cape',guards=[at('cape','helper'),has('cape','tripping_risk')],effects=[change('cape',add=('gathered','safe'),remove=('tripping_risk',))]),
   event('lift_hem',S('helper',V('lift',Poss('cape','hem'))),actor='helper',patient='cape',guards=[at('cape','helper'),has('cape','tripping_risk')],effects=[change('cape',add=('lifted','safe'),remove=('tripping_risk',))])),
  event('fetch_sun',S('hero',A(V('fetch',R('disk')),PP('from',R('box')))),patient='disk',destination='hero',guards=[at('disk','box')],effects=[change('disk',location='hero')],portable='fetch'),
  event('give_sun',S('hero',V('give',R('helper'),R('disk'))),patient='disk',destination='helper',guards=[at('disk','hero')],effects=[change('disk',location='helper')],portable='transfer',
   qa=[Q('sun','how','What helped Rafi look like the Sun?','Nia gave Rafi the Sun disk. He also had her golden cape.','hero','helper','disk','cape',supports=('choice',))]),
  event('perform_together',S('helper',V('raise',R('disk'))),S('hero',A(V('swirl'),PP('with',R('ribbons')))),patient='ribbons',
   guards=[has('cape','safe'),at('disk','helper'),at('ribbons','hero')],effects=[change('hero',add=('performed',)),change('helper',add=('performed',))],
   qa=[Q('performance','what_next','How did both children take part?','Rafi raised the Sun disk. Nia swirled with her blue ribbons.','hero','helper','disk','ribbons')]),
  event('return_costume',S('helper',A(V('hang',R('cape')),PP('in',R('bench')))),S(R('cape'),V('shine')),actor='helper',patient='cape',destination='bench',
   guards=[at('cape','helper'),has('hero','performed'),has('cape','intact')],effects=[change('cape',location='bench')],portable='put_item',
   qa=[Q('return','where','Where did the cape end up?','Rafi hung the cape in the costume cupboard. Its gold still shone.','helper','cape','bench')])
 ),target='cape',tool_id='disk',premise='Nia lends her coveted cape so Rafi can look like the Sun without damaging a borrowed costume.',
 fidelity='Share the cape, gather its trailing hem instead of cutting it, perform with ribbons and return the costume intact.',variants=['Gather the front or lift the hem.'])
