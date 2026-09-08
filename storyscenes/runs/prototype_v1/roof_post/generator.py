from simulation import build
from runtime import solve, realize
import random


def render(run, rng):
    events = run["events"]
    initial = run["initial"]
    final = run["final"]
    names = {key: value["name"] for key, value in run["entities"].items()}

    wind_words = {1: "a gentle", 2: "a brisk"}
    count = initial["invitations.count"]

    beginning_choices = [
        (
            f"Before sunset, Ada had {count} garden-party invitations waiting at the roof post. "
            f"Pip the young dragon stood beside her, eager to help, while Mara watched the roof paths and the "
            f"planters below. The ribbon wind-marker flickered. “We need every invitation to arrive safely,” Ada said. "
            f"“Then we should find out what the roof is telling us first.”"
        ),
        (
            f"The invitations were ready, but the rooftops were not a simple road. Ada counted {count} papers, "
            f"Pip warmed his cheeks for a helpful puff, and Mara checked the nearby pots. “No daring guesses,” Mara said. "
            f"Ada nodded. “We will notice, test, and change our method if we need to.” Above them, the marker ribbon began to dance."
        ),
    ]

    def text_for(event):
        sid = event["scene"]
        before = event["before"]
        after = event["after"]

        if sid == "inspect_wind":
            wind = after["ada.knows.ribbon.wind"]
            return (
                f"Ada leaned close to the ribbon without grabbing it. It streamed toward the chimney, then relaxed. "
                f"She watched twice before deciding the wind was {wind_words.get(wind, 'an unusual')} breeze. "
                f"“It is only strength {wind},” she told herself, “but that is enough to matter.”"
            )
        if sid == "inspect_paper":
            return (
                "Ada lifted the top invitation by its corner and checked the stack. The paper was dry and un-torn. "
                "She smoothed one curled edge. “Good,” she said. “We can carry these, but we must keep them from fluttering loose.”"
            )
        if sid == "inspect_route":
            route = after["ada.knows.glasshouse.route"]
            if route == "open":
                return (
                    "Ada peered along the roofline toward the glasshouse. The route was open, with no fallen tools or "
                    "blocked stepping stones. She pointed it out to Mara. “That path may be useful,” she said, “if the wind agrees.”"
                )
            return (
                "Ada looked toward the glasshouse and found the route closed. A small gate barred the way. "
                "“That settles it,” she said. “We need the sheltered chimney nook instead of pretending a closed path is open.”"
            )
        if sid == "test_pip_puff":
            control = after["pip.knows.breath_control"]
            if control >= 2:
                return (
                    "Pip gave the ribbon a tiny warm puff. It lifted neatly and settled without whipping away. "
                    "His eyes widened. “I can make a small breeze,” he said. Ada grinned. “Small and steady is exactly what we need.”"
                )
            return (
                "Pip tried a tiny warm puff, but the ribbon bobbed sideways and nearly brushed a pot. "
                "He stopped at once. “My breath is wobbly today,” he admitted. Ada answered, “Then we will use your eyes and ears, not a big puff.”"
            )
        if sid == "tell_mara_wind":
            wind = after["mara.knows.ribbon.wind"]
            return (
                f"Ada explained what she had seen: the ribbon showed strength {wind} wind. "
                "Mara listened rather than glancing at the sky. “Thank you,” she said. “Now I can lend the carrier that fits the weather.”"
            )
        if sid == "repair_pouch":
            return (
                "Mara turned the cloth pouch inside out and found its loose seam. With twine and careful little stitches, "
                "she repaired it. She tugged the mouth twice. “Now it will hold,” she said, “but only because we checked it first.”"
            )
        if sid == "lend_pouch":
            return (
                "Mara placed the ready pouch in Ada’s hands. “Keep it low and tied,” she said. Ada accepted it carefully. "
                "The pouch was no longer merely waiting at the post; it was now part of their working arrangement."
            )
        if sid == "lend_twine":
            return (
                "Mara passed Ada the coil of twine. “A line gives the pouch a boundary,” she explained. "
                "Ada tested the cord between her fingers. “So Pip can guide the bundle without chasing it,” she replied."
            )
        if sid == "lend_basket":
            return (
                "Because the glasshouse route was closed, Mara lent Ada the light basket. "
                "“Cover the papers,” she warned. Ada nodded, and Pip peered over the rim. “A basket can travel on the safe side,” Ada said."
            )
        if sid == "pack_pouch":
            return (
                "Ada placed the invitations in the pouch while Pip held its mouth open with careful claws. "
                "Together they tied it shut. The papers were secured inside, not merely imagined there. "
                "Pip whispered, “No heroic gusts.” Ada replied, “Only tested ones.”"
            )
        if sid == "pack_basket":
            return (
                "Ada settled the invitations into the light basket. Pip helped lower the cloth cover, and Ada tucked every corner beneath the rim. "
                "The bundle could no longer skate away in a sudden breeze."
            )
        if sid == "tie_wind_line":
            return (
                "Ada and Mara stretched the twine between safe roof posts and tied firm knots. "
                "Mara pulled the line once; it answered with a quiet twang. “That is a road with rails,” Ada said."
            )
        if sid == "guide_pouch":
            return (
                "With the pouch tied to the guiding line, Ada watched the stopping point while Pip gave measured warm puffs. "
                "The pouch slid, paused, and slid again instead of flying. At the glasshouse, the invitations reached the labeled pots together."
            )
        if sid == "guide_basket":
            return (
                "Pip nudged the covered basket in short, gentle bursts. Ada watched its feet skim the safe route and called, "
                "“Stop!” whenever the basket neared an edge. It arrived in the chimney nook, where the invitations rested beneath shelter."
            )
        if sid == "hand_deliver_glasshouse":
            return (
                "The calm route was open, so Ada and Mara carried the dry invitations by hand. "
                "They walked slowly past the planters and placed each paper with the labeled pots. "
                "“No flight needed,” Mara said. “Good noticing did the traveling.”"
            )
        if sid == "hand_deliver_shelter":
            return (
                "Pip’s breath was not ready for cargo, so Ada and Mara chose the sheltered route. "
                "They carried small dry batches through the chimney nook, with Pip watching the ribbon and calling, “Gust coming!” "
                "Every invitation reached its safe resting place."
            )
        return event["summary"] + "."

    paragraphs = [
        {
            "text": rng.choice(beginning_choices),
            "event_ids": [],
            "kind": "beginning",
        }
    ]

    for index, event in enumerate(events):
        is_last = index == len(events) - 1
        text = text_for(event)
        if is_last:
            arrangement = final["invitations.arrangement"]
            if arrangement == "pots_full":
                text += " The labeled pots now held the complete invitation bundle, a bright row of proof that their careful arrangement had worked."
            else:
                text += " The complete bundle now rested in the chimney nook, safely covered in its final arrangement beneath the shelter."
        paragraphs.append({
            "text": text,
            "event_ids": [event["id"]],
            "kind": "ending" if is_last else "scene",
        })

    return paragraphs


def generate(seed, prose_seed=None):
    return realize(
        solve(build(seed), seed),
        render,
        seed if prose_seed is None else prose_seed,
    )
