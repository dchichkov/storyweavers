#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.3-codex-spark/trouser_rhyme_happy_ending_bravery_nursery_rhyme.py
================================================================================

Seed words: trouser
Features: Rhyme, Happy Ending, Bravery
Style: Nursery Rhyme

Source tale written from seed:
A child in a windy lane loses a trouser over the edge of a tall play rope bridge.
Instead of giving up, the child and a friend recite a brave nursery rhyme together,
use a practical rescue plan, and bring the trouser back safely.
The trouble is solved because the physical plan, the setting limits, and the brave
song work together, and the ending image proves the recovery.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Route:
    key: str
    phrase: str
    opening: str
    width: int
    footing: int
    helper_space: int
    brave_bonus: int
    ending_image: str


@dataclass(frozen=True)
class TrouserHazard:
    key: str
    label: str
    routes: tuple[str, ...]
    signal: str
    mishap: str
    width_need: int
    footing_need: int
    bravery_need: int
    focus_need: int
    recovery_need: int
    help_needed: bool


@dataclass(frozen=True)
class Rhyme:
    key: str
    label: str
    chant: str
    bravery: float
    focus: float
    steadying: float


@dataclass(frozen=True)
class BravePlan:
    key: str
    label: str
    tool: str
    bravery: float
    focus: float
    recovery: float
    helper_needed: bool
    helper_bonus: float
    narration: str


@dataclass
class StoryParams:
    route: str
    hazard: str
    rhyme: str
    plan: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryWorld:
    params: StoryParams
    route: Route
    hazard: TrouserHazard
    rhyme: Rhyme
    plan: BravePlan
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    history: list[dict[str, str]] = field(default_factory=list)
    facts: dict[str, str | bool | int | float] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, ent_id: str) -> Entity:
        return self.entities[ent_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event: str, detail: str, result: str = "") -> None:
        self.history.append({"event": event, "detail": detail, "result": result})
        if result:
            self.say(result)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def dump_trace(self) -> str:
        out = ["--- world model state ---"]
        for ent in self.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            details = [f"kind={ent.kind}", f"type={ent.type}", f"label={ent.label}"]
            if meters:
                details.append(f"meters={dict(meters)}")
            if memes:
                details.append(f"memes={dict(memes)}")
            out.append(f"  {ent.id}: {' '.join(details)}")
        out.append(f"facts={dict(self.facts)}")
        out.append(f"history={self.history}")
        return "\n".join(out)


ROUTES: dict[str, Route] = {
    "latticed_lane": Route(
        "latticed_lane",
        "the latticed lane near the old clock tower",
        "a lane of painted stones and a small moon-shaped rope bridge near a windmill",
        width=2,
        footing=2,
        helper_space=1,
        brave_bonus=1,
        ending_image=(
            "The lane looked calm again, and the blue trouser hung clean and whole across"
            " the hero's arm, now tied with a bright ribbon and ready for tomorrow's play."
        ),
    ),
    "wobbly_boardway": Route(
        "wobbly_boardway",
        "the wobbly boardway beside the market pond",
        "a narrow board bridge over a little stream, with one side leaning in the wind",
        width=1,
        footing=3,
        helper_space=0,
        brave_bonus=0,
        ending_image=(
            "A soft bell rang by the pond as the boardway still held steady, and the blue trouser"
            " lay washed and warm in a basket, no longer tugged by the wind."
        ),
    ),
    "moonlit_garden": Route(
        "moonlit_garden",
        "the moonlit garden path behind the bakery",
        "a broad little bridge with a rail and a singing toy windmill watching from a corner",
        width=3,
        footing=3,
        helper_space=1,
        brave_bonus=2,
        ending_image=(
            "In the moonlit garden, the bridge sang softly, the wind settled, and the trouser"
            " fluttered lightly like a calm blue banner in the hero's hands."
        ),
    ),
}

HAZARDS: dict[str, TrouserHazard] = {
    "breezy_bridge": TrouserHazard(
        "breezy_bridge",
        "a trouser snagged on the bridge post",
        routes=("latticed_lane", "moonlit_garden", "wobbly_boardway"),
        signal="a tiny snap and a quick flapping sound up above the bridge",
        mishap=(
            "A clever gust snatched a blue trouser from the hero's knees and caught it on the"
            " high post by the bridge edge."
        ),
        width_need=2,
        footing_need=2,
        bravery_need=2,
        focus_need=1,
        recovery_need=3,
        help_needed=False,
    ),
    "swinging_plank": TrouserHazard(
        "swinging_plank",
        "a plank that swung like a giggle-bob and trapped the trouser",
        routes=("latticed_lane", "moonlit_garden"),
        signal="the soft thud of wood and a ribbon-tail rustle",
        mishap=(
            "The wind bounced the board and twined the hero's trouser in a swinging loop near"
            " the far side where footing felt tricky." 
        ),
        width_need=1,
        footing_need=2,
        bravery_need=3,
        focus_need=2,
        recovery_need=4,
        help_needed=False,
    ),
    "storm_rope": TrouserHazard(
        "storm_rope",
        "a storm-swollen rope and a stuck trouser knot",
        routes=("moonlit_garden",),
        signal="a wet pluck like a violin string from the rope",
        mishap=(
            "A stronger wind whipped the support rope hard, and the trouser made a brave but bad" 
            " loop around the knot where the bridge crossed above the lane."
        ),
        width_need=2,
        footing_need=2,
        bravery_need=4,
        focus_need=3,
        recovery_need=5,
        help_needed=True,
    ),
}

RHYTHMS: dict[str, Rhyme] = {
    "one_two_being": Rhyme(
        "one_two_being",
        "one-two-brave",
        '"One, two, step! One, two, cheer! Keep your feet and keep it near. "',
        bravery=2,
        focus=1,
        steadying=1,
    ),
    "dawn_and_dip": Rhyme(
        "dawn_and_dip",
        "dawn-and-dip",
        '"Up on the lane, down on the wind, brave hearts count before we begin. "',
        bravery=1,
        focus=3,
        steadying=2,
    ),
    "brave_beat": Rhyme(
        "brave_beat",
        "brave beat",
        '"Brave and bright, brave and bold, we can face the wind and hold. "',
        bravery=3,
        focus=2,
        steadying=3,
    ),
}

PLANS: dict[str, BravePlan] = {
    "borrow_ladder": BravePlan(
        "borrow_ladder",
        "lean-and-lift with a borrowed ladder",
        "a light ladder",
        bravery=1,
        focus=2,
        recovery=3,
        helper_needed=False,
        helper_bonus=0,
        narration=(
            "They set a small ladder beside the post, held it with both hands, and"
            " lifted the trouser with careful patience."
        ),
    ),
    "friended_bridge": BravePlan(
        "friended_bridge",
        "steady bridge handoff with a friend",
        "a helper's steady hands",
        bravery=2,
        focus=2,
        recovery=4,
        helper_needed=True,
        helper_bonus=1,
        narration=(
            "The friend moved beside the hero, gave a solid hand, and made a quiet two-step"
            " rhythm that kept the hands from shaking."
        ),
    ),
    "rope_loop": BravePlan(
        "rope_loop",
        "loop and pull with a long cloth-rope",
        "a soft cloth rope",
        bravery=2,
        focus=3,
        recovery=5,
        helper_needed=False,
        helper_bonus=0,
        narration=(
            "They threw a long cloth rope, made a quick loop, and used it like a gentle harness"
            " to draw the trouser down from the high post."
        ),
    ),
}

NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Lina", "Milo", "Ari", "Nora"),
    "boy": ("Tavi", "Omar", "Noah", "Kian"),
    "child": ("Briar", "Sage", "Will", "Moss"),
}

FRIEND_CHOICES = ("Mina", "Jules", "Pip", "Ollie", "Ari", "Lila", "Noor")

CURATED: list[StoryParams] = [
    StoryParams("latticed_lane", "breezy_bridge", "one_two_being", "borrow_ladder", "Lina", "girl", "Mina", "boy"),
    StoryParams("moonlit_garden", "storm_rope", "brave_beat", "friended_bridge", "Omar", "boy", "Nina", "girl"),
    StoryParams("moonlit_garden", "swinging_plank", "dawn_and_dip", "rope_loop", "Sage", "child", "Pip", "boy"),
    StoryParams("wobbly_boardway", "breezy_bridge", "dawn_and_dip", "borrow_ladder", "Will", "child", "Lila", "girl"),
]


def _pick_name(pool: tuple[str, ...], rng: random.Random) -> str:
    return rng.choice(pool)


def _pick_friend(rng: random.Random) -> str:
    return rng.choice(FRIEND_CHOICES)


def valid_combo(route_key: str, hazard_key: str, rhyme_key: str, plan_key: str) -> bool:
    if route_key not in ROUTES or hazard_key not in HAZARDS or rhyme_key not in RHYTHMS or plan_key not in PLANS:
        return False
    route = ROUTES[route_key]
    hazard = HAZARDS[hazard_key]
    rhyme = RHYTHMS[rhyme_key]
    plan = PLANS[plan_key]

    if route.key not in hazard.routes:
        return False
    if route.width < hazard.width_need:
        return False
    if route.footing < hazard.footing_need:
        return False
    if route.helper_space < 1 and (hazard.help_needed or plan.helper_needed):
        return False
    if rhyme.bravery + plan.bravery < hazard.bravery_need:
        return False
    if rhyme.focus + plan.focus < hazard.focus_need:
        return False
    return rhyme.steadying + plan.recovery + route.brave_bonus >= hazard.recovery_need


def combo_reason(route_key: str, hazard_key: str, rhyme_key: str, plan_key: str) -> str:
    if route_key not in ROUTES:
        return f"No story: unknown route {route_key!r}."
    if hazard_key not in HAZARDS:
        return f"No story: unknown hazard {hazard_key!r}."
    if rhyme_key not in RHYTHMS:
        return f"No story: unknown rhyme {rhyme_key!r}."
    if plan_key not in PLANS:
        return f"No story: unknown rescue plan {plan_key!r}."

    route = ROUTES[route_key]
    hazard = HAZARDS[hazard_key]
    rhyme = RHYTHMS[rhyme_key]
    plan = PLANS[plan_key]

    if route.key not in hazard.routes:
        return "The selected route does not let this hazard happen there."
    if route.width < hazard.width_need:
        return f"The route {route.phrase} is too narrow for this hazard."
    if route.footing < hazard.footing_need:
        return f"The route footing in {route.phrase} is too unsure for safe recovery."
    if route.helper_space < 1 and (hazard.help_needed or plan.helper_needed):
        return f"This recovery needs a helper, but {route.phrase} does not allow one safely."
    if rhyme.bravery + plan.bravery < hazard.bravery_need:
        return (
            "The rhyme and rescue plan do not add enough courage to match the hazard"
            f" ({rhyme.bravery + plan.bravery} < {hazard.bravery_need})."
        )
    if rhyme.focus + plan.focus < hazard.focus_need:
        return (
            "The rhyme and rescue plan do not give enough focus for this hazard"
            f" ({rhyme.focus + plan.focus} < {hazard.focus_need})."
        )
    if rhyme.steadying + plan.recovery + route.brave_bonus < hazard.recovery_need:
        return (
            f"This route and rescue are not enough to recover from the hazard safely"
            f" ({rhyme.steadying + plan.recovery + route.brave_bonus} < {hazard.recovery_need})."
        )
    return ""


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for route_id in sorted(ROUTES):
        for hazard_id in sorted(HAZARDS):
            for rhyme_id in sorted(RHYTHMS):
                for plan_id in sorted(PLANS):
                    if valid_combo(route_id, hazard_id, rhyme_id, plan_id):
                        combos.append((route_id, hazard_id, rhyme_id, plan_id))
    return combos


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.route is None or c[0] == args.route)
        and (args.hazard is None or c[1] == args.hazard)
        and (args.rhyme is None or c[2] == args.rhyme)
        and (args.plan is None or c[3] == args.plan)
    ]
    return filtered


def _params_from_combo(args: argparse.Namespace, combo: tuple[str, str, str, str], idx: int) -> StoryParams:
    rng = random.Random((args.seed or 0) + idx)
    hero_type = args.hero_type or rng.choice(sorted(NAMES))
    friend_type = args.friend_type or rng.choice(sorted(NAMES))
    hero = args.hero or _pick_name(NAMES[hero_type], rng)
    friend = args.friend or _pick_friend(rng)

    if friend == hero:
        if friend_type in NAMES and len(NAMES[friend_type]) > 1:
            friend = _pick_name(NAMES[friend_type], random.Random((args.seed or 0) + idx + 11))
        else:
            friend = f"{friend} Jr"

    route_id, hazard_id, rhyme_id, plan_id = combo
    return StoryParams(
        route=route_id,
        hazard=hazard_id,
        rhyme=rhyme_id,
        plan=plan_id,
        hero=hero,
        hero_type=hero_type,
        friend=friend,
        friend_type=friend_type,
        seed=(args.seed or 0) + idx,
    )


def reasonableness_gate(params: StoryParams) -> None:
    reason = combo_reason(params.route, params.hazard, params.rhyme, params.plan)
    if reason:
        raise StoryError(reason)


def build_world(params: StoryParams) -> StoryWorld:
    reasonableness_gate(params)

    route = ROUTES[params.route]
    hazard = HAZARDS[params.hazard]
    rhyme = RHYTHMS[params.rhyme]
    plan = PLANS[params.plan]

    world = StoryWorld(params=params, route=route, hazard=hazard, rhyme=rhyme, plan=plan)

    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type=params.hero_type,
            label=params.hero,
            traits=["curious", "brave"],
            meters={"steadiness": 0.9, "ready": 1.0},
            memes={
                "calm": 0.6,
                "hope": 0.8,
                "fear": 0.0,
                "focus": 0.0,
                "courage": 0.0,
                "joy": 0.0,
                "bravery": 0.0,
            },
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="character",
            type=params.friend_type,
            label=params.friend,
            traits=["steady"],
            meters={"steadiness": 1.2},
            memes={"patience": 0.9, "steadying": 0.0, "joy": 0.0},
        )
    )
    world.add(
        Entity(
            id="trouser",
            kind="clothing",
            type="trouser",
            label="the blue trouser",
            meters={"stuck": 1.0, "distance": 1.0},
            memes={"comfort": 0.1, "risk": 1.2},
        )
    )
    world.add(
        Entity(
            id="bridge",
            kind="place",
            type="bridge",
            label=route.phrase,
            meters={"width": route.width, "footing": route.footing},
            memes={"safe": 0.0},
        )
    )
    world.add(
        Entity(
            id="wind",
            kind="weather",
            type="wind",
            label="the lane wind",
            meters={"force": 1.0},
            memes={"nervous": 0.3},
        )
    )

    world.facts.update(
        {
            "route": route.key,
            "hazard": hazard.key,
            "rhyme": rhyme.key,
            "plan": plan.key,
            "hero": hero.id,
            "friend": friend.id,
            "seed": params.seed,
            "style": "nursery_rhyme",
            "feature": "bravery+rhythm",
            "seed_word": "trouser",
        }
    )

    return world


def _hero(world: StoryWorld) -> Entity:
    return world.get(world.params.hero)


def _friend(world: StoryWorld) -> Entity:
    return world.get(world.params.friend)


def intro(world: StoryWorld) -> None:
    hero = _hero(world)
    route = world.route
    world.say(
        f"Once upon a time, there was a little {hero.type} named {hero.id}. "
        f"{hero.id} came to {route.phrase} for a windy afternoon rhyme game."
    )
    world.say(f"The opening scene was {route.opening}.")
    world.record("premise", "hero steps into route",
                 f"{hero.id} wore a bright blue trouser with pockets that jingled like tiny bells.")


def trouble(world: StoryWorld) -> None:
    hero = _hero(world)
    hazard = world.hazard
    world.say(hazard.signal)
    world.say(f"Then {hazard.mishap}")
    trouser = world.get("trouser")
    trouser.memes["risk"] += 0.8
    hero.memes["fear"] += hazard.bravery_need
    hero.memes["focus"] = 0.6
    world.record("trouble", "wind snag", f"The blue trouser was now stuck high above the route on the {hazard.label}.")


def turn(world: StoryWorld) -> None:
    hero = _hero(world)
    friend = _friend(world)
    route = world.route
    plan = world.plan
    rhyme = world.rhyme
    hazard = world.hazard
    trouser = world.get("trouser")

    world.say(
        f"{friend.id} looked up and said, \"We can do this, one brave heartbeat at a time!\""
    )
    world.say(
        f"They tapped the ground twice, then {hero.id} sang, {rhyme.chant}"
    )

    courage_total = rhyme.bravery + plan.bravery + route.brave_bonus
    focus_total = rhyme.focus + plan.focus
    steady_total = rhyme.steadying + plan.recovery

    world.say(
        f"Their chosen brave plan was {plan.label}. {plan.narration}"
    )

    world.record(
        "turn_plan",
        "rhyme + plan",
        f"Bravery check: {courage_total}/{hazard.bravery_need}, focus check: {focus_total}/{hazard.focus_need}"
    )

    hero.memes["courage"] += courage_total
    hero.memes["focus"] = max(hero.memes.get("focus", 0.0), focus_total)
    hero.memes["joy"] += plan.focus * 0.5

    if plan.helper_needed:
        if route.helper_space < 1:
            raise StoryError("This plan needs a helper, but the route cannot hold one safely.")
        friend.memes["steadying"] += plan.helper_bonus
        world.say(
            f"{friend.id} stood close, gave a steady hand, and added a calm helper beat." 
        )

    if courage_total < hazard.bravery_need:
        raise StoryError("Even with help, bravery was not enough for this recovery.")
    if focus_total < hazard.focus_need:
        raise StoryError("Focus was not enough to finish the rescue safely.")
    if steady_total + route.brave_bonus < hazard.recovery_need:
        raise StoryError("The chosen action did not provide enough recovery strength for this hazard.")

    trouser.meters["stuck"] = 0.0
    trouser.meters["distance"] = 0.0
    trouser.memes["risk"] = 0.0
    trouser.memes["safety"] = 1.0
    wind = world.get("wind")
    wind.meters["force"] = max(0.0, wind.meters["force"] - 0.7)
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.memes["bravery"] += 1.0
    friend.memes["joy"] += 1.0
    world.facts["resolved"] = True
    world.record("turn", "recovery", "The blue trouser came loose and was safely lowered.")


def finish(world: StoryWorld) -> None:
    hero = _hero(world)
    friend = _friend(world)
    world.para()
    route = world.route
    ending = route.ending_image.replace("blue trouser", "the blue trouser")
    world.facts["ending_image"] = ending

    world.say(f"Then the bridge settled, and {ending}")
    world.say(
        f"{hero.id} and {friend.id} smiled, and {hero.id} learned that bravery can be"
        " a rhythm, not a shout: a brave heart, one clear plan, and a kind friend side by side."
    )


def generate_story(world: StoryWorld) -> StoryWorld:
    intro(world)
    world.para()
    trouble(world)
    world.para()
    turn(world)
    finish(world)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    return [
        "Write a nursery-rhyme style rescue story about a trouser lost on a windy route.",
        f"Use a rhyme line and a brave helper action to solve the problem in {world.route.phrase}.",
        "End with a concrete happy image showing the recovery succeeded and the danger is gone.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    route = world.route
    hazard = world.hazard
    trouser = world.get("trouser")

    outcome = "safe" if world.facts.get("resolved") else "still stuck"
    return [
        QAItem(
            "Where does the story happen?",
            f"It happens in {route.phrase}. The lane setting is important because the width and"
            f" footing of that bridge changed how carefully the child had to move."
            " So the place itself becomes part of the rescue, not just a backdrop.",
        ),
        QAItem(
            "What created the problem?",
            "The wind tore the child's blue trouser away and caught it on the route obstacle."
            " That created a physical snag high above, and because it was tied to height and"
            " wind, it could not be solved by guessing.",
        ),
        QAItem(
            "How did the hero solve it?",
            f"The hero and {friend.label} used the plan {world.plan.label}."
            f" That gave tools, steadiness, and a clear sequence, while the hero's rhyme line kept them"
            " moving with attention."
        ),
        QAItem(
            "How did bravery show up in the story?",
            f"Bravery appeared as action, not as magic: when {hero.id} felt fear rise,"
            " they still held to the rhyme and used the practical recovery method."
            " Because the brave line and the calm plan matched the hazard needs, the result stayed"
            " safe instead of becoming reckless.",
        ),
        QAItem(
            "What changed by the ending?",
            f"The ending image shows the change: {world.facts.get('ending_image')}."
            " The meter states in the world moved too; the trouser is no longer stuck, and its"
            f" risk level dropped to {trouser.memes['risk']:.1f}, so the world ended in a happy, grounded state.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    hazard = world.hazard
    rhyme = world.rhyme
    plan = world.plan
    route = world.route

    return [
        QAItem(
            "Why must this world run a reasonableness gate before rendering?",
            "Without the gate, it could generate a setup where a route is too narrow or footing too weak"
            " for the hazard. The gate prevents that by checking physical compatibility directly"
            " before story time, so stories stay grounded in what could actually happen.",
        ),
        QAItem(
            f"Why does the rhyme matter for bravery in this world?",
            "The rhyme is not decoration; it raises bravery and steadying support in the state model."
            f" Here it contributes {rhyme.bravery:.0f} bravery points and {rhyme.steadying:.0f} steadying support."
            " Those values combine with route and plan qualities to decide if recovery is safe.",
        ),
        QAItem(
            f"How could this story fail in this model?",
            f"Recovery can fail if the hero's courage and focus checks do not meet the {hazard.label}"
            " needs, if the wrong route is too narrow, or if a helper-dependent plan is used"
            " where no helper space exists. When that happens, the trace would show the trouser"
            " still above the bridge and the ending image would not become a safe recovery.",
        ),
        QAItem(
            "What proves success in the final world state?",
            f"Success is explicit: the entity `trouser` has `stuck=0`, `distance=0`, and `safety=1`."
            " In this design, that means the action moved the object from hanging risk to a safe recovered state.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = generate_story(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(Route, Hazard, Rhyme, Plan) :-
    route(Route, W, F, Helper, Bonus),
    hazard(Hazard, Route, WidthNeed, FootingNeed, BrNeed, FoNeed, RecoveryNeed, HNeed),
    rhyme(Rhyme, RBr, RFo, RSt),
    plan(Plan, PBr, PFo, PRc, PHelp, _),
    W >= WidthNeed,
    F >= FootingNeed,
    RBr + PBr >= BrNeed,
    RFo + PFo >= FoNeed,
    RSt + PRc + Bonus >= RecoveryNeed,
    Helper >= HNeed,
    Helper >= PHelp.

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for route in sorted(ROUTES.values(), key=lambda r: r.key):
        rows.append(asp.fact("route", route.key, route.width, route.footing, route.helper_space, route.brave_bonus))
    for hazard in sorted(HAZARDS.values(), key=lambda h: h.key):
        for allowed_route in hazard.routes:
            rows.append(
                asp.fact(
                    "hazard",
                    hazard.key,
                    allowed_route,
                    hazard.width_need,
                    hazard.footing_need,
                    hazard.bravery_need,
                    hazard.focus_need,
                    hazard.recovery_need,
                    1 if hazard.help_needed else 0,
                )
            )
    for rhyme in sorted(RHYTHMS.values(), key=lambda r: r.key):
        rows.append(asp.fact("rhyme", rhyme.key, rhyme.bravery, rhyme.focus, rhyme.steadying))
    for plan in sorted(PLANS.values(), key=lambda p: p.key):
        rows.append(
            asp.fact(
                "plan",
                plan.key,
                plan.bravery,
                plan.focus,
                plan.recovery,
                1 if plan.helper_needed else 0,
                plan.helper_bonus,
            )
        )
    return "\n".join(rows)


def asp_program(params: StoryParams | None = None) -> str:
    import asp

    chosen = ""
    if params is not None:
        chosen = asp.fact(
            "selected",
            params.route,
            params.hazard,
            params.rhyme,
            params.plan,
        ) + "\n"
    return f"{ASP_RULES}\n{asp_facts()}\n{chosen}"


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str]] = set()
    for model in asp.solve(asp_program(), models=0):
        combos.update(asp.atoms(model, "valid"))
    return combos


def _asp_accepts(params: StoryParams) -> bool:
    import asp

    check_program = (
        asp_program(params)
        + "\n"
        + "ok :- selected(R, H, Rh, P), valid(R, H, Rh, P).\n"
        + "#show ok/0."
    )
    model = asp.one_model(check_program)
    return bool(asp.atoms(model, "ok"))


def verify() -> str:
    py_set = set(valid_combos())
    asp_set = asp_valid_combos()
    if py_set != asp_set:
        raise StoryError(f"ASP/Python mismatch. only_python={sorted(py_set - asp_set)} only_asp={sorted(asp_set - py_set)}")

    sample_indexes = sorted(py_set)[:6]
    for idx, combo in enumerate(sample_indexes, 1):
        params = StoryParams(*combo, hero="Lina", hero_type="girl", friend="Mina", friend_type="boy", seed=idx)  # type: ignore[arg-type]
        if not _asp_accepts(params):
            raise StoryError(f"ASP rejected valid combo {combo!r}.")

        sample = generate(params)
        if not sample.world:
            raise StoryError(f"Missing world for {combo!r}.")
        if "trouser" not in sample.story.lower():
            raise StoryError(f"Generated story for {combo!r} forgot the seed word trouser.")
        if sample.story.count("\n\n") < 2:
            raise StoryError(f"Generated story for {combo!r} lacks beginning, turn, and ending.")
        if not sample.prompts or len(sample.prompts) < 3:
            raise StoryError(f"Generated story for {combo!r} is missing prompts.")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            raise StoryError(f"Generated story for {combo!r} is missing QA breadth.")
        for qa in sample.story_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"Story QA answer too short for {combo!r}: {qa.question!r}")
        for qa in sample.world_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"World QA answer too short for {combo!r}: {qa.question!r}")
        if any(token in sample.story for token in ["{", "}", "meters", "memes", "World("]):
            raise StoryError(f"Story for {combo!r} leaked scaffold text.")

    return f"OK: {len(py_set)} valid Python combos, and ASP parity plus sample checks passed."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nursery-rhyme trouser rescue world with bravery and rhyme.")
    parser.add_argument("--route", choices=sorted(ROUTES), default=None)
    parser.add_argument("--hazard", choices=sorted(HAZARDS), default=None)
    parser.add_argument("--rhyme", choices=sorted(RHYTHMS), default=None)
    parser.add_argument("--plan", choices=sorted(PLANS), default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--hero-type", choices=sorted(NAMES), default=None)
    parser.add_argument("--friend", default=None)
    parser.add_argument("--friend-type", choices=sorted(NAMES), default=None)
    parser.add_argument("-n", type=int, default=1, help="number of stories")
    parser.add_argument("--all", action="store_true", help="render curated examples")
    parser.add_argument("--seed", type=int, default=None, help="base random seed")
    parser.add_argument("--trace", action="store_true", help="dump world trace")
    parser.add_argument("--qa", action="store_true", help="include prompts + QA")
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    parser.add_argument("--asp", action="store_true", help="show valid (route,hazard,rhyme,plan) tuples")
    parser.add_argument("--verify", action="store_true", help="run verify and exit")
    parser.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return parser


def _print_qa(sample: StorySample) -> None:
    print("== Generation prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print()
    print("== Story-grounded QA ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print()
    print("== World-knowledge QA ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        _print_qa(sample)
    if trace and sample.world is not None:
        print("\n" + sample.world.dump_trace())


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    candidates = matching_combos(args)
    if not candidates:
        raise StoryError("No valid combinations match the requested filters.")
    combo = rng.choice(candidates)
    params = _params_from_combo(args, combo, index)
    if args.route is None and args.hazard is None and args.rhyme is None and args.plan is None:
        return params
    # If explicit filters are active, use first matching combo to keep deterministic behavior.
    return params


def resolve_with_filters(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = matching_combos(args)
    if not combos:
        raise StoryError(
            "No story: no valid route/hazard/rhyme/plan combo matches your filters. "
            "Try relaxing one constraint."
        )
    if args.route is not None and args.hazard is not None and args.rhyme is not None and args.plan is not None:
        combo = (args.route, args.hazard, args.rhyme, args.plan)
    else:
        combo = rng.choice(combos)
    return _params_from_combo(args, combo, args.seed or 0)


def print_asp() -> None:
    print(asp_program())



def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print_asp()
        return
    if args.verify:
        try:
            print(verify())
            sys.exit(0)
        except StoryError as exc:
            print(exc, file=sys.stderr)
            sys.exit(1)
    if args.asp:
        for route, hazard, rhyme, plan in sorted(asp_valid_combos()):
            print(f"{route}\t{hazard}\t{rhyme}\t{plan}")
        return

    try:
        samples: list[StorySample] = []
        if args.all:
            samples = [generate(params) for params in CURATED]
        else:
            base_seed = args.seed if args.seed is not None else random.randrange(2**31)
            seen: set[str] = set()
            i = 0
            while len(samples) < args.n and i < max(args.n * 50, 60):
                i += 1
                params = resolve_params(args, random.Random(base_seed + i), i)
                sample = generate(params)
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return

        for index, sample in enumerate(samples):
            header = ""
            if args.all:
                p = sample.params
                header = f"### {p.route} / {p.hazard} / {p.rhyme} / {p.plan}"
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        print(exc, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
