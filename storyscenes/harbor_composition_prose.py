"""Scene realization from the successful composed trace, never search branches."""
from .capabilities.reading import Document, Statement


def render(spec, state, config, seed=0, *, include_ending=True):
    rows = []
    events = list(state.events)
    will_hang = any(e.action.id in {"hang_chart", "clip_chart", "board_chart"} for e in events)
    seen = []
    chart_mounts = lamp_places = lamp_window_visits = 0
    chart_place = None
    lamp_place = None
    launched = False

    def add(id, text, question, answer, support, premises=()):
        rows.append(Statement(id=id, text=text, question=question, answer=answer,
            kind=id, focus="ari", entity_ids=("ari", "cy", "bo"),
            event_ids=tuple(support) + tuple(f"initial/{p}" for p in premises),
            needs=(rows[-1].id,) if rows else ()))

    add("opening", 'Ari had drawn the harbor on one sheet of paper. Cy had made a boat small enough to sail in a tub. '
        'Both were ready to show their work; the harbor was not quite ready for them. '
        'Ari wanted the chart hanging upright, and Cy wanted water underneath the boat. '
        + ('The chart was meant to have a light of its own in the quay window.' if config.light_window else
           'Ari also wanted to leave a lantern shining at the jetty.') +
        ' Bo waited beside the covered launch tub. Its heavy lid needed the tools and Ari\'s rope to lift it.',
        "What were Ari and Cy trying to arrange?",
        "Ari wanted to hang the chart and arrange the lantern. Cy wanted to launch the little boat in the tub.",
        (), ("chart", "boat", "lamp", "cover", "chart_made", "boat_made"))

    for event in events:
        action = event.action.id
        seen.append(event)
        support = tuple(e.id for e in seen)
        if action in ("hang_chart", "clip_chart", "board_chart"):
            place = {"hang_chart": "rope", "clip_chart": "clip", "board_chart": "board"}[action]
            chart_mounts += 1
            if chart_mounts > 1 and place == "clip":
                text = 'Ari brought the chart back to the window, but not the rope. The small clip closed on the paper. '
                text += '"You can stay here without holding up the boat." The chart was upright again; the rope could keep its other job.'
                question = "How did Ari restore the display without taking the rope back?"
                answer = "Ari fastened the chart in the window clip. The paper stood upright while the rope stayed at the tub."
            elif chart_mounts > 1 and place == "board":
                text = 'Ari fitted the chart into the jetty board\'s clamps. "A change of address," Ari told the paper. '
                text += 'The rope could stay by the tub; the chart had something else to hold it.'
                question = "How could the chart be displayed while the rope stayed at the tub?"
                answer = "Ari moved the chart onto the jetty board. Its clamps held the paper without the rope."
            elif chart_mounts > 1:
                text = 'Ari brought the rope back from the jetty and hung the chart again. '
                text += '"You can have your harbor back now," Ari told the paper. The drawing spread out against the window. '
                text += 'The rope had finished lifting; it could go back to holding.'
                question = "Why could Ari hang the chart again?"
                answer = "The rope had already helped Bo open the tub. Ari brought it back and used it to hang the chart again."
            elif place == "rope":
                text = 'Ari took the chart and rope to the quay window. The rope held the paper upright. '
                text += '"There. A harbor that cannot get your feet wet." '
                text += ('Cy\'s boat was already on real water; now the paper harbor had its turn.' if launched else
                         'The little drawn jetty looked ready for visitors.')
                question = "How did Ari first hang the chart?"
                answer = "Ari hung it from the rope in the quay window. The paper was upright instead of lying flat."
            elif place == "clip":
                text = 'At the quay window, Ari fitted the chart into a small clip. "Just paper," Ari said. "You do not need a whole rope." '
                text += 'The clip kept its grip. The rope could stay out of the picture.'
                question = "What kept the chart upright without using the rope?"
                answer = "Ari fastened the paper in the window clip. That left the rope available for the tub cover."
            else:
                text = 'Ari carried the chart to the jetty and fitted it into the board\'s clamps. '
                text += '"You have brought a map to the place itself," Bo said. "Now we can see whether I got it right," Ari answered. '
                text += 'The paper stayed up without the rope.'
                question = "Where did Ari put the chart instead of using the window?"
                answer = "Ari mounted it on the jetty board. The clamps held it without using the rope."
            add(f"chart_{chart_mounts}", text, question, answer, support)
            chart_place = place
        elif action == "deliver_case":
            add("delivery", 'With the rope out of the case, Cy could manage the tools. '
                'The little boat came along too, still dry. Cy set the case beside Bo at the jetty. '
                '"I have brought nearly everything," Cy said. Bo looked for the coil. "Nearly is not quite a handle."',
                "What changed in the case before Cy brought it to Bo?",
                "The rope had been taken out of the case. Cy then brought the tools to Bo at the jetty.",
                support, ("load",))
        elif action == "take_chart_rope":
            add("dismantle", 'The rope was doing a good job at the window. That was the trouble. '
                'Ari lifted the chart down and held the paper by its edges. "You will have to be a folded harbor for a moment." '
                'With the chart off, Ari could take the rope to the tub.',
                "Why did Ari take down a chart that was already hanging?",
                "The same rope was needed to lift the tub cover. Ari took the chart down to free it for that job.",
                support, ("cover",))
            chart_place = None
        elif action == "open_tub":
            add("cover", 'Ari brought the rope to the jetty. Bo used it with the tools to lift the heavy cover. '
                'Cy leaned toward the water. "It looks much more like a harbor with the lid off." '
                + ('But the dark water was hard to see. The boat stayed in Cy\'s hands for the moment.' if config.dark_launch and lamp_place != "jetty" else
                   'For the first time, there was room for the boat to go somewhere.'),
                "What made it possible to open the launch tub?",
                "The rope and the case of tools were together at the jetty. Bo used them to lift the cover.",
                support, ("cover", "darkness"))
        elif action == "take_lantern_display":
            add("move_light", 'Ari lifted the lantern from the window. Its pool of light went with it. '
                '"The paper can wait for its light," Ari said. "The water needs it first." '
                'The lantern had another place to be before it could stay here.',
                "Why did Ari move the lantern away from the window?",
                "The launch needed light so Cy could see where to lower the boat. Ari carried the lantern to the jetty first.",
                support, ("darkness",))
        elif action in ("lamp_quay", "lamp_jetty"):
            lamp_places += 1
            dest = "quay" if action == "lamp_quay" else "jetty"
            if dest == "quay" and lamp_place == "jetty":
                movement = "back to" if lamp_window_visits else "to"
                text = f'After the launch, Ari carried the lantern {movement} the window. "You can stop being a lighthouse now." '
                text += ('Its light found the hanging chart.' if chart_place else
                         'Its light waited on the shelf for the chart to return.' if chart_mounts else
                         'Its light spread across the empty window shelf.')
                question = "Where did the lantern go after helping with the launch?"
                answer = f"Ari carried it {movement} the quay window. It was meant to light the chart there."
            elif dest == "quay":
                text = 'Ari opened the lantern shutter and set it in the quay window. '
                text += ('The lines of the chart stood out in its light.' if chart_place else
                         'A small bright patch marked the place where the chart would hang.' if will_hang else
                         'Light spread across the empty window shelf.')
                text += ' "A bit of daylight we can put where we want it."'
                question = "Where did Ari first arrange the light?"
                answer = "Ari opened the lantern shutter and put it in the quay window. Light spread from the lantern into the window."
            else:
                text = 'Ari set the open lantern beside the tub at the jetty. '
                text += ('The light caught the little boat already floating on the water.' if launched else
                         'The light reached the water where Cy would lower the boat.' if "open_tub" in {e.action.id for e in seen} else
                         'Its light lay across the covered tub, ready for the work still to come.')
                text += ' "A small harbor light," Bo said.'
                question = "What did Ari bring to light the launch area?"
                answer = "Ari set the open lantern beside the tub at the jetty. Its light fell across the launch area."
            add(f"lamp_{lamp_places}", text, question, answer, support, ("glow",))
            lamp_window_visits += dest == "quay"
            lamp_place = dest
        elif action == "launch":
            text = 'Cy lowered the boat onto the water and opened both hands. For a moment the little hull rested still. '
            text += '"It does not need me to hold it," Cy said. Bo watched it float. "That was the idea."'
            add("launch", text, "What happened when Cy let go of the boat?",
                "The boat floated on the tub water. Cy no longer had to hold it.", support)
            launched = True

    if not include_ending:
        return Document(title=spec.title, statements=tuple(rows))
    chart = state.get("parents", "chart").parent
    lamp = state.get("parents", "lantern").parent
    if chart == "board":
        image = 'The drawn harbor stood on the jetty board beside the real one. Below it, Cy\'s little boat had water instead of paper underneath it.'
    elif lamp == "display":
        image = 'Light filled the harbor on Ari\'s chart. Out at the jetty, Cy\'s boat floated in its own small harbor. Neither one needed a hand to keep it in place.'
    else:
        image = 'The chart hung at the window, and the lantern stayed by the water. Cy\'s boat floated beside its light, smaller than the harbor Ari had drawn and quite large enough for itself.'
    add("ending", image, "What was arranged by the end?",
        f"The chart hung {'on the jetty board' if chart == 'board' else 'in the quay window'}, and Cy's boat floated in the tub. "
        + ("The lantern lit the window." if lamp == "display" else "The lantern stayed at the jetty."),
        tuple(e.id for e in events))
    return Document(title=spec.title, statements=tuple(rows))
