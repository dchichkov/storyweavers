from runtime import WorldSpec, Scene, Condition as C, Effect as E, Rule
from runtime import observe, tell, transfer
import random


def build(seed: int) -> WorldSpec:
    rng = random.Random(seed)

    entities = {
        "ada": {"name": "Ada", "kind": "child"},
        "ben": {"name": "Ben", "kind": "child"},
        "mica": {"name": "Mica", "kind": "moth"},
        "keeper": {"name": "Garden steward", "kind": "person"},
        "night_garden": {"name": "night garden", "kind": "place"},
        "stone_path": {"name": "stone path", "kind": "place"},
        "fern_corner": {"name": "fern corner", "kind": "place"},
        "flower_bed": {"name": "flower bed", "kind": "place"},
        "bright_edge": {"name": "bright edge", "kind": "place"},
        "dark_edge": {"name": "dark edge", "kind": "place"},
        "lamp": {"name": "lamp", "kind": "prop"},
        "lamp_hook": {"name": "lamp hook", "kind": "place"},
        "low_stone": {"name": "low stone", "kind": "place"},
        "pale_cloth": {"name": "pale cloth", "kind": "prop"},
        "flower_sign": {"name": "flower sign", "kind": "prop"},
        "seed_pouch": {"name": "seed pouch", "kind": "prop"},
        "welcome_circle": {"name": "welcome circle", "kind": "place"},
    }

    starts_high = rng.choice((True, False))
    cloth_ready = rng.choice((True, False))
    chosen_landing = rng.choice(("fern", "flowers"))
    moth_start = rng.choice(("bright_edge", "dark_edge"))
    windy = rng.choice((True, False))

    initial = {
        "ada.memes.Curiosity": rng.choice((1, 2)),
        "ada.memes.Care": 1,
        "ben.memes.Ambition": rng.choice((1, 2)),
        "ben.memes.Care": rng.choice((1, 2)),
        "keeper.memes.Care": 2,

        "ada.location": "night_garden",
        "ben.location": "night_garden",
        "mica.location": moth_start,
        "mica.settled": False,
        "mica.comfort": "waiting",
        "mica.resting_place": None,

        "lamp.lit": False,
        "lamp.brightness": 0,
        "lamp.position": "hook" if starts_high else "stone",
        "lamp.shadow": "none",
        "lamp.owner": "keeper",

        "pale_cloth.owner": "keeper",
        "pale_cloth.location": "under_cloth" if cloth_ready else "folded",
        "pale_cloth.hung": False,
        "pale_cloth.flutters": windy,

        "flower_sign.owner": "keeper",
        "flower_sign.location": "flower_bed",
        "seed_pouch.owner": "keeper",

        "flower_bed.clear": chosen_landing != "flowers",
        "fern_corner.clear": chosen_landing != "fern",

        "welcome_circle.ready": False,
        "welcome_circle.landing": None,
        "welcome_circle.light_style": None,
        "welcome_circle.resting_place": None,

        "ada.knows.mica.location": None,
        "ada.knows.lamp.shadow": None,
        "ada.knows.lamp.position": None,
        "ada.knows.landing": None,
        "keeper.knows.landing": None,
    }

    rules = (
        Rule(
            "lamp_has_one_supported_position",
            (C("lamp.position", "in", ("hook", "stone")),),
        ),
        Rule(
            "hung_cloth_is_at_lamp",
            (
                C("pale_cloth.location", "eq", "lamp"),
                C("pale_cloth.owner", "eq", "ada"),
            ),
            when=(C("pale_cloth.hung", "eq", True),),
        ),
        Rule(
            "flower_welcome_has_clear_landing",
            (
                C("flower_bed.clear", "eq", True),
                C("welcome_circle.resting_place", "eq", "flower_sign"),
            ),
            when=(
                C("welcome_circle.ready", "eq", True),
                C("welcome_circle.landing", "eq", "flowers"),
            ),
        ),
        Rule(
            "fern_welcome_has_clear_landing",
            (
                C("fern_corner.clear", "eq", True),
                C("welcome_circle.resting_place", "eq", "flower_sign"),
            ),
            when=(
                C("welcome_circle.ready", "eq", True),
                C("welcome_circle.landing", "eq", "fern"),
            ),
        ),
        Rule(
            "settled_mica_has_a_safe_welcome",
            (
                C("welcome_circle.ready", "eq", True),
                C("mica.location", "eq", "welcome_circle"),
                C("mica.comfort", "eq", "safe"),
                C("mica.resting_place", "eq", "flower_sign"),
            ),
            when=(C("mica.settled", "eq", True),),
        ),
    )

    scenes = (
        Scene(
            "light_lamp",
            "ambition",
            ("ben", "lamp"),
            (
                C("ben.location", "eq", "night_garden"),
                C("ben.memes.Ambition", "ge", 1),
                C("lamp.lit", "eq", False),
            ),
            (
                E("lamp.lit", True),
                E("lamp.brightness", 2),
                E("lamp.shadow", "long"),
            ),
            "Ben lit the lamp brightly for the welcome",
        ),
        observe(
            "inspect_mica",
            "ada",
            "mica.location",
            requires=(
                C("ada.location", "eq", "night_garden"),
                C("ada.memes.Curiosity", "ge", 1),
                C("lamp.lit", "eq", True),
                C("mica.settled", "eq", False),
            ),
            summary="Ada watched the edge where Mica waited",
        ),
        observe(
            "inspect_shadow",
            "ada",
            "lamp.shadow",
            requires=(
                C("ada.location", "eq", "night_garden"),
                C("ada.memes.Curiosity", "ge", 1),
                C("lamp.lit", "eq", True),
            ),
            summary="Ada inspected the lamp's shadow",
        ),
        observe(
            "inspect_lamp_position",
            "ada",
            "lamp.position",
            requires=(
                C("ada.location", "eq", "night_garden"),
                C("ada.memes.Curiosity", "ge", 1),
                C("lamp.lit", "eq", True),
            ),
            summary="Ada checked where the lamp was standing",
        ),
        Scene(
            "find_landing",
            "observation",
            ("ada", "stone_path"),
            (
                C("ada.knows.mica.location", "in", ("bright_edge", "dark_edge")),
                C("ada.knows.lamp.shadow", "eq", "long"),
                C("ada.knows.landing", "eq", None),
            ),
            (E("ada.knows.landing", chosen_landing),),
            "Ada traced the long shadow to the clearer landing edge",
        ),
        tell(
            "explain_landing_need",
            "ada",
            "keeper",
            "landing",
            requires=(C("ada.memes.Care", "ge", 1),),
            summary="Ada explained which landing edge needed gentler light",
        ),
        transfer(
            "lend_pale_cloth",
            "keeper",
            "ada",
            "pale_cloth",
            requires=(
                C("keeper.memes.Care", "ge", 1),
                C("keeper.knows.landing", "in", ("fern", "flowers")),
                C("pale_cloth.location", "in", ("under_cloth", "folded")),
            ),
            summary="The steward lent Ada the pale cloth",
        ),
        Scene(
            "hang_pale_cloth",
            "cooperation",
            ("ada", "ben", "pale_cloth", "lamp"),
            (
                C("pale_cloth.owner", "eq", "ada"),
                C("pale_cloth.hung", "eq", False),
                C("pale_cloth.flutters", "eq", False),
                C("lamp.lit", "eq", True),
                C("lamp.brightness", "eq", 2),
                C("ben.memes.Care", "ge", 1),
            ),
            (
                E("pale_cloth.hung", True),
                E("pale_cloth.location", "lamp"),
                E("lamp.shadow", "soft"),
            ),
            "Ada and Ben hung the still cloth to soften the light",
        ),
        Scene(
            "dim_lamp",
            "care",
            ("ben", "lamp"),
            (
                C("ben.memes.Care", "ge", 1),
                C("lamp.lit", "eq", True),
                C("lamp.brightness", "eq", 2),
            ),
            (
                E("lamp.brightness", 1),
                E("lamp.shadow", "soft"),
            ),
            "Ben turned the lamp down to a quieter glow",
        ),
        Scene(
            "move_lamp_low",
            "cooperation",
            ("ada", "ben", "lamp", "low_stone"),
            (
                C("ada.knows.lamp.position", "eq", "hook"),
                C("ben.memes.Care", "ge", 1),
                C("lamp.lit", "eq", True),
                C("lamp.brightness", "eq", 2),
                C("lamp.position", "eq", "hook"),
            ),
            (
                E("lamp.position", "stone"),
                E("lamp.shadow", "short"),
            ),
            "The children moved the lamp down to the low stone",
        ),
        Scene(
            "clear_flower_landing",
            "care",
            ("ada", "ben", "flower_bed", "flower_sign"),
            (
                C("ada.knows.landing", "eq", "flowers"),
                C("ben.memes.Care", "ge", 1),
                C("flower_bed.clear", "eq", False),
                C("flower_sign.location", "eq", "flower_bed"),
            ),
            (
                E("flower_bed.clear", True),
                E("flower_sign.location", "stone_path"),
            ),
            "The children moved the sign and cleared the flower bed",
        ),
        Scene(
            "clear_fern_landing",
            "care",
            ("ada", "ben", "fern_corner", "flower_sign"),
            (
                C("ada.knows.landing", "eq", "fern"),
                C("ben.memes.Care", "ge", 1),
                C("fern_corner.clear", "eq", False),
                C("flower_sign.location", "eq", "flower_bed"),
            ),
            (
                E("fern_corner.clear", True),
                E("flower_sign.location", "stone_path"),
            ),
            "The children carried the sign aside and opened the fern corner",
        ),
        Scene(
            "mark_flower_circle",
            "cooperation",
            ("ada", "ben", "welcome_circle", "flower_sign"),
            (
                C("ada.knows.landing", "eq", "flowers"),
                C("flower_bed.clear", "eq", True),
                C("flower_sign.location", "eq", "stone_path"),
                C("lamp.shadow", "in", ("soft", "short")),
                C("welcome_circle.ready", "eq", False),
            ),
            (
                E("welcome_circle.ready", True),
                E("welcome_circle.landing", "flowers"),
                E("welcome_circle.light_style", "flower_glow"),
                E("welcome_circle.resting_place", "flower_sign"),
                E("flower_sign.location", "welcome_circle"),
            ),
            "Ada and Ben set the flower-sign welcome circle by the open bed",
        ),
        Scene(
            "mark_fern_circle",
            "cooperation",
            ("ada", "ben", "welcome_circle", "flower_sign"),
            (
                C("ada.knows.landing", "eq", "fern"),
                C("fern_corner.clear", "eq", True),
                C("flower_sign.location", "eq", "stone_path"),
                C("lamp.shadow", "in", ("soft", "short")),
                C("welcome_circle.ready", "eq", False),
            ),
            (
                E("welcome_circle.ready", True),
                E("welcome_circle.landing", "fern"),
                E("welcome_circle.light_style", "fern_edge"),
                E("welcome_circle.resting_place", "flower_sign"),
                E("flower_sign.location", "welcome_circle"),
            ),
            "Ada and Ben set the flower-sign welcome circle by the fern edge",
        ),
        Scene(
            "mica_settles",
            "care",
            ("mica", "welcome_circle", "flower_sign"),
            (
                C("mica.settled", "eq", False),
                C("welcome_circle.ready", "eq", True),
                C("welcome_circle.landing", "in", ("fern", "flowers")),
                C("welcome_circle.light_style", "in", ("flower_glow", "fern_edge")),
                C("welcome_circle.resting_place", "eq", "flower_sign"),
                C("lamp.shadow", "in", ("soft", "short")),
            ),
            (
                E("mica.settled", True),
                E("mica.location", "welcome_circle"),
                E("mica.comfort", "safe"),
                E("mica.resting_place", "flower_sign"),
            ),
            "Mica settled safely on the flower sign in the welcome circle",
        ),
    )

    goal = (
        C("mica.settled", "eq", True),
        C("mica.comfort", "eq", "safe"),
        C("welcome_circle.ready", "eq", True),
    )

    labels = {
        "lamp.position": "lamp position",
        "lamp.brightness": "lamp brightness",
        "lamp.shadow": "shadow quality",
        "pale_cloth.hung": "pale cloth hung",
        "flower_bed.clear": "flower bed clear",
        "fern_corner.clear": "fern corner clear",
        "mica.location": "Mica's location",
        "mica.settled": "Mica settled",
        "mica.resting_place": "Mica's resting place",
        "welcome_circle.ready": "welcome circle ready",
        "welcome_circle.landing": "chosen landing area",
        "welcome_circle.light_style": "welcome light arrangement",
    }

    return WorldSpec(
        "The Moonlit Welcome",
        entities,
        initial,
        scenes,
        goal,
        rules=rules,
        labels=labels,
    )
