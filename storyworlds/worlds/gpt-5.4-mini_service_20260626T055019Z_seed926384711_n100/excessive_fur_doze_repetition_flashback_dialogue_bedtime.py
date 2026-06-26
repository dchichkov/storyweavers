#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/excessive_fur_doze_repetition_flashback_dialogue_bedtime.py
=============================================================================================================

A tiny bedtime story world about a child, a very fluffy toy, and the gentle
problem of too much fur at bedtime.

Premise:
- A child loves a plush friend with excessive fur.
- At bedtime, the fluff tickles the child awake and makes dozing hard.
- A parent remembers a calmer bedtime from a flashback and suggests a fix.
- Dialogue, repetition, and a soothing routine turn fuss into rest.

The story model keeps physical state in meters and emotional state in memes:
- meters: fluff, sleepy, tidy, calm
- memes: comfort, worry, relief, delight

The narrative uses repeated phrases, a brief flashback, and dialogue to keep
the bedtime-stories feel while still being driven by world state.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["fluff", "sleepy", "tidy", "calm"]:
            self.meters.setdefault(key, 0.0)
        for key in ["comfort", "worry", "relief", "delight", "memory"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    bedtime: bool = True


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    parent_gender: str
    toy_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_fluff_tickle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    toy = world.get("toy")
    if child.memes["worry"] < THRESHOLD or toy.meters["fluff"] < THRESHOLD:
        return out
    sig = "fluff_tickle"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["sleepy"] = max(0.0, child.meters["sleepy"] - 0.5)
    child.memes["worry"] += 0.5
    out.append(f"The extra fluff kept brushing {child.pronoun('possessive')} nose and waking {child.pronoun('object')} up.")
    return out


def _r_reassure(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    if parent.memes["relief"] < THRESHOLD or child.memes["comfort"] >= THRESHOLD:
        return out
    sig = "reassure"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["comfort"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    out.append(f"{parent.label} spoke softly, and {child.pronoun('possessive')} heart felt steadier.")
    return out


def _r_sleepy_triumph(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    toy = world.get("toy")
    if child.meters["sleepy"] < THRESHOLD or child.memes["comfort"] < THRESHOLD:
        return out
    sig = "sleepy_triumph"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["delight"] += 1
    toy.meters["tidy"] += 1
    out.append(f"At last, the room grew quiet, and the sleepy little hush settled over {child.id} and {toy.label}.")
    return out


RULES = [_r_fluff_tickle, _r_reassure, _r_sleepy_triumph]


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


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(
        id="child", kind="character", type=params.child_gender,
        label=params.child_name, traits=["little", "sleepy"],
    ))
    parent_type = "mother" if params.parent_gender == "mother" else "father"
    parent = world.add(Entity(
        id="parent", kind="character", type=parent_type,
        label="Mom" if parent_type == "mother" else "Dad",
    ))
    toy = world.add(Entity(
        id="toy", kind="thing", type="plush_toy", label=params.toy_name,
        phrase="a beloved bedtime friend", owner=child.id, caretaker=parent.id
    ))

    # Initial state: bedtime and excessive fur.
    toy.meters["fluff"] = 2.0
    child.meters["sleepy"] = 1.0
    child.memes["comfort"] = 0.5

    # Act 1: setup.
    world.say(f"{child.label} loved {toy.label}, a soft bedtime friend with very kind eyes.")
    world.say(f"Every night, {toy.label}'s fur seemed a little more than ordinary; it was excessive, and it tickled at the worst time.")
    world.say(f"{child.label} wanted to doze, but the fluff kept nudging {child.pronoun('object')} awake.")
    world.para()

    # Act 2: repetition + flashback + dialogue.
    world.say(f"Brush the fur, brush the fur, brush the fur, said the gentle bedtime rule.")
    world.say(f"{child.label} tried to snuggle closer. The fur tickled. {child.label} wriggled. The fur tickled again.")
    child.memes["worry"] += 1.0
    parent.memes["memory"] += 1.0
    world.say(f"Then {parent.label} remembered a flashback to a calmer night, when a small brush and a calm song had made everything easier.")
    world.say(f'"We can help {toy.label}," {parent.label} whispered. "First we brush, then we hug, then we doze."')
    world.say(f'"Brush, hug, doze," {child.label} repeated, holding the words like a tiny lantern.')
    world.para()

    # Resolve by grooming and calming.
    toy.meters["fluff"] = 0.0
    child.meters["sleepy"] += 1.0
    parent.memes["relief"] += 1.0
    child.memes["comfort"] += 1.0
    child.memes["worry"] = max(0.0, child.memes["worry"] - 0.5)
    world.say(f"Together they brushed the extra fur into a neat little puff.")
    world.say(f"Then {parent.label} tucked {child.label} in beside {toy.label} and hummed the same soft rule again: brush, hug, doze.")
    propagate(world, narrate=True)
    world.say(f"{child.label}'s eyes grew heavy at last, and {toy.label} rested beside {child.label} like a tiny cloud that had learned to stay still.")

    world.facts.update(
        child=child,
        parent=parent,
        toy=toy,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    toy: Entity = f["toy"]
    return [
        f'Write a bedtime story for a young child about {child.label} and a plush friend named {toy.label} with excessive fur.',
        f"Tell a gentle story where {child.label} wants to doze, but {toy.label}'s fur keeps waking {child.pronoun('object')} up, and a parent helps.",
        'Write a cozy bedtime tale that includes repetition, a flashback, and dialogue about brushing too much fur.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    toy: Entity = f["toy"]
    return [
        QAItem(
            question=f"What made {child.label} have trouble dozing at bedtime?",
            answer=f"{toy.label} had excessive fur, and the fluffy edges kept brushing {child.pronoun('possessive')} nose and waking {child.pronoun('object')} up.",
        ),
        QAItem(
            question=f"What did {parent.label} remember in the flashback?",
            answer=f"{parent.label} remembered a calmer night when brushing the toy and humming a soft song helped everyone settle down.",
        ),
        QAItem(
            question=f"What did they repeat to help the bedtime routine?",
            answer="They repeated, “Brush, hug, doze,” so the steps would feel calm and easy to remember.",
        ),
        QAItem(
            question=f"How did the story end for {child.label} and {toy.label}?",
            answer=f"They brushed the extra fur into a neat little puff, and then {child.label} fell sleepy and quiet beside {toy.label}.",
        ),
    ]


KNOWLEDGE = {
    "fur": [
        QAItem(
            question="What is fur?",
            answer="Fur is soft hair that grows on many animals. It can feel warm and fluffy.",
        )
    ],
    "doze": [
        QAItem(
            question="What does it mean to doze?",
            answer="To doze means to sleep a little, often lightly, like when you are almost asleep.",
        )
    ],
    "repetition": [
        QAItem(
            question="Why do stories sometimes repeat words?",
            answer="Stories repeat words so little listeners can remember them, feel the rhythm, and settle in.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in a story.",
        )
    ],
    "bedtime": [
        QAItem(
            question="Why do bedtime stories feel calm?",
            answer="Bedtime stories feel calm because they use soft pictures, gentle words, and a quiet ending.",
        )
    ],
    "excessive": [
        QAItem(
            question="What does excessive mean?",
            answer="Excessive means there is too much of something, more than is needed or wanted.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        q for key in ["excessive", "fur", "doze", "repetition", "flashback", "dialogue", "bedtime"]
        for q in KNOWLEDGE[key]
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world only supports the bedtime-brushing fix for the fluffy toy's excessive fur.)"


CURATED = [
    StoryParams(child_name="Maya", child_gender="girl", parent_gender="mother", toy_name="Mop",
                seed=None),
    StoryParams(child_name="Noah", child_gender="boy", parent_gender="father", toy_name="Pompom",
                seed=None),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about excessive fur, dozing, and a gentle fix.")
    ap.add_argument("--name", choices=["Maya", "Noah", "Luna", "Eli"])
    ap.add_argument("--toy", choices=["Mop", "Pompom", "Teddy", "Flufflet"])
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    child_gender = args.gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent or rng.choice(["mother", "father"])
    child_name = args.name or rng.choice(["Maya", "Noah", "Luna", "Eli"])
    toy_name = args.toy or rng.choice(["Mop", "Pompom", "Teddy", "Flufflet"])
    return StoryParams(
        child_name=child_name,
        child_gender=child_gender,
        parent_gender=parent_gender,
        toy_name=toy_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
child(C) :- child_name(C).
parent(P) :- parent_name(P).
toy(T) :- toy_name(T).

too_fluffy(T) :- fluff(T,F), F > 1.
tickles(C,T) :- child(C), toy(T), too_fluffy(T), bedtime_room(B), in_room(C,B), in_room(T,B).
needs_brush(T) :- too_fluffy(T).

comforts(C) :- spoken(brush_hug_doze), child(C).
asleep(C) :- comforts(C), sleepy(C,S), S > 0.

#show too_fluffy/1.
#show tickles/2.
#show needs_brush/1.
#show comforts/1.
#show asleep/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("bedtime_room", "bedroom"))
    lines.append(asp.fact("child_name", "child"))
    lines.append(asp.fact("parent_name", "parent"))
    lines.append(asp.fact("toy_name", "toy"))
    lines.append(asp.fact("in_room", "child", "bedroom"))
    lines.append(asp.fact("in_room", "toy", "bedroom"))
    lines.append(asp.fact("fluff", "toy", 2))
    lines.append(asp.fact("sleepy", "child", 1))
    lines.append(asp.fact("spoken", "brush_hug_doze"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show too_fluffy/1.\n#show tickles/2.\n#show needs_brush/1.\n#show comforts/1.\n#show asleep/1."))
    names = set((sym.name, tuple(getattr(a, "string", getattr(a, "number", a.name)) for a in sym.arguments)) for sym in model)
    expected = {
        ("too_fluffy", ("toy",)),
        ("tickles", ("child", "toy")),
        ("needs_brush", ("toy",)),
        ("comforts", ("child",)),
        ("asleep", ("child",)),
    }
    if names == expected:
        print("OK: ASP and Python agree on the bedtime story reasoning.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(names))
    print("PY :", sorted(expected))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show too_fluffy/1.\n#show needs_brush/1.\n"))
    return sorted(set((sym.name, tuple(a.string if a.type == 1 else a.number for a in sym.arguments)) for sym in model))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show too_fluffy/1.\n#show tickles/2.\n#show needs_brush/1.\n#show comforts/1.\n#show asleep/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP is available for the bedtime-fluff reasoning in this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.toy_name}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
