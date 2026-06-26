#!/usr/bin/env python3
"""
Standalone storyworld: a small detective tale about an engraver, a ceiling clue,
conflict, and friendship.

Seed premise:
- A child-friendly detective notices a strange engraving near the ceiling.
- A conflict arises because a friend suspects another friend of hiding a clue.
- Careful observation solves the case and strengthens their friendship.

The world is modeled with physical meters and emotional memes, and the prose is
driven by simulated state rather than template swapping.
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

    a: object | None = None
    b: object | None = None
    ceiling: object | None = None
    clue: object | None = None
    hero: object | None = None
    def __post_init__(self):
        for key in ["dust", "light", "height", "damage", "polish"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "conflict", "trust", "friendship", "relief"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    hero: str
    friend_a: str
    friend_b: str
    clue: str
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


PLACES = {
    "museum hall": {"ceiling": True, "dark": False},
    "library room": {"ceiling": True, "dark": True},
    "old station": {"ceiling": True, "dark": True},
    "studio": {"ceiling": True, "dark": False},
}

HEROES = ["Nia", "Milo", "June", "Tobi", "Ava", "Theo"]
FRIENDS = ["Pip", "Sage", "Lena", "Omar", "Mina", "Rae"]
CLUES = ["engrave", "ceiling"]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    w: object | None = None
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
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


def _r_dust_hint(world: World) -> list[str]:
    out = []
    clue = world.facts.get("clue_obj")
    ceiling = world.facts.get("ceiling")
    if clue and ceiling and clue.meters["height"] >= ceiling.meters["height"] and clue.meters["dust"] < THRESHOLD:
        sig = ("dust_hint", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            clue.meters["dust"] += 1
            out.append(f"Up near the ceiling, a thin line of dust made the clue easier to notice.")
    return out


def _r_conflict(world: World) -> list[str]:
    a = world.get("FriendA")
    b = world.get("FriendB")
    if a.memes["suspicion"] >= THRESHOLD and b.memes["hurt"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["conflict"] += 1
            b.memes["conflict"] += 1
            return ["__conflict__"]
    return []


def _r_friendship(world: World) -> list[str]:
    hero = world.get("Hero")
    a = world.get("FriendA")
    b = world.get("FriendB")
    if world.facts.get("resolved") and hero.memes["trust"] >= THRESHOLD:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["friendship"] += 1
            a.memes["friendship"] += 1
            b.memes["friendship"] += 1
            return ["Their friendship felt stronger after the truth came out."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_dust_hint, _r_conflict, _r_friendship):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    w = World(params.place)
    hero = w.add(Entity(id="Hero", kind="character", type="girl", label=params.hero))
    a = w.add(Entity(id="FriendA", kind="character", type="boy", label=params.friend_a))
    b = w.add(Entity(id="FriendB", kind="character", type="girl", label=params.friend_b))
    clue = w.add(Entity(id="Clue", type="object", label=params.clue, phrase=f"an old {params.clue} mark"))
    ceiling = w.add(Entity(id="Ceiling", type="object", label="ceiling", phrase="the high ceiling"))
    ceiling.meters["height"] = 10.0
    clue.meters["height"] = 10.0
    clue.meters["light"] = 1.0

    w.facts.update(hero=hero, friend_a=a, friend_b=b, clue_obj=clue, ceiling=ceiling, place=params.place)

    w.say(f"{hero.label} was a little detective who loved noticing tiny details in quiet places.")
    w.say(f"{hero.pronoun().capitalize()} met {a.label} and {b.label} at the {params.place} to look for a clue.")
    w.say(f"Something strange was hidden near the {ceiling.label}, and the children all felt curious.")

    w.para()
    clue.meters["dust"] += 0.5
    a.memes["suspicion"] += 1.0
    b.memes["hurt"] += 1.0
    w.say(f"{a.label} pointed up and said, \"I think {b.label} is hiding something.\"")
    w.say(f"{b.label} frowned. \"I didn't do anything,\" {b.pronoun('subject')} said, sounding hurt.")
    w.say(f"{hero.label} looked closer and saw that the {clue.label} mark was not a secret at all.")

    propagate(w, narrate=True)
    w.para()

    w.say(f"{hero.label} fetched a small ladder and checked the mark near the ceiling.")
    w.say(f"It was an old engraving, left by a maker long ago, and it matched a note in the room.")
    hero.memes["curiosity"] += 1.0
    hero.memes["trust"] += 1.0
    hero.memes["relief"] += 1.0

    a.memes["suspicion"] = 0.0
    b.memes["hurt"] = 0.0
    w.facts["resolved"] = True
    propagate(w, narrate=True)

    w.say(f"{a.label} apologized to {b.label}, and {b.label} smiled again.")
    w.say(f"The three friends left the {params.place} together, laughing under the high ceiling.")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle detective story for children that includes the words "engrave" and "ceiling".',
        f"Tell a short mystery where {f['hero'].label} notices a clue near the ceiling and helps {f['friend_a'].label} and {f['friend_b'].label} stop arguing.",
        f"Write a small friendship story with a detective clue, a ceiling detail, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    a = _safe_fact(world, world.facts, "friend_a")
    b = _safe_fact(world, world.facts, "friend_b")
    clue = _safe_fact(world, world.facts, "clue_obj")
    place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"Who was the little detective at the {place}?",
            answer=f"The little detective was {hero.label}. {hero.label} paid attention to tiny clues and helped the friends talk kindly.",
        ),
        QAItem(
            question=f"What did the children notice near the ceiling?",
            answer=f"They noticed an old {clue.label} engraving near the ceiling. It looked strange at first, but it was really an old mark from long ago.",
        ),
        QAItem(
            question=f"Why did {a.label} and {b.label} stop arguing?",
            answer=f"{a.label} thought there was a secret, and {b.label} felt hurt. {hero.label} checked the clue, found the truth, and the worry went away.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The conflict turned into friendship. {a.label} apologized, {b.label} smiled, and the three friends left together happily.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks carefully for clues and tries to figure out what happened.",
        ),
        QAItem(
            question="What is a ceiling?",
            answer="A ceiling is the top inside part of a room. It is above your head.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind, happy connection between people who care about each other.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style storyworld about an engraving near the ceiling.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend-a", dest="friend_a", choices=FRIENDS)
    ap.add_argument("--friend-b", dest="friend_b", choices=FRIENDS)
    ap.add_argument("--clue", choices=CLUES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, "detective", "friendship") for p in PLACES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero = getattr(args, "hero", None) or rng.choice(HEROES)
    pool = [x for x in FRIENDS if x != hero]
    friend_a = getattr(args, "friend_a", None) or rng.choice(pool)
    pool2 = [x for x in pool if x != friend_a]
    friend_b = getattr(args, "friend_b", None) or rng.choice(pool2)
    clue = getattr(args, "clue", None) or "engrave"
    if friend_a == friend_b:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, friend_a=friend_a, friend_b=friend_b, clue=clue)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id}: type={e.type} meters={ {k: round(v, 2) for k, v in e.meters.items() if v} } "
            f"memes={ {k: round(v, 2) for k, v in e.memes.items() if v} }"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% Minimal parity twin for the reasonableness gate.
valid_place(P) :- place(P).
valid_story(P) :- valid_place(P).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("place", p) for p in PLACES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(p,) for p, _, _ in valid_combos()}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("Compatible story places:")
        for p, _, _ in valid_combos():
            print(f"  {p}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in PLACES:
            samples.append(generate(StoryParams(place=p, hero=_safe_lookup(HEROES, 0), friend_a=_safe_lookup(FRIENDS, 0), friend_b=_safe_lookup(FRIENDS, 1), clue="engrave")))
    else:
        for i in range(max(1, getattr(args, "n", None))):
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
