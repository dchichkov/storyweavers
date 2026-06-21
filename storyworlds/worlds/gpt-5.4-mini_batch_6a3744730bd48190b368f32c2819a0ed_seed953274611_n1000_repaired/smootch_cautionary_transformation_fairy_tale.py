#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smootch_cautionary_transformation_fairy_tale.py
===============================================================================

A tiny fairy-tale storyworld about a curious child, a strange enchanted kiss
called a smootch, and a cautionary transformation that teaches a gentle lesson.

The world is intentionally small:
- a child in a fairy-tale village
- a hedge-witch's charm
- a transformation that can go wrong
- a wise helper who knows how to reverse the spell

The premise is built around the seed word "smootch" and the requested features:
Cautionary + Transformation, with a fairy-tale tone.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "witch", "woman", "sister"}
        male = {"boy", "father", "king", "man", "brother", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    tone: str
    weather: str
    magic_sign: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    magic: str
    danger: str
    reversal_hint: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Creature:
    id: str
    label: str
    type: str
    kind: str
    vulnerable: bool = False
    transformed_form: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.meters["enchanted"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["changed"] += 1
    child.memes["fear"] += 1
    child.memes["wonder"] += 1
    out.append("__transform__")
    return out


def _r_warning(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.meters["changed"] < THRESHOLD:
        return out
    sig = ("warn",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["concern"] += 1
    out.append("__warn__")
    return out


CAUSAL_RULES = [Rule("transformation", _r_transformation), Rule("warning", _r_warning)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def can_target(charm: Charm, creature: Creature) -> bool:
    return "mirror" in charm.tags and creature.vulnerable


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.power >= 2]


def resolve_spell(remedy: Remedy, severity: int) -> bool:
    return remedy.power >= severity


def fairy_tale_opening(setting: Setting, child: Entity, helper: Entity) -> None:
    child.memes["curiosity"] += 1
    helper.memes["wisdom"] += 1
    world = child.attrs["world"]
    world.say(
        f"Long ago, in {setting.place}, {child.id} lived under {setting.tone} skies, "
        f"where every lantern glow seemed to hide a secret."
    )
    world.say(
        f"One day {child.id} met {helper.id}, a {helper.label} who knew the old sayings "
        f"of the lane and the leaves."
    )


def wonder_about_charm(world: World, child: Entity, charm: Charm) -> None:
    child.memes["desire"] += 1
    world.say(
        f"On the market square, a little stall shone with {charm.phrase}. "
        f'The seller whispered, "{charm.magic}"'
    )
    world.say(
        f'{child.id} leaned close. "What is a smootch?" {child.pronoun()} asked, '
        f'and the stallkeeper smiled at the foolish sparkle in the air.'
    )


def warn_about_charm(world: World, helper: Entity, child: Entity, charm: Charm, creature: Creature) -> None:
    helper.memes["concern"] += 1
    world.say(
        f'{helper.id} touched {child.pronoun("possessive")} sleeve and said, '
        f'"Child, do not smootch the {creature.label_word if hasattr(creature, "label_word") else creature.label} '
        f"when a charm is near. {charm.danger}."
        f' {charm.reversal_hint}."'
    )


def do_smootch(world: World, child: Entity, charm: Charm, creature: Creature) -> None:
    child.memes["boldness"] += 1
    child.meters["enchanted"] += 1
    world.say(
        f'But {child.id} gave the charm a quick smootch, thinking the bright spell '
        f'would be kind and pretty.'
    )
    world.say(
        f'At once the air snapped like a ribbon. The magic ran to {creature.label}, '
        f'and the old {creature.label} began to shimmer.'
    )
    child.attrs["target"] = creature.id


def transform_creature(world: World, child: Entity, creature: Creature) -> None:
    creature.meters["changed"] += 1
    creature.memes["panic"] += 1
    world.say(
        f'The {creature.label} stretched and shrank until it became {creature.transformed_form}. '
        f"{child.id} stared, wide-eyed, because the wish had turned into a warning."
    )


def call_for_help(world: World, helper: Entity, child: Entity, remedy: Remedy, creature: Creature) -> None:
    world.say(
        f"Then {helper.id} ran to the herb shelf, took {remedy.phrase}, and spoke a steadying rhyme."
    )
    if resolve_spell(remedy, 2):
        creature.meters["changed"] = 0.0
        child.meters["enchanted"] = 0.0
        helper.memes["relief"] += 1
        child.memes["relief"] += 1
        world.say(
            f"The rhyme worked. The magic unwound from the {creature.label}, and it returned to itself, blinking in the grass."
        )
    else:
        world.say(
            f"The rhyme trembled and failed. The spell stayed put, and the night grew too strange for comfort."
        )


def lesson(world: World, child: Entity, helper: Entity, charm: Charm, creature: Creature) -> None:
    child.memes["wisdom"] += 1
    helper.memes["love"] += 1
    world.say(
        f"{helper.id} hugged {child.id} and said, 'A smootch is not a game when magic is watching. "
        f"Some curious things must be left alone.'"
    )
    world.say(
        f"{child.id} nodded. From then on, {child.pronoun()} kept {child.pronoun('possessive')} hands to {child.pronoun('possessive')}self, "
        f"and the {creature.label} never wore the spell again."
    )


def tell(setting: Setting, charm: Charm, creature: Creature, remedy: Remedy,
         child_name: str = "Mara", child_gender: str = "girl",
         helper_name: str = "Aunt Willow", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name))
    thing = world.add(Entity(id="creature", kind="thing", type=creature.type, label=creature.label))
    child.attrs["world"] = world

    fairy_tale_opening(setting, child, helper)
    world.para()
    wonder_about_charm(world, child, charm)
    warn_about_charm(world, helper, child, charm, creature)
    world.para()
    do_smootch(world, child, charm, thing)
    propagate(world, narrate=False)
    transform_creature(world, child, thing)
    world.para()
    call_for_help(world, helper, child, remedy, thing)
    lesson(world, child, helper, charm, thing)

    world.facts.update(
        child=child, helper=helper, creature=thing, charm=charm, remedy=remedy,
        setting=setting, transformed=thing.meters["changed"] >= THRESHOLD,
        warned=True, outcome="reversed" if thing.meters["changed"] == 0 else "transformed",
    )
    return world


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="a little cottage beside the wood",
        tone="silver",
        weather="soft",
        magic_sign="moonlight on the window",
    ),
    "village": Setting(
        id="village",
        place="a quiet village at the edge of the hill",
        tone="golden",
        weather="mild",
        magic_sign="lanterns in the market lane",
    ),
}

CHARMS = {
    "mirror_leaf": Charm(
        id="mirror_leaf",
        label="mirror-leaf charm",
        phrase="a mirror-leaf charm in a blue cloth",
        magic="A smootch makes the mirror answer back.",
        danger="It can reflect a spell onto the nearest creature",
        reversal_hint="Only a calm song can loosen it again",
        tags={"mirror", "spell"},
    ),
    "rose_cup": Charm(
        id="rose_cup",
        label="rose-cup charm",
        phrase="a rose-cup charm with a gold thread",
        magic="A smootch invites the hidden magic to wake.",
        danger="If the charm is kissed too soon, it will wake the wrong sort of magic",
        reversal_hint="A brave helper can undo it with a morning rhyme",
        tags={"rose", "spell"},
    ),
}

CREATURES = {
    "frog": Creature(
        id="frog",
        label="frog",
        type="frog",
        kind="creature",
        vulnerable=True,
        transformed_form="a green ribboned frog-prince",
        tags={"frog", "transformation"},
    ),
    "cat": Creature(
        id="cat",
        label="cat",
        type="cat",
        kind="creature",
        vulnerable=True,
        transformed_form="a tiny velvet cat with a crown",
        tags={"cat", "transformation"},
    ),
}

REMEDIES = {
    "rhyme": Remedy(
        id="rhyme",
        label="morning rhyme",
        phrase="a morning rhyme",
        power=3,
        tags={"song", "reversal"},
    ),
    "herbs": Remedy(
        id="herbs",
        label="bitter herbs",
        phrase="a cup of bitter herbs",
        power=2,
        tags={"herbs", "reversal"},
    ),
}

CHILD_NAMES = ["Mara", "Lina", "Elsa", "Nora", "Tilda", "Sera", "Ivy", "Pippa"]
HELPER_NAMES = ["Aunt Willow", "Old Rose", "Nana Fern", "Sage Beatrice"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, charm in CHARMS.items():
            for gid, creature in CREATURES.items():
                if can_target(charm, creature):
                    combos.append((sid, cid, gid))
    return combos


@dataclass
class StoryParams:
    setting: str
    charm: str
    creature: str
    remedy: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale cautionary transformation storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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


def explain_rejection(charm: Charm, creature: Creature) -> str:
    return (
        f"(No story: the charm could not reasonably transform the {creature.label}, "
        f"or the helper would have no true warning to give.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.charm and args.creature:
        if not can_target(CHARMS[args.charm], CREATURES[args.creature]):
            raise StoryError(explain_rejection(CHARMS[args.charm], CREATURES[args.creature]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.charm is None or c[1] == args.charm)
              and (args.creature is None or c[2] == args.creature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, creature = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(REMEDIES))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        charm=charm,
        creature=creature,
        remedy=remedy,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a young child that includes the word "smootch" and a small warning about {f["charm"].label}.',
        f"Tell a cautionary transformation story where {f['child'].id} ignores a wise warning, gives a charm a smootch, and must be helped afterward.",
        f"Write a gentle fairy tale ending in which a spell is reversed and the child learns not to trust a glittering charm too quickly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, charm, creature = f["child"], f["helper"], f["charm"], f["creature"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who is tempted by {charm.label}, and {helper.id}, who tries to keep things safe."),
        ("What did the child do?",
         f"{child.id} gave the charm a smootch, which was the wrong thing to do because the magic was ready to move."),
        ("What happened next?",
         f"The spell ran onto the {creature.label} and changed it. That is the cautionary turn of the story: a small mistake led to a strange transformation."),
    ]
    if f.get("transformed"):
        qa.append((
            "How was the transformation fixed?",
            f"{helper.id} brought out {f['remedy'].phrase} and sang a steady rhyme. The spell unwound, and the creature came back to itself."
        ))
        qa.append((
            "What did the child learn?",
            f"{child.id} learned to leave strange magic alone and to ask for help before touching anything glittering or unknown. The ending proves the lesson because the child is careful afterward."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["charm"].tags) | set(f["creature"].tags) | set(f["remedy"].tags)
    knowledge = {
        "mirror": [("What does a mirror do?",
                    "A mirror shows you an image of what is in front of it. In fairy tales, mirrors can also seem magical.")],
        "spell": [("What is a spell?",
                   "A spell is a magic rule or magic words that make something happen in a story.")],
        "frog": [("What is a frog?",
                  "A frog is a small hopping animal that likes wet places near ponds and grass.")],
        "cat": [("What is a cat?",
                 "A cat is a small animal with whiskers and soft paws. Cats like warm spots and quiet corners.")],
        "song": [("Why can singing help in a story?",
                   "A calm song can help a worried heart slow down. In fairy tales, songs sometimes break enchantments.")],
        "herbs": [("What are herbs?",
                   "Herbs are plants with strong smells or tastes that people use for cooking or old remedies.")],
        "reversal": [("What does it mean to reverse a spell?",
                      "To reverse a spell means to make the magic go backward so the change is undone.")],
        "transformation": [("What is a transformation?",
                             "A transformation is a big change, like when something becomes a different form.")],
    }
    order = ["mirror", "spell", "frog", "cat", "song", "herbs", "reversal", "transformation"]
    out: list[tuple[str, str]] = []
    for key in order:
        if key in tags:
            out.extend(knowledge[key])
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
vulnerable_child(child) :- child_type(child).
can_transform(C, T) :- charm(C), creature(T), mirror_charm(C), vulnerable_creature(T).
transformed :- enchanted(child), can_transform(C, T).
warning(helper) :- transformed.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if "mirror" in charm.tags:
            lines.append(asp.fact("mirror_charm", cid))
    for gid, creature in CREATURES.items():
        lines.append(asp.fact("creature", gid))
        if creature.vulnerable:
            lines.append(asp.fact("vulnerable_creature", gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show can_transform/2."))
    return sorted(set(asp.atoms(model, "can_transform")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == {(c, t) for _, c, t in valid_combos()}:
        print(f"OK: ASP matches Python valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, charm=None, creature=None, remedy=None,
            name=None, gender=None, helper=None, helper_gender=None
        ), random.Random(777)))
        _ = sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


CURATED = [
    StoryParams(
        setting="cottage", charm="mirror_leaf", creature="frog", remedy="rhyme",
        child_name="Mara", child_gender="girl", helper_name="Aunt Willow", helper_gender="woman"
    ),
    StoryParams(
        setting="village", charm="rose_cup", creature="cat", remedy="herbs",
        child_name="Lina", child_gender="girl", helper_name="Old Rose", helper_gender="woman"
    ),
]


def generate(params: StoryParams) -> StorySample:
    for table, key in ((SETTINGS, params.setting), (CHARMS, params.charm), (CREATURES, params.creature), (REMEDIES, params.remedy)):
        if key not in table:
            raise StoryError(f"Unknown story parameter: {key!r}")
    world = tell(
        SETTINGS[params.setting],
        CHARMS[params.charm],
        CREATURES[params.creature],
        REMEDIES[params.remedy],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
    )
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid stories available.")
    setting, charm, creature = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(REMEDIES))
    return StoryParams(
        setting=args.setting or setting,
        charm=args.charm or charm,
        creature=args.creature or creature,
        remedy=remedy,
        child_name=args.name or rng.choice(CHILD_NAMES),
        child_gender=args.gender or rng.choice(["girl", "boy"]),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        helper_gender=args.helper_gender or rng.choice(["woman", "man"]),
    )


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show can_transform/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible transform combos:")
        for c, t in asp_valid_combos():
            print(f"  {c} -> {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
