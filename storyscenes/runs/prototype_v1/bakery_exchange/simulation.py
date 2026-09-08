from runtime import WorldSpec, Scene, Condition as C, Effect as E, Rule
from runtime import observe, tell, transfer
import random


def build(seed: int) -> WorldSpec:
    rng = random.Random(seed)

    label_state = rng.choice(("correct", "swapped", "missing"))
    noor_need = rng.choice(("plain", "berry"))
    tool = rng.choice(("plate", "scale"))
    generous = rng.choice((True, False))
    pip_priority = rng.choice(("ownership", "promise", "taste"))

    label_present = label_state != "missing"
    label_accurate = label_state == "correct"

    entities = {
        "ada": {"name": "Ada", "kind": "child"},
        "pip": {"name": "Pip", "kind": "animal"},
        "noor": {"name": "Noor", "kind": "person"},
        "mara": {"name": "Mara", "kind": "keeper"},
        "stall": {"name": "sunny market stall", "kind": "place"},
        "tray": {"name": "baking tray", "kind": "prop"},
        "basket": {"name": "shared basket", "kind": "prop"},
        "label": {"name": "paper label", "kind": "prop"},
        "plate": {"name": "tasting plate", "kind": "prop"},
        "scale": {"name": "small scale", "kind": "prop"},
        "nut": {"name": "nut bun", "kind": "prop"},
        "berry": {"name": "berry bun", "kind": "prop"},
        "plain": {"name": "plain bun", "kind": "prop"},
        "exchange": {"name": "market exchange", "kind": "arrangement"},
    }

    initial = {
        "ada.location": "stall",
        "pip.location": "stall",
        "noor.location": "stall",
        "mara.location": "stall",
        "tray.location": "stall",
        "basket.location": "stall",
        "label.location": "tray",
        "plate.location": "stall",
        "scale.location": "stall",
        "nut.location": "tray",
        "berry.location": "tray",
        "plain.location": "tray",

        "nut.owner": "mara",
        "berry.owner": "mara",
        "plain.owner": "mara",
        "label.owner": "mara",

        "nut.filling": "nut",
        "berry.filling": "berry",
        "plain.filling": "plain",
        "label.present": label_present,
        "label.accurate": label_accurate,
        "plate.available": tool == "plate",
        "scale.available": tool == "scale",

        "mara.generous": generous,
        "mara.evidence_seen": False,
        "mara.memes.Care": 1,
        "mara.knows.label.accurate": None,

        "ada.memes.Curiosity": 1,
        "ada.memes.Care": 1,
        "ada.memes.Ambition": 1,
        "ada.evidence_ready": False,
        "ada.knows.label.accurate": None,
        "ada.knows.berry.filling": None,
        "ada.knows.noor.need": None,

        "pip.memes.Pride": 2,
        "pip.priority": pip_priority,
        "pip.claimed": False,
        "pip.satisfied": False,

        "noor.hungry": True,
        "noor.need": noor_need,
        "noor.received": None,

        "stall.display": "confusing",
        "exchange.success": False,
        "exchange.fair": False,
    }

    scenes = (
        Scene(
            "inspect_label",
            "observation",
            ("ada", "label", "tray"),
            (
                C("ada.location", "eq", "stall"),
                C("label.location", "eq", "tray"),
                C("label.present", "eq", True),
                C("ada.memes.Curiosity", "ge", 1),
            ),
            (
                E("ada.knows.label.accurate", "label.accurate", "copy"),
                E("ada.evidence_ready", True),
                E("ada.memes.Curiosity", 1, "inc"),
            ),
            "Ada inspected the label beside the tray",
        ),
        Scene(
            "taste_berry_crumb",
            "observation",
            ("ada", "berry", "plate"),
            (
                C("ada.location", "eq", "stall"),
                C("berry.location", "eq", "tray"),
                C("plate.location", "eq", "stall"),
                C("plate.available", "eq", True),
                C("ada.memes.Curiosity", "ge", 1),
            ),
            (
                E("ada.knows.berry.filling", "berry.filling", "copy"),
                E("ada.evidence_ready", True),
                E("ada.memes.Curiosity", 1, "inc"),
            ),
            "Ada sampled one careful crumb on the tasting plate",
        ),
        Scene(
            "weigh_buns",
            "observation",
            ("ada", "scale", "tray"),
            (
                C("ada.location", "eq", "stall"),
                C("scale.location", "eq", "stall"),
                C("scale.available", "eq", True),
                C("ada.memes.Curiosity", "ge", 1),
            ),
            (
                E("ada.knows.berry.filling", "berry.filling", "copy"),
                E("ada.evidence_ready", True),
                E("ada.memes.Ambition", 1, "inc"),
            ),
            "Ada compared the bun shapes and weights on the small scale",
        ),
        Scene(
            "ask_noor",
            "care",
            ("ada", "noor", "stall"),
            (
                C("ada.location", "eq", "stall"),
                C("noor.location", "eq", "stall"),
                C("noor.hungry", "eq", True),
            ),
            (
                E("ada.knows.noor.need", "noor.need", "copy"),
                E("ada.memes.Care", 1, "inc"),
            ),
            "Ada asked Noor which filling would be gentle and filling",
        ),
        tell(
            "tell_mara_label",
            "ada",
            "mara",
            "label.accurate",
            requires=(
                C("ada.knows.label.accurate", "ne", None),
                C("ada.location", "eq", "stall"),
                C("mara.location", "eq", "stall"),
            ),
            summary="Ada told Mara what the tray label seemed to say",
        ),
        Scene(
            "show_mara_evidence",
            "communication",
            ("ada", "mara", "tray"),
            (
                C("ada.location", "eq", "stall"),
                C("mara.location", "eq", "stall"),
                C("ada.evidence_ready", "eq", True),
                C("ada.knows.noor.need", "ne", None),
            ),
            (
                E("mara.evidence_seen", True),
                E("ada.memes.Ambition", 1, "inc"),
            ),
            "Ada showed Mara the careful evidence before suggesting a share",
        ),
        Scene(
            "pip_claims_saved_nut",
            "pride",
            ("pip", "nut", "tray"),
            (
                C("pip.location", "eq", "stall"),
                C("nut.location", "eq", "tray"),
                C("nut.owner", "eq", "mara"),
                C("pip.priority", "in", ("ownership", "promise")),
                C("pip.memes.Pride", "ge", 1),
            ),
            (
                E("pip.claimed", True),
                E("pip.memes.Pride", 1, "inc"),
            ),
            "Pip proudly reminded everyone about his saved nut bun",
        ),
        Scene(
            "pip_chooses_nut",
            "cooperation",
            ("pip", "mara", "nut"),
            (
                C("pip.location", "eq", "stall"),
                C("mara.location", "eq", "stall"),
                C("pip.priority", "eq", "taste"),
                C("nut.owner", "eq", "mara"),
            ),
            (
                E("nut.owner", "pip"),
                E("pip.satisfied", True),
            ),
            "Pip chose the nut bun he liked best",
        ),
        Scene(
            "reserve_claimed_nut",
            "cooperation",
            ("pip", "mara", "nut"),
            (
                C("pip.claimed", "eq", True),
                C("nut.owner", "eq", "mara"),
                C("mara.location", "eq", "stall"),
            ),
            (
                E("nut.owner", "pip"),
                E("pip.claimed", False),
                E("pip.satisfied", True),
            ),
            "Mara reserved Pip's promised nut bun for him",
        ),
        Scene(
            "grant_generous_permission",
            "cooperation",
            ("mara", "ada", "basket"),
            (
                C("mara.generous", "eq", True),
                C("mara.evidence_seen", "eq", True),
                C("ada.knows.noor.need", "ne", None),
                C("basket.location", "eq", "stall"),
            ),
            (
                E("ada.memes.Care", 1, "inc"),
                E("ada.memes.Ambition", 1, "inc"),
            ),
            "Mara welcomed Ada's careful plan for the shared basket",
        ),
        Scene(
            "grant_cautious_permission",
            "cooperation",
            ("mara", "ada", "tray"),
            (
                C("mara.generous", "eq", False),
                C("mara.evidence_seen", "eq", True),
                C("ada.knows.noor.need", "ne", None),
                C("ada.memes.Care", "ge", 2),
            ),
            (
                E("ada.memes.Ambition", 1, "inc"),
            ),
            "Cautious Mara agreed after Ada explained whom the bun would help",
        ),
        Scene(
            "give_plain_bun",
            "care",
            ("ada", "noor", "plain", "basket"),
            (
                C("ada.knows.noor.need", "eq", "plain"),
                C("noor.need", "eq", "plain"),
                C("plain.owner", "eq", "mara"),
                C("plain.location", "eq", "tray"),
                C("mara.evidence_seen", "eq", True),
            ),
            (
                E("plain.owner", "noor"),
                E("plain.location", "basket"),
                E("noor.hungry", False),
                E("noor.received", "plain"),
                E("exchange.success", True),
                E("exchange.fair", True),
            ),
            "Ada placed the plain bun in Noor's portion of the basket",
        ),
        Scene(
            "give_berry_bun",
            "care",
            ("ada", "noor", "berry", "basket"),
            (
                C("ada.knows.noor.need", "eq", "berry"),
                C("noor.need", "eq", "berry"),
                C("berry.owner", "eq", "mara"),
                C("berry.location", "eq", "tray"),
                C("mara.evidence_seen", "eq", True),
            ),
            (
                E("berry.owner", "noor"),
                E("berry.location", "basket"),
                E("noor.hungry", False),
                E("noor.received", "berry"),
                E("exchange.success", True),
                E("exchange.fair", True),
            ),
            "Ada placed the berry bun in Noor's portion of the basket",
        ),
        Scene(
            "display_checked_labels",
            "arrangement",
            ("ada", "mara", "label", "tray"),
            (
                C("label.present", "eq", True),
                C("mara.evidence_seen", "eq", True),
                C("exchange.success", "eq", True),
                C("pip.satisfied", "eq", True),
            ),
            (
                E("label.accurate", True),
                E("stall.display", "clear"),
            ),
            "Ada and Mara set out a checked, accurate label beside the tray",
        ),
        Scene(
            "make_new_label_from_sample",
            "arrangement",
            ("ada", "mara", "label", "tray"),
            (
                C("label.present", "eq", False),
                C("ada.knows.berry.filling", "eq", "berry"),
                C("mara.evidence_seen", "eq", True),
                C("exchange.success", "eq", True),
                C("pip.satisfied", "eq", True),
            ),
            (
                E("label.present", True),
                E("label.accurate", True),
                E("stall.display", "clear"),
            ),
            "Ada and Mara made a new accurate label from the checked bun",
        ),
        transfer(
            "lend_spare_label",
            "mara",
            "ada",
            "label",
            requires=(
                C("mara.memes.Care", "ge", 1),
                C("mara.location", "eq", "stall"),
                C("ada.location", "eq", "stall"),
            ),
            summary="Mara lent Ada the spare paper label",
        ),
    )

    rules = (
        Rule(
            "bun_owners_are_people",
            (
                C("nut.owner", "in", ("mara", "ada", "pip", "noor")),
                C("berry.owner", "in", ("mara", "ada", "pip", "noor")),
                C("plain.owner", "in", ("mara", "ada", "pip", "noor")),
            ),
        ),
        Rule(
            "plain_need_gets_plain_bun",
            (
                C("noor.received", "eq", "plain"),
                C("plain.owner", "eq", "noor"),
            ),
            when=(
                C("noor.hungry", "eq", False),
                C("noor.need", "eq", "plain"),
            ),
        ),
        Rule(
            "berry_need_gets_berry_bun",
            (
                C("noor.received", "eq", "berry"),
                C("berry.owner", "eq", "noor"),
            ),
            when=(
                C("noor.hungry", "eq", False),
                C("noor.need", "eq", "berry"),
            ),
        ),
        Rule(
            "clear_display_has_true_label",
            (
                C("label.present", "eq", True),
                C("label.accurate", "eq", True),
            ),
            when=(C("stall.display", "eq", "clear"),),
        ),
        Rule(
            "successful_exchange_feeds_noor",
            (C("noor.hungry", "eq", False),),
            when=(C("exchange.success", "eq", True),),
        ),
    )

    goal = (
        C("exchange.success", "eq", True),
        C("exchange.fair", "eq", True),
        C("pip.satisfied", "eq", True),
        C("stall.display", "eq", "clear"),
    )

    labels = {
        "ada.memes.Curiosity": "Ada's curiosity",
        "ada.memes.Care": "Ada's care",
        "ada.memes.Ambition": "Ada's determination",
        "noor.hungry": "Noor is hungry",
        "noor.received": "Noor's bun",
        "pip.satisfied": "Pip's saved-bun wish is respected",
        "exchange.success": "successful sharing",
        "exchange.fair": "fair arrangement",
        "stall.display": "stall display",
        "label.accurate": "label matches the buns",
    }

    return WorldSpec(
        "The Crumb-and-Label Exchange",
        entities,
        initial,
        scenes,
        goal,
        rules=rules,
        labels=labels,
    )
