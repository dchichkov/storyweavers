#!/usr/bin/env python3
"""
Storyworld: flooded street curiosity pirate tale.

A small, self-contained story simulation about a curious pirate child exploring
a flooded street, discovering danger, and developing a safer plan with a grownup.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

WORLD_NAME = "flooded_street_curiosity_pirate_tale"



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
class StoryParams:
    name: str
    ship: str
    treasure: str
    adult: str
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = None
    memes: dict[str, float] = None

    adult: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = __import__('collections').defaultdict(float)
        if self.memes is None:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.zone: set[str] = set()
        self.water_high: bool = True

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


THRESHOLD = 1.0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Curious pirate story in a flooded street.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--adult", choices=["mother", "father", "captain"])
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


NAMES = ["Mira", "Nico", "Lena", "Owen", "Pip", "Tessa", "Arlo", "June"]
SHIPS = {
    "little_boat": "little boat",
    "cardboard_ship": "cardboard ship",
    "toy_ship": "toy ship",
}
TREASURES = {
    "shell_map": "shiny shell map",
    "gold_coin": "bright gold coin",
    "red_flag": "red pirate flag",
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [("flooded_street", ship, treasure) for ship in SHIPS for treasure in TREASURES]


def explain_rejection(ship: str, treasure: str) -> str:
    return f"(No story: {ship} and {treasure} do not make an impossible pair in this world.)"


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "flooded_street")]
    for s in SHIPS:
        lines.append(asp.fact("ship", s))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    lines.append(asp.fact("weather", "floodwater"))
    return "\n".join(lines)


ASP_RULES = r"""
% A curious child wants to explore when the street is flooded.
curious(child) :- child(X), desire(X), flooded(street).

% If the street is flooded and the child is curious, the grownup worries.
worry(A) :- child(A), curious(A), flooded(street).

% A safer plan develops when the child listens and stays on the curb.
safe_plan(A) :- worry(A), helper(H), curb(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f'Write a pirate-style story for a young child named {hero.id} who feels curiosity in a flooded street.',
        f"Tell a gentle tale where {hero.id} wants to explore the flooded street but learns a safer way to look at the water.",
        f'Write a short story that includes the word "develop" and ends with a pirate child choosing a smart plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    adult: Entity = _safe_fact(world, f, "adult")
    ship = _safe_fact(world, f, "ship")
    treasure = _safe_fact(world, f, "treasure")
    return [
        QAItem(
            question=f"Who is the curious pirate child in the story?",
            answer=f"The curious pirate child is {hero.id}.",
        ),
        QAItem(
            question=f"Why did {adult.label} worry when {hero.id} wanted to go farther into the flooded street?",
            answer=f"{adult.label} worried because the street was flooded, the water could hide a hole, and {hero.id} might slip while chasing the {treasure}.",
        ),
        QAItem(
            question=f"What safer plan did they develop together?",
            answer=f"They developed a safer plan to stay on the curb, use the {ship} as a lookout, and watch the water from dry ground.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does flooded mean?",
            answer="Flooded means covered with too much water.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to look, ask, and learn about something new.",
        ),
        QAItem(
            question="Why should children be careful near deep water?",
            answer="Children should be careful near deep water because it can hide slippery ground and dangerous holes.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={e.meters} memes={e.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    ship = getattr(args, "ship", None) or rng.choice(list(SHIPS))
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    adult = getattr(args, "adult", None) or rng.choice(["mother", "father", "captain"])
    if ship not in SHIPS or treasure not in TREASURES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, ship=ship, treasure=treasure, adult=adult)


def _narrate_intro(world: World, hero: Entity, adult: Entity, ship_label: str, treasure_label: str) -> None:
    world.say(
        f"{hero.id} was a little pirate with bright eyes and a curious heart."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} loved {treasure_label} and dreamed of a grand voyage."
    )
    world.say(
        f"One day, {hero.id} and {adult.label} found a flooded street shining like a silver sea."
    )
    world.say(
        f"Near the curb, there was a {ship_label} waiting like a tiny ship at harbor."
    )


def _r_curious(world: World) -> list[str]:
    out: list[str] = []
    hero: Entity = world.get("hero")
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return out
    sig = "curious_once"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.say(f"{hero.id} leaned forward, full of curiosity, and tried to step toward the deeper water.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero: Entity = world.get("hero")
    adult: Entity = world.get("adult")
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return out
    sig = "worry_once"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    adult.memes["worry"] = adult.memes.get("worry", 0) + 1
    world.say(
        f"{adult.label} подня? "
    )
    return out

def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero: Entity = world.get("hero")
    adult: Entity = world.get("adult")
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return out
    sig = "worry_once"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    adult.memes["worry"] = adult.memes.get("worry", 0) + 1
    world.say(
        f"{adult.label} grew worried, because the water could hide stones, holes, and rushing bits of trash."
    )
    return out


def _r_resolution(world: World) -> list[str]:
    out: list[str] = []
    hero: Entity = world.get("hero")
    adult: Entity = world.get("adult")
    if adult.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = "resolution_once"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    hero.memes["curiosity"] = 0
    world.say(
        f"Then they developed a safer plan: {hero.id} stayed on the curb, used the little ship as a lookout, and watched the floodwater without wading in."
    )
    world.say(
        f"{hero.id} still felt curious, but now the curiosity was wise instead of wild."
    )
    return out


def tell(name: str, ship: str, treasure: str, adult_kind: str) -> World:
    world = World()
    hero = world.add(Entity(id=name, kind="character", type="child", meters={}, memes={"curiosity": 1.0}))
    adult = world.add(Entity(id="adult", kind="character", type=adult_kind, label=f"the {adult_kind}", meters={}, memes={}))
    world.add(Entity(id="ship", kind="thing", type=ship, label=_safe_lookup(SHIPS, ship)))
    world.add(Entity(id="treasure", kind="thing", type=treasure, label=_safe_lookup(TREASURES, treasure)))

    world.facts.update(hero=hero, adult=adult, ship=ship, treasure=treasure)

    _narrate_intro(world, hero, adult, _safe_lookup(SHIPS, ship), _safe_lookup(TREASURES, treasure))
    world.para()
    _r_curious(world)
    _r_worry(world)
    _r_resolution(world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.ship, params.treasure, params.adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
    StoryParams(name="Mira", ship="little_boat", treasure="shell_map", adult="captain"),
    StoryParams(name="Nico", ship="cardboard_ship", treasure="gold_coin", adult="mother"),
    StoryParams(name="Tessa", ship="toy_ship", treasure="red_flag", adult="father"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = seed
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.ship} with {p.treasure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
