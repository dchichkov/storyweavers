from runtime import WorldSpec, Scene, Condition as C, Effect as E, Rule
from runtime import observe, tell, transfer
import random


def build(seed: int) -> WorldSpec:
    rng = random.Random(seed)

    borrowed = rng.choice(("borrowed_button", "tin_whistle", "cracked_marble"))
    request = rng.choice(("display", "pad", "return"))
    needed_tool = "pad" if request == "pad" else rng.choice(("lamp", "pad"))
    space = rng.choice(("roomy", "crowded"))
    mark = rng.choice(("maker_mark", "family_mark"))

    condition_key = borrowed + ".condition"
    mark_key = borrowed + ".mark"
    ada_condition = "ada.knows." + borrowed + ".condition"
    ada_mark = "ada.knows." + borrowed + ".mark"
    pip_mark = "pip.knows." + borrowed + ".mark"
    ada_request = "ada.knows.owner_elsie.request"

    entities = {
        "ada": {"name": "Ada", "kind": "child"},
        "bo": {"name": "Bo", "kind": "child"},
        "pip": {"name": "Pip", "kind": "magpie"},
        "mara": {"name": "Mara", "kind": "keeper"},
        "owner_elsie": {"name": "Elsie", "kind": "owner"},
        "museum": {"name": "town museum", "kind": "place"},
        "museum_gallery": {"name": "museum gallery", "kind": "place"},
        "worktable": {"name": "worktable", "kind": "place"},
        "display_case": {"name": "display case", "kind": "place"},
        "courtyard": {"name": "courtyard", "kind": "place"},
        "borrowed_button": {"name": "borrowed button", "kind": "prop"},
        "old_key": {"name": "old key", "kind": "prop"},
        "cracked_marble": {"name": "cracked marble", "kind": "prop"},
        "tin_whistle": {"name": "tin whistle", "kind": "prop"},
        "label_cards": {"name": "label cards", "kind": "prop"},
        "velvet_pad": {"name": "velvet pad", "kind": "prop"},
        "lamp": {"name": "small lamp", "kind": "prop"},
        "returning_box": {"name": "returning box", "kind": "prop"},
        "owner_letter": {"name": "owner letter", "kind": "prop"},
    }

    initial = {
        "ada.location": "museum_gallery",
        "bo.location": "museum_gallery",
        "pip.location": "museum_gallery",
        "mara.location": "museum_gallery",
        "owner_elsie.location": "courtyard",

        "ada.memes.Curiosity": 2,
        "ada.memes.Care": 1,
        "bo.memes.Craft": 2,
        "bo.memes.Curiosity": 1,
        "pip.memes.Curiosity": 2,
        "mara.memes.Care": rng.randint(1, 2),

        ada_condition: None,
        ada_mark: None,
        pip_mark: None,
        ada_request: None,
        "bo.knows.display_case.space": None,
        "mara.knows.owner_elsie.request": None,

        "borrowed_button.location": "museum_gallery",
        "old_key.location": "museum_gallery",
        "cracked_marble.location": "museum_gallery",
        "tin_whistle.location": "museum_gallery",
        "borrowed_button.owner": "owner_elsie" if borrowed == "borrowed_button" else "museum",
        "old_key.owner": "museum",
        "cracked_marble.owner": "owner_elsie" if borrowed == "cracked_marble" else "museum",
        "tin_whistle.owner": "owner_elsie" if borrowed == "tin_whistle" else "museum",

        "borrowed_button.condition": "sound",
        "old_key.condition": "worn",
        "cracked_marble.condition": "cracked",
        "tin_whistle.condition": "sound",
        "borrowed_button.mark": mark if borrowed == "borrowed_button" else "thread_mark",
        "old_key.mark": "locksmith_mark",
        "cracked_marble.mark": mark if borrowed == "cracked_marble" else "quarry_mark",
        "tin_whistle.mark": mark if borrowed == "tin_whistle" else "music_mark",

        "owner_elsie.request": request,
        "owner_elsie.approved": False,
        "owner_letter.location": "worktable",

        "velvet_pad.owner": "mara",
        "lamp.owner": "mara",
        "returning_box.owner": "mara",
        "velvet_pad.location": "museum_gallery",
        "lamp.location": "museum_gallery",
        "returning_box.location": "museum_gallery",
        "label_cards.location": "worktable",

        "display_case.space": space,
        "display_case.focus": "none",
        "display_case.stable": False,
        "display_case.open": False,
        "display_case.label_accurate": False,
        "display_case.borrowed_displayed": False,
        "display_case.pad_used": False,
        "display_case.lamp_used": False,

        "museum.borrowed_id": borrowed,
        "museum.needed_tool": needed_tool,
        "museum.resolution": "none",
        "museum.open": False,
    }

    scenes = [
        observe(
            "inspect_borrowed_object",
            "ada",
            condition_key,
            requires=(
                C("ada.location", "eq", "museum_gallery"),
                C(borrowed + ".location", "eq", "museum_gallery"),
                C("ada.memes.Curiosity", "ge", 1),
            ),
            summary="Ada inspected the borrowed object's condition",
        ),
        observe(
            "pip_notices_mark",
            "pip",
            mark_key,
            requires=(
                C("pip.location", "eq", "museum_gallery"),
                C(borrowed + ".location", "eq", "museum_gallery"),
                C("pip.memes.Curiosity", "ge", 1),
            ),
            summary="Pip noticed the small mark on the borrowed object",
        ),
        tell(
            "pip_shares_mark",
            "pip",
            "ada",
            mark_key,
            requires=(
                C("ada.location", "eq", "museum_gallery"),
                C("pip.location", "eq", "museum_gallery"),
            ),
            summary="Pip showed Ada the mark he had found",
        ),
        Scene(
            "read_owner_letter",
            "care",
            ("mara", "ada", "owner_letter"),
            (
                C("mara.location", "eq", "museum_gallery"),
                C("ada.location", "eq", "museum_gallery"),
                C("owner_letter.location", "eq", "worktable"),
            ),
            (
                E("mara.knows.owner_elsie.request", "owner_elsie.request", "copy"),
                E(ada_request, "owner_elsie.request", "copy"),
                E("owner_elsie.approved", True),
            ),
            "Mara read Elsie's request aloud with Ada",
            1.0,
            1,
        ),
        Scene(
            "test_display_case",
            "observation",
            ("bo", "mara", "display_case"),
            (
                C("bo.location", "eq", "museum_gallery"),
                C("mara.location", "eq", "museum_gallery"),
            ),
            (
                E("bo.knows.display_case.space", "display_case.space", "copy"),
                E("bo.memes.Craft", 1, "inc"),
            ),
            "Bo tested how much room the display case had",
            1.0,
            1,
        ),
        Scene(
            "clear_case_space",
            "cooperation",
            ("ada", "bo", "pip", "display_case"),
            (
                C("ada.location", "eq", "museum_gallery"),
                C("bo.location", "eq", "museum_gallery"),
                C("pip.location", "eq", "museum_gallery"),
                C("bo.knows.display_case.space", "eq", "crowded"),
                C(ada_condition, "ne", None),
            ),
            (
                E("display_case.space", "roomy"),
                E("bo.memes.Craft", 1, "inc"),
            ),
            "The children removed extra objects to give the case breathing room",
            1.0,
            1,
        ),
        transfer(
            "lend_velvet_pad",
            "mara",
            "ada",
            "velvet_pad",
            requires=(
                C("mara.memes.Care", "ge", 1),
                C("velvet_pad.location", "eq", "museum_gallery"),
            ),
            summary="Mara lent Ada a velvet pad for careful handling",
        ),
        transfer(
            "lend_lamp",
            "mara",
            "bo",
            "lamp",
            requires=(
                C("mara.memes.Care", "ge", 1),
                C("lamp.location", "eq", "museum_gallery"),
            ),
            summary="Mara lent Bo a small lamp for the display",
        ),
        Scene(
            "prepare_padded_display",
            "care",
            ("ada", "bo", "display_case", "velvet_pad"),
            (
                C(ada_request, "in", ("display", "pad")),
                C("museum.needed_tool", "eq", "pad"),
                C("owner_elsie.approved", "eq", True),
                C(ada_condition, "ne", None),
                C("display_case.space", "eq", "roomy"),
                C("velvet_pad.owner", "eq", "ada"),
            ),
            (
                E("display_case.focus", borrowed),
                E("display_case.borrowed_displayed", True),
                E("display_case.pad_used", True),
                E(borrowed + ".location", "display_case"),
                E("museum.resolution", "displayed"),
            ),
            "Ada and Bo set the borrowed treasure on its velvet pad",
            1.0,
            1,
        ),
        Scene(
            "prepare_lit_display",
            "care",
            ("ada", "bo", "display_case", "lamp"),
            (
                C(ada_request, "eq", "display"),
                C("museum.needed_tool", "eq", "lamp"),
                C("owner_elsie.approved", "eq", True),
                C(ada_condition, "ne", None),
                C("display_case.space", "eq", "roomy"),
                C("lamp.owner", "eq", "bo"),
            ),
            (
                E("display_case.focus", borrowed),
                E("display_case.borrowed_displayed", True),
                E("display_case.lamp_used", True),
                E(borrowed + ".location", "display_case"),
                E("museum.resolution", "displayed"),
            ),
            "Bo aimed the lamp while Ada placed the borrowed treasure safely",
            1.0,
            1,
        ),
        Scene(
            "prepare_key_exhibit",
            "cooperation",
            ("ada", "bo", "pip", "old_key", "display_case"),
            (
                C(ada_request, "eq", "return"),
                C(ada_condition, "ne", None),
                C("display_case.space", "eq", "roomy"),
                C("old_key.location", "eq", "museum_gallery"),
            ),
            (
                E("display_case.focus", "old_key"),
                E("old_key.location", "display_case"),
            ),
            "The team made the worn old key the exhibit's new centerpiece",
            1.0,
            1,
        ),
        Scene(
            "return_borrowed_object",
            "care",
            ("ada", "mara", "returning_box"),
            (
                C(ada_request, "eq", "return"),
                C("display_case.focus", "eq", "old_key"),
                C("returning_box.location", "eq", "museum_gallery"),
                C(borrowed + ".location", "eq", "museum_gallery"),
            ),
            (
                E(borrowed + ".location", "courtyard"),
                E("returning_box.location", "courtyard"),
                E("museum.resolution", "returned"),
            ),
            "Mara and Ada packed the borrowed object safely to return to Elsie",
            1.0,
            1,
        ),
        Scene(
            "write_accurate_label",
            "craft",
            ("ada", "bo", "label_cards"),
            (
                C(ada_mark, "ne", None),
                C(ada_request, "ne", None),
                C("display_case.focus", "ne", "none"),
            ),
            (
                E("display_case.label_accurate", True),
                E("label_cards.location", "display_case"),
            ),
            "Ada and Bo wrote a label that named the mark and Elsie's wishes",
            1.0,
            1,
        ),
        Scene(
            "stabilize_arrangement",
            "craft",
            ("bo", "ada", "display_case"),
            (
                C("display_case.focus", "ne", "none"),
                C("display_case.label_accurate", "eq", True),
                C("display_case.space", "eq", "roomy"),
                C("museum.resolution", "in", ("displayed", "returned")),
            ),
            (E("display_case.stable", True),),
            "Bo checked the arrangement while Ada held the case steady",
            1.0,
            1,
        ),
        Scene(
            "open_small_things_exhibit",
            "cooperation",
            ("mara", "ada", "bo", "display_case"),
            (
                C("display_case.label_accurate", "eq", True),
                C("display_case.stable", "eq", True),
                C("museum.resolution", "in", ("displayed", "returned")),
            ),
            (
                E("display_case.open", True),
                E("museum.open", True),
            ),
            "Mara opened the Museum of Small Things exhibit",
            1.0,
            1,
        ),
    ]

    rules = (
        Rule(
            "borrowed_items_need_permission",
            (C("display_case.borrowed_displayed", "eq", False),),
            (C("owner_elsie.approved", "eq", False),),
        ),
        Rule(
            "returned_items_are_not_displayed",
            (C("display_case.borrowed_displayed", "eq", False),),
            (C("owner_elsie.request", "eq", "return"),),
        ),
        Rule(
            "displayed_item_stays_in_case",
            (C(borrowed + ".location", "eq", "display_case"),),
            (C("display_case.borrowed_displayed", "eq", True),),
        ),
        Rule(
            "returned_item_reaches_courtyard",
            (C(borrowed + ".location", "eq", "courtyard"),),
            (C("museum.resolution", "eq", "returned"),),
        ),
        Rule(
            "museum_opens_only_with_a_stable_labelled_case",
            (
                C("display_case.stable", "eq", True),
                C("display_case.label_accurate", "eq", True),
            ),
            (C("museum.open", "eq", True),),
        ),
        Rule(
            "open_case_requires_a_respectful_resolution",
            (C("museum.resolution", "in", ("displayed", "returned")),),
            (C("display_case.open", "eq", True),),
        ),
    )

    goal = (
        C("museum.open", "eq", True),
        C("display_case.open", "eq", True),
        C("display_case.stable", "eq", True),
        C("display_case.label_accurate", "eq", True),
        C("museum.resolution", "in", ("displayed", "returned")),
    )

    labels = {
        "museum.borrowed_id": "borrowed object",
        "museum.needed_tool": "needed display tool",
        "museum.resolution": "respectful resolution",
        "museum.open": "museum exhibit open",
        "display_case.focus": "exhibit centerpiece",
        "display_case.borrowed_displayed": "borrowed object displayed",
        "display_case.label_accurate": "accurate exhibit label",
        "display_case.stable": "stable arrangement",
        "display_case.open": "display case open",
        "display_case.pad_used": "velvet pad used",
        "display_case.lamp_used": "lamp used",
    }

    return WorldSpec(
        "The Museum of Small Things",
        entities,
        initial,
        scenes,
        goal,
        rules=rules,
        labels=labels,
    )
