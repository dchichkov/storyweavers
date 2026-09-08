from runtime import WorldSpec, Scene, Condition as C, Effect as E, Rule
from runtime import observe, tell, transfer
import random


def build(seed: int) -> WorldSpec:
    rng = random.Random(seed)

    bell_stuck = rng.choice((True, False))
    gear_frosty = rng.choice((True, False))
    upper_cluttered = rng.choice((True, False))
    prefers_lower = rng.choice((True, False))
    nella_asleep = rng.choice((True, False))

    entities = {
        "ada": {"name": "Ada", "kind": "child"},
        "brindle": {"name": "Brindle", "kind": "dragon"},
        "keeper": {"name": "Keeper Moss", "kind": "person"},
        "nella": {"name": "Nella", "kind": "person"},
        "tower": {"name": "clocktower", "kind": "place"},
        "upper": {"name": "upper clubroom", "kind": "place"},
        "lower": {"name": "lower landing", "kind": "place"},
        "house": {"name": "nearby house", "kind": "place"},
        "bell": {"name": "old bell", "kind": "prop"},
        "rope": {"name": "bell-rope", "kind": "prop"},
        "gear": {"name": "brass gear", "kind": "prop"},
        "notice": {"name": "noticeboard", "kind": "prop"},
        "cushions": {"name": "cushions", "kind": "prop"},
        "lantern": {"name": "lantern", "kind": "prop"},
        "flag": {"name": "club flag", "kind": "prop"},
        "papers": {"name": "tower papers", "kind": "prop"},
        "club": {"name": "Clocktower Club", "kind": "group"},
    }

    initial = {
        "ada.location": "tower",
        "brindle.location": "tower",
        "keeper.location": "tower",
        "nella.location": "house",

        "tower.club_time": "unknown",
        "upper.accessible": True,
        "upper.cluttered": upper_cluttered,
        "lower.accessible": True,
        "lower.arranged": False,

        "bell.location": "upper",
        "bell.owner": "keeper",
        "bell.stuck": bell_stuck,

        "rope.location": "upper",
        "rope.owner": "keeper",

        "gear.location": "upper",
        "gear.aligned": not bell_stuck,
        "gear.frosty": gear_frosty,

        "notice.location": "upper",
        "notice.outdated": True,
        "notice.clear": False,
        "notice.open": False,

        "cushions.location": "tower",
        "cushions.owner": "ada",
        "lantern.location": "tower",
        "lantern.owner": "ada",
        "flag.location": "tower",
        "flag.owner": "ada",
        "flag.signal": "none",
        "flag.tested": False,

        "papers.location": "upper",
        "papers.safe": True,

        "nella.asleep": nella_asleep,
        "nella.quiet_needed": True,
        "nella.prefers_lower": prefers_lower,
        "nella.agreed": False,
        "nella.relocation_requested": False,

        "club.ready": False,
        "club.meeting_place": "none",

        "ada.memes.Curiosity": 0,
        "ada.memes.Cooperation": 0,
        "ada.memes.Ambition": 1,
        "brindle.memes.Curiosity": 0,
        "brindle.memes.Cooperation": 0,
        "brindle.memes.Ambition": 1,
        "keeper.memes.Care": 1,

        "ada.knows.bell.stuck": None,
        "ada.knows.notice.outdated": None,
        "ada.knows.nella.quiet_needed": None,
        "brindle.knows.gear.frosty": None,
        "keeper.knows.nella.quiet_needed": True,
    }

    scenes = (
        Scene(
            "explore_tower",
            "observation",
            ("ada", "brindle"),
            (
                C("ada.location", "eq", "tower"),
                C("brindle.location", "eq", "tower"),
            ),
            (
                E("ada.memes.Curiosity", 1, "inc"),
                E("brindle.memes.Curiosity", 1, "inc"),
                E("ada.memes.Cooperation", 1, "inc"),
            ),
            "Ada and Brindle explored the clocktower together",
        ),
        Scene(
            "inspect_machinery",
            "observation",
            ("ada", "brindle"),
            (
                C("ada.location", "eq", "tower"),
                C("brindle.location", "eq", "tower"),
                C("ada.memes.Curiosity", "ge", 1),
                C("brindle.memes.Curiosity", "ge", 1),
                C("upper.accessible", "eq", True),
            ),
            (
                E("ada.knows.bell.stuck", "bell.stuck", "copy"),
                E("brindle.knows.gear.frosty", "gear.frosty", "copy"),
            ),
            "Ada inspected the bell while Brindle inspected the brass gear",
        ),
        observe(
            "inspect_notice",
            "ada",
            "notice.outdated",
            requires=(
                C("ada.location", "eq", "tower"),
                C("ada.memes.Curiosity", "ge", 1),
                C("upper.accessible", "eq", True),
            ),
            summary="Ada inspected the old noticeboard",
        ),
        tell(
            "keeper_explains_quiet",
            "keeper",
            "ada",
            "nella.quiet_needed",
            requires=(
                C("keeper.location", "eq", "tower"),
                C("ada.location", "eq", "tower"),
                C("keeper.memes.Care", "ge", 1),
            ),
            summary="Keeper Moss explained Nella's need for quiet",
        ),
        Scene(
            "invite_nella_upstairs",
            "care",
            ("ada", "nella"),
            (
                C("ada.location", "eq", "tower"),
                C("nella.location", "eq", "house"),
                C("ada.knows.nella.quiet_needed", "eq", True),
                C("nella.prefers_lower", "eq", False),
            ),
            (
                E("nella.location", "tower"),
                E("nella.asleep", False),
                E("nella.agreed", True),
                E("tower.club_time", "daytime"),
            ),
            "Ada walked with Nella to the tower and agreed on a gentle daytime meeting",
        ),
        Scene(
            "invite_nella_lower",
            "care",
            ("ada", "nella"),
            (
                C("ada.location", "eq", "tower"),
                C("nella.location", "eq", "house"),
                C("ada.knows.nella.quiet_needed", "eq", True),
                C("nella.prefers_lower", "eq", True),
            ),
            (
                E("nella.location", "tower"),
                E("nella.asleep", False),
                E("nella.relocation_requested", True),
                E("tower.club_time", "daytime"),
            ),
            "Ada walked with Nella to the tower and heard her lower-landing suggestion",
        ),
        transfer(
            "lend_rope",
            "keeper",
            "ada",
            "rope",
            requires=(
                C("keeper.location", "eq", "tower"),
                C("ada.location", "eq", "tower"),
                C("keeper.memes.Care", "ge", 1),
            ),
            summary="Keeper Moss lent Ada the bell-rope",
        ),
        Scene(
            "loosen_frost",
            "experimentation",
            ("ada", "brindle"),
            (
                C("ada.location", "eq", "tower"),
                C("brindle.location", "eq", "tower"),
                C("brindle.knows.gear.frosty", "eq", True),
                C("gear.frosty", "eq", True),
                C("papers.safe", "eq", True),
            ),
            (
                E("gear.frosty", False),
                E("brindle.memes.Cooperation", 1, "inc"),
            ),
            "Brindle used a small careful breath to loosen frost from the gear",
        ),
        Scene(
            "secure_bell_gear",
            "cooperation",
            ("ada", "keeper"),
            (
                C("ada.location", "eq", "tower"),
                C("keeper.location", "eq", "tower"),
                C("ada.knows.bell.stuck", "in", (True, False)),
                C("rope.owner", "eq", "ada"),
                C("gear.frosty", "eq", False),
            ),
            (
                E("gear.aligned", True),
                E("bell.stuck", False),
                E("rope.owner", "keeper"),
                E("flag.signal", "bell"),
            ),
            "Ada and Keeper Moss fastened the bell gear carefully with the rope",
        ),
        Scene(
            "post_visual_schedule",
            "communication",
            ("ada", "brindle"),
            (
                C("ada.location", "eq", "tower"),
                C("brindle.location", "eq", "tower"),
                C("ada.knows.notice.outdated", "eq", True),
                C("notice.outdated", "eq", True),
            ),
            (
                E("notice.outdated", False),
                E("notice.clear", True),
                E("flag.signal", "visual"),
            ),
            "Ada posted a clear schedule and chose a visual arrival signal",
        ),
        Scene(
            "arrange_upper_room",
            "physical_arrangement",
            ("ada", "brindle"),
            (
                C("ada.location", "eq", "tower"),
                C("brindle.location", "eq", "tower"),
                C("nella.agreed", "eq", True),
                C("tower.club_time", "eq", "daytime"),
            ),
            (
                E("upper.cluttered", False),
                E("cushions.location", "upper"),
                E("lantern.location", "upper"),
            ),
            "Ada and Brindle arranged cushions and a lantern in the upper clubroom",
        ),
        Scene(
            "arrange_lower_landing",
            "physical_arrangement",
            ("ada", "brindle"),
            (
                C("ada.location", "eq", "tower"),
                C("brindle.location", "eq", "tower"),
                C("nella.relocation_requested", "eq", True),
                C("tower.club_time", "eq", "daytime"),
            ),
            (
                E("lower.arranged", True),
                E("cushions.location", "lower"),
                E("lantern.location", "lower"),
                E("flag.location", "lower"),
            ),
            "Ada and Brindle arranged cushions, lantern, and flag on the lower landing",
        ),
        Scene(
            "test_bell_signal",
            "experimentation",
            ("ada", "keeper"),
            (
                C("ada.location", "eq", "tower"),
                C("keeper.location", "eq", "tower"),
                C("flag.signal", "eq", "bell"),
                C("bell.stuck", "eq", False),
                C("gear.aligned", "eq", True),
                C("nella.agreed", "eq", True),
                C("nella.asleep", "eq", False),
                C("tower.club_time", "eq", "daytime"),
            ),
            (E("flag.tested", True),),
            "Ada and Keeper Moss tested one gentle daytime bell signal",
        ),
        Scene(
            "test_visual_signal",
            "experimentation",
            ("ada", "brindle"),
            (
                C("ada.location", "eq", "tower"),
                C("brindle.location", "eq", "tower"),
                C("flag.signal", "eq", "visual"),
                C("flag.location", "eq", "lower"),
                C("nella.relocation_requested", "eq", True),
            ),
            (E("flag.tested", True),),
            "Ada and Brindle tested the quiet visual club signal",
        ),
        Scene(
            "open_upper_club",
            "ambition",
            ("ada", "brindle", "keeper"),
            (
                C("ada.location", "eq", "tower"),
                C("brindle.location", "eq", "tower"),
                C("keeper.location", "eq", "tower"),
                C("cushions.location", "eq", "upper"),
                C("lantern.location", "eq", "upper"),
                C("flag.signal", "eq", "bell"),
                C("flag.tested", "eq", True),
                C("nella.agreed", "eq", True),
            ),
            (
                E("notice.open", True),
                E("club.ready", True),
                E("club.meeting_place", "upper"),
            ),
            "Ada and Brindle opened the first club meeting beneath one gentle chime",
        ),
        Scene(
            "open_lower_club",
            "ambition",
            ("ada", "brindle"),
            (
                C("ada.location", "eq", "tower"),
                C("brindle.location", "eq", "tower"),
                C("lower.arranged", "eq", True),
                C("cushions.location", "eq", "lower"),
                C("lantern.location", "eq", "lower"),
                C("flag.signal", "eq", "visual"),
                C("flag.tested", "eq", True),
                C("nella.relocation_requested", "eq", True),
            ),
            (
                E("notice.open", True),
                E("club.ready", True),
                E("club.meeting_place", "lower"),
            ),
            "Ada and Brindle opened the first no-bell club on the lower landing",
        ),
    )

    rules = (
        Rule(
            "a tested bell respects Nella's quiet",
            (
                C("nella.asleep", "eq", False),
                C("nella.agreed", "eq", True),
                C("tower.club_time", "eq", "daytime"),
            ),
            (
                C("flag.signal", "eq", "bell"),
                C("flag.tested", "eq", True),
            ),
        ),
        Rule(
            "a bell signal uses sound machinery",
            (
                C("bell.stuck", "eq", False),
                C("gear.aligned", "eq", True),
            ),
            (C("flag.signal", "eq", "bell"),),
        ),
        Rule(
            "an upper club has its agreed arrangement",
            (
                C("notice.open", "eq", True),
                C("flag.signal", "eq", "bell"),
                C("flag.tested", "eq", True),
                C("cushions.location", "eq", "upper"),
                C("lantern.location", "eq", "upper"),
                C("nella.agreed", "eq", True),
            ),
            (
                C("club.ready", "eq", True),
                C("club.meeting_place", "eq", "upper"),
            ),
        ),
        Rule(
            "a lower club has its quiet arrangement",
            (
                C("notice.open", "eq", True),
                C("flag.signal", "eq", "visual"),
                C("flag.tested", "eq", True),
                C("lower.arranged", "eq", True),
                C("cushions.location", "eq", "lower"),
                C("lantern.location", "eq", "lower"),
                C("nella.relocation_requested", "eq", True),
            ),
            (
                C("club.ready", "eq", True),
                C("club.meeting_place", "eq", "lower"),
            ),
        ),
    )

    goal = (C("club.ready", "eq", True),)

    labels = {
        "bell.stuck": "bell condition",
        "gear.aligned": "gear alignment",
        "gear.frosty": "gear frost",
        "upper.cluttered": "upper room clutter",
        "lower.arranged": "lower landing arrangement",
        "notice.clear": "schedule clarity",
        "notice.open": "club opening",
        "flag.signal": "club signal",
        "flag.tested": "signal tested",
        "tower.club_time": "club meeting time",
        "nella.agreed": "Nella's agreement",
        "nella.relocation_requested": "Nella's lower-landing request",
        "club.ready": "club readiness",
        "club.meeting_place": "club meeting place",
    }

    return WorldSpec(
        "The Clocktower Club",
        entities,
        initial,
        scenes,
        goal,
        rules=rules,
        labels=labels,
    )
