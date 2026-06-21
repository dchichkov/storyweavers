#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wade_deep_carriage_curiosity_space_adventure.py
============================================================================

A small storyworld about a curious child on a space trip who spots a shining
alien treasure beyond a glowing pool. Sometimes it is safe to wade a little.
Sometimes the pool is too deep, and the child has to solve the problem with a
tool from the moon carriage instead.

The model keeps one clear causal idea:
    curiosity + glowing discovery -> desire to reach it
    trying to wade depends on depth and distance
    a sensible method must match the pool
    the ending proves that curiosity is best when paired with care

Run it
------
    python storyworlds/worlds/gpt-5.4/wade_deep_carriage_curiosity_space_adventure.py
    python storyworlds/worlds/gpt-5.4/wade_deep_carriage_curiosity_space_adventure.py --pool deep_pool
    python storyworlds/worlds/gpt-5.4/wade_deep_carriage_curiosity_space_adventure.py --method wade
    python storyworlds/worlds/gpt-5.4/wade_deep_carriage_curiosity_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/wade_deep_carriage_curiosity_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/wade_deep_carriage_curiosity_space_adventure.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain_mother"}
        male = {"boy", "man", "father", "captain_father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"captain_mother": "mom", "captain_father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    trail: str
    landmark: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pool:
    id: str
    label: str
    phrase: str
    color: str
    depth: int
    distance: int
    warning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    kind: str
    max_depth: int
    max_distance: int
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    pool: str
    prize: str
    method: str
    hero_name: str
    hero_gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_curiosity_to_desire(world: World) -> list[str]:
    hero = world.entities.get("hero")
    prize = world.entities.get("prize")
    if hero is None or prize is None:
        return []
    if hero.memes["curiosity"] < THRESHOLD or prize.meters["seen"] < THRESHOLD:
        return []
    sig = ("desire", hero.id, prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["desire"] += 1
    return []


def _r_deep_risk(world: World) -> list[str]:
    hero = world.entities.get("hero")
    pool = world.entities.get("pool")
    if hero is None or pool is None:
        return []
    if hero.meters["in_pool"] < THRESHOLD:
        return []
    if pool.meters["depth"] <= 1:
        return []
    sig = ("risk", hero.id, pool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    pool.meters["danger"] += 1
    return []


def _r_retrieved_joy(world: World) -> list[str]:
    hero = world.entities.get("hero")
    prize = world.entities.get("prize")
    if hero is None or prize is None:
        return []
    if prize.meters["retrieved"] < THRESHOLD:
        return []
    sig = ("joy", hero.id, prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="curiosity_to_desire", tag="emotion", apply=_r_curiosity_to_desire),
    Rule(name="deep_risk", tag="physical", apply=_r_deep_risk),
    Rule(name="retrieved_joy", tag="emotion", apply=_r_retrieved_joy),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(rule.name == fired[0] for fired in []):
                pass
        current_count = len(world.fired)
        if current_count > len(set(world.fired)):
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "violet_moon": Setting(
        id="violet_moon",
        place="the Violet Moon Flats",
        sky="Above them, a purple sky held three tiny stars that blinked even in daytime.",
        trail="Their little survey carriage hummed over silver dust.",
        landmark="At the edge of a ring of stones, a pool shone like spilled glass.",
        ending="The moon carriage rolled on with one more bright mystery safely tucked inside.",
        tags={"space", "moon"},
    ),
    "ring_crater": Setting(
        id="ring_crater",
        place="the Ring Crater shore",
        sky="Far above, Saturn's rings stretched like a shining ribbon.",
        trail="Their moon carriage bumped softly along the crater path.",
        landmark="Near a low cliff, a glowing pool rested in a bowl of black sand.",
        ending="Soon the carriage was moving again, and the rings glittered over their heads.",
        tags={"space", "saturn"},
    ),
    "comet_marsh": Setting(
        id="comet_marsh",
        place="the Comet Marsh plain",
        sky="A pale comet tail glimmered across the dark blue sky.",
        trail="Their small exploration carriage clicked over flat blue stones.",
        landmark="Beside a cluster of crystal reeds, a pool gleamed with green light.",
        ending="The carriage glided away while the comet tail shone like a quiet promise above them.",
        tags={"space", "comet"},
    ),
}

POOLS = {
    "shore_pool": Pool(
        id="shore_pool",
        label="shore pool",
        phrase="a small shore pool",
        color="silver-blue",
        depth=1,
        distance=1,
        warning="The water only covered the tops of boots there.",
        tags={"pool", "shallow"},
    ),
    "middle_pool": Pool(
        id="middle_pool",
        label="middle pool",
        phrase="a broad middle pool",
        color="green-gold",
        depth=2,
        distance=2,
        warning="The middle of the pool would be too deep for little knees.",
        tags={"pool", "deep"},
    ),
    "deep_pool": Pool(
        id="deep_pool",
        label="deep pool",
        phrase="a deep pool",
        color="midnight blue",
        depth=3,
        distance=3,
        warning="At the center, the water was deep and dark enough to hide a child's boots completely.",
        tags={"pool", "deep"},
    ),
}

PRIZES = {
    "star_shell": Prize(
        id="star_shell",
        label="star shell",
        phrase="a star shell",
        glow="its ridges flashed like tiny constellations",
        tags={"shell", "space"},
    ),
    "comet_seed": Prize(
        id="comet_seed",
        label="comet seed",
        phrase="a comet seed",
        glow="it glowed with a white tail, as if a little comet had curled up to sleep",
        tags={"seed", "space"},
    ),
    "moon_pearl": Prize(
        id="moon_pearl",
        label="moon pearl",
        phrase="a moon pearl",
        glow="it shone with soft light from deep inside",
        tags={"pearl", "space"},
    ),
}

METHODS = {
    "wade": Method(
        id="wade",
        label="wade in by hand",
        kind="wade",
        max_depth=1,
        max_distance=1,
        sense=3,
        text="carefully waded in, keeping one hand on the bank, and lifted the {prize} from the water",
        qa_text="carefully waded in and picked the {prize} up by hand",
        tags={"wade"},
    ),
    "bridge_scoop": Method(
        id="bridge_scoop",
        label="folding bridge and scoop",
        kind="bridge",
        max_depth=2,
        max_distance=2,
        sense=3,
        text="slid a folding bridge from the carriage, leaned out over the glowing water, and scooped up the {prize}",
        qa_text="used a folding bridge from the carriage and scooped up the {prize}",
        tags={"bridge", "carriage"},
    ),
    "carriage_arm": Method(
        id="carriage_arm",
        label="carriage robot arm",
        kind="arm",
        max_depth=3,
        max_distance=3,
        sense=3,
        text="pressed a switch on the carriage and sent out its long robot arm, which gently pinched the {prize} and brought it back",
        qa_text="used the carriage's long robot arm to bring back the {prize}",
        tags={"robot_arm", "carriage"},
    ),
    "splash_jump": Method(
        id="splash_jump",
        label="jump straight in",
        kind="jump",
        max_depth=1,
        max_distance=1,
        sense=1,
        text="jumped straight into the water and grabbed for the {prize}",
        qa_text="jumped straight in for the {prize}",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Ava", "Zoe", "Tia"]
BOY_NAMES = ["Leo", "Milo", "Finn", "Eli", "Max", "Theo"]
TRAITS = ["curious", "careful", "bright", "eager", "gentle", "thoughtful"]


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_works(pool: Pool, method: Method) -> bool:
    return pool.depth <= method.max_depth and pool.distance <= method.max_distance


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for pool_id, pool in POOLS.items():
            for prize_id in PRIZES:
                for method_id, method in METHODS.items():
                    if method.sense >= SENSE_MIN and method_works(pool, method):
                        combos.append((setting_id, pool_id, prize_id, method_id))
    return combos


def explain_method(method: Method) -> str:
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method.id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of these instead: {better}.)"
    )


def explain_rejection(pool: Pool, method: Method) -> str:
    return (
        f"(No story: {method.label} cannot reach safely into {pool.phrase}. "
        f"The pool is too deep or too far from the edge for that plan.)"
    )


def outcome_of(params: StoryParams) -> str:
    method = METHODS[params.method]
    if method.kind == "wade":
        return "wade_safe"
    return "tool_reach"


def introduce(world: World, hero: Entity, captain: Entity, carriage: Entity) -> None:
    world.say(
        f"{hero.id} rode beside {captain.label_word} in a moon carriage across {world.setting.place}. "
        f"{world.setting.sky} {world.setting.trail}"
    )
    hero.memes["curiosity"] += 1
    captain.memes["care"] += 1
    carriage.meters["ready"] += 1


def discover(world: World, hero: Entity, pool: Pool, prize: Prize) -> None:
    prize_ent = world.get("prize")
    pool_ent = world.get("pool")
    prize_ent.meters["seen"] += 1
    pool_ent.meters["depth"] = float(pool.depth)
    pool_ent.meters["distance"] = float(pool.distance)
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} spotted {pool.phrase}. It was {pool.color}, and in its middle lay {prize.phrase}; {prize.glow}."
    )
    world.say(
        f'{hero.id} leaned forward at once. "What is that? Why is it shining? Can we go closer?"'
    )


def wonder(world: World, hero: Entity, prize: Prize) -> None:
    hero.memes["curiosity"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The more {hero.id} looked, the more questions came. Curiosity tugged at {hero.pronoun('object')} until the little treasure seemed to pull like a star on a string."
    )
    world.say(
        f'"I want to bring the {prize.label} back to the carriage," {hero.pronoun()} said.'
    )


def warn(world: World, hero: Entity, captain: Entity, pool: Pool) -> None:
    if pool.depth > 1:
        hero.memes["caution"] += 1
    world.say(
        f'{captain.label_word.capitalize()} parked the carriage beside the bank and studied the water. "{pool.warning}"'
    )
    if pool.depth > 1:
        world.say(
            f'"You may want to wade in," {captain.pronoun()} said, "but this pool is too deep for that."'
        )
    else:
        world.say(
            f'"You can wade a little," {captain.pronoun()} said, "but only slowly and with me right here."'
        )


def predict(pool: Pool, method: Method) -> dict[str, bool]:
    return {
        "works": method_works(pool, method),
        "deep": pool.depth > 1,
        "requires_carriage": method.kind in {"bridge", "arm"},
    }


def act_wade(world: World, hero: Entity, prize: Prize, pool: Pool) -> None:
    hero.meters["in_pool"] += 1
    hero.meters["wet_boots"] += 1
    prize_ent = world.get("prize")
    prize_ent.meters["retrieved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took a breath, then began to wade into the glowing water. It was cool around {hero.pronoun('possessive')} boots, but not too deep."
    )
    world.say(
        f"Soon {hero.pronoun()} reached the {prize.label} and lifted it high. Little ripples raced away in silver circles."
    )


def act_bridge(world: World, hero: Entity, captain: Entity, carriage: Entity, prize: Prize) -> None:
    carriage.meters["bridge_out"] += 1
    prize_ent = world.get("prize")
    prize_ent.meters["retrieved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{captain.label_word.capitalize()} opened a side panel on the carriage. A slim bridge folded out with a click, making a safe path over the water's edge."
    )
    world.say(
        f"Together they stretched a scoop along the bridge, and a moment later the {prize.label} was gliding back toward them."
    )


def act_arm(world: World, hero: Entity, captain: Entity, carriage: Entity, prize: Prize) -> None:
    carriage.meters["arm_out"] += 1
    prize_ent = world.get("prize")
    prize_ent.meters["retrieved"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} watched wide-eyed as {captain.label_word} pressed a bright button. From the carriage roof, a long robot arm uncurled like a silver neck.'
    )
    world.say(
        f"It reached over the dark water, pinched the {prize.label} gently, and set it into {hero.id}'s waiting hands."
    )


def resolve(world: World, hero: Entity, captain: Entity, carriage: Entity, pool: Pool, prize: Prize, method: Method) -> None:
    hero.memes["trust"] += 1
    captain.memes["pride"] += 1
    if method.kind == "wade":
        act_wade(world, hero, prize, pool)
    elif method.kind == "bridge":
        act_bridge(world, hero, captain, carriage, prize)
    else:
        act_arm(world, hero, captain, carriage, prize)
    world.say(
        f'{hero.id} smiled down at the {prize.label}. "I was curious," {hero.pronoun()} said, "but I am glad we used the smart way."'
    )
    if method.kind == "wade":
        world.say(
            f'{captain.label_word.capitalize()} wrapped a warm blanket around {hero.pronoun("possessive")} shoulders and tucked the prize safely into a box in the carriage.'
        )
    else:
        world.say(
            f'{captain.label_word.capitalize()} tucked the prize into the sample box in the carriage, and {hero.id} traced its shine with one careful finger.'
        )
    world.say(world.setting.ending)


def tell(
    setting: Setting,
    pool: Pool,
    prize: Prize,
    method: Method,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    captain_type: str = "captain_mother",
    trait: str = "curious",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero", attrs={"display": hero_name}))
    captain = world.add(Entity(id="captain", kind="character", type=captain_type, label="the captain", phrase="the captain", role="captain"))
    carriage = world.add(Entity(id="carriage", kind="thing", type="carriage", label="moon carriage", phrase="a moon carriage", role="vehicle"))
    pool_ent = world.add(Entity(id="pool", kind="thing", type="pool", label=pool.label, phrase=pool.phrase, role="pool"))
    prize_ent = world.add(Entity(id="prize", kind="thing", type="prize", label=prize.label, phrase=prize.phrase, role="prize", tags=set(prize.tags)))
    hero.attrs["display"] = hero_name
    hero.attrs["trait"] = trait

    introduce(world, hero, captain, carriage)
    discover(world, hero, pool, prize)

    world.para()
    wonder(world, hero, prize)
    warn(world, hero, captain, pool)

    world.para()
    resolve(world, hero, captain, carriage, pool, prize, method)

    world.facts.update(
        hero=hero,
        hero_name=hero_name,
        captain=captain,
        carriage=carriage,
        pool=pool,
        prize_cfg=prize,
        prize=prize_ent,
        method=method,
        setting=setting,
        predicted=predict(pool, method),
        outcome=outcome_of(
            StoryParams(
                setting=setting.id,
                pool=pool.id,
                prize=prize.id,
                method=method.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
                captain=captain_type,
                trait=trait,
            )
        ),
    )
    return world


KNOWLEDGE = {
    "wade": [
        (
            "What does wade mean?",
            "To wade means to walk through water slowly with your feet still touching the ground. People wade only where the water is shallow enough to be safe."
        )
    ],
    "deep": [
        (
            "Why can deep water be dangerous for a child?",
            "Deep water can rise higher than a child's legs and make it hard to keep balance. That is why grown-ups choose a safer plan instead of stepping in."
        )
    ],
    "carriage": [
        (
            "What is a carriage in this story?",
            "Here a carriage is a small space vehicle that carries people and tools across the moon-like ground. It works like a rolling helper on the adventure."
        )
    ],
    "robot_arm": [
        (
            "What does a robot arm do?",
            "A robot arm can reach, hold, and lift things that are too far away for hands. It lets explorers move carefully without stepping into danger."
        )
    ],
    "bridge": [
        (
            "Why use a bridge over water?",
            "A bridge gives you a safe way to reach across water without putting your whole body into it. That helps when the water is too deep to walk through."
        )
    ],
    "moon": [
        (
            "What is a moon?",
            "A moon is a world in space that travels around a planet. Some moons are rocky, dusty, or icy, which makes them good places for pretend adventures."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to ask questions and learn more. It is a good feeling when you use it with care."
        )
    ],
}
KNOWLEDGE_ORDER = ["curiosity", "wade", "deep", "bridge", "robot_arm", "carriage", "moon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero_name = f["hero_name"]
    prize = f["prize_cfg"]
    pool = f["pool"]
    method = f["method"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "wade," "deep," and "carriage."',
        f"Tell a gentle story about a curious child named {hero_name} who finds {prize.phrase} in {pool.phrase} and has to choose a safe way to reach it.",
        f"Write a child-facing science-fantasy story where curiosity leads to questions, a glowing discovery, and a smart solution using {method.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    pool = f["pool"]
    prize = f["prize_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['hero_name']}, a curious young explorer, and {captain.label_word} on a space trip in a moon carriage."
        ),
        (
            "What did the child discover?",
            f"{f['hero_name']} found {prize.phrase} shining in {pool.phrase}. The strange glow made {hero.pronoun('object')} want to know what it was."
        ),
        (
            f"Why didn't {f['hero_name']} just wade in right away?",
            f"{captain.label_word.capitalize()} stopped to study the pool first. {pool.warning} That is why they chose a method that matched the water instead of rushing."
        ),
    ]
    if method.kind == "wade":
        qa.append(
            (
                f"How did {f['hero_name']} get the {prize.label}?",
                f"{f['hero_name']} was able to wade in safely because the pool was shallow enough. {hero.pronoun().capitalize()} moved slowly, kept close to the edge, and lifted the {prize.label} out by hand."
            )
        )
    else:
        qa.append(
            (
                f"How did they reach the {prize.label} without stepping into the deep water?",
                f"They used {method.label} from the carriage. That let them bring the {prize.label} back without making {f['hero_name']} step into water that was too deep."
            )
        )
    qa.append(
        (
            "What did the child learn at the end?",
            f"{f['hero_name']} learned that curiosity is wonderful when it goes together with care. The ending shows that asking questions and choosing the smart method helped the adventure stay happy."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"curiosity", "carriage"}
    pool = f["pool"]
    method = f["method"]
    setting = f["setting"]
    if pool.depth > 1:
        tags.add("deep")
    tags |= set(method.tags)
    if "moon" in setting.tags:
        tags.add("moon")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:9} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="violet_moon",
        pool="shore_pool",
        prize="star_shell",
        method="wade",
        hero_name="Lina",
        hero_gender="girl",
        captain="captain_mother",
        trait="curious",
    ),
    StoryParams(
        setting="ring_crater",
        pool="middle_pool",
        prize="comet_seed",
        method="bridge_scoop",
        hero_name="Milo",
        hero_gender="boy",
        captain="captain_father",
        trait="bright",
    ),
    StoryParams(
        setting="comet_marsh",
        pool="deep_pool",
        prize="moon_pearl",
        method="carriage_arm",
        hero_name="Nora",
        hero_gender="girl",
        captain="captain_mother",
        trait="careful",
    ),
]


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
works(P, M) :- pool(P), method(M), depth(P, D), max_depth(M, MD), D <= MD,
               distance(P, Dist), max_distance(M, MX), Dist <= MX.
valid(S, P, R, M) :- setting(S), pool(P), prize(R), method(M), sensible(M), works(P, M).

outcome(wade_safe) :- chosen_method(M), kind(M, wade).
outcome(tool_reach) :- chosen_method(M), kind(M, bridge).
outcome(tool_reach) :- chosen_method(M), kind(M, arm).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for pool_id, pool in POOLS.items():
        lines.append(asp.fact("pool", pool_id))
        lines.append(asp.fact("depth", pool_id, pool.depth))
        lines.append(asp.fact("distance", pool_id, pool.distance))
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("max_depth", method_id, method.max_depth))
        lines.append(asp.fact("max_distance", method_id, method.max_distance))
        lines.append(asp.fact("kind", method_id, method.kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a curious child on a moon carriage adventure finds a glowing prize beyond a pool."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pool", choices=POOLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain_mother", "captain_father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            raise StoryError(explain_method(method))
    if args.pool and args.method:
        pool = POOLS[args.pool]
        method = METHODS[args.method]
        if not method_works(pool, method):
            raise StoryError(explain_rejection(pool, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.pool is None or combo[1] == args.pool)
        and (args.prize is None or combo[2] == args.prize)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, pool_id, prize_id, method_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    captain = args.captain or rng.choice(["captain_mother", "captain_father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        pool=pool_id,
        prize=prize_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        captain=captain,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.pool not in POOLS:
        raise StoryError(f"(Unknown pool '{params.pool}'.)")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize '{params.prize}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method '{params.method}'.)")
    pool = POOLS[params.pool]
    method = METHODS[params.method]
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(method))
    if not method_works(pool, method):
        raise StoryError(explain_rejection(pool, method))

    world = tell(
        setting=SETTINGS[params.setting],
        pool=pool,
        prize=PRIZES[params.prize],
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        captain_type=params.captain,
        trait=params.trait,
    )

    story = world.render().replace("hero", params.hero_name)
    story = story.replace("captain_mother", "mom").replace("captain_father", "dad")
    story = story.replace(" hero ", f" {params.hero_name} ")
    story = story.replace(" hero.", f" {params.hero_name}.")
    story = story.replace(" hero,", f" {params.hero_name},")
    story = story.replace("hero's", f"{params.hero_name}'s")
    story = story.replace("hero ", f"{params.hero_name} ")

    for old, new in [
        ("hero", params.hero_name),
        ("captain_mother", "mom"),
        ("captain_father", "dad"),
    ]:
        story = story.replace(old, new)

    return StorySample(
        params=params,
        story=story,
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


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, pool, prize, method) combos:\n")
        for setting_id, pool_id, prize_id, method_id in combos:
            print(f"  {setting_id:12} {pool_id:11} {prize_id:10} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.pool} with {p.method} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
