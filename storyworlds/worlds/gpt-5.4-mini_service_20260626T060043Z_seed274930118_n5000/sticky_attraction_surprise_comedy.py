#!/usr/bin/env python3
"""
A standalone storyworld for a sticky attraction surprise comedy.

Premise:
A child is delighted by a carnival toy that sticks to things because of static
sparkles. The fun goes wrong when the toy becomes irresistibly attracted to a
metal statue and snatches a snack tray instead. A surprise fix turns the trouble
into a silly performance.

This world models:
- physical meters: stickiness, attraction, mess, sparkle
- emotional memes: delight, surprise, embarrassment, amusement, relief
- a small causal loop: play -> surprise mishap -> comic repair -> happy ending
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    glove: object | None = None
    hero: object | None = None
    metal: object | None = None
    parent: object | None = None
    snack: object | None = None
    spoon: object | None = None
    toy_ent: object | None = None
    def noun(self) -> str:
        return self.label or self.type or self.id

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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


class World:
    def __init__(self, setting: "Setting") -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


@dataclass
class Setting:
    place: str
    indoors: bool
    vibe: str
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


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    attraction_target: str
    sticky_kind: str
    surprise_source: str
    fix: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    setting: str
    toy: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "carnival": Setting(place="the carnival", indoors=False, vibe="bright and noisy"),
    "playroom": Setting(place="the playroom", indoors=True, vibe="small and busy"),
    "market": Setting(place="the market", indoors=False, vibe="crowded and cheerful"),
}

TOYS = {
    "sticky_balloon": Toy(
        id="sticky_balloon",
        label="sticky balloon",
        phrase="a shiny sticky balloon with a ribbon",
        attraction_target="metal_statue",
        sticky_kind="static",
        surprise_source="a silly float",
        fix="a cloth glove",
    ),
    "snappy_magnet": Toy(
        id="snappy_magnet",
        label="snappy magnet toy",
        phrase="a tiny magnet toy on a string",
        attraction_target="metal_cookie_tin",
        sticky_kind="magnetic",
        surprise_source="a snack tray",
        fix="a wooden spoon",
    ),
    "glitter_scooper": Toy(
        id="glitter_scooper",
        label="glitter scooper",
        phrase="a glitter scooper with a sticky handle",
        attraction_target="metal_bucket",
        sticky_kind="tacky",
        surprise_source="a jelly cup",
        fix="a paper napkin",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Tia", "Nora", "Ivy", "Ruby"]
BOY_NAMES = ["Ben", "Toby", "Leo", "Max", "Owen", "Zeke"]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def sticky_is_fun(world: World, child: Entity, toy: Toy) -> None:
    child.memes["delight"] += 1
    world.say(
        f"{child.id} found {toy.phrase} and grinned. "
        f"It was the kind of toy that made little hands feel clever."
    )
    world.say(
        f"{child.pronoun().capitalize()} loved how the sticky part clung to fingers "
        f"for a moment and then let go with a tiny pop."
    )


def attraction_notice(world: World, child: Entity, toy: Toy) -> None:
    world.say(
        f"Near {world.setting.place}, there was a shiny metal thing that seemed to "
        f"call the toy over like a funny whisper."
    )
    world.say(
        f"{toy.label.capitalize()} had a strong attraction to it, as if the two "
        f"were long-lost cousins at a party."
    )


def surprise_mishap(world: World, child: Entity, parent: Entity, toy: Toy) -> None:
    toy_ent = world.get(toy.id)
    target = world.get(toy.attraction_target)
    snack = world.get("snack_tray")

    toy_ent.meters["attraction"] += 1
    toy_ent.meters["stickiness"] += 1
    target.meters["shine"] += 1

    child.memes["surprise"] += 1
    child.memes["embarrassment"] += 1
    parent.memes["surprise"] += 1
    parent.memes["amusement"] += 1

    snack.carried_by = None
    snack.meters["tilted"] += 1
    snack.meters["mess"] += 1

    world.say(
        f"Then came a surprise. The toy zipped straight toward {target.noun()}, "
        f"and in the same silly tug it hooked the snack tray."
    )
    world.say(
        f"Crackers skittered one way, napkins fluttered the other, and {child.id} "
        f"blinked in stunned silence."
    )


def comic_fix(world: World, child: Entity, parent: Entity, toy: Toy) -> None:
    glove = world.get("glove")
    spoon = world.get("spoon")
    parent.memes["relief"] += 1
    child.memes["relief"] += 1
    child.memes["amusement"] += 1

    glove.carried_by = child.id
    spoon.carried_by = parent.id

    world.say(
        f"{parent.pronoun().capitalize()} laughed first and said, "
        f"\"Let's make the sticky attraction useful.\""
    )
    world.say(
        f"They used {glove.noun()} and {spoon.noun()} like a tiny rescue team, "
        f"and soon the toy was safely hanging from a banner instead of stealing snacks."
    )
    world.say(
        f"{child.id} laughed so hard that {child.pronoun('possessive')} cheeks went pink, "
        f"and the surprise turned into a silly game for everyone nearby."
    )


def ending_image(world: World, child: Entity, toy: Toy) -> None:
    world.say(
        f"By the end, {child.id} was proudly showing off {toy.label}, the snack tray "
        f"was back in place, and even the metal statue looked like it was smiling."
    )
    world.say(
        f"The whole spot at {world.setting.place} felt bright again, with laughter "
        f"still hanging in the air like confetti."
    )


def make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    toy = _safe_lookup(TOYS, params.toy)
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="parent",
    ))
    toy_ent = world.add(Entity(
        id=toy.id,
        type="toy",
        label=toy.label,
        phrase=toy.phrase,
        owner=hero.id,
        meters={"stickiness": 1.0},
    ))
    metal = world.add(Entity(
        id=toy.attraction_target,
        type="thing",
        label=toy.attraction_target.replace("_", " "),
        meters={"shine": 1.0},
    ))
    snack = world.add(Entity(
        id="snack_tray",
        type="thing",
        label="snack tray",
        meters={"mess": 0.0, "tilted": 0.0},
    ))
    glove = world.add(Entity(id="glove", type="tool", label=toy.fix))
    spoon = world.add(Entity(id="spoon", type="tool", label="a wooden spoon"))

    world.facts.update(
        hero=hero,
        parent=parent,
        toy=toy,
        toy_ent=toy_ent,
        metal=metal,
        snack=snack,
        glove=glove,
        spoon=spoon,
    )

    world.say(
        f"{hero.id} was a little {hero.type} who loved funny things that stuck "
        f"to other things."
    )
    world.say(
        f"At {setting.place}, {hero.id} found {toy.phrase}, and the day already felt "
        f"like it might wobble into a joke."
    )

    world.para()
    sticky_is_fun(world, hero, toy)
    attraction_notice(world, hero, toy)

    world.para()
    surprise_mishap(world, hero, parent, toy)

    world.para()
    comic_fix(world, hero, parent, toy)
    ending_image(world, hero, toy)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    toy: Toy = _safe_fact(world, f, "toy")
    hero: Entity = _safe_fact(world, f, "hero")
    return [
        f'Write a short comedy story for a young child about {hero.id} and a '
        f'"{toy.label}" that gets into a sticky attraction surprise.',
        f"Tell a cheerful story where {hero.id} finds {toy.phrase} at "
        f"{world.setting.place} and something silly happens because of attraction.",
        f"Write a funny, gentle story for a small child that ends with laughter "
        f"after a sticky toy causes a surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    toy: Toy = _safe_fact(world, f, "toy")

    return [
        QAItem(
            question=f"What did {hero.id} find at {world.setting.place}?",
            answer=f"{hero.id} found {toy.phrase}. It was sticky and looked fun to play with.",
        ),
        QAItem(
            question=f"Why was the toy such a surprise?",
            answer=(
                f"It had a strong attraction to {toy.attraction_target.replace('_', ' ')}, "
                f"so it zipped there in a silly rush and tugged the snack tray along too."
            ),
        ),
        QAItem(
            question=f"How did {parent.pronoun('subject').capitalize()} help fix the mess?",
            answer=(
                f"{parent.pronoun('subject').capitalize()} helped by using {toy.fix} and a "
                f"careful joke of a plan, so the toy could stay useful without causing a mess."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    toy: Toy = _safe_fact(world, f, "toy")
    return [
        QAItem(
            question="What does sticky mean?",
            answer="Sticky things cling to other things for a little while, like tape or glue.",
        ),
        QAItem(
            question="What is attraction in this story?",
            answer=(
                "Attraction means something being strongly pulled toward something else, "
                "like a magnet or a shiny object drawing attention."
            ),
        ),
        QAItem(
            question="Why can surprise make a story funny?",
            answer=(
                "Surprise can be funny when something unexpected happens in a harmless, silly way "
                "that makes people laugh instead of worry."
            ),
        ),
        QAItem(
            question=f"Why was {toy.label} easy to laugh about?",
            answer=(
                f"It was playful and a little bit wild, so when it caused trouble it felt more "
                f"like a comedy joke than a serious problem."
            ),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.carried_by:
            bits.append(f"carried_by={ent.carried_by}")
        lines.append(f"  {ent.id} ({ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(carnival). place(playroom). place(market).

toy(sticky_balloon). toy(snappy_magnet). toy(glitter_scooper).

setting_has(carnival, sticky_balloon).
setting_has(playroom, glitter_scooper).
setting_has(market, snappy_magnet).

attraction(sticky_balloon, metal_statue).
attraction(snappy_magnet, metal_cookie_tin).
attraction(glitter_scooper, metal_bucket).

fix(sticky_balloon, cloth_glove).
fix(snappy_magnet, wooden_spoon).
fix(glitter_scooper, paper_napkin).

surprise(sticky_balloon, float).
surprise(snappy_magnet, snack_tray).
surprise(glitter_scooper, jelly_cup).

valid_story(S, T) :- setting_has(S, T), attraction(T, _), surprise(T, _), fix(T, _).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("place", s))
        lines.append(asp.fact("setting_has", s, next(iter([t for t in TOYS if s in {
            "carnival": {"sticky_balloon"},
            "playroom": {"glitter_scooper"},
            "market": {"snappy_magnet"},
        }[s]]))))
    for t in TOYS.values():
        lines.append(asp.fact("toy", t.id))
        lines.append(asp.fact("attraction", t.id, t.attraction_target))
        lines.append(asp.fact("fix", t.id, t.fix))
        lines.append(asp.fact("surprise", t.id, t.surprise_source))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, t) for s in SETTINGS for t in TOYS if {
        "carnival": {"sticky_balloon"},
        "playroom": {"glitter_scooper"},
        "market": {"snappy_magnet"},
    }[s] == {t}}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [
        ("carnival", "sticky_balloon"),
        ("playroom", "glitter_scooper"),
        ("market", "snappy_magnet"),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sticky attraction surprise comedy storyworld.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--toy", choices=sorted(TOYS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "setting", None) and getattr(args, "toy", None):
        if (getattr(args, "setting", None), getattr(args, "toy", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "name", None) is None:
        pass
    choices = valid_combos()
    if getattr(args, "setting", None):
        choices = [c for c in choices if c[0] == getattr(args, "setting", None)]
    if getattr(args, "toy", None):
        choices = [c for c in choices if c[1] == getattr(args, "toy", None)]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, toy = rng.choice(choices)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, toy=toy, hero_name=name, hero_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print("\n".join(f"{a} {b}" for a, b in combos))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, (setting, toy) in enumerate(valid_combos()):
            params = StoryParams(
                setting=setting,
                toy=toy,
                hero_name=_safe_lookup(GIRL_NAMES, i % len(GIRL_NAMES)),
                hero_type="girl" if i % 2 == 0 else "boy",
                parent_type="mother" if i % 2 == 0 else "father",
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.toy} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
