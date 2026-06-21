#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/settle_frame_twist_bad_ending_mystery.py
========================================================================

A small mystery storyworld: a child, a broken frame, a few clues, a twist, and
a bad ending. The story is driven by world state rather than a frozen paragraph.

Seed words:
- settle
- frame

Features:
- Twist
- Bad Ending

Style:
- Mystery
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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


@dataclass
class StoryParams:
    setting: str
    frame_kind: str
    clue_kind: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    culprit_name: str
    culprit_gender: str
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


@dataclass
class Setting:
    id: str
    place: str
    dark_spot: str
    morning_sound: str
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


@dataclass
class FrameItem:
    id: str
    label: str
    phrase: str
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
class ClueItem:
    id: str
    label: str
    phrase: str
    points_to: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["broken"] < THRESHOLD:
            continue
        sig = ("suspicion", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in list(world.entities.values()):
            if ent.role in {"detective", "helper"}:
                ent.memes["worry"] += 1
        out.append("__suspicion__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("settle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["resolve"] += 1
        out.append("__settle__")
    return out


CAUSAL_RULES = [
    Rule("suspicion", "social", _r_suspicion),
    Rule("settle", "social", _r_settle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_ok(frame: FrameItem, clue: ClueItem) -> bool:
    return frame.fragile and clue.points_to in {"window", "floor", "hall"}


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for s in SETTINGS:
        for f in FRAMES:
            for c in CLUES:
                if hazard_ok(FRAMES[f], CLUES[c]):
                    out.append((s, f, c))
    return out


def _pronoun_name(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with a twist and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--frame", choices=FRAMES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--culprit")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.frame and args.clue and not hazard_ok(FRAMES[args.frame], CLUES[args.clue]):
        raise StoryError("That clue would not lead to a believable frame mystery.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.frame is None or c[1] == args.frame)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, frame, clue = rng.choice(sorted(combos))
    dname, dg = args.detective or rng.choice(GIRL_NAMES + BOY_NAMES), rng.choice(["girl", "boy"])
    hname, hg = args.helper or rng.choice(GIRL_NAMES + BOY_NAMES), rng.choice(["girl", "boy"])
    cname, cg = args.culprit or rng.choice(GIRL_NAMES + BOY_NAMES), rng.choice(["girl", "boy"])
    if len({dname, hname, cname}) < 3:
        raise StoryError("Pick distinct names for the detective, helper, and culprit.")
    return StoryParams(setting=setting, frame_kind=frame, clue_kind=clue,
                       detective_name=dname, detective_gender=dg,
                       helper_name=hname, helper_gender=hg,
                       culprit_name=cname, culprit_gender=cg, seed=None)


def tell(params: StoryParams) -> World:
    world = World()
    s = SETTINGS[params.setting]
    frame = FRAMES[params.frame_kind]
    clue = CLUES[params.clue_kind]

    det = world.add(Entity(id=params.detective_name, kind="character", type=params.detective_gender, role="detective"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    culprit = world.add(Entity(id=params.culprit_name, kind="character", type=params.culprit_gender, role="culprit"))
    frame_ent = world.add(Entity(id="frame", type="frame", label=frame.label, tags=set(frame.tags)))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label, tags=set(clue.tags)))

    det.memes["curiosity"] += 1
    helper.memes["care"] += 1
    culprit.memes["nervy"] += 1

    world.say(f"At {s.place}, {det.id} found a quiet mystery. The air felt still, and even the dust seemed to settle.")
    world.say(f"Near {s.dark_spot}, {det.id} noticed {frame.phrase}. Something had gone wrong there.")

    world.para()
    world.say(f'{helper.id} leaned close and pointed at {clue.phrase}. "That clue matters," {helper.pronoun()} said.')
    world.say(f'{culprit.id} looked away too fast, and {det.id} felt a small chill in {det.pronoun("possessive")} chest.')

    world.para()
    clue_ent.meters["found"] += 1
    frame_ent.meters["broken"] += 1
    propagate(world, narrate=False)
    world.say(f"{det.id} checked the place again. The {frame.label} was cracked, and the clue seemed to frame the whole suspicion.")

    world.para()
    world.say(f"Then came the twist: the clue pointed not at the helper, but at {culprit.id}.")
    world.say(f"At first that felt like an answer, but it only made the room feel colder.")

    world.para()
    world.say(f'{det.id} tried to settle the matter and speak clearly, but nobody wanted to listen for long.')
    world.say(f"{culprit.id} slipped outside while everyone argued, and the broken frame stayed broken.")

    world.para()
    world.say(f"In the end, the mystery did not heal. {det.id} went home with a heavy heart, and the house kept its secret.")
    world.say(f"The last thing anyone saw was the crooked frame on the wall, waiting in the dim light.")

    world.facts.update(
        setting=s,
        frame=frame,
        clue=clue,
        detective=det,
        helper=helper,
        culprit=culprit,
        frame_ent=frame_ent,
        clue_ent=clue_ent,
        outcome="bad",
        twist=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the words "{f["setting"].id}" and "frame", and ends with a twist.',
        f'Tell a short mystery where {f["detective"].id} investigates a broken frame, but the clue leads to an unexpected person.',
        "Write a mystery with a bad ending in which the dust settles, but the answer comes too late.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    culprit = f["culprit"]
    return [
        QAItem(
            question="What was the mystery about?",
            answer=f"It was about a broken frame and a clue that made everyone suspicious. The detective looked carefully, but the answer turned into a twist instead of a clean solution.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The clue seemed to point toward {culprit.id}, not {helper.id}. That changed the story, but it did not fix the trouble in the room.",
        ),
        QAItem(
            question=f"What happened to {det.id} at the end?",
            answer=f"{det.id} went home feeling disappointed because the mystery stayed unresolved. The broken frame was still there, and the story ended in a bad way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when dust settles?",
            answer="It means the tiny bits in the air stop floating around and come to rest. The room becomes still and quiet again.",
        ),
        QAItem(
            question="What is a frame?",
            answer="A frame is the border around a picture or photo. It helps hold the picture and show it off on a wall or shelf.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        bits.append(f"  {e.id:10} ({e.type}) {' '.join(parts)}")
    return "\n".join(bits)


SETTINGS = {
    "hall": Setting(id="hall", place="the hall", dark_spot="the far corner", morning_sound="footsteps"),
    "house": Setting(id="house", place="the old house", dark_spot="the stair landing", morning_sound="pipes"),
    "school": Setting(id="school", place="the school hallway", dark_spot="the coat rack", morning_sound="bells"),
}

FRAMES = {
    "picture": FrameItem(id="picture", label="picture frame", phrase="a cracked picture frame"),
    "gold": FrameItem(id="gold", label="gold frame", phrase="a bent gold frame"),
    "wood": FrameItem(id="wood", label="wood frame", phrase="a chipped wood frame"),
}

CLUES = {
    "smudge": ClueItem(id="smudge", label="smudge", phrase="a dark smudge on the sill", points_to="window"),
    "mud": ClueItem(id="mud", label="mud", phrase="a muddy print near the door", points_to="floor"),
    "thread": ClueItem(id="thread", label="thread", phrase="a loose thread caught on a nail", points_to="hall"),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Zoe", "Maya"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Ben", "Owen", "Max"]


CURATED = [
    StoryParams(setting="hall", frame_kind="picture", clue_kind="smudge", detective_name="Mina", detective_gender="girl", helper_name="Noah", helper_gender="boy", culprit_name="Eli", culprit_gender="boy"),
    StoryParams(setting="house", frame_kind="gold", clue_kind="mud", detective_name="Theo", detective_gender="boy", helper_name="Ivy", helper_gender="girl", culprit_name="Max", culprit_gender="boy"),
    StoryParams(setting="school", frame_kind="wood", clue_kind="thread", detective_name="Lily", detective_gender="girl", helper_name="Ben", helper_gender="boy", culprit_name="Owen", culprit_gender="boy"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FRAMES:
        lines.append(asp.fact("frame", fid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points_to", cid, clue.points_to))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,F,C) :- setting(S), frame(F), clue(C), points_to(C,window).
valid(S,F,C) :- setting(S), frame(F), clue(C), points_to(C,floor).
valid(S,F,C) :- setting(S), frame(F), clue(C), points_to(C,hall).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid_combos():")
        print(" python-only:", sorted(py - cl))
        print(" clingo-only:", sorted(cl - py))
    else:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAILED: generate() smoke test crashed: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.frame_kind not in FRAMES or params.clue_kind not in CLUES:
        raise StoryError("Unknown setting, frame, or clue.")
    if not hazard_ok(FRAMES[params.frame_kind], CLUES[params.clue_kind]):
        raise StoryError("That clue and frame do not make a believable mystery.")
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
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
