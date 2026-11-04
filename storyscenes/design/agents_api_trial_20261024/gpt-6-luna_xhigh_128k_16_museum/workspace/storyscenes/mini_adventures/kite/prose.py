'''Short scene plays rendered from committed state and physical outcomes.'''


def _peg(value):
    return 'lamp-side peg' if value == 'near_torch' else 'screen-side peg'


def _observation(value):
    if value == 'unreadable':
        return 'a washed-out patch'
    quality, size = value.split('_')
    adjective = 'crisp' if quality == 'clear' else 'soft'
    shape = 'little' if size == 'small' else 'wide'
    return f'a {adjective}, {shape} outline'


def _ending_extras(state, outcome):
    extras = []
    if state['visitor.present']:
        if outcome == 'honest_inconclusive':
            extras.append('June stayed to read the honest note.')
        else:
            extras.append('June stayed to see the larger shape.')
    if state['sketch.made']:
        if outcome == 'honest_inconclusive':
            extras.append('Tavi clipped his first sketch beside it.')
        else:
            extras.append('Tavi clipped his first sketch beside the marks.')
    return ' '.join(extras)


def render(scene_id, params, before, after):
    if scene_id == 'borrow_torch':
        return ('Mara had volunteered to make the museum’s shadow exhibit work before Saturday’s visitors arrived; '
                'her cousin Tavi wanted to know why its poster promised a giant silhouette. Mr. Bell lent them '
                'the squat torch. Mara checked its beam against the bare wall, then Tavi carried the paper figure '
                'to the marked table. “Bring it back with a useful answer,” Bell said.')

    if scene_id == 'first_demo':
        seen = _observation(after['shadow.first_observation'])
        return (f'Mara aimed the borrowed torch at the paper figure, still on the screen-side peg. The screen held '
                f'{seen}. She compared it with the poster’s enormous silhouette. “I’m puzzled,” she admitted. '
                'Tavi stopped her from moving everything at once. “Keep the screen still. We’ll read the label and '
                'change one distance.” Their first outline stayed on the wall as evidence.')

    if scene_id == 'read_label':
        printed = _peg(after['label.target'])
        return (f'After the first try, Tavi read the small print: “Put the figure on the {printed} for a giant '
                'shadow.” The poster promised a shape far bigger than the one they had seen. “So the card might be '
                'right,” Mara said, “or it might be bragging.” Tavi tapped both painted marks. “Let’s check one thing '
                'at a time.” They left the label untouched.')

    if scene_id == 'vignette_visitor':
        return ('June, waiting at the next table, frowned at the odd shadow and called it a ghost. Tavi held up '
                'the paper figure; Mara moved her hand away from the screen so June could see the shape had no '
                'teeth. June laughed and stayed to watch. “Show me when you solve it,” she asked. They promised '
                'no magic tricks, only a fair test.')

    if scene_id == 'vignette_sketch':
        return ('Tavi drew the first shadow exactly as it appeared, even though Mara wanted to make it grander. '
                'He marked the screen-side peg beneath the small outline. “If we improve the picture too, we’ll '
                'fool ourselves,” he said. Mara put her pencil beside his instead of correcting it. The sketch '
                'made their first trial something they could compare, not just remember.')

    if scene_id == 'inspect_setup':
        shade = ('Mara drew the room shade across the high window; daylight had washed the screen.'
                 if before['room.ambient'] else
                 'The room was already dim, so Mara left the shade untouched.')
        distance = after['figure.distance_cm']
        return (f'Tavi clicked the torch off and moved the figure to the lamp-side peg, {distance} centimetres '
                f'from the beam. {shade} Mara held the same screen steady. “Same torch, same paper, same wall,” '
                'Tavi said. They had changed only the figure’s distance, so the next shadow could answer their '
                'question fairly.')

    if scene_id == 'retest':
        first = _observation(after['shadow.first_observation'])
        second = _observation(after['shadow.second_observation'])
        if after['shadow.evidence'] == 'near_torch':
            ending = ('“Near the torch makes it larger,” Mara said. Tavi compared the two distance marks. '
                      '“Now we know which peg the picture means.”')
        else:
            ending = ('One reading was still too faint to compare fairly. Tavi would not call a blur proof. '
                      'Mara’s shoulders drooped, then she nodded. “We’ll write down what happened, not what we hoped.”')
        return (f'With the room dimmer, Tavi switched the torch on again. At the lamp-side peg the screen held '
                f'{second}; the first reading had been {first}. {ending} The screen and figure had stayed the same, '
                'so their comparison finally meant something.')

    if scene_id == 'ending_show':
        extras = _ending_extras(after, 'accurate_demonstration')
        extra_text = f' {extras}' if extras else ''
        return ('The measurements agreed: the figure nearer the torch made the larger shadow, just as the card '
                'promised. Mara left it on that peg; Tavi kept both distance marks visible for the next group. '
                f'{extras} They switched off the torch and returned it to Mr. Bell. He kept their tested setup '
                'for visitors.')

    if scene_id == 'ending_correct_label':
        extras = _ending_extras(after, 'corrected_label')
        extra_text = f' {extras}' if extras else ''
        return ('The comparison showed the lamp-side peg made the larger shadow; the printed screen-side instruction '
                'was wrong. Tavi corrected the label while Mara left the figure on the accurate peg. '
                f'{extras} They showed the fixed setup to Mr. Bell, switched off his torch, and returned it. '
                '“That will save the next group ten minutes,” he said.')

    if scene_id == 'ending_honest':
        extras = _ending_extras(after, 'honest_inconclusive')
        extra_text = f' {extras}' if extras else ''
        return ('One trial was too faint to read, even with the room dim. Mara wanted to announce a result, but '
                'Tavi posted a plain note: the comparison was inconclusive. They switched off the torch and returned '
                f'it to Mr. Bell for a proper recharge.{extra_text} He thanked them for not teaching a guess.')

    raise ValueError(f'No prose for scene: {scene_id}')
