from simulation import build
from runtime import solve, realize


def render(run, rng):
    initial = run["initial"]
    final = run["final"]
    events = run["events"]

    borrowed = initial["museum.borrowed_id"]
    borrowed_name = run["entities"][borrowed]["name"]
    request = initial["owner_elsie.request"]
    condition = initial[borrowed + ".condition"]
    mark = initial[borrowed + ".mark"]

    openings = [
        (
            "At the quiet end of the town museum, Ada and Bo were preparing "
            "the Museum of Small Things. A borrowed "
            + borrowed_name
            + " rested among old objects, carrying a story too small to shout "
            "and too interesting to ignore. Pip the magpie clicked from a shelf. "
            '"Let\'s make people look closely," Bo said. '
            'Ada smiled. "Closely—and respectfully."'
        ),
        (
            "The gallery was peaceful except for Pip's bright little clicks and "
            "Bo's grand whispering. Ada had found a borrowed "
            + borrowed_name
            + " for the new exhibit, while an old key and other overlooked "
            "treasures waited nearby. "
            '"A centerpiece!" Bo announced. '
            '"A carefully understood centerpiece," Ada corrected. '
            'Mara, the keeper, tapped the empty case. '
            '"That difference matters."'
        ),
    ]

    paragraphs = [{
        "text": rng.choice(openings),
        "event_ids": [],
        "kind": "beginning",
    }]

    def text_for(event):
        scene = event["scene"]

        if scene == "inspect_borrowed_object":
            return (
                "Ada examined the borrowed "
                + borrowed_name
                + " without picking it up. She noticed that its condition "
                + condition
                + ". "
                '"It has been looked after," she said, '
                '"so we must keep looking after it."'
            )

        if scene == "pip_notices_mark":
            return (
                "Pip hopped nearer and spotted a tiny "
                + mark
                + " on the "
                + borrowed_name
                + ". He gave a careful chirp and pointed with one glossy wing "
                "instead of grabbing. "
                '"Even the smallest mark can be a clue," Bo said.'
            )

        if scene == "pip_shares_mark":
            return (
                "Pip showed Ada the mark he had found on the "
                + borrowed_name
                + ". Ada listened to his chirps and studied the place he indicated. "
                '"We can describe what we know," she said, '
                '"but we must not invent the rest."'
            )

        if scene == "read_owner_letter":
            return (
                "At the worktable, Mara opened Elsie's letter and read it aloud "
                "with Ada. Elsie's request was clear: she wanted the object to be "
                + request
                + ". "
                '"So the owner gets a say, even when our idea is exciting?" '
                "Bo asked. "
                '"Especially then," Mara replied.'
            )

        if scene == "test_display_case":
            return (
                "Bo tested the display case while Mara watched its shelves and "
                "corners. He discovered that the case was "
                + initial["display_case.space"]
                + ". "
                '"My dramatic arrangement may be dramatically crowded," he admitted. '
                '"A good display leaves room for objects and eyes," Mara said.'
            )

        if scene == "clear_case_space":
            return (
                "With Ada and Pip helping, Bo removed extra objects from the "
                "crowded case and returned them to the gallery. The shelves gained "
                "breathing room. "
                '"It is less busy," Bo said, looking again. '
                '"That means the important thing can finally speak."'
            )

        if scene == "lend_velvet_pad":
            return (
                "Mara lent Ada the velvet pad. Ada accepted it with both hands and "
                "set it beside the case. "
                '"This is not decoration," Mara explained. '
                '"It keeps a borrowed object from being scraped." '
                '"A soft promise," Ada said.'
            )

        if scene == "lend_lamp":
            return (
                "Mara lent Bo the small lamp. He carried it slowly, keeping its "
                "cord clear of the case. "
                '"Light can help people notice," Bo said. '
                '"Yes," Mara replied, "but aim it like a question, not a shout."'
            )

        if scene == "prepare_padded_display":
            return (
                "Ada placed the "
                + borrowed_name
                + " on the velvet pad while Bo watched the edges and empty space. "
                "Nothing scraped or wobbled. The borrowed treasure became the "
                "focus of the case without being squeezed among its neighbors. "
                '"Now it looks important because we cared for it," Bo whispered.'
            )

        if scene == "prepare_lit_display":
            return (
                "Bo aimed the small lamp, and Ada carefully placed the "
                + borrowed_name
                + " in the roomy case. The light caught its surface without "
                "glare. Pip tilted his head. "
                '"Not flashy," Ada said. "Just enough for the mark to be seen."'
            )

        if scene == "prepare_key_exhibit":
            return (
                "Because Elsie wanted her borrowed treasure home, the team changed "
                "the centerpiece. They set the worn old key in the roomy case and "
                "turned its locksmith mark outward. Bo stared at the space where "
                "the borrowed object might have gone. "
                '"An absence can tell part of a story too," Ada said.'
            )

        if scene == "return_borrowed_object":
            return (
                "Mara and Ada placed the borrowed "
                + borrowed_name
                + " in the returning box. They carried it carefully toward the "
                "courtyard, where it could go back to Elsie. "
                '"Returning it is not giving up," Bo said. '
                '"No," Ada answered. "It is finishing the borrowing properly."'
            )

        if scene == "write_accurate_label":
            return (
                "Ada and Bo wrote the label only after Ada had learned the "
                + borrowed_name
                + "'s mark and Elsie's request. They named the mark and explained "
                "the owner's wish instead of pretending the museum owned everything "
                "it displayed. "
                '"Accurate—and kind," Mara said when she read it.'
            )

        if scene == "stabilize_arrangement":
            return (
                "Bo checked the arrangement from several angles while Ada held the "
                "case steady. The centerpiece had space, the label was clear, and "
                "nothing leaned against anything fragile. He gave the shelf a tiny "
                "test. It stayed still. "
                '"Stable," he announced. "My favorite kind of impressive."'
            )

        if scene == "open_small_things_exhibit":
            if final["museum.resolution"] == "displayed":
                return (
                    "Mara opened the Museum of Small Things. The case stood ready: "
                    "labeled, balanced, and honest about the borrowed treasure. "
                    "The small mark caught the lamp as the first visitors leaned "
                    "close. "
                    '"Look closely," Ada invited, "but please do not touch."'
                )
            return (
                "Mara opened the Museum of Small Things. The old key held the "
                "center of the balanced case, while the label explained that a "
                "borrowed treasure had been returned to its owner. "
                '"Look closely," Ada invited. "The empty space is part of the story."'
            )

        return event["summary"] + "."

    for event in events:
        paragraphs.append({
            "text": text_for(event),
            "event_ids": [event["id"]],
            "kind": "scene",
        })

    if final["museum.resolution"] == "displayed":
        ending = (
            "By closing time, the borrowed "
            + borrowed_name
            + " rested safely in the case. Its little mark glimmered beside an "
            "accurate label, and visitors bent close without touching. Bo's grand "
            "plan had become something better: an exhibit that made room for "
            "another person's treasure and voice."
        )
    else:
        ending = (
            "By closing time, Elsie's "
            + borrowed_name
            + " was safely on its way home in the returning box. The old key "
            "held the center of the open case, and the label told visitors why "
            "the empty space mattered. Ada looked at the arrangement and smiled: "
            "the exhibit displayed not just an object, but a promise kept."
        )

    paragraphs.append({
        "text": ending,
        "event_ids": [events[-1]["id"]],
        "kind": "ending",
    })
    return paragraphs


def generate(seed, prose_seed=None):
    return realize(
        solve(build(seed), seed),
        render,
        seed if prose_seed is None else prose_seed,
    )
