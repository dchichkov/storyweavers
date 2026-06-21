#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cashier_jewish_fortune_transformation_humor_bad_ending.py
==========================================================================================

A small detective-style storyworld about a curious child, a cashier, a fortune
cookie, and a transformation that goes wrong in a funny way. The world is built
to support the seed words and features: cashier, jewish, fortune, Transformation,
Humor, Bad Ending, with a classic mystery tone.

The domain stays gentle and concrete: a child detective follows clues in a tiny
neighborhood market, misunderstands a fortune, and ends up transformed in a way
that makes the solution messier instead of better. The ending is bad in the sense
that the goal fails and the transformation causes trouble, but the story remains
child-facing and non-grim.

This script follows the Storyweavers contract:
- stdlib-only storyworld file
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate plus inline ASP twin
- QA sets grounded in simulated state, not by parsing rendered prose
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
    transformed_into: str = ""

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Suspect:
    id: str
    label: str
    alibi: str
    clue: str
    suspicious: bool = True
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
class Trigger:
    id: str
    label: str
    phrase: str
    wonder: str
    transforms_to: str
    makes_humor: bool = True
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
class Transformation:
    id: str
    label: str
    result_type: str
    result_label: str
    result_pronoun: str
    effect: str
    bad_for: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
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
class Rule:
    name: str
    tag: str
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


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("detective")
    if detective and detective.meters["embarrassment"] >= THRESHOLD:
        sig = ("humor", detective.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["amused"] += 1
            out.append("__humor__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("detective")
    trigger = world.entities.get("fortune")
    if not detective or not trigger:
        return out
    if detective.meters["sparked"] < THRESHOLD:
        return out
    sig = ("transform", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.transformed_into = trigger.attrs.get("transforms_to", "frog")
    detective.type = "animal"
    detective.label = f"a {detective.transformed_into}"
    detective.meters["lost_gear"] += 1
    detective.memes["panic"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("humor", "social", _r_humor),
    Rule("transformation", "magic", _r_transformation),
]


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


def reasonableness_ok(place: Place, trigger: Trigger, trans: Transformation, suspect: Suspect) -> bool:
    return ("mystery" in place.tags and "magic" in trigger.tags and
            trans.id == trigger.transforms_to and suspect.suspicious)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TRIGGERS.values():
            for x in TRANSFORMATIONS.values():
                for s in SUSPECTS.values():
                    if reasonableness_ok(p, t, x, s):
                        combos.append((p.id, t.id, x.id, s.id))
    return combos


@dataclass
class StoryParams:
    place: str
    trigger: str
    transformation: str
    suspect: str
    detective_name: str
    detective_gender: str
    cashier_name: str
    cashier_gender: str
    jewish_cashier: bool
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


PLACES = {
    "market": Place(
        id="market",
        label="the corner market",
        mood="busy and bright",
        affords={"mystery"},
        tags={"mystery", "shop"},
    ),
    "deli": Place(
        id="deli",
        label="the little deli",
        mood="warm and crowded",
        affords={"mystery"},
        tags={"mystery", "shop"},
    ),
}

SUSPECTS = {
    "oldman": Suspect("oldman", "an old man in a blue hat", "he claimed he was buying tea", "blue hat", tags={"hat"}),
    "cat": Suspect("cat", "a striped cat", "it was napping by the bread", "striped tail", tags={"cat"}),
    "lamp": Suspect("lamp", "a little lamp in the window", "it never moved", "shiny glass", suspicious=False, tags={"lamp"}),
}

TRIGGERS = {
    "fortune_cookie": Trigger(
        id="fortune_cookie",
        label="a fortune cookie",
        phrase="the fortune inside",
        wonder="the tiny slip of paper",
        transforms_to="frog",
        makes_humor=True,
        tags={"fortune", "magic"},
    ),
    "fortune_note": Trigger(
        id="fortune_note",
        label="a fortune note",
        phrase="the fortune written in curling ink",
        wonder="the folded note",
        transforms_to="parrot",
        makes_humor=True,
        tags={"fortune", "magic"},
    ),
}

TRANSFORMATIONS = {
    "frog": Transformation(
        id="frog",
        label="frog transformation",
        result_type="animal",
        result_label="frog",
        result_pronoun="it",
        effect="hopped instead of walking",
        bad_for="the detective's notebook",
        tags={"transformation", "frog"},
    ),
    "parrot": Transformation(
        id="parrot",
        label="parrot transformation",
        result_type="animal",
        result_label="parrot",
        result_pronoun="it",
        effect="squawked at every clue",
        bad_for="the detective's serious voice",
        tags={"transformation", "parrot"},
    ),
}

DETECTIVE_NAMES = ["Mina", "Rae", "Ivy", "Nora", "Eli", "Sam"]
CASHIER_NAMES = ["Leah", "Ben", "Mara", "Noah", "Tali", "Ari"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with a funny magical mistake and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--cashier-name")
    ap.add_argument("--cashier-gender", choices=["girl", "boy"])
    ap.add_argument("--jewish-cashier", action="store_true")
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


def _pick_name(rng: random.Random, gender: str, used: str = "") -> str:
    pool = [n for n in (DETECTIVE_NAMES if gender == "girl" else CASHIER_NAMES) if n != used]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    trigger = args.trigger or rng.choice(list(TRIGGERS))
    transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    if not reasonableness_ok(PLACES[place], TRIGGERS[trigger], TRANSFORMATIONS[transformation], SUSPECTS[suspect]):
        raise StoryError("No valid detective story matches those options.")
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    cashier_gender = args.cashier_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_gender)
    cashier_name = args.cashier_name or _pick_name(rng, cashier_gender, used=detective_name)
    return StoryParams(
        place=place,
        trigger=trigger,
        transformation=transformation,
        suspect=suspect,
        detective_name=detective_name,
        detective_gender=detective_gender,
        cashier_name=cashier_name,
        cashier_gender=cashier_gender,
        jewish_cashier=bool(args.jewish_cashier) or rng.choice([True, False]),
    )


def tell(place: Place, trigger: Trigger, transformation: Transformation, suspect: Suspect,
         detective_name: str, detective_gender: str, cashier_name: str, cashier_gender: str,
         jewish_cashier: bool) -> World:
    world = World()
    detective = world.add(Entity(id="detective", kind="character", type=detective_gender, label=detective_name, role="detective"))
    cashier = world.add(Entity(id="cashier", kind="character", type=cashier_gender, label=cashier_name, role="cashier"))
    suspect_ent = world.add(Entity(id="suspect", kind="character", type="thing", label=suspect.label))
    world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    world.add(Entity(id="fortune", kind="thing", type="trigger", label=trigger.label, attrs={"transforms_to": transformation.result_label}))
    detective.memes["curious"] += 1
    cashier.memes["busy"] += 1
    if jewish_cashier:
        cashier.attrs["jewish"] = True
    world.say(
        f"On a rainy evening at {place.label}, {detective_name} was trying to solve a tiny mystery. "
        f"At the counter, {cashier_name} the cashier rang up snacks, and the line moved like a patient snake."
    )
    world.say(
        f"{detective_name} noticed {suspect.label}, a suspicious little clue with {suspect.clue} and an alibi that sounded too neat."
    )
    if jewish_cashier:
        world.say(f"{cashier_name} was jewish, wore a bright apron, and smiled while folding paper bags with quick hands.")
    else:
        world.say(f"{cashier_name} kept the register humming and listened to every strange question.")
    world.para()
    world.say(
        f'{detective_name} leaned close to the counter. "{trigger.phrase}," {detective_name} whispered, '
        f'and {trigger.wonder} looked almost magical in the light.'
    )
    detective.meters["sparked"] += 1
    detective.meters["embarrassment"] += 1
    world.say(
        f"The joke was that the fortune was less of a clue and more of a punchline, because it said the detective should follow the crumbs before the crumbs followed back."
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"Then the mistake happened. The fortune was hot with nonsense, and {detective_name} touched it to the wrong lamp, as if that would make the case clearer."
    )
    detective.meters["sparked"] += 1
    propagate(world, narrate=True)
    world.para()
    if detective.transformed_into:
        world.say(
            f"With a pop and a puff, {detective_name} turned into {detective.transformed_into} {transformation.effect}."
        )
        world.say(
            f"{cashier_name} blinked, then laughed so hard the receipt tape wiggled. 'Well,' {cashier_name} said, 'that is the weirdest customer complaint I have ever heard.'"
        )
        world.say(
            f"{suspect.label_word if hasattr(suspect, 'label_word') else suspect.label} slipped away while everyone stared, so the case stayed unsolved."
        )
        world.say(
            f"By the time the tiny detective hopped out the door, the clue trail was gone, the notebook was soggy, and the whole mystery had become a joke that nobody could fix."
        )
        world.say(
            f"The end was no good at all: {detective_name} was stuck as a {detective.transformed_into}, the suspect escaped, and the cashier could only shake {cashier.pronoun('possessive')} head."
        )
    world.facts.update(
        place=place,
        trigger=trigger,
        transformation=transformation,
        suspect=suspect,
        detective=detective,
        cashier=cashier,
        jewish_cashier=jewish_cashier,
        outcome="bad",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a detective story for a child that includes the words cashier, jewish, and fortune, and ends with a bad magical mistake.",
        f"Tell a funny mystery about {f['detective'].label} and a {f['cashier'].label_word} at the {f['place'].label}, where a fortune causes a transformation.",
        f"Write a short detective tale where a child follows a clue, meets a cashier who is jewish, and the fortune leads to a silly bad ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective: Entity = f["detective"]
    cashier: Entity = f["cashier"]
    trig: Trigger = f["trigger"]
    trans: Transformation = f["transformation"]
    suspect: Suspect = f["suspect"]
    ans1 = (
        f"{detective.label} was trying to solve a mystery at {f['place'].label}. "
        f"{cashier.label} was the cashier, and the strange fortune caused the trouble. "
        f"It became funny, but the case went wrong at the end."
    )
    ans2 = (
        f"The fortune made {detective.label} touch the wrong thing, and that started the transformation. "
        f"After the change, the detective could not keep working normally, so the suspect got away."
    )
    ans3 = (
        f"The story ended badly because the detective turned into a {trans.result_label} and lost the chance to solve the case. "
        f"The cashier laughed, but the mystery stayed unsolved."
    )
    return [
        ("Who was the detective trying to question?", ans1),
        ("What caused the transformation?", ans2),
        ("How did the story end?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    qas = []
    qas.append(("What is a cashier?", "A cashier is the person at a store counter who takes money, rings up items, and gives receipts."))
    qas.append(("What is a fortune?", "A fortune is a short message that says what might happen or gives a playful prediction."))
    qas.append(("What is a transformation?", "A transformation is a change from one form into another form."))
    qas.append(("Why can mystery stories be funny?", "Mystery stories can be funny when clues go wrong, people say surprising things, or the detective makes a silly mistake."))
    return qas


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.transformed_into:
            bits.append(f"transformed_into={e.transformed_into}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(place="market", trigger="fortune_cookie", transformation="frog", suspect="cat",
                    detective_name="Mina", detective_gender="girl", cashier_name="Leah",
                    cashier_gender="girl", jewish_cashier=True),
        StoryParams(place="deli", trigger="fortune_note", transformation="parrot", suspect="oldman",
                    detective_name="Eli", detective_gender="boy", cashier_name="Ari",
                    cashier_gender="boy", jewish_cashier=True),
    ]


CURATED = valid_story_params()


def explain_rejection() -> str:
    return "(No story: that setup does not make a believable mystery, magical transformation, and bad ending all at once.)"


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES or params.trigger not in TRIGGERS or params.transformation not in TRANSFORMATIONS or params.suspect not in SUSPECTS:
        raise StoryError("Invalid params.")
    if not reasonableness_ok(PLACES[params.place], TRIGGERS[params.trigger], TRANSFORMATIONS[params.transformation], SUSPECTS[params.suspect]):
        raise StoryError(explain_rejection())
    return tell(
        PLACES[params.place], TRIGGERS[params.trigger], TRANSFORMATIONS[params.transformation],
        SUSPECTS[params.suspect], params.detective_name, params.detective_gender,
        params.cashier_name, params.cashier_gender, params.jewish_cashier
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for t in p.tags:
            lines.append(asp.fact("tagged", p.id, t))
    for t in TRIGGERS.values():
        lines.append(asp.fact("trigger", t.id))
        lines.append(asp.fact("transforms_to", t.id, t.transforms_to))
    for x in TRANSFORMATIONS.values():
        lines.append(asp.fact("transformation", x.id))
    for s in SUSPECTS.values():
        lines.append(asp.fact("suspect", s.id))
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_possible(P,T,X,S) :- place(P), trigger(T), transformation(X), suspect(S), tagged(P,mystery), trigger(T), transformation(X), suspect(S).
valid(P,T,X,S) :- reasonably_possible(P,T,X,S), transforms_to(T,frog), transformation(X).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches Python gate.")
    else:
        rc = 1
        print("Mismatch between ASP and Python gates.")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"Smoke test failed: {e}")
        return 1
    return rc


def build_parser_and_main(): ...


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with a cashier, fortune, and a bad magical ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--cashier-name")
    ap.add_argument("--cashier-gender", choices=["girl", "boy"])
    ap.add_argument("--jewish-cashier", action="store_true")
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
              and (args.trigger is None or c[1] == args.trigger)
              and (args.transformation is None or c[2] == args.transformation)
              and (args.suspect is None or c[3] == args.suspect)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, trigger, transformation, suspect = rng.choice(sorted(combos))
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    cg = args.cashier_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        trigger=trigger,
        transformation=transformation,
        suspect=suspect,
        detective_name=args.detective_name or _pick_name(rng, dg),
        detective_gender=dg,
        cashier_name=args.cashier_name or _pick_name(rng, cg),
        cashier_gender=cg,
        jewish_cashier=bool(args.jewish_cashier) or rng.choice([True, False]),
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    return valid_story_param_tuples()


def valid_story_param_tuples() -> list[tuple[str, str, str, str]]:
    return valid_combos_python()


def valid_combos_python() -> list[tuple[str, str, str, str]]:
    return [(p.id, t.id, x.id, s.id) for p in PLACES.values() for t in TRIGGERS.values() for x in TRANSFORMATIONS.values() for s in SUSPECTS.values() if reasonableness_ok(p, t, x, s)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
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
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
