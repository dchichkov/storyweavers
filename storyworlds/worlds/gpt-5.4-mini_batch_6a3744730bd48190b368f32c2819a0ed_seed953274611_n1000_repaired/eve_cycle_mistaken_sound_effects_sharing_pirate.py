#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/eve_cycle_mistaken_sound_effects_sharing_pirate.py
===================================================================================

A small storyworld in pirate-tale style about an eve harbor game, a bicycle
that makes a mistaken sound, and a sharing-based resolution. The children hear
something that sounds like a monster at the dock, but it is only a cycle wheel
and a squeaky gear. They share the right tools, correct the mistake, and finish
their play with bright lanterns, a map, and a calm sea.

Seed words to include:
- eve
- cycle
- mistaken

Features:
- Sound Effects
- Sharing

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  --show-asp
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
SOUND_MIN = 2
CONFUSION_INIT = 4.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
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
class Harbor:
    id: str
    name: str
    detail: str
    sound_word: str
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
class Noise:
    id: str
    label: str
    source: str
    sound_effect: str
    mistaken_for: str
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
class ShareItem:
    id: str
    label: str
    phrase: str
    gives_light: bool = False
    helps_listen: bool = False
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.memes["confusion"] < THRESHOLD:
            continue
        sig = ("confusion", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        out.append("__confusion__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared"):
        sig = ("settle",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.characters():
                kid.memes["joy"] += 1
                kid.memes["confusion"] = 0.0
            out.append("__settled__")
    return out


CAUSAL_RULES = [Rule("confusion", "social", _r_confusion), Rule("settle", "social", _r_settle)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SOUND_MIN]


def reasonableness_gate(noise: Noise, share: ShareItem) -> bool:
    return noise.sound_effect and share.helps_listen


def predict_mistake(world: World, noise_id: str) -> dict:
    sim = world.copy()
    _do_noise(sim, sim.get("noise"), narrate=False)
    return {
        "confusion": sum(k.memes["confusion"] for k in sim.characters()),
        "danger": sim.get("dock").meters["danger"],
    }


def _do_noise(world: World, noise: Entity, narrate: bool = True) -> None:
    noise.meters["heard"] += 1
    for kid in world.characters():
        kid.memes["confusion"] += 1
    propagate(world, narrate=narrate)


def set_scene(world: World, harbor: Harbor, kid1: Entity, kid2: Entity) -> None:
    world.say(
        f"On the eve of the lantern festival, {kid1.id} and {kid2.id} turned the dock "
        f"into {harbor.name}. {harbor.detail}"
    )
    world.say(
        f"The waves went {harbor.sound_word}, and the little ship rope creaked like a tune."
    )


def hear_sound(world: World, kid: Entity, noise: Noise) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"Then came a sudden sound: {noise.sound_effect} {noise.mistaken_for}. "
        f"{kid.id} froze and listened again."
    )
    world.say(f'"That sounded {noise.label}," {kid.id} whispered.')


def correct_mistake(world: World, friend: Entity, kid: Entity, noise: Noise, item: ShareItem) -> None:
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} leaned closer and smiled. \"No, that was only the {noise.source}. "
        f"Listen -- when we share {item.label}, we can check safely together.\""
    )


def share_and_check(world: World, a: Entity, b: Entity, item: ShareItem, noise: Noise) -> None:
    world.facts["shared"] = True
    a.meters["holding"] += 1
    b.meters["holding"] += 1
    if item.helps_listen:
        a.memes["calm"] += 1
        b.memes["calm"] += 1
    world.say(
        f"{a.id} held up {item.phrase}, and {b.id} held the other end. "
        f"They listened together, and the sound turned out to be just {noise.source}."
    )


def brighten(world: World, a: Entity, b: Entity, light: ShareItem, harbor: Harbor) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"Next, they shared {light.phrase} so the deck glowed gold. "
        f"With the bright light, the tiny harbor looked brave instead of mistaken."
    )
    world.say(
        f"The evening breeze tickled the flags, and the children went on with their pirate game."
    )


def ending(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"By bedtime, {a.id} and {b.id} were laughing at how one little sound had fooled them. "
        f"They shared the gear, solved the mystery, and sailed home under the purple eve sky."
    )


def tell(harbor: Harbor, noise: Noise, shared_item: ShareItem, light: ShareItem,
         hero: str = "Eve", hero_type: str = "girl",
         mate: str = "Finn", mate_type: str = "boy",
         parent: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=hero, kind="character", type=hero_type, role="leader"))
    b = world.add(Entity(id=mate, kind="character", type=mate_type, role="mate"))
    p = world.add(Entity(id=parent, kind="character", type="mother" if parent == "mother" else "father", role="parent"))
    dock = world.add(Entity(id="dock", type="place", label="the dock"))
    world.facts["dock"] = dock

    set_scene(world, harbor, a, b)
    world.para()
    hear_sound(world, a, noise)
    predict_mistake(world, noise.id)
    correct_mistake(world, b, a, noise, shared_item)
    share_and_check(world, a, b, shared_item, noise)
    world.para()
    brighten(world, a, b, light, harbor)
    ending(world, a, b)

    world.facts.update(hero=a, mate=b, parent=p, harbor=harbor, noise=noise,
                       shared_item=shared_item, light=light, shared=True,
                       outcome="shared")
    return world


HARBORS = {
    "harbor": Harbor(
        id="harbor",
        name="a little pirate harbor",
        detail="A lantern boat bobbed at the pier, and the captain's map rested on a barrel.",
        sound_word="swish-swish",
        tags={"pirate", "eve"},
    ),
    "cove": Harbor(
        id="cove",
        name="a quiet moon cove",
        detail="A wooden sign pointed to the treasure cove, and gulls watched from the mast.",
        sound_word="lap-lap",
        tags={"pirate", "eve"},
    ),
}

NOISES = {
    "cycle": Noise(
        id="cycle",
        label="mistaken",
        source="the cycle wheel",
        sound_effect="whirr-whirr",
        mistaken_for="by the ropes",
        tags={"cycle", "mistaken", "sound"},
    ),
    "chain": Noise(
        id="chain",
        label="mistaken",
        source="the chain on the little cycle",
        sound_effect="clink-clink",
        mistaken_for="near the barrels",
        tags={"cycle", "mistaken", "sound"},
    ),
    "sail": Noise(
        id="sail",
        label="mistaken",
        source="the sail snapping in the wind",
        sound_effect="flap-flap",
        mistaken_for="above the mast",
        tags={"mistaken", "sound"},
    ),
}

SHARES = {
    "map": ShareItem(
        id="map",
        label="the map",
        phrase="the map",
        helps_listen=True,
        tags={"sharing"},
    ),
    "lantern": ShareItem(
        id="lantern",
        label="the lantern",
        phrase="the lantern",
        gives_light=True,
        tags={"sharing"},
    ),
    "spyglass": ShareItem(
        id="spyglass",
        label="the spyglass",
        phrase="the spyglass",
        helps_listen=True,
        tags={"sharing"},
    ),
}

RESPONSES = {
    "listen": Response(
        id="listen",
        sense=3,
        power=3,
        text="held still, listened closely, and found the real source of the sound",
        fail="tried to listen, but the noise kept echoing and felt too confusing",
        qa_text="held still and listened closely until the real source of the sound was clear",
        tags={"sound", "sharing"},
    ),
    "share_map": Response(
        id="share_map",
        sense=3,
        power=3,
        text="shared the map and used it to check the dock together",
        fail="shared the map, but the clues were still too hard to read",
        qa_text="shared the map and checked the dock together",
        tags={"sharing"},
    ),
    "share_lantern": Response(
        id="share_lantern",
        sense=3,
        power=4,
        text="shared the lantern and lit the deck so they could look safely",
        fail="shared the lantern, but the light was too weak to settle the worry",
        qa_text="shared the lantern and lit the deck so they could look safely",
        tags={"sharing", "light"},
    ),
    "tap_mast": Response(
        id="tap_mast",
        sense=1,
        power=1,
        text="tapped the mast and made the confusion worse",
        fail="tapped the mast and only made more noise",
        qa_text="tapped the mast",
        tags={"bad"},
    ),
}

HEROES = ["Eve", "Nina", "Mira", "Pia", "Tia"]
MATES = ["Finn", "Tom", "Bram", "Jett", "Leo"]


@dataclass
class StoryParams:
    harbor: str
    noise: str
    share_item: str
    light: str
    hero: str
    hero_type: str
    mate: str
    mate_type: str
    parent: str
    response: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hid in HARBORS:
        for nid, noise in NOISES.items():
            for sid, item in SHARES.items():
                if reasonableness_gate(noise, item):
                    combos.append((hid, nid, sid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld about eve, a cycle, a mistaken sound, and sharing.")
    ap.add_argument("--harbor", choices=HARBORS)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--share-item", choices=SHARES)
    ap.add_argument("--light", choices=SHARES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--mate")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.noise and args.share_item:
        n, s = NOISES[args.noise], SHARES[args.share_item]
        if not reasonableness_gate(n, s):
            raise StoryError("No story: the sound and sharing item do not fit together well enough.")
    combos = [c for c in valid_combos()
              if (args.harbor is None or c[0] == args.harbor)
              and (args.noise is None or c[1] == args.noise)
              and (args.share_item is None or c[2] == args.share_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    harbor, noise, share_item = rng.choice(sorted(combos))
    light = args.light or rng.choice(sorted(SHARES))
    response = args.response or rng.choice(["listen", "share_map", "share_lantern"])
    hero = args.hero or rng.choice(HEROES)
    mate = args.mate or rng.choice([n for n in MATES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    hero_type = "girl" if hero in {"Eve", "Nina", "Mira", "Pia", "Tia"} else "boy"
    mate_type = "boy"
    return StoryParams(
        harbor=harbor,
        noise=noise,
        share_item=share_item,
        light=light,
        hero=hero,
        hero_type=hero_type,
        mate=mate,
        mate_type=mate_type,
        parent=parent,
        response=response,
    )


def generate(params: StoryParams) -> StorySample:
    if params.harbor not in HARBORS:
        raise StoryError("Invalid harbor.")
    if params.noise not in NOISES:
        raise StoryError("Invalid noise.")
    if params.share_item not in SHARES:
        raise StoryError("Invalid sharing item.")
    if params.light not in SHARES:
        raise StoryError("Invalid light item.")
    if params.response not in RESPONSES:
        raise StoryError("Invalid response.")
    world = tell(
        HARBORS[params.harbor],
        NOISES[params.noise],
        SHARES[params.share_item],
        SHARES[params.light],
        hero=params.hero,
        hero_type=params.hero_type,
        mate=params.mate,
        mate_type=params.mate_type,
        parent=params.parent,
    )
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
    return [
        'Write a pirate-tale story for a young child that includes the words "eve", "cycle", and "mistaken".',
        f"Tell a story where {f['hero'].id} hears a mistaken sound by the harbor, then shares tools with {f['mate'].id} to check what it was.",
        f"Write a gentle pirate story with sound effects and sharing, ending with a calm eve at the dock.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mate, noise, item = f["hero"], f["mate"], f["noise"], f["shared_item"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {mate.id}, who are playing a pirate game on the eve at the harbor."),
        ("What sound did they hear?",
         f"They heard {noise.sound_effect}, which sounded {noise.label} at first. It was only {noise.source}."),
        ("How did they solve the mistake?",
         f"They shared {item.phrase} and checked together. Sharing helped them calm down and find the real source of the sound."),
        ("How did the story end?",
         f"It ended with a safe, happy pirate evening under the eve sky. The children kept playing after they learned what the sound really was."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["noise"].tags) | set(f["shared_item"].tags) | {"sharing", "sound"}
    qa: list[tuple[str, str]] = []
    if "cycle" in tags:
        qa.append(("What is a cycle?",
                    "A cycle is a bicycle or bike with wheels. It can make whirring or clinking sounds when it moves."եպ to=functions.emit_python_file code
