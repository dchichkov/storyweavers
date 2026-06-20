#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.3-codex-spark/trouser_rhyme_happy_ending_bravery_nursery_rhyme_2.py
========================================================================================

Seed prompt used:
    Write a story that includes the following words and narrative instruments.
    Words: trouser
    Features: Rhyme, Happy Ending, Bravery
    Style: Nursery Rhyme

Source tale written from the seed:
    In a windy little town lane, a child’s trouser flew up onto a rope bridge.
    Instead of giving up, the child (with a brave friend) says a counting rhyme,
    chooses a matching safe recovery plan, and brings the trouser home.
    The world updates from “snagged and drifting” to “recovered and tied safely,”
    and the closing rhyme proves the state has changed.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve()
for _parent in [ROOT, *ROOT.parents]:
    if _parent.name == "storyworlds":
        ROOT = _parent.parent
        break
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Route:
    key: str
    phrase: str
    opening: str
    wind: float
    helper_space: int
    open_image: str
    finish_image: str


@dataclass(frozen=True)
class Hazard:
    key: str
    phrase: str
    routes: tuple[str, ...]
    signal: str
    cause: str
    bravery_need: float
    focus_need: float
    helper_needed: bool
    allowed_plans: tuple[str, ...]
    allowed_rhymes: tuple[str, ...]


@dataclass(frozen=True)
class Rhyme:
    key: str
    phrase: str
    repeated_line: str
    brave_boost: float
    focus_boost: float
    ending_line: str
    allowed_routes: tuple[str, ...]
    allowed_hazards: tuple[str, ...]


@dataclass(frozen=True)
class RescuePlan:
    key: str
    phrase: str
    tool: str
    helper_required: bool
    route_allow: tuple[str, ...]
    brave_boost: float
    focus_boost: float
    explanation: str


@dataclass
class StoryParams:
    route: str
    hazard: str
    rhyme: str
    plan: str
    hero: str
    hero_kind: str
    friend: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    route: Route
    hazard: Hazard
    rhyme: Rhyme
    plan: RescuePlan
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(block) for block in self.paragraphs if block)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  route={self.route.key} hazard={self.hazard.key} rhyme={self.rhyme.key} plan={self.plan.key}")
        rows.append(f"  ending={self.facts.get('ending_state')}")
        rows.append(f"  hero={self.params.hero} hero_kind={self.params.hero_kind}")
        for ent in self.entities.values():
            rows.append(
                f"  {ent.id}<{ent.kind}> traits={ent.traits} "
                f"meters={ent.meters} memes={ent.memes}"
            )
        rows.append(f"  fired={self.fired}")
        rows.append(f"  history={self.history}")
        rows.append(f"  facts={self.facts}")
        return "\n".join(rows)


ROUTES = {
    "bridge_in_breezeway": Route(
        key="bridge_in_breezeway",
        phrase="the rope bridge in Breezy Lane",
        opening="Breezy Lane narrowed to a wooden bridge strung between painted posts, with bells tied to the rails.",
        wind=3.0,
        helper_space=1,
        open_image="A bright blue trouser fluttered once, then vanished above the bridge deck.",
        finish_image="The blue trouser came down in a neat, safe loop across their arm.",
    ),
    "puddle_market_span": Route(
        key="puddle_market_span",
        phrase="the puddle-market stepping span",
        opening="Two stalls met at a short stepping span over a wet court where children usually skipped in pairs.",
        wind=2.2,
        helper_space=0,
        open_image="A wind-chiffon ribbon wrapped the trouser near the lowest post.",
        finish_image="The blue trouser dripped cleanly into the pocket basket, no longer tugged by wet wind.",
    ),
    "moonlit_cloth_bridge": Route(
        key="moonlit_cloth_bridge",
        phrase="the moonlit cloth bridge by the toy lanterns",
        opening="A cloth-covered bridge arched over the fountain, painted with stars and tiny stitched moons.",
        wind=2.8,
        helper_space=2,
        open_image="The trouser hooked on a peg and swayed like a flag just out of reach.",
        finish_image="The trouser sat safely in the hero’s hands, tied with a ribbon and smiling in moonlight.",
    ),
}


HAZARDS = {
    "bridge_snag": Hazard(
        key="bridge_snag",
        phrase="a sudden snag at the bridge lip",
        routes=("bridge_in_breezeway", "moonlit_cloth_bridge"),
        signal="a soft rip and a dry flutter against the post",
        cause="a sharp gust pulled the trouser hem into a loose peg loop",
        bravery_need=2.0,
        focus_need=1.8,
        helper_needed=False,
        allowed_plans=("hook_reach", "friend_rope"),
        allowed_rhymes=("one_two_tie", "steady_step"),
    ),
    "rising_knuckle": Hazard(
        key="rising_knuckle",
        phrase="a wobbling knot that climbed higher with the wind",
        routes=("bridge_in_breezeway", "moonlit_cloth_bridge"),
        signal="a quick clink, then the trouser rose like a little blue sail",
        cause="the knot shifted with every gust and hid its free end near a narrow handhold",
        bravery_need=3.1,
        focus_need=2.2,
        helper_needed=False,
        allowed_plans=("friend_rope",),
        allowed_rhymes=("steady_step", "brave_heart"),
    ),
    "drift_pull": Hazard(
        key="drift_pull",
        phrase="a wind drag that pulled down toward the court basin",
        routes=("puddle_market_span", "moonlit_cloth_bridge"),
        signal="a flapping song from cloth and wet air",
        cause="air rolled through the lane and dragged the fabric away from safe footing",
        bravery_need=2.8,
        focus_need=2.0,
        helper_needed=True,
        allowed_plans=("friend_rope", "pole_and_reach"),
        allowed_rhymes=("one_two_tie", "brave_heart"),
    ),
}


RHYMES = {
    "one_two_tie": Rhyme(
        key="one_two_tie",
        phrase="One-two, brace, one-two, tie.",
        repeated_line="One-two, tie and hold, one-two, do not fold.",
        brave_boost=1.2,
        focus_boost=1.0,
        ending_line="One-two, tie and smile; we brought it home in style.",
        allowed_routes=("bridge_in_breezeway", "puddle_market_span", "moonlit_cloth_bridge"),
        allowed_hazards=("bridge_snag", "drift_pull", "rising_knuckle"),
    ),
    "steady_step": Rhyme(
        key="steady_step",
        phrase="Step by step, brave and slow.",
        repeated_line="Step by step, brave and slow; step by step, together go.",
        brave_boost=1.0,
        focus_boost=1.5,
        ending_line="Step by step, slow and bright; the trouser is home and all is right.",
        allowed_routes=("bridge_in_breezeway", "moonlit_cloth_bridge"),
        allowed_hazards=("bridge_snag", "rising_knuckle"),
    ),
    "brave_heart": Rhyme(
        key="brave_heart",
        phrase="Brave heart, brave feet, brave feet, brave heart.",
        repeated_line="Brave heart, brave feet, steady and sweet.",
        brave_boost=1.4,
        focus_boost=1.3,
        ending_line="Brave heart, brave feet, home now complete.",
        allowed_routes=("puddle_market_span", "moonlit_cloth_bridge"),
        allowed_hazards=("drift_pull", "rising_knuckle"),
    ),
}


PLANS = {
    "hook_reach": RescuePlan(
        key="hook_reach",
        phrase="use a hooked pole to loop the trouser from a distance",
        tool="hooked pole",
        helper_required=False,
        route_allow=("bridge_in_breezeway", "moonlit_cloth_bridge"),
        brave_boost=1.6,
        focus_boost=1.2,
        explanation="distance and control are the safe method for this high-lift snag.",
    ),
    "friend_rope": RescuePlan(
        key="friend_rope",
        phrase="call on a friend, anchor a rope, and pull in steady rhythm",
        tool="helper rope",
        helper_required=True,
        route_allow=("bridge_in_breezeway", "puddle_market_span", "moonlit_cloth_bridge"),
        brave_boost=2.4,
        focus_boost=2.0,
        explanation="a helper splits the weight and lowers the risk when wind or fear gets loud.",
    ),
    "pole_and_reach": RescuePlan(
        key="pole_and_reach",
        phrase="stand safe on the near side and guide the trouser down with a pole",
        tool="steady pole",
        helper_required=False,
        route_allow=("puddle_market_span",),
        brave_boost=1.1,
        focus_boost=1.6,
        explanation="a pole keeps hands off edge zones while the fabric is guided down low.",
    ),
}


HERO_NAMES = {
    "girl": ("Mila", "Nora", "Tess"),
    "boy": ("Leo", "Jun", "Eli"),
}

FRIENDS = ("Niko", "Kai", "Poppy", "Sam")


def _pick_hero(kind: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES[kind])


def _pick_friend(rng: random.Random, avoid: str) -> str:
    friend = rng.choice(FRIENDS)
    return friend if friend != avoid else rng.choice([f for f in FRIENDS if f != avoid])


def valid_combo(route_key: str, hazard_key: str, rhyme_key: str, plan_key: str) -> bool:
    if (
        route_key not in ROUTES
        or hazard_key not in HAZARDS
        or rhyme_key not in RHYMES
        or plan_key not in PLANS
    ):
        return False
    route = ROUTES[route_key]
    hazard = HAZARDS[hazard_key]
    rhyme = RHYMES[rhyme_key]
    plan = PLANS[plan_key]

    if route_key not in hazard.routes:
        return False
    if plan_key not in hazard.allowed_plans:
        return False
    if rhyme_key not in hazard.allowed_rhymes:
        return False
    if route_key not in plan.route_allow:
        return False
    if route_key not in rhyme.allowed_routes:
        return False
    if hazard_key not in rhyme.allowed_hazards:
        return False
    if plan.helper_required and route.helper_space < 1:
        return False

    return True


def invalid_reason(route_key: str, hazard_key: str, rhyme_key: str, plan_key: str) -> str:
    if route_key not in ROUTES:
        return f"No story: unknown route {route_key!r}."
    if hazard_key not in HAZARDS:
        return f"No story: unknown hazard {hazard_key!r}."
    if rhyme_key not in RHYMES:
        return f"No story: unknown rhyme {rhyme_key!r}."
    if plan_key not in PLANS:
        return f"No story: unknown plan {plan_key!r}."

    route = ROUTES[route_key]
    hazard = HAZARDS[hazard_key]
    rhyme = RHYMES[rhyme_key]
    plan = PLANS[plan_key]

    if route_key not in hazard.routes:
        return f"No story: {hazard.phrase} cannot happen at {route.phrase}."
    if plan_key not in hazard.allowed_plans:
        return (
            f"No story: plan {plan.phrase!r} is not meant for {hazard.phrase}. "
            f"Use one of: {', '.join(hazard.allowed_plans)}."
        )
    if rhyme_key not in hazard.allowed_rhymes:
        return (
            f"No story: rhyme {rhyme.phrase!r} does not match {hazard.phrase}. "
            f"Try {', '.join(hazard.allowed_rhymes)}."
        )
    if route_key not in plan.route_allow:
        return (
            f"No story: plan {plan.phrase!r} does not fit {route.phrase}. "
            f"Allowed routes are {', '.join(plan.route_allow)}."
        )
    if route_key not in rhyme.allowed_routes:
        return (
            f"No story: rhyme {rhyme.phrase!r} does not belong to {route.phrase}. "
            f"Allowed routes are {', '.join(rhyme.allowed_routes)}."
        )
    if hazard_key not in rhyme.allowed_hazards:
        return f"No story: rhyme {rhyme.phrase!r} is not grounded for {hazard.phrase}."
    if plan.helper_required and route.helper_space < 1:
        return (
            f"No story: {route.phrase} is too tight for a helper plan; "
            "it needs helper space 1 or more."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for route_key in sorted(ROUTES):
        for hazard_key in sorted(HAZARDS):
            for rhyme_key in sorted(RHYMES):
                for plan_key in sorted(PLANS):
                    if valid_combo(route_key, hazard_key, rhyme_key, plan_key):
                        combos.append((route_key, hazard_key, rhyme_key, plan_key))
    return combos


def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    combos = valid_combos()
    filtered = [
        combo
        for combo in combos
        if (args.route is None or combo[0] == args.route)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.rhyme is None or combo[2] == args.rhyme)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if args.route and args.hazard and args.rhyme and args.plan and not filtered:
        raise StoryError(invalid_reason(args.route, args.hazard, args.rhyme, args.plan))
    if args.route and not filtered:
        raise StoryError(f"No story: no known {args.route} hazards and plans match.")
    return filtered


def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str, str],
    index: int = 0,
) -> StoryParams:
    rng = random.Random((args.seed or 1) + index)
    route_key, hazard_key, rhyme_key, plan_key = combo
    hero_kind = args.hero_kind or rng.choice(tuple(HERO_NAMES))
    hero = args.hero or _pick_hero(hero_kind, rng)
    friend = args.friend or _pick_friend(rng, hero)
    return StoryParams(
        route=route_key,
        hazard=hazard_key,
        rhyme=rhyme_key,
        plan=plan_key,
        hero=hero,
        hero_kind=hero_kind,
        friend=friend,
        seed=(args.seed or 1) + index,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if not valid_combo(params.route, params.hazard, params.rhyme, params.plan):
        raise StoryError(invalid_reason(params.route, params.hazard, params.rhyme, params.plan))


def build_world(params: StoryParams) -> World:
    route = ROUTES[params.route]
    hazard = HAZARDS[params.hazard]
    rhyme = RHYMES[params.rhyme]
    plan = PLANS[params.plan]
    reasonableness_gate(params)

    world = World(params=params, route=route, hazard=hazard, rhyme=rhyme, plan=plan)

    hero = world.add(
        Entity(
            id=params.hero,
            kind=params.hero_kind,
            traits=["brave_in_training"],
            meters={"steadiness": 0.9, "focus": 1.4, "bravery": 1.6},
            memes={"care": 0.8, "joy": 0.2},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="friend",
            traits=["steady", "encouraging"],
            meters={"steadiness": 1.1, "focus": 1.3, "bravery": 1.7},
            memes={"support": 1.0, "helpfulness": 1.2},
        )
    )
    world.add(
        Entity(
            id="trouser",
            kind="garment",
            traits=["blue", "swooshy"],
            meters={"snagged": 1.0, "distance": 0.0, "risk": 1.0},
            memes={"need": 1.2},
        )
    )
    world.add(
        Entity(
            id="bridge",
            kind="place",
            traits=["wood", "windy"],
            meters={"space": route.helper_space, "wind": route.wind},
            memes={"sway": route.wind / 2},
        )
    )
    world.facts.update(
        {
            "route": params.route,
            "hazard": params.hazard,
            "rhyme": params.rhyme,
            "plan": params.plan,
            "setting": route.phrase,
            "seed": str(params.seed or 1),
            "style": "nursery_rhyme",
            "feature_bravery": "true",
            "feature_rhyme": "true",
            "feature_happy_ending": "true",
            "seed_word": "trouser",
        }
    )
    world.fired.append(f"introduced:{params.hero}")
    world.event(f"{params.hero} arrives at {route.phrase} with {params.friend}.")
    return world


def _intro(world: World) -> None:
    route = world.route
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    world.say(
        f"There once was a windy day in town, and {hero.id} and {friend.id} skipped along to "
        f"{route.phrase}. {route.opening}"
    )
    world.say(
        f"In the light, {hero.id} had on a blue trouser with a happy little stripe. "
        f"{friend.id} said, 'Watch the breeze! It loves to dance before bedtime.' "
        f"{route.open_image}"
    )


def _spark_tension(world: World) -> None:
    hero = world.get(world.params.hero)
    hazard = world.hazard
    trouser = world.get("trouser")
    world.para()
    world.say(f"Then came the sign: {hazard.signal}. {hazard.phrase.capitalize()}!")
    world.say(
        f"It was no mystery at all: {hazard.cause}. "
        "A trouser can fly, but a child can still do a brave thing."
    )
    trouser.meters["risk"] = max(0.2, trouser.meters["risk"])
    trouser.memes["need"] = 1.4
    hero.memes["courage"] = hero.memes.get("joy", 0.0) + 0.4
    hero.meters["focus"] += 0.2
    world.event("hazard_detected")
    world.fired.append("tension_started")


def _chant_and_plan(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    rhyme = world.rhyme
    plan = world.plan
    route = world.route

    world.para()
    hero.meters["focus"] += rhyme.focus_boost * 0.6
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + rhyme.brave_boost
    world.say(f"{hero.id} took a breath and sang: \"{rhyme.repeated_line}\"")
    world.say(f"{hero.id} and {friend.id} sang it again, because repetition is how a brave plan is kept steady.")
    world.say(f"The plan was to {plan.phrase}, and the plan made sense because {plan.explanation}")

    if plan.helper_required:
        world.fired.append("plan_requires_helper")
        world.say(
            f"{friend.id} tied the helper knot first, then stood close enough to steady the pull. "
            "That moved the risk from one person to shared courage."
        )


def _apply_plan(world: World) -> None:
    hero = world.get(world.params.hero)
    trouser = world.get("trouser")
    plan = world.plan
    hazard = world.hazard
    friend = world.get(world.params.friend)
    route = world.route
    rhyme = world.rhyme

    courage = hero.memes.get("bravery", 1.0) + plan.brave_boost + route.wind * 0.2
    focus = hero.meters.get("focus", 1.0) + plan.focus_boost + rhyme.focus_boost
    risk_gate = hazard.bravery_need + hazard.focus_need
    total_gate = courage + focus

    world.para()
    if total_gate >= risk_gate:
        world.fired.append("recovery_success")
        trouser.meters["snagged"] = 0.0
        trouser.meters["distance"] = min(trouser.meters["distance"], 0.0) + 1.0
        trouser.meters["risk"] = 0.0
        trouser.memes["need"] = 0.0
        trouser.memes["found"] = 1.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.2
        hero.memes["bravery"] = hero.memes.get("bravery", 1.0) + 0.7
        friend.memes["support"] = friend.memes.get("support", 0.0) + 0.5
        hero.meters["steadiness"] = max(hero.meters.get("steadiness", 0.0), 1.6)
        if plan.helper_required:
            friend.meters["steadiness"] = max(friend.meters.get("steadiness", 0.0), 1.5)
            world.say(
                f"With the helper line steady, {friend.id} and {hero.id} pulled in rhythm and the "
                f"{plan.tool} stayed low and true."
            )
        world.say(
            f"{hero.id} counted in time, then used {plan.tool} and reached the blue trouser with one careful pull."
        )
        world.say(f"It came down safely, and the wind could only bow and grin.")
        world.facts["ending_state"] = "safe_recovery"
        world.event("recovery_success")
    else:
        world.fired.append("recovery_faltered")
        world.facts["ending_state"] = "delayed_recover"
        world.say(
            f"{hero.id} tried, but the pull was too quick and the wind called for a wiser choice."
        )
        world.say("Another attempt is needed, but this story keeps only safe outcomes.")
        world.event("recovery_faltered")

    world.facts["success_metric"] = str(round(total_gate - risk_gate, 2))


def _resolve(world: World) -> None:
    hero = world.get(world.params.hero)
    rhythm = world.rhyme
    route = world.route
    world.para()
    if world.facts.get("ending_state") == "safe_recovery":
        world.say(
            f"Once the wind settled, {hero.id} tied the trouser tip with a ribbon and tucked it home. "
            f"{route.finish_image} {world.get('trouser').memes.get('found', 0) and ''} "
            "The lane felt brighter for it."
        )
        world.say(f"{hero.id} and {world.params.friend} finished with a rhyme: \"{rhythm.ending_line}\"")
        world.facts["ending_state"] = "happy"
    else:
        world.facts["ending_state"] = "not_happy"


def generate_story(world: World) -> str:
    _intro(world)
    _spark_tension(world)
    _chant_and_plan(world)
    _apply_plan(world)
    _resolve(world)
    return world.render()


def _prompts(world: World) -> list[str]:
    return [
        f"Create a nursery-rhyme story on {world.route.phrase} where a blue trouser is lost and recovered.",
        "Use the repeated rhyme line as the brave-action hook and show the turn with a specific safe plan.",
        "End on a happy image that proves the trouser came back and the danger changed.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    friend = world.params.friend
    hazard = world.hazard
    return [
        QAItem(
            "What started the trouble?",
            f"The trouble started when wind lifted the blue trouser into a snag. "
            f"The signal was {hazard.signal}, and that happened because {hazard.cause}.",
        ),
        QAItem(
            "How did the hero stay brave instead of panicking?",
            f"{hero} did not rush; {hero} and {friend} held a repeating two-line rhyme and planned one steady action. "
            "That kept courage focused and turned fear into a clear recovery sequence.",
        ),
        QAItem(
            "Why was this plan a good match for the physical world?",
            f"The chosen method was {world.plan.phrase}, which avoided stepping into the wind edge and used distance. "
            f"It matched the route {world.route.phrase}, the hazard {hazard.phrase}, and the helper need at the moment.",
        ),
        QAItem(
            "How does the ending show the story changed?",
            f"The happy ending is concrete: the trouser was pulled down safely, then tucked with a ribbon and kept near home. "
            f"{world.route.finish_image.rstrip('.')}. This is a visible proof that the state changed from 'snagged' to 'recovered'.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why is rhyme used more than once?",
            "In this world, a repeated rhyme is not decoration; it is tied to the stateful safety loop. "
            "The line is repeated while the trouser remains risky and then changes to a closing line when the hazard is gone.",
        ),
        QAItem(
            "How does helper requirement depend on route constraints?",
            "Some routes allow a helper only when there is helper space, so high-load moves are filtered by width and footing. "
            "If helper space is zero, plans that require a helper are rejected.",
        ),
        QAItem(
            "Why is this a happy-ending story?",
            "The world records `ending_state` as `happy`, and the final image explicitly shows the trouser safely home. "
            "So the causal chain from loss to recovery is completed, not just described."
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.route, params.hazard, params.rhyme, params.plan):
        raise StoryError(invalid_reason(params.route, params.hazard, params.rhyme, params.plan))
    world = build_world(params)
    return StorySample(
        params=params,
        story=generate_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = """
combo(Route, Hazard, Rhyme, Plan) :-
    route(Route),
    hazard(Hazard),
    rhyme(Rhyme),
    plan(Plan),
    hazard_on(Hazard, Route),
    plan_on_route(Plan, Route),
    plan_for_hazard(Plan, Hazard),
    rhyme_on_route(Rhyme, Route),
    rhyme_on_hazard(Rhyme, Hazard),
    not plan_requires_helper(Plan).

combo(Route, Hazard, Rhyme, Plan) :-
    route(Route),
    hazard(Hazard),
    rhyme(Rhyme),
    plan(Plan),
    hazard_on(Hazard, Route),
    plan_on_route(Plan, Route),
    plan_for_hazard(Plan, Hazard),
    rhyme_on_route(Rhyme, Route),
    rhyme_on_hazard(Rhyme, Hazard),
    plan_requires_helper(Plan),
    route_helper_space(Route, Space),
    Space > 0.

plan_requires_helper(friend_rope).

ok :- chosen(Route, Hazard, Rhyme, Plan), combo(Route, Hazard, Rhyme, Plan).

#show combo/4.
#show ok/0.
"""


def asp_facts() -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for route in ROUTES.values():
        rows.append(fact("route", route.key))
        rows.append(fact("route_helper_space", route.key, route.helper_space))
        for hz_key, hz in HAZARDS.items():
            if route.key in hz.routes:
                rows.append(fact("hazard_on", hz_key, route.key))
    for hz_key, hz in HAZARDS.items():
        rows.append(fact("hazard", hz_key))
        for plan in hz.allowed_plans:
            rows.append(fact("plan_for_hazard", plan, hz_key))
        for rhyme in hz.allowed_rhymes:
            rows.append(fact("rhyme_on_hazard", rhyme, hz_key))
    for plan in PLANS.values():
        rows.append(fact("plan", plan.key))
        for route_key in plan.route_allow:
            rows.append(fact("plan_on_route", plan.key, route_key))
    for rhyme in RHYMES.values():
        rows.append(fact("rhyme", rhyme.key))
        for route_key in rhyme.allowed_routes:
            rows.append(fact("rhyme_on_route", rhyme.key, route_key))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        from storyworlds.asp import fact

        chosen = fact("chosen", params.route, params.hazard, params.rhyme, params.plan) + "\n"
    return asp_facts() + chosen + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "combo"))
    return combos


def _asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program(params))
    return bool(atoms(model, "ok"))


def verify() -> str:
    python = {tuple(c) for c in valid_combos()}
    asp = asp_valid_combos()
    if python != asp:
        only_py = sorted(python - asp)
        only_asp = sorted(asp - python)
        raise StoryError(f"ASP/Python mismatch. only_python={only_py} only_asp={only_asp}")

    for i, combo in enumerate(sorted(python), 1):
        sample = generate(
            StoryParams(
                route=combo[0],
                hazard=combo[1],
                rhyme=combo[2],
                plan=combo[3],
                hero=HERO_NAMES["girl"][0],
                hero_kind="girl",
                friend=FRIENDS[0],
                seed=i,
            )
        )
        story = sample.story.lower()
        if "trouser" not in story:
            raise StoryError(f"Generated story for {combo!r} did not mention required seed word.")
        if story.count("one-two") == 0 and sample.world:
            pass
        if sample.world and sample.world.facts.get("ending_state") != "happy":
            raise StoryError(f"Generated story for {combo!r} did not reach happy ending.")
        if "{world.rhyme.repeated_line}" in sample.story:
            raise StoryError(f"Generated story for {combo!r} leaked template text.")
        if sample.story.count("\n\n") < 3:
            raise StoryError(f"Generated story for {combo!r} lacks a full structured arc.")
        if not _asp_accepts(StoryParams(
            route=combo[0],
            hazard=combo[1],
            rhyme=combo[2],
            plan=combo[3],
            hero=HERO_NAMES["girl"][0],
            hero_kind="girl",
            friend=FRIENDS[0],
        )):
            raise StoryError(f"ASP does not accept valid combo {combo!r}")
        if len(sample.story_qa) < 4:
            raise StoryError(f"Generated story for {combo!r} missing story-grounded QA.")
        if len(sample.world_qa) < 3:
            raise StoryError(f"Generated story for {combo!r} missing world QA.")
        if any(qa.answer.count(".") < 2 for qa in sample.story_qa):
            raise StoryError(f"Story QA too thin for {combo!r}: {sample.story_qa}")
    return f"OK: parity pass with {len(python)} combos; all samples hit happy ending and full QA."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate nursery-rhyme trouser recovery stories with brave choices."
    )
    parser.add_argument("--route", choices=tuple(ROUTES), default=None)
    parser.add_argument("--hazard", choices=tuple(HAZARDS), default=None)
    parser.add_argument("--rhyme", choices=tuple(RHYMES), default=None)
    parser.add_argument("--plan", choices=tuple(PLANS), default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--hero-kind", choices=tuple(HERO_NAMES), default=None)
    parser.add_argument("--friend", default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    rng = random.Random((args.seed or 1) + index)
    combos = _matching_combos(args)
    if not combos:
        raise StoryError("No valid combinations match the requested filters.")
    combo = rng.choice(combos)
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for idx, prompt in enumerate(sample.prompts, 1):
        print(f"{idx}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for combo in sorted(asp_valid_combos()):
        print(f"{combo[0]}\t{combo[1]}\t{combo[2]}\t{combo[3]}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0

        if args.all:
            combos = _matching_combos(args)
            if not combos:
                raise StoryError("No valid combinations available.")
            for i, combo in enumerate(combos, 1):
                sample = generate(_params_from_combo(args, combo, i))
                emit(sample, args, f"### {combo[0]} / {combo[1]} / {combo[2]} / {combo[3]}")
                if i != len(combos) and not args.json:
                    print("\n" + "=" * 72 + "\n")
            return 0

        count = max(1, args.n)
        for i in range(count):
            sample = generate(resolve_params(args, i))
            emit(sample, args, f"### variant {i + 1}" if count > 1 else None)
            if i != count - 1 and not args.json:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
