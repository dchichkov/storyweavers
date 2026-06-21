#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/time_waive_magic_mystery_to_solve_animal.py
======================================================================

A small story world about woodland animals solving a gentle magical mystery
before home-time.

Premise
-------
Each evening, a magic signal in the woods tells the young animals when it is
time to come home. One day the signal behaves strangely: it stays quiet when it
should ring, or it flashes too early. The hero and a helper follow a clue,
solve the mystery, and restore the signal before dark.

This world rebuilds that tiny tale as state, not as one frozen paragraph with
swapped nouns. It tracks physical meters (hidden, blocked, restored) and
emotional memes (worry, curiosity, relief), uses a small causal rule engine,
and includes an ASP twin for the reasonableness gate and outcome parity.

Run it
------
    python storyworlds/worlds/gpt-5.4/time_waive_magic_mystery_to_solve_animal.py
    python storyworlds/worlds/gpt-5.4/time_waive_magic_mystery_to_solve_animal.py --setting meadow --cause tangled_vine
    python storyworlds/worlds/gpt-5.4/time_waive_magic_mystery_to_solve_animal.py --cause shiny_leaf --solution kindly_ask
    python storyworlds/worlds/gpt-5.4/time_waive_magic_mystery_to_solve_animal.py --all
    python storyworlds/worlds/gpt-5.4/time_waive_magic_mystery_to_solve_animal.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/time_waive_magic_mystery_to_solve_animal.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"owl_mother", "fox_girl", "rabbit_girl", "mouse_girl", "deer_girl"}
        male = {"owl_father", "fox_boy", "rabbit_boy", "mouse_boy", "hedgehog_boy", "badger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    clue_place: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    phrase: str
    home_time: str
    normal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    symptom: str
    notice: str
    clue: str
    trail: str
    reveal: str
    allows: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    act: str
    result: str
    fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_disturbance(world: World) -> list[str]:
    out: list[str] = []
    signal = world.entities.get("signal")
    if signal is None:
        return out
    if signal.meters["disturbed"] >= THRESHOLD:
        sig = ("disturbance", "signal")
        if sig not in world.fired:
            world.fired.add(sig)
            for ent in list(world.entities.values()):
                if ent.role in {"hero", "helper", "elder"}:
                    ent.memes["concern"] += 1
            out.append("__disturbance__")
    return out


def _r_clue(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if hero is None or helper is None:
        return []
    if hero.meters["saw_clue"] >= THRESHOLD:
        sig = ("clue", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["hope"] += 1
            helper.memes["hope"] += 1
    return []


def _r_restore(world: World) -> list[str]:
    signal = world.entities.get("signal")
    if signal is None:
        return []
    if signal.meters["restored"] >= THRESHOLD:
        sig = ("restore", "signal")
        if sig not in world.fired:
            world.fired.add(sig)
            for ent in list(world.entities.values()):
                if ent.role in {"hero", "helper", "elder"}:
                    ent.memes["relief"] += 1
                    ent.memes["joy"] += 1
            world.get("woods").meters["calm"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="disturbance", tag="mystery", apply=_r_disturbance),
    Rule(name="clue", tag="mystery", apply=_r_clue),
    Rule(name="restore", tag="resolution", apply=_r_restore),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the moon meadow",
        detail="Clover heads nodded under the evening breeze, and the path home shone pale between the grasses.",
        clue_place="a soft patch of moss beside the path",
        allows={"tangled_vine", "borrowed_charm"},
        tags={"meadow"},
    ),
    "riverbank": Setting(
        id="riverbank",
        place="the silver riverbank",
        detail="The water whispered past the reeds, and flat stones held the last orange light.",
        clue_place="a line of smooth stones near the reeds",
        allows={"borrowed_charm", "shiny_leaf"},
        tags={"river"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the lantern orchard",
        detail="Round apples hung over the path, and little pockets of dusk gathered under the branches.",
        clue_place="a rooty patch beneath the oldest tree",
        allows={"tangled_vine", "shiny_leaf"},
        tags={"orchard"},
    ),
}

SIGNALS = {
    "moonbell": Signal(
        id="moonbell",
        label="Moonbell",
        phrase="the Moonbell",
        home_time="home-time",
        normal="glowed silver and rang one clear note",
        tags={"bell", "magic"},
    ),
    "duskflower": Signal(
        id="duskflower",
        label="Duskflower",
        phrase="the Duskflower",
        home_time="home-time",
        normal="opened its blue petals and spilled a small ribbon of gold light",
        tags={"flower", "magic"},
    ),
    "starlantern": Signal(
        id="starlantern",
        label="Starlantern",
        phrase="the Starlantern",
        home_time="home-time",
        normal="shone like a warm star above the stump",
        tags={"lantern", "magic"},
    ),
}

CAUSES = {
    "tangled_vine": Cause(
        id="tangled_vine",
        symptom="late",
        notice="When it was {home_time}, {signal} stayed quiet.",
        clue="On the bark below it lay one fresh green curl and a dusting of rubbed leaves.",
        trail="The clue pointed upward, where a thin vine had crept around the magic thing and pinched it tight.",
        reveal="The mystery was not a thief at all. A wandering vine had wrapped itself where it should never have grown.",
        allows={"meadow", "orchard"},
        fixes={"gently_unwind"},
        tags={"vine", "plant"},
    ),
    "borrowed_charm": Cause(
        id="borrowed_charm",
        symptom="late",
        notice="When it was {home_time}, {signal} stayed still, as if it had forgotten the time.",
        clue="In the dust below sparkled a trail of tiny round pawprints and one silver thread.",
        trail="The small prints led to a low nook where a sleepy little mouse was rocking a baby sibling.",
        reveal="The charm had been borrowed, not stolen. The little mouse had tucked it beside the baby because the soft glow made the nook feel less dark.",
        allows={"meadow", "riverbank"},
        fixes={"kindly_ask"},
        tags={"borrow", "kindness"},
    ),
    "shiny_leaf": Cause(
        id="shiny_leaf",
        symptom="early",
        notice="Long before {home_time}, {signal} suddenly flashed too soon.",
        clue="Across the ground ran a bright stripe of light that did not belong there.",
        trail="Following the stripe, they found a glossy leaf leaned against a stone at just the wrong angle.",
        reveal="No spell had gone wild. The sunset had bounced off the shiny leaf and fooled the magic into thinking evening had come.",
        allows={"riverbank", "orchard"},
        fixes={"turn_aside"},
        tags={"reflection", "light"},
    ),
}

SOLUTIONS = {
    "gently_unwind": Solution(
        id="gently_unwind",
        act="Together they loosened the vine a careful turn at a time, so no stem snapped and no magic bellied up in a hurry.",
        result="{signal} gave a tiny shiver, then worked the way it should.",
        fixes={"tangled_vine"},
        tags={"vine"},
    ),
    "kindly_ask": Solution(
        id="kindly_ask",
        act='They knelt by the nook and spoke softly. "May we carry the charm back now?" the hero asked. "We will help your baby sibling feel brave in another way."',
        result="The little mouse nodded, returned the charm, and the magic settled back into place.",
        fixes={"borrowed_charm"},
        tags={"kindness", "sharing"},
    ),
    "turn_aside": Solution(
        id="turn_aside",
        act="The helper tipped the glossy leaf away from the sunset, and the hero tucked it under a root where it could no longer throw a false gleam.",
        result="At once the mistaken shine disappeared, and the magic waited for the real evening.",
        fixes={"shiny_leaf"},
        tags={"reflection"},
    ),
}

ANIMALS = [
    ("Pip", "rabbit_boy", "rabbit"),
    ("Mimi", "mouse_girl", "mouse"),
    ("Fern", "deer_girl", "fawn"),
    ("Tuck", "hedgehog_boy", "hedgehog"),
    ("Roo", "fox_girl", "fox"),
    ("Nibbles", "rabbit_girl", "rabbit"),
    ("Moss", "badger", "badger"),
]

ELDERS = [
    ("Grandmother Owl", "owl_mother", "owl"),
    ("Uncle Badger", "badger", "badger"),
]

KNOWLEDGE = {
    "magic": [(
        "What is magic in a story like this?",
        "Magic in a story is something wonderful that does not happen in ordinary life, like a bell that knows the right time to ring. It helps the story feel bright and mysterious."
    )],
    "bell": [(
        "What does a bell do?",
        "A bell makes a ringing sound that people or animals can hear from far away. In stories, a bell can be used to call everyone together."
    )],
    "flower": [(
        "How can a flower be magical in a story?",
        "A magical flower can glow or open at a special moment, even though real flowers do not usually do that on purpose. The magic gives the characters a clue to notice."
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a light with a cover around it, so it can shine safely and be carried or hung up. It helps people see when it gets dark."
    )],
    "vine": [(
        "What is a vine?",
        "A vine is a long, bending plant that can curl and climb around trees, posts, or fences. If it grows in the wrong place, it can tangle things up."
    )],
    "borrow": [(
        "What does it mean to borrow something?",
        "To borrow something means you use it for a little while and then give it back. It is kind to ask first and careful to return it."
    )],
    "kindness": [(
        "Why is kindness useful when solving a problem?",
        "Kindness helps other people feel safe enough to tell the truth and help fix the problem. A gentle voice can solve more than a sharp one."
    )],
    "reflection": [(
        "What is a reflection?",
        "A reflection is light bouncing off a shiny surface, like water, glass, or a glossy leaf. Sometimes that bounced light can trick your eyes."
    )],
    "river": [(
        "What do you find by a riverbank?",
        "You often find water, reeds, stones, and damp soil by a riverbank. Animals may come there to drink or listen to the water."
    )],
    "meadow": [(
        "What is a meadow?",
        "A meadow is an open field full of grasses and wildflowers. Small animals can hide, hop, and play there."
    )],
    "orchard": [(
        "What is an orchard?",
        "An orchard is a place where many fruit trees grow together. Their branches can make cool shady paths underneath."
    )],
}
KNOWLEDGE_ORDER = [
    "magic", "bell", "flower", "lantern", "vine", "borrow", "kindness",
    "reflection", "river", "meadow", "orchard",
]


def valid_combo(setting_id: str, cause_id: str, solution_id: str) -> bool:
    if setting_id not in SETTINGS or cause_id not in CAUSES or solution_id not in SOLUTIONS:
        return False
    setting = SETTINGS[setting_id]
    cause = CAUSES[cause_id]
    solution = SOLUTIONS[solution_id]
    return cause_id in setting.allows and cause_id in solution.fixes and setting_id in cause.allows


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for signal_id in SIGNALS:
            for cause_id in CAUSES:
                for solution_id in SOLUTIONS:
                    if valid_combo(setting_id, cause_id, solution_id):
                        combos.append((setting_id, signal_id, cause_id, solution_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    signal: str
    cause: str
    solution: str
    hero_name: str
    hero_type: str
    hero_species: str
    helper_name: str
    helper_type: str
    helper_species: str
    elder_name: str
    elder_type: str
    elder_species: str
    seed: Optional[int] = None


def predict_issue(world: World, cause: Cause) -> dict:
    sim = world.copy()
    signal = sim.get("signal")
    if cause.symptom == "late":
        signal.meters["silent"] += 1
        signal.meters["disturbed"] += 1
    else:
        signal.meters["early"] += 1
        signal.meters["disturbed"] += 1
    propagate(sim, narrate=False)
    return {
        "disturbed": signal.meters["disturbed"] >= THRESHOLD,
        "concern": sum(ent.memes["concern"] for ent in sim.entities.values() if ent.role in {"hero", "helper", "elder"}),
    }


def setup_routine(world: World, hero: Entity, helper: Entity, elder: Entity, signal: Signal) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} the {hero.attrs['species']} and {helper.id} the {helper.attrs['species']} loved to watch {signal.phrase} each evening."
    )
    world.say(world.setting.detail)
    world.say(
        f"At {signal.home_time}, {signal.phrase} always {signal.normal}, and every young animal knew it was time to pad, hop, or scamper home."
    )
    elder.memes["duty"] += 1
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1


def disturbance(world: World, hero: Entity, helper: Entity, elder: Entity, signal_cfg: Signal, cause: Cause) -> None:
    pred = predict_issue(world, cause)
    signal = world.get("signal")
    if cause.symptom == "late":
        signal.meters["silent"] += 1
    else:
        signal.meters["early"] += 1
    signal.meters["disturbed"] += 1
    propagate(world, narrate=False)
    world.say(cause.notice.format(home_time=signal_cfg.home_time, signal=signal_cfg.phrase))
    if pred["disturbed"]:
        world.say(
            f"{hero.id}'s ears lifted, and {helper.id} stopped mid-step. Something about the magic was plainly wrong."
        )
    world.say(
        f'"We must solve this before the little ones wander too long," said {elder.id}. "{signal_cfg.home_time} matters, and I will not waive the rule just because the woods are puzzled."'
    )


def search_for_clue(world: World, hero: Entity, helper: Entity, cause: Cause) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"So the two friends searched around {world.setting.clue_place}, looking for the smallest thing out of place."
    )
    hero.meters["saw_clue"] += 1
    propagate(world, narrate=False)
    world.say(cause.clue)
    world.say(
        f'"That is our clue," whispered {hero.id}. "A mystery always leaves a tiny trail if we take the time to look."'
    )


def follow_trail(world: World, hero: Entity, helper: Entity, cause: Cause) -> None:
    world.say(cause.trail)
    world.say(cause.reveal)
    world.facts["solved_by_reasoning"] = True
    if cause.id == "borrowed_charm":
        hero.memes["kindness"] += 1
        helper.memes["kindness"] += 1


def repair(world: World, hero: Entity, helper: Entity, signal_cfg: Signal, solution: Solution) -> None:
    signal = world.get("signal")
    world.say(solution.act)
    signal.meters["silent"] = 0.0
    signal.meters["early"] = 0.0
    signal.meters["disturbed"] = 0.0
    signal.meters["restored"] += 1
    propagate(world, narrate=False)
    world.say(solution.result.format(signal=signal_cfg.phrase))
    if signal_cfg.id == "moonbell":
        closing = "A clear silver ring rolled over the grass."
    elif signal_cfg.id == "duskflower":
        closing = "Blue petals opened slowly, and a gold ribbon spilled onto the path."
    else:
        closing = "A warm starry light shone over the stump and down the path home."
    world.say(closing)
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1


def closing(world: World, hero: Entity, helper: Entity, elder: Entity, signal_cfg: Signal) -> None:
    world.say(
        f'{elder.id} smiled at them both. "Now the woods can trust {signal.phrase} again," {elder.pronoun()} said.'
    )
    world.say(
        f"The younger animals lifted their heads, heard the true sign, and hurried home at the right time."
    )
    world.say(
        f"{hero.id} and {helper.id} walked beside the glowing path, pleased that a mystery had become a kindness-filled answer instead of a fright."
    )


def tell(
    setting: Setting,
    signal_cfg: Signal,
    cause: Cause,
    solution: Solution,
    hero_name: str,
    hero_type: str,
    hero_species: str,
    helper_name: str,
    helper_type: str,
    helper_species: str,
    elder_name: str,
    elder_type: str,
    elder_species: str,
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        attrs={"species": hero_species},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        attrs={"species": helper_species},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=elder_name,
        role="elder",
        attrs={"species": elder_species},
    ))
    world.add(Entity(
        id="signal",
        kind="thing",
        type="signal",
        label=signal_cfg.label,
        phrase=signal_cfg.phrase,
        role="signal",
        tags=set(signal_cfg.tags),
    ))
    world.add(Entity(id="woods", type="place", label=setting.place))

    world.facts["hero_name"] = hero_name
    world.facts["helper_name"] = helper_name
    world.facts["elder_name"] = elder_name

    setup_routine(world, hero, helper, elder, signal_cfg)
    world.para()
    disturbance(world, hero, helper, elder, signal_cfg, cause)
    search_for_clue(world, hero, helper, cause)
    world.para()
    follow_trail(world, hero, helper, cause)
    repair(world, hero, helper, signal_cfg, solution)
    world.para()
    closing(world, hero, helper, elder, signal_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        setting=setting,
        signal_cfg=signal_cfg,
        cause=cause,
        solution=solution,
        solved=world.get("signal").meters["restored"] >= THRESHOLD,
        symptom=cause.symptom,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    signal_cfg = f["signal_cfg"]
    cause = f["cause"]
    hero = f["hero"]
    helper = f["helper"]
    elder = f["elder"]
    return [
        f'Write an animal story for a 3-to-5-year-old with magic and a mystery to solve. Include the words "time" and "waive".',
        f"Tell a gentle mystery where {world.facts['hero_name']} the {hero.attrs['species']} and {world.facts['helper_name']} the {helper.attrs['species']} notice that {signal_cfg.phrase} behaves strangely at {signal_cfg.home_time} and must find out why.",
        f"Write a cozy woodland story where {elder.label} refuses to waive the {signal_cfg.home_time} rule, and two small animals solve the problem caused by {cause.id.replace('_', ' ')} before dark.",
    ]


def pair_noun(hero: Entity, helper: Entity) -> str:
    return f"a {hero.attrs['species']} and a {helper.attrs['species']}"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    elder = f["elder"]
    signal_cfg = f["signal_cfg"]
    cause = f["cause"]
    solution = f["solution"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, helper)}, {world.facts['hero_name']} and {world.facts['helper_name']}, and {elder.label} who watches over the woods. They all care about the magic sign that tells everyone when it is time to go home."
        ),
        (
            f"What was strange about {signal_cfg.phrase}?",
            f"{cause.notice.format(home_time=signal_cfg.home_time, signal=signal_cfg.phrase)} That strange moment started the mystery because the animals trusted the magic to tell the right time."
        ),
        (
            "Why did they need to solve the mystery quickly?",
            f"They needed the true home-time sign before the younger animals wandered too long or came home at the wrong moment. {elder.label} would not waive the rule, because the signal helped keep the woods orderly and safe."
        ),
        (
            "What clue helped them solve the mystery?",
            f"They found a clue near {world.setting.clue_place}: {cause.clue.lower()} The clue gave them a direction to follow instead of guessing wildly."
        ),
        (
            "What was really causing the problem?",
            f"{cause.reveal} Once they understood the real cause, the mystery stopped feeling scary and started feeling fixable."
        ),
        (
            "How did they fix the magic?",
            f"{solution.act} {solution.result.format(signal=signal_cfg.phrase)}"
        ),
        (
            "How did the story end?",
            f"The magic sign worked again, and the younger animals hurried home at the right time. {world.facts['hero_name']} and {world.facts['helper_name']} ended the story walking along the glowing path, proud that they had solved the mystery kindly."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["signal_cfg"].tags) | set(f["cause"].tags) | set(f["solution"].tags) | set(world.setting.tags)
    tags.add("magic")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="meadow",
        signal="moonbell",
        cause="tangled_vine",
        solution="gently_unwind",
        hero_name="Pip",
        hero_type="rabbit_boy",
        hero_species="rabbit",
        helper_name="Mimi",
        helper_type="mouse_girl",
        helper_species="mouse",
        elder_name="Grandmother Owl",
        elder_type="owl_mother",
        elder_species="owl",
    ),
    StoryParams(
        setting="riverbank",
        signal="starlantern",
        cause="borrowed_charm",
        solution="kindly_ask",
        hero_name="Fern",
        hero_type="deer_girl",
        hero_species="fawn",
        helper_name="Tuck",
        helper_type="hedgehog_boy",
        helper_species="hedgehog",
        elder_name="Uncle Badger",
        elder_type="badger",
        elder_species="badger",
    ),
    StoryParams(
        setting="orchard",
        signal="duskflower",
        cause="shiny_leaf",
        solution="turn_aside",
        hero_name="Roo",
        hero_type="fox_girl",
        hero_species="fox",
        helper_name="Moss",
        helper_type="badger",
        helper_species="badger",
        elder_name="Grandmother Owl",
        elder_type="owl_mother",
        elder_species="owl",
    ),
]


def explain_rejection(setting_id: str, cause_id: str, solution_id: str) -> str:
    if setting_id in SETTINGS and cause_id in CAUSES:
        if cause_id not in SETTINGS[setting_id].allows or setting_id not in CAUSES[cause_id].allows:
            return (
                f"(No story: {CAUSES[cause_id].id.replace('_', ' ')} is not a good fit for {SETTINGS[setting_id].place}. "
                f"Pick a setting where that clue and cause make sense.)"
            )
    if cause_id in CAUSES and solution_id in SOLUTIONS:
        if cause_id not in SOLUTIONS[solution_id].fixes:
            good = ", ".join(sorted(CAUSES[cause_id].fixes))
            return (
                f"(No story: solution '{solution_id}' does not actually fix cause '{cause_id}'. "
                f"Try one of: {good}.)"
            )
    return "(No story: this combination does not make a reasonable magical mystery.)"


def smoke_story(sample: StorySample) -> None:
    if not sample.story.strip():
        raise StoryError("Generated empty story.")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("Generated story contains unresolved template braces.")


ASP_RULES = r"""
compatible_setting(S, C) :- setting(S), cause(C), allows(S, C), cause_allows(C, S).
compatible_solution(C, Sol) :- cause(C), solution(Sol), fixes(Sol, C).
valid(S, Sig, C, Sol) :- setting(S), signal(Sig), cause(C), solution(Sol),
                         compatible_setting(S, C), compatible_solution(C, Sol).

outcome(solved) :- chosen_setting(S), chosen_signal(Sig), chosen_cause(C), chosen_solution(Sol),
                   valid(S, Sig, C, Sol).
outcome(invalid) :- chosen_setting(S), chosen_signal(Sig), chosen_cause(C), chosen_solution(Sol),
                    not valid(S, Sig, C, Sol).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for cause_id in sorted(setting.allows):
            lines.append(asp.fact("allows", setting_id, cause_id))
    for signal_id in SIGNALS:
        lines.append(asp.fact("signal", signal_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for setting_id in sorted(cause.allows):
            lines.append(asp.fact("cause_allows", cause_id, setting_id))
    for solution_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", solution_id))
        for cause_id in sorted(solution.fixes):
            lines.append(asp.fact("fixes", solution_id, cause_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_signal", params.signal),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_solution", params.solution),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "solved" if valid_combo(params.setting, params.cause, params.solution) else "invalid"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

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
        smoke_story(sample)
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: woodland animals solve a gentle magical mystery before home-time."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_two_animals(rng: random.Random) -> tuple[tuple[str, str, str], tuple[str, str, str]]:
    first = rng.choice(ANIMALS)
    second = rng.choice([a for a in ANIMALS if a[0] != first[0]])
    return first, second


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cause and args.solution:
        if not valid_combo(args.setting, args.cause, args.solution):
            raise StoryError(explain_rejection(args.setting, args.cause, args.solution))
    if args.setting and args.cause and args.solution is None:
        good = [sid for sid, sol in SOLUTIONS.items() if args.cause in sol.fixes]
        if args.cause not in SETTINGS[args.setting].allows:
            raise StoryError(explain_rejection(args.setting, args.cause, good[0] if good else ""))
    if args.cause and args.solution and args.setting is None:
        example_setting = next(iter(CAUSES[args.cause].allows))
        if args.cause not in SOLUTIONS[args.solution].fixes:
            raise StoryError(explain_rejection(example_setting, args.cause, args.solution))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.signal is None or combo[1] == args.signal)
        and (args.cause is None or combo[2] == args.cause)
        and (args.solution is None or combo[3] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, signal_id, cause_id, solution_id = rng.choice(sorted(combos))
    hero, helper = pick_two_animals(rng)
    elder_name, elder_type, elder_species = rng.choice(ELDERS)
    return StoryParams(
        setting=setting_id,
        signal=signal_id,
        cause=cause_id,
        solution=solution_id,
        hero_name=hero[0],
        hero_type=hero[1],
        hero_species=hero[2],
        helper_name=helper[0],
        helper_type=helper[1],
        helper_species=helper[2],
        elder_name=elder_name,
        elder_type=elder_type,
        elder_species=elder_species,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.signal not in SIGNALS:
        raise StoryError(f"(Unknown signal: {params.signal})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")
    if not valid_combo(params.setting, params.cause, params.solution):
        raise StoryError(explain_rejection(params.setting, params.cause, params.solution))

    world = tell(
        setting=SETTINGS[params.setting],
        signal_cfg=SIGNALS[params.signal],
        cause=CAUSES[params.cause],
        solution=SOLUTIONS[params.solution],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        hero_species=params.hero_species,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        helper_species=params.helper_species,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
        elder_species=params.elder_species,
    )
    sample = StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("helper", params.helper_name).replace("elder", params.elder_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    smoke_story(sample)
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    text = sample.story
    for key, label in [("hero", sample.params.hero_name), ("helper", sample.params.helper_name), ("elder", sample.params.elder_name)]:
        text = text.replace(key, label)
    if header:
        print(header)
    print(text)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, signal, cause, solution) combos:\n")
        for setting_id, signal_id, cause_id, solution_id in combos:
            print(f"  {setting_id:10} {signal_id:11} {cause_id:15} {solution_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name} & {p.helper_name}: {p.signal} / {p.cause} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
