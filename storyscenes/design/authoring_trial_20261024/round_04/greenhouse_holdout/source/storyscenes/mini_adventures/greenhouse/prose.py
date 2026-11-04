"""Authored encounters; all consequential variants read executed world state."""


def render(sid, b, a):
    if sid == "gate":
        weather = "Wind rattled" if b["weather.kind"] == "wind" else "Sun glittered on"
        return (f"{weather} the allotment greenhouse. Mara arrived with a waxed paper parcel of replacement beans. "
                "She had forgotten Ivo's watering, then blamed the tap. She wanted her friend back. "
                "At the gate she shifted the stone jamming its foot, pulled it open and carried the parcel up the path.")
    if sid == "measuring":
        return ("Their old measuring stick stood beside the door. Mara read the highest pencil mark: Ivo's initials, "
                "from a Sunday when the beans had grown without her. She touched the wood below it. Through the glass, "
                "he watched her hand. She let it fall without adding a mark of her own.")
    if sid == "enter":
        return ('"Can I come in?" Mara asked. Ivo lifted his bucket away from the doorway. '
                '"Mind the latch." She opened the door, carried the parcel inside and put it on the dry bench before shutting '
                "the door. The dead bean stalks stood in their row. He had not thrown them away yet.")
    if sid == "snail":
        return ("A snail was edging around an empty pot. Mara slipped a fallen leaf beneath it and set it in the big pot "
                "beside the doorway. Last summer they had called every snail Admiral. She nearly said it now. Ivo watched "
                "the leaf settle, but neither of them supplied the name.")
    if sid == "admit":
        return ('"The beans are for you," Mara said. Ivo left the string alone. "Did the shop have a tap too?" '
                'Her prepared excuses deserted her. "I forgot. The tap worked. Then I lied." '
                'He pressed a thumb into the bench soil. "I spent an hour taking it apart." This time she did not explain herself away.')
    if sid == "deflect":
        return ('Mara pushed the parcel towards him. "The tap must have stuck. These should replace them." '
                'Ivo pushed it back. "I checked the tap. There was nothing wrong with it." '
                "She kept her hands beside the parcel instead of answering. Between them the string lay in a neat bow, still untied.")
    if sid == "tea":
        response = ('"Thanks," he said, not yet looking at her.' if b["mara.confessed"] else
                    'He took the cup but left the parcel where it was.')
        return ("Mara unscrewed her small flask and divided the tea between two cups. There was only enough for half a cup each. "
                f"{response} They drained their cups standing at opposite ends of the bench. She screwed the flask's lid back on rather carefully.")
    if sid == "gust":
        return ("A gust lifted the roof vent. Rain blew through the gap onto Ivo's young tomatoes, bending the matchstick stems. "
                "He pulled the closing cord; it came away in his hand. Mara caught the swinging end. Neither pull had moved the vent. "
                '"We need to hold it down," he said, looking up at the next cloud.')
    if sid == "heat":
        return ("The greenhouse had grown close and breathless. Ivo's young tomatoes drooped towards the hot bench. He pulled the vent cord, "
                "but the cord parted and the pane stayed shut. Mara watched a leaf curl against the glass. "
                '"It has to stay open," Ivo said. "Not just while someone stands here holding it."')
    if sid == "patch_tape":
        work = ("lowered the frame while she wedged the notched wooden stay between its handle and the bracket" if b["weather.kind"] == "wind" else
                "raised the frame while she seated the notched wooden stay between frame and sill, taking its weight")
        result = "rain stopped reaching the tray" if b["weather.kind"] == "wind" else "air reached the leaves"
        return (f"Mara tested the roll. Enough tape remained. Ivo {work}. "
                f"She taped the stay's foot to the bracket. They let go; {result}. "
                "The parcel stayed tied on the bench.")
    if sid == "patch_parcel":
        work = ("lowered the frame; she braced its handle with the notched wooden stay and trapped the paper over the rain gap" if b["weather.kind"] == "wind" else
                "raised the frame; she seated the notched wooden stay beneath it, padding its foot with the paper. The timber took the weight")
        return ('The roll was empty. "May I use your tin?" Mara asked. Ivo opened it; she unwrapped the beans and tipped them in. '
                f"He {work}. She lashed the stay to the bracket with the parcel string. They let go. The frame held.")
    if sid == "shelter":
        offer = ('"Tape the wooden stay?" Ivo asked.' if b["tape.available"] else
                 '"Your parcel string could secure the wooden stay," Ivo said.')
        unused = "The tape lay unused." if b["tape.available"] else "The parcel was still tied."
        if b["weather.kind"] == "wind":
            return (f'The tray sagged in Mara\'s hands. {offer} "Moving them will be quicker," Mara said. '
                    "She put her parcel underneath. Ivo joined her. They spent half an hour teasing rooted pots free and carrying them down. "
                    "The first gust bruised leaves; the next snapped two stems before they reached shelter. "
                    f"Ten seedlings stood on the lower bench. {unused}")
        return (f'The tray sagged in Mara\'s hands. {offer} "Moving them will be quicker," Mara said. '
                "She sheltered the parcel and opened the door. Ivo joined her. They spent half an hour freeing rooted pots for the shaded lower bench. "
                "Leaves wilted first; by the last trip, two seedlings had scorched leaves. "
                f"They were alive, but those leaves would not recover. {unused}")
    if sid == "sow":
        source = "the sandwich tin" if b["beans.location"] == "tin" else "the parcel she opened"
        invitation = ('"You can take a turn again," he said. "But tell me if you cannot come."' if b["ivo.receptive"] else
                      '"Only while I am here," he said. Mara nodded and stayed beside him.')
        return (f"Mara took the dry beans from {source}. Ivo moved six empty pots towards her and kept six for himself. "
                f"{invitation} They pressed a bean into each pot. She watered them from the full can until twelve dark circles spread across the soil.")
    if sid == "store":
        reason = ('"These beans feel damp," Mara said.' if b["beans.damp"] else
                  '"Not another tray today," Ivo said, looking at the damaged seedlings.')
        handoff = ('She asked for his sandwich tin; Ivo opened it. She unwrapped the beans and spread them inside.'
                   if not b["tin.borrowed"] else
                   'The borrowed sandwich tin was still open. Mara spread the beans out inside it.')
        return (f'{reason} {handoff} She set the open tin on the shelf. '
                '"Can I come back to help?" Mara asked. "Saturday. While I am here," Ivo said. She nodded, leaving the beans unsown.')
    if sid == "return":
        carrier = "the tin" if b["beans.location"] == "tin" else "the parcel she opened"
        exchange = ('"I helped, though." He nodded towards the vent. "That was help. It wasn\'t an answer about the tap."'
                    if b["tomatoes.state"] == "saved" else
                    '"I wanted to make it right." He looked at the damaged seedlings. "You kept the present. I wanted you to tell me the truth."')
        return (f'Ivo gathered the beans from {carrier} and tipped them into Mara\'s cupped hands. '
                '"They are yours. I did not ask for replacements." She looked at the small hard shapes. '
                f'{exchange}')
    if sid == "ledger":
        return ("Ivo opened the allotment notebook to the next blank Saturday. Mara wrote her name below his, not across the whole space. "
                '"If I cannot come, I will tell you beforehand." He left the pencil between the pages. '
                "The entry was smaller than the promise she had made last time, and easier to check.")
    if sid == "ending_joint":
        image = ("The paper patch breathed above the pots." if b["parcel.location"] == "vent" and b["weather.kind"] == "wind" else
                 "Above the pots, the repaired vent held steady.")
        callback = " Their names waited together in the notebook." if b["ledger.written"] else ""
        return ('Outside, Mara closed the greenhouse door. Ivo put the spare key in her palm. '
                '"This does not make last week disappear," Ivo said. "I know," Mara said. '
                f"Through the glass they could see twelve dark circles of watered soil. {image}{callback} She closed her hand around the key, not the beans.")
    if sid == "ending_trial":
        image = "twelve newly filled pots" if b["beans.location"] == "pots" else "an open tin of unsown beans"
        return ('They stepped onto the path and Mara closed the door. Ivo kept the key. "Knock on Saturday." '
                'She nodded without asking for it. Through the glass stood '
                f"{image}. There would be no coming and going on her own yet. She waited until he had finished speaking before turning towards the gate.")
    if sid == "ending_apart":
        paper = ("Her waxed paper stayed in the vent." if b["parcel.location"] == "vent" else
                 "The empty waxed paper stayed on his bench.")
        return ('Mara stepped outside, shut the door and walked back to the open gate with the beans in her hands. '
                f"{paper} Ivo stayed by the greenhouse. "
                "She had brought something to leave behind and was carrying the important part away. At the gate she put the beans in her pocket, one careful handful at a time.")
    raise ValueError(sid)
