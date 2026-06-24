#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a keen suburban sharing moment that goes
wrong in a believable way and ends with a bad ending image.

The seed idea:
- A keen child in a suburban neighborhood wants to share something nice.
- The sharing is well-meant, but the item is too fragile / too limited / too
  quickly consumed.
- The ending is not a rescue; it lands on a small, honest disappointment.
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
# Basic model
# ---------------------------------------------------------------------------

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
    shares: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    gift: object | None = None
    neighbor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    place: str
    suburban: bool = True
    afford_share: set[str] = field(default_factory=set)
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
class Gift:
    id: str
    label: str
    phrase: str
    kind: str
    fragile: bool = False
    limited: bool = False
    share_method: str = "pass it around"
    ending: str = "Soon there was not enough left"
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
    gift: str
    name: str
    gender: str
    neighbor: str
    seed: Optional[int] = None
    params: object | None = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "suburban_stoop": Setting(place="the suburban front stoop", suburban=True, afford_share={"cookie", "stickers"}),
    "suburban_backyard": Setting(place="the suburban backyard", suburban=True, afford_share={"lemonade", "chalk"}),
    "suburban_sidewalk": Setting(place="the suburban sidewalk", suburban=True, afford_share={"crackers", "balloons"}),
}

GIFTS = {
    "cookie": Gift(
        id="cookie",
        label="cookie",
        phrase="a neat plate of small cookies",
        kind="food",
        fragile=False,
        limited=True,
        share_method="break it into pieces",
        ending="Only crumbs stayed on the plate",
    ),
    "stickers": Gift(
        id="stickers",
        label="stickers",
        phrase="a shiny sheet of stickers",
        kind="paper",
        fragile=True,
        limited=True,
        share_method="try to split the sheet",
        ending="the sheet was torn and bent",
    ),
    "lemonade": Gift(
        id="lemonade",
        label="lemonade",
        phrase="a little pitcher of lemonade",
        kind="drink",
        fragile=False,
        limited=True,
        share_method="pour cups for everyone",
        ending="the pitcher came up empty",
    ),
    "chalk": Gift(
        id="chalk",
        label="chalk",
        phrase="a box of bright sidewalk chalk",
        kind="toy",
        fragile=True,
        limited=True,
        share_method="hand out the best colors first",
        ending="the sharp corners wore down fast",
    ),
    "crackers": Gift(
        id="crackers",
        label="crackers",
        phrase="a tin of buttery crackers",
        kind="food",
        fragile=False,
        limited=True,
        share_method="pass the tin around",
        ending="the tin echoed with only one last cracker",
    ),
    "balloons": Gift(
        id="balloons",
        label="balloons",
        phrase="a bundle of bright balloons",
        kind="party",
        fragile=True,
        limited=True,
        share_method="tie one for each child",
        ending="one balloon slipped and drifted away",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Eli", "Ava", "Finn", "Ivy", "Theo"]
NEIGHBORS = ["neighbor kid", "cousin", "friend", "little sister", "little brother"]
TRAITS = ["keen", "careful", "bright", "hopeful", "eager"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def can_share(gift: Gift) -> bool:
    return gift.limited or gift.fragile


def reasonableness_gate(setting: Setting, gift: Gift) -> bool:
    return setting.suburban and can_share(gift)


def setting_line(setting: Setting) -> str:
    if "stoop" in setting.place:
        return "The houses were close together, and the afternoon felt quiet and neighborly."
    if "backyard" in setting.place:
        return "Fences, porch steps, and patchy grass made the yard feel small and familiar."
    return "Cars rolled slowly by, and the sidewalk felt like the center of the block."


def intro(world: World, child: Entity, gift: Entity) -> None:
    world.say(
        f"{child.id} was a keen little {child.type} who liked the tidy, ordinary way "
        f"the suburban street shared things."
    )
    world.say(f"{child.pronoun('possessive').capitalize()} favorite thing that day was {gift.phrase}.")


def desire(world: World, child: Entity, gift: Entity) -> None:
    child.memes["want"] = child.memes.get("want", 0) + 1
    world.say(
        f"{child.id} wanted to share {gift.pronoun('object')} right away, because "
        f"{child.pronoun('subject')} liked seeing other kids smile."
    )


def sharing_turn(world: World, child: Entity, neighbor: Entity, gift: Entity) -> None:
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    world.say(setting_line(world.setting))
    world.say(
        f"{child.id} sat on the {world.setting.place.split()[-1]} and said, "
        f'"You can have some too."'
    )
    world.say(
        f"They tried to {gift.phrase and _safe_lookup(GIFTS, gift.id).share_method}."
    )


def bad_ending(world: World, child: Entity, neighbor: Entity, gift: Entity) -> None:
    child.memes["sad"] = child.memes.get("sad", 0) + 1
    child.memes["embarrassed"] = child.memes.get("embarrassed", 0) + 1
    if gift.id == "cookie":
        world.say(
            "But the cookies were so small that each piece vanished in one bite, "
            "and nobody got a second one."
        )
    elif gift.id == "stickers":
        world.say(
            "But the stickers tore as soon as they were split, and the shiny sheet "
            "looked tired and crooked."
        )
    elif gift.id == "lemonade":
        world.say(
            "But the lemonade ran out before everyone had a full cup, and the pitcher "
            "bumped softly against the empty counter."
        )
    elif gift.id == "chalk":
        world.say(
            "But the chalk snapped into short stubs, and the bright colors got dusty "
            "and mixed together."
        )
    elif gift.id == "crackers":
        world.say(
            "But the crackers were gone too fast, and the tin sounded hollow when it was tipped."
        )
    else:
        world.say(
            "But one balloon slipped free, and the rest were no longer enough to make the game fair."
        )
    world.say(
        f"{neighbor.id} looked disappointed, and {child.id} stared at the small mess of {gift.label}."
    )


def ending_image(world: World, child: Entity, gift: Entity) -> None:
    world.say(
        f"In the end, {child.id} held the last little bit of {gift.label} while the suburban afternoon went on."
    )


def tell(setting: Setting, gift_cfg: Gift, name: str, gender: str, neighbor_kind: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    neighbor = world.add(Entity(id="Neighbor", kind="character", type=neighbor_kind, label=neighbor_kind))
    gift = world.add(Entity(id="gift", kind="thing", type=gift_cfg.kind, label=gift_cfg.label, phrase=gift_cfg.phrase, owner=child.id, shares=True))

    intro(world, child, gift)
    world.para()
    desire(world, child, gift)
    world.say(f"{child.id} chose to share it anyway, even though it was {gift_cfg.ending.lower()}.")
    world.say(f"{child.id} tried to {gift_cfg.share_method}.")
    world.para()
    sharing_turn(world, child, neighbor, gift)
    bad_ending(world, child, neighbor, gift)
    world.para()
    ending_image(world, child, gift)

    world.facts.update(child=child, neighbor=neighbor, gift=gift, gift_cfg=gift_cfg, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    gift = _safe_fact(world, f, "gift_cfg")
    return [
        f'Write a short slice-of-life story about a keen suburban child sharing {gift.phrase}.',
        f"Tell a gentle story where {child.id} wants to share a {gift.label}, but the sharing does not go perfectly.",
        f'Write a simple story set in a suburban neighborhood that ends with a disappointing sharing moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, neighbor, gift, setting = f["child"], f["neighbor"], f["gift"], f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a keen little {child.type} in {setting.place}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the {gift.label}?",
            answer=f"{child.id} wanted to share the {gift.label} with {neighbor.label}.",
        ),
        QAItem(
            question=f"How did the sharing end?",
            answer=f"It ended badly because {gift.label}s were limited, so there was not enough for everyone.",
        ),
        QAItem(
            question=f"What was the final image?",
            answer=f"{child.id} was left holding the last little bit of the {gift.label} while the afternoon went on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does suburban mean?",
            answer="Suburban means a neighborhood with homes and streets near a city, often with yards, sidewalks, and close neighbors.",
        ),
        QAItem(
            question="Why can sharing cookies be hard?",
            answer="Sharing cookies can be hard because they get eaten quickly, so there may not be enough for everyone.",
        ),
        QAItem(
            question="Why can stickers be tricky to share?",
            answer="Stickers can be tricky to share because one sheet can tear if people try to split it too many ways.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
#show valid_story/4.

setting(suburban_stoop).
setting(suburban_backyard).
setting(suburban_sidewalk).

suburban(suburban_stoop).
suburban(suburban_backyard).
suburban(suburban_sidewalk).

gift(cookie).
gift(stickers).
gift(lemonade).
gift(chalk).
gift(crackers).
gift(balloons).

shares(cookie).
shares(stickers).
shares(lemonade).
shares(chalk).
shares(crackers).
shares(balloons).

valid(S, G) :- suburban(S), gift(G), shares(G).

valid_story(S, G, N, C) :- valid(S, G), child_name(N), child_type(C).
child_name(mia;leo;nora;eli;ava;finn;ivy;theo).
child_type(girl;boy).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.suburban:
            lines.append(asp.fact("suburban", sid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        if can_share(g):
            lines.append(asp.fact("shares", gid))
    for n in NAMES:
        lines.append(asp.fact("child_name", n.lower()))
    lines.append(asp.fact("child_type", "girl"))
    lines.append(asp.fact("child_type", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((sid, gid) for sid in SETTINGS for gid, g in GIFTS.items() if reasonableness_gate(_safe_lookup(SETTINGS, sid), g))
    cl = asp_valid_combos()
    if set(py) == set(cl):
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(set(py) - set(cl)))
    print("asp only:", sorted(set(cl) - set(py)))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life suburban sharing storyworld with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--neighbor", choices=NEIGHBORS)
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
    combos = [(s, g) for s in SETTINGS for g, gift in GIFTS.items() if reasonableness_gate(_safe_lookup(SETTINGS, s), gift)]
    if getattr(args, "setting", None) and getattr(args, "gift", None) and not reasonableness_gate(_safe_lookup(SETTINGS, getattr(args, "setting", None)), _safe_lookup(GIFTS, getattr(args, "gift", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = [
        (s, g) for s, g in combos
        if (not getattr(args, "setting", None) or s == getattr(args, "setting", None))
        and (not getattr(args, "gift", None) or g == getattr(args, "gift", None))
    ]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_id, gift_id = rng.choice(sorted(choices))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    neighbor = getattr(args, "neighbor", None) or rng.choice(NEIGHBORS)
    return StoryParams(setting=setting_id, gift=gift_id, name=name, gender=gender, neighbor=neighbor)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(GIFTS, params.gift), params.name, params.gender, params.neighbor)
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
        print("\n-- trace --")
        for k, v in sample.world.facts.items():
            if k in {"child", "neighbor", "gift"}:
                continue
            print(f"{k}: {v}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, gift) combos")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for s in SETTINGS:
            for g in GIFTS:
                if reasonableness_gate(_safe_lookup(SETTINGS, s), _safe_lookup(GIFTS, g)):
                    params = StoryParams(setting=s, gift=g, name="Mia", gender="girl", neighbor="friend")
                    samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
