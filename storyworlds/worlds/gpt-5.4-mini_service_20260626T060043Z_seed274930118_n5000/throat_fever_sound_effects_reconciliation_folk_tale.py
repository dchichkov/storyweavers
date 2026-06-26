#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/throat_fever_sound_effects_reconciliation_folk_tale.py
================================================================================

A small folk-tale storyworld about a child, a throaty sickness, noisy remedies,
and a reconciliation at the end.

Premise:
- A little singer has a scratchy throat and a fever.
- The village hears the coughs and the kettle's sound effects.
- A caretaker and a helper argue over the right remedy.
- They reconcile when the child rests, drinks warm broth, and the song returns.

The world is intentionally narrow:
- Only a few reasonable combinations are generated.
- State changes drive narration; the story is not a static template.
- Python and ASP agree on the same validity gate.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: list[str] = field(default_factory=list)
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
class Setting:
    place: str
    indoors: bool
    winds: str
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
class Remedy:
    id: str
    label: str
    sound: str
    warmth: str
    method: str
    helps: set[str]
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
    place: str
    child_type: str
    child_name: str
    caretaker_type: str
    helper_type: str
    remedy: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _add_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _add_meme(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


SETTINGS = {
    "hearth": Setting(place="the hearth-house", indoors=True, winds="quiet"),
    "orchard": Setting(place="the orchard lane", indoors=False, winds="soft"),
    "green": Setting(place="the green by the well", indoors=False, winds="cool"),
}

REMEDIES = {
    "broth": Remedy(
        id="broth",
        label="warm broth",
        sound="glug-glug",
        warmth="warm",
        method="sip",
        helps={"throat", "fever"},
    ),
    "honey": Remedy(
        id="honey",
        label="honey tea",
        sound="hmm-mm",
        warmth="warm",
        method="sip",
        helps={"throat"},
    ),
    "cloth": Remedy(
        id="cloth",
        label="a cool cloth",
        sound="soft-fresh",
        warmth="cool",
        method="rest with",
        helps={"fever"},
    ),
}

CHILD_NAMES = ["Milo", "Nina", "Tessa", "Jory", "Lena", "Pip", "Oona", "Bram"]
CHILD_TYPES = ["boy", "girl"]
CARETAKER_TYPES = ["mother", "father", "grandmother", "grandfather"]
HELPER_TYPES = ["neighbor", "aunt", "uncle", "sister", "brother"]
TRAITS = ["small", "brave", "gentle", "bright", "patient"]


def reasonableness_gate(place: str, remedy: str) -> bool:
    return place in SETTINGS and remedy in REMEDIES


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for remedy in REMEDIES:
            out.append((place, remedy))
    return out


ASP_RULES = r"""
place(hearth). place(orchard). place(green).
remedy(broth). remedy(honey). remedy(cloth).

valid(P,R) :- place(P), remedy(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world of throat fever, sound effects, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--caretaker-type", choices=CARETAKER_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    if getattr(args, "place", None) and getattr(args, "remedy", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "remedy", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    remedy = getattr(args, "remedy", None) or rng.choice(sorted(REMEDIES))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    child_type = getattr(args, "child_type", None) or rng.choice(CHILD_TYPES)
    caretaker_type = getattr(args, "caretaker_type", None) or rng.choice(CARETAKER_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    return StoryParams(place=place, child_type=child_type, child_name=name,
                       caretaker_type=caretaker_type, helper_type=helper_type,
                       remedy=remedy)


def _narrate_sickness(world: World, child: Entity) -> None:
    _add_meter(child, "throat", 1)
    _add_meter(child, "fever", 1)
    _add_meme(child, "worry", 1)
    world.say(
        f"{child.id} woke with a scratchy throat and a hot fever. "
        f"Every swallow went down like a small thorn."
    )
    world.say("Cough-cough went the child, and the morning seemed to listen.")


def _narrate_remedy(world: World, caretaker: Entity, helper: Entity, child: Entity, remedy: Remedy) -> None:
    if remedy.id == "broth":
        world.say(
            f"{caretaker.label_word} set a pot on the fire and let it go glug-glug."
        )
    elif remedy.id == "honey":
        world.say(
            f"{helper.label_word} stirred the cup and it answered with a gentle hmm-mm."
        )
    else:
        world.say(
            f"{helper.label_word} laid a cool cloth on {child.pronoun('possessive')} brow with a soft-fresh sigh."
        )


def _tension(world: World, caretaker: Entity, helper: Entity, child: Entity, remedy: Remedy) -> None:
    _add_meme(caretaker, "worry", 1)
    _add_meme(helper, "confidence", 1)
    world.say(
        f"{caretaker.label_word} wanted rest, but {helper.label_word} said the old way was best."
    )
    world.say(
        f"They spoke over the kettle: splash, hiss, hush."
    )
    _add_meme(caretaker, "hurt", 1)
    _add_meme(helper, "stubborn", 1)
    world.say(
        f"{child.id} heard their voices and coughed again, small as a bird in the rain."
    )


def _reconcile(world: World, caretaker: Entity, helper: Entity, child: Entity, remedy: Remedy) -> None:
    _add_meme(caretaker, "reconciled", 1)
    _add_meme(helper, "reconciled", 1)
    _add_meme(child, "safe", 1)
    world.say(
        f"Then {caretaker.label} and {helper.label} looked at the little face on the pillow and smiled at once."
    )
    world.say(
        f'"Let us do both," said {caretaker.label}. "A sip, a rest, and a soft song."'
    )
    world.say(
        f'{helper.label.capitalize()} nodded. "So be it," they said, and the room grew kind again.'
    )
    world.say(
        f"{child.id} drank the {remedy.label}, breathed slowly, and the coughs softened to a whisper."
    )
    world.say(
        f"By evening the fever had fallen, and {child.id}'s throat was only a little tired."
    )
    world.say(
        f"Outside, the wind went whoosh through the branches, and inside the hearth sang crackle-crackle."
    )
    world.say(
        f"{child.id} slept with a cool brow and a steady breath, while the old folk tale found its happy peace."
    )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    remedy = _safe_lookup(REMEDIES, params.remedy)
    world = World(setting)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label=params.child_name,
        traits=["little", rng_choice([params.child_type, "sick", "soft"]) if False else "sick"],
    ))
    caretaker = world.add(Entity(
        id="caretaker",
        kind="character",
        type=params.caretaker_type,
        label=f"the {params.caretaker_type}",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=f"the {params.helper_type}",
    ))

    world.facts.update(
        child=child, caretaker=caretaker, helper=helper, remedy=remedy, setting=setting
    )

    world.say(
        f"Once, in {setting.place}, there lived a little {child.type} named {child.id}."
    )
    world.say(
        f"{child.id} was a bright child, and the village loved {child.pronoun('object')} for a soft voice and a careful heart."
    )
    world.para()
    _narrate_sickness(world, child)
    world.say(
        f"The {setting.winds} wind went through the eaves, but {child.id} only wanted a warm drink and a quiet lap."
    )
    world.para()
    _narrate_remedy(world, caretaker, helper, child, remedy)
    _tension(world, caretaker, helper, child, remedy)
    world.para()
    _reconcile(world, caretaker, helper, child, remedy)
    return world


def rng_choice(seq):
    return random.choice(seq)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")  # type: ignore[assignment]
    remedy: Remedy = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "remedy")  # type: ignore[assignment]
    return [
        f'Write a short folk tale for a child with a sore throat and a fever that includes the sound "{remedy.sound}".',
        f"Tell a gentle story where {child.id} has a scratchy throat, a hot fever, and the grown-ups find peace again.",
        f"Write a simple story about a sick child, a healing drink, and reconciliation, with a few cozy sound effects.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")  # type: ignore[assignment]
    caretaker: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "caretaker")  # type: ignore[assignment]
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")  # type: ignore[assignment]
    remedy: Remedy = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "remedy")  # type: ignore[assignment]
    setting: Setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was wrong with {child.id} at {setting.place}?",
            answer=f"{child.id} had a scratchy throat and a fever, so every swallow hurt and the child felt hot and weak.",
        ),
        QAItem(
            question=f"Why did {caretaker.label} and {helper.label} argue?",
            answer=f"They disagreed about how best to help {child.id}: one wanted rest and the other wanted the old remedy to be used right away.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"{caretaker.label} and {helper.label} reconciled, {child.id} drank the {remedy.label}, the fever settled, and the child fell asleep in peace.",
        ),
        QAItem(
            question=f"What sound did the remedy make in the story?",
            answer=f"The remedy made a cozy sound: {remedy.sound}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fever?",
            answer="A fever is when the body gets too warm because it is fighting illness.",
        ),
        QAItem(
            question="Why can a sore throat make it hard to talk?",
            answer="A sore throat can hurt when you swallow or speak, so talking may feel scratchy and uncomfortable.",
        ),
        QAItem(
            question="Why do warm drinks help some sick people feel better?",
            answer="Warm drinks can be soothing, and they may make a sore throat feel less scratchy.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing and make peace again.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help a story feel lively by letting you hear what the characters hear.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    StoryParams(place="hearth", child_type="girl", child_name="Nina", caretaker_type="mother", helper_type="aunt", remedy="broth"),
    StoryParams(place="orchard", child_type="boy", child_name="Bram", caretaker_type="grandmother", helper_type="brother", remedy="honey"),
    StoryParams(place="green", child_type="girl", child_name="Tessa", caretaker_type="father", helper_type="neighbor", remedy="cloth"),
]


def asp_program_text(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program_text("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_text("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_list()
        print(f"{len(vals)} valid place/remedy pairs:")
        for p, r in vals:
            print(f"  {p:8} {r}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.child_name}: {p.place} with {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
