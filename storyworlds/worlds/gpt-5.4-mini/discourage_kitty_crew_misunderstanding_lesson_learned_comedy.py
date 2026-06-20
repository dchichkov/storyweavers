#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/discourage_kitty_crew_misunderstanding_lesson_learned_comedy.py
================================================================================================

A standalone storyworld for a tiny comedy domain about a kid, a kitty, and a
crew who get tangled in a misunderstanding, then learn a lesson together.

Premise
-------
A child and a small crew want to put on a pretend show with a kitty as the
"star." One child tries to discourage a risky, silly idea, but the discouraging
gets misunderstood as mean. The crew briefly thinks the kitty has been banned,
then realizes the adult concern is about a prop and a messy stage problem, not
the kitty itself. The group fixes the mistake, the kitty gets a safe part in the
show, and everyone learns to speak clearly.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly for QAItem, StoryError, StorySample
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate plus an inline ASP twin
- produces story-grounded QA and world-knowledge QA from simulated state
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
    place: str
    stage: str
    mood: str
    crowd: str
    audio: str


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    risky: bool = False
    messy: bool = False
    funny: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Kitty:
    id: str
    label: str
    phrase: str
    role: str
    color: str
    tricks: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    label: str
    clue: str
    fix: str
    comedy_tag: str
    tags: set[str] = field(default_factory=set)


@dataclass
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("mess", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in world.entities.values():
            if other.kind == "character":
                other.memes["alarm"] += 1
        out.append("__mess__")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("misunderstanding_started") and not world.facts.get("misunderstanding_resolved"):
        sig = ("misunderstanding",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["confusion"] += 1
        out.append("__misunderstanding__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("mess", "physical", _r_mess),
    Rule("misunderstanding", "social", _r_misunderstanding),
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


def pet_at_risk(prop: Prop) -> bool:
    return prop.risky and prop.messy


def reasonable_combo(prop: Prop, kitty: Kitty, lesson: Lesson) -> bool:
    return pet_at_risk(prop) and kitty.role == "star" and lesson.fix != ""


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, prop in PROPS.items():
            for kid in KITTIES:
                for lid in LESSONS:
                    if reasonable_combo(prop, KITTIES[kid], LESSONS[lid]):
                        combos.append((sid, pid, kid))
    return combos


def predict(world: World, prop_id: str) -> dict:
    sim = world.copy()
    sim.get(prop_id).meters["mess"] += 1
    propagate(sim, narrate=False)
    return {
        "alarm": max(e.memes["alarm"] for e in sim.entities.values() if e.kind == "character"),
        "confusion": max(e.memes["confusion"] for e in sim.entities.values() if e.kind == "character"),
    }


def setup(world: World, child: Entity, pal: Entity, kitty: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    pal.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {pal.id} arrived at {setting.place}, "
        f"where {setting.stage} felt ready for a show."
    )
    world.say(
        f"They had {setting.crowd}, {setting.audio}, and one very important kitty named {kitty.id}."
    )


def tempt(world: World, child: Entity, prop: Prop) -> None:
    child.memes["silliness"] += 1
    world.say(
        f'{child.id} pointed at {prop.label}. "What if the {prop.label} is the star?" '
        f"they asked, already grinning."
    )
    world.say("The idea sounded funny enough to make the crew snicker.")
    

def discourage(world: World, pal: Entity, child: Entity, prop: Prop, kitty: Kitty, lesson: Lesson) -> None:
    pred = predict(world, prop.id)
    pal.memes["care"] += 1
    world.facts["predicted_alarm"] = pred["alarm"]
    world.say(
        f'{pal.id} shook {pal.pronoun("possessive")} head. "Please discourage that idea," '
        f'{pal.pronoun()} said, then added, "I mean: please don\'t use {prop.label}. '
        f"The stage could get {lesson.clue}, and the kitty would only get worried.""
    )


def misunderstand(world: World, child: Entity, pal: Entity, kitty: Kitty, prop: Prop) -> None:
    child.memes["hurt"] += 1
    world.facts["misunderstanding_started"] = True
    world.say(
        f"{child.id}'s grin slipped. The crew heard 'discourage' and thought {pal.id} "
        f"was trying to send the kitty away."
    )
    world.say(
        f'"But kitty is part of the crew!" {child.id} cried. "We are not banning {kitty.label}!"'
    )


def clarify(world: World, pal: Entity, child: Entity, kitty: Kitty, prop: Prop, lesson: Lesson) -> None:
    world.facts["misunderstanding_resolved"] = True
    pal.memes["care"] += 1
    world.say(
        f'{pal.id} laughed softly. "No no," {pal.pronoun()} said. "I am not discouraging '
        f"{kitty.label}. I am discouraging {prop.label}. That prop would make the stage "
        f"{lesson.clue}.""
    )
    world.say(
        f"The crew blinked, then looked at the prop and the tiny kitty hat beside it."
    )


def fix(world: World, child: Entity, pal: Entity, kitty: Kitty, lesson: Lesson) -> None:
    child.memes["relief"] += 1
    pal.memes["relief"] += 1
    kitty.meters["spotlight"] += 1
    world.say(
        f"Then {child.id} and {pal.id} moved the prop offstage and chose {lesson.fix} instead."
    )
    world.say(
        f"The kitty got a safe bow, the crew got their laughs, and everybody kept the show."
    )


def lesson_learned(world: World, child: Entity, pal: Entity, kitty: Kitty, lesson: Lesson) -> None:
    for ent in (child, pal):
        ent.memes["lesson"] += 1
    world.say(
        f"After the curtains stopped wobbling, {pal.id} smiled. "
        f'"Next time, we will say what we mean," {pal.pronoun()} said. '
        f'"That way no one worries about the wrong thing."'
    )
    world.say(
        f"{child.id} nodded. The crew laughed, the kitty purred, and the lesson stuck."
    )


def tell(setting: Setting, prop: Prop, kitty: Kitty, lesson: Lesson,
         child_name: str = "Mina", child_gender: str = "girl",
         pal_name: str = "Jo", pal_gender: str = "boy",
         adult_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    pal = world.add(Entity(id=pal_name, kind="character", type=pal_gender, role="pal"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the adult"))
    world.add(Entity(id=prop.id, type="prop", label=prop.label))
    world.add(Entity(id=kitty.id, type="kitty", label=kitty.label))
    setup(world, child, pal, kitty, setting)
    world.para()
    tempt(world, child, prop)
    discourage(world, pal, child, prop, kitty, lesson)
    misunderstand(world, child, pal, kitty, prop)
    world.para()
    clarify(world, pal, child, kitty, prop, lesson)
    world.get(prop.id).meters["mess"] += 1
    propagate(world, narrate=False)
    fix(world, child, pal, kitty, lesson)
    lesson_learned(world, child, pal, kitty, lesson)
    world.facts.update(
        child=child, pal=pal, adult=adult, prop=prop, kitty=kitty, lesson=lesson,
        setting=setting, outcome="lesson_learned", misunderstood=True,
    )
    return world


SETTINGS = {
    "playroom": Setting("playroom", "the playroom", "the little stage", "sparkly and silly", "a few giggling friends", "a toy trumpet going honk-honk"),
    "backyard": Setting("backyard", "the backyard", "the blanket stage", "breezy and bouncy", "two neighbors peeking over the fence", "wind rustling the paper stars"),
    "kitchen": Setting("kitchen", "the kitchen", "the chair stage", "warm and clattery", "one parent and one sleepy dog", "a spoon tapping a cup"),
}

PROPS = {
    "confetti_cannon": Prop("confetti_cannon", "confetti cannon", "a giant confetti cannon", risky=True, messy=True, funny=True, tags={"confetti"}),
    "glitter_tube": Prop("glitter_tube", "glitter tube", "a glitter tube", risky=True, messy=True, funny=True, tags={"glitter"}),
    "squirty_flower": Prop("squirty_flower", "squirty flower", "a squirty flower", risky=True, messy=True, funny=True, tags={"water"}),
}

KITTIES = {
    "Mochi": Kitty("Mochi", "kitty", "the kitty", role="star", color="orange", tricks=["spin", "bow"], tags={"kitty"}),
    "Pip": Kitty("Pip", "kitty", "the kitty", role="star", color="gray", tricks=["wave", "peek"], tags={"kitty"}),
    "Noodle": Kitty("Noodle", "kitty", "the kitty", role="star", color="black", tricks=["sit", "jump"], tags={"kitty"}),
}

LESSONS = {
    "capable_words": Lesson("capable_words", "say what you mean", "a little glittery", "a cardboard star", "clear words", tags={"lesson"}),
    "gentle_fix": Lesson("gentle_fix", "choose the safe prop", "too sparkly", "a paper crown", "safe choice", tags={"lesson"}),
    "kitty_first": Lesson("kitty_first", "keep the kitty comfy", "too noisy", "a soft bow", "kitty care", tags={"lesson"}),
}

GIRL_NAMES = ["Mina", "Lina", "Tia", "Pia", "Nina", "Zoe"]
BOY_NAMES = ["Jo", "Ben", "Max", "Sam", "Theo", "Kai"]
TRAITS = ["cheery", "curious", "goofy", "gentle", "lively"]


@dataclass
class StoryParams:
    setting: str
    prop: str
    kitty: str
    lesson: str
    child: str
    child_gender: str
    pal: str
    pal_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a kitty crew, a misunderstanding, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--kitty", choices=KITTIES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--pal")
    ap.add_argument("--pal-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting or args.prop or args.kitty:
        combos = [c for c in combos
                  if (args.setting is None or c[0] == args.setting)
                  and (args.prop is None or c[1] == args.prop)
                  and (args.kitty is None or c[2] == args.kitty)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, kitty = rng.choice(sorted(combos))
    lesson = args.lesson or rng.choice(sorted(LESSONS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    pal_gender = args.pal_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or _pick_name(rng, child_gender)
    pal = args.pal or _pick_name(rng, pal_gender, avoid=child)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, prop, kitty, lesson, child, child_gender, pal, pal_gender, adult, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, pal, prop, kitty = f["child"], f["pal"], f["prop"], f["kitty"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "discourage", "kitty", and "crew".',
        f"Tell a comedy story where {child.id} and {pal.id} are part of a small crew with {kitty.label}, and one of them tries to discourage a silly prop idea.",
        f"Write a lighthearted lesson-learned story where a misunderstanding about discouraging {kitty.label} gets fixed with clearer words and a safe stage plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, pal, kitty, prop, lesson = f["child"], f["pal"], f["kitty"], f["prop"], f["lesson"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {pal.id}, and the kitty crew. They were trying to put on a silly show together."
        ),
        QAItem(
            question="What did the crew misunderstand?",
            answer=f"The crew thought {pal.id} was discouraging {kitty.label}, when really {pal.id} was discouraging {prop.label}. That mix-up made everyone worry for a moment."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They moved away the {prop.label} and picked {lesson.fix} instead. After that, the kitty could stay in the show and the stage stayed safe."
        ),
        QAItem(
            question="What lesson did they learn?",
            answer="They learned to say exactly what they mean. Clear words stop silly mix-ups before they turn into a bigger fuss."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does discourage mean?",
            answer="To discourage something means to tell someone not to do it or to explain why it may be a bad idea."
        ),
        QAItem(
            question="What is a kitty?",
            answer="A kitty is a small cat. Kitties can be playful, soft, and very cute."
        ),
        QAItem(
            question="What is a crew?",
            answer="A crew is a group of people who work or play together."
        ),
        QAItem(
            question="Why do people need clear words?",
            answer="Clear words help everyone understand the same thing. That makes it easier to avoid mistakes and work together."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(setting: Setting, prop: Prop, kitty: Kitty, lesson: Lesson,
         child_name: str, child_gender: str, pal_name: str, pal_gender: str,
         adult: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    pal = world.add(Entity(id=pal_name, kind="character", type=pal_gender, role="pal"))
    world.add(Entity(id="adult", kind="character", type=adult, role="adult", label="the adult"))
    world.add(Entity(id=prop.id, type="prop", label=prop.label))
    world.add(Entity(id=kitty.id, type="kitty", label=kitty.label))
    setup(world, child, pal, kitty, setting)
    world.para()
    tempt(world, child, prop)
    discourage(world, pal, child, prop, kitty, lesson)
    misunderstand(world, child, pal, kitty, prop)
    world.para()
    clarify(world, pal, child, kitty, prop, lesson)
    world.get(prop.id).meters["mess"] += 1
    propagate(world, narrate=False)
    fix(world, child, pal, kitty, lesson)
    lesson_learned(world, child, pal, kitty, lesson)
    world.facts.update(child=child, pal=pal, kitty=kitty, prop=prop, lesson=lesson,
                       setting=setting, outcome="lesson_learned")
    return world


def setup(world: World, child: Entity, pal: Entity, kitty: Kitty, setting: Setting) -> None:
    child.memes["joy"] += 1
    pal.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {pal.id} showed up at {setting.place}. "
        f"{setting.stage.capitalize()} was ready, and {kitty.id} was ready too."
    )
    world.say(
        f"The whole crew waited for a funny little show, with {setting.crowd} and {setting.audio} in the air."
    )


def tempt(world: World, child: Entity, prop: Prop) -> None:
    child.memes["silliness"] += 1
    world.say(
        f'{child.id} pointed at {prop.phrase}. "What if this is the grand star?" '
        f'{child.pronoun()} asked with a giggle.'
    )


def discourage(world: World, pal: Entity, child: Entity, prop: Prop, kitty: Kitty, lesson: Lesson) -> None:
    pred = predict(world, prop.id)
    pal.memes["care"] += 1
    world.facts["predicted_alarm"] = pred["alarm"]
    world.say(
        f'{pal.id} frowned at the prop. "I am trying to discourage that," {pal.pronoun()} said. '
        f'"If we use {prop.label}, the stage could get {lesson.clue}, and {kitty.id} might get spooked."'
    )


def misunderstand(world: World, child: Entity, pal: Entity, kitty: Kitty, prop: Prop) -> None:
    world.facts["misunderstanding_started"] = True
    child.memes["confusion"] += 1
    world.say(
        f"{child.id} gasped. The crew heard the word discourage and thought {pal.id} was banning {kitty.label}."
    )
    world.say(
        f'"No way," {child.id} said. "The kitty is the crew!"'
    )


def clarify(world: World, pal: Entity, child: Entity, kitty: Kitty, prop: Prop, lesson: Lesson) -> None:
    world.facts["misunderstanding_resolved"] = True
    pal.memes["relief"] += 1
    world.say(
        f'{pal.id} laughed. "No, no," {pal.pronoun()} said. "I am discouraging {prop.label}, not {kitty.label}. '
        f"The prop would make the stage {lesson.clue}."'
    )
    world.say("The crew looked at the prop, then at the kitty, then at each other, and all the faces made sense again.")


def fix(world: World, child: Entity, pal: Entity, kitty: Kitty, lesson: Lesson) -> None:
    child.memes["relief"] += 1
    pal.memes["relief"] += 1
    kitty.meters["spotlight"] += 1
    world.say(
        f"Then {child.id} and {pal.id} moved the prop aside and picked {lesson.fix} instead."
    )
    world.say(
        f"{kitty.id} got a tiny bow, the crew got a clean stage, and the room filled with happy laughter."
    )


def lesson_learned(world: World, child: Entity, pal: Entity, kitty: Kitty, lesson: Lesson) -> None:
    for ent in (child, pal):
        ent.memes["lesson"] += 1
    world.say(
        f'"Next time," {pal.id} said, "we will say exactly what we mean."'
    )
    world.say(
        f"{child.id} nodded. The kitty purred, the crew cheered, and the lesson was learned with a grin."
    )


def valid_combos_python() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, prop in PROPS.items():
            for kid, kitty in KITTIES.items():
                if reasonable_combo(prop, kitty, LESSONS["gentle_fix"]):
                    combos.append((sid, pid, kid))
    return combos


ASP_RULES = r"""
prop_risky(P) :- prop(P), risky(P), messy(P).
valid(S, P, K) :- setting(S), prop(P), kitty(K), prop_risky(P), kitty_star(K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.risky:
            lines.append(asp.fact("risky", pid))
        if p.messy:
            lines.append(asp.fact("messy", pid))
    for kid, k in KITTIES.items():
        lines.append(asp.fact("kitty", kid))
        if k.role == "star":
            lines.append(asp.fact("kitty_star", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos_python()):
        print("OK: ASP gate matches Python gate.")
    else:
        rc = 1
        print("MISMATCH in validity gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, prop=None, kitty=None, lesson=None, child=None, child_gender=None, pal=None, pal_gender=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("playroom", "confetti_cannon", "Mochi", "capable_words", "Mina", "girl", "Jo", "boy", "mother", "cheery"),
    StoryParams("backyard", "glitter_tube", "Pip", "gentle_fix", "Kai", "boy", "Lina", "girl", "father", "curious"),
    StoryParams("kitchen", "squirty_flower", "Noodle", "kitty_first", "Zoe", "girl", "Ben", "boy", "mother", "goofy"),
]


def explain_rejection(prop: Prop) -> str:
    return f"(No story: the {prop.label} is too harmless here, so there is no funny misunderstanding to fix.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], PROPS[params.prop], KITTIES[params.kitty], LESSONS[params.lesson],
        params.child, params.child_gender, params.pal, params.pal_gender, params.adult
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible triples:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos_python()
    if args.setting or args.prop or args.kitty:
        combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
                  and (args.prop is None or c[1] == args.prop)
                  and (args.kitty is None or c[2] == args.kitty)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, kitty = rng.choice(sorted(combos))
    lesson = args.lesson or rng.choice(sorted(LESSONS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    pal_gender = args.pal_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or _pick_name(rng, child_gender)
    pal = args.pal or _pick_name(rng, pal_gender, avoid=child)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, prop, kitty, lesson, child, child_gender, pal, pal_gender, adult, trait)


if __name__ == "__main__":
    main()
