#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tangle_sycamore_nap_room_quest_transformation_rhyme.py
==============================================================================================================

A tiny fairy-tale story world about a child in a nap room who goes on a quest,
meets a tangle beneath a sycamore, and earns a transformation with a rhyme.

The source tale imagined for this world:
---
In a quiet nap room, a small child named Mira could not sleep because her blanket
had tumbled into a tangle by the window. Outside the window stood a sycamore
tree, and its leaves tapped a soft rhythm like a song. An old teacher told Mira
that if she wished to rest, she had to go on a tiny quest: find the lost moon
button, untie the tangle, and speak a rhyme to wake the blanket's kindness.

Mira followed the clue under the sycamore, where she found the moon button
caught in a knot of ribbon. She untied it, said a little rhyme, and the blanket
changed from scratchy and twisted into soft and smooth. At last she curled up
again, and the nap room became quiet as a dream.

World model notes:
---
- The nap room is a gentle indoor setting with pillows, cots, and a window.
- A tangle is a physical knot of ribbon/blanket that blocks rest.
- The quest is to retrieve the moon button and untie the tangle.
- The transformation changes the blanket from twisted to soft.
- The rhyme is a child-sized spoken spell that helps the change settle.
"""

from __future__ import annotations

import argparse
import copy
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the nap room"
    indoor: bool = True
    affords: set[str] = field(default_factory=lambda: {"quest", "tangle", "transformation", "rhyme"})


@dataclass
class Quest:
    id: str
    title: str
    target: str
    clue: str
    path: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    from_state: str
    to_state: str
    method: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rhyme:
    id: str
    line1: str
    line2: str
    line3: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_unwind_tangle(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    tangle = world.entities.get("tangle")
    if not child or not tangle:
        return out
    if child.memes.get("questing", 0.0) < THRESHOLD:
        return out
    if tangle.meters.get("knotted", 0.0) < THRESHOLD:
        return out
    sig = ("unwind_tangle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tangle.meters["knotted"] = 0.0
    tangle.meters["open"] = 1.0
    out.append("The tangle loosened its grip.")
    return out


def _r_transform_blanket(world: World) -> list[str]:
    out: list[str] = []
    blanket = world.entities.get("blanket")
    rhyme = world.entities.get("rhyme")
    if not blanket or not rhyme:
        return out
    if blanket.meters.get("smooth", 0.0) >= THRESHOLD:
        return out
    if blanket.memes.get("heard_rhyme", 0.0) < THRESHOLD:
        return out
    sig = ("transform_blanket",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    blanket.meters["scratchy"] = 0.0
    blanket.meters["smooth"] = 1.0
    blanket.memes["kind"] = 1.0
    out.append("The blanket grew soft and smooth.")
    return out


def _r_sleep(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    blanket = world.entities.get("blanket")
    if not child or not blanket:
        return out
    if child.memes.get("rest", 0.0) >= THRESHOLD:
        return out
    if blanket.meters.get("smooth", 0.0) < THRESHOLD:
        return out
    sig = ("sleep",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["rest"] = 1.0
    out.append("At last, the child could rest.")
    return out


RULES = [_r_unwind_tangle, _r_transform_blanket, _r_sleep]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world(params: "StoryParams") -> World:
    world = World(Setting())
    child = world.add(Entity(
        id="child", kind="character", type=params.gender, label=params.name,
        traits=["little", params.trait, "dreamy"],
        meters={"tired": 0.0},
        memes={"curiosity": 1.0},
    ))
    teacher = world.add(Entity(
        id="teacher", kind="character", type="teacher", label="the teacher",
        traits=["gentle", "old"],
    ))
    sycamore = world.add(Entity(
        id="sycamore", type="tree", label="the sycamore",
        phrase="a tall sycamore by the window",
        tags={"sycamore"},
    ))
    tangle = world.add(Entity(
        id="tangle", type="knot", label="the tangle",
        phrase="a tight knot of ribbon and blanket",
        meters={"knotted": 1.0},
        memes={"stuck": 1.0},
        tags={"tangle"},
    ))
    moon_button = world.add(Entity(
        id="moon_button", type="button", label="the moon button",
        phrase="a little moon-shaped button",
        tags={"quest"},
    ))
    blanket = world.add(Entity(
        id="blanket", type="blanket", label="the blanket",
        phrase="a soft blanket with a silver hem",
        meters={"scratchy": 1.0, "smooth": 0.0},
        memes={"sleepy": 0.5},
    ))
    rhyme = world.add(Entity(
        id="rhyme", type="rhyme", label="a rhyme",
        phrase="a tiny rhyme with a bright beat",
        tags={"rhyme"},
    ))

    # Act I
    world.say(
        f"In the {world.setting.place}, {child.label} was too awake to sleep because "
        f"{blanket.label} had fallen into a tangle."
    )
    world.say(
        f"By the window stood {sycamore.phrase}, and its leaves tapped like a small song."
    )
    world.say(
        f"{teacher.label.capitalize()} told {child.label} that a quiet quest would help: "
        f"find {moon_button.label}, untie the tangle, and speak a rhyme."
    )

    # Act II
    world.para()
    child.memes["questing"] = 1.0
    world.say(
        f"{child.label} took a soft breath and began the quest under {sycamore.label}."
    )
    world.say(
        f"There, {moon_button.label} was caught in the knot, shining like a pebble of light."
    )
    world.say(
        f"{child.label} pulled the ribbon, and {tangle.label} started to loosen."
    )
    propagate(world, narrate=True)

    # Act III
    world.para()
    child.memes["rhyme_spoken"] = 1.0
    rhyme_text = [
        "Moon button bright, make the night light,",
        "Knot grow kind, and loosen the bind,",
        "Soft blanket, stay, and carry sleep my way.",
    ]
    rhyme.line1, rhyme.line2, rhyme.line3 = rhyme_text
    rhyme.memes = {"heard": 1.0} if hasattr(rhyme, "memes") else {}
    blanket.memes["heard_rhyme"] = 1.0
    world.say(
        f"Then {child.label} whispered a rhyme:"
    )
    world.say(f'"{rhyme.line1} {rhyme.line2} {rhyme.line3}"')
    propagate(world, narrate=True)
    world.say(
        f"After that, {blanket.label} was soft, {child.label} curled up beneath it, "
        f"and the nap room grew as quiet as a dream."
    )

    world.facts.update(
        child=child,
        teacher=teacher,
        sycamore=sycamore,
        tangle=tangle,
        moon_button=moon_button,
        blanket=blanket,
        rhyme=rhyme,
        setting=world.setting,
    )
    return world


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mira", "Luna", "Ivy", "Nora", "Pippa"]
NAMES_BOY = ["Milo", "Theo", "Finn", "Owen", "Ari"]
TRAITS = ["curious", "gentle", "brave", "soft-spoken", "dreamy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a fairy-tale story for a small child in a nap room about a quest, a tangle, a sycamore, and a rhyme.",
        f"Tell a gentle bedtime story where {f['child'].label} must go on a quest to fix a tangle beneath a sycamore.",
        "Create a child-facing tale in which a spoken rhyme causes a transformation and helps everyone rest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    teacher = f["teacher"]
    blanket = f["blanket"]
    tangle = f["tangle"]
    return [
        QAItem(
            question=f"Why could {child.label} not sleep at first?",
            answer=f"{child.label} could not sleep because {blanket.label} had fallen into a tangle and felt scratchy.",
        ),
        QAItem(
            question=f"What did {teacher.label} ask {child.label} to do?",
            answer=f"{teacher.label.capitalize()} asked {child.label} to go on a small quest, find the moon button, untie the tangle, and speak a rhyme.",
        ),
        QAItem(
            question=f"What changed after the rhyme was spoken?",
            answer=f"After the rhyme was spoken, {tangle.label} loosened and {blanket.label} became soft and smooth.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.label} curled under {blanket.label}, resting quietly in the nap room.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sycamore?",
            answer="A sycamore is a kind of tree with broad leaves and a sturdy trunk.",
        ),
        QAItem(
            question="What is a tangle?",
            answer="A tangle is a knot or messy twist that is hard to pull apart.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a short bit of language where the sounds at the ends of words match or echo each other.",
        ),
        QAItem(
            question="What is a quest in a fairy tale?",
            answer="A quest is a special journey or task where someone goes looking for something important.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a change from one state into another, like something rough becoming soft.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(name="Ivy", gender="girl", parent="mother", trait="dreamy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world set in a nap room.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
setting(nap_room).
affords(nap_room,quest).
affords(nap_room,tangle).
affords(nap_room,transformation).
affords(nap_room,rhyme).

valid_story(nap_room,quest,tangle).
valid_story(nap_room,quest,transformation).
valid_story(nap_room,quest,rhyme).

% The world is only interesting if a child has to quest through a tangle,
% speak a rhyme, and then get a transformation that allows rest.
needs_fix(quest,tangle).
causes(transformation,rhyme).
restful(nap_room) :- valid_story(nap_room,quest,tangle), causes(transformation,rhyme).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "nap_room"),
        asp.fact("indoor", "nap_room"),
        asp.fact("quest_feature", "quest"),
        asp.fact("quest_feature", "transformation"),
        asp.fact("quest_feature", "rhyme"),
        asp.fact("symbol", "sycamore"),
        asp.fact("symbol", "tangle"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("nap_room", "quest", "tangle"), ("nap_room", "quest", "transformation"), ("nap_room", "quest", "rhyme")}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python set ({len(clingo_set)} facts).")
        return 0
    print("MISMATCH:")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
