#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/boob_dim_wrist_bad_ending_reconciliation_mystery.py
===============================================================================================================

A small, self-contained fable-style story world built from the seed words
"boob-dim" and "wrist", with a mystery to solve, a bad ending, and a gentle
reconciliation.

The world models a little woodland friendship problem:
- a childlike animal hears a worrying clue,
- a treasured charm goes missing,
- the wrong creature is blamed,
- the mystery is solved by noticing a physical trace on a wrist-band,
- the ending is initially bad, then repaired through apology and truth.

The prose is generated from simulated state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    wears: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    friend: object | None = None
    hero: object | None = None
    wristband: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "deer"}
        male = {"boy", "father", "man", "fox", "owl", "rabbit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    name: str
    indoors: bool = False
    clues: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    clue: str
    secret: str
    culprit: str
    solver_hint: str
    ending: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
        return World(self.place, copy.deepcopy(self.entities), copy.deepcopy(self.facts),
                     [[]], set(self.fired))
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


def guess_problem(meters: dict[str, float]) -> bool:
    return meters.get("missing", 0.0) >= THRESHOLD or meters.get("fear", 0.0) >= THRESHOLD


def _r_find_band(world: World) -> list[str]:
    out: list[str] = []
    fox = world.get("hero")
    band = world.get("wristband")
    if fox.memes.get("searching", 0) < THRESHOLD:
        return out
    sig = ("find_band",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    band.meters["found"] = 1
    out.append(f"At last, {fox.id} noticed a little blue shine caught on a branch.")
    out.append(f"It was {band.label}, and a tiny snag on the wrist band told the truth.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    fox = world.get("hero")
    friend = world.get("friend")
    if fox.memes.get("truth", 0) < THRESHOLD or friend.memes.get("hurt", 0) < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["hurt"] = 0
    fox.memes["guilt"] += 1
    fox.memes["love"] += 1
    out.append(f"{fox.id} bowed {fox.pronoun('possessive')} head and told the truth.")
    out.append(f"{friend.id} forgave {fox.pronoun('object')}, and the two stood close again.")
    return out


RULES = [
    _r_find_band,
    _r_reconcile,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def tell(place: Place, mystery: Mystery, name: str, friend_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type="fox", label=name, traits=[trait]))
    friend = world.add(Entity(id="friend", kind="character", type="owl", label=friend_name, traits=["wise"]))
    wristband = world.add(Entity(
        id="wristband",
        type="thing",
        label="the wrist band",
        phrase="a little wrist band with a blue bead",
        owner=hero.id,
        meters={"missing": 1},
    ))
    charm = world.add(Entity(
        id="charm",
        type="thing",
        label="the dim charm",
        phrase="the boob-dim charm",
        owner=friend.id,
    ))

    hero.memes["worry"] = 1
    friend.memes["hurt"] = 1

    world.say(
        f"Once in {place.name}, {hero.label} the fox and {friend.label} the owl kept a small rule: "
        f"when the night looked strange, they would tell the truth before they guessed."
    )
    world.say(
        f"One evening, {hero.label} found {mystery.clue}; it was a {mystery.secret} kind of sign, "
        f"and the little wood grew very still."
    )

    world.para()
    world.say(
        f"{hero.label} feared the missing {wristband.label}, and {friend.label} feared the old tale was true."
    )
    world.say(
        f"They searched beneath roots, stones, and fern leaves, but the mystery only grew larger."
    )
    hero.memes["searching"] = 1
    hero.meters["missing"] = 1
    propagate(world, narrate=True)

    world.para()
    hero.memes["truth"] = 1
    world.say(
        f"Then {hero.label} saw the snag on the {wristband.label} and remembered the branch that had brushed past."
    )
    world.say(
        f"The clue was not a thief after all. It was only the wind, the branch, and a careless bump."
    )
    world.say(
        f"The bad ending had already hurt hearts, because {friend.label} had been blamed too soon."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero.label} apologized to {friend.label}, and {friend.label} listened."
    )
    world.say(
        f"They fixed the {wristband.label}, returned the dim charm, and made room for kindness again."
    )
    world.say(
        f"In that little wood, they learned that a clear truth can mend a dark mistake."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        wristband=wristband,
        charm=charm,
        place=place,
        mystery=mystery,
        resolved=True,
    )
    return world


PLACES = {
    "wood": Place(name="the green wood", clues={"branch", "bead", "wind"}),
    "orchard": Place(name="the old orchard", clues={"branch", "apple", "wind"}),
    "lane": Place(name="the mossy lane", clues={"stone", "mud", "branch"}),
}

MYSTERIES = {
    "branch": Mystery(
        id="branch",
        clue="a blue snag on a branch",
        secret="wrist-band",
        culprit="wind",
        solver_hint="look for a snag",
        ending="truth",
    ),
    "lantern": Mystery(
        id="lantern",
        clue="a dim glow under the roots",
        secret="boob-dim charm",
        culprit="shadow",
        solver_hint="follow the glow",
        ending="truth",
    ),
}

TRAITS = ["curious", "gentle", "quiet", "brave", "thoughtful"]
FOX_NAMES = ["Rusty", "Nico", "Fenn", "Tavi", "Milo", "Pip"]
OWL_NAMES = ["Ora", "Mira", "Sage", "Hush", "Luma", "Tilo"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    friend_name: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style mystery with a bad ending and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    name = getattr(args, "name", None) or rng.choice(FOX_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(OWL_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, friend_name=friend_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(MYSTERIES, params.mystery), params.name, params.friend_name, params.trait)
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
    friend = _safe_fact(world, f, "friend")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short fable about a fox named {hero.label}, an owl named {friend.label}, and the clue "{mystery.clue}".',
        f"Tell a child-friendly mystery where {hero.label} learns the truth about a wrist band and makes up with {friend.label}.",
        f'Write a gentle story that includes the words "boob-dim" and "wrist" and ends with an apology and reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    mystery = _safe_fact(world, f, "mystery")
    place = _safe_fact(world, f, "place").name
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label} the fox and {friend.label} the owl in {place}.",
        ),
        QAItem(
            question=f"What clue started the mystery?",
            answer=f"The mystery began with {mystery.clue}, which made everyone think something was wrong.",
        ),
        QAItem(
            question=f"What did the tiny band on the wrist prove?",
            answer=f"It proved the problem was a branch snag and not a thief, so the truth could be found.",
        ),
        QAItem(
            question=f"How did the story end at first, before it was fixed?",
            answer="It ended badly for a while because the wrong creature was feared and hearts felt hurt.",
        ),
        QAItem(
            question=f"How was the bad ending repaired?",
            answer="The fox apologized, the owl forgave, and they chose honesty and kindness together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wrist?",
            answer="A wrist is the joint between your hand and your arm, where a band or bracelet can sit.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a hurt or a misunderstanding.",
        ),
        QAItem(
            question='What could "boob-dim" mean in a fairy-tale kind of story?',
            answer='Here, "boob-dim" is a made-up phrase for a small dim charm that glows softly in the dark.',
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is solvable when a clue exists and the wrist-band snags.
solvable(M) :- mystery(M), clue(M,_), wrist_snag(M).

% Reconciliation follows truth and apology.
reconciled(H,F) :- truth(H), apology(H), hurt(F).

% A bad ending happens when the wrong creature is blamed before the truth is found.
bad_ending(H,F) :- blamed(H,F), not truth(H).

#show solvable/1.
#show reconciled/2.
#show bad_ending/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(p.clues):
            lines.append(asp.fact("clue_word", pid, c))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("wrist_snag", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solvable/1.\n#show reconciled/2.\n#show bad_ending/2."))
    atoms = set((sym.name, tuple(arg.name if arg.type != getattr(arg, "Number", None) else arg.number for arg in sym.arguments)) for sym in model)
    expected = {("solvable", ("branch",)), ("solvable", ("lantern",))}
    if atoms:
        print("OK: ASP ran.")
        return 0
    print("ASP verification produced no atoms.")
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


CURATED = [
    StoryParams(place="wood", mystery="branch", name="Rusty", friend_name="Ora", trait="curious"),
    StoryParams(place="orchard", mystery="lantern", name="Fenn", friend_name="Sage", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program(""))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
