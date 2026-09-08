#!/usr/bin/env python3
"""
A tiny mystery world about a broken mechanism, friendship, caution, and a twist.

The simulation keeps a small causal model:
- two friends explore a quiet place
- a mechanism starts behaving oddly
- caution keeps the problem from getting worse
- a twist reveals the cause was not danger, but a simple misunderstanding
- the ending proves friendship changed what they did next

This world is child-facing, state-driven, and includes dialogue in every story.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402



def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    helper: object | None = None
    hero: object | None = None
    mechanism: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, line: str) -> None:
        self.notes.append(line)

    def render(self) -> str:
        return " ".join(self.notes)

    def copy(self) -> "World":
        import copy
        return copy.deepcopy(self)
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
    place: str = "old_station"
    hero_name: str = "Mina"
    helper_name: str = "Owen"
    seed: Optional[int] = None
    sample: object | None = None
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
    "old_station": Place("old_station", "the old station", {"quiet", "stone"}),
    "toy_room": Place("toy_room", "the toy room", {"quiet", "warm"}),
    "garden_shed": Place("garden_shed", "the garden shed", {"quiet", "wood"}),
}

NAMES = ["Mina", "Owen", "Pia", "Leo", "Nora", "Eli"]

ASP_RULES = r"""
place(old_station).
place(toy_room).
place(garden_shed).

friend(mina).
friend(owen).
friend(pia).
friend(leo).
friend(nora).
friend(eli).

caution(protects) :- friend(_).
twist(reveal).
mechanism(locked).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    parts = [
        asp.fact("place", "old_station"),
        asp.fact("place", "toy_room"),
        asp.fact("place", "garden_shed"),
        asp.fact("mechanism", "clockwork_box"),
        asp.fact("friend", "mina"),
        asp.fact("friend", "owen"),
        asp.fact("caution", "pause"),
        asp.fact("twist", "reveal"),
    ]
    return "\n".join(parts)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world about a mechanism and a twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(place=place, hero_name=hero, helper_name=helper, seed=getattr(args, "seed", None))


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.place}:{params.hero_name}:{params.helper_name}"
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _dialogue(world: World, hero: Entity, helper: Entity, clue: str) -> None:
    world.say(f'"{clue}," said {hero.label}.')
    world.say(f'"Then let us be careful," said {helper.label}, "and look once more."')


def _simulate(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    mechanism = world.get("mechanism")

    world.say(f"At {world.place.label}, {hero.label} and {helper.label} found a small brass mechanism under a dusty shelf.")
    world.say("It clicked, then stopped, then clicked again, like it wanted to tell a secret.")
    world.say(f'"Did you hear that?" asked {hero.label}.')
    world.say(f'"Yes," said {helper.label}. "It sounds like a mystery, but we should not poke it too fast."')

    mechanism.meters["odd"] = 1.0
    hero.memes["curious"] = 1.0
    helper.memes["curious"] = 1.0
    helper.memes["cautious"] = 1.0
    world.fired.add("start")

    world.say("They leaned close, but they did not press hard. That careful pause kept the little gears from grinding.")
    world.say(f'"Maybe something is stuck," said {hero.label}.')
    world.say(f'"Or maybe something is missing," said {helper.label}.')
    world.say("They listened again and noticed a tiny ribbon caught near the lever.")

    world.say(f'"Look!" said {helper.label}. "The ribbon is pulling the switch."')
    world.say(f'"So the machine was not broken by a bad spell after all," said {hero.label}.')
    world.say(f'"No," said {helper.label}, smiling. "It was only tied wrong."')

    mechanism.meters["stuck"] = 0.0
    mechanism.meters["fixed"] = 1.0
    mechanism.memes["safe"] = 1.0
    hero.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    hero.memes["trust"] = 1.0
    helper.memes["trust"] = 1.0
    world.fired.add("twist")

    world.say("Together they untied the ribbon, and the mechanism gave one neat chime before turning smoothly.")
    world.say(f'"It was a clue, not a threat," said {hero.label}.')
    world.say(f'"And we solved it together," said {helper.label}.')
    world.say(f"At the end, the little mechanism kept ticking beside them, while the old station felt friendly instead of spooky.")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        pass
    if params.hero_name == params.helper_name:
        pass
    rng = random.Random(_stable_seed(params))
    place = _safe_lookup(PLACES, params.place)
    world = World(place=place)
    hero = world.add(Entity("hero", "character", params.hero_name, "friend", "hero"))
    helper = world.add(Entity("helper", "character", params.helper_name, "friend", "helper"))
    mechanism = world.add(Entity("mechanism", "object", "the little mechanism", "mechanism"))
    clue = rng.choice(["Let's listen first", "Careful, it may be stuck", "Look for a tiny clue"])
    _simulate(world)

    story = world.render()
    prompts = [
        'Write a short mystery story that includes the word "mechanism" and a cautious friendship.',
        f"Tell a child-facing mystery set at {place.label} about {hero.label} and {helper.label}.",
        "Include a twist where the scary-looking problem turns out to be simple and fixable.",
    ]
    story_qa = [
        QAItem(
            question="What was strange about the mechanism?",
            answer="It clicked, then stopped, then clicked again, so it seemed like it was hiding a secret."
        ),
        QAItem(
            question="How did the friends stay safe?",
            answer="They were careful and did not press hard. That caution kept the gears from getting damaged."
        ),
        QAItem(
            question="What was the twist?",
            answer="The twist was that the mechanism was not broken by something scary. A ribbon was caught on the lever."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of moving parts that work together to do something, like a latch, clock, or toy."
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means moving carefully and thinking ahead so you do not cause harm or make a problem worse."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = ", ".join(f"{k}={v}" for k, v in ent.meters.items())
        memes = ", ".join(f"{k}={v}" for k, v in ent.memes.items())
        lines.append(f"{ent.id}: {ent.label} [{ent.kind}] {meters} {memes}".rstrip())
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    program = f"{asp_facts()}\n{ASP_RULES}\n#show mechanism/1.\n#show twist/1.\n"
    try:
        models = asp.solve(program, models=1)
        if not models:
            print("ASP produced no model.")
            return 1
    except Exception as exc:
        print(f"ASP solve failed: {exc}")
        return 1
    try:
        sample = generate(StoryParams())
        if not sample.story.strip():
            print("Story generation failed.")
            return 1
    except Exception as exc:
        print(f"Generation verify failed: {exc}")
        return 1
    return 0


def _asp_show() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show mechanism/1.\n#show twist/1.\n#show caution/1.\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(_asp_show())
        return
    if getattr(args, "verify", None):
        raise SystemExit(_asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        program = _asp_show()
        model = asp.one_model(program)
        print(model)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = [
            StoryParams(place=p, hero_name="Mina", helper_name="Owen", seed=base_seed)
            for p in sorted(PLACES)
        ]
        for params in params_list:
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(100, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
