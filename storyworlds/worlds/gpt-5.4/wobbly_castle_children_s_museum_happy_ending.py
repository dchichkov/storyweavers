#!/usr/bin/env python3
"""
wobbly_castle_children_s_museum_happy_ending.py
================================================

Internal source tale:
    A child visits a children's museum and longs to carry a cloth star through
    a wobbly castle exhibit. The bridge or ramp trembles, the child pauses,
    then uses the right brave plan to cross safely, reach the turret, and end
    in a bright, happy image.

This world keeps the domain small and constrained on purpose. The stateful turn
is always about a brave choice inside the museum's wobbly castle, and the
ending image proves that the child changed from hesitant to proud.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Bridge:
    key: str
    phrase: str
    footing: str
    view: str
    allows_wobbles: tuple[str, ...]
    prize: str
    height_meters: float


@dataclass(frozen=True)
class Wobble:
    key: str
    phrase: str
    cause: str
    need: str
    risk: str
    tremble_meters: float


@dataclass(frozen=True)
class BravePlan:
    key: str
    phrase: str
    action: str
    helper_name: str
    helper_role: str
    helper_phrase: str
    solves: tuple[str, ...]
    rhyme: str


@dataclass(frozen=True)
class Prize:
    key: str
    phrase: str
    ending_image: str
    lesson: str


@dataclass
class StoryParams:
    bridge: str
    wobble: str
    plan: str
    prize: str
    hero: str
    gender: str
    seed: int | None = None


@dataclass
class Entity:
    key: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    summary: str


@dataclass
class World:
    params: StoryParams
    bridge: Bridge
    wobble: Wobble
    plan: BravePlan
    prize: Prize
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)
    story: str = ""

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def add_event(self, event_id: str, summary: str) -> None:
        self.history.append(Event(event_id, summary))

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(
            f"  params: bridge={self.params.bridge}, wobble={self.params.wobble}, "
            f"plan={self.params.plan}, prize={self.params.prize}, hero={self.params.hero}"
        )
        for key, ent in self.entities.items():
            meters = ", ".join(f"{name}={value:g}" for name, value in sorted(ent.meters.items())) or "none"
            memes = ", ".join(f"{name}={value:g}" for name, value in sorted(ent.memes.items())) or "none"
            notes = ", ".join(f"{name}={value}" for name, value in sorted(ent.notes.items())) or "none"
            lines.append(f"  {key}: {ent.label} ({ent.kind})")
            lines.append(f"    meters: {meters}")
            lines.append(f"    memes: {memes}")
            lines.append(f"    notes: {notes}")
        lines.append(f"  facts: {self.facts}")
        lines.append("  history:")
        for event in self.history:
            lines.append(f"    - {event.id}: {event.summary}")
        return "\n".join(lines)


BRIDGES: dict[str, Bridge] = {
    "banner_bridge": Bridge(
        key="banner_bridge",
        phrase="the banner bridge inside the wobbly castle",
        footing="padded blue planks and ribbon rails",
        view="paper pennants flickering above beanbag dragons",
        allows_wobbles=("sway",),
        prize="bell",
        height_meters=1.2,
    ),
    "cushion_steps": Bridge(
        key="cushion_steps",
        phrase="the cushion steps by the castle gate",
        footing="round foam stones that dip and rise",
        view="painted mice in armor peeking from the wall",
        allows_wobbles=("bounce",),
        prize="stamp",
        height_meters=0.8,
    ),
    "moon_ramp": Bridge(
        key="moon_ramp",
        phrase="the moon ramp curling to the turret window",
        footing="a silver slope and cloud-soft rails",
        view="a tall window shining on velvet stars",
        allows_wobbles=("tilt",),
        prize="flag",
        height_meters=1.5,
    ),
}

WOBBLES: dict[str, Wobble] = {
    "sway": Wobble(
        key="sway",
        phrase="a side-to-side sway",
        cause="the hanging bridge rocked when small feet landed together",
        need="rail",
        risk="freezing in the middle",
        tremble_meters=0.7,
    ),
    "bounce": Wobble(
        key="bounce",
        phrase="a bobbing bounce",
        cause="the foam stones bounced back with springy little hops",
        need="count",
        risk="rushing two steps at once",
        tremble_meters=0.8,
    ),
    "tilt": Wobble(
        key="tilt",
        phrase="a gentle leaning tilt",
        cause="the curved ramp tipped higher near the bright turret glass",
        need="hand",
        risk="stopping halfway up the climb",
        tremble_meters=0.9,
    ),
}

PLANS: dict[str, BravePlan] = {
    "rail_touch": BravePlan(
        key="rail_touch",
        phrase="the ribbon-rail plan",
        action="kept one hand on the ribbon rail and one foot on each blue plank",
        helper_name="Guide June",
        helper_role="museum guide",
        helper_phrase="Guide June pointed to the rail and nodded in time",
        solves=("rail",),
        rhyme="Hand to the rail, slow as a snail.",
    ),
    "counting_rhyme": BravePlan(
        key="counting_rhyme",
        phrase="the counting rhyme plan",
        action="landed one careful foot on each round stone",
        helper_name="Drum Dot",
        helper_role="museum drummer",
        helper_phrase="Drum Dot tapped a tiny beat on a soft parade drum",
        solves=("count",),
        rhyme="One, two, three, step small as can be.",
    ),
    "helper_hand": BravePlan(
        key="helper_hand",
        phrase="the helper-hand plan",
        action="held a grown-up hand at the steep part and looked at the window star instead of the floor",
        helper_name="Dad",
        helper_role="careful grown-up",
        helper_phrase="Dad stood beside the ramp with a warm and steady palm",
        solves=("hand",),
        rhyme="Hand in hand, brave we stand.",
    ),
}

PRIZES: dict[str, Prize] = {
    "bell": Prize(
        key="bell",
        phrase="the brass bell in the top arch",
        ending_image="the brass bell chimed while paper pennants skipped in the museum light",
        lesson="Bravery can sound bright when a child goes slowly and uses the safe support nearby.",
    ),
    "stamp": Prize(
        key="stamp",
        phrase="the star stamp by the gate table",
        ending_image="a gold star stamp bloomed on the museum card beside a grinning castle mouse",
        lesson="Bravery can look small from far away, yet steady little steps carry it all the same.",
    ),
    "flag": Prize(
        key="flag",
        phrase="the satin flag at the turret window",
        ending_image="the satin flag fluttered by the high window while the whole castle glowed soft and glad",
        lesson="Bravery grows when a child takes safe help and keeps moving toward the bright place ahead.",
    ),
}

HEROES: dict[str, tuple[str, ...]] = {
    "girl": ("Mina", "Tess", "Lila", "Poppy"),
    "boy": ("Owen", "Nico", "Rory", "Jude"),
}


def _pronouns(gender: str) -> tuple[str, str]:
    if gender == "boy":
        return ("he", "his")
    return ("she", "her")


def valid_combo(bridge_key: str, wobble_key: str, plan_key: str, prize_key: str) -> bool:
    if bridge_key not in BRIDGES or wobble_key not in WOBBLES or plan_key not in PLANS or prize_key not in PRIZES:
        return False
    bridge = BRIDGES[bridge_key]
    wobble = WOBBLES[wobble_key]
    plan = PLANS[plan_key]
    prize = PRIZES[prize_key]
    if wobble.key not in bridge.allows_wobbles:
        return False
    if wobble.need not in plan.solves:
        return False
    if bridge.prize != prize.key:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for bridge_key in sorted(BRIDGES):
        for wobble_key in sorted(WOBBLES):
            for plan_key in sorted(PLANS):
                for prize_key in sorted(PRIZES):
                    if valid_combo(bridge_key, wobble_key, plan_key, prize_key):
                        combos.append((bridge_key, wobble_key, plan_key, prize_key))
    return combos


def explain_rejection(bridge_key: str, wobble_key: str, plan_key: str, prize_key: str) -> str:
    if bridge_key not in BRIDGES:
        return f"No story: unknown bridge {bridge_key!r}."
    if wobble_key not in WOBBLES:
        return f"No story: unknown wobble {wobble_key!r}."
    if plan_key not in PLANS:
        return f"No story: unknown brave plan {plan_key!r}."
    if prize_key not in PRIZES:
        return f"No story: unknown prize {prize_key!r}."
    bridge = BRIDGES[bridge_key]
    wobble = WOBBLES[wobble_key]
    plan = PLANS[plan_key]
    prize = PRIZES[prize_key]
    if wobble.key not in bridge.allows_wobbles:
        return f"No story: {bridge.phrase} does not wobble with {wobble.phrase}."
    if wobble.need not in plan.solves:
        return (
            f"No story: {plan.phrase} does not solve the problem of {wobble.phrase}. "
            f"The child needs support for {wobble.need!r} here."
        )
    if bridge.prize != prize.key:
        expected = PRIZES[bridge.prize].phrase
        return f"No story: {bridge.phrase} leads to {expected}, not {prize.phrase}."
    return "No story: that museum setup is outside this world's reasonable choices."


def params_from_combo(combo: tuple[str, str, str, str], seed: int, hero: str | None = None, gender: str | None = None) -> StoryParams:
    chosen_gender = gender or ("girl" if seed % 2 == 0 else "boy")
    chosen_hero = hero or HEROES[chosen_gender][seed % len(HEROES[chosen_gender])]
    return StoryParams(
        bridge=combo[0],
        wobble=combo[1],
        plan=combo[2],
        prize=combo[3],
        hero=chosen_hero,
        gender=chosen_gender,
        seed=seed,
    )


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    return [
        combo
        for combo in valid_combos()
        if (args.bridge is None or combo[0] == args.bridge)
        and (args.wobble is None or combo[1] == args.wobble)
        and (args.plan is None or combo[2] == args.plan)
        and (args.prize is None or combo[3] == args.prize)
    ]


def build_world(params: StoryParams) -> World:
    if params.gender not in HEROES:
        raise StoryError(f"No story: unknown gender group {params.gender!r}.")
    if not valid_combo(params.bridge, params.wobble, params.plan, params.prize):
        raise StoryError(explain_rejection(params.bridge, params.wobble, params.plan, params.prize))

    bridge = BRIDGES[params.bridge]
    wobble = WOBBLES[params.wobble]
    plan = PLANS[params.plan]
    prize = PRIZES[params.prize]

    world = World(params=params, bridge=bridge, wobble=wobble, plan=plan, prize=prize)
    world.entities["museum"] = Entity(
        key="museum",
        label="the children's museum",
        kind="place",
        meters={"light": 1.0, "open": 1.0},
        memes={"wonder": 1.2},
        notes={"room": "climbing court"},
    )
    world.entities["castle"] = Entity(
        key="castle",
        label="the wobbly castle",
        kind="exhibit",
        meters={
            "height": bridge.height_meters,
            "wobble": wobble.tremble_meters,
            "safe_path": 0.0,
            "prize_reached": 0.0,
        },
        memes={"welcome": 1.0},
        notes={"view": bridge.view, "footing": bridge.footing},
    )
    world.entities["hero"] = Entity(
        key="hero",
        label=params.hero,
        kind="child",
        meters={"feet_forward": 0.0, "pause": 0.0, "at_turret": 0.0},
        memes={"wonder": 1.6, "fear": 1.2, "bravery": 0.7, "joy": 0.8},
        notes={"goal": prize.phrase},
    )
    world.entities["helper"] = Entity(
        key="helper",
        label=plan.helper_name,
        kind=plan.helper_role,
        meters={"nearby": 1.0, "support": 1.0},
        memes={"care": 1.3, "calm": 1.1},
        notes={"cue": plan.phrase},
    )
    world.entities["prize"] = Entity(
        key="prize",
        label=prize.phrase,
        kind="reward",
        meters={"visible": 1.0, "held": 0.0},
        memes={"gleam": 1.0},
        notes={"lesson": prize.lesson},
    )

    world.add_event("arrival", f"{params.hero} entered the children's museum and saw the wobbly castle.")
    world.add_event("goal", f"{params.hero} wanted to reach {prize.phrase}.")
    world.facts["setting"] = "children's museum"
    world.facts["goal"] = prize.phrase
    world.facts["need"] = wobble.need
    return world


def simulate(world: World) -> None:
    hero = world.get("hero")
    castle = world.get("castle")
    prize = world.get("prize")
    helper = world.get("helper")

    hero.meters["pause"] = 1.0
    hero.memes["fear"] += 0.5
    world.add_event("wobble", f"The path had {world.wobble.phrase} because {world.wobble.cause}.")

    hero.memes["bravery"] += 0.9
    hero.memes["fear"] = max(0.4, hero.memes["fear"] - 0.6)
    helper.meters["support"] = 1.2
    castle.meters["safe_path"] = 1.0
    world.add_event("brave_choice", f"{world.plan.helper_phrase}, and {world.params.hero} chose {world.plan.phrase}.")

    hero.meters["feet_forward"] = 3.0
    castle.meters["wobble"] = max(0.2, castle.meters["wobble"] - 0.4)
    world.add_event("crossing", f"{world.params.hero} {world.plan.action}.")

    hero.meters["at_turret"] = 1.0
    prize.meters["held"] = 1.0
    castle.meters["prize_reached"] = 1.0
    hero.memes["joy"] += 1.4
    world.add_event("reward", f"{world.params.hero} reached {world.prize.phrase}.")

    hero.memes["wonder"] += 0.4
    world.facts["ending"] = "happy"
    world.facts["change"] = "fear_to_pride"
    world.add_event("ending", world.prize.ending_image)


def render_story(world: World) -> str:
    hero = world.get("hero")
    helper = world.get("helper")
    subject, possessive = _pronouns(world.params.gender)
    bravery = hero.memes["bravery"]
    fear = hero.memes["fear"]

    opening = (
        f"{world.params.hero} came to the children's museum in the middle of the mellow day. "
        f"There stood a wobbly castle, bright and tall, with {world.bridge.footing} underfoot and {world.bridge.view} overhead."
    )
    tension = (
        f"{world.params.hero} wished to win {world.prize.phrase}, yet the path had {world.wobble.phrase}. "
        f"{world.wobble.cause.capitalize()}, and {subject} made a tiny worried stop because {world.wobble.risk} felt closer than play."
    )
    turn = (
        f"Then came {world.plan.phrase}. {world.plan.helper_phrase}. "
        f"{world.params.hero} whispered, \"{world.plan.rhyme}\" and {world.plan.action}, so fear grew smaller and brave thoughts chose to stay."
    )
    ending = (
        f"Step after step, {world.params.hero} reached {world.prize.phrase}, and {world.prize.ending_image}. "
        f"{world.prize.lesson} {world.params.hero} walked back down with {possessive} cheeks alight, and the whole room felt glad and bright."
    )

    if bravery <= fear:
        raise StoryError("No story: the bravery turn did not complete successfully.")

    return "\n\n".join([opening, tension, turn, ending])


def generation_prompts(world: World) -> list[str]:
    return [
        f"Tell a nursery-rhyme-style story in a children's museum with a wobbly castle and a brave child named {world.params.hero}.",
        f"The challenge is {world.wobble.phrase} on {world.bridge.phrase}, and the safe brave plan is {world.plan.phrase}.",
        f"End with {world.prize.phrase} and a clearly happy final image that proves the child changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    castle = world.get("castle")
    return [
        QAItem(
            question="Where does the story happen?",
            answer=(
                "The story happens in a children's museum, right inside the climbing court with the wobbly castle. "
                "That setting matters because the child faces a pretend adventure in a carefully padded real place."
            ),
        ),
        QAItem(
            question=f"Why did {world.params.hero} stop before crossing?",
            answer=(
                f"{world.params.hero} stopped because the path had {world.wobble.phrase}. "
                f"{world.wobble.cause.capitalize()}, so the pause came from a real wobble instead of from silliness alone."
            ),
        ),
        QAItem(
            question=f"What brave plan helped {world.params.hero} keep going?",
            answer=(
                f"{world.params.hero} used {world.plan.phrase}. "
                f"The plan worked because {world.params.hero} {world.plan.action}, which matched the exact need created by the wobble."
            ),
        ),
        QAItem(
            question="Who helped during the hard middle?",
            answer=(
                f"{helper.label} helped during the hard middle. "
                f"{world.plan.helper_phrase}, and that nearby support turned the brave moment into a safe one."
            ),
        ),
        QAItem(
            question="How can we tell the ending is happy?",
            answer=(
                f"We can tell the ending is happy because {world.params.hero} reached {world.prize.phrase}. "
                f"The last image shows that {world.prize.ending_image}, which proves the fear did not stay in charge."
            ),
        ),
        QAItem(
            question=f"What changed inside {world.params.hero} by the end?",
            answer=(
                f"{world.params.hero} began with more worry than pride, but ended with more bravery and joy. "
                f"The castle still existed, yet the child's feelings changed from a pause into a proud return walk."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is a rail useful on a wobbly play bridge?",
            answer=(
                "A rail gives a child a steady place for one hand while the feet learn the bridge's movement. "
                "That extra contact can turn a wild sway into a slow and manageable crossing."
            ),
        ),
        QAItem(
            question="Why can counting or chanting help on bouncy steps?",
            answer=(
                "Counting gives the body a rhythm, and rhythm helps feet land one at a time instead of in a rush. "
                "A rhyme also keeps the mind busy with courage instead of only with wobble."
            ),
        ),
        QAItem(
            question="Why does a grown-up hand matter on a high museum ramp?",
            answer=(
                "A steady hand gives balance and calm at the same moment. "
                "When the child trusts the support, the climb can stay careful instead of freezing halfway through."
            ),
        ),
        QAItem(
            question="What makes a happy ending feel earned in a brave story?",
            answer=(
                "A happy ending feels earned when the child meets a real problem, chooses a fitting safe plan, and then reaches a changed final moment. "
                "The joy matters more when the world shows exactly how the brave turn happened."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    world.story = render_story(world)
    return StorySample(
        params=params,
        story=world.story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(B,W,P,Z) :-
    bridge(B),
    wobble(W),
    plan(P),
    prize(Z),
    bridge_allows(B,W),
    wobble_need(W,N),
    plan_solves(P,N),
    bridge_prize(B,Z).

ok :- chosen(B,W,P,Z), valid(B,W,P,Z).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds import asp

    lines: list[str] = []
    for bridge in BRIDGES.values():
        lines.append(asp.fact("bridge", bridge.key))
        for wobble_key in bridge.allows_wobbles:
            lines.append(asp.fact("bridge_allows", bridge.key, wobble_key))
        lines.append(asp.fact("bridge_prize", bridge.key, bridge.prize))
    for wobble in WOBBLES.values():
        lines.append(asp.fact("wobble", wobble.key))
        lines.append(asp.fact("wobble_need", wobble.key, wobble.need))
    for plan in PLANS.values():
        lines.append(asp.fact("plan", plan.key))
        for solve in plan.solves:
            lines.append(asp.fact("plan_solves", plan.key, solve))
    for prize in PRIZES.values():
        lines.append(asp.fact("prize", prize.key))
    if params is not None:
        lines.append(asp.fact("chosen", params.bridge, params.wobble, params.plan, params.prize))
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None, show: str = "") -> str:
    return asp_facts(params) + ASP_RULES + ("\n" + show if show else "")


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from storyworlds.asp import atoms, one_model

    return sorted(atoms(one_model(asp_program()), "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise StoryError("Verification failed: sample is missing its live world.")
    hero = world.get("hero")
    castle = world.get("castle")
    prize = world.get("prize")
    story_lower = sample.story.lower()

    if "wobbly castle" not in story_lower:
        raise StoryError("Verification failed: story is missing 'wobbly castle'.")
    if "children's museum" not in story_lower:
        raise StoryError("Verification failed: story is missing 'children's museum'.")
    if sample.story.count("\n\n") < 3:
        raise StoryError("Verification failed: story should have four paragraphs.")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("Verification failed: unresolved template braces leaked into prose.")
    if "meters" in sample.story or "memes" in sample.story:
        raise StoryError("Verification failed: debug labels leaked into prose.")
    if "  " in sample.story:
        raise StoryError("Verification failed: doubled spaces leaked into prose.")
    if hero.meters["at_turret"] < 1.0:
        raise StoryError("Verification failed: the child never reached the goal.")
    if prize.meters["held"] < 1.0 or castle.meters["prize_reached"] < 1.0:
        raise StoryError("Verification failed: the prize was not reached.")
    if hero.memes["bravery"] <= hero.memes["fear"]:
        raise StoryError("Verification failed: bravery did not overtake fear.")
    if hero.memes["joy"] <= 1.0:
        raise StoryError("Verification failed: joy did not rise into a happy ending.")
    if castle.meters["safe_path"] < 1.0:
        raise StoryError("Verification failed: the safe path was never established.")
    required_events = {"arrival", "goal", "wobble", "brave_choice", "crossing", "reward", "ending"}
    present_events = {event.id for event in world.history}
    if required_events - present_events:
        raise StoryError(f"Verification failed: missing events {sorted(required_events - present_events)}.")
    if len(sample.prompts) != 3:
        raise StoryError("Verification failed: expected exactly three generation prompts.")
    if len(sample.story_qa) < 6 or len(sample.world_qa) < 4:
        raise StoryError("Verification failed: QA sets are too thin.")
    for qa in list(sample.story_qa) + list(sample.world_qa):
        if len(qa.answer.split()) < 12:
            raise StoryError(f"Verification failed: answer is too short for question {qa.question!r}.")


def verify() -> str:
    py = sorted(valid_combos())
    lp = asp_valid_combos()
    if py != lp:
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        raise StoryError(f"Python/ASP mismatch. only_py={only_py} only_asp={only_lp}")

    for index, combo in enumerate(py):
        sample = generate(params_from_combo(combo, 1000 + index))
        verify_sample(sample)

    return (
        f"OK: Python and ASP agree on {len(py)} valid wobbly-castle museum combinations.\n"
        f"OK: Exercised all {len(py)} generated stories with grounded QA and happy endings."
    )


def format_qa(sample: StorySample) -> str:
    lines = ["PROMPTS"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("STORY QA")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate brave nursery-rhyme stories about a wobbly castle in a children's museum.")
    parser.add_argument("--bridge", choices=sorted(BRIDGES))
    parser.add_argument("--wobble", choices=sorted(WOBBLES))
    parser.add_argument("--plan", choices=sorted(PLANS))
    parser.add_argument("--prize", choices=sorted(PRIZES))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = matching_combos(args)
    if not combos:
        bridge_key = args.bridge or next(iter(BRIDGES))
        wobble_key = args.wobble or next(iter(WOBBLES))
        plan_key = args.plan or next(iter(PLANS))
        prize_key = args.prize or next(iter(PRIZES))
        raise StoryError(explain_rejection(bridge_key, wobble_key, plan_key, prize_key))

    explicit = all(getattr(args, field) is not None for field in ("bridge", "wobble", "plan", "prize"))
    seed = (args.seed if args.seed is not None else 1) + index
    chosen_gender = args.gender or rng.choice(sorted(HEROES))

    if explicit:
        params = StoryParams(
            bridge=args.bridge,
            wobble=args.wobble,
            plan=args.plan,
            prize=args.prize,
            hero=args.hero or HEROES[chosen_gender][seed % len(HEROES[chosen_gender])],
            gender=chosen_gender,
            seed=seed,
        )
        if not valid_combo(params.bridge, params.wobble, params.plan, params.prize):
            raise StoryError(explain_rejection(params.bridge, params.wobble, params.plan, params.prize))
        return params

    combo = rng.choice(combos)
    return params_from_combo(combo, seed, hero=args.hero, gender=chosen_gender)


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_combos(args)
        if not combos:
            bridge_key = args.bridge or next(iter(BRIDGES))
            wobble_key = args.wobble or next(iter(WOBBLES))
            plan_key = args.plan or next(iter(PLANS))
            prize_key = args.prize or next(iter(PRIZES))
            raise StoryError(explain_rejection(bridge_key, wobble_key, plan_key, prize_key))
        samples: list[StorySample] = []
        for index, combo in enumerate(combos):
            params = params_from_combo(
                combo,
                (args.seed if args.seed is not None else 1) + index,
                hero=args.hero,
                gender=args.gender,
            )
            samples.append(generate(params))
        return samples

    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        seed = (args.seed if args.seed is not None else 1) + index
        params = resolve_params(args, random.Random(seed), index)
        samples.append(generate(params))
    return samples


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)

    try:
        if args.show_asp:
            print(asp_program(show="#show valid/4.\n#show ok/0."))
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in asp_valid_combos():
                print("\t".join(combo))
            return 0

        samples = samples_from_args(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = ""
            if args.all:
                p = sample.params
                header = f"### bridge={p.bridge} wobble={p.wobble} plan={p.plan} prize={p.prize}"
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as err:
        print(err, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
