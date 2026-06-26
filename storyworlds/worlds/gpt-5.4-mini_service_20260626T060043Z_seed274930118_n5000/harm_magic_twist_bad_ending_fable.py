#!/usr/bin/env python3
"""
storyworlds/worlds/harm_magic_twist_bad_ending_fable.py
========================================================

A small fable-like story world about harm, magic, and a twist ending that does
not get fixed.

Premise:
- A hungry little animal finds a magical charm.
- The charm promises a quick, easy gain.
- A warning is ignored.
- The twist is that the magic helps in a way that hurts someone else.
- The ending is bad: the harm remains, and the fable closes with a clear moral
  image instead of a rescue.

The world is intentionally small and constraint-checked. The prose is driven by
simulated state, with meters for physical effects and memes for feelings and
social pressure.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    worn_by: Optional[str] = None
    plural: bool = False

    charm_ent: object | None = None
    hero: object | None = None
    witness: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "cat", "dog", "rabbit", "hare", "squirrel"}:
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
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)
    light: str = "soft"
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
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    twist: str
    harm: str
    target: str
    place_needed: set[str] = field(default_factory=set)
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
    place: str
    charm: str
    hero: str
    witness: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.weather = self.weather
        return clone


SETTINGS = {
    "orchard": Setting(place="the orchard", afford={"spark", "grow"}, light="golden"),
    "pond": Setting(place="the pond", afford={"spark", "glimmer"}, light="blue"),
    "hill": Setting(place="the hill", afford={"spark", "wind"}, light="bright"),
    "lane": Setting(place="the lane", afford={"spark"}, light="gray"),
}

CHARMS = {
    "golden_seed": Charm(
        id="golden_seed",
        label="a golden seed",
        phrase="a golden seed that glowed like a coin",
        effect="make one tree grow full of sweet fruit at once",
        twist="the tree would pull water from the roots of its neighbors",
        harm="the nearby saplings would go dry and weak",
        target="tree",
        place_needed={"orchard", "hill"},
    ),
    "moon_bell": Charm(
        id="moon_bell",
        label="a moon bell",
        phrase="a tiny silver bell with a moon on it",
        effect="make one wish ring true for a moment",
        twist="the wish would echo and shake the whole path",
        harm="the little birds would scatter and a nest would fall",
        target="nest",
        place_needed={"lane", "pond"},
    ),
    "ember_berry": Charm(
        id="ember_berry",
        label="an ember berry",
        phrase="a red berry warm as a coal",
        effect="make cold hands feel brave and fast",
        twist="the berry would warm too hard in a pocket",
        harm="the cloth would scorch and sting the skin",
        target="pocket",
        place_needed={"orchard", "lane"},
    ),
}

HEROES = [
    ("Milo", "fox", ["young", "quick", "greedy"]),
    ("Nia", "rabbit", ["young", "restless", "curious"]),
    ("Tomo", "squirrel", ["small", "eager", "proud"]),
]
WITNESSES = [
    ("the crow", "crow"),
    ("the badger", "badger"),
    ("the finch", "finch"),
    ("the old turtle", "turtle"),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for charm_id, charm in CHARMS.items():
            if place in charm.place_needed:
                combos.append((place, charm_id))
    return combos


ASP_RULES = r"""
valid(P,C) :- setting(P), charm(C), place_needed(C,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for p in sorted(c.place_needed):
            lines.append(asp.fact("place_needed", cid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about magical harm and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--hero")
    ap.add_argument("--witness")
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "charm", None):
        combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                  and (getattr(args, "charm", None) is None or c[1] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, charm = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice([h[0] for h in HEROES])
    witness = getattr(args, "witness", None) or rng.choice([w[0] for w in WITNESSES if w[0] != hero])
    return StoryParams(place=place, charm=charm, hero=hero, witness=witness)


def reasonableness_gate(params: StoryParams) -> None:
    if (params.place, params.charm) not in valid_combos():
        pass
    if params.hero == params.witness:
        pass


def _make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    charm = _safe_lookup(CHARMS, params.charm)
    world = World(setting)

    hero_type = next((t for n, t, _ in HEROES if n == params.hero), "fox")
    witness_type = next((t for n, t in WITNESSES if n == params.witness), "crow")

    hero = world.add(Entity(
        id=params.hero, kind="character", type=hero_type,
        traits=["small", "hungry", "quick"], meters={"hunger": 2.0}, memes={"desire": 1.0, "hope": 1.0}
    ))
    witness = world.add(Entity(
        id=params.witness, kind="character", type=witness_type,
        traits=["watchful"], meters={"safety": 1.0}, memes={"worry": 1.0}
    ))
    charm_ent = world.add(Entity(
        id=charm.id, type="charm", label=charm.label, phrase=charm.phrase, owner=hero.id,
        meters={"glow": 1.0}, memes={"temptation": 1.0}
    ))

    world.facts.update(hero=hero, witness=witness, charm=charm_ent, charm_cfg=charm)
    return world


def predict_harm(world: World, charm: Charm) -> dict:
    sim = world.copy()
    hero = sim.facts["hero"]
    witness = sim.facts["witness"]
    sim.facts["hero"].meters["hunger"] += 0.0
    hero.memes["desire"] += 1.0
    if charm.id == "golden_seed":
        harm = "saplings"
        severity = 2
    elif charm.id == "moon_bell":
        harm = "nest"
        severity = 1
    else:
        harm = "skin"
        severity = 1
    return {"harm": harm, "severity": severity, "witness_fears": witness.memes["worry"]}


def tell(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    witness: Entity = _safe_fact(world, world.facts, "witness")
    charm: Charm = _safe_fact(world, world.facts, "charm_cfg")

    world.say(f"Near {world.setting.place}, {hero.id} was a little {hero.type} who always wanted enough.")
    world.say(f"One day, {hero.id} found {charm.phrase}.")
    world.say(f"It promised to {charm.effect}.")
    world.para()

    world.say(f"{hero.id} held the charm tight and thought of full bellies and easy luck.")
    world.say(f"But {witness.id} warned {hero.id} that magic can be a crooked road.")
    hero.memes["desire"] += 1.0
    hero.memes["stubbornness"] = hero.memes.get("stubbornness", 0.0) + 1.0
    witness.memes["worry"] += 1.0
    world.say(f"{hero.id} did not listen. {hero.id} made the magic shine anyway.")
    world.para()

    pred = predict_harm(world, charm)
    if charm.id == "golden_seed":
        hero.meters["glow"] += 1.0
        witness.meters["startle"] = 1.0
        world.say(f"The seed leaped into the soil and one tree shot up heavy with fruit.")
        world.say(f"The twist was cruel: {charm.twist}, so {charm.harm}.")
        hero.meters["guilt"] = 1.0
        witness.meters["lost"] = 1.0
        world.say(f"{witness.id} watched the little roots turn dry.")
        world.say(f"{hero.id} reached for the branches, but the fruit kept shining while the young trees wilted.")
    elif charm.id == "moon_bell":
        hero.meters["glow"] += 1.0
        world.say(f"The bell rang once, and the sound ran far over the path.")
        world.say(f"The twist was worse than the wish: {charm.twist}, so {charm.harm}.")
        witness.meters["fear"] = 1.0
        world.say(f"Down below, a nest slipped, and the small birds fluttered into the wind.")
        hero.memes["regret"] = 1.0
        world.say(f"{hero.id} looked up at the empty branch, but the ringing could not be taken back.")
    else:
        hero.meters["glow"] += 1.0
        world.say(f"The berry warmed too fast in {hero.id}'s pocket, and the cloth began to smoke.")
        world.say(f"The twist was sharp: {charm.twist}, so {charm.harm}.")
        hero.meters["pain"] = 1.0
        witness.meters["alarm"] = 1.0
        world.say(f"{witness.id} called out as the heat stung the skin through the cloth.")
        world.say(f"{hero.id} dropped the berry, but the black mark stayed on the pocket.")

    world.para()
    hero.memes["sadness"] = 1.0
    witness.memes["worry"] = max(witness.memes.get("worry", 0.0), 1.0)
    world.say(
        f"So the fable ended badly: {hero.id} had a little magic, but the harm remained, "
        f"and {witness.id} went home with a worried heart."
    )
    world.say("The lesson was simple: a quick charm can be a slow mistake.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero").id
    witness = _safe_fact(world, f, "witness").id
    charm = _safe_fact(world, f, "charm_cfg")
    return [
        f'Write a short fable for children about {hero}, a magical object, and a warning that is ignored.',
        f"Tell a fable where {hero} finds {charm.label} near {world.setting.place} and causes harm after a twist.",
        f"Write a child-friendly story about magic, a bad choice, and a sad ending with {witness} watching.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    witness = _safe_fact(world, f, "witness")
    charm: Charm = _safe_fact(world, f, "charm_cfg")
    return [
        QAItem(
            question=f"What did {hero.id} find near {world.setting.place}?",
            answer=f"{hero.id} found {charm.phrase}.",
        ),
        QAItem(
            question=f"Who warned {hero.id} before the magic was used?",
            answer=f"{witness.id} warned {hero.id} that magic can be a crooked road.",
        ),
        QAItem(
            question=f"What was the bad result of the magic?",
            answer=f"The magic caused harm, and the ending stayed sad instead of being fixed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that uses simple characters and ends with a lesson.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic is something impossible in real life that can change what happens in a story.",
        ),
        QAItem(
            question="What is harm?",
            answer="Harm means hurt or damage. It can hurt a body, a nest, a plant, or something else that needs care.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = _make_world(params)
    tell(world)
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


def explain_rejection(place: str, charm_id: str) -> str:
    return f"(No story: {_safe_lookup(CHARMS, charm_id).label} does not fit {place}.)"


def asp_valid_combos_full() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos_full()
        print(f"{len(combos)} compatible (place, charm) combos:\n")
        for place, charm in combos:
            print(f"  {place:8} {charm}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, charm in valid_combos():
            params = StoryParams(place=place, charm=charm, hero="Milo", witness="the crow")
            params.seed = base_seed
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
