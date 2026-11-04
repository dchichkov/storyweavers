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
                f"{response} They drank standing at opposite ends of the bench. When the flask was empty, she screwed its lid back on rather carefully.")
    if sid == "gust":
        return ("A gust lifted the roof vent. Rain blew through the gap onto Ivo's young tomatoes, bending the matchstick stems. "
                "He pulled the closing cord; it came away in his hand. Mara caught the swinging end. Neither pull had moved the vent. "
                '"We need to hold it down," he said, looking up at the next cloud.')
    if sid == "heat":
        return ("The greenhouse had grown close and breathless. Ivo's young tomatoes drooped towards the hot bench. He pulled the vent cord, "
                "but the cord parted and the pane stayed shut. Mara watched a leaf curl against the glass. "
                '"It has to stay open," Ivo said. "Not just while someone stands here holding it."')
    if sid == "patch_tape":
        work = ("held the vent down while she taped its handle to the bracket" if b["weather.kind"] == "wind" else
                "held the vent up while she bound its handle to the upper bracket")
        result = "rain stopped striking the tray" if b["weather.kind"] == "wind" else "cooler air reached the tray"
        return (f"Mara tested the repair roll. Enough tape remained. Ivo {work}. She used the last length and set the empty roll down. "
                f"When they let go, {result}. The parcel was still on the bench, its bow untouched; for once it had not been the answer.")
    if sid == "patch_parcel":
        work = ("spread the waxed paper across the gap and tied it against the vent handle" if b["weather.kind"] == "wind" else
                "folded the waxed paper into a thick wedge and tied the raised vent handle to its bracket")
        return ("The tape roll was empty. Mara showed Ivo the cardboard centre, then asked for his sandwich tin. "
                "He opened it. She untied the parcel, tipped the beans into the tin, and "
                f"{work} with the parcel string. The tomatoes were sheltered now; her present had become a piece of the greenhouse.")
    if sid == "shelter":
        danger = "wind shook" if b["weather.kind"] == "wind" else "heat curled"
        return ("Mara tried to lift the tomato tray, but its rotten wooden base sagged. She set it back before it broke. "
                f"As the {danger} the leaves, she slid her parcel under the bench instead. "
                "By the time she looked up, the stems had collapsed. The replacement beans were protected. Ivo's tomatoes were not.")
    if sid == "sow":
        source = "the sandwich tin" if b["beans.location"] == "tin" else "the parcel she opened"
        invitation = ('"You can take a turn again," he said. "But tell me if you cannot come."' if b["ivo.receptive"] else
                      '"Only while I am here," he said. Mara nodded and stayed beside him.')
        return (f"Mara took the dry beans from {source}. Ivo moved six empty pots towards her and kept six for himself. "
                f"{invitation} They pressed a bean into each pot. She left the soil loose this time, watching how lightly his fingers moved.")
    if sid == "store":
        reason = ('The beans felt damp. "We need to see whether these spoil," Ivo said.' if b["beans.damp"] else
                  'Ivo looked at the collapsed tomatoes. "Not another tray today," he said.')
        return (f'{reason} Mara spread the beans in his open sandwich tin and put it on the shelf. '
                '"I can come back and help clear up." He paused. "Saturday. While I am here." '
                "She left the tin open. There was work to return for, not a harvest to claim.")
    if sid == "return":
        carrier = "the tin" if b["beans.location"] == "tin" else "the parcel she opened"
        exchange = ('"I helped, though." He nodded towards the vent. "That was help. It wasn\'t an answer about the tap."'
                    if b["tomatoes.state"] == "saved" else
                    '"I wanted to make it right." He looked at the fallen tomatoes. "You saved the present. I wanted you to tell me the truth."')
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
                '"This does not make last week disappear." "I know." '
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
