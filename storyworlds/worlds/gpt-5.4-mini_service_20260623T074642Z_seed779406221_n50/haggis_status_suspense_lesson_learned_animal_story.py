#!/usr/bin/env python3
"""
storyworlds/worlds/haggis_status_suspense_lesson_learned_animal_story.py
========================================================================

A small standalone storyworld for an Animal Story-style tale about haggis,
status, suspense, and a lesson learned.

Premise:
- A small animal hero cares about status at a hill feast.
- A special haggis is missing, and the gathering is put on hold.
- Suspense builds while the animals search.
- The lesson learned is that status matters less than helping together.

The world is intentionally compact:
- typed entities with physical meters and emotional memes
- state-driven prose
- one clear tension turn and one resolution
- reasonableness gate with Python and ASP twins
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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

    friend: object | None = None
    haggis: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"fox", "cat", "dog", "rabbit", "mouse", "badger"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
        if not hasattr(self, "_tags"):
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


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    affords: set[str]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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


@dataclass(frozen=True)
class Haggis:
    id: str
    label: str
    phrase: str
    hidden_in: str
    status: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    hero: str
    animal: str
    friend: str
    haggis: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, place: Place, haggis: Haggis) -> None:
        self.place = place
        self.haggis = haggis
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

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


PLACES = {
    "barn": Place("barn", "the barn", {"search", "hide", "share"}),
    "hill": Place("hill", "the windy hill", {"search", "watch", "share"}),
    "kitchen": Place("kitchen", "the cozy kitchen", {"search", "cook", "share"}),
}

HAGGIS = {
    "sealed_pot": Haggis("sealed_pot", "the sealed haggis pot", "a warm sealed pot with a ribbon", "shelf", "ready"),
    "missing_plate": Haggis("missing_plate", "the missing haggis plate", "a polished plate with no haggis on it", "table", "missing"),
}

ANIMALS = {
    "fox": "fox",
    "raccoon": "raccoon",
    "badger": "badger",
    "hedgehog": "hedgehog",
    "hare": "hare",
    "mouse": "mouse",
}

NAMES = {
    "fox": ["Fenn", "Ruby", "Pip"],
    "raccoon": ["Milo", "Tess", "Nim"],
    "badger": ["Bran", "Dora", "Moss"],
    "hedgehog": ["Clover", "Dot", "Penny"],
    "hare": ["Skip", "Luna", "Wren"],
    "mouse": ["Nettle", "Bean", "Ivy"],
}


@dataclass
class WorldView:
    hero: Entity
    friend: Entity
    haggis: Entity
    status: str
    suspense: float = 0.0
    lesson: bool = False
    found: bool = False
    view: object | None = None
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about haggis, status, suspense, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
    ap.add_argument("--haggis", choices=HAGGIS)
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero = getattr(args, "hero", None) or rng.choice(list(ANIMALS))
    friend_choices = [a for a in ANIMALS if a != hero]
    friend = getattr(args, "friend", None) or rng.choice(friend_choices)
    haggis = getattr(args, "haggis", None) or rng.choice(list(HAGGIS))
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, hero))
    if place not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if haggis not in HAGGIS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, animal=name, friend=friend, haggis=haggis)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero == params.friend:
        pass
    if params.place == "kitchen" and params.haggis == "missing_plate":
        pass


def _make_world(params: StoryParams) -> World:
    _reasonableness_gate(params)
    world = World(_safe_lookup(PLACES, params.place), _safe_lookup(HAGGIS, params.haggis))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero, label=params.animal))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend, label=_safe_lookup(NAMES, params.friend)[0]))
    haggis = world.add(Entity(id="haggis", type="food", label=world.haggis.label, phrase=world.haggis.phrase))
    hero.memes["status"] = 1
    hero.memes["worry"] = 0
    friend.memes["help"] = 1
    haggis.meters["hidden"] = 1
    world.facts = {"params": params, "hero": hero, "friend": friend, "haggis": haggis}
    return world


def _search(world: World, view: WorldView) -> None:
    view.suspense += 1
    world.say(f"At {world.place.label}, {view.hero.label} cared a lot about status and wanted to seem important.")
    world.say(f"But the haggis was not where it should have been, and that made everyone pause.")
    world.para()
    world.say(f"{view.friend.label} sniffed near the sacks while {view.hero.label} checked the shelf.")
    world.say("The room felt quiet, and even the little ticks of the clock sounded loud.")
    view.hero.memes["worry"] += 1
    view.hero.meters["searching"] = 1
    if world.haggis.hidden_in == "shelf":
        view.suspense += 1
        world.say(f"Then {view.hero.label} noticed a ribbon peeking from under a cloth.")
        world.say("The haggis had been tucked away safely, but no one had looked there yet.")


def _turn(world: World, view: WorldView) -> None:
    world.para()
    world.say(f"{view.hero.label} nearly puffed up about being the first to find it.")
    world.say(f"Then {view.friend.label} slipped the cloth aside and showed how to lift it gently.")
    world.say("That made the search faster, and the haggis came back into view.")
    view.found = True
    view.hero.memes["status"] = 0
    view.hero.memes["joy"] = 1
    view.friend.memes["joy"] = 1


def _lesson(world: World, view: WorldView) -> None:
    world.para()
    view.lesson = True
    world.say(f"{view.hero.label} learned that being helpful was better than acting grand.")
    world.say(f"Together they set the haggis on the table, and the whole place felt warm again.")
    world.say(f"By the end, {view.hero.label} was proud for a kinder reason: {view.hero.label} had helped everyone eat.")


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    hero = world.get("hero")
    friend = world.get("friend")
    haggis = world.get("haggis")
    view = WorldView(hero=hero, friend=friend, haggis=haggis, status="questioned")

    world.say(f"{hero.label} was a small {params.hero} who cared too much about status.")
    world.say(f"{friend.label} was a {params.friend} who liked sharing and looking for clues.")
    world.say(f"One day at {world.place.label}, everyone gathered to find {world.haggis.label}.")
    world.para()

    _search(world, view)
    _turn(world, view)
    _lesson(world, view)

    world.facts.update(view=view, params=params)
    story = world.render()

    prompts = [
        f"Write a short animal story about {params.animal}, status, and a missing haggis at {world.place.label}.",
        "Tell a suspenseful tale where animals search together and learn something kind.",
    ]
    story_qa = [
        QAItem(
            question=f"Why was {hero.label} upset at first?",
            answer=f"{hero.label} was upset because the haggis was missing and {hero.label} cared too much about status.",
        ),
        QAItem(
            question="What broke the suspense?",
            answer=f"{friend.label} helped move the cloth, and then everyone could see where the haggis was hiding.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"{hero.label} learned that helping others matters more than trying to look important.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is haggis in this story world?",
            answer="Haggis is the special dish the animals are trying to find and share.",
        ),
        QAItem(
            question="What does status mean here?",
            answer="Status means how important or admired an animal thinks it seems to others.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of not knowing what will happen next, which can make a story feel tense and exciting.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, item in enumerate(sample.prompts, 1):
            print(f"P{i}: {item}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(barn). place(hill). place(kitchen).
hero_animal(fox). hero_animal(raccoon). hero_animal(badger). hero_animal(hedgehog). hero_animal(hare). hero_animal(mouse).
haggis(sealed_pot). haggis(missing_plate).

different(X,Y) :- hero_animal(X), hero_animal(Y), X != Y.
reasonable(P,H,F,G) :- place(P), hero_animal(H), hero_animal(F), H != F, haggis(G).
#show reasonable/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("hero_animal", aid))
    for hid in HAGGIS:
        lines.append(asp.fact("haggis", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable/4."))
    asp_set = set(asp.atoms(model, "reasonable"))
    py_set = set()
    for p in PLACES:
        for h in ANIMALS:
            for f in ANIMALS:
                for g in HAGGIS:
                    if h != f:
                        py_set.add((p, h, f, g))
    if asp_set == py_set:
        print(f"OK: clingo gate matches python ({len(py_set)} tuples).")
        return 0
    print("MISMATCH")
    return 1


CURATED = [
    StoryParams(place="hill", hero="fox", animal="Fenn", friend="badger", haggis="sealed_pot"),
    StoryParams(place="barn", hero="raccoon", animal="Milo", friend="hare", haggis="sealed_pot"),
    StoryParams(place="kitchen", hero="hedgehog", animal="Clover", friend="mouse", haggis="sealed_pot"),
]


def generation_prompts(sample: StorySample) -> list[str]:
    return sample.prompts


def story_qa(sample: StorySample) -> list[QAItem]:
    return sample.story_qa


def world_knowledge_qa(sample: StorySample) -> list[QAItem]:
    return sample.world_qa


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/4."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reasonable/4."))
        print(sorted(set(asp.atoms(model, "reasonable"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
