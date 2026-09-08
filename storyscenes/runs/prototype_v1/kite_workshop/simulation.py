from runtime import WorldSpec, Scene, Condition as C, Effect as E, Rule
from runtime import observe, transfer
import random


def build(seed: int) -> WorldSpec:
    rng = random.Random(seed)

    wind_pattern = rng.choice(("gentle", "gusty"))
    defect = rng.choice(("frame", "knot", "tail", "sound"))
    bulky_note = rng.choice((True, False))
    scarce_materials = rng.choice((True, False))
    breath_control = rng.choice(("unpracticed", "ready"))

    entities = {
        "mina": {"name": "Mina", "kind": "child"},
        "brindle": {"name": "Brindle", "kind": "young dragon"},
        "orra": {"name": "Orra", "kind": "workshop keeper"},
        "workshop": {"name": "rooftop workshop", "kind": "place"},
        "platform": {"name": "launch platform", "kind": "place"},
        "basket": {"name": "marked basket", "kind": "place"},
        "wind": {"name": "rooftop wind", "kind": "weather"},
        "kite": {"name": "paper kite", "kind": "prop"},
        "tube": {"name": "message tube", "kind": "prop"},
        "note": {"name": "small note", "kind": "prop"},
        "rope": {"name": "tether rope", "kind": "prop"},
        "repair_kit": {"name": "repair kit", "kind": "prop"},
        "ribbon": {"name": "wind ribbon", "kind": "prop"},
        "wind_sock": {"name": "wind sock", "kind": "prop"},
    }

    initial = {
        "mina.location": "workshop",
        "brindle.location": "workshop",
        "orra.location": "workshop",
        "kite.location": "workshop",
        "tube.location": "workshop",
        "note.location": "workshop",
        "rope.location": "workshop",
        "repair_kit.location": "workshop",
        "ribbon.location": "workshop",
        "wind_sock.location": "workshop",
        "basket.location": "workshop",

        "wind.pattern": wind_pattern,

        "kite.defect": defect,
        "kite.balanced": defect == "sound",
        "kite.route": None,
        "kite.launched": False,
        "kite.stable": False,
        "kite.delivered": False,

        "note.bulky": bulky_note,
        "note.prepared": False,
        "note.secured": False,
        "note.carrier": None,
        "note.delivered": False,

        "tube.contains": None,
        "tube.attachment": None,
        "tube.location": "workshop",
        "tube.ready": False,

        "rope.owner": "orra",
        "repair_kit.owner": "orra" if scarce_materials else "mina",

        "brindle.breath_control": breath_control,
        "brindle.memes.Ambition": 2,
        "brindle.memes.Care": 1,
        "brindle.memes.Curiosity": 2,
        "mina.memes.Care": 2,
        "mina.memes.Curiosity": 2,
        "orra.memes.Care": 2,

        "mina.knows.kite.defect": None,
        "brindle.knows.wind.pattern": None,
        "brindle.knows.breath.practice": False,

        "basket.received": False,
        "orra.confirmed": False,
    }

    scenes = [
        observe(
            "inspect_kite",
            "mina",
            "kite.defect",
            requires=(
                C("mina.location", "eq", "workshop"),
                C("mina.memes.Curiosity", "ge", 1),
            ),
            summary="Mina inspected the kite for the trouble spot",
        ),
        observe(
            "read_wind",
            "brindle",
            "wind.pattern",
            requires=(
                C("brindle.location", "eq", "workshop"),
                C("brindle.memes.Curiosity", "ge", 1),
            ),
            summary="Brindle watched the wind sock and ribbon",
        ),
        Scene(
            "borrow_repair_kit",
            "cooperation",
            ("mina", "orra"),
            (
                C("repair_kit.owner", "eq", "orra"),
                C("mina.knows.kite.defect", "not_in", (None, "sound")),
                C("orra.memes.Care", "ge", 1),
            ),
            (
                E("repair_kit.owner", "mina"),
            ),
            "Orra lent Mina the repair kit after hearing what she found",
        ),
        transfer(
            "lend_tether_rope",
            "orra",
            "mina",
            "rope",
            requires=(
                C("mina.location", "eq", "workshop"),
                C("orra.location", "eq", "workshop"),
                C("mina.memes.Care", "ge", 1),
                C("orra.memes.Care", "ge", 1),
            ),
            summary="Orra lent Mina the short tether rope",
        ),
        Scene(
            "straighten_frame",
            "repair",
            ("mina",),
            (
                C("mina.knows.kite.defect", "eq", "frame"),
                C("kite.defect", "eq", "frame"),
                C("repair_kit.owner", "eq", "mina"),
            ),
            (
                E("kite.defect", "sound"),
                E("kite.balanced", True),
            ),
            "Mina straightened the bowed frame with the repair kit",
        ),
        Scene(
            "secure_knot",
            "repair",
            ("mina", "brindle"),
            (
                C("mina.knows.kite.defect", "eq", "knot"),
                C("kite.defect", "eq", "knot"),
                C("repair_kit.owner", "eq", "mina"),
            ),
            (
                E("kite.defect", "sound"),
                E("kite.balanced", True),
            ),
            "Mina and Brindle tightened the loose knot carefully",
        ),
        Scene(
            "lengthen_tail",
            "repair",
            ("mina",),
            (
                C("mina.knows.kite.defect", "eq", "tail"),
                C("kite.defect", "eq", "tail"),
                C("repair_kit.owner", "eq", "mina"),
            ),
            (
                E("kite.defect", "sound"),
                E("kite.balanced", True),
            ),
            "Mina added a longer tail from the repair kit",
        ),
        Scene(
            "prepare_message",
            "preparation",
            ("mina",),
            (
                C("note.prepared", "eq", False),
                C("note.location", "eq", "workshop"),
            ),
            (
                E("note.bulky", False),
                E("note.prepared", True),
                E("tube.contains", "note"),
            ),
            "Mina rolled the note into the little message tube",
        ),
        Scene(
            "practice_breath",
            "experiment",
            ("brindle",),
            (
                C("brindle.breath_control", "eq", "unpracticed"),
                C("brindle.knows.wind.pattern", "eq", "gentle"),
                C("brindle.memes.Care", "ge", 1),
            ),
            (
                E("brindle.breath_control", "ready"),
                E("brindle.knows.breath.practice", True),
            ),
            "Brindle practiced a small puff against the ribbon",
        ),
        Scene(
            "choose_high_route",
            "planning",
            ("mina", "brindle"),
            (
                C("brindle.knows.wind.pattern", "eq", "gentle"),
                C("kite.balanced", "eq", True),
            ),
            (
                E("kite.route", "high"),
            ),
            "Mina and Brindle chose the high kite route in gentle wind",
        ),
        Scene(
            "choose_low_route",
            "planning",
            ("mina", "brindle"),
            (
                C("brindle.knows.wind.pattern", "eq", "gusty"),
                C("rope.owner", "eq", "mina"),
            ),
            (
                E("kite.route", "low"),
                E("tube.ready", True),
            ),
            "Mina chose a low tether route instead of risking the kite",
        ),
        Scene(
            "attach_message",
            "cooperation",
            ("mina", "brindle"),
            (
                C("note.prepared", "eq", True),
                C("tube.contains", "eq", "note"),
                C("kite.route", "in", ("high", "low")),
            ),
            (
                E("note.secured", True),
                E("note.carrier", "tube"),
                E("tube.attachment", "secured"),
            ),
            "Mina and Brindle secured the message tube for its route",
        ),
        Scene(
            "launch_high_kite",
            "launch",
            ("mina", "brindle"),
            (
                C("kite.route", "eq", "high"),
                C("kite.balanced", "eq", True),
                C("note.secured", "eq", True),
                C("brindle.breath_control", "eq", "ready"),
            ),
            (
                E("kite.location", "platform"),
                E("kite.launched", True),
                E("kite.stable", True),
                E("tube.ready", True),
            ),
            "Brindle gave the balanced kite one measured launch puff",
        ),
        Scene(
            "send_high_message",
            "delivery",
            ("mina", "brindle"),
            (
                C("kite.route", "eq", "high"),
                C("kite.launched", "eq", True),
                C("kite.stable", "eq", True),
                C("tube.ready", "eq", True),
                C("note.secured", "eq", True),
            ),
            (
                E("kite.location", "basket"),
                E("kite.delivered", True),
                E("tube.location", "basket"),
                E("note.delivered", True),
                E("basket.received", True),
            ),
            "The high kite carried the tube to the marked basket",
        ),
        Scene(
            "send_low_message",
            "delivery",
            ("mina", "brindle"),
            (
                C("kite.route", "eq", "low"),
                C("rope.owner", "eq", "mina"),
                C("tube.ready", "eq", True),
                C("note.secured", "eq", True),
            ),
            (
                E("tube.location", "basket"),
                E("note.delivered", True),
                E("basket.received", True),
            ),
            "The tether guided the message tube safely to the marked basket",
        ),
        Scene(
            "confirm_receipt",
            "communication",
            ("orra",),
            (
                C("orra.location", "eq", "workshop"),
                C("basket.received", "eq", True),
                C("note.delivered", "eq", True),
                C("tube.location", "eq", "basket"),
            ),
            (
                E("orra.confirmed", True),
            ),
            "Orra checked the marked basket and confirmed the message",
        ),
    ]

    rules = (
        Rule(
            "delivery_keeps_note_secured",
            (
                C("note.secured", "eq", True),
                C("tube.location", "eq", "basket"),
            ),
            (
                C("note.delivered", "eq", True),
            ),
        ),
        Rule(
            "received_means_delivered",
            (
                C("note.delivered", "eq", True),
            ),
            (
                C("basket.received", "eq", True),
            ),
        ),
        Rule(
            "high_kite_needs_safe_launch",
            (
                C("kite.route", "eq", "high"),
                C("kite.stable", "eq", True),
                C("brindle.breath_control", "eq", "ready"),
            ),
            (
                C("kite.launched", "eq", True),
            ),
        ),
        Rule(
            "high_delivery_reaches_basket",
            (
                C("kite.location", "eq", "basket"),
                C("kite.route", "eq", "high"),
            ),
            (
                C("kite.delivered", "eq", True),
            ),
        ),
    )

    goal = (
        C("basket.received", "eq", True),
        C("note.delivered", "eq", True),
        C("orra.confirmed", "eq", True),
    )

    labels = {
        "wind.pattern": "wind pattern",
        "kite.defect": "kite condition",
        "kite.route": "chosen route",
        "kite.stable": "kite stability",
        "note.secured": "message secured",
        "note.delivered": "message delivered",
        "basket.received": "message at marked basket",
        "orra.confirmed": "keeper confirmed receipt",
    }

    return WorldSpec(
        title="The Kite Workshop: A Message on the Wind",
        entities=entities,
        initial=initial,
        scenes=tuple(scenes),
        goal=goal,
        rules=rules,
        labels=labels,
    )
