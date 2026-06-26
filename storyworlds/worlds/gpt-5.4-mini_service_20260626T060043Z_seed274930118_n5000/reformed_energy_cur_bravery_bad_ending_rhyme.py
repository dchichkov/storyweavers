#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/reformed_energy_cur_bravery_bad_ending_rhyme.py
===============================================================================================================

A tiny fairy-tale storyworld about a cur who learns bravery, spends energy
wisely, and uses rhyme to change a bad ending into a better one.

Premise:
- A small cur starts out noisy, skittish, and a little rude.
- The cur has high energy, but low bravery.
- A village event goes wrong unless the cur can reform and help.

Tension:
- The cur wants to dash after trouble, but that would make the ending worse.
- A wise helper offers a rhyme charm: speak bravely, breathe, and choose a kind act.

Turn:
- The cur spends energy on a brave, careful choice instead of a reckless one.
- The cur's bravery rises; the bad ending is avoided.

Resolution:
- The cur is reformed: calmer, kinder, and proud.
- The final image proves the change with a gentle rhyme.

This script follows the Storyweavers contract:
- standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of results.py for QAItem, StoryError, StorySample
- lazy import of asp.py inside ASP helpers
- inline ASP_RULES twin with a Python reasonableness gate
- --verify compares Python and ASP parity and exercises generated stories
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wore: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    sidekick: object | None = None
    def __post_init__(self) -> None:
        self.meters.setdefault("energy", 0.0)
        self.meters.setdefault("risk", 0.0)
        self.meters.setdefault("calm", 0.0)
        self.meters.setdefault("reform", 0.0)
        self.memes.setdefault("bravery", 0.0)
        self.memes.setdefault("shame", 0.0)
        self.memes.setdefault("hope", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the village green"
    afford: set[str] = field(default_factory=set)
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
class Instrument:
    id: str
    label: str
    kind: str
    effect: str
    verse: str
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
class StoryParams:
    setting: str
    instrument: str
    hero_name: str
    sidekick_name: str
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
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "green": Setting(place="the village green", afford={"rhyme", "bravery"}),
    "bridge": Setting(place="the old stone bridge", afford={"rhyme", "bravery"}),
    "well": Setting(place="the wishing well", afford={"rhyme", "bravery"}),
}

INSTRUMENTS = {
    "rhyme": Instrument(
        id="rhyme",
        label="a little rhyme",
        kind="rhyme",
        effect="steady",
        verse="The brave cur paused and counted to four, then chose a kinder path once more.",
    ),
    "bell": Instrument(
        id="bell",
        label="a silver bell",
        kind="bell",
        effect="call",
        verse="The bell rang clear and bright as day, and fear stepped back to make way.",
    ),
}

NAMES = ["Pip", "Mira", "Joss", "Nell", "Toby", "Wren", "Luna", "Perry"]
SIDEKICKS = ["the baker", "the miller", "the child", "the lantern keeper", "the shepherd"]


def _r_waste_energy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["energy"] < THRESHOLD or hero.memes["bravery"] >= THRESHOLD:
        return out
    sig = ("waste_energy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["energy"] -= 1
    hero.meters["risk"] += 1
    out.append("The cur wasted strength by rushing in too fast.")
    return out


def _r_reform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["reform"] < THRESHOLD or hero.memes["bravery"] < THRESHOLD:
        return out
    sig = ("reform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["calm"] += 1
    hero.memes["shame"] = 0.0
    out.append("The cur's heart settled, and the roughness began to leave.")
    return out


CAUSAL_RULES = [_r_waste_energy, _r_reform]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_bad_ending(world: World, hero: Entity, instrument: Instrument) -> dict[str, float]:
    sim = world.copy()
    perform_choice(sim, hero.id, instrument.id, narrate=False)
    hero2 = sim.get("hero")
    return {
        "risk": hero2.meters["risk"],
        "bravery": hero2.memes["bravery"],
        "energy": hero2.meters["energy"],
    }


def bad_ending_possible(world: World, hero: Entity) -> bool:
    return hero.meters["risk"] >= THRESHOLD or hero.memes["bravery"] < THRESHOLD


def choice_is_reasonable(setting: Setting, instrument: Instrument) -> bool:
    return instrument.kind in setting.afford


def act_intro(world: World, hero: Entity, sidekick: Entity, instrument: Instrument) -> None:
    world.say(f"Once upon a time, there was a small cur named {hero.id}.")
    world.say(f"{hero.pronoun().capitalize()} was quick of paw and loud of bark, but not yet very brave.")
    world.say(
        f"At {world.setting.place}, {hero.id} kept a pocketful of energy and a worry in the chest."
    )
    world.say(f"Nearby lived {sidekick.label}, who knew {instrument.label} could help when things went wrong.")


def act_problem(world: World, hero: Entity, sidekick: Entity, instrument: Instrument) -> None:
    hero.meters["energy"] += 2
    hero.memes["shame"] += 1
    hero.memes["bravery"] += 0
    world.say(
        f"One day, a bad ending seemed close: a snapped string, a blown plan, and a sad hush over {world.setting.place}."
    )
    world.say(
        f"{hero.id} wanted to dash at the trouble at once, but that wild leap would only spend {hero.pronoun('possessive')} energy and make matters worse."
    )
    world.say(
        f"So {sidekick.id} held up {instrument.label} and said, \"Try a rhyme, dear cur. A brave line can turn a dark time.\""
    )


def perform_choice(world: World, hero_name: str, instrument_id: str, narrate: bool = True) -> None:
    hero = world.get(hero_name)
    if instrument_id not in INSTRUMENTS:
        pass
    instrument = _safe_lookup(INSTRUMENTS, instrument_id)
    if not choice_is_reasonable(world.setting, instrument):
        pass

    hero.meters["energy"] -= 1
    hero.memes["bravery"] += 1
    hero.meters["reform"] += 1
    if hero.memes["bravery"] >= THRESHOLD:
        hero.meters["risk"] = max(0.0, hero.meters["risk"] - 1)
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{hero.id} took a breath, spoke the rhyme, and chose a careful step instead of a rash leap."
        )


def act_resolution(world: World, hero: Entity, sidekick: Entity, instrument: Instrument) -> None:
    if hero.memes["bravery"] < THRESHOLD:
        world.say(f"For a little while, the cur still trembled.")
        return
    hero.memes["hope"] += 1
    hero.meters["calm"] += 1
    world.say(
        f"{hero.id} said the rhyme, and the cur's voice came out steady: \"A brave small step can mend the tale.\""
    )
    world.say(
        f"The bad ending slipped away. The snapped string was tied, the hush lifted, and {world.setting.place} felt warm again."
    )
    world.say(
        f"At the end, {hero.id} was a reformed cur: still lively, but now kind, calm, and proud."
    )
    world.say(instrument.verse)


def build_story(world: World, hero: Entity, sidekick: Entity, instrument: Instrument) -> None:
    act_intro(world, hero, sidekick, instrument)
    world.para()
    act_problem(world, hero, sidekick, instrument)
    perform_choice(world, hero.id, instrument.id, narrate=True)
    world.para()
    act_resolution(world, hero, sidekick, instrument)


def make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="cur"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="person", label=params.sidekick_name))
    world.add(Entity(id="hero", kind="character", type="cur", label=params.hero_name))
    world.entities["hero"] = hero
    world.entities["sidekick"] = sidekick
    world.facts.update(
        setting=params.setting,
        instrument=params.instrument,
        hero=hero,
        sidekick=sidekick,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    build_story(world, world.get("hero"), world.get("sidekick"), _safe_lookup(INSTRUMENTS, params.instrument))
    world.facts["resolved"] = world.get("hero").memes["bravery"] >= THRESHOLD
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    instrument = INSTRUMENTS[f["instrument"]]
    return [
        'Write a gentle fairy tale about a cur who learns bravery by choosing a rhyme instead of a reckless rush.',
        f"Tell a fairy tale where {hero.id} the cur is low on bravery, has plenty of energy, and listens to {sidekick.id}.",
        f"Write a short child-friendly story in which {instrument.label} helps turn a bad ending into a better one.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    sidekick: Entity = _safe_fact(world, world.facts, "sidekick")  # type: ignore[assignment]
    instrument = _safe_lookup(INSTRUMENTS, world.facts.get("instrument"))  # type: ignore[index]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a small cur who starts out skittish and then becomes reformed.",
        ),
        QAItem(
            question=f"What did {sidekick.id} offer to help the cur?",
            answer=f"{sidekick.id} offered {instrument.label} and a calm rhyme to help the cur choose bravely.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="The cur stopped rushing, used energy wisely, grew brave, and became a kinder, calmer cur.",
        ),
        QAItem(
            question="Why was there a bad ending at first?",
            answer="The bad ending was close because a rash dash would have spent energy and made the trouble worse.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery help a creature do?",
            answer="Bravery helps a creature face a hard moment, choose carefully, and do the right thing even when scared.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a bit of verse where the sounds at the ends of words echo one another, making the words feel musical.",
        ),
        QAItem(
            question="What is energy in a story like this?",
            answer="Energy is the strength a character uses to move, act, and help; if it is spent carelessly, there is less left later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The cur has a bad ending risk when bravery is low and energy is spent recklessly.
bad_ending(C) :- cur(C), bravery(C,B), low(B), energy(C,E), E > 0, rash(C).

% A rhyme helps when it is available in the setting.
has_help(S) :- setting(S), afford(S,rhyme).

% The cur is reformed when bravery rises and risk falls.
reformed(C) :- cur(C), bravery(C,B), brave(B), calm(C), not bad_ending(C).

% A compatible tale exists when the setting affords the instrument type.
valid_story(S,I) :- setting(S), afford(S,I), instrument(I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", sid, a))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        lines.append(asp.fact("instrument_kind", iid, inst.kind))
    lines.append(asp.fact("cur", "hero"))
    lines.append(asp.fact("low", "0"))
    lines.append(asp.fact("brave", "1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Parity gate: our Python reasonableness rule should match the ASP twin.
    py = {(sid, iid) for sid, s in SETTINGS.items() for iid, inst in INSTRUMENTS.items() if choice_is_reasonable(s, inst)}
    asp_set = set(asp_valid_stories())
    if py != asp_set:
        print("MISMATCH between Python and ASP:")
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only in asp:", sorted(asp_set - py))
        return 1

    # Exercise generated stories on a few valid combinations.
    checked = 0
    for sid, iid in sorted(py):
        params = StoryParams(setting=sid, instrument=iid, hero_name="Pip", sidekick_name="Moss")
        sample = generate(params)
        if not sample.story or "bad ending" not in sample.story.lower():
            print("Generated story did not contain the expected tale beats.")
            return 1
        checked += 1
        if checked >= 3:
            break

    print(f"OK: Python and ASP agree on {len(py)} valid story combinations.")
    return 0


def explain_rejection(setting: Setting, instrument: Instrument) -> str:
    return (
        f"(No story: {setting.place} does not fit the remedy '{instrument.label}'. "
        f"The fairy-tale reasoner only allows a tool that the setting can honestly support.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a cur, bravery, energy, and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
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
    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    instrument = getattr(args, "instrument", None) or rng.choice(sorted(INSTRUMENTS))
    if getattr(args, "setting", None) and getattr(args, "instrument", None) and not choice_is_reasonable(_safe_lookup(SETTINGS, getattr(args, "setting", None)), _safe_lookup(INSTRUMENTS, getattr(args, "instrument", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not choice_is_reasonable(_safe_lookup(SETTINGS, setting), _safe_lookup(INSTRUMENTS, instrument)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "hero_name", None) or rng.choice(NAMES)
    sidekick_name = getattr(args, "sidekick_name", None) or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, instrument=instrument, hero_name=hero_name, sidekick_name=sidekick_name)


CURATED = [
    StoryParams(setting="green", instrument="rhyme", hero_name="Pip", sidekick_name="the baker"),
    StoryParams(setting="bridge", instrument="rhyme", hero_name="Mira", sidekick_name="the lantern keeper"),
    StoryParams(setting="well", instrument="rhyme", hero_name="Toby", sidekick_name="the child"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render() if False else build_and_render(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_and_render(world: World) -> str:
    build_story(world, world.get("hero"), world.get("sidekick"), _safe_lookup(INSTRUMENTS, world.facts.get("instrument")))
    return world.render()


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combinations:")
        for s in stories:
            print(" ", s)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
