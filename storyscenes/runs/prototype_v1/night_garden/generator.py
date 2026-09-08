from simulation import build
from runtime import solve, realize


def render(run, rng):
    events = run["events"]
    entities = run["entities"]
    initial = run["initial"]
    final = run["final"]

    def name(entity_id):
        return entities.get(entity_id, {}).get("name", entity_id.replace("_", " "))

    opening_choices = [
        "Night folded itself around the garden, and Ada and Ben prepared a welcome for Mica, a shy moth who had not yet decided whether their garden felt safe.",
        "The garden glittered with dew beneath the moon. Ada watched the quiet edges while Ben imagined the most impressive welcome a moth had ever seen.",
        "A small visitor was due in the night garden. Ada brought her careful eyes, Ben brought his grand ideas, and Mica hovered somewhere beyond the brightest patch of light.",
    ]
    paragraphs = [{
        "text": rng.choice(opening_choices) + " They soon discovered that welcoming someone was not the same as making everything brighter.",
        "event_ids": [],
        "kind": "beginning",
    }]

    dialogue = {
        "light_lamp": "“Now it will look splendid!” Ben said, turning the lamp up.",
        "inspect_mica": "Ada leaned toward the edge without rushing. “There you are,” she whispered.",
        "inspect_shadow": "“The shadow is telling us something,” Ada murmured, studying its shape.",
        "inspect_lamp_position": "Ada checked the lamp carefully. “Before we change anything, we should know where it is.”",
        "find_landing": "Ada followed the shadow with one finger. “This is the clearer way in,” she said.",
        "explain_landing_need": "“Mica needs a gentler edge and room to land,” Ada told the steward.",
        "lend_pale_cloth": "The steward listened, then handed Ada the pale cloth. “Use it thoughtfully,” they said.",
        "hang_pale_cloth": "Ben held the corners while Ada arranged the cloth. “Soft light,” they agreed.",
        "dim_lamp": "Ben turned the lamp down. “Impressive can mean comfortable, too.”",
        "move_lamp_low": "Ada and Ben lifted together. “Slowly—keep the path clear,” Ada said.",
        "clear_flower_landing": "They moved the sign aside and opened the flower bed. “A landing place needs to be a real place,” Ben said.",
        "clear_fern_landing": "They carried the sign away from the ferns. “No tripping over our welcome,” Ada said.",
        "mark_flower_circle": "Together they set the sign in the new circle. “This is ready,” Ben said, “but only if Mica agrees.”",
        "mark_fern_circle": "They marked the fern-side circle with the flower sign. “A quiet edge,” Ada said.",
        "mica_settles": "Mica circled once, then twice. “Your turn,” Ada whispered. “Choose the place that feels right.”",
    }

    def detail(event):
        scene = event["scene"]
        before = event.get("before", {})
        after = event.get("after", {})
        changes = event.get("changes", {})
        lines = [event["summary"] + "."]
        if scene == "light_lamp":
            lines.append("Its bright beam stretched a long shadow across the garden.")
        elif scene == "inspect_mica":
            lines.append("Ada learned which edge Mica was watching, instead of guessing.")
        elif scene == "inspect_shadow":
            lines.append("The shadow reached farther than anyone had expected.")
        elif scene == "inspect_lamp_position":
            lines.append("She tucked that useful fact away before suggesting a change.")
        elif scene == "find_landing":
            landing = after.get("ada.knows.landing", "the open edge")
            lines.append("Her careful tracing pointed toward the " + str(landing) + " side.")
        elif scene == "dim_lamp":
            lines.append("The garden kept its welcoming glow, but the sharp brightness eased.")
        elif scene == "move_lamp_low":
            lines.append("The lamp settled on the low stone, and its shadow shortened.")
        elif scene.startswith("clear_"):
            lines.append("Leaves and clutter no longer blocked the chosen approach.")
        elif scene.startswith("mark_"):
            landing = after.get("welcome_circle.landing", "chosen")
            lines.append("The circle now offered a reachable resting place by the " + str(landing) + " edge.")
        elif scene == "hang_pale_cloth":
            lines.append("The still cloth softened the beam without fluttering into the path.")
        elif scene == "lend_pale_cloth":
            lines.append("The borrowed cloth became part of the experiment, not a decoration to ignore.")
        elif scene == "mica_settles":
            lines.append("Mica settled safely, her wings folding over the flower sign.")
        elif scene == "explain_landing_need":
            lines.append("The steward now knew which landing edge Ada had discovered.")
        return " ".join(lines)

    for index, event in enumerate(events):
        text = detail(event)
        if event["scene"] in dialogue:
            text = dialogue[event["scene"]] + " " + text
        if index == len(events) - 1:
            text += " Ada and Ben watched quietly, letting the changed arrangement speak for itself."
        paragraphs.append({
            "text": text,
            "event_ids": [event["id"]],
            "kind": "ending" if index == len(events) - 1 else "scene",
        })

    return paragraphs


def generate(seed, prose_seed=None):
    return realize(
        solve(build(seed), seed),
        render,
        seed if prose_seed is None else prose_seed,
    )
