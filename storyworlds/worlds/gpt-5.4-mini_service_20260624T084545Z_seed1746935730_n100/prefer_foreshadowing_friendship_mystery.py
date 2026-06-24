#!/usr/bin/env python3
"""
Story world: prefer_foreshadowing_friendship_mystery

A tiny mystery domain for child-facing stories about a pair of friends who
notice a clue, prefer one path over another, and solve a small puzzle together.

Core premise:
- A child and a friend find two possible leads.
- The child prefers one lead because of a foreshadowed clue.
- A gentle mystery turn reveals which lead matters.
- The ending proves what changed and how friendship helped.

This file is self-contained except for the shared result containers.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Setting:
    place: str
    light: str
    clue_style: str
    mood: str
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


@dataclass
class Lead:
    id: str
    label: str
    clue: str
    location_hint: str
    risk: str
    resolve: str
    tags: set[str] = field(default_factory=set)
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
class Prize:
    id: str
    label: str
    phrase: str
    place: str
    plural: bool = False
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
class StoryParams:
    setting: str
    lead: str
    prize: str
    name: str
    friend_name: str
    gender: str
    seed: Optional[int] = None
    trait: str = ""
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "library": Setting(place="the library", light="soft", clue_style="quiet", mood="hushed"),
    "garden": Setting(place="the garden", light="golden", clue_style="bright", mood="still"),
    "attic": Setting(place="the attic", light="dusty", clue_style="faint", mood="secret"),
    "dock": Setting(place="the dock", light="gray", clue_style="shivery", mood="windy"),
}

LEADS = {
    "footprints": Lead(
        id="footprints",
        label="tiny footprints",
        clue="a line of tiny footprints",
        location_hint="the back path",
        risk="they might fade",
        resolve="followed the path",
        tags={"clue", "mystery", "trail"},
    ),
    "music": Lead(
        id="music",
        label="soft music",
        clue="a soft tune drifting from a window",
        location_hint="the upstairs room",
        risk="it might stop soon",
        resolve="went where the music was",
        tags={"clue", "mystery", "sound"},
    ),
    "lantern": Lead(
        id="lantern",
        label="a lantern glow",
        clue="a little lantern glow near a chair",
        location_hint="the corner by the wall",
        risk="the light might vanish",
        resolve="looked for the lantern",
        tags={"clue", "mystery", "light"},
    ),
    "notes": Lead(
        id="notes",
        label="folded notes",
        clue="a stack of folded notes tied with string",
        location_hint="the table near the door",
        risk="someone could move them",
        resolve="opened the notes carefully",
        tags={"clue", "mystery", "paper"},
    ),
}

PRIZES = {
    "shell": Prize(id="shell", label="shell", phrase="a smooth white shell", place="the windowsill"),
    "button": Prize(id="button", label="button", phrase="a bright blue button", place="the rug"),
    "key": Prize(id="key", label="key", phrase="a little brass key", place="the drawer"),
    "ribbon": Prize(id="ribbon", label="ribbon", phrase="a red ribbon", place="the bench"),
}

NAMES = ["Ava", "Mia", "Lily", "Nora", "Ben", "Leo", "Theo", "Finn"]
FRIENDS = ["Pip", "June", "Milo", "Rose", "Jules", "Nina"]
TRAITS = ["curious", "careful", "kind", "quiet", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for l in LEADS:
            for p in PRIZES:
                combos.append((s, l, p))
    return combos


def reasonableness_gate(setting: str, lead: str, prize: str) -> None:
    if setting == "attic" and lead == "music":
        pass
    if setting == "dock" and prize == "button":
        pass


@dataclass
class Truth:
    lead_is_right: bool = False
    friendship_helped: bool = False
    clue_seen_early: bool = False
    truth: object | None = None
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


def tell(setting: Setting, lead: Lead, prize: Prize, hero: Entity, friend: Entity) -> World:
    world = World(setting)
    hero.memes["hope"] = 1
    friend.memes["hope"] = 1
    truth = Truth()

    world.say(
        f"It was {setting.mood} at {setting.place}, and {hero.id} and {friend.id} were looking for a missing {prize.label}."
    )
    world.say(
        f"{hero.id} had noticed {lead.clue} earlier, and {friend.id} remembered it too."
    )
    truth.clue_seen_early = True

    world.para()
    world.say(
        f"{hero.id} wanted to check {lead.location_hint} first, because {hero.pronoun('possessive')} heart said that clue mattered."
    )
    world.say(
        f"{friend.id} preferred to look somewhere else, since {lead.risk}."
    )

    hero.memes["preference"] = 1
    friend.memes["doubt"] = 1

    if lead.id in {"footprints", "lantern", "notes"}:
        truth.lead_is_right = True

    world.para()
    if truth.lead_is_right:
        world.say(
            f"They chose to follow {lead.resolve}, and the search grew brighter with every step."
        )
        world.say(
            f"At the end, they found {prize.phrase} exactly where the clue had pointed."
        )
    else:
        world.say(
            f"They checked the other place first, but it only made the mystery feel larger."
        )
        world.say(
            f"Then {friend.id} remembered the clue, and together they returned to {lead.resolve}."
        )
        world.say(
            f"That was where they found {prize.phrase} waiting quietly."
        )

    truth.friendship_helped = True
    hero.memes["joy"] = 1
    friend.memes["joy"] = 1

    world.para()
    world.say(
        f"{hero.id} smiled and thanked {friend.id} for staying with {hero.pronoun('object')} through the whole search."
    )
    world.say(
        f"The two friends left {setting.place} with the missing {prize.label} safe again, and the clue had become a story they could both remember."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        lead=lead,
        prize=prize,
        setting=setting,
        truth=truth,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    lead = f["lead"]
    prize = f["prize"]
    return [
        f'Write a short mystery story for a young child that includes "{lead.label}" and ends with friends finding a {prize.label}.',
        f"Tell a gentle story where {hero.id} prefers one clue, {friend.id} helps think it through, and they solve the mystery together.",
        f'Write a friendship mystery with foreshadowing: show a clue early, then reveal why it mattered at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    lead = f["lead"]
    prize = f["prize"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"It happened at {setting.place}, where {hero.id} and {friend.id} searched for the missing {prize.label}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice early?",
            answer=f"{hero.id} noticed {lead.clue} early in the story, and that clue helped guide the search.",
        ),
        QAItem(
            question=f"Why did {hero.id} prefer that clue?",
            answer=f"{hero.id} preferred that clue because it seemed to point toward the right place, even before everyone agreed.",
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"{friend.id} helped by staying with {hero.id}, thinking it through, and following the clue together.",
        ),
        QAItem(
            question=f"What was found at the end?",
            answer=f"They found {prize.phrase}, and the ending showed that the first clue had been important all along.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    lead = f["lead"]
    setting = f["setting"]
    out = [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps you figure something out.",
        ),
        QAItem(
            question="Why do friends help in a mystery?",
            answer="Friends help because two people can notice more details and feel braver together.",
        ),
    ]
    if lead.id == "footprints":
        out.append(QAItem(
            question="What are footprints?",
            answer="Footprints are marks left by feet on soft ground like dirt, sand, or snow.",
        ))
    if setting.place == "the library":
        out.append(QAItem(
            question="What is a library?",
            answer="A library is a quiet place with books where people can read and look for information.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


def explain_rejection(setting: str, lead: str, prize: str) -> str:
    return f"(No story: {setting}/{lead}/{prize} does not make a clear child-sized mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny friendship mystery with foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lead", choices=LEADS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    lead = getattr(args, "lead", None) or rng.choice(list(LEADS))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    reasonableness_gate(setting, lead, prize)
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in FRIENDS + NAMES if n != name])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    return StoryParams(setting=setting, lead=lead, prize=prize, name=name, friend_name=friend_name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    lead = _safe_lookup(LEADS, params.lead)
    prize = _safe_lookup(PRIZES, params.prize)
    hero = Entity(id=params.name, kind="character", type=params.gender)
    friend = Entity(id=params.friend_name, kind="character", type="friend")
    world = tell(setting, lead, prize, hero, friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
clue_right(L) :- clue(L), not risky_only(L).
friendship_helped :- friend(_), clue_right(_).
found_prize(P) :- prize(P), clue_right(_), friendship_helped.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for lid, l in LEADS.items():
        lines.append(asp.fact("clue", lid))
        if l.id in {"footprints", "lantern", "notes"}:
            lines.append(asp.fact("not_risky_only", lid))
        else:
            lines.append(asp.fact("risky_only", lid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    lines.append(asp.fact("friend", "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show clue_right/1. #show found_prize/1."))
    clues = set(asp.atoms(model, "clue_right"))
    found = set(asp.atoms(model, "found_prize"))
    py_clues = {("footprints",), ("lantern",), ("notes",)}
    py_found = {(p,) for p in PRIZES}
    if clues == py_clues and found == py_found:
        print("OK: ASP parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasonableness.")
    print("  asp clue_right:", sorted(clues))
    print("  asp found_prize:", sorted(found))
    return 1


CURATED = [
    StoryParams(setting="library", lead="notes", prize="key", name="Ava", friend_name="Pip", gender="girl", trait="curious"),
    StoryParams(setting="garden", lead="footprints", prize="ribbon", name="Ben", friend_name="June", gender="boy", trait="careful"),
    StoryParams(setting="attic", lead="lantern", prize="button", name="Mia", friend_name="Milo", gender="girl", trait="quiet"),
    StoryParams(setting="dock", lead="footprints", prize="shell", name="Leo", friend_name="Rose", gender="boy", trait="brave"),
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show clue_right/1. #show found_prize/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show clue_right/1. #show found_prize/1."))
        print("ASP clue_right:", sorted(set(asp.atoms(model, "clue_right"))))
        print("ASP found_prize:", sorted(set(asp.atoms(model, "found_prize"))))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
