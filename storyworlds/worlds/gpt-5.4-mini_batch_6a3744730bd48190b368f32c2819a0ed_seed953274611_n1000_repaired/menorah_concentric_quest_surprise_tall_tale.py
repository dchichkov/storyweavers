#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/menorah_concentric_quest_surprise_tall_tale.py
===============================================================================

A standalone story world for a tall-tale quest about a menorah, a concentric
trail, and a surprise ending.

The domain is small on purpose:
- a child and a guide follow a quest map through a barn, a lane, and a hill;
- the map marks concentric circles that only make sense once the child notices
  they are a lantern spiral around a hidden gift;
- the key objects are a menorah, a quest map, a lantern ring, and the surprise
  prize at the center.

The world is modeled as state changes, not frozen prose:
- physical meters track travel, brightness, tidiness, and discovery;
- emotional memes track hope, wonder, worry, and delight;
- a few causal rules move the story from premise to turn to ending.

This script supports:
default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
and --show-asp.
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
QUEST_MIN = 1
SURPRISE_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    in_county: str
    has_barn: bool = False
    has_hill: bool = False
    has_lane: bool = False
    has_lanterns: bool = False
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
class QuestItem:
    id: str
    label: str
    phrase: str
    where: str
    clue: str
    weight: int = 1
    surprise: bool = False
    concentric: bool = False
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Guide:
    id: str
    label: str
    title: str
    brave_line: str
    hint_line: str
    has_map: bool = True
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
class SurpriseGift:
    id: str
    label: str
    phrase: str
    shine: str
    reveal: str
    delight: str
    important: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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


def _r_wonder(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["discovered"] < THRESHOLD:
            continue
        sig = ("wonder", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["wonder"] += 1
        out.append("__wonder__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    gift = world.entities.get("gift")
    center = world.entities.get("center")
    if not kid or not gift or not center:
        return out
    if kid.meters["quest_progress"] < THRESHOLD:
        return out
    if gift.meters["revealed"] < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["delight"] += 1
    center.meters["glow"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("wonder", _r_wonder), Rule("surprise", _r_surprise)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for q in QUESTS:
            for g in GIFTS:
                if q.concentric and g.surprise:
                    combos.append((p.id, q.id, g.id))
    return combos


@dataclass
class StoryParams:
    place: str
    quest: str
    guide: str
    gift: str
    hero: str
    hero_gender: str
    elder: str
    elder_gender: str
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
    "hilltown": Place("hilltown", "Hilltown", "Morrow County", has_barn=True, has_hill=True, has_lane=True, has_lanterns=True),
    "laneway": Place("laneway", "Laneway Farm", "Morrow County", has_barn=True, has_hill=False, has_lane=True, has_lanterns=True),
    "ridge": Place("ridge", "Ridge Hollow", "Morrow County", has_barn=True, has_hill=True, has_lane=True, has_lanterns=True),
}

QUESTS = {
    "lantern_rings": QuestItem(
        id="lantern_rings",
        label="concentric lantern rings",
        phrase="concentric rings of lantern light",
        where="around the old barn",
        clue="The rings pointed toward the middle of the yard.",
        concentric=True,
    ),
    "wagon_tracks": QuestItem(
        id="wagon_tracks",
        label="wagon tracks",
        phrase="wagon tracks that looped and looped",
        where="along the lane",
        clue="The loops all pointed toward one square of grass.",
        concentric=True,
    ),
    "hay_circles": QuestItem(
        id="hay_circles",
        label="hay circles",
        phrase="concentric hay circles",
        where="behind the hill",
        clue="Each ring was a breadcrumb for brave feet.",
        concentric=True,
    ),
}

GUIDES = {
    "grandpa": Guide("grandpa", "Grandpa", "old river-tale teller", "He had the straightest voice in the county.", "He knew a clue when it twinkled."),
    "aunt": Guide("aunt", "Aunt May", "barn-corner watcher", "She could smell a mystery from three fields away.", "She said the middle is where surprises hide."),
}

GIFTS = {
    "menorah": SurpriseGift(
        id="menorah",
        label="menorah",
        phrase="a shining menorah",
        shine="glimmered like a row of little moons",
        reveal="was waiting at the center of the rings",
        delight="made the whole night look kinder",
    ),
    "starbox": SurpriseGift(
        id="starbox",
        label="star box",
        phrase="a little star box",
        shine="sparkled with painted stars",
        reveal="sat snug in a nest of straw",
        delight="felt like a prize from the sky",
    ),
}

GIRL_NAMES = ["Mina", "Ruth", "Lila", "Nora", "Ada", "Mabel", "Ivy", "Sara"]
BOY_NAMES = ["Ezra", "Levi", "Noah", "Jonah", "Ben", "Cal", "Owen", "Eli"]


def would_find_surprise(quest: QuestItem, gift: SurpriseGift) -> bool:
    return quest.concentric and gift.surprise


def choose_valid_hero(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return name, gender


def predict(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    _quest_sim(sim, narrate=False)
    return {
        "found": sim.get("center").meters["revealed"] >= THRESHOLD,
        "delight": sim.get("child").memes["delight"],
    }


def _quest_sim(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    elder = world.get("elder")
    guide = world.get("guide")
    quest = world.facts["quest"]
    gift = world.facts["gift"]
    world.say(
        f"On a moon-bright night in {world.place.label}, {child.id} and {elder.id} set out on a quest."
    )
    world.say(
        f"{guide.label} unfolded a map of {quest.phrase}, and the trail bent toward {quest.where}."
    )
    child.memes["hope"] += 1
    elder.memes["hope"] += 1
    child.meters["quest_progress"] += 1
    child.meters["seen_clue"] += 1
    world.get("center").meters["revealed"] += 1
    world.get("gift").meters["revealed"] += 1
    world.say(
        f"They followed the clue: {quest.clue} At the heart of it all, {gift.label} {gift.reveal}."
    )
    if gift.id == "menorah":
        world.say(
            f"The {gift.label} {gift.shine}, and its light felt like a trail of tiny campfires."
        )
    else:
        world.say(f"The {gift.label} {gift.shine}.")
    propagate(world, narrate=narrate)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="quester"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_gender, role="guide"))
    guide = world.add(Entity(id="guide", kind="character", type="grandfather", label=GUIDES[params.guide].label, role="helper"))
    quest = QUESTS[params.quest]
    gift = GIFTS[params.gift]
    world.add(Entity(id="center", type="place", label="the center"))
    world.add(Entity(id="gift", type="gift", label=gift.label))
    child.memes["curiosity"] += 1
    elder.memes["calm"] += 1
    world.facts.update(quest=quest, gift=gift)
    world.say(
        f"{child.id} had heard of a strange quest in {place.label}, where the path was said to be concentric as a wheel."
    )
    world.say(
        f"{elder.id} said it was a tale worth chasing, because a good surprise can hide in plain sight."
    )
    world.para()
    _quest_sim(world)
    world.para()
    world.say(
        f"When the last lantern was reached, {child.id} laughed, because the whole grand mystery had been a careful surprise."
    )
    world.say(
        f"{gift.label.capitalize()} at the center, concentric rings around it, and a brave heart to find it—that was the story."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: QuestItem = f["quest"]
    g: SurpriseGift = f["gift"]
    return [
        f'Write a tall tale for a child that includes the words "menorah" and "concentric".',
        f"Tell a quest story where a child follows {q.label} and finds a surprise at the center.",
        f"Write a brave, folksy story with a hidden gift, concentric clues, and a warm ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    q: QuestItem = f["quest"]
    g: SurpriseGift = f["gift"]
    child = world.get("child")
    elder = world.get("elder")
    return [
        ("What kind of story is this?",
         "It is a tall-tale quest story, full of lantern light, a winding trail, and a surprise at the center."),
        (f"What did {child.id} follow?",
         f"{child.id} followed {q.phrase}. The clues were concentric, so each ring led closer to the middle."),
        (f"What was the surprise?",
         f"The surprise was {g.phrase}. It was waiting right at the center, so the quest ended with a bright reveal."),
        (f"Who went on the quest with {child.id}?",
         f"{elder.id} went with {child.id}, and that made the journey feel safe and grand."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does concentric mean?",
         "Concentric means things share the same center, like circles nested around one middle spot."),
        ("What is a menorah?",
         "A menorah is a candle or lamp stand with several branches, often lit to give a warm glow."),
        ("What is a quest?",
         "A quest is a journey to find something important or solve a problem."),
        ("What is a surprise?",
         "A surprise is something unexpected that appears or happens when you do not see it coming."),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hilltown", quest="lantern_rings", guide="grandpa", gift="menorah", hero="Mina", hero_gender="girl", elder="Ezra", elder_gender="boy"),
    StoryParams(place="laneway", quest="wagon_tracks", guide="aunt", gift="starbox", hero="Levi", hero_gender="boy", elder="Ada", elder_gender="girl"),
]


def explain_rejection(place: Place, quest: QuestItem, gift: SurpriseGift) -> str:
    if not would_find_surprise(quest, gift):
        return "(No story: this quest and surprise do not fit the concentric clue pattern.)"
    return "(No story: the chosen combination is not reasonable.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if q.concentric:
            lines.append(asp.fact("concentric", qid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        if g.surprise:
            lines.append(asp.fact("surprise", gid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,Q,G) :- place(P), quest(Q), gift(G), concentric(Q), surprise(G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, quest=None, guide=None, gift=None, hero=None, elder=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
    except Exception as e:
        print(f"EMIT SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale quest world with a menorah and concentric clues.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", dest="elder_gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid quest exists.")
    place = args.place or rng.choice(sorted(PLACES))
    quest = args.quest or rng.choice(sorted(QUESTS))
    gift = args.gift or rng.choice(sorted(GIFTS))
    if not would_find_surprise(QUESTS[quest], GIFTS[gift]):
        raise StoryError("(No story: this combination does not produce a concentric-surprise quest.)")
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["boy", "girl"])
    hero = args.hero or (rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES))
    elder = args.elder or (rng.choice([n for n in (BOY_NAMES if elder_gender == "boy" else GIRL_NAMES) if n != hero]))
    guide = args.guide or rng.choice(sorted(GUIDES))
    return StoryParams(place=place, quest=quest, guide=guide, gift=gift, hero=hero, hero_gender=hero_gender, elder=elder, elder_gender=elder_gender)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.quest not in QUESTS or params.guide not in GUIDES or params.gift not in GIFTS:
        raise StoryError("Invalid story parameters.")
    world = World(PLACES[params.place])
    world.add(Entity(id="child", kind="character", type=params.hero_gender, role="quester"))
    world.add(Entity(id="elder", kind="character", type=params.elder_gender, role="guide"))
    world.add(Entity(id="guide", kind="character", type="grandfather", label=GUIDES[params.guide].label, role="helper"))
    world.add(Entity(id="center", type="thing", label="the center"))
    world.add(Entity(id="gift", type="thing", label=GIFTS[params.gift].label))
    world.facts.update(quest=QUESTS[params.quest], gift=GIFTS[params.gift])
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
