#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld with a single built-in turn:
a crew hears a roar, chases treasure, and ends in a bad ending
when the storm and the warning are ignored.

The story is still state-driven: ship, weather, crew morale, cargo,
and treasure ownership all matter to the prose.
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

STYLES = {"pirate"}
LOCATIONS = {
    "deck": "the deck",
    "cove": "the cove",
    "reef": "the reef",
}
WEATHERS = {
    "calm": "calm seas",
    "storm": "a stormy sea",
}
TREASURES = {
    "map": ("a wrinkled map", "map"),
    "key": ("a brass key", "key"),
    "coin": ("a bright gold coin", "coin"),
}
CREW_NAMES = ["Nell", "Rory", "Mina", "Tess", "Jory", "Pip", "Wren", "Mack"]
CAPTAIN_NAMES = ["Captain Brine", "Captain Salt", "Captain Wave", "Captain Moss"]
TRAITS = ["bold", "quick", "loud", "restless", "curious", "brave"]



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
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    name: str
    place: str
    weather: str
    sails_up: bool = True
    lanterns_lit: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    ship: object | None = None
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
class StoryParams:
    style: str
    location: str
    weather: str
    treasure: str
    hero: str
    captain: str
    trait: str
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


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        nw = World(copy.deepcopy(self.ship))
        nw.entities = copy.deepcopy(self.entities)
        nw.fired = set(self.fired)
        nw.paragraphs = [[]]
        nw.facts = dict(self.facts)
        return nw


def _narrate_list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def ship_condition(ship: Ship) -> str:
    if ship.meters["damage"] >= 2:
        return "the ship was badly damaged"
    if ship.meters["water"] >= 1:
        return "the deck was slick with seawater"
    return "the ship was steady"


def raise_roar(world: World, hero: Entity) -> None:
    hero.memes["fear"] += 1
    world.ship.memes["fear"] += 1
    world.say(
        f"A roar rolled over the water, loud as thunder. {hero.id} froze for a moment, "
        f"because the sound made the whole ship feel smaller."
    )


def warn_about_storm(world: World, captain: Entity, hero: Entity) -> None:
    world.say(
        f'"That roar means trouble," {captain.id} said. "The storm is waking up, and we should turn back."'
    )
    hero.memes["hope"] += 1


def rush_for_treasure(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["panic"] += 1
    treasure.carried_by = hero.id
    world.say(
        f"But {hero.id} wanted the treasure more than the warning. "
        f"{hero.id} ran for {treasure.phrase} and clutched it tight."
    )


def storm_hits(world: World) -> None:
    if world.ship.weather == "a stormy sea":
        world.ship.meters["water"] += 1
        world.ship.meters["damage"] += 1
        world.ship.lanterns_lit = False
        world.ship.sails_up = False
        world.say(
            "Then the wind punched the sails, rain slapped the deck, and the lanterns went out."
        )


def bad_ending(world: World, hero: Entity, captain: Entity, treasure: Entity) -> None:
    hero.memes["fear"] += 2
    captain.memes["gloom"] += 1
    treasure.meters["lost"] += 1
    treasure.carried_by = None
    world.say(
        f"The rope snapped, {hero.id} skidded across the wet boards, and the {treasure.label} "
        f"slid into the dark sea."
    )
    world.say(
        f"{captain.id} reached for {hero.id}, but the waves rose between them. "
        f"In the end, the crew could only watch the treasure vanish below the foam."
    )


def tell(params: StoryParams) -> World:
    ship = Ship(name="The Little Gull", place=_safe_lookup(LOCATIONS, params.location), weather=_safe_lookup(WEATHERS, params.weather))
    world = World(ship)

    hero = world.add(Entity(id=params.hero, kind="character", type="pirate", label=params.hero))
    captain = world.add(Entity(id=params.captain, kind="character", type="captain", label=params.captain))
    treasure_label, treasure_key = _safe_lookup(TREASURES, params.treasure)
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure_key,
        label=treasure_key,
        phrase=treasure_label,
        owner=hero.id,
    ))

    world.say(
        f"On {world.ship.name}, {hero.id} was a {params.trait} pirate who loved shiny things and stormy tales."
    )
    world.say(
        f"{captain.id} kept the crew together while the ship waited near {world.ship.place}, "
        f"and {hero.id} found {treasure.phrase} tucked away like a secret."
    )

    world.para()
    world.say(
        f"One evening, the sea went quiet, and then a deep roar sounded over the waves."
    )
    raise_roar(world, hero)
    warn_about_storm(world, captain, hero)
    rush_for_treasure(world, hero, treasure)
    storm_hits(world)

    world.para()
    bad_ending(world, hero, captain, treasure)
    world.say(
        f"By morning, {ship_condition(world.ship)}, and the only thing left was salt on the wood and a sad hush."
    )

    world.facts.update(hero=hero, captain=captain, treasure=treasure, ship=ship, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short pirate story for a child that includes a loud "roar" and ends sadly at {_safe_lookup(LOCATIONS, p.location)}.',
        f"Tell a pirate tale where {p.hero} ignores {p.captain}'s warning, chases {_safe_lookup(TREASURES, p.treasure)[0]}, and the storm wins.",
        "Write a simple story about a pirate crew, a roaring sea, and a treasure that is lost in a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    treasure: Entity = _safe_fact(world, world.facts, "treasure")
    ship: Ship = _safe_fact(world, world.facts, "ship")
    return [
        QAItem(
            question=f"What kind of story is this about {p.hero} and the crew?",
            answer=f"It is a pirate story about {p.hero} on {ship.name} near {ship.place}.",
        ),
        QAItem(
            question=f"What did {p.hero} want after hearing the roar?",
            answer=f"{p.hero} wanted {treasure.phrase} and ran for it even though {p.captain} warned the crew.",
        ),
        QAItem(
            question=f"What happened to {treasure.phrase} at the end?",
            answer=f"The {p.treasure} was lost in the sea, so the story ends badly for the crew.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=(
                f"The storm hit, the rope snapped, and {p.hero} could not keep hold of the treasure. "
                f"The crew ended with only salt, rain, and an empty deck."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a roar sound like?",
            answer="A roar is a very loud sound, like thunder or a big animal calling out.",
        ),
        QAItem(
            question="What can a storm do to a ship?",
            answer="A storm can soak the deck, break sails, and make a ship hard to steer.",
        ),
        QAItem(
            question="Why is treasure exciting in a pirate tale?",
            answer="Treasure is exciting because pirates imagine gold, maps, and secrets hidden in it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  ship     ({world.ship.name}) place={world.ship.place} weather={world.ship.weather}")
    lines.append(f"           meters={world.ship.meters} memes={world.ship.memes} sails_up={world.ship.sails_up} lanterns_lit={world.ship.lanterns_lit}")
    for e in list(world.entities.values()):
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(location: str, weather: str) -> str:
    return f"(No story: {location} with {weather} does not fit the bad-ending pirate setup.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a roar and a bad ending.")
    ap.add_argument("--style", choices=sorted(STYLES))
    ap.add_argument("--location", choices=sorted(LOCATIONS))
    ap.add_argument("--weather", choices=sorted(WEATHERS))
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--hero")
    ap.add_argument("--captain")
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    style = getattr(args, "style", None) or "pirate"
    if style not in STYLES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    location = getattr(args, "location", None) or rng.choice(list(LOCATIONS))
    weather = getattr(args, "weather", None) or rng.choice(list(WEATHERS))
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    hero = getattr(args, "hero", None) or rng.choice(CREW_NAMES)
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if location == "reef" and weather == "calm":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(style=style, location=location, weather=weather, treasure=treasure, hero=hero, captain=captain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
bad_ending(H,C,T) :- hears_roar(H), warned(C,H), wants_treasure(H,T), storm, lost_treasure(T).
compatible_story(L,W,T) :- location(L), weather(W), treasure(T), bad_ending(h,c,T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
    for w in WEATHERS:
        lines.append(asp.fact("weather", w))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    lines.append(asp.fact("hears_roar", "h"))
    lines.append(asp.fact("warned", "c", "h"))
    lines.append(asp.fact("wants_treasure", "h", "map"))
    lines.append(asp.fact("storm"))
    lines.append(asp.fact("lost_treasure", "map"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    clingo_set = set(asp.atoms(model, "compatible_story"))
    python_set = set((loc, weat, treas) for loc in LOCATIONS for weat in WEATHERS for treas in TREASURES if not (loc == "reef" and weat == "calm"))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for location in LOCATIONS:
            for weather in WEATHERS:
                for treasure in TREASURES:
                    params = StoryParams(
                        style="pirate",
                        location=location,
                        weather=weather,
                        treasure=treasure,
                        hero=CrewNames if False else "Nell",
                        captain="Captain Brine",
                        trait="bold",
                    )
                    samples.append(generate(params))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
