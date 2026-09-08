from simulation import build
from runtime import solve, realize


def render(run, rng):
    events = run["events"]
    initial = run["initial"]
    final = run["final"]
    entities = run["entities"]
    paragraphs = []

    wind = initial.get("wind.pattern")
    defect = initial.get("kite.defect")
    bulky = initial.get("note.bulky")

    opening_choices = [
        "On the rooftop of Orra's workshop, Mina held a tiny note between her fingers. She and Brindle wanted to send it to the marked basket, but the kite, the wind, and Brindle's enthusiastic breath all had opinions of their own.",
        "The little rooftop workshop buzzed with a very important job: one small message had to travel to the marked basket. Mina studied the kite while Brindle watched the sky, already looking eager to help.",
        "Mina spread the kite across the workbench. Somewhere beyond the roof waited a marked basket, and inside Mina's hand was a note meant to reach it. Brindle puffed a hopeful little cloud and tried not to look too excited."
    ]
    paragraphs.append({
        "text": rng.choice(opening_choices),
        "event_ids": [],
        "kind": "beginning",
    })

    names = {key: value["name"] for key, value in entities.items()}

    def event_text(event, index):
        sid = event["scene"]
        before = event["before"]
        after = event["after"]
        actor_names = [names.get(actor, actor) for actor in event["actors"]]
        actors = " and ".join(actor_names)

        if sid == "inspect_kite":
            return (f"Mina bent close to the paper kite and ran one careful finger along its frame. "
                    f"She found the trouble at last: the kite's {defect} condition was not a guess anymore. "
                    f"“Now we know what we are fixing,” she said.")
        if sid == "read_wind":
            pattern = after.get("brindle.knows.wind.pattern", wind)
            detail = "the ribbon snapped and danced in impatient jerks" if pattern == "gusty" else "the ribbon floated in a soft, steady wave"
            return (f"Brindle watched the wind sock instead of charging toward the launch platform. "
                    f"{detail.capitalize()}. “It is {pattern} today,” Brindle reported, making the weather part of the plan.")
        if sid == "borrow_repair_kit":
            return ("After Mina explained what she had discovered, Orra opened the cupboard and lent her the repair kit. "
                    "“A tool is most useful when it is used for the problem you actually have,” Orra said.")
        if sid == "lend_tether_rope":
            return ("Orra passed Mina the short tether rope. Mina tested its knots and thanked her. "
                    "It was not as grand as a soaring flight, perhaps, but it was a real, dependable way to keep a message safe.")
        if sid == "straighten_frame":
            return ("Mina set the repair tool against the bowed frame and eased it straight, little by little. "
                    "The paper stopped puckering. She lifted the kite and smiled when both sides balanced.")
        if sid == "secure_knot":
            return ("Mina and Brindle worked together at the loose knot. Mina held the string steady while Brindle used careful claws, not enthusiastic ones. "
                    "The knot tightened and stayed put.")
        if sid == "lengthen_tail":
            return ("Mina added the extra tail material and smoothed its edge. When she let the kite settle, its tail no longer whipped sideways. "
                    "“Sometimes the answer is behind the kite,” Brindle observed.")
        if sid == "prepare_message":
            if bulky:
                return ("The note began too bulky for a breezy trip, so Mina rolled it tightly and tucked it into the little tube. "
                        "The tube clicked shut around the message. “Lighter,” she said. “Much wiser.”")
            return ("Mina rolled the note neatly and placed it inside the little message tube. "
                    "She checked that no corner stuck out, then gave the tube a satisfied tap.")
        if sid == "practice_breath":
            return ("Brindle practiced against the loose ribbon, beginning with a breath so small it barely stirred a thread. "
                    "The ribbon lifted without snapping. “I can do gentle,” Brindle said, sounding surprised and proud.")
        if sid == "choose_high_route":
            return ("With the wind understood and the kite balanced, Mina and Brindle chose the high route. "
                    "Mina pointed toward the open air. Brindle nodded, ready to help only as much as the kite needed.")
        if sid == "choose_low_route":
            return ("The gusts shoved at the wind sock, so Mina changed the arrangement. "
                    "“No high flight today,” she decided. They chose the low tether route, where the short rope could guide the tube safely.")
        if sid == "attach_message":
            return ("Mina and Brindle secured the tube to the carrier. Mina tugged once, Brindle tugged twice, and nothing slipped. "
                    "The tiny note was no longer merely prepared; it was safely attached.")
        if sid == "launch_high_kite":
            return ("At the platform, Mina released the kite while Brindle gave one measured puff. "
                    "The paper rose instead of buckling. Its string hummed, its tail steadied, and the kite held the air.")
        if sid == "send_high_message":
            return ("The stable kite climbed toward the marked basket, carrying the secured tube. "
                    "For one bright moment its tail drew a neat loop against the sky. Then kite, tube, and message reached the basket together.")
        if sid == "send_low_message":
            return ("Mina and Brindle guided the tube along the short tether. A gust scuffed the basket and made Brindle squeak, but the rope held. "
                    "The tube arrived low, steady, and completely secure.")
        if sid == "confirm_receipt":
            return ("Orra checked the marked basket and found the tube waiting inside. "
                    "She lifted it carefully and called across the roof, “The message arrived!” The workshop suddenly felt wonderfully quiet.")
        return event["summary"] + "."

    for index, event in enumerate(events):
        text = event_text(event, index)
        if index == len(events) - 1:
            paragraphs.append({
                "text": text,
                "event_ids": [event["id"]],
                "kind": "ending",
            })
        else:
            paragraphs.append({
                "text": text,
                "event_ids": [event["id"]],
                "kind": "scene",
            })

    return paragraphs


def generate(seed, prose_seed=None):
    return realize(
        solve(build(seed), seed),
        render,
        seed if prose_seed is None else prose_seed,
    )
