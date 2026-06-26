#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/instrument_chapped_gap_friend_s_backyard_misunderstanding.py
===============================================================================================================================

A small comedy storyworld about a child, an instrument, a chapped mouth, and a
gap in a friend's backyard that makes everyone misunderstand what is going on.

Seed tale imagined from the prompt:
---
A child came to a friend's backyard with a tiny instrument and wanted to play.
Their lips were chapped from too much windy play, so every note came out squeaky.
A friend heard the funny sounds from a gap in the fence, misunderstood the fuss,
then shared lip balm and water. The child tried again and again, and the repeated
notes bounced through the gap like a silly echo until both friends were laughing.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    balm: object | None = None
    friend: object | None = None
    gap: object | None = None
    hero: object | None = None
    instrument: object | None = None
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
    place: str = "a friend's backyard"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    repetition: str
    requires_moist_lips: bool = False
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
    instrument: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    inst = world.get("instrument")
    gap = world.get("gap")
    if hero.memes["try_playing"] < THRESHOLD:
        return out
    if inst.id not in world.fired:
        world.fired.add(("play", inst.id))
        hero.meters["sound"] += 1
        out.append(f'{hero.id} blew the {inst.label}, and it made a squeaky "{inst.sound}!"')
    if gap.meters["echo"] < THRESHOLD:
        return out
    if ("echo", inst.id) in world.fired:
        return out
    world.fired.add(("echo", inst.id))
    hero.memes["amusement"] += 1
    out.append(f'The sound bounced through the gap and came back again: "{inst.repetition}!"')
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    balm = world.get("balm")
    if hero.meters["chapped"] < THRESHOLD:
        return out
    if friend.memes["noticed"] < THRESHOLD:
        return out
    if ("share", balm.id) in world.fired:
        return out
    world.fired.add(("share", balm.id))
    hero.meters["chapped"] = max(0.0, hero.meters["chapped"] - 1)
    hero.meters["moisture"] += 1
    friend.memes["kind"] += 1
    hero.memes["relief"] += 1
    out.append(f'{friend.id} shared lip balm and a sip of water.')
    return out


CAUSAL_RULES = [_r_share, _r_repeat]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world) if hasattr(rule, "apply") else rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="a friend's backyard", affords={"play", "share", "repeat"})

INSTRUMENTS = {
    "recorder": Instrument(
        id="recorder",
        label="recorder",
        phrase="a tiny plastic recorder",
        sound="peep",
        repetition="peep-peep",
        requires_moist_lips=False,
    ),
    "harmonica": Instrument(
        id="harmonica",
        label="harmonica",
        phrase="a shiny little harmonica",
        sound="squeak",
        repetition="squeak-squeak",
        requires_moist_lips=True,
    ),
    "trumpet": Instrument(
        id="trumpet",
        label="trumpet",
        phrase="a bright toy trumpet",
        sound="toot",
        repetition="toot-toot",
        requires_moist_lips=True,
    ),
}

NAMES = ["Mia", "Noah", "Lena", "Owen", "Ivy", "Eli", "Zoe", "Theo"]
GENDERS = {"girl": ["Mia", "Lena", "Ivy", "Zoe"], "boy": ["Noah", "Owen", "Eli", "Theo"]}

ASP_RULES = r"""
% A story is valid when the backyard has the needed features:
% an instrument to play, a gap that can echo, and a friend who can share.
valid_story(I) :- instrument(I), backyard(place), has_gap, can_share.
play_creates_sound(I) :- valid_story(I), instrument_requires_moist_lips(I).
share_resolves(I) :- valid_story(I), can_share.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("backyard", "place"), asp.fact("has_gap"), asp.fact("can_share")]
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        if inst.requires_moist_lips:
            lines.append(asp.fact("instrument_requires_moist_lips", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str]]:
    return [(iid,) for iid in INSTRUMENTS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: an instrument, a chapped mouth, and a gap.")
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    inst = getattr(args, "instrument", None) or rng.choice(list(INSTRUMENTS))
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "hero_name", None) or rng.choice(_safe_lookup(GENDERS, hero_gender))
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(inst, hero_name, hero_gender, friend_name, friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend_name))
    inst_cfg = _safe_lookup(INSTRUMENTS, params.instrument)
    instrument = world.add(Entity(id="instrument", type="instrument", label=inst_cfg.label, phrase=inst_cfg.phrase))
    gap = world.add(Entity(id="gap", type="thing", label="gap"))
    balm = world.add(Entity(id="balm", type="thing", label="lip balm"))

    world.facts.update(hero=hero, friend=friend, instrument=instrument, gap=gap, balm=balm, cfg=inst_cfg)

    hero.memes["want_playing"] += 1
    hero.meters["chapped"] += 1
    gap.meters["echo"] += 1

    world.say(
        f"{hero.label} came into {SETTING.place} with {instrument.phrase}. "
        f"{hero.pronoun().capitalize()} wanted to play it right away."
    )
    world.say(
        f"But {hero.label}'s lips were chapped, so every puff came out funny."
    )
    world.para()
    world.say(
        f"{friend.label} heard the strange noise from a gap in the fence and looked over."
    )
    friend.memes["noticed"] += 1
    world.say(
        f"For a silly moment, {friend.label} thought {hero.label} was teasing the backyard birds."
    )
    world.say(
        f"Then {friend.label} saw the chapped lips and the {instrument.label} and started laughing instead."
    )

    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{friend.label} held out lip balm and water, and {hero.label} took the hint."
    )
    hero.memes["try_playing"] += 1
    propagate(world, narrate=True)
    world.say(
        f"After that, {hero.label} tried again and again until the {instrument.label} sounded much better, "
        f"and the little gap kept tossing the notes back like a joke."
    )
    hero.memes["joy"] += 1
    friend.memes["amusement"] += 1

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short comedy story for a child about an instrument, chapped lips, and a gap in a backyard fence.',
        f"Tell a funny story where {f['hero'].label} wants to play a {f['cfg'].label} in a friend's backyard, but the chapped mouth causes a misunderstanding.",
        "Write a gentle repetition-filled story where a friend shares something helpful and the same little sound keeps bouncing back.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, inst = f["hero"], f["friend"], f["cfg"]
    return [
        QAItem(
            question=f"What did {hero.label} bring to the backyard?",
            answer=f"{hero.label} brought {inst.phrase} and wanted to play it in the friend's backyard.",
        ),
        QAItem(
            question=f"Why was the first sound so funny?",
            answer=f"It was funny because {hero.label}'s lips were chapped, so the {inst.label} came out squeaky.",
        ),
        QAItem(
            question=f"What misunderstanding did {friend.label} have at first?",
            answer=f"{friend.label} first thought {hero.label} was making a big fuss on purpose, but really the sound was just bouncing through the gap in the fence.",
        ),
        QAItem(
            question=f"How did the friends fix the problem?",
            answer=f"{friend.label} shared lip balm and water, which helped {hero.label}'s chapped lips and made playing the {inst.label} easier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lip balm for?",
            answer="Lip balm is used to soothe dry lips and keep them from feeling chapped.",
        ),
        QAItem(
            question="What does a gap mean?",
            answer="A gap is an open space or hole between things, like a space in a fence.",
        ),
        QAItem(
            question="Why do sounds echo?",
            answer="Sounds echo when they bounce off a surface and come back to your ears again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:10}) meters={dict(meters)} memes={dict(memes)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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
    StoryParams(instrument="harmonica", hero_name="Mia", hero_gender="girl", friend_name="Owen", friend_gender="boy"),
    StoryParams(instrument="trumpet", hero_name="Noah", hero_gender="boy", friend_name="Ivy", friend_gender="girl"),
    StoryParams(instrument="recorder", hero_name="Zoe", hero_gender="girl", friend_name="Theo", friend_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible instrument combos:\n")
        for (iid,) in vals:
            print(f"  {iid}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name} with {p.instrument}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
