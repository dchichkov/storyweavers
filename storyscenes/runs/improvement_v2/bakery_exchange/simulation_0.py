import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)

    tray_label = rng.choice(("star", "plain"))
    flour_mark = rng.choice(("sweet", "salty"))
    cup_owner = rng.choice(("bramble", "mina"))
    arrival = rng.choice(("hungry", "carrying_prize"))

    entities = {
        "mina": {"name": "Mina", "kind": "child baker"},
        "bramble": {"name": "Bramble", "kind": "squirrel"},
        "niko": {"name": "Niko", "kind": "neighbor"},
        "stall": {"name": "striped bakery stall", "kind": "setting"},
        "tray": {"name": "three-bun tray", "kind": "prop"},
        "bun_a": {"name": "star bun", "kind": "prop"},
        "bun_b": {"name": "plain warm bun", "kind": "prop"},
        "bun_c": {"name": "clover bun", "kind": "prop"},
        "flour": {"name": "flour sack", "kind": "prop"},
        "cup": {"name": "acorn-cup", "kind": "prop"},
        "ribbon": {"name": "red ribbon", "kind": "prop"},
        "prize": {"name": "Golden Rolling Pin card", "kind": "prize"},
        "board": {"name": "small chalkboard", "kind": "prop"},
    }

    initial = {
        "mina.memes.welcome": 2,
        "mina.wants": "shared_treat",
        "mina.agrees.share": False,
        "mina.beliefs.niko.role": "critic" if arrival == "carrying_prize" else "customer",
        "mina.knows.flour.mark": None,
        "mina.knows.tray.label": None,
        "mina.knows.niko.arrival": None,
        "mina.knows.niko.wants": None,

        "bramble.memes.pride": 3,
        "bramble.wants": "grand_trade",
        "bramble.agrees.trade": False,
        "bramble.beliefs.tray.claim": "star",
        "bramble.knows.tray.label": None,
        "bramble.knows.cup.owner": None,

        "niko.memes.hunger": 2,
        "niko.memes.pride": 2,
        "niko.wants": "plain",
        "niko.arrival": arrival,
        "niko.offered": None,
        "niko.content": None,

        "stall.open": True,

        "tray.owner": "mina",
        "tray.label": tray_label,
        "tray.final_bun": None,

        "bun_a.owner": "mina",
        "bun_a.taste": "unbaked",
        "bun_b.owner": "mina",
        "bun_b.taste": "unbaked",
        "bun_c.owner": "mina",
        "bun_c.taste": "unbaked",

        "flour.owner": "mina",
        "flour.mark": flour_mark,

        "cup.owner": cup_owner,
        "ribbon.owner": "bramble",
        "ribbon.position": "cup",

        "prize.owner": "niko" if arrival == "carrying_prize" else "stall",
        "board.message": "closed",
    }

    scenes = (
        observe(
            "look_flour", "mina", "flour.mark",
            requires=(C("stall.open", "eq", True),),
            summary="Mina read the flour-sack label",
        ),
        observe(
            "look_tray_bramble", "bramble", "tray.label",
            requires=(C("stall.open", "eq", True),),
            summary="Bramble inspected the star mark on the tray",
        ),
        observe(
            "look_cup", "bramble", "cup.owner",
            requires=(C("stall.open", "eq", True),),
            summary="Bramble checked who was holding the acorn-cup",
        ),
        observe(
            "notice_niko_card", "mina", "niko.arrival",
            requires=(C("stall.open", "eq", True),),
            summary="Mina noticed why Niko had come to the stall",
        ),
        scene(
            "swap_ribbon", "Mistake", ("bramble",),
            when=(
                C("flour.mark", "eq", "sweet"),
                C("ribbon.position", "eq", "cup"),
                C("bramble.memes.pride", "ge", 2),
            ),
            set_values={
                "flour.mark": "salty",
                "ribbon.position": "flour_sack",
                "board.message": "ribbon_mischief",
            },
            summary="Bramble tied the red ribbon around the wrong flour sack",
        ),
        tell(
            "tell_label", "bramble", "mina", "tray.label",
            requires=(
                C("bramble.knows.tray.label", "in", ("star", "plain")),
            ),
            summary="Bramble told Mina what the tray mark actually said",
        ),
        scene(
            "ask_taste", "Invitation", ("mina", "niko"),
            when=(
                C("mina.knows.niko.arrival", "in", ("hungry", "carrying_prize")),
                C("niko.memes.pride", "ge", 1),
            ),
            set_values={
                "mina.agrees.share": True,
                "board.message": "what_would_you_like",
            },
            copies={"mina.knows.niko.wants": "niko.wants"},
            summary="Mina asked Niko what sort of bun he truly wanted",
            pivotal=True,
        ),
        scene(
            "admit_swap", "Confession", ("bramble", "mina"),
            when=(
                C("board.message", "eq", "ribbon_mischief"),
                C("bramble.agrees.trade", "eq", True),
            ),
            set_values={"board.message": "ribbon_invitation"},
            summary="Bramble admitted that his fancy ribbon had changed the flour mark",
            pivotal=True,
        ),
        scene(
            "choose_star_bramble", "Bargain", ("mina", "bramble"),
            when=(
                C("mina.knows.tray.label", "eq", "star"),
                C("bramble.beliefs.tray.claim", "eq", "star"),
                C("bramble.agrees.trade", "eq", True),
            ),
            set_values={"tray.final_bun": "bramble"},
            summary="Mina set aside the star bun for Bramble's proposed trade",
        ),
        scene(
            "offer_cup", "Bargain", ("bramble",),
            when=(
                C("bramble.knows.cup.owner", "eq", "bramble"),
                C("bramble.memes.pride", "ge", 2),
            ),
            set_values={"bramble.agrees.trade": True},
            summary="Bramble offered his acorn-cup for a truly grand bun",
        ),
        transfer(
            "give_star", "mina", "bramble", "bun_a",
            requires=(
                C("tray.final_bun", "eq", "bramble"),
                C("bramble.agrees.trade", "eq", True),
                C("bun_a.taste", "eq", "unbaked"),
            ),
            summary="Mina placed the star bun in Bramble's paws",
        ),
        transfer(
            "trade_cup", "bramble", "mina", "cup",
            requires=(
                C("bramble.agrees.trade", "eq", True),
                C("bun_a.owner", "eq", "bramble"),
            ),
            summary="Bramble gave Mina the acorn-cup as the fair half of the trade",
        ),
        scene(
            "finish_trade", "Bargain", ("mina", "bramble"),
            when=(
                C("cup.owner", "eq", "mina"),
                C("bun_a.owner", "eq", "bramble"),
            ),
            set_values={"board.message": "trade_done"},
            summary="The chalkboard welcomed tasters to Bramble's completed trade",
        ),
        scene(
            "bake_plain", "Making", ("mina",),
            when=(
                C("mina.knows.flour.mark", "in", ("sweet", "salty")),
                C("bun_b.owner", "eq", "mina"),
            ),
            set_values={"bun_b.taste": "plain"},
            summary="Mina baked a plain warm bun with a crackly little top",
        ),
        scene(
            "bake_sweet", "Making", ("mina",),
            when=(
                C("mina.knows.flour.mark", "eq", "sweet"),
                C("bun_a.owner", "eq", "mina"),
            ),
            set_values={"bun_a.taste": "fancy"},
            summary="Mina made the star bun sweet and showy",
        ),
        scene(
            "bake_clover", "Making", ("mina",),
            when=(
                C("mina.knows.flour.mark", "eq", "salty"),
                C("bun_a.owner", "eq", "mina"),
            ),
            set_values={"bun_a.taste": "fancy"},
            summary="Mina turned the salty flour into a daring clover-sour star bun",
        ),
        scene(
            "present_plain", "Performance", ("mina", "niko"),
            when=(
                C("mina.knows.niko.wants", "eq", "plain"),
                C("bun_b.taste", "eq", "plain"),
                C("bun_b.owner", "eq", "mina"),
            ),
            set_values={
                "bun_b.owner": "niko",
                "niko.offered": "plain",
                "board.message": "plain_on_a_plate",
            },
            summary="Mina presented the plain warm bun without any trumpet flourishes",
        ),
        scene(
            "present_fancy", "Performance", ("mina", "niko"),
            when=(
                C("mina.beliefs.niko.role", "eq", "critic"),
                C("bun_a.taste", "eq", "fancy"),
                C("bun_a.owner", "eq", "mina"),
            ),
            set_values={
                "bun_a.owner": "niko",
                "niko.offered": "fancy",
                "board.message": "fancy_tasting",
            },
            summary="Mina gave Niko the fancy star bun as though he were a grand judge",
        ),
        scene(
            "accept_snack", "Welcome", ("niko",),
            when=(
                C("niko.offered", "eq", "plain"),
                C("niko.wants", "eq", "plain"),
                C("mina.agrees.share", "eq", True),
            ),
            set_values={
                "niko.content": True,
                "board.message": "welcome_shared",
            },
            summary="Niko accepted the warm plain bun with an honest, happy crunch",
        ),
        scene(
            "reject_fancy", "Turning Point", ("niko", "mina"),
            when=(
                C("niko.offered", "eq", "fancy"),
                C("niko.wants", "eq", "plain"),
                C("niko.memes.pride", "ge", 1),
            ),
            set_values={
                "niko.content": False,
                "board.message": "plain_is_best",
            },
            summary="Niko politely refused the fancy bun and asked for something simple",
        ),
        scene(
            "award_prize", "Prize", ("niko", "mina"),
            when=(
                C("niko.content", "eq", True),
                C("niko.offered", "eq", "plain"),
                C("prize.owner", "eq", "niko"),
                C("mina.agrees.share", "eq", True),
            ),
            set_values={"prize.owner": "mina"},
            summary="Niko gave Mina the Golden Rolling Pin card for the welcome she made",
        ),
    )

    rules = (
        Rule(
            "a prize follows a welcome",
            must=(C("mina.agrees.share", "eq", True),),
            when=(C("prize.owner", "eq", "mina"),),
        ),
        Rule(
            "a cup trade is agreed",
            must=(C("bramble.agrees.trade", "eq", True),),
            when=(C("cup.owner", "eq", "mina"),),
        ),
        Rule(
            "the ribbon confession includes an offer",
            must=(C("bramble.agrees.trade", "eq", True),),
            when=(C("board.message", "eq", "ribbon_invitation"),),
        ),
    )

    return WorldSpec(
        "The Crumb-and-Clover Exchange",
        entities,
        initial,
        scenes,
        goal=(
            C(
                "board.message",
                "in",
                ("welcome_shared", "trade_done", "plain_is_best", "ribbon_invitation"),
            ),
        ),
        rules=rules,
        labels={
            "tray.label": "the tray's mark",
            "flour.mark": "the flour-sack mark",
            "cup.owner": "the acorn-cup's holder",
            "board.message": "the chalkboard message",
            "prize.owner": "the Golden Rolling Pin card's holder",
        },
        prune=True,
        premise_keys=("tray.label", "flour.mark", "cup.owner", "niko.arrival"),
        outcome_keys=("prize.owner", "niko.content", "cup.owner", "board.message"),
    )
