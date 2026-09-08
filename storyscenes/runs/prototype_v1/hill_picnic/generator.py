from simulation import build
from runtime import solve, realize
import random


def render(run, rng):
    events = run["events"]
    final = run["final"]
    paragraphs = []

    openings = [
        "Ada had announced a hilltop picnic with the grand seriousness of a mayor opening a bridge. Ben checked the baskets twice, Moss flicked one thoughtful ear, and Noor waited at the hill's foot. The plan sounded splendid—but a splendid plan still had to fit the path, the weather, and the people invited.",
        "The picnic began with a hopeful map scratched in the dust: food below, hilltop above, and Noor somewhere comfortable between them. Ada loved the highest part of an idea. Ben loved checking whether an idea had enough room. Moss loved neither mud nor lopsided panniers.",
        "Ada wanted a picnic with a view. Ben wanted a picnic that stayed attached to the ground. At the hill's foot, Noor smiled patiently while Moss inspected the baskets as if he had been appointed chief of sensible arrangements."
    ]
    paragraphs.append({
        "text": rng.choice(openings),
        "event_ids": [],
        "kind": "beginning",
    })

    def scene_text(event, before, after):
        name = event["scene"]
        choices = {
            "inspect_path": (
                "Ada crouched beside the hill path and pressed a finger into its edge. "
                "“The ground is telling us something,” she said. The test showed that the route was "
                + ("soft and muddy." if after.get("path.condition") == "muddy" else "firm and gentle.")
                + " Ben nodded. “Then we use the path we have, not the path we wish we had.”"
            ),
            "ask_noor": (
                "Ada turned from the hill to Noor. “What would make this picnic truly comfortable?” "
                "Noor answered honestly: "
                + ("“I need a place sheltered from the gusts.”" if after.get("noor.preference") == "shelter"
                   else "“I can come, but only with slow, careful steps—and I do want the view.”")
                + " Ada listened instead of guessing."
            ),
            "tell_moss_path": (
                "Ada explained the path and Noor’s needs to Moss. Moss listened, then gave a low, "
                "considering hee-haw. “Good,” said Ben. “Now everybody is working with the same facts.”"
            ),
            "pack_small_picnic": (
                "Ben measured the basket with his hands. Ada tucked the bread and fruit into the "
                "substantial basket, while Ben placed the little view snack in its own bag. "
                "“Separate loads,” he said. “That way one heavy wobble cannot spoil everything.”"
            ),
            "invite_moss_rest": (
                "Before asking Moss to help, Ada brought him water. Moss drank, leaned into the quiet "
                "moment, and stood ready. “A helper is not a machine,” Ada reminded herself. "
                "Moss's pleased blink suggested he agreed."
            ),
            "roll_cart_to_shelter": (
                "The muddy ground made carrying awkward, so Ada and Ben guided the handcart instead. "
                "Moss walked beside them, pointing the safest way with his nose. The loaded basket "
                "rolled to the shelter without a heroic leap or a single unnecessary splash."
            ),
            "carry_picnic_up": (
                "On the gentle, calm path, the group climbed slowly. Noor chose each step, Moss carried "
                "only the manageable load, and Ada resisted the urge to hurry. At the top, everyone was "
                "breathing hard—but everyone, including the picnic, had arrived together."
            ),
            "spread_hilltop_blanket": (
                "Ada and Ben lifted the blanket from the basket and spread it where Noor could sit. "
                "The valley opened below them in green folds. “This is the view I hoped for,” Noor said, "
                "“and the welcome I hoped for too.”"
            ),
            "raise_windbreak": (
                "At the shelter, gusts tugged at every loose thing. Ada and Ben tied the cloth firmly "
                "between two posts. Noor tested the calm pocket behind it. “Much better,” Noor said. "
                "The cloth snapped like a little flag, but stayed put."
            ),
            "arrange_shelter_picnic": (
                "The friends arranged the blanket and basket inside the shelter. Noor settled in, while "
                "Moss found a dry patch nearby. The hill was still visible beyond the opening, so the "
                "picnic had not lost its purpose—it had simply chosen a wiser doorway."
            ),
            "carry_view_bag_up": (
                "Because the main path was muddy but the weather was calm, Ada, Ben, and Moss carried "
                "only the tiny view bag upward. They left Noor's substantial picnic safely below and "
                "placed a note at the top: a small bridge between two places."
            ),
            "return_from_view": (
                "The trio returned from the hilltop with the muddy path behind them and the note safely "
                "carried down. “We brought the view back,” Ada announced. Noor laughed. “And you brought "
                "yourselves back, which is even better.”"
            ),
            "arrange_split_picnic": (
                "Below, Noor and the children arranged the main picnic in the shelter. The hilltop note "
                "rested beside the basket, carrying the high view into the shared meal. It was not one "
                "picnic pretending to be two; it was one welcome with two connected places."
            ),
            "serve_hilltop_picnic": (
                "At last, Noor shared the bread and fruit on the hilltop. Moss rested nearby, his load "
                "safe and light. Ada looked over the valley and grinned. “The grand plan worked,” she "
                "said. Ben corrected her gently: “The changed plan worked.”"
            ),
            "serve_shelter_picnic": (
                "Noor served the bread and fruit beneath the shelter while the windbreak fluttered "
                "outside. Moss munched his reward in the quiet corner. “A good picnic,” Noor declared, "
                "“is a place where nobody has to pretend to be comfortable.”"
            ),
            "serve_split_picnic": (
                "Noor shared the rich picnic below and read the hilltop note aloud. Somewhere above, "
                "the view waited; here, the food and friendship were real and close. Ada placed the "
                "note beside the basket like a bridge laid across the table."
            ),
        }
        return choices.get(name, event["summary"] + ".")

    for index, event in enumerate(events):
        before = event.get("before", {})
        after = event.get("after", {})
        last = index == len(events) - 1
        text = scene_text(event, before, after)
        if last:
            place = final.get("picnic.place")
            if place == "hilltop":
                text += " The blanket held steady, the baskets were manageable, and the valley shone beyond Noor’s shoulder."
            elif place == "shelter":
                text += " The completed arrangement was sheltered, generous, and chosen with Noor rather than for Noor."
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
