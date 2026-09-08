import random

from runtime import WorldSpec, Scene, Condition as C, Effect as E, Rule
from runtime import observe, tell, transfer


def build(seed: int) -> WorldSpec:
    rng = random.Random(seed)

    solution = rng.choice(("alcove", "rope", "bench"))
    bell_stuck = rng.choice((True, False))
    starting_confidence = rng.choice((1, 2))

    if solution == "alcove":
        wind_strength = "gusty"
        alcove_sheltered = True
        fastener_enough = False
        bench_blocks_breeze = False
        goal = (
            C("stage.location", "eq", "alcove"),
            C("show.style", "eq", "sheltered"),
            C("show.performed", "eq", True),
        )
    elif solution == "rope":
        wind_strength = "lively"
        alcove_sheltered = False
        fastener_enough = True
        bench_blocks_breeze = False
        goal = (
            C("curtain.secured", "eq", True),
            C("show.style", "eq", "windy"),
            C("show.performed", "eq", True),
        )
    else:
        wind_strength = "blustery"
        alcove_sheltered = False
        fastener_enough = False
        bench_blocks_breeze = True
        goal = (
            C("bench.location", "eq", "windbreak"),
            C("show.style", "eq", "windbreak"),
            C("show.performed", "eq", True),
        )

    entities = {
        "ada": {"name": "Ada", "kind": "child"},
        "pip": {"name": "Pip", "kind": "child"},
        "mara": {"name": "Mara", "kind": "keeper"},
        "courtyard": {"name": "Sunny Courtyard", "kind": "place"},
        "alcove": {"name": "Sheltered Alcove", "kind": "place"},
        "windbreak": {"name": "Bench Windbreak", "kind": "place"},
        "stage": {"name": "Puppet Stage", "kind": "stage"},
        "curtain": {"name": "Blue Wind Curtain", "kind": "prop"},
        "sun": {"name": "Sun Puppet", "kind": "puppet"},
        "cloud": {"name": "Cloud Puppet", "kind": "puppet"},
        "bell": {"name": "Little Bell", "kind": "prop"},
        "rope": {"name": "Coiled Rope", "kind": "prop"},
        "pins": {"name": "Clothespins", "kind": "prop"},
        "bench": {"name": "Movable Bench", "kind": "prop"},
        "wind": {"name": "Courtyard Breeze", "kind": "weather"},
        "show": {"name": "Weather Show", "kind": "event"},
    }

    initial = {
        "ada.location": "courtyard",
        "ada.memes.Curiosity": 2,
        "ada.memes.Ambition": 2,
        "ada.knows.wind.strength": None,
        "ada.knows.alcove.sheltered": None,
        "ada.knows.curtain.fastener_enough": None,
        "ada.knows.bench.blocks_breeze": None,
        "ada.knows.bell.stuck": None,
        "ada.knows.cloud.safe_in_wind": None,
        "pip.location": "courtyard",
        "pip.confidence": starting_confidence,
        "pip.memes.Care": 1,
        "pip.knows.cloud.safe_in_wind": True,
        "mara.location": "courtyard",
        "mara.memes.Care": 2,
        "mara.knows.wind.strength": None,
        "alcove.sheltered": alcove_sheltered,
        "wind.strength": wind_strength,
        "stage.location": "courtyard",
        "curtain.location": "stage",
        "curtain.secured": False,
        "curtain.fastener_enough": fastener_enough,
        "sun.owner": "pip",
        "sun.location": "stage",
        "cloud.owner": "pip",
        "cloud.location": "stage",
        "cloud.safe_in_wind": True,
        "bell.location": "stage",
        "bell.stuck": bell_stuck,
        "rope.owner": "mara",
        "rope.location": "courtyard",
        "pins.location": "stage",
        "bench.location": "courtyard",
        "bench.blocks_breeze": bench_blocks_breeze,
        "show.signal_ready": False,
        "show.signal": "none",
        "show.performed": False,
        "show.style": "none",
    }

    scenes = (
        observe(
            "survey_breeze",
            "ada",
            "wind.strength",
            requires=(
                C("ada.location", "eq", "courtyard"),
                C("ada.memes.Curiosity", "ge", 1),
            ),
            summary="Ada watched the curtain and judged the strength of the breeze",
        ),
        tell(
            "tell_mara_about_breeze",
            "ada",
            "mara",
            "wind.strength",
            requires=(
                C("ada.location", "eq", "courtyard"),
                C("mara.location", "eq", "courtyard"),
            ),
            summary="Ada told Mara what the breeze was doing",
        ),
        tell(
            "pip_names_the_sturdy_puppet",
            "pip",
            "ada",
            "cloud.safe_in_wind",
            requires=(
                C("pip.location", "eq", "courtyard"),
                C("ada.location", "eq", "courtyard"),
            ),
            summary="Pip explained that the cloud puppet could manage a breeze",
        ),
        Scene(
            "practice_behind_the_stage",
            "cooperation",
            ("ada", "pip", "stage"),
            (
                C("ada.knows.cloud.safe_in_wind", "eq", True),
                C("pip.confidence", "lt", 2),
                C("stage.location", "eq", "courtyard"),
            ),
            (
                E("pip.confidence", 1, "inc"),
            ),
            "Ada and Pip practiced one short cloud-puppet line behind the stage",
            weight=1.4,
        ),
        observe(
            "inspect_alcove",
            "ada",
            "alcove.sheltered",
            requires=(
                C("ada.location", "eq", "courtyard"),
                C("ada.knows.wind.strength", "eq", "gusty"),
            ),
            summary="Ada checked whether the alcove was truly sheltered",
        ),
        observe(
            "test_one_clothespin",
            "ada",
            "curtain.fastener_enough",
            requires=(
                C("ada.location", "eq", "courtyard"),
                C("ada.knows.wind.strength", "eq", "lively"),
                C("pins.location", "eq", "stage"),
                C("curtain.location", "eq", "stage"),
            ),
            summary="Ada tested whether a careful fastening plan would hold the curtain",
        ),
        observe(
            "inspect_bench_position",
            "ada",
            "bench.blocks_breeze",
            requires=(
                C("ada.location", "eq", "courtyard"),
                C("ada.knows.wind.strength", "eq", "blustery"),
                C("bench.location", "eq", "courtyard"),
            ),
            summary="Ada checked how the bench could turn the breeze aside",
        ),
        transfer(
            "borrow_rope",
            "mara",
            "ada",
            "rope",
            requires=(
                C("mara.memes.Care", "ge", 1),
                C("mara.knows.wind.strength", "eq", "lively"),
            ),
            summary="Mara lent Ada the rope for the curtain",
        ),
        Scene(
            "fasten_curtain_with_rope",
            "cooperation",
            ("ada", "mara", "curtain", "rope", "pins"),
            (
                C("rope.owner", "eq", "ada"),
                C("ada.knows.curtain.fastener_enough", "eq", True),
                C("mara.knows.wind.strength", "eq", "lively"),
                C("curtain.secured", "eq", False),
            ),
            (
                E("curtain.secured", True),
                E("rope.location", "stage"),
            ),
            "Ada and Mara tied the curtain with rope and clothespins",
            weight=1.5,
        ),
        Scene(
            "move_bench_as_windbreak",
            "cooperation",
            ("ada", "mara", "bench"),
            (
                C("ada.knows.bench.blocks_breeze", "eq", True),
                C("mara.knows.wind.strength", "eq", "blustery"),
                C("bench.location", "eq", "courtyard"),
            ),
            (
                E("bench.location", "windbreak"),
            ),
            "Ada and Mara moved the bench into a useful windbreak",
            weight=1.5,
        ),
        Scene(
            "shift_stage_to_alcove",
            "care",
            ("ada", "pip", "mara", "stage"),
            (
                C("ada.knows.alcove.sheltered", "eq", True),
                C("mara.knows.wind.strength", "eq", "gusty"),
                C("stage.location", "eq", "courtyard"),
                C("ada.location", "eq", "courtyard"),
                C("pip.location", "eq", "courtyard"),
                C("mara.location", "eq", "courtyard"),
            ),
            (
                E("stage.location", "alcove"),
                E("curtain.location", "alcove"),
                E("sun.location", "alcove"),
                E("cloud.location", "alcove"),
                E("bell.location", "alcove"),
                E("ada.location", "alcove"),
                E("pip.location", "alcove"),
                E("mara.location", "alcove"),
            ),
            "The group carried the small stage and its props into the alcove",
            weight=1.5,
        ),
        observe(
            "inspect_bell",
            "ada",
            "bell.stuck",
            requires=(
                C("ada.memes.Curiosity", "ge", 1),
                C("bell.location", "in", ("stage", "alcove")),
            ),
            summary="Ada inspected the bell before choosing an opening cue",
        ),
        Scene(
            "use_spoken_opening_cue",
            "adaptation",
            ("ada", "pip", "stage"),
            (
                C("ada.knows.bell.stuck", "eq", True),
                C("show.signal_ready", "eq", False),
            ),
            (
                E("show.signal_ready", True),
                E("show.signal", "spoken"),
            ),
            "Ada changed the opening signal to Pip's clear spoken cue",
            weight=1.3,
        ),
        Scene(
            "ring_ready_bell",
            "observation",
            ("ada", "bell"),
            (
                C("ada.knows.bell.stuck", "eq", False),
                C("bell.stuck", "eq", False),
                C("show.signal_ready", "eq", False),
            ),
            (
                E("show.signal_ready", True),
                E("show.signal", "bell"),
            ),
            "Ada chose the working bell as the opening signal",
            weight=1.3,
        ),
        Scene(
            "perform_sheltered_show",
            "cooperation",
            ("ada", "pip", "mara", "stage", "cloud"),
            (
                C("stage.location", "eq", "alcove"),
                C("ada.knows.cloud.safe_in_wind", "eq", True),
                C("pip.confidence", "ge", 2),
                C("show.signal_ready", "eq", True),
                C("show.performed", "eq", False),
            ),
            (
                E("show.performed", True),
                E("show.style", "sheltered"),
            ),
            "Pip performed the weather play beside the sheltered stage",
            weight=2.0,
        ),
        Scene(
            "perform_windy_show",
            "ambition",
            ("ada", "pip", "mara", "stage", "cloud", "curtain"),
            (
                C("stage.location", "eq", "courtyard"),
                C("curtain.secured", "eq", True),
                C("ada.knows.cloud.safe_in_wind", "eq", True),
                C("pip.confidence", "ge", 2),
                C("show.signal_ready", "eq", True),
                C("show.performed", "eq", False),
            ),
            (
                E("show.performed", True),
                E("show.style", "windy"),
            ),
            "Pip gave the cloud puppet a dramatic breezy entrance in the courtyard",
            weight=2.0,
        ),
        Scene(
            "perform_windbreak_show",
            "cooperation",
            ("ada", "pip", "mara", "stage", "cloud", "bench"),
            (
                C("stage.location", "eq", "courtyard"),
                C("bench.location", "eq", "windbreak"),
                C("ada.knows.cloud.safe_in_wind", "eq", True),
                C("pip.confidence", "ge", 2),
                C("show.signal_ready", "eq", True),
                C("show.performed", "eq", False),
            ),
            (
                E("show.performed", True),
                E("show.style", "windbreak"),
            ),
            "Pip performed the weather play behind the bench windbreak",
            weight=2.0,
        ),
    )

    rules = (
        Rule(
            "stage_stays_in_a_real_place",
            (C("stage.location", "in", ("courtyard", "alcove")),),
        ),
        Rule(
            "rope_has_one_of_its_known_caretakers",
            (C("rope.owner", "in", ("mara", "ada")),),
        ),
        Rule(
            "sheltered_style_matches_sheltered_stage",
            (C("stage.location", "eq", "alcove"),),
            (C("show.style", "eq", "sheltered"),),
        ),
        Rule(
            "windy_style_has_a_fastened_curtain",
            (C("curtain.secured", "eq", True),),
            (C("show.style", "eq", "windy"),),
        ),
        Rule(
            "windbreak_style_has_the_bench_in_place",
            (C("bench.location", "eq", "windbreak"),),
            (C("show.style", "eq", "windbreak"),),
        ),
        Rule(
            "performed_show_has_a_signal_and_a_ready_puppeteer",
            (
                C("show.signal_ready", "eq", True),
                C("pip.confidence", "ge", 2),
            ),
            (C("show.performed", "eq", True),),
        ),
    )

    labels = {
        "wind.strength": "breeze strength",
        "curtain.secured": "curtain fastened",
        "bench.location": "bench position",
        "stage.location": "stage position",
        "bell.stuck": "bell clapper stuck",
        "show.signal": "opening signal",
        "show.style": "performance arrangement",
        "show.performed": "weather show performed",
        "pip.confidence": "Pip's confidence",
    }

    return WorldSpec(
        "The Courtyard Weather Show",
        entities,
        initial,
        scenes,
        goal,
        rules=rules,
        labels=labels,
    )
