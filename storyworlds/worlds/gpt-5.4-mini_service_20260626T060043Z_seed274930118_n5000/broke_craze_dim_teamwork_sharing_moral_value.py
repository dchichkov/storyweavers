#!/usr/bin/env python3
"""
A small nursery-rhyme-style storyworld about something broken, a shared fix,
and the gentle moral that teamwork and sharing can make a hard moment sweet.
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

BROKEN_THRESHOLD = 1.0
DIM_THRESHOLD = 1.0



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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    traits: object | None = None
    friend: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    sw: object | None = None
    w: object | None = None
    world: object | None = None
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w
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
class Character:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
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
class ObjectKind:
    id: str
    label: str
    phrase: str
    type: str
    damage: str
    dim_reason: str
    fix: str
    shares_with: str
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
    name: str
    friend: str
    object_kind: str
    seed: Optional[int] = None
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


CHARACTERS = [
    Character("Mira", "girl", "Mira", ["small", "bright"]),
    Character("Toby", "boy", "Toby", ["small", "kind"]),
    Character("Nell", "girl", "Nell", ["small", "cheery"]),
    Character("Pip", "boy", "Pip", ["small", "spry"]),
]

FRIENDS = [
    Character("Bea", "girl", "Bea", ["kind"]),
    Character("Owen", "boy", "Owen", ["kind"]),
    Character("Luna", "girl", "Luna", ["gentle"]),
    Character("Max", "boy", "Max", ["gentle"]),
]

OBJECTS = {
    "lantern": ObjectKind(
        id="lantern",
        label="lantern",
        phrase="a tiny lantern with a red handle",
        type="lantern",
        damage="broke",
        dim_reason="craze-dim",
        fix="glued and polished",
        shares_with="a candle lantern",
    ),
    "toy_wheel": ObjectKind(
        id="toy_wheel",
        label="toy wheel",
        phrase="a bright toy cart with a little wheel",
        type="toy",
        damage="broke",
        dim_reason="craze-dim",
        fix="taped and tucked",
        shares_with="the cart piece",
    ),
    "music_box": ObjectKind(
        id="music_box",
        label="music box",
        phrase="a small music box with a silver top",
        type="box",
        damage="broke",
        dim_reason="craze-dim",
        fix="wound and mended",
        shares_with="the winding key",
    ),
}

HEROES = [c.id for c in CHARACTERS]
HELPERS = [c.id for c in FRIENDS]


class StoryWorld:
    def __init__(self) -> None:
        self.world = World()

    def add_line(self, text: str) -> None:
        self.world.say(text)

    def broken_and_dim(self, obj: Entity) -> None:
        obj.meters["broke"] += 1
        obj.meters["craze-dim"] += 1

    def teamwork_fix(self, hero: Entity, friend: Entity, obj: Entity) -> None:
        hero.memes["worry"] += 1
        friend.memes["helping"] += 1
        hero.memes["teamwork"] += 1
        friend.memes["teamwork"] += 1
        hero.memes["sharing"] += 1
        friend.memes["sharing"] += 1
        hero.memes["moral_value"] += 1
        friend.memes["moral_value"] += 1
        obj.meters["broke"] = 0
        obj.meters["craze-dim"] = 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: broke, craze-dim, teamwork, sharing.")
    ap.add_argument("--name", choices=HEROES)
    ap.add_argument("--friend", choices=HELPERS)
    ap.add_argument("--object-kind", choices=sorted(OBJECTS))
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
    name = getattr(args, "name", None) or rng.choice(HEROES)
    friend = getattr(args, "friend", None) or rng.choice([f for f in HELPERS if f != name])
    obj = getattr(args, "object_kind", None) or rng.choice(sorted(OBJECTS))
    if friend == name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, friend=friend, object_kind=obj)


def _add_story_text(world: World, hero: Entity, friend: Entity, objcfg: ObjectKind) -> None:
    world.say(f"Little {hero.id} had {objcfg.phrase}, bright in the hall.")
    world.say(f"One day it went broke, and its light grew craze-dim and small.")
    world.para()
    world.say(f"{hero.id} looked sad; {hero.pronoun()} did not know what to do.")
    world.say(f"Then {friend.id} came in with a grin and said, “Let me help you.”")
    world.para()
    world.say(f"They shared the work and used soft glue, and tape, and twine.")
    world.say(f"Together they mended the {objcfg.label}, and the fix turned out fine.")
    world.say(f"In the end they shared the little shine, and both felt proud and warm.")
    world.say(f"For teamwork and sharing had made a sweet light from the storm.")


def _trace_text(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    sw = StoryWorld()
    world = sw.world
    hero_cfg = next(c for c in CHARACTERS if c.id == params.name)
    friend_cfg = next(c for c in FRIENDS if c.id == params.friend)
    objcfg = _safe_lookup(OBJECTS, params.object_kind)

    hero = world.add(Entity(id=hero_cfg.id, kind="character", type=hero_cfg.type, label=hero_cfg.label, traits=hero_cfg.traits))
    friend = world.add(Entity(id=friend_cfg.id, kind="character", type=friend_cfg.type, label=friend_cfg.label, traits=friend_cfg.traits))
    obj = world.add(Entity(id=objcfg.id, type=objcfg.type, label=objcfg.label, phrase=objcfg.phrase, owner=hero.id, caretaker=friend.id))

    sw.broken_and_dim(obj)
    hero.memes["sad"] += 1
    friend.memes["kindness"] += 1
    _add_story_text(world, hero, friend, objcfg)
    sw.teamwork_fix(hero, friend, obj)

    world.facts.update(hero=hero, friend=friend, obj=obj, objcfg=objcfg)
    prompts = [
        "Write a short nursery rhyme about a broken thing and a kind helper.",
        f"Tell a gentle story where {hero.id} and {friend.id} fix a {objcfg.label} together.",
        "Write a rhyme with teamwork, sharing, and a soft happy ending.",
    ]
    story_qa = [
        QAItem(
            question=f"What went wrong with {hero.id}'s {objcfg.label}?",
            answer=f"It went broke and grew craze-dim, so its little shine did not work well anymore.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} fix the problem?",
            answer=f"They used teamwork and sharing. {friend.id} helped with glue, tape, and twine, and together they mended it.",
        ),
        QAItem(
            question="What moral does the story show?",
            answer="The story shows that teamwork and sharing can help fix a hard problem and make everyone feel proud.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have, or letting someone use it too, so everyone can help or enjoy it.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a kind guide for how to act, like being kind, honest, helpful, or fair.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(_trace_text(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
hero(X) :- child(X).
friend(Y) :- helper(Y).
object(O) :- thing(O).
needs_teamwork(H,F,O) :- child(H), helper(F), thing(O).
moral_value(H) :- child(H), shared(H,_), helped(H,_).
shared(H,O) :- child(H), thing(O), shares(H,O).
resolved(H,O) :- child(H), thing(O), fixed(H,O), teamwork(H,_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for c in CHARACTERS:
        lines.append(asp.fact("child", c.id))
    for c in FRIENDS:
        lines.append(asp.fact("helper", c.id))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("thing", oid))
        lines.append(asp.fact("shares", "Mira", oid))
        lines.append(asp.fact("fixable", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    prog = asp_program("#show child/1.\n#show helper/1.\n#show thing/1.")
    model = asp.one_model(prog)
    c = set(asp.atoms(model, "child"))
    h = set(asp.atoms(model, "helper"))
    t = set(asp.atoms(model, "thing"))
    ok = c == {(x.id,) for x in CHARACTERS} and h == {(x.id,) for x in FRIENDS} and t == {(x,) for x in OBJECTS}
    if ok:
        print("OK: ASP facts reflect the registries.")
        return 0
    print("MISMATCH in ASP registry parity.")
    return 1


def generation_prompts(sample: StorySample) -> list[str]:
    return list(sample.prompts)


def story_qa(sample: StorySample) -> list[QAItem]:
    return list(sample.story_qa)


def world_knowledge_qa(sample: StorySample) -> list[QAItem]:
    return list(sample.world_qa)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show child/1.\n#show helper/1.\n#show thing/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show child/1.\n#show helper/1.\n#show thing/1."))
        print("children:", sorted(asp.atoms(model, "child")))
        print("helpers:", sorted(asp.atoms(model, "helper")))
        print("things:", sorted(asp.atoms(model, "thing")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("Mira", "Bea", "lantern"),
            StoryParams("Toby", "Luna", "toy_wheel"),
            StoryParams("Nell", "Owen", "music_box"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
