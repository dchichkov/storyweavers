import random
from runtime import WorldSpec, Condition as C, scene, observe, tell, transfer

def build(seed):
    rng = random.Random(seed)
    problem = rng.choice(("mixed", "curled", "misbelief"))

    entities = {
        "ada": {"name": "Ada", "kind": "child"},
        "pip": {"name": "Pip", "kind": "dragon"},
        "mrsbean": {"name": "Mrs. Bean", "kind": "neighbor"},
        "tin": {"name": "invitation tin", "kind": "prop"},
        "invitation.blue": {"name": "blue invitation", "kind": "prop"},
        "invitation.red": {"name": "red invitation", "kind": "prop"},
        "invitation.green": {"name": "green invitation", "kind": "prop"},
        "party": {"name": "roof garden party", "kind": "event"},
    }

    mixed = problem == "mixed"
    curled = problem == "curled"
    misbelief = problem == "misbelief"

    initial = {
        "ada.memes.Curiosity": 2,
        "pip.memes.Helpfulness": 3,
        "tin.open": False,
        "tin.owner": "ada",
        "invitation.blue.owner": "ada",
        "invitation.blue.location": "tin",
        "invitation.blue.mark": "music" if mixed else "quiet",
        "invitation.blue.condition": "flat",
        "invitation.red.owner": "ada",
        "invitation.red.location": "tin",
        "invitation.red.mark": "quiet",
        "invitation.red.condition": "curled" if curled else "flat",
        "invitation.green.owner": "ada",
        "invitation.green.location": "tin",
        "invitation.green.mark": "quiet",
        "invitation.green.condition": "flat",
        "ada.belief.mrsbean.preference": "music" if misbelief else "quiet",
        "pip.belief.safe_carry": False if curled else True,
        "mrsbean.preference": "quiet" if misbelief else "music",
        "mrsbean.asked": False,
        "mrsbean.agreed": False,
        "party.problem": problem,
        "party.mode": "none",
        "party.invitations.delivered": 0,
        "party.performed": False,
        "mrsbean.response": "none",
        "ada.knows.tin.open": None,
        "ada.knows.invitation.blue.mark": None,
        "pip.knows.invitation.blue.mark": None,
        "ada.knows.invitation.red.condition": None,
        "ada.knows.mrsbean.preference": None,
        "pip.knows.mrsbean.preference": None,
    }

    scenes = (
        scene(
            "open_tin", "access", ("ada",),
            when=(C("tin.open", "eq", False),),
            set_values={"tin.open": True},
            summary="Ada opened the invitation tin",
        ),
        observe(
            "observe_blue_mark", "ada", "invitation.blue.mark",
            requires=(C("tin.open", "eq", True), C("party.problem", "eq", "mixed")),
            summary="Ada read the blue invitation mark",
        ),
        tell(
            "tell_blue_mark", "ada", "pip", "invitation.blue.mark",
            when=(C("ada.knows.invitation.blue.mark", "ne", None),),
            summary="Ada told Pip what the blue mark said",
        ),
        transfer(
            "give_blue", "ada", "pip", "invitation.blue",
            when=(
                C("party.problem", "eq", "mixed"),
                C("pip.knows.invitation.blue.mark", "eq", "music"),
            ),
            summary="Ada handed Pip the blue invitation",
        ),
        scene(
            "deliver_blue", "delivery", ("pip",),
            when=(
                C("party.problem", "eq", "mixed"),
                C("invitation.blue.owner", "eq", "pip"),
                C("invitation.blue.location", "eq", "tin"),
            ),
            set_values={
                "invitation.blue.location": "mrsbean.roof",
                "party.invitations.delivered": 1,
            },
            summary="Pip delivered the blue invitation",
        ),
        observe(
            "discover_red", "ada", "invitation.red.condition",
            requires=(
                C("tin.open", "eq", True),
                C("party.problem", "eq", "curled"),
            ),
            summary="Ada discovered that the red invitation was curled",
        ),
        scene(
            "tie_ribbon", "Ada", ("ada",),
            when=(
                C("party.problem", "eq", "curled"),
                C("ada.knows.invitation.red.condition", "eq", "curled"),
            ),
            set_values={
                "invitation.red.location": "ribbon",
                "pip.belief.safe_carry": True,
            },
            summary="Ada tied the curled invitation to a ribbon",
        ),
        transfer(
            "give_red", "ada", "pip", "invitation.red",
            when=(
                C("party.problem", "eq", "curled"),
                C("invitation.red.location", "eq", "ribbon"),
                C("pip.belief.safe_carry", "eq", True),
            ),
            summary="Ada gave Pip the ribbon-tethered invitation",
        ),
        scene(
            "deliver_red", "delivery", ("pip",),
            when=(
                C("party.problem", "eq", "curled"),
                C("invitation.red.owner", "eq", "pip"),
            ),
            set_values={"invitation.red.location": "mrsbean.roof"},
            increments={"party.invitations.delivered": 1},
            summary="Pip delivered the ribbon-tethered invitation",
        ),
        scene(
            "ask_mrsbean", "conversation", ("ada", "mrsbean"),
            when=(
                C("party.problem", "eq", "misbelief"),
                C("mrsbean.asked", "eq", False),
            ),
            set_values={"mrsbean.asked": True},
            summary="Ada asked Mrs. Bean about the party",
        ),
        observe(
            "observe_preference", "ada", "mrsbean.preference",
            requires=(
                C("mrsbean.asked", "eq", True),
                C("party.problem", "eq", "misbelief"),
            ),
            summary="Ada heard Mrs. Bean's quiet preference",
        ),
        tell(
            "tell_preference", "ada", "pip", "mrsbean.preference",
            when=(C("ada.knows.mrsbean.preference", "eq", "quiet"),),
            summary="Ada told Pip that Mrs. Bean preferred quiet",
        ),
        transfer(
            "give_green", "ada", "pip", "invitation.green",
            when=(
                C("party.problem", "eq", "misbelief"),
                C("pip.knows.mrsbean.preference", "eq", "quiet"),
            ),
            summary="Ada gave Pip the green invitation",
        ),
        scene(
            "deliver_green", "delivery", ("pip",),
            when=(
                C("party.problem", "eq", "misbelief"),
                C("invitation.green.owner", "eq", "pip"),
            ),
            set_values={"invitation.green.location": "mrsbean.roof"},
            increments={"party.invitations.delivered": 1},
            summary="Pip delivered the green invitation",
        ),
        scene(
            "agree_music", "agreement", ("mrsbean",),
            when=(
                C("party.problem", "eq", "mixed"),
                C("invitation.blue.location", "eq", "mrsbean.roof"),
            ),
            set_values={
                "mrsbean.agreed": True,
                "party.mode": "musical",
                "mrsbean.response": "bell concert",
            },
            summary="Mrs. Bean agreed to a tiny musical party",
        ),
        scene(
            "agree_ribbon", "agreement", ("mrsbean",),
            when=(
                C("party.problem", "eq", "curled"),
                C("invitation.red.location", "eq", "mrsbean.roof"),
            ),
            set_values={
                "mrsbean.agreed": True,
                "party.mode": "ribbon",
                "mrsbean.response": "ribbon parade",
            },
            summary="Mrs. Bean agreed to a careful ribbon parade",
        ),
        scene(
            "agree_gentle", "agreement", ("mrsbean",),
            when=(
                C("party.problem", "eq", "misbelief"),
                C("invitation.green.location", "eq", "mrsbean.roof"),
            ),
            set_values={
                "mrsbean.agreed": True,
                "party.mode": "gentle",
                "mrsbean.response": "flower greeting",
            },
            summary="Mrs. Bean agreed to a gentle dragon greeting",
        ),
        scene(
            "perform_party", "performance", ("pip",),
            when=(
                C("mrsbean.agreed", "eq", True),
                C("party.performed", "eq", False),
            ),
            set_values={"party.performed": True},
            summary="Pip performed the promised roof-garden greeting",
        ),
    )

    return WorldSpec(
        "The Roof Garden Invitation Parade",
        entities,
        initial,
        scenes,
        goal=(
            C("party.invitations.delivered", "ge", 1),
            C("mrsbean.agreed", "eq", True),
            C("party.performed", "eq", True),
        ),
        rules=(),
        labels={
            "party.mode": "party style",
            "party.performed": "the greeting",
            "mrsbean.response": "Mrs. Bean's response",
        },
        prune=True,
        premise_keys=(
            "invitation.blue.location",
            "invitation.red.condition",
            "ada.belief.mrsbean.preference",
            "pip.belief.safe_carry",
        ),
        outcome_keys=(
            "party.invitations.delivered",
            "party.mode",
            "party.performed",
            "mrsbean.response",
        ),
    )
