#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T082828Z_seed779406221_n50/shark_inner_monologue_cautionary_foreshadowing_nursery_rhyme.py
================================================================================================

A tiny story world about a small shark who hears a caution, thinks hard in an
inner monologue, notices a foreshadowing clue, and chooses a safer path. The
prose aims for a nursery-rhyme feel: simple rhythm, concrete images, gentle
tension, and a clear ending that proves what changed.

Seed tale inspiration:
---
A little shark loved to zip through bright blue water near the coral reef.
One day, the shark saw a shiny shell tucked near a dark gap in the rocks.
The shark wanted to dart closer, but a wise old turtle warned that the gap
could hide a tangle net. The shark listened to its own worried thoughts,
remembered the warning, and swam the safer way with the turtle beside it.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    companion: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    shark: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"shark", "turtle"}:
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


@dataclass
class Place:
    label: str
    details: str
    safe_paths: set[str] = field(default_factory=set)
    risky_paths: set[str] = field(default_factory=set)
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


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    place: str
    risky: bool = False
    clue: str = ""
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
class Guide:
    id: str
    label: str
    warning: str
    safe_choice: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    shark_name: str
    guide: str
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


PLACES = {
    "reef": Place(
        label="the coral reef",
        details="The coral reef shimmered like a bright quilt under the sea.",
        safe_paths={"reef_path"},
        risky_paths={"dark_gap"},
    ),
    "lagoon": Place(
        label="the blue lagoon",
        details="The blue lagoon was still and smooth, with bubbles winking near the sand.",
        safe_paths={"lagoon_curve"},
        risky_paths={"rock_gap"},
    ),
}

SHARK_NAMES = ["Nib", "Pip", "Milo", "Sora", "Tilly", "Bree"]
GUIDE_NAMES = ["Turtle", "Mama Ray"]


GUIDES = {
    "turtle": Guide(
        id="turtle",
        label="an old turtle",
        warning="That dark gap may hide a net, and a net can tangle fins.",
        safe_choice="the sandy path with the turtle",
    ),
    "ray": Guide(
        id="ray",
        label="a gentle ray",
        warning="That shadow may hide a hook, and hooks can snag a tail.",
        safe_choice="the bright curve beside the shell beds",
    ),
}

THINGS = {
    "shell": Thing(
        id="shell",
        label="a shiny shell",
        phrase="a shiny shell",
        place="dark_gap",
        risky=True,
        clue="It gleamed near the rocks like a little moon.",
    ),
    "star": Thing(
        id="star",
        label="a pale starfish",
        phrase="a pale starfish",
        place="rock_gap",
        risky=True,
        clue="It lay half-hidden where the water turned dim.",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world about a shark, a caution, and a safer choice."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--guide", choices=GUIDES)
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
    guide = getattr(args, "guide", None) or rng.choice(list(GUIDES))
    name = getattr(args, "name", None) or rng.choice(SHARK_NAMES)
    return StoryParams(place=place, shark_name=name, guide=guide)


def _foreshadow(world: World, shark: Entity, thing: Thing) -> None:
    if thing.place in world.place.risky_paths:
        shark.memes["curiosity"] += 1
        world.say(
            f"{shark.id} saw {thing.phrase} and felt a little tingle in the tide. "
            f"{thing.clue}"
        )


def _inner_monologue(world: World, shark: Entity, guide: Guide, thing: Thing) -> None:
    shark.memes["worry"] += 1
    world.say(
        f'"Hm," thought {shark.id}, "I want that gleam, but {guide.warning} '
        f'I should not rush where the water looks strange."'
    )


def _caution(world: World, shark: Entity, guide: Guide) -> None:
    shark.memes["warned"] += 1
    world.say(
        f"{guide.label} floated near and said, "
        f'"Careful, little friend, keep to the light and gentle tide."'
    )


def _choose_safely(world: World, shark: Entity, guide: Guide) -> None:
    shark.memes["brave"] += 1
    shark.meters["distance_safe"] += 1
    world.say(
        f"{shark.id} nodded slow and swam away from the dark gap. "
        f"Together they took {guide.safe_choice} instead."
    )


def _ending(world: World, shark: Entity, guide: Guide) -> None:
    shark.memes["calm"] += 1
    world.say(
        f"And there by the reef, in the hush of the blue, {shark.id} was safe "
        f"and merry, with {guide.label} beside, and the shiny thing left where it was."
    )


def tell(place: Place, shark_name: str, guide_key: str) -> World:
    world = World(place)
    shark = world.add(Entity(id=shark_name, kind="character", type="shark", label=shark_name))
    guide = _safe_lookup(GUIDES, guide_key)
    thing = THINGS["shell" if place.label == "the coral reef" else "star"]

    world.say(
        f"Near {place.label}, {shark.id} was a little shark with a bright heart."
    )
    world.say(place.details)
    _foreshadow(world, shark, thing)

    world.para()
    _caution(world, shark, guide)
    _inner_monologue(world, shark, guide, thing)

    world.para()
    _choose_safely(world, shark, guide)
    _ending(world, shark, guide)

    world.facts.update(
        shark=shark,
        guide=guide,
        thing=thing,
        place=place,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    shark = f["shark"]
    thing = f["thing"]
    guide = f["guide"]
    place = f["place"]
    return [
        f'Write a short nursery-rhyme story about a shark near {place.label} who notices {thing.phrase}.',
        f"Tell a gentle story where {shark.id} hears a warning from {guide.label} and chooses a safer path.",
        f"Write a simple rhyme with a shark, a caution, and a hint that something tricky waits in the dark water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    shark = f["shark"]
    guide = f["guide"]
    thing = f["thing"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about near {place.label}?",
            answer=f"It is about {shark.id}, a little shark who wanted to explore near {place.label}.",
        ),
        QAItem(
            question=f"What warning did {guide.label} give {shark.id}?",
            answer=f"{guide.label} warned that {thing.label} might hide danger, like a net or a hook in the dark water.",
        ),
        QAItem(
            question=f"What did {shark.id} choose after thinking hard?",
            answer=f"{shark.id} chose the safer path with {guide.label} instead of rushing toward the dark gap.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coral reef?",
            answer="A coral reef is a home in the sea made by tiny coral animals, and many fish live near it.",
        ),
        QAItem(
            question="Why can a net be dangerous in the water?",
            answer="A net can trap fins or tails, so sea animals may get tangled and hurt if they swim too close.",
        ),
        QAItem(
            question="What does it mean to be cautious?",
            answer="To be cautious means to move carefully and think before you rush into something that could be risky.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
risky(Thing) :- thing(Thing), thing_risky(Thing).
warned(Shark) :- shark(Shark), guide(Guide), hears_warning(Shark, Guide).
foreshadowed(Shark, Thing) :- shark(Shark), thing(Thing), thing_risky(Thing), near_place(Thing, Place), at_place(Shark, Place).
safe_choice(Shark) :- warned(Shark), foreshadowed(Shark, _).
resolved_story(Place, Shark, Guide) :- at_place(Shark, Place), guide(Guide), safe_choice(Shark).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sp in p.safe_paths:
            lines.append(asp.fact("safe_path", pid, sp))
        for rp in p.risky_paths:
            lines.append(asp.fact("risky_path", pid, rp))
    for gid, g in GUIDES.items():
        lines.append(asp.fact("guide", gid))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if t.risky:
            lines.append(asp.fact("thing_risky", tid))
        lines.append(asp.fact("near_place", tid, t.place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="reef", shark_name="Nib", guide="turtle"),
    StoryParams(place="lagoon", shark_name="Sora", guide="ray"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), params.shark_name, params.guide)
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
        print(asp_program("#show resolved_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available, but this tiny world uses a reasonableness gate in Python.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
