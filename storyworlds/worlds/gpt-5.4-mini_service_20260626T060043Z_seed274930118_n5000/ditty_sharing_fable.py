#!/usr/bin/env python3
"""
A small fable-style storyworld about sharing a ditty.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ditty: object | None = None
    listener: object | None = None
    singer: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "girl", "female", "squirrel"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "fox", "wolf", "male"}:
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
class StoryParams:
    singer: str
    listener: str
    place: str
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


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    w: object | None = None
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


SINGERS = {
    "mole": ("Milo", "mole", "little mole"),
    "mouse": ("Mara", "mouse", "little mouse"),
    "bird": ("Bibi", "bird", "little bird"),
    "fox": ("Fenn", "fox", "clever fox"),
}

LISTENERS = {
    "hare": ("Hattie", "hare", "quick hare"),
    "squirrel": ("Soren", "squirrel", "squirrel"),
    "bear": ("Bram", "bear", "bear"),
    "mouse": ("Mimi", "mouse", "mouse"),
}

PLACES = {
    "meadow": "the meadow",
    "brook": "the brook",
    "garden": "the garden",
    "hill": "the hill",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld about sharing a ditty.")
    ap.add_argument("--singer", choices=SINGERS)
    ap.add_argument("--listener", choices=LISTENERS)
    ap.add_argument("--place", choices=PLACES)
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
    singer = getattr(args, "singer", None) or rng.choice(list(SINGERS))
    listener = getattr(args, "listener", None) or rng.choice(list(LISTENERS))
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    if singer == listener:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(singer=singer, listener=listener, place=place)


def asp_facts() -> str:
    import asp
    lines = []
    for s in SINGERS:
        lines.append(asp.fact("singer", s))
    for l in LISTENERS:
        lines.append(asp.fact("listener", l))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    return "\n".join(lines)


ASP_RULES = r"""
shared_story(S,L,P) :- singer(S), listener(L), place(P), S != L.
#show shared_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shared_story/3."))
    clingo_set = set(asp.atoms(model, "shared_story"))
    py_set = set((s, l, p) for s in SINGERS for l in LISTENERS for p in PLACES if s != l)
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    if clingo_set - py_set:
        print(" only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print(" only in python:", sorted(py_set - clingo_set))
    return 1


def tell(params: StoryParams) -> World:
    w = World()
    singer_name, singer_type, singer_desc = _safe_lookup(SINGERS, params.singer)
    listener_name, listener_type, listener_desc = _safe_lookup(LISTENERS, params.listener)
    place = _safe_lookup(PLACES, params.place)

    singer = w.add(Entity(id=singer_name, kind="character", type=singer_type, label=singer_desc))
    listener = w.add(Entity(id=listener_name, kind="character", type=listener_type, label=listener_desc))
    ditty = w.add(Entity(id="ditty", type="song", label="ditty", phrase="a bright little ditty", owner=singer.id))

    singer.memes["joy"] = 1
    singer.memes["pride"] = 1
    listener.memes["curiosity"] = 1

    w.say(f"{singer.id} was a {singer_desc} who had made up a bright little ditty.")
    w.say(f"{{singer.pronoun('subject').capitalize()}} loved to hum it as {singer.pronoun('subject')} walked.")
    w.say(f"One day at {place}, {singer.id} met {listener.id}, a {listener_desc}, and began to sing the ditty aloud.")
    w.para()

    singer.memes["desire"] = 1
    listener.memes["wanting"] = 1
    w.say(f"{listener.id} listened close and smiled. \"That tune is sweet,\" {listener.pronoun()} said.")
    w.say(f"{listener.id} asked to hear it again, but this time to sing along.")
    singer.memes["guarding"] = 1
    w.say(f"{singer.id} grew tight for a moment, for {singer.pronoun('possessive')} ditty felt like a tiny treasure.")

    if singer.memes["guarding"] >= 1:
        w.say(f"Then {singer.id} remembered a small truth: a song grows lighter when it is shared.")
        singer.memes["kindness"] = 1
        listener.memes["joy"] = 1
        singer.memes["guarding"] = 0
        w.para()
        w.say(f"So {singer.id} taught {listener.id} the tune one line at a time.")
        w.say(f"Soon the two of them were singing together, and the ditty sounded even merrier in {place}.")
        w.say(f"By the end, {singer.id} was glad, {listener.id} was glad, and the little song belonged to both of them in the best way.")
    else:
        w.para()
        w.say(f"The song drifted on the air, and nobody kept it to themselves.")

    w.facts.update(
        singer=singer,
        listener=listener,
        ditty=ditty,
        place=place,
        singer_type=singer_type,
        listener_type=listener_type,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s: Entity = _safe_fact(world, f, "singer")
    l: Entity = _safe_fact(world, f, "listener")
    return [
        f"Write a short fable about {s.id} sharing a ditty with {l.id} at {f['place']}.",
        f"Tell a child-friendly story where a small song is shared instead of kept alone.",
        f"Write a gentle moral tale about how {s.id} and {l.id} learned that a ditty can grow when it is shared.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Entity = _safe_fact(world, f, "singer")
    l: Entity = _safe_fact(world, f, "listener")
    return [
        QAItem(
            question=f"Who made up the ditty in the story?",
            answer=f"{s.id} made up the ditty and was the first one to sing it.",
        ),
        QAItem(
            question=f"What did {l.id} want to do after hearing the song?",
            answer=f"{l.id} wanted to sing along and hear the ditty again.",
        ),
        QAItem(
            question=f"What changed when the song was shared?",
            answer=f"The song became merrier, and both {s.id} and {l.id} felt glad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ditty?",
            answer="A ditty is a short, simple song or tune that is easy to remember and sing.",
        ),
        QAItem(
            question="Why can sharing a song be nice?",
            answer="Sharing a song can be nice because other people can enjoy it too, and singing together can make everyone feel happy.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(singer="mole", listener="hare", place="meadow"),
    StoryParams(singer="mouse", listener="squirrel", place="garden"),
    StoryParams(singer="bird", listener="bear", place="hill"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show shared_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show shared_story/3."))
        print(sorted(set(asp.atoms(model, "shared_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
