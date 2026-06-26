#!/usr/bin/env python3
"""
storyworlds/worlds/beetle_sound_effects_surprise_pirate_tale.py
===============================================================

A small standalone storyworld about a pirate crew, a beetle, sound effects,
and a cheerful surprise.

Premise:
- A little pirate crew is preparing for a quiet treasure check.
- A beetle turns up in an unexpected place and makes a dramatic sound.
- The noise startles the crew, but the surprise turns out to be friendly.
- The ending proves the ship has changed: the beetle becomes part of the
  celebration instead of the problem.

The world is intentionally tiny and classical: a handful of entities, a few
causal rules, and a child-facing story with a clear turn and resolution.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    beetle: object | None = None
    captain: object | None = None
    crew: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
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
class Ship:
    name: str = "the ship"
    place: str = "the deck"
    treasure_room: str = "the hold"
    is_quiet: bool = True
    sound_level: float = 0.0
    world: object | None = None
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
class Beetle:
    id: str
    label: str = "beetle"
    sound: str = "skitter-scuttle"
    surprise: str = "a tiny surprise"
    jumpiness: float = 1.0
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
class CrewMood:
    calm: float = 0.0
    surprise: float = 0.0
    delight: float = 0.0
    worry: float = 0.0
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
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
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
        clone = World(_copy.deepcopy(self.ship))
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    beetle = world.entities.get("beetle")
    crew = world.entities.get("crew")
    if not beetle or not crew:
        return out
    if beetle.memes.get("startled", 0.0) < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.ship.sound_level += 1.0
    crew.memes["surprise"] = crew.memes.get("surprise", 0.0) + 1.0
    out.append(f"Skitter-scuttle! went the beetle across the deck.")
    out.append(f"The sound bounced under the sails and made every pirate look up.")
    return out


def _r_turn_delight(world: World) -> list[str]:
    out: list[str] = []
    beetle = world.entities.get("beetle")
    crew = world.entities.get("crew")
    if not beetle or not crew:
        return out
    if crew.memes.get("surprise", 0.0) < THRESHOLD:
        return out
    sig = ("delight",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew.memes["delight"] = crew.memes.get("delight", 0.0) + 1.0
    crew.memes["worry"] = 0.0
    beetle.memes["safe"] = 1.0
    out.append(f"Then the surprise turned soft and friendly, like a joke with a wink.")
    return out


CAUSAL_RULES = [
    _r_noise,
    _r_turn_delight,
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


@dataclass
class StoryParams:
    ship_name: str = "the Lucky Gull"
    hero_name: str = "Mina"
    hero_type: str = "girl"
    captain_name: str = "Captain Bram"
    beetle_name: str = "Blinky"
    seed: Optional[int] = None
    params: object | None = None
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


SHIPS = [
    "the Lucky Gull",
    "the Bright Kestrel",
    "the Wobbly Wave",
]

HEROES = [
    ("Mina", "girl"),
    ("Ned", "boy"),
    ("Pip", "boy"),
    ("Luna", "girl"),
]

CAPTAINS = [
    "Captain Bram",
    "Captain Sera",
    "Captain Wren",
]

BEETLES = [
    "Blinky",
    "Dot",
    "Nib",
    "Sprig",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world with beetle sound effects and a surprise.")
    ap.add_argument("--ship-name", choices=SHIPS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--captain-name", choices=CAPTAINS)
    ap.add_argument("--beetle-name")
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
    return StoryParams(
        ship_name=getattr(args, "ship_name", None) or rng.choice(SHIPS),
        hero_name=getattr(args, "hero_name", None) or rng.choice([n for n, _ in HEROES if not getattr(args, "hero_type", None) or _ == getattr(args, "hero_type", None)]),
        hero_type=getattr(args, "hero_type", None) or rng.choice(["girl", "boy"]),
        captain_name=getattr(args, "captain_name", None) or rng.choice(CAPTAINS),
        beetle_name=getattr(args, "beetle_name", None) or rng.choice(BEETLES),
    )


def make_world(params: StoryParams) -> World:
    world = World(Ship(name=params.ship_name))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name, traits=["little", "brave"]))
    captain = world.add(Entity(id="captain", kind="character", type="pirate", label=params.captain_name, traits=["patient"]))
    crew = world.add(Entity(id="crew", kind="character", type="pirate", label="the crew", plural=True))
    beetle = world.add(Entity(id="beetle", kind="creature", type="thing", label=params.beetle_name, traits=["tiny"], location=world.ship.place))
    world.facts.update(hero=hero, captain=captain, crew=crew, beetle=beetle, params=params)
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero = world.get("hero")
    captain = world.get("captain")
    crew = world.get("crew")
    beetle = world.get("beetle")

    world.say(f"On {world.ship.name}, little {hero.label} helped {captain.label} look for treasure.")
    world.say(f"{hero.label} liked the creak of ropes, the flap of sails, and the salty air.")

    world.para()
    world.say(f"Near the hatch, {hero.label} spotted a tiny beetle named {beetle.label}.")
    world.say(f"It sat still for one blink, then made a big {beetle.sound} as it zipped across a plank.")

    beetle.memes["startled"] = 1.0
    crew.memes["worry"] = 1.0
    propagate(world)

    world.para()
    world.say(f"Everyone jumped at the sound, but {hero.label} giggled first.")
    world.say(f"{hero.label} whispered that the beetle sounded like a marching drum in a very tiny parade.")
    world.say(f"At that, {captain.label} smiled and lifted a crumb of biscuit for the beetle.")

    world.para()
    world.say(f"The beetle climbed onto the biscuit and the pirates made its funny {beetle.sound} sound again, only this time they laughed with it.")
    world.say(f"By the end, the deck was calm, the beetle was safe, and the ship felt full of a happy surprise.")

    world.facts.update(
        ship_name=params.ship_name,
        hero_name=params.hero_name,
        captain_name=params.captain_name,
        beetle_name=params.beetle_name,
        sound=beetle.sound,
        surprise=beetle.surprise,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short pirate tale for a young child that includes the sound "skitter-scuttle" and a beetle surprise.',
        f"Tell a simple story on a ship where {p.hero_name} and {p.captain_name} meet a beetle and turn a scare into a laugh.",
        f"Write a child-friendly pirate story about {p.hero_name}, a beetle, and a funny sound effect.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    return [
        QAItem(
            question=f"Who found the beetle on the ship?",
            answer=f"{p.hero_name} found the beetle while helping on {p.ship_name}.",
        ),
        QAItem(
            question=f"What sound did the beetle make?",
            answer="The beetle made a skitter-scuttle sound as it zipped across the deck.",
        ),
        QAItem(
            question=f"What changed from the start of the story to the end?",
            answer="At first the sound startled everyone, but in the end the beetle became a happy surprise and the crew laughed instead of worrying.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beetle?",
            answer="A beetle is a small insect with a hard shell and six legs.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word or phrase that helps readers imagine a noise, like a skitter, bang, or swoosh.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that makes someone stop and look or feel excited.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  ship.sound_level={world.ship.sound_level}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
beetle(B) :- beetle_name(B).
hero(H) :- hero_name(H).
crew(c) :- true.
startled(B) :- beetle(B).
noise :- startled(_).
surprise :- noise.
delight :- surprise.
#show surprise/0.
#show delight/0.
#show noise/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("beetle_name", "Blinky"),
        asp.fact("beetle_name", "Dot"),
        asp.fact("beetle_name", "Nib"),
        asp.fact("beetle_name", "Sprig"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show surprise/0.\n#show delight/0.\n"))
    if any(sym.name == "surprise" for sym in model) and any(sym.name == "delight" for sym in model):
        print("OK: ASP rules produce surprise and delight.")
        return 0
    print("MISMATCH: ASP did not produce expected atoms.")
    return 1


def build_sample(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show surprise/0.\n#show delight/0.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, name in enumerate(BEETLES):
            params = StoryParams(
                ship_name=_safe_lookup(SHIPS, i % len(SHIPS)),
                hero_name=_safe_lookup(HEROES, i % len(HEROES))[0],
                hero_type=_safe_lookup(HEROES, i % len(HEROES))[1],
                captain_name=_safe_lookup(CAPTAINS, i % len(CAPTAINS)),
                beetle_name=name,
                seed=base_seed + i,
            )
            samples.append(build_sample(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = build_sample(params)
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
