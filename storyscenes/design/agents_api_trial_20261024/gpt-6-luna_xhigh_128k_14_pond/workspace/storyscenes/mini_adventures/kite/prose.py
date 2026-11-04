"""Short scene prose rendered from the local actions that actually occurred."""


def render(scene_id, params, before, after):
    if scene_id == 'spot_boat':
        return ('Mara and Jules stopped on the dry stone rim. Jules’s blue wooden boat had slipped from his hand and lodged against a reed clump, its little mast tilted. “Granddad carved that,” he said. Mara wanted to fetch it; Jules wanted it back, but neither wanted wet shoes or a lecture. They promised to stay on the bank.')
    if scene_id == 'remember_boat':
        return ('“Granddad made the hull from a fruit crate,” Jules said, rubbing a thumb over the blue sail. “He said it would cross the whole pond.” Mara noticed the little pencil initials under its stern. “Then we’ll bring back your boat, not prove anything.” Jules nodded, glad she remembered why it mattered.')
    if scene_id == 'read_reeds':
        if before['pond.weeds']:
            return ('Jules watched the reeds instead of the boat. “There’s a gap by that flat stone. The stems lean away from it.” Mara crouched beside him, still on the path, and followed his pointing finger. The opening was narrow, but wide enough for the net hoop. For once, looking carefully seemed faster than hurrying.')
        return ('Mara studied the pond’s edge while Jules kept watch on his boat. There were reeds farther along, but none between them and the little hull. “A clear line,” she said. Jules nodded. He wanted to hurry; she wanted to know what the net would meet before they lowered it. The water barely stirred.')
    if scene_id == 'borrow_net':
        return ('The park keeper, Mr. Imani, was coiling a hose nearby. Mara asked to borrow his long-handled net and promised to bring it straight back. He checked the mesh with his thumb. “No fishing, and no stepping in. Let the hoop do the reaching.” Jules watched closely as Mara took the handle with both hands.')
    if scene_id == 'bank_plan':
        return ('Mara chalked a small line on the dry path and knelt behind it. Jules stood back where he could see the boat without crowding her elbows. “You stay there; I’ll tell you if the stern moves,” he said. They agreed that neither would wade or lean over the edge. The plan felt steadier than a dare.')
    if scene_id == 'cast_net':
        if after['attempt.result'] == 'retrieved':
            pause = 'They waited for the breeze to soften. ' if before['pond.wind'] == 'breezy' else ''
            target = 'through the opening Jules had spotted' if before['pond.weeds'] else 'under its hull'
            return (f'{pause}At Mara’s nod, she guided the hoop {target}. The net slid beneath the boat without pushing it farther out. She raised the handle slowly; water streamed through the mesh and the little hull settled on dry stones. Jules waited behind the chalk line until it was still.')
        if after['attempt.result'] == 'gust':
            return ('A gust kept combing the pond toward the middle. Mara held the net beside her instead of throwing it after the boat. “It’s moving farther out, and the water’s pulling too,” Jules said. They watched one more gust pass. The handle had helped them judge the reach; neither child leaned or stepped down.')
        if after['attempt.result'] == 'out_of_reach':
            return ('Mara laid the handle along the path’s edge to compare its reach with the boat’s distance. The hoop stopped short. “I could lean a little,” she began. Jules shook his head. “That’s how a little becomes a splash.” She set the handle back. The net had answered the question without either child entering the water.')
        if after['attempt.result'] == 'mesh_torn':
            return ('The hoop passed under the hull, but the torn mesh let the boat slip through. Mara drew the net back from the bank at once. “One more try?” Jules asked, then saw the widening hole. “No. We shouldn’t make Mr. Imani’s net worse.” The toy stayed stuck by the reeds; they kept both feet on stone.')
        return ('Mara guided the hoop toward the reeds, but the stems caught its rim before it reached the boat. She stopped pulling. Jules held his place while she eased the empty net free from the bank. The boat remained stuck beyond the stems. “We found the wrong opening,” she said. “And we know not to yank.”')
    if scene_id == 'return_net':
        if after['net.used_for'] == 'retrieval':
            use = 'It had brought Jules’s boat within reach without bringing either child near the water.'
        elif after['net.used_for'] == 'reach_check':
            use = 'It showed them the honest limit of a safe reach.'
        elif after['net.used_for'] == 'safety_check':
            use = 'It gave them a clear reason not to cast into the gusts.'
        elif after['net.used_for'] == 'mesh_test':
            use = 'It showed them the torn mesh would not hold the boat.'
        else:
            use = 'It caught reeds, not the boat, and they freed it without pulling hard.'
        return (f'Mara carried the net back to Mr. Imani and told him exactly what had happened. {use} He checked the hoop and took it with a nod. “Thanks for bringing it back in one piece.” Jules stayed beside Mara, looking toward the pond rather than hiding behind her.')
    if scene_id == 'ending_boat_home':
        memory = 'Jules told Mr. Imani the story of his grandfather’s boat while the water dripped away.' if before['boat.story_shared'] else 'Jules turned the little boat over in his hands, checking the mast.'
        return (f'Jules took his boat from the dry stones. {memory} Its sail was crooked, but the hull still floated. “You got it back,” he said. Mara smiled; she had wanted to help, not to be called brave. Together they carried the usable boat toward the park bench, both still dry.')
    if scene_id == 'ending_boat_left':
        memory = 'Jules remembered how his grandfather had shaped the hull, and drew it carefully from memory.' if before['boat.story_shared'] else 'Jules drew the blue hull and its tilted mast as he remembered them.'
        return (f'The boat stayed caught beyond the safe reach of the net. Jules’s face fell, and Mara said she was sorry. {memory} They added a chalk dock on the dry path and named the drawing Captain Blue. It was not the boat, but it was something they made together. Neither went into the pond.')
    raise ValueError(f'No prose for scene: {scene_id}')
