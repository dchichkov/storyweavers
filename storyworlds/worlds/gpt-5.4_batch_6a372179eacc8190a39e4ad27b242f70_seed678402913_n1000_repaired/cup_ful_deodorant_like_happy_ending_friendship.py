#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cup_ful_deodorant_like_happy_ending_friendship.py
============================================================================

A small story world about two friends getting a cozy play space ready for an
afternoon together. One child has the wrong idea that a cup-ful of water mixed
with deodorant will make everything smell nice. In a small space, that choice
can make the air sharp and dampen nearby things. A wiser friend can stop it, or
a calm grown-up can help them fix it and teach the better lesson:
deodorant is for bodies, not for rooms, forts, or toys.

The world models:
- typed entities with physical meters and emotional memes
- a tiny forward-chaining rule engine
- a Python reasonableness gate plus an inline ASP twin
- state-driven prose, QA, trace, and JSON output

Run examples
------------
python storyworlds/worlds/gpt-5.4/cup_ful_deodorant_like_happy_ending_friendship.py
python storyworlds/worlds/gpt-5.4/cup_ful_deodorant_like_happy_ending_friendship.py --all
python storyworlds/worlds/gpt-5.4/cup_ful_deodorant_like_happy_ending_friendship.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/cup_ful_deodorant_like_happy_ending_friendship.py --show-asp
python storyworlds/worlds/gpt-5.4/cup_ful_deodorant_like_happy_ending_friendship.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLDNESS_INIT = 5.0
CAREFUL_TRAITS = {"careful", "gentle", "thoughtful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    enclosed: bool = False
    absorbency: int = 0
    washable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    scene: str
    prep_line: str
    enclosed: bool
    comfort_item: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    place_line: str
    wet_effect: str
    absorbency: int
    washable: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class DeodorantPlan:
    id: str
    label: str
    body_line: str
    splash_line: str
    lesson_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    target: str
    plan: str
    response: str
    instigator: str
    instigator_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    friend_age: int = 6
    relation: str = "friends"
    trust: int = 6
    pet: str = ""
    seed: Optional[int] = None


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "friend"}]

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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sharp_air(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("space")
    target = world.get("target")
    if room.meters["deodorant_mix"] < THRESHOLD:
        return out
    sig = ("sharp_air",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["sharp_air"] += 1 + room.meters["enclosed_bonus"]
    for kid in world.kids():
        kid.memes["discomfort"] += 1
    if target.absorbency:
        target.meters["damp"] += 1
    out.append("__sharp_air__")
    return out


def _r_damp_damage(world: World) -> list[str]:
    out: list[str] = []
    target = world.get("target")
    if target.meters["damp"] < THRESHOLD:
        return out
    sig = ("damp_damage", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["messy"] += 1
    out.append("__damp__")
    return out


CAUSAL_RULES = [
    Rule(name="sharp_air", tag="physical", apply=_r_sharp_air),
    Rule(name="damp_damage", tag="physical", apply=_r_damp_damage),
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


SETTINGS = {
    "fort": Setting(
        id="fort",
        scene="a blanket fort by the sofa",
        prep_line="They tucked blankets over two chairs and made a little doorway with a clothespin.",
        enclosed=True,
        comfort_item="paper star garland",
        tags={"fort", "air"},
    ),
    "reading_nook": Setting(
        id="reading_nook",
        scene="a reading nook by the window",
        prep_line="They stacked pillows in the corner and lined up their favorite books in a neat row.",
        enclosed=False,
        comfort_item="bookmark box",
        tags={"books", "air"},
    ),
    "play_tent": Setting(
        id="play_tent",
        scene="a play tent in the living room",
        prep_line="They spread a soft blanket inside and set a tiny lamp beside the flap.",
        enclosed=True,
        comfort_item="friendship picture",
        tags={"tent", "air"},
    ),
}

TARGETS = {
    "paper_chain": Target(
        id="paper_chain",
        label="paper chain",
        phrase="a paper chain they had made together",
        place_line="A bright paper chain hung right by the opening.",
        wet_effect="The paper links curled at the edges when the drops touched them.",
        absorbency=2,
        washable=False,
        tags={"paper", "craft"},
    ),
    "stuffed_bunny": Target(
        id="stuffed_bunny",
        label="stuffed bunny",
        phrase="a soft stuffed bunny from the reading shelf",
        place_line="A stuffed bunny sat in the place of honor, ready to listen to stories.",
        wet_effect="The bunny's fur turned a little sticky and carried the strong smell.",
        absorbency=1,
        washable=True,
        tags={"toy", "wash"},
    ),
    "cushion": Target(
        id="cushion",
        label="cushion",
        phrase="a puffy floor cushion",
        place_line="One round cushion made the coziest seat inside.",
        wet_effect="The cushion darkened in spots and smelled far too strong.",
        absorbency=1,
        washable=True,
        tags={"fabric", "wash"},
    ),
    "library_book": Target(
        id="library_book",
        label="library book",
        phrase="a library book with shiny animal pictures",
        place_line="A library book lay open to the page with the fox in boots.",
        wet_effect="The pages puckered, and the room smelled too sharp to keep reading.",
        absorbency=2,
        washable=False,
        tags={"book", "paper"},
    ),
}

PLANS = {
    "mix_and_splash": DeodorantPlan(
        id="mix_and_splash",
        label="a cup-ful of water with deodorant mixed in",
        body_line='“If we mix a cup-ful of water with deodorant, it will smell like flowers,”',
        splash_line="The fine drops landed everywhere at once.",
        lesson_line="deodorant is for bodies, not for forts or books",
        tags={"deodorant", "water"},
    ),
}

RESPONSES = {
    "air_out_and_wipe": Response(
        id="air_out_and_wipe",
        sense=3,
        power=3,
        text="opened the window wide, carried the damp thing into the fresh air, and wiped the little drops away with a clean cloth",
        fail="opened the window and wiped fast, but the smell had already sunk in too deeply",
        qa_text="opened the window, moved the damp item into fresh air, and wiped the drops away",
        tags={"window", "clean"},
    ),
    "wash_and_wait": Response(
        id="wash_and_wait",
        sense=3,
        power=2,
        text="took the washable thing to the sink, rinsed it carefully, and let the room breathe until the sharp smell faded",
        fail="rinsed and waited, but the sharp smell in the room was still too strong",
        qa_text="rinsed the washable thing and let the room breathe",
        tags={"wash", "window"},
    ),
    "cover_with_blanket": Response(
        id="cover_with_blanket",
        sense=1,
        power=1,
        text="threw a blanket over the smell and hoped it would go away",
        fail="covered everything with a blanket, but that only trapped the strong smell inside",
        qa_text="covered it with a blanket",
        tags={"wrong_fix"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "gentle", "thoughtful", "sensible", "curious", "cheerful"]
PETS = ["the cat", "the puppy", "the little dog", "the kitten", ""]


def hazard_at_risk(setting: Setting, target: Target, plan: DeodorantPlan) -> bool:
    return bool(plan.id == "mix_and_splash" and target.absorbency > 0 and setting.enclosed)


def sensible_responses(target: Target) -> list[Response]:
    out: list[Response] = []
    for response in RESPONSES.values():
        if response.sense < SENSE_MIN:
            continue
        if response.id == "wash_and_wait" and not target.washable:
            continue
        out.append(response)
    return out


def best_response(target: Target) -> Response:
    allowed = sensible_responses(target)
    if not allowed:
        raise StoryError("(No sensible response exists for this target.)")
    return max(allowed, key=lambda r: (r.sense, r.power))


def severity_of(setting: Setting, target: Target, delay: int) -> int:
    return target.absorbency + (1 if setting.enclosed else 0) + delay


def contained_by(setting: Setting, target: Target, response: Response, delay: int) -> bool:
    return response.power >= severity_of(setting, target, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, friend_age: int, trait: str) -> bool:
    older_friend = relation == "friends" and friend_age > instigator_age
    authority = initial_care(trait) + 1.0 + (2.0 if older_friend else 0.0)
    return older_friend and authority > BOLDNESS_INIT


def predict_misuse(world: World) -> dict:
    sim = world.copy()
    do_misuse(sim, narrate=False)
    return {
        "sharp_air": sim.get("space").meters["sharp_air"],
        "target_damp": sim.get("target").meters["damp"],
    }


def do_misuse(world: World, narrate: bool = True) -> None:
    room = world.get("space")
    room.meters["deodorant_mix"] += 1
    world.get("target").meters["sprayed"] += 1
    propagate(world, narrate=narrate)


def setup_scene(world: World, a: Entity, b: Entity, setting: Setting, target: Target) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After school, {a.id} and {b.id} met for a quiet afternoon together. "
        f"They were making {setting.scene} so they could read and whisper like it was their own tiny world."
    )
    world.say(setting.prep_line)
    world.say(target.place_line)


def admire_space(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f"{b.id} smiled and said the little place looked warm and bright. "
        f"{a.id} wanted it to feel extra special before they climbed inside."
    )
    if setting.comfort_item:
        world.say(
            f"They even moved {setting.comfort_item} into just the right spot."
        )


def tempt(world: World, a: Entity, plan: DeodorantPlan) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'{a.id} spotted a can of deodorant on the hall table and pointed to a small cup. '
        f'{plan.body_line} {a.id} said.'
    )
    world.say(
        f"For one second, the idea sounded clever, almost like a grown-up trick."
    )


def warn(world: World, b: Entity, a: Entity, parent: Entity, target: Target) -> None:
    pred = predict_misuse(world)
    b.memes["care"] += 1
    world.facts["predicted_sharp_air"] = pred["sharp_air"]
    world.facts["predicted_target_damp"] = pred["target_damp"]
    extra = ""
    if pred["target_damp"] >= THRESHOLD:
        extra = f" And {target.label} could get damp too."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, that is not a good idea. '
        f'Deodorant is strong, and this little place is too small for spraying it in."'
        f"{extra}"
    )
    world.say(
        f'{b.id} added, "If we need help, we can ask {parent.label_word} instead of guessing."'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity, setting: Setting) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked around the small space again, then nodded. "You are right," {a.pronoun()} said.'
    )
    world.say(
        f"They left the deodorant alone and asked {parent.label_word} how to make {setting.scene} feel fresh without strong spray."
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    if b.memes["trust"] >= 6:
        world.say(
            f'{a.id} grinned. "It will be fine," {a.pronoun()} said, and before {b.id} could stop {a.pronoun("object")}, '
            f'{a.pronoun()} tipped the cup and shook the deodorant over it.'
        )
    else:
        world.say(
            f'{a.id} still thought the idea sounded smart. Before {b.id} could move the cup away, '
            f'{a.pronoun()} tipped in the water and sprayed the deodorant over it.'
        )


def mishap(world: World, a: Entity, b: Entity, target: Target, plan: DeodorantPlan) -> None:
    do_misuse(world, narrate=False)
    world.say(
        f"The room filled with a misty smell all at once. {plan.splash_line}"
    )
    if world.get("space").meters["sharp_air"] >= THRESHOLD:
        world.say(
            f"{b.id} blinked and backed out first. The air was too sharp to breathe in happily."
        )
    if world.get("target").meters["damp"] >= THRESHOLD:
        world.say(target.wet_effect)


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(
        f'"{parent.label_word.capitalize()}!" {b.id} called. "Something smells too strong in here!"'
    )


def rescue(world: World, parent: Entity, response: Response, target: Target) -> None:
    room = world.get("space")
    tgt = world.get("target")
    room.meters["sharp_air"] = 0.0
    tgt.meters["damp"] = 0.0
    tgt.meters["messy"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {response.text}."
    )
    world.say(
        f"Soon the little space felt calm again instead of prickly and confusing."
    )
    if target.washable:
        world.say(
            f'"That worked because we cleaned the wet part and gave the smell somewhere to go," {parent.pronoun()} explained.'
        )


def rescue_fail(world: World, parent: Entity, response: Response) -> None:
    world.get("space").meters["sharp_air"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.fail}."
    )
    world.say(
        "The room was no good for stories that afternoon, and everyone had to leave it empty until much later."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, plan: DeodorantPlan) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["discomfort"] = 0.0
    world.say(
        f'Then {parent.label_word} crouched beside them. "{plan.lesson_line.capitalize()}," '
        f'{parent.pronoun()} said softly. "If something needs cleaning, fresh air and the right kind of washing help more than strong spray."'
    )
    world.say(
        f'{a.id} looked at {b.id}. "Next time I will ask first," {a.pronoun()} said.'
    )
    world.say(
        f'"And next time I will help you think before we try something," {b.id} said.'
    )


def safe_ending(world: World, a: Entity, b: Entity, parent: Entity, setting: Setting, target: Target) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    pet = world.facts.get("pet", "")
    world.say(
        f"{parent.label_word.capitalize()} opened the window a little more and brought them orange slices for a snack."
    )
    world.say(
        f"After that, {a.id} and {b.id} fixed up {setting.scene} the simple way and climbed in together."
    )
    if target.id in {"paper_chain", "library_book"}:
        world.say(
            f"They chose new gentle decorations and made the place feel bright without spraying anything at all."
        )
    else:
        world.say(
            f"The clean, dry {target.label} went back to its place, and the whole corner felt cozy again."
        )
    if pet:
        world.say(f"Even {pet} settled nearby, as if the room liked the fresh air better too.")
    world.say(
        f"They read until the sky turned peach, and the little space felt just how friendship should feel: easy, careful, and kind."
    )


def tell(
    setting: Setting,
    target_cfg: Target,
    plan: DeodorantPlan,
    response: Response,
    instigator: str = "Lily",
    instigator_gender: str = "girl",
    friend: str = "Mia",
    friend_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    friend_age: int = 7,
    relation: str = "friends",
    trust: int = 6,
    pet: str = "",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=friend,
        kind="character",
        type=friend_gender,
        role="friend",
        age=friend_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    space = world.add(Entity(
        id="space",
        type="space",
        label=setting.scene,
        enclosed=setting.enclosed,
        tags=set(setting.tags),
    ))
    target = world.add(Entity(
        id="target",
        type="target",
        label=target_cfg.label,
        phrase=target_cfg.phrase,
        absorbency=target_cfg.absorbency,
        washable=target_cfg.washable,
        tags=set(target_cfg.tags),
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=plan.label,
        tags=set(plan.tags),
    ))

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["trust"] = float(trust)
    b.memes["care"] = initial_care(trait)
    space.meters["enclosed_bonus"] = 1.0 if setting.enclosed else 0.0

    world.facts["pet"] = pet

    setup_scene(world, a, b, setting, target_cfg)
    admire_space(world, a, b, setting)

    world.para()
    tempt(world, a, plan)
    warn(world, b, a, parent, target_cfg)

    averted = would_avert(relation, instigator_age, friend_age, trait)

    if averted:
        back_down(world, a, b, parent, setting)
        world.para()
        lesson(world, parent, a, b, plan)
        safe_ending(world, a, b, parent, setting, target_cfg)
        outcome = "averted"
        severity = 0
    else:
        defy(world, a, b)
        world.para()
        mishap(world, a, b, target_cfg, plan)
        alarm(world, b, parent)
        severity = severity_of(setting, target_cfg, delay)
        contained = contained_by(setting, target_cfg, response, delay)
        world.para()
        if contained:
            rescue(world, parent, response, target_cfg)
            lesson(world, parent, a, b, plan)
            world.para()
            safe_ending(world, a, b, parent, setting, target_cfg)
            outcome = "contained"
        else:
            rescue_fail(world, parent, response)
            lesson(world, parent, a, b, plan)
            world.para()
            world.say(
                "They could not use the little space that day, but they sat by the open window together with a stack of books and promised to choose gentler ideas next time."
            )
            outcome = "ruined"

    world.facts.update(
        setting=setting,
        target_cfg=target_cfg,
        plan=plan,
        response=response,
        instigator=a,
        friend=b,
        parent=parent,
        target=target,
        tool=tool,
        relation=relation,
        outcome=outcome,
        severity=severity,
        delay=delay,
        averted=(outcome == "averted"),
        contained=(outcome == "contained"),
        misused=(outcome != "averted"),
        washable=target_cfg.washable,
    )
    return world


KNOWLEDGE = {
    "deodorant": [(
        "What is deodorant?",
        "Deodorant is something people put on their bodies to help with sweaty smells. It is not for spraying on books, toys, or little rooms."
    )],
    "water": [(
        "What is a cup-ful?",
        "A cup-ful is as much as one cup can hold. It is a simple way to talk about one full cup of something."
    )],
    "air": [(
        "Why does fresh air help a strong smell go away?",
        "Fresh air moves the smelly air out and brings clean air in. That makes the room easier and safer to breathe in."
    )],
    "paper": [(
        "Why can paper get ruined by water drops?",
        "Paper soaks up water quickly. When it gets wet, it can curl, wrinkle, or tear."
    )],
    "book": [(
        "Why should library books be kept dry?",
        "Library books belong to many readers. Keeping them dry helps the pages stay smooth and clean for the next child."
    )],
    "toy": [(
        "Why should you ask before cleaning a toy with something strong?",
        "Some sprays are too strong for toys and can leave sticky smells behind. A grown-up can help choose a safer way to clean it."
    )],
    "wash": [(
        "Why does washing help some fabric things?",
        "Washing can rinse away sticky drops and strong smells from fabric. After that, the fabric needs time to dry in fresh air."
    )],
    "window": [(
        "What should you do if a room smells too strong?",
        "Tell a grown-up and move to fresh air. Opening a window can help the room breathe."
    )],
    "friendship": [(
        "What does a good friend do when an idea seems wrong?",
        "A good friend speaks kindly and tries to keep everyone safe. Friendship means helping each other make better choices."
    )],
}
KNOWLEDGE_ORDER = ["deodorant", "water", "air", "paper", "book", "toy", "wash", "window", "friendship"]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    setting = f["setting"]
    target = f["target_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a slice-of-life story for a 3-to-5-year-old that includes the words "cup-ful", "deodorant", and "like".',
            f"Tell a gentle friendship story where {a.id} wants to freshen {setting.scene} with deodorant, but {b.id} talks {a.pronoun('object')} out of it before anything gets sprayed.",
            f"Write a happy-ending story with a lesson learned: two friends almost use deodorant in the wrong way near {target.label}, then choose fresh air and kindness instead.",
        ]
    if outcome == "ruined":
        return [
            'Write a slice-of-life story that includes the words "cup-ful", "deodorant", and "like", and has a soft lesson about asking first.',
            f"Tell a friendship story where {a.id} mixes a cup-ful of water with deodorant in {setting.scene}, the air turns too strong, and the cozy spot cannot be used that day.",
            "Write a child-facing cautionary story with a calm grown-up, a lesson learned, and friends who still end up caring for each other.",
        ]
    return [
        'Write a slice-of-life story for a 3-to-5-year-old that includes the words "cup-ful", "deodorant", and "like".',
        f"Tell a happy-ending friendship story where two children get a cozy place ready, one child tries a wrong idea with deodorant, and a grown-up helps them fix it kindly.",
        f"Write a simple story with a lesson learned: strong smells do not make a little place better, and {target.label} stays safer with fresh air and care.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    parent = f["parent"]
    setting = f["setting"]
    target = f["target_cfg"]
    plan = f["plan"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, spending an afternoon together. {parent.label_word.capitalize()} helps them when their plan goes wrong."
        ),
        (
            "What were they getting ready?",
            f"They were making {setting.scene} for a quiet time together. They wanted it to feel cozy before they sat down to read and talk."
        ),
        (
            f"What idea did {a.id} have?",
            f"{a.id} wanted to use {plan.label} to make the little space smell nice. The idea sounded clever to {a.pronoun('object')}, but it was the wrong tool for that job."
        ),
        (
            f"What did {b.id} think about the idea?",
            f"{b.id} did not like the plan and warned that deodorant was too strong for such a small place. {b.pronoun().capitalize()} was trying to protect both the room and {target.label}."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What happened after {b.id} warned {a.id}?",
            f"{a.id} listened and backed down, so nothing got sprayed at all. That choice kept the little space comfortable and showed trust between friends."
        ))
        qa.append((
            "What lesson did they learn?",
            f"They learned that {plan.lesson_line}. They also learned that asking first is better than guessing with strong things."
        ))
    elif outcome == "contained":
        qa.append((
            "What went wrong when the deodorant mixture was used?",
            f"The air became sharp and uncomfortable, and {target.label} got damp. The problem happened because the cup-ful of water and deodorant was splashed inside a small cozy place instead of used the right way."
        ))
        qa.append((
            f"How did {parent.label_word} fix the problem?",
            f"{parent.label_word.capitalize()} {response.qa_text}. That helped because the room needed fresh air and the wet spots needed proper cleaning, not more spray."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily. The friends used the little space together after it was calm again, and the ending showed they had learned to be more careful."
        ))
    else:
        qa.append((
            "Could they use the cozy place right away after the mistake?",
            f"No. The smell was still too strong, so they had to leave the space empty for a while. Even so, they stayed together by the window and turned the mistake into a lesson."
        ))
        qa.append((
            "What lesson did they learn from the problem?",
            f"They learned that deodorant is not like magic room spray. Strong things should be used the right way, and asking a grown-up first can save a special place from being spoiled."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["plan"].tags) | set(f["setting"].tags) | set(f["target_cfg"].tags) | {"friendship"}
    tags |= set(f["response"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.enclosed:
            bits.append("enclosed=True")
        if ent.absorbency:
            bits.append(f"absorbency={ent.absorbency}")
        if ent.washable:
            bits.append("washable=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for target_id, target in TARGETS.items():
            for plan_id, plan in PLANS.items():
                if not hazard_at_risk(setting, target, plan):
                    continue
                if not sensible_responses(target):
                    continue
                combos.append((setting_id, target_id, plan_id))
    return combos


def explain_rejection(setting: Setting, target: Target, plan: DeodorantPlan) -> str:
    if not setting.enclosed:
        return (
            f"(No story: {setting.scene} is open enough that this deodorant mistake would not create a strong, trapped-air problem. "
            f"Pick a smaller enclosed place like a fort or play tent.)"
        )
    if target.absorbency <= 0:
        return (
            f"(No story: {target.label} would not really soak up the spray, so there is no clear mistake to fix.)"
        )
    if plan.id != "mix_and_splash":
        return "(No story: this plan does not fit the world model.)"
    return "(No story: this combination has no clear cozy-space deodorant mistake.)"


def explain_response(target: Target, response_id: str) -> str:
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response_id}': it scores too low on common sense. "
            f"Try a safer option like {', '.join(sorted(r.id for r in sensible_responses(target)))}.)"
        )
    if response.id == "wash_and_wait" and not target.washable:
        return (
            f"(Refusing response '{response_id}': {target.label} is not something this storyworld treats as washable. "
            f"Choose a response that uses fresh air and careful wiping instead.)"
        )
    return "(Refusing response: it does not fit this target.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.friend_age, params.trait):
        return "averted"
    setting = SETTINGS[params.setting]
    target = TARGETS[params.target]
    response = RESPONSES[params.response]
    return "contained" if contained_by(setting, target, response, params.delay) else "ruined"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(S, T, P) :- setting(S), target(T), plan(P),
                   enclosed(S), absorbency(T, A), A > 0, plan_kind(P, mix_and_splash).

sensible_for(T, R) :- response(R), sense(R, S), sense_min(M), S >= M,
                      not wash_only(R).
sensible_for(T, R) :- response(R), wash_only(R), washable(T),
                      sense(R, S), sense_min(M), S >= M.

valid(S, T, P) :- hazard(S, T, P), sensible_for(T, _).

% --- outcome model ---------------------------------------------------------
care_now(5) :- trait(T), careful_trait(T).
care_now(3) :- trait(T), not careful_trait(T).
older_friend :- relation(friends), friend_age(FA), instigator_age(IA), FA > IA.
authority(C + 1 + B) :- care_now(C), older_friend, bonus(2), B = 2.
authority(C + 1 + 0) :- care_now(C), not older_friend.
averted :- older_friend, authority(A), boldness_init(B), A > B.

severity(V) :- chosen_setting(S), chosen_target(T), delay(D),
               absorbency(T, A), enclosed_bonus(S, E), V = A + E + D.
contained :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(ruined) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        if setting.enclosed:
            lines.append(asp.fact("enclosed", setting_id))
            lines.append(asp.fact("enclosed_bonus", setting_id, 1))
        else:
            lines.append(asp.fact("enclosed_bonus", setting_id, 0))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("absorbency", target_id, target.absorbency))
        if target.washable:
            lines.append(asp.fact("washable", target_id))
    for plan_id in PLANS:
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("plan_kind", plan_id, "mix_and_splash"))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        if response_id == "wash_and_wait":
            lines.append(asp.fact("wash_only", response_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


CURATED = [
    StoryParams(
        setting="fort",
        target="paper_chain",
        plan="mix_and_splash",
        response="air_out_and_wipe",
        instigator="Ava",
        instigator_gender="girl",
        friend="Mia",
        friend_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=5,
        friend_age=7,
        relation="friends",
        trust=6,
        pet="the kitten",
    ),
    StoryParams(
        setting="play_tent",
        target="stuffed_bunny",
        plan="mix_and_splash",
        response="wash_and_wait",
        instigator="Leo",
        instigator_gender="boy",
        friend="Nora",
        friend_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=6,
        friend_age=6,
        relation="friends",
        trust=5,
        pet="the cat",
    ),
    StoryParams(
        setting="fort",
        target="library_book",
        plan="mix_and_splash",
        response="air_out_and_wipe",
        instigator="Tom",
        instigator_gender="boy",
        friend="Ella",
        friend_gender="girl",
        parent="mother",
        trait="gentle",
        delay=1,
        instigator_age=7,
        friend_age=6,
        relation="friends",
        trust=4,
        pet="",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: friends, a cozy place, a wrong deodorant idea, and a lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include QA")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.target and args.plan:
        if not hazard_at_risk(SETTINGS[args.setting], TARGETS[args.target], PLANS[args.plan]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], TARGETS[args.target], PLANS[args.plan]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.target is None or combo[1] == args.target)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, target_id, plan_id = rng.choice(sorted(combos))
    target = TARGETS[target_id]

    if args.response:
        if args.response not in RESPONSES:
            raise StoryError("(Unknown response.)")
        if RESPONSES[args.response].sense < SENSE_MIN or (args.response == "wash_and_wait" and not target.washable):
            raise StoryError(explain_response(target, args.response))
        response_id = args.response
    else:
        response_id = rng.choice(sorted(r.id for r in sensible_responses(target)))

    instigator, instigator_gender = _pick_kid(rng)
    friend, friend_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    instigator_age, friend_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(3, 8)
    pet = rng.choice(PETS)

    return StoryParams(
        setting=setting_id,
        target=target_id,
        plan=plan_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        friend_age=friend_age,
        relation="friends",
        trust=trust,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        target = TARGETS[params.target]
        plan = PLANS[params.plan]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not hazard_at_risk(setting, target, plan):
        raise StoryError(explain_rejection(setting, target, plan))
    if response.sense < SENSE_MIN or (response.id == "wash_and_wait" and not target.washable):
        raise StoryError(explain_response(target, response.id))

    world = tell(
        setting=setting,
        target_cfg=target,
        plan=plan,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        friend=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        friend_age=params.friend_age,
        relation=params.relation,
        trust=params.trust,
        pet=params.pet,
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(25):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed on seed {seed}.")
            break

    bad = 0
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
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
        print(f"{len(combos)} compatible (setting, target, plan) combos:\n")
        for setting_id, target_id, plan_id in combos:
            allowed = ", ".join(sorted(r.id for r in sensible_responses(TARGETS[target_id])))
            print(f"  {setting_id:12} {target_id:12} {plan_id:14} responses=[{allowed}]")
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.instigator} & {p.friend}: {p.setting}, {p.target}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
