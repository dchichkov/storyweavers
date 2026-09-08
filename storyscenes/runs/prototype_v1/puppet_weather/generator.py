from simulation import build
from runtime import solve, realize


def render(run, rng):
    events = run["events"]
    entities = run["entities"]

    def name(entity_id):
        return entities.get(entity_id, {}).get("name", entity_id)

    opening_choices = (
        "Ada had promised a weather show in the sunny courtyard, and she meant it to be grand. Pip held the puppets close, while Mara watched the curtains flutter.",
        "The little puppet stage stood ready in the courtyard. Ada wanted a spectacular weather show, Pip knew the puppets best, and Mara knew every useful corner of the place.",
    )
    paragraphs = [{
        "text": rng.choice(opening_choices),
        "event_ids": [],
        "kind": "beginning",
    }]

    descriptions = {
        "survey_breeze": (
            "Ada narrowed her eyes at the curtain. She watched its pull, listened to the rush of air, and announced, "
            "\"This breeze is stronger than it looks.\""
        ),
        "inspect_bell": (
            "Before anyone counted on the opening bell, Ada lifted it and gave it a careful look. "
            "She found the clapper's trouble and said, \"Now we know what it can—and cannot—do.\""
        ),
        "tell_mara_about_breeze": (
            "Ada hurried to Mara with her news. \"The breeze is lively,\" she said, or, \"It is gusty!\" "
            "Mara nodded. \"Good noticing. Now we can choose something sturdy.\""
        ),
        "pip_names_the_sturdy_puppet": (
            "Pip peeped from behind the stage. \"The cloud puppet can manage the moving air,\" Pip explained. "
            "\"Its wide cloth catches the breeze without being pulled apart.\" Ada listened carefully."
        ),
        "practice_behind_the_stage": (
            "Ada and Pip practiced a single line behind the stage. Pip lifted the cloud puppet and whispered, "
            "\"I am a cloud sailing over the town!\" Ada answered, \"Louder, captain cloud.\" Pip tried again, and the line rang out bravely."
        ),
        "inspect_alcove": (
            "Ada tested the alcove with a strip of curtain cloth. Inside, it barely trembled. "
            "\"This is genuinely sheltered,\" she reported, changing her grand courtyard idea into a safer one."
        ),
        "test_one_clothespin": (
            "Ada clipped one clothespin to the curtain and watched. It held—or did not hold—just as the breeze tugged. "
            "She did not guess; she tested. Then she gave Mara the useful result."
        ),
        "inspect_bench_position": (
            "Ada walked around the bench and watched the air curl past it. "
            "\"Placed this way, it turns the breeze aside,\" she said. Mara rubbed her hands, ready to help move it."
        ),
        "borrow_rope": (
            "Mara loosened the rope from its coil and placed it in Ada's hands. "
            "\"Use it carefully and bring it back after the show,\" she said. Ada promised, and the rope changed helpers."
        ),
        "fasten_curtain_with_rope": (
            "Ada and Mara tied the curtain firmly, adding the clothespins where they mattered. "
            "The rope stretched from its coil to the stage, and the curtain stayed put when the breeze tugged."
        ),
        "move_bench_as_windbreak": (
            "Ada and Mara heaved the bench across the courtyard. They set it where the tested angle mattered, "
            "making a broad little windbreak instead of pretending the breeze had vanished."
        ),
        "shift_stage_to_alcove": (
            "Together, Ada, Pip, and Mara carried the stage and its props into the alcove. "
            "The sun, cloud, bell, and curtain followed, and the whole group stepped into the calmer pocket of air."
        ),
        "use_spoken_opening_cue": (
            "Ada tapped the silent bell, then smiled at Pip. \"You be the signal. Say, 'Weather begins!'\" "
            "Pip took a breath and practiced the words until they sounded clear."
        ),
        "ring_ready_bell": (
            "Ada tested the bell once more. This time its bright ring answered the courtyard. "
            "\"That is our cue,\" she said, and Mara grinned at the perfectly ordinary, useful sound."
        ),
        "perform_sheltered_show": (
            "At the sheltered stage, Pip lifted the cloud puppet. The spoken cue—or the ready signal—began the play, "
            "and Pip performed with a steady voice while the curtain rested neatly nearby."
        ),
        "perform_windy_show": (
            "The signal sounded, and Pip sent the cloud puppet sweeping into the lively air. "
            "The secured curtain held while the puppet's entrance danced with the breeze. Ada's grand idea had become a real, workable weather trick."
        ),
        "perform_windbreak_show": (
            "Behind the bench windbreak, Pip raised the cloud puppet and began. The air still moved beyond the bench, "
            "but the stage stayed useful, and every line reached the watching courtyard."
        ),
    }

    for index, event in enumerate(events):
        scene_id = event["scene"]
        text = descriptions.get(scene_id, event["summary"] + ".")
        if index == len(events) - 1:
            final = run["final"]
            style = final.get("show.style")
            if style == "sheltered":
                ending = "When the last line ended, the alcove held the stage snugly, and the folded curtain rested without a flutter."
            elif style == "windy":
                ending = "When the last line ended, the rope and clothespins still held fast, while the cloud puppet bobbed proudly in the living breeze."
            elif style == "windbreak":
                ending = "When the last line ended, the bench remained in its windbreak place, proof that a careful arrangement could make room for a show."
            else:
                ending = "When the last line ended, the finished arrangement showed exactly how the children had solved the courtyard's problem."
            text = text + " " + ending
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
