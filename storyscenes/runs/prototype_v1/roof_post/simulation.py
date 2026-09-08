from runtime import WorldSpec, Scene, Condition as C, Effect as E, Rule
from runtime import observe, tell, transfer
import random


def build(seed: int) -> WorldSpec:
    rng = random.Random(seed)

    wind_strength = 2 if rng.random() < 0.55 else 1
    glasshouse_open = rng.random() < 0.68
    pouch_ready = rng.random() < 0.62
    breath_control = 2 if rng.random() < 0.55 else 1
    invitation_count = 3 if rng.random() < 0.5 else 4
    delicate_section = "herb_roof" if rng.random() < 0.5 else "glasshouse"

    entities = {
        "ada": {"name": "Ada", "kind": "child"},
        "pip": {"name": "Pip", "kind": "dragon"},
        "mara": {"name": "Mara", "kind": "keeper"},
        "roof_post": {"name": "roof post", "kind": "place"},
        "herb_roof": {"name": "herb roof", "kind": "place"},
        "glasshouse": {"name": "glasshouse roof", "kind": "place"},
        "chimney_nook": {"name": "chimney nook", "kind": "place"},
        "invitations": {"name": "garden-party invitations", "kind": "prop"},
        "pouch": {"name": "cloth pouch", "kind": "prop"},
        "basket": {"name": "light basket", "kind": "prop"},
        "twine": {"name": "twine", "kind": "prop"},
        "ribbon": {"name": "ribbon wind-marker", "kind": "prop"},
        "pots": {"name": "labeled pots", "kind": "group"},
    }

    initial = {
        "ada.location": "roof_post",
        "pip.location": "roof_post",
        "mara.location": "roof_post",

        "invitations.location": "roof_post",
        "invitations.owner": "ada",
        "invitations.count": invitation_count,
        "invitations.delivered": 0,
        "invitations.torn": False,
        "invitations.secured": False,
        "invitations.carrier": "none",
        "invitations.arrangement": "loose",

        "pouch.location": "roof_post",
        "pouch.owner": "mara",
        "pouch.condition": "ready" if pouch_ready else "repair",
        "pouch.tied": False,

        "basket.location": "roof_post",
        "basket.owner": "mara",
        "basket.loaded": False,
        "basket.covered": False,

        "twine.location": "roof_post",
        "twine.owner": "mara",
        "twine.tied": False,

        "ribbon.location": "roof_post",
        "ribbon.wind": wind_strength,

        "roof_post.route": "open",
        "herb_roof.route": "open",
        "glasshouse.route": "open" if glasshouse_open else "closed",
        "chimney_nook.route": "open",

        "pots.location": "glasshouse",
        "pots.delicate_section": delicate_section,
        "pots.display": "empty",
        "chimney_nook.display": "empty",

        "ada.memes.Ambition": 2,
        "ada.memes.Care": 1,
        "ada.memes.Curiosity": 1,
        "ada.knows.ribbon.wind": None,
        "ada.knows.invitations.torn": None,
        "ada.knows.glasshouse.route": None,

        "pip.memes.Ambition": 1,
        "pip.memes.Care": 1,
        "pip.memes.Curiosity": 1,
        "pip.breath_control": breath_control,
        "pip.puff_tested": False,
        "pip.puff_used": False,
        "pip.knows.breath_control": None,

        "mara.memes.Care": 2,
        "mara.knows.ribbon.wind": None,
        "mara.knows.glasshouse.route": "open" if glasshouse_open else "closed",
    }

    scenes = (
        observe(
            "inspect_wind",
            "ada",
            "ribbon.wind",
            requires=(
                C("ada.location", "eq", "roof_post"),
                C("ribbon.location", "eq", "roof_post"),
                C("ada.memes.Curiosity", "ge", 1),
            ),
            summary="Ada inspected the ribbon wind-marker at the roof post",
        ),
        observe(
            "inspect_paper",
            "ada",
            "invitations.torn",
            requires=(
                C("ada.location", "eq", "roof_post"),
                C("invitations.location", "eq", "roof_post"),
            ),
            summary="Ada checked that the invitation papers were intact",
        ),
        observe(
            "inspect_route",
            "ada",
            "glasshouse.route",
            requires=(
                C("ada.location", "eq", "roof_post"),
                C("glasshouse.route", "in", ("open", "closed")),
            ),
            summary="Ada checked whether the glasshouse roof route was open",
        ),
        Scene(
            "test_pip_puff",
            "observation",
            ("pip", "ribbon", "roof_post"),
            (
                C("pip.location", "eq", "roof_post"),
                C("ribbon.location", "eq", "roof_post"),
                C("pip.puff_tested", "eq", False),
                C("pip.memes.Curiosity", "ge", 1),
            ),
            (
                E("pip.puff_tested", True),
                E("pip.knows.breath_control", "pip.breath_control", "copy"),
                E("pip.memes.Curiosity", 1, "inc"),
            ),
            "Pip tested a tiny warm puff beside the ribbon",
        ),
        tell(
            "tell_mara_wind",
            "ada",
            "mara",
            "ribbon.wind",
            requires=(
                C("ada.location", "eq", "roof_post"),
                C("mara.location", "eq", "roof_post"),
            ),
            summary="Ada told Mara what the ribbon showed about the wind",
        ),
        Scene(
            "repair_pouch",
            "care",
            ("mara", "pouch", "twine"),
            (
                C("mara.location", "eq", "roof_post"),
                C("pouch.owner", "eq", "mara"),
                C("pouch.condition", "eq", "repair"),
                C("twine.owner", "eq", "mara"),
            ),
            (
                E("pouch.condition", "ready"),
                E("pouch.tied", True),
            ),
            "Mara repaired the cloth pouch with a careful twine stitch",
        ),
        transfer(
            "lend_pouch",
            "mara",
            "ada",
            "pouch",
            requires=(
                C("mara.memes.Care", "ge", 1),
                C("mara.knows.ribbon.wind", "eq", 2),
                C("pouch.condition", "eq", "ready"),
            ),
            summary="Mara lent Ada the ready cloth pouch",
        ),
        transfer(
            "lend_twine",
            "mara",
            "ada",
            "twine",
            requires=(
                C("mara.memes.Care", "ge", 1),
                C("mara.knows.ribbon.wind", "eq", 2),
            ),
            summary="Mara lent Ada twine for a guiding line",
        ),
        transfer(
            "lend_basket",
            "mara",
            "ada",
            "basket",
            requires=(
                C("mara.memes.Care", "ge", 1),
                C("ada.knows.glasshouse.route", "eq", "closed"),
            ),
            summary="Mara lent Ada the light basket for the sheltered route",
        ),
        Scene(
            "pack_pouch",
            "cooperation",
            ("ada", "pip", "pouch", "invitations"),
            (
                C("ada.location", "eq", "roof_post"),
                C("pip.location", "eq", "roof_post"),
                C("pouch.owner", "eq", "ada"),
                C("pouch.condition", "eq", "ready"),
                C("ada.knows.invitations.torn", "eq", False),
                C("invitations.secured", "eq", False),
            ),
            (
                E("pouch.tied", True),
                E("invitations.secured", True),
                E("invitations.carrier", "pouch"),
            ),
            "Ada and Pip tied the dry invitations inside the pouch",
        ),
        Scene(
            "pack_basket",
            "cooperation",
            ("ada", "pip", "basket", "invitations"),
            (
                C("ada.location", "eq", "roof_post"),
                C("pip.location", "eq", "roof_post"),
                C("basket.owner", "eq", "ada"),
                C("ada.knows.invitations.torn", "eq", False),
                C("invitations.secured", "eq", False),
            ),
            (
                E("basket.loaded", True),
                E("basket.covered", True),
                E("invitations.secured", True),
                E("invitations.carrier", "basket"),
            ),
            "Ada and Pip covered the invitations in the light basket",
        ),
        Scene(
            "tie_wind_line",
            "cooperation",
            ("ada", "mara", "twine", "roof_post"),
            (
                C("ada.location", "eq", "roof_post"),
                C("mara.location", "eq", "roof_post"),
                C("twine.owner", "eq", "ada"),
                C("mara.knows.ribbon.wind", "eq", 2),
                C("twine.tied", "eq", False),
            ),
            (E("twine.tied", True),),
            "Ada and Mara tied a guiding line between safe roof posts",
        ),
        Scene(
            "guide_pouch",
            "cooperation",
            ("ada", "pip", "pouch", "twine"),
            (
                C("ada.location", "eq", "roof_post"),
                C("pip.location", "eq", "roof_post"),
                C("ada.knows.ribbon.wind", "eq", 2),
                C("ada.knows.glasshouse.route", "eq", "open"),
                C("pip.puff_tested", "eq", True),
                C("pip.knows.breath_control", "ge", 2),
                C("twine.tied", "eq", True),
                C("pouch.tied", "eq", True),
                C("invitations.carrier", "eq", "pouch"),
                C("invitations.delivered", "eq", 0),
            ),
            (
                E("pip.puff_used", True),
                E("pouch.location", "glasshouse"),
                E("invitations.location", "glasshouse"),
                E("invitations.delivered", "invitations.count", "copy"),
                E("invitations.arrangement", "pots_full"),
                E("pots.display", "full"),
            ),
            "Pip gave the guided pouch measured warm puffs to the labeled pots",
        ),
        Scene(
            "guide_basket",
            "cooperation",
            ("ada", "pip", "basket", "chimney_nook"),
            (
                C("ada.location", "eq", "roof_post"),
                C("pip.location", "eq", "roof_post"),
                C("ada.knows.glasshouse.route", "eq", "closed"),
                C("pip.puff_tested", "eq", True),
                C("pip.knows.breath_control", "ge", 2),
                C("basket.loaded", "eq", True),
                C("basket.covered", "eq", True),
                C("invitations.carrier", "eq", "basket"),
                C("invitations.delivered", "eq", 0),
            ),
            (
                E("pip.puff_used", True),
                E("basket.location", "chimney_nook"),
                E("invitations.location", "chimney_nook"),
                E("invitations.delivered", "invitations.count", "copy"),
                E("invitations.arrangement", "nook_full"),
                E("chimney_nook.display", "full"),
            ),
            "Pip nudged the covered basket in short bursts into the chimney nook",
        ),
        Scene(
            "hand_deliver_glasshouse",
            "cooperation",
            ("ada", "mara", "invitations", "pots"),
            (
                C("ada.location", "eq", "roof_post"),
                C("mara.location", "eq", "roof_post"),
                C("ada.knows.invitations.torn", "eq", False),
                C("ada.knows.ribbon.wind", "eq", 1),
                C("ada.knows.glasshouse.route", "eq", "open"),
                C("mara.knows.glasshouse.route", "eq", "open"),
                C("invitations.secured", "eq", False),
                C("invitations.delivered", "eq", 0),
            ),
            (
                E("ada.location", "glasshouse"),
                E("mara.location", "glasshouse"),
                E("invitations.location", "glasshouse"),
                E("invitations.carrier", "hands"),
                E("invitations.delivered", "invitations.count", "copy"),
                E("invitations.arrangement", "pots_full"),
                E("pots.display", "full"),
            ),
            "Ada and Mara carried the invitations along the calm glasshouse route",
        ),
        Scene(
            "hand_deliver_shelter",
            "care",
            ("ada", "mara", "invitations", "chimney_nook"),
            (
                C("ada.location", "eq", "roof_post"),
                C("mara.location", "eq", "roof_post"),
                C("ada.knows.invitations.torn", "eq", False),
                C("ada.knows.ribbon.wind", "ne", None),
                C("mara.knows.ribbon.wind", "ne", None),
                C("ada.knows.glasshouse.route", "in", ("open", "closed")),
                C("pip.breath_control", "eq", 1),
                C("invitations.secured", "eq", False),
                C("invitations.delivered", "eq", 0),
            ),
            (
                E("ada.location", "chimney_nook"),
                E("mara.location", "chimney_nook"),
                E("invitations.location", "chimney_nook"),
                E("invitations.carrier", "hands"),
                E("invitations.delivered", "invitations.count", "copy"),
                E("invitations.arrangement", "nook_full"),
                E("chimney_nook.display", "full"),
            ),
            "Ada and Mara carried small dry batches through the sheltered chimney nook",
        ),
    )

    rules = (
        Rule(
            "delivery_never_exceeds_bundle",
            (C("invitations.delivered", "le", invitation_count),),
        ),
        Rule(
            "torn_paper_is_not_delivered",
            (C("invitations.delivered", "eq", 0),),
            (C("invitations.torn", "eq", True),),
        ),
        Rule(
            "pouch_cargo_is_tied",
            (C("pouch.tied", "eq", True),),
            (C("invitations.carrier", "eq", "pouch"),),
        ),
        Rule(
            "basket_cargo_is_covered",
            (
                C("basket.loaded", "eq", True),
                C("basket.covered", "eq", True),
            ),
            (C("invitations.carrier", "eq", "basket"),),
        ),
        Rule(
            "puffs_use_secured_cargo",
            (C("invitations.secured", "eq", True),),
            (C("pip.puff_used", "eq", True),),
        ),
        Rule(
            "pouch_has_one_owner",
            (C("pouch.owner", "in", ("ada", "mara")),),
        ),
        Rule(
            "basket_has_one_owner",
            (C("basket.owner", "in", ("ada", "mara")),),
        ),
        Rule(
            "twine_has_one_owner",
            (C("twine.owner", "in", ("ada", "mara")),),
        ),
    )

    goal = (
        C("invitations.delivered", "eq", invitation_count),
        C("invitations.arrangement", "in", ("pots_full", "nook_full")),
    )

    labels = {
        "ribbon.wind": "wind strength",
        "glasshouse.route": "glasshouse route",
        "invitations.count": "total invitations",
        "invitations.delivered": "invitations delivered",
        "invitations.carrier": "invitation carrier",
        "invitations.arrangement": "final invitation arrangement",
        "pots.display": "labeled-pot arrangement",
        "chimney_nook.display": "chimney-nook arrangement",
        "pip.breath_control": "Pip's breath control",
    }

    return WorldSpec(
        "Invitations Above the Roofs",
        entities,
        initial,
        scenes,
        goal,
        rules=rules,
        labels=labels,
    )
