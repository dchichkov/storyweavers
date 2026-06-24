#!/usr/bin/env python3
"""
A bedtime story world about a child, a blue surprise, and a gentle lesson
learned through sharing with a confidante.

The core premise:
- A child loves a blue bedtime treasure.
- A close confidante worries when the child refuses to share it.
- A surprise reveals that sharing makes bedtime warmer, calmer, and happier.
- The lesson learned is that sharing can turn a small upset into a good night.

The simulation uses physical meters and emotional memes:
- meters track tangible things like blanket warmth, toy ownership, and softness
- memes track feelings like worry, pride, comfort, and trust

The story is built from a small world model with explicit state changes so the
prose follows causality instead of swapping nouns into a frozen paragraph.
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
# Registry content
# ---------------------------------------------------------------------------

NAMES = ["Mia", "Noah", "Luna", "Theo", "Ava", "Eli", "Nina", "Owen"]
CONFIDANTE_NAMES = ["mom", "dad", "grandma", "grandpa", "aunt", "uncle"]

BLUE_THINGS = [
    ("blanket", "a soft blue blanket", "blanket"),
    ("bear", "a blue teddy bear", "bear"),
    ("pillow", "a blue star pillow", "pillow"),
    ("book", "a little blue picture book", "book"),
]

BEDTIME_SETTINGS = [
    "the cozy bedroom",
    "the little nursery",
    "the quiet upstairs room",
    "the warm moonlit bedroom",
]

# ---------------------------------------------------------------------------
# Shared model objects
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["warmth", "softness", "blue", "shared", "sleepiness", "tidiness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "trust", "pride", "calm", "surprise", "conflict"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_plural(self) -> bool:
        return self.plural


@dataclass
class BlueThing:
    key: str
    label: str
    phrase: str


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    confidante_type: str
    blue_thing: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: str):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Domain rules
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    name: str
    apply: callable


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    confidante = world.get("confidante")
    thing = world.get("blue_thing")
    if child.memes["trust"] >= 1 and thing.meters["shared"] >= 1:
        sig = ("comfort",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["calm"] += 1
            confidante.memes["pride"] += 1
            out.append("The room felt softer, like the blanket had made a little circle of calm.")
    return out


RULES = [Rule("comfort", _r_comfort)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(params.setting)
    child_type = params.child_type
    confidante_type = params.confidante_type
    blue_key, blue_label, blue_phrase = next(v for v in BLUE_THINGS if v[0] == params.blue_thing)

    child = world.add(Entity(id="child", kind="character", type=child_type, label=params.child_name))
    confidante = world.add(Entity(id="confidante", kind="character", type=confidante_type, label=confidante_type))
    thing = world.add(Entity(
        id="blue_thing",
        kind="thing",
        type=blue_key,
        label=blue_label,
        phrase=blue_phrase,
        owner="child",
        caretakers=["confidante"],
    ))

    world.facts.update(
        child=child,
        confidante=confidante,
        thing=thing,
        blue_key=blue_key,
        blue_label=blue_label,
        blue_phrase=blue_phrase,
        setting=params.setting,
    )
    return world


def setup_lines(world: World) -> None:
    child = world.get("child")
    confidante = world.get("confidante")
    thing = world.get("blue_thing")
    world.say(
        f"{child.label} lived in {world.setting}, where the nightlight glowed like a tiny star."
    )
    world.say(
        f"{child.pronoun().capitalize()} loved {thing.phrase} and kept it close at bedtime."
    )
    world.say(
        f"The confidante, {confidante.label}, knew every sleepy sigh and every busy thought."
    )


def tension_lines(world: World) -> None:
    child = world.get("child")
    confidante = world.get("confidante")
    thing = world.get("blue_thing")
    child.memes["joy"] += 1
    child.meters["shared"] += 0
    confidante.memes["worry"] += 1
    world.para()
    world.say(
        f"One night, {child.label} wanted to keep {thing.phrase} all to {child.pronoun('object')}. "
        f"{confidante.pronoun().capitalize()} asked gently, \"Can we share it for bedtime?\""
    )
    world.say(
        f"{child.pronoun().capitalize()} clutched {thing.phrase} tighter and felt a little proud, but also a little stuck."
    )
    child.memes["conflict"] += 1


def surprise_and_sharing(world: World) -> None:
    child = world.get("child")
    confidante = world.get("confidante")
    thing = world.get("blue_thing")

    world.para()
    child.memes["surprise"] += 1
    confidante.memes["trust"] += 1
    world.say(
        f"Then came a surprise: {confidante.label} had folded a second sleepy blanket nearby, "
        f"the same blue color as {thing.phrase}."
    )
    world.say(
        f"\"You can keep your favorite one close, and I can tuck you in with the other,\" "
        f"{confidante.pronoun().capitalize()} said."
    )

    thing.meters["shared"] += 1
    thing.meters["tidiness"] += 1
    child.memes["trust"] += 1
    child.memes["conflict"] = 0
    child.memes["joy"] += 1
    world.say(
        f"{child.label} slowly shared {thing.phrase}, and the room felt less prickly right away."
    )

    propagate(world, narrate=True)

    world.say(
        f"{child.label} smiled, because sharing had not taken the blue joy away at all. "
        f"It had made bedtime feel bigger."
    )


def ending_lines(world: World) -> None:
    child = world.get("child")
    confidante = world.get("confidante")
    thing = world.get("blue_thing")
    world.para()
    world.say(
        f"At last, {child.label} drifted off with {thing.phrase} nearby, "
        f"and {confidante.label} watching with a quiet, proud heart."
    )
    world.say(
        f"The lesson learned was simple: when {child.label} shared, the blue surprise turned bedtime into a gentler place."
    )


def build_story(params: StoryParams) -> World:
    world = setup_world(params)
    setup_lines(world)
    tension_lines(world)
    surprise_and_sharing(world)
    ending_lines(world)
    return world


# ---------------------------------------------------------------------------
# Registries and parameter validation
# ---------------------------------------------------------------------------

BLUE_THING_REGISTRY = {
    key: BlueThing(key=key, label=label, phrase=phrase) for key, label, phrase in BLUE_THINGS
}

SETTING_REGISTRY = {s: s for s in BEDTIME_SETTINGS}

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in BEDTIME_SETTINGS:
        for blue_key in BLUE_THING_REGISTRY:
            for child_type in ["girl", "boy"]:
                combos.append((setting, blue_key, child_type))
    return combos


def explain_rejection(setting: str, blue_key: str) -> str:
    thing = BLUE_THING_REGISTRY[blue_key]
    return (
        f"(No story: in {setting}, {thing.phrase} would not create a clear shared bedtime surprise. "
        f"Try a different blue object.)"
    )


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a blue surprise and a lesson learned through sharing.")
    ap.add_argument("--setting", choices=BEDTIME_SETTINGS)
    ap.add_argument("--blue", choices=list(BLUE_THING_REGISTRY))
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--confidante-type", choices=CONFIDANTE_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(BEDTIME_SETTINGS)
    blue_key = args.blue or rng.choice(list(BLUE_THING_REGISTRY))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    confidante_type = args.confidante_type or rng.choice(CONFIDANTE_NAMES)
    if args.blue and args.setting:
        if (setting, blue_key, child_type) not in valid_combos():
            raise StoryError(explain_rejection(setting, blue_key))
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        child_name=name,
        child_type=child_type,
        confidante_type=confidante_type,
        blue_thing=blue_key,
        setting=setting,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    thing = f["thing"]
    confidante = f["confidante"]
    return [
        f'Write a bedtime story for a young child that includes a blue {thing.type} and a lesson learned about sharing.',
        f"Tell a gentle story where {child.label} wants to keep {thing.phrase} near at bedtime, but {confidante.label} helps with a surprise.",
        f"Write a soft, child-facing bedtime tale set in {world.setting} about sharing, a blue treasure, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    confidante = f["confidante"]
    thing = f["thing"]
    return [
        QAItem(
            question=f"Who was the bedtime story about?",
            answer=f"It was about {child.label}, who loved {thing.phrase}, and about the confidante {confidante.label} helping at bedtime.",
        ),
        QAItem(
            question=f"What was the blue thing in the story?",
            answer=f"The blue thing was {thing.phrase}, and it mattered because {child.label} did not want to share it at first.",
        ),
        QAItem(
            question=f"What lesson did {child.label} learn?",
            answer=f"{child.label} learned that sharing can make bedtime feel warmer, calmer, and kinder.",
        ),
        QAItem(
            question=f"What surprise helped the story turn into a happy ending?",
            answer=f"The surprise was that {confidante.label} had a second blue bedtime blanket ready, so {child.label} could share without losing the favorite one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do people share a blanket at bedtime?",
            answer="People share a blanket to stay warm, to feel close, and to make bedtime feel safe and comforting.",
        ),
        QAItem(
            question="What does a confidante mean?",
            answer="A confidante is a trusted person you can talk to, especially when you have a worry or a feeling you want to share.",
        ),
        QAItem(
            question="Why can a surprise feel happy instead of scary?",
            answer="A surprise can feel happy when it is kind and helpful, like when it gives comfort or solves a problem gently.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} label={e.label!r} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A bedtime story is valid when a child has a blue thing, a confidante, and
% the story supports a sharing-based turn with a surprise.
blue_item(B) :- blue(B).
bedtime_setting(S) :- setting(S).

valid_story(S, B, C) :- bedtime_setting(S), blue_item(B), confidante(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in BEDTIME_SETTINGS:
        lines.append(asp.fact("setting", s))
    for key in BLUE_THING_REGISTRY:
        lines.append(asp.fact("blue", key))
    for c in CONFIDANTE_NAMES:
        lines.append(asp.fact("confidante", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(s, b, c) for s in BEDTIME_SETTINGS for b in BLUE_THING_REGISTRY for c in CONFIDANTE_NAMES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for row in vals[:50]:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in BEDTIME_SETTINGS:
            for blue_key in BLUE_THING_REGISTRY:
                params = StoryParams(
                    child_name="Mia",
                    child_type="girl",
                    confidante_type="mom",
                    blue_thing=blue_key,
                    setting=setting,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
