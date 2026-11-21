from .schema import *

SPEC=story(4,'seaside',dict(
    hero=person('Tessa','she',memes={'Desire':.8}),helper=person('Milo','he'),
    work=place('seaside'),bench=place('garden wall'),pool=place('sheltered pool'),
    map=tool('map',location='bench'),book=obj('sketchbook',location='hero',state=('blank',)),
    tide=obj('tide',state=('low',)),anemone=obj('green anemone',location='pool',state=('closed',))),
    chain(
        event('windy_pages',S(R('book'),B('windblown')),Say('hero',V('want',V('draw',N('sea')))),patient='book',
            qa=[Q('goal','what','What did Tessa want to do?','Tessa wanted to draw the sea. Her sketchbook was windblown.','hero','book')]),
        event('fetch_map',S('hero',A(V('fetch',R('map')),PP('from',R('bench')))),patient='map',destination='hero',
            guards=[at('map','bench')],effects=[change('map',location='hero')],portable='fetch'),
        event('wrong_landmark',S('hero',V('follow',N('bathhouse path'))),Say('helper',B('worried'),listener='hero'),
            effects=[change('hero',add=('wrong_turn',)),change('tide',add=('rising',),remove=('low',))],
            qa=[Q('mistake','where','Which wrong path did Tessa follow?','Tessa followed the bathhouse path. Milo was worried.','hero','helper')]),
        event('rising_water',S(R('tide'),B('high')),Say('hero',V('need',V('turn'))),patient='tide',guards=[has('tide','rising')],
            qa=[Q('danger','why','Why did Tessa decide to turn back?','The tide was high. Tessa said she needed to turn back.','hero','tide')]),
        fork('check_direction',
            event('milo_reads_map',S('hero',V('give',R('helper'),R('map'))),actor='hero',patient='map',destination='helper',
                guards=[at('map','hero'),together('hero','helper')],effects=[change('map',location='helper')],portable='transfer'),
            event('tessa_checks_map',S('hero',V('check',R('map'))),patient='map',guards=[at('map','hero')],effects=[change('hero',add=('checked_map',))])),
        event('safe_steps',S(Both(R('hero'),R('helper')),V('follow',N('upper path'))),
            guards=[has('hero','wrong_turn')],effects=[change('hero',add=('safe_route',),remove=('wrong_turn',)),change('helper',add=('safe_route',))],
            qa=[Q('route','how','How did the children leave the unsafe path?','Tessa and Milo followed the upper path. The tide below was high.','hero','helper','tide',supports=('danger',))]),
        event('sheltered_sketch',S('hero',A(V('draw',N('sea')),PP('in',R('book')))),S('helper',V('watch',R('anemone'))),patient='book',
            guards=[has('hero','safe_route')],effects=[change('book',add=('sea_drawing',),remove=('blank',))],
            qa=[Q('drawing','who','Who drew while Milo watched the anemone?','Tessa drew the sea in her sketchbook. Milo watched the green anemone.','hero','helper','book','anemone')]),
        event('pool_flower',S(R('anemone'),A(V('open'),'slowly')),S(R('book'),B('still')),patient='anemone',
            guards=[has('book','sea_drawing')],effects=[change('anemone',add=('open',),remove=('closed',))],
            qa=[Q('outcome','what_next','What changed at the sheltered pool?','The green anemone opened slowly. Tessa’s sketchbook stayed still.','anemone','book')])
    ),target='book',tool_id='map',premise='A mistaken seaside landmark leads to rising water; the children need the safe upper path.',
    fidelity='Mistake the bathhouse for the rock landmark, turn back before the tide, reach shelter and observe the anemone.',
    variants=['Milo receives the map or Tessa checks it herself before taking the upper path.'])
