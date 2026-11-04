'''Short scene prose rendered only from the selected local play and its state.'''


def render(scene_id, params, before, after):
    older = params.older_name
    younger = params.younger_name

    if scene_id == 'borrow_map':
        return (
            f'{older} had packed apple rolls, but wanted a place where wind could not steal the napkins. '
            f'At Aunt June’s kiosk, {younger} tapped the half-moon cove on her map. '
            '“Can we borrow it?” “Bring it back with the right way marked,” June said. '
            f'{older} promised; {younger} tucked the map under one arm.'
        )
    if scene_id == 'follow_white_gull':
        paper = ('The paper sat crooked in ' + older + '’s hand. ') if before['map.orientation'] == 'rotated' else 'The folded legend stayed beneath their thumb. '
        faded = 'Sea mist had blurred the tiny print. ' if params.legend_faded else ''
        return (
            'At the fork, a white gull on a post seemed to match the map’s mark. '
            f'“That says landing, not picnic,” {younger} said. {paper}{faded}'
            f'{older} hurried on anyway. The track ended on an exposed shelf: salt spray, hard glare, '
            f'no half-moon cove, nowhere for a blanket. “Wrong landmark,” {younger} said. '
            f'{older} looked back at the map.'
        )
    if scene_id == 'tidepool_pause':
        return (
            f'A shallow pool beside the false post held a shell striped like a tiny sunrise. '
            f'{younger} lifted it while {older} watched the water whisper around the rocks. '
            '“Take it for the picnic?” “Only if we carry it back with us.” They tucked the shell safely away, '
            'and for once neither sibling told the other to hurry.'
        )
    if scene_id == 'fisher_pause':
        return (
            'A net-mender was trying to free a bright float snagged below the path. '
            f'{younger} held the net steady while {older} eased the line loose. '
            '“That white gull marks the ferry landing,” the fisher said. “The half-moon is the cove.” '
            f'{older} thanked them. {younger} glanced at the map, now listening.'
        )
    if scene_id == 'compare_landmarks':
        orient = (
            f'{younger} turned the map until its north arrow followed the water. '
            if before['map.orientation'] == 'rotated'
            else f'{younger} flattened the already upright map against the post. '
        )
        if before['fisher.clue']:
            clue = 'The net-mender had said the gull was the ferry landing; the half-moon was the cove. '
        elif before['map.legend'] == 'clear':
            clue = 'The clear legend named the gull as the ferry landing and the half-moon as their cove. '
        else:
            clue = 'The legend had run pale, so they matched the shore’s curve to the half-moon instead. '
        return (
            orient + clue + f'{older} stared at the exposed shelf. “I rushed it. You were right.” '
            f'{younger} pointed beyond the post. “We can still find a place. Just read the coast with me.”'
        )
    if scene_id == 'choose_safe_route':
        if after['party.route'] == 'strand':
            return (
                'The water lay low enough to uncover the narrow strand toward the cove, though its edge was already turning. '
                f'“We can make it if we keep watching,” {younger} said. {older} handed over the map. '
                'They chose the low path together, agreeing to turn back rather than race the sea.'
            )
        return (
            'Water was climbing over the lower stones. The cove was still on the map, but reaching it would mean gambling with the return. '
            f'{younger} pointed up the bluff. “The harbor awning is dry.” {older} nodded. '
            'They let go of the secret cove and chose the safe, sheltered way above the tide.'
        )
    if scene_id == 'reach_shelter':
        if after['party.location'] == 'crescent_cove':
            return (
                'The low path curved around the headland, and at last the half-moon notch appeared: '
                'a small cove tucked behind dark rock. The real shore matched the map. '
                f'{younger} chose a dry patch above the wrack line, and {older} waited for their signal. '
                'The sea remained in view, but its wind could not reach the shelter.'
            )
        return (
            'The bluff path climbed above the wet stones and bent toward the harbor. Beneath the old net shed’s awning, '
            'the wall blocked the gusts and the boards stayed dry. It was not the secret cove on the map, '
            f'but {younger} pointed to the shelter and {older} nodded: safe, close, and good enough for lunch.'
        )
    if scene_id == 'windbreak_pause':
        shelter = 'the cove’s rock lip' if before['party.location'] == 'crescent_cove' else 'the harbor wall'
        return (
            f'At {shelter}, {younger} pointed to the leeward end. “I want to sit where we can still see the water.” '
            f'{older} began to point somewhere else, then handed over the blanket. They chose a place together, '
            'with the map between them instead of tucked under one elbow.'
        )
    if scene_id == 'picnic':
        place = 'the crescent cove' if before['party.location'] == 'crescent_cove' else 'the harbor awning'
        if params.wind == 'gusty':
            anchor = 'smooth stones' if before['party.location'] == 'crescent_cove' else 'a bench slat'
            weather = f'The gust caught the blanket, so they pinned its corners with {anchor}. '
        else:
            weather = 'The sheltered air let the blanket lie flat without a fight. '
        shell = (
            f'{younger} set the striped shell beside the map. '
            if before['shell.holder'] == 'younger' else ''
        )
        seat = f'{younger} chose the spot they had agreed on. ' if before['younger.chose_seat'] else ''
        return (
            f'At {place}, {weather}{seat}{shell}{older} opened the basket. '
            f'{younger} chose the smaller roll, and {older} broke the other in half. '
            'They ate slowly, sharing the last apple slices while the tide moved beyond their shelter.'
        )
    if scene_id == 'ending_cove':
        shell = f'{younger} carried the little shell back. ' if after['shell.holder'] == 'younger' and before['shell.holder'] == 'blanket' else ''
        return (
            'When the last crumbs were gone, they folded the blanket and walked back to Aunt June’s kiosk. '
            f'{older} returned her map with the white gull marked “ferry landing” and the half-moon traced clearly. '
            '“Now it can guide the next people,” June said. ' + shell +
            f'{younger} led the way out, and {older} let them.'
        )
    if scene_id == 'ending_harbor':
        shell = f'{younger} carried the little shell back. ' if after['shell.holder'] == 'younger' and before['shell.holder'] == 'blanket' else ''
        return (
            'After lunch, they folded the blanket and returned to Aunt June’s kiosk. '
            f'{older} marked the map: gull for the ferry, bluff for the harbor shelter when the tide rose. '
            'June smiled. “That will save someone else a wrong turn.” ' + shell +
            f'{younger} kept the map between them until they handed it back together.'
        )
    raise ValueError(f'No prose for scene: {scene_id}')
