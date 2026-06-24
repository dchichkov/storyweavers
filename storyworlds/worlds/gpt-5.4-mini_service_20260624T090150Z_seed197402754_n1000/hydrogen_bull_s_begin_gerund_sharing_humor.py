#!/usr/bin/env python3
"""
storyworlds/worlds/hydrogen_bull_s_begin_gerund_sharing_humor.py
==================================================================

A small slice-of-life story world about sharing, a bit of humor,
and a hydrogen balloon that helps the characters begin a gentle
conversation.

Seed-tale image:
---
Mina comes home from the corner market with a bright hydrogen balloon.
Her little brother jokes that it is "the bull's balloon" because a paper
tag on the string says "bull's prize." Mina laughs, then notices her
neighbor Ollie looking sad because his own balloon popped.

Mina begins-ging? No—she is beginning to think. She shares the balloon
string, then the two children take turns holding it while they walk to
the porch steps and watch it bob in the breeze. Everybody feels lighter,
and the joke turns into a small, happy afternoon.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    friend: object | None = None
    hero: object | None = None
    prize_ent: object | None = None
    shared_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    place: str
    indoors: bool
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plurality: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class SharedThing:
    id: str
    label: str
    phrase: str
    help_word: str
    tail: str
    kind: str = "thing"
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
    setting: str
    prize: str
    shared: str
    name: str
    gender: str
    friend: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "porch": Setting(place="the porch", indoors=False, affords={"share"}),
    "kitchen": Setting(place="the kitchen table", indoors=True, affords={"share"}),
    "yard": Setting(place="the yard bench", indoors=False, affords={"share"}),
}

PRIZES = {
    "juice": Prize(id="juice", label="juice box", phrase="a cool juice box", region="hands"),
    "cookie": Prize(id="cookie", label="cookie", phrase="a big cookie", region="hands"),
    "hat": Prize(id="hat", label="hat", phrase="a neat little hat", region="head"),
}

SHARED = {
    "balloon": SharedThing(
        id="balloon",
        label="hydrogen balloon",
        phrase="a shiny hydrogen balloon",
        help_word="share",
        tail="held the string together and let the balloon bob above them",
    ),
    "joke": SharedThing(
        id="joke",
        label="bull's joke",
        phrase="a silly bull's joke",
        help_word="laugh",
        tail="laughed until the joke felt friendly instead of strange",
    ),
    "phrase": SharedThing(
        id="phrase",
        label="begin-gerund phrase",
        phrase='the phrase "beginning to begin"',
        help_word="begin",
        tail="smiled and began using the odd phrase like a tiny game",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Tia", "Rosa"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Milo", "Pip", "Jun"]
FRIENDS = ["neighbor", "brother", "sister", "friend"]


def reason_ok(setting: Setting, prize: Prize, shared: SharedThing) -> bool:
    if shared.id == "balloon" and prize.region != "head":
        return True
    if shared.id in {"joke", "phrase"}:
        return True
    return False


def invalid_reason(prize: Prize, shared: SharedThing) -> str:
    return f"(No story: {shared.label} does not fit a gentle sharing scene with {prize.label}.)"


def _share(world: World, hero: Entity, friend: Entity, shared: SharedThing, prize: Entity) -> None:
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    friend.memes["hope"] = friend.memes.get("hope", 0.0) + 1
    if shared.id == "balloon":
        hero.meters["light"] = hero.meters.get("light", 0.0) + 1
        friend.meters["light"] = friend.meters.get("light", 0.0) + 1
    if shared.id == "joke":
        hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
        friend.memes["humor"] = friend.memes.get("humor", 0.0) + 1
    if shared.id == "phrase":
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
        friend.memes["curiosity"] = friend.memes.get("curiosity", 0.0) + 1


def introduce(world: World, hero: Entity, friend: Entity, prize: Entity, shared: SharedThing) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who liked quiet afternoons and small jokes."
    )
    world.say(
        f"One day, {hero.id} had {hero.pronoun('possessive')} {prize.label} and also found {shared.phrase}."
    )
    world.say(
        f"{friend.id} was nearby, watching with a patient face and a soft smile."
    )


def begin_turn(world: World, hero: Entity, friend: Entity, prize: Entity, shared: SharedThing) -> None:
    if shared.id == "balloon":
        world.say(
            f"{hero.id} was beginning to walk home when {friend.id} saw the {shared.label} bobbing in the air."
        )
    elif shared.id == "joke":
        world.say(
            f"{hero.id} began to tell the silly {shared.label}, and {friend.id} snorted before trying not to laugh."
        )
    else:
        world.say(
            f"{hero.id} began to say the odd phrase out loud, and {friend.id} repeated it with a grin."
        )


def trouble(world: World, hero: Entity, friend: Entity, prize: Entity, shared: SharedThing) -> None:
    if shared.id == "balloon":
        world.say(
            f"Then {friend.id} looked sad, because {friend.pronoun('possessive')} own balloon had popped."
        )
        world.say(
            f"{hero.id} noticed {friend.id}'s face and felt a little tug in {hero.pronoun('possessive')} chest."
        )
    elif shared.id == "joke":
        world.say(
            f"The joke was so odd that {hero.id} worried it might sound mean, even though it was not meant that way."
        )
    else:
        world.say(
            f"The phrase sounded funny, but also confusing, and both children paused to make sure nobody felt left out."
        )


def resolution(world: World, hero: Entity, friend: Entity, prize: Entity, shared: SharedThing) -> None:
    _share(world, hero, friend, shared, prize)
    if shared.id == "balloon":
        world.say(
            f"{hero.id} offered to share the string, and {friend.id} held the other side."
        )
        world.say(
            f"They {shared.tail}, while the {prize.label} stayed safe in {hero.pronoun('possessive')} pocket."
        )
    elif shared.id == "joke":
        world.say(
            f"{hero.id} explained the joke kindly, and {friend.id} laughed for real this time."
        )
        world.say(
            f"That made the silly words feel warm instead of awkward, and the afternoon got lighter."
        )
    else:
        world.say(
            f"{hero.id} turned the phrase into a game, so {friend.id} could say it too."
        )
        world.say(
            f"They {shared.tail}, and the room filled with easy laughter."
        )


def tell(setting: Setting, prize: Prize, shared: SharedThing, hero_name: str, hero_gender: str, friend_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_kind, label=f"the {friend_kind}"))
    prize_ent = world.add(Entity(id="Prize", label=prize.label, phrase=prize.phrase, type=prize.label, region=prize.region))
    shared_ent = world.add(Entity(id=shared.id, label=shared.label, phrase=shared.phrase, type=shared.kind))

    introduce(world, hero, friend, prize_ent, shared_ent)
    world.para()
    begin_turn(world, hero, friend, prize_ent, shared_ent)
    trouble(world, hero, friend, prize_ent, shared_ent)
    world.para()
    resolution(world, hero, friend, prize_ent, shared_ent)

    world.facts = {
        "hero": hero,
        "friend": friend,
        "prize": prize_ent,
        "shared": shared_ent,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, prize, shared = f["hero"], f["friend"], f["prize"], f["shared"]
    return [
        f'Write a short slice-of-life story that includes "{shared.label}" and a kind share.',
        f"Tell a gentle story about {hero.id} and {friend.id} where a {shared.label} leads to a happy moment.",
        f"Write a simple story that uses the words hydrogen, bull's, and begin-gerund naturally.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, shared = f["hero"], f["friend"], f["prize"], f["shared"]
    return [
        QAItem(
            question=f"What did {hero.id} have in the story?",
            answer=f"{hero.id} had {hero.pronoun('possessive')} {prize.label} and also found {shared.phrase}.",
        ),
        QAItem(
            question=f"Why did {friend.id} look sad at first?",
            answer=f"{friend.id} looked sad because {friend.pronoun('possessive')} own balloon had popped.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The children shared the {shared.label}, and the mood changed from worried to cheerful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hydrogen?",
            answer="Hydrogen is a very light gas. It can be used to fill balloons so they float up.",
        ),
        QAItem(
            question="What does it mean to begin doing something?",
            answer="To begin doing something means to start it. It is the first step of an action.",
        ),
        QAItem(
            question="Why can sharing make people happier?",
            answer="Sharing can make people happier because it helps everyone feel included and cared for.",
        ),
        QAItem(
            question="Why are jokes sometimes funny?",
            answer="Jokes can be funny because they surprise you with words or ideas in a playful way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for sid, s in SHARED.items():
        lines.append(asp.fact("shared", sid))
        lines.append(asp.fact("shares", sid, "kindness" if sid != "balloon" else "turns"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Setting, Prize, Shared) :- setting(Setting), prize(Prize), shared(Shared), affords(Setting, share), okay(Prize, Shared).
okay(Prize, balloon) :- region(Prize, head).
okay(Prize, joke).
okay(Prize, phrase).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((sid, pid, shid) for sid in SETTINGS for pid, p in PRIZES.items() for shid in SHARED if reason_ok(_safe_lookup(SETTINGS, sid), p, SHARED[shid]))
    cl = asp_valid()
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python:", py)
    print("clingo:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about sharing, humor, and a hydrogen balloon.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--shared", choices=SHARED)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for pid, p in PRIZES.items():
            for shid, sh in SHARED.items():
                if reason_ok(_safe_lookup(SETTINGS, sid), p, sh):
                    out.append((sid, pid, shid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "prize", None) is None or c[1] == getattr(args, "prize", None))
              and (getattr(args, "shared", None) is None or c[2] == getattr(args, "shared", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, prize, shared = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIENDS)
    return StoryParams(setting=setting, prize=prize, shared=shared, name=name, gender=gender, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PRIZES, params.prize), SHARED[params.shared], params.name, params.gender, params.friend)
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
        samples = [generate(StoryParams(setting=s, prize=p, shared=sh, name="Mina", gender="girl", friend="neighbor"))
                   for s, p, sh in valid_combos()]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
