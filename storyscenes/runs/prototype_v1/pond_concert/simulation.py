from runtime import WorldSpec, Scene, Condition as C, Effect as E, Rule
from runtime import observe, tell, transfer
import random


def build(seed: int) -> WorldSpec:
    rng = random.Random(seed)

    carrier_kind = rng.choice(("pads", "log", "sail"))
    listener_place = rng.choice(("reedbank", "dock", "root"))
    water_condition = rng.choice(("still", "rippling"))
    hearing_need = "quiet" if listener_place == "reedbank" else "vibration"

    entities = {
        "ada": {"name": "Ada", "kind": "child"},
        "milo": {"name": "Milo", "kind": "child"},
        "pip": {"name": "Pip", "kind": "frog"},
        "tansy": {"name": "Tansy", "kind": "turtle"},
        "lilypond": {"name": "Lilypond", "kind": "place"},
        "reedbank": {"name": "reed bank", "kind": "place"},
        "dock": {"name": "old dock", "kind": "place"},
        "root": {"name": "long root", "kind": "place"},
        "stage": {"name": "lily-pad stage", "kind": "prop"},
        "pads": {"name": "floating lily pads", "kind": "group"},
        "pad1": {"name": "first floating pad", "kind": "prop"},
        "pad2": {"name": "second floating pad", "kind": "prop"},
        "log": {"name": "hollow log", "kind": "prop"},
        "sail": {"name": "leaf sail", "kind": "prop"},
        "rope": {"name": "rope", "kind": "prop"},
        "reeds": {"name": "basket of soft reeds", "kind": "prop"},
        "water": {"name": "pond water", "kind": "feature"},
        "carrier": {"name": "available floating carrier", "kind": "feature"},
        "music": {"name": "Pip's music", "kind": "feature"},
        "concert": {"name": "pond concert", "kind": "event"},
    }

    initial = {
        "ada.location": "reedbank",
        "milo.location": "reedbank",
        "pip.location": "stage",
        "tansy.location": listener_place,
        "stage.location": "lilypond",
        "pad1.location": "lilypond",
        "pad2.location": "lilypond",
        "log.location": "lilypond",
        "sail.location": "lilypond",
        "rope.location": "lilypond",
        "reeds.location": "reedbank",
        "pads.linked": False,
        "log.anchored": False,
        "sail.displayed": False,
        "reeds.dampening": False,
        "rope.owner": "pip",
        "reeds.owner": "lilypond",
        "water.condition": water_condition,
        "carrier.kind": carrier_kind,
        "music.style": "croak",
        "tansy.hears": hearing_need,
        "tansy.tested": False,
        "tansy.response": False,
        "concert.arranged": False,
        "concert.route": "none",
        "concert.performed": False,
        "concert.success": False,
        "pip.memes.Ambition": 1,
        "pip.memes.Care": 1,
        "ada.memes.Curiosity": 1,
        "ada.memes.Care": 1,
        "milo.memes.Curiosity": 1,
        "milo.memes.Care": 1,
        "ada.knows.tansy.hears": None,
        "ada.knows.water.condition": None,
        "milo.knows.carrier.kind": None,
        "pip.knows.water.condition": None,
    }

    scenes = (
        Scene(
            "walk_to_tansy",
            "observation",
            ("ada", "lilypond"),
            (
                C("ada.location", "eq", "reedbank"),
                C("tansy.location", "ne", "reedbank"),
            ),
            (E("ada.location", listener_place),),
            "Ada walked along the pond edge to Tansy's listening place.",
        ),
        observe(
            "inspect_tansy",
            "ada",
            "tansy.hears",
            requires=(
                C("ada.location", "eq", listener_place),
                C("ada.memes.Curiosity", "ge", 1),
            ),
            summary="Ada watched how Tansy listened beside the pond.",
        ),
        observe(
            "inspect_water",
            "ada",
            "water.condition",
            requires=(
                C("ada.location", "eq", "reedbank"),
                C("ada.memes.Curiosity", "ge", 1),
            ),
            summary="Ada checked whether the pond water was still or rippling.",
        ),
        observe(
            "inspect_carrier",
            "milo",
            "carrier.kind",
            requires=(
                C("milo.location", "eq", "reedbank"),
                C("milo.memes.Curiosity", "ge", 1),
            ),
            summary="Milo inspected the floating things available for the concert.",
        ),
        transfer(
            "lend_rope",
            "pip",
            "milo",
            "rope",
            requires=(
                C("pip.memes.Care", "ge", 1),
                C("rope.owner", "eq", "pip"),
            ),
            summary="Pip lent Milo the rope for a careful pond arrangement.",
        ),
        Scene(
            "link_pads",
            "cooperation",
            ("ada", "milo", "pads", "rope"),
            (
                C("milo.knows.carrier.kind", "eq", "pads"),
                C("ada.knows.tansy.hears", "eq", "vibration"),
                C("rope.owner", "eq", "milo"),
                C("pads.linked", "eq", False),
            ),
            (
                E("pads.linked", True),
                E("concert.arranged", True),
                E("concert.route", "pads"),
            ),
            "Ada and Milo tied the floating pads into a gentle vibration bridge.",
        ),
        Scene(
            "anchor_log",
            "cooperation",
            ("ada", "milo", "log", "rope"),
            (
                C("milo.knows.carrier.kind", "eq", "log"),
                C("ada.knows.tansy.hears", "eq", "vibration"),
                C("rope.owner", "eq", "milo"),
                C("log.anchored", "eq", False),
            ),
            (
                E("log.anchored", True),
                E("log.location", listener_place),
                E("concert.arranged", True),
                E("concert.route", "log"),
            ),
            "Ada and Milo anchored the hollow log beside Tansy's listening place.",
        ),
        Scene(
            "raise_sail",
            "cooperation",
            ("ada", "milo", "sail"),
            (
                C("milo.knows.carrier.kind", "eq", "sail"),
                C("ada.knows.water.condition", "eq", "rippling"),
                C("sail.displayed", "eq", False),
            ),
            (
                E("sail.displayed", True),
                E("sail.location", "reedbank"),
                E("concert.arranged", True),
                E("concert.route", "sail"),
            ),
            "Ada and Milo raised the leaf sail where its signals could be seen.",
        ),
        Scene(
            "place_soft_reeds",
            "care",
            ("ada", "reeds", "lilypond"),
            (
                C("ada.knows.tansy.hears", "eq", "quiet"),
                C("reeds.owner", "eq", "lilypond"),
                C("reeds.dampening", "eq", False),
            ),
            (
                E("reeds.dampening", True),
                E("reeds.location", "reedbank"),
                E("concert.arranged", True),
                E("concert.route", "reeds"),
            ),
            "Ada placed soft reeds to hush the splashy side of the pond.",
        ),
        Scene(
            "float_stage_near_tansy",
            "cooperation",
            ("ada", "milo", "stage"),
            (
                C("ada.knows.tansy.hears", "eq", "vibration"),
                C("ada.knows.water.condition", "eq", "still"),
                C("stage.location", "eq", "lilypond"),
            ),
            (
                E("stage.location", listener_place),
                E("concert.arranged", True),
                E("concert.route", "stage"),
            ),
            "Ada and Milo floated Pip's stage closer to Tansy's steady listening place.",
        ),
        Scene(
            "tansy_tests_arrangement",
            "observation",
            ("tansy", "concert"),
            (
                C("concert.arranged", "eq", True),
                C("concert.route", "ne", "none"),
                C("tansy.tested", "eq", False),
            ),
            (
                E("tansy.tested", True),
                E("tansy.response", True),
            ),
            "Tansy tested the new arrangement with one patient rhythmic foot tap.",
        ),
        tell(
            "tell_pip_about_water",
            "ada",
            "pip",
            "water.condition",
            requires=(),
            summary="Ada told Pip what the water would do to his music.",
        ),
        Scene(
            "choose_tapping",
            "adaptation",
            ("pip", "music", "water"),
            (
                C("pip.knows.water.condition", "eq", "rippling"),
                C("tansy.tested", "eq", True),
                C("pip.memes.Ambition", "ge", 1),
                C("music.style", "ne", "tap"),
            ),
            (E("music.style", "tap"),),
            "Pip changed his big croaks into clear, gentle tapping rhythms.",
        ),
        Scene(
            "choose_call_and_response",
            "adaptation",
            ("pip", "music", "water"),
            (
                C("pip.knows.water.condition", "eq", "still"),
                C("tansy.tested", "eq", True),
                C("pip.memes.Ambition", "ge", 1),
                C("music.style", "ne", "call"),
            ),
            (E("music.style", "call"),),
            "Pip chose a patient call-and-response tune for the still pond.",
        ),
        Scene(
            "perform_tapping_concert",
            "accomplishment",
            ("pip", "tansy", "concert", "music"),
            (
                C("concert.arranged", "eq", True),
                C("tansy.tested", "eq", True),
                C("tansy.response", "eq", True),
                C("water.condition", "eq", "rippling"),
                C("music.style", "eq", "tap"),
            ),
            (
                E("concert.performed", True),
                E("concert.success", True),
            ),
            "Pip performed a tapping concert that traveled kindly across the ripples.",
        ),
        Scene(
            "perform_call_concert",
            "accomplishment",
            ("pip", "tansy", "concert", "music"),
            (
                C("concert.arranged", "eq", True),
                C("tansy.tested", "eq", True),
                C("tansy.response", "eq", True),
                C("water.condition", "eq", "still"),
                C("music.style", "eq", "call"),
            ),
            (
                E("concert.performed", True),
                E("concert.success", True),
            ),
            "Pip performed a call-and-response concert over the still pond.",
        ),
    )

    rules = (
        Rule(
            "an_arrangement_has_a_route",
            (C("concert.route", "ne", "none"),),
            (C("concert.arranged", "eq", True),),
        ),
        Rule(
            "pad_route_needs_linked_pads",
            (
                C("pads.linked", "eq", True),
                C("concert.arranged", "eq", True),
            ),
            (C("concert.route", "eq", "pads"),),
        ),
        Rule(
            "log_route_needs_anchored_log",
            (
                C("log.anchored", "eq", True),
                C("concert.arranged", "eq", True),
            ),
            (C("concert.route", "eq", "log"),),
        ),
        Rule(
            "sail_route_needs_sail",
            (
                C("sail.displayed", "eq", True),
                C("concert.arranged", "eq", True),
            ),
            (C("concert.route", "eq", "sail"),),
        ),
        Rule(
            "reed_route_needs_dampening",
            (
                C("reeds.dampening", "eq", True),
                C("concert.arranged", "eq", True),
            ),
            (C("concert.route", "eq", "reeds"),),
        ),
        Rule(
            "stage_route_moves_stage",
            (
                C("stage.location", "eq", listener_place),
                C("concert.arranged", "eq", True),
            ),
            (C("concert.route", "eq", "stage"),),
        ),
        Rule(
            "success_requires_tansys_test",
            (
                C("concert.performed", "eq", True),
                C("tansy.tested", "eq", True),
                C("tansy.response", "eq", True),
            ),
            (C("concert.success", "eq", True),),
        ),
    )

    goal = (
        C("concert.performed", "eq", True),
        C("concert.success", "eq", True),
        C("tansy.response", "eq", True),
    )

    labels = {
        "pads.linked": "linked floating-pad bridge",
        "log.anchored": "anchored hollow log",
        "sail.displayed": "raised leaf sail",
        "reeds.dampening": "soft reeds damping splashes",
        "stage.location": "lily-pad stage location",
        "concert.route": "concert arrangement",
        "concert.success": "successful pond concert",
        "tansy.response": "Tansy's rhythmic response",
        "music.style": "Pip's chosen music style",
    }

    return WorldSpec(
        "The Pond Concert: Many Ways to Listen",
        entities,
        initial,
        scenes,
        goal,
        rules=rules,
        labels=labels,
    )
