#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sociable_land_genetic_bravery_sound_effects_kindness.py
=======================================================================================

A standalone story world for a tiny rhyming tale about a child on the land,
a brave little moment, friendly sound effects, and kindness that turns a worry
into a win.  The world keeps three seed words in play -- sociable, land, genetic
-- and uses physical meters plus emotional memes so the story is driven by state,
not by a frozen paragraph with swapped nouns.

Core premise:
- A child wants to speak at a small community garden gathering on the land.
- A little stage problem makes the child nervous.
- A kind helper notices the fear, offers a brave practice, and the child learns
  that a gifted "genetic" bravery streak is not enough without kind support.
- Sound effects in the prose mark the emotional turns: tap, clap, hum, whoosh.

The script supports:
- default random stories
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp

It is intentionally self-contained and stdlib-only.
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
BRAVERY_INIT = 5.0
KIND_TRAITS = {"kind", "gentle", "helpful", "warm"}
SOCIABLE_TRAITS = {"sociable", "friendly", "chatty"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    scene: str
    sounds: list[str]
    kind_word: str
    seed_word: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ChildTrait:
    id: str
    label: str
    bravery_bonus: float
    sociable_bonus: float

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SoundEffect:
    id: str
    text: str
    kind: str = "warm"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class KindAction:
    id: str
    text: str
    effect: str
    bravery_boost: float
    kindness_boost: float

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_bravery_rises(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["bravery"] < THRESHOLD:
        return out
    sig = ("bravery_rises",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 0.5
    out.append("__bravery__")
    return out


def _r_kindness_spreads(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    child = world.entities.get("child")
    if not helper or not child:
        return out
    if helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness_spreads",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["safe"] += 0.5
    helper.memes["joy"] += 0.5
    out.append("__kindness__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("bravery", "social", _r_bravery_rises),
    Rule("kindness", "social", _r_kindness_spreads),
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


def _do_stage(world: World, child: Entity, narrate: bool = True) -> None:
    child.meters["stage"] += 1
    child.memes["nervous"] += 1
    propagate(world, narrate=narrate)


def _do_kind(world: World, child: Entity, helper: Entity, action: KindAction, narrate: bool = True) -> None:
    child.memes["bravery"] += action.bravery_boost
    child.memes["joy"] += 1
    helper.memes["kindness"] += action.kindness_boost
    helper.memes["joy"] += 1
    if narrate:
        world.say(action.text)
    propagate(world, narrate=narrate)


def predict_turn(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    _do_stage(sim, child, narrate=False)
    return {
        "nervous": sim.get("child").memes["nervous"],
        "bravery": sim.get("child").memes["bravery"],
    }


def tell(place: Place, trait: ChildTrait, sound: SoundEffect, kindness: KindAction,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Luna", helper_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(
        id="child", kind="character", type=child_gender, label=child_name,
        role="speaker", traits=["sociable", trait.label],
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type=helper_gender, label=helper_name,
        role="friend", traits=["kind", "gentle"],
    ))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    stage = world.add(Entity(id="stage", kind="thing", type="stage", label=place.label))
    world.facts["place"] = place
    world.facts["trait"] = trait
    world.facts["sound"] = sound
    world.facts["kindness"] = kindness
    world.facts["parent"] = parent
    world.facts["stage"] = stage

    child.memes["bravery"] = BRAVERY_INIT + trait.bravery_bonus
    child.memes["sociable"] = 1.0 + trait.sociable_bonus

    world.say(
        f"On the {place.seed_word} land, {child.label} was sociable and bright. "
        f"{place.scene}"
    )
    world.say(
        f"{child.label} liked the little crowd, the leafy row, and every friendly face; "
        f"the day felt like a song in the right old place."
    )
    world.para()

    world.say(
        f"But when it was time to speak from the stage, {child.label}'s voice went thin. "
        f"{sound.text} went the boards, and the brave words hid within."
    )
    _do_stage(world, child, narrate=False)
    pred = predict_turn(world)
    world.facts["predicted_nervous"] = pred["nervous"]

    world.say(
        f"{helper.label} saw the wobble and smiled with care. "
        f'"You can do it," {helper.pronoun()} said, "I will be there."'
    )
    _do_kind(world, child, helper, kindness, narrate=True)

    world.para()
    world.say(
        f"{child.label} took one breath, then another, and stepped up tall; "
        f"{sound.text.upper()} came the cheers from the garden wall."
    )
    world.say(
        f"{child.label} spoke with a grin, and the little crowd clapped in time; "
        f"the words came out clear, like bells in a rhyme."
    )
    world.say(
        f"By the end, {child.label} was smiling on the {place.seed_word} land, "
        f"braver through kindness, and strong enough to stand."
    )

    world.facts.update(
        child=child, helper=helper, outcome="shared-bravery",
        spoke=True, helped=True, sound_used=sound.text, place_id=place.id,
    )
    return world


PLACES = {
    "community_garden": Place(
        "community_garden", "small stage by the tomato rows",
        "The bean vines leaned close, and the tomatoes wore red hats like tiny suns.",
        ["tap", "clap", "hum"], "land", "land",
    ),
    "school_yard": Place(
        "school_yard", "bench by the maple tree",
        "The swings whispered, and the grass made the yard feel soft and wide.",
        ["tap", "cheer", "hum"], "land", "land",
    ),
    "farm_fair": Place(
        "farm_fair", "pallet stage beside the apple cart",
        "The apples shone, and the hay bales stood in a bright neat line.",
        ["tap", "clap", "whoosh"], "land", "land",
    ),
}

TRAITS = {
    "bold": ChildTrait("bold", "bold", 1.5, 0.2),
    "curious": ChildTrait("curious", "curious", 0.8, 0.5),
    "gentle": ChildTrait("gentle", "gentle", 0.6, 1.0),
    "sociable": ChildTrait("sociable", "sociable", 1.0, 1.2),
}

SOUNDS = {
    "tap": SoundEffect("tap", "Tap-tap went the tiny stage boards."),
    "clap": SoundEffect("clap", "Clap-clap went the hands in the air."),
    "hum": SoundEffect("hum", "Hum-hum hummed the warm little crowd."),
    "whoosh": SoundEffect("whoosh", "Whoosh went a friendly breeze through the flags."),
}

KINDNESS = {
    "practice": KindAction(
        "practice", "The helper took a breath and practiced the line together.",
        "practice", 0.8, 1.0,
    ),
    "praise": KindAction(
        "praise", "The helper smiled and praised the first brave try.",
        "praise", 0.9, 1.2,
    ),
    "hand_hold": KindAction(
        "hand_hold", "The helper held a warm hand and counted one, two, three.",
        "hand_hold", 1.2, 1.4,
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Nia", "Zoe", "Ella", "Ivy", "Maya"]
BOY_NAMES = ["Noah", "Finn", "Leo", "Theo", "Eli", "Max", "Owen", "Sam"]
PARENT_TYPES = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, s) for p in PLACES for t in TRAITS for s in SOUNDS]


@dataclass
@dataclass
class StoryParams:
    place: str
    trait: str
    sound: str
    kindness: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = {
    "sociable": [("What does sociable mean?",
                  "Sociable means friendly and happy to be with other people.")],
    "bravery": [("What is bravery?",
                 "Bravery means doing something even when you feel nervous. It does not mean you are never scared.")],
    "kindness": [("What is kindness?",
                  "Kindness means caring about someone else's feelings and helping in a gentle way.")],
    "sound": [("Why do stories use sound effects?",
                "Sound effects help you hear the action in your mind, like clap, tap, hum, or whoosh.")],
    "land": [("What does land mean?",
              "Land is the ground we walk on, like fields, yards, gardens, and hills.")],
    "genetic": [("What does genetic mean?",
                 "Genetic means something is passed from parents to children in a family.")],
}

KNOWLEDGE_ORDER = ["sociable", "bravery", "kindness", "sound", "land", "genetic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    sound: SoundEffect = f["sound"]
    return [
        f'Write a rhyming story for a young child that includes the words "sociable", "land", and "genetic".',
        f"Tell a story on the {place.seed_word} where a sociable child gets nervous on stage, hears {sound.text.lower()}, and finds bravery through kindness.",
        f'Write a gentle rhyming story with sound effects and a kind helper, ending with the child speaking bravely on the land.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place: Place = f["place"]
    sound: SoundEffect = f["sound"]
    kindness: KindAction = f["kindness"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.label}, a sociable child who gets a chance to speak on the {place.seed_word}."),
        ("What made {0} nervous?".format(child.label),
         f"{sound.text} came from the little stage, and {child.label} felt the words disappear for a moment. "
         f"That nervous feeling was the turn in the story, before kindness helped it change."),
        ("How did the helper help?",
         f"{helper.label} offered {kindness.effect} and stayed close. That kindness gave {child.label} enough bravery to step up and try again."),
        ("What changed by the end?",
         f"{child.label} went from shaky to strong, and the story ended with a cheerful voice on the {place.seed_word}. "
         f"The ending proves bravery can grow when kindness is near."),
    ]
    if f.get("spoke"):
        qa.append((
            "What did the child do at the end?",
            f"{child.label} spoke to the little crowd and everyone clapped along. The child stood on the {place.seed_word} land feeling brave and glad."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sociable", "bravery", "kindness", "sound", "land", "genetic"}
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("community_garden", "sociable", "clap", "practice", "Mia", "girl", "Luna", "girl", "mother"),
    StoryParams("school_yard", "bold", "hum", "praise", "Noah", "boy", "Ava", "girl", "father"),
    StoryParams("farm_fair", "gentle", "whoosh", "hand_hold", "Ella", "girl", "Maya", "girl", "mother"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TRAITS:
        lines.append(asp.fact("trait", tid))
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
    for kid in KINDNESS:
        lines.append(asp.fact("kindness", kid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,S) :- place(P), trait(T), sound(S).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, trait=None, sound=None, kindness=None,
            child_name=None, child_gender=None, helper_name=None, helper_gender=None,
            parent=None, seed=None,
        ), random.Random(7)))
        assert sample.story.strip()
        print("OK: smoke-tested ordinary story generation.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a sociable child on the land, brave sound effects, and kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--kindness", choices=KINDNESS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trait is None or c[1] == args.trait)
              and (args.sound is None or c[2] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trait, sound = rng.choice(sorted(combos))
    kindness = args.kindness or rng.choice(sorted(KINDNESS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" and rng.random() < 0.5 else "girl")
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child_name])
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place, trait, sound, kindness, child_name, child_gender, helper_name, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TRAITS[params.trait], SOUNDS[params.sound], KINDNESS[params.kindness],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos[:50]:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
