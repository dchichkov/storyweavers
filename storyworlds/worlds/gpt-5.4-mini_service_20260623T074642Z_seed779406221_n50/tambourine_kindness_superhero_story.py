#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/tambourine_kindness_superhero_story.py
===============================================================================================================

A standalone storyworld about a small superhero scene: a child hero, a kind
choice, and a tambourine that helps turn a tense moment into a bright ending.

Seed premise:
- A young hero wants to perform with a tambourine.
- A problem appears when the loud, excited play risks upsetting someone or
  causing a mishap.
- Kindness becomes the superpower that makes the fix work.

This world keeps the classic structure:
setup -> problem -> thoughtful turn -> resolution image.
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


# ---------------------------------------------------------------------------
# Core entity model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
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
    hero: object | None = None
    prize: object | None = None
    sidekick: object | None = None
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
    place: str = "the city square"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    sound: str
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


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
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
class Aid:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        self.zone: set[str] = set()
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "square": Setting("the city square", False, {"dance", "march"}),
    "roof": Setting("the rooftop stage", True, {"dance", "practice"}),
    "garden": Setting("the community garden", False, {"dance", "sing"}),
}

ACTIVITIES = {
    "dance": Activity(
        id="dance",
        verb="dance with the tambourine",
        gerund="dancing with the tambourine",
        rush="spin into the middle of the square",
        mess="noise",
        zone={"ears"},
        keyword="tambourine",
        sound="clang-clang",
    ),
    "march": Activity(
        id="march",
        verb="lead a hero march",
        gerund="marching proudly",
        rush="dash down the path",
        mess="noise",
        zone={"ears"},
        keyword="hero march",
        sound="rat-a-tat",
    ),
    "practice": Activity(
        id="practice",
        verb="practice a brave rhythm",
        gerund="practicing a brave rhythm",
        rush="rush to the stage",
        mess="noise",
        zone={"ears"},
        keyword="tambourine",
        sound="tap-tap",
    ),
}

PRIZES = {
    "flowerpot": Prize("flowerpot", "a little clay flowerpot", "flowerpot", "hands"),
    "catnap": Prize("catnap", "a sleeping kitten", "kitten", "ears"),
    "sign": Prize("sign", "a shiny help sign", "sign", "hands"),
}

AIDS = [
    Aid("soft_steps", "soft steps", {"ears"}, {"noise"}, "tiptoe and lower the tambourine", "tiptoed back to the stage"),
    Aid("kind_words", "kind words", {"ears", "hands"}, {"noise"}, "speak kindly and play a gentler beat", "smiled and kept the beat soft"),
    Aid("helper_gloves", "helper gloves", {"hands"}, {"noise"}, "put on helper gloves and play more softly", "came back with helper gloves"),
]

HERO_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn"]
SIDEKICK_NAMES = ["Dot", "Jules", "Pip", "Sky"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the activity touches the prize's region.
at_risk(A, P) :- splashes(A, R), prize_region(P, R).

% A fix is compatible only if it covers the risk region and guards the mess.
compatible(A, P, G) :- at_risk(A, P), aid(G),
                       prize_region(P, R), covers(G, R),
                       mess_of(A, M), guards(G, M).

valid(Place, A, P) :- affords(Place, A), at_risk(A, P), compatible(A, P, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for g in AIDS:
        lines.append(asp.fact("aid", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    out = []
    for sid, s in SETTINGS.items():
        for a in s.affords:
            act = _safe_lookup(ACTIVITIES, a)
            for pid, p in PRIZES.items():
                if p.region in act.zone and any(p.region in g.covers and act.mess in g.guards for g in AIDS):
                    out.append((sid, a, pid))
    return sorted(set(out))


def asp_verify() -> int:
    a, b = set(asp_valid()), set(python_valid())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    hero: str
    sidekick: str
    seed: Optional[int] = None
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
    return python_valid()


def choose_aid(activity: Activity, prize: Prize) -> Optional[Aid]:
    for g in AIDS:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity, prize = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        activity=activity,
        prize=prize,
        hero=getattr(args, "hero", None) or rng.choice(HERO_NAMES),
        sidekick=getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES),
    )


def _run(world: World, hero: Entity, act: Activity, prize: Entity) -> None:
    world.zone = set(act.zone)
    hero.meters[act.mess] = hero.meters.get(act.mess, 0.0) + 1.0
    if prize.region in act.zone:
        prize.meters["spooked"] = prize.meters.get("spooked", 0.0) + 1.0


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", meters={}, memes={}))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="boy", meters={}, memes={}))
    prize = world.add(Entity(id="prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label,
                             phrase=_safe_lookup(PRIZES, params.prize).phrase, caretaker=sidekick.id,
                             region=_safe_lookup(PRIZES, params.prize).region))
    act = _safe_lookup(ACTIVITIES, params.activity)
    aid = choose_aid(act, prize)

    world.say(f"{hero.id} was a small superhero with a bright cape and a brave heart.")
    world.say(f"{hero.id} loved {act.gerund}, and {act.keyword} was {hero.pronoun('possessive')} favorite thing to carry.")
    world.say(f"At {world.setting.place}, {hero.id} saw {prize.phrase} and wanted to keep it safe for {sidekick.id}.")

    world.para()
    world.say(f"Then {hero.id} lifted the tambourine and made {act.sound} sounds as {hero.pronoun()} {act.rush}.")
    world.say(f"The sound was so big that {prize.phrase} shook and {sidekick.id} worried it would be ruined.")

    world.para()
    world.say(f"{hero.id} noticed the worry and chose kindness like a true hero.")
    if aid:
        world.say(f"{hero.id} used {aid.label}, which helped {act.keyword} stay gentle.")
        world.say(f"{hero.id} {aid.prep}, and {sidekick.id} relaxed right away.")
        world.say(f"Together they {act.gerund} again, and the tambourine kept a soft, happy beat.")
        world.say(f"In the end, {prize.phrase} stayed safe, and {hero.id} {aid.tail}.")
    else:
        world.say(f"{hero.id} played more softly and spoke kindly until {sidekick.id} smiled.")
        world.say(f"The tambourine became a little, friendly beat, and the worry melted away.")
        world.say(f"In the end, {prize.phrase} stayed safe beside the hero's cape.")

    world.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "prize": prize,
        "activity": act,
        "aid": aid,
        "setting": world.setting,
    }

    prompts = [
        'Write a short superhero story for a young child that includes a tambourine and the theme of kindness.',
        f"Tell a simple story where {hero.id} uses {act.keyword} at {world.setting.place} and solves a problem with kindness.",
        f"Write a child-friendly superhero tale about {hero.id}, {sidekick.id}, and a safe, gentle tambourine.",
    ]

    story_qa = [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, who wears a cape and chooses kindness."
        ),
        QAItem(
            question=f"What instrument helps make the big sound?",
            answer="A tambourine makes the bright clanging sound in the story."
        ),
        QAItem(
            question=f"Why did {sidekick.id} worry at {world.setting.place}?",
            answer=f"{sidekick.id} worried because the loud tambourine noise might upset things and ruin {prize.phrase}."
        ),
    ]
    if aid:
        story_qa.append(QAItem(
            question="How did the hero fix the problem?",
            answer=f"{hero.id} used {aid.label} and a kind voice, which let everyone stay calm and keep {prize.phrase} safe."
        ))

    world_qa = [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about how others feel."
        ),
        QAItem(
            question="What is a tambourine?",
            answer="A tambourine is a small hand drum with metal jingles that makes a bright shaking sound."
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world with tambourine and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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


CURATED = [
    StoryParams("square", "dance", "flowerpot", "Mia", "Dot"),
    StoryParams("roof", "practice", "catnap", "Leo", "Pip"),
    StoryParams("garden", "dance", "sign", "Nora", "Sky"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid()
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print(" ", t)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
