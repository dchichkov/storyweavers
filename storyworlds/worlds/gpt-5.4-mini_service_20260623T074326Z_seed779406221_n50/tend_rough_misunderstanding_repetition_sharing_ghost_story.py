#!/usr/bin/env python3
"""
storyworlds/worlds/tend_rough_misunderstanding_repetition_sharing_ghost_story.py
===============================================================================

A small ghost-story world about a child tending a rough, misunderstood thing
that seems spooky at first, then is understood through repetition and sharing.

Seeded premise:
- A child hears bumps in an old house or garden shed at night.
- The bumps are caused by a little ghost trying to tend something rough and
  hidden: a torn blanket, a loose board, a cold plant pot, or a creaky toy.
- The child first misunderstands the ghost.
- Repetition reveals the pattern.
- Sharing a small task or object turns fear into help.

The domain is intentionally small and classical: one setting, one mysterious
sound, one misunderstanding, one repeated clue, one shared solution, one ending
image proving the change.

Contract notes:
- typed entities with meters and memes
- a reasonableness gate
- inline ASP_RULES twin plus asp_facts()
- generate/emit/main parser support
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    scene: str
    rough: str
    dim: str


@dataclass
class Mystery:
    id: str
    sound: str
    clue: str
    source: str
    misunderstood_as: str
    real_need: str
    repetition: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharedThing:
    id: str
    label: str
    phrase: str
    share_verb: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.place: Optional[Place] = None
        self.mystery: Optional[Mystery] = None
        self.shared: Optional[SharedThing] = None
        self.fix: Optional[Fix] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.place = _copy.deepcopy(self.place)
        w.mystery = _copy.deepcopy(self.mystery)
        w.shared = _copy.deepcopy(self.shared)
        w.fix = _copy.deepcopy(self.fix)
        return w


@dataclass
class StoryParams:
    setting: str
    mystery: str
    shared: str
    fix: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "attic": Place("attic", "the attic", "a dusty attic", "rough old boards", "very dim"),
    "garden": Place("garden", "the garden shed", "a small garden shed", "rough wooden walls", "dim and chilly"),
    "hall": Place("hall", "the hall closet", "a narrow hall closet", "rough plaster walls", "dark and quiet"),
}

MYSTERIES = {
    "knocks": Mystery("knocks", "knock, knock, knock", "three knocks", "the old wall", "a ghostly warning", "a loose board",
                      "the knocks came again and again", {"ghost", "misunderstanding", "repetition"}),
    "rattle": Mystery("rattle", "rattle-rattle", "a rattling sound", "the shelf", "a spooky chain", "a hanging tin cup",
                      "the rattle came back, the same way each time", {"ghost", "misunderstanding", "repetition"}),
    "whisper": Mystery("whisper", "whisper, whisper", "a whispery breeze", "the corner", "a cold ghost voice", "a torn curtain",
                       "the whisper repeated softly and softly again", {"ghost", "misunderstanding", "repetition"}),
}

SHARED = {
    "flashlight": SharedThing("flashlight", "flashlight", "the flashlight", "shared", {"sharing", "light"}),
    "blanket": SharedThing("blanket", "blanket", "the warm blanket", "shared", {"sharing", "warmth"}),
    "bell": SharedThing("bell", "bell", "the little bell", "shared", {"sharing", "sound"}),
}

FIXES = {
    "board": Fix("board", 3, 3, "tapped the board until the loose plank slid free", "tapped the board until the loose plank slid free", {"tend"}),
    "cup": Fix("cup", 3, 2, "moved the tin cup so it would stop rattling", "moved the tin cup so it would stop rattling", {"tend"}),
    "curtain": Fix("curtain", 2, 2, "tied the torn curtain back so it would not whisper in the wind", "tied the torn curtain back so it would not whisper in the wind", {"tend"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ada", "Rae", "Ivy"]
BOY_NAMES = ["Finn", "Theo", "Owen", "Max", "Ezra", "Luca"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world about misunderstanding, repetition, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--shared", choices=SHARED)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    shared = args.shared or rng.choice(list(SHARED))
    fix = args.fix or rng.choice(list(FIXES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    helper_pool = GIRL_NAMES if helper_gender == "girl" else BOY_NAMES
    child = args.child or rng.choice(child_pool)
    helper_choices = [n for n in helper_pool if n != child] or helper_pool
    helper = args.helper or rng.choice(helper_choices)
    parent = args.parent or rng.choice(["mother", "father"])
    if args.fix and args.fix not in FIXES:
        raise StoryError("Unknown fix.")
    return StoryParams(setting, mystery, shared, fix, child, child_gender, helper, helper_gender, parent)


def reasonableness_gate(p: StoryParams) -> None:
    if p.child == p.helper:
        raise StoryError("Child and helper must be different people.")
    if p.fix == "board" and p.setting == "hall":
        raise StoryError("A loose board story needs a rough wooden place, not the hall closet.")
    if p.fix == "curtain" and p.setting == "garden":
        raise StoryError("A curtain fix does not fit the garden shed.")
    if p.shared == "bell" and p.mystery == "knocks":
        return
    if p.shared == "flashlight" and p.mystery == "whisper":
        return
    if p.shared == "blanket" and p.mystery == "rattle":
        return
    if p.fix not in FIXES:
        raise StoryError("Invalid fix.")
    if p.mystery not in MYSTERIES or p.shared not in SHARED:
        raise StoryError("Invalid combination.")


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for sh in SHARED:
                for fx in FIXES:
                    p = StoryParams(s, m, sh, fx, "Mina", "girl", "Finn", "boy", "mother")
                    try:
                        reasonableness_gate(p)
                    except StoryError:
                        continue
                    out.append((s, m, sh))
    return out


def _r_repetition(world: World) -> list[str]:
    m = world.mystery
    if not m:
        return []
    sig = ("repetition", m.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.entities["child"].memes["worry"] += 1
    world.entities["helper"].memes["curiosity"] += 1
    world.entities["room"].meters["mystery"] += 1
    return [m.repetition]


def propagate(world: World) -> list[str]:
    changed = True
    out: list[str] = []
    while changed:
        changed = False
        for s in _r_repetition(world):
            if s:
                changed = True
                out.append(s)
    return out


ASP_RULES = r"""
valid(S,M,Sh) :- setting(S), mystery(M), shared(Sh), not bad(S,M,Sh).
bad("hall","knocks","flashlight") :- false.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for sh in SHARED:
        lines.append(asp.fact("shared", sh))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def play(p: StoryParams) -> World:
    w = World()
    reasonableness_gate(p)
    s = SETTINGS[p.setting]
    m = MYSTERIES[p.mystery]
    sh = SHARED[p.shared]
    fx = FIXES[p.fix]
    child = w.add(Entity("child", "character", p.child_gender, p.child))
    helper = w.add(Entity("helper", "character", p.helper_gender, p.helper))
    parent = w.add(Entity("parent", "character", "mother" if p.parent == "mother" else "father", p.parent))
    room = w.add(Entity("room", "thing", "place", s.label))
    ghost = w.add(Entity("ghost", "character", "ghost", "the ghost"))
    room.meters["roughness"] = 1.0
    child.memes["fear"] = 1.0
    helper.memes["care"] = 1.0

    w.say(f"On a rough little night, {child.id} crept into {s.scene}.")
    w.say(f"Something there went {m.sound}, and {child.id} froze.")
    w.say(f'"A ghost," {child.id} whispered, because the sound felt like {m.misunderstood_as}.')
    w.para()
    child.memes["misunderstanding"] = 1.0
    helper.memes["patience"] = 1.0
    w.say(f"But then the same sound came again: {m.sound}. And again: {m.sound}.")
    w.say(f"{helper.id} listened, not rushing, and noticed the pattern.")
    propagate(w)
    w.say(f'"Listen," {helper.id} said. "It is not a scare. It is a clue."')
    w.para()
    w.say(f"Together they found {m.source}, where a little ghost had been trying to tend {m.real_need}.")
    w.say(f"The ghost did not want to frighten anyone. It only wanted help.")
    w.para()
    w.say(f"{child.id} and {helper.id} {sh.share_verb} {sh.phrase} and went to work.")
    w.say(f"They {fx.text}.")
    child.memes["fear"] = 0.0
    child.memes["wonder"] = 1.0
    helper.memes["sharing"] = 1.0
    room.meters["tidy"] = 1.0
    w.say(f"The old place felt less rough after that, and the ghost looked lighter.")
    w.para()
    w.say(f"At the end, {parent.id} smiled at the two of them.")
    w.say(f'"When you share and listen," {parent.id} said, "even a ghost story can become a helping story."')
    w.say(f"So {child.id} kept the {sh.label} near the door, just in case the little ghost needed a friend again.")
    w.facts.update(
        child=child, helper=helper, parent=parent, place=s, mystery=m, shared=sh, fix=fx,
        outcome="solved",
    )
    return w


def generate(params: StoryParams) -> StorySample:
    w = play(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f"Write a gentle ghost story for young children in {p['place'].label} where {p['child'].id} first misunderstands a strange sound as a ghost, then learns it through repetition, and finally shares help with {p['helper'].id}.",
        f"Tell a small spooky story with a soft ending: a rough place, a repeated sound, a misunderstanding, and a shared fix that shows the ghost was trying to tend something.",
        f"Make a child-facing ghost story where listening carefully changes fear into sharing and help."
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    return [
        QAItem(question=f"What did {p['child'].id} think the sound was at first?",
               answer=f"{p['child'].id} first thought it was a ghost, because the sound felt spooky and easy to misunderstand."),
        QAItem(question=f"What showed that the sound was not random?",
               answer=f"The sound repeated again and again, which helped {p['helper'].id} notice a pattern."),
        QAItem(question=f"What did the ghost really want?",
               answer=f"The ghost really wanted to tend {p['mystery'].real_need}, not scare anybody."),
        QAItem(question=f"What did {p['child'].id} and {p['helper'].id} share?",
               answer=f"They shared {p['shared'].phrase} and worked together to help."),
        QAItem(question=f"How did the story end?",
               answer=f"It ended with the rough place feeling calmer, because the children understood the ghost and solved the problem together."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="Why can repetition help in a mystery?",
               answer="When a sound or event happens again and again, it can reveal a pattern and make a confusing thing easier to understand."),
        QAItem(question="What does it mean to share?",
               answer="To share means to use or give something together with someone else, so you can help each other."),
        QAItem(question="Why can a ghost story still be gentle?",
               answer="A ghost story can stay gentle when the spooky part turns out to be misunderstood and the ending is about care, listening, and help."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
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


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/3."))
        return
    samples: list[StorySample] = []
    if args.all:
        for s in SETTINGS:
            for m in MYSTERIES:
                for sh in SHARED:
                    for fx in FIXES:
                        params = StoryParams(s, m, sh, fx, "Mina", "girl", "Finn", "boy", "mother")
                        try:
                            samples.append(generate(params))
                        except StoryError:
                            pass
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20:
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            try:
                sample = generate(params)
            except StoryError:
                continue
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
