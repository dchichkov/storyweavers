#!/usr/bin/env python3
"""
A standalone storyworld for a tiny pirate tale with a peaceful, happy ending.

Seed premise:
- Pirate tale style
- Includes peace
- Happy ending
- Small simulated domain with concrete state changes
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

    captain: object | None = None
    crew: object | None = None
    rivals: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pirate", "captain", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
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
class Harbor:
    name: str = "the sunny harbor"
    tide: str = "calm"
    wind: str = "soft"
    peace: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    harbor: object | None = None
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
class Treasure:
    id: str
    label: str
    phrase: str
    shiny: bool = True
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
    hero_name: str = "Finn"
    crew_name: str = "the Sea Star crew"
    rival_name: str = "the island folk"
    treasure: str = "golden compass"
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
    def __init__(self, harbor: Harbor):
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


def make_world(params: StoryParams) -> World:
    harbor = Harbor()
    world = World(harbor)

    captain = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="pirate",
        label=params.hero_name,
        meters={"boldness": 1.0},
        memes={"greed": 0.0, "peace": 0.0, "joy": 0.0},
    ))
    crew = world.add(Entity(
        id="crew",
        kind="group",
        type="pirate_crew",
        label=params.crew_name,
        meters={"sail_power": 1.0},
        memes={"hunger": 0.2, "worry": 0.0},
    ))
    rivals = world.add(Entity(
        id="rivals",
        kind="group",
        type="islanders",
        label=params.rival_name,
        meters={"shore_watch": 1.0},
        memes={"worry": 0.6, "anger": 0.2},
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=params.treasure,
        phrase=f"a {params.treasure}",
        owner="rivals",
        carried_by=None,
        meters={"value": 1.0},
        memes={"shine": 1.0},
    ))
    world.facts.update(captain=captain, crew=crew, rivals=rivals, treasure=treasure)
    return world


def raise_tension(world: World) -> None:
    captain = world.get("Finn")
    crew = world.get("crew")
    rivals = world.get("rivals")
    treasure = world.get("treasure")

    world.say(
        f"Captain {captain.label} sailed with {crew.label} into {world.harbor.name}, "
        f"where the wind was soft and the tide was calm."
    )
    world.say(
        f"They had heard that {rivals.label} kept {treasure.phrase} on the shore, "
        f"and the crew's eyes went wide with pirate greed."
    )
    captain.memes["greed"] += 1.0
    crew.memes["hunger"] += 0.5
    rivals.memes["worry"] += 0.7
    world.harbor.meters["boats_near_shore"] = 1.0


def peace_turn(world: World) -> None:
    captain = world.get("Finn")
    crew = world.get("crew")
    rivals = world.get("rivals")
    treasure = world.get("treasure")

    if world.fired.intersection({"peace_offer", "peace_accept"}):
        return

    world.para()
    world.say(
        f"When the captain saw the island folk standing by the water, he did not lift a sword. "
        f"Instead, he held up both hands and asked for peace."
    )
    world.fired.add("peace_offer")
    captain.memes["peace"] += 1.0
    rivals.memes["worry"] -= 0.2
    rivals.memes["anger"] = max(0.0, rivals.memes["anger"] - 0.1)

    if captain.memes["greed"] >= 1.0:
        world.say(
            f"The crew still wanted the {treasure.label}, but the captain saw that a fight would only bruise the harbor."
        )

    world.say(
        f"The island folk listened, and then they showed the captain why the treasure mattered: "
        f"it was a compass that guided boats away from the rocks."
    )
    world.fired.add("peace_accept")
    world.harbor.peace = True
    treasure.owner = "shared"
    treasure.carried_by = "Finn"
    treasure.memes["shine"] += 0.2
    crew.memes["worry"] = max(0.0, crew.memes["worry"] - 0.2)
    rivals.memes["worry"] = max(0.0, rivals.memes["worry"] - 0.5)


def happy_ending(world: World) -> None:
    captain = world.get("Finn")
    crew = world.get("crew")
    rivals = world.get("rivals")
    treasure = world.get("treasure")

    world.para()
    world.say(
        f"So the captain and the island folk shared the {treasure.label} and used it to guide every ship safely past the rocks."
    )
    world.say(
        f"By sunset, the crew waved from the deck, the island folk waved from the shore, "
        f"and {world.harbor.name} felt warm with peace."
    )
    captain.memes["joy"] += 1.0
    crew.memes["sail_power"] += 0.2
    rivals.memes["joy"] = 1.0
    world.harbor.meters["safe_passage"] = 1.0
    world.harbor.memes["peace"] = 1.0


def tell(params: StoryParams) -> World:
    world = make_world(params)
    raise_tension(world)
    peace_turn(world)
    happy_ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    treasure: Entity = _safe_fact(world, f, "treasure")
    return [
        f'Write a short pirate tale for a child that includes the word "peace" and ends happily.',
        f"Tell a story where Captain {f['captain'].label} visits a harbor, avoids a fight, and shares {treasure.phrase}.",
        f"Write a gentle pirate story about treasure, a calm harbor, and a peaceful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    treasure: Entity = _safe_fact(world, world.facts, "treasure")
    captain: Entity = _safe_fact(world, world.facts, "captain")
    rivals: Entity = _safe_fact(world, world.facts, "rivals")
    return [
        QAItem(
            question="What did Captain Finn ask for instead of starting a fight?",
            answer="Captain Finn asked for peace instead of starting a fight.",
        ),
        QAItem(
            question=f"What was special about the {treasure.label}?",
            answer=f"It was a compass that could guide boats safely away from the rocks.",
        ),
        QAItem(
            question=f"Who shared the {treasure.label} in the end?",
            answer=f"Captain {captain.label} and {rivals.label} shared it so everyone could use it safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does peace mean?",
            answer="Peace means people are calm, safe, and not fighting.",
        ),
        QAItem(
            question="What is a compass for?",
            answer="A compass helps sailors know which way to go.",
        ),
        QAItem(
            question="Why do ships need to stay away from rocks?",
            answer="Rocks can damage a ship, so sailors steer away from them to stay safe.",
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
    lines.append(
        f"harbor: name={world.harbor.name!r} tide={world.harbor.tide!r} wind={world.harbor.wind!r} peace={world.harbor.peace}"
    )
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A harbor story is reasonable when peace replaces conflict and the treasure
% ends up shared instead of stolen.
conflict(harbor) :- greedy(crew), guarded(rivals).
peaceful(harbor) :- asks_for_peace(captain), listens(rivals).
shared_treasure(T) :- treasure(T), peaceful(harbor).

valid_story :- peaceful(harbor), shared_treasure(_).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("captain", "Finn"),
        asp.fact("crew", "crew"),
        asp.fact("rivals", "rivals"),
        asp.fact("treasure", "treasure"),
        asp.fact("greedy", "crew"),
        asp.fact("guarded", "rivals"),
        asp.fact("asks_for_peace", "Finn"),
        asp.fact("listens", "rivals"),
        asp.fact("treasure", "treasure"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale world with peace and a happy ending.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name", default="Finn")
    ap.add_argument("--treasure", default="golden compass")
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
    return StoryParams(
        hero_name=getattr(args, "name", None) or rng.choice(["Finn", "Nate", "Rory", "Mara"]),
        treasure=getattr(args, "treasure", None) or rng.choice(["golden compass", "silver key", "pearl map"]),
        seed=getattr(args, "seed", None),
    )


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


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/0.")
    model = asp.one_model(program)
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP program derives a valid peaceful story.")
        return 0
    print("MISMATCH: ASP program did not derive valid_story.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print(f"valid_story atoms: {len([s for s in model if s.name == 'valid_story'])}")
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(resolve_params(args, rng))]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i))
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
