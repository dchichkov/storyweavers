"""Short scene plays rendered only from the committed state and local outcome."""


def render(scene_id, p, before, after):
    if scene_id == 'notice':
        weather = ('The greenhouse roof ticked in the heat.' if p.heat == 'hot'
                   else 'Warm afternoon light rested on the greenhouse panes.')
        return (f'{weather} Mina found Rosa’s seedling tray drooping at the bench edge; '
                'the little leaves pointed down like tired fingers. Ivo’s note beside the blue '
                'watering can said, “If Rosa’s starts look thirsty, use this. Please bring it '
                'back rinsed.” Mina wanted to help before Rosa returned.')
    if scene_id == 'borrow_can':
        return ('Mina lifted the blue can from its rack, careful not to scrape the other tools. '
                'The handle wobbled, and she tested its weight with both hands. “I’ll bring it '
                'back clean,” she told the quiet greenhouse. The can was still Ivo’s; for now, '
                'it was useful in Mina’s hands, not hers to keep.')
    if scene_id == 'read_labels':
        return ('At the tray, Mina read Rosa’s marker: “Keep evenly moist; don’t flood the new '
                'roots.” A spare rubber band held the marker to its stake. Mina slipped it off '
                'and kept it beside the label, noticing that the words made the job smaller: '
                'water the cells, not the whole bench. She left the marker where Rosa could find it.')
    if scene_id == 'talk_to_rosa':
        if p.shade_cloth:
            return ('Rosa came in with compost on her gloves. “They’re thirsty, but don’t leave '
                    'them baking after you water.” She pointed Mina to a rolled screen on the '
                    'north rack. “That one still slides. I’ve been meaning to put it up.” Mina '
                    'listened, then asked how far the screen should sit above the leaves.')
        return ('Rosa came in with compost on her gloves. “The screen roll is gone,” she said, '
                'seeing Mina look toward the rack. She showed her the cool shelf tucked beside '
                'the water tank. “Move the tray there for the afternoon. It’s not perfect, but '
                'it keeps the leaves out of the sharpest sun.” Mina nodded and made room.')
    if scene_id == 'fill_and_water':
        if after['band.used']:
            opening = ('The rubber band held the split seam while Mina filled the can. '
                       'Following the label, she poured into the seedling cells in measured turns. ')
        elif p.can_leak:
            opening = ('A thread of water escaped through the split seam as Mina filled the can. '
                       'She watched one measure splash into the drain, then poured what remained '
                       'carefully into the seedling cells. ')
        else:
            opening = ('The can filled without a drip. Mina bent close and poured into the '
                       'seedling cells instead of soaking the whole bench. ')
        if after['seedling.status'] == 'watered':
            ending = ('The soil darkened evenly. It had received enough for the roots to drink, '
                      'though Mina knew water alone would not stop the hot light.')
        else:
            ending = ('The soil darkened, but some cells stayed pale. Mina stopped rather than '
                      'pretend the small supply could do more than it could.')
        return opening + ending
    if scene_id == 'make_shade':
        if after['seedling.shade'] == 'screen':
            return ('With Rosa’s directions in mind, Mina drew the screen down above the tray, '
                    'leaving air around the leaves. The hard glare softened to a greenish glow. '
                    'The soil was damp; now the seedlings had a cooler place to settle instead '
                    'of facing the full afternoon sun.')
        if p.shade_cloth:
            return ('Rosa had not shown Mina the screen, so she did not pull at the rack. Mina '
                    'slid the tray onto the cool shelf beside the tank, where the wall cast a '
                    'broad shadow. It was a modest shelter, not a cure, but the leaves no longer '
                    'sat in the sharpest band of light.')
        return ('There was no shade cloth on the rack. Mina slid the tray onto the cool shelf '
                'beside the tank, where the wall cast a broad shadow. It was a modest shelter, '
                'not a cure, but the leaves no longer sat in the sharpest band of light. She '
                'kept the labels facing outward.')
    if scene_id == 'return_can':
        if before['band.used']:
            return ('Mina rinsed the blue can at the sink and unwound the rubber band from its '
                    'spout. She clipped it back to Rosa’s marker before hanging the can on Ivo’s '
                    'rack. The borrowed tool had carried water where it mattered, and it was '
                    'clean and ready for the next gardener.')
        return ('Mina rinsed the blue can at the sink and hung it on Ivo’s rack, handle facing '
                'out. She checked that no water remained pooled in its bottom. The borrowed '
                'tool had carried water where it mattered, and it was clean and ready for the '
                'next gardener.')
    if scene_id == 'ending_stable':
        return ('The seedlings stood steadier beneath the screen, their roots damp and the harsh '
                'light off their leaves. Mina could not make them grow in an instant, but the '
                'tray was watered, sheltered, and safe for the afternoon. She had protected '
                'Rosa’s starts without keeping Ivo’s can or wasting what the shared tank held.')
    if scene_id == 'ending_cuttings':
        return ('The tray was sheltered, but its thirsty starts were too weak to call saved. '
                'Mina pinched two still-firm tips and rooted them in damp compost plugs, writing '
                'Rosa’s name beside them. The original tray had not been rescued; something '
                'living had. Mina had returned the can and faced the result honestly.')
    raise ValueError(f'No prose for scene: {scene_id}')
