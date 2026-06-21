#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/purr_croquette_wet_stairs_suspense_rhyming_story.py
===============================================================================

A standalone storyworld about a child carrying croquettes to a waiting cat on
wet stairs. The world model tracks slippery steps, wobbling bowls, careful help,
and the cat's hunger. The rendered story keeps a child-facing rhyming tone with
a small suspense beat and a concrete ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/purr_croquette_wet_stairs_suspense_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/purr_croquette_wet_stairs_suspense_rhyming_story.py --stairs porch --container bowl
    python storyworlds/worlds/gpt-5.4/purr_croquette_wet_stairs_suspense_rhyming_story.py --method tiptoe_fast
    python storyworlds/worlds/gpt-5.4/purr_croquette_wet_stairs_suspense_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/purr_croquette_wet_stairs_suspense_rhyming_story.py --verify
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "cat":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Staircase:
    id: str
    label: str
    phrase: str
    wet_source: str
    landing: str
    wetness: int
    steepness: int
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    wobble: int
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    drying: int
    support: int
    text: str
    rescue_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CatConfig:
    id: str
    name: str
    coat: str
    waiting_sound: str
    curl_place: str
    tags: set[str] = field(default_factory=set)


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


def hazard_score(stairs: Staircase, container: Container) -> int:
    return stairs.wetness + stairs.steepness + container.wobble


def method_power(method: Method) -> int:
    return method.drying + method.support


def is_safe(method: Method, stairs: Staircase, container: Container) -> bool:
    return method_power(method) >= hazard_score(stairs, container)


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for stair_id in STAIRS:
        for container_id in CONTAINERS:
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN:
                    combos.append((stair_id, container_id, method_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    stairs = STAIRS[params.stairs]
    container = CONTAINERS[params.container]
    return "safe" if is_safe(method, stairs, container) else "spill"


def _r_risk(world: World) -> list[str]:
    child = world.get("child")
    stairs = world.get("stairs")
    bowl = world.get("container")
    out: list[str] = []
    if child.meters["climbing"] < THRESHOLD:
        return out
    sig = ("risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["risk"] += stairs.attrs.get("wetness", 0) + stairs.attrs.get("steepness", 0)
    bowl.meters["risk"] += bowl.attrs.get("wobble", 0)
    out.append("__risk__")
    return out


def _r_spill(world: World) -> list[str]:
    child = world.get("child")
    bowl = world.get("container")
    stairs = world.get("stairs")
    out: list[str] = []
    if child.meters["risk"] + bowl.meters["risk"] < world.facts.get("safety_power", 0) + 1:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["spilled"] += 1
    child.memes["alarm"] += 1
    stairs.meters["messy"] += 1
    world.get("cat").memes["hungry"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="spill", tag="physical", apply=_r_spill),
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
        for sent in produced:
            world.say(sent)
    return produced


def predict(world: World, method: Method) -> dict:
    sim = world.copy()
    sim.facts["safety_power"] = method_power(method)
    sim.get("child").meters["climbing"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": sim.get("container").meters["spilled"] >= THRESHOLD,
        "risk": sim.get("child").meters["risk"] + sim.get("container").meters["risk"],
    }


def introduce(world: World, child: Entity, parent: Entity, cat: Entity, stairs: Staircase) -> None:
    world.say(
        f"{child.id} heard a soft {cat.attrs['waiting_sound']} above {stairs.phrase}, "
        f"where {cat.id} waited by {stairs.landing}. The house was quiet, but the shiny steps "
        f"made a hush that felt deep."
    )
    world.say(
        f"It had just been left {stairs.wet_source}, and each wet stair gave back a silver gleam. "
        f"In that small bright shine, the climb did not feel simple; it felt like a little dream."
    )
    world.say(
        f"By the kitchen tin stood a dish of croquette bites for {cat.id} to eat. "
        f"{child.id} wanted to carry them up at once on quick and eager feet."
    )
    parent.memes["care"] += 1
    child.memes["love"] += 1
    cat.memes["hungry"] += 1


def choose_container(world: World, child: Entity, container: Container) -> None:
    world.say(
        f"{child.id} tipped the croquettes into {container.phrase}. "
        f"They made {container.rhyme} as they settled in a heap, "
        f"and that tiny sound made the stairway seem more steep."
    )
    world.get("container").attrs["wobble"] = container.wobble


def warn(world: World, child: Entity, parent: Entity, stairs: Staircase, method: Method, container: Container) -> None:
    pred = predict(world, method)
    world.facts["predicted_spill"] = pred["spill"]
    world.facts["predicted_risk"] = pred["risk"]
    if pred["spill"]:
        world.say(
            f'"Wait," said {parent.label_word}, very low. "Those stairs are wet, and {container.label} can wobble so. '
            f'If you hurry on that slippery flight, the croquettes may tumble in the light."'
        )
    else:
        world.say(
            f'"Wait," said {parent.label_word}, very low. "The stairs are wet, so slow is best to go. '
            f'We can still feed {world.get("cat").id}, but only if we move with care and not a bit too fleet."'
        )
    child.memes["worry"] += 1
    parent.memes["caution"] += 1


def suspense_beat(world: World, child: Entity, stairs: Staircase) -> None:
    world.say(
        f"{child.id} looked up. The wet stairs shone, one by one, like moonlit stone. "
        f"For half a breath {child.pronoun()} stood quite still, listening to each tiny drip and spill."
    )
    world.say(
        f"Above, a whiskered shadow moved, then froze. No one knew what the next small step would choose."
    )


def use_method(world: World, child: Entity, parent: Entity, method: Method, stairs: Staircase) -> None:
    world.facts["safety_power"] = method_power(method)
    world.say(
        f"Then {parent.label_word} and {child.id} {method.text}. "
        f"The rail felt cool, the air felt tight, and every step held a pinch of night."
    )
    child.meters["climbing"] += 1
    child.meters["support"] += method.support
    world.get("stairs").meters["dryness"] += method.drying
    propagate(world, narrate=False)


def safe_arrival(world: World, child: Entity, cat: Entity, container: Container, stairs: Staircase) -> None:
    child.memes["relief"] += 1
    cat.memes["hungry"] = 0.0
    cat.memes["content"] += 1
    world.say(
        f"Up went {child.id}, slow and light, past the last wet gleam of night. "
        f"Not one croquette slipped away. {cat.id} reached the top and purred to say hello in {cat.attrs['waiting_sound']} play."
    )
    world.say(
        f"Soon the bowl was set by {stairs.landing}, safe and dry. "
        f"{cat.id} bent near with a happy purr, and the whole small worry fluttered by."
    )
    world.say(
        f"In the end, the stairs still shone, but not with fright alone. "
        f"Now they glimmered under careful feet, and the croquette supper smelled warm and sweet."
    )


def spill_then_fix(world: World, child: Entity, parent: Entity, cat: Entity, method: Method, stairs: Staircase) -> None:
    world.say(
        f"But halfway up came a tiny skid. The bowl gave a tick, then a tilt, then a hidy-hid. "
        f"Croquettes skipped down with a clatter-clack, bouncing off the wet stair and sliding back."
    )
    world.say(
        f"{child.id} gasped, but {parent.label_word} held {child.pronoun('object')} fast. "
        f'"Feet first, food next," said {parent.pronoun()}, calm and vast.'
    )
    world.say(
        f"Together they went back down, wiped each shining tread, and filled the bowl again with the croquettes that had not spread."
    )
    world.say(
        f"Then {parent.label_word} {method.rescue_text}. Up on the landing, {cat.id} gave a round soft purr, "
        f"as if to say that waiting a little had been worth it for her."
    )
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    cat.memes["hungry"] = 0.0
    cat.memes["content"] += 1
    world.say(
        f"When the tale was done, the wet stairs no longer seemed sly. "
        f"They were only stairs to dry, then climb, with a hand to help and a patient eye."
    )


def tell(
    stairs: Staircase,
    container: Container,
    method: Method,
    cat_cfg: CatConfig,
    child_name: str = "Nora",
    child_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    cat = world.add(
        Entity(
            id=cat_cfg.name,
            kind="character",
            type="cat",
            role="cat",
            label="the cat",
            attrs={"waiting_sound": cat_cfg.waiting_sound, "curl_place": cat_cfg.curl_place},
            tags=set(cat_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="stairs",
            kind="thing",
            type="stairs",
            label=stairs.label,
            phrase=stairs.phrase,
            attrs={"wetness": stairs.wetness, "steepness": stairs.steepness, "sound": stairs.sound},
            tags=set(stairs.tags),
        )
    )
    world.add(
        Entity(
            id="container",
            kind="thing",
            type="container",
            label=container.label,
            phrase=container.phrase,
            attrs={"wobble": container.wobble},
            tags=set(container.tags),
        )
    )

    introduce(world, child, parent, cat, stairs)
    world.para()
    choose_container(world, child, container)
    warn(world, child, parent, stairs, method, container)
    suspense_beat(world, child, stairs)
    world.para()
    use_method(world, child, parent, method, stairs)

    outcome = "safe" if world.get("container").meters["spilled"] < THRESHOLD else "spill"
    if outcome == "safe":
        safe_arrival(world, child, cat, container, stairs)
    else:
        spill_then_fix(world, child, parent, cat, method, stairs)

    world.facts.update(
        child=child,
        parent=parent,
        cat=cat,
        stairs_cfg=stairs,
        container_cfg=container,
        method=method,
        outcome=outcome,
        spilled=world.get("container").meters["spilled"] >= THRESHOLD,
        safety_power=method_power(method),
        hazard=hazard_score(stairs, container),
    )
    return world


KNOWLEDGE = {
    "purr": [
        (
            "What is a purr?",
            "A purr is a soft, rumbly sound many cats make when they feel calm or pleased. It can also mean a cat feels safe and close to someone it trusts.",
        )
    ],
    "croquette": [
        (
            "What is a croquette in this story?",
            "Here a croquette is a little crunchy piece of cat food. Many tiny croquettes together make a meal for a cat.",
        )
    ],
    "wet_stairs": [
        (
            "Why are wet stairs slippery?",
            "Wet stairs are slippery because the water makes shoes grip less well. That means feet can slide instead of sticking firmly to each step.",
        )
    ],
    "handrail": [
        (
            "Why does holding a handrail help on stairs?",
            "A handrail gives your body another point of support. If one foot slips a little, your hand can help keep you steady.",
        )
    ],
    "towel": [
        (
            "Why does drying a stair with a towel help?",
            "A towel soaks up water. When there is less water on the step, it is easier for shoes to grip and stay steady.",
        )
    ],
    "cat_wait": [
        (
            "Can a cat wait a little for food?",
            "Yes, a cat can wait a little while a grown-up makes things safe. Waiting a moment is better than hurrying into danger.",
        )
    ],
}
KNOWLEDGE_ORDER = ["purr", "croquette", "wet_stairs", "handrail", "towel", "cat_wait"]


STAIRS = {
    "porch": Staircase(
        id="porch",
        label="porch stairs",
        phrase="the wet porch stairs",
        wet_source="shiny from the rain",
        landing="the porch landing",
        wetness=2,
        steepness=2,
        sound="plink-plink",
        tags={"wet_stairs", "towel", "handrail"},
    ),
    "garden": Staircase(
        id="garden",
        label="garden steps",
        phrase="the wet garden steps",
        wet_source="splashed by the hose",
        landing="the mossy top step",
        wetness=1,
        steepness=1,
        sound="tip-tip",
        tags={"wet_stairs", "towel", "handrail"},
    ),
    "hall": Staircase(
        id="hall",
        label="hall stairs",
        phrase="the wet hall stairs",
        wet_source="freshly mopped",
        landing="the upstairs hall rug",
        wetness=2,
        steepness=1,
        sound="swish-swish",
        tags={"wet_stairs", "towel", "handrail"},
    ),
}

CONTAINERS = {
    "bowl": Container(
        id="bowl",
        label="bowl",
        phrase="a round blue bowl",
        wobble=2,
        rhyme="a pecking click-click",
        tags={"croquette"},
    ),
    "cup": Container(
        id="cup",
        label="cup",
        phrase="a little handled cup",
        wobble=1,
        rhyme="a tidy tick-tick",
        tags={"croquette"},
    ),
    "tin": Container(
        id="tin",
        label="tin",
        phrase="a small lidded tin",
        wobble=0,
        rhyme="a muted tin-tin",
        tags={"croquette"},
    ),
}

METHODS = {
    "towel_and_rail": Method(
        id="towel_and_rail",
        label="dry the stairs and hold the rail",
        sense=3,
        drying=2,
        support=2,
        text="wiped the wet edges with a towel and held the rail on the climb",
        rescue_text="carried the fresh bowl while the child kept one hand on the rail",
        qa_text="They dried the stairs with a towel and used the handrail",
        tags={"towel", "handrail"},
    ),
    "grownup_carries": Method(
        id="grownup_carries",
        label="let the grown-up carry the food",
        sense=3,
        drying=0,
        support=4,
        text="let the grown-up carry the croquettes while the child climbed close beside the rail",
        rescue_text="carried the bowl the second time while the child followed carefully",
        qa_text="The grown-up carried the croquettes while the child climbed carefully",
        tags={"handrail", "cat_wait"},
    ),
    "slow_with_rail": Method(
        id="slow_with_rail",
        label="go slowly with the rail",
        sense=2,
        drying=0,
        support=2,
        text="took the rail and began the climb step by careful step",
        rescue_text="carried the bowl on the second try after more drying and steadier steps",
        qa_text="They used the rail and went slowly",
        tags={"handrail"},
    ),
    "tiptoe_fast": Method(
        id="tiptoe_fast",
        label="tiptoe quickly",
        sense=1,
        drying=0,
        support=0,
        text="tried to tiptoe quickly",
        rescue_text="hurried again",
        qa_text="They tried to hurry on the wet stairs",
        tags=set(),
    ),
}

CATS = {
    "miso": CatConfig(
        id="miso",
        name="Miso",
        coat="ginger",
        waiting_sound="mrrr-mrrr",
        curl_place="the old mat",
        tags={"purr", "cat_wait"},
    ),
    "pebble": CatConfig(
        id="pebble",
        name="Pebble",
        coat="gray",
        waiting_sound="prrt-prrt",
        curl_place="the top rug",
        tags={"purr", "cat_wait"},
    ),
    "socks": CatConfig(
        id="socks",
        name="Socks",
        coat="black-and-white",
        waiting_sound="brrr-brrr",
        curl_place="the dry corner",
        tags={"purr", "cat_wait"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "Ava", "Ivy", "Ella", "Ruby", "Tessa"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Sam", "Noah", "Eli", "Theo", "Max"]


@dataclass
class StoryParams:
    stairs: str
    container: str
    method: str
    cat: str
    child_name: str
    child_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        stairs="porch",
        container="bowl",
        method="towel_and_rail",
        cat="miso",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        stairs="garden",
        container="cup",
        method="slow_with_rail",
        cat="pebble",
        child_name="Leo",
        child_gender="boy",
        parent="father",
    ),
    StoryParams(
        stairs="hall",
        container="bowl",
        method="slow_with_rail",
        cat="socks",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        stairs="porch",
        container="tin",
        method="grownup_carries",
        cat="miso",
        child_name="Finn",
        child_gender="boy",
        parent="father",
    ),
]


def explain_method(mid: str) -> str:
    method = METHODS[mid]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{mid}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cat = f["cat"]
    stairs = f["stairs_cfg"]
    container = f["container_cfg"]
    outcome = f["outcome"]
    if outcome == "spill":
        return [
            f'Write a suspenseful rhyming story for a 3-to-5-year-old that includes the words "purr" and "croquette". Set it on {stairs.phrase}.',
            f"Tell a rhyming story where {child.id} tries to carry croquettes to {cat.id} up wet stairs, something spills, and a calm grown-up helps make the climb safe.",
            f"Write a child-friendly poem-story about shiny wet steps, a waiting cat, and a small spill that becomes a careful lesson.",
        ]
    return [
        f'Write a suspenseful rhyming story for a 3-to-5-year-old that includes the words "purr" and "croquette". Set it on {stairs.phrase}.',
        f"Tell a gentle rhyming story where {child.id} carries croquettes in {container.phrase} toward a waiting cat, and a grown-up helps with the slippery climb.",
        "Write a short story-poem with a worried pause in the middle and a safe ending that proves careful steps can beat a slippery problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    cat = f["cat"]
    stairs = f["stairs_cfg"]
    container = f["container_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child carrying croquettes to {cat.id}, and {pw} who helps on the wet stairs. The waiting cat makes the climb feel urgent and suspenseful.",
        ),
        (
            f"Why did {child.id} want to go up the stairs?",
            f"{child.id} wanted to bring croquettes to {cat.id}, who was waiting above the stairs. Hearing the cat made {child.id} want to hurry.",
        ),
        (
            "Why were the stairs a problem?",
            f"The stairs were wet, so they were slippery. That made carrying {container.label} risky because a foot or the bowl could slip.",
        ),
        (
            f"What did {pw} do to help?",
            f"{method.qa_text}. {pw.capitalize()} helped because the wet stairs made balance more important than speed.",
        ),
    ]
    if outcome == "safe":
        qa.append(
            (
                f"How did the story end?",
                f"It ended safely, with the croquettes reaching {cat.id} and a soft purr at the top. The ending image proves the danger changed because the careful plan worked.",
            )
        )
    else:
        qa.append(
            (
                "What happened on the stairs?",
                f"There was a little slip, and the croquettes scattered down the wet steps. {pw.capitalize()} steadied {child.id} first, because staying safe mattered more than the food.",
            )
        )
        qa.append(
            (
                "How was the problem finally solved?",
                f"They went back down, made the stairs safer, and tried again with more help. After that, {cat.id} got supper and answered with a purr.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"purr", "croquette"}
    stairs_cfg = world.facts["stairs_cfg"]
    method = world.facts["method"]
    cat = world.facts["cat"]
    tags |= set(stairs_cfg.tags) | set(method.tags) | set(cat.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(St, C, M) :- stairs(St), container(C), method(M), sensible(M).

hazard(H) :- chosen_stairs(St), wetness(St, W), steepness(St, T),
             chosen_container(C), wobble(C, B), H = W + T + B.
power(P) :- chosen_method(M), drying(M, D), support(M, S), P = D + S.
outcome(safe) :- hazard(H), power(P), P >= H.
outcome(spill) :- hazard(H), power(P), P < H.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for stair_id, stair in STAIRS.items():
        lines.append(asp.fact("stairs", stair_id))
        lines.append(asp.fact("wetness", stair_id, stair.wetness))
        lines.append(asp.fact("steepness", stair_id, stair.steepness))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        lines.append(asp.fact("wobble", container_id, container.wobble))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("drying", method_id, method.drying))
        lines.append(asp.fact("support", method_id, method.support))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_stairs", params.stairs),
            asp.fact("chosen_container", params.container),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a cat, croquettes, and wet stairs."
    )
    ap.add_argument("--stairs", choices=STAIRS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--cat", choices=CATS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.stairs is None or combo[0] == args.stairs)
        and (args.container is None or combo[1] == args.container)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    stairs_id, container_id, method_id = rng.choice(sorted(combos))
    cat_id = args.cat or rng.choice(sorted(CATS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        stairs=stairs_id,
        container=container_id,
        method=method_id,
        cat=cat_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.stairs not in STAIRS:
        raise StoryError(f"(Unknown stairs option: {params.stairs})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container option: {params.container})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method option: {params.method})")
    if params.cat not in CATS:
        raise StoryError(f"(Unknown cat option: {params.cat})")
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    world = tell(
        stairs=STAIRS[params.stairs],
        container=CONTAINERS[params.container],
        method=METHODS[params.method],
        cat_cfg=CATS[params.cat],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only in clingo:", sorted(asp_set - py))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

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
        sample = generate(CURATED[0])
        if not sample.story or "croquette" not in sample.story or "purr" not in sample.story:
            raise StoryError("(Smoke test failed: generated story missing required seed words or empty text.)")
        print("OK: smoke test story generated successfully.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (stairs, container, method) combos:\n")
        for stairs_id, container_id, method_id in combos:
            print(f"  {stairs_id:8} {container_id:8} {method_id}")
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
            header = f"### {p.child_name}: {p.container} on {p.stairs} stairs ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
