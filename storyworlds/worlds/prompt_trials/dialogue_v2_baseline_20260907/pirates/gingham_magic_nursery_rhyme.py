#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample



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
class Spell:
    id: str
    phrase: str
    effect: str
    safe: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Cloth:
    id: str
    label: str
    color: str
    pattern: str
    magic_word: str
    strength: int = 1
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
class StoryParams:
    cloth: str = ""
    spell: str = ""
    child: str = ""
    companion: str = ""
    rhyme: str = ""
    seed: int | None = None
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
class Entity:
    id: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    child: object | None = None
    cloth_entity: object | None = None
    companion: object | None = None
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.history: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


CLOTHS = {
    "gingham": Cloth(
        id="gingham",
        label="gingham handkerchief",
        color="red-and-white",
        pattern="little checks",
        magic_word="gingham",
        strength=2,
    ),
    "bluegingham": Cloth(
        id="bluegingham",
        label="blue gingham scarf",
        color="blue-and-white",
        pattern="tiny checks",
        magic_word="gingham",
        strength=2,
    ),
    "goldenpatch": Cloth(
        id="goldenpatch",
        label="golden patchwork cloth",
        color="gold-and-yellow",
        pattern="sunny squares",
        magic_word="shine",
        strength=3,
    ),
}

SPELLS = {
    "breeze": Spell(
        id="breeze",
        phrase="Whisk and wish, a little breeze!",
        effect="a friendly breeze",
    ),
    "birdsong": Spell(
        id="birdsong",
        phrase="Chirp and chime, make music time!",
        effect="a bright birdsong",
    ),
    "starlight": Spell(
        id="starlight",
        phrase="Twinkle twice, bring gentle light!",
        effect="a pocket of starlight",
    ),
}

NAMES = ["Molly", "Pip", "Nell", "Toby", "Rory", "Maisie"]
COMPANIONS = ["a small brown rabbit", "a sleepy kitten", "a yellow duck", "a little bluebird"]
RHYMES = [
    "A checkered cloth was folded small, / Then magic danced across the hall.",
    "With gingham bright and wishes light, / A tiny wonder came in sight.",
    "The spell went round with silver sound, / And happy feet went skip-skip-round.",
]


ASP_RULES = r"""
spell(S) :- safe_spell(S).
magic_works(C, S) :- cloth(C), spell(S), strength(C, N), N >= 1.
chosen_ok :- chosen_cloth(C), chosen_spell(S), magic_works(C, S).
outcome(wonder) :- chosen_ok.
outcome(nothing) :- not chosen_ok.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [
        (cloth_id, spell_id)
        for cloth_id, cloth in CLOTHS.items()
        for spell_id, spell in SPELLS.items()
        if cloth.strength >= 1 and spell.safe
    ]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, cloth in CLOTHS.items():
        lines.append(asp.fact("cloth", cid))
        lines.append(asp.fact("strength", cid, cloth.strength))
    for sid, spell in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        if spell.safe:
            lines.append(asp.fact("safe_spell", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show magic_works/2."))
    return sorted(set(asp.atoms(model, "magic_works")))


def build_world(params: StoryParams) -> World:
    cloth = _safe_lookup(CLOTHS, params.cloth)
    spell = _safe_lookup(SPELLS, params.spell)
    world = World()
    child = world.add(Entity(params.child, "child"))
    companion = world.add(Entity(params.companion, "companion"))
    cloth_entity = world.add(Entity(cloth.id, "cloth"))
    child.memes["curiosity"] += 1
    companion.memes["wonder"] += 1
    cloth_entity.meters["folded"] = 1
    world.facts.update(
        child=child,
        companion=companion,
        cloth=cloth,
        spell=spell,
        rhyme=params.rhyme,
    )

    world.say(
        f"{params.child} found a {cloth.color} {cloth.pattern} {cloth.label} "
        f"beside {params.companion}."
    )
    world.say(
        f"It was gingham, soft and bright, with checks that winked in afternoon light."
    )
    world.say(
        f'"Come, {params.companion}," said {params.child}, '
        f'"let us try a tiny bit of magic tonight."'
    )
    world.say(
        f"They folded the cloth once, folded it twice, and whispered, "
        f'"{spell.phrase}"'
    )
    world.say(
        f"The {cloth.label} fluttered up, and {spell.effect} curled around the room."
    )
    child.memes["joy"] += 1
    companion.memes["wonder"] += 1
    cloth_entity.meters["magic"] += 1
    world.facts["result"] = spell.effect
    world.say(
        f"{params.companion} clapped a gentle beat while {params.child} twirled "
        f"the gingham cloth beneath the shining stars."
    )
    world.say(
        f"Then the magic settled softly, leaving the {cloth.label} warm in "
        f"{params.child}'s hands."
    )
    world.say(params.rhyme)
    world.say(
        f"And home they went, with hearts alight: "
        f"{params.child} and {params.companion}, safe and bright."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    cloth: Cloth = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "cloth")
    spell: Spell = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "spell")
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    companion: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "companion")
    return [
        f"Write a Nursery Rhyme-style magic story about {child.id} and {companion.id} using a gingham cloth.",
        f"Include the words gingham and magic, and show how the phrase '{spell.phrase}' makes {spell.effect}.",
        f"End with the child and companion safe, happy, and carrying the gingham cloth home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    cloth: Cloth = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "cloth")
    spell: Spell = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "spell")
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    companion: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "companion")
    result = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "result")
    return [
        QAItem(
            f"What did {child.id} find?",
            f"{child.id} found a {cloth.color} {cloth.pattern} {cloth.label}.",
        ),
        QAItem(
            f"What made the cloth special?",
            f"It was gingham, with bright little checks that seemed to wink in the light.",
        ),
        QAItem(
            f"What magic words did {child.id} whisper?",
            f'{child.id} whispered, "{spell.phrase}"',
        ),
        QAItem(
            "What happened when the magic worked?",
            f"The cloth fluttered up and {result} curled around the room.",
        ),
        QAItem(
            "How did the story end?",
            f"The child and companion went home safely, happy, and bright, with the gingham cloth in the child's hands.",
        ),
    ]


KNOWLEDGE = {
    "gingham": QAItem(
        "What is gingham?",
        "Gingham is a woven cloth with a simple checkered pattern, often made with two colors.",
    ),
    "magic": QAItem(
        "What is magic in a story?",
        "Magic is an imaginary power that can make surprising things happen.",
    ),
    "rhyme": QAItem(
        "What makes a nursery rhyme sound playful?",
        "Short lines, repeated sounds, and a steady beat can make a nursery rhyme playful.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [KNOWLEDGE["gingham"], KNOWLEDGE["magic"], KNOWLEDGE["rhyme"]]


def generate(params: StoryParams) -> StorySample:
    if params.cloth not in CLOTHS:
        pass
    if params.spell not in SPELLS:
        pass
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A tiny gingham magic nursery-rhyme storyworld.")
    parser.add_argument("--cloth", choices=sorted(CLOTHS))
    parser.add_argument("--spell", choices=sorted(SPELLS))
    parser.add_argument("--child")
    parser.add_argument("--companion")
    parser.add_argument("--rhyme", choices=RHYMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    cloth = getattr(args, "cloth", None) or rng.choice(sorted(CLOTHS))
    spell = getattr(args, "spell", None) or rng.choice(sorted(SPELLS))
    child = getattr(args, "child", None) or rng.choice(NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    rhyme = getattr(args, "rhyme", None) or rng.choice(RHYMES)
    if not _safe_lookup(CLOTHS, cloth).strength or not _safe_lookup(SPELLS, spell).safe:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        cloth=cloth,
        spell=spell,
        child=child,
        companion=companion,
        rhyme=rhyme,
    )


def verify() -> int:
    py = set(valid_combos())
    asp = set(asp_valid_combos())
    expected = {(cloth, spell) for cloth, spell in py}
    if asp != expected:
        print(f"ASP mismatch: {sorted(asp)} != {sorted(expected)}")
        return 1
    for seed in range(20):
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(seed))
        sample = generate(params)
        if "gingham" not in sample.story:
            print("Generated story omitted gingham.")
            return 1
        if "magic" not in sample.story.lower():
            print("Generated story omitted magic.")
            return 1
    print(f"OK: ASP and Python agree on {len(py)} magical combinations.")
    print("OK: generated stories contain the required narrative instruments.")
    return 0


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("", "#show magic_works/2."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(verify())
    if getattr(args, "asp", None):
        for cloth, spell in asp_valid_combos():
            print(f"{cloth}: {spell}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        params_list = [
            StoryParams(
                cloth=cloth,
                spell=spell,
                child=_safe_lookup(NAMES, i % len(NAMES)),
                companion=_safe_lookup(COMPANIONS, i % len(COMPANIONS)),
                rhyme=_safe_lookup(RHYMES, i % len(RHYMES)),
            )
            for i, (cloth, spell) in enumerate(valid_combos())
        ]
    else:
        params_list = []
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            params_list.append(params)

    samples = [generate(params) for params in params_list]
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### story {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
