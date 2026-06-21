#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/calf_surprise_bedtime_story.py
========================================================

A small bedtime storyworld about a sleepy child, a moonlit surprise, and a calf
that has wandered away from its barn.

The world model is intentionally narrow. A child is getting ready for bed at a
farm home when a soft moo sounds from the dark. The surprise is not a monster or
a storm, but a real calf standing somewhere it should not be. The grown-up and
child go out with a gentle plan, calm the calf in a way that fits its need, and
lead it back to its warm place for the night.

The reasonableness gate is simple and explicit:

* a calf has a nighttime need: hungry, lonely, or startled
* only some comforting methods fit that need
* one method is usually the best match, while another may still work more slowly
* obviously poor ideas, like offering a cookie, are refused

The prose is driven by simulated state: unease, wonder, trust, calm, distance
from the barn, and whether the calf follows.

Run it
------
    python storyworlds/worlds/gpt-5.4/calf_surprise_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/calf_surprise_bedtime_story.py --need hungry --method warm_bottle
    python storyworlds/worlds/gpt-5.4/calf_surprise_bedtime_story.py --method cookie
    python storyworlds/worlds/gpt-5.4/calf_surprise_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/calf_surprise_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/calf_surprise_bedtime_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from the repo root. This file lives under storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    home: str
    surprise_place: str
    sky: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    sound: str
    cause: str
    child_guess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    action: str
    soothe: set[str] = field(default_factory=set)
    preferred_for: set[str] = field(default_factory=set)
    sense: int = 1
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


def _r_distress(world: World) -> list[str]:
    calf = world.get("calf")
    child = world.get("child")
    out: list[str] = []
    for need_key in ("hungry", "lonely", "startled"):
        if calf.meters[need_key] < THRESHOLD:
            continue
        sig = ("distress", need_key)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        calf.memes["uneasy"] += 1
        child.memes["worry"] += 1
        out.append("__uneasy__")
    return out


def _r_soothe(world: World) -> list[str]:
    calf = world.get("calf")
    method = world.facts.get("method_cfg")
    if method is None or not world.facts.get("method_used"):
        return []
    for need_key in ("hungry", "lonely", "startled"):
        if calf.meters[need_key] < THRESHOLD:
            continue
        if need_key not in method.soothe:
            continue
        sig = ("soothe", need_key, method.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        calf.memes["trust"] += 1
        calf.memes["calm"] += 1
        calf.meters["following"] += 1
        return ["__soothed__"]
    return []


def _r_return(world: World) -> list[str]:
    calf = world.get("calf")
    barn = world.get("barn")
    if calf.meters["following"] < THRESHOLD or calf.meters["distance_from_barn"] <= 0:
        return []
    sig = ("return", calf.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    calf.meters["distance_from_barn"] = 0.0
    barn.meters["occupied"] += 1
    calf.meters["safe"] += 1
    return ["__returned__"]


CAUSAL_RULES = [
    Rule(name="distress", tag="emotional", apply=_r_distress),
    Rule(name="soothe", tag="emotional", apply=_r_soothe),
    Rule(name="return", tag="physical", apply=_r_return),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            notes = rule.apply(world)
            if notes:
                changed = True
                produced.extend(notes)
    return produced


SETTINGS = {
    "window": Setting(
        id="window",
        home="the farm cottage",
        surprise_place="under the bedroom window",
        sky="The moon made a pale square on the quilt.",
        path="the short path past the pump to the barn",
        tags={"farm", "bedtime"},
    ),
    "garden": Setting(
        id="garden",
        home="the small farmhouse",
        surprise_place="beside the moonlit garden gate",
        sky="Silver light lay over the blanket and the floorboards.",
        path="the path by the herb patch to the barn",
        tags={"farm", "garden", "bedtime"},
    ),
    "orchard": Setting(
        id="orchard",
        home="the warm farmhouse",
        surprise_place="near the first apple tree on the orchard path",
        sky="Moonlight rested softly on the curtains.",
        path="the orchard path back to the barn",
        tags={"farm", "orchard", "bedtime"},
    ),
}

NEEDS = {
    "hungry": Need(
        id="hungry",
        label="hungry",
        sound="a thin, hopeful moo",
        cause="its supper had come late, and its little belly felt empty",
        child_guess="Maybe the calf is looking for milk.",
        tags={"calf", "barn"},
    ),
    "lonely": Need(
        id="lonely",
        label="lonely",
        sound="a soft, searching moo",
        cause="it had woken and could not see its mother in the dark",
        child_guess="Maybe the calf does not want to be alone.",
        tags={"calf", "barn", "lullaby"},
    ),
    "startled": Need(
        id="startled",
        label="startled",
        sound="a shaky little moo",
        cause="a flapping sheet on the line had frightened it",
        child_guess="Maybe the calf got scared.",
        tags={"calf", "lantern"},
    ),
}

METHODS = {
    "warm_bottle": Method(
        id="warm_bottle",
        label="warm bottle",
        phrase="a warm bottle of milk",
        action="warmed a small bottle of milk and held it where the calf could smell it",
        soothe={"hungry", "lonely"},
        preferred_for={"hungry"},
        sense=2,
        tags={"bottle", "calf"},
    ),
    "hay_bundle": Method(
        id="hay_bundle",
        label="hay bundle",
        phrase="a sweet hay bundle",
        action="carried out a sweet-smelling bundle of hay and rustled it gently",
        soothe={"hungry"},
        preferred_for=set(),
        sense=2,
        tags={"hay", "calf"},
    ),
    "lullaby": Method(
        id="lullaby",
        label="lullaby",
        phrase="a low bedtime song",
        action="sang in a low, slow voice the way one sings at bedtime",
        soothe={"lonely", "startled"},
        preferred_for={"lonely"},
        sense=2,
        tags={"lullaby", "bedtime"},
    ),
    "lantern_walk": Method(
        id="lantern_walk",
        label="lantern walk",
        phrase="a shaded lantern and quiet steps",
        action="lit the shaded lantern low and walked so slowly that the shadows stopped jumping",
        soothe={"startled"},
        preferred_for={"startled"},
        sense=2,
        tags={"lantern", "bedtime"},
    ),
    "cookie": Method(
        id="cookie",
        label="cookie",
        phrase="a honey cookie",
        action="brought out a honey cookie from the kitchen tin",
        soothe=set(),
        preferred_for=set(),
        sense=0,
        tags={"cookie"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Theo"]


def method_fits(need: Need, method: Method) -> bool:
    return method.sense >= SENSE_MIN and need.id in method.soothe


def best_method(need: Need, method: Method) -> bool:
    return need.id in method.preferred_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for need_id, need in NEEDS.items():
            for method_id, method in METHODS.items():
                if method_fits(need, method):
                    combos.append((setting_id, need_id, method_id))
    return combos


def explain_method_rejection(method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(No story: {method.phrase} is not a sensible way to guide a calf at night. "
            f"A calf needs a gentle, calf-safe comfort like a lullaby, hay, milk, or a calm lantern walk.)"
        )
    return "(No story: that method does not suit the calf's need.)"


def explain_combo_rejection(need: Need, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return explain_method_rejection(method)
    return (
        f"(No story: a {need.label} calf would not settle for {method.phrase}. "
        f"Choose a method that truly matches why the calf wandered.)"
    )


def outcome_of(params: "StoryParams") -> str:
    need = NEEDS[params.need]
    method = METHODS[params.method]
    if not method_fits(need, method):
        return "invalid"
    return "quick" if best_method(need, method) else "patient"


def predict_follow(world: World, need: Need, method: Method) -> dict:
    sim = world.copy()
    sim.facts["method_cfg"] = method
    sim.facts["method_used"] = True
    calf = sim.get("calf")
    calf.meters[need.id] += 1
    propagate(sim, narrate=False)
    return {
        "follow": calf.meters["following"] >= THRESHOLD,
        "returned": calf.meters["safe"] >= THRESHOLD or calf.meters["distance_from_barn"] == 0,
    }


def bedtime_setup(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    child.memes["sleepy"] += 1
    adult.memes["calm"] += 1
    world.say(
        f"In {setting.home}, {child.id} had been washed, tucked in, and kissed good night by "
        f"{child.pronoun('possessive')} {adult.label_word}."
    )
    world.say(setting.sky)
    world.say(
        f"{child.id} was almost asleep, listening to the house settle and the hens go quiet."
    )


def surprise_sound(world: World, child: Entity, need: Need) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Then, from outside, came {need.sound}. {child.id}'s eyes opened wide."
    )
    world.say(
        f'"Did you hear that?" {child.pronoun()} whispered. "{need.child_guess}"'
    )


def discover_calf(world: World, child: Entity, adult: Entity, setting: Setting, need: Need) -> None:
    calf = world.get("calf")
    calf.meters[need.id] += 1
    propagate(world, narrate=False)
    world.say(
        f"{adult.label_word.capitalize()} lifted the curtain, and there was the surprise: "
        f"a little calf stood {setting.surprise_place}, looking much too small for the dark."
    )
    world.say(
        f"It had wandered away because {need.cause}. The night suddenly felt bigger, "
        f"and {child.id} slipped a hand into {adult.pronoun('possessive')} hand."
    )


def choose_plan(world: World, child: Entity, adult: Entity, need: Need, method: Method) -> None:
    pred = predict_follow(world, need, method)
    world.facts["predicted_follow"] = pred["follow"]
    world.say(
        f'"Let us help it gently," said {adult.label_word}. "{method.phrase.capitalize()} should do better than any rush or shout."'
    )


def use_method(world: World, child: Entity, adult: Entity, method: Method, outcome: str) -> None:
    world.facts["method_cfg"] = method
    world.facts["method_used"] = True
    child.memes["brave"] += 1
    adult.memes["calm"] += 1
    world.say(
        f"So they put on slippers and stepped outside. {adult.label_word.capitalize()} {method.action}."
    )
    if outcome == "patient":
        child.memes["patience"] += 1
        world.say(
            f"At first the calf only blinked and shifted its small hooves. {child.id} waited without tugging or calling too loudly."
        )
    else:
        world.say(
            f"The calf turned its soft nose toward them at once."
        )
    propagate(world, narrate=False)


def return_to_barn(world: World, child: Entity, adult: Entity, setting: Setting, outcome: str) -> None:
    calf = world.get("calf")
    if calf.meters["safe"] < THRESHOLD:
        raise StoryError("(Story failure: the calf did not make it safely back to the barn.)")
    child.memes["relief"] += 1
    calf.memes["calm"] += 1
    if outcome == "patient":
        world.say(
            f"After another quiet moment, the calf took one step, then another, and followed them along {setting.path}."
        )
    else:
        world.say(
            f"The calf tucked itself close and followed them along {setting.path}."
        )
    world.say(
        f"In the barn, the warm straw smell wrapped around them. The calf gave a tiny nuzzle to {child.id}'s sleeve, as if saying thank you for the midnight kindness."
    )


def ending(world: World, child: Entity, adult: Entity, method: Method) -> None:
    child.memes["sleepy"] += 1
    child.memes["safe"] += 1
    world.say(
        f"Back in bed, {child.id} felt the house grow still again. {child.pronoun('possessive').capitalize()} surprise was no longer a worrying sound in the dark, but a story of how a little calf had found its way home."
    )
    if method.id == "lullaby":
        world.say(
            "Soon the last thing in the room was the memory of that soft song and the silver moon on the quilt."
        )
    elif method.id == "lantern_walk":
        world.say(
            "Soon the last thing in the room was the memory of one tiny lantern glow moving safely toward the barn."
        )
    elif method.id == "warm_bottle":
        world.say(
            "Soon the last thing in the room was the thought of the calf warm and full, sleeping in its straw bed."
        )
    else:
        world.say(
            "Soon the last thing in the room was the sweet hay smell that seemed to follow them back inside."
        )


def tell(
    setting: Setting,
    need: Need,
    method: Method,
    *,
    child_name: str = "Lily",
    child_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, phrase=child_name, role="child"))
    adult = world.add(Entity(id="adult", kind="character", type=parent_type, label="the parent", phrase="the parent", role="adult"))
    calf = world.add(Entity(id="calf", kind="thing", type="calf", label="calf", phrase="a little calf", role="calf"))
    barn = world.add(Entity(id="barn", kind="thing", type="barn", label="barn", phrase="the barn", role="place"))
    child.attrs["name"] = child_name
    adult.attrs["name"] = adult.label_word.capitalize()
    calf.meters["distance_from_barn"] = 1.0

    bedtime_setup(world, child, adult, setting)
    world.para()
    surprise_sound(world, child, need)
    discover_calf(world, child, adult, setting, need)
    world.para()
    choose_plan(world, child, adult, need, method)
    outcome = "quick" if best_method(need, method) else "patient"
    use_method(world, child, adult, method, outcome)
    return_to_barn(world, child, adult, setting, outcome)
    world.para()
    ending(world, child, adult, method)

    world.facts.update(
        child=child,
        adult=adult,
        calf=calf,
        barn=barn,
        setting=setting,
        need_cfg=need,
        method_cfg=method,
        child_name=child_name,
        outcome=outcome,
        returned=calf.meters["safe"] >= THRESHOLD,
        surprise_place=setting.surprise_place,
    )
    return world


KNOWLEDGE = {
    "calf": [
        (
            "What is a calf?",
            "A calf is a baby cow. Calves are smaller than grown cows and need gentle care."
        )
    ],
    "barn": [
        (
            "What is a barn for?",
            "A barn is a farm building where animals and hay can stay warm and dry. It gives them a safe place to rest."
        )
    ],
    "lullaby": [
        (
            "What is a lullaby?",
            "A lullaby is a soft, slow song sung to help someone feel calm and sleepy. Quiet singing can make a frightened animal feel safer too."
        )
    ],
    "lantern": [
        (
            "What does a lantern do at night?",
            "A lantern gives a gentle light so people can see in the dark. A calm light is better than rushing and startling an animal."
        )
    ],
    "hay": [
        (
            "What is hay?",
            "Hay is dried grass that farm animals can eat. It smells sweet and is often kept in a barn."
        )
    ],
    "bottle": [
        (
            "Why would a young calf want milk?",
            "A young calf drinks milk, so a warm bottle can comfort a hungry one. The smell tells the calf that help is near."
        )
    ],
    "bedtime": [
        (
            "Why do bedtime stories feel calm?",
            "Bedtime stories use quiet sounds, safe endings, and gentle pictures. They help a child feel peaceful before sleep."
        )
    ],
}
KNOWLEDGE_ORDER = ["calf", "barn", "lullaby", "lantern", "hay", "bottle", "bedtime"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    need = world.facts["need_cfg"]
    method = world.facts["method_cfg"]
    setting = world.facts["setting"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the word "calf" and contains a gentle surprise.',
        f"Tell a sleepy farm story where a child named {child.attrs['name']} hears {need.sound} at night and discovers a calf {setting.surprise_place}.",
        f"Write a calm story where a grown-up and child use {method.phrase} to help a wandering calf feel safe before the child goes back to bed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    need = world.facts["need_cfg"]
    method = world.facts["method_cfg"]
    setting = world.facts["setting"]
    outcome = world.facts["outcome"]
    adult_word = adult.label_word
    answers: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.attrs['name']}, {child.pronoun('possessive')} {adult_word}, and a little calf outside at bedtime. The surprise begins when the quiet night is broken by a moo."
        ),
        (
            "What was the surprise in the story?",
            f"The surprise was that a calf was standing {setting.surprise_place} in the dark. {child.attrs['name']} expected bedtime quiet, not a farm animal so close to the house."
        ),
        (
            "Why had the calf wandered away?",
            f"The calf had wandered because it was {need.label}. In this story, {need.cause}."
        ),
        (
            f"How did {child.attrs['name']} and {adult_word} help the calf?",
            f"They used {method.phrase} and stayed very gentle. That worked because it matched what the calf needed that night."
        ),
    ]
    if outcome == "patient":
        answers.append(
            (
                "Did the calf come right away?",
                f"Not right away. At first it hesitated, but the child and grown-up stayed patient and quiet, and that gave the calf time to trust them."
            )
        )
    else:
        answers.append(
            (
                "Did the calf follow them quickly?",
                f"Yes. The calf turned toward them at once and followed them back to the barn. The plan fit the calf's need very well."
            )
        )
    answers.append(
        (
            "How did the story end?",
            f"It ended with the calf safe in the barn and {child.attrs['name']} back in bed. The ending feels calm because the worrying surprise became a gentle memory."
        )
    )
    return answers


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["need_cfg"].tags) | set(world.facts["method_cfg"].tags) | set(world.facts["setting"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    setting: str
    need: str
    method: str
    child_name: str
    child_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="window",
        need="lonely",
        method="lullaby",
        child_name="Lily",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        setting="garden",
        need="hungry",
        method="warm_bottle",
        child_name="Ben",
        child_gender="boy",
        parent="father",
    ),
    StoryParams(
        setting="orchard",
        need="startled",
        method="lantern_walk",
        child_name="Maya",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        setting="garden",
        need="hungry",
        method="hay_bundle",
        child_name="Leo",
        child_gender="boy",
        parent="father",
    ),
    StoryParams(
        setting="window",
        need="startled",
        method="lullaby",
        child_name="Anna",
        child_gender="girl",
        parent="mother",
    ),
]


ASP_RULES = r"""
fit(N, M) :- soothes(M, N), sense(M, S), sense_min(Min), S >= Min.
best(N, M) :- preferred(M, N).

valid(S, N, M) :- setting(S), need(N), method(M), fit(N, M).

outcome(quick) :- chosen_need(N), chosen_method(M), fit(N, M), best(N, M).
outcome(patient) :- chosen_need(N), chosen_method(M), fit(N, M), not best(N, M).
invalid_choice :- chosen_need(N), chosen_method(M), not fit(N, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for need_id in sorted(method.soothe):
            lines.append(asp.fact("soothes", method_id, need_id))
        for need_id in sorted(method.preferred_for):
            lines.append(asp.fact("preferred", method_id, need_id))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_need", params.need),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1.\n#show invalid_choice/0."))
    invalid = asp.atoms(model, "invalid_choice")
    if invalid:
        return "invalid"
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld: a moonlit surprise and a wandering calf."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and question sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method is not None:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            raise StoryError(explain_method_rejection(method))
    if args.need is not None and args.method is not None:
        need = NEEDS[args.need]
        method = METHODS[args.method]
        if not method_fits(need, method):
            raise StoryError(explain_combo_rejection(need, method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.need is None or combo[1] == args.need)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, need_id, method_id = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        need=need_id,
        method=method_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    need = NEEDS[params.need]
    method = METHODS[params.method]
    if not method_fits(need, method):
        raise StoryError(explain_combo_rejection(need, method))

    world = tell(
        SETTINGS[params.setting],
        need,
        method,
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
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches.append((params, asp_outcome(params), outcome_of(params)))
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcome model:")
        for params, a_out, p_out in mismatches[:5]:
            print(" ", params, a_out, p_out)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        printed = buf.getvalue()
        if "calf" not in sample.story.lower():
            raise StoryError('(Smoke test failed: story omitted required word "calf".)')
        if "### smoke" not in printed:
            raise StoryError("(Smoke test failed: emit() output missing header.)")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1.\n#show invalid_choice/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, need, method) combos:\n")
        for setting_id, need_id, method_id in combos:
            print(f"  {setting_id:8} {need_id:9} {method_id}")
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
            header = f"### {p.child_name}: {p.need} calf at {p.setting} ({p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
