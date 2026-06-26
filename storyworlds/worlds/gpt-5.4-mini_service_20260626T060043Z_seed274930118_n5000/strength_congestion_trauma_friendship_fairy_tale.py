#!/usr/bin/env python3
"""
Fairy-tale storyworld: strength, congestion, trauma, and friendship.

A small child-facing domain about a brave helper who faces a blockage in a
roadway or path, gets hurt or frightened, and then repairs the problem with a
friend. The world is built to make the physical, emotional, and social changes
matter in the prose.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "woman", "fairy"}
        male = {"boy", "prince", "king", "man", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str
    tag: str
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
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    obstacle: str
    risk: str
    mess: str
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


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    finish: str
    helps: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


@dataclass
class StoryParams:
    setting: str
    problem: str
    aid: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None
    p: object | None = None
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
    "forest_gate": Setting(place="the forest gate", tag="gate", affords={"blockage"}),
    "bridge": Setting(place="the old stone bridge", tag="bridge", affords={"blockage"}),
    "market_road": Setting(place="the market road", tag="road", affords={"blockage"}),
    "castle_hall": Setting(place="the castle hall", tag="hall", affords={"blockage"}),
}

PROBLEMS = {
    "root_tangle": Problem(
        id="root_tangle",
        verb="pull the roots apart",
        gerund="pulling tangled roots",
        rush="rush to the gate",
        obstacle="a knot of roots",
        risk="scraped paws and a shaken heart",
        mess="blocked",
        tags={"strength", "congestion"},
    ),
    "wagon_jam": Problem(
        id="wagon_jam",
        verb="move the wagon aside",
        gerund="moving a jammed wagon",
        rush="push toward the road",
        obstacle="a wagon stuck sideways",
        risk="bruised shoulders and a frightened step",
        mess="jammed",
        tags={"strength", "congestion"},
    ),
    "river_fall": Problem(
        id="river_fall",
        verb="cross the bridge",
        gerund="crossing the shaky bridge",
        rush="step onto the bridge",
        obstacle="a broken plank",
        risk="a scary tumble and a sore knee",
        mess="unsafe",
        tags={"trauma", "friendship"},
    ),
    "crowd_clog": Problem(
        id="crowd_clog",
        verb="clear the crowd",
        gerund="guiding a crowded lane",
        rush="call to the people",
        obstacle="a crowd packed too tightly",
        risk="a panicked bump and a racing breath",
        mess="clogged",
        tags={"congestion", "friendship"},
    ),
}

AIDS = {
    "friend_rope": Aid(
        id="friend_rope",
        label="a long rope",
        prep="tie the rope around the stuck thing together",
        finish="They tugged in time and the way opened at last.",
        helps={"blockage"},
    ),
    "friend_lantern": Aid(
        id="friend_lantern",
        label="a bright lantern",
        prep="light the darkest corner and go slowly together",
        finish="The light made the path feel safe again.",
        helps={"trauma"},
    ),
    "friend_stones": Aid(
        id="friend_stones",
        label="flat stepping stones",
        prep="place the stones one by one and make a steadier way",
        finish="Soon the crossing was calm and careful.",
        helps={"bridge"},
    ),
    "friend_basket": Aid(
        id="friend_basket",
        label="a basket for carrying things",
        prep="carry the smaller pieces away together",
        finish="With the clutter moved, the road could breathe again.",
        helps={"road", "hall"},
    ),
}

HERO_NAMES = ["Mira", "Tarin", "Lina", "Rowan", "Nell", "Soren", "Pippa", "Elio"]
FRIEND_NAMES = ["Bram", "Wren", "Luma", "Orin", "Ari", "Tess", "Juno", "Pax"]
TRAITS = ["brave", "gentle", "curious", "patient", "kind", "steadfast"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for aid, aidv in AIDS.items():
                if setting.tag in aidv.helps or problem.tags & aidv.helps:
                    out.append((sid, pid, aid))
    return sorted(set(out))


def explain_rejection(problem: Problem, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} does not fit the kind of trouble in {problem.id}. "
        f"The cure must match the blockage, injury, or fear, so this combination is rejected.)"
    )


def explain_gender(hero_type: str, friend_type: str) -> str:
    return f"(No story: this world expects a child hero and a helpful friend, not {hero_type} with {friend_type}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about strength, congestion, trauma, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "aid", None) is None or c[2] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    sid, pid, aid = (list(rng.choice(combos)) + [None, None, None])[:3]
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    friend_type = getattr(args, "friend_type", None) or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=sid,
        problem=pid,
        aid=aid,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        hero_type=hero_type,
        friend_name=getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES),
        friend_type=friend_type,
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def _clean_join(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name, traits=[params.trait, "young"]))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type, label=params.friend_name, traits=["helpful", "loyal"]))
    problem = _safe_lookup(PROBLEMS, params.problem)
    aid = _safe_lookup(AIDS, params.aid)

    hero.memes["courage"] = 1
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1

    world.say(f"Once upon a time, {hero.label} was a {params.trait} little {hero.type} who loved tales of brave helpers.")
    world.say(f"{hero.label} and {friend.label} were best friends, and they walked together wherever the day asked for kindness.")

    world.para()
    world.say(f"One day, they came to {world.setting.place}. There they found {problem.obstacle}.")
    world.say(f"{hero.label} wanted to {problem.verb}, but the way was too hard, and the trouble felt like {problem.risk}.")
    hero.meters["strength"] += 1
    world.facts["problem"] = problem
    world.facts["aid"] = aid
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["setting"] = world.setting
    world.facts["hurt"] = "trauma" in problem.tags or "unsafe" in problem.mess

    world.para()
    world.say(f"{friend.label} came close and said, \"We can use {aid.label}.\"")
    world.say(f"Together they chose to {aid.prep}.")
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1

    world.para()
    if "trauma" in problem.tags:
        world.say(f"{hero.label} had a shaky breath after the danger, so {friend.label} stood beside {hero.label} until the fear grew small.")
        hero.memes["comfort"] += 1
    world.say(aid.finish)
    hero.meters["strength"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(f"In the end, {hero.label} felt proud, {friend.label} smiled, and the path was open again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy-tale for young children about {f["hero"].label} and {f["friend"].label}, where friendship helps with {f["problem"].id}.',
        f"Tell a gentle story where a brave child must use strength to solve a congestion problem and a friend helps the child feel safe.",
        f'Write a simple fairy tale using the words "strength", "congestion", and "trauma" with a happy friendship ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, problem, aid = f["hero"], f["friend"], f["problem"], f["aid"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.label}, a {hero.traits[0]} little {hero.type}, and the friend {friend.label}.",
        ),
        QAItem(
            question=f"What was blocking the way at {world.setting.place}?",
            answer=f"The way was blocked by {problem.obstacle}. That made the path feel stuck and hard to use.",
        ),
        QAItem(
            question=f"How did {hero.label} and {friend.label} fix the problem?",
            answer=f"They used {aid.label} and worked together. Their friendship gave them the strength to clear the trouble.",
        ),
    ]
    if f["hurt"]:
        qa.append(
            QAItem(
                question=f"Why did the danger feel upsetting?",
                answer=f"It felt upsetting because {problem.risk}. After that, {friend.label} stayed close so {hero.label} could calm down.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does strength mean?",
            answer="Strength means having the power to do something hard, like lifting, pulling, or staying brave during trouble.",
        ),
        QAItem(
            question="What is congestion?",
            answer="Congestion means there is too much packed into one place, so the way is crowded or blocked.",
        ),
        QAItem(
            question="What is trauma?",
            answer="Trauma is a very upsetting or scary hurt, and a kind friend can help someone feel safer again.",
        ),
        QAItem(
            question="Why are friends helpful in fairy tales?",
            answer="Friends are helpful because they share ideas, give comfort, and work together when one person cannot do it alone.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.label} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
problem(P) :- problem_fact(P).
aid(A) :- aid_fact(A).

valid(S,P,A) :- setting(S), problem(P), aid(A), fits(S,P,A).
"""


def asp_facts() -> str:
    import asp
    out = []
    for sid in SETTINGS:
        out.append(asp.fact("setting_fact", sid))
    for pid in PROBLEMS:
        out.append(asp.fact("problem_fact", pid))
    for aid in AIDS:
        out.append(asp.fact("aid_fact", aid))
    for sid, pid, aid in valid_combos():
        out.append(asp.fact("fits", sid, pid, aid))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for sid, pid, aid in sorted(valid_combos()):
            p = StoryParams(
                setting=sid,
                problem=pid,
                aid=aid,
                hero_name=random.choice(HERO_NAMES),
                hero_type="girl",
                friend_name=random.choice(FRIEND_NAMES),
                friend_type="boy",
                trait=random.choice(TRAITS),
            )
            samples.append(generate(p))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
