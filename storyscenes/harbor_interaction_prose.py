"""Realize coupled plans through the actions that enable and obstruct them."""
import random

from .capabilities.reading import Document, Statement


def render_shared_rope(spec, state, config, seed):
    rng = random.Random(seed)
    events = {e.action.id: e for e in state.events}
    facts = {f.id for f in spec.records["facts"]}
    refused = "decline_rope" in events
    clipped, moved, relaxed = (action in events for action in ("clip_chart", "board_chart", "release_deadline"))
    interrupted = not refused and events["unhang_chart"].tick < events["hang_chart"].tick + config.display_ticks
    sailed = "sail_tub" in events
    rows = []

    def add(id, text, question, answer, *, actions=(), premises=(), needs=()):
        if not set(premises) <= facts:
            raise ValueError("Missing shared-rope premise")
        rows.append(Statement(id=id, text=text, focus="cy", kind=id, question=question, answer=answer,
            event_ids=tuple(events[a].id for a in actions) + tuple(f"initial/{p}" for p in premises),
            entity_ids=("cy", "ari", "bo"), needs=needs))

    add("plans", rng.choice((
        'Ari had a harbor chart to hang in the quay window. Cy had a little boat to sail. Between the two plans lay Bo\'s coil of rope. '
        'Ari needed it for the chart; Bo needed it, with the tools, to lift the heavy cover off the launch tub before the ferry bell.',
        '"One rope," Bo said. "Two uses." Ari looked toward the quay window, where the harbor chart was meant to hang. '
        'Cy looked at the little boat. The same rope and a bundle of tools had to reach the jetty to open its covered launch tub before the ferry bell.')),
        "Why did two plans depend on the same rope?",
        "Ari needed it to hang the chart, while Bo needed it with the tools to open the launch tub for Cy's boat before the ferry bell.",
        premises=("goal", "ari_goal", "bo_goal", "tub", "schedule"))
    add("offer", 'Bo offered to lend Ari the rope. "It has another job afterward," Bo said. Ari listened to where it had to come back. '
        'The rope would still belong to Bo, even while it held up Ari\'s picture of the harbor.',
        "Who owned the rope Bo offered to lend?",
        "Bo owned the rope. Offering to lend it did not make Ari its owner.",
        actions=("offer_rope", "read_rope_terms"), needs=("plans",))
    if refused:
        add("choice", 'Ari counted the display time and the trip to the jetty. "I cannot keep it that long and bring it back in time. '
            'I had better leave it with you." Bo did not have to pull the rope away. Ari had already stopped reaching for it.',
            "Why did Ari decline the rope loan?",
            "The planned display and return trip would take too long. Ari declined rather than hold up the launch.",
            actions=("decline_rope",), needs=("offer",))
        add("display", 'Ari carried the chart to the quay and laid it flat on the window shelf instead of hanging it. '
            '"You will have to look down at this harbor," Ari told the chart. It was not the display Ari had planned, but the rope was free.',
            "How did Ari arrange the chart without borrowing the rope?",
            "Ari carried it to the quay and laid it flat on the window shelf.",
            actions=("take_chart", "ari_workshop_quay", "lay_chart"), needs=("choice",))
    else:
        add("choice", 'Ari accepted the rope and promised Bo to return it by the ferry bell. "At the jetty," Bo said. '
            '"Into your hands," Ari answered. Cy looked at the little boat. A promise could hold a plan together, but it could not lift a cover.',
            "What did Ari promise after borrowing the rope?",
            "Ari promised to return Bo's rope by the ferry bell. They agreed that Bo would receive it at the jetty.",
            actions=("accept_rope", "borrow_rope", "promise_rope"), needs=("offer",))
        add("display", 'Ari carried the rope and chart to the quay. The rope went up at the window; the chart hung from it. '
            'For a little while, the whole harbor lay flat against the glass instead of flat on a shelf.',
            "What did Ari use the borrowed rope for?",
            "Ari hung the harbor chart from it in the quay window.",
            actions=("take_chart", "ari_workshop_quay", "hang_rope", "hang_chart"), needs=("choice",))
    add("load", ('Bo took the rope out of the tool case. ' if refused else
                 'With the rope away at the window, there were only tools left in the case. ') +
        'Cy could lift it now. "That helped," Cy said. "We still need the rope at the other end," Bo said. '
        + ('They took the short path to the jetty together.' if config.direct_path else
           'The short path was closed, so they carried the load around by the quay.') +
        ' Cy set the case beside the covered tub.',
        "How did removing the rope help Cy without finishing the whole job?",
        "It made the tool case light enough for Cy to carry to the jetty. The rope was still needed there to lift the tub's cover.",
        actions=tuple(a for a in ("bo_rope", "lift_case", "deliver_case") if a in events), needs=("display",))
    if not refused:
        if relaxed:
            add("new_plan", 'Bo and Cy walked to the quay. "There is water in the workshop basin," Cy said. '
                '"I could sail there while the chart stays up." Bo looked at Ari. "Then I can wait for my rope. '
                'You do not have to bring it before the bell." "It is still coming back," Ari said. "I know," Bo answered.',
                "Did Ari simply ignore the promised return time?",
                "No. Bo released the before-bell deadline while there was still time. The rope remained a loan and still had to come back.",
                actions=("bo_jetty_quay", "cy_jetty_quay", "release_deadline"), premises=("basin_water",), needs=("load",))
            add("basin", 'Cy carried the boat from the quay to the workshop and lowered it onto the clean basin water. '
                '"You do not know the name of your water, do you?" The small hull floated just the same. Bo went back to the jetty to wait for the rope.',
                "What did Cy do instead of waiting for the launch tub?",
                "Cy carried the boat to the workshop and put it on the basin water. Bo returned to the jetty to receive the rope.",
                actions=("cy_quay_workshop", "sail_basin", "bo_quay_jetty"), needs=("new_plan",))
        if clipped:
            add("turn", 'Ari drew a spring clip from a pocket and held it beside the thick rope. "All that rope for one sheet of paper." '
                'The clip went onto the window shelf. Ari lifted the chart off the rope and fastened it in the clip. '
                'The paper stayed up. The coil was free. "I borrowed the biggest answer," Ari said, collecting it.',
                "How could the chart stay hanging while Ari returned the rope?",
                "Ari mounted a spring clip at the window and fastened the chart in it. The clip supported the paper, freeing the rope for Bo.",
                actions=("mount_clip", "unhang_chart", "clip_chart", "retrieve_rope"),
                premises=("clip_support",), needs=("load",))
        elif moved:
            add("turn", 'The window was not the only place to hang a chart: there was a mounting board at the jetty. '
                'Ari took down the chart but did not put it on the shelf. "You can come with the rope." '
                'It would not be a window display anymore. It could still be a display.',
                "Why did Ari take the chart along instead of waiting at the window?",
                "The mounting board at the jetty could hold it. Moving the display would let Ari bring the rope to Bo in time.",
                actions=("unhang_chart", "retrieve_rope"), premises=("board_support",), needs=("load",))
        elif interrupted:
            add("turn", 'At the quay, Ari looked from the hanging chart toward the jetty. The display was supposed to stay up longer. '
                '"I promised to bring the rope back." Ari took the chart down early and laid it on the shelf. The picture of the harbor no longer needed the rope; the real little boat still did.',
                "What did Ari give up to return the rope in time?",
                "Ari shortened the hanging display, taking the chart down before its planned interval ended.",
                actions=("unhang_chart", "lay_chart"), needs=("load",))
        else:
            add("turn", ('Ari let the planned display finish. The chart stayed hanging until its time was up. Then Ari took it down and laid it on the shelf. '
                'At last the rope was free again.' if sailed or relaxed else
                'Ari saw that the return time was getting close, but left the chart hanging for its full planned display. '
                '"Only a little longer," Ari said. By the time the chart came down onto the shelf, little longer had become too long.'),
                "Did Ari finish the planned hanging display or shorten it?",
                "Ari let the full display interval finish before taking the chart down.",
                actions=("unhang_chart", "lay_chart"), needs=("basin",) if relaxed else ("load",))
        add("return", ('Ari carried the chart and rope to the jetty. The chart fitted into the board\'s clamps. '
            '"A better view of the thing itself," Ari said. ' if moved else
            'Ari carried the freed rope from the window to the jetty. ') +
            f'Bo held out both hands and accepted {"the rope" if moved else "it"}. ' +
            ('"No cover to lift today," Bo said, putting the coil beside the tools. "But still my rope." "Still your rope," Ari agreed.' if relaxed else
             'Bo put the coil beside the tools. "You brought the whole harbor," Cy said to Ari. "Only the paper part," Ari answered.' if moved else
             'Bo put the coil beside the tools. "It is back," Ari said. Cy looked at the covered tub.' if not sailed else
             '"It held the whole harbor," Ari said. "Now it has to help one boat," Bo answered. Bo put the coil beside the tools.'),
            "Was the rope actually returned, rather than merely promised back?",
            "Yes. Ari carried it to the jetty, returned it into Bo's hands, and Bo put it beside the tools.",
            actions=("retrieve_rope", "ari_quay_jetty", "return_rope", "bo_deliver_rope") + (("board_chart",) if moved else ()), needs=("turn",))
    if relaxed:
        add("ending", 'The launch tub stayed covered at the jetty. In the workshop, the little boat floated in the basin. '
            'Ari had finished the full window display and Bo had the rope back. Cy watched the hull make its small voyage. '
            'The plan had changed; the boat had not needed to.',
            "Did changing the launch plan leave the boat dry or the rope unreturned?",
            "No. Cy's boat floated in the workshop basin, and Ari returned the rope to Bo at the jetty. The tub stayed closed.",
            actions=("sail_basin", "return_rope", "release_deadline"), needs=("return",))
    elif sailed:
        add("ending", ('The rope and tools reached the tub before the ferry bell. Bo lifted the heavy cover with them. '
            'Cy set the boat on the water and finally let go. ' +
            ('The chart stayed up in its small clip for the rest of the display. One sheet of paper had stopped holding up a whole voyage.' if clipped else
             'The chart hung on the jetty board for the rest of its display. Beside the drawn harbor, Cy\'s boat had real water underneath it.' if moved else
             'The chart had lost its rope early, but the little boat had gained a harbor.' if interrupted else
             'Ari\'s chart lay flat on the window shelf; Cy\'s boat no longer lay in anyone\'s hand.' if refused else
             'The rope had held up a picture of the harbor and helped make a real small voyage. Neither job had kept it forever.')),
            "What became possible once the rope and tools were together in time?",
            "Bo opened the launch tub with them, and Cy put the boat onto the water before the ferry bell.",
            actions=("open_tub", "sail_tub"), needs=("load",) if refused else ("return",))
    else:
        add("ending", 'The ferry bell\'s launch time had passed. The rope was back, but the covered tub had to stay shut. '
            'Cy put the boat in the open tool case as a dry dock. "You brought back the rope," Cy said. Ari looked at the small, dry hull. '
            '"I did not bring back the time."',
            "Why could Cy not sail even though Ari returned the rope?",
            "The rope arrived after the launch deadline. The tub stayed closed, so Cy put the boat in the tool case instead of on the water.",
            actions=("dry_dock",), needs=("return",))
    if not refused and not relaxed:
        fulfilled = state.get("promises", "rope_return").status == "fulfilled"
        # The ending paragraph carries the retrospective QA without adding an
        # administrative sentence to the story itself.
        last = rows[-1]
        from dataclasses import replace
        rows[-1] = replace(last, event_ids=last.event_ids + (events["assess_rope_promise"].id,),
            answer=last.answer + (" Ari kept the return promise." if fulfilled else
                                 " Returning the rope late did not undo the missed launch."))
    return Document(title=spec.title, statements=tuple(rows))
