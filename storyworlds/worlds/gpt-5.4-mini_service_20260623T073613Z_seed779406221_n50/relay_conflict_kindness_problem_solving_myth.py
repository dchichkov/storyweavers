#!/usr/bin/env python3
"""
storyworlds/worlds/relay_conflict_kindness_problem_solving_myth.py
==================================================================

A small myth-style storyworld about a sacred relay, a conflict over the path,
kindness offered at the right moment, and a problem solved by sharing the work.

The domain stays tiny on purpose: one relay journey, one obstacle, one dispute,
and one kind, practical solution. Stories are generated from simulated state so
the prose changes with the world.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    carries_torch: bool = False
    carries_bowl: bool = False

    guardian: object | None = None
    helper: object | None = None
    runner: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "queen", "maiden"}
        male = {"boy", "man", "father", "brother", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Shrine:
    id: str
    label: str
    phrase: str
    obstacle: str
    path: str
    blessing: str
    feels: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Relay:
    id: str
    label: str
    phrase: str
    task: str
    handoff: str
    finish: str
    symbol: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

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
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    result: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

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
        other = World()
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        return other


RELIGIOUS_RULES = []


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    runner = world.get("runner")
    guardian = world.get("guardian")
    if runner.memes.get("frustration", 0.0) >= THRESHOLD and guardian.memes.get("blocking", 0.0) >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            runner.memes["conflict"] = runner.memes.get("conflict", 0.0) + 1
            out.append("The path tightened with conflict.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RELIGIOUS_RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def set_conflict(world: World, runner: Entity, guardian: Entity) -> None:
    runner.memes["frustration"] = runner.memes.get("frustration", 0.0) + 1
    guardian.memes["blocking"] = guardian.memes.get("blocking", 0.0) + 1
    propagate(world)


def predict_trouble(world: World, relay: Relay) -> dict:
    sim = world.copy()
    sim.get("runner").memes["frustration"] = 1.0
    sim.get("guardian").memes["blocking"] = 1.0
    propagate(sim, narrate=False)
    return {"conflict": sim.get("runner").memes.get("conflict", 0.0) >= THRESHOLD}


def tell_shrine(shrine: Shrine) -> str:
    return f"In the old time, {shrine.label} watched over {shrine.phrase}."


def tell_relay(relay: Relay, shrine: Shrine) -> str:
    return f"The {relay.label} was {relay.phrase}, and its task was to {relay.task} along {shrine.path}."


def tell_problem(runner: Entity, guardian: Entity, shrine: Shrine, relay: Relay) -> str:
    return (
        f"But {runner.id} wanted to hurry through {shrine.obstacle}, while {guardian.id} feared "
        f"the {relay.symbol} would be lost."
    )


def tell_kindness(world: World, helper: Entity, runner: Entity, shrine: Shrine, relay: Relay) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    runner.memes["seen_kindness"] = runner.memes.get("seen_kindness", 0.0) + 1
    world.say(
        f"Then {helper.id} gave {runner.id} a calm hand and said, "
        f'"Let us share the {relay.label}; one carries, one watches, and the road stays true."'
    )


def solve_problem(world: World, runner: Entity, guardian: Entity, relay: Relay, fix: Fix, shrine: Shrine) -> None:
    runner.memes["joy"] = runner.memes.get("joy", 0.0) + 1
    guardian.memes["relief"] = guardian.memes.get("relief", 0.0) + 1
    runner.memes["conflict"] = 0.0
    world.say(
        f"They chose {fix.phrase}, {fix.method}, and the old trouble loosened at once. "
        f"The {relay.label} could {relay.finish}, and the {shrine.label} shone without harm."
    )


def tell(world: World, shrine: Shrine, relay: Relay, fix: Fix,
         runner_name: str, runner_type: str, guardian_name: str, guardian_type: str,
         helper_name: str, helper_type: str) -> World:
    runner = world.add(Entity(id=runner_name, kind="character", type=runner_type, role="runner"))
    guardian = world.add(Entity(id=guardian_name, kind="character", type=guardian_type, role="guardian"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="torch", label="torch", carries_torch=True))
    world.add(Entity(id="bowl", label="bowl", carries_bowl=True))

    world.say(tell_shrine(shrine))
    world.say(tell_relay(relay, shrine))
    world.say(
        f"{runner.id} loved the {relay.label}, because {relay.phrase.lower()} felt like a bright promise."
    )
    world.para()
    world.say(tell_problem(runner, guardian, shrine, relay))
    set_conflict(world, runner, guardian)
    if predict_trouble(world, relay)["conflict"]:
        world.say(
            f"{guardian.id} raised a hand, not to block forever, but to keep the sacred {relay.symbol} safe."
        )
    world.para()
    tell_kindness(world, helper, runner, shrine, relay)
    solve_problem(world, runner, guardian, relay, fix, shrine)
    world.say(
        f"In the ending light, {runner.id} carried the task with care, {guardian.id} smiled, "
        f"and {helper.id} walked beside them."
    )

    world.facts.update(
        runner=runner,
        guardian=guardian,
        helper=helper,
        shrine=shrine,
        relay=relay,
        fix=fix,
        conflict=runner.memes.get("conflict", 0.0) >= THRESHOLD,
        resolved=True,
    )
    return world


SHRINES = {
    "hill": Shrine(
        id="hill",
        label="the hill shrine",
        phrase="a bowl of dawn-fire",
        obstacle="the stone steps",
        path="the winding path",
        blessing="morning light",
        feels="high and wind-bright",
    ),
    "river": Shrine(
        id="river",
        label="the river temple",
        phrase="a lantern of silver water",
        obstacle="the slippery ford",
        path="the river road",
        blessing="cool water",
        feels="deep and shimmering",
    ),
    "grove": Shrine(
        id="grove",
        label="the grove altar",
        phrase="a woven crown of leaves",
        obstacle="the thorn gate",
        path="the green trail",
        blessing="leaf shade",
        feels="quiet and moss-soft",
    ),
}

RELAYS = {
    "torch": Relay(
        id="torch",
        label="relay torch",
        phrase="a torch carried from hand to hand",
        task="pass the flame",
        handoff="hand it on",
        finish="reach the altar without dimming",
        symbol="torch",
        tags={"relay"},
    ),
    "drum": Relay(
        id="drum",
        label="relay drum",
        phrase="a drum that called the walkers forward",
        task="beat the road-song",
        handoff="give the rhythm on",
        finish="sound at the shrine gate",
        symbol="drum",
        tags={"relay"},
    ),
}

FIXES = {
    "share": Fix(
        id="share",
        label="shared carrying",
        phrase="shared carrying",
        method="one bore the weight while the other cleared the way",
        result="the burden became light",
        power=3,
        tags={"kindness", "problem_solving"},
    ),
    "guide": Fix(
        id="guide",
        label="guiding rope",
        phrase="a guiding rope",
        method="they tied the rope to keep the relay steady over the rough place",
        result="the path opened again",
        power=3,
        tags={"problem_solving"},
    ),
}

NAMES = ["Ari", "Mira", "Niko", "Sera", "Jon", "Lena", "Koa", "Tala"]
TYPES = ["girl", "boy", "woman", "man"]


@dataclass
class StoryParams:
    shrine: str
    relay: str
    fix: str
    runner: str
    runner_type: str
    guardian: str
    guardian_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, r, f) for s in SHRINES for r in RELAYS for f in FIXES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic relay storyworld about conflict, kindness, and problem solving.")
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--relay", choices=RELAYS)
    ap.add_argument("--fix", choices=FIXES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "shrine", None) is None or c[0] == getattr(args, "shrine", None))
              if (getattr(args, "relay", None) is None or c[1] == getattr(args, "relay", None))
              if (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    shrine, relay, fix = rng.choice(list(combos))
    runner = rng.choice(NAMES)
    guardian = rng.choice([n for n in NAMES if n != runner])
    helper = rng.choice([n for n in NAMES if n not in {runner, guardian}])
    return StoryParams(
        shrine=shrine, relay=relay, fix=fix,
        runner=runner, runner_type=rng.choice(TYPES),
        guardian=guardian, guardian_type=rng.choice(TYPES),
        helper=helper, helper_type=rng.choice(TYPES),
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    world = tell(world, _safe_lookup(SHRINES, params.shrine), _safe_lookup(RELAYS, params.relay), _safe_lookup(FIXES, params.fix),
                 params.runner, params.runner_type, params.guardian, params.guardian_type,
                 params.helper, params.helper_type)
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
    return [
        f'Write a small myth about a sacred {f["relay"].label} and a conflict on the path.',
        f"Tell a child-friendly myth where {f['runner'].id} and {f['guardian'].id} disagree about the {f['relay'].label}, then solve it with kindness.",
        f"Write a mythic story that includes relay, kindness, and problem solving, and ends with the shrine safely reached.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    runner, guardian, helper, shrine, relay, fix = f["runner"], f["guardian"], f["helper"], f["shrine"], f["relay"], f["fix"]
    return [
        QAItem(
            question=f"What was the story about?",
            answer=f"It was about {runner.id}, {guardian.id}, and {helper.id}, who guided a sacred {relay.label} to {shrine.label}.",
        ),
        QAItem(
            question=f"What caused the conflict?",
            answer=f"{runner.id} wanted to hurry through {shrine.obstacle}, but {guardian.id} feared the {relay.symbol} would be lost.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {fix.phrase} and worked together, so the {relay.label} could {relay.finish}.",
        ),
        QAItem(
            question=f"How did kindness help?",
            answer=f"{helper.id} chose kindness by sharing the work, which calmed the conflict and made the path easier.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a relay?", answer="A relay is a task passed along from one helper to the next so the work can keep moving."),
        QAItem(question="What does kindness do in a hard moment?", answer="Kindness can lower hurt feelings and help everyone keep working together."),
        QAItem(question="What is problem solving?", answer="Problem solving means finding a practical way around trouble instead of giving up."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
combo(S,R,F) :- shrine(S), relay(R), fix(F).
conflict :- runner(R), guardian(G), problem(P), P = path_block.
kindness :- helper(H), H = helper.
solved :- kindness, problem_solving(F).
#show combo/3.
"""


def asp_facts() -> str:
    import asp
    out = []
    for s in SHRINES:
        out.append(asp.fact("shrine", s))
    for r in RELAYS:
        out.append(asp.fact("relay", r))
    for f in FIXES:
        out.append(asp.fact("fix", f))
    out.append(asp.fact("problem", "path_block"))
    out.append(asp.fact("problem_solving", "share"))
    out.append(asp.fact("problem_solving", "guide"))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show combo/3."))
    asp_set = set(asp.atoms(model, "combo"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only asp:", sorted(asp_set - py_set))
    print("only py:", sorted(py_set - asp_set))
    return 1


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
        print(asp_program("#show combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show combo/3."))
        print(sorted(set(asp.atoms(model, "combo"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(s, r, f, "Ari", "girl", "Koa", "boy", "Mira", "girl")) for s, r, f in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
