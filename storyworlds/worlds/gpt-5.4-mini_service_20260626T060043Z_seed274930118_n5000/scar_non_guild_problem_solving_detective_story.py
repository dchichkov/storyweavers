#!/usr/bin/env python3
"""
storyworlds/worlds/scar_non_guild_problem_solving_detective_story.py
=====================================================================

A tiny detective-style story world about a careful investigator, a suspicious
scar, and a guild dispute that gets solved by looking closely.

Seed tale:
---
A young detective noticed a lantern maker with a long scar on one cheek near the
guild hall. The maker said he was not with the guild, but a guild badge had been
found near the broken latch. The detective followed small clues: a muddy boot
print, a bent key, and a torn ribbon. In the end, the detective learned that a
helpful non-guild messenger had taken the badge to keep it safe, and the real
trouble was a simple broken latch. The guild got its badge back, the messenger
got an apology, and the detective wrote down every clue.

World premise:
- Entities have physical meters and emotional memes.
- A case can be solved only by matching clues to their source.
- The "scar" is a visible physical clue that can mislead the investigation.
- "guild" and "non-guild" are social status facts that affect suspicion, but do
  not determine guilt by themselves.
- The resolution comes from problem solving: comparing clues, testing a lock,
  and returning the missing object to its owner.

Story shape:
- Setup: introduce detective, place, key object, and suspicious people.
- Tension: a missing guild badge and a scarred stranger create uncertainty.
- Turn: the detective tests clues and finds the broken latch.
- Resolution: the badge is returned, the misunderstanding is cleared, and the
  detective’s confidence grows.

This is a standalone world script that follows the Storyweavers contract.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    badge: object | None = None
    casebook: object | None = None
    detective: object | None = None
    lock: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"girl", "woman", "detective"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "man"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

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
class Location:
    name: str
    indoor: bool = True
    features: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    suspect: str
    clue: str
    name: str
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
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.location)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "guildhall": Location(name="the guild hall", indoor=True, features={"badge", "latch", "ledger"}),
    "workshop": Location(name="the lantern workshop", indoor=True, features={"soot", "tools", "ribbon"}),
    "dock": Location(name="the dock office", indoor=True, features={"mud", "key", "crate"}),
}

SUSPECTS = {
    "guild": ("guild lantern maker", True),
    "non_guild": ("non-guild messenger", False),
    "apprentice": ("guild apprentice", True),
}

CLUES = {
    "scar": "a long scar on one cheek",
    "badge": "a brass guild badge",
    "key": "a bent brass key",
    "mud": "a muddy boot print",
    "ribbon": "a torn ribbon",
}


@dataclass
class ReasonableCase:
    suspect: str
    clue: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world with clues, guilds, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
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


def valid_cases() -> list[ReasonableCase]:
    return [
        ReasonableCase("guild", "scar"),
        ReasonableCase("guild", "badge"),
        ReasonableCase("non_guild", "badge"),
        ReasonableCase("non_guild", "key"),
        ReasonableCase("apprentice", "mud"),
        ReasonableCase("apprentice", "ribbon"),
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    cases = valid_cases()
    if getattr(args, "suspect", None) and getattr(args, "clue", None):
        pair = (getattr(args, "suspect", None), getattr(args, "clue", None))
        if not any(c.suspect == pair[0] and c.clue == pair[1] for c in cases):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in cases
        if (getattr(args, "suspect", None) is None or c.suspect == getattr(args, "suspect", None))
        and (getattr(args, "clue", None) is None or c.clue == getattr(args, "clue", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    pick = rng.choice(filtered)
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(["Mara", "Ivy", "Noel", "June", "Tess"])
    return StoryParams(place=place, suspect=pick.suspect, clue=pick.clue, name=name)


def make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    detective = world.add(Entity(id=params.name, kind="character", type="detective", label=params.name))
    suspect_label, is_guild = _safe_lookup(SUSPECTS, params.suspect)
    suspect = world.add(Entity(id="suspect", kind="character", type="person", label=suspect_label))
    clue_text = _safe_lookup(CLUES, params.clue)
    badge = world.add(Entity(id="badge", type="thing", label="badge", phrase="a brass guild badge", owner="guild"))
    lock = world.add(Entity(id="lock", type="thing", label="latch", phrase="a stubborn latch"))
    casebook = world.add(Entity(id="casebook", type="thing", label="notebook", phrase="a neat notebook"))

    world.facts.update(
        detective=detective,
        suspect=suspect,
        clue=clue_text,
        suspect_is_guild=is_guild,
        badge=badge,
        lock=lock,
        casebook=casebook,
    )

    detective.memes["curiosity"] = 1
    detective.memes["confidence"] = 0

    world.say(f"{detective.id} was a careful detective who liked quiet rooms and clear clues.")
    world.say(f"One evening, {detective.id} went to {world.location.name} with {casebook.label_word if hasattr(casebook, 'label_word') else 'a notebook'} ready.")
    world.say(f"There, {detective.id} found {suspect.label}, and {suspect.pronoun('possessive')} face had {CLUES['scar']}.")

    world.para()
    world.say(f"On the table lay {badge.phrase}, and that made the room feel strange and tense.")
    if params.clue == "scar":
        world.say(f"The scar made {suspect.label} look suspicious, but {detective.id} knew a scar was only a mark, not a story.")
    elif params.clue == "badge":
        world.say(f"The missing badge was important because the guild used it to open the records drawer.")
    elif params.clue == "key":
        world.say(f"A bent key can stop a latch from opening, which gave {detective.id} a better question to ask.")
    elif params.clue == "mud":
        world.say(f"The muddy print was small and uneven, so {detective.id} looked near the door instead of at the suspect.")
    else:
        world.say(f"The torn ribbon looked like it came from someone rushing, which was a clue worth keeping.")

    world.para()
    world.say(f"{detective.id} did not guess. {detective.id} tested the latch, matched the print, and checked where the badge had been.")
    world.say(f"The clue that mattered was {clue_text}, and it pointed away from blame and toward a broken part.")
    world.say(f"When {detective.id} fixed the latch and lifted the loose panel, the badge turned up hidden behind it.")

    world.para()
    if params.suspect == "non_guild":
        world.say(f"It turned out the non-guild messenger had moved the badge to keep it safe, not to steal it.")
        world.say(f"{suspect.label} smiled in relief when {detective.id} explained the mistake.")
    elif params.suspect == "guild":
        world.say(f"The guild lantern maker had no reason to hide the badge; the real problem was the broken latch.")
        world.say(f"{suspect.label} helped hold the door while {detective.id} returned the badge to the records drawer.")
    else:
        world.say(f"The guild apprentice had touched the drawer, but only because the latch had jammed and needed help.")
        world.say(f"{suspect.label} thanked {detective.id} for looking carefully before accusing anyone.")

    detective.memes["confidence"] += 1
    detective.memes["joy"] += 1
    world.facts["solved"] = True
    world.facts["scar_text"] = CLUES["scar"]
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for children that includes the words "scar", "non", and "guild".',
        f"Tell a story about {f['detective'].id}, who solves a small mystery at {world.location.name} by checking clues instead of guessing.",
        f"Write a gentle problem-solving story where a guild badge, a scar, and a careful question lead to the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    suspect = _safe_fact(world, f, "suspect")
    clue = _safe_fact(world, f, "clue")
    return [
        QAItem(
            question=f"Who solved the mystery at {world.location.name}?",
            answer=f"{detective.id} solved it by looking closely and following the clues.",
        ),
        QAItem(
            question="Why did the scar not prove that the suspect was guilty?",
            answer="Because a scar is only a mark on someone's skin, not proof that they did anything wrong.",
        ),
        QAItem(
            question="What did the detective find after checking the latch?",
            answer="The detective found the missing guild badge hidden behind the loose panel.",
        ),
        QAItem(
            question="What clue mattered most in the case?",
            answer=f"The clue that mattered most was {clue}, because it pointed to the real problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a guild?",
            answer="A guild is a group of people who work in the same craft or trade.",
        ),
        QAItem(
            question="What does non-guild mean?",
            answer="Non-guild means someone does not belong to that guild.",
        ),
        QAItem(
            question="What is a scar?",
            answer="A scar is a mark left on skin after a cut or hurt has healed.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues because clues help them solve a mystery without guessing.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, (label, is_guild) in SUSPECTS.items():
        lines.append(asp.fact("suspect", pid))
        lines.append(asp.fact("role", pid, "guild_member" if is_guild else "non_guild"))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    return "\n".join(lines)


ASP_RULES = r"""
chosen_case(S, C) :- suspect(S), clue(C).
reasonable(S, C) :- chosen_case(S, C), clue(C), suspect(S).

#show reasonable/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    python_set = {(c.suspect, c.clue) for c in valid_cases()}
    asp_set = set(asp_valid_cases())
    if asp_set == python_set:
        print(f"OK: clingo gate matches valid_cases() ({len(asp_set)} cases).")
        return 0
    print("MISMATCH between clingo and python valid cases.")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


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
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  location: {world.location.name}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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


CURATED = [
    StoryParams(place="guildhall", suspect="non_guild", clue="scar", name="Mara"),
    StoryParams(place="workshop", suspect="guild", clue="badge", name="Ivy"),
    StoryParams(place="dock", suspect="apprentice", clue="mud", name="Tess"),
]


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    if getattr(args, "all", None):
        return [generate(p) for p in CURATED]
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
        rng = random.Random(base_seed + i)
        i += 1
        params = resolve_params(args, rng)
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        cases = asp_valid_cases()
        print(f"{len(cases)} reasonable cases:\n")
        for s, c in cases:
            print(f"  {s} + {c}")
        return

    samples = build_samples(args)

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
            header = f"### {p.name}: {p.place}, {p.suspect}, {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
