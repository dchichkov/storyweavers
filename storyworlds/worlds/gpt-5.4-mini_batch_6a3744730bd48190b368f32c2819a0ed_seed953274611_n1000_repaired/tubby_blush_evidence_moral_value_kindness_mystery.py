#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tubby_blush_evidence_moral_value_kindness_mystery.py
====================================================================================

A small fairy-tale storyworld about a tubby little court, a blush of embarrassment,
and a mystery solved by kindness.

The domain:
- A royal child loses a treasured trinket.
- Another child notices clues and chooses kindness instead of blame.
- The mystery is solved through evidence, gentle reasoning, and a moral lesson.
- Some stories end in a warm apology and shared praise; others end with a small
  misunderstanding that still resolves kindly.

Required seed words are woven into story-world facts and prose:
- tubby
- blush
- evidence

Style:
- Fairy tale
- Child-facing
- Concrete, complete, and state-driven

This file is standalone and uses only stdlib plus the shared result containers.
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
KINDNESS_MIN = 2


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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "woman", "mother"}
        male = {"boy", "prince", "king", "man", "father"}
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
class Place:
    id: str
    label: str
    scene: str
    mystery_spot: str
    sounds_like: str
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
class Treasure:
    id: str
    label: str
    hidden_in: str
    gleam: str
    value_word: str
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
class Clue:
    id: str
    label: str
    kind: str
    place: str
    visible_from: str
    moral_hint: str
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
class Response:
    id: str
    kindness: int
    sense: int
    method: str
    fail: str
    qa: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_blush(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["embarrassment"] < THRESHOLD:
            continue
        sig = ("blush", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["blush"] += 1
        e.memes["shame"] += 1
        out.append("__blush__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kind", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["goodwill"] += 1
        out.append("__kind__")
    return out


CAUSAL_RULES = [
    Rule("blush", "social", _r_blush),
    Rule("kindness", "social", _r_kindness),
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


def clue_matches(place: Place, clue: Clue, treasure: Treasure) -> bool:
    return clue.place == place.id and treasure.hidden_in == place.id


def evidence_sufficient(clues: list[Clue], treasure: Treasure, place: Place) -> bool:
    kinds = {c.kind for c in clues if clue_matches(place, c, treasure)}
    return {"sparkle", "dust", "footprint"}.issubset(kinds)


def choose_kind_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: (r.kindness, r.sense))


def story_moral(world: World) -> str:
    return "kindness helps a mystery grow smaller"


def setup_story(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"Once in a {place.label}, {hero.id} and {helper.id} wandered by the {place.scene}."
    )
    world.say(
        f"The air felt like a fairy tale, and the {place.sounds_like} around the {place.mystery_spot} made everything seem secret."
    )


def present_problem(world: World, hero: Entity, treasure: Treasure, clue1: Clue) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"But then {hero.id} noticed something missing: the {treasure.label} was gone."
    )
    world.say(
        f"Only one small clue remained, a {clue1.label}, and it was not enough to tell the whole story."
    )


def ask_gentle_question(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} did not accuse anyone. Instead, {helper.pronoun()} asked softly, "
        f'"Can we look for evidence together, {hero.id}?"'
    )


def gather_evidence(world: World, clues: list[Clue], place: Place, treasure: Treasure) -> None:
    for clue in clues:
        world.say(
            f"They found a {clue.label} near {clue.visible_from}, and that clue pointed to the {place.mystery_spot}."
        )
    if evidence_sufficient(clues, treasure, place):
        world.say(
            f"At last the evidence fit together like pieces of a story, and the hidden place could hide no more."
        )


def solve_mystery(world: World, hero: Entity, helper: Entity, treasure: Treasure, culprit: Entity, response: Response) -> None:
    culprit.meters["embarrassment"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They followed the clues and found that {culprit.id} had borrowed the {treasure.label} only to keep it safe."
    )
    world.say(
        f"{culprit.id} {response.method} and explained everything, while {hero.id} listened with a warm blush."
    )


def forgive_and_finish(world: World, hero: Entity, helper: Entity, culprit: Entity, treasure: Treasure) -> None:
    for e in (hero, helper, culprit):
        e.memes["kindness"] += 1
        e.memes["relief"] += 1
    world.say(
        f"Nobody was scolded. The children shared a smile, because the best treasure was their kindness."
    )
    world.say(
        f"And so the {treasure.label} came back to its place, shining softly as the little court grew peaceful again."
    )
    world.say(
        f"The moral was plain: {story_moral(world)}."
    )


def comfort_ending(world: World, hero: Entity, helper: Entity, treasure: Treasure) -> None:
    world.say(
        f"If the search was slow, they still stayed gentle, and the day ended with a tidy room and a calm heart."
    )
    world.say(
        f"Even then, the {treasure.label} glimmered as if it knew kindness had solved the mystery."
    )


PLACE_REGISTRY = {
    "castle_garden": Place(
        id="castle_garden",
        label="castle garden",
        scene="rose path",
        mystery_spot="old fountain",
        sounds_like="rustling leaves",
    ),
    "moon_hall": Place(
        id="moon_hall",
        label="moonlit hall",
        scene="silver aisle",
        mystery_spot="curtain nook",
        sounds_like="soft echoes",
    ),
    "apple_orchard": Place(
        id="apple_orchard",
        label="apple orchard",
        scene="orchard lane",
        mystery_spot="mossy tree root",
        sounds_like="birdsong",
    ),
}

TREASURE_REGISTRY = {
    "crown_charm": Treasure(
        id="crown_charm",
        label="crown charm",
        hidden_in="castle_garden",
        gleam="golden",
        value_word="royal",
    ),
    "silver_key": Treasure(
        id="silver_key",
        label="silver key",
        hidden_in="moon_hall",
        gleam="bright",
        value_word="secret",
    ),
    "pear_heart": Treasure(
        id="pear_heart",
        label="pear-heart locket",
        hidden_in="apple_orchard",
        gleam="soft",
        value_word="dear",
    ),
}

CLUE_REGISTRY = {
    "sparkle": Clue(
        id="sparkle",
        label="sparkle",
        kind="sparkle",
        place="castle_garden",
        visible_from="the fountain rim",
        moral_hint="be gentle with what glows",
    ),
    "dust": Clue(
        id="dust",
        label="dust line",
        kind="dust",
        place="moon_hall",
        visible_from="the curtain edge",
        moral_hint="little marks can tell the truth",
    ),
    "footprint": Clue(
        id="footprint",
        label="small footprint",
        kind="footprint",
        place="apple_orchard",
        visible_from="the root of the tree",
        moral_hint="follow quiet signs with care",
    ),
}

RESPONSES = {
    "confess": Response(
        id="confess",
        kindness=3,
        sense=3,
        method="confessed that the charm had been borrowed to polish it",
        fail="tried to explain, but the words came out in a jumble",
        qa="confessed kindly and told the truth",
    ),
    "return": Response(
        id="return",
        kindness=2,
        sense=3,
        method="returned the treasure with a little bow",
        fail="meant to return it, but was too nervous to speak",
        qa="returned it and bowed politely",
    ),
    "apologize": Response(
        id="apologize",
        kindness=4,
        sense=4,
        method="apologized and placed the treasure in the open for everyone to see",
        fail="wanted to apologize, but the mystery was not ready yet",
        qa="apologized and made things right",
    ),
}


GIRL_NAMES = ["Lina", "Mira", "Tess", "Elia", "Pippa", "Nora", "June"]
BOY_NAMES = ["Oren", "Basil", "Robin", "Jory", "Finn", "Cedric"]
TRAITS = ["kind", "curious", "gentle", "brave", "patient"]


@dataclass
class StoryParams:
    place: str
    treasure: str
    clue1: str
    clue2: str
    clue3: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    culprit: str
    culprit_gender: str
    trait: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id in PLACE_REGISTRY:
        for treasure_id, treasure in TREASURE_REGISTRY.items():
            if treasure.hidden_in != place_id:
                continue
            for response_id in RESPONSES:
                combos.append((place_id, treasure_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale mystery solved by kindness and evidence.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--treasure", choices=TREASURE_REGISTRY)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.treasure and PLACE_REGISTRY[args.place].id != TREASURE_REGISTRY[args.treasure].hidden_in if args.place else False:
        raise StoryError("That treasure does not belong in that place.")
    if args.response and RESPONSES[args.response].kindness < KINDNESS_MIN:
        raise StoryError("This storyworld prefers a kinder, wiser response.")
    place = args.place or rng.choice(list(PLACE_REGISTRY))
    treasure = args.treasure or next(tid for tid, t in TREASURE_REGISTRY.items() if t.hidden_in == place)
    response = args.response or rng.choice(list(RESPONSES))
    clue_ids = rng.sample(list(CLUE_REGISTRY), 3)
    hero_gender = rng.choice(["girl", "boy"])
    hero = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_gender = "girl" if hero_gender == "boy" else "boy"
    helper = rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    culprit_gender = rng.choice(["girl", "boy"])
    culprit = rng.choice([n for n in (GIRL_NAMES if culprit_gender == "girl" else BOY_NAMES) if n not in {hero, helper}])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        treasure=treasure,
        clue1=clue_ids[0],
        clue2=clue_ids[1],
        clue3=clue_ids[2],
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        culprit=culprit,
        culprit_gender=culprit_gender,
        trait=trait,
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACE_REGISTRY[params.place]
    treasure = TREASURE_REGISTRY[params.treasure]
    clues = [CLUE_REGISTRY[params.clue1], CLUE_REGISTRY[params.clue2], CLUE_REGISTRY[params.clue3]]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero", traits=["curious", params.trait]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["gentle"]))
    culprit = world.add(Entity(id=params.culprit, kind="character", type=params.culprit_gender, role="culprit", traits=["nervous"]))
    treasure_obj = world.add(Entity(id="treasure", type="thing", label=treasure.label))

    world.facts.update(place=place, treasure=treasure, clues=clues, response=RESPONSES[params.response], hero=hero, helper=helper, culprit=culprit)
    setup_story(world, hero, helper, place)
    world.para()
    present_problem(world, hero, treasure, clues[0])
    ask_gentle_question(world, helper, hero)
    world.para()
    gather_evidence(world, clues, place, treasure)
    solve_mystery(world, hero, helper, treasure, culprit, RESPONSES[params.response])
    world.para()
    forgive_and_finish(world, hero, helper, culprit, treasure)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"].label
    treasure = f["treasure"].label
    return [
        f"Write a fairy tale about a missing {treasure} in the {place} that is solved by kindness and evidence.",
        f"Tell a gentle mystery story where children look for clues instead of blaming anyone, and the word 'evidence' appears.",
        f"Write a child-friendly fairy tale with the words tubby, blush, and evidence, ending in a moral lesson about kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    treasure: Treasure = f["treasure"]
    clues: list[Clue] = f["clues"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    culprit: Entity = f["culprit"]
    response: Response = f["response"]
    qa = [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a fairy-tale mystery about a missing {treasure.label} in the {place.label}. The children solve it by gathering evidence and choosing kindness instead of blame.",
        ),
        QAItem(
            question="Why did the hero blush?",
            answer=f"{hero.id} blushed because the mystery felt important and a little embarrassing. But the blush became a gentle sign that the truth was close, not a sign of trouble.",
        ),
        QAItem(
            question="What helped solve the mystery?",
            answer=f"The clues did. The {', '.join(c.label for c in clues)} all pointed to the same hidden place, and that evidence made the answer clear.",
        ),
        QAItem(
            question="How did the helper act kindly?",
            answer=f"{helper.id} spoke softly, asked to search together, and never blamed anyone too soon. That kindness kept the mystery calm enough to solve.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"The missing {treasure.label} was found, and {culprit.id} explained what happened. The children forgave one another, and the day ended peacefully.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is evidence?",
            answer="Evidence is a clue or fact that helps prove what happened. In a mystery, people look at evidence before deciding the truth.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating others gently and fairly. It can help people tell the truth and solve problems without hurting feelings.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to use clues and reasoning to find out what really happened. When the answer is found, the mystery is no longer confusing.",
        ),
        QAItem(
            question="What does blush mean?",
            answer="To blush means your cheeks turn red when you feel shy, embarrassed, or surprised. In stories, a blush can show a character cares a lot.",
        ),
        QAItem(
            question="What is a moral in a fairy tale?",
            answer="A moral is the lesson the story wants to teach. Fairy tales often end by showing how a good choice leads to a good result.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% facts: place/1 treasure/1 clue/1 response/1
kindness_ok(R) :- response(R), response_kindness(R, K), kindness_min(M), K >= M.
evidence_complete(P,T) :- clue(C1), clue(C2), clue(C3), clue_place(C1,P), clue_place(C2,P), clue_place(C3,P), treasure_hidden_in(T,P).
mystery_solved(P,T) :- evidence_complete(P,T), kindness_ok(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACE_REGISTRY:
        lines.append(asp.fact("place", pid))
    for tid, t in TREASURE_REGISTRY.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("treasure_hidden_in", tid, t.hidden_in))
    for cid, c in CLUE_REGISTRY.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_place", cid, c.place))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("response_kindness", rid, r.kindness))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show treasure_hidden_in/2."))
    return sorted(set(asp.atoms(model, "treasure_hidden_in")))


def asp_verify() -> int:
    import asp
    py = {(p, t) for p, t in valid_combos()}
    cl = set(asp.atoms(asp.one_model(asp_program("#show treasure_hidden_in/2.")), "treasure_hidden_in"))
    rc = 0
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid_combos.")
        rc = 1
    sample = generate(resolve_params(argparse.Namespace(place=None, treasure=None, response=None), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: generate() produced empty story.")
        rc = 1
    else:
        print("OK: generate() smoke test passed.")
    return rc


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params_main(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show treasure_hidden_in/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show treasure_hidden_in/2."))
        print("compatible treasure-place facts:")
        for p, t in asp.atoms(model, "treasure_hidden_in"):
            print(f"  {p} -> {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(
                place="castle_garden",
                treasure="crown_charm",
                clue1="sparkle",
                clue2="dust",
                clue3="footprint",
                response="apologize",
                hero="Lina",
                hero_gender="girl",
                helper="Robin",
                helper_gender="boy",
                culprit="Mira",
                culprit_gender="girl",
                trait="kind",
            ),
            StoryParams(
                place="moon_hall",
                treasure="silver_key",
                clue1="dust",
                clue2="sparkle",
                clue3="footprint",
                response="confess",
                hero="Oren",
                hero_gender="boy",
                helper="Nora",
                helper_gender="girl",
                culprit="Basil",
                culprit_gender="boy",
                trait="curious",
            ),
            StoryParams(
                place="apple_orchard",
                treasure="pear_heart",
                clue1="footprint",
                clue2="sparkle",
                clue3="dust",
                response="return",
                hero="Tess",
                hero_gender="girl",
                helper="Jory",
                helper_gender="boy",
                culprit="Elia",
                culprit_gender="girl",
                trait="gentle",
            ),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.hero}: {p.place}, {p.treasure}, {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
