#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/immature_pensive_music_room_lesson_learned_repetition.py
=========================================================================================

A standalone story world sketch for a tiny superhero story set in a music room.

Premise:
- A young, immature little hero wants to impress others by making a big sound.
- A pensive helper notices the problem first and worries about the music room.
- The hero repeats the mistake, creating a small mess and a hard lesson.
- A grown-up fix and a repeated practice turn the ending into a better rhythm.

The story must include the seed words "immature" and "pensive", and it should
feel like a small superhero story with clear cause, turn, lesson learned, and a
final image of better behavior.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/immature_pensive_music_room_lesson_learned_repetition.py
    python storyworlds/worlds/gpt-5.4-mini/immature_pensive_music_room_lesson_learned_repetition.py --all
    python storyworlds/worlds/gpt-5.4-mini/immature_pensive_music_room_lesson_learned_repetition.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/immature_pensive_music_room_lesson_learned_repetition.py --verify
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
TEMPERATURE_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    noisy: bool = False
    fragile: bool = False
    musical: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class RoomSetting:
    id: str
    place: str
    detail: str
    has_piano: bool = True
    has_tin_drums: bool = True
    has_stands: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class SoundSource:
    id: str
    label: str
    phrase: str
    noise: str
    repeats: int
    too_loud: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Mess:
    id: str
    label: str
    phrase: str
    cleanup: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_hot(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["noise"] < THRESHOLD:
            continue
        sig = ("hot", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["overheated"] += 1
        out.append("")
    return out


def _r_alert(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    if not room:
        return out
    noisy = any(e.meters["noise"] >= THRESHOLD for e in world.characters())
    if noisy and room.meters["mess"] >= THRESHOLD:
        sig = ("alert",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in world.characters():
                e.memes["concern"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("hot", _r_hot), Rule("alert", _r_alert)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    return produced


def reasonableness_gate(source: SoundSource, mess: Mess, fix: Fix) -> bool:
    return source.too_loud and mess.fragile and fix.sense >= SENSE_MIN


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def outcome_of(params: StoryParams) -> str:
    if params.source not in SOUNDS or params.mess not in MESS_TYPES or params.fix not in FIXES:
        return "invalid"
    return "learned" if FIXES[params.fix].power >= 1 else "oops"


def predict_mess(world: World, source: SoundSource) -> dict:
    sim = world.copy()
    room = sim.get("room")
    room.meters["mess"] += 1
    room.meters["noise"] += 1
    return {"messy": room.meters["mess"] >= THRESHOLD, "noise": room.meters["noise"]}


def tell(setting: RoomSetting, source: SoundSource, mess: Mess, fix: Fix,
         hero_name: str, hero_gender: str, helper_name: str, helper_gender: str,
         mentor_name: str, mentor_gender: str, repetition: int = 2) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=["young", "bold", "immature"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["pensive", "careful"]))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_gender, role="mentor", label="the mentor"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    instrument = world.add(Entity(id=source.id, type="instrument", label=source.label, noisy=True, musical=True))
    target = world.add(Entity(id="target", type="thing", label=mess.label, fragile=mess.fragile))
    world.facts["setting"] = setting
    world.facts["source"] = source
    world.facts["mess"] = mess
    world.facts["fix"] = fix
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["mentor"] = mentor
    world.facts["repetition"] = repetition

    hero.memes["pride"] += 1
    helper.memes["pensive"] += 1
    world.say(f"In the music room, {hero.id} was an immature little hero who wanted to make the biggest sound of all.")
    world.say(f"{helper.id} sat by the piano, pensive and quiet, while {setting.detail}")

    world.para()
    world.say(f'{hero.id} pointed at {source.phrase} and grinned. "If I play it again and again, everyone will notice me," {hero.pronoun()} said.')
    world.say(f'But {helper.id} warned, "{source.label} can be {source.noise}; it might upset the music room."')
    helper.memes["concern"] += 1

    world.para()
    for _ in range(repetition):
        hero.meters["noise"] += 1
        room.meters["noise"] += 1
        target.meters["jostled"] += 1
    room.meters["mess"] += 1
    propagate(world)
    world.say(f"{hero.id} did it again, and again, and then once more. The repeated beat rattled the room, and {mess.phrase} tipped over with a clatter.")
    world.say(f"{source.noise.capitalize()} filled the room, and the little hero finally looked less proud and more worried.")

    world.para()
    fix_name = fix.text.replace("{source}", source.label).replace("{mess}", mess.label)
    if fix.power < 1:
        world.say(f"The mentor tried to help, but the plan was not strong enough, and the room stayed in a jumble.")
        world.say(f"{hero.id} had to stop the noise the hard way and listen to the quiet after it.")
        outcome = "oops"
    else:
        room.meters["mess"] = 0
        room.meters["noise"] = 0
        hero.memes["lesson"] += 1
        helper.memes["relief"] += 1
        mentor.memes["pride"] += 1
        world.say(f"Then {mentor.label_word} came in, smiled, and {fix_name}.")
        world.say(f"The sound settled down, the mess was cleaned, and {hero.id} learned that one clever note is better than a wild repeat.")
        world.para()
        world.say(f"This time {hero.id} played a softer rhythm once, then stopped to listen. {helper.id} nodded, and the music room felt calm again.")
        outcome = "learned"

    world.facts["outcome"] = outcome
    world.facts["instrument"] = instrument
    world.facts["target"] = target
    return world


@dataclass
class StoryParams:
    setting: str
    source: str
    mess: str
    fix: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    mentor_name: str
    mentor_gender: str
    repetition: int = 2
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


SETTINGS = {
    "music_room": RoomSetting(id="music_room", place="the music room", detail="the piano waited by the wall and the drums sat in a neat row."),
}

SOUNDS = {
    "drum": SoundSource(id="drum", label="the tiny drum", phrase="a tiny drum", noise="boom", repeats=3, too_loud=True, tags={"music", "noise"}),
    "triangle": SoundSource(id="triangle", label="the bright triangle", phrase="a bright triangle", noise="clang", repeats=4, too_loud=True, tags={"music", "noise"}),
    "horn": SoundSource(id="horn", label="the shiny horn", phrase="a shiny horn", noise="toot", repeats=3, too_loud=True, tags={"music", "noise"}),
}

MESS_TYPES = {
    "sheet_stack": Mess(id="sheet_stack", label="sheet stack", phrase="the sheet stack", cleanup="straightened the pages", fragile=True, tags={"paper", "music"}),
    "cup_of_stickers": Mess(id="cup_of_stickers", label="cup of stickers", phrase="the cup of stickers", cleanup="picked up the stickers", fragile=True, tags={"paper", "music"}),
    "music_stand": Mess(id="music_stand", label="music stand", phrase="the music stand", cleanup="set the stand upright", fragile=True, tags={"music"}),
}

FIXES = {
    "pause_and_breathe": Fix(id="pause_and_breathe", sense=3, power=1, text="paused the room, took one deep breath, and asked {source} to wait", fail="paused, but the noise was already too wild", lesson="learned to slow down"),
    "count_to_three": Fix(id="count_to_three", sense=3, power=1, text="counted to three and asked everyone to play one note at a time", fail="counted, but the mess was still too big", lesson="learned to take turns"),
    "ask_for_earmuffs": Fix(id="ask_for_earmuffs", sense=2, power=1, text="brought gentle earmuffs and helped {source} sound softer", fail="found earmuffs, but the noise stayed too sharp", lesson="learned to be thoughtful"),
}

GIRL_NAMES = ["Mina", "Ivy", "Luna", "Nora", "Zoe", "Maya"]
BOY_NAMES = ["Arlo", "Ben", "Theo", "Eli", "Noah", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, source in SOUNDS.items():
        for mid, mess in MESS_TYPES.items():
            for fid, fix in FIXES.items():
                if reasonableness_gate(source, mess, fix):
                    combos.append((sid, mid, fid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: immature hero, pensive helper, music room lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOUNDS)
    ap.add_argument("--mess", choices=MESS_TYPES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--mentor-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--mentor-gender", choices=["woman", "man"])
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
              if (args.source is None or c[0] == args.source)
              and (args.mess is None or c[1] == args.mess)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    source, mess, fix = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    mentor_gender = args.mentor_gender or rng.choice(["woman", "man"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero_name]
    helper_name = args.helper_name or rng.choice(helper_pool)
    mentor_name = args.mentor_name or rng.choice(["Ms. Ray", "Coach Blue", "Aunt Joy", "Mr. Reed"])
    repetition = 3 if fix == "count_to_three" else 2
    return StoryParams(setting=args.setting or "music_room", source=source, mess=mess, fix=fix,
                       hero_name=hero_name, hero_gender=hero_gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       mentor_name=mentor_name, mentor_gender=mentor_gender,
                       repetition=repetition)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    source = f["source"]
    return [
        f'Write a superhero story set in a music room that includes the words "immature" and "pensive".',
        f"Tell a small lesson-learned story where {hero.id} is immature, {f['helper'].id} is pensive, and {source.label} gets repeated one too many times.",
        f"Write a child-friendly superhero story about a noisy music room, a repeated mistake, and a calmer ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mentor = f["mentor"]
    source = f["source"]
    mess = f["mess"]
    qa = [
        QAItem(question="Who is the story about?", answer=f"It is about {hero.id}, a young superhero who started out immature, and {helper.id}, who watched pensive and careful."),
        QAItem(question="What did the hero keep repeating?", answer=f"{hero.id} kept repeating the noisy action with {source.phrase}, trying to make a bigger and bigger sound. That repetition made the music room harder to calm down."),
        QAItem(question="What problem happened in the music room?", answer=f"The repeated noise tipped over {mess.phrase} and made a mess. The room became too loud and too cluttered for easy playing."),
    ]
    if f["outcome"] == "learned":
        qa.append(QAItem(question="How did the story end?", answer=f"{mentor.label_word.capitalize()} helped fix the problem, and {hero.id} learned to slow down and listen. By the end, the hero played one softer rhythm and the room felt peaceful again."))
        qa.append(QAItem(question="What lesson was learned?", answer=f"{hero.id} learned that repeating a loud move does not make it better. A careful pause and a smaller sound can be much smarter in a music room."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a music room?", answer="A music room is a room where people practice instruments and listen carefully to sound."),
        QAItem(question="Why can repeated noise be a problem?", answer="Repeated noise can make it hard to think, hard to listen, and hard to keep things tidy. It may also startle other people in the room."),
        QAItem(question="What does pensive mean?", answer="Pensive means quiet, thoughtful, and a little worried while you are thinking."),
        QAItem(question="What does immature mean?", answer="Immature means not yet acting as carefully or sensibly as you should. A person who is immature may rush ahead without thinking."),
    ]


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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="music_room", source="drum", mess="sheet_stack", fix="pause_and_breathe",
                hero_name="Nova", hero_gender="girl", helper_name="Milo", helper_gender="boy",
                mentor_name="Coach Blue", mentor_gender="man", repetition=2),
    StoryParams(setting="music_room", source="triangle", mess="music_stand", fix="count_to_three",
                hero_name="Ace", hero_gender="boy", helper_name="Iris", helper_gender="girl",
                mentor_name="Ms. Ray", mentor_gender="woman", repetition=3),
    StoryParams(setting="music_room", source="horn", mess="cup_of_stickers", fix="ask_for_earmuffs",
                hero_name="Pip", hero_gender="boy", helper_name="Lina", helper_gender="girl",
                mentor_name="Aunt Joy", mentor_gender="woman", repetition=2),
]


ASP_RULES = r"""
valid(S,M,F) :- source(S), mess(M), fix(F), too_loud(S), fragile(M), sense(F, X), x_min(Y), X >= Y.
outcome(learned) :- valid(_,_,_), fix_power(F, P), P >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("source", sid))
        if s.too_loud:
            lines.append(asp.fact("too_loud", sid))
    for mid, m in MESS_TYPES.items():
        lines.append(asp.fact("mess", mid))
        if m.fragile:
            lines.append(asp.fact("fragile", mid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("fix_power", fid, f.power))
    lines.append(asp.fact("x_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    print("OK: verify passed and story generation smoke test succeeded.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.source not in SOUNDS or params.mess not in MESS_TYPES or params.fix not in FIXES:
        raise StoryError("(Invalid parameters for this story world.)")
    world = tell(SETTINGS[params.setting], SOUNDS[params.source], MESS_TYPES[params.mess], FIXES[params.fix],
                 params.hero_name, params.hero_gender, params.helper_name, params.helper_gender,
                 params.mentor_name, params.mentor_gender, params.repetition)
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
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combinations")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
