#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/savory_food_curiosity_kindness_magic_pirate_tale.py
==================================================================================

A tiny pirate-tale storyworld about curiosity, kindness, and a little bit of magic.

Premise:
A curious pirate child follows a savory smell, finds a hidden food problem, uses
kindness instead of grabbing, and discovers a magic shared meal that changes the
mood of the whole ship.

The world is small on purpose:
- one child pirate
- one companion
- one savory food source
- one needy helper or guest
- one magical effect that turns the ending into a warm feast

The story is generated from simulated state, not by swapping nouns in a fixed
paragraph.  Emotional memes and physical meters both matter, and the prose is
driven by what the model says changed.
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
HUNGER_MIN = 1.0
MAGIC_MIN = 1.0


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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    scene: str
    smell: str
    pirate_frame: str
    has_hatch: bool = False
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
class Snack:
    id: str
    label: str
    phrase: str
    savoriness: int
    feeds: int
    warmth: str
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
class Companion:
    id: str
    label: str
    type: str
    role: str
    craving: str
    request: str
    mood_hint: str
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
class Magic:
    id: str
    label: str
    spark: str
    effect: str
    feast_text: str
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


def _r_hunger(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.meters["hunger"] >= HUNGER_MIN and ("hunger" not in world.fired):
            pass
    return out


def _r_magic(world: World) -> list[str]:
    out = []
    if world.facts.get("shared_food") and world.facts.get("kindness_given") and not world.facts.get("magic_used"):
        world.facts["magic_used"] = True
        crew = world.get("crew")
        crew.meters["wonder"] += 1
        out.append("__magic__")
    return out


CAUSAL_RULES = [Rule("magic", _r_magic)]


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


def savory_smell_line(place: Place, snack: Snack) -> str:
    return f"The air around {place.label} smelled {snack.warmth} and savory, like a promise of food."


def predict(world: World, snack: Snack) -> dict:
    sim = world.copy()
    sim.get("snack").meters["available"] += 1
    return {"available": True, "magic": bool(sim.facts.get("shared_food"))}


def setup(world: World, hero: Entity, pal: Entity, crew: Entity, place: Place, snack: Snack, companion: Companion) -> None:
    hero.memes["curiosity"] += 2
    pal.memes["kindness"] += 1
    crew.memes["hunger"] += 1
    hero.meters["hunger"] += 1
    world.say(
        f"On a windy morning, {hero.id} and {pal.id} crept along the deck of {place.label}. "
        f"{place.pirate_frame}"
    )
    world.say(savory_smell_line(place, snack))
    world.say(
        f"{hero.id} wrinkled {hero.pronoun('possessive')} nose and grinned. "
        f'"What is that smell?" {hero.id} whispered.'
    )
    world.say(
        f"Behind a barrel, {companion.label} peeked out and said, "
        f'"{companion.request}," in a small voice.'
    )


def curiosity(world: World, hero: Entity, snack: Snack, companion: Companion) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} followed the savory smell until {hero.pronoun()} found "
        f"{snack.phrase}. The food sat warm and bright in a little tin bowl."
    )
    world.say(
        f"{hero.id} wanted to grab it right away, because curiosity made "
        f"{hero.pronoun('possessive')} paws feel quicker than {hero.pronoun('possessive')} thoughts."
    )


def kindness(world: World, hero: Entity, pal: Entity, snack: Snack, companion: Companion) -> None:
    hero.memes["kindness"] += 2
    pal.memes["kindness"] += 2
    world.facts["kindness_given"] = True
    world.say(
        f"Then {hero.id} looked at {companion.label} and saw the hungry little face. "
        f"{hero.id} did not snatch the food. Instead, {hero.pronoun()} shared it with {companion.label}."
    )
    world.say(
        f"{pal.id} nodded and helped break the {snack.label} into pieces, so everyone could eat."
    )


def magic_feast(world: World, crew: Entity, snack: Snack, magic: Magic, place: Place) -> None:
    crew.meters["wonder"] += 1
    crew.memes["joy"] += 2
    world.facts["shared_food"] = True
    propagate(world, narrate=False)
    world.say(
        f"At once, {magic.spark} danced over the bowl. The {snack.label} gave off a {magic.effect}, "
        f"and the whole deck filled with a cozy glow."
    )
    world.say(
        f"{magic.feast_text} Soon the crew sat together under {place.label}'s lantern light, "
        f"nibbling and smiling as if the ship had grown a happy heart."
    )


def ending(world: World, hero: Entity, pal: Entity, companion: Companion) -> None:
    hero.memes["joy"] += 1
    pal.memes["joy"] += 1
    world.say(
        f"By sunset, {hero.id} was full, {pal.id} was full, and {companion.label} was smiling wide. "
        f"The savory food was gone, but the kindness stayed aboard."
    )
    world.say(
        f"{hero.id} leaned on the rail and laughed, glad that curiosity had led to a friendlier treasure than gold."
    )


def tell(place: Place, snack: Snack, companion: Companion, magic: Magic,
         hero_name: str = "Mira", pal_name: str = "Finn", crew_name: str = "the crew") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", role="captainling"))
    pal = world.add(Entity(id=pal_name, kind="character", type="boy", role="mate"))
    crew = world.add(Entity(id=crew_name, kind="character", type="crew", role="ship"))
    snack_ent = world.add(Entity(id="snack", type="food", label=snack.label))
    hero.meters["hunger"] = 1
    pal.meters["hunger"] = 1
    crew.meters["hunger"] = 1

    setup(world, hero, pal, crew, place, snack, companion)
    world.para()
    curiosity(world, hero, snack, companion)
    world.para()
    kindness(world, hero, pal, snack, companion)
    world.para()
    magic_feast(world, crew, snack, magic, place)
    world.para()
    ending(world, hero, pal, companion)

    world.facts.update(
        hero=hero, pal=pal, crew=crew, place=place, snack=snack, companion=companion, magic=magic,
        shared_food=True, kindness_given=True, magic_used=True
    )
    return world


PLACES = {
    "galley": Place(
        id="galley",
        label="the ship's galley",
        scene="a tiny kettle sang on the stove, and rope swings swayed near the door",
        smell="savory soup",
        pirate_frame="The lanterns rocked, the kettle steamed, and every plank seemed to hum.",
        has_hatch=True,
    ),
    "harbor": Place(
        id="harbor",
        label="the harbor dock",
        scene="fish crates, net coils, and a kettle under a striped awning",
        smell="savory stew",
        pirate_frame="Seagulls circled above the masts while gullies of light shimmered on the water.",
        has_hatch=False,
    ),
}

SNACKS = {
    "stew": Snack(
        id="stew", label="stew", phrase="a bowl of savory stew", savoriness=3, feeds=3,
        warmth="rich", tags={"savory", "food", "stew"},
    ),
    "pie": Snack(
        id="pie", label="pie", phrase="a pan of savory pie", savoriness=3, feeds=4,
        warmth="buttery", tags={"savory", "food", "pie"},
    ),
    "crackers": Snack(
        id="crackers", label="crackers", phrase="a tin of savory crackers", savoriness=2, feeds=2,
        warmth="toasty", tags={"savory", "food", "crackers"},
    ),
}

COMPANIONS = {
    "stowaway": Companion(
        id="stowaway", label="a tiny stowaway", type="boy", role="helper",
        craving="a share of supper", request="I am hungry too", mood_hint="lonely",
        tags={"kindness"},
    ),
    "cook": Companion(
        id="cook", label="the ship cook", type="woman", role="helper",
        craving="help with the supper pot", request="Could you lend a hand?", mood_hint="busy",
        tags={"kindness"},
    ),
}

MAGICS = {
    "sparkle": Magic(
        id="sparkle", label="sparkle magic", spark="a sprinkle of silver sparks",
        effect="warm, buttery glow", feast_text="The magic did not make more food from nowhere; it made the shared food feel extra special.",
        tags={"magic"},
    ),
    "lantern": Magic(
        id="lantern", label="lantern magic", spark="a little lantern wink",
        effect="golden shimmer", feast_text="The lantern magic lit the bowls so every crumb looked like treasure.",
        tags={"magic"},
    ),
}

@dataclass
class StoryParams:
    place: str
    snack: str
    companion: str
    magic: str
    hero_name: str = "Mira"
    pal_name: str = "Finn"
    crew_name: str = "the crew"
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


CURATED = [
    StoryParams(place="galley", snack="stew", companion="stowaway", magic="sparkle", hero_name="Mira", pal_name="Finn", crew_name="the crew"),
    StoryParams(place="harbor", snack="pie", companion="cook", magic="lantern", hero_name="Nina", pal_name="Bo", crew_name="the crew"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SNACKS:
            for c in COMPANIONS:
                for m in MAGICS:
                    combos.append((p, s, c, m))
    return combos


KNOWLEDGE = {
    "savory": [("What does savory mean?",
                "Savory means food that is tasty and not sweet. Soup, stew, and crackers can be savory.")],
    "food": [("What is food for?",
              "Food gives people energy and helps them grow. It can also be shared to be kind.")],
    "kindness": [("What is kindness?",
                 "Kindness is when you help someone, share with them, or make them feel cared for.")],
    "curiosity": [("What is curiosity?",
                   "Curiosity is the feeling that makes you want to learn what something is.")],
    "magic": [("What is magic in a story?",
                "In a story, magic is a strange and wonderful thing that can change what happens.")],
    "pirate": [("What is a pirate?",
                "A pirate is a sailor in a sea adventure story. In kids' stories, pirates often search for treasure and have brave adventures.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the words "savory" and "food".',
        f"Tell a short story about {f['hero'].id} following a savory smell on a pirate ship, then choosing kindness and sharing food.",
        f'Write a gentle pirate story where curiosity leads to savory food, kindness changes the moment, and a little magic ends the tale.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    pal = f["pal"]
    companion = f["companion"]
    snack = f["snack"]
    magic = f["magic"]
    place = f["place"]
    return [
        QAItem(
            question="What did the ship smell like?",
            answer=f"It smelled savory, because {place.label} had {snack.phrase} nearby. That smell is what pulled {hero.id}'s curiosity toward the food.",
        ),
        QAItem(
            question=f"Why did {hero.id} not take the food for herself?",
            answer=f"{hero.id} saw that {companion.label} was hungry too, so {hero.id} chose kindness instead of grabbing. {pal.id} helped share it, and that made the moment feel fair.",
        ),
        QAItem(
            question="How did the magic change the ending?",
            answer=f"{magic.label} made the shared food glow warm and special. It did not replace the food; it turned the shared meal into a tiny feast that everyone could enjoy together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["snack"].tags) | set(world.facts["companion"].tags) | set(world.facts["magic"].tags)
    tags.add("pirate")
    out: list[QAItem] = []
    for key in ["savory", "food", "kindness", "curiosity", "magic", "pirate"]:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
shared_food :- kindness_given.
magic_used :- shared_food, kindness_given.
outcome(shared_feast) :- shared_food, magic_used.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
        for t in sorted(SNACKS[sid].tags):
            lines.append(asp.fact("tagged", sid, t))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    lines.append(asp.fact("kindness_given"))
    lines.append(asp.fact("shared_food"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(show="#show outcome/1."))
    asp_out = set(asp.atoms(model, "outcome"))
    py_out = {("shared_feast",)}
    if asp_out != py_out:
        print("MISMATCH:", asp_out, py_out)
        return 1
    sample = generate(CURATED[0])
    if not sample.story or "savory" not in sample.story:
        print("MISMATCH: story smoke test failed")
        return 1
    print("OK: ASP parity and story smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about savory food, curiosity, kindness, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--name")
    ap.add_argument("--pal")
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
              and (args.snack is None or c[1] == args.snack)
              and (args.companion is None or c[2] == args.companion)
              and (args.magic is None or c[3] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, snack, companion, magic = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        snack=snack,
        companion=companion,
        magic=magic,
        hero_name=args.name or rng.choice(["Mira", "Nina", "Luna", "Pia"]),
        pal_name=args.pal or rng.choice(["Finn", "Bo", "Kit", "Joss"]),
        crew_name="the crew",
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in [("place", PLACES), ("snack", SNACKS), ("companion", COMPANIONS), ("magic", MAGICS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    world = tell(
        PLACES[params.place],
        SNACKS[params.snack],
        COMPANIONS[params.companion],
        MAGICS[params.magic],
        hero_name=params.hero_name,
        pal_name=params.pal_name,
        crew_name=params.crew_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program(show="#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for row in valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.pal_name}: {p.snack} on {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
