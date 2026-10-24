"""Scene-sized, trace-conditioned prose for the harbor experiment only.

Passages cite enacted events and declared initial premises. They are authored
realizations, not a proof of English entailment; keep story-only judging too.
"""
import random

from .capabilities.reading import Document, Statement


def render(spec, state, config, seed=0):
    if config.purpose == "shared_rope":
        from .harbor_interaction_prose import render_shared_rope
        return render_shared_rope(spec, state, config, seed)
    if config.purpose != "trial":
        return render_errand(spec, state, config, seed)
    rng = random.Random(seed)
    by_action = {}
    for event in state.events:
        by_action.setdefault(event.action.id, []).append(event)
    rows = []
    initial = {table: {row.id: row for row in records} for table, records in spec.records.items()}

    def choose(*variants):
        return rng.choice(variants)

    def add(id, text, *, events=(), premises=(), kind="what", focus="cy", question="", answer="", needs=()):
        event_ids = tuple(e.id for action in events for e in by_action[action])
        for fact in premises:
            if fact not in initial["facts"]:
                raise ValueError(f"Unknown initial premise {fact}")
        rows.append(Statement(id=id, text=text, kind=kind, focus=focus, answer=answer,
            question=question, event_ids=event_ids + tuple(f"initial/{p}" for p in premises),
            entity_ids=(focus,), needs=needs))

    def quote(action, *, tag=False):
        line = by_action[action][0].action.reason
        if not line:
            raise ValueError(f"Missing enacted dialogue: {action}")
        return f'"{line.rstrip(".") + "," if tag else line}"'

    opening = choose(
        "Cy's little wooden boat had a red cloth sail. Cy held it on the quay, ready to try it in the sheltered harbor pool.",
        "On the quay, Cy held a little wooden boat with a red sail. The boat was ready for the harbor pool; Cy was ready to see it float.",
        "The red sail on Cy's wooden boat was ready. Cy had brought the boat to the quay for a first try in the harbor pool.")
    add("opening", opening + " First came the measuring stick: the pool had to be deep enough. "
        "And the harbor timetable allowed no new launches after the ferry bell.",
        premises=("goal", "boat_design", "schedule"), kind="goal",
        question="What did Cy want to do, and what had to happen first?",
        answer="Cy wanted to try the wooden boat in the harbor pool before launch time ended. First, Cy had to check the water with the measuring stick.")

    add("old_message", choose(
        'Ari found the stick in Bo\'s tool case at the workshop and sent Cy a message. "Your stick is in the workshop. I have just seen it in the case."',
        'At the workshop, Ari checked Bo\'s tool case. There was Cy\'s measuring stick. "Found it," Ari told Cy in a message. "In the case, here in the workshop."',
        'Ari looked into the tool case at the workshop. "Your measuring stick is here," said the message Ari sent to Cy. "I checked."'),
        events=("old_look", "old_send"), focus="ari", kind="claim",
        question="What did Ari's first message tell Cy?",
        answer="Ari reported seeing the measuring stick in the tool case at the workshop. That described where it was when Ari checked.")

    early_handoff = "give_stick" in by_action
    moved = "bo_deposit" in by_action
    if moved:
        add("move", choose(
            'Before that message reached Cy, Bo picked up the tool case. "I need the case at the jetty," Bo said. The stick went along inside it.',
            'The message was still on its way when Bo carried the case to the jetty. Cy\'s stick traveled with the tools, without any message of its own.',
            'Bo had a use for the tool case at the jetty. By the time Cy heard Ari\'s message, Bo had carried it there and set it down, measuring stick and all.'),
            events=("bo_lift", "bo_deposit"), focus="bo", kind="why",
            question="Why did Ari's first message no longer give the stick's current location?",
            answer="Bo carried the tool case, with the measuring stick inside, from the workshop to the jetty before Cy received the message.",
            needs=("old_message",))

    if early_handoff:
        add("early_arrival", "This message reached Cy at once. Cy went straight to the workshop. "
            "Bo already had the case in hand, but had not left with it.",
            events=("old_receive", "bo_lift", "cy_quay_workshop"), kind="why",
            question="How did the prompt message help Cy?",
            answer="Cy reached the workshop while Bo was still there with the case. Cy could ask for the stick before it was carried away.", needs=("old_message",))
        add("handoff", choose(
            '"Could I have my measuring stick before you go?" Cy asked. Bo held out the case. "All of this?" "Just the stick," said Cy. Bo handed it over and kept the case.',
            '"Wait. My stick is in there," Cy said. Bo stopped. "Do you need it?" Cy held up the boat. "She has not had her first voyage." "Then we had better not keep her waiting." Bo took out the stick and handed it over.',
            '"I need the stick, not the whole case," Cy said. "Could you pass it to me?" "That I can do," said Bo, putting the stick into Cy\'s hand. Cy tucked it alongside the little boat.'),
            events=("deliver_stick_request", "accept_stick_request", "give_stick"), focus="bo", kind="how",
            question="How did Cy get the stick without taking Bo's case?",
            answer="Cy asked Bo to hand over just the measuring stick. Bo agreed and gave it to Cy, keeping the case.", needs=("early_arrival",))
        acquired = "handoff"
    else:
        search = state.get("evidence", "search")
        wrong_place = search is not None and search.outcome != "exact"
        fresh = "fresh_receive" in by_action
        if config.cautious and config.message_delay:
            add("wait", choose(
                'Cy read the message twice. Ari had sent it a while ago. "Still there?" Cy wondered, and waited on the quay for newer news.',
                'The message was old. Cy nearly set off, then stayed beside the timetable. "I hope you have looked again, Ari." The little red sail waited too.'),
                events=("old_receive",), kind="why",
                question="Why did Cy wait instead of going straight to the workshop?",
                answer="Ari's message described an earlier inspection. Cy waited for newer information rather than assuming the stick had stayed there.", needs=("old_message",))
            if not fresh:
                add("no_update", "No newer message arrived while Cy waited. Waiting had not found the stick. Cy went to check the workshop instead.",
                    events=("search_look",), kind="how",
                    question="What did Cy do when waiting brought no newer message?",
                    answer="Cy stopped waiting and checked the workshop in person.", needs=("wait",))
        if wrong_place:
            add("empty_workshop", choose(
                    'Cy tried the workshop first. No case. No measuring stick. "You said it was here, Ari." Cy looked at the little boat, still dry in one hand.',
                    'At the workshop, Cy searched for the stick. It was gone, and so was the case. "That was a short voyage," Cy told the boat. "We have come to the wrong port."',
                    'Cy went to the workshop. The place where the case had stood was empty. Cy read Ari\'s message again, then folded it away. The boat would need another plan.'),
                events=("search_look",), kind="what",
                question="What went wrong when Cy tried the workshop?",
                answer="Cy could not see the measuring stick there. Ari's earlier report had been accurate, but the case had since been moved to the jetty.", needs=("old_message", "move"))
        if fresh:
            fresh_evidence = state.get("evidence", "fresh")
            destination = state.get("propositions", fresh_evidence.proposition).result.value
            at_jetty = destination == "jetty"
            where = "jetty" if at_jetty else "workshop"
            add("new_message", choose(
                f'Ari checked the case again and sent a second message. "I can see your stick now. In the case at the {where}." "Now is better," Cy said, and set off.',
                f'Then came Ari\'s second message. "I have looked again. Your stick is in the case at the {where}." Cy read the new time on it. "Right. The {where}."',
                f'Ari looked inside the case once more. "At the {where}," the new message said. "Your stick is here. I have just checked." Cy put the old message away.'),
                events=("fresh_look", "fresh_send", "fresh_receive"), focus="ari", kind="what",
                question="What made Ari's second message more useful than the first?",
                answer=f"Ari had inspected the stick again and reported its more recent location at the {where}. Cy could act on the newer report.", needs=("old_message",))
        if wrong_place and not fresh:
            add("search_elsewhere", 'There was one other place to try: the jetty. "Come on, boat," said Cy. "One more port." Cy went there to look.',
                events=("find_look",), kind="how",
                question="How did Cy continue the search without a corrected message?",
                answer="After finding no stick in sight at the workshop, Cy tried the jetty and looked there in person.", needs=("empty_workshop",))
        tag = "find" if "find_look" in by_action else "search"
        found_where = state.get("propositions", f"{tag}:proposition").result.value
        opened = "cy_open" in by_action
        add("found", ("Cy opened the tool case. " if opened else "") + choose(
            f'At the {found_where}, the measuring stick lay inside the tool case. {quote("take_stick", tag=True)} Cy said, picking it up. Cy held it beside the boat like a very tall mast.',
            f'Cy found the stick inside the tool case at the {found_where} and picked it up. {quote("take_stick")} The wooden boat and its measuring stick were together at last.'),
            events=tuple(a for a in ("cy_open", f"{tag}_look", "take_stick") if a in by_action), kind="where",
            question="Where did Cy finally find the measuring stick?",
            answer=f"Cy found it in the tool case at the {found_where} and picked it up.",
            needs=(("new_message",) if fresh else ("search_elsewhere",) if wrong_place else ("old_message",)))
        acquired = "found"

    measure_tick = by_action["measure"][0].tick
    detoured = any(e.action.id == "cy_workshop_quay" for e in state.events
                   if e.tick < measure_tick)
    if not config.direct_path and detoured:
        detour = choose("The closed workshop path had already taken Cy the long way around by the quay. ",
                        "Getting here had meant going around the closed path by the quay. The boat had traveled farther in a hand than it had on water. ")
    else:
        detour = ""
    # The controller reaches the jetty and performs this actual instrument-backed check.
    deep = state.get("propositions", state.get("evidence", "depth").proposition).result.value == "deep enough"
    measurement = (choose('The wet mark was high enough. "Room for your bottom," Cy told the boat.',
                         'There was enough water under the little hull. "You will fit," Cy said.') if deep else
                   choose('The stick touched bottom almost at once. "Oh." Cy held it beside the boat. The water would not cover the little keel.',
                          'Only the tip came back wet. Cy held it against the hull. "You would sit on the mud." The pool was too shallow.'))
    add("measurement", detour + 'At the pool, Cy lowered the measuring stick into the water. ' + measurement,
        events=("measure",), kind="how",
        question="How did Cy check whether the pool was deep enough?",
        answer="Cy used the measuring stick at the pool. The check showed that the water was " +
            ("deep enough" if deep else "too shallow") + " for the wooden boat.", needs=(acquired,))

    if "launch" in by_action:
        add("ending", choose(
            f'There was still time. {quote("launch", tag=True)} Cy said, and put the boat on the harbor pool. After all the carrying, the red sail finally belonged over water.',
            f'The launch time had not passed. Cy set the wooden boat on the pool. {quote("launch")} For once, the boat was doing its own part of the journey.',
            f'Cy lowered the boat onto the pool before launch time ended. {quote("launch")} The measuring stick stayed in Cy\'s hand; the red sail was on the water.'),
            events=("launch",), premises=("schedule", "boat_design"), kind="result",
            question="Did Cy get the harbor voyage that was planned?",
            answer="Yes. Cy checked the depth and put the boat on the harbor pool before launch time ended.", needs=("opening", "measurement"))
    else:
        obstacle = ("The pool was deep enough, but the time on the harbor timetable had passed. "
                    '"We missed it," Cy said. The boat stayed in Cy\'s hand all the way back to the workshop.' if deep else
                    'Cy held the boat over the pool, then drew it back. "Not on the mud. You are a boat, not a sled." '
                    'The stick had spoiled the plan, but it had saved the boat. Cy carried it back to the workshop.')
        add("late", obstacle,
            events=("measure",), premises=("schedule",), kind="why",
            question="Why didn't Cy launch the boat in the harbor even after finding the stick?",
            answer=("The depth was sufficient, but the permitted launch time had already ended." if deep else
                    "The measuring stick showed that the pool was too shallow for the boat.") +
                    " Cy brought the boat back to the workshop instead.", needs=("opening", "measurement"))
        basin = "basin" if deep else "basin_shallow"
        postpone = "postpone" if deep else "postpone_shallow"
        if basin in by_action:
            add("ending", choose(
                f'The washbasin was available, full of clean water. {quote(basin, tag=True)} Cy said. The wooden boat went onto the basin water. This little harbor had room for one red sail.',
                f'Back at the workshop, the washbasin offered a much smaller voyage. Cy put the boat on its clean water. {quote(basin)} The red sail was finally over water, just not the water Cy had planned.'),
                events=(basin,), premises=("basin_water", "boat_design"), kind="result",
                question="How did Cy change the plan when the harbor voyage could not happen?",
                answer="Cy put the boat on the clean water in the workshop washbasin. It was a smaller trial instead of the planned harbor voyage.", needs=("late",))
        else:
            add("ending", choose(
                f'The washbasin was closed, too. {quote(postpone, tag=True)} Cy said. Cy put the boat on the dry shelf, red sail still ready. The voyage could wait; the boat would wait somewhere dry.',
                f'The washbasin was closed. Cy set the boat on the dry shelf instead. {quote(postpone)} The sail was still red and the hull was still dry. Cy kept the measuring stick in hand for the next try.'),
                events=(postpone,), premises=("boat_design",), kind="result",
                question="What happened to the boat when neither launch option was available?",
                answer="Cy put it on the dry shelf at the workshop. Cy did not launch it during this attempt.", needs=("late",))
    if not measure_tick <= config.last_launch and "launch" in by_action:
        raise ValueError("Late harbor launch cannot receive a success ending")
    doc = Document(title=spec.title, statements=tuple(rows))
    known = {r.id for r in rows}
    if any(set(r.needs) - known for r in rows):
        raise ValueError("Narrative dependency was omitted")
    return doc


def render_errand(spec, state, config, seed):
    """Select whole scenes from enacted work, consent and custody changes."""
    rng = random.Random(seed)
    events = {e.action.id: e for e in state.events}
    rows = []

    def add(id, text, question, answer, *, actions=(), premises=(), needs=()):
        rows.append(Statement(id=id, text=text, kind=id, focus="cy", question=question, answer=answer,
            event_ids=tuple(events[a].id for a in actions) + tuple("initial/" + p for p in premises),
            entity_ids=("cy",), needs=needs))

    def pick(*texts):
        return rng.choice(texts)

    if config.purpose == "carry":
        helped = "bo_rope" in events
        complete = state.get("parents", "rope").parent == "jetty"
        add("purpose", pick(
            'Cy had meant to spend the morning with the little boat. Instead, Bo\'s tool case stood waiting at the workshop. The tools and rope were needed at the jetty before the ferry bell. "One quick job," Cy said.',
            'There was a tool case between Cy and a morning of sailing. Bo needed its tools and rope at the jetty before the ferry bell. Cy looked from the case to the little boat. "We can help first."'),
            "What did Cy decide to do before playing with the boat?",
            "Cy decided to bring Bo's tools and rope to the jetty before the ferry bell.", premises=("goal", "schedule"))
        add("weight", pick('The rope and tools made the case too heavy for Cy to lift together. '
            'Cy took both hands off the handle. "Perhaps not such a quick job."',
            'Cy gripped the handle. The case, with all the tools and rope inside, was more than Cy could carry. "I can carry a boat," Cy told it. The case did not seem impressed.',
            'It was easy to promise to carry a case. Carrying this one was harder. The tools and the heavy rope were too much together, and Cy had to let go of the handle.'),
            "Why couldn't Cy simply carry the whole case?",
            "The case with both the tools and rope exceeded what Cy could carry. The load had to be divided.", premises=("load",), needs=("purpose",))
        if helped:
            add("split", pick(
                'Bo was still at the workshop. "Could you carry the rope?" Cy asked. "I thought you were taking the case." "I am. But it does not all have to stay inside." Bo lifted out the coil. Cy lifted the lighter case.',
                '"That handle needs four hands," Cy said. Bo looked into the case. "Or two journeys." "Or two loads." Bo took out the rope. With only the tools left inside, Cy could lift the case.'),
                "How did Cy and Bo solve the carrying problem?",
                "Bo took the rope out and carried it separately. Cy could then lift the case containing only the tools.",
                actions=("bo_rope", "lift_case"), premises=("crew",), needs=("weight",))
        else:
            add("split", pick('Bo was already at the jetty. Cy took the rope out and set it on the workshop floor. '
                'The case was lighter now. "You first," Cy told the tools, and lifted it.',
                'There was no Bo to ask; Bo was waiting at the jetty. Cy looked inside the case, lifted out the rope and put it on the floor. Without it, the tools could travel. Cy picked up the case.'),
                "What did Cy leave behind on the first trip, and why?",
                "Cy left the rope at the workshop so the case would be light enough to carry with the tools inside.",
                actions=("cy_rope", "leave_rope", "lift_case"), premises=("crew",), needs=("weight",))
        travel = tuple(a for a in events if a.startswith("cy_") and a.endswith("_jetty"))
        add("journey", ('The direct path was closed. Cy had to go around by the quay, with the case in one hand and the little boat in the other. '
                'This was becoming a long way to earn a short sail.' if not config.direct_path else
                'Cy carried the lighter case along the short path to the jetty. The little boat came too, still waiting for its own turn.'),
                "Which route did Cy use to bring the case to the jetty?",
                "Cy went around by the quay because the direct path was closed." if not config.direct_path else
                "Cy took the short path to the jetty.", actions=travel, needs=("split",))
        if helped:
            add("delivery", pick('Bo set down the rope at the jetty. Cy put the case beside it. '
                '"There," said Bo. "The whole load." "Just not in one hand," said Cy.',
                'At the jetty, the rope and the case met again. Bo had carried one; Cy had carried the other. "Was it lighter?" Bo asked. Cy set the case down. "Only half as impossible."'),
                "Did both parts of the load reach the jetty?",
                "Yes. Bo delivered the rope, and Cy delivered the case with the tools inside.",
                actions=("bo_deliver_rope", "deliver_case"), needs=("journey",))
        elif complete:
            add("delivery", pick('Cy set down the case and checked the time. There was room for another trip. '
                'Back to the workshop, up with the rope, back to the jetty. "Two journeys," Cy told Bo. "One delivery." The coil went down beside the case.',
                'Cy left the tools at the jetty. There was still enough time to go back for the rope, so back Cy went. The rope made the second journey alone. When Cy put it beside the case, Bo had everything.'),
                "How did Cy finish the delivery without help carrying?",
                "Cy left the case at the jetty, returned to collect the rope, and brought it on a second trip before the deadline.",
                actions=("deliver_case", "collect_rope", "cy_deliver_rope"), needs=("journey",))
        else:
            add("delivery", 'Cy set the case down at the jetty and checked the time. Another trip would run past the ferry bell. '
                '"The tools are here," Cy told Bo. "The rope is still at the workshop. I could not carry both." Bo looked into the case. "Then we can start with the tools."',
                "Why did only part of the load arrive before the deadline?",
                "Cy could not carry the whole load at once, and the longer route left insufficient time for a second trip. The rope stayed at the workshop.",
                actions=("deliver_case",), premises=("schedule",), needs=("journey",))
        if complete:
            add("reveal", pick('"Now we can open it," Bo said. Beside the jetty stood a launch tub, already filled and checked for little boats. Its heavy cover needed the rope and tools. Bo used them to lift the cover. Cy stared at the water. "That was what the delivery was for?"',
                'Bo took the rope and tools to the covered launch tub beside the jetty. The water inside had already been checked for toy boats; the heavy cover was the last problem. With the delivered things, Bo lifted it. "I thought this was work before sailing," Cy said. "It was work for sailing," Bo replied.'),
                "Why did Bo need both the rope and tools?",
                "They were needed to lift the heavy cover off the prepared launch tub. Once both arrived, Bo opened it for the little boat.",
                actions=("open_tub",), premises=("tub",), needs=("delivery",))
        add("finish", (pick('Cy lowered the boat onto the tub water. It no longer weighed anything in Cy\'s hands. "There," Bo said. "Your turn to carry nothing." Cy watched the little hull float.',
                'The boat went onto the water in the tub. Cy let go, slowly. The case, the rope and the two tired hands stayed on dry land. Only the little boat had somewhere else to go.',
                'Cy put the boat on the tub water. "She has had a long way to come," Cy said. "Not as long as you," said Bo. For the first time that morning, Cy watched the boat without holding it.') if complete else
                'Cy looked into the open case, then set the little boat among the tools. "A repair dock," Cy said. '
                'Bo smiled. "Does she need repairs?" "Not yet. But this is where she can wait." The boat fitted neatly beside the tools that had made it such a long morning.'),
                "What happened to the little boat at the end?",
                "Cy put the boat on the water in the prepared launch tub after Bo opened its cover." if complete else
                "Cy put the boat in the tool case and pretended it was a repair dock. The rope remained at the workshop.",
                actions=(("sail_tub",) if complete else ("dry_dock",)),
                needs=(("reveal",) if complete else ("delivery",)))
    elif config.purpose == "lend":
        declined = "decline" in events
        late = state.tick > config.last_launch
        add("purpose", pick(
            '"Could your boat be in my window display?" Ari asked at the workshop. Cy held the little wooden boat closer. It was meant to have a voyage before the ferry bell. "Only if I get it back in time."',
            'Ari wanted a boat for the display in the quay window. Cy had a boat, but also a plan to take it sailing before the ferry bell. "It would look lovely on the shelf," Ari said. "It would look lovely on the water," said Cy.'),
            "What competing plans did Ari and Cy have for the boat?",
            "Ari wanted it for a window display at the quay. Cy wanted it back for a voyage before the ferry bell.", premises=("goal", "schedule"))
        add("terms", pick('Cy offered to lend the boat, not give it away. "Back into my hands afterward," Cy said. '
            'Ari listened. The display could borrow a boat; it could not keep one.',
            '"It is still mine," Cy said, offering the loan. "Bring it back to me yourself." Ari listened carefully. Borrowing the little boat meant making a return journey too.',
            'Cy held the boat between them. "You may borrow her. Then she comes back into my hands." "Not a gift," Ari said. "Not even a very small gift," said Cy.'),
            "Did Cy offer to give Ari the boat permanently?",
            "No. Cy offered a loan and asked for the boat to be returned directly to Cy afterward.", actions=("offer", "read_terms"), needs=("purpose",))
        if declined:
            add("decision", 'Ari counted the time for the display and the walk back. "I cannot finish before your sailing time," Ari said. "I had better not borrow it." Cy loosened the tight hold on the hull.',
                "Why did Ari turn down the loan?",
                "The planned display and return trip would take too long for Cy's sailing plan. Ari declined before collecting the boat.", actions=("decline",), needs=("terms",))
            add("custody", 'No boat changed hands. Ari looked once more at its little hull, but left it with Cy. "Thank you for offering," Ari said.',
                "Who kept the boat when the loan was declined?",
                "Cy kept the boat. Ari never collected it, so no active loan began.", actions=("decline",), needs=("decision",))
            add("consequence", '"Your window will be empty," Cy said. "Only of this boat," said Ari. Ari picked up the harbor chart from the workshop. '
                '"This one has room for every boat." Ari carried the chart to the quay and put it on the window shelf.',
                "What did Ari display instead of borrowing Cy's boat?",
                "Ari carried the harbor chart from the workshop to the quay and put it on the display shelf. Cy kept the boat.",
                actions=("pick_chart", "display_chart"), premises=("chart",), needs=("custody",))
            add("finish", 'In the quay window lay the whole harbor on a sheet of paper. Back at the workshop, one small wooden boat was still in Cy\'s hands. '
                'Ari had found room for the harbor without taking away Cy\'s voyage.',
                "Where did the boat and the chart end this exchange?",
                "The boat remained in Cy's hands at the workshop. Ari's harbor chart was on the display shelf at the quay.", actions=("decline", "display_chart"), needs=("consequence",))
        else:
            add("decision", pick('"All right," said Ari. Cy let the boat pass into Ari\'s waiting hands. '
                '"Mind the little hull." "I will." Ari carried it to the quay and set it on the window shelf.',
                'Ari agreed and held out two hands. Cy passed over the boat. It went with Ari to the quay and took its place on the window shelf, a little vessel with a view of the harbor but no water under it.',
                '"I understand," Ari said. Cy handed over the boat. Ari carried it to the quay, set it on the window shelf and stepped back. "There. My display has a boat."'),
                "How did the boat reach the window display?",
                "Ari accepted the loan, collected the boat from Cy, carried it to the quay, and put it on the display shelf.",
                actions=("accept", "collect", "exhibit"), needs=("terms",))
            add("retrieval", pick('When the display time was over, Ari lifted the boat off the shelf. '
                '"Time to be a boat again," Ari said, and carried it back to the workshop.',
                'At the end of the display, Ari picked the boat up again. The shelf looked bare without it. "You are wanted somewhere else," Ari said. Back to the workshop went the boat.',
                'The display could not last all day. Ari took the boat from the window shelf and carried it back to the workshop. It was still Cy\'s boat, even after being the best part of Ari\'s window.'),
                "Did leaving the boat on display end the loan?",
                "No. Ari took the boat off the shelf and started carrying it back. It still had to reach Cy's hands.",
                actions=("retrieve", "ari_quay_workshop"), needs=("decision",))
            if config.moved:
                add("search", pick('But Cy had gone to the jetty. Ari found an empty place at the workshop and had to carry the boat farther. '
                    'At the jetty, Cy looked up. "I was waiting here." "I was looking there," Ari said.',
                    'Cy was not at the workshop. Cy had gone to the jetty. Ari had to take the boat there instead. "You moved," Ari said when they met. Cy glanced at the boat. "So did she."',
                    'There was nobody to receive the boat at the workshop. Cy had gone to wait at the jetty. Ari carried it on. "Next time," Ari said on finding Cy, "we need a meeting place as well as a boat."'),
                    "What complicated the return after the display?",
                    "Cy had moved from the workshop to the jetty. Ari first went to the workshop, then continued to the jetty to find Cy.",
                    actions=("ari_quay_workshop", "cy_workshop_jetty" if config.direct_path else "cy_quay_jetty", "ari_workshop_jetty" if config.direct_path else "ari_quay_jetty"),
                    needs=("retrieval",))
            add("return", pick('Ari offered the boat back. Cy held out both hands and accepted it. '
                '"There you are," Cy said to the little hull. "Your first voyage was into a window."',
                '"Home again," Ari said, holding out the boat. Cy took it in both hands. The return was a small thing to watch: one pair of hands becoming empty, another becoming full.',
                'Ari waited until Cy was ready, then passed the boat back. "She was the finest boat in the window," Ari said. "The only boat?" "That too." Cy held the little hull again.'),
                "When was the loan actually settled?",
                "It was settled when Ari handed the boat back into Cy's ready hands. Merely leaving the display had not returned it.",
                actions=("offer_back", "accept_back", "return"), needs=(("search",) if config.moved else ("retrieval",)))
            add("finish", ('The time for launching had passed. Cy held the boat without putting it down. "Next time we choose where to meet," Cy said. '
                    'Ari nodded. The little hull was safely home, though its water voyage would have to wait.' if late else
                    'There was still time before the ferry bell. Cy turned the boat toward the water. "Window first, harbor next." '
                    'Ari smiled at the empty hands that had brought it back.'),
                    "Did the return leave time for Cy's planned voyage?",
                    "No. Ari returned the boat safely, but the launch time had passed." if late else
                    "Yes. The boat was back with Cy while there was still time before the ferry bell. This story ends before the voyage itself.",
                    actions=("return",), premises=("schedule",), needs=("return",))
    else:
        wrong = "fix_lamp_tag" in events
        wrong_trip = "put_back_blue" in events
        add("purpose", pick(
            'Bo needed the lantern at the jetty. At the workshop, Cy checked the packing list: lantern in the blue box, cleaning cloth in the red one. "Blue, then," Cy said. It looked like the easiest errand of the morning.',
            'Two parcel boxes waited in the workshop. The list said the blue one held Bo\'s lantern and the red one held a cleaning cloth. Bo was at the jetty, waiting for a light, so Cy reached for the blue box.'),
            "Which box did the packing list say contained Bo's lantern?",
            "The list assigned the lantern to the blue box and the cleaning cloth to the red box. Cy wanted to bring Bo the lantern.", premises=("goal", "packing_list", "crew"))
        add("inspection", ('Cy carried the blue box all the way to the jetty. "Your lantern," Cy announced. '
                '"Shall we look?" Bo asked. Cy opened it.' if not config.cautious else
                'Cy stopped with one hand on the blue box. "Better look before I carry it." The lid came open at the workshop.'),
                "Where did Cy first inspect the blue box?",
                "Cy carried it to the jetty before opening it." if not config.cautious else
                "Cy opened it at the workshop before setting off.", actions=("open_blue", "inspect_blue"), needs=("purpose",))
        if wrong:
            add("mistake", pick('Inside was a folded cloth, beside a slip marked LANTERN. "A very soft lantern," Cy said. '
                'It had no handle, no glass, and no light. The slip was not going to help it shine.',
                'Cy unfolded a cleaning cloth. The packing slip beside it said LANTERN. Cy turned the cloth over. "No. Not even on this side." The name was right for the errand; the thing was wrong.',
                'A cloth lay where the lantern ought to be. Beside it was a slip with the word LANTERN. Cy stared at both. "You will clean a window," Cy told the cloth. "You will not light one."'),
                "What was wrong with the blue box?",
                "It contained the cleaning cloth, although the packing list and its slip called it the lantern parcel.",
                actions=("inspect_blue",), premises=("packing_list",), needs=("inspection",))
            add("other_box", ('"I brought the words," Cy told Bo. "I will go back for the light." Cy carried the blue box back to the workshop and set it down. '
                    if wrong_trip else 'Cy left the blue box at the workshop and opened the red one instead. ') +
                ('Cy opened the red box. ' if wrong_trip else '') +
                'There was the lantern, beside a slip marked CLOTH. "You two have traded names," Cy said.',
                "Where did Cy find the actual lantern?",
                "Cy inspected the red box at the workshop and found the lantern there, beside the cloth slip.",
                actions=tuple(a for a in ("put_back_blue", "open_red", "inspect_red") if a in events), needs=("mistake",))
            add("correction", pick('Cy moved the lantern slip into the red box and the cloth slip into the blue one. '
                'Then Cy took the red box to the jetty. This time the thing inside, not the old list, had chosen the parcel.',
                'The slips were easy to carry. Cy moved LANTERN to the red box and CLOTH to the blue one, then carried the red parcel to the jetty. The packing list had started the errand. Looking inside had finished choosing the box.'),
                "How did Cy correct the packing mistake?",
                "Cy exchanged the two slips so each matched its box's contents, then carried the red box containing the lantern to Bo.",
                actions=("fix_lamp_tag", "fix_cloth_tag", "pick_red"), needs=("other_box",))
        else:
            add("contents", 'The lantern was inside, just as the list said. Cy lifted the corner of the packing slip to check the handle beneath it. '
                '"A real lantern," Cy said. "Not just its name."',
                "Did the blue box's contents match the list?",
                "Yes. Cy inspected the blue box and found the actual lantern inside.", actions=("inspect_blue",), needs=("inspection",))
            add("journey", ('Cy carried the checked parcel from the workshop to the jetty. ' if config.cautious else
                            'Cy kept the open parcel ready at the jetty. ') +
                'Bo held out both hands. "That is the one I need."',
                "How did Cy know the parcel was right before handing it over?",
                "Cy had opened the box and inspected the lantern itself before handing the parcel to Bo.",
                actions=("inspect_blue", "ready_parcel"), needs=("contents",))
        color = "red" if wrong else "blue"
        add("handover", f'Cy put the {color} box into Bo\'s hands. "One lantern," Cy said. '
                'Bo looked at the handle in the box. "And no need to make a cloth shine."' if wrong else
                f'Cy put the {color} box into Bo\'s hands. "One lantern," Cy said. "Checked before delivery." Bo smiled down at its handle.',
                "What did Bo actually receive?",
                f"Bo received the {color} box containing the lantern. The cleaning cloth was at the workshop at the end.",
                actions=("give_parcel",), needs=(("correction",) if wrong else ("journey",)))
        add("shutter", ('But the lantern was dark behind its closed shutter. "Now I have brought a light that will not shine," Cy said. '
                'Bo slid the shutter open. The battery bulb was glowing inside. "It was shining," Bo said. "We just had not let the light out."' if not wrong else
                'Bo slid open the lantern shutter. Inside, the battery bulb was already glowing. Light fell across the packing slips. "There," Cy said. "That is what I meant to bring."'),
                "Why did light become visible when Bo opened the lantern?",
                "The battery bulb was already glowing behind the closed shutter. Bo opened the shutter and could see the light inside.",
                actions=("open_shutter", "see_light"), needs=("handover",))
        add("finish", pick('Bo held the open parcel at the jetty. Light from the lantern lay across Bo\'s hands. Cy no longer had to explain which box was right.',
                'The lantern glowed in its box at the jetty. Its little pool of light reached farther than the packing slip. Cy stood beside Bo and watched it.'),
                "Where was the lantern at the end, and was its light visible?",
                f"It was inside the {color} box in Bo's hands at the jetty. Its shutter was open and its glowing bulb was visible.",
                actions=("give_parcel", "open_shutter", "see_light"), needs=("shutter",))
    return Document(title=spec.title, statements=tuple(rows))
