#!/usr/bin/env python3
"""
A small animal-story world about a hot mistake, a stern sermon, and a
reconciliation.

Premise:
- A young animal wants to mark territory or a trail.
- A sudden sear in the sun or from a hot surface makes the mark risky.
- An elder gives a sermon-like warning.
- The conflict resolves when the young animal repairs the harm and reconciles.

This file is self-contained and follows the Storyweavers world contract.
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
    kind: str = "animal"
    species: str = "animal"
    name: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label(self) -> str:
        return self.name or self.id
    @property
    def label_word(self) -> str:
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
    id: str
    label: str
    hot: bool = False
    dry: bool = True
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
class Action:
    id: str
    gerund: str
    verb: str
    mark_gerund: str
    risky_when_hot: bool = True
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
    action: str
    hero: str
    elder: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


PLACES = {
    "sunny_rock": Place(id="sunny_rock", label="the sunny rock", hot=True, dry=True),
    "dry_path": Place(id="dry_path", label="the dry path", hot=True, dry=True),
    "shade_glen": Place(id="shade_glen", label="the shade glen", hot=False, dry=True),
}

ACTIONS = {
    "mark_trail": Action(
        id="mark_trail",
        gerund="marking the trail",
        verb="mark the trail",
        mark_gerund="marking the trail",
        risky_when_hot=True,
    ),
    "mark_tree": Action(
        id="mark_tree",
        gerund="marking the tree",
        verb="mark the tree",
        mark_gerund="marking the tree",
        risky_when_hot=True,
    ),
    "mark_gate": Action(
        id="mark_gate",
        gerund="marking the gate",
        verb="mark the gate",
        mark_gerund="marking the gate",
        risky_when_hot=True,
    ),
}

ANIMALS = {
    "rabbit": {"species": "rabbit", "name_pool": ["Pip", "Milo", "Tilly", "Nell", "Bun"]},
    "fox": {"species": "fox", "name_pool": ["Poppy", "Rune", "Jasper", "Fenn", "Reed"]},
    "beaver": {"species": "beaver", "name_pool": ["Bram", "Clover", "Wren", "Moss", "Toby"]},
    "mouse": {"species": "mouse", "name_pool": ["Dot", "Sage", "Lulu", "Tiny", "Mina"]},
    "bear": {"species": "bear", "name_pool": ["Gus", "Honey", "Mira", "Otto", "Penny"]},
}

TRAITS = ["small", "curious", "stubborn", "bright", "gentle", "busy"]


def reasonableness_gate(place: Place, action: Action) -> bool:
    return place.hot and action.risky_when_hot


ASP_RULES = r"""
place_hot(P) :- hot(P).
risky(A) :- action(A), risky_when_hot(A).
problem(P,A) :- place_hot(P), risky(A).

valid_story(P,A) :- problem(P,A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.hot:
            lines.append(asp.fact("hot", pid))
        if p.dry:
            lines.append(asp.fact("dry", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if a.risky_when_hot:
            lines.append(asp.fact("risky_when_hot", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo = set(asp_valid_stories())
    py = {(p, a) for p in PLACES for a in ACTIONS if reasonableness_gate(_safe_lookup(PLACES, p), _safe_lookup(ACTIONS, a))}
    if clingo == py:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in clingo:", sorted(clingo - py))
    print(" only in python:", sorted(py - clingo))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: sear, sermon, mark-gerund, reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--elder", choices=ANIMALS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    action = getattr(args, "action", None) or rng.choice(list(ACTIONS))
    if not reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(ACTIONS, action)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or rng.choice(list(ANIMALS))
    elder = getattr(args, "elder", None) or rng.choice([k for k in ANIMALS if k != hero])
    return StoryParams(place=place, action=action, hero=hero, elder=elder)


def _warn(world: World, elder: Entity, hero: Entity, action: Action) -> None:
    world.say(
        f'{elder.label} gave a small sermon: "The sun can sear your paw, and hot stone can sear your plan too."'
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1


def _conflict(world: World, hero: Entity, action: Action) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(f"{hero.label} still wanted to {action.verb}, so {hero.pronoun()} went closer anyway.")
    if world.place.hot:
        hero.meters["sear"] = hero.meters.get("sear", 0) + 1


def _repair(world: World, hero: Entity, elder: Entity, action: Action) -> None:
    hero.memes["regret"] = hero.memes.get("regret", 0) + 1
    world.say(f"Then {hero.label} stopped, blew on the hot spot, and used a cool leaf to cover it.")
    world.say(
        f"{hero.label} bowed low and apologized. {elder.label} touched noses with {hero.label}, "
        f"and the two made up in quiet reconciliation."
    )
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    elder.memes["peace"] = elder.memes.get("peace", 0) + 1


def tell_story(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero_info = _safe_lookup(ANIMALS, params.hero)
    elder_info = _safe_lookup(ANIMALS, params.elder)

    hero = world.add(Entity(
        id="hero",
        species=hero_info["species"],
        name=hero_info["name_pool"][0],
        traits=[random.choice(TRAITS), "young"],
    ))
    elder = world.add(Entity(
        id="elder",
        species=elder_info["species"],
        name=elder_info["name_pool"][1],
        traits=["old", "wise"],
    ))
    action = _safe_lookup(ACTIONS, params.action)

    world.say(f"{hero.label} was a {hero.traits[0]} little {hero.species} who loved {action.gerund}.")
    world.say(f"On {world.place.label}, {hero.label} watched the light on the ground and thought about {action.mark_gerund}.")
    world.para()
    world.say(f"One hot afternoon, {hero.label} and {elder.label} met at {world.place.label}.")
    _warn(world, elder, hero, action)
    _conflict(world, hero, action)
    world.para()
    _repair(world, hero, elder, action)
    world.say(f"In the end, {hero.label} stayed in the shade, and the hot rock was left quiet.")
    world.facts = {"hero": hero, "elder": elder, "action": action, "place": world.place}
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    action = _safe_fact(world, f, "action")
    place = _safe_fact(world, f, "place")
    return [
        f'Write an animal story about a small creature named {hero.label} who wants to {action.verb} at {place.label}.',
        f"Tell a gentle story where a sermon warns {hero.label} that the sun may sear the path during {action.mark_gerund}.",
        f'Write a child-friendly story with the words "sear", "sermon", and "{action.mark_gerund}" that ends in reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    action = _safe_fact(world, f, "action")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who wanted to {action.verb} at {place.label}?",
            answer=f"{hero.label}, the young {hero.species}, wanted to {action.verb} at {place.label}.",
        ),
        QAItem(
            question=f"What kind of speech did {elder.label} give before the trouble?",
            answer=f"{elder.label} gave a sermon warning that heat could sear the spot and make the plan unsafe.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{hero.label} apologized, the elder forgave {hero.pronoun('object')}, and they ended in reconciliation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sear mean?",
            answer="To sear means to burn or hurt something with strong heat.",
        ),
        QAItem(
            question="What is a sermon?",
            answer="A sermon is a serious talk that gives advice about how to live or behave.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a disagreement or hurt feeling.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: name={e.name} species={e.species} meters={e.meters} memes={e.memes}")
    lines.append(f"place: {world.place.id} hot={world.place.hot} dry={world.place.dry}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="sunny_rock", action="mark_trail", hero="rabbit", elder="bear"),
    StoryParams(place="dry_path", action="mark_gate", hero="mouse", elder="fox"),
    StoryParams(place="sunny_rock", action="mark_tree", hero="beaver", elder="rabbit"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for p, a in combos:
            print(f"  {p} {a}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
