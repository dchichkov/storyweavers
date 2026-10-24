"""Show the physical cost of a chosen plan, without calling deferral success."""
from dataclasses import replace

from .harbor_composition_prose import render as render_composition
from .capabilities.reading import Document, Statement


def render(spec, state, config, seed=0):
    choice = state.get("harbor_choices", "evening")
    rules = state.get("harbor_resource_rules", "harbor")
    document = render_composition(spec, state, config, seed, include_ending=not choice.deferred)
    rows = list(document.statements)
    opening = rows[0]
    text = opening.text
    if rules.hold_cover:
        text += ' The rope would have to stay secured there to keep the cover up.'
    if rules.keep_launch_light:
        text += ' The lantern would have to stay beside the boat while it floated in the dark.'
    rows[0] = replace(opening, text=text,
        event_ids=opening.event_ids + (("initial/darkness",) if rules.keep_launch_light else ()))
    events = {e.action.id: e for e in state.events}
    order = {e.id: i for i, e in enumerate(state.events)}

    def add(id, text, question, answer, action, premises=()):
        rows.append(Statement(id=id, text=text, question=question, answer=answer, kind=id, focus="ari",
            event_ids=(events[action].id,) + tuple(f"initial/{p}" for p in premises), entity_ids=("ari", "cy", "bo")))

    if not choice.deferred:
        choice_text = 'Ari considered the three jobs. "We can make room for all of them." It might mean moving things more than once, but nothing had to be given up.'
    elif choice.deferred == ("boat",):
        if "rope" in choice.blockers:
            constraint = ('The window clip was jammed, and Ari wanted the chart to stay in that window.' if config.light_window else
                          'Neither the window clip nor the board clamps would open.')
            choice_text = constraint + ' "The chart stays up," Ari decided. "That means the rope cannot hold the lid as well."'
        else:
            choice_text = 'There was only one lantern. "I want the window lit," Ari decided. "Then it cannot stay with the boat too."'
        choice_text += ' Cy\'s voyage would have to wait.'
    elif set(choice.deferred) == {"chart", "lamp"}:
        choice_text = 'Ari looked at the boat. "Let it have its voyage. My chart can lie flat, and the light can stay by the water." '
        choice_text += 'The window would not look the way Ari had planned.'
    elif choice.deferred == ("chart",):
        choice_text = '"Let the rope hold the cover," Ari decided. "My chart can lie flat." '
        choice_text += 'It was a choice between showing the paper upright and putting the boat on water. Ari chose the boat.'
    else:
        choice_text = '"Leave the light with the boat," Ari decided. "The window can be dark." '
        choice_text += 'The chart could still be displayed, but it would have to do without its little patch of daylight.'
    labels = dict(chart="hang the chart", lamp="light the window" if config.light_window else "leave the light at the jetty", boat="launch the boat")

    def goal_list(goals):
        names = [labels[g] for g in goals]
        return " and ".join(names) if len(names) < 3 else ", ".join(names[:-1]) + " and " + names[-1]

    answer = f"Ari chose to {goal_list(choice.kept)}. "
    if not choice.deferred:
        answer += "None of the three plans had to be deferred."
    elif len(choice.deferred) == 1:
        answer += f"The plan to {goal_list(choice.deferred)} was deferred."
    else:
        answer += f"The plans to {goal_list(choice.deferred)} were deferred."
    add("choice", choice_text, "Which plans did Ari choose to carry out?",
        answer,
        "choose_goals", ("priorities", "cover", "darkness", "clip", "board"))

    if "lay_chart_flat" in events:
        add("flat_chart", 'Ari laid the chart flat on the window shelf. The drawn harbor was still there, but visitors would have to look down at it. '
            '"Not quite my exhibition," Ari said, smoothing an edge. "Still my harbor."',
            "What happened to the chart when Ari gave up hanging it?",
            "Ari laid it flat on the window shelf. It was still displayed, but not upright as originally planned.", "lay_chart_flat")
    if "dock_boat" in events:
        add("dry_boat", 'Cy carried the boat to the jetty and set it in the dry cradle beside the tub. '
            '"A berth, not a voyage," Cy said. Bo looked at the covered water. The little hull would have to keep its first wake for another time.',
            "Did Cy launch the boat after Ari deferred that plan?",
            "No. Cy put it in the dry cradle beside the tub. The boat had a resting place, but it had not sailed.", "dock_boat")
    if choice.deferred:
        boat = state.get("parents", "boat").parent
        chart = state.get("parents", "chart").parent
        lantern = state.get("parents", "lantern").parent
        if boat == "dry_dock":
            ending = 'The chart had its place and the lantern had its light. At the jetty, the boat rested in a cradle without a ripple underneath it. '
            ending += 'Ari\'s harbor was ready to be looked at. Cy\'s was still waiting.'
            answer = "The chart and light were arranged, but the boat remained dry in its cradle. The planned voyage did not happen."
        elif chart == "display":
            ending = 'At the window, the chart lay flat. Out at the jetty, Cy\'s boat stood upright on the water. '
            ending += ('The lantern stayed with it; the window had neither the hanging picture nor its light.' if lantern == "jetty" and config.light_window else
                       'The window still had its light, but the rope had a heavier thing to hold.' if lantern == "display" else
                       'The lantern lit the little hull, and the rope kept the cover above it.')
            answer = "The boat floated while the chart lay flat instead of hanging. " + (
                "The lantern stayed with the boat." if lantern == "jetty" else "The lantern lit the window.")
        else:
            ending = 'The chart hung without its pool of light. At the jetty, the lantern made the little boat bright on the dark water. '
            ending += 'Ari had kept the drawing upright and let its daylight go somewhere else.'
            answer = "The chart was displayed and the boat floated. The lantern stayed at the jetty, so the window did not get its light."
        add("ending", ending, "What was gained and what was left unfinished?", answer,
            state.events[-1].action.id, ("chart", "boat", "lamp"))
    # Insert the new choice/resting-state scenes at their actual trace position.
    # The ending stays last even if its support includes a late non-prose action.
    rows.sort(key=lambda s: (len(state.events) + 1 if s.id == "ending" else
                             max((order[e] for e in s.event_ids if e in order), default=-1)))
    rows = [replace(s, needs=(rows[i-1].id,) if i else ()) for i, s in enumerate(rows)]
    return Document(title=spec.title, statements=tuple(rows))
