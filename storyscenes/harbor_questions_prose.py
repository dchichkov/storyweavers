"""Scene-sized prose around requests, evidence, changed plans and consequences."""
from .capabilities.reading import Document, Statement
from .harbor_questions_story import understood_value
from .harbor_recovery import add_second_look, decision, divided_scene


def render(spec, state):
    kind = state.get("harbor_jobs", "ari").kind
    seen = state.get("evidence", "seen")
    mode = decision(state).mode
    value = understood_value(state)
    first_result = state.get("propositions", seen.proposition).result
    first_value = first_result.value if first_result.kind == "exact" else None
    reported = seen.observer == "cy"
    observer = "Cy" if reported else "Ari"
    events = {e.action.id: e.id for e in state.events}
    commitment = state.get("harbor_jobs", "ari").prior_commitment
    refused = state.get("requests", "help").response == "declined"
    unknown_route = kind == "shortcut" and value is None
    rows = []

    def add(id, text, question, answer, *actions):
        rows.append(Statement(id=id, text=text, question=question, answer=answer, kind=id, focus="ari",
            event_ids=tuple(events[a] for a in actions), entity_ids=("ari", "cy", "crate"),
            needs=(rows[-1].id,) if rows else ()))

    opening = {
        "load": 'A space on the handcart was waiting for a crate of stone slabs. There was a large crate on the workshop floor, which was almost the same thing. '
                'Ari looked from it to Cy. Cy had two perfectly ordinary arms, but at the moment they seemed more promising than Ari\'s own.',
        "parcel": 'The picnic boat needed cups. Ari found a box in the workshop and began planning where it should go before looking inside it. '
                  'There was room beside the boat for one more useful thing, and Ari was pleased to have found it.',
        "shortcut": 'Ari wanted a parcel taken to the jetty. From the workshop, the footbridge was the short way; the lane past the sheds was the long way. '
                    'In Ari\'s mind, the parcel was already halfway across the bridge. Cy, who would have to carry it, was still standing on the floor.',
        "tool": 'A tied parcel of paper flags waited in the workshop. Ari had decided that opening it was a job for scissors. '
                'Cy had a pair. This made Cy, for the moment, the most useful person in the harbor.',
    }[kind]
    add("opening", opening, "What was Ari trying to arrange?", {
        "load": "Ari wanted the crate loaded onto the handcart. Ari believed it held stone slabs and wanted help carrying it.",
        "parcel": "Ari wanted cups put onto the picnic boat. Ari believed the workshop box contained them.",
        "shortcut": "Ari wanted the parcel delivered to the jetty. Ari expected Cy to use the footbridge.",
        "tool": "Ari wanted to open the parcel of paper flags. Ari believed scissors would be needed.",
    }[kind], "ask")

    if commitment:
        add("commitment", 'Cy had already promised Bo the brass key by the bell. Bo had gone to the jetty to wait for it. '
            'The key was still with Cy. It was a small thing to carry, but it had brought a whole earlier arrangement with it.',
            "What earlier promise did Cy have?",
            "Cy had promised to bring Bo the brass key at the jetty by the bell. Bo had already gone there, while Cy still held the key.",
            "prior_promise", "bo_lane", "bo_round")

    request = {
        "load": '"Could you put that on the cart?" Ari asked. "It will be heavy."\n"Will it?" said Cy.\n"It is a stone crate."\n"That tells me what you call it." Cy stayed beside the crate. "Shall we find out what is in it?"',
        "parcel": '"Will you put the box on the boat?" Ari asked. "Then the cups are dealt with."\n"Are they?" said Cy.\n"They will be when you put it there."\nCy looked at the box. "I was thinking of an earlier step."',
        "shortcut": '"Will you take it over? The bridge will save you a walk."\n"A longer walk," Cy said. "It will still be a walk."\n"A much shorter one."\nCy looked toward the crossing. "Let us make sure it goes all the way across."',
        "tool": '"May I have the scissors?" Ari asked.\n"What are you cutting?"\n"Whatever is keeping this parcel shut."\nCy did not pass them over yet. "It might be something we want to keep."',
    }[kind]
    add("request", request, "What did Ari ask Cy to do?", {
        "load": "Ari asked Cy to load the crate onto the cart. Cy suggested checking its contents before doing that.",
        "parcel": "Ari asked Cy to put the box on the boat. Cy wanted the contents checked first.",
        "shortcut": "Ari asked Cy to take the parcel to the jetty. They paused to check the footbridge before setting off.",
        "tool": "Ari asked to use Cy's scissors. Cy wanted to know what held the parcel shut before handing them over.",
    }[kind], "request", "acknowledge")

    if first_value is None:
        inspection = {
            "load": f'{observer} looked into the opened crate, but an inner wrapping still hid what it held. "I cannot tell from here." The space on the cart remained an empty space, not an answer.',
            "parcel": f'{observer} looked inside. The contents were still wrapped. The open lid had revealed another covering, not what lay beneath it.',
            "shortcut": f'{observer} tried to make out the footbridge through the fog. The far end disappeared. "I cannot see enough to call it open." The parcel did not grow any nearer the jetty.',
            "tool": f'{observer} looked at the fastening. A fold of wrapping hid how it was tied. "I still cannot see what the scissors would cut." Cy kept the scissors.',
        }[kind]
        answer = f"{observer} could not get a clear enough view to check Ari's assumption. The inspection left the answer unknown."
    else:
        inspection = {
            ("load", True): f'{observer} looked into the crate. Stone slabs lay inside, with hardly any space between them. It was a load of real stones, not merely a large box with an important name.',
            ("load", False): f'{observer} looked into the crate. There was the wooden bottom, with nothing on it. The stone slabs existed, for the moment, only in Ari\'s instructions.',
            ("parcel", True): f'{observer} looked inside the box. There were the paper cups, nested one inside another. The useful little spaces had been packed together into a very small space indeed.',
            ("parcel", False): f'{observer} looked inside the box. Paint tins occupied the places Ari had already assigned to cups. They might be useful at the harbor, but not for drinking out of at the picnic.',
            ("shortcut", True): f'{observer} checked the footbridge. The barrier was open and the crossing was clear. For once, the short route in Ari\'s head matched the route outside.',
            ("shortcut", False): f'{observer} checked the footbridge. Its barrier was shut. The short way was still short; it simply was not a way they could use.',
            ("tool", True): f'{observer} examined the fastening. A sealed band held the parcel shut; there was no loose end to pull. This was a job for the scissors after all.',
            ("tool", False): f'{observer} examined the fastening and found the loose end of a bow. It had looked rather permanent from farther away. Close up, it offered a place to start.',
        }[(kind, first_value)]
        finding = {("load", True): "stone slabs inside the crate", ("load", False): "an empty crate",
                   ("parcel", True): "paper cups inside the box", ("parcel", False): "paint tins instead of cups",
                   ("shortcut", True): "an open footbridge", ("shortcut", False): "a closed footbridge",
                   ("tool", True): "a sealed band that needed cutting", ("tool", False): "a bow with a loose end"}[(kind, first_value)]
        answer = f"{observer} found {finding}. " + ("That supported Ari's original assumption." if first_value else "That contradicted Ari's original assumption.")
    add("inspection", inspection, "Who checked first, and what did that inspection establish?"
        if state.get("evidence", "reseen") else "Who checked, and what did the inspection establish?", answer, "inspect")

    if reported:
        text = ('Cy described the part that was still hidden. Ari listened. "Then you have not found out either."\n"No," Cy said. "I have found out that I cannot tell yet."'
                if first_value is None else
                'Cy told Ari what the inspection had shown. Ari listened to the whole answer before reaching for anything. "I asked you for help," Ari said. "I suppose that includes telling me what you find."')
        add("report", text, "How did Ari receive the first inspection result?"
            if state.get("evidence", "reseen") else "How did Ari receive the inspection result?",
            "Cy explained what the inspection had shown, and Ari listened. Ari was using Cy's report rather than a separate personal inspection.",
            "explain", "hear", "understand")

    add_second_look(add, state)

    if refused:
        revision = 'Cy looked at the key. "I cannot do your job first. I promised Bo."\n"But we have just checked mine," Ari said.\n"Yes. Now we know what it needs. It does not make Bo stop waiting."'
        if kind == "parcel":
            revision += '\nAri looked at the box of cups. "I can carry this one."\n"Then you need not wait for me either," Cy said.'
        else:
            revision += '\nAri looked at the unfinished job. It had not become less real. Neither had the other one.'
        answer = "Cy declined to help immediately because of the earlier promise to Bo. The confirmed need did not cancel that commitment."
    elif unknown_route:
        revision = '"We still do not know about the bridge," Ari said.\n"I know the lane," Cy answered. "Past the sheds, all the way to the jetty."\n"But it is longer."\n"Only than a bridge we can cross." Ari looked at the parcel. "The lane, then."'
        answer = "Ari did not learn whether the footbridge was open. Cy accepted the delivery using the known lane instead, so uncertainty about the shortcut did not stop the whole task."
    elif mode == "defer":
        revision = '"Let us stop this job here," Ari said. "I have been giving instructions to a guess."\nCy nodded. "It did sound very sure of itself."\nAri did not replace the first guess with a second one.'
        answer = "Ari withdrew the request because the available evidence was unclear. Ari did not claim to have proved the original assumption false."
    elif mode == "adopt":
        revision = {
            "load": '"So I do need help," Ari said.\n"Yes," said Cy. "Now we know what with."\nAri moved aside to leave room by the crate. The request sounded smaller now, and more useful.',
            "parcel": '"Cups," Ari said. "As requested."\n"As checked," Cy answered.\nAri smiled. "Both, then. Will you take them?" This time the question included a real box of cups.',
            "shortcut": '"You can take the bridge," Ari said.\n"Now I can," Cy answered.\nAri looked at the clear crossing. Waiting to check had not made the bridge any longer.',
            "tool": '"I was right about the scissors," Ari said.\n"You were," Cy agreed.\nAri waited.\n"And we have not cut anything merely to find that out."',
        }[kind]
        answer = "Ari kept the original plan after the inspection supported it. Cy then accepted the request."
    else:
        revision = {
            "load": '"I asked you to carry the stones before I had found any stones," Ari said.\n"You did."\n"I can manage the box."\n"That," Cy said, "is a different request. It seems to be addressed to you."',
            "parcel": '"Do not put it on the boat," Ari said. "I will take it to the workbench. We can use the paint for the sign."\n"And the cups?"\n"Are still a separate job," Ari admitted.',
            "shortcut": '"The lane, then," Ari said.\n"Past the sheds."\n"The long way."\n"The way that reaches the jetty," Cy said. Ari stopped trying to shorten it with words.',
            "tool": '"Keep the scissors," Ari said. "I think my fingers can do this."\n"They have been available all morning," Cy said.\nAri took hold of the loose end instead of the blades.',
        }[kind]
        answer = {"load": "Ari withdrew the request for Cy to load the crate. Ari would carry the empty box instead.",
                  "parcel": "Ari withdrew the request to put the box on the boat. Ari chose to put the paint at the workbench instead.",
                  "shortcut": "Ari gave up the footbridge route after learning it was closed. The parcel still needed to reach the jetty, so Cy accepted the delivery by the longer route.",
                  "tool": f"{observer} had found a bow, so Ari withdrew the request for scissors. Ari chose to untie it instead of cutting it."}[kind]
    add("revision", revision, "Why did Cy decline this request?" if refused else "What did Ari do with the new information?", answer,
        ("re" + mode) if state.get("evidence", "reseen") else mode, "say_uncertain" if value is None else "say_decision", "cy_understands",
        "refuse" if refused else "withdraw" if kind != "shortcut" and (value is None or value is False) else "accept")

    if commitment and state.get("requests", "help").response == "accepted" and kind in {"load", "parcel"}:
        add("priority", '"I will do this first," Cy said. "Then the key."\nAri looked pleased. Cy kept the key close while turning to the other work. '
            'Moving one job ahead had not moved the promised time further away.',
            "Which task did Cy put first?",
            "Cy chose to perform Ari's accepted request before taking the key to Bo. The earlier promise still had the same deadline.",
            "accept", "prior_promise")

    if refused:
        if kind == "parcel":
            action = 'Ari picked up the box of cups and put it aboard the picnic boat. It was an ordinary lift, once Ari stopped waiting for someone else to make it.'
            ending = 'The cups were aboard. Ari had asked for a pair of hands and discovered that the nearer pair would do.'
            action_answer = "Ari loaded the box of cups onto the picnic boat without Cy's help. Cy's refusal did not prevent that lighter task from being completed."
            ending_answer = "The cups reached the picnic boat through Ari's own work. Cy remained free to keep the earlier promise."
        elif state.get("harbor_jobs", "ari").recover:
            action, action_answer, ending = divided_scene()
            ending_answer = "The two slabs were repacked in the crate on the cart after Ari carried them separately. Cy did not have to break the earlier promise to carry Ari's load."
        else:
            action = 'The stone-filled crate stayed on the workshop floor. Ari did not lift one end merely to prove a point. It would still need help after Cy had taken the key.'
            ending = 'The space on the cart remained empty. This time, Ari knew both what belonged there and why it was not there yet.'
            action_answer = "The heavy crate remained on the workshop floor. Cy did not perform the declined loading request, and Ari did not attempt the heavy lift alone."
            ending_answer = "The loading was still unfinished. Ari had a confirmed need for help, but Cy had not abandoned the earlier promise to provide it."
    elif unknown_route:
        action = 'Cy carried the parcel along the lane past the sheds and put it down at the jetty. The fog had not answered their question about the footbridge. It had not needed to answer this one.'
        ending = 'The parcel rested at the jetty. Behind Cy lay the longer walk, now finished; the invisible shortcut no longer had the power to keep the parcel at home.'
        action_answer = "Cy delivered the parcel by the known lane past the sheds. No one needed to pretend that the footbridge had been found open or closed."
        ending_answer = "The delivery was complete even though the footbridge remained unverified. Cy used a known alternative without changing the uncertain belief into a fact."
    elif value is None:
        action = {"load": 'The crate stayed on the workshop floor. Cy did not load it, and Ari did not pretend that an unanswered question had become a lighter box.',
                  "parcel": 'The box stayed in the workshop. Nothing from it went onto the picnic boat. The cups would have to be found by looking, not by sending this box in their place.',
                  "shortcut": 'Cy set off nowhere. The parcel stayed in the workshop while the far end of the footbridge remained hidden. A delivery that had not happened was better than an arrival they could only imagine.',
                  "tool": 'The scissors stayed with Cy. The parcel stayed tied. Ari left the hidden fastening alone instead of making a cut that could not be taken back.'}[kind]
        ending = {"load": 'The space on the cart was still empty. This time Ari looked at it as room for something they had yet to find, not something already promised.',
                  "parcel": 'Ari stood beside the box, no longer calling it the cups. The picnic boat had one fewer thing aboard than planned, and one fewer guess riding with it.',
                  "shortcut": 'Between the workshop and the unseen far end lay a short bridge and an honest pause. The parcel was still here. For now, that was the only arrival Ari could name.',
                  "tool": 'The unused scissors stayed in Cy\'s hand. For the first time that morning, Ari was glad they had not been useful.'}[kind]
        object_name = {"load": "crate", "parcel": "box", "shortcut": "parcel", "tool": "parcel"}[kind]
        action_answer = f"The request was withdrawn and its physical task was not performed. The {object_name} remained in the workshop."
        ending_answer = "The original task remained unfinished. Ari stopped treating an uncertain assumption as enough reason to carry it out."
    else:
        action = {
            ("load", True): 'Cy lifted the loaded crate onto the handcart. Ari watched the stone slabs arrive where they were meant to be, inside a crate rather than inside an argument. "Thank you," Ari said. This was easier than giving instructions.',
            ("load", False): 'Ari picked up the empty crate and carried it to the workbench. It was not nearly as impressive a feat as the one Ari had requested. It was, however, a useful empty box.',
            ("parcel", True): 'Cy lifted the box onto the picnic boat. The cups went with it, still nested together. Ari did not have to imagine them being there this time.',
            ("parcel", False): 'Ari carried the paint box to the workbench. It did not become a box of cups on the way. Its usefulness simply stopped depending on that mistake.',
            ("shortcut", True): 'Cy picked up the parcel, crossed the footbridge and set it down at the jetty. The route was short, as Ari had hoped. The delivery was real, which mattered more.',
            ("shortcut", False): 'Cy took the parcel along the lane, past the sheds, and down to the jetty. There were more steps than Ari had intended. At the end of them, there was the right place to put the parcel.',
            ("tool", True): 'Cy handed over the scissors when Ari was ready to take them. Ari cut the sealed band, opened the parcel and put it on the bench. The folded paper flags lay inside, still whole.',
            ("tool", False): 'Ari pulled the loose end. The bow came free and the parcel opened. Ari carried it to the bench, with the paper flags inside and the scissors still in Cy\'s hand.',
        }[(kind, value)]
        ending = {
            ("load", True): 'The cart held the stones. Beside it, Ari had two perfectly ordinary arms again, and someone to ask when they were not enough.',
            ("load", False): 'The empty crate stood on the bench. There was plenty of room, now that the imaginary stones were out.',
            ("parcel", True): 'The box sat aboard the boat, full of exactly what Ari had said it was. Being right after a question felt quieter than being right before one.',
            ("parcel", False): 'The paint waited beside the unfinished sign. Finding cups was still a job for later. This box could finally be useful as the thing it was.',
            ("shortcut", True): 'At the jetty, the parcel rested where it belonged. The bridge behind Cy had carried a person and a parcel, not merely a good idea.',
            ("shortcut", False): 'The parcel rested on the jetty. Behind it, the long route had become a completed journey. The short one was still only a line Ari had wanted to take.',
            ("tool", True): 'On the bench lay the open parcel and its uncut paper flags. The scissors had done a small, exact job. Ari liked them better that way.',
            ("tool", False): 'The flags lay in their opened parcel, and the bow no longer held anything shut. The scissors had done nothing at all. Ari gave them a grateful look anyway.',
        }[(kind, value)]
        action_answer = {("load", True): "Cy lifted the stone-filled crate onto the cart. The requested loading was completed.",
                         ("load", False): "Ari carried the empty crate to the workbench. Cy did not have to perform the requested loading.",
                         ("parcel", True): "Cy put the box of cups onto the picnic boat. That completed the request.",
                         ("parcel", False): "Ari put the paint box at the workbench. It was not sent onto the picnic boat as cups.",
                         ("shortcut", True): "Cy carried the parcel over the footbridge and put it at the jetty. The delivery was completed.",
                         ("shortcut", False): "Cy carried the parcel along the lane past the sheds and put it at the jetty. The delivery succeeded without using the closed bridge.",
                         ("tool", True): "Cy handed Ari the scissors, and Ari used them to open the sealed parcel. Ari put the opened parcel on the bench.",
                         ("tool", False): "Ari untied the bow and put the opened parcel on the bench. Cy kept the scissors because they were not needed."}[(kind, value)]
        ending_answer = {
            ("load", True): "The stone-filled crate was on the cart instead of the floor. Checking had confirmed that Ari really did need help with that load.",
            ("load", False): "The crate was empty and now stood on the bench. Ari had changed the request after learning that the expected stones were not inside.",
            ("parcel", True): "The cups were aboard the boat in their box. This time Ari's plan was supported by an actual inspection.",
            ("parcel", False): "The paint was at the workbench rather than on the picnic boat. Finding the cups remained a separate unfinished job.",
            ("shortcut", True): "The parcel had reached the jetty by the open bridge. The route had been checked before Cy relied on it.",
            ("shortcut", False): "The parcel had reached the jetty by the longer route. Ari's assumption about the bridge had changed, but the delivery goal had still been met.",
            ("tool", True): "The parcel was open and its paper flags were still whole. The scissors had been used for the fastening that the inspection actually found.",
            ("tool", False): "The parcel was open without using the scissors. Checking the bow had changed how Ari opened it.",
        }[(kind, value)]
    add("action", action, "What was actually done after the decision?", action_answer, "finish")
    if commitment:
        promise = state.get("promises", "key_return")
        late = promise.status == "breached"
        if late:
            text = 'Cy took the lane to the jetty and held out the brass key. Bo took it.\n"You said by the bell."\n"I helped Ari first."\n"I know what first means," Bo said. "I was here second."\nCy had brought the key back. The promised time could not be carried back with it.'
            answer = "Cy returned the key after the promised time because helping Ari came first. The physical return was completed, but it did not make the earlier deadline fulfilled."
            ending += ' The key was back in Bo\'s hand, with the lateness still belonging to Cy.'
        elif kind == "shortcut":
            text = 'Bo was waiting at the jetty. After setting down Ari\'s parcel, Cy handed over the brass key on time.\n"Both coming here?" Bo asked.\n"Both," said Cy. "That was the useful part."'
            answer = "Cy brought the parcel and the key to the same destination. Bo received the key on time, so the delivery and the earlier promise were both fulfilled."
            ending += ' Beside the delivered parcel, Bo held the key. Two jobs had fitted into one journey.'
        elif kind == "tool" and value is True:
            text = 'Passing over the scissors had left Cy time to take the key along the lane to the jetty. Bo received it on time. Ari had done the cutting; Cy had done the carrying. The two jobs had needed different things from Cy.'
            answer = "Cy handed Ari the scissors and still returned Bo's key on time. Ari did the cutting, and the brief handover left time for the key delivery."
            ending += ' At the jetty, Bo held the key on time; at the workshop, Ari had the open flags.'
        else:
            text = 'Cy took the key along the lane to the jetty. Bo accepted it by the promised time.\n"Here," Cy said.\nBo closed a hand around the brass. The small thing had arrived with the arrangement around it still whole.'
            answer = "Cy took the key to Bo at the jetty and handed it over by the promised time. The earlier promise was fulfilled by that actual return."
            if kind == "tool" and value is False:
                ending = 'The flags lay in their opened parcel at the workshop. The scissors had left with Cy without cutting a thing; the loose bow had been enough.'
            elif kind == "tool" and value is None:
                ending = 'At the workshop, the parcel remained tied and uncut. Ari had not needed an answer badly enough to cut into a hidden fastening.'
            ending += ' At the jetty, the brass key was in Bo\'s hand on time.'
        add("promise_result", text, "What happened to Cy's earlier promise?", answer, "key_return", "key_assess")
    add("ending", ending, "What was different at the end?", ending_answer, "finish")
    return Document(title=spec.title, statements=tuple(rows))
