from simulation import build
from runtime import solve, realize


def render(run, rng):
    events = run["events"]
    initial = run["initial"]
    final = run["final"]

    need = initial.get("noor.need", "plain")
    need_words = {
        "plain": "a plain bun",
        "berry": "a berry bun",
    }
    suitable = need_words.get(need, "a suitable bun")

    beginning_texts = [
        "Sunlight spilled across Mara's market stall, where three buns waited on a tray and one paper label seemed determined to cause trouble. Ada stood ready to help Pip the squirrel and hungry Noor share the morning's baking.",
        "At the sunny market stall, the buns looked delicious—but the label did not make everything clear. Ada glanced from proud Pip to hungry Noor and decided that careful checking would be better than guessing.",
    ]
    paragraphs = [{
        "text": rng.choice(beginning_texts),
        "event_ids": [],
        "kind": "beginning",
    }]

    fixed = {
        "inspect_label": "Ada leaned over the tray and examined the paper label. She frowned thoughtfully: a label could be neat and still be wrong.",
        "taste_berry_crumb": "With Mara's tasting plate ready, Ada sampled one tiny berry crumb. “That tells us what this bun truly holds,” she said, wiping her fingers.",
        "weigh_buns": "Ada placed the buns on the little scale and compared their shapes and weights. “Evidence first,” she announced, as the pointer bobbed and settled.",
        "ask_noor": "Ada turned to Noor. “Which filling will be gentle and filling for you?” Noor answered clearly, and Ada listened instead of making a guess.",
        "tell_mara_label": "Ada told Mara what the label seemed to say. Mara listened carefully, though she knew that Ada's first clue might not be the whole truth.",
        "show_mara_evidence": "Ada showed Mara what she had checked and explained Noor's need. “Now we can make a fair choice,” she said.",
        "pip_claims_saved_nut": "Pip puffed out his little chest. “That nut bun is the one I saved!” he declared, making sure everyone heard his promise.",
        "pip_chooses_nut": "Pip pointed straight at the nut bun. “That is my favorite,” he said, and Mara let him choose it openly.",
        "reserve_claimed_nut": "Since Pip had claimed the bun for a promise, Mara reserved it for him. Pip relaxed, pleased that his word had been remembered.",
        "grant_generous_permission": "Mara smiled and welcomed Ada's careful idea. “You may arrange the basket,” she said, giving permission before anything was moved.",
        "grant_cautious_permission": "Mara considered Ada's evidence, then nodded. “I wanted to be sure,” she explained. “Now I agree you may arrange the share.”",
        "give_plain_bun": "Ada placed the plain bun in Noor's basket portion. Noor's shoulders loosened, and the hungry neighbor finally had food that suited them.",
        "give_berry_bun": "Ada placed the berry bun in Noor's basket portion. Noor smiled at the safe, bright filling and thanked Ada for checking first.",
        "display_checked_labels": "Ada and Mara set out the checked label beside the tray. The display was no longer confusing: its words matched the buns.",
        "make_new_label_from_sample": "There was no useful label to trust, so Ada and Mara made a fresh one from the checked evidence. It stood plainly beside the tray.",
        "lend_spare_label": "Mara handed Ada the spare paper label. “Use it carefully,” she said, and Ada accepted the useful bit of stall equipment.",
    }

    for event in events:
        sid = event["scene"]
        text = fixed.get(sid, event["summary"] + ".")
        if sid == "inspect_label":
            known = event["after"].get("ada.knows.label.accurate")
            text += " Ada discovered that it was " + ("accurate." if known else "not accurate.")
        elif sid == "tell_mara_label":
            text += " Now Mara knew what Ada had observed, too."
        elif sid == "show_mara_evidence":
            text += " Mara could see why the arrangement needed care."
        elif sid in ("give_plain_bun", "give_berry_bun"):
            text += " Noor received " + suitable + ", while the other buns stayed accounted for."
        elif sid in ("display_checked_labels", "make_new_label_from_sample"):
            text += " Pip's choice and Noor's portion could now be seen without confusion."
        elif sid == "lend_spare_label":
            text += " The label was borrowed, not mysteriously created."
        elif sid == "weigh_buns":
            text += " Ada still waited for Mara's permission before rearranging anything."
        elif sid == "reserve_claimed_nut":
            text += " Pip's promised nut bun remained his, while the sharing problem continued to be solved around it."

        paragraphs.append({
            "text": text,
            "event_ids": [event["id"]],
            "kind": "scene",
        })

    last_id = events[-1]["id"] if events else 0
    received = final.get("noor.received")
    received_name = {"plain": "plain", "berry": "berry"}.get(received, "suitable")
    display = final.get("stall.display")
    ending = (
        "By the end, Noor held the " + received_name + " bun, Pip's saved nut bun was "
        + ("still his" if final.get("nut.owner") == "pip" else "settled fairly")
        + ", and the stall's display was "
        + ("clear and accurate." if display == "clear" else "carefully arranged.")
        + " The fresh label and the basket made the change visible: no bun had vanished, and nobody had to rely on a proud guess."
    )
    paragraphs.append({
        "text": ending,
        "event_ids": [last_id],
        "kind": "ending",
    })
    return paragraphs


def generate(seed, prose_seed=None):
    return realize(
        solve(build(seed), seed),
        render,
        seed if prose_seed is None else prose_seed,
    )
