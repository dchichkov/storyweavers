'''Authored local-scene prose rendered only from enacted state.'''


def render(scene_id, params, before, after):
    if scene_id == 'borrow_compass':
        needle = 'held steady beside the arrow.' if after['compass.calibrated'] else 'swung east of the arrow.'
        return (
            'At the trailhead, ranger Inez handed Nia the brass compass. '
            '“Back before the main gate closes, please.” Rowan tucked the folded trail card into his pocket; '
            'his new boot had begun rubbing already. Nia checked the needle against the board’s north arrow. '
            f'It {needle} “We’ll keep together,” she said, and Rowan nodded.'
        )
    if scene_id == 'fern_vignette':
        if before['compass.calibrated']:
            return (
                'Rowan stopped beside a fern uncurling over the brook. “Look—the bend points north, '
                'not along the footpath.” Nia checked the compass against the familiar curve, and its '
                'steady needle agreed. They marked the fern on the card. The pause cost a few minutes, '
                'but gave Rowan a landmark he could recognize on the way back.'
            )
        return (
            'Rowan stopped beside a fern uncurling over the brook. “The water bends north here.” '
            'Nia held the compass beside that known curve; its wandering needle settled into a usable '
            'bearing. They marked the fern on the card. The pause cost a few minutes, but now they had '
            'a second way to check their direction if the trail signs disappeared.'
        )
    if scene_id == 'lace_vignette':
        return (
            'Rowan shifted his weight and winced. Nia sat on a flat stump while he showed her the red '
            'rub above his heel. She found a strip of first-aid tape in the trail pouch and smoothed it '
            'over the sore place. “Not magic,” Rowan said, testing his boot. “Just enough.” They stood '
            'when he was ready, not when the clock told them to.'
        )
    if scene_id == 'route_choice':
        if after['story.route'] == 'shortcut':
            return (
                'At the fork, the compass pointed along the open stone-step shortcut. Rowan tested his '
            'newly taped heel. “I can manage if we don’t race.” Nia had wanted to get ahead, but she '
            'waited until he was beside her. They chose the short way together, checking the bearing '
            'against Rowan’s brook landmark. Neither friend was sent off alone.'
            )
        if not before['trail.shortcut_open']:
            detail = 'The shortcut gate was shut, its wet steps beyond reach.'
        elif before['friend.heel_sore']:
            detail = 'The open shortcut had steep stones, wrong for Rowan’s sore heel.'
        else:
            detail = 'The shortcut was open, but its turns were hard to read without a sure bearing.'
        return (
            f'At the fork, Nia raised the compass and read the marked ridge. {detail} '
            'For a moment she pictured reaching the pool sooner by running ahead. Then Rowan tapped '
            'the trail card. “We came to discover it, not to win a race.” Nia chose the broad ridge '
            'with him beside her. His shoulders loosened as they started.'
        )
    if scene_id == 'puddle_cross':
        if after['friend.boots_muddy']:
            surface = 'Rain had deepened the puddle, so the stepping stones vanished under brown water.'
            crossing = 'They followed the marked bank around it, helping one another over the slick roots.'
        else:
            surface = 'A shallow puddle lay between the stepping stones, bright with reflected leaves.'
            crossing = 'They crossed one at a time, Rowan setting the pace and Nia waiting on the far stone.'
        return (
            f'{surface} {crossing} '
            'The compass stayed dry in Nia’s palm, and Rowan’s boot found solid ground. '
            '“That was slower than jumping,” Nia said. “And we both made it,” Rowan answered, '
            'already looking for the trail marker on the other side.'
        )
    if scene_id == 'ridge_walk':
        route = 'stone shortcut' if after['story.route'] == 'shortcut' else 'broad ridge path'
        bearing = ('The calibrated needle matched the painted blazes.' if after['compass.calibrated']
                   else 'When the needle wandered, the painted blazes kept them oriented.')
        return (
            f'The friends followed the {route}. Nia walked ahead twice, then noticed Rowan’s careful '
            'stride and came back to his shoulder. They traded the compass and trail card between them. '
            f'{bearing} Rowan pointed out a woodpecker’s fresh chips; Nia stopped long enough to look. '
            'The pool spur was still ahead, but the walk had become theirs rather than hers.'
        )
    if scene_id == 'discovery':
        if after['story.discovery'] == 'glasswing_pool':
            return (
                'The trees opened onto a clear pool before the marked spur’s time ran out. A glasswing '
                'butterfly rested on a leaf, its transparent wings catching a thin stripe of sun. '
                'Rowan sketched it while Nia held the card still. “You found the tiny one,” she said. '
                '“We did,” Rowan corrected, smiling as the butterfly lifted over the water.'
            )
        if before['trail.rain']:
            reason = 'Rain blurred the pool spur and made its stones unsafe.'
        else:
            reason = 'The pool spur’s quiet-hour marker had passed while they kept Rowan’s pace.'
        return (
            f'{reason} They turned into the marked shelter instead of pretending the pool was theirs. '
            'From under its roof they heard frogs calling in the wet grass. Rowan drew their ripples '
            'on the trail card; Nia added the shelter’s crooked post. “Not the picture I planned,” '
            'she said. “Still something we found,” Rowan replied.'
        )
    if scene_id == 'ending_pool':
        bearing = ('They told Inez the north board and brook had confirmed the compass.'
                   if after['compass.calibration_source'] == 'stream'
                   else 'They told Inez the compass had matched the north board at the fork.'
                   if after['compass.calibrated']
                   else 'They showed Inez where the compass needle had wandered, and which blazes kept them safe.')
        return (
            f'At the trailhead, Nia returned Inez’s compass, then showed her Rowan’s glasswing sketch. '
            f'{bearing} Inez thanked them for checking instead of trusting a faulty reading. Rowan '
            'added the frog-free pool mark to the trail card, and Nia wrote both their names beneath it. '
            'They had reached the water together; neither name looked like a guest.'
        )
    if scene_id == 'ending_shelter':
        bearing = ('They reported that the brook bend had helped correct the compass.'
                   if after['compass.calibration_source'] == 'stream'
                   else 'They reported the compass’s true bearing from the north board.'
                   if after['compass.calibrated']
                   else 'They told Inez the needle wandered, so they had followed the blazes instead.')
        return (
            f'At the trailhead, Nia returned Inez’s compass and Rowan showed her the frog sketch. '
            f'{bearing} Inez thanked them for the useful report. They had missed the pool, but Rowan '
            'had found a chorus worth drawing, and Nia had not left him to chase a picture alone. '
            'They walked out tired, muddy, and still talking about which frog had sung loudest.'
        )
    raise ValueError(f'No prose for scene: {scene_id}')
