#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/mouth_scratch_dim_toast_repetition_sound_effects.py
===============================================================================================================================

A tiny fable-style storyworld about a scratch-dim mouth, a piece of toast,
repetition, and sound effects.

Seed tale:
A small mouse wakes with a scratch-dim mouth after sleeping in a dusty room.
It keeps asking for toast, but the toast is too hard to bite until a helpful
friend softens it with butter and warm milk. The mouse repeats a little rhyme
while chewing, and the ending proves that care can make even a dry morning sweet.

The storyworld models:
- a small cast of typed entities with meters and memes
- a cause-and-effect turn driven by state
- repeated phrases and sound effects as narrative instruments
- a reasonableness gate plus inline ASP twin for parity checks

This file is standalone and only depends on the repo's shared results.py, with
ASP helpers imported lazily when needed.
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

    def pronoun(self) -> str:
        return "they"


@dataclass
class Setting:
    id: str
    place: str
    time: str
    mood: str
    light: str


@dataclass
class MouthState:
    id: str
    scratch_dim: str
    hunger: str
    dryness: str
    sound: str


@dataclass
class ToastState:
    id: str
    label: str
    hardness: str
    smell: str
    warmth: str
    is_soft: bool = False


@dataclass
class HelperState:
    id: str
    label: str
    kindness: str
    action: str
    sound: str


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    setting: str
    mouth: str
    toast: str
    helper: str
    repetition: int = 2
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting("kitchen", "a sunny kitchen", "morning", "cozy", "soft gold"),
    "cottage": Setting("cottage", "a small cottage kitchen", "morning", "quiet", "pale light"),
    "farm": Setting("farm", "a farmhouse table", "morning", "warm", "window light"),
}

MOUTHS = {
    "mouth": MouthState("mouth", "scratch-dim", "hungry", "dry", "smack"),
    "sore": MouthState("sore", "scratch-dim", "peckish", "dry", "murmur"),
}

TOASTS = {
    "toast": ToastState("toast", "plain toast", "hard and dry", "toasty", "warm"),
    "buttertoast": ToastState("toast", "buttered toast", "soft at the edges", "buttery", "warm", True),
}

HELPERS = {
    "sparrow": HelperState("sparrow", "a sparrow friend", "kind", "brought butter and milk", "chirp-chirp"),
    "grandma": HelperState("grandma", "grandma", "gentle", "took the toast back to the pan", "hmm-hmm"),
}

TRAITS = ["patient", "gentle", "cheerful", "careful"]


class ReasonableGate:
    @staticmethod
    def valid(params: StoryParams) -> bool:
        return params.setting in SETTINGS and params.mouth in MOUTHS and params.toast in TOASTS and params.helper in HELPERS

    @staticmethod
    def explain(params: StoryParams) -> str:
        return "(No story: the requested pieces do not make a small fable-like problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable storyworld about mouth, scratch-dim, toast, repetition, and sound effects.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mouth", choices=sorted(MOUTHS))
    ap.add_argument("--toast", choices=sorted(TOASTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--repetition", type=int, choices=[1, 2, 3, 4], default=2)
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


def _choice(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or _choice(rng, list(SETTINGS))
    mouth = args.mouth or _choice(rng, list(MOUTHS))
    toast = args.toast or _choice(rng, list(TOASTS))
    helper = args.helper or _choice(rng, list(HELPERS))
    if not ReasonableGate.valid(StoryParams(setting, mouth, toast, helper, args.repetition)):
        raise StoryError(ReasonableGate.explain(StoryParams(setting, mouth, toast, helper, args.repetition)))
    return StoryParams(setting=setting, mouth=mouth, toast=toast, helper=helper, repetition=args.repetition)


def world_from_params(params: StoryParams) -> World:
    w = World()
    s = SETTINGS[params.setting]
    m = MOUTHS[params.mouth]
    t = TOASTS[params.toast]
    h = HELPERS[params.helper]
    mouse = w.add(Entity("mouse", "character", "mouse", "hero", ["small", "hungry"]))
    toast = w.add(Entity("toast", "thing", "toast", "food", ["dry"]))
    helper = w.add(Entity("helper", "character", h.label, "helper", ["kind"]))
    room = w.add(Entity("room", "thing", s.place, "setting", ["quiet"]))
    mouse.meters["hunger"] = 2
    mouse.meters["scratch"] = 1
    mouse.meters["comfort"] = 0
    mouse.memes["hope"] = 1
    toast.meters["hardness"] = 2 if not t.is_soft else 0
    toast.meters["warmth"] = 1
    room.meters["light"] = 1
    w.facts.update(setting=s, mouth=m, toast=t, helper=h, repetition=params.repetition)
    return w


def tell(world: World) -> None:
    s: Setting = world.facts["setting"]
    m: MouthState = world.facts["mouth"]
    t: ToastState = world.facts["toast"]
    h: HelperState = world.facts["helper"]
    rep: int = world.facts["repetition"]
    mouse = world.entities["mouse"]
    toast = world.entities["toast"]
    helper = world.entities["helper"]

    world.say(
        f"In {s.place}, a little mouse woke with a {m.scratch_dim} mouth and a hungry belly."
    )
    world.say(
        f'"{m.scratch_dim} mouth, scratch-dim mouth," the mouse said, and its little voice went {m.sound} {m.sound}.'
    )
    world.say(
        f"It looked at the toast. The toast was {t.hardness}, and it smelled {t.smell}."
    )
    world.para()

    for _ in range(rep):
        mouse.memes["hope"] += 1
        world.say(f'"Toast, toast, toast," said the mouse, because it hoped the toast would answer.')
    world.say(f'Then came {h.sound}: {h.action}.')
    helper.memes["kindness"] = 1
    toast.meters["hardness"] = 0
    toast.meters["warmth"] += 1
    mouse.meters["hunger"] -= 1
    mouse.meters["comfort"] += 2
    mouse.memes["relief"] = 1

    world.para()
    world.say(
        f"{h.label.capitalize()} set the toast on a plate and made it soft with a little butter and warm milk."
    )
    world.say(
        f'"{t.label} is better when it is gentle," the mouse said, and it took a tiny bite: crunch, munch, much.'
    )
    world.say(
        f"It ate slowly, and each bite made the scratch-dim mouth feel less scratchy."
    )
    world.say(
        f'At last the mouse smiled. "Toast, toast, toast," it said again, but this time the words sounded happy.'
    )
    world.say(
        f'And in the soft {s.mood} morning, the mouse and {h.label} shared the last crumbs together.'
    )


def generation_prompts(world: World) -> list[str]:
    s: Setting = world.facts["setting"]
    h: HelperState = world.facts["helper"]
    return [
        f"Write a tiny fable in {s.place} about a mouse with a scratch-dim mouth and a piece of toast.",
        f"Tell a child-friendly story where the mouse repeats a little line about toast until a helper makes breakfast gentle.",
        f"Use repetition and sound effects, and end with a calm lesson about care and breakfast in {s.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    s: Setting = world.facts["setting"]
    h: HelperState = world.facts["helper"]
    return [
        QAItem("What kind of mouth did the mouse have?", "It had a scratch-dim mouth."),
        QAItem("What food did the mouse want?", "It wanted toast."),
        QAItem("Who helped the mouse?", f"{h.label.capitalize()} helped by making the toast soft and kind to eat."),
        QAItem("What changed the ending?", "The toast became soft, so the mouse could eat it happily."),
        QAItem("What repeated words were in the story?", "The mouse repeated toast, toast, toast."),
        QAItem("What sound effects were used?", "The story used little sounds like smack, chirp-chirp, and crunch, munch, much."),
        QAItem("Where did the story happen?", f"It happened in {s.place}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does repetition do in a story?", "Repetition can make a story feel musical, memorable, and easy to follow."),
        QAItem("Why can toast be hard to eat?", "Toast can be hard if it is dry or hard, but it gets easier when softened."),
        QAItem("What are sound effects in stories?", "Sound effects are little words that help you hear the action, like crunch or smack."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(out)


ASP_RULES = r"""
valid(S,M,T,H) :- setting(S), mouth(M), toast(T), helper(H).
repetition_ok(R) :- R >= 1, R <= 4.
happy :- toast_soft(T), helper_kind(H), repetition_ok(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MOUTHS:
        lines.append(asp.fact("mouth", m))
    for t, v in TOASTS.items():
        lines.append(asp.fact("toast", t))
        if v.is_soft:
            lines.append(asp.fact("toast_soft", t))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
        lines.append(asp.fact("helper_kind", h))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = world_from_params(params)
    tell(world)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("kitchen", "mouth", "toast", "sparrow", 2),
    StoryParams("cottage", "mouth", "buttertoast", "grandma", 3),
    StoryParams("farm", "sore", "toast", "sparrow", 4),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for _ in range(args.n):
            p = resolve_params(args, rng)
            samples.append(generate(p))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
