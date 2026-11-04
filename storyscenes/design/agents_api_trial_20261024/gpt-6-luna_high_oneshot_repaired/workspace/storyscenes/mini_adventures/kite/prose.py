"""Short authored scene plays rendered from the actions actually enacted."""


def render(scene_id, params, before, after):
    if scene_id == "workshop":
        return (
            'Nia found Tamsin winding a string reel beside the village kite workshop. '
            '"May I borrow it for the afternoon? Pavel just moved next door, and I want us to fly together." '
            'Tamsin glanced at the frayed edge. "Bring it back with the line wound neatly." '
            'Nia promised, and carried the reel as carefully as a cup of tea.'
        )
    if scene_id == "build":
        strength = after["kite.frame_strength"]
        detail = "The willow bent without splitting." if strength >= 2 else "The thin willow bowed when she tightened the paper."
        return (
            f'At the workbench, Nia crossed two willow sticks and stretched blue paper over them. {detail} '
            'She tied each corner twice, then gave the frame a cautious shake. '
            'It looked less like a kite than a promise with a tail. '
            'Outside, a strip of cloud slid over the rooftops.'
        )
    if scene_id == "invite":
        if params.shyness == 3:
            return (
                'Nia waited at the field gate instead of calling across the lane. '
                '"Pavel, would you like to come? You can help me choose when to let the line out." '
                'He looked at his shoes. "I could try." '
                'Nia held the reel low, not like a prize. Pavel came beside her, and the kite rested between them.'
            )
        return (
            'Nia found Pavel watching from his doorstep. "We have a kite. Would you help me with its tail?" '
            'He studied the bright paper. "I can do that." '
            'She waited while he fetched his jacket; no one hurried him. '
            'At the field, Pavel stood close enough to touch the kite, and Nia let him choose their first job.'
        )
    if scene_id == "ribbon":
        return (
            'A spool of red ribbon lay in the workshop basket. Nia offered it to Pavel. '
            'He chose a short piece and tied it to the paper tail, testing the knot with one careful tug. '
            '"It needs something bright," he said. '
            'The ribbon flicked in the breeze, making the kite easier to see against the pale afternoon sky.'
        )
    if scene_id == "practice":
        return (
            'Before trying the full flight, Nia paid out a few arm-lengths of string. '
            'Pavel held the tail while she eased the reel, then they traded places for one small pull. '
            'The line ran more smoothly when neither child jerked it. '
            'Pavel smiled at the kite. "I know what it wants now." Nia nodded and let him keep the reel.'
        )
    if scene_id == "hand_reel":
        return (
            'Nia held out the reel. "Would you like to hold it? You can tell me when the kite needs more line." '
            'Pavel hesitated, then curled both hands around the wooden sides. '
            '"Not too fast," he said. "I know." Nia moved to the kite, glad that the important job was his, '
            'not something she had to explain away.'
        )
    if scene_id == "keep_reel":
        return (
            'Nia kept the reel against her coat. "I will mind the line. Could you guide the tail until it catches air?" '
            'Pavel considered this, then took the kite by its lower edge. '
            '"I can do that." It was not the same job as holding the spool, but it was his choice, '
            'and Nia waited for his nod before stepping back.'
        )
    if scene_id == "launch":
        if after["flight.result"] == "aloft":
            holder = "Pavel called" if after["flight.mode"] == "Pavel" else "Pavel watched and called"
            return (
                f'Nia ran three quick steps and lifted the kite. {holder}, "Now!" '
                'The line drew taut, then streamed through the reel as the paper climbed above the roofs. '
                'Neither child pulled too hard. The kite steadied in the wind, blue against the clouds, '
                'while Pavel and Nia grinned at each other.'
            )
        if after["kite.frame_strength"] + int(after["kite.ribbon"]) + after["nia.skill"] < after["weather.wind"] + 1:
            trouble = "A gust folded the light frame before it could climb."
        else:
            trouble = "The worn line tugged sharply, so they lowered the kite before it could tear."
        return (
            f'Nia started the launch, but {trouble} Pavel kept the reel steady while she caught the tail. '
            'They brought the kite down gently; no one was hurt, and the borrowed line stayed on its spool. '
            'Pavel brushed grass from the paper. "That was still our flight," he said. Nia agreed.'
        )
    if scene_id == "ending_airborne_shared":
        return (
            'On the walk back, Pavel carried the kite while Nia held the reel. '
            'At the workshop, they wound the remaining string in even loops and returned it to Tamsin. '
            '"Still good for another kite," she said. Pavel looked up at Nia. '
            'He had held the line in the sky, not merely watched it. She had wanted a flight together, and they had one.'
        )
    if scene_id == "ending_airborne_guided":
        return (
            'They carried the kite home together, Pavel still describing the moment its tail caught the breeze. '
            'Nia wound the remaining string neatly and returned the reel to Tamsin, ready for another flight. '
            'Pavel had guided the kite into the air, and Nia had listened when he said when to run. '
            'At the gate, he asked whether they could fly again sometime.'
        )
    if scene_id == "ending_grounded":
        return (
            'The kite came back to the workshop in one piece, even if it had never risen. '
            'Nia wound the useful remaining string onto Tamsin’s reel and returned it. '
            'Pavel walked beside her, no longer lingering at the edge of the group. '
            '"I liked being the one who steadied it," he said. Nia smiled: their afternoon had belonged to both of them.'
        )
    raise ValueError(f"No prose for scene: {scene_id}")
