"""Scene-sized realizations of failed attempts, completed work and repairs."""
from .capabilities.reading import Document, Statement
from .harbor_questions_story import understood_value
from .harbor_recovery import add_second_look, divided_scene


def render(spec, state):
    job = state.get("harbor_jobs", "ari")
    trial = state.get("harbor_trials", "first")
    outcome = state.get("harbor_resolutions", "end").outcome
    events = {e.action.id: e.id for e in state.events}
    rows = []
    def add(id, text, question, answer, *actions):
        rows.append(Statement(id=id, text=text, question=question, answer=answer, kind=id, focus="ari",
            event_ids=tuple(events[a] for a in actions), entity_ids=("ari", "cy", "crate"),
            needs=(rows[-1].id,) if rows else ()))

    opening, goal = {
        "load": ('Ari thought the crate held stone slabs and wanted it on the handcart. "I can manage," Ari said, before anyone had suggested otherwise. The crate waited on the workshop floor. It had not agreed to anything.',
                 "Ari wanted to load what was believed to be a crate of stone slabs onto the handcart. Ari chose to try the lift before asking for help."),
        "parcel": ('The picnic boat needed cups. Ari had a box that was supposed to hold them, and a very short plan: put the box on the boat. Looking inside was not yet part of it.',
                   "Ari wanted cups aboard the picnic boat. Ari acted on the belief that the box held them, before checking its contents."),
        "shortcut": ('Ari had a parcel for the jetty. The footbridge was the short way, and a short way seemed like a promise that the work would be over sooner. Ari took the parcel, not a helper.',
                     "Ari wanted to deliver a parcel to the jetty by the footbridge. Ari tried the route personally before asking Cy to help."),
        "tool": ('The paper flags were still inside a tied parcel. Ari meant to open it without scissors. "There ought to be a way," Ari said, as though the fastening might be persuaded by being told what ought to happen.',
                 "Ari wanted to open the parcel of paper flags by pulling its fastening. No scissors had been requested or used."),
    }[job.kind]
    add("opening", opening, "What was Ari trying to do?", goal, "first_try")
    if job.prior_commitment:
        add("commitment", 'Cy had an earlier arrangement: bring Bo the brass key at the jetty by the bell. Bo had already gone there. The key was still with Cy, and so was the promise.',
            "What earlier arrangement did Cy have?",
            "Cy had promised to bring Bo the brass key at the jetty by the bell. Bo was already there while Cy still held the key.",
            "prior_promise", "bo_lane", "bo_round")

    attempt_text, attempt_answer, actions = {
        ("load", "too_heavy"): ('Ari tried the lift. The crate stayed on the floor. "I can manage," Ari repeated, more quietly, and took both hands away from the handles.',
            "Ari tried to lift the crate but could not carry that load. The attempt did not move it onto the cart.", ("first_try",)),
        ("load", "liftable"): ('The crate came up in Ari\'s hands and went onto the cart. That had been surprisingly easy. Ari looked at the lid. A success could be suspicious too.',
            "Ari lifted the crate and put it on the handcart. This proved it was light enough to carry, not what was inside.", ("first_try", "early_take", "early_place")),
        ("parcel", "delivered_unchecked"): ('Ari put the box aboard. "Done." The lid was still shut. Ari looked at it again. The boat now had a box; whether it had cups was a different question.',
            "Ari put the unopened box on the picnic boat. The physical delivery happened before its contents were checked.", ("early_take", "early_place", "first_try")),
        ("shortcut", "passable"): ('Ari crossed the footbridge with the parcel and set it down at the jetty. "Here," Ari told the parcel, rubbing the marks its handles had left. It had been a short walk, though long enough to make empty hands feel good.',
            "Ari crossed the open footbridge and put the parcel at the jetty. The delivery was performed without Cy carrying it.", ("first_try", "early_cross", "early_place")),
        ("shortcut", "blocked"): ('The barrier stopped Ari at the crossing. Carrying the parcel did not make it a pass. Ari put it back down at the workshop. "Still here," Ari said. The parcel had acquired a journey without acquiring an arrival.',
            "Ari encountered the closed crossing and could not travel over it. Ari put the parcel back at the workshop rather than pretending it had arrived.", ("first_try", "put_back")),
        ("tool", "gives_way"): ('Ari pulled, and the fastening gave way. The parcel opened. Ari put it on the bench with the paper flags still whole inside. "Oh," Ari said. It was a small word for an unexpectedly finished job.',
            "Ari opened the parcel by pulling the fastening and put it on the bench. The flags remained whole, and no scissors were used.", ("first_try", "early_open", "early_place")),
        ("tool", "resists"): ('Ari pulled. The fastening held. Ari stopped before pulling harder could become the whole plan. "There ought to be a way," Ari said again. This time it sounded more like a question.',
            "The fastening resisted Ari's attempt and the parcel remained closed. Ari stopped without cutting or opening it.", ("first_try",)),
    }[(job.kind, trial.result)]
    add("attempt", attempt_text, "What actually happened when Ari tried?", attempt_answer, *actions)

    if "inspect" in events:
        evidence = state.get("evidence", "seen")
        observer = "Cy" if evidence.observer == "cy" else "Ari"
        result = state.get("propositions", evidence.proposition).result
        value = result.value if result.kind == "exact" else None
        if value is None:
            inspection = f'{observer} tried to check more closely. ' + {
                "load": 'An inner wrapping hid the contents. The lift had given an answer about carrying, not about what the crate held.',
                "parcel": 'Opening the lid revealed another wrapping. Nothing in view established that the boat had received cups.',
                "shortcut": 'Fog still hid the far end of the bridge. The failed crossing was real, even though a complete view was not available.',
                "tool": 'A fold of wrapping hid the fastening. The failed pull did not show where it would be safe to cut.',
            }[job.kind]
            finding = {
                "load": "The wrapping hid the crate's contents. Trying to lift it did not establish whether it contained stone slabs.",
                "parcel": "Inner wrapping prevented the inspector from identifying the contents. Delivering the box had not established whether there were cups aboard.",
                "shortcut": "Fog prevented a complete view of the crossing. Ari's earlier encounter with the barrier had already stopped that delivery attempt.",
                "tool": "The wrapping hid the fastening from inspection. The failed pull did not show where to cut safely.",
            }[job.kind]
        else:
            detail = {("load", True): "stone slabs packed inside the crate", ("load", False): "an empty wooden bottom",
                      ("parcel", True): "paper cups nested inside the box", ("parcel", False): "paint tins instead of cups",
                      ("shortcut", False): "the closed footbridge barrier", ("tool", True): "a sealed band without a loose end"}[(job.kind, value)]
            inspection = f'{observer} checked and found {detail}. ' + {
                "load": 'The contents and the first attempt now belonged to the same explanation.',
                "parcel": 'The box had not changed its contents by being delivered. Only their understanding of the delivery had changed.',
                "shortcut": 'The parcel needed a different route, not a more determined walk at this one.',
                "tool": 'Fingers had tried their part. The band needed a different kind of help.',
            }[job.kind]
            finding = f"{observer} found {detail}. That supplied information beyond the earlier attempt."
        add("inspection", inspection, "What did the first inspection establish?"
            if state.get("evidence", "reseen") else "What did the later inspection establish?", finding, "inspect")
        if evidence.observer == "cy":
            add("report", 'Cy explained the result to Ari. Ari listened instead of repeating the first plan. "All right," Ari said. "Tell me what we actually have."',
                "How did Ari receive the first inspection result?" if state.get("evidence", "reseen") else "How did Ari receive that inspection result?",
                "Cy described the inspection result, and Ari heard and understood the report. Ari did not perform a second personal inspection.",
                "explain", "hear", "understand")

    add_second_look(add, state)

    request = state.get("requests", "help")
    if request is not None:
        words, answer = {
            "load": ('"Could you help me put it on the cart?" Ari asked Cy.\n"You have tried?"\n"Yes."\nThis request had a crate on the floor behind it, not just Ari\'s opinion of how easy lifting ought to be.',
                     "Ari asked Cy to load the heavy crate after failing to lift it. The request followed a physical attempt and a check of the contents."),
            "parcel": ('"Could you take that box off the boat and put it by the sign?" Ari asked.\n"Taking it off is part of the job now?" Cy said.\n"I made it part of the job." Ari looked at the paint box. "It is not cups."',
                       "Ari asked Cy to remove the paint box from the boat and put it at the workbench. This was a request to repair an earlier mistaken delivery."),
            "shortcut": ('"Do you know another way?" Ari asked Cy.\n"The lane past the sheds."\n"Will you take the parcel?"\nCy looked at it where Ari had put it down. "To the jetty. Not just toward it."',
                         "Ari asked Cy to deliver the parcel after the first crossing failed. Cy knew the lane past the sheds as an alternative route."),
            "tool": ('"May I use the scissors?" Ari asked.\nCy looked at the unopened parcel. "What changed?"\n"My plan," Ari said. "Not the band."',
                     "Ari asked for scissors after the pull failed and inspection found a sealed band. The new request changed the method rather than pretending the parcel had opened."),
        }[job.kind]
        add("request", words, "What help did Ari ask for after trying?", answer, "request", "acknowledge")
        if request.response == "declined":
            add("response", '"Not before I take Bo the key," Cy said. "I promised."\nAri looked at the unfinished work. It was tempting to make it sound more important. That would not make the earlier promise disappear.',
                "Why did Cy decline the immediate request?",
                "Cy chose to keep the earlier key-return promise first. The refusal did not mean Ari's task had been completed or was unimportant.", "refuse")
        else:
            text = 'Cy agreed to help. "This part, then," Cy said. Ari left room for the work instead of making another prediction.'
            if job.prior_commitment and job.kind in {"load", "parcel"}:
                text += ' The key would have to wait until afterward, though its promised time had not changed.'
            add("response", text, "Did Cy agree to the new request?",
                "Cy accepted the request. Acceptance was followed by actual performance; it was not counted as the finished job by itself.", "accept")

    results = {
        "self_delivered": ('Ari nearly called for Cy out of habit, then looked down at the parcel. There it was, in the right place. Ari left it alone.',
            "Ari's parcel was at the jetty after the actual crossing. No request to Cy was needed to complete that delivery.", "The parcel rested on the jetty, with Ari's hands empty beside it."),
        "opened_without_asking": ('The unused scissors were still with Cy. Ari had not needed to borrow them, or to give a long account of why they had been unnecessary. There were the flags on the bench. They made a shorter explanation.',
            "The parcel was open on the bench and the flags were intact. Cy kept the unused scissors because no handover was needed.", "The fastening no longer held anything shut; the paper flags were still whole."),
        "retracted_unverified": ('Ari took the box back from its supposed destination and set it on the workshop floor. "Not done," Ari said. It was less satisfying than the first announcement, but it fitted the box better.',
            "Ari removed the unverified cargo from its earlier destination and put it back in the workshop. Its hidden contents were still unknown.", "The open lid exposed wrapping, not a reason to announce success."),
        "stopped_after_attempt": ('"Leave it a moment," Ari said. Cy did. The object stayed in the workshop while Ari stood beside it, no longer pulling or trying to lift.',
            "The attempt did not complete the job, and the later inspection remained inconclusive. Ari left the object at the workshop rather than inventing a result.", "The unfinished object stayed in the workshop, unchanged by the fact that Ari now wanted an answer."),
        "delivery_confirmed_afterward": ('There were cups aboard after all. Ari left the box on the boat. "Done," Ari said again. It was the same word as before, but this time the open box could answer for it.',
            "Inspection confirmed that the delivered box held cups. Ari left the correctly delivered box aboard instead of moving it again.", "The cups sat nested in their open box, no longer traveling under a guess."),
        "empty_load_removed": ('Ari took the empty crate off the cart and put it on the workbench. The impressive lift had delivered no stones. "I can manage this," Ari said, and this time meant the useful empty box.',
            "Ari removed the empty crate from the cart and placed it on the workbench. The earlier easy lift was not treated as a successful delivery of stones.", "The cart's space was empty again; the empty crate had a more honest job on the bench."),
        "self_repaired_delivery": ('Ari took the paint box off the boat and carried it to the workbench. The second trip was as real as the first. "I can undo my part," Ari said. The box waited beside the unfinished sign instead of taking up room for cups.',
            "After Cy declined, Ari removed the paint box from the boat and put it at the workbench. The wrong delivery was physically repaired without Cy doing that carrying.", "The paint belonged beside the sign. Finding cups remained a separate job."),
        "failed_lift_waits_for_help": ('The crate stayed on the floor. Ari did not try to turn Cy\'s refusal into strength in Ari\'s own arms. The next attempt would need help, not a louder version of the first one.',
            "The heavy crate remained in the workshop after Ari's failed lift and Cy's refusal. It had not been loaded onto the cart.", "The cart still had an empty space, and the crate still had its weight."),
        "help_after_failed_lift": ('Cy lifted the crate onto the handcart. Ari watched the floor appear underneath it. "That was the part I could not do," Ari said.\n"I noticed," Cy said, and let go of the handles.',
            "Cy loaded the heavy crate onto the cart after accepting Ari's request. Ari's failed lift was followed by successful assistance from Cy.", "The crate rested squarely on the cart. Ari's hands were still empty."),
        "wrong_delivery_repaired": ('Cy took the paint box off the boat and put it on the workbench. Ari looked at the space it had left. "That is where the cups ought to be."\n"When you find them," Cy said. The repair had removed a wrong answer without supplying the missing one.',
            "Cy removed the paint box from the boat and put it at the workbench. The mistaken delivery was repaired, but cups had not been found by doing so.", "The boat had room for cups again. The paint was waiting beside the unfinished sign."),
        "rerouted_after_attempt": ('Cy carried the parcel along the lane past the sheds and put it down at the jetty. Ari\'s short trip had ended where it began; this longer one ended at the intended place.',
            "Cy used the known lane and delivered the parcel to the jetty. That completed the delivery after Ari's attempted footbridge route had failed.", "The parcel rested at the jetty. The longer route had finally made the distance smaller."),
        "tool_after_failed_pull": ('Cy handed over the scissors. Ari cut the sealed band, opened the parcel and put it on the bench. The flags were whole. The fastening had needed a cut, not a stronger opinion about pulling.',
            "Cy handed Ari the scissors, and Ari used them to open the sealed parcel. The opened flags were placed on the bench after the unsuccessful pull.", "The cut band no longer held the parcel shut. The paper flags had not been cut with it."),
    }
    results["divided_after_refusal"] = divided_scene()
    text, answer, image = results[outcome]
    add("result", text, "What was completed or repaired?", answer, "finish")
    final_answer = answer
    if job.prior_commitment:
        late = state.get("promises", "key_return").status == "breached"
        if late:
            text = 'At the jetty, Cy handed Bo the key after the promised time.\n"I helped Ari first."\n"I was waiting here," Bo said.\nThe brass key could be returned. The waiting could not.'
            answer = "Cy completed the key handoff late after helping Ari first. The physical return did not erase the missed promise deadline."
            image += ' At the jetty, Bo held the key that had arrived late.'
        else:
            text = 'Cy handed the brass key to Bo at the jetty by the promised time. The earlier arrangement had survived the new work, whether that work had been finished, shared or left for later.'
            answer = "Cy handed the key to Bo by the promised time. The actual handoff fulfilled the earlier commitment."
            image += ' Bo also had the key on time.'
        add("promise_result", text, "What happened to Cy's earlier promise?", answer, "key_return", "key_assess")
        final_answer += " " + answer
    add("ending", image, "What final state did the story leave?", final_answer, "finish")
    return Document(title=spec.title, statements=tuple(rows))
