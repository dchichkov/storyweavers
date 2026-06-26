#!/usr/bin/env python3
"""
Standalone storyworld: a tiny space-adventure nap-room tale with sound effects
and a bad ending.

The world premise:
- A junior space crew enters a nap room on a ship.
- They appoint a helper for the room.
- A rattle is used as a quieting tool, but its sound effect becomes the problem.
- The room's hush fails, the nap breaks, and the story ends with a bad ending.

This is a small classical simulation: entities have meters and memes, actions
change state, state drives prose, and a reasonableness gate keeps the premise
tight.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    rattle: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for k in ["noise", "sleepiness", "tension", "order", "shock"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the nap room"
    afford: set[str] = field(default_factory=lambda: {"appoint", "rattle"})
    SETTING: object | None = None
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    world: object | None = None
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

    def copy(self) -> "World":
        import copy

        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            fired=set(self.fired),
            facts=dict(self.facts),
        )


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
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
    name: str = ""
    crew_type: str = ""
    helper_type: str = ""
    setting: str = "nap_room"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    params: object | None = None
    py: set[str] = field(default_factory=set)
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


SETTING = Setting()

NAMES = ["Mina", "Jett", "Nova", "Pip", "Rae", "Timo", "Luna", "Sol"]
CREW_TYPES = ["girl", "boy"]
HELPER_TYPES = ["robot", "cadet", "mousebot"]

# A rattle is the key object; in this world it is a bad idea.
RATTLE_NAMES = [
    "silver rattle",
    "tiny rattle",
    "ringing rattle",
]


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------

def sound_effect(label: str) -> str:
    return {
        "rattle": "rattle-rattle!",
        "hatch": "whirr-clack.",
        "whisper": "shh...",
        "alarm": "beep-beep-beep!",
    }.get(label, "tap.")


def establish(world: World, hero: Entity, helper: Entity, rattle: Entity) -> None:
    world.say(
        f"{hero.id} stood at the door of the {world.setting.place}, where the lights were dim "
        f"and the blankets floated like little clouds."
    )
    world.say(
        f"Beside {hero.pronoun('object')}, the ship's crew had asked {helper.id} to help keep the room calm."
    )
    world.facts["hero"] = hero.id
    world.facts["helper"] = helper.id
    world.facts["rattle"] = rattle.id


def appoint(world: World, hero: Entity, helper: Entity, rattle: Entity) -> None:
    hero.memes["hope"] += 1
    helper.role = "appointed keeper"
    world.say(
        f"{hero.id} decided to appoint {helper.id} as the nap-room keeper and handed over the "
        f"{rattle.label} with a proud grin."
    )
    world.say(
        f'"Use it only for a tiny cue," {hero.id} said, "and then let the room get quiet."'
    )


def use_rattle(world: World, helper: Entity, rattle: Entity) -> None:
    sig = ("use_rattle", helper.id, rattle.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    helper.meters["noise"] += 2
    helper.memes["excitement"] += 1
    world.say(f"{helper.id} tried to be careful, but the {rattle.label} went {sound_effect('rattle')}")
    world.say(f"The sound bounced off the walls of the nap room like a tiny meteor.")
    world.facts["noise_spike"] = True


def wake(world: World, hero: Entity, helper: Entity) -> None:
    sig = ("wake", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["sleepiness"] += 1
    hero.memes["shock"] += 1
    helper.meters["tension"] += 1
    world.say(
        f"The soft hush shattered. Even the sleepy pillows seemed to sit up straight."
    )
    world.say(
        f"{hero.id} flinched, and the dreamy calm slipped away before it could settle."
    )
    world.facts["wake"] = True


def bad_ending(world: World, hero: Entity, helper: Entity, rattle: Entity) -> None:
    hero.memes["sadness"] += 1
    helper.memes["guilt"] += 1
    world.say(
        f"In the end, the nap room was not peaceful at all. {helper.id} put the {rattle.label} down, "
        f"but the quiet was already gone."
    )
    world.say(
        f"{hero.id} had to leave the room without a nap, and the ship drifted on through the stars "
        f"with one tired crew and one very bad ending."
    )
    world.facts["ending"] = "bad"


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.crew_type))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type))
    rattle = world.add(Entity(
        id="rattle",
        kind="thing",
        type="rattle",
        label=random.choice(RATTLE_NAMES),
        phrase="a shiny little rattle",
        owner=helper.id,
    ))

    establish(world, hero, helper, rattle)
    world.para()
    appoint(world, hero, helper, rattle)
    use_rattle(world, helper, rattle)
    wake(world, hero, helper)
    world.para()
    bad_ending(world, hero, helper, rattle)
    world.facts.update(setting=world.setting.place)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(params: StoryParams) -> bool:
    return params.setting == "nap_room" and params.name in NAMES and params.crew_type in CREW_TYPES


def explain_invalid(params: StoryParams) -> str:
    return "(No story: this tiny world only works in the nap room with a space crew and a rattle.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(nap_room).
crew(girl;boy).
helper(robot;cadet;mousebot).
prop(rattle).

valid_story(N,T,H) :- setting(nap_room), crew(T), helper(H), prop(rattle), name(N).

bad_ending(N) :- valid_story(N,T,H), prop(rattle), appoint(N,H), rattle_sound(N).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("setting", "nap_room"))
    for n in NAMES:
        lines.append(asp.fact("name", n))
    for t in CREW_TYPES:
        lines.append(asp.fact("crew", t))
    for h in HELPER_TYPES:
        lines.append(asp.fact("helper", h))
    lines.append(asp.fact("prop", "rattle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(n, t, h) for n in NAMES for t in CREW_TYPES for h in HELPER_TYPES if valid_story(StoryParams(n, t, h))}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python valid_story() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short space-adventure story set in a nap room that includes the words "appoint" and "rattle".',
        f"Tell a child-friendly story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")} tries to keep a nap room calm, but a rattle makes things go wrong.",
        "Write a tiny spaceship story with sound effects and a bad ending in the nap room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What room was the story set in?",
            answer="It was set in the nap room, where the lights were dim and the blankets waited for sleep.",
        ),
        QAItem(
            question=f"What did {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")} appoint the helper to do?",
            answer=f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")} appointed {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")} to keep the nap room calm.",
        ),
        QAItem(
            question="What sound effect caused the trouble?",
            answer="The rattle went rattle-rattle!, and that noisy sound ruined the quiet.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly: the nap room lost its calm, the nap was ruined, and the crew left tired.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rattle?",
            answer="A rattle is a small toy or object that makes a shaking sound when you move it.",
        ),
        QAItem(
            question="Why is a nap room supposed to be quiet?",
            answer="A nap room is supposed to be quiet so tired people can rest and fall asleep.",
        ),
        QAItem(
            question="What does a bad ending mean in a story?",
            answer="A bad ending means the problem is not solved in a happy way, so things end poorly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type}, role={e.role or '-'}, meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}}, "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or rng.choice(NAMES)
    crew_type = getattr(args, "crew_type", None) or rng.choice(CREW_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    params = StoryParams(name=name, crew_type=crew_type, helper_type=helper_type, seed=getattr(args, "seed", None))
    if not valid_story(params):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure nap-room storyworld with sound effects and a bad ending.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--crew-type", choices=CREW_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


CURATED = [
    StoryParams(name="Nova", crew_type="girl", helper_type="robot"),
    StoryParams(name="Jett", crew_type="boy", helper_type="cadet"),
    StoryParams(name="Luna", crew_type="girl", helper_type="mousebot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} valid stories:")
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
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
