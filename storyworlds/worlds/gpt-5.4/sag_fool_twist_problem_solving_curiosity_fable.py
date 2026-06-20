#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sag_fool_twist_problem_solving_curiosity_fable.py
==============================================================================

A standalone story world for a tiny fable domain built from the seed words
"sag" and "fool" with the requested features: twist, problem solving, and
curiosity.

Premise
-------
Two small animals need to get food across a stream. One is curious and pauses
to ask why the old crossing sags. The other laughs and calls that caution
foolish. The twist is that curiosity is what keeps them safe: the crossing
really is weak, and a thoughtful solution turns the day around.

This world models:
- physical meters: strain, sag, wobble, wetness, safety
- emotional memes: curiosity, pride, fear, relief, respect
- a reasonableness gate: only combinations with a real bridge-risk and a real
  workable solution are allowed
- an inline ASP twin for the same gate and outcome logic
- three Q&A sets grounded in simulated state, not English parsing

Run it
------
    python storyworlds/worlds/gpt-5.4/sag_fool_twist_problem_solving_curiosity_fable.py
    python storyworlds/worlds/gpt-5.4/sag_fool_twist_problem_solving_curiosity_fable.py --all
    python storyworlds/worlds/gpt-5.4/sag_fool_twist_problem_solving_curiosity_fable.py --bridge rope --cargo melon_sack
    python storyworlds/worlds/gpt-5.4/sag_fool_twist_problem_solving_curiosity_fable.py --solution bundle_reeds
    python storyworlds/worlds/gpt-5.4/sag_fool_twist_problem_solving_curiosity_fable.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
CURIOSITY_INIT = 5.0
PRIDE_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"fox", "crow", "rabbit", "otter", "hedgehog", "boy", "father"}
        female = {"hen", "goose", "girl", "mother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Bridge:
    id: str
    label: str
    phrase: str
    texture: str
    base_strength: int
    sag_word: str
    danger_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    weight: int
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    sense: int
    power: int
    requires_inspection: bool
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    opening: str
    sky: str
    ending: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sag_alarm(world: World) -> list[str]:
    out: list[str] = []
    bridge = world.get("bridge")
    if bridge.meters["sag"] < THRESHOLD:
        return out
    sig = ("sag_alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("hero", "boaster"):
        world.get(eid).memes["fear"] += 1
    bridge.meters["danger"] += 1
    out.append("__sag__")
    return out


def _r_mockery_backfires(world: World) -> list[str]:
    out: list[str] = []
    boaster = world.get("boaster")
    hero = world.get("hero")
    if hero.memes["proved_right"] < THRESHOLD or boaster.memes["mockery"] < THRESHOLD:
        return out
    sig = ("mockery_backfires",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boaster.memes["shame"] += 1
    boaster.memes["respect"] += 1
    out.append("__twist__")
    return out


CAUSAL_RULES = [
    Rule("sag_alarm", "physical", _r_sag_alarm),
    Rule("mockery_backfires", "social", _r_mockery_backfires),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_score(bridge: Bridge, cargo: Cargo) -> int:
    return max(0, cargo.weight - bridge.base_strength)


def bridge_at_risk(bridge: Bridge, cargo: Cargo) -> bool:
    return risk_score(bridge, cargo) >= 1


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def solution_works(solution: Solution, bridge: Bridge, cargo: Cargo) -> bool:
    return solution.power >= risk_score(bridge, cargo)


def inspect_needed(solution: Solution, bridge: Bridge, cargo: Cargo) -> bool:
    return bridge_at_risk(bridge, cargo) and solution.requires_inspection


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for bid, bridge in BRIDGES.items():
        for cid, cargo in CARGOS.items():
            if bridge_at_risk(bridge, cargo) and any(solution_works(s, bridge, cargo) for s in sensible_solutions()):
                combos.append((bid, cid))
    return combos


def predict_sag(world: World, bridge_id: str, cargo_id: str) -> dict:
    sim = world.copy()
    bridge = sim.get(bridge_id)
    cargo = sim.get(cargo_id)
    attempt_cross(sim, bridge, cargo, narrate=False)
    return {
        "sags": bridge.meters["sag"] >= THRESHOLD,
        "danger": bridge.meters["danger"] >= THRESHOLD,
        "wet": sim.get("cargo").meters["wet"] >= THRESHOLD,
    }


def opening(world: World, hero: Entity, boaster: Entity, mood: Mood, cargo: Cargo) -> None:
    hero.memes["curiosity"] += 1
    boaster.memes["pride"] += 1
    world.say(
        f"{mood.opening}, {hero.id} and {boaster.id} set out with {cargo.phrase}. "
        f"{mood.sky}"
    )
    world.say(
        f"They meant to carry it to the far meadow, where {cargo.reward} waited."
    )


def arrive_bridge(world: World, hero: Entity, boaster: Entity, bridge: Bridge) -> None:
    world.say(
        f"Soon they reached {bridge.phrase}. It was {bridge.texture}, and it hung over a bright little stream."
    )
    world.say(
        f"{hero.id} slowed down. {hero.pronoun().capitalize()} watched the crossing and wondered why it might {bridge.sag_word} in the middle."
    )
    hero.memes["curiosity"] += 1


def mock(world: World, hero: Entity, boaster: Entity) -> None:
    boaster.memes["mockery"] += 1
    world.say(
        f'"Why stop for questions?" {boaster.id} laughed. "Only a fool stares at a bridge when there is supper on the other side."'
    )
    world.say(
        f"But {hero.id} kept looking instead of hurrying."
    )


def inspect(world: World, hero: Entity, bridge: Entity, bridge_cfg: Bridge) -> None:
    hero.memes["curiosity"] += 1
    bridge.meters["inspected"] += 1
    bridge.meters["weakness_seen"] += 1
    world.say(
        f"{hero.id} crouched beside the crossing and touched the ropes and boards. {hero.pronoun().capitalize()} found one tired place where {bridge_cfg.danger_text}."
    )
    world.facts["inspected"] = True


def attempt_cross(world: World, bridge: Entity, cargo: Entity, narrate: bool = True) -> None:
    bridge_cfg = world.facts["bridge_cfg"]
    cargo_cfg = world.facts["cargo_cfg"]
    strain = float(risk_score(bridge_cfg, cargo_cfg))
    if strain <= 0:
        return
    bridge.meters["strain"] += strain
    bridge.meters["sag"] += 1
    propagate(world, narrate=narrate)


def warning(world: World, hero: Entity, bridge: Bridge, cargo: Cargo) -> None:
    pred = predict_sag(world, "bridge", "cargo")
    world.facts["predicted_sag"] = pred["sags"]
    world.say(
        f'"Wait," said {hero.id}. "This {bridge.label} will {bridge.sag_word} if we drag {cargo.label} across all at once."'
    )
    if pred["danger"]:
        world.say(
            f"{hero.pronoun().capitalize()} was not being timid. {hero.pronoun().capitalize()} had read the danger in the bridge itself."
        )


def boast_step(world: World, boaster: Entity, bridge: Entity, bridge_cfg: Bridge, cargo: Cargo) -> None:
    boaster.memes["pride"] += 1
    world.say(
        f'{boaster.id} sniffed and stepped onto the first boards with {cargo.label}. At once the old crossing gave a low creak and began to {bridge_cfg.sag_word}.'
    )
    attempt_cross(world, bridge, world.get("cargo"))


def choose_solution(world: World, hero: Entity, boaster: Entity, solution: Solution, bridge: Bridge, cargo: Cargo) -> None:
    hero.memes["problem_solving"] += 1
    world.say(
        f"{hero.id} did not scold. {hero.pronoun().capitalize()} looked at the stream, the bank, and the load, and then {solution.text}"
    )


def solve_success(world: World, hero: Entity, boaster: Entity, solution: Solution, cargo: Cargo, mood: Mood) -> None:
    bridge = world.get("bridge")
    bridge.meters["danger"] = 0.0
    bridge.meters["sag"] = 0.0
    world.get("cargo").meters["wet"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["proved_right"] += 1
    boaster.memes["relief"] += 1
    boaster.memes["respect"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Bit by bit, they carried the load safely to the far side. The stream kept singing below them, but nothing slipped, and nobody got wet."
    )
    if boaster.memes["shame"] >= THRESHOLD or boaster.memes["respect"] >= THRESHOLD:
        world.say(
            f'{boaster.id} lowered {boaster.pronoun("possessive")} head. "I called you a fool," {boaster.pronoun()} said, "but your questions were wiser than my hurry."'
        )
    world.say(
        f"{mood.ending} The sweet smell of {cargo.reward} drifted across the meadow, and both travelers ate with quieter hearts."
    )


def solve_fail(world: World, hero: Entity, boaster: Entity, solution: Solution, cargo: Cargo) -> None:
    world.get("cargo").meters["wet"] += 1
    world.get("bridge").meters["danger"] += 1
    hero.memes["fear"] += 1
    boaster.memes["fear"] += 1
    world.say(
        solution.fail
    )
    world.say(
        f"The load splashed into the stream and came up dripping. No one was hurt, but supper had to be made from a much smaller meal."
    )
    hero.memes["proved_right"] += 1
    boaster.memes["shame"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{boaster.id} whispered, "I was the fool this time."'
    )


def moral(world: World, outcome: str) -> None:
    if outcome == "safe":
        world.say(
            "And so the little ones learned that curiosity is not foolish at all. The question that slows your feet may save your basket."
        )
    else:
        world.say(
            "And so they learned, even on a wet day, that mockery sees less than curiosity. A quick tongue can make a fool of the one who uses it."
        )


def tell(
    bridge_cfg: Bridge,
    cargo_cfg: Cargo,
    solution_cfg: Solution,
    mood: Mood,
    hero_name: str = "Nim",
    hero_type: str = "rabbit",
    boaster_name: str = "Rusk",
    boaster_type: str = "fox",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    boaster = world.add(Entity(id="boaster", kind="character", type=boaster_type, label=boaster_name, role="boaster"))
    bridge = world.add(Entity(id="bridge", type="bridge", label=bridge_cfg.label))
    cargo = world.add(Entity(id="cargo", type="cargo", label=cargo_cfg.label))
    stream = world.add(Entity(id="stream", type="stream", label="stream"))

    hero.id = hero_name
    boaster.id = boaster_name
    world.entities[hero_name] = world.entities.pop("hero")
    world.entities[boaster_name] = world.entities.pop("boaster")
    world.entities["hero"] = world.entities[hero_name]
    world.entities["boaster"] = world.entities[boaster_name]

    hero = world.get("hero")
    boaster = world.get("boaster")

    hero.memes["curiosity"] = CURIOSITY_INIT
    boaster.memes["pride"] = PRIDE_INIT

    world.facts.update(
        bridge_cfg=bridge_cfg,
        cargo_cfg=cargo_cfg,
        solution_cfg=solution_cfg,
        mood=mood,
        risk=risk_score(bridge_cfg, cargo_cfg),
    )

    opening(world, hero, boaster, mood, cargo_cfg)
    arrive_bridge(world, hero, boaster, bridge_cfg)

    world.para()
    mock(world, hero, boaster)
    if solution_cfg.requires_inspection:
        inspect(world, hero, world.get("bridge"), bridge_cfg)
    warning(world, hero, bridge_cfg, cargo_cfg)
    boast_step(world, boaster, world.get("bridge"), bridge_cfg, cargo_cfg)

    world.para()
    choose_solution(world, hero, boaster, solution_cfg, bridge_cfg, cargo_cfg)
    works = solution_works(solution_cfg, bridge_cfg, cargo_cfg)
    if works:
        solve_success(world, hero, boaster, solution_cfg, cargo_cfg, mood)
        outcome = "safe"
    else:
        solve_fail(world, hero, boaster, solution_cfg, cargo_cfg)
        outcome = "wet"

    world.para()
    moral(world, outcome)

    world.facts.update(
        hero=hero,
        boaster=boaster,
        bridge=world.get("bridge"),
        cargo=world.get("cargo"),
        bridge_phrase=bridge_cfg.phrase,
        outcome=outcome,
        worked=works,
        inspected=world.facts.get("inspected", False),
    )
    return world


BRIDGES = {
    "rope": Bridge(
        "rope",
        "rope bridge",
        "an old rope bridge",
        "made of slats tied with vine and rope",
        1,
        "sag",
        "one knot had frayed to a pale, furry thread",
        tags={"bridge", "rope", "sag"},
    ),
    "plank": Bridge(
        "plank",
        "plank bridge",
        "a narrow plank bridge",
        "built from thin boards over willow posts",
        2,
        "sag",
        "one board was soft in the middle and bent under a careful paw",
        tags={"bridge", "wood", "sag"},
    ),
    "stone": Bridge(
        "stone footbridge",
        "stone footbridge",
        "a low stone footbridge",
        "patched with old mortar and moss",
        3,
        "dip",
        "a cracked edge had loosened where water had licked it for years",
        tags={"bridge", "stone", "sag"},
    ),
}

CARGOS = {
    "berry_basket": Cargo(
        "berry_basket",
        "a berry basket",
        "a round basket full of red berries",
        2,
        "berries and bread",
        tags={"berries", "basket"},
    ),
    "turnip_bundle": Cargo(
        "turnip_bundle",
        "a turnip bundle",
        "a bundle of fat turnips tied in cloth",
        3,
        "turnip stew",
        tags={"turnip", "bundle"},
    ),
    "melon_sack": Cargo(
        "melon_sack",
        "a melon sack",
        "a bulging sack of little melons",
        4,
        "sweet melon slices",
        tags={"melon", "sack"},
    ),
}

SOLUTIONS = {
    "one_by_one": Solution(
        "one_by_one",
        "carry one by one",
        3,
        2,
        True,
        "said, \"We will not trust the middle with all our weight. We will carry the food one piece at a time and keep to the stronger edges.\"",
        "They tried to divide the load, but the sacks still dragged too hard, and the bridge lurched so sharply that the last bundle tumbled away.",
        "carried the food over one piece at a time along the strongest part",
        tags={"careful", "problem_solving"},
    ),
    "bundle_reeds": Solution(
        "bundle_reeds",
        "bundle reeds beneath the weak place",
        3,
        3,
        True,
        "gathered long reeds from the bank and tucked them under the weak middle, making a springy little brace before they crossed in smaller trips",
        "They pushed reeds under the middle, but the weight was still too great, and the brace slid free with a splash.",
        "braced the weak middle with reeds and crossed in smaller trips",
        tags={"reeds", "problem_solving"},
    ),
    "stream_ferry": Solution(
        "stream_ferry",
        "float the load across",
        3,
        4,
        False,
        "said, \"The stream is gentler than the bridge. Let us bind the baskets to driftwood and guide them across the shallow bend.\"",
        "They set the load on driftwood, but the bundle rolled, tipped, and bobbed away before they could catch it.",
        "floated the load across on driftwood at the shallow bend",
        tags={"stream", "problem_solving"},
    ),
    "push_fast": Solution(
        "push_fast",
        "rush across",
        1,
        1,
        False,
        "said nothing at all and only tried to shove the load over before the bridge could complain",
        "They rushed the load forward, and the old crossing lurched so hard that the bundle slipped straight into the stream.",
        "tried to rush the load across",
        tags={"rush"},
    ),
}

MOODS = {
    "dawn": Mood("dawn", "At dawn", "Mist lay on the grass like folded wool.", "At the end of the crossing, morning seemed brighter than before."),
    "noon": Mood("noon", "By noon", "Sunlight flashed on the stream like tiny coins.", "When all was done, even the hard noon light felt gentle."),
    "evening": Mood("evening", "Toward evening", "The reeds whispered as the gold light thinned.", "By the time the shadows lengthened, wisdom felt warmer than pride."),
}

ANIMALS = {
    "rabbit": ["Nim", "Pip", "Moss", "Tumble"],
    "fox": ["Rusk", "Bram", "Flint", "Taw"],
    "crow": ["Cor", "Ink", "Sable", "Rill"],
    "otter": ["Nettle", "Rip", "Sedge", "Marlow"],
    "hedgehog": ["Burr", "Thimble", "Poke", "Hazel"],
}

TRAIT_PAIRS = [
    ("rabbit", "fox"),
    ("crow", "otter"),
    ("hedgehog", "fox"),
    ("rabbit", "crow"),
]


@dataclass
class StoryParams:
    bridge: str
    cargo: str
    solution: str
    mood: str
    hero_name: str
    hero_type: str
    boaster_name: str
    boaster_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bridge": [(
        "Why can an old bridge sag?",
        "An old bridge can sag when its ropes, boards, or stones grow weak. Heavy weight pulls hardest on the weakest place."
    )],
    "rope": [(
        "Why do ropes get weak over time?",
        "Ropes can rub, fray, and get wet in weather. Little damage adds up until the rope cannot hold as strongly as before."
    )],
    "wood": [(
        "Why can wooden boards bend?",
        "Wooden boards can bend when they get thin, old, or soft with water. Then weight pushes them downward."
    )],
    "stone": [(
        "How can a stone bridge become unsafe?",
        "Even stone can crack when water and time wear at it. A loose edge may shift when something heavy passes over it."
    )],
    "berries": [(
        "Why is a basket easier to carry in small trips?",
        "Small trips spread the weight out. That makes each crossing lighter and safer."
    )],
    "turnip": [(
        "Why is a bundle of turnips heavy?",
        "Turnips are solid and full of water, so a big bundle can weigh a lot. Heavy loads press hard on anything carrying them."
    )],
    "melon": [(
        "Why is a sack of melons hard to balance?",
        "Melons are round, so they can shift and roll inside a sack. That makes the load wobble while you carry it."
    )],
    "reeds": [(
        "What are reeds?",
        "Reeds are tall water plants that grow near streams. People and animals in stories sometimes use them to prop, weave, or tie things."
    )],
    "stream": [(
        "What is a shallow bend in a stream?",
        "It is a place where the water turns and often runs slower and lower. That can make it easier to guide something across."
    )],
    "careful": [(
        "Why is asking questions sometimes wise?",
        "Questions help you notice danger before it grows bigger. Curiosity can protect you because it makes you look closely."
    )],
}
KNOWLEDGE_ORDER = ["bridge", "rope", "wood", "stone", "berries", "turnip", "melon", "reeds", "stream", "careful"]


def pair_noun(hero: Entity, boaster: Entity) -> str:
    return f"two travelers, {hero.id} and {boaster.id}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    boaster = f["boaster"]
    bridge = f["bridge_cfg"]
    cargo = f["cargo_cfg"]
    solution = f["solution_cfg"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the words "sag" and "fool". The story should involve curiosity and a problem at {bridge.phrase}.',
        f"Tell a fable where {hero.id} notices danger in {bridge.phrase}, {boaster.id} mocks the warning, and the twist proves curiosity wiser than pride.",
        f"Write a gentle animal fable in which a heavy load of {cargo.label} threatens to make a crossing sag, and the characters solve the problem by {solution.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    boaster = f["boaster"]
    bridge = f["bridge_cfg"]
    cargo = f["cargo_cfg"]
    solution = f["solution_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, boaster)} carrying {cargo.label} toward the far meadow. One was curious, and the other was in too much of a hurry."
        ),
        (
            f"Why did {hero.id} stop at the bridge?",
            f"{hero.id} saw that the old {bridge.label} might {bridge.sag_word} under the heavy load. {hero.pronoun().capitalize()} stopped because curiosity made {hero.pronoun('object')} look closely instead of rushing."
        ),
        (
            f"Why did {boaster.id} call {hero.id} a fool?",
            f"{boaster.id} thought questions were only a delay and wanted to hurry to the meal waiting across the stream. The insult came from pride, not from careful thinking."
        ),
    ]
    if f.get("inspected"):
        qa.append((
            f"What did {hero.id} find by looking closely?",
            f"{hero.id} found a weak place in the crossing where {bridge.danger_text}. That discovery turned curiosity into useful evidence."
        ))
    if outcome == "safe":
        qa.append((
            "How did they solve the problem?",
            f"They solved it by using a safer plan: {solution.qa_text}. The solution worked because it reduced the strain that was making the bridge {bridge.sag_word}."
        ))
        qa.append((
            "What was the twist in the story?",
            f"The twist was that the one called a fool was the wisest one there. {hero.id}'s questions saved the food and taught {boaster.id} that caution can be clever."
        ))
        qa.append((
            "How did the story end?",
            f"They reached the far side safely and still had their meal. The ending shows that curiosity changed danger into a calm success."
        ))
    else:
        qa.append((
            "Did their plan work?",
            f"No. Their plan was too weak for such a heavy load, so the food fell into the stream and got wet. Even so, {boaster.id} finally understood that {hero.id} had seen the danger first."
        ))
        qa.append((
            "What was the lesson after the accident?",
            f"The lesson was that mockery is a poor guide when there is real danger. Curiosity had been pointing toward the truth all along."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["bridge_cfg"].tags) | set(f["cargo_cfg"].tags) | set(f["solution_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for key, ent in world.entities.items():
        if key not in {"hero", "boaster"} and key != ent.id and ent.id in {"hero", "boaster"}:
            continue
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {key:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rope", "berry_basket", "one_by_one", "dawn", "Nim", "rabbit", "Rusk", "fox"),
    StoryParams("plank", "turnip_bundle", "bundle_reeds", "noon", "Ink", "crow", "Marlow", "otter"),
    StoryParams("stone", "melon_sack", "stream_ferry", "evening", "Burr", "hedgehog", "Taw", "fox"),
    StoryParams("rope", "melon_sack", "bundle_reeds", "evening", "Pip", "rabbit", "Cor", "crow"),
    StoryParams("plank", "melon_sack", "one_by_one", "dawn", "Hazel", "hedgehog", "Flint", "fox"),
]


def explain_rejection(bridge: Bridge, cargo: Cargo) -> str:
    if not bridge_at_risk(bridge, cargo):
        return (
            f"(No story: {cargo.label} is not heavy enough to make the {bridge.label} truly sag, "
            f"so there is no honest bridge problem to solve.)"
        )
    return (
        f"(No story: the {bridge.label} and {cargo.label} create a real risk, "
        f"but none of the sensible solutions in this world can solve it.)"
    )


def explain_solution(solution_id: str) -> str:
    s = SOLUTIONS[solution_id]
    better = ", ".join(sorted(sol.id for sol in sensible_solutions()))
    return (
        f"(Refusing solution '{solution_id}': it scores too low on common sense "
        f"(sense={s.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "safe" if solution_works(SOLUTIONS[params.solution], BRIDGES[params.bridge], CARGOS[params.cargo]) else "wet"


ASP_RULES = r"""
% --- gate ------------------------------------------------------------------
risk(B, C, R) :- base_strength(B, S), weight(C, W), R = W - S, R >= 1.
sensible(Sol) :- solution(Sol), sense(Sol, V), sense_min(M), V >= M.
has_fix(B, C) :- risk(B, C, R), sensible(Sol), power(Sol, P), P >= R.
valid(B, C) :- risk(B, C, _), has_fix(B, C).

% --- outcome ---------------------------------------------------------------
chosen_risk(R) :- chosen_bridge(B), chosen_cargo(C), risk(B, C, R).
works :- chosen_solution(Sol), chosen_risk(R), power(Sol, P), P >= R.
outcome(safe) :- works.
outcome(wet) :- not works.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for bid, bridge in BRIDGES.items():
        lines.append(asp.fact("bridge", bid))
        lines.append(asp.fact("base_strength", bid, bridge.base_strength))
    for cid, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("weight", cid, cargo.weight))
    for sid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, sol.sense))
        lines.append(asp.fact("power", sid, sol.power))
        if sol.requires_inspection:
            lines.append(asp.fact("requires_inspection", sid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_bridge", params.bridge),
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_solution", params.solution),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    p_set = set(valid_combos())
    a_set = set(asp_valid_combos())
    if p_set == a_set:
        print(f"OK: gate matches valid_combos() ({len(p_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_set - p_set:
            print("  only in clingo:", sorted(a_set - p_set))
        if p_set - a_set:
            print("  only in python:", sorted(p_set - a_set))

    p_sense = {s.id for s in sensible_solutions()}
    a_sense = set(asp_sensible())
    if p_sense == a_sense:
        print(f"OK: sensible solutions match ({sorted(p_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible solutions: clingo={sorted(a_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny fable world about curiosity, a sagging bridge, and a twist that turns mockery back on itself."
    )
    ap.add_argument("--bridge", choices=BRIDGES)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--hero-type", choices=sorted(ANIMALS))
    ap.add_argument("--boaster-type", choices=sorted(ANIMALS))
    ap.add_argument("--hero-name")
    ap.add_argument("--boaster-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def pick_name(rng: random.Random, animal_type: str, avoid: str = "") -> str:
    pool = [n for n in ANIMALS[animal_type] if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bridge and args.cargo:
        if not bridge_at_risk(BRIDGES[args.bridge], CARGOS[args.cargo]):
            raise StoryError(explain_rejection(BRIDGES[args.bridge], CARGOS[args.cargo]))
    if args.solution and SOLUTIONS[args.solution].sense < SENSE_MIN:
        raise StoryError(explain_solution(args.solution))

    combos = [
        c for c in valid_combos()
        if (args.bridge is None or c[0] == args.bridge)
        and (args.cargo is None or c[1] == args.cargo)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    bridge_id, cargo_id = rng.choice(sorted(combos))
    solution_choices = [
        sid for sid, sol in SOLUTIONS.items()
        if sol.sense >= SENSE_MIN
    ]
    solution_id = args.solution or rng.choice(sorted(solution_choices))
    mood = args.mood or rng.choice(sorted(MOODS))

    hero_type = args.hero_type or rng.choice([a for a, _ in TRAIT_PAIRS])
    boaster_type = args.boaster_type or rng.choice([b for _, b in TRAIT_PAIRS])
    if hero_type == boaster_type:
        boaster_type = rng.choice([t for t in sorted(ANIMALS) if t != hero_type])

    hero_name = args.hero_name or pick_name(rng, hero_type)
    boaster_name = args.boaster_name or pick_name(rng, boaster_type, avoid=hero_name)

    return StoryParams(
        bridge=bridge_id,
        cargo=cargo_id,
        solution=solution_id,
        mood=mood,
        hero_name=hero_name,
        hero_type=hero_type,
        boaster_name=boaster_name,
        boaster_type=boaster_type,
    )


def generate(params: StoryParams) -> StorySample:
    bridge = BRIDGES[params.bridge]
    cargo = CARGOS[params.cargo]
    solution = SOLUTIONS[params.solution]
    if not bridge_at_risk(bridge, cargo):
        raise StoryError(explain_rejection(bridge, cargo))
    if solution.sense < SENSE_MIN:
        raise StoryError(explain_solution(params.solution))

    world = tell(
        bridge,
        cargo,
        solution,
        MOODS[params.mood],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        boaster_name=params.boaster_name,
        boaster_type=params.boaster_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible solutions: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (bridge, cargo) combos:\n")
        for bridge, cargo in combos:
            print(f"  {bridge:8} {cargo}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.boaster_name}: {p.cargo} on {p.bridge} with {p.solution} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
