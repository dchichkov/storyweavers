#!/usr/bin/env python3
"""
storyworlds/worlds/meteor_saucer_problem_solving_pirate_tale.py
==============================================================

A standalone storyworld for a small pirate tale about a meteor, a saucer,
and a problem that can be solved with clever crewwork.

Premise:
- A pirate crew is sailing at night.
- A bright meteor drops a broken saucer into their path.
- The saucer is not treasure, but it can be repaired or used to guide the ship.

Tension:
- The crew wants to keep sailing, but the saucer is cracked and unsteady.
- The captain worries the wrong choice will waste time or sink morale.

Turn:
- The crew studies the damage, finds a useful part, and uses it to solve a new
  problem: the ship's lantern or compass cover needs a smooth metal dish.

Resolution:
- The saucer becomes part of a working fix, proving the crew can solve trouble
  without throwing useful things away.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven narration
- concise, child-facing story prose
- QA grounded in the story and the world
- inline ASP twin and Python reasonableness gate
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
# Entities and world state
# ---------------------------------------------------------------------------

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    mate: object | None = None
    meteor: object | None = None
    saucer: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pirate", "captain", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace_notes: list[str] = field(default_factory=list)

    clone: object | None = None
    world: object | None = None
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Parameters
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
    setting: str = "harbor"
    problem: str = "broken_saucer"
    solution: str = "lantern_shield"
    captain: str = "Mara"
    first_mate: str = "Jett"
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


SETTINGS = {
    "harbor": {
        "place": "the moonlit harbor",
        "weather": "clear",
        "detail": "The tide lapped softly against the dock, and the stars made a silver path on the water.",
    },
    "reef": {
        "place": "the reef",
        "weather": "windy",
        "detail": "The waves hissed around the reef, and the ship rocked like a sleepy cradle.",
    },
}

PIRATE_NAMES = ["Mara", "Jett", "Bram", "Nina", "Tess", "Rook", "Ivy", "Finn"]
FIRST_MATES = ["Jett", "Bram", "Nina", "Tess", "Rook", "Ivy", "Finn", "Mira"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, problem: str, solution: str) -> bool:
    if setting not in SETTINGS:
        return False
    if problem != "broken_saucer":
        return False
    return solution in {"lantern_shield", "signal_dish"}


def explain_rejection(setting: str, problem: str, solution: str) -> str:
    return (
        f"(No story: this pirate tale needs a broken saucer problem and a fix "
        f"that actually uses the saucer, such as a lantern shield or signal dish.)"
    )


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World()
    scene = _safe_lookup(SETTINGS, params.setting)

    captain = world.add(Entity(
        id=params.captain,
        kind="character",
        type="captain",
        label=params.captain,
        meters={"calm": 1.0},
        memes={"care": 1.0, "worry": 0.0, "hope": 0.0},
    ))
    mate = world.add(Entity(
        id=params.first_mate,
        kind="character",
        type="pirate",
        label=params.first_mate,
        meters={"energy": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "hope": 0.0},
    ))
    meteor = world.add(Entity(
        id="meteor",
        kind="thing",
        type="meteor",
        label="the meteor",
        phrase="a bright fallen stone",
        meters={"glow": 1.0, "heat": 0.0},
    ))
    saucer = world.add(Entity(
        id="saucer",
        kind="thing",
        type="saucer",
        label="saucer",
        phrase="a small silver saucer",
        owner=None,
        caretaker=params.captain,
        meters={"crack": 1.0, "shine": 1.0, "balance": 0.5},
        memes={"value": 0.5, "usefulness": 0.0},
    ))

    world.facts.update(
        scene=scene,
        captain=captain,
        mate=mate,
        meteor=meteor,
        saucer=saucer,
        solution=params.solution,
    )

    world.say(
        f"At {scene['place']}, Captain {captain.label} and {mate.label} watched the sea "
        f"under a clear dark sky."
    )
    world.say(
        f"A meteor flashed overhead and clinked down into the deck with a tiny spark, "
        f"leaving behind a cracked saucer."
    )
    world.para()
    world.say(scene["detail"])
    world.say(
        f"{mate.label} picked up the saucer, but {captain.label} held up a hand and frowned. "
        f"The crack made it wobble, and the crew did not want a useless shiny thing."
    )

    # tension: worry rises
    captain.memes["worry"] += 1.0
    mate.memes["worry"] += 1.0
    saucer.meters["balance"] -= 0.5
    world.trace_notes.append("saucer found cracked and wobbly")

    world.para()
    if params.solution == "lantern_shield":
        world.say(
            f"{mate.label} noticed the saucer still had one smooth curve. "
            f"{mate.pronoun().capitalize()} held it near the lantern, and the light stopped "
            f"flickering in the wind."
        )
        saucer.meters["usefulness"] += 1.0
        saucer.meters["crack"] -= 0.5
        world.say(
            f"Together they bent a wire loop around the rim and made a lantern shield. "
            f"Now the deck had a steady glow, and the broken saucer had found a new job."
        )
    else:
        world.say(
            f"{mate.label} studied the saucer, then used its curve like a signal dish to catch "
            f"the captain's lantern beam."
        )
        saucer.meters["usefulness"] += 1.0
        world.say(
            f"The bright circle flashed back to a passing ship, and the crew used it to ask "
            f"for help without shouting over the waves."
        )

    captain.memes["worry"] = 0.0
    captain.memes["hope"] = 1.0
    mate.memes["hope"] = 1.0
    world.say(
        f"By dawn, the crew was sailing on with a clever fix, and the saucer was no longer "
        f"just broken treasure."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    scene = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "scene")
    return [
        'Write a short pirate tale for a young child that includes the words "meteor" and "saucer".',
        f"Tell a story set at {scene['place']} where a captain and crew solve a problem with a found saucer.",
        "Write a gentle problem-solving pirate story with a bright meteor, a damaged saucer, and a clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "captain")
    m = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "mate")
    scene = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "scene")
    saucer = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "saucer")
    solution = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "solution")

    if solution == "lantern_shield":
        fix_answer = "They turned the saucer into a lantern shield, so the wind would not blow out the light."
    else:
        fix_answer = "They used the saucer like a signal dish to send a bright message to another ship."

    return [
        QAItem(
            question=f"Who found the saucer at {scene['place']}?",
            answer=f"{m.label} found it after the meteor fell, and Captain {c.label} watched carefully.",
        ),
        QAItem(
            question="What was wrong with the saucer?",
            answer="It was cracked and wobbly, so it needed a clever new use.",
        ),
        QAItem(
            question="How did the crew solve the problem?",
            answer=fix_answer,
        ),
        QAItem(
            question="What happened to the crew's feelings by the end?",
            answer="Their worry faded and their hope grew, because the broken saucer became useful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a meteor?",
            answer="A meteor is a bright space rock that can streak through the sky and sometimes fall to Earth.",
        ),
        QAItem(
            question="What is a saucer?",
            answer="A saucer is a small, shallow dish that can hold a cup or, in a story, be turned into a useful shape.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way to make trouble better or use what you have in a smart way.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting is valid when it exists.
valid_setting(S) :- setting(S).

% The only story problem in this small world is a broken saucer.
valid_problem(broken_saucer).

% A solution is compatible if it genuinely uses the saucer in a new role.
valid_solution(lantern_shield) :- solution(lantern_shield).
valid_solution(signal_dish) :- solution(signal_dish).

valid_story(S, P, Sol) :- valid_setting(S), valid_problem(P), valid_solution(Sol).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("problem", "broken_saucer"))
    lines.append(asp.fact("solution", "lantern_shield"))
    lines.append(asp.fact("solution", "signal_dish"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, "broken_saucer", sol) for s in SETTINGS for sol in {"lantern_shield", "signal_dish"}}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Serialization and trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    if world.trace_notes:
        lines.append("  notes: " + "; ".join(world.trace_notes))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate tale world with a meteor, a saucer, and a problem-solving fix."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--solution", choices=["lantern_shield", "signal_dish"])
    ap.add_argument("--captain")
    ap.add_argument("--first-mate", dest="first_mate")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    solution = getattr(args, "solution", None) or rng.choice(["lantern_shield", "signal_dish"])
    if not valid_combo(setting, "broken_saucer", solution):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    captain = getattr(args, "captain", None) or rng.choice(PIRATE_NAMES)
    first_mate = getattr(args, "first_mate", None) or rng.choice([n for n in FIRST_MATES if n != captain])
    return StoryParams(
        setting=setting,
        problem="broken_saucer",
        solution=solution,
        captain=captain,
        first_mate=first_mate,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(setting="harbor", problem="broken_saucer", solution="lantern_shield", captain="Mara", first_mate="Jett"),
            StoryParams(setting="reef", problem="broken_saucer", solution="signal_dish", captain="Nina", first_mate="Rook"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.captain} and {p.first_mate} at {p.setting} ({p.solution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
