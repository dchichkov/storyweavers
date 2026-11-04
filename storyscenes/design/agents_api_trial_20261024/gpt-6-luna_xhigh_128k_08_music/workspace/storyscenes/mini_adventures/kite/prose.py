'''Short local plays rendered from enacted state, not whole-story variants.'''


def render(scene_id, p, before, after):
    child, newcomer = p.child, p.newcomer
    if scene_id == 'borrow_drum':
        return (f'{child} wanted the new girl to feel at home, and the little drum on Ms Vale’s shelf looked like a beginning. '
                f'“May I borrow it for practice?” {child} asked. Ms Vale passed it over carefully. '
                '“Bring it back after, please.” {child} promised, feeling its wooden rim warm in their hands.')
    if scene_id == 'newcomer_arrives':
        return (f'{newcomer} paused just inside the community music room, one hand still on the door. '
                f'{child} introduced themself without crossing the floor. “You can sit wherever you like,” they said. '
                f'{newcomer} nodded, watching the practisers at the far end. Their fingers worried a sleeve, but they came in.')
    if scene_id == 'make_space':
        if before['room.chairs_ready']:
            return (f'{child} turned one of the waiting chairs slightly sideways and left an open space beside it. '
                    '“Nobody has to perform from this seat,” they said. '
                    f'{newcomer} chose the chair nearest the door: close enough to hear, and far enough to leave.')
        return (f'The chairs were stacked against the wall. {child} dragged one stool into the room, then stopped before placing another beside it. '
                '“You can pick yours,” they said. '
                f'{newcomer} set a chair near the door, angled toward the music stand. The open space felt like an invitation, not a trap.')
    if scene_id == 'ribbon_cue':
        if before['ribbon.length_cm'] >= 35:
            cue = 'A long ribbon lay across the music stand, where its loose end could sway.'
        else:
            cue = 'The short ribbon made a bright loop around the drum handle.'
        return (f'Before asking anything, {child} took a ribbon from a pocket. {cue} '
                '“It helps me keep time,” they said. “You can follow it or ignore it.” '
                f'{newcomer} watched the small movement, not yet answering.')
    if scene_id == 'quiet_demo':
        return (f'{child} tapped a small pattern on the drum, then rested both hands on their knees. '
                f'They did not look at {newcomer} for a reaction. The last note faded beneath the brass practice down the hall. '
                f'{newcomer} tilted their head. “It sounds different from over here,” they said. {child} smiled; that was enough.')
    if scene_id == 'open_invitation':
        return (f'“I’m trying a call-and-answer,” {child} said. “You could tap once, keep time on your knee, listen, or pass. '
                'All of those count as being here.” They left the drum between them, not in the newcomer’s lap. '
                f'{newcomer} looked at the open space around it and took a breath.')
    if scene_id == 'accept_beat':
        return (f'“One beat,” {newcomer} said at last. “Just one, and I can stop after.” '
                f'{child} nodded and kept their hands still, making room for that limit. '
                f'{newcomer} moved their chair closer by a few inches. The choice had come from them, and nobody hurried it.')
    if scene_id == 'pass_for_now':
        return (f'“I think I want to listen,” {newcomer} said. {child} nodded without bargaining for a different answer. '
                '“Listening counts. You can change your mind, or not.” '
                f'{newcomer} let out a breath and settled into the chair. The drum stayed with {child}, not placed in their hands.')
    if scene_id == 'duet':
        if before['drum.head_taut']:
            opening = f'{child} played a clear, gentle call on the taut drumhead.'
        else:
            opening = f'{child} found a soft, low sound by tapping near the drum’s loose edge.'
        return (f'{opening} {newcomer} answered with one small beat. {child} kept their hands still afterward, leaving the next choice open. '
                f'“That was my sound,” {newcomer} said, surprised. They tried the pattern once more, then let it end while it still felt like theirs.')
    if scene_id == 'listening_pattern':
        return (f'{child} played a slow pattern for the person who had chosen to listen. '
                f'{newcomer} followed its pauses, then said it sounded like rain tapping a window. '
                f'{child} repeated the rhythm, softer this time. No second drum joined in, but the answer changed how the first one sounded.')
    if scene_id == 'ending_duet':
        ribbon = ' The ribbon came back to the child’s pocket.' if before['vignette.ribbon_done'] else ''
        return (f'When the last beat settled, {newcomer} grinned. “That one was mine.” '
                f'{child} carried the borrowed drum to Ms Vale, who thanked them both and returned it to its shelf.{ribbon} '
                f'{newcomer} stayed to help stack chairs. Their song had lasted seconds, but its next beat belonged to them both.')
    if scene_id == 'ending_listening':
        ribbon = ' The ribbon came back to the child’s pocket.' if before['vignette.ribbon_done'] else ''
        return (f'{newcomer} had chosen to listen, and {child} let that answer stand. '
                f'They carried the borrowed drum back to Ms Vale, who smiled at the pattern they described.{ribbon} '
                f'{newcomer} stayed while the chairs were stacked. No duet had happened; still, the room held a shared piece of music.')
    raise ValueError(f'No prose for scene: {scene_id}')
