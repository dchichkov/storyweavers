#!/usr/bin/env python3
"""
storyworlds/worlds/skating_conflict_animal_story.py
===================================================

A small story world about animal friends, skating, and a conflict that
resolves with a fair turn-taking compromise.

Seed tale inspiration:
---
Two animal friends want to skate on the same patch of ice. One is fast and
confident, the other is smaller and nervous. They argue over whose turn it is.
A helpful adult animal notices the conflict and suggests a simple rule: one
friend skates first while the other waits by the bench with a warm scarf.
They both agree, and the ice turns from a problem into a fun afternoon.

The world model tracks:
- who is skating,
- what they want,
- what object or place is contested,
- how the conflict grows,
- and how a turn-taking compromise resolves it.
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

ANIMAL_NAMES = {
    "bear": ["Benny", "Milo", "Bruno"],
    "fox": ["Fiona", "Ruby", "Pip"],
    "rabbit": ["Mimi", "Toby", "Nina"],
    "penguin": ["Poppy", "Penny", "Pip"],
    "otter": ["Ollie", "Tessa", "Nori"],
}

ANIMALS = ["bear", "fox", "rabbit", "penguin", "otter"]
HELPERS = ["mother", "father", "aunt", "uncle", "coach", "grandparent"]
PLACES = ["pond", "rink", "frozen lake", "ice patch", "winter garden"]
OBJECTS = [
    ("bench", "the bench"),
    ("scarf", "a warm scarf"),
    ("bell", "a little silver bell"),
    ("mitten", "a striped mitten"),
]
FEELINGS = ["proud", "eager", "nervous", "shy", "silly", "competitive"]



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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    contest: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
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
    place: str
    animal_a: str
    animal_b: str
    helper: str
    object: str
    name_a: str
    name_b: str
    feeling_a: str
    feeling_b: str
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
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    turn_taken: bool = False
    conflict: bool = False
    resolved: bool = False

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        buf = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world about animal skating conflict and compromise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal-a", choices=ANIMALS)
    ap.add_argument("--animal-b", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--object", dest="object_", choices=[o[0] for o in OBJECTS])
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--feeling-a", choices=FEELINGS)
    ap.add_argument("--feeling-b", choices=FEELINGS)
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
    place = getattr(args, "place", None) or rng.choice(PLACES)
    animal_a = getattr(args, "animal_a", None) or rng.choice(ANIMALS)
    animal_b = getattr(args, "animal_b", None) or rng.choice([a for a in ANIMALS if a != animal_a])
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    obj = getattr(args, "object_", None) or rng.choice([o[0] for o in OBJECTS])
    name_a = getattr(args, "name_a", None) or rng.choice(_safe_lookup(ANIMAL_NAMES, animal_a))
    name_b = getattr(args, "name_b", None) or rng.choice(_safe_lookup(ANIMAL_NAMES, animal_b))
    feeling_a = getattr(args, "feeling_a", None) or rng.choice(FEELINGS)
    feeling_b = getattr(args, "feeling_b", None) or rng.choice([f for f in FEELINGS if f != feeling_a])
    if animal_a == animal_b:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        animal_a=animal_a,
        animal_b=animal_b,
        helper=helper,
        object=obj,
        name_a=name_a,
        name_b=name_b,
        feeling_a=feeling_a,
        feeling_b=feeling_b,
    )


def _object_phrase(key: str) -> str:
    for k, phrase in OBJECTS:
        if k == key:
            return phrase
    return key


def tell(params: StoryParams) -> World:
    world = World(place=params.place)
    a = world.add(Entity(id="A", kind="character", type=params.animal_a, label=params.name_a))
    b = world.add(Entity(id="B", kind="character", type=params.animal_b, label=params.name_b))
    helper = world.add(Entity(id="H", kind="character", type=params.helper, label=f"the {params.helper}"))
    contest = world.add(Entity(id="O", type=params.object, label=params.object, phrase=_object_phrase(params.object)))

    a.memes["eagerness"] = 1
    b.memes["eagerness"] = 1
    a.memes["confidence"] = 1
    b.memes["confidence"] = 1

    world.say(
        f"{a.label} the {a.type} and {b.label} the {b.type} came to {world.place} to skate."
    )
    world.say(
        f"{a.label} felt {params.feeling_a}, and {b.label} felt {params.feeling_b}, but both wanted the ice."
    )
    world.say(
        f"Near the rink sat {contest.phrase}, and both animals decided they wanted that spot first."
    )

    world.para()
    a.meters["skating"] += 1
    b.meters["skating"] += 1
    world.say(f"{a.label} pushed forward on tiny skates, while {b.label} reached the same patch of ice.")
    world.say(f"They started to talk at once, and the talk turned into a conflict.")

    world.conflict = True
    a.memes["conflict"] = 1
    b.memes["conflict"] = 1
    world.say(
        f'"I was here first!" said {a.label}. "No, I was!" said {b.label}.'
    )
    world.say(
        f"Their voices got louder, and the happy skating stopped for a moment."
    )

    world.para()
    helper.memes["calm"] = 1
    world.say(
        f"{helper.label.capitalize()} noticed the conflict and came over with a gentle smile."
    )
    world.say(
        f'"How about {a.label} skates first, and then {b.label} gets a turn?" {helper.label} asked.'
    )
    world.say(
        f'"You can wait by the bench with the {params.object}," said {helper.label}, "and then the other one can switch."'
    )

    a.memes["conflict"] = 0
    b.memes["conflict"] = 0
    a.memes["joy"] = 1
    b.memes["joy"] = 1
    world.turn_taken = True
    world.resolved = True
    world.say(
        f"{a.label} nodded, and {b.label} nodded too. The first skater glided around the ice, then the second one did."
    )
    world.say(
        f"By the end, both animals were laughing, and {contest.phrase} stayed where it belonged while the bench was the waiting place."
    )

    world.facts = {
        "params": params,
        "hero_a": a,
        "hero_b": b,
        "helper": helper,
        "contest": contest,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a short animal story about {p.name_a} and {p.name_b} skating at the {p.place}.",
        f"Tell a gentle story where two animals have a conflict over skating and a {p.helper} helps them take turns.",
        f"Write a child-friendly story about animals on ice that ends with a fair compromise and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    a = _safe_fact(world, world.facts, "hero_a")
    b = _safe_fact(world, world.facts, "hero_b")
    helper = _safe_fact(world, world.facts, "helper")
    contest = _safe_fact(world, world.facts, "contest")
    return [
        QAItem(
            question=f"Who were the two animals that wanted to skate at the {p.place}?",
            answer=f"The two animals were {a.label} the {a.type} and {b.label} the {b.type}. They both wanted to skate at the {p.place}.",
        ),
        QAItem(
            question=f"What problem happened when {a.label} and {b.label} tried to use the ice at the same time?",
            answer="They got into a conflict because both of them wanted the same skating spot first. Their voices got louder, and the fun stopped for a moment.",
        ),
        QAItem(
            question=f"How did {helper.label} help the two animals solve the problem?",
            answer=f"{helper.label.capitalize()} suggested a turn-taking rule: {a.label} skated first, then {b.label} got a turn. That fair plan ended the conflict.",
        ),
        QAItem(
            question=f"What stayed safe and waiting while the animals skated?",
            answer=f"{contest.phrase} stayed by the rink, and the bench was the waiting place while the animals took turns.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is skating?",
            answer="Skating is moving on ice or another smooth surface using skates on your feet.",
        ),
        QAItem(
            question="Why do people take turns when they share something?",
            answer="People take turns so everyone gets a fair chance and the shared thing does not turn into an argument.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem where people or animals want different things at the same time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    lines.append(f"  conflict={world.conflict} turn_taken={world.turn_taken} resolved={world.resolved}")
    return "\n".join(lines)


ASP_RULES = r"""
animal(A) :- hero_a(A).
animal(B) :- hero_b(B).

conflict(A,B) :- wants_same_ice(A,B), A != B.
resolved :- conflict(A,B), helper_rule.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for animal in ANIMALS:
        lines.append(asp.fact("animal", animal))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper))
    lines.append(asp.fact("activity", "skating"))
    lines.append(asp.fact("theme", "conflict"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show place/1."))
    if model is None:
        print("ASP produced no model.")
        return 1
    print("OK: ASP twin is loadable.")
    return 0


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
    StoryParams(
        place="rink",
        animal_a="bear",
        animal_b="rabbit",
        helper="mother",
        object="bench",
        name_a="Benny",
        name_b="Mimi",
        feeling_a="proud",
        feeling_b="nervous",
    ),
    StoryParams(
        place="pond",
        animal_a="fox",
        animal_b="penguin",
        helper="coach",
        object="scarf",
        name_a="Fiona",
        name_b="Poppy",
        feeling_a="eager",
        feeling_b="shy",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show place/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name_a} and {p.name_b} at the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
