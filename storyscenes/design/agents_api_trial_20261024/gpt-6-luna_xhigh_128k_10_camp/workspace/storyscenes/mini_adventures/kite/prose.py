"""Short scene plays rendered from their enacted local outcomes."""


def _site(site):
    return 'the tent edge' if site == 'tent_edge' else 'the fern hollow'


def render(scene_id, params, before, after):
    if scene_id == 'borrow_lantern':
        return ('The tent flap snapped while Kit searched under the bedrolls. Dad passed Mira the battery lantern, already glowing. '
                '“Borrow it, but bring it back before supper,” he said. Mira promised. Kit stayed close enough to touch her sleeve; '
                'the shadows between the tents were stretching longer.')
    if scene_id == 'tell_about_fox':
        return (f'“Pip is gone,” Kit whispered. He remembered { _site(after["kit.memory_site"]) }, though he was not sure. '
                'The trees beyond camp looked taller than they had at lunch. Mira could have called the fox only a toy. '
                'Instead, she waited for Kit to finish explaining and said, “We will look together.”')
    if scene_id == 'shadow_vignette':
        return ('On the tent wall, Mira made two ears with her fingers. “That is Pip,” Kit decided, stretching the shadow into a fox. '
                'His laugh came out shaky, then steadier. Mira offered him the lantern. He took it with both hands. '
                '“I can carry the sun,” he said, and stayed beside her.')
    if scene_id == 'trail_vignette':
        return ('Dad clipped orange reflector tabs along the guyline toward the fern hollow. “They catch the lantern light,” he said. '
                '“If you lose sight of camp, follow these back. I will keep the fire going.” Kit touched one bright tab. '
                'Mira understood that the path home was something they could prepare, not just hope for.')
    if scene_id == 'choose_search':
        place = _site(after['camp.location'])
        carrier = 'Kit' if after['lantern.holder'] == 'kit' else 'Mira'
        if after['mira.search_policy'] == 'sweep':
            plan = 'If this is empty, we can spend what remains on one more sweep.'
        else:
            plan = 'We will make one careful search, then turn back rather than wander.'
        if after['kit.hand_in_mira']:
            footing = 'Wet roots crossed the path, so Mira and Kit held hands and stepped slowly.'
        elif after['camp.location'] == 'fern_hollow':
            footing = 'They took the narrow path between the ferns, watching where they placed their boots.'
        else:
            footing = 'They stopped by the tent edge, where the bedrolls and rainfly were easy to inspect.'
        return (f'{carrier} carried the lantern as they followed Kit’s memory to {place}. Mira explained their choice: '
                f'“{plan}” {footing} Kit nodded; he had helped choose the search, not just follow it.')
    if scene_id == 'search_fox':
        if after['search.found']:
            if after['search.stop_reason'] == 'found_first':
                found_line = f'The beam found Pip at { _site(after["camp.location"]) }, where Kit had remembered him.'
            else:
                found_line = (f'The first place was empty, so they used the next sweep at { _site(after["camp.location"]) }. '
                              'There the beam caught Pip.')
            if before['fox.covered']:
                cover_line = 'Mira lifted the curled rainfly, and Kit pulled the soft fox free.'
            else:
                cover_line = 'Kit reached down and lifted the soft fox from the open ground.'
            return (f'{found_line} {cover_line} “Pip!” Kit hugged him against his coat. '
                    'The lantern had spent another bar, but the fox was warm in Kit’s arms. Mira checked that they still knew the way back.')
        if after['search.stop_reason'] == 'conserve':
            return (f'The beam swept { _site(after["search.first_area"]) }, but found only a pinecone and a mitten. '
                    'Mira kept the agreement they had made: one careful look, then back together. Kit swallowed his disappointment. '
                    '“I thought I knew,” he said. “You remembered what you could,” Mira answered.')
        return (f'The lantern swept { _site(after["search.first_area"]) }, but Pip was not there. They checked the other place only after the last light or daylight allowed it; '
                'neither search found him. Mira called the search off. Kit was sad, but he held her hand instead of staring into the trees.')
    if scene_id == 'return_to_camp':
        if after['return.path'] == 'lantern':
            route = 'Mira switched the lantern on and carried its beam along the path. It used another bar, but kept Kit close and showed each turn.'
        elif after['return.path'] == 'reflectors':
            route = 'The lantern had gone dark, so they followed Dad’s orange reflector tabs back along the guyline.'
        elif after['return.path'] == 'daylight':
            route = 'With the last daylight still visible, they retraced the path they had walked together.'
        else:
            route = 'The lantern was empty; they turned toward the familiar orange glow of their family fire.'
        muddy = ' Mud clung to both pairs of boots.' if after['mira.boots_muddy'] else ''
        return (f'{route}{muddy} Kit still felt a little nervous, but the path no longer belonged to the dark alone. '
                'The tent and the fire came into view. They had returned together, with the borrowed lantern still in hand.')
    if scene_id == 'ending_found':
        muddy = ' Their boots left muddy marks beside the bedroll.' if before['mira.boots_muddy'] else ''
        dad = ('Dad used the remaining lantern light beside the supper pot.' if after['dad.used_lantern']
               else 'Dad took the dark lantern back and set it beside the cooking pot.')
        return (f'Kit settled Pip beside his bedroll and wiped the fox’s muddy ear on a blanket.{muddy} '
                '“I was scared,” he said, “but I carried the light.” Mira smiled; she had not needed to search alone to lead. '
                f'{dad} The fox was home, and the siblings sat down to supper together.')
    if scene_id == 'ending_lost':
        place = _site(after['fox.location'])
        dad = ('Dad used the remaining lantern light beside the supper pot.' if after['dad.used_lantern']
               else 'Dad took the dark lantern back and set it beside the cooking pot.')
        muddy = ' Mira’s knees were muddy, and Kit noticed.' if before['mira.boots_muddy'] else ''
        return (f'Pip remained out at {place}. Kit accepted the blue camp blanket and let himself be sad without being alone.{muddy} '
                '“I am still scared of the trees,” he said, “but not of being here with you.” Mira returned the lantern to Dad. '
                f'{dad} They ate supper beside the fire, together.')
    raise ValueError(f'No prose for scene: {scene_id}')
