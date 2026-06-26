#!/usr/bin/env python3
"""
storyworlds/worlds/skill_daze_friendship_kindness_detective_story.py
=====================================================================

A small story world with a detective-story shape: a child detective notices a
friend in a daze, uses skill and kindness to follow clues, and ends with
friendship made stronger by the solved case.

Seed tale used as the premise:
---
A little detective loved solving small mysteries. One morning, her friend was in a
daze because a special token had gone missing before the school fair. The detective
did not tease or rush. Instead, she listened kindly, looked carefully, and used
her skill to follow tiny clues. She found the token, and the friend smiled again.
Their friendship felt even warmer after the case was solved.
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
    hidden_at: Optional[str] = None
    found: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    detective: object | None = None
    friend: object | None = None
    missing: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        for k in ("dust", "care", "order", "rest", "skill"):
            self.meters.setdefault(k, 0.0)
        for k in ("friendship", "kindness", "daze", "worry", "joy", "confidence"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the library"
    affords: set[str] = field(default_factory=set)
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
class Case:
    id: str
    missing_label: str
    missing_phrase: str
    clue_label: str
    clue_phrase: str
    hiding_places: set[str]
    tool_label: str
    tool_phrase: str
    tool_help: str
    keyword: str = "skill"
    tags: set[str] = field(default_factory=set)
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


SETTINGS = {
    "library": Setting("the library", affords={"search"}),
    "garden": Setting("the garden", affords={"search"}),
    "school": Setting("the school hallway", affords={"search"}),
    "market": Setting("the market", affords={"search"}),
}

CASES = {
    "badge": Case(
        id="badge",
        missing_label="badge",
        missing_phrase="a shiny fair badge",
        clue_label="sticker",
        clue_phrase="a tiny star sticker",
        hiding_places={"library", "school"},
        tool_label="magnifying glass",
        tool_phrase="a small magnifying glass",
        tool_help="look closely at little marks",
        keyword="skill",
        tags={"skill", "friendship", "kindness"},
    ),
    "key": Case(
        id="key",
        missing_label="key",
        missing_phrase="a brass music key",
        clue_label="ribbon",
        clue_phrase="a blue ribbon",
        hiding_places={"garden", "market"},
        tool_label="notebook",
        tool_phrase="a neat notebook",
        tool_help="keep clues in order",
        keyword="skill",
        tags={"skill", "friendship", "kindness"},
    ),
    "ball": Case(
        id="ball",
        missing_label="ball",
        missing_phrase="a red play ball",
        clue_label="mud mark",
        clue_phrase="a muddy little print",
        hiding_places={"garden", "school"},
        tool_label="lantern",
        tool_phrase="a bright lantern",
        tool_help="shine into dark corners",
        keyword="daze",
        tags={"skill", "friendship", "kindness", "daze"},
    ),
}

DETECTIVES = ["Maya", "Luca", "Nina", "Theo", "Ivy", "Noah", "Zoe", "Ben"]
FRIENDS = ["Eli", "Mila", "June", "Arlo", "Sage", "Ruby", "Owen", "Lia"]
TRAITS = ["careful", "brave", "gentle", "patient", "bright", "quick"]


@dataclass
class StoryParams:
    place: str
    case: str
    detective: str
    friend: str
    trait: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for case_id, case in CASES.items():
            if place in setting.affords and place in case.hiding_places:
                combos.append((place, case_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: skill, daze, friendship, kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--detective")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "case", None) is None or c[1] == getattr(args, "case", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, case_id = rng.choice(list(combos))
    detective = getattr(args, "detective", None) or rng.choice(DETECTIVES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in FRIENDS if n != detective])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, case=case_id, detective=detective, friend=friend, trait=trait)


def _case_help(case: Case) -> str:
    return case.keyword


def tell(setting: Setting, case: Case, detective_name: str, friend_name: str, trait: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type="girl" if detective_name in {"Maya", "Nina", "Ivy", "Zoe"} else "boy"))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl" if friend_name in {"Mila", "June", "Ruby", "Lia"} else "boy"))
    missing = world.add(Entity(id="missing", type=case.missing_label, label=case.missing_label, phrase=case.missing_phrase, owner=friend.id, hidden_at=setting.place))
    clue = world.add(Entity(id="clue", type=case.clue_label, label=case.clue_label, phrase=case.clue_phrase, hidden_at=setting.place))
    tool = world.add(Entity(id="tool", type=case.tool_label, label=case.tool_label, phrase=case.tool_phrase, owner=detective.id))

    friend.memes["daze"] += 1
    friend.memes["worry"] += 1
    detective.memes["friendship"] += 1
    detective.memes["kindness"] += 1

    world.say(f"{detective.id} was a {trait} little detective who liked solving quiet mysteries.")
    world.say(f"{detective.id} and {friend.id} were good friends, and they trusted each other with small secrets.")
    world.say(f"One day, {friend.id} looked in a daze because {friend.pronoun('possessive')} {case.missing_label} had gone missing before the fair.")
    world.para()
    world.say(f"{detective.id} did not laugh or rush. {detective.pronoun().capitalize()} spoke kindly and asked where {friend.id} had last seen it.")
    world.say(f"Then {detective.id} used {tool.phrase} to {case.tool_help} and began to follow the clue.")

    if setting.place in case.hiding_places:
        detective.meters["skill"] += 1
        clue.found = True
        missing.found = True
        missing.hidden_at = None
        friend.memes["daze"] = 0.0
        friend.memes["joy"] += 1
        friend.memes["kindness"] += 1
        detective.memes["friendship"] += 1
        detective.memes["joy"] += 1
        world.para()
        world.say(f"Near a {case.clue_label} by {setting.place}, {detective.id} noticed a tiny mark and followed it with skill.")
        world.say(f"At last, {detective.id} found {case.missing_phrase} tucked away where it had slipped out of sight.")
        world.say(f"{friend.id} smiled, and the two friends stood together with the case solved.")
        world.say(f"Their friendship felt warmer than before, and {detective.id}'s kindness made the answer feel even better.")
    else:
        pass

    world.facts.update(
        detective=detective,
        friend=friend,
        missing=missing,
        clue=clue,
        tool=tool,
        case=case,
        setting=setting,
        resolved=missing.found,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = _safe_fact(world, f, "case")
    detective: Entity = _safe_fact(world, f, "detective")
    friend: Entity = _safe_fact(world, f, "friend")
    return [
        f'Write a short detective story for a young child that includes the word "{case.keyword}".',
        f"Tell a gentle mystery about {detective.id} helping {friend.id} with kindness and friendship.",
        f"Write a child-sized detective tale where a missing {case.missing_label} is found by using skill.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = _safe_fact(world, f, "detective")
    friend: Entity = _safe_fact(world, f, "friend")
    case: Case = _safe_fact(world, f, "case")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who solved the mystery in {setting.place}?",
            answer=f"{detective.id} solved the mystery by using skill, kindness, and careful looking.",
        ),
        QAItem(
            question=f"Why was {friend.id} in a daze?",
            answer=f"{friend.id} was in a daze because {friend.pronoun('possessive')} {case.missing_label} had gone missing before the fair.",
        ),
        QAItem(
            question=f"What did {detective.id} use to help with the search?",
            answer=f"{detective.id} used {case.tool_phrase} to help follow the clue and find the missing item.",
        ),
        QAItem(
            question=f"How did the story end for the two friends?",
            answer=f"The missing {case.missing_label} was found, {friend.id} smiled again, and their friendship felt warmer at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = _safe_fact(world, f, "case")
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and tries to figure out what happened.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the warm feeling between people who care about each other and like spending time together.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps solve a mystery.",
        ),
        QAItem(
            question=f"What is a {case.tool_label} for?",
            answer=f"A {case.tool_label} is useful for {case.tool_help}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.hidden_at:
            parts.append(f"hidden_at={e.hidden_at}")
        if e.found:
            parts.append("found=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", case="badge", detective="Maya", friend="Eli", trait="careful"),
    StoryParams(place="garden", case="ball", detective="Luca", friend="Ruby", trait="gentle"),
    StoryParams(place="school", case="badge", detective="Ivy", friend="Arlo", trait="bright"),
]


ASP_RULES = r"""
place(library). place(garden). place(school). place(market).
case(badge). case(key). case(ball).

affords(library,search). affords(garden,search). affords(school,search). affords(market,search).
hiding_at(badge,library). hiding_at(badge,school).
hiding_at(key,garden). hiding_at(key,market).
hiding_at(ball,garden). hiding_at(ball,school).

valid(Place,Case) :- affords(Place,search), hiding_at(Case,Place).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in sorted(_safe_lookup(SETTINGS, pid).affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        for p in sorted(case.hiding_places):
            lines.append(asp.fact("hiding_at", cid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CASES, params.case), params.detective, params.friend, params.trait)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = valid_combos_asp()
        print(f"{len(combos)} compatible (place, case) combos:\n")
        for place, case in combos:
            print(f"  {place:8} {case:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective} and {p.friend}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
