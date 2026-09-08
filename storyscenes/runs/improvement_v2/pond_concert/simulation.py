import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)

    presence = rng.choice(("cattails", "cattails", "away"))
    hearing = rng.choice(("keen", "muffled"))
    tom_plan = rng.choice(("loud", "clever"))
    pip_knows_enjoys = rng.choice((True, True, False))

    entities = {
        "mira": {"name": "Mira", "kind": "child"},
        "tom": {"name": "Tom", "kind": "child"},
        "pip": {"name": "Pip", "kind": "frog"},
        "nella": {"name": "Nella", "kind": "neighbor"},
        "reedstage": {"name": "floating reed stage", "kind": "prop"},
        "drum": {"name": "silver kettle-drum", "kind": "prop"},
        "lanterns": {"name": "lantern ribbon", "kind": "prop"},
        "spoon": {"name": "Golden Tadpole Spoon", "kind": "prop"},
        "invitation": {"name": "paper invitation", "kind": "prop"},
        "concert": {"name": "pond concert", "kind": "event"},
        "audience": {"name": "frog audience", "kind": "group"},
        "pond": {"name": "moonlit pond", "kind": "setting"},
    }

    initial = {
        "mira.wants": "spectacle",
        "mira.believes.cheering": True,
        "mira.knows.nella.presence": None,
        "tom.wants": "spoon",
        "tom.plan": tom_plan,
        "tom.agrees": False,
        "tom.knows.nella.hearing": None,
        "tom.knows.pip.wish": None,
        "pip.wants": "moon_song",
        "pip.wish": "moon_song",
        "pip.knows.nella.hearing": None,
        "pip.knows.pip.wish": "moon_song",
        "pip.knows.nella.enjoys": pip_knows_enjoys,
        "nella.presence": presence,
        "nella.hearing": hearing,
        "nella.invited": False,
        "nella.location": presence,
        "reedstage.location": "bank",
        "drum.owner": "tom",
        "lanterns.location": "bank",
        "spoon.owner": "pond",
        "invitation.owner": "pip",
        "concert.started": False,
        "concert.finished": False,
        "concert.rehearsal": "none",
        "concert.style": "none",
        "audience.delighted": False,
    }

    scenes = (
        observe(
            "look_nella",
            "mira",
            "nella.presence",
            requires=(C("nella.location", "in", ("cattails", "away")),),
            summary="Mira looked toward the cattails for Nella.",
        ),
        observe(
            "notice_quiet",
            "pip",
            "nella.hearing",
            requires=(C("nella.presence", "eq", "cattails"),),
            summary="Pip listened closely and noticed how Nella could hear.",
        ),
        tell(
            "tell_tom_hearing",
            "pip",
            "tom",
            "nella.hearing",
            requires=(
                C("pip.knows.nella.hearing", "in", ("keen", "muffled")),
                C("nella.presence", "eq", "cattails"),
            ),
            summary="Pip told Tom what he had learned about Nella's hearing.",
        ),
        tell(
            "tell_tom_wish",
            "pip",
            "tom",
            "pip.wish",
            requires=(C("pip.knows.pip.wish", "eq", "moon_song"),),
            summary="Pip told Tom about the moon-song he hoped to play.",
        ),
        transfer(
            "invite_nella",
            "pip",
            "nella",
            "invitation",
            requires=(
                C("nella.presence", "eq", "cattails"),
                C("nella.location", "eq", "cattails"),
            ),
            summary="Pip sent the paper invitation through the cattails.",
        ),
        scene(
            "accept_invitation",
            "Invitation",
            ("nella",),
            when=(
                C("invitation.owner", "eq", "nella"),
                C("nella.presence", "eq", "cattails"),
            ),
            set_values={"nella.invited": True},
            summary="Nella accepted the invitation from behind the cattails.",
        ),
        scene(
            "float_stage",
            "Prepare",
            ("mira", "pip"),
            when=(C("reedstage.location", "eq", "bank"),),
            set_values={"reedstage.location": "pond"},
            summary="Mira and Pip floated the reed stage onto the pond.",
        ),
        scene(
            "hang_lanterns",
            "Prepare",
            ("mira",),
            when=(
                C("reedstage.location", "eq", "pond"),
                C("lanterns.location", "eq", "bank"),
            ),
            set_values={"lanterns.location": "reedstage"},
            summary="Mira draped the lantern ribbon over the reed stage.",
        ),
        scene(
            "rehearse_roar",
            "Rehearse",
            ("tom",),
            when=(
                C("drum.owner", "eq", "tom"),
                C("tom.plan", "eq", "loud"),
            ),
            set_values={"concert.rehearsal": "roar"},
            summary="Tom rehearsed a booming kettle-drum finale.",
        ),
        scene(
            "rehearse_ripple",
            "Rehearse",
            ("tom",),
            when=(
                C("drum.owner", "eq", "tom"),
                C("tom.plan", "eq", "clever"),
            ),
            set_values={"concert.rehearsal": "roar"},
            summary="Tom practiced a clever drum ripple that grew wonderfully loud.",
        ),
        scene(
            "rehearse_moon",
            "Rehearse",
            ("pip",),
            when=(C("reedstage.location", "eq", "pond"),),
            set_values={"concert.rehearsal": "moon"},
            summary="Pip rehearsed his gentle moon-song on the floating stage.",
        ),
        scene(
            "choose_kind_finale",
            "Choose",
            ("tom", "pip"),
            when=(
                C("tom.plan", "eq", "clever"),
                C("tom.knows.pip.wish", "eq", "moon_song"),
                C("tom.knows.nella.hearing", "eq", "keen"),
                C("nella.presence", "eq", "cattails"),
                C("pip.knows.nella.enjoys", "eq", True),
            ),
            set_values={"tom.agrees": True, "tom.plan": "gentle"},
            summary="Tom chose Pip's moon-song over a prize-winning roar.",
            pivotal=True,
        ),
        scene(
            "call_concert_away",
            "Invite",
            ("mira", "tom", "pip"),
            when=(
                C("mira.knows.nella.presence", "eq", "away"),
                C("reedstage.location", "eq", "pond"),
                C("lanterns.location", "eq", "reedstage"),
                C("concert.started", "eq", False),
            ),
            set_values={"concert.started": True},
            summary="With Nella away, the friends called the frogs to the pond concert.",
        ),
        scene(
            "call_concert_guest",
            "Invite",
            ("mira", "tom", "pip", "nella"),
            when=(
                C("nella.invited", "eq", True),
                C("reedstage.location", "eq", "pond"),
                C("lanterns.location", "eq", "reedstage"),
                C("concert.started", "eq", False),
            ),
            set_values={"concert.started": True},
            summary="The invited concert began beneath the pond lanterns.",
        ),
        scene(
            "perform_roar",
            "Perform",
            ("tom",),
            when=(
                C("concert.started", "eq", True),
                C("concert.rehearsal", "eq", "roar"),
            ),
            set_values={
                "concert.style": "loud",
                "audience.delighted": True,
            },
            summary="Tom's kettle-drum finale boomed across the lily pads.",
        ),
        scene(
            "perform_moon",
            "Perform",
            ("pip",),
            when=(
                C("concert.started", "eq", True),
                C("concert.rehearsal", "eq", "moon"),
                C("tom.agrees", "eq", True),
            ),
            set_values={
                "concert.style": "soft",
                "audience.delighted": True,
            },
            summary="Pip played the moon-song softly enough for the reeds to listen.",
        ),
        scene(
            "perform_mixed",
            "Perform",
            ("pip", "tom"),
            when=(
                C("concert.started", "eq", True),
                C("concert.rehearsal", "eq", "moon"),
                C("tom.agrees", "eq", True),
                C("drum.owner", "eq", "tom"),
            ),
            set_values={
                "concert.style": "mixed",
                "audience.delighted": True,
            },
            summary="Pip's moon-song ended in Tom's playful silver drum ripple.",
        ),
        transfer(
            "award_spoon_loud",
            "pond",
            "tom",
            "spoon",
            requires=(
                C("concert.style", "eq", "loud"),
                C("audience.delighted", "eq", True),
            ),
            summary="The frogs awarded Tom the Golden Tadpole Spoon.",
        ),
        transfer(
            "award_spoon_mixed",
            "pond",
            "tom",
            "spoon",
            requires=(
                C("concert.style", "eq", "mixed"),
                C("audience.delighted", "eq", True),
            ),
            summary="The frogs gave Tom the Golden Tadpole Spoon for the mixed finale.",
        ),
        scene(
            "close_loud",
            "Close",
            ("tom",),
            when=(
                C("concert.style", "eq", "loud"),
                C("spoon.owner", "eq", "tom"),
                C("concert.finished", "eq", False),
            ),
            set_values={"concert.finished": True},
            summary="The loud pond concert ended with Tom's prize held high.",
        ),
        scene(
            "close_soft",
            "Close",
            ("pip", "nella"),
            when=(
                C("concert.style", "eq", "soft"),
                C("concert.finished", "eq", False),
            ),
            set_values={"concert.finished": True},
            summary="The moon-song concert ended in a warm, quiet hush.",
        ),
        scene(
            "close_mixed",
            "Close",
            ("pip", "tom"),
            when=(
                C("concert.style", "eq", "mixed"),
                C("spoon.owner", "eq", "tom"),
                C("concert.finished", "eq", False),
            ),
            set_values={"concert.finished": True},
            summary="The mixed pond concert ended with cheers and a shining spoon.",
        ),
    )

    rules = (
        Rule(
            "finished_concert_has_a_style",
            (C("concert.style", "ne", "none"),),
            when=(C("concert.finished", "eq", True),),
        ),
        Rule(
            "delighted_audience_heard_a_concert",
            (C("concert.style", "in", ("loud", "soft", "mixed")),),
            when=(C("audience.delighted", "eq", True),),
        ),
    )

    return WorldSpec(
        "The Moonlit Pond Concert",
        entities,
        initial,
        scenes,
        goal=(
            C("concert.finished", "eq", True),
            C("audience.delighted", "eq", True),
        ),
        rules=rules,
        labels={
            "nella.presence": "where Nella is",
            "nella.hearing": "Nella's hearing",
            "tom.plan": "Tom's planned finale",
            "concert.style": "the concert's style",
            "spoon.owner": "keeper of the Golden Tadpole Spoon",
        },
        prune=True,
        premise_keys=(
            "nella.presence",
            "nella.hearing",
            "tom.plan",
            "pip.knows.nella.enjoys",
        ),
        outcome_keys=(
            "concert.style",
            "audience.delighted",
            "spoon.owner",
        ),
    )
