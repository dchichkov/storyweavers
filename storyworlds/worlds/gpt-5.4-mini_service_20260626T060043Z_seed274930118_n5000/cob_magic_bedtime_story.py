#!/usr/bin/env python3
"""
cob_magic_bedtime_story.py
===========================

A tiny bedtime-story world about a child, a little cob, and gentle magic.

Premise seed:
---
At bedtime, a child finds a tiny cob that glows like a moonbeam. The child
wants to keep it under the blanket, but the glow feels too bright. A parent
helps by using a little magic to turn the cob into a soft nightlight, and the
child drifts to sleep feeling safe.

World model:
---
- The cob can glow, warm, and calm.
- Too much glow can keep the child awake.
- Magic can soften the glow into a sleepy lantern.
- When the child feels safe, sleepiness rises and worry fades.

The script follows the Storyweavers storyworld contract.
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bedroom"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"glow", "lull"})


@dataclass
class Cob:
    label: str
    phrase: str
    type: str = "cob"
    glow: str = "softly glowing"
    sleepiness: str = "sleepy and calm"
    risk: str = "too bright"
    zone: set[str] = field(default_factory=lambda: {"hands", "torso"})


@dataclass
class Magic:
    id: str
    label: str
    phrase: str
    softens: set[str] = field(default_factory=lambda: {"glow"})
    turns_into: str = "a soft nightlight"
    spell: str = "whisper a gentle spell"
    tail: str = "the light became a cozy little moon in the room"


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    cob = world.get("cob")
    if cob.meters.get("glow", 0.0) < THRESHOLD:
        return out
    if world.facts.get("magic_softened"):
        return out
    if child.memes.get("worry", 0.0) >= THRESHOLD:
        sig = ("soften",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        cob.meters["glow"] = 0.4
        cob.meters["calm"] = 1.0
        child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
        child.memes["safe"] = child.memes.get("safe", 0.0) + 1.0
        out.append("The glow softened into a sleepy little lantern.")
    return out


def _r_sleep(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    cob = world.get("cob")
    if child.memes.get("safe", 0.0) < THRESHOLD:
        return out
    if child.memes.get("sleepy", 0.0) >= THRESHOLD:
        return out
    sig = ("sleep",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["sleepy"] = 1.0
    cob.meters["rest"] = cob.meters.get("rest", 0.0) + 1.0
    out.append("Soon the child felt sleepy, and the room grew quiet.")
    return out


RULES = [_r_soften, _r_sleep]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_brightness(world: World) -> bool:
    sim = world.copy()
    cob = sim.get("cob")
    child = sim.get("child")
    cob.meters["glow"] = 1.0
    child.memes["worry"] = 1.0
    propagate(sim, narrate=False)
    return cob.meters.get("glow", 0.0) >= 1.0


def tell(name: str = "Mina", child_type: str = "girl") -> World:
    setting = Setting()
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=name,
        traits=["little", "sleepy-eyed", "gentle"],
        meters={"tired": 0.0},
        memes={"love": 1.0, "worry": 0.0, "safe": 0.0, "sleepy": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type="mother",
        label="mom",
        traits=["soft-voiced"],
        meters={"patience": 1.0},
        memes={"care": 1.0},
    ))
    cob = world.add(Entity(
        id="cob",
        kind="thing",
        type="cob",
        label="little cob",
        phrase="a little golden cob",
        owner=child.id,
        caretaker=parent.id,
        meters={"glow": 1.0, "warmth": 1.0},
        memes={"wonder": 1.0},
    ))
    magic = world.add(Entity(
        id="magic",
        kind="thing",
        type="magic",
        label="magic",
        phrase="gentle bedtime magic",
        meters={"softness": 1.0},
        memes={"kind": 1.0},
    ))

    world.say(f"{child.label} was a little child who loved bedtime stories and quiet lights.")
    world.say(f"One night, {child.label} found {cob.phrase} under the pillow, shining with a tiny warm glow.")
    world.say(f"{child.label} loved {cob.label} at once, because it felt like holding a moonbeam in small hands.")
    world.para()
    world.say(f"When the bedroom lights went out, the glow looked brighter, and {child.label} began to worry.")
    world.say(f"{child.label} wanted to keep the cob close, but the bright shine made the room feel too awake.")
    world.say(f"\"If the cob stays this bright, you may not fall asleep,\" {parent.label} said softly.")
    child.memes["worry"] += 1.0
    child.meters["tired"] += 0.5

    world.para()
    world.say(f"{child.label} looked down, then hugged {cob.label} anyway. The cob glimmered against the blanket.")
    if predict_brightness(world):
        world.say(f"Then {parent.label} lifted a hand and decided to use {magic.label}.")
        world.say(f"{parent.label} knew a gentle way: {magic.spell} and ask the glow to hush.")
        child.memes["worry"] += 0.0
        world.facts["magic_softened"] = True
        world.facts["magic"] = magic
        world.facts["parent"] = parent
        world.facts["child"] = child
        world.facts["cob"] = cob
        world.facts["setting"] = setting
        world.say(f"{parent.label} whispered a spell over the cob, and its bright shine became soft and sleepy.")
        propagate(world, narrate=True)
        world.para()
        world.say(f"{child.label} smiled, tucked {cob.label} by the bedside, and listened to the quiet little glow.")
        world.say(f"At last {child.label} drifted off, and {cob.label} kept watch like {magic.turns_into}.")
    else:
        world.say(f"But the room was already soft enough, so {parent.label} only kissed {child.label}'s forehead.")
        child.memes["safe"] += 1.0
        propagate(world, narrate=True)
        world.para()
        world.say(f"{child.label} yawned, cuddled the cob, and fell asleep with a tiny smile.")

    world.facts.update(child=child, parent=parent, cob=cob, magic=magic, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a gentle bedtime story for a small child named {child.label} about a glowing cob and a little bit of magic.',
        f'Tell a cozy story where {child.label} finds a cob at bedtime, worries it is too bright, and a parent uses magic to help.',
        'Write a bedtime story with moonlike light, a small cob, and a calm ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    cob = f["cob"]
    return [
        QAItem(
            question=f"What did {child.label} find at bedtime?",
            answer=f"{child.label} found a little golden cob that glowed like a tiny moonbeam.",
        ),
        QAItem(
            question=f"Why did {child.label} worry about the cob?",
            answer=f"{child.label} worried because the cob's glow felt too bright and made the room feel too awake.",
        ),
        QAItem(
            question=f"How did {parent.label} help {child.label}?",
            answer=f"{parent.label} used gentle magic to soften the cob's shine into a sleepy little lantern.",
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=f"{child.label} fell asleep while the cob kept a cozy watch beside the bed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is magic in a bedtime story?",
            answer="Magic is a pretend, wondrous force that can make impossible things happen in a kind and gentle way.",
        ),
        QAItem(
            question="Why are nightlights comforting?",
            answer="Nightlights make a room feel less dark, so children can feel safe enough to fall asleep.",
        ),
        QAItem(
            question="What does a cob usually mean?",
            answer="A cob is the center part of an ear of corn, though stories can give it a special glowing life.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:7} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str = "Mina"
    gender: str = "girl"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story world about a cob and a little magic.")
    ap.add_argument("--name", choices=["Mina", "Lina", "Nora", "Tessa"])
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    name = args.name or rng.choice(["Mina", "Lina", "Nora", "Tessa"])
    gender = args.gender or "girl"
    return StoryParams(name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender)
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


ASP_RULES = r"""
% If the cob glows and magic is present, it can be softened.
soften(cob) :- glowing(cob), magic_present.

% A child settles when the cob is softened.
settle(child) :- soften(cob).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("glowing", "cob"),
            asp.fact("magic_present"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show soften/1. #show settle/1."))
    atoms = {(sym.name, tuple(a.name if a.type == a.type.SymbolType.Function else getattr(a, 'number', getattr(a, 'string', str(a))) for a in sym.arguments)) for sym in model}
    expected = {("soften", ("cob",)), ("settle", ("child",))}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


CURATED = [StoryParams(name=n, gender="girl") for n in ["Mina", "Lina", "Nora", "Tessa"]]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show soften/1. #show settle/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show soften/1. #show settle/1."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
