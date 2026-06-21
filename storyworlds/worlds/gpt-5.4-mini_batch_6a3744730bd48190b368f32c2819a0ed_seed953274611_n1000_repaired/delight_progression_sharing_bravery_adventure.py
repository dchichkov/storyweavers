#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/delight_progression_sharing_bravery_adventure.py
=================================================================================

A standalone storyworld for a tiny adventure about a child, a shared trail, and
a brave step forward. The seed words are "delight" and "progression"; the feature
pair is sharing + bravery, so the world models a small expedition where children
find a path, share a helpful item, and grow bolder together.

The story engine is built from typed entities with physical meters and emotional
memes. The prose is state-driven: a map is partly explored, a gap must be crossed,
a helper item can be shared, and the ending proves what changed.

Supported CLI:
- default run
- -n
- --all
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
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
BRAVERY_INIT = 5.0
SHARING_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
    scene: str
    challenge: str
    path_word: str
    goal: str
    can_share: bool = True
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
class Item:
    id: str
    label: str
    phrase: str
    helps: str
    shared: bool = False
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
class Challenge:
    id: str
    label: str
    risk: str
    progress_need: int
    bravery_need: int
    success_text: str
    fail_text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["sharing"] < SHARING_MIN:
            continue
        sig = ("share", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["shared"] += 1
        out.append("__share__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["bravery"] < BRAVERY_INIT:
            continue
        sig = ("brave", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["boldness"] += 1
        out.append("__brave__")
    return out


CAUSAL_RULES = [Rule("share", _r_share), Rule("bravery", _r_bravery)]


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


def path_at_risk(place: Place, challenge: Challenge) -> bool:
    return place.can_share and challenge.progress_need >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, challenge in CHALLENGES.items():
            for iid, item in ITEMS.items():
                if path_at_risk(place, challenge) and iid in SHARED_ITEMS:
                    combos.append((pid, cid, iid))
    return combos


def predict(world: World, hero_id: str, item_id: str, challenge_id: str) -> dict:
    sim = world.copy()
    hero = sim.get(hero_id)
    item = sim.get(item_id)
    challenge = CHALLENGES[challenge_id]
    _share_item(sim, hero, item, narrate=False)
    success = hero.meters["progress"] >= challenge.progress_need and hero.memes["bravery"] >= challenge.bravery_need
    return {"shared": item.meters["shared"] >= THRESHOLD, "success": success}


def _share_item(world: World, hero: Entity, item: Entity, narrate: bool = True) -> None:
    item.meters["shared"] += 1
    hero.memes["sharing"] += 1
    propagate(world, narrate=narrate)


def begin(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["delight"] += 1
    friend.memes["delight"] += 1
    world.say(
        f"{hero.id} and {friend.id} set off on an adventure through {place.label}. "
        f"{place.scene}"
    )


def need(world: World, hero: Entity, friend: Entity, place: Place, challenge: Challenge) -> None:
    world.say(
        f"But {place.challenge} blocked the trail, and the map pointed toward {place.goal}. "
        f"{hero.id} peered ahead. \"We need a way to keep going,\" {hero.pronoun()} said."
    )


def warn(world: World, friend: Entity, hero: Entity, challenge: Challenge, item: Item) -> None:
    pred = predict(world, hero.id, "gear", challenge.id)
    friend.memes["care"] += 1
    world.facts["predicted_success"] = pred["success"]
    world.say(
        f"{friend.id} took a breath. \"We should share the {item.label} and use it together,\" "
        f"{friend.pronoun()} said. \"That way we can cross the hard part safely.\""
    )


def share_and_step(world: World, hero: Entity, friend: Entity, item: Item, challenge: Challenge) -> None:
    hero.memes["sharing"] += 1
    hero.meters["progress"] += 1
    friend.meters["progress"] += 1
    item.shared = True
    _share_item(world, hero, world.get("gear"))
    world.say(
        f"{hero.id} nodded and handed the {item.label} to {friend.id}. "
        f"Together they used it to move past the hard ground, one careful step at a time."
    )


def brave_turn(world: World, hero: Entity, friend: Entity, challenge: Challenge) -> None:
    hero.memes["bravery"] += 1
    friend.memes["bravery"] += 1
    world.say(
        f"The moment felt big, but {hero.id} kept going. {friend.id} stayed close, and the two of them "
        f"crossed the place they had feared."
    )


def success(world: World, place: Place, challenge: Challenge, item: Item) -> None:
    world.get("hero").meters["progress"] += 1
    world.get("friend").meters["progress"] += 1
    world.get("hero").memes["delight"] += 1
    world.get("friend").memes["delight"] += 1
    world.say(
        f"At last they reached {place.goal}. {challenge.success_text} "
        f"Their shared {item.label} was still in their hands, and the trail ahead looked bright."
    )


def fail(world: World, place: Place, challenge: Challenge, item: Item) -> None:
    world.get("hero").memes["worry"] += 1
    world.get("friend").memes["worry"] += 1
    world.say(
        f"They tried to hurry, but {challenge.fail_text} "
        f"Still, they stayed together and found a safer path back to the campfire."
    )
    world.say(
        f"By the time they returned, the {item.label} had been shared, and the map was ready for a better day."
    )


def tell(place: Place, challenge: Challenge, item_cfg: Item,
         hero_name: str = "Milo", friend_name: str = "Nia",
         hero_type: str = "boy", friend_type: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="leader"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="helper"))
    gear = world.add(Entity(id="gear", kind="thing", type="tool", label=item_cfg.label))

    hero.id = hero_name
    friend.id = friend_name
    gear.id = "gear"

    hero.memes["bravery"] = BRAVERY_INIT
    friend.memes["sharing"] = 1.0

    begin(world, hero, friend, place)
    world.para()
    need(world, hero, friend, place, challenge)
    warn(world, friend, hero, challenge, item_cfg)
    world.para()
    share_and_step(world, hero, friend, item_cfg, challenge)
    brave_turn(world, hero, friend, challenge)

    if hero.meters["progress"] >= challenge.progress_need and hero.memes["bravery"] >= challenge.bravery_need:
        world.para()
        success(world, place, challenge, item_cfg)
        outcome = "success"
    else:
        world.para()
        fail(world, place, challenge, item_cfg)
        outcome = "fail"

    world.facts.update(place=place, challenge=challenge, item=item_cfg, hero=hero, friend=friend, outcome=outcome)
    return world


PLACES = {
    "trail": Place(id="trail", label="the forest trail", scene="Tall trees leaned over the path, and birds flashed between the branches.", challenge="a rocky stream", path_word="trail", goal="the sunlit hilltop", can_share=True, tags={"adventure", "sharing"}),
    "cave": Place(id="cave", label="the cave mouth", scene="The cave glittered with small stones, but the dark tunnel waited ahead.", challenge="a narrow dark bend", path_word="cave", goal="the hidden chamber", can_share=True, tags={"adventure", "bravery"}),
    "island": Place(id="island", label="the little island path", scene="Blue water sparkled around the sand, and the wind tugged at their shirts.", challenge="a tide pool crossing", path_word="path", goal="the lookout rock", can_share=True, tags={"adventure", "sharing", "bravery"}),
}

ITEMS = {
    "rope": Item(id="rope", label="rope", phrase="a sturdy rope", helps="bridge a gap", tags={"share"}),
    "lantern": Item(id="lantern", label="lantern", phrase="a bright lantern", helps="light the way", tags={"brave"}),
    "cloak": Item(id="cloak", label="cloak", phrase="a warm cloak", helps="keep them steady", tags={"share"}),
}

SHARED_ITEMS = {"rope", "lantern", "cloak"}

CHALLENGES = {
    "stream": Challenge(id="stream", label="stream", risk="wet feet", progress_need=1, bravery_need=1, success_text="The rope made a small bridge, and the stream no longer looked impossible.", fail_text="the water splashed too high and slowed them down", tags={"sharing"}),
    "dark_bend": Challenge(id="dark_bend", label="dark bend", risk="deep shadows", progress_need=1, bravery_need=1, success_text="The lantern turned the tunnel into a friendly place.", fail_text="the shadows felt too big and made them stop", tags={"bravery"}),
    "crossing": Challenge(id="crossing", label="crossing", risk="slippery stones", progress_need=1, bravery_need=1, success_text="Their careful steps carried them over the stones and onto dry ground.", fail_text="the water rushed faster than their feet", tags={"sharing", "bravery"}),
}

@dataclass
class StoryParams:
    place: str
    challenge: str
    item: str
    name: str
    friend: str
    seed: Optional[int] = None
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


CURATED = [
    StoryParams(place="trail", challenge="stream", item="rope", name="Milo", friend="Nia", seed=1),
    StoryParams(place="cave", challenge="dark_bend", item="lantern", name="Ari", friend="June", seed=2),
    StoryParams(place="island", challenge="crossing", item="cloak", name="Leah", friend="Bo", seed=3),
]

GIRL_NAMES = ["Nia", "June", "Leah", "Mina", "Ruby", "Ivy"]
BOY_NAMES = ["Milo", "Ari", "Bo", "Finn", "Theo", "Jude"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that uses the words "delight" and "progression" and features sharing and bravery.',
        f"Tell a small story where {f['hero'].label_word} and {f['friend'].label_word} travel through {f['place'].label} and share {f['item'].label} to keep progressing.",
        f'Write a brave adventure with a shared helper item, a clear obstacle, and an ending image of happy progression.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    place: Place = f["place"]
    challenge: Challenge = f["challenge"]
    item: Item = f["item"]
    return [
        ("Who are the story about?",
         f"The story is about {hero.label_word} and {friend.label_word}, two children on a small adventure together."),
        ("What obstacle did they face?",
         f"They had to get past {place.challenge}. That part of the path slowed their progression, so they needed to be brave and work together."),
        ("How did they solve the problem?",
         f"They shared the {item.label} and used it together. That sharing helped their progression because it gave them a careful, useful way forward."),
        ("How did the ending show delight?",
         f"They reached {place.goal} feeling delighted and proud. The last image shows them still together, holding the shared {item.label} after making progress."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is sharing?",
         "Sharing means letting someone else use or enjoy something with you. It is a kind way to help a friend."),
        ("What is bravery?",
         "Bravery means doing something even when you feel worried or scared. Brave people keep going and try their best."),
        ("What does progression mean?",
         "Progression means moving forward little by little. In a story, it can mean getting closer to a goal one step at a time."),
        ("What does delight mean?",
         "Delight is a very happy feeling. It is the warm feeling you get when something goes well and makes you smile."),
    ]


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
share_boost(E) :- sharing(E), sharing_min(M), M <= 1.
brave(E) :- bravery(E), bravery_init(B), B >= 5.
valid(P, C, I) :- place(P), challenge(C), item(I), can_share(P), shared_item(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.can_share:
            lines.append(asp.fact("can_share", pid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        if iid in SHARED_ITEMS:
            lines.append(asp.fact("shared_item", iid))
    lines.append(asp.fact("sharing_min", SHARING_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about delight, progression, sharing, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
              and (args.challenge is None or c[1] == args.challenge)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, item = rng.choice(sorted(combos))
    hero = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(place=place, challenge=challenge, item=item, name=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.challenge not in CHALLENGES or params.item not in ITEMS:
        raise StoryError("Invalid StoryParams choice.")
    place = PLACES[params.place]
    challenge = CHALLENGES[params.challenge]
    item = ITEMS[params.item]
    world = World()
    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in BOY_NAMES else "girl", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl" if params.friend in GIRL_NAMES else "boy", label=params.friend))
    gear = world.add(Entity(id="gear", kind="thing", type="tool", label=item.label))
    hero.memes["bravery"] = BRAVERY_INIT
    friend.memes["sharing"] = 1.0
    world.facts.update(hero=hero, friend=friend, place=place, challenge=challenge, item=item)

    begin(world, hero, friend, place)
    world.para()
    need(world, hero, friend, place, challenge)
    warn(world, friend, hero, challenge, item)
    world.para()
    share_and_step(world, hero, friend, item, challenge)
    brave_turn(world, hero, friend, challenge)
    world.para()
    if hero.memes["bravery"] >= challenge.bravery_need and hero.meters["progress"] >= challenge.progress_need:
        success(world, place, challenge, item)
        outcome = "success"
    else:
        fail(world, place, challenge, item)
        outcome = "fail"
    world.facts["outcome"] = outcome
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
