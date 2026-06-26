#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/octopi_commit_cling_flashback_humor_mystery_to.py
===========================================================================================================================

A heartwarming storyworld about an octopus helper who learns to commit, cling
to a clue, and solve a small mystery with a funny flashback.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    clue_ent: object | None = None
    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Setting:
    place: str = "the tide pool"
    detail: str = "bright rocks and swaying sea grass"
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
class Clue:
    id: str
    label: str
    phrase: str
    hint: str
    hides_in: str
    found_by: str
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
    clue: str
    name: str
    companion: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.flashback_seen = False
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.flashback_seen = self.flashback_seen
        return c


def _flashed_back(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("hero")
    clue = _safe_fact(world, world.facts, "clue")
    if world.flashback_seen:
        return out
    if child.memes.get("puzzled", 0) < THRESHOLD:
        return out
    sig = ("flashback")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.flashback_seen = True
    out.append(
        f"Then {child.id} remembered a funny moment from earlier: the little crab had "
        f"worn the same clue like a hat, and everyone had laughed until bubbles rose."
    )
    return out


def _cling_to_clue(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("hero")
    clue = world.get("clue")
    if child.memes.get("commitment", 0) < THRESHOLD:
        return out
    if child.memes.get("curious", 0) < THRESHOLD:
        return out
    sig = ("cling", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    out.append(f"{child.id} kept clinging to the clue, because it felt important and kind.")
    return out


def _solve_mystery(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("hero")
    clue = world.get("clue")
    friend = world.get("companion")
    if child.memes.get("hope", 0) < THRESHOLD:
        return out
    if friend.memes.get("trust", 0) < THRESHOLD:
        return out
    sig = ("solve")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["mystery_solved"] = 1
    clue.meters["found"] = 1
    out.append(
        f"Together they solved the mystery: the missing shell charm had never been lost. "
        f"It had slipped into a coral nook where the current liked to tuck tiny things."
    )
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_flashed_back, _cling_to_clue, _solve_mystery):
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "tidepool": Setting(place="the tide pool", detail="bright rocks and swaying sea grass"),
    "harbor": Setting(place="the harbor", detail="stacked nets and a sleepy blue boat"),
    "reef": Setting(place="the reef", detail="pink coral and warm sunbeams in the water"),
}

CLUES = {
    "shell": Clue(
        id="clue",
        label="shell charm",
        phrase="a tiny shell charm with a blue ribbon",
        hint="The ribbon was tied in a neat knot.",
        hides_in="coral nook",
        found_by="careful searching",
    ),
    "pearl": Clue(
        id="clue",
        label="pearl button",
        phrase="a round pearl button from an old coat",
        hint="It shimmered like moonlight under water.",
        hides_in="sand pocket",
        found_by="gentle digging",
    ),
}

COMPANIONS = {
    "crab": ("crab", "a cheerful crab friend"),
    "seahorse": ("seahorse", "a shy seahorse friend"),
    "turtle": ("turtle", "a patient turtle friend"),
}

NAMES = ["Mina", "Nori", "Ollie", "Pia", "Rin", "Tavi", "Luna", "Milo"]


@dataclass
class WorldState:
    setting: Setting
    clue: Clue
    hero: Entity
    companion: Entity
    quest: str
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


def build_world(params: StoryParams) -> World:
    setting = SETTINGS["reef" if params.clue == "pearl" else "tidepool"]
    clue = _safe_lookup(CLUES, params.clue)
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="octopus",
        label="little octopus",
        traits=["helpful", "curious", "warmhearted"],
        meters={"arms": 8},
        memes={"curious": 1.0, "commitment": 0.0, "puzzled": 0.0, "hope": 0.0},
    ))
    companion_key, companion_label = _safe_lookup(COMPANIONS, params.companion)
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=companion_key,
        label=companion_label,
        traits=["kind", "steady"],
        memes={"trust": 1.0},
    ))
    clue_ent = world.add(Entity(
        id="clue",
        type="thing",
        label=clue.label,
        phrase=clue.phrase,
        meters={"hidden": 1.0},
        owner=None,
    ))
    world.facts.update(clue=clue_ent, hero=hero, companion=companion, setting=setting)

    world.say(
        f"{hero.id} was a little octopus who loved helping at {setting.place}. "
        f"{setting.detail.capitalize()} made the water feel like a friendly secret."
    )
    world.say(
        f"One morning, {hero.id} noticed something missing: {clue.phrase}. "
        f"{hero.id} wanted to find it before the little dock lanterns came on."
    )
    world.para()
    world.say(
        f"{hero.id} looked under shells and behind seaweed, but the clue was still gone. "
        f"{hero.id} felt puzzled, then made a brave little promise to keep looking."
    )
    hero.memes["puzzled"] = 1.0
    hero.memes["commitment"] = 1.0
    world.say(
        f"Then {params.companion} swam over with a grin and said, "
        f"\"Let's solve it together.\""
    )
    propagate(world, narrate=True)
    if clue.meters.get("found", 0) >= THRESHOLD:
        world.para()
        world.say(
            f"{hero.id} tucked the shell charm safely back where it belonged. "
            f"The water looked calmer, and everyone smiled because the small mystery was solved."
        )
    world.facts["story_state"] = WorldState(setting=setting, clue=clue, hero=hero, companion=companion, quest="find clue")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    clue = _safe_fact(world, f, "clue")
    setting = _safe_fact(world, f, "setting")
    return [
        f"Write a heartwarming story about an octopus named {hero.id} who tries to find {clue.phrase} at {setting.place}.",
        f"Tell a gentle mystery story with a flashback and a funny moment, where {hero.id} keeps a promise and solves a small problem.",
        f"Create a child-friendly story about octopi, a clue, and a kind friend who helps with the search.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    clue = _safe_fact(world, f, "clue")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little octopus who wants to help and solve a mystery.",
        ),
        QAItem(
            question=f"What was missing at {setting.place}?",
            answer=f"The missing thing was {clue.phrase}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the clue?",
            answer=f"{companion.label.capitalize()} helped {hero.id} keep looking and solve the mystery together.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember the funny flashback?",
            answer=(
                f"{hero.id} remembered it because the search felt puzzly, and the memory of the crab wearing the clue "
                f"like a hat made the moment lighter."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the mystery solved and the missing charm safely put back where it belonged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are octopi?",
            answer="Octopi are sea animals with eight arms. They can squeeze into small spaces and are very clever.",
        ),
        QAItem(
            question="What does it mean to commit to something?",
            answer="To commit means to decide to keep trying and not give up when something is a little hard.",
        ),
        QAItem(
            question="What does it mean to cling?",
            answer="To cling means to hold on tightly or keep close to something.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand yet and want to figure out.",
        ),
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback shows something that happened earlier, so the story can remember an old moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    out.append(f"fired={sorted({x[0] for x in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
% If the hero is puzzled and committed, the flashback may appear.
flashback(H) :- puzzled(H), committed(H).

% Clinging to the clue is a sign of care and attention.
cling(H, C) :- committed(H), clue(C).

% A mystery is solved when the hero and companion trust each other,
% and the clue is found.
solve(H, C) :- cling(H, C), trust(COMP), companion(COMP), clue(C), committed(H).

#show flashback/1.
#show cling/2.
#show solve/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for cid, (_, label) in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming octopi mystery storyworld.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("tidepool", "shell", c) for c in COMPANIONS] + [("reef", "pearl", c) for c in COMPANIONS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    companion = getattr(args, "companion", None) or rng.choice(list(COMPANIONS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(clue=clue, name=name, companion=companion, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show flashback/1.\n#show cling/2.\n#show solve/2."))
    if model is None:
        print("ASP returned no model.")
        return 1
    print("OK: ASP program loaded.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show flashback/1.\n#show cling/2.\n#show solve/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available, but this world's main gate is narrative-first.")
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for clue in CLUES:
            for comp in COMPANIONS:
                samples.append(generate(StoryParams(clue=clue, name=rng.choice(NAMES), companion=comp)))
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i))
            samples.append(generate(p))

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
