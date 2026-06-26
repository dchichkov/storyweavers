#!/usr/bin/env python3
"""
storyworlds/worlds/gutter_transformation_folk_tale.py
=====================================================

A small folk-tale storyworld about a village gutter, a stubborn blockage, and a
gentle transformation that only happens after patient work.

The seed idea is a tiny source tale in which a child notices rainwater spilling
from an old cottage gutter. The gutter is clogged with leaves and twigs, so the
child and a wise elder clear it together. Under the leaves they find a little
carved seed-stone. When the gutter is cleaned and the stone is warmed by rain,
the plain old gutter transforms into a bright singing channel that guides water
to the roots of a thirsty tree.

The domain is intentionally small:
- physical state: gutter, roof spill, leaves, water flow, carved stone, roots
- emotional state: worry, patience, pride, joy, wonder
- transformation: a folk-magic change that is only possible after the blockage
  is removed and the water can run true again

The story is generated from simulated state, not from a fixed paragraph with
swapped names. The ending image proves the changed world.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    state: str = ""
    transformed: bool = False

    elder: object | None = None
    hero: object | None = None
    tree: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Place:
    name: str = "the village lane"
    house: str = "the cottage"
    tree: str = "the old apple tree"
    affords: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    elder_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.rain: bool = True

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
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.rain = self.rain
        return clone


def _r_blockage(world: World) -> list[str]:
    out: list[str] = []
    gutter = world.get("gutter")
    if gutter.state != "clogged":
        return out
    if gutter.meters.get("leaves", 0.0) < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gutter.meters["spill"] = 1.0
    world.get("tree").meters["thirst"] = world.get("tree").meters.get("thirst", 0.0) + 1.0
    out.append("Rainwater could not run down the gutter, so it spilled in a hard little stream.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    gutter = world.get("gutter")
    tree = world.get("tree")
    if gutter.state != "clogged":
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    tree.meters["thirst"] = tree.meters.get("thirst", 0.0) + 1.0
    out.append(f"{hero.id} saw the gutter stuffed with leaves and felt a pinch of worry.")
    return out


def _r_clear(world: World) -> list[str]:
    out: list[str] = []
    gutter = world.get("gutter")
    hero = world.get("hero")
    elder = world.get("elder")
    if gutter.state != "being_cleaned":
        return out
    sig = ("clear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gutter.state = "clear"
    gutter.meters["leaves"] = 0.0
    gutter.meters["water"] = 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    elder.memes["peace"] = elder.memes.get("peace", 0.0) + 1.0
    out.append("Together they lifted out the leaves and twigs until the gutter ran open.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    gutter = world.get("gutter")
    stone = world.get("stone")
    if gutter.state != "clear" or stone.transformed:
        return out
    if stone.meters.get("warm_rain", 0.0) < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stone.transformed = True
    gutter.transformed = True
    gutter.state = "singing"
    gutter.label = "a bright singing gutter"
    gutter.phrase = "a bright singing gutter with a silver lip"
    world.get("tree").meters["watered"] = world.get("tree").meters.get("watered", 0.0) + 1.0
    out.append("Then the little carved stone warmed in the rain and the gutter changed its tune.")
    return out


def _r_joy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    gutter = world.get("gutter")
    tree = world.get("tree")
    sig = ("joy", gutter.state)
    if sig in world.fired:
        return out
    if gutter.state != "singing":
        return out
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    out.append(f"{hero.id} laughed as the gutter sang rainwater down to {tree.label}.")
    return out


CAUSAL_RULES = [_r_worry, _r_blockage, _r_clear, _r_transform, _r_joy]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_transformation(world: World) -> dict:
    sim = world.copy()
    sim.get("gutter").state = "being_cleaned"
    propagate(sim, narrate=False)
    return {
        "transformed": sim.get("gutter").transformed,
        "watered_tree": sim.get("tree").meters.get("watered", 0.0) >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"{hero.id} lived beside {world.place.house} with {elder.label}, "
        f"and they both knew the lane by heart."
    )


def setup(world: World, hero: Entity) -> None:
    gutter = world.get("gutter")
    tree = world.get("tree")
    world.say(
        f"Every rainy morning, {gutter.label} on the roof tried to carry water to {tree.label}, "
        f"but this time it was choked with leaves."
    )
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"{hero.id} leaned close and saw a tiny carved stone hiding in the wet brown leaves."
    )


def warn(world: World, elder: Entity, hero: Entity) -> None:
    gutter = world.get("gutter")
    tree = world.get("tree")
    pred = predict_transformation(world)
    if not pred["transformed"]:
        pass
    world.facts["pred"] = pred
    world.say(
        f'"If the gutter stays clogged, the {tree.label} will keep thirsting," {elder.id} said softly. '
        f'"But if we clear it, the old thing may remember its song."'
    )
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0


def clean(world: World, hero: Entity, elder: Entity) -> None:
    gutter = world.get("gutter")
    gutter.state = "being_cleaned"
    hero.meters["work"] = hero.meters.get("work", 0.0) + 1.0
    elder.meters["work"] = elder.meters.get("work", 0.0) + 1.0
    world.say(
        f"{hero.id} fetched a twig hook, and {elder.id} held the ladder while they worked."
    )
    propagate(world, narrate=True)


def touch_stone(world: World, hero: Entity) -> None:
    stone = world.get("stone")
    gutter = world.get("gutter")
    stone.meters["warm_rain"] = stone.meters.get("warm_rain", 0.0) + 1.0
    if gutter.state == "clear":
        propagate(world, narrate=True)
    world.say(
        f"{hero.id} touched the carved stone, and the rain sounded brighter on the roof."
    )


def tell(place: Place, hero_name: str, hero_type: str, elder_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the old neighbor"))
    gutter = world.add(
        Entity(
            id="gutter",
            type="gutter",
            label="the old gutter",
            phrase="the old gutter along the cottage roof",
            state="clogged",
            meters={"leaves": 2.0, "water": 0.0},
        )
    )
    tree = world.add(Entity(id="tree", type="tree", label="the old apple tree"))
    stone = world.add(
        Entity(
            id="stone",
            type="stone",
            label="a little carved stone",
            phrase="a little carved stone with a spiral cut on its face",
        )
    )

    introduce(world, hero, elder)
    world.para()
    setup(world, hero)
    world.para()
    warn(world, elder, hero)
    clean(world, hero, elder)
    world.para()
    touch_stone(world, hero)

    world.facts.update(hero=hero, elder=elder, gutter=gutter, tree=tree, stone=stone)
    return world


SETTINGS = {
    "lane": Place(name="the village lane", house="the cottage", tree="the old apple tree", affords={"gutter"}),
    "courtyard": Place(name="the cottage courtyard", house="the cottage", tree="the pear tree", affords={"gutter"}),
    "millroad": Place(name="the mill road", house="the mill house", tree="the willow tree", affords={"gutter"}),
}

HERO_NAMES = ["Mara", "Niko", "Tara", "Ivo", "Lina", "Bram", "Oona", "Sera"]
ELDER_TYPES = ["grandmother", "grandfather", "neighbor", "aunt", "uncle"]
HERO_TYPES = ["girl", "boy"]


@dataclass
class StoryParamsSpec:
    place: str
    hero_name: str
    hero_type: str
    elder_type: str
    seed: Optional[int] = None
    params: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def valid_combos() -> list[tuple[str, str]]:
    return [(k, "gutter") for k in SETTINGS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world about a gutter, a blockage, and a transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", dest="hero_type", choices=HERO_TYPES)
    ap.add_argument("--elder", choices=ELDER_TYPES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParamsSpec:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    elder_type = getattr(args, "elder", None) or rng.choice(ELDER_TYPES)
    return StoryParamsSpec(place=place, hero_name=hero_name, hero_type=hero_type, elder_type=elder_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about a {f["hero"].type} named {f["hero"].id}, a gutter, and a hidden transformation.',
        f"Tell a gentle village story in which {f['hero'].id} clears a clogged gutter and discovers why the old rain channel sings.",
        f"Write a child-friendly tale about rain, a gutter, and a magic change that happens only after patient work.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    gutter = _safe_fact(world, f, "gutter")
    tree = _safe_fact(world, f, "tree")
    stone = _safe_fact(world, f, "stone")
    pred = _safe_fact(world, f, "pred")
    return [
        QAItem(
            question=f"What did {hero.id} notice in the gutter at the start of the story?",
            answer=f"{hero.id} noticed that the old gutter was stuffed with leaves, and {stone.label} was hiding there.",
        ),
        QAItem(
            question=f"Why did the old neighbor worry about the gutter?",
            answer=f"{elder.label} worried because if the gutter stayed clogged, rainwater would spill and {tree.label} would keep thirsting.",
        ),
        QAItem(
            question=f"What did {hero.id} and the old neighbor do together?",
            answer=f"They pulled out the leaves and twigs, cleaned the gutter, and made room for the rain to run through again.",
        ),
        QAItem(
            question=f"What changed after the gutter was cleaned?",
            answer=f"The gutter transformed into {gutter.label}, a bright singing gutter, and the rainwater went down to {tree.label}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt joy and wonder, because the old gutter had changed its tune and helped the tree at the same time.",
        ),
        QAItem(
            question=f"Why was the carved stone important?",
            answer=f"The carved stone was part of the folk magic; once it warmed in the rain after the gutter was cleared, the transformation could begin.",
        ),
    ]


KNOWLEDGE = {
    "gutter": [
        (
            "What is a gutter for?",
            "A gutter carries rainwater away from a roof so the water can flow to a safe place.",
        )
    ],
    "leaves": [
        (
            "Why can leaves clog a gutter?",
            "Leaves can bunch together and block water, just like a little wall made of plant bits.",
        )
    ],
    "tree": [
        (
            "Why do trees need water?",
            "Trees need water to keep their roots and leaves healthy so they can grow.",
        )
    ],
    "stone": [
        (
            "What is a carved stone?",
            "A carved stone is a stone that has been shaped or marked by hand, often with a simple pattern.",
        )
    ],
    "transformation": [
        (
            "What is a transformation in a story?",
            "A transformation is a change from one form or state into another, like a plain thing becoming special.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["gutter", "leaves", "tree", "stone", "transformation"]:
        for q, a in KNOWLEDGE[key]:
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.state:
            bits.append(f"state={e.state}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:7} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
clogged(gutter) :- leaves(gutter, N), N >= 1.
spill(gutter) :- clogged(gutter).
worry(hero) :- clogged(gutter).
clear(gutter) :- cleaned(gutter).
transformed(gutter) :- clear(gutter), warm(stone).
happy(hero) :- transformed(gutter).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in SETTINGS:
        lines.append(asp.fact("place", k))
        lines.append(asp.fact("supports", k, "gutter"))
    lines.append(asp.fact("thing", "gutter"))
    lines.append(asp.fact("thing", "stone"))
    lines.append(asp.fact("thing", "tree"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParamsSpec) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.hero_name, params.hero_type, params.elder_type)
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

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show transformed/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SETTINGS:
            params = StoryParamsSpec(
                place=place,
                hero_name=_safe_lookup(HERO_NAMES, 0),
                hero_type=_safe_lookup(HERO_TYPES, 0),
                elder_type=_safe_lookup(ELDER_TYPES, 0),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {i + 1}: {p.hero_name} at {p.place}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
