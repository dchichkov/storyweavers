"""Authored mini-plays rendered from enacted outcomes, never whole-story templates."""


def render(scene_id, p, before, after):
    a, b = p.captain, p.explorer
    if scene_id == "launch":
        return (
            f'{a} stood by the back door in boots and a paper hat. "I\'m captain. You\'re the crew."\n'
            f'"Explorer," {b} said. "I choose things too."\n'
            f'Mom brought a map. "Treasure under the apple tree. No trampling my flowers." '
            f'{b} took it.\n"Even for treasure?" {a} asked.\n"Especially for treasure."'
        )
    if scene_id == "old_flag":
        return (
            f'{b} found a damp paper flag behind the boots. "From our last ship."\n'
            f'"That one sank," {a} said.\n"You sat on it."\n"It wasn\'t built for captains."\n'
            f'{b} smoothed the flag. A biscuit crumb still clung to the tape. '
            'The flag went on the windowsill to dry.'
        )
    if scene_id == "read_map":
        if before["map.upside_down"]:
            return (
                f'{b} spread the map on the bench. "Left," {a} announced.\n'
                f'"That\'s the fence." {b} turned the paper until its little house faced their house.\n'
                f'"Oh." {a} studied it again. "You\'d better keep that."\n'
                f'{b} folded it into a pocket, with the red cross safely inside.'
            )
        return (
            f'{b} spread the map on the bench. {a} traced the path with a finger. '
            f'"It looks shorter on paper."\n"So do we," {b} said, pointing to two tiny figures by the house.\n'
            f'{a} laughed. "Keep it safe." {b} folded the map into a pocket.'
        )
    if scene_id == "change_clothes":
        if after["captain.coat"] == "green":
            return (
                f'Mom glanced at {a}\'s new red coat. "In that?"\n"I\'ve got boots."\n'
                f'{b} pointed above them. "Mud goes higher."\n'
                'Mom offered an old green jacket.\n"But captains wear red."\n'
                f'"I\'ll still hear your orders," {b} said. {a} changed jackets and hung the red coat up.'
            )
        return (
            f'Mom glanced at {a}\'s new red coat. "In that?"\n"I\'ve got boots."\n'
            f'{b} pointed above them. "Mud goes higher."\n'
            'Mom offered an old jacket, but the brass buttons were too splendid to give up.\n'
            f'"I\'ll be careful," {a} said, fastening the last one.'
        )
    if scene_id == "gutter":
        start = "Outside, " if before["party.location"] == "house" else "By the gutter, "
        return (
            f'{start}a drip landed on {a}\'s paper hat. "We\'re under attack!"\n'
            f'{b} stepped sideways. "The enemy can\'t turn."\n'
            f'{a} followed, inspecting the soggy brim. Folding the wet bit underneath made it shorter '
            'and rather crooked.\n"Battle damage," the captain said, giving the gutter a wide berth.'
        )
    if scene_id == "enter_summerhouse":
        start = "Outside, they passed" if before["party.location"] == "house" else "They came to"
        shutters = "Open shutters striped the floor with sunlight." if before["summerhouse.daylight"] else "The shutters were closed."
        return (
            f'{start} the summerhouse. {a} opened its door. "A cave. We should explore it."\n'
            f'"The treasure\'s at the tree," {b} said.\n"There might be two treasures."\n'
            f'They went inside. {shutters} {a} switched on the light. A coat hung above an empty deckchair.'
        )
    if scene_id == "lights":
        if after["summerhouse.apology"]:
            return (
                f'{a} switched off the light. "A proper cave!"\n'
                f'The coat became a tall shape. {b} caught a sleeve. "Put it back on."\n'
                '"It\'s only the coat."\n"Then I want to see the coat."\n'
                f'{a} clicked the switch. "Sorry."\n{b} let go. "Leave it on while I\'m here."'
            )
        return (
            f'{a} switched off the light. "A proper cave!"\n'
            f'{b} looked at the sunny floor. "Your cave has windows."\n'
            f'{a} held both hands up to make a shadow. {b} made a bigger one beside it.\n'
            f'"Mine wins."\n{a} clicked the light back on. "Next time we need a cave without windows."'
        )
    if scene_id == "height_marks":
        return (
            f'{b} found pencil marks on the doorframe. "You used to be this tall."\n'
            f'{a} stood beside the lowest mark. It barely reached a shoulder. '
            '"I don\'t remember being that small."\n'
            '"You called this the sandwich house."\n"Better name."\n'
            'They checked the empty cushions, just in case.'
        )
    if scene_id == "exit_summerhouse":
        reminder = (
            f'"You can switch it off now," {b} said from the doorway. '
            if before["summerhouse.apology"] else f'"No treasure," {b} said. "Let\'s try the tree." '
        )
        if before["summerhouse.sticky"]:
            end = (f'The latch bounced open. "Lift it," {a} said. {b} lifted the door by its handle. '
                   'This time it caught.')
        else:
            end = f'The latch clicked. {a} rattled the handle once to check. "Cave secured."'
            if before["explorer.remembers_height"]:
                end += f'\n"Sandwich house," {b} said.'
            else:
                end += f'\n{b} tucked the map under an arm. "Off we go."'
        return f'{reminder}{a} turned out the light. They stepped into the garden and pulled the door shut. {end}'
    if scene_id == "crossing":
        start = "Outside, a" if before["party.location"] == "house" else "A"
        coat = after["captain.coat"]
        if after["party.route"] == "board":
            return (
                f'{start} puddle covered the path to the apple tree. "The sea," {a} said.\n'
                f'{b} helped lay a board across it, both ends resting on dry ground. '
                'They pressed it with their boots. It stayed firm.\n'
                '"One at a time."\nThey crossed slowly. Neither boot touched the brown water.'
            )
        failure = ("Its far end slipped underwater" if before["board.length"] < before["puddle.width"] + 20
                   else "The rotten end crumbled")
        return (
            f'{start} puddle covered the path. {a} laid down a board; {b} tested it with a boot. '
            f'{failure}, splashing the captain\'s {coat} sleeve.\n'
            f'They pulled it out. {b} pointed around the flower bed. "Land all the way."\n'
            f'{a} stepped aside. "Show me." Together they followed the longer path to the apple tree.'
        )
    if scene_id == "treasure":
        lift = (
            f'{a} tugged at it. "Help?" {b} took the other side. Together they set it aside.'
            if after["pot.mass"] > after["captain.strength"] else
            f'{a} lifted it aside. "There!"'
        )
        garment = "green jacket" if before["captain.coat"] == "green" else "coat"
        lid = ""
        if before["captain.hands_wet"]:
            lid = f'{a} tried the lid, then dried slippery fingers on the {garment}. '
        if before["tin.tight"]:
            opening = f'{b} braced the tin. "Ready?"\n{a} pulled. Pop!'
        elif before["captain.hands_wet"]:
            opening = 'This time the lid came away easily.'
        else:
            opening = f'{a} eased the lid open.'
        return (
            f'Under the apple tree stood an upside-down flowerpot. {lift}\n'
            f'{b} picked up the biscuit tin underneath. {lid}{opening}\n'
            'Inside were two ginger biscuits, one broken.\n"Gold?"\n"Better. You can eat this."'
        )
    if scene_id == "share":
        if after["captain.claimed_whole"]:
            return (
                f'"Captains get the whole one," {a} said. {b} stopped reaching.\n'
                f'{a} divided the broken pieces into two piles, then broke the whole biscuit '
                'and added half to each.\n"Explorers get half."\n"Half of which?"\n"Both."\n'
                f'{b} checked both piles. They ate beneath the dripping leaves.'
            )
        return (
            f'{a} broke the whole biscuit in half. {b} divided the broken pieces into two piles.\n'
            '"Which do you want?"\n"That one has a bigger crumb."\n'
            f'{a} moved the crumb to the other pile. They looked again, then laughed. '
            'Both took a share. Soon only ginger crumbs remained on their fingers.'
        )
    route = "They crossed the board again" if before["party.route"] == "board" else "They took the long path home"
    home = f'{route}, carrying the empty tin. At home, boots came off and the tin went on the table. '
    sleeve = ""
    if before["captain.sleeve_wet"]:
        if before["captain.coat"] == "red":
            regret = "Should have changed." if before["captain.clothing_decided"] else "That needs washing."
            sleeve = f'{a} rubbed the muddy red sleeve. "{regret}" '
        else:
            sleeve = f'{a} hung up the muddy green jacket; the red coat was still clean. '
    if scene_id == "ending_bridge":
        return (
            home + f'On the sofa, {b} drew their bridge on the map.\n'
            '"Biscuit Bridge," the captain decided.\n"We both built it."\n'
            f'{a} added two tiny figures beside it, standing shoulder to shoulder.'
        )
    if scene_id == "ending_explorer":
        return (
            home + sleeve + f'{b} named the long way Biscuit Passage on the map. '
            f'{a} offered the paper hat.\n"Your turn to be captain."\n'
            f'{b} put it on and made room on the sofa. "Let\'s choose where to go."'
        )
    if scene_id == "ending_together":
        return (
            home + sleeve + f'{a} offered {b} the paper hat. "Captain tomorrow?"\n'
            f'"Together." {b} put it on. "But ask before making it dark."\n"I will."\n'
            'They spread the map between them on the sofa. Neither kept it on their own knee.'
        )
    raise ValueError(f"No prose for scene: {scene_id}")
