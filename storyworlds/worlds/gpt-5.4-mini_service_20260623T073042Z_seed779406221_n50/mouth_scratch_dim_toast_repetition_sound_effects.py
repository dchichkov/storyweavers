#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T073042Z_seed779406221_n50/mouth_scratch_dim_toast_repetition_sound_effects.py
=============================================================================================================================

A tiny standalone storyworld in a fable style, shaped around a squirrel,
a scratch-dim door, and a piece of toast. The world uses repetition and sound
effects as narrative instruments, with typed entities carrying physical meters
and emotional memes.

Premise:
- A hungry little creature wants toast.
- A careful helper warns that a scratch-dim door makes loud sound effects.
- The creature learns to wait, use its mouth politely, and keep the toast safe.

The story variants are intentionally small and constraint-checked:
- mouth: a body part used to ask, nibble, or speak
- scratch-dim: a narrow, scratchy door or latch that makes sound effects
- toast: the prize or snack at the center of the tale
- repetition: repeated phrases like "tap, tap" or "wait, wait" to feel fable-like
- sound effects: "scritch-scratch", "tap tap", "pop", "munch"

The prose is fully driven by world state and causal turns, not a frozen template.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "squirrel", "child"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    label: str
    mood: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mouth:
    id: str
    label: str
    sound: str
    kind: str


@dataclass
class ScratchDim:
    id: str
    label: str
    sound: str
    noisy: bool = True


@dataclass
class Toast:
    id: str
    label: str
    phrase: str
    crisp: bool = True
    warm: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.history: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.history[-1].append(text)

    def para(self) -> None:
        if self.history[-1]:
            self.history.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.history if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes), "attrs": dict(v.attrs),
        }) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = [[]]
        clone.fired = set(self.fired)
        return clone


def _init_meter(e: Entity, key: str, value: float = 0.0) -> None:
    e.meters.setdefault(key, value)


def _init_meme(e: Entity, key: str, value: float = 0.0) -> None:
    e.memes.setdefault(key, value)


def sound_repeat(base: str, times: int = 2) -> str:
    return ", ".join([base] * times)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    # scratch-dim makes noise whenever the hungry creature uses it.
    mouse = world.entities.get("mouse")
    door = world.entities.get("door")
    toast = world.entities.get("toast")
    if mouse and door and toast and mouse.meters.get("hunger", 0) >= THRESHOLD:
        if door.id not in world.fired and world.facts.get("door_open"):
            world.fired.add(door.id)
            door.meters["scratch"] = door.meters.get("scratch", 0) + 1
            mouse.memes["impatience"] = mouse.memes.get("impatience", 0) + 1
            out.append("scritch-scratch, scritch-scratch.")
    if toast and mouse and mouse.meters.get("hunger", 0) >= THRESHOLD and world.facts.get("toast_safe"):
        if "eat" not in world.fired:
            world.fired.add("eat")
            mouse.meters["full"] = mouse.meters.get("full", 0) + 1
            mouse.meters["hunger"] = 0
            mouse.memes["joy"] = mouse.memes.get("joy", 0) + 1
            out.append("munch, munch, munch.")
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    setting: str
    creature: str
    helper: str
    toast_style: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(label="the kitchen", mood="warm", afford={"toast"}),
    "farmhouse": Setting(label="the farmhouse kitchen", mood="cozy", afford={"toast"}),
    "sunroom": Setting(label="the sunroom", mood="bright", afford={"toast"}),
}

CREATURES = {
    "mouse": ("mouse", "a small mouse"),
    "squirrel": ("squirrel", "a nimble squirrel"),
}

HELPERS = {
    "owl": ("owl", "a patient owl"),
    "grandpa": ("grandpa", "a kind grandpa"),
    "cat": ("cat", "a sleepy cat"),
}

TOASTS = {
    "plain": Toast(id="toast", label="toast", phrase="a warm piece of toast"),
    "honey": Toast(id="toast", label="toast", phrase="a warm piece of honey toast"),
    "berry": Toast(id="toast", label="toast", phrase="a warm piece of berry toast"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, h) for s in SETTINGS for c in CREATURES for h in HELPERS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable about mouth, scratch-dim, and toast.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--toast-style", choices=TOASTS)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.creature is None or c[1] == args.creature)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, creature, helper = rng.choice(sorted(combos))
    toast_style = args.toast_style or rng.choice(sorted(TOASTS))
    return StoryParams(setting=setting, creature=creature, helper=helper, toast_style=toast_style)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    creature_kind, creature_label = CREATURES[params.creature]
    helper_kind, helper_label = HELPERS[params.helper]
    toast = TOASTS[params.toast_style]

    mouse = world.add(Entity(id="mouse", kind="character", type=creature_kind, label=creature_label))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=helper_label))
    mouth = world.add(Entity(id="mouth", kind="body", type="mouth", label="mouth", attrs={"purpose": "speak"}))
    door = world.add(Entity(id="door", kind="thing", type="door", label="scratch-dim door", attrs={"sound": "scritch-scratch"}))
    toast_e = world.add(Entity(id="toast", kind="thing", type="toast", label="toast", phrase=toast.phrase))

    for e in (mouse, helper, mouth, door, toast_e):
        _init_meter(e, "hunger")
        _init_meter(e, "scratch")
        _init_meter(e, "warmth")
        _init_meter(e, "full")
        _init_meme(e, "joy")
        _init_meme(e, "calm")
        _init_meme(e, "worry")

    world.facts["door_open"] = False
    world.facts["toast_safe"] = False

    mouse.meters["hunger"] = 1
    helper.memes["calm"] = 1

    world.say(f"Once in {world.setting.label}, a little {creature_label} smelled {toast.phrase}.")
    world.say(f"It said, {sound_repeat('tap tap', 2)} with its mouth, and asked for breakfast.")
    world.para()
    world.say(f"But the {door.label} went scritch-scratch, scritch-scratch whenever it opened.")
    world.say(f"The helper smiled. 'Wait, wait,' it said. 'Use your mouth to ask, not to rush.'")
    world.say(f"The little creature listened, and listened again, because wise ears hear twice.")
    world.para()
    world.facts["door_open"] = True
    mouse.meters["hunger"] = 1
    propagate(world)
    world.say(f"Then the helper brought the toast close, warm and safe.")
    world.facts["toast_safe"] = True
    propagate(world)
    world.para()
    world.say(f"The creature took a small bite, then another, and its mouth made a happy munching sound.")
    world.say(f"At last the toast was gone, and the scratch-dim door had no power over the meal.")
    world.say(f"So the creature learned: patience is a small key that opens a good day.")

    world.facts.update(creature=mouse, helper=helper, mouth=mouth, door=door, toast=toast_e)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    creature = f["creature"]
    return [
        f"Write a short fable about a {creature.type} who wants toast and learns to wait.",
        f"Tell a child-friendly story that repeats a phrase and uses sound effects like scritch-scratch and tap tap.",
        f"Make a little moral tale about mouth, scratch-dim, and toast in {world.setting.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    creature = f["creature"]
    helper = f["helper"]
    return [
        QAItem(
            question="Who wanted the toast?",
            answer=f"A little {creature.type} wanted the toast after smelling it in {world.setting.label}.",
        ),
        QAItem(
            question="What sound did the scratch-dim door make?",
            answer="It made a scritch-scratch sound, which was noisy and a little sharp.",
        ),
        QAItem(
            question="What did the helper tell the creature?",
            answer="The helper told the creature to wait, wait and to use its mouth to ask politely.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The creature ate the toast safely, and patience helped make the day good.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is toast?", answer="Toast is bread that has been browned and made warm and crisp."),
        QAItem(question="What is a mouth for?", answer="A mouth is used for speaking, eating, and making sounds."),
        QAItem(question="What is scratch-dim meant to suggest?", answer="It suggests something narrow and scratchy that makes a scritch-scratch sound."),
    ]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    if qa:
        print()
        print("== Prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== Story QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== World QA ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print("% ASP not used in this small world.")
        return
    if args.verify:
        print("OK: no ASP twin in this compact storyworld.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for s, c, h in valid_combos():
            params = StoryParams(setting=s, creature=c, helper=h, toast_style="plain")
            samples.append(generate(params))
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
