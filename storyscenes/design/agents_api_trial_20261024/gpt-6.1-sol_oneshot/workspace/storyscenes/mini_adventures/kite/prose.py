"""Local prose follows committed outcomes; no random or deferred effects."""

def render(sid, b, a):
    if sid == 'welcome':
        return ('Mara held her yellow kite up in the village workshop. Through the window she could see Ivo, the new neighbour, sitting alone on his step. Yesterday her enormous hello had sent him indoors. “Try something smaller,” Nan Bell said. Mara lowered the kite. This afternoon she wanted company more than applause.')
    if sid == 'borrow':
        if not b['reel.sound']:
            middle = ('Mara cut out the fray and tied a fresh loop. “Shorter, but sound,” Nan said.' if a['reel.sound'] else 'Mara noticed a fray but left it alone. “No flying on that bit,” Nan warned.')
        else:
            middle = 'Mara checked the line between her fingers. It was smooth, and the loop held under a tug.'
        return 'Her own string was at home. Nan lent her red reel. ' + middle + ' Carrying kite and reel, Mara crossed to Ivo’s step.'
    if sid == 'invite':
        if a['ivo.trust']:
            return ('Mara sat on the wall, leaving a space. “Would you like to hold the reel? You needn’t shout.” Ivo turned its wooden cheek with one finger. “Not in the middle of everyone.” Mara had wanted the middle. “The lower field, then.” He stood up, still looking at the little wheel.')
        return ('“Come and launch my kite!” Mara called across the step. Ivo tucked his hands behind his back. “I’ll watch.” For a moment she wanted to insist; she had brought everything especially. Instead she nodded. He came to the gate beside her, but left the reel firmly in her hands.')
    if sid == 'bird':
        return ('A sparrow hopped out of the workshop doorway with a shaving stuck to one foot. Mara stopped. Ivo pointed, holding his breath. The bird shook itself free and flew to the gutter. “It brought its own tail,” he said. Mara laughed softly. Neither child moved until the shaving stopped turning on the stones.')
    if sid == 'window':
        return ('Mara found a blue paper square in her pocket. She pressed it onto the yellow kite with the sticky paste still on its edge. “A window,” she said. Ivo inspected the back. “Nobody inside.” “Only glue.” His mouth twitched. She smoothed the patch once more before picking up the frame.')
    if sid == 'field':
        if a['kite.flew']:
            return ('They chose the lower field. A steady breeze lifted the yellow paper from Mara’s fingers. Ivo let the reel turn, then stopped it with his thumb. Mara came beside him. “That’s you doing that.” Above the hedge, the kite tugged; he smiled without taking his eyes off it. She forgot to look for applause.')
        reason = ('The grass lay still; the kite would not lift.' if b['weather.wind'] == 0 else 'Hard gusts flattened the grass. Mara kept the kite down.' if b['weather.wind'] == 2 else 'Mara kept the kite down: the frayed line could not take a pull.' if not b['reel.sound'] else 'Ivo stayed back. Mara put the reel down rather than press him into holding it.')
        return 'At the lower field, they stopped. ' + reason + ' She felt the afternoon shrink. Ivo crouched beside the frame. “It’s still a good shape,” he said. They watched the other kites before turning back.'
    if sid == 'return':
        start = 'They brought the kite down and wound the line evenly. ' if b['kite.flew'] else 'They carried the unused kite back to the workshop. '
        repair = 'Nan helped Mara cut out the fray and tie a sound loop. ' if not b['reel.sound'] else 'Mara checked the loop once more. '
        return start + repair + 'The red reel went into Nan’s hands. She spun it freely between her palms and put it ready for the morning class. “That’ll do nicely.”'
    if sid == 'ending_air':
        return ('Outside the workshop, Ivo paused beside Mara’s kite. “I could feel it choosing a direction.” “You were choosing too,” she said. He held the frame while she fastened her bag. They had not flown highest, but he was still beside her, describing the tug with his hands. Mara listened all the way to his gate.')
    if sid == 'ending_table':
        return ('Mara put scrap paper between two stools. “What shape would you make?” Ivo sat down and drew a broad kite with a tiny door. She drew someone looking out. Their afternoon had not become the flight she wanted. But he pulled the second stool closer, and they filled the paper together before Nan closed up.')
    raise ValueError(sid)
