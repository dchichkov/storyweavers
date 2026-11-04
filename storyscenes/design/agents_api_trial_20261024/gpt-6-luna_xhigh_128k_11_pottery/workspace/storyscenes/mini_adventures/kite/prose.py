'''Scene-local narration grounded in the actions and state of this pottery play.'''


def render(scene_id, params, before, after):
    if scene_id == 'borrow_rib':
        return ('“Can I borrow your wooden rib, Mrs. Vale?” Mina asked. “I want to make Grandpa a cup he can hold with his stiff fingers.” Mrs. Vale turned the tool over. “Bring it back clean; I need it for the next bowl.” Mina promised, and the rib left its peg for her worktable.')
    if scene_id == 'old_handle_memory':
        return ('Mina looked at the old cup she had sketched in her notebook. Grandpa’s broad handle had a thumb hollow where his stiff fingers could rest. She remembered him turning the cup until his thumb found that comfortable dent. “Not fancy,” she murmured. “Just easy to hold.”')
    if scene_id == 'wedge_clay':
        if params.sponge_damp:
            return ('Mina carried a lump of clay from the covered tray and kneaded it beside the wheel. The sponge was already damp, not dripping. She wiped a thin film of water across the wheel, then pressed until the lump stopped wobbling under her palms. “Quiet clay,” Mrs. Vale said. Mina smiled and centered it.')
        return ('Mina carried a lump of clay from the covered tray. The dry sponge dragged, so she dipped it and squeezed until it stopped dripping. She kneaded the clay beside the wheel, then wiped on a thin film of water. The lump wobbled at first; Mina pressed steadily until it centered.')
    if scene_id == 'shape_cup':
        rim = 'The wheel stayed level, but one part of the rim still rippled.' if params.wheel_level else 'The wheel knocked, and one side of the rim climbed higher.'
        thumb = 'She pinched a thumb hollow into the broad handle, remembering Grandpa’s old cup.' if after['cup.thumb_rest'] else 'She made the handle broad enough for Grandpa’s stiff fingers.'
        return (f'Mina opened the clay and pulled its walls upward. {rim} She drew Mrs. Vale’s borrowed rib along the outside; it smoothed the wall without making the rim perfectly straight. {thumb} She set the raw cup on the drying shelf and saw the flaw clearly.')
    if scene_id == 'sheltered_shelf':
        return ('“My sponge is a puddle,” Omi said. Mina slid her cup into a sheltered cubby, away from the open window, and lent him hers. He wrung it out with both hands. “Thin clay cracks if it dries too fast,” he said. Mina took the sponge back; Omi’s sticky lump was finally ready.')
    if scene_id == 'decide_flaw':
        if after['cup.treatment'] == 'kept':
            return ('The rim leaned, and Mina could not make that disappear. She pinched the lowest edge into a small pouring lip, then smoothed it with the damp sponge. “It will still look crooked,” Omi said. “Yes,” Mina replied. “But Grandpa can pour the last tea without tipping so far.”')
        return ('The rim leaned, and the thin side bothered Mina. She used a small reserve of clay to strengthen it, then compressed the line with Mrs. Vale’s rib. The edge grew more even, though the cup took extra clay and careful pressure. “I chose to mend it,” Mina said, checking that the wall held.')
    if scene_id == 'fire_cup':
        if after['cup.cracked']:
            return ('Mina brushed clear glaze over the cup and loaded it into the kiln. The uneven heat caught its thin wall with a sharp tick. When the cup cooled, a crack ran down one side; it could not safely hold tea. Mina traced the line once, then carried it to the cooling rack.')
        detail = 'The cup had dried slowly in Omi’s sheltered cubby.' if after['cup.slow_dried'] else 'Mina waited while the glazed cup fired and cooled.'
        return (f'Mina brushed clear glaze over the cup and set it in the kiln. {detail} The firing held. When she lifted the cup from the cooling rack, the rim still showed its chosen shape, but there was no crack. She checked the broad handle before carrying it to Grandpa.')
    if scene_id == 'ending_kept':
        thumb = 'His thumb settled into its hollow.' if after['cup.thumb_rest'] else 'His fingers fit around the broad handle.'
        return (f'Mina cleaned the rib and returned it to its peg; Mrs. Vale used it on her next bowl. At home, Grandpa turned the cup in his hands. {thumb} He poured tea from the crooked lip without spilling, took a sip, and grinned. “That works better than my old one.” Mina watched him keep drinking.')
    if scene_id == 'ending_repaired':
        thumb = 'His thumb found the hollow Mina had remembered.' if after['cup.thumb_rest'] else 'The broad handle sat comfortably in his hand.'
        return (f'Mina cleaned the rib and returned it to its peg; Mrs. Vale used it to shape her next bowl. Grandpa ran a finger around the smoother rim. {thumb} He lifted the cup, drank his tea, and set it down without a wobble. “You took your time with this,” he said. Mina nodded, glad she had.')
    if scene_id == 'ending_cracked':
        return ('Mina cleaned the rib and returned it to its peg; Mrs. Vale put it straight to work on a bowl. “The cup cracked,” Mina told Grandpa. “It won’t hold tea.” He set it beside his pencils instead, where it kept them from rolling. “Then it has a job,” he said. Mina helped arrange them, and stayed for tea.')
    raise ValueError(f'No prose for scene: {scene_id}')
