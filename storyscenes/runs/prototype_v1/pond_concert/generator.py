from simulation import build
from runtime import solve, realize


def render(run, rng):
    events = run["events"]
    entities = run["entities"]
    initial = run["initial"]
    final = run["final"]

    def name(entity_id):
        return entities.get(entity_id, {}).get("name", entity_id)

    water = initial.get("water.condition")
    place = initial.get("tansy.location")
    carrier = initial.get("carrier.kind")

    openings = [
        f"At Lilypond, Pip dreamed of filling the morning with music. Ada and Milo stood at the water's edge while Tansy listened from the {name(place)}. Nobody yet knew which sounds would reach her kindly.",
        f"Pip had announced a concert at Lilypond, though his first plan was mostly volume. Ada watched carefully, Milo eyed every floating object, and Tansy waited near the {name(place)}, listening in her own way.",
        f"The pond glittered around Pip's little stage. “A concert!” he croaked. Ada smiled but studied the water, Milo studied the props, and Tansy settled beside the {name(place)}. A good performance, they decided, would need more than a loud voice.",
    ]
    paragraphs = [{
        "text": rng.choice(openings),
        "event_ids": [],
        "kind": "beginning",
    }]

    texts = {
        "walk_to_tansy": lambda e: (
            f"Ada followed the pond edge from the reed bank to Tansy's listening place. "
            f"“I want to see what the music feels like there,” she said, taking careful steps beside the water."
        ),
        "inspect_tansy": lambda e: (
            f"Ada watched Tansy instead of guessing. The turtle tilted her shell and rested a foot against the {name(place)}. "
            f"“You are listening through {e['after'].get('ada.knows.tansy.hears', 'the pond')}, not simply waiting for a croak,” Ada said."
        ),
        "inspect_water": lambda e: (
            f"Ada crouched and studied the surface. The pond was {e['after'].get('water.condition', water)}. "
            f"“That matters,” she murmured. “Water can carry a rhythm, or scatter it.”"
        ),
        "inspect_carrier": lambda e: (
            f"Milo tested the floating choices with a tap and a nudge. The useful carrier was the {e['after'].get('carrier.kind', carrier)}. "
            f"“This one answers back,” he told Ada, rapping it gently."
        ),
        "lend_rope": lambda e: (
            f"Pip handed Milo the rope. “Use it carefully,” he said, puffing out his throat. "
            f"Milo looped it over his arm. “Careful is exactly what a concert engineer needs.”"
        ),
        "link_pads": lambda e: (
            f"Ada and Milo tied the floating pads together, making a small bridge instead of three drifting islands. "
            f"Milo tugged the knot. “Now a tap can travel from pad to pad.” Ada nodded: “And Tansy can feel it.”"
        ),
        "anchor_log": lambda e: (
            f"Together they anchored the hollow log beside Tansy's listening place. Milo struck its side softly; a low, friendly thrum moved through the water. "
            f"Tansy lifted her head. “That is much better than a shout,” she said."
        ),
        "raise_sail": lambda e: (
            f"Milo raised the leaf sail where it could be seen across the rippling pond. It fluttered like a green flag. "
            f"“If the water muddles the sound,” Ada said, “we can let the rhythm show itself too.”"
        ),
        "place_soft_reeds": lambda e: (
            f"Ada placed the soft reeds along the splashy side of the pond. They whispered and settled, damping the noisy slosh. "
            f"“Now a gentle tune has room,” she said. Tansy gave an approving blink."
        ),
        "float_stage_near_tansy": lambda e: (
            f"Ada and Milo eased Pip's stage closer to Tansy's steady listening place. The lily pad bobbed, but did not wander. "
            f"Pip tried one tiny note. “Not too close, not too far,” Milo observed."
        ),
        "tansy_tests_arrangement": lambda e: (
            f"Tansy tested the arrangement herself. She pressed one patient foot against the {name(place)} and listened. "
            f"Then she tapped back. “There,” she said. “I can answer that.”"
        ),
        "tell_pip_about_water": lambda e: (
            f"Ada carried her observation to Pip. “The water is {e['after'].get('pip.knows.water.condition', water)}, so your music must suit it.” "
            f"Pip considered this, then nodded. “A composer can change a tune without losing its heart.”"
        ),
        "choose_tapping": lambda e: (
            f"Pip abandoned his biggest croak and tried tapping instead. Tap-tap, pause; tap-tap, pause. "
            f"“The ripples are busy,” he explained. “So I will give them a rhythm they can carry.”"
        ),
        "choose_call_and_response": lambda e: (
            f"Pip shaped a patient call-and-response tune. “I will call,” he said, “and Tansy can answer.” "
            f"His next note was warm and round, leaving a neat space for her reply."
        ),
        "perform_tapping_concert": lambda e: (
            f"Pip performed at last, tapping a bright pattern that traveled kindly across the ripples. Tansy's foot answered from the anchored arrangement. "
            f"The pads and log trembled together, turning the pond into a gentle, shared drum."
        ),
        "perform_call_concert": lambda e: (
            f"Pip began his call-and-response concert. His tune crossed the quiet water, and Tansy answered with one patient foot tap, then another. "
            f"The stage, the softened pond edge, and her listening place now belonged to the same small song."
        ),
    }

    for index, event in enumerate(events):
        scene_id = event["scene"]
        if scene_id in texts:
            text = texts[scene_id](event)
        else:
            changed = list(event.get("changes", {}).keys())
            detail = changed[0] if changed else "the arrangement"
            text = (
                f"{', '.join(name(actor) for actor in event.get('actors', []))} "
                f"worked on the pond concert. Their action changed {detail}, and the next sound could now travel differently."
            )

        kind = "ending" if index == len(events) - 1 else "scene"
        if kind == "ending":
            route = final.get("concert.route")
            style = final.get("music.style")
            text += (
                f" By the final moment, the {route} arrangement was in place and Pip's music was {style}; "
                f"Tansy's answering tap proved that this concert had truly reached its listener."
            )
        paragraphs.append({
            "text": text,
            "event_ids": [event["id"]],
            "kind": kind,
        })

    return paragraphs


def generate(seed, prose_seed=None):
    return realize(
        solve(build(seed), seed),
        render,
        seed if prose_seed is None else prose_seed,
    )
