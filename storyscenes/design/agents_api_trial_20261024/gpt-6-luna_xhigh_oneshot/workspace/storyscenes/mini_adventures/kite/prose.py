'''Scene-local prose, conditioned on committed world state.'''


def render(scene_id, params, before, after):
    if scene_id == 'workshop':
        return ('Nia wanted June, the new girl on Willow Lane, to fly a kite with her—not watch from behind the gate. '
                'At Tomas’s village workshop she pointed to the blue string reel. “May I borrow it for the afternoon?” '
                'Tomas turned its wooden handle. “Bring it back wound tight; it was my father’s.” '
                'Nia promised, and carried it out carefully.')

    if scene_id == 'invite':
        if after['neighbor.comfort'] == 'quiet':
            return ('June kept one shoulder behind the gate. “I don’t know how to fly one,” she said. '
                    'Nia resisted saying it was easy. “You can choose when we let it go. We can stay away from the crowd.” '
                    'June studied the blue reel. “Just us?” Nia nodded. June opened the gate, still holding her sleeve.')
        return ('June opened the gate. “I’ve never flown a kite,” she said. Nia admitted that her first one had landed '
                'in a cabbage patch. June laughed, then glanced at the children gathering on the green. “I don’t like '
                'everyone watching.” “Then we’ll have our own bit of sky,” Nia said. June stepped out beside her.')

    if scene_id == 'vignette_mark':
        return ('By the lane, June asked to draw on the kite. Nia handed her the pencil instead of choosing for her. '
                'June made one small blue star near the corner. “My brother said a mark helps you find your own kite,” '
                'she said. Nia liked the star. It made the plain paper feel shared already.')

    if scene_id == 'prepare_kite':
        if after['kite.repaired']:
            return ('At the bench, June found a split spar. Nia used three careful turns from the borrowed reel to lash it; '
                    'the knot held. They tied on a balanced tail, though the repair spent some of their line. '
                    '“A mend, not a miracle,” June said, carrying the kite out with Nia.')
        if after['kite.frame_ok']:
            return ('At the bench, June held the frame while Nia checked each bamboo spar. Nothing had split, so they '
                    'tied on a tail weighted for the day’s breeze and kept the reel’s line free. “Ready?” Nia asked. '
                    'June tested the knot with a gentle tug. “Ready enough to try.” They carried the kite out together.')
        return ('At the bench, June found a split spar. The reel was too short to lash it safely, so Nia fitted the tail '
                'without pretending the frame was sound. “We can try gently,” she said. June held the kite level, not by '
                'its weak corner. They carried it out together.')

    if scene_id == 'vignette_ribbon':
        if after['wind.vane'] == 'gusty':
            return ('Before they left, June tied a ribbon to the weather pole. It streamed, sagged, then snapped straight '
                    'again. “The wind keeps changing its mind,” she said. Nia had been watching the kites overhead, not '
                    'the gaps between gusts. They agreed to wait for June’s count before choosing a moment to run.')
        return ('Before they left, June tied a ribbon to the weather pole. It streamed steadily. “Not much of a gust,” '
                'she said. Nia had been watching the kites overhead, not the air at their hands. June smiled at the '
                'ribbon. “I can tell you when it changes.” Nia gave her the loose end to carry.')

    if scene_id == 'walk_to_commons':
        return ('They carried the kite and reel along the bakery wall to the open common. June stayed beside Nia, not '
                'behind her, and held the kite away from the damp hedge. The green was busy at its far end, so they '
                'chose the quiet patch near the hawthorn. “This is our bit of sky,” Nia said. June nodded.')

    if scene_id == 'first_flight':
        if after['kite.tangled']:
            return ('The kite lifted over the grass, then a sharp gust drove its line into a low hawthorn twig. June '
                    'caught the tail before it tore free. Nia let the borrowed reel run instead of yanking; the kite '
                    'hung crooked, trembling just above the hedge.')
        if after['kite.initial_lift']:
            return ('On Nia’s count, the kite rose above the grass. Borrowed line slid through the reel, and June kept '
                    'one hand at the tail. It climbed only as high as the hedge before the wind faltered, but it had '
                    'flown. Then the line quivered in Nia’s palm.')
        return ('The kite hopped once and nosed into the grass. The borrowed line kept it from skittering away. June '
                'picked up the tail, careful not to touch the weak spar. “It tried,” Nia said. A gust rattled the hedge; '
                'neither child blamed the other for the drop.')

    if scene_id == 'response':
        if before['kite.tangled']:
            opening = ('The gust had looped line around a low hawthorn twig. June held the tail while Nia fed slack '
                       'from the reel, and together they eased it free. ')
        else:
            opening = 'They checked the clear line together, watching the gust rather than fighting it. '
        if after['neighbor.role'] == 'reel':
            body = ('Nia offered June the handle. June’s fingers shook, but she took it and called each lull; Nia '
                    'steadied the tail. They waited for June’s count before deciding how high to try.')
        else:
            body = ('June was not ready to hold the reel. Nia offered her the tail and let her choose the release. '
                    '“Wait—now,” June said. Nia kept the handle steady. They would not yank the line just to prove '
                    'the kite could fly.')
        return opening + body

    if scene_id == 'ending_flight':
        if before['neighbor.role'] == 'reel':
            control = 'June guided the handle while Nia steadied the kite’s tail. '
        else:
            control = 'June called the lull while Nia let the reel run. '
        if before['kite.mark']:
            mark = 'They signed beside June’s blue star and set the kite on the workshop rack.'
        else:
            mark = 'They signed their kite and set it on the workshop rack.'
        return ('On the second run, the kite rose above the hawthorn and held. ' + control +
                'They brought it down before the gusts returned, rewound the loose line, and carried it back to Tomas. '
                'He took his borrowed reel with a nod. ' + mark + ' The blue paper turned in the afternoon light.')

    if scene_id == 'ending_grounded':
        if before['kite.height'] == 'low':
            first = 'The kite had climbed above the grass before the gust pulled it back. '
        else:
            first = 'The kite had only hopped across the grass. '
        mark = 'June’s blue star showed between their names. ' if before['kite.mark'] else ''
        return (first + 'June asked them not to pull harder. Nia listened. They folded the kite carefully; '
                'the borrowed reel had kept it from escaping and brought the loose line home. Tomas took back his '
                'wound spool. ' + mark + 'The girls signed the paper and hung it in the workshop window, '
                'where the afternoon light found it.')

    raise ValueError(f'No prose for scene: {scene_id}')
