#!/usr/bin/env python3
"""
storyworlds/worlds/bouncer_average_relief_swimming_pool_kindness_humor.py
===========================================================================

A small comedy storyworld set at a swimming pool: an average bouncer tries to
keep order, a child wants to play, and kindness plus humor turn tension into
relief.

Premise:
- The bouncer is responsible for the pool gate.
- A child wants to bring a messy, silly pool game through the gate.
- The bouncer worries about chaos and rules.

Turn:
- The child uses kindness and a joke to soften the bouncer.
- The bouncer notices the joke is harmless and the mood changes.

Resolution:
- The bouncer lets them through with a sensible compromise.
- Everyone feels relief, and the pool day becomes funny instead of tense.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    bouncer: object | None = None
    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bouncer", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Pool:
    place: str = "the swimming pool"
    affords: set[str] = field(default_factory=lambda: {"enter", "swim", "joke", "kindness"})
    POOL: object | None = None
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
class StoryParams:
    name: str
    child_name: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
    def __init__(self, pool: Pool):
        self.pool = pool
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        w = World(self.pool)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    bouncer = world.get("bouncer")
    child = world.get("child")
    if bouncer.memes.get("annoyance", 0.0) >= THRESHOLD and child.memes.get("kindness", 0.0) >= THRESHOLD:
        sig = ("relief",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        bouncer.memes["relief"] = bouncer.memes.get("relief", 0.0) + 1
        bouncer.memes["softened"] = 1
        out.append("The tight feeling at the gate loosened.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_relief,):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_story(world: World, bouncer: Entity, child: Entity) -> None:
    world.say(
        f"At {world.pool.place}, {bouncer.id} was an average bouncer with a tidy whistle and a serious face."
    )
    world.say(
        f"{child.id} arrived grinning, holding a squeaky pool ring and hoping to make a splash."
    )
    world.para()
    world.say(
        f"{child.id} wanted to slip past the gate, but {bouncer.id} held up a hand and frowned."
    )
    bouncer.memes["annoyance"] = 1
    bouncer.memes["duty"] = 1
    child.memes["worry"] = 1
    world.say(
        f"'Pool rules are pool rules,' {bouncer.pronoun('subject')} said, looking very average and very firm."
    )
    world.say(
        f"{child.id} paused, then told a tiny joke about a duck wearing goggles."
    )
    child.memes["humor"] = 1
    child.memes["kindness"] = 1
    world.say(
        f"{child.id} also offered to wait in line and keep the deck neat, which was a kind thing to do."
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{bouncer.id} snorted despite {bouncer.pronoun('possessive')}self and waved {child.pronoun('object')} through."
    )
    bouncer.memes["relief"] = bouncer.memes.get("relief", 0.0) + 1
    bouncer.memes["annoyance"] = 0
    child.memes["joy"] = 1
    child.memes["relief"] = 1
    world.say(
        f"By the water, they both laughed, and the pool gate felt friendly instead of tense."
    )
    world.facts.update(
        bouncer=bouncer,
        child=child,
        pool=world.pool,
        resolved=True,
        humor=True,
        kindness=True,
        relief=bouncer.memes.get("relief", 0.0) >= THRESHOLD,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short comedy story set at a swimming pool about a bouncer, kindness, and humor.',
        'Tell a gentle story where an average bouncer at the swimming pool relaxes after a child uses kindness and a joke.',
        'Write a kid-friendly pool story that ends with relief and laughter at the gate.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bouncer: Entity = _safe_fact(world, f, "bouncer")
    child: Entity = _safe_fact(world, f, "child")
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens at the swimming pool, where {bouncer.id} stands at the gate and {child.id} comes in with a pool ring.",
        ),
        QAItem(
            question=f"Why did {bouncer.id} look serious at first?",
            answer=f"{bouncer.id} was doing {bouncer.pronoun('possessive')} job as a bouncer, so {bouncer.pronoun('subject')} watched the gate carefully and worried about rules.",
        ),
        QAItem(
            question=f"What did {child.id} do that changed the mood?",
            answer=f"{child.id} told a silly joke about a duck wearing goggles and acted kindly by waiting in line and keeping the deck neat.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The gate became calm and funny, {bouncer.id} waved {child.pronoun('object')} through, and everyone felt relief and laughed by the pool.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bouncer?",
            answer="A bouncer is a person who watches a door or gate and helps decide who can come in.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and thoughtful toward other people.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is what makes people laugh, like a silly joke or a funny idea.",
        ),
        QAItem(
            question="What is relief?",
            answer="Relief is the happy feeling you get when a worry goes away and things feel easier.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


POOL = Pool()

NAMES = ["Milo", "Ava", "Nina", "Toby", "Zoe", "Finn", "Luna", "Ben"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or "Arlo"
    child_name = getattr(args, "child_name", None) or rng.choice([n for n in NAMES if n != name])
    if child_name == name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, child_name=child_name)


def generate(params: StoryParams) -> StorySample:
    world = World(POOL)
    bouncer = world.add(Entity(id=params.name, kind="character", type="bouncer", label="bouncer"))
    child = world.add(Entity(id=params.child_name, kind="character", type="child", label="child"))
    build_story(world, bouncer, child)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
bouncer(X) :- named(X,bouncer).
child(X) :- named(X,child).

kindness(X) :- has_kindness(X).
humor(X) :- has_humor(X).

relief(B,C) :- bouncer(B), child(C), annoyed(B), kind(C), funny(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("named", "bouncer", "bouncer"))
    lines.append(asp.fact("named", "child", "child"))
    lines.append(asp.fact("has_kindness", "child"))
    lines.append(asp.fact("has_humor", "child"))
    lines.append(asp.fact("annoyed", "bouncer"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld set at a swimming pool.")
    ap.add_argument("--name")
    ap.add_argument("--child-name")
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


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show relief/2."))
    got = set(asp.atoms(model, "relief"))
    expected = {("bouncer", "child")}
    if got == expected:
        print("OK: ASP gate matches Python story logic (1 relief relation).")
        return 0
    print("MISMATCH between ASP and Python logic.")
    print("ASP:", sorted(got))
    print("PY :", sorted(expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show relief/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(name=n, child_name=c)) for n, c in [("Arlo", "Milo"), ("Nina", "Toby")]]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
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
